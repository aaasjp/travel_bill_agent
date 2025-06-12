# RAG功能实现方案

## 📋 概述

本文档详细描述了在差旅报销智能体中集成RAG（Retrieval-Augmented Generation）功能的完整实现方案。RAG系统将为智能体提供基于知识库的上下文增强能力，显著提升回答准确性和政策合规性。

## 🎯 实现目标

### 核心目标
1. **知识增强**：为LLM提供准确的差旅政策和流程知识
2. **上下文感知**：根据用户查询动态检索相关信息
3. **合规保障**：确保建议符合最新的企业政策
4. **无缝集成**：与现有LangGraph工作流深度融合

### 业务价值
- 提高回答准确性从70%提升至95%
- 减少政策违规风险80%
- 提升用户体验和满意度
- 降低人工审核成本60%

## 🏗️ 架构设计

### 整体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    RAG增强工作流                              │
├─────────────────────────────────────────────────────────────┤
│  用户输入 → 意图分析 → RAG检索 → 任务规划 → 工具执行 → 结果输出    │
│              ↓         ↓         ↓                          │
│          知识增强   上下文注入   政策验证                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   RAG核心组件架构                             │
├─────────────────────────────────────────────────────────────┤
│  文档加载器 → 文本分割 → 向量化 → 向量数据库                   │
│      ↓                                ↓                     │
│  知识库管理 ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ 语义检索                   │
│      ↓                                ↓                     │
│  上下文增强 → 提示优化 → LLM调用 → 结果验证                   │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件
1. **知识库管理系统** (Knowledge Management)
2. **文档处理引擎** (Document Processing)
3. **向量检索系统** (Vector Retrieval)
4. **上下文增强器** (Context Augmentor)
5. **RAG集成节点** (RAG Integration Nodes)

## 📁 文件结构设计

```
src/
├── rag/                           # RAG核心模块
│   ├── __init__.py
│   ├── knowledge/                 # 知识管理
│   │   ├── __init__.py
│   │   ├── loader.py             # 文档加载器
│   │   ├── splitter.py           # 文本分割器
│   │   ├── embedder.py           # 向量化器
│   │   └── manager.py            # 知识库管理器
│   ├── retrieval/                # 检索系统
│   │   ├── __init__.py
│   │   ├── retriever.py          # 检索器
│   │   ├── reranker.py           # 重排序器
│   │   └── filters.py            # 过滤器
│   ├── enhancement/              # 增强系统
│   │   ├── __init__.py
│   │   ├── augmentor.py          # 上下文增强器
│   │   ├── validator.py          # 结果验证器
│   │   └── optimizer.py          # 提示优化器
│   └── integration/              # 集成组件
│       ├── __init__.py
│       ├── rag_node.py          # RAG节点
│       └── rag_tools.py         # RAG工具
├── nodes/                        # 现有节点（需要改造）
│   ├── intent_analysis.py       # 集成RAG的意图分析
│   ├── task_planning.py         # 集成RAG的任务规划
│   └── ...
├── data/                        # 数据目录（新增）
│   ├── knowledge_base/          # 知识库文档
│   │   ├── policies/           # 政策文档
│   │   ├── procedures/         # 流程文档
│   │   ├── faqs/              # 常见问题
│   │   └── templates/         # 模板文档
│   └── vector_store/           # 向量数据库
│       └── chroma_db/         # ChromaDB存储
└── config/
    └── rag_config.py           # RAG配置文件
```

## 🔧 技术实现细节

### 1. 依赖更新 (requirements.txt)

```python
# 现有依赖保持不变...

# RAG相关新增依赖
chromadb>=0.4.15              # 向量数据库
sentence-transformers>=2.2.2  # 句子嵌入
langchain-community>=0.0.13   # 文档加载器
pypdf>=3.17.0                 # PDF处理
python-docx>=1.1.0           # Word文档处理
openpyxl>=3.1.2              # Excel处理
markdown>=3.5.1              # Markdown处理
jieba>=0.42.1                # 中文分词
rank-bm25>=0.2.2             # BM25检索
faiss-cpu>=1.7.4             # FAISS向量检索（可选）
```

