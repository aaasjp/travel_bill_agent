"""
工具执行节点
处理LangGraph与工具之间的交互
"""
from typing import Dict, Any, List, Optional
import json
import time
from ..states.state import State
from ..tool.registry import tool_registry
import asyncio

class ToolExecutionNode:
    """
    工具执行节点，负责执行来自决策节点的工具调用请求。
    
    该节点接收决策节点输出的待执行工具列表，逐个执行工具，并将结果返回给下一个节点。
    支持循环执行直到所有工具都执行完成。
    """
    
    def __init__(self):
        """初始化工具执行节点"""
        self.tool_registry = tool_registry
    
    async def __call__(self, state: State) -> State:
        """执行工具调用
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 检查是否有待执行的工具
            pending_tools = state.get("pending_tools", [])
            if not pending_tools:
                return state
            
            # 初始化状态
            self._initialize_state(state)
            
            # 记录成功执行的工具名称，用于后续从pending_tools中移除
            successful_tools = []
            
            # 循环执行所有待执行工具
            for current_tool in pending_tools:
                tool_name = current_tool.get("tool_name", "")
                parameters = current_tool.get("parameters", {})
                step_id = current_tool.get("step_id", "")
                step_name = current_tool.get("step_name", "")
                step_desc = current_tool.get("step_desc", "")
                reasoning = current_tool.get("reasoning", "")
                
                if not tool_name:
                    raise Exception(f"tool_name is empty")
                
                # 执行工具调用
                execution_result = await self._execute_single_tool(
                    tool_name, parameters, step_id, step_name, step_desc, reasoning
                )
                
                if execution_result["status"] == "success":
                    # 记录成功结果
                    self._record_success_result(state, execution_result)
                    successful_tools.append(tool_name)
                else:
                    # 记录失败结果并停止执行
                    self._record_error_result(state, execution_result)
                    state["status"] = "tool_execution_failed"
                    return state
            
            # 从pending_tools中移除成功执行的工具
            state["pending_tools"] = [tool for tool in pending_tools if tool.get("tool_name") not in successful_tools]
            
            # 所有工具执行成功
            state["status"] = "tools_completed"
            self._record_completion_log(state)

            return state
            
        except Exception as e:
            # 记录未捕获的异常
            self._record_system_error(state, str(e))
            state["status"] = "tool_execution_failed"
            return state
    
    def _initialize_state(self, state: State) -> None:
        """初始化状态中的必要字段"""
        if "tool_results" not in state:
            state["tool_results"] = {}
        if "execution_log" not in state:
            state["execution_log"] = []
        if "completed_tools" not in state:
            state["completed_tools"] = []
        # 初始化current_results属性，记录当前最新的执行结果
        if "current_results" not in state:
            state["current_results"] = None
    
    async def _execute_single_tool(self, tool_name: str, parameters: Dict, 
                                 step_id: str, step_name: str, step_desc: str, reasoning: str) -> Dict:
        """执行单个工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            step_id: 步骤ID
            step_name: 步骤名称
            step_desc: 步骤描述
            reasoning: 推理过程
            
        Returns:
            执行结果字典
        """
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            tool_start_time = time.time()
            
            try:
                print(f"----tool_execution tool_name: {tool_name}")
                print(f"----tool_execution parameters: {parameters}")
                if retry_count > 0:
                    print(f"----tool_execution retry attempt: {retry_count}")
                
                # 执行工具
                result = await self.tool_registry.execute_tool(tool_name, parameters)
                execution_time = time.time() - tool_start_time
                
                return {
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time,
                    "step_id": step_id,
                    "step_name": step_name,
                    "step_desc": step_desc,
                    "parameters": parameters,
                    "reasoning": reasoning,
                    "error_type": None,
                    "retry_count": retry_count
                }
                
            except Exception as e:
                execution_time = time.time() - tool_start_time
                error_message = str(e)
                error_type = self._classify_error(e)
                can_retry = self._can_retry_error(error_type)
                
                # 如果不可重试或已达到最大重试次数，返回错误
                if not can_retry or retry_count >= max_retries:
                    return {
                        "status": "error",
                        "error": error_message,
                        "error_type": error_type,
                        "execution_time": execution_time,
                        "step_id": step_id,
                        "step_name": step_name,
                        "step_desc": step_desc,
                        "parameters": parameters,
                        "reasoning": reasoning,
                        "result": None,
                        "retry_count": retry_count,
                        "can_retry": can_retry
                    }
                
                # 可以重试，增加重试计数并继续循环
                retry_count += 1
                print(f"----tool_execution retrying tool {tool_name}, attempt {retry_count}/{max_retries}")
                # 等待一段时间再重试，避免立即重试
                await asyncio.sleep(1)
    
    def _record_success_result(self, state: State, execution_result: Dict) -> None:
        """记录成功执行的结果
        
        Args:
            state: 状态对象
            execution_result: 执行结果
        """
        tool_name = execution_result.get("step_name", "unknown_tool")
        retry_count = execution_result.get("retry_count", 0)
        
        # 记录工具结果
        state["tool_results"][tool_name] = execution_result
        
        # 更新current_results属性，供反思节点使用
        state["current_results"] = {
            "tool_name": tool_name,
            "status": "success",
            "result": execution_result["result"],
            "execution_time": execution_result["execution_time"],
            "step_id": execution_result["step_id"],
            "step_name": execution_result["step_name"],
            "step_desc": execution_result["step_desc"],
            "parameters": execution_result["parameters"],
            "reasoning": execution_result["reasoning"]
        }
        
        # 添加到已完成工具列表
        state["completed_tools"].append({
            "tool_name": tool_name,
            "step_id": execution_result["step_id"],
            "status": "success",
            "result": execution_result["result"],
            "execution_time": execution_result["execution_time"],
            "error_type": None,
            "retry_count": retry_count
        })
        
        # 记录执行日志
        log_message = f"调用工具: {tool_name}"
        if retry_count > 0:
            log_message += f" (重试{retry_count}次后成功)"
            
        self._add_execution_log(state, "tool_execution", log_message, {
            "tool_name": tool_name,
            "step_id": execution_result["step_id"],
            "step_name": execution_result["step_name"],
            "parameters": execution_result["parameters"],
            "result": execution_result["result"],
            "execution_time": execution_result["execution_time"],
            "status": "success",
            "retry_count": retry_count
        })
    
    def _record_error_result(self, state: State, execution_result: Dict) -> None:
        """记录错误执行的结果
        
        Args:
            state: 状态对象
            execution_result: 执行结果
        """
        tool_name = execution_result.get("step_name", "unknown_tool")
        retry_count = execution_result.get("retry_count", 0)
        
        # 记录错误
        if "errors" not in state:
            state["errors"] = []
        
        state["errors"].append({
            "node": "tool_execution",
            "tool": tool_name,
            "error": execution_result["error"],
            "error_type": execution_result["error_type"],
            "timestamp": str(state.get("updated_at", time.time())),
            "can_retry": execution_result["can_retry"],
            "retry_count": retry_count
        })
        
        # 记录工具结果
        state["tool_results"][tool_name] = execution_result
        
        # 更新current_results属性，供反思节点使用
        state["current_results"] = {
            "tool_name": tool_name,
            "status": "error",
            "error": execution_result["error"],
            "error_type": execution_result["error_type"],
            "execution_time": execution_result["execution_time"],
            "step_id": execution_result["step_id"],
            "step_name": execution_result["step_name"],
            "step_desc": execution_result["step_desc"],
            "parameters": execution_result["parameters"],
            "reasoning": execution_result["reasoning"],
            "can_retry": execution_result["can_retry"],
            "retry_count": retry_count
        }
        
        # 记录执行日志
        log_message = f"工具执行失败: {tool_name}"
        if retry_count > 0:
            log_message += f" (已重试{retry_count}次)"
            
        self._add_execution_log(state, "tool_execution", log_message, {
            "tool_name": tool_name,
            "step_id": execution_result["step_id"],
            "step_name": execution_result["step_name"],
            "parameters": execution_result["parameters"],
            "error": execution_result["error"],
            "error_type": execution_result["error_type"],
            "execution_time": execution_result["execution_time"],
            "status": "error",
            "can_retry": execution_result["can_retry"],
            "retry_count": retry_count
        })
    
    def _record_completion_log(self, state: State) -> None:
        """记录完成日志
        
        Args:
            state: 状态对象
        """
        self._add_execution_log(state, "tool_execution", "工具执行完成", {
            "final_status": state["status"],
            "completed_tools_count": len(state.get("completed_tools", []))
        })
    
    def _record_system_error(self, state: State, error_message: str) -> None:
        """记录系统错误
        
        Args:
            state: 状态对象
            error_message: 错误信息
        """
        if "errors" not in state:
            state["errors"] = []
            
        state["errors"].append({
            "node": "tool_execution",
            "error": error_message,
            "error_type": "system_error",
            "timestamp": str(state.get("updated_at", time.time()))
        })
    
    def _add_execution_log(self, state: State, node: str, action: str, details: Dict) -> None:
        """添加执行日志
        
        Args:
            state: 状态对象
            node: 节点名称
            action: 执行动作
            details: 详细信息
        """
        state["execution_log"].append({
            "node": node,
            "action": action,
            "details": details,
            "timestamp": time.time()
        })
    
    def _classify_error(self, exception: Exception) -> str:
        """分类错误类型
        
        Args:
            exception: 异常对象
            
        Returns:
            错误类型
        """
        error_message = str(exception).lower()
        
        # 参数验证错误
        if "valueerror" in error_message or "参数" in error_message or "不能为空" in error_message:
            return "parameter_validation_error"
        
        # 权限错误
        if "permission" in error_message or "权限" in error_message or "unauthorized" in error_message:
            return "permission_error"
        
        # 网络错误
        if "timeout" in error_message or "connection" in error_message or "网络" in error_message:
            return "network_error"
        
        # 资源不存在
        if "not found" in error_message or "不存在" in error_message or "不存在" in error_message:
            return "resource_not_found"
        
        # 业务逻辑错误
        if "业务" in error_message or "business" in error_message or "规则" in error_message:
            return "business_logic_error"
        
        # 系统错误
        if "system" in error_message or "系统" in error_message or "internal" in error_message:
            return "system_error"
        
        # 默认错误类型
        return "unknown_error"
    
    def _can_retry_error(self, error_type: str) -> bool:
        """判断错误是否可以重试
        
        Args:
            error_type: 错误类型
            
        Returns:
            是否可以重试
        """
        # 可以重试的错误类型
        retryable_errors = [
            "network_error",
            "system_error",
            "timeout_error"
        ]
        
        return error_type in retryable_errors
    