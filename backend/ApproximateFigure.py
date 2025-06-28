import os
import pickle
import uuid  # 用于生成唯一文件名
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import json

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

# --- 新增：对象存储 ---
from minio import Minio
from minio.error import S3Error

# ==============================================================================
# 1. 初始化和配置
# ==============================================================================
load_dotenv()

# 清除代理环境变量，确保直接连接
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

app = Flask(__name__)
CORS(app)

# --- MinIO 客户端初始化 ---
try:
    minio_client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False  # 如果您的MinIO没有配置SSL，请设为False
    )
    print("MinIO 客户端初始化成功。")
except Exception as e:
    print(f"MinIO 客户端初始化失败: {e}")
    minio_client = None


# --- 数据库、模型加载等函数 (这部分代码没有问题，保持原样) ---
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


# --- 新增VR资料上传接口 ---
@app.route('/vr/upload', methods=['POST'])
def upload_vr_profile():
    """
    接收表单数据（name 和 profile_picture），上传图片到MinIO，并将信息存入数据库的vr表。
    """
    # 1. 检查输入
    if minio_client is None:
        return jsonify({'error': '对象存储服务未初始化'}), 503  # 503 Service Unavailable

    if 'profile_picture' not in request.files:
        return jsonify({'error': '请求中未包含名为 "profile_picture" 的图片文件'}), 400
    if 'name' not in request.form:
        return jsonify({'error': '请求中未包含名为 "name" 的文本字段'}), 400

    image_file = request.files['profile_picture']
    name = request.form['name']

    if image_file.filename == '':
        return jsonify({'error': '未选择任何图片文件'}), 400
    if not name:
        return jsonify({'error': 'name 字段不能为空'}), 400

    # 2. 上传图片到MinIO
    try:
        bucket_name = os.getenv('MINIO_BUCKET_VR', 'cover-pictures')

        # 检查存储桶是否存在，如果不存在则创建
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)
            print(f"存储桶 '{bucket_name}' 已创建。")

        # 为防止文件名冲突，生成一个唯一的文件名
        file_ext = os.path.splitext(image_file.filename)[1]
        object_name = f"{uuid.uuid4()}{file_ext}"

        # 从文件流上传
        image_file.seek(0, os.SEEK_END)
        file_length = image_file.tell()
        image_file.seek(0, os.SEEK_SET)

        minio_client.put_object(
            bucket_name,
            object_name,
            image_file,
            length=file_length,
            content_type=image_file.content_type
        )

        # 构造可访问的URL
        image_url = f"http://{os.getenv('MINIO_ENDPOINT')}/{bucket_name}/{object_name}"
        print(f"文件成功上传到MinIO，URL: {image_url}")

    except S3Error as exc:
        print(f"上传到MinIO时发生错误: {exc}")
        return jsonify({'error': f'无法上传文件到对象存储: {exc}'}), 500

    # 3. 将信息存入数据库
    connection = get_db_connection()
    if not connection:
        # 注意：此时图片已上传到MinIO，但数据库失败。在生产环境中，您可能需要一个清理机制。
        return jsonify({'error': '数据库连接失败，数据未保存'}), 500

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `vr` (`name`, `profile_picture`) VALUES (%s, %s)"
            cursor.execute(sql, (name, image_url))
        connection.commit()
    except pymysql.Error as e:
        print(f"数据库插入错误: {e}")
        # 同上，这里也需要考虑清理已上传的MinIO对象
        return jsonify({'error': f'数据库写入失败: {e}'}), 500
    finally:
        if connection:
            connection.close()

    # 4. 返回成功响应
    return jsonify({
        'status': 'success',
        'message': 'VR资料上传成功',
        'data': {
            'name': name,
            'profile_picture_url': image_url
        }
    }), 201  # 201 Created


# --- ↓↓↓ 在这里添加缺失的接口 ↓↓↓ ---
@app.route('/vr/profile', methods=['GET'])
def get_vr_profile():
    """
    根据查询参数 'name' 从数据库中查找对应的全景图片URL。
    """
    # 1. 从请求的查询参数中获取 'name'
    name = request.args.get('name')
    if not name:
        return jsonify({'error': '缺少 "name" 查询参数'}), 400

    # 2. 连接数据库
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': '数据库连接失败'}), 500

    # 3. 执行查询
    try:
        with connection.cursor() as cursor:
            # 假设每个名称是唯一的，我们只取第一条记录
            sql = "SELECT profile_picture FROM `vr` WHERE `name` = %s LIMIT 1"
            cursor.execute(sql, (name,))
            result = cursor.fetchone()

            if result:
                # 如果找到了，返回一个包含 profile_picture 的 JSON 对象和 200 OK
                return jsonify(result), 200
            else:
                # 如果在数据库中没找到，返回一个错误信息和 404 Not Found
                return jsonify({'error': '数据库中未找到匹配的VR资料'}), 404
    except pymysql.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({'error': '数据库查询失败'}), 500
    finally:
        if connection:
            connection.close()


# --- ↑↑↑ 添加结束 ↑↑↑ ---

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