### 2. RAG配置文件 (src/config/rag_config.py)

```python
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class RAGConfig:
    """RAG系统配置"""
    
    # 向量数据库配置
    VECTOR_DB_TYPE: str = "chroma"  # chroma, faiss
    VECTOR_DB_PATH: str = "data/vector_store/chroma_db"
    COLLECTION_NAME: str = "expense_knowledge"
    
    # 嵌入模型配置
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # 文本分割配置
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # 检索配置
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    RERANK_TOP_K: int = 3
    
    # 知识库路径
    KNOWLEDGE_BASE_PATH: str = "data/knowledge_base"
    POLICIES_PATH: str = "data/knowledge_base/policies"
    PROCEDURES_PATH: str = "data/knowledge_base/procedures"
    FAQS_PATH: str = "data/knowledge_base/faqs"
    
    # 检索策略
    RETRIEVAL_STRATEGIES: Dict[str, Any] = {
        "semantic": {"weight": 0.7},  # 语义检索权重
        "keyword": {"weight": 0.3},   # 关键词检索权重
        "hybrid": True                # 是否启用混合检索
    }
    
    # 缓存配置
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 缓存过期时间(秒)

# 全局配置实例
rag_config = RAGConfig()
```

### 3. 知识库管理器 (src/rag/knowledge/manager.py)

```python
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings

from .loader import DocumentLoader
from .splitter import TextSplitter
from .embedder import EmbeddingService
from ...config.rag_config import rag_config

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self):
        """初始化知识库管理器"""
        self.config = rag_config
        self.client = None
        self.collection = None
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()
        self.embedder = EmbeddingService()
        
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """初始化向量数据库"""
        try:
            # 创建ChromaDB客户端
            persist_directory = Path(self.config.VECTOR_DB_PATH)
            persist_directory.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            try:
                self.collection = self.client.get_collection(
                    name=self.config.COLLECTION_NAME
                )
                logger.info(f"成功连接到现有集合: {self.config.COLLECTION_NAME}")
            except:
                self.collection = self.client.create_collection(
                    name=self.config.COLLECTION_NAME,
                    metadata={"description": "差旅报销知识库"}
                )
                logger.info(f"创建新集合: {self.config.COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {str(e)}")
            raise
    
    async def build_knowledge_base(self, force_rebuild: bool = False):
        """构建知识库"""
        logger.info("开始构建知识库...")
        
        if force_rebuild:
            await self._clear_knowledge_base()
        
        # 加载各类文档
        knowledge_paths = [
            (self.config.POLICIES_PATH, "policy"),
            (self.config.PROCEDURES_PATH, "procedure"), 
            (self.config.FAQS_PATH, "faq")
        ]
        
        total_chunks = 0
        for path, doc_type in knowledge_paths:
            if os.path.exists(path):
                chunks = await self._process_directory(path, doc_type)
                total_chunks += len(chunks)
                logger.info(f"处理 {doc_type} 文档: {len(chunks)} 个片段")
        
        logger.info(f"知识库构建完成，共 {total_chunks} 个文档片段")
        return total_chunks
    
    async def _process_directory(self, directory_path: str, doc_type: str) -> List[Dict[str, Any]]:
        """处理目录下的所有文档"""
        chunks = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.warning(f"目录不存在: {directory_path}")
            return chunks
        
        # 支持的文件类型
        supported_extensions = {'.md', '.txt', '.pdf', '.docx', '.xlsx'}
        
        for file_path in directory.rglob('*'):
            if file_path.suffix.lower() in supported_extensions:
                try:
                    # 加载文档
                    documents = await self.loader.load_document(str(file_path))
                    
                    for doc in documents:
                        # 分割文本
                        text_chunks = self.splitter.split_text(doc.content)
                        
                        # 生成向量并存储
                        for i, chunk in enumerate(text_chunks):
                            chunk_data = {
                                "id": f"{file_path.stem}_{i}",
                                "content": chunk,
                                "metadata": {
                                    "source": str(file_path),
                                    "doc_type": doc_type,
                                    "title": doc.metadata.get("title", file_path.stem),
                                    "chunk_index": i,
                                    "total_chunks": len(text_chunks)
                                }
                            }
                            chunks.append(chunk_data)
                            
                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {str(e)}")
                    continue
        
        # 批量存储到向量数据库
        if chunks:
            await self._store_chunks(chunks)
        
        return chunks
    
    async def _store_chunks(self, chunks: List[Dict[str, Any]]):
        """批量存储文档片段到向量数据库"""
        try:
            # 提取文本内容
            texts = [chunk["content"] for chunk in chunks]
            
            # 生成嵌入向量
            embeddings = await self.embedder.embed_texts(texts)
            
            # 准备存储数据
            ids = [chunk["id"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            
            # 存储到ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"成功存储 {len(chunks)} 个文档片段")
            
        except Exception as e:
            logger.error(f"存储文档片段失败: {str(e)}")
            raise
    
    async def _clear_knowledge_base(self):
        """清空知识库"""
        try:
            self.client.delete_collection(self.config.COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"description": "差旅报销知识库"}
            )
            logger.info("知识库已清空")
        except Exception as e:
            logger.error(f"清空知识库失败: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.config.COLLECTION_NAME,
                "embedding_model": self.config.EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
```

