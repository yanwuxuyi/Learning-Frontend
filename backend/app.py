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
        prompt = f"请根据以下信息为旅游产品智能定价：城市：{city}，当前价格：{current_price}，用户评分：{rating}。只返回一个数字，单位元。"
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
    prompt = f"请根据以下信息为旅游产品智能定价：城市：{product_name}，当前价格：{current_price}，用户评分：{rating}。只返回一个数字，单位元。"
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

# ========== 机票搜索相关API ==========
from flight_crawler import search_flights_api, cleanup_crawler

@app.route('/api/flights/search', methods=['POST'])
def search_flights():
    """机票搜索API"""
    try:
        data = request.get_json()
        departure = data.get('departure')
        arrival = data.get('arrival')
        departure_date = data.get('departureDate')
        return_date = data.get('returnDate')
        
        if not departure or not arrival or not departure_date:
            return jsonify({
                'success': False,
                'message': '缺少必要参数：出发地、目的地、出发日期'
            }), 400
        
        print(f"开始搜索机票: {departure} -> {arrival}, 日期: {departure_date}")
        
        # 调用爬虫API
        result = search_flights_api(departure, arrival, departure_date, return_date)
        
        if result.get('success'):
            print(f"机票搜索成功，找到 {len(result.get('flights', []))} 个航班")
        else:
            print(f"机票搜索失败: {result.get('message')}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"机票搜索API错误: {e}")
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}',
            'flights': []
        }), 500

@app.route('/api/flights/status', methods=['GET'])
def get_flight_search_status():
    """获取机票搜索功能状态"""
    try:
        # 检查seleniumwire是否可用
        import seleniumwire
        return jsonify({
            'available': True,
            'message': '机票搜索功能可用'
        })
    except ImportError:
        return jsonify({
            'available': False,
            'message': '机票搜索功能不可用，缺少seleniumwire依赖'
        })

@app.route('/api/flights/cleanup', methods=['POST'])
def cleanup_flight_crawler():
    """清理机票爬虫资源"""
    try:
        cleanup_crawler()
        return jsonify({
            'success': True,
            'message': '爬虫资源清理成功'
        })
    except Exception as e:
        print(f"清理爬虫资源失败: {e}")
        return jsonify({
            'success': False,
            'message': f'清理失败: {str(e)}'
        }), 500

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
COURSE_INDEX_MAPPING_PATH = 'course_index_mapping.json'  # 新增：维护课程ID和向量索引的映射
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
    """从文件加载FAISS索引、课程数据和索引映射"""
    log_message("正在加载FAISS索引、课程数据和索引映射...")
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)
        log_message(f"已加载现有FAISS索引，包含 {index.ntotal} 条记录。")
    else:
        index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        log_message("未找到FAISS索引，已创建新索引。")

    if os.path.exists(COURSES_DATA_PATH):
        with open(COURSES_DATA_PATH, 'r', encoding='utf-8') as f:
            courses = json.load(f)
        
        # 数据清理：过滤掉没有id字段的无效数据
        original_count = len(courses)
        courses = [course for course in courses if 'id' in course]
        if len(courses) < original_count:
            log_message(f"数据清理完成：移除了 {original_count - len(courses)} 条无效记录（缺少id字段）")
        
        log_message(f"已加载课程数据，共 {len(courses)} 个课程。")
    else:
        courses = []
        log_message("未找到课程数据文件。")

    if os.path.exists(COURSE_INDEX_MAPPING_PATH):
        with open(COURSE_INDEX_MAPPING_PATH, 'r', encoding='utf-8') as f:
            course_index_mapping = json.load(f)
        log_message(f"已加载课程索引映射，共 {len(course_index_mapping)} 个映射。")
    else:
        course_index_mapping = {}
        log_message("未找到课程索引映射文件。")
    
    return index, courses, course_index_mapping

