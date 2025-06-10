from typing import Dict, List
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..models.state import ExpenseState
from config.config import MODEL_NAME, MODEL_BASE_URL, API_KEY

class TaskPlanningNode:
    """任务规划节点"""
    
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = ChatOpenAI(model_name=model_name,base_url=MODEL_BASE_URL,api_key=API_KEY)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销规划助手。基于用户的意图和上下文，请生成详细的执行计划。
            
            请考虑以下步骤：
            1. 获取出差申请信息
            2. 收集报销凭证
            3. 费用分类和验证
            4. 生成报销表单
            5. 提交审批流程
            6. 跟踪审批状态
            
            请以JSON格式输出，包含以下字段：
            - steps: 执行步骤列表
            - dependencies: 步骤间的依赖关系
            - required_tools: 每个步骤需要的工具
            - estimated_time: 预计完成时间
            """),
            ("user", "意图: {intent}\n上下文: {context}")
        ])
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """处理状态并返回更新后的状态"""
        # 获取意图和上下文
        intent = state["intent"]
        context = state["context"]
        
        # 调用模型进行任务规划
        chain = self.prompt | self.model
        result = await chain.ainvoke({
            "intent": intent,
            "context": context
        })
        
        # 更新状态
        state["plan"] = result.get("steps", [])
        state["context"].update({
            "dependencies": result.get("dependencies", {}),
            "required_tools": result.get("required_tools", {}),
            "estimated_time": result.get("estimated_time")
        })
        
        return state 