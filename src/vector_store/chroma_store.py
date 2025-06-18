import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from .config import CHROMA_PERSIST_DIRECTORY, CHROMA_COLLECTION_METADATA

class ChromaStore:
    def __init__(self, persist_directory: str = CHROMA_PERSIST_DIRECTORY):
        """
        初始化Chroma向量存储
        
        Args:
            persist_directory: 持久化存储目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        
    def create_collection(self, collection_name: str) -> None:
        """
        创建新的集合
        
        Args:
            collection_name: 集合名称
        """
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=CHROMA_COLLECTION_METADATA
        )
        
    def add_documents(self, 
                     documents: List[str],
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None) -> None:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            metadatas: 元数据列表
            ids: 文档ID列表
        """
        if metadatas is None:
            metadatas = [{} for _ in documents]
        if ids is None:
            ids = [str(i) for i in range(len(documents))]
            
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
    def search(self,
              query_texts: List[str],
              n_results: int = 5,
              where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        搜索相似文档
        
        Args:
            query_texts: 查询文本列表
            n_results: 返回结果数量
            where: 过滤条件
            
        Returns:
            包含搜索结果、距离和元数据的字典
        """
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where
        )
        return results
    
    def delete_collection(self, collection_name: str) -> None:
        """
        删除集合
        
        Args:
            collection_name: 集合名称
        """
        self.client.delete_collection(name=collection_name)
        
    def list_collections(self) -> List[str]:
        """
        列出所有集合
        
        Returns:
            集合名称列表
        """
        return [collection.name for collection in self.client.list_collections()] 