"""
工具执行节点
处理LangGraph与工具之间的交互
"""
from typing import Dict, Any, List, Optional
import json
import time
from ..states.state import State
from ..tool.registry import tool_registry

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
            
            # 初始化工具结果
            if "tool_results" not in state:
                state["tool_results"] = {}
            
            # 初始化执行日志
            if "execution_log" not in state:
                state["execution_log"] = []
            
            # 初始化已完成工具列表
            if "completed_tools" not in state:
                state["completed_tools"] = []
            
            # 初始化当前执行索引
            if "current_tool_index" not in state:
                state["current_tool_index"] = 0
            
            # 获取当前要执行的工具
            current_index = state["current_tool_index"]
            if current_index >= len(pending_tools):
                # 所有工具都已执行完成
                state["status"] = "tools_completed"
                state["execution_log"].append({
                    "node": "tool_execution",
                    "action": "所有工具执行完成",
                    "details": {
                        "total_tools": len(pending_tools),
                        "completed_tools": len(state["completed_tools"])
                    },
                    "timestamp": time.time()
                })
                return state
            
            current_tool = pending_tools[current_index]
            tool_name = current_tool.get("tool_name", "")
            parameters = current_tool.get("parameters", {})
            step_id = current_tool.get("step_id", "")
            step_name = current_tool.get("step_name", "")
            step_desc = current_tool.get("step_desc", "")
            reasoning = current_tool.get("reasoning", "")
            
            if not tool_name:
                # 跳过无效工具
                state["current_tool_index"] += 1
                return state
            
            # 记录开始时间
            tool_start_time = time.time()
            
            # 执行工具调用
            try:
                print(f"----tool_execution tool_name: {tool_name}")
                print(f"----tool_execution parameters: {parameters}")
                
                # 执行工具
                result = await self.tool_registry.execute_tool(tool_name, parameters)
                
                # 计算执行时间
                execution_time = time.time() - tool_start_time
                
                # 记录成功结果
                state["tool_results"][tool_name] = {
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time,
                    "step_id": step_id,
                    "step_name": step_name,
                    "step_desc": step_desc,
                    "parameters": parameters,
                    "reasoning": reasoning
                }
                
                # 添加到已完成工具列表
                state["completed_tools"].append({
                    "tool_name": tool_name,
                    "step_id": step_id,
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time
                })
                
                # 记录执行日志
                state["execution_log"].append({
                    "node": "tool_execution",
                    "action": f"调用工具: {tool_name}",
                    "details": {
                        "tool_name": tool_name,
                        "step_id": step_id,
                        "step_name": step_name,
                        "parameters": parameters,
                        "result": result,
                        "execution_time": execution_time
                    },
                    "timestamp": time.time()
                })
                
                # 移动到下一个工具
                state["current_tool_index"] += 1
                
                # 检查是否还有更多工具需要执行
                if state["current_tool_index"] >= len(pending_tools):
                    state["status"] = "tools_completed"
                    state["execution_log"].append({
                        "node": "tool_execution",
                        "action": "所有工具执行完成",
                        "details": {
                            "total_tools": len(pending_tools),
                            "completed_tools": len(state["completed_tools"])
                        },
                        "timestamp": time.time()
                    })
                else:
                    state["status"] = "tool_executed"
                
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
                    "step_id": step_id,
                    "step_name": step_name,
                    "error": error_message,
                    "timestamp": str(state["updated_at"])
                })
                
                # 记录失败结果
                state["tool_results"][tool_name] = {
                    "status": "error",
                    "error": error_message,
                    "execution_time": execution_time,
                    "step_id": step_id,
                    "step_name": step_name,
                    "step_desc": step_desc,
                    "parameters": parameters,
                    "reasoning": reasoning
                }
                
                # 添加到已完成工具列表（标记为失败）
                state["completed_tools"].append({
                    "tool_name": tool_name,
                    "step_id": step_id,
                    "status": "error",
                    "error": error_message,
                    "execution_time": execution_time
                })
                
                # 记录执行日志
                state["execution_log"].append({
                    "node": "tool_execution",
                    "action": f"工具执行失败: {tool_name}",
                    "details": {
                        "tool_name": tool_name,
                        "step_id": step_id,
                        "step_name": step_name,
                        "parameters": parameters,
                        "error": error_message,
                        "execution_time": execution_time
                    },
                    "timestamp": time.time()
                })
                
                # 移动到下一个工具（即使失败也继续）
                state["current_tool_index"] += 1
                
                # 检查是否还有更多工具需要执行
                if state["current_tool_index"] >= len(pending_tools):
                    state["status"] = "tools_completed_with_errors"
                    state["execution_log"].append({
                        "node": "tool_execution",
                        "action": "所有工具执行完成（包含错误）",
                        "details": {
                            "total_tools": len(pending_tools),
                            "completed_tools": len(state["completed_tools"]),
                            "errors": len(state["errors"])
                        },
                        "timestamp": time.time()
                    })
                else:
                    state["status"] = "tool_executed_with_error"
            
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
            
            return state
    
    def get_execution_summary(self, state: State) -> Dict[str, Any]:
        """获取执行摘要
        
        Args:
            state: 当前状态
            
        Returns:
            执行摘要
        """
        pending_tools = state.get("pending_tools", [])
        completed_tools = state.get("completed_tools", [])
        tool_results = state.get("tool_results", {})
        errors = state.get("errors", [])
        
        # 统计成功和失败的工具
        successful_tools = [tool for tool in completed_tools if tool.get("status") == "success"]
        failed_tools = [tool for tool in completed_tools if tool.get("status") == "error"]
        
        summary = {
            "total_tools": len(pending_tools),
            "completed_tools": len(completed_tools),
            "successful_tools": len(successful_tools),
            "failed_tools": len(failed_tools),
            "remaining_tools": len(pending_tools) - len(completed_tools),
            "current_tool_index": state.get("current_tool_index", 0),
            "status": state.get("status", "unknown"),
            "errors": len(errors)
        }
        
        return summary 