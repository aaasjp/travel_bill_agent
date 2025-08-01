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
from .nodes.conversation import ConversationNode
from .tool.registry import tool_registry
from .config import PORT, HOST

# 加载环境变量
load_dotenv()

# 配置 LangSmith 环境变量（如果没有在.env文件中设置）
if "LANGCHAIN_TRACING_V2" not in os.environ:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
if "LANGCHAIN_PROJECT" not in os.environ:
    os.environ["LANGCHAIN_PROJECT"] = "智能体"  # 可自定义项目名称

# 检查 LangSmith 配置
try:
    langsmith_enabled = bool(os.environ.get("LANGCHAIN_API_KEY"))
    langchain.verbose = True if langsmith_enabled else False
except Exception as e:
    langsmith_enabled = False

app = FastAPI(title="智能体")

# 初始化节点
intent_node = AnalysisNode()
planning_node = PlanningNode()
decision_node = DecisionNode()
tool_node = ToolExecutionNode()
reflection_node = ReflectionNode()
human_intervention_node = HumanInterventionNode()
conversation_node = ConversationNode()

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
    workflow.add_node("conversation", conversation_node)
    
    def route_after_analysis(state: State) -> Literal["planning"]:
        """分析后的路由逻辑
        
        直接转向规划节点
        """
        return "planning"
    
    def route_after_planning(state: State) -> Union[Literal["conversation"], Literal["decision"]]:
        """规划后的路由逻辑
        
        根据status属性决定下一步：
        - conversation_ready: 进入对话节点
        - decision_ready: 进入决策节点
        """
        status = state.get("status", "")
        if status == "conversation_ready":
            return "conversation"
        elif status == "decision_ready":
            return "decision"
        else:
            # 默认进入决策节点
            return "decision"
    
    def route_after_conversation(state: State) -> Literal["END"]:
        """对话后的路由逻辑
        
        对话完成后直接结束
        """
        return "END"
    
    def route_after_decision(state: State) -> Union[Literal["tool_execution"], Literal["human_intervention"]]:
        """决策后的路由逻辑
        
        根据status和pending_tools决定下一步：
        - status为ready_for_execution且有pending_tools: 执行工具
        - status为waiting_for_human: 人工干预
        """
        status = state.get("status", "")
        
        # 检查是否需要人工干预
        if status == "waiting_for_human":
            return "human_intervention"
        
        # 检查是否有待执行的工具
        if status == "ready_for_execution":
            return "tool_execution"
        
        # 默认进行反思
        return "human_intervention"
    
    def route_after_tool(state: State) -> Literal["reflection_node"]:
        """工具执行后的路由逻辑

        工具执行完成后直接进行反思
        """
        return "reflection_node"
    
    def route_after_reflection(state: State) -> Union[Literal["planning"], Literal["human_intervention"], Literal["END"]]:
        """反思后的路由逻辑
        
        根据反思节点设置的status值决定下一步：
        - status为replan: 重新规划
        - status为waiting_for_human: 人工干预
        - status为end: 结束流程
        """
        status = state.get("status", "end")
        
        if status == "replan":
            return "planning"
        elif status == "waiting_for_human":
            return "human_intervention"
        else:
            return "END"
        
    
    def route_after_human_intervention(state: State) -> Union[Literal["planning"], Literal["decision"], Literal["END"], Literal["human_intervention"]]:
        """人工干预后的路由逻辑
        
        根据人工反馈和status决定下一步操作：
        - status为intervention_completed: 进入决策节点
        - status为intervention_error: 结束流程
        """
        status = state.get("status", "")
        
        # 检查人工干预完成状态
        if status == "intervention_completed":
            return "decision"
        
        # 检查人工干预错误状态
        if status == "intervention_error":
            return "END"
        
        # 默认进入决策节点
        return "decision"
    
    
    
    # 设置边和条件路由
    workflow.add_conditional_edges(
        "analysis",
        route_after_analysis,
        {
            "planning": "planning"
        }
    )
    
    workflow.add_conditional_edges(
        "planning",
        route_after_planning,
        {
            "conversation": "conversation",
            "decision": "decision"
        }
    )
    
    workflow.add_conditional_edges(
        "conversation",
        route_after_conversation,
        {
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "tool_execution": "tool_execution",
            "human_intervention": "human_intervention"
        }
    )
    
    workflow.add_conditional_edges(
        "tool_execution",
        route_after_tool,
        {
            "reflection_node": "reflection_node"
        }
    )
    
    workflow.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {
            "planning": "planning",
            "human_intervention": "human_intervention",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "human_intervention",
        route_after_human_intervention,
        {
            "decision": "decision",
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
    """处理报销请求"""
    try:
        # 验证输入
        if "input" not in input_data:
            raise HTTPException(status_code=400, detail="缺少 'input' 字段")
        
        user_input = input_data["input"]
        client_id = input_data.get("client_id", "default_client")
        
        # 创建初始状态
        initial_state = create_state(
            user_input=user_input,
            client_id=client_id
        )
        
        # 获取工作流
        workflow = create_workflow()
        
        try:
            final_state = await workflow.ainvoke(initial_state)
            
            # 保存任务状态
            tasks_store[final_state["task_id"]] = final_state
        except Exception as e:
            # 检查是否是GraphInterrupt（人工干预中断）
            if "GraphInterrupt" in str(type(e)) or "interrupt" in str(e).lower():
                # 这是正常的人工干预中断，不是错误
                # 从异常中提取中断信息
                interrupt_data = getattr(e, 'value', {})
                
                # 保存当前状态（包含干预请求）
                tasks_store[initial_state["task_id"]] = initial_state
                
                # 返回需要人工干预的响应
                return {
                    "task_id": initial_state["task_id"],
                    "status": "waiting_for_human",
                    "message": "需要人工干预",
                    "intervention_request": initial_state.get("intervention_request", {}),
                    "instruction": interrupt_data.get("instruction", "需要人工干预"),
                    "next_action": "请调用 /human_feedback/{task_id} 端点提供反馈"
                }
            else:
                # 这是真正的错误，重新抛出
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
        
        # 如果是对话节点完成的，添加对话相关信息
        if final_state.get("status") in ["conversation_completed", "conversation_error"]:
            response_data["conversation_response"] = final_state.get("conversation_response", "")
            response_data["result"]["conversation_type"] = "plan_empty"
        
        # 如果需要人工干预，添加干预请求
        if final_state.get("status") == "waiting_for_human":
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
                project_name = os.environ.get('LANGCHAIN_PROJECT', '智能体')
                
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
        "created_at": state.get("created_at", ""),
        "updated_at": state.get("updated_at", "")
    }
    
    # 如果需要人工干预，添加干预请求
    if state.get("status") == "waiting_for_human":
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
    
    if state.get("status") != "waiting_for_human":
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
        "name": "智能体",
        "version": "1.0.0",
        "status": "运行中",
        "endpoints": {
            "process": "/process - 处理智能体请求",
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