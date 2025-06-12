from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph, END
from datetime import datetime
import uuid
from typing import Dict, Any, List, Literal, Union, cast
import os
from dotenv import load_dotenv
import langchain

from .models.state import ExpenseState
from .nodes.intent_analysis import IntentAnalysisNode
from .nodes.task_planning import TaskPlanningNode
from .nodes.execution import ExecutionNode
from .nodes.tool_execution import ToolExecutionNode
from .nodes.retrieval import RetrievalNode
from .nodes.reflection import ReflectionNode
from .nodes.human_intervention import HumanInterventionNode
from .tool.registry import tool_registry
from .config import PORT, HOST
from .utils.logger import log_app_info, log_app_debug, log_error, log_workflow_transition

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
    
    if langsmith_enabled:
        log_app_info("LangSmith 集成已启用")
        log_app_info(f"LangSmith 项目: {os.environ.get('LANGCHAIN_PROJECT')}")
        log_app_info(f"LangSmith 端点: {os.environ.get('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')}")
        
        # 启用 LangChain 追踪
        langchain.verbose = True
        log_app_info("LangChain 追踪已启用")
    else:
        log_app_info("警告: 未设置 LANGCHAIN_API_KEY，LangSmith 追踪不可用")
        log_app_info("请在 .env 文件中设置 LANGCHAIN_API_KEY")
except Exception as e:
    log_error("配置", f"LangSmith 配置检查失败: {str(e)}")
    langsmith_enabled = False

app = FastAPI(title="差旅报销智能体")

# 初始化节点
intent_node = IntentAnalysisNode()
planning_node = TaskPlanningNode()
execution_node = ExecutionNode()
tool_node = ToolExecutionNode()
retrieval_node = RetrievalNode()
reflection_node = ReflectionNode()
human_intervention_node = HumanInterventionNode()

