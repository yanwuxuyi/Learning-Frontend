# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, Response, stream_with_context, Blueprint
from flask_cors import CORS
import requests
import pandas as pd
import faiss
import numpy as np
import json
import os
import datetime
import math
from sqlalchemy import create_engine

app = Flask(__name__)
CORS(app, supports_credentials=True)

price_suggestion_bp = Blueprint('price_suggestion', __name__)

# ========== 定价相关API ==========
import requests
import pandas as pd

# 读取城市热度
CITY_CSV_PATH = 'scrape.csv'
def get_city_hot(city_name):
    # try:
    #     df = pd.read_csv(CITY_CSV_PATH, encoding='gbk')
    #     row = df[df['城市'] == city_name]
    #     if not row.empty:
    #         hot_str = str(row.iloc[0]['景点热度'])
    #         # 提取数字部分
    #         hot_num = int(''.join(filter(str.isdigit, hot_str)))
    #         return hot_num
    # except Exception as e:
    #     print(f"读取城市热度失败: {e}")
    return 10000  # 默认热度

# 规则定价
def rule_based_price(current_price, rating, hot):
    # 规则：当前价格*0.5 + 热度*0.0001 + 评分*100
    return round(current_price * 0.5 + hot * 0.0001 + rating * 100, 2)

# AI定价（调用本地Ollama模型API）
def ai_based_price_ollama(city, current_price, rating, hot):
    try:
        prompt = f"请根据以下信息为旅游产品智能定价：城市：{city}，当前价格：{current_price}，用户评分：{rating}，城市热度：{hot}。只返回一个数字，单位元。"
        data = {
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1
        }
        resp = requests.post('http://127.0.0.1:11434/api/generate', json=data, timeout=60)
        if resp.status_code == 200:
            res_json = resp.json()
            ai_response = res_json.get('response', '')
            import re
            price = float(re.findall(r"\d+\.?\d*", ai_response)[0])
            return round(price, 2), ai_response
        else:
            print(f"Ollama接口返回异常: {resp.status_code}")
    except Exception as e:
        print(f"Ollama AI定价失败: {e}")
    return None, ""

@price_suggestion_bp.route('/api/price_suggestion', methods=['POST'])
def price_suggestion():
    req = request.get_json()
    rating = req.get('rating')
    product_name = req.get('product_name')
    current_price = req.get('current_price')
    if rating is None or product_name is None or current_price is None:
        return jsonify({'error': '缺少评分、产品名称或当前价格参数'}), 400
    # 获取城市热度
    hot = get_city_hot(product_name)
    # 规则定价
    rule_price = rule_based_price(current_price, rating, hot)
    # AI定价（Ollama）
    ai_price, ai_full_response = ai_based_price_ollama(product_name, current_price, rating, hot)
    return jsonify({
        'rule_price': rule_price,
        'ai_price': ai_price,
        'hot': hot,
        'ai_full_response': ai_full_response
    })