### 4. 检索器 (src/rag/retrieval/retriever.py)

```python
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from rank_bm25 import BM25Okapi
import jieba
import numpy as np

from ..knowledge.manager import KnowledgeManager
from ...config.rag_config import rag_config

logger = logging.getLogger(__name__)

class RetrievalResult:
    """检索结果数据类"""
    def __init__(self, content: str, metadata: Dict[str, Any], score: float):
        self.content = content
        self.metadata = metadata
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score
        }

class HybridRetriever:
    """混合检索器 - 结合语义检索和关键词检索"""
    
    def __init__(self, knowledge_manager: KnowledgeManager):
        self.knowledge_manager = knowledge_manager
        self.config = rag_config
        self.bm25_index = None
        self.bm25_docs = []
        self.bm25_metadata = []
        
        # 初始化BM25索引
        asyncio.create_task(self._build_bm25_index())
    
    async def _build_bm25_index(self):
        """构建BM25索引"""
        try:
            # 从向量数据库获取所有文档
            collection = self.knowledge_manager.collection
            results = collection.get()
            
            if not results['documents']:
                logger.warning("知识库为空，无法构建BM25索引")
                return
            
            # 分词处理
            tokenized_docs = []
            for doc in results['documents']:
                tokens = list(jieba.cut(doc))
                tokenized_docs.append(tokens)
            
            # 构建BM25索引
            self.bm25_index = BM25Okapi(tokenized_docs)
            self.bm25_docs = results['documents']
            self.bm25_metadata = results['metadatas']
            
            logger.info(f"BM25索引构建完成，包含 {len(tokenized_docs)} 个文档")
            
        except Exception as e:
            logger.error(f"构建BM25索引失败: {str(e)}")
    
    async def retrieve(self, query: str, top_k: int = None) -> List[RetrievalResult]:
        """混合检索"""
        if top_k is None:
            top_k = self.config.TOP_K
        
        # 并行执行语义检索和关键词检索
        semantic_results, keyword_results = await asyncio.gather(
            self._semantic_retrieve(query, top_k * 2),
            self._keyword_retrieve(query, top_k * 2)
        )
        
        # 融合结果
        fused_results = self._fuse_results(semantic_results, keyword_results)
        
        # 返回Top-K结果
        return fused_results[:top_k]
    
    async def _semantic_retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """语义检索"""
        try:
            collection = self.knowledge_manager.collection
            
            # 查询向量化
            query_embedding = await self.knowledge_manager.embedder.embed_texts([query])
            
            # 向量检索
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 转换为RetrievalResult
            retrieval_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                # 将距离转换为相似度分数
                similarity_score = 1 / (1 + distance)
                
                if similarity_score >= self.config.SIMILARITY_THRESHOLD:
                    retrieval_results.append(RetrievalResult(
                        content=doc,
                        metadata=metadata,
                        score=similarity_score
                    ))
            
            logger.debug(f"语义检索返回 {len(retrieval_results)} 个结果")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"语义检索失败: {str(e)}")
            return []
    
    async def _keyword_retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """关键词检索（BM25）"""
        try:
            if not self.bm25_index:
                logger.warning("BM25索引未构建，跳过关键词检索")
                return []
            
            # 查询分词
            query_tokens = list(jieba.cut(query))
            
            # BM25检索
            scores = self.bm25_index.get_scores(query_tokens)
            
            # 获取Top-K结果
            top_k_indices = np.argsort(scores)[::-1][:top_k]
            
            retrieval_results = []
            for idx in top_k_indices:
                if scores[idx] > 0:  # 只返回有得分的结果
                    retrieval_results.append(RetrievalResult(
                        content=self.bm25_docs[idx],
                        metadata=self.bm25_metadata[idx],
                        score=float(scores[idx])
                    ))
            
            logger.debug(f"关键词检索返回 {len(retrieval_results)} 个结果")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"关键词检索失败: {str(e)}")
            return []
    
    def _fuse_results(self, semantic_results: List[RetrievalResult], 
                     keyword_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """融合语义检索和关键词检索结果"""
        
        # 获取权重配置
        semantic_weight = self.config.RETRIEVAL_STRATEGIES["semantic"]["weight"]
        keyword_weight = self.config.RETRIEVAL_STRATEGIES["keyword"]["weight"]
        
        # 使用文档ID去重并融合分数
        fused_dict = {}
        
        # 处理语义检索结果
        for result in semantic_results:
            doc_id = result.metadata.get("source", "") + str(hash(result.content))
            fused_dict[doc_id] = {
                "result": result,
                "semantic_score": result.score,
                "keyword_score": 0.0
            }
        
        # 处理关键词检索结果
        for result in keyword_results:
            doc_id = result.metadata.get("source", "") + str(hash(result.content))
            if doc_id in fused_dict:
                fused_dict[doc_id]["keyword_score"] = result.score
            else:
                fused_dict[doc_id] = {
                    "result": result,
                    "semantic_score": 0.0,
                    "keyword_score": result.score
                }
        
        # 计算融合分数并排序
        fused_results = []
        for doc_id, data in fused_dict.items():
            # 计算加权分数
            final_score = (
                data["semantic_score"] * semantic_weight + 
                data["keyword_score"] * keyword_weight
            )
            
            # 更新结果分数
            result = data["result"]
            result.score = final_score
            fused_results.append(result)
        
        # 按分数降序排列
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"融合后返回 {len(fused_results)} 个结果")
        return fused_results
```

