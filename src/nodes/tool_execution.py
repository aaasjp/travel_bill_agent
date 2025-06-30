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
            print("--------------------------------工具执行节点开始执行--------------------------------")
            # 设置created_at时间戳（如果不存在）
            if "created_at" not in state:
                from datetime import datetime
                state["created_at"] = datetime.now()
            
            # 检查是否有待执行的工具
            pending_tools = state.get("pending_tools", [])
            if not pending_tools:
                # 清理状态对象，移除可能导致循环引用的字段
                return self._clean_state_for_serialization(state)
            
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
                    state, tool_name, parameters, step_id, step_name, step_desc, reasoning
                )
                
                if execution_result["status"] == "success":
                    # 记录成功结果
                    self._record_success_result(state, execution_result)
                    successful_tools.append(tool_name)
                else:
                    # 记录失败结果并停止执行
                    self._record_error_result(state, execution_result)
                    state["status"] = "tool_execution_failed"
                    
                    # 更新时间戳
                    from datetime import datetime
                    state["updated_at"] = datetime.now()
                    
                    # 清理状态对象，移除可能导致循环引用的字段
                    return self._clean_state_for_serialization(state)
            
            # 从pending_tools中移除成功执行的工具
            state["pending_tools"] = [tool for tool in pending_tools if tool.get("tool_name") not in successful_tools]
            
            # 所有工具执行成功
            state["status"] = "tools_completed"
            self._record_completion_log(state)

            # 更新时间戳
            from datetime import datetime
            state["updated_at"] = datetime.now()

            # 清理状态对象，移除可能导致循环引用的字段
            return self._clean_state_for_serialization(state)
            
        except Exception as e:
            # 记录未捕获的异常
            self._record_system_error(state, str(e))
            state["status"] = "tool_execution_failed"
            
            # 更新时间戳
            from datetime import datetime
            state["updated_at"] = datetime.now()
            
            # 清理状态对象，移除可能导致循环引用的字段
            return self._clean_state_for_serialization(state)
    
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
    
    def _clean_state_for_serialization(self, state: State) -> State:
        """清理状态对象，移除可能导致循环引用的字段
        
        Args:
            state: 原始状态对象
            
        Returns:
            清理后的状态对象
        """
        # 创建状态对象的副本，避免修改原始对象
        cleaned_state = state.copy()
        
        # 移除可能导致循环引用的字段
        problematic_fields = [
            "available_tools",  # 工具schema可能包含循环引用
            "tool_registry",    # 工具注册表实例
            "llm",             # 语言模型实例
            "memory_store",    # 记忆存储实例
            "self",            # 可能的self引用
            "_tool_registry",  # 私有字段
            "_llm",           # 私有字段
            "_memory_store"   # 私有字段
        ]
        
        for field in problematic_fields:
            if field in cleaned_state:
                del cleaned_state[field]
        
        # 清理工具结果中的复杂对象
        if "tool_results" in cleaned_state:
            for tool_name, result in cleaned_state["tool_results"].items():
                if isinstance(result, dict):
                    # 移除可能包含循环引用的字段
                    problematic_result_fields = ["schema", "tool_instance", "self", "_tool", "tool"]
                    for field in problematic_result_fields:
                        if field in result:
                            del result[field]
        
        # 清理执行日志中的复杂对象
        if "execution_log" in cleaned_state:
            for log_entry in cleaned_state["execution_log"]:
                if isinstance(log_entry, dict) and "details" in log_entry:
                    details = log_entry["details"]
                    if isinstance(details, dict):
                        # 移除可能包含循环引用的字段
                        problematic_detail_fields = ["schema", "tool_instance", "self", "_tool", "tool"]
                        for field in problematic_detail_fields:
                            if field in details:
                                del details[field]
        
        # 清理参数验证结果中的复杂对象
        if "parameter_validation_results" in cleaned_state:
            for validation_key, validation_result in cleaned_state["parameter_validation_results"].items():
                if isinstance(validation_result, dict):
                    # 移除可能包含循环引用的字段
                    if "schema" in validation_result:
                        # 只保留schema的基本信息，移除可能包含循环引用的部分
                        schema = validation_result["schema"]
                        if isinstance(schema, dict):
                            # 保留基本信息，移除复杂对象
                            safe_schema = {
                                "name": schema.get("name"),
                                "description": schema.get("description"),
                                "group": schema.get("group")
                            }
                            if "parameters" in schema:
                                safe_schema["parameters"] = {
                                    "type": schema["parameters"].get("type"),
                                    "required": schema["parameters"].get("required", [])
                                }
                            validation_result["schema"] = safe_schema
        
        # 清理反思结果中的复杂对象
        if "reflection_results" in cleaned_state:
            reflection_results = cleaned_state["reflection_results"]
            if isinstance(reflection_results, dict):
                # 移除可能包含循环引用的字段
                problematic_reflection_fields = ["schema", "tool_instance", "self", "_tool", "tool"]
                for field in problematic_reflection_fields:
                    if field in reflection_results:
                        del reflection_results[field]
        
        return cleaned_state
    
    async def _execute_single_tool(self, state: State, tool_name: str, parameters: Dict, 
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
                
                
                # 从state中获取工具的required参数信息
                available_tools = state.get("available_tools", [])
                required_params = []
                for tool_schema in available_tools:
                    if tool_schema.get("name") == tool_name:
                        required_params = tool_schema.get("parameters", {}).get("required", [])
                        break
                
                print(f"----tool_execution tool_name: {tool_name}, parameters: ({parameters}), required_parameters: ({required_params})")
                
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
            "timestamp": str(time.time()),
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
        self._add_execution_log(state, "tool_execution", "所有工具执行完成", {
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
            "timestamp": str(time.time())
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
    