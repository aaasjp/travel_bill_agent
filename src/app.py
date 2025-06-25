from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph, END
from datetime import datetime
import uuid
from typing import Dict, Any, List, Literal, Union, cast
import os
from dotenv import load_dotenv
import langchain

from .states.state import State, create_state
from .nodes.analysis import AnalysisNode
from .nodes.planning import PlanningNode
from .nodes.decision import DecisionNode
from .nodes.tool_execution import ToolExecutionNode
from .nodes.reflection import ReflectionNode
from .nodes.human_intervention import HumanInterventionNode
from .tool.registry import tool_registry
from .config import PORT, HOST

# 加载环境变量
load_dotenv()

# 配置 LangSmith 环境变量（如果没有在.env文件中设置）
if "LANGCHAIN_TRACING_V2" not in os.environ:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
if "LANGCHAIN_PROJECT" not in os.environ:
    os.environ["LANGCHAIN_PROJECT"] = "差旅报销智能体"  # 可自定义项目名称

# 检查 LangSmith 配置
try:
    langsmith_enabled = bool(os.environ.get("LANGCHAIN_API_KEY"))
    langchain.verbose = True if langsmith_enabled else False
except Exception as e:
    langsmith_enabled = False

app = FastAPI(title="差旅报销智能体")

# 初始化节点
intent_node = AnalysisNode()
planning_node = PlanningNode()
decision_node = DecisionNode()
tool_node = ToolExecutionNode()
reflection_node = ReflectionNode()
human_intervention_node = HumanInterventionNode()

# 创建工作流
def create_workflow():
    workflow = StateGraph(State)
    
    # 添加节点
    workflow.add_node("analysis", intent_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("tool_execution", tool_node)
    workflow.add_node("reflection_node", reflection_node)  # 修改节点名称避免冲突
    workflow.add_node("human_intervention", human_intervention_node)
    
    
    def route_after_decision(state: State) -> Union[Literal["tool_execution"], Literal["reflection_node"]]:
        """执行后的路由逻辑
        
        如果有待执行的工具，则执行工具；否则进行反思
        """
        # 先检查任务是否已完成
        if state.get("is_complete", False) or state.get("steps_completed", False):
            return "reflection_node"
        
        # 检查是否有待执行的工具
        pending_tools = state.get("pending_tools", [])
        if pending_tools:
            return "tool_execution"
        
        return "reflection_node"
    
    def route_after_tool(state: State) -> Union[Literal["decision"], Literal["reflection_node"]]:
        """工具执行后的路由逻辑
        直接转向反思节点
        """
        return "reflection_node"
    
    def route_after_reflection(state: State) -> Union[Literal["planning"], Literal["decision"], Literal["human_intervention"], Literal["END"]]:
        """反思后的路由逻辑
        
        根据反思结果决定是重新规划、继续执行、人工干预或结束
        """
        reflection_result = state.get("reflection_result", {})
        action = reflection_result.get("action", "end")
        detected_repetition = reflection_result.get("detected_repetition", False)
        
        # 检查是否已经处于人工干预状态
        already_in_intervention = state.get("status") == "waiting_for_human" or state.get("needs_human_intervention", False)
        
        # 如果检测到重复调用或其他可能需要人工干预的情况，且尚未进入人工干预状态，转向人工干预节点
        if (detected_repetition or len(state.get("errors", [])) > 0) and not already_in_intervention:
            return "human_intervention"
        elif action == "replan":
            return "planning"
        elif action == "continue":
            return "decision"
        else:
            return "END"
    
    def route_after_human_intervention(state: State) -> Union[Literal["planning"], Literal["decision"], Literal["END"], Literal["human_intervention"]]:
        """人工干预后的路由逻辑
        
        根据人工反馈决定下一步操作
        """
        # 检查是否有人工反馈
        if state.get("status") == "waiting_for_human":
            # 如果没有人工反馈，则保持在人工干预节点
            return "human_intervention"
        
        # 如果有人工反馈，根据反馈决定下一步操作
        intervention_response = state.get("intervention_response", {})
        action = intervention_response.get("action", "end")
        
        if action == "replan":
            return "planning"
        elif action == "continue" or action == "modify":
            return "decision"
        else:
            return "END"
    
    # 设置边和条件路由
    workflow.add_edge(
        "analysis",
         "planning"
    )
    
    workflow.add_edge(
        "planning",
        "decision"
    )
    
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "tool_execution": "tool_execution",
            "reflection_node": "reflection_node"
        }
    )
    
    workflow.add_conditional_edges(
        "tool_execution",
        route_after_tool,
        {
            "decision": "decision",
            "reflection_node": "reflection_node"
        }
    )
    
    workflow.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {
            "planning": "planning",
            "decision": "decision",
            "human_intervention": "human_intervention",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "human_intervention",
        route_after_human_intervention,
        {
            "planning": "planning",
            "decision": "decision",
            "human_intervention": "human_intervention",
            "END": END
        }
    )
    
    # 设置入口点
    workflow.set_entry_point("analysis")
    
    return workflow.compile()

