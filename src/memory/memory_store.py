from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime
import os
from enum import Enum
from langchain.prompts import PromptTemplate
import sys
from pathlib import Path
import uuid  # 添加uuid导入
import re

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent.parent)
print(project_root)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config import get_llm
from src.utils.json_utils import extract_json_from_response

class MemoryType(Enum):
    """记忆类型枚举"""
    FACT = "fact"           # 事实性记忆
    EXPERIENCE = "experience"  # 经验性记忆
    PREFERENCE = "preference"  # 偏好性记忆
    EMOTION = "emotion"     # 情感性记忆
    TASK = "task"          # 任务相关记忆
    CONVERSATION = "conversation"  # 对话记忆
    OTHER = "other"        # 其他类型

class MemoryUnit:
    """记忆单元类"""
    def __init__(
        self,
        id: str,
        name: str,
        content: Any,
        memory_type: Union[str, MemoryType],
        create_time: Optional[str] = None,
        meta_data: Optional[Dict] = None
    ):
        """
        初始化记忆单元
        
        Args:
            id: 记忆ID
            name: 记忆名称
            content: 记忆内容
            memory_type: 记忆类型
            create_time: 创建时间（ISO格式字符串）
            meta_data: 元数据
        """
        self.id = id
        self.name = name
        self.content = content
        self.memory_type = MemoryType(memory_type) if isinstance(memory_type, str) else memory_type
        self.create_time = create_time or datetime.now().isoformat()
        self.meta_data = meta_data or {}
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "type": self.memory_type.value,
            "create_time": self.create_time,
            "meta_data": self.meta_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryUnit':
        """从字典创建记忆单元"""
        return cls(
            id=data["id"],
            name=data["name"],
            content=data["content"],
            memory_type=data["type"],
            create_time=data["create_time"],
            meta_data=data["meta_data"]
        )

class MemoryStore:
    def __init__(self, storage_path: str = "memory_data"):
        """
        初始化记忆存储
        
        Args:
            storage_path: 存储文件的路径
        """
        self.storage_path = storage_path
        self.memories: List[MemoryUnit] = []
        self._ensure_storage_dir()
        self._load_memories()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def _load_memories(self):
        """从文件加载记忆"""
        memory_file = os.path.join(self.storage_path, "memories.json")
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                memories_data = json.load(f)
                self.memories = [MemoryUnit.from_dict(memory_data) for memory_data in memories_data]
    
    def _save_memories(self):
        """保存记忆到文件"""
        memory_file = os.path.join(self.storage_path, "memories.json")
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(
                [memory.to_dict() for memory in self.memories],
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def add_memory(
        self,
        name: str,
        content: Any,
        memory_type: Union[str, MemoryType],
        meta_data: Optional[Dict] = None
    ) -> str:
        """
        添加新的记忆
        
        Args:
            name: 记忆名称
            content: 记忆内容
            memory_type: 记忆类型
            meta_data: 元数据
            
        Returns:
            str: 记忆ID
        """
        memory_id = str(uuid.uuid4())  # 使用UUID4生成唯一ID
        memory = MemoryUnit(
            id=memory_id,
            name=name,
            content=content,
            memory_type=memory_type,
            meta_data=meta_data
        )
        self.memories.append(memory)
        self._save_memories()
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryUnit]:
        """
        获取指定记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[MemoryUnit]: 记忆单元，如果不存在则返回None
        """
        for memory in self.memories:
            if memory.id == memory_id:
                return memory
        return None
    
    def update_memory(
        self,
        memory_id: str,
        name: Optional[str] = None,
        content: Optional[Any] = None,
        memory_type: Optional[Union[str, MemoryType]] = None,
        meta_data: Optional[Dict] = None
    ) -> bool:
        """
        更新现有记忆
        
        Args:
            memory_id: 记忆ID
            name: 新的记忆名称
            content: 新的记忆内容
            memory_type: 新的记忆类型
            meta_data: 新的元数据
            
        Returns:
            bool: 是否成功更新
        """
        for memory in self.memories:
            if memory.id == memory_id:
                if name is not None:
                    memory.name = name
                if content is not None:
                    memory.content = content
                if memory_type is not None:
                    memory.memory_type = MemoryType(memory_type) if isinstance(memory_type, str) else memory_type
                if meta_data is not None:
                    memory.meta_data.update(meta_data)
                self._save_memories()
                return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功删除
        """
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                del self.memories[i]
                self._save_memories()
                return True
        return False
    
    def search_by_type(self, memory_type: Union[str, MemoryType]) -> List[MemoryUnit]:
        """
        按类型搜索记忆
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            List[MemoryUnit]: 指定类型的记忆列表
        """
        type_value = memory_type.value if isinstance(memory_type, MemoryType) else memory_type
        return [memory for memory in self.memories if memory.memory_type.value == type_value]
    
    def search_by_content(self, query: str, case_sensitive: bool = False) -> List[MemoryUnit]:
        """
        按内容搜索记忆
        
        Args:
            query: 搜索查询
            case_sensitive: 是否区分大小写
            
        Returns:
            List[MemoryUnit]: 匹配的记忆列表
        """
        results = []
        if not case_sensitive:
            query = query.lower()
        
        for memory in self.memories:
            content = str(memory.content)
            if not case_sensitive:
                content = content.lower()
            if query in content:
                results.append(memory)
        
        return results
    
    def search_by_metadata(self, metadata_filter: Dict) -> List[MemoryUnit]:
        """
        按元数据过滤记忆
        
        Args:
            metadata_filter: 元数据过滤条件
            
        Returns:
            List[MemoryUnit]: 匹配的记忆列表
        """
        return [
            memory for memory in self.memories
            if all(
                memory.meta_data.get(key) == value
                for key, value in metadata_filter.items()
            )
        ]
    
    def search_by_time_range(self, start_time: str, end_time: str) -> List[MemoryUnit]:
        """
        按时间范围搜索记忆
        
        Args:
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）
            
        Returns:
            List[MemoryUnit]: 时间范围内的记忆列表
        """
        return [
            memory for memory in self.memories
            if start_time <= memory.create_time <= end_time
        ]
    
    def get_latest_memories(self, count: int) -> List[MemoryUnit]:
        """
        获取最新的记忆
        
        Args:
            count: 要获取的记忆数量
            
        Returns:
            List[MemoryUnit]: 最新的记忆列表
        """
        sorted_memories = sorted(
            self.memories,
            key=lambda x: x.create_time,
            reverse=True
        )
        return sorted_memories[:count]
    
    def get_earliest_memories(self, count: int) -> List[MemoryUnit]:
        """
        获取最早的记忆
        
        Args:
            count: 要获取的记忆数量
            
        Returns:
            List[MemoryUnit]: 最早的记忆列表
        """
        sorted_memories = sorted(
            self.memories,
            key=lambda x: x.create_time
        )
        return sorted_memories[:count]

    def _parse_llm_response(self, response: str) -> str:
        """
        解析大模型返回的内容，去掉think标签的内容，只返回最终结果
        
        Args:
            response: 大模型返回的原始响应内容
            
        Returns:
            str: 处理后的结果内容
        """
        if "<think>" in response and "</think>" in response:
            # 提取think标签后的内容
            return response.split("</think>")[-1].strip()
        return response.strip()

    def add_memory_by_llm(self, memory_desc: str) -> str:
        """
        使用大模型解析记忆描述并创建记忆单元
        
        Args:
            memory_desc: 记忆描述文本
            
        Returns:
            str: 新创建的记忆ID
        """
        # 获取LLM实例
        llm = get_llm()
        
        # 构建提示模板
        prompt_template = PromptTemplate(
            input_variables=["memory_desc"],
            template="""