### 5. RAG集成节点 (src/rag/integration/rag_node.py)

```python
import logging
from typing import Dict, Any, List, Optional
import asyncio

from ...models.state import ExpenseState
from ..knowledge.manager import KnowledgeManager
from ..retrieval.retriever import HybridRetriever
from ..enhancement.augmentor import ContextAugmentor
from ...config.rag_config import rag_config

logger = logging.getLogger(__name__)

class RAGNode:
    """RAG节点 - 负责知识检索和上下文增强"""
    
    def __init__(self):
        self.config = rag_config
        self.knowledge_manager = KnowledgeManager()
        self.retriever = HybridRetriever(self.knowledge_manager)
        self.augmentor = ContextAugmentor()
        
    async def enhance_intent_analysis(self, state: ExpenseState) -> ExpenseState:
        """为意图分析提供知识增强"""
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                return state
            
            # 检索相关知识
            relevant_docs = await self.retriever.retrieve(user_input)
            
            # 构建知识上下文
            knowledge_context = self._build_knowledge_context(relevant_docs)
            
            # 增强状态
            enhanced_state = state.copy()
            enhanced_state["rag_context"] = {
                "knowledge_context": knowledge_context,
                "retrieved_docs": [doc.to_dict() for doc in relevant_docs],
                "retrieval_query": user_input
            }
            
            logger.info(f"为意图分析检索到 {len(relevant_docs)} 个相关文档")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"意图分析RAG增强失败: {str(e)}")
            return state
    
    async def enhance_task_planning(self, state: ExpenseState) -> ExpenseState:
        """为任务规划提供知识增强"""
        try:
            intent = state.get("intent", {})
            user_input = state.get("user_input", "")
            
            # 构建检索查询
            planning_query = self._build_planning_query(intent, user_input)
            
            # 检索流程和政策相关知识
            relevant_docs = await self.retriever.retrieve(planning_query)
            
            # 过滤出流程相关文档
            procedure_docs = [doc for doc in relevant_docs 
                            if doc.metadata.get("doc_type") == "procedure"]
            policy_docs = [doc for doc in relevant_docs 
                         if doc.metadata.get("doc_type") == "policy"]
            
            # 构建任务规划上下文
            planning_context = {
                "procedures": self._build_knowledge_context(procedure_docs),
                "policies": self._build_knowledge_context(policy_docs),
                "all_context": self._build_knowledge_context(relevant_docs)
            }
            
            # 更新状态
            enhanced_state = state.copy()
            if "rag_context" not in enhanced_state:
                enhanced_state["rag_context"] = {}
            
            enhanced_state["rag_context"]["planning_context"] = planning_context
            enhanced_state["rag_context"]["planning_docs"] = [doc.to_dict() for doc in relevant_docs]
            
            logger.info(f"为任务规划检索到 {len(relevant_docs)} 个相关文档")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"任务规划RAG增强失败: {str(e)}")
            return state
    
    def _build_knowledge_context(self, docs: List) -> str:
        """构建知识上下文字符串"""
        if not docs:
            return "暂无相关知识。"
        
        context_parts = []
        for i, doc in enumerate(docs[:self.config.RERANK_TOP_K], 1):
            source = doc.metadata.get("source", "未知来源")
            title = doc.metadata.get("title", "无标题")
            content = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
            
            context_parts.append(f"""
{i}. 【{title}】
来源: {source}
内容: {content}
相关度: {doc.score:.3f}
            """.strip())
        
        return "\n\n".join(context_parts)
    
    def _build_planning_query(self, intent: Dict[str, Any], user_input: str) -> str:
        """构建任务规划的检索查询"""
        intent_type = intent.get("主要意图", "")
        details = intent.get("细节", {})
        
        # 基础查询
        query_parts = [user_input, intent_type]
        
        # 添加细节信息
        for key, value in details.items():
            if isinstance(value, str) and value:
                query_parts.append(f"{key}:{value}")
        
        # 添加任务规划相关关键词
        query_parts.extend(["流程", "步骤", "规划", "要求"])
        
        return " ".join(query_parts)
```

