from .chroma_store import ChromaStore

print("开始测试向量存储")
# 创建向量存储实例

from src.config import CHROMA_COLLECTION_NAME
vector_store = ChromaStore()

# 创建旅游信息集合
vector_store.create_collection(CHROMA_COLLECTION_NAME)

# 存储一些旅游相关的文本
documents = [
    "北京故宫是中国明清两代的皇家宫殿",
    "上海外滩是著名的历史建筑群",
    "西安兵马俑是世界第八大奇迹"
]
metadatas = [
    {"city": "北京", "type": "历史景点", "uri": "https://example.com/beijing/forbidden-city"},
    {"city": "上海", "type": "城市景观", "uri": "https://example.com/shanghai/the-bund"},
    {"city": "西安", "type": "历史遗迹", "uri": "https://example.com/xian/terracotta-warriors"}
]

# 添加文档到向量存储（使用自动生成的UUID）
doc_ids = vector_store.add_documents(documents, metadatas,ids=["1","2","3"],summarize_content=True)
print(f"生成的文档IDs: {doc_ids}")

# 搜索相似内容
results = vector_store.search(["我想了解中国的历史景点"], n_results=2)

print("搜索结果:")
print(f"文档IDs: {results['ids']}")
print(f"文档内容: {results['documents']}")
print(f"元数据: {results['metadatas']}")
print(f"相似度距离: {results['distances']}")