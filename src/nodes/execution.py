from typing import Dict, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..models.state import ExpenseState
from config.config import MODEL_NAME, MODEL_BASE_URL, API_KEY
class ExecutionNode:
    """执行节点"""
    
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = ChatOpenAI(model_name=model_name,base_url=MODEL_BASE_URL,api_key=API_KEY)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销执行助手。请执行当前步骤的任务。
            
            请考虑以下方面：
            1. 执行当前步骤的具体操作
            2. 记录执行结果和日志
            3. 处理可能的错误和异常
            4. 准备下一步的执行条件
            
            请以JSON格式输出，包含以下字段：
            - status: 执行状态（success/failure）
            - result: 执行结果
            - logs: 执行日志
            - errors: 错误信息（如果有）
            - next_step: 下一步建议
            """),
            ("user", "当前步骤: {current_step}\n计划: {plan}\n上下文: {context}")
        ])
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """处理状态并返回更新后的状态"""
        # 获取当前状态信息
        current_step = state["current_step"]
        plan = state["plan"]
        context = state["context"]
        
        # 调用模型执行当前步骤
        chain = self.prompt | self.model
        result = await chain.ainvoke({
            "current_step": current_step,
            "plan": plan,
            "context": context
        })
        
        # 更新状态
        state["execution_log"].append({
            "step": current_step,
            "status": result.get("status"),
            "result": result.get("result"),
            "logs": result.get("logs"),
            "errors": result.get("errors")
        })
        
        # 更新结果
        state["results"][f"step_{current_step}"] = result.get("result")
        
        # 如果有错误，添加到错误列表
        if result.get("errors"):
            state["errors"].extend(result.get("errors"))
        
        # 更新下一步
        state["current_step"] += 1
        
        return state 