## 🔄 现有节点改造

### 6. 增强版意图分析节点

需要修改 `src/nodes/intent_analysis.py`，在关键位置集成RAG功能：

```python
# 在 IntentAnalysisNode 类中添加RAG集成

from ..rag.integration.rag_node import RAGNode

class IntentAnalysisNode:
    def __init__(self, model_name: str = "qwen3-235b-a22b"):
        self.model_name = model_name
        self.rag_node = RAGNode()  # 新增RAG节点
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """处理用户输入，识别意图和工具调用"""
        
        # 1. RAG增强 - 获取相关知识上下文
        enhanced_state = await self.rag_node.enhance_intent_analysis(state)
        
        # 2. 构建增强的系统提示（包含知识上下文）
        system_prompt = self._build_enhanced_system_prompt(
            tools, 
            enhanced_state.get("rag_context", {}).get("knowledge_context", "")
        )
        
        # ... 其余逻辑保持不变
        
    def _build_enhanced_system_prompt(self, tools: List[Dict[str, Any]], knowledge_context: str) -> str:
        """构建包含RAG知识的增强系统提示"""
        
        tools_desc = ""
        if tools:
            tools_desc = "可用工具:\n"
            for i, tool in enumerate(tools, 1):
                tools_desc += f"{i}. {tool['name']}: {tool['description']}\n"
                tools_desc += f"   参数: {json.dumps(tool['parameters'], ensure_ascii=False)}\n\n"
        
        return f"""你是一个专业的差旅报销助手，负责理解用户的报销需求并提供帮助。

【相关知识和政策】:
{knowledge_context}

【可用工具列表】:
{tools_desc}

请基于上述知识和政策，分析用户输入，识别用户的意图和需要执行的操作。

如果用户请求需要使用工具，请生成工具调用。工具调用格式如下:
{{
  "id": "工具调用ID",
  "name": "工具名称", 
  "arguments": {{
    "参数1": "值1",
    "参数2": "值2"
  }}
}}

回复格式:
{{
  "intent": {{
    "主要意图": "用户的主要意图",
    "细节": {{
      "关键字段1": "值1",
      "关键字段2": "值2"
    }},
    "政策依据": "相关政策条款",
    "合规性检查": "是否符合政策要求"
  }},
  "tool_calls": [
    {{
      "id": "工具调用ID",
      "name": "工具名称",
      "arguments": {{
        "参数1": "值1",
        "参数2": "值2"
      }}
    }}
  ]
}}

如果不需要使用工具，则不要包含tool_calls字段。
请始终以JSON格式返回，确保格式正确。"""
```

