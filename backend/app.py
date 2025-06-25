from flask import Flask, request, jsonify
from flask_cors import CORS
import faiss
import numpy as np
import requests
import json
import os
import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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

if __name__ == '__main__':
    log_message("Flask服务器启动中...")
    app.run(host='0.0.0.0', port=5000, debug=True) 