def save_data(index, courses, course_index_mapping):
    """将FAISS索引、课程数据和索引映射保存到文件"""
    log_message(f"正在保存FAISS索引 (共 {index.ntotal} 条记录)、课程数据 (共 {len(courses)} 个课程) 和索引映射 (共 {len(course_index_mapping)} 个映射)...")
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(COURSES_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    with open(COURSE_INDEX_MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(course_index_mapping, f, ensure_ascii=False, indent=2)
    log_message("数据保存完成。")

def rebuild_index_from_courses(courses):
    """从课程数据重建FAISS索引和映射"""
    log_message(f"正在从 {len(courses)} 个课程重建FAISS索引...")
    new_index = faiss.IndexFlatL2(VECTOR_DIMENSION)
    new_mapping = {}
    
    for i, course in enumerate(courses):
        # 安全检查：确保课程数据包含id字段
        if 'id' not in course:
            log_message(f"警告: 课程数据缺少id字段，跳过该记录: {course}")
            continue
            
        course_info = f"旅游项目名称: {course['name']}. 旅游安排: {course['description']}. 目的地: {course.get('destination', '')}. 价格: {course.get('price', '未提供')}元."
        vector = embed(course_info)
        if vector is not None:
            new_index.add(np.array([vector], dtype=np.float32))
            new_mapping[str(course['id'])] = new_index.ntotal - 1
    
    log_message(f"索引重建完成，包含 {new_index.ntotal} 条记录。")
    return new_index, new_mapping

@app.route('/api/add_course', methods=['POST'])
def add_course():
    """添加课程，同时添加到向量数据库"""
    log_message("收到 /api/add_course 请求...")
    data = request.json
    if not data or 'name' not in data or 'description' not in data:
        log_message("请求失败: 课程数据无效。")
        return jsonify({'error': '课程数据无效'}), 400

    index, courses, course_index_mapping = load_data()

    # 如果没有ID，生成一个临时ID（基于时间戳）
    if 'id' not in data:
        import time
        data['id'] = int(time.time() * 1000)  # 使用毫秒时间戳作为临时ID
        log_message(f"为新课程生成临时ID: {data['id']}")

    course_info = f"旅游项目名称: {data['name']}. 旅游安排: {data['description']}. 目的地: {data.get('destination', '')}. 价格: {data.get('price', '未提供')}元."
    
    vector = embed(course_info)
    if vector is None:
        return jsonify({'error': '创建嵌入向量失败'}), 500

    # 添加向量到索引
    index.add(np.array([vector], dtype=np.float32))
    
    # 添加课程数据
    courses.append(data)
    
    # 更新映射关系
    course_index_mapping[str(data['id'])] = index.ntotal - 1
    
    save_data(index, courses, course_index_mapping)
    
    log_message(f"课程 '{data['name']}' 添加成功。")
    return jsonify({'message': '课程添加成功', 'id': data['id']}), 201

@app.route('/api/update_course', methods=['PUT'])
def update_course():
    """更新课程，同时更新向量数据库中的对应向量"""
    log_message("收到 /api/update_course 请求...")
    data = request.json
    if not data or 'id' not in data or 'name' not in data or 'description' not in data:
        log_message("请求失败: 课程数据无效。")
        return jsonify({'error': '课程数据无效'}), 400

    index, courses, course_index_mapping = load_data()
    
    # 查找要更新的课程
    course_id = str(data['id'])
    
    # 检查向量数据库中是否存在该课程
    if course_id not in course_index_mapping:
        log_message(f"课程ID {course_id} 在向量数据库中不存在，将直接添加新记录")
        # 如果不存在，直接添加新记录
        course_info = f"旅游项目名称: {data['name']}. 旅游安排: {data['description']}. 目的地: {data.get('destination', '')}. 价格: {data.get('price', '未提供')}元."
        new_vector = embed(course_info)
        if new_vector is None:
            return jsonify({'error': '创建嵌入向量失败'}), 500

        # 添加向量到索引
        index.add(np.array([new_vector], dtype=np.float32))
        
        # 添加课程数据
        courses.append(data)
        
        # 更新映射关系
        course_index_mapping[str(data['id'])] = index.ntotal - 1
        
        save_data(index, courses, course_index_mapping)
        
        log_message(f"课程 '{data['name']}' 已添加到向量数据库。")
        return jsonify({'message': '课程已添加到向量数据库'}), 201
    
    # 如果存在，执行正常的更新逻辑
    log_message(f"课程ID {course_id} 在向量数据库中存在，执行更新操作")
    
    # 生成新的向量
    course_info = f"旅游项目名称: {data['name']}. 旅游安排: {data['description']}. 目的地: {data.get('destination', '')}. 价格: {data.get('price', '未提供')}元."
    new_vector = embed(course_info)
    if new_vector is None:
        return jsonify({'error': '创建嵌入向量失败'}), 500

    # 更新FAISS索引中的向量
    # 由于FAISS不支持直接更新，我们需要重建索引
    log_message(f"正在更新课程 '{data['name']}' 的向量...")
    
    # 找到课程在courses列表中的位置
    course_index = None
    for i, course in enumerate(courses):
        # 安全检查：确保课程数据包含id字段
        if 'id' not in course:
            log_message(f"警告: 课程数据缺少id字段，跳过该记录: {course}")
            continue
        if str(course['id']) == course_id:
            course_index = i
            break
    
    if course_index is None:
        log_message(f"请求失败: 课程ID {course_id} 在课程列表中不存在。")
        return jsonify({'error': '课程不存在'}), 404
    
    # 更新课程数据
    courses[course_index] = data
    
    # 重建索引和映射
    new_index, new_mapping = rebuild_index_from_courses(courses)
    
    # 保存更新后的数据
    save_data(new_index, courses, new_mapping)
    
    log_message(f"课程 '{data['name']}' 更新成功。")
    return jsonify({'message': '课程更新成功'}), 200

@app.route('/api/delete_course', methods=['DELETE'])
def delete_course():
    """删除课程，同时从向量数据库中删除对应向量"""
    log_message("收到 /api/delete_course 请求...")
    data = request.json
    if not data or 'id' not in data:
        log_message("请求失败: 课程ID无效。")
        return jsonify({'error': '课程ID无效'}), 400

    index, courses, course_index_mapping = load_data()
    
    course_id = str(data['id'])
    
    # 检查向量数据库中是否存在该课程
    if course_id not in course_index_mapping:
        log_message(f"课程ID {course_id} 在向量数据库中不存在，忽略删除操作")
        return jsonify({'message': '课程在向量数据库中不存在，已忽略删除操作'}), 200
    
    # 如果存在，执行正常的删除逻辑
    log_message(f"课程ID {course_id} 在向量数据库中存在，执行删除操作")
    
    # 获取要删除的课程名称用于日志
    course_name = None
    for course in courses:
        # 安全检查：确保课程数据包含id字段
        if 'id' not in course:
            log_message(f"警告: 课程数据缺少id字段，跳过该记录: {course}")
            continue
        if str(course['id']) == course_id:
            course_name = course['name']
            break
    
    if course_name is None:
        log_message(f"请求失败: 课程ID {course_id} 在课程列表中不存在。")
        return jsonify({'error': '课程不存在'}), 404
    
    # 从课程数据中删除
    courses = [course for course in courses if str(course['id']) != course_id]
    
    # 重建索引和映射
    log_message(f"正在删除课程 '{course_name}' 的向量...")
    new_index, new_mapping = rebuild_index_from_courses(courses)
    
    # 保存更新后的数据
    save_data(new_index, courses, new_mapping)
    
    log_message(f"课程 '{course_name}' 删除成功。")
    return jsonify({'message': '课程删除成功'}), 200

@app.route('/api/search_courses', methods=['POST'])
def search_courses():
    """根据用户查询搜索相似的课程"""
    log_message("收到 /api/search_courses 请求...")
    query = request.json.get('query')
    if not query:
        log_message("请求失败: 必须提供查询内容。")
        return jsonify({'error': '必须提供查询内容'}), 400
    
    log_message(f"用户查询: '{query}'")

    index, courses, course_index_mapping = load_data()
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