### 7. 增强版任务规划节点

需要修改 `src/nodes/task_planning.py`：

```python
# 在 TaskPlanningNode 类中集成RAG

from ..rag.integration.rag_node import RAGNode

class TaskPlanningNode:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = ChatOpenAI(model_name=model_name, base_url=MODEL_BASE_URL, api_key=API_KEY)
        self.tool_registry = tool_registry
        self.rag_node = RAGNode()  # 新增RAG节点
        
        # 更新提示模板以包含RAG上下文
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销规划助手。

【业务流程说明】:
{business_process_prompt}

【相关政策知识】:
{rag_policies_context}

【流程指导】:
{rag_procedures_context}

【可用工具列表】:
{available_tools}

基于上述信息，请为用户生成详细的执行计划。

要求：
1. 严格遵循相关政策要求
2. 按照标准流程设计步骤
3. 为每个步骤分配适当的工具
4. 确保合规性和完整性

请以JSON格式输出，包含以下字段：
- steps: 执行步骤列表
- tools_needed: 每个步骤需要的工具
- dependencies: 步骤间的依赖关系
- compliance_notes: 合规性说明
- estimated_time: 预计完成时间
            """),
            ("user", "意图: {intent}\n上下文: {context}")
        ])
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行任务规划"""
        
        # 1. RAG增强 - 获取规划相关知识
        enhanced_state = await self.rag_node.enhance_task_planning(state)
        
        # 2. 提取RAG上下文
        rag_context = enhanced_state.get("rag_context", {})
        planning_context = rag_context.get("planning_context", {})
        
        # 3. 准备增强的输入
        tools_description = self._get_available_tools_description()
        
        inputs = {
            "intent": enhanced_state["intent"],
            "context": enhanced_state.get("context", {}),
            "business_process_prompt": business_process_prompt,
            "rag_policies_context": planning_context.get("policies", "暂无相关政策"),
            "rag_procedures_context": planning_context.get("procedures", "暂无相关流程指导"),
            "available_tools": tools_description
        }
        
        # ... 其余逻辑保持不变，但使用增强的输入
```

## 📊 性能优化与监控

### 8. 缓存机制 (src/rag/enhancement/cache.py)

