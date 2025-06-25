# coding = utf-8
import time
import math
import pandas as pd
from sqlalchemy import create_engine
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from operator import itemgetter

# --- 数据库配置 ---
DB_CONFIG = {
    'user': 'root',
    'password': '123456',
    'host': '127.0.0.1',
    'port': '3306',
    'database': 'learning'
}

# --- 初始化 FastAPI 应用 ---
app = FastAPI(
    title="Real-time Recommendation System API",
    description="An API that provides real-time course recommendations by querying the database on each request.",
    version="2.0.0"
)

# --- 配置 CORS (保持不变) ---
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "null"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 数据库引擎 ---
# 我们在应用启动时创建一次引擎，以便复用连接
try:
    db_connection_str = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(db_connection_str)
    # 检查连接是否成功
    with engine.connect() as connection:
        print("Database connection successful for the API.")
except Exception as e:
    print(f"FATAL: Database connection failed on startup: {e}")
    engine = None


# --- 实时推荐的核心逻辑函数 ---
def calculate_recommendations_realtime(user_id: str, top_n: int, n_sim_user: int):
    """
    在单次请求中完成所有计算并返回推荐结果。
    这个函数整合了原 UserBasedCF 类的所有逻辑。
    """
    if not engine:
        raise Exception("Database engine is not available.")

    # === 1. 从数据库加载最新数据 ===
    query = """
    SELECT u.id AS userId, e.course_id AS movieId
    FROM evaluation AS e
    JOIN user AS u ON e.user_name = u.username;
    """
    ratings_df = pd.read_sql(query, engine)

    trainSet = {}
    for _, row in ratings_df.iterrows():
        db_user, db_movie = str(row['userId']), str(row['movieId'])
        trainSet.setdefault(db_user, {})
        trainSet[db_user][db_movie] = 1

    if user_id not in trainSet:
        return []  # 冷启动用户，直接返回空

    # === 2. 实时计算用户相似度 ===
    # 2.1 建立课程-用户倒排表
    movie_user = {}
    for u, movies in trainSet.items():
        for movie in movies:
            movie_user.setdefault(movie, set())
            movie_user[movie].add(u)

    # 2.2 计算用户间共同看过的课程数
    user_sim_matrix = {}
    for _, users in movie_user.items():
        for u in users:
            for v in users:
                if u == v: continue
                user_sim_matrix.setdefault(u, {})
                user_sim_matrix[u].setdefault(v, 0)
                user_sim_matrix[u][v] += 1

    # 2.3 计算余弦相似度
    for u, related_users in user_sim_matrix.items():
        for v, count in related_users.items():
            len_u = len(trainSet.get(u, {}))
            len_v = len(trainSet.get(v, {}))
            if len_u > 0 and len_v > 0:
                user_sim_matrix[u][v] = count / math.sqrt(len_u * len_v)

    # === 3. 生成推荐列表 (与之前逻辑相同) ===
    rank = {}
    watched_movies = trainSet.get(user_id, {})

    if user_id not in user_sim_matrix:
        return []

    similar_users = sorted(user_sim_matrix[user_id].items(), key=itemgetter(1), reverse=True)[0:n_sim_user]

    for v, wuv in similar_users:
        for movie in trainSet.get(v, {}):
            if movie in watched_movies:
                continue
            rank.setdefault(movie, 0)
            rank[movie] += wuv

    sorted_rank = sorted(rank.items(), key=itemgetter(1), reverse=True)
    recommended_ids = [item[0] for item in sorted_rank]

    return recommended_ids[:top_n]


@app.get("/")
def read_root():
    return {"status": "Real-time Recommendation API is running."}


@app.get("/recommend/{user_id}", response_model=List[str])
def get_recommendations_for_user(user_id: int, top_n: int = 10):
    """
    为指定用户ID实时生成推荐课程ID列表。
    - 每次调用都会重新从数据库拉取数据并计算。
    """
    start_time = time.time()
    user_id_str = str(user_id)

    if engine is None:
        raise HTTPException(status_code=503, detail="Database connection is not available.")

    try:
        # 调用实时计算函数
        # 这里的 n_sim_user=20 是原来 UserBasedCF 的默认值，可以按需调整
        recommended_ids = calculate_recommendations_realtime(user_id_str, top_n, n_sim_user=20)

        end_time = time.time()
        print(f"Real-time recommendation for user {user_id} took {end_time - start_time:.4f} seconds.")

        return recommended_ids
    except Exception as e:
        print(f"Error during real-time recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")