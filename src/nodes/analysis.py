from typing import Dict, Any, List, Optional, cast, Literal
import json
import re
import uuid
import time
from datetime import datetime

from ..states.state import State
from ..config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from ..memory.memory_store import MemoryStore
from ..utils.json_utils import extract_json_from_response

class AnalysisNode:
    """意图分析节点，负责分析用户输入并识别意图"""
    
    def __init__(self, model_name: str = "qwen3-235b-a22b"):
        """初始化意图分析节点
        
        Args:
            model_name: 使用的大语言模型名称
        """
        self.model_name = model_name
        self.memory_store = MemoryStore("memory_data")
    
    def __call__(self, state: State) -> State:
        """处理用户输入，识别意图
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 获取用户输入
            user_input = state.get("user_input", "")
            print(f'----user_input: {user_input}')
            if not user_input:
                return state.copy()
            print(f'----state: {state}')

            # 构建系统提示
            system_prompt = self._build_system_prompt(user_input)
            
            # 构建用户提示
            user_prompt = self._build_user_prompt(user_input)
            
            # 调用LLM获取回复
            response = self._call_llm(system_prompt, user_prompt)
            
            # 解析意图
            intent = self._parse_response(response)
            
            # 更新状态
            updated_state = state.copy()
            updated_state["intent"] = intent
            
            # 更新时间戳
            updated_state["updated_at"] = datetime.now()
            
            return updated_state
            
        except Exception as e:
            return state.copy()
    
    def _build_system_prompt(self, user_input: str) -> str:
        """构建系统提示
        
        Args:
            user_input: 用户输入
            
        Returns:
            系统提示
        """
        # 使用search_by_llm获取相关记忆
        relevant_memories = self.memory_store.search_by_llm(user_input, top_k=3)
        
        # 格式化记忆信息
        memory_info = "[]"
        if relevant_memories:
            memory_list = [memory.to_dict() for memory in relevant_memories]
            memory_info = json.dumps(memory_list, ensure_ascii=False, indent=2)
        print(f'----memory_info: {memory_info}')
        system_prompt= f"""
你是一个差旅报销助手，负责理解用户的需求并提供帮助。请分析用户输入和用户记忆信息，识别用户的意图。

用户记忆信息:
{memory_info}

请始终以JSON格式返回，确保格式正确,回复格式:
{{
  "intent": {{
    "主要意图": "用户的主要意图",
    "细节": {{
      "关键字段1": "值1",
      "关键字段2": "值2"
    }}
  }}
}}
"""
        print(f'analysis build system prompt: {system_prompt}')
        return system_prompt
    
    def _build_user_prompt(self, user_input: str) -> str:
        """构建用户提示
        
        Args:
            user_input: 用户输入
            
        Returns:
            用户提示
        """
        return f"""
用户输入:
{user_input}

请分析上述输入，识别用户意图，并按照指定格式返回。"""
    
    def _create_fallback_intent(self, user_prompt: str) -> Dict[str, Any]:
        """创建回退意图，当LLM调用或解析失败时使用
        
        Args:
            user_prompt: 用户提示
            
        Returns:
            回退意图结果
        """
        try:
            # 安全地提取用户输入
            if "用户输入:" in user_prompt:
                # 找到用户输入部分
                lines = user_prompt.split("\n")
                user_input_line = ""
                for i, line in enumerate(lines):
                    if "用户输入:" in line and i + 1 < len(lines):
                        user_input_line = lines[i + 1].strip()
                        break
                
                if user_input_line:
                    return {
                        "intent": {
                            "主要意图": user_input_line,
                            "细节": {"原始输入": user_input_line}
                        }
                    }
            
            # 如果无法提取，返回通用错误意图
            return {
                "intent": {
                    "主要意图": "处理用户请求",
                    "细节": {"错误": "无法解析用户输入"}
                }
            }
            
        except Exception as e:
            print(f"创建回退意图失败: {str(e)}")
            return {
                "intent": {
                    "主要意图": "未知请求",
                    "细节": {"错误": "解析失败"}
                }
            }
    
    def _parse_response(self, response: Dict[str, Any]) -> Any:
        """解析LLM响应，提取意图
        
        Args:
            response: LLM响应结果
            
        Returns:
            意图
        """
        try:
            if isinstance(response, dict):
                intent = response.get("intent", "")
                return intent
            else:
                # 如果响应不是字典，返回原始响应作为意图
                return response
                
        except Exception as e:
            print(f"解析响应失败: {str(e)}")
            return response
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用大语言模型
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            
        Returns:
            模型响应
        """
        try:
            # 获取配置的LLM实例
            llm = get_llm()
            
            # 构建消息
            messages=[
                {'role':'system','content':system_prompt},
                {'role':'user','content':user_prompt+'/no_think'}
            ]
            
            # 调用LLM
            response = llm.invoke(messages)
            response_text=response.content
            print(f"----intent analysis llm response: {response_text}")
            json_str=extract_json_from_response(response_text)

            import json
            try:
                intent_result = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"解析JSON失败: {str(e)}")
                intent_result = self._create_fallback_intent(user_prompt)
            return intent_result    
            
        except Exception as e:
            print(f"调用LLM失败: {str(e)}")
            # 如果调用失败，返回用户输入作为意图
            intent_result = self._create_fallback_intent(user_prompt)
            return intent_result