```python
import hashlib
import json
import time
from typing import Any, Optional, Dict
import redis
from ...config.rag_config import rag_config

class RAGCache:
    """RAG结果缓存系统"""
    
    def __init__(self):
        self.config = rag_config
        self.redis_client = None
        
        if self.config.ENABLE_CACHE:
            try:
                self.redis_client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    decode_responses=True
                )
                self.redis_client.ping()
            except:
                self.redis_client = None  # 降级为内存缓存
                self.memory_cache = {}
    
    def _generate_cache_key(self, query: str, context: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        cache_data = {"query": query}
        if context:
            cache_data["context"] = context
        
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return f"rag:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def get(self, query: str, context: Dict[str, Any] = None) -> Optional[Any]:
        """获取缓存结果"""
        if not self.config.ENABLE_CACHE:
            return None
        
        cache_key = self._generate_cache_key(query, context)
        
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # 内存缓存
                cached_item = self.memory_cache.get(cache_key)
                if cached_item and time.time() - cached_item['timestamp'] < self.config.CACHE_TTL:
                    return cached_item['data']
        except Exception:
            pass
        
        return None
    
    def set(self, query: str, result: Any, context: Dict[str, Any] = None):
        """设置缓存结果"""
        if not self.config.ENABLE_CACHE:
            return
        
        cache_key = self._generate_cache_key(query, context)
        
        try:
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    self.config.CACHE_TTL, 
                    json.dumps(result, ensure_ascii=False)
                )
            else:
                # 内存缓存
                self.memory_cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                
                # 清理过期缓存
                current_time = time.time()
                expired_keys = [
                    k for k, v in self.memory_cache.items() 
                    if current_time - v['timestamp'] > self.config.CACHE_TTL
                ]
                for key in expired_keys:
                    del self.memory_cache[key]
                    
        except Exception:
            pass
```

## 🚀 部署与使用

### 9. 知识库初始化脚本 (scripts/init_knowledge_base.py)

```python
#!/usr/bin/env python3
"""知识库初始化脚本"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.rag.knowledge.manager import KnowledgeManager

async def main():
    """主函数"""
    print("开始初始化知识库...")
    
    # 创建知识库管理器
    manager = KnowledgeManager()
    
    # 构建知识库
    try:
        total_chunks = await manager.build_knowledge_base(force_rebuild=True)
        print(f"✅ 知识库初始化成功！共处理 {total_chunks} 个文档片段")
        
        # 显示统计信息
        stats = manager.get_collection_stats()
        print(f"📊 知识库统计信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ 知识库初始化失败: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### 10. 使用示例

```bash
# 1. 安装新依赖
pip install -r requirements.txt

# 2. 准备知识库文档
mkdir -p data/knowledge_base/{policies,procedures,faqs}

# 3. 放置文档到对应目录
# - 政策文档 -> data/knowledge_base/policies/
# - 流程文档 -> data/knowledge_base/procedures/  
# - 常见问题 -> data/knowledge_base/faqs/

# 4. 初始化知识库
python scripts/init_knowledge_base.py

# 5. 启动应用（RAG功能自动集成）
langgraph dev --port 2024
```

## 📈 效果评估

### 预期改进指标
- **回答准确性**: 70% → 95%
- **政策合规性**: 60% → 98%  
- **用户满意度**: 3.5/5 → 4.7/5
- **处理效率**: 提升40%

### 监控指标
- 检索响应时间 < 500ms
- 知识库覆盖率 > 90%
- 缓存命中率 > 60%
- 检索相关性 > 0.8

## 🎯 总结

此RAG实现方案提供了：

1. **完整的知识管理系统** - 支持多种文档格式的自动处理
2. **高效的混合检索** - 结合语义和关键词检索优势
3. **无缝的工作流集成** - 与现有LangGraph节点深度融合
4. **灵活的配置管理** - 支持个性化参数调优
5. **完善的缓存机制** - 提升系统性能和用户体验

通过此方案，差旅报销智能体将具备强大的知识推理能力，为用户提供更准确、更合规的服务体验。