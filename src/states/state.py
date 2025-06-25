from typing import Dict, List, Optional, Any, Union
from typing_extensions import TypedDict
from datetime import datetime
from pydantic import BaseModel, Field

class ToolCall(TypedDict):
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]

class ToolResult(TypedDict):
    """工具执行结果"""
    id: str
    name: str
    result: Any
    error: Optional[str]

class State(TypedDict, total=False):
    """节点状态"""
    
    # 基本信息
    task_id: str  # 任务ID
    user_input: str  # 用户输入
    client_id: str  # 客户端ID
    messages: List[Dict[str, Any]]  # 对话历史，每条消息包含 role(user/assistant)、content(内容)和action(用户动作)
    
    # 用户基本信息
    user_info: Dict[str, Any]  # 用户基本信息，包含姓名、工号、部门、职位、手机号、邮箱、性别、年龄等
    
    # 分析节点
    intent: Dict[str, Any]  # 意图分析结果
    memory_records: List[Dict[str, Any]]  # 用户记忆信息

    # 决策节点
    plan: List[Dict[str, Any]]  # 任务执行计划
    step_tools: List[Dict[str, Any]]  # 每个步骤选择的工具信息
    execution_log: List[Dict[str, Any]]  # 执行日志
    results: Dict[str, Any]  # 执行结果
    errors: List[Dict[str, Any]]  # 错误信息
    
    # 参数验证节点
    parameter_validation_results: Optional[Dict[str, Any]]  # 参数验证结果
    pending_tools: Optional[List[Dict[str, Any]]]  # 待执行的工具列表
    validated_tools: Optional[List[str]]  # 已完成参数验证的工具列表
    
    # 工具执行节点
    completed_tools: Optional[List[Dict[str, Any]]]  # 已完成的工具列表
    current_tool_index: Optional[int]  # 当前执行的工具索引
    
    # 工具调用相关
    tool_calls: Optional[List[Dict[str, Any]]]  # 工具调用请求
    tool_results: Optional[Dict[str, Any]]  # 工具调用结果
    
    # 反思相关
    reflection: Dict[str, Any]  # 反思结果
    reflection_result: Dict[str, Any]  # 详细反思分析结果
    
    # 任务完成标志
    is_complete: bool  # 当前步骤是否完成
    final_output: str  # 最终输出结果
    
    # 时间信息
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
    
    # 人工干预相关
    status: str  # 可能的值: running, waiting_for_human, processing, completed, error
    needs_human_intervention: bool  # 是否需要人工干预
    intervention_request: Optional[Dict[str, Any]]  # 人工干预请求
    intervention_response: Optional[Dict[str, Any]]  # 人工干预响应
    intervention_type: Optional[str]  # 介入类型：信息补充、决策确认、异常处理、权限授予
    intervention_priority: Optional[str]  # 介入优先级

# 初始化函数
def create_state(
    task_id: str,
    user_input: str,
    client_id: str = "default",
    user_info: Optional[Dict[str, Any]] = None
) -> State:
    """创建初始状态
    
    Args:
        task_id: 任务ID
        user_input: 用户输入
        client_id: 客户端ID
        user_info: 用户基本信息，包含姓名、工号、部门、职位、手机号、邮箱、性别、年龄等
        
    Returns:
        初始状态
    """
    return {
        # 基础信息
        "task_id": task_id,
        "client_id": client_id,
        "user_input": user_input,
        "messages": [],  # 初始化空的对话历史
        
        # 用户基本信息
        "user_info": user_info or {},
        
        # 分析结果
        "intent": {},
        "plan": [],
        
        # 执行信息
        "execution_log": [],
        "results": {},
        "errors": [],
        
        # 反思信息
        "reflection": {},
        "reflection_result": {},
        
        # 状态控制
        "is_complete": False,
        "final_output": "",
        
        # 时间戳
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        
        # 人工干预相关
        "status": "running",  # 可能的值: running, waiting_for_human, processing, completed, error
        "needs_human_intervention": False,
        "intervention_request": None,
        "intervention_response": None,
        "intervention_type": None,
        "intervention_priority": None
    } 