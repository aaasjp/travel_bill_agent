from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from ..states.state import State
from ..llm import get_llm
import json
from datetime import datetime
import time


class ConversationNode:
    """对话节点，用于处理当规划节点的plan为空时的情况"""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化对话节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
    
    def _get_conversation_messages(self, state: State) -> List[Dict[str, str]]:
        """获取对话消息列表，使用role、content格式
        
        Args:
            state: 当前状态
            
        Returns:
            消息列表
        """
        user_input = state.get("user_input", "")
        intent = state.get("intent", "")
        
        # 直接从state中获取用户记忆
        memory_text = json.dumps(state.get("memory_records", []), ensure_ascii=False, indent=2)
        
        # 直接从state中获取知识库内容
        knowledge_text = state.get("knowledge_content", "无知识库内容")
        
        # 构建系统消息
        system_content = f"""你是一个专业的助手。当用户的请求无法生成具体的执行计划时，你需要与用户进行对话，帮助澄清需求或提供相关信息。

你的职责：
1. 理解用户的需求
2. 提供相关的政策信息
3. 引导用户提供更具体的信息
4. 解答用户的疑问
5. 提供友好的对话体验

【用户记忆】
{memory_text}

【知识库内容】
{knowledge_text}

【用户意图】
{intent}

根据用户的需求、历史记忆和知识库内容，提供相应的回复。如果用户的需求不够明确，请引导用户提供更多信息。"""
        
        messages = state.get("messages",[])
        formatted_messages = []
        formatted_messages.append({"role": "system", "content": system_content})
        for msg in messages[:-1]:
            if msg["role"] == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        formatted_messages.append({"role": "user", "content": user_input})
        return formatted_messages
        
    
    async def __call__(self, state: State) -> State:
        """执行对话处理
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            print("--------------------------------------------------------------------------------conversation node start----------------------------------------------------------")
            
            # 设置created_at时间戳（如果不存在）
            if "created_at" not in state:
                state["created_at"] = datetime.now()
            
            # 获取对话消息
            messages = self._get_conversation_messages(state)
            
            # 执行对话
            print(f"【PROMPT】:\n{messages}")
            response = self.llm.invoke(messages)
            response_text = response.content

            print(f"【RESPONSE】:\n{response_text}")
            
            # 更新状态
            state["conversation_response"] = response_text
            state["status"] = "conversation_completed"
            state["final_output"] = response_text
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"----conversation node error: {e}")
            
            # 记录错误到状态中
            if "errors" not in state:
                state["errors"] = []
            
            state["errors"].append({
                "node": "conversation",
                "error": str(e),
                "error_type": "conversation_error",
                "timestamp": str(time.time())
            })
            
            # 出错时设置默认回复
            state["conversation_response"] = "抱歉，我遇到了一些技术问题。请稍后再试或联系技术支持。"
            state["status"] = "conversation_error"
            state["final_output"] = state["conversation_response"]
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
            
            return state 