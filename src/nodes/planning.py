from typing import Dict, Any, List, Optional
import json
import time
import re
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from ..states.state import State
from ..llm import get_llm
from ..tool.registry import tool_registry
from ..tool.registry import ToolGroup
from ..vector_store.chroma_store import ChromaStore
from ..config import CHROMA_COLLECTION_NAME


class PlanningNode:
    """任务规划节点，负责制定处理流程的计划"""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化任务规划节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        self.tool_registry = tool_registry
        
        # 初始化向量存储
        self.vector_store = ChromaStore()
        self.vector_store.create_collection(CHROMA_COLLECTION_NAME)
    
    def _get_planning_prompt(self) -> ChatPromptTemplate:
        """获取规划提示模板
        
        Returns:
            规划提示模板
        """
        return ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销规划助手。"""),
            ("user", """            
            【相关知识】:
            {knowledge}

            【用户历史记录】:
            {memory_record}    
            
            【可用工具列表】:
            {available_tools}
             
            【用户意图】: {intent}
             
             参考上述信息，针对用户的意图，生成详细的执行计划。
            
            要求：
            1. step_id 必须按照 "step_1", "step_2" 等格式递增
            2. step_name 必须是简短的步骤名称，例如："提交出差申请"、"上传火车票"等
            3. action 必须是对步骤执行动作的详细描述，例如："使用出差申请工具提交申请"、"使用上传工具上传火车票"等
            4. tool.name 必须是可用工具列表中的工具名称
            5. tool.parameters 必须包含该工具所需的所有参数，参数值必须符合工具要求
            6. 不要添加任何额外的字段或注释
            7. 确保JSON格式完全正确，包括所有引号和逗号
            8. 每个步骤必须包含完整的工具信息
            9. 严格按照以下JSON格式输出，不要添加任何额外的字段或注释：

            {{
                "plan": {{
                    "steps": [
                        {{
                            "step_id": "step_1",
                            "step_name": "步骤名称",
                            "action": "执行动作描述",
                            "tool": {{
                                "name": "工具名称",
                                "parameters": {{
                                    "参数名": "参数值"
                                }}
                            }}
                        }}
                    ]
                }}
            }}
            
            """)
        ])
    
    def _query_knowledge_base(self, query: str, n_results: int = 5) -> str:
        """查询向量知识库
        
        Args:
            query: 查询语句
            n_results: 返回结果数量
            
        Returns:
            知识库查询结果字符串
        """
        try:
            # 执行向量搜索
            search_results = self.vector_store.search(
                query_texts=[query],
                n_results=n_results,
                similarity_threshold=0.5,  # 设置相似度阈值
                use_llm_similarity=True   # 使用大模型进行相似性判断
            )
            
            # 格式化搜索结果
            knowledge_content = ""
            if search_results and search_results.get("documents"):
                documents = search_results["documents"][0]  # 第一个查询的结果
                metadatas = search_results.get("metadatas", [[]])[0]
                
                for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                    filename = metadata.get("filename", f"文档{i+1}")
                    summary = metadata.get("summary", "")
                    
                    knowledge_content += f"\n--- 知识来源: {filename} ---\n"
                    if summary:
                        knowledge_content += f"摘要: {summary}\n"
                    knowledge_content += f"内容: {doc[:1000]}...\n"  # 限制内容长度
                    knowledge_content += "---\n"
            
            if not knowledge_content.strip():
                knowledge_content = "未找到相关的知识库信息。"
                
            return knowledge_content
            
        except Exception as e:
            print(f"向量知识库查询失败: {e}")
            return "知识库查询失败，将使用默认知识。"
    
    def extract_json_from_response(self, text: str) -> str:
        """从响应中提取JSON部分
        
        Args:
            text: 响应文本
            
        Returns:
            提取的JSON字符串
        """
        # 尝试找到JSON块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, text)
        
        if json_match:
            # 找到了JSON块
            return json_match.group(1).strip()
        
        # 如果没有找到JSON块，尝试直接解析为JSON
        # 移除<think>标签块
        text = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()
        
        # 尝试找到完整的JSON对象
        try:
            # 查找可能的JSON开始位置
            start_pos = text.find('{')
            if start_pos >= 0:
                # 尝试逐字符解析，找到有效的JSON
                for end_pos in range(len(text), start_pos, -1):
                    try:
                        json_candidate = text[start_pos:end_pos]
                        # 尝试解析
                        json.loads(json_candidate)
                        # 如果成功解析，返回这个JSON字符串
                        return json_candidate
                    except json.JSONDecodeError:
                        # 解析失败，继续尝试
                        continue
        except Exception:
            # 发生其他异常，忽略并继续
            pass
            
        # 如果上述方法都失败，使用正则表达式查找JSON对象
        # 这个更宽松的模式可能会找到不完整的JSON
        json_pattern = r'({[\s\S]*?})'
        json_match = re.search(json_pattern, text)
        
        if json_match:
            return json_match.group(1).strip()
            
        # 最后尝试查找任何花括号包围的内容
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < end:
                return text[start:end]
        
        # 如果都失败了，返回一个有效的空JSON对象
        return '{}'
    
    def _get_available_tools_description(self) -> str:
        """获取可用工具的描述
        
        Returns:
            工具描述字符串
        """
        # 获取所有工具模式
        tool_schemas = self.tool_registry.get_schemas_by_group(ToolGroup.BUSINESS_TRIP)
        
        # 格式化工具描述
        tools_description = ""
        for idx, tool in enumerate(tool_schemas):
            tool_desc = f"{idx+1}. {tool['name']}\n"
            tool_desc += f"   描述: {tool['description']}\n"
            tool_desc += f"   参数: {json.dumps(tool['parameters']['properties'], ensure_ascii=False, indent=2)}\n"
            tools_description += tool_desc + "\n"
        
        return tools_description
    
    async def __call__(self, state: State) -> State:
        """执行任务规划
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            print("--------------------------------------------------------------------------------planning node start----------------------------------------------------------")
            
            # 将用户意图转换为查询语句
            query = self._convert_intent_to_query(state["intent"])

            # 查询向量知识库
            knowledge_content = self._query_knowledge_base(query)
            
            # 获取可用工具描述
            tools_description = self._get_available_tools_description()
            
            # 获取规划提示模板
            prompt = self._get_planning_prompt()
            
            # 准备输入
            inputs = {
                "intent": state["intent"],
                "knowledge": knowledge_content,  # 使用向量知识库查询结果
                "memory_record": state.get("memory_records", "无历史记录"),
                "available_tools": tools_description
            }
            
            # 执行规划
            print(f"【PROMPT】:\n{prompt.format_messages(**inputs)}")
            response = self.llm.invoke(prompt.format_messages(**inputs))
            response_text = response.content

            print(f"【RESPONSE】:\n{response_text}")
            
            # 提取并解析 JSON
            json_str = self.extract_json_from_response(response_text)
            
            # 解析JSON
            try:
                planning_result = json.loads(json_str)
            except json.JSONDecodeError:
                # 如果解析失败，创建默认结果
                planning_result = {
                    "plan": {
                        "steps": []
                    }
                }
            
            # 更新计划
            state["plan"] = planning_result.get("plan", {}).get("steps", [])
            
            # 确保每个步骤都包含必要的信息
            for i, step in enumerate(state["plan"]):
                if not isinstance(step, dict):
                    continue
                    
                # 确保步骤有唯一ID
                if "step_id" not in step:
                    step["step_id"] = f"step_{i+1}"
                
                # 确保步骤名称存在
                if "step_name" not in step:
                    step["step_name"] = f"步骤{i+1}"
                
                # 确保执行动作描述存在
                if "action" not in step:
                    step["action"] = f"执行步骤{i+1}"
                
                # 确保工具信息格式正确
                if "tool" not in step:
                    step["tool"] = {
                        "name": "",
                        "parameters": {}
                    }
                elif isinstance(step["tool"], dict):
                    if "name" not in step["tool"]:
                        step["tool"]["name"] = ""
                    if "parameters" not in step["tool"]:
                        step["tool"]["parameters"] = {}
            
            # 保存规划结果到状态
            state["planning_result"] = planning_result
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"----task planning llm error: {e}")
            # 出错时设置空计划
            state["plan"] = []
            return state 

    def _convert_intent_to_query(self, intent: str) -> str:
        """将用户意图转换为查询语句
        
        Args:
            intent: 用户意图
            
        Returns:
            查询语句
        """
        try:
            if isinstance(intent, dict):
                intent = json.dumps(intent, ensure_ascii=False, indent=2)
            else:
                intent = str(intent)
                
            # 创建意图转换查询的提示模板
            intent_to_query_prompt = """你是一个专业的差旅报销查询助手。你的任务是将用户的意图转换为适合进行知识库查询的语句。
请根据用户的意图，生成一个查询语句，用于在差旅报销相关的知识库中搜索相关信息。

要求：
1. 查询语句应该包含关键信息，有利于更详细的信息查询
2. 查询语句应该涵盖用户意图的核心内容
3. 如果用户意图涉及具体流程或政策，查询语句应该包含相关关键词
4. 返回格式：直接返回查询语句，不要添加任何额外的格式或说明

用户意图: {intent}"""
            
            # 准备输入
            inputs = {
                "intent": intent
            }
            print(f"【PROMPT】:\n{intent_to_query_prompt.format(**inputs)}")
            
            # 执行转换
            response = self.llm.invoke(intent_to_query_prompt.format(**inputs))
            response_text = response.content.strip()
            
            # 只输出</think>后面的内容
            query = response_text.split('</think>')[1].strip()
            print(f"【RESPONSE】:\n{query}")
            return query
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"----intent to query conversion error: {e}")
            # 出错时返回原始意图作为查询
            return intent