# 创建工作流实例
workflow = create_workflow()

# 存储任务状态
tasks_store = {}

@app.post("/process")
async def process_expense(input_data: Dict[str, Any]):
    """处理差旅报销请求"""
    try:
        # 获取客户端ID
        client_id = input_data.get("client_id", "default")
        
        # 获取用户信息
        user_info = input_data.get("user_info", None)
        
        # 创建初始状态
        initial_state = create_state(
            task_id=str(uuid.uuid4()),
            user_input=input_data.get("input", ""),
            client_id=client_id,
            user_info=user_info
        )
        
        # 执行工作流
        try:
            final_state = await workflow.ainvoke(initial_state)
            
            # 保存任务状态
            tasks_store[final_state["task_id"]] = final_state
        except Exception as e:
            raise
        
        # 准备响应数据
        response_data = {
            "task_id": final_state["task_id"],
            "status": final_state.get("status", "success"),
            "result": {
                "intent": final_state.get("intent", {}),
                "output": final_state.get("final_output", ""),
            }
        }
        
        # 如果需要人工干预，添加干预请求
        if final_state.get("needs_human_intervention", False):
            response_data["needs_human_intervention"] = True
            response_data["intervention_request"] = final_state.get("intervention_request", {})
        
        # 如果有错误，添加到响应
        if final_state.get("errors"):
            response_data["errors"] = final_state["errors"]
        
        # 如果有工具结果，添加到响应
        if final_state.get("tool_results"):
            response_data["tool_results"] = final_state["tool_results"]
        
        # 如果启用了 LangSmith，添加项目链接
        if langsmith_enabled:
            try:
                # 构建 LangSmith 项目链接
                langsmith_endpoint = os.environ.get('LANGCHAIN_ENDPOINT', 'https://smith.langchain.com')
                project_name = os.environ.get('LANGCHAIN_PROJECT', '差旅报销智能体')
                
                # 提供项目链接
                project_url = f"{langsmith_endpoint}/projects/{project_name}"
                response_data["langsmith_url"] = project_url
            except Exception:
                pass
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    state = tasks_store[task_id]
    
    # 准备状态响应
    status_response = {
        "task_id": task_id,
        "status": state.get("status", "unknown"),
        "needs_human_intervention": state.get("needs_human_intervention", False),
        "created_at": state.get("created_at", ""),
        "updated_at": state.get("updated_at", "")
    }
    
    # 如果需要人工干预，添加干预请求
    if state.get("needs_human_intervention", False):
        status_response["intervention_request"] = state.get("intervention_request", {})
    
    # 如果有最终输出，添加到响应
    if state.get("final_output"):
        status_response["final_output"] = state["final_output"]
    
    return status_response

