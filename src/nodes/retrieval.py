from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import time

from ..models.state import ExpenseState
from ..config import get_llm

class RetrievalNode:
    """
    检索节点，负责从知识库中检索相关信息。
    
    该节点会根据当前状态中的检索需求，从知识库中检索相关信息，并将结果添加到状态中。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化检索节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        
        # 定义检索分析提示模板
        self.retrieval_prompt = ChatPromptTemplate.from_template("""
        你是一个专业的差旅报销助手的检索组件。
        根据用户的问题和当前的任务，分析需要检索哪些信息来支持后续处理。
        
        ## 用户输入
        {user_input}
        
        ## 当前意图
        {intent}
        
        ## 当前计划
        {plan}
        
        请分析需要从知识库中检索哪些信息，以便更好地完成任务。以JSON格式返回结果：
        
        ```json
        {
            "query_keywords": ["关键词1", "关键词2"...],
            "information_types": ["政策", "表格", "流程"...],
            "rationale": "为什么需要检索这些信息的解释"
        }
        ```
        """)
        
        # 定义查询解析器
        self.parser = JsonOutputParser()
        
        # 构建检索链
        self.chain = self.retrieval_prompt | self.llm | self.parser
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行检索操作
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 准备检索分析输入
            inputs = {
                "user_input": state["user_input"],
                "intent": state["intent"],
                "plan": state["plan"]
            }
            
            # 分析需要检索的内容
            retrieval_analysis = await self.chain.ainvoke(inputs)
            
            # 这里是模拟检索操作
            # 在实际应用中，应该根据 retrieval_analysis 的内容
            # 从向量数据库或其他知识库中检索实际信息
            retrieval_start_time = time.time()
            
            # 模拟的检索结果
            retrieval_results = {
                "policy_info": {
                    "max_meal_allowance": "每日100元",
                    "hotel_limit": "四星级以下",
                    "transportation": "经济舱/二等座"
                },
                "form_templates": ["标准报销单", "出差申请单", "交通费报销明细"],
                "process_info": {
                    "approval_flow": ["部门经理", "财务审核", "财务经理"],
                    "time_requirement": "报销需在出差结束后30天内提交"
                }
            }
            
            # 更新状态中的上下文
            if "context" not in state:
                state["context"] = {}
                
            state["context"].update({
                "retrieval_analysis": retrieval_analysis,
                "retrieval_results": retrieval_results
            })
            
            # 设置检索完成标志
            state["need_retrieval"] = False
            return state
            
        except Exception as e:
            # 记录错误
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "retrieval",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            # 即使出错也继续流程
            state["need_retrieval"] = False
            return state 