from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph, END
from datetime import datetime
import uuid
from typing import Dict, Any

from .models.state import ExpenseState
from .nodes.intent_analysis import IntentAnalysisNode
from .nodes.task_planning import TaskPlanningNode
from .nodes.execution import ExecutionNode

app = FastAPI(title="差旅报销智能体")

# 初始化节点
intent_node = IntentAnalysisNode()
planning_node = TaskPlanningNode()
execution_node = ExecutionNode()

# 创建工作流
def create_workflow():
    workflow = StateGraph(ExpenseState)
    
    # 添加节点
    workflow.add_node("intent_analysis", intent_node)
    workflow.add_node("task_planning", planning_node)
    workflow.add_node("execution", execution_node)
    
    # 设置边
    workflow.add_edge("intent_analysis", "task_planning")
    workflow.add_edge("task_planning", "execution")
    workflow.add_edge("execution", END)
    
    # 设置入口
    workflow.set_entry_point("intent_analysis")
    
    return workflow.compile()

# 创建工作流实例
workflow = create_workflow()

@app.post("/process")
async def process_expense(input_data: Dict[str, Any]):
    """处理差旅报销请求"""
    try:
        # 创建初始状态
        initial_state = ExpenseState(
            task_id=str(uuid.uuid4()),
            user_input=input_data.get("input", ""),
            intent={},
            plan=[],
            context={},
            execution_log=[],
            current_step=0,
            results={},
            errors=[],
            reflection={},
            final_output="",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 执行工作流
        final_state = await workflow.ainvoke(initial_state)
        
        return {
            "task_id": final_state["task_id"],
            "status": "success",
            "result": final_state["results"],
            "errors": final_state["errors"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """获取任务状态"""
    # TODO: 实现状态查询逻辑
    return {"status": "not_implemented"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 