@price_suggestion_bp.route('/api/price_suggestion_stream', methods=['POST'])
def price_suggestion_stream():
    req = request.get_json()
    rating = req.get('rating')
    product_name = req.get('product_name')
    current_price = req.get('current_price')
    hot = get_city_hot(product_name)
    prompt = f"请根据以下信息为旅游产品智能定价：城市：{product_name}，当前价格：{current_price}，用户评分：{rating}，城市热度：{hot}。只返回一个数字，单位元。"
    data = {
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": True,
        "temperature": 0.1
    }
    import time
    def generate():
        with requests.post('http://127.0.0.1:11434/api/generate', json=data, stream=True) as r:
            buffer = b""
            for chunk in r.iter_content(chunk_size=32):
                if chunk:
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line.strip():
                            yield line + b'\n'
                            # time.sleep(0.2)  # 可选：便于观察流式效果
    return Response(
        stream_with_context(generate()),
        content_type='text/plain',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

# ========== 智能客服相关API ==========
from flask import Flask, request, jsonify
from flask_cors import CORS
import faiss
import numpy as np
import requests
import json
import os
import datetime

# --- 配置 ---
EMBEDDING_MODEL = 'nomic-embed-text'
OLLAMA_API_URL = 'http://127.0.0.1:11434/api/embeddings'
FAISS_INDEX_PATH = 'courses.faiss'
COURSES_DATA_PATH = 'courses.json'
VECTOR_DIMENSION = 768  # nomic-embed-text 模型的向量维度

# --- 辅助函数 ---
def log_message(message):
    """打印带时间戳的日志信息"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def embed(text):
    """使用Ollama为给定文本生成嵌入向量"""
    log_message(f"准备嵌入文本: '{text[:50]}...'")
    try:
        response = requests.post(OLLAMA_API_URL, json={'model': EMBEDDING_MODEL, 'prompt': text})
        response.raise_for_status()
        embedding = response.json().get('embedding')
        log_message("文本嵌入成功。")
        return embedding
    except requests.exceptions.RequestException as e:
        log_message(f"错误: 文本嵌入失败 - {e}")
        return None

def load_data():
    """从文件加载FAISS索引和课程数据"""
    log_message("正在加载FAISS索引和课程数据...")
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)
        log_message(f"已加载现有FAISS索引，包含 {index.ntotal} 条记录。")
    else:
        index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        log_message("未找到FAISS索引，已创建新索引。")

    if os.path.exists(COURSES_DATA_PATH):
        with open(COURSES_DATA_PATH, 'r', encoding='utf-8') as f:
            courses = json.load(f)
        log_message(f"已加载课程数据，共 {len(courses)} 个课程。")
    else:
        courses = []
        log_message("未找到课程数据文件。")
    return index, courses

def save_data(index, courses):
    """将FAISS索引和课程数据保存到文件"""
    log_message(f"正在保存FAISS索引 (共 {index.ntotal} 条记录) 和课程数据 (共 {len(courses)} 个课程)...")
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(COURSES_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    log_message("数据保存成功。")

# --- API端点 ---
@app.route('/api/add_course', methods=['POST'])
def add_course():
    """接收新课程，向量化后添加到数据库"""
    log_message("收到 /api/add_course 请求...")
    data = request.json
    if not data or 'name' not in data or 'description' not in data:
        log_message("请求失败: 课程数据无效。")
        return jsonify({'error': '课程数据无效'}), 400

    index, courses = load_data()

    course_info = f"旅游项目名称: {data['name']}. 旅游安排: {data['description']}. 目的地: {data.get('destination', '')}. 价格: {data.get('price', '未提供')}元."
    
    vector = embed(course_info)
    if vector is None:
        return jsonify({'error': '创建嵌入向量失败'}), 500

    index.add(np.array([vector], dtype=np.float32))
    courses.append(data)
    
    save_data(index, courses)
    
    log_message(f"课程 '{data['name']}' 添加成功。")
    return jsonify({'message': '课程添加成功', 'id': len(courses) - 1}), 201

@app.route('/api/search_courses', methods=['POST'])
def search_courses():
    """根据用户查询搜索相似的课程"""
    log_message("收到 /api/search_courses 请求...")
    query = request.json.get('query')
    if not query:
        log_message("请求失败: 必须提供查询内容。")
        return jsonify({'error': '必须提供查询内容'}), 400
    
    log_message(f"用户查询: '{query}'")

    index, courses = load_data()
    if index.ntotal == 0:
        log_message("数据库为空，无法执行搜索。")
        return jsonify({'context': '没有可供查询的旅游项目。'})

    query_vector = embed(query)
    if query_vector is None:
        return jsonify({'error': '创建查询嵌入向量失败'}), 500

    log_message("正在FAISS中搜索相似向量...")
    distances, indices = index.search(np.array([query_vector], dtype=np.float32), k=3)
    log_message(f"搜索完成。找到的索引: {indices[0]}")

    context_parts = []
    for i in indices[0]:
        if i != -1 and i < len(courses):
            course = courses[i]
            context_parts.append(f"- 旅游项目: {course['name']}. 简介: {course['description']}.")
    
    context = "相关旅游项目信息如下：\n" + "\n".join(context_parts) if context_parts else "没有找到相关的旅游项目信息。"
    log_message(f"构建的上下文:\n{context}")
    
    return jsonify({'context': context})

app.register_blueprint(price_suggestion_bp)

if __name__ == '__main__':
    log_message("Flask服务器启动中...")
    app.run(host='0.0.0.0', port=5000, debug=True) 