# 创建工作流
def create_workflow():
    workflow = StateGraph(ExpenseState)
    
    # 添加节点
    workflow.add_node("intent_analysis", intent_node)
    workflow.add_node("task_planning", planning_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("tool_execution", tool_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("reflection_node", reflection_node)  # 修改节点名称避免冲突
    workflow.add_node("human_intervention", human_intervention_node)
    
    # 定义路由函数
    def route_after_intent(state: ExpenseState) -> Union[Literal["task_planning"], Literal["tool_execution"]]:
        """意图分析后的路由逻辑
        
        如果有工具调用，执行工具调用；否则进行任务规划
        """
        has_tool_calls = "tool_calls" in state and state["tool_calls"]
        next_node = "tool_execution" if has_tool_calls else "task_planning"
        
        log_workflow_transition(
            "intent_analysis",
            next_node,
            f"意图分析完成，{'需要工具调用' if has_tool_calls else '进行任务规划'}"
        )
        
        if has_tool_calls:
            return "tool_execution"
        return "task_planning"
    
    def route_after_planning(state: ExpenseState) -> Union[Literal["execution"], Literal["retrieval"]]:
        """任务规划后的路由逻辑
        
        如果需要检索信息，转向检索节点；否则执行任务
        """
        needs_retrieval = state.get("need_retrieval", False)
        next_node = "retrieval" if needs_retrieval else "execution"
        
        log_workflow_transition(
            "task_planning",
            next_node,
            f"任务规划完成，{'需要信息检索' if needs_retrieval else '执行任务'}"
        )
        
        if needs_retrieval:
            return "retrieval"
        return "execution"
    
    def route_after_retrieval(state: ExpenseState) -> Literal["task_planning"]:
        """检索后的路由逻辑
        
        检索完成后返回任务规划
        """
        log_workflow_transition(
            "retrieval",
            "task_planning",
            "信息检索完成，返回任务规划"
        )
        
        return "task_planning"
    
    def route_after_execution(state: ExpenseState) -> Union[Literal["tool_execution"], Literal["reflection_node"]]:
        """执行后的路由逻辑
        
        如果有工具调用，执行工具调用；否则进行反思
        """
        # 先检查任务是否已完成
        if state.get("is_complete", False) or state.get("steps_completed", False):
            log_workflow_transition(
                "execution",
                "reflection_node",
                f"{'任务已标记为完成' if state.get('is_complete', False) else '当前计划步骤已全部执行'}，跳过工具调用，直接进行反思"
            )
            return "reflection_node"
        
        # 安全地检查tool_calls是否存在
        tool_calls = state.get("tool_calls", [])
        next_node = "tool_execution" if tool_calls else "reflection_node"
        
        log_workflow_transition(
            "execution",
            next_node,
            f"执行完成，{'需要工具调用' if tool_calls else '进行反思'}"
        )
        log_app_debug(f"工具调用详情: {tool_calls}")
        
        if tool_calls:  # 如果工具调用列表非空
            return "tool_execution"
        return "reflection_node"
    
    def route_after_tool(state: ExpenseState) -> Union[Literal["execution"], Literal["reflection_node"]]:
        """工具执行后的路由逻辑
        
        如果有最终输出，进行反思；否则继续执行
        """
        is_complete = state.get("is_complete", False)
        next_node = "reflection_node" if is_complete else "execution"
        
        log_workflow_transition(
            "tool_execution",
            next_node,
            f"工具执行完成，{'任务已完成，进行反思' if is_complete else '继续执行'}"
        )
        
        if is_complete:
            return "reflection_node"
        return "execution"
    
    def route_after_reflection(state: ExpenseState) -> Union[Literal["task_planning"], Literal["execution"], Literal["human_intervention"], Literal["END"]]:
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
            next_node = "human_intervention"
            reason = "可能需要人工干预"
        elif action == "replan":
            next_node = "task_planning"
            reason = "需要重新规划"
        elif action == "continue":
            next_node = "execution"
            reason = "继续执行"
        else:
            next_node = "END"
            reason = "任务结束"
        
        log_workflow_transition(
            "reflection_node",
            next_node,
            f"反思完成，{reason}"
        )
        
        if (detected_repetition or len(state.get("errors", [])) > 0) and not already_in_intervention:
            return "human_intervention"
        elif action == "replan":
            return "task_planning"
        elif action == "continue":
            return "execution"
        else:
            return "END"
    
    def route_after_human_intervention(state: ExpenseState) -> Union[Literal["task_planning"], Literal["execution"], Literal["END"], Literal["human_intervention"]]:
        """人工干预后的路由逻辑
        
        根据人工反馈决定下一步操作
        """
        # 检查是否有人工反馈
        if state.get("status") == "waiting_for_human":
            # 如果没有人工反馈，则保持在人工干预节点
            log_workflow_transition(
                "human_intervention",
                "human_intervention",
                "等待人工反馈"
            )
            return "human_intervention"
        
        # 如果有人工反馈，根据反馈决定下一步操作
        intervention_response = state.get("intervention_response", {})
        action = intervention_response.get("action", "end")
        
        if action == "replan":
            next_node = "task_planning"
            reason = "人工要求重新规划"
        elif action == "continue":
            next_node = "execution"
            reason = "人工要求继续执行"
        elif action == "modify":
            # 如果人工选择修改状态，可能需要重新规划或继续执行
            # 这里简单处理为返回到执行节点
            next_node = "execution"
            reason = "人工修改后继续执行"
        else:
            next_node = "END"
            reason = "人工要求结束任务"
        
        log_workflow_transition(
            "human_intervention",
            next_node,
            f"人工干预完成，{reason}"
        )
        
        if action == "replan":
            return "task_planning"
        elif action == "continue" or action == "modify":
            return "execution"
        else:
            return "END"
    
    # 设置边和条件路由
    workflow.add_edge(
        "intent_analysis",
         "task_planning"
      
    )
    
    workflow.add_conditional_edges(
        "task_planning",
        route_after_planning,
        {
            "execution": "execution",
            "retrieval": "retrieval"
        }
    )
    
    workflow.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {
            "task_planning": "task_planning"
        }
    )
    
    workflow.add_conditional_edges(
        "execution",
        route_after_execution,
        {
            "tool_execution": "tool_execution",
            "reflection_node": "reflection_node"
        }
    )
    
    workflow.add_conditional_edges(
        "tool_execution",
        route_after_tool,
        {
            "execution": "execution",
            "reflection_node": "reflection_node"
        }
    )
    
    workflow.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {
            "task_planning": "task_planning",
            "execution": "execution",
            "human_intervention": "human_intervention",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "human_intervention",
        route_after_human_intervention,
        {
            "task_planning": "task_planning",
            "execution": "execution",
            "human_intervention": "human_intervention",
            "END": END
        }
    )
    
    # 设置入口
    workflow.set_entry_point("intent_analysis")
    
    log_app_info("工作流创建完成")
    
    # 编译工作流
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
        log_app_info(f"收到来自客户端 {client_id} 的请求")
        
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
            client_id=client_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            need_retrieval=False,
            is_complete=False,
            reflection_result={},
            status="running",
            needs_human_intervention=False,
            intervention_request=None,
            intervention_response=None
        )
        
        log_app_info(f"创建任务 {initial_state['task_id']}")
        
        # 执行工作流
        try:
            log_app_info(f"开始执行工作流 {initial_state['task_id']}")
            final_state = await workflow.ainvoke(initial_state)
            log_app_info(f"工作流执行完成 {final_state['task_id']}")
            
            # 保存任务状态
            tasks_store[final_state["task_id"]] = final_state
        except Exception as e:
            log_error("工作流", f"工作流执行错误: {str(e)}")
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
            except Exception as e:
                log_error("LangSmith", f"获取 LangSmith 项目链接失败: {str(e)}")
        
        return response_data
        
    except Exception as e:
        log_error("API", f"处理请求时出错: {str(e)}")
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
        "completion_rate": state.get("reflection", {}).get("task_completion_rate", 0),
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
        log_app_info(f"继续执行工作流 {task_id} 并处理人工反馈")
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
        log_error("人工反馈", f"处理人工反馈时出错: {str(e)}")
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

# 添加优先级通知设置端点
@app.post("/notification_settings")
async def update_notification_settings(settings: Dict[str, Any]):
    """更新通知设置"""
    try:
        # 验证设置
        if "channels" not in settings or not isinstance(settings["channels"], dict):
            raise HTTPException(status_code=400, detail="设置必须包含'channels'字段")
        
        # 更新人工干预节点的通知渠道配置
        for priority, channels in settings["channels"].items():
            if priority in ["urgent", "important", "normal"]:
                human_intervention_node.notification_channels[priority] = channels
        
        # 如果提供了超时配置，也更新它
        if "timeout" in settings and isinstance(settings["timeout"], dict):
            for priority, timeout in settings["timeout"].items():
                if priority in ["urgent", "important", "normal"]:
                    human_intervention_node.timeout_config[priority] = timeout
        
        return {
            "status": "success",
            "message": "通知设置已更新",
            "current_settings": {
                "channels": human_intervention_node.notification_channels,
                "timeout": human_intervention_node.timeout_config
            }
        }
    except Exception as e:
        log_error("通知设置", f"更新通知设置时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    import uvicorn
    port = PORT
    host = HOST
    print(f"启动服务器 {host}:{port}")
    uvicorn.run("src.app:app", host=host, port=port) 