@app.post("/human_feedback/{task_id}")
async def provide_human_feedback(task_id: str, feedback: Dict[str, Any]):
    """提供人工反馈"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    state = tasks_store[task_id]
    
    if not state.get("needs_human_intervention", False):
        raise HTTPException(status_code=400, detail=f"任务 {task_id} 不需要人工干预")
    
    # 验证反馈格式
    if "action" not in feedback:
        raise HTTPException(status_code=400, detail="反馈必须包含 'action' 字段")
    
    # 验证动作是否有效
    valid_actions = ["continue", "replan", "end", "modify", "grant", "skip", "confirm"]
    if feedback["action"] not in valid_actions:
        raise HTTPException(status_code=400, detail=f"无效的动作: {feedback['action']}. 有效动作: {valid_actions}")
    
    # 验证必要的参数
    if feedback["action"] == "modify" and "additional_info" not in feedback:
        raise HTTPException(status_code=400, detail="'modify'动作需要提供'additional_info'参数")
    
    if feedback["action"] == "grant" and ("permission_scope" not in feedback or "duration" not in feedback):
        raise HTTPException(status_code=400, detail="'grant'动作需要提供'permission_scope'和'duration'参数")
    
    if feedback["action"] == "confirm" and "confirmation_note" not in feedback:
        raise HTTPException(status_code=400, detail="'confirm'动作需要提供'confirmation_note'参数")
    
    try:
        # 记录人工干预历史
        if "intervention_history" not in state:
            state["intervention_history"] = []
            
        # 保存当前干预请求和响应到历史记录
        intervention_history_entry = {
            "timestamp": datetime.now(),
            "request": state.get("intervention_request", {}),
            "response": feedback,
            "intervention_type": state.get("intervention_type"),
            "intervention_priority": state.get("intervention_priority")
        }
        state["intervention_history"].append(intervention_history_entry)
        
        # 提供反馈
        await human_intervention_node.provide_feedback(task_id, feedback)
        
        # 更新任务状态
        state["intervention_response"] = feedback
        state["status"] = "processing"  # 从 waiting_for_human 更新为 processing
        tasks_store[task_id] = state
        
        # 继续执行工作流
        final_state = await workflow.ainvoke(state)
        
        # 更新任务状态
        tasks_store[task_id] = final_state
        
        # 准备响应
        response = {
            "task_id": task_id,
            "status": final_state.get("status", "success"),
            "message": "人工反馈已处理",
            "result": {
                "output": final_state.get("final_output", "")
            }
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 添加新的API端点用于获取干预历史
@app.get("/intervention_history/{task_id}")
async def get_intervention_history(task_id: str):
    """获取任务的人工干预历史"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    state = tasks_store[task_id]
    
    intervention_history = state.get("intervention_history", [])
    
    # 准备响应
    response = {
        "task_id": task_id,
        "intervention_count": len(intervention_history),
        "intervention_history": intervention_history
    }
    
    return response


@app.get("/tools")
async def get_tools():
    """获取可用工具列表"""
    try:
        tools = tool_registry.get_all_schemas()
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """返回基本信息和指引"""
    info = {
        "name": "差旅报销智能体",
        "version": "1.0.0",
        "status": "运行中",
        "endpoints": {
            "process": "/process - 处理差旅报销请求",
            "status": "/status/{task_id} - 获取任务状态",
            "human_feedback": "/human_feedback/{task_id} - 提供人工反馈",
            "tools": "/tools - 获取可用工具列表"
        },
        "langsmith_status": "已启用" if langsmith_enabled else "未启用"
    }
    
    if langsmith_enabled:
        info["langsmith_project"] = os.environ.get("LANGCHAIN_PROJECT")
        info["langsmith_url"] = os.environ.get("LANGCHAIN_ENDPOINT", "https://smith.langchain.com")
        info["langsmith_studio_url"] = f"https://smith.langchain.com/studio/thread?baseUrl=http://127.0.0.1:8000&mode=graph"
    
    return info

def create_app():
    """创建并返回 FastAPI 应用实例"""
    return app

if __name__ == "__main__":
    import uvicorn
    port = PORT
    host = HOST
    uvicorn.run("src.app:app", host=host, port=port) 