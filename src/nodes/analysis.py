from typing import Dict, Any, List, Optional, cast, Literal, Tuple
import json
import re
import uuid
import time
from datetime import datetime
import json


from ..states.state import State
from ..llm import get_llm
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
        self.memory_store = MemoryStore()
    
    def _get_user_related_memories(self, user_input: str, state: State) -> None:
        """获取用户记忆并保存到state中
        
        Args:
            user_input: 用户输入
            state: 当前状态
        """
        try:    
            relevant_memories = self.memory_store.get_latest_memories(count=10)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"获取用户记忆失败: {str(e)}")
            relevant_memories = []
            
        memory_list = []
        if relevant_memories:
            memory_list = [memory.to_dict() for memory in relevant_memories]
        # 将memory_list转换为json字符串
        # print(f"----intent analysis memory_list: {json.dumps(memory_list, ensure_ascii=False, indent=2)}")
        state["memory_records"] = memory_list

    def _add_user_intent_memories(self, intent:str, state: State) -> None:
        """添加用户意图记忆到state
        
        Args:
            intent: 用户意图
            state: 当前状态
        """

        try:
            if "memory_records" not in state:
                state["memory_records"] = []
            
            # 将意图转换为字符串描述
            if isinstance(intent, str):
                memory_desc = intent
            elif isinstance(intent, dict):
                memory_desc = json.dumps(intent, ensure_ascii=False, indent=2)
            else:
                memory_desc = str(intent)
            
            # 调用 add_memory_by_llm 方法，传入记忆描述
            memory = self.memory_store.add_memory_by_llm(memory_desc)
            
            # 获取记忆对象
            if memory:
                state["memory_records"].append(memory.to_dict())
            else:
                print(f"无法获取记忆对象: {memory.to_dict()}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"添加用户意图记忆失败: {str(e)}")

    def _add_user_message(self, state: State, content: str, action: str = "") -> None:
        """添加用户消息到对话历史
        
        Args:
            state: 当前状态
            content: 用户输入内容
            action: 用户执行的动作
        """
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append({
            "role": "user",
            "content": content,
            "action": action
        })

    def _add_assistant_message(self, state: State, content: str = "", action: str = "") -> None:
        """添加助手消息到对话历史
        
        Args:
            state: 当前状态
            content: 助手回复内容
            action: 助手执行的动作
        """
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append({
            "role": "assistant",
            "content": content,
            "action": action
        })

    def __call__(self, state: State) -> State:
        """处理用户输入，识别意图
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            print("--------------------------------------------------------------------------------analysis node start----------------------------------------------------------")
            # 获取用户输入
            user_input = state.get("user_input", "")
            if not user_input:
                return state.copy()

            # 设置created_at时间戳（如果不存在）
            if "created_at" not in state:
                state["created_at"] = datetime.now()

            # 将用户输入添加到messages中
            self._add_user_message(state, user_input)
            self._add_assistant_message(state)

            # 获取用户记忆
            self._get_user_related_memories(user_input, state)

            # 构建系统提示
            system_prompt = self._build_system_prompt(user_input)
            
            # 构建用户提示
            user_prompt = self._build_user_prompt(user_input, state)
            
            # 调用LLM获取回复
            response = self._call_llm(system_prompt, user_prompt)
            
            # 解析意图
            intent = self._parse_response(response)

            #print(f"----intent analysis intent: {json.dumps(intent, ensure_ascii=False, indent=2)}")
            
            self._add_user_intent_memories(intent, state)
            state["intent"] = intent
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
            
            return state
            
        except Exception as e:
            return state.copy()
    
    def _build_system_prompt(self, user_input: str) -> str:
        """构建系统提示
        
        Args:
            user_input: 用户输入
            
        Returns:
            系统提示
        """
        system_prompt = """你是一个人工智能助手，负责理解用户的需求,识别用户的意图。"""
        return system_prompt
    
    def _build_user_prompt(self, user_input: str, state: State) -> str:
        """构建用户提示
        
        Args:
            user_input: 用户输入
            
        Returns:
            用户提示
        """
        memory_records = state.get("memory_records", [])
        if memory_records:
            memory_records_str = json.dumps(memory_records, ensure_ascii=False, indent=2)
        else:
            memory_records_str = "无记忆记录"
        
        messages = state.get("messages", [])
        if messages:
            messages_str = json.dumps(messages, ensure_ascii=False, indent=2)
        else:
            messages_str = "无对话记录"
        
        # 获取用户信息
        user_info = state.get("user_info", {})
        user_info_str = ""
        if user_info:
            user_info_lines = []
            for key, value in user_info.items():
                user_info_lines.append(f"{key}：{value}")
            user_info_str = "\n".join(user_info_lines)
        else:
            user_info_str = "用户信息未设置"
        
        return f"""
【用户基本信息】:
{user_info_str}

【用户记忆记录】:
{memory_records_str}

【用户对话记录】:
{messages_str}

用户输入:
{user_input}

请分析上述输入，识别用户意图，并按照以下JSON格式返回:
{{
  "intent": {{
    "主要意图": "用户的主要意图",
    "细节": {{
      "关键字段1": "值1",
      "关键字段2": "值2"
    }}
  }}
}}
要求：
1. 返回的结果必须符合JSON格式
2. 细节中的关键字段和值尽量详细
"""
    
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
            import traceback
            traceback.print_exc()
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
            import traceback
            traceback.print_exc()   
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
                {'role':'user','content':user_prompt}
            ]
            print(f"【PROMPT】:\n{json.dumps(messages, ensure_ascii=False, indent=2)}")
            # 调用LLM
            response = llm.invoke(messages)
            response_text=response.content
            print(f"【RESPONSE】:\n{response_text}")
            json_str=extract_json_from_response(response_text)

            try:
                intent_result = json.loads(json_str)
            except json.JSONDecodeError as e:
                import traceback
                traceback.print_exc()
                print(f"解析JSON失败: {str(e)}")
                intent_result = self._create_fallback_intent(user_prompt)
            return intent_result    
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"调用LLM失败: {str(e)}")
            # 如果调用失败，返回用户输入作为意图
            intent_result = self._create_fallback_intent(user_prompt)
            return intent_result