请分析以下记忆描述，并将其解析为结构化的记忆单元。需要提取以下信息：
1. 记忆名称（name）：简洁的标题
2. 记忆内容（content）：详细内容
3. 记忆类型（type）：必须是以下类型之一：fact（事实）, experience（经验）, preference（偏好）, emotion（情感）, task（任务）, conversation（对话）, other（其他）
4. 元数据（meta_data）：相关的额外信息，如时间、地点、人物等

记忆描述：
{memory_desc}

请以JSON格式返回解析结果，格式如下：
{{
    "name": "记忆名称",
    "content": "记忆内容",
    "type": "记忆类型",
    "meta_data": {{
        "key1": "value1",
        "key2": "value2"
    }}
}}

只返回JSON格式的结果，不要其他内容。
"""
        )
        
        # 构建完整提示
        prompt = prompt_template.format(memory_desc=memory_desc)
        
        # 调用LLM
        response = llm.invoke(prompt)
        
        try:
            # 解析响应内容
            content = extract_json_from_response(response.content)
            # 解析JSON
            memory_data = json.loads(content)
            
            # 创建记忆单元
            return self.add_memory(
                name=memory_data["name"],
                content=memory_data["content"],
                memory_type=memory_data["type"],
                meta_data=memory_data.get("meta_data", {})
            )
        except Exception as e:
            print(f"解析LLM响应时出错: {e}")
            raise ValueError(f"无法解析记忆描述: {e}")

    def search_by_llm(
        self,
        query: str,
        top_k: int = 5,
        memory_limit: int = 10
    ) -> List[MemoryUnit]:
        """
        使用大语言模型进行语义搜索
        
        Args:
            query: 搜索查询
            top_k: 返回最相关的k条记忆
            memory_limit: 发送给LLM的最大记忆数量
            
        Returns:
            List[MemoryUnit]: 语义相关的记忆列表
        """
        # 获取最近的记忆
        recent_memories = self.get_latest_memories(memory_limit)
        
        # 获取LLM实例
        llm = get_llm()
        
        # 构建提示模板
        prompt_template = PromptTemplate(
            input_variables=["query", "memories"],
            template="""
请分析以下查询和记忆列表，找出与查询语义最相关的记忆。

查询: {query}

记忆列表:
{memories}

请返回最相关的{top_k}条记忆的ID，用逗号分隔。只返回ID，不要其他内容。
"""
        )
        
        # 格式化记忆列表
        memories_text = json.dumps(
                [memory.to_dict() for memory in recent_memories],
                ensure_ascii=False,
                indent=2
            )
        
        # 构建完整提示
        prompt = prompt_template.format(
            query=query,
            memories=memories_text,
            top_k=top_k
        )
        
        print("search by llm prompt: ", prompt)
        # 调用LLM
        response = llm.invoke(prompt)

        print("search by llm response: ", response.content)
        
        # 解析响应，获取相关记忆的ID
        try:
            # 解析响应内容
            content = self._parse_llm_response(response.content)
            # 获取ID列表
            relevant_ids = [id.strip() for id in content.split(",")]
            # 获取对应的记忆
            relevant_memories = [
                memory for memory in recent_memories
                if memory.id in relevant_ids
            ]
            return relevant_memories
        except Exception as e:
            print(f"解析LLM响应时出错: {e}")
            return [] 