cd backend
conda activate pytorch

# RAG+大模型
pip install flask faiss-cpu requests numpy gunicorn
python app.py

# 推荐算法
python -m uvicorn api:app --reload