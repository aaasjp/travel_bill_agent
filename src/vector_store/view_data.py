import chromadb
from chromadb.config import Settings
import os
import json

def view_vector_store():
    """
    查看向量库中存储的数据
    """
    persist_directory = "data/chroma_db"
    
    # 确保目录存在
    os.makedirs(persist_directory, exist_ok=True)
    
    # 创建持久化客户端
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=chromadb.config.Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # 获取所有集合
    collections = client.list_collections()
    print("\n=== 可用的集合 ===")
    for collection in collections:
        print(f"\n集合名称: {collection.name}")
        
        # 获取集合中的所有文档
        results = collection.get()
        
        if results and results['documents']:
            print("\n文档内容:")
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"\n文档 {i+1}:")
                print(f"内容: {doc}")
                print(f"元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
        else:
            print("该集合中没有文档")

if __name__ == "__main__":
    view_vector_store() 