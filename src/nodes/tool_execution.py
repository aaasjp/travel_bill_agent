"""
工具执行节点
处理LangGraph与工具之间的交互
"""
from typing import Dict, Any, List, Optional
import json
import time
from ..models.state import ExpenseState
from ..tool.registry import tool_registry
from ..utils.logger import log_node_activity, log_error, log_tool_activity, log_node_entry, log_node_exit

class ToolExecutionNode:
    """
    工具执行节点，负责执行来自意图分析或执行节点的工具调用请求。
    
    该节点接收工具调用请求，调用相应的工具，并将结果返回给下一个节点。
    """
    
    def __init__(self):
        """初始化工具执行节点"""
        self.tool_registry = tool_registry
    
    def _add_log_entry(self, state: ExpenseState, action: str, details: Dict[str, Any]) -> None:
        """添加日志条目
        
        Args:
            state: 当前状态
            action: 执行的动作
            details: 详细信息
        """
        if "execution_log" not in state:
            state["execution_log"] = []
        
        # 获取当前时间戳
        timestamp = str(state["updated_at"])
        
        # 创建日志条目
        log_entry = {
            "node": "tool_execution",
            "action": action,
            "timestamp": timestamp,
            "details": details
        }
        
        # 添加日志到状态
        state["execution_log"].append(log_entry)
        
        # 同时记录到文件日志
        log_node_activity("tool_execution", action, details)
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行工具调用
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        # 记录节点开始执行
        state_id = state.get("id", "unknown")
        start_time = time.time()
        log_node_entry("tool_execution", state_id, {
            "tool_calls_count": len(state.get("tool_calls", [])),
            "user_input": state.get("user_input", ""),
            "intent": state.get("intent", {})
        })
        
        try:
            # 检查是否有工具调用请求
            if "tool_calls" not in state or not state["tool_calls"]:
                # 如果没有工具调用请求，记录日志并直接返回
                self._add_log_entry(
                    state, 
                    "无工具调用请求", 
                    {"message": "没有发现工具调用请求，跳过工具执行"}
                )
                
                # 记录节点执行完成
                execution_time = time.time() - start_time
                log_node_exit("tool_execution", state_id, execution_time, {
                    "status": "skipped",
                    "reason": "no_tool_calls",
                    "execution_time": f"{execution_time:.4f}秒"
                })
                
                return state
            
            # 初始化工具结果
            if "tool_results" not in state:
                state["tool_results"] = {}
            
            # 记录开始执行工具的日志
            tools_to_execute = [tool.get("name") for tool in state["tool_calls"]]
            self._add_log_entry(
                state,
                "开始执行工具调用",
                {
                    "tools_count": len(state["tool_calls"]),
                    "tools": tools_to_execute
                }
            )
            
            # 执行每个工具调用
            for tool_index, tool_call in enumerate(state["tool_calls"]):
                tool_name = tool_call.get("name")
                parameters = tool_call.get("parameters", {})
                
                # 记录工具调用请求
                self._add_log_entry(
                    state,
                    f"调用工具: {tool_name}",
                    {
                        "tool": tool_name,
                        "parameters": parameters,
                        "tool_index": tool_index + 1,
                        "total_tools": len(state["tool_calls"])
                    }
                )
                
                # 记录开始时间
                tool_start_time = time.time()
                
                # 执行工具调用
                try:
                    # 记录工具执行中状态
                    self._add_log_entry(
                        state,
                        f"工具 {tool_name} 执行中",
                        {
                            "tool": tool_name,
                            "status": "running",
                            "start_time": tool_start_time
                        }
                    )
                    
                    # 执行工具
                    result = await self.tool_registry.execute_tool(tool_name, parameters)
                    
                    # 计算执行时间
                    execution_time = time.time() - tool_start_time
                    
                    # 记录成功结果
                    state["tool_results"][tool_name] = {
                        "status": "success",
                        "result": result,
                        "execution_time": execution_time
                    }
                    
                    # 记录成功日志
                    result_summary = str(result)
                    if len(result_summary) > 100:
                        result_summary = result_summary[:100] + "..."
                    
                    self._add_log_entry(
                        state,
                        f"工具 {tool_name} 执行成功",
                        {
                            "tool": tool_name,
                            "status": "success",
                            "execution_time": f"{execution_time:.4f}秒",
                            "result_summary": result_summary
                        }
                    )
                    
                    # 更新上下文
                    if "context" not in state:
                        state["context"] = {}
                    
                    if "tool_outputs" not in state["context"]:
                        state["context"]["tool_outputs"] = {}
                    
                    state["context"]["tool_outputs"][tool_name] = result
                    
                    # 记录上下文更新
                    self._add_log_entry(
                        state,
                        f"更新上下文: {tool_name}",
                        {
                            "context_update": "tool_outputs",
                            "tool": tool_name
                        }
                    )
                    
                except Exception as e:
                    # 计算执行时间
                    execution_time = time.time() - tool_start_time
                    
                    # 记录错误
                    error_message = str(e)
                    if "errors" not in state:
                        state["errors"] = []
                    
                    state["errors"].append({
                        "node": "tool_execution",
                        "tool": tool_name,
                        "error": error_message,
                        "timestamp": str(state["updated_at"])
                    })
                    
                    # 记录失败结果
                    state["tool_results"][tool_name] = {
                        "status": "error",
                        "error": error_message,
                        "execution_time": execution_time
                    }
                    
                    # 记录失败日志
                    self._add_log_entry(
                        state,
                        f"工具 {tool_name} 执行失败",
                        {
                            "tool": tool_name,
                            "status": "error",
                            "execution_time": f"{execution_time:.4f}秒",
                            "error": error_message
                        }
                    )
                    
                    # 记录详细错误日志
                    log_error(
                        "tool_execution",
                        f"工具 {tool_name} 执行失败",
                        {
                            "tool": tool_name,
                            "parameters": parameters,
                            "execution_time": f"{execution_time:.4f}秒",
                            "error": error_message
                        }
                    )
            
            # 记录所有工具执行完成
            total_execution_time = time.time() - start_time
            tools_status = {
                name: result.get("status", "unknown")
                for name, result in state.get("tool_results", {}).items()
            }
            
            self._add_log_entry(
                state,
                "工具执行完成",
                {
                    "tools_count": len(state.get("tool_calls", [])),
                    "execution_time": f"{total_execution_time:.4f}秒",
                    "tools_status": tools_status
                }
            )
            
            # 记录节点执行完成
            log_node_exit("tool_execution", state_id, total_execution_time, {
                "status": "completed",
                "tools_executed": len(state.get("tool_calls", [])),
                "tools_status": tools_status,
                "total_execution_time": f"{total_execution_time:.4f}秒"
            })
            
            return state
            
        except Exception as e:
            # 记录未捕获的异常
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "tool_execution",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            # 记录错误日志
            self._add_log_entry(
                state,
                "节点执行错误",
                {
                    "error": error_message
                }
            )
            
            # 记录详细错误日志
            log_error(
                "tool_execution",
                "节点执行过程中发生未捕获的异常",
                {
                    "error": error_message
                }
            )
            
            # 记录节点执行完成（错误）
            execution_time = time.time() - start_time
            log_node_exit("tool_execution", state_id, execution_time, {
                "status": "error",
                "error": error_message,
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            # 重新抛出异常或返回当前状态
            return state 