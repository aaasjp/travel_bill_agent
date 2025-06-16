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
    工具执行节点，负责执行来自任务规划节点的工具调用请求。
    
    该节点接收任务规划中的工具调用请求，调用相应的工具，并将结果返回给下一个节点。
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
            # 检查是否有任务计划
            if "plan" not in state or not state["plan"]:
                return state
            
            # 初始化工具结果
            if "tool_results" not in state:
                state["tool_results"] = {}
            
            # 执行每个步骤中的工具调用
            for step in state["plan"]:
                if not isinstance(step, dict):
                    continue
                    
                tool_info = step.get("tool", {})
                if not isinstance(tool_info, dict):
                    continue
                    
                tool_name = tool_info.get("name")
                parameters = tool_info.get("parameters", {})
                
                if not tool_name:
                    continue
                
                # 记录开始时间
                tool_start_time = time.time()
                
                # 执行工具调用
                try:
                    # 执行工具
                    print(f"----tool_execution tool_name: {tool_name}")
                    result = await self.tool_registry.execute_tool(tool_name, parameters)
                    
                    # 计算执行时间
                    execution_time = time.time() - tool_start_time
                    
                    # 记录成功结果
                    state["tool_results"][tool_name] = {
                        "status": "success",
                        "result": result,
                        "execution_time": execution_time,
                        "step_id": step.get("step_id", ""),
                        "step_name": step.get("step_name", ""),
                        "action": step.get("action", "")
                    }
                    
                    # 更新上下文
                    if "context" not in state:
                        state["context"] = {}
                    
                    if "tool_outputs" not in state["context"]:
                        state["context"]["tool_outputs"] = {}
                    
                    state["context"]["tool_outputs"][tool_name] = result
                    
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
                        "step_id": step.get("step_id", ""),
                        "step_name": step.get("step_name", ""),
                        "error": error_message,
                        "timestamp": str(state["updated_at"])
                    })
                    
                    # 记录失败结果
                    state["tool_results"][tool_name] = {
                        "status": "error",
                        "error": error_message,
                        "execution_time": execution_time,
                        "step_id": step.get("step_id", ""),
                        "step_name": step.get("step_name", ""),
                        "action": step.get("action", "")
                    }
            
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