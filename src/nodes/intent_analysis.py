from typing import Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..models.state import ExpenseState
from config.config import MODEL_NAME, MODEL_BASE_URL, API_KEY

class IntentAnalysisNode:
    """意图识别节点"""
    
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = ChatOpenAI(
            model_name=model_name,
            base_url=MODEL_BASE_URL,
            api_key=API_KEY
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销助手。请分析用户的输入，识别以下信息：
            1. 业务类型（差旅报销申请/查询/修改等）
            2. 时间范围
            3. 出差地点
            4. 申请类型
            5. 其他关键信息
            
            请以JSON格式输出，包含以下字段：
            - business_type: 业务类型
            - time_range: 时间范围
            - location: 出差地点
            - application_type: 申请类型
            - other_info: 其他信息
            """),
            ("user", "{input}")
        ])
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """处理状态并返回更新后的状态"""
        # 获取用户输入
        user_input = state["user_input"]
        
        # 调用模型进行意图分析
        chain = self.prompt | self.model
        result = await chain.ainvoke({"input": user_input})
        
        # 更新状态
        state["intent"] = result
        state["context"] = {
            "business_type": result.get("business_type"),
            "time_range": result.get("time_range"),
            "location": result.get("location"),
            "application_type": result.get("application_type"),
            "other_info": result.get("other_info")
        }
        
        return state 