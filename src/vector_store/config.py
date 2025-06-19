"""
向量存储配置
"""

# ChromaDB 配置
CHROMA_PERSIST_DIRECTORY = "data/chroma_db"
CHROMA_COLLECTION_METADATA = {
    "hnsw:space": "cosine",  # 使用余弦相似度
    "embedding_model": "Alibaba-NLP/gte-modernbert-base",  # 使用 Alibaba 的 embedding 模型
    "embedding_dimension": 768  # 模型输出维度
} 

# Embedding 模型配置
EMBEDDING_MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"
EMBEDDING_MODEL_DIMENSION = 768  # gte-modernbert-base 模型的输出维度 