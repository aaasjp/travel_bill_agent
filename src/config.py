import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 禁用ChromaDB遥测
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["CHROMA_ANONYMIZED_TELEMETRY"] = "false"

# 模型配置
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen3-235b-a22b")
MODEL_BASE_URL = os.environ.get("MODEL_BASE_URL", "http://10.249.238.52:13206/member3/qwen3-235b-a22b/v1")
API_KEY = os.environ.get("API_KEY", "EMPTY")

# 应用配置
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

# LangSmith配置
LANGSMITH_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "")
LANGSMITH_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "智能体")
LANGSMITH_ENDPOINT = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# 工具配置
TOOLS_ENABLED = os.environ.get("TOOLS_ENABLED", "true").lower() == "true"

# ChromaDB 配置
CHROMA_PERSIST_DIRECTORY = "data/chroma_db"
CHROMA_COLLECTION_NAME = "travel_reimbursement"
CHROMA_COLLECTION_METADATA = {
    "hnsw:space": "cosine",  # 使用余弦相似度
    "embedding_model": "Alibaba-NLP/gte-modernbert-base",  # 使用 Alibaba 的 embedding 模型
    "embedding_dimension": 768  # 模型输出维度
}

# Embedding 模型配置
EMBEDDING_MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"
EMBEDDING_MODEL_DIMENSION = 768  # gte-modernbert-base 模型的输出维度 