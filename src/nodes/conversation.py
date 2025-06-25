from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..states.state import State
from ..llm import get_llm


class ConversationNode:
    """对话节点，用于处理当规划节点的plan为空时的情况"""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化对话节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
    
    def _get_memories_from_state(self, state: State) -> List[Dict[str, Any]]:
        """从state中获取用户记忆
        
        Args:
            state: 当前状态
            
        Returns:
            记忆列表
        """
        return state.get("memory_records", [])
    
    def _get_knowledge_from_state(self, state: State) -> List[Dict[str, Any]]:
        """从state中获取知识库内容
        
        Args:
            state: 当前状态
            
        Returns:
            知识内容列表
        """
        # 从state中获取知识库搜索结果
        knowledge_results = state.get("knowledge_search_results", {})
        
        knowledge_list = []
        if knowledge_results:
            documents = knowledge_results.get("documents", [[]])
            metadatas = knowledge_results.get("metadatas", [[]])
            distances = knowledge_results.get("distances", [[]])
            
            if documents and documents[0]:
                for i, doc in enumerate(documents[0]):
                    metadata = metadatas[0][i] if metadatas and metadatas[0] and i < len(metadatas[0]) else {}
                    distance = distances[0][i] if distances and distances[0] and i < len(distances[0]) else 1.0
                    
                    knowledge_list.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity": 1.0 - distance
                    })
        
        return knowledge_list
    
    def _format_memories_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """格式化记忆内容用于提示
        
        Args:
            memories: 记忆列表
            
        Returns:
            格式化的记忆文本
        """
        if not memories:
            return "无相关历史记忆。"
        
        memory_texts = []
        for memory in memories:
            memory_text = f"- {memory['name']}: {memory['content']}"
            if memory.get('meta_data'):
                meta_info = []
                for key, value in memory['meta_data'].items():
                    if key not in ['client_id']:  # 排除内部字段
                        meta_info.append(f"{key}: {value}")
                if meta_info:
                    memory_text += f" (元数据: {', '.join(meta_info)})"
            memory_texts.append(memory_text)
        
        return "相关历史记忆:\n" + "\n".join(memory_texts)
    
    def _format_knowledge_for_prompt(self, knowledge_list: List[Dict[str, Any]]) -> str:
        """格式化知识库内容用于提示
        
        Args:
            knowledge_list: 知识内容列表
            
        Returns:
            格式化的知识文本
        """
        if not knowledge_list:
            return "无相关知识库内容。"
        
        knowledge_texts = []
        for knowledge in knowledge_list:
            content = knowledge["content"]
            metadata = knowledge.get("metadata", {})
            similarity = knowledge.get("similarity", 0.0)
            
            # 添加文件名信息
            filename = metadata.get("filename", "未知文件")
            knowledge_text = f"- 来源: {filename} (相似度: {similarity:.2f})\n  内容: {content}"
            knowledge_texts.append(knowledge_text)
        
        return "相关知识库内容:\n" + "\n".join(knowledge_texts)
    
    def _get_conversation_messages(self, state: State) -> List[Dict[str, str]]:
        """获取对话消息列表，使用role、content格式
        
        Args:
            state: 当前状态
            
        Returns:
            消息列表
        """
        user_input = state.get("user_input", "")
        intent = state.get("intent", "")
        
        # 从state中获取用户记忆
        memories = self._get_memories_from_state(state)
        memory_text = self._format_memories_for_prompt(memories)
        
        # 从state中获取知识库内容
        knowledge_list = self._get_knowledge_from_state(state)
        knowledge_text = self._format_knowledge_for_prompt(knowledge_list)
        
        # 构建系统消息
        system_content = f"""你是一个专业的差旅报销助手。当用户的请求无法生成具体的执行计划时，你需要与用户进行对话，帮助澄清需求或提供相关信息。

你的职责：
1. 理解用户的需求
2. 提供相关的差旅报销政策信息
3. 引导用户提供更具体的信息
4. 解答用户的疑问
5. 提供友好的对话体验

{memory_text}

{knowledge_text}

请保持专业、友好、耐心的态度。根据用户的历史记忆和知识库内容，提供个性化的回复。"""
        
        # 构建用户消息
        user_content = f"""用户输入: {user_input}

用户意图: {intent}

请根据用户的需求、历史记忆和知识库内容，提供相应的回复。如果用户的需求不够明确，请引导用户提供更多信息。"""
        
        # 返回消息列表
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    
    async def __call__(self, state: State) -> State:
        """执行对话处理
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            print("--------------------------------------------------------------------------------conversation node start----------------------------------------------------------")
            
            # 获取对话消息
            messages = self._get_conversation_messages(state)
            
            # 转换为LangChain消息格式
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            # 执行对话
            print(f"【PROMPT】:\n{messages}")
            response = self.llm.invoke(langchain_messages)
            response_text = response.content

            print(f"【RESPONSE】:\n{response_text}")
            
            # 更新状态
            state["conversation_response"] = response_text
            state["status"] = "conversation_completed"
            state["final_output"] = response_text
            
            # 标记任务完成
            state["is_complete"] = True
            state["steps_completed"] = True
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"----conversation node error: {e}")
            
            # 出错时设置默认回复
            state["conversation_response"] = "抱歉，我遇到了一些技术问题。请稍后再试或联系技术支持。"
            state["status"] = "conversation_error"
            state["final_output"] = state["conversation_response"]
            state["is_complete"] = True
            state["steps_completed"] = True
            
            return state 