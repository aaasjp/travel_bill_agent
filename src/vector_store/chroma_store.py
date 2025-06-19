import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
import uuid
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from chromadb import Documents, EmbeddingFunction, Embeddings
from src.config import (
    CHROMA_PERSIST_DIRECTORY, 
    CHROMA_COLLECTION_METADATA,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME
)
from ..utils.file_utils import is_valid_file, process_file
from ..llm import get_llm

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
                     ids: Optional[List[str]] = None,
                     summarize_content: bool = False) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            metadatas: 元数据列表
            ids: 文档ID列表，如果不提供则自动生成UUID
            summarize_content: 是否对文档内容进行总结，默认为False
            
        Returns:
            生成的文档ID列表
        """
        if metadatas is None:
            metadatas = [{} for _ in documents]
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # 如果需要总结内容，对每个文档进行总结
        if summarize_content:
            for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                summary_result = self.summarize_text_content(doc)
                if summary_result["success"]:
                    metadata["summary"] = summary_result["summary"]
                    metadata["summary_length"] = summary_result["summary_length"]
                else:
                    # 如果总结失败，记录错误信息
                    metadata["summary_error"] = summary_result["error"]
            
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
        
    def search(self,
              query_texts: List[str],
              n_results: int = 5,
              where: Optional[Dict[str, Any]] = None,
              similarity_threshold: float = 0.0) -> Dict[str, Any]:
        """
        搜索相似文档
        
        Args:
            query_texts: 查询文本列表
            n_results: 返回结果数量
            where: 过滤条件
            similarity_threshold: 相似度阈值，范围0-1，只有相似度大于等于此值的结果才会返回，默认为0.0（返回所有结果）
            
        Returns:
            包含搜索结果、距离和元数据的字典
        """
        # 验证相似度阈值
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError("相似度阈值必须在0.0到1.0之间")
        
        # 获取更多结果用于后续过滤
        max_results = max(n_results * 3, 50)  # 获取更多结果以确保有足够的结果通过阈值过滤
        
        results = self.collection.query(
            query_texts=query_texts,
            n_results=max_results,
            where=where,
            include=[
                "metadatas",
                "documents", 
                "distances"
                #"embeddings"
            ]
        )
        
        # 如果不需要阈值过滤，直接返回原始结果
        if similarity_threshold == 0.0:
            # 只返回请求的数量
            for key in results:
                if isinstance(results[key], list) and len(results[key]) > 0:
                    results[key] = results[key][:n_results]
            return results
        
        # 过滤结果：将距离转换为相似度，然后根据阈值过滤
        filtered_results = {
            "ids": [],
            "distances": [],
            "metadatas": [],
            "documents": []
        }
        
        for i, query_text in enumerate(query_texts):
            query_ids = results["ids"][i] if results["ids"] else []
            query_distances = results["distances"][i] if results["distances"] else []
            query_metadatas = results["metadatas"][i] if results["metadatas"] else []
            query_documents = results["documents"][i] if results["documents"] else []
            
            filtered_ids = []
            filtered_distances = []
            filtered_metadatas = []
            filtered_documents = []
            
            for j, distance in enumerate(query_distances):
                # 将距离转换为相似度 (距离越小，相似度越高)
                # 使用余弦相似度的转换公式：similarity = 1 - distance
                similarity = 1.0 - distance
                
                if similarity >= similarity_threshold:
                    filtered_ids.append(query_ids[j])
                    filtered_distances.append(distance)
                    filtered_metadatas.append(query_metadatas[j])
                    filtered_documents.append(query_documents[j])
                    
                    # 如果已经达到请求的结果数量，停止添加
                    if len(filtered_ids) >= n_results:
                        break
            
            filtered_results["ids"].append(filtered_ids)
            filtered_results["distances"].append(filtered_distances)
            filtered_results["metadatas"].append(filtered_metadatas)
            filtered_results["documents"].append(filtered_documents)
        
        return filtered_results
    
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
    
    def add_file(self, file_path: str, summarize_content: bool = False) -> Dict[str, Any]:
        """
        添加单个文件到向量数据库
        
        Args:
            file_path: 文件路径
            summarize_content: 是否对文件内容进行总结，默认为False
            
        Returns:
            包含处理结果的字典，包括成功状态、文件信息和错误信息
        """
        try:
            # 转换为Path对象进行有效性检查
            path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not path_obj.exists():
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "文件不存在"
                }
            
            # 检查文件是否有效
            if not is_valid_file(path_obj):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "文件无效（临时文件或隐藏文件）"
                }
            
            # 处理文件内容
            try:
                content = process_file(file_path)
                if not content.strip():
                    return {
                        "success": False,
                        "file_path": file_path,
                        "error": "文件内容为空"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"文件处理失败: {str(e)}"
                }
            
            # 准备添加到向量数据库的数据
            document_id = str(uuid.uuid4())
            metadata = {
                "path": file_path,
                "filename": path_obj.name,
                "file_extension": path_obj.suffix.lower(),
                "file_size": path_obj.stat().st_size
            }
            
            # 如果需要总结内容，进行总结
            if summarize_content:
                summary_result = self.summarize_text_content(content)
                if summary_result["success"]:
                    metadata["summary"] = summary_result["summary"]
                    metadata["summary_length"] = summary_result["summary_length"]
                else:
                    metadata["summary_error"] = summary_result["error"]
            
            # 添加到向量数据库
            try:
                self.add_documents(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[document_id],
                    summarize_content=False  # 已经手动处理了总结
                )
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "document_id": document_id,
                    "metadata": metadata,
                    "content_length": len(content)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"向量数据库添加失败: {str(e)}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": f"处理文件时发生错误: {str(e)}"
            }
    
    def add_files_batch(self, file_paths: List[str], summarize_content: bool = False) -> Dict[str, Any]:
        """
        批量添加文件到向量数据库
        
        Args:
            file_paths: 文件路径列表
            summarize_content: 是否对文件内容进行总结，默认为False
            
        Returns:
            包含处理结果的字典，包括成功添加的文件、失败的文件和统计信息
        """
        successful_files = []
        failed_files = []
        documents = []
        metadatas = []
        ids = []
        
        for file_path in file_paths:
            try:
                # 转换为Path对象进行有效性检查
                path_obj = Path(file_path)
                
                # 检查文件是否存在
                if not path_obj.exists():
                    failed_files.append({
                        "file_path": file_path,
                        "error": "文件不存在"
                    })
                    continue
                
                # 检查文件是否有效
                if not is_valid_file(path_obj):
                    failed_files.append({
                        "file_path": file_path,
                        "error": "文件无效（临时文件或隐藏文件）"
                    })
                    continue
                
                # 处理文件内容
                try:
                    content = process_file(file_path)
                    if not content.strip():
                        failed_files.append({
                            "file_path": file_path,
                            "error": "文件内容为空"
                        })
                        continue
                except Exception as e:
                    failed_files.append({
                        "file_path": file_path,
                        "error": f"文件处理失败: {str(e)}"
                    })
                    continue
                
                # 准备添加到向量数据库的数据
                metadata = {
                    "path": file_path,
                    "filename": path_obj.name,
                    "file_extension": path_obj.suffix.lower(),
                    "file_size": path_obj.stat().st_size
                }
                
                # 如果需要总结内容，进行总结
                if summarize_content:
                    summary_result = self.summarize_text_content(content)
                    if summary_result["success"]:
                        metadata["summary"] = summary_result["summary"]
                        metadata["summary_length"] = summary_result["summary_length"]
                    else:
                        metadata["summary_error"] = summary_result["error"]
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(str(uuid.uuid4()))
                
                successful_files.append(file_path)
                
            except Exception as e:
                failed_files.append({
                    "file_path": file_path,
                    "error": f"处理文件时发生错误: {str(e)}"
                })
        
        # 如果有成功处理的文件，添加到向量数据库
        if documents:
            try:
                self.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    summarize_content=False  # 已经手动处理了总结
                )
            except Exception as e:
                # 如果批量添加失败，将所有文件标记为失败
                failed_files.extend([
                    {
                        "file_path": file_path,
                        "error": f"向量数据库添加失败: {str(e)}"
                    }
                    for file_path in successful_files
                ])
                successful_files = []
        
        return {
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_files": len(file_paths),
            "successful_count": len(successful_files),
            "failed_count": len(failed_files)
        }
    
    def add_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        将目录下的所有文件添加到向量数据库
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归处理子目录，默认为True
            
        Returns:
            包含处理结果的字典，包括成功添加的文件、失败的文件和统计信息
        """
        directory = Path(directory_path)
        
        # 检查目录是否存在
        if not directory.exists():
            return {
                "successful_files": [],
                "failed_files": [],
                "total_files": 0,
                "successful_count": 0,
                "failed_count": 0,
                "error": f"目录不存在: {directory_path}"
            }
        
        if not directory.is_dir():
            return {
                "successful_files": [],
                "failed_files": [],
                "total_files": 0,
                "successful_count": 0,
                "failed_count": 0,
                "error": f"路径不是目录: {directory_path}"
            }
        
        # 收集所有文件路径
        file_paths = []
        if recursive:
            # 递归收集所有文件
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    file_paths.append(str(file_path))
        else:
            # 只收集当前目录下的文件
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_paths.append(str(file_path))
        
        # 使用批量添加方法处理文件
        return self.add_files_batch(file_paths)
    
    def summarize_text_content(self, content: str, max_length: int = 500, content_type: str = "text") -> Dict[str, Any]:
        """
        使用大模型总结文本内容
        
        Args:
            content: 要总结的文本内容
            max_length: 总结文本的最大长度，默认为1000字符
            content_type: 内容类型，用于提示大模型更好地理解内容，默认为"text"
            
        Returns:
            包含总结结果的字典，包括成功状态、总结内容和错误信息
        """
        try:
            # 检查内容是否为空
            if not content or not content.strip():
                return {
                    "success": False,
                    "error": "文本内容为空"
                }
            
            # 获取大模型实例
            try:
                llm = get_llm()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"获取大模型实例失败: {str(e)}"
                }
            
            # 构建总结提示
            summary_prompt = f"""
请对以下{content_type}内容进行总结，要求：
1. 总结要简洁明了，突出重点信息
2. 总结长度控制在{max_length}字符以内
3. 保留关键的业务信息、数据、结论等
4. 如果是表格或结构化数据，提取主要数据点
5. 如果是政策文档，提取核心条款和要求
6. 如果是技术文档，提取主要概念和步骤

内容类型: {content_type}
内容长度: {len(content)} 字符

内容:
{content}

仅输出总结，不要输出其他内容。/no_think
"""
            
            # 调用大模型进行总结
            try:
                response = llm.invoke(summary_prompt)
                summary = response.content.strip()
                # 去掉think部分
                summary = summary.split("</think>")[1].strip()
                print(f"summary: {summary}")
                # 如果总结为空，返回错误
                if not summary:
                    return {
                        "success": False,
                        "error": "大模型返回的总结为空"
                    }
                
                return {
                    "success": True,
                    "original_content_length": len(content),
                    "summary": summary,
                    "summary_length": len(summary),
                    "content_type": content_type
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"大模型总结失败: {str(e)}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"处理文本时发生错误: {str(e)}"
            }
    
