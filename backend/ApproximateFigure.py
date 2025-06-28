import os
import pickle
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import json  # 确保导入 json

# --- Web & Database ---
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# --- ML/AI & Web Requests ---
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.models import Model
from sklearn.metrics.pairwise import cosine_similarity
import requests

# ==============================================================================
# 1. 初始化和配置
# ==============================================================================
load_dotenv()

# 清除代理环境变量，确保直接连接
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

app = Flask(__name__)
CORS(app)


# --- 数据库、模型加载等函数 (这部分代码没有问题，保持原样) ---
# ... (为简洁起见，省略 get_db_connection, extract_features, build_index, load_or_build_index 的代码) ...
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'), user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'learning'), charset='utf8mb4', cursorclass=DictCursor
        )
        return connection
    except pymysql.Error as e:
        print(f"数据库连接失败: {e}")
        return None


def extract_features(image_stream):
    try:
        img = Image.open(image_stream).convert('RGB').resize((224, 224))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        expanded_img_array = np.expand_dims(img_array, axis=0)
        preprocessed_img = preprocess_input(expanded_img_array)
        features = model.predict(preprocessed_img, verbose=0).flatten()
        return features / np.linalg.norm(features)
    except Exception as e:
        print(f"提取特征时出错: {e}")
        return None


def build_index():
    print("正在从数据库建立新的特征索引...")
    connection = get_db_connection()
    if not connection: return None, None
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id, cover_picture FROM `course` WHERE approved = 1"
            cursor.execute(sql)
            results = cursor.fetchall()
            id_list, feature_list = [], []
            for record in results:
                record_id, image_url = record['id'], record['cover_picture']
                if not image_url: continue
                try:
                    response = requests.get(image_url, timeout=10, proxies={"http": None, "https": None})
                    response.raise_for_status()
                    features = extract_features(BytesIO(response.content))
                    if features is not None:
                        id_list.append(record_id)
                        feature_list.append(features)
                except Exception as e:
                    print(f"处理 ID: {record_id} 的图片 URL ({image_url}) 时出错: {e}")
            if not feature_list: return None, None
            with open('db_features.pkl', 'wb') as f:
                pickle.dump(np.array(feature_list), f)
            with open('db_ids.pkl', 'wb') as f:
                pickle.dump(id_list, f)
            print(f"索引创建完成！共处理了 {len(id_list)} 条记录。")
            return np.array(feature_list), id_list
    finally:
        if connection: connection.close()


def load_or_build_index():
    if os.path.exists('db_features.pkl') and os.path.exists('db_ids.pkl'):
        with open('db_features.pkl', 'rb') as f:
            features = pickle.load(f)
        with open('db_ids.pkl', 'rb') as f:
            ids = pickle.load(f)
        return features, ids
    else:
        return build_index()


# ==============================================================================
# 3. API 路由 (Endpoints)
# ==============================================================================

@app.route('/search', methods=['POST'])
def search_image():
    # ... 此函数保持不变 ...
    if 'image' not in request.files: return jsonify({'error': '请求中未包含图片文件'}), 400
    file = request.files['image']
    if not file.filename: return jsonify({'error': '未选择任何图片文件'}), 400
    query_features = extract_features(file.stream).reshape(1, -1)
    similarities = cosine_similarity(query_features, INDEX_FEATURES).flatten()
    top_indices = np.argsort(similarities)[-1::-1][:5]
    result_similarities = {INDEX_IDS[i]: float(similarities[i]) for i in top_indices if similarities[i] > 0.5}
    if not result_similarities: return jsonify({'results': []})
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(result_similarities))
            sql = f"SELECT id, name, cover_picture, description FROM `course` WHERE id IN ({format_strings})"
            cursor.execute(sql, tuple(result_similarities.keys()))
            db_results = cursor.fetchall()
            final_results = []
            for res in db_results:
                res['similarity'] = result_similarities.get(res['id'])
                final_results.append(res)
            final_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            return jsonify({'results': final_results})
    finally:
        if connection: connection.close()





# ==============================================================================
# 4. 启动应用
# ==============================================================================
if __name__ == '__main__':
    # 初始化ResNet50模型和数据库索引
    print("正在加载ResNet50模型...")
    try:
        base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
        model = Model(inputs=base_model.input, outputs=base_model.output)
        print("模型加载完成。")
        INDEX_FEATURES, INDEX_IDS = load_or_build_index()
        if INDEX_FEATURES is None:
            print("错误：索引初始化失败，服务将以受限模式启动。")
    except Exception as e:
        print(f"初始化失败: {e}")
        exit()

    print("服务准备就绪，开始在 http://0.0.0.0:5001 运行...")
    app.run(host='0.0.0.0', port=5001, debug=True)