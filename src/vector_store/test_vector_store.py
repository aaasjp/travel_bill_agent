from chroma_store import ChromaStore

# 创建向量存储实例
vector_store = ChromaStore()

# 创建旅游信息集合
vector_store.create_collection("travel_info")

# 存储一些旅游相关的文本
documents = [
    "北京故宫是中国明清两代的皇家宫殿",
    "上海外滩是著名的历史建筑群",
    "西安兵马俑是世界第八大奇迹"
]
metadatas = [
    {"city": "北京", "type": "历史景点"},
    {"city": "上海", "type": "城市景观"},
    {"city": "西安", "type": "历史遗迹"}
]

# 添加文档到向量存储
vector_store.add_documents(documents, metadatas)

# 搜索相似内容
results = vector_store.search(["我想了解中国的历史景点"], n_results=2)

print(results)