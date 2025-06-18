"""
向量存储配置
"""

# ChromaDB 配置
CHROMA_PERSIST_DIRECTORY = "memory_data/chroma_db"
CHROMA_COLLECTION_METADATA = {
    "hnsw:space": "cosine"  # 使用余弦相似度
} 