import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
import uuid
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from chromadb import Documents, EmbeddingFunction, Embeddings
from .config import (
    CHROMA_PERSIST_DIRECTORY, 
    CHROMA_COLLECTION_METADATA,
    EMBEDDING_MODEL_NAME
)

class GTEEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
    def __call__(self, input: Documents) -> Embeddings:
        # 对文本进行编码
        batch_dict = self.tokenizer(
            input, 
            max_length=8192, 
            padding=True, 
            truncation=True, 
            return_tensors='pt'
        )
        
        # 获取模型输出
        with torch.no_grad():
            outputs = self.model(**batch_dict)
        
        # 使用 CLS token 作为句子表示
        embeddings = outputs.last_hidden_state[:, 0]
        
        # L2 归一化
        embeddings = F.normalize(embeddings, p=2, dim=1)
        
        return embeddings.tolist()

class ChromaStore:
    def __init__(self, persist_directory: str = CHROMA_PERSIST_DIRECTORY):
        """
        初始化Chroma向量存储
        
        Args:
            persist_directory: 持久化存储目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 embedding 函数
        self.embedding_function = GTEEmbeddingFunction(EMBEDDING_MODEL_NAME)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    def create_collection(self, collection_name: str) -> None:
        """
        创建新的集合
        
        Args:
            collection_name: 集合名称
        """
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=CHROMA_COLLECTION_METADATA,
            embedding_function=self.embedding_function
        )
        
    def add_documents(self, 
                     documents: List[str],
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     uris: Optional[List[str]] = None,
                     ids: Optional[List[str]] = None) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            metadatas: 元数据列表
            uris: URI列表
            ids: 文档ID列表，如果不提供则自动生成UUID
            
        Returns:
            生成的文档ID列表
        """
        if metadatas is None:
            metadatas = [{} for _ in documents]
        if uris is None:
            uris = ["" for _ in documents]
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
            
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            uris=uris,
            ids=ids
        )
        
        return ids
        
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
            包含搜索结果、距离、元数据和URIs的字典
        """
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            include=[
                "metadatas",
                "documents", 
                "distances",
                "uris"
                #"embeddings"
            ]
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