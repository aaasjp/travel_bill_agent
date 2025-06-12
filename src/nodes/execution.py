from typing import Dict, Any, List, Optional, Tuple
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import time

from ..models.state import ExpenseState
from ..config import get_llm
from ..tool.registry import tool_registry
from ..utils.logger import log_node_activity, log_error, log_node_entry, log_node_exit

class ExecutionNode:
    """
    执行节点，负责执行任务计划中的具体步骤。
    
    根据任务计划，执行当前步骤，更新状态，并决定是否需要调用工具。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化执行节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        self.tool_registry = tool_registry
        
        # 定义执行提示模板
        self.execution_prompt = ChatPromptTemplate.from_template("""你是一个专业的差旅报销助手的执行组件。
根据当前的任务计划和状态，你需要执行当前步骤。

## 用户输入
{user_input}

## 意图分析
{intent}

## 任务计划
{plan}

## 当前执行步骤: {current_step}

## 当前步骤详情
{current_step_details}

## 上下文信息
{context}

## 执行日志
{execution_log}

## 已执行的行动
{action_taken}

## 可用工具列表
{available_tools}

请执行当前步骤，并返回JSON格式的结果：

```json
{{
    "action_taken": "执行的具体操作",
    "result": "操作结果或生成的内容",
    "requires_tool": true/false,
    "tool_calls": [
        {{
            "name": "工具名称",
            "parameters": {{"参数1": "值1", "参数2": "值2"}}
        }}
    ],
    "next_step": 2,  // 下一步骤编号，如果是最后一步则为-1
    "is_complete": true/false,  // 整个任务是否完成
    "final_output": "如果任务完成，提供最终输出内容"
}}
```

注意：
1. 如果需要调用工具，设置 requires_tool 为 true，并在 tool_calls 中指定工具名称和参数。
2. 如果是最后一步或任务已完成，设置 is_complete 为 true。
3. 如果不需要调用工具，直接执行操作并返回结果。
4. 只能使用上面列出的可用工具，不要尝试调用不存在的工具。
5. 工具调用时，确保参数名称和类型与工具定义匹配。
6. 请尽可能使用任务规划中为当前步骤推荐的工具，这样能更好地完成任务。""")
        
        # 定义解析器
        self.parser = JsonOutputParser()
        
        # 构建执行链
        self.chain = self.execution_prompt | self.llm | self.parser
    
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
            "node": "execution",
            "action": action,
            "timestamp": timestamp,
            "details": details
        }
        
        # 添加日志到状态
        state["execution_log"].append(log_entry)
        
        # 同时记录到文件日志
        log_node_activity("execution", action, details)
    
    def _get_available_tools_description(self) -> Tuple[str, List[Dict[str, Any]]]:
        """获取可用工具的描述
        
        Returns:
            工具描述字符串和工具模式列表
        """
        # 获取所有工具模式
        tool_schemas = self.tool_registry.get_all_schemas()
        
        # 格式化工具描述
        tools_description = ""
        for idx, tool in enumerate(tool_schemas):
            tool_desc = f"{idx+1}. {tool['name']}\n"
            tool_desc += f"   描述: {tool['description']}\n"
            tool_desc += f"   参数: {json.dumps(tool['parameters']['properties'], ensure_ascii=False, indent=2)}\n"
            tools_description += tool_desc + "\n"
        
        return tools_description, tool_schemas
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行当前步骤
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        # 记录节点开始执行
        state_id = state.get("id", "unknown")
        start_time = time.time()
        log_node_entry("execution", state_id, {
            "current_step": state.get("current_step", 0),
            "total_steps": len(state.get("plan", [])),
            "user_input": state.get("user_input", ""),
            "intent": state.get("intent", {})
        })
        
        try:
            # 记录执行开始
            self._add_log_entry(
                state, 
                "开始执行任务步骤", 
                {"message": "开始执行执行节点"}
            )
            
            # 获取当前步骤
            current_step = state.get("current_step", 0)
            plan = state.get("plan", [])
            
            # 初始化已执行步骤跟踪
            if "executed_steps_count" not in state:
                state["executed_steps_count"] = 0
                
            # 初始化已执行步骤列表
            if "executed_steps" not in state:
                state["executed_steps"] = []
                
            # 初始化遗漏步骤列表
            if "missed_steps" not in state:
                state["missed_steps"] = []
            
            # 检查是否有来自反思节点的遗漏步骤需要重新执行
            if "missed_steps_to_execute" in state and state["missed_steps_to_execute"]:
                # 获取第一个需要重新执行的遗漏步骤
                missed_step = state["missed_steps_to_execute"][0]
                current_step = missed_step
                
                # 从列表中移除这个步骤
                state["missed_steps_to_execute"] = state["missed_steps_to_execute"][1:]
                
                self._add_log_entry(
                    state,
                    "执行遗漏步骤",
                    {
                        "missed_step": missed_step,
                        "remaining_missed_steps": len(state["missed_steps_to_execute"]),
                        "message": f"开始执行之前遗漏的步骤 {missed_step + 1}"
                    }
                )
                
                # 更新当前步骤
                state["current_step"] = current_step
            
            # 检查是否还有步骤可执行
            if not plan or current_step >= len(plan):
                # 标记步骤完成，但不立即结束任务
                # 让反思节点决定是继续执行、重新规划还是结束任务
                state["steps_completed"] = True
                
                self._add_log_entry(
                    state,
                    "步骤已全部执行",
                    {
                        "message": "当前计划中的所有步骤已执行完毕，等待反思节点决策", 
                        "steps_completed": True,
                        "executed_steps_count": state["executed_steps_count"],
                        "executed_steps": state["executed_steps"],
                        "total_steps": len(plan)
                    }
                )
                
                # 记录节点执行完成
                execution_time = time.time() - start_time
                log_node_exit("execution", state_id, execution_time, {
                    "status": "completed",
                    "reason": "all_steps_completed",
                    "execution_time": f"{execution_time:.4f}秒",
                    "steps_completed": True,
                    "executed_steps_count": state["executed_steps_count"],
                    "executed_steps": state["executed_steps"],
                    "total_steps": len(plan),
                    "completion_ratio": f"{state['executed_steps_count']}/{len(plan)}",
                    "is_complete": state.get("is_complete", False)  # 保留原始的完成状态
                })
                
                return state
            
            # 获取当前步骤详情
            current_step_details = plan[current_step]
            
            # 检查步骤中是否包含推荐工具信息
            step_tool_info = None
            if isinstance(current_step_details, dict) and "tool" in current_step_details:
                step_tool_info = current_step_details.get("tool")
                self._add_log_entry(
                    state,
                    "步骤包含工具信息",
                    {
                        "step": current_step,
                        "tool_info": step_tool_info
                    }
                )
            
            # 记录当前步骤信息
            self._add_log_entry(
                state,
                f"执行步骤 {current_step+1}/{len(plan)}",
                {
                    "current_step": current_step,
                    "total_steps": len(plan),
                    "executed_steps_count": state["executed_steps_count"],
                    "executed_steps": state["executed_steps"],
                    "missed_steps": state["missed_steps"],
                    "step_details": current_step_details,
                    "has_tool_info": step_tool_info is not None
                }
            )
            
            # 准备执行当前步骤所需的上下文
            tools_description, _ = self._get_available_tools_description()
            
            # 准备执行上下文
            context = state.get("context", {})
            context_description = json.dumps(context, ensure_ascii=False, indent=2)
            
            # 准备执行日志
            execution_log = state.get("execution_log", [])
            if len(execution_log) > 5:
                execution_log = execution_log[-5:]  # 只保留最近的5条日志
            execution_log_description = json.dumps(execution_log, ensure_ascii=False, indent=2)
            
            # 准备已执行的行动
            action_taken = state.get("action_taken", [])
            if len(action_taken) > 3:
                action_taken = action_taken[-3:]  # 只保留最近的3条行动
            action_taken_description = json.dumps(action_taken, ensure_ascii=False, indent=2)
            
            # 记录准备执行LLM调用
            llm_call_start_time = time.time()
            self._add_log_entry(
                state,
                "准备执行LLM调用",
                {
                    "current_step": current_step,
                    "context_keys": list(context.keys()),
                    "execution_log_length": len(execution_log),
                    "action_taken_length": len(action_taken)
                }
            )
            
            # 执行当前步骤
            try:
                execution_result = await self.chain.ainvoke({
                    "user_input": state.get("user_input", ""),
                    "intent": json.dumps(state.get("intent", {}), ensure_ascii=False, indent=2),
                    "plan": json.dumps(plan, ensure_ascii=False, indent=2),
                    "current_step": current_step + 1,  # 1-indexed for human readability
                    "current_step_details": json.dumps(current_step_details, ensure_ascii=False, indent=2),
                    "context": context_description,
                    "execution_log": execution_log_description,
                    "action_taken": action_taken_description,
                    "available_tools": tools_description
                })
                
                # 计算LLM调用执行时间
                llm_execution_time = time.time() - llm_call_start_time
                
                # 记录LLM调用成功
                self._add_log_entry(
                    state,
                    "LLM调用成功",
                    {
                        "execution_time": f"{llm_execution_time:.4f}秒",
                        "result_keys": list(execution_result.keys())
                    }
                )
                
                # 增加已执行步骤计数
                state["executed_steps_count"] += 1
                
                # 记录已执行的步骤
                if current_step not in state["executed_steps"]:
                    state["executed_steps"].append(current_step)
                
                # 如果这是之前遗漏的步骤，从遗漏列表中移除
                if current_step in state["missed_steps"]:
                    state["missed_steps"].remove(current_step)
                    self._add_log_entry(
                        state,
                        "已执行遗漏步骤",
                        {
                            "step": current_step,
                            "remaining_missed_steps": len(state["missed_steps"]),
                            "message": f"成功执行之前遗漏的步骤 {current_step + 1}"
                        }
                    )
                
            except Exception as e:
                # 计算LLM调用执行时间
                llm_execution_time = time.time() - llm_call_start_time
                
                # 记录LLM调用失败
                error_message = str(e)
                self._add_log_entry(
                    state,
                    "LLM调用失败",
                    {
                        "execution_time": f"{llm_execution_time:.4f}秒",
                        "error": error_message
                    }
                )
                
                # 记录详细错误日志
                log_error(
                    "execution",
                    "LLM调用失败",
                    {
                        "step": current_step,
                        "execution_time": f"{llm_execution_time:.4f}秒",
                        "error": error_message
                    }
                )
                
                # 创建基本的执行结果
                execution_result = {
                    "action_taken": f"执行步骤 {current_step+1} 时出错: {error_message}",
                    "result": f"执行出错: {error_message}",
                    "requires_tool": False,
                    "tool_calls": [],
                    "next_step": current_step + 1,  # 保持在当前步骤
                    "is_complete": False
                }
                
                # 记录执行失败的步骤
                if current_step not in state["missed_steps"]:
                    state["missed_steps"].append(current_step)
                    self._add_log_entry(
                        state,
                        "记录遗漏步骤",
                        {
                            "step": current_step,
                            "missed_steps_count": len(state["missed_steps"]),
                            "message": f"步骤 {current_step + 1} 执行失败，标记为遗漏步骤"
                        }
                    )
            
            # 更新状态
            if "action_taken" not in state:
                state["action_taken"] = []
                
            # 添加当前步骤的执行结果
            state["action_taken"].append({
                "step": current_step + 1,
                "action": execution_result.get("action_taken", "未指定动作"),
                "result": execution_result.get("result", "未返回结果")
            })
            
            # 判断是否需要工具调用
            requires_tool = execution_result.get("requires_tool", False)
            if requires_tool:
                tool_calls = execution_result.get("tool_calls", [])
                
                # 记录要请求的工具调用
                self._add_log_entry(
                    state,
                    "需要工具调用",
                    {
                        "tool_calls_count": len(tool_calls),
                        "tools": [call.get("name") for call in tool_calls]
                    }
                )
                
                # 设置工具调用
                state["tool_calls"] = tool_calls
            else:
                # 清除可能存在的工具调用请求
                state["tool_calls"] = []
                
                # 记录不需要工具调用
                self._add_log_entry(
                    state,
                    "不需要工具调用",
                    {
                        "message": "当前步骤不需要调用工具"
                    }
                )
            
            # 检查是否有遗漏步骤需要先执行
            if "missed_steps_to_execute" in state and state["missed_steps_to_execute"]:
                # 如果还有遗漏步骤需要执行，那么下一步就是第一个遗漏步骤
                next_step = state["missed_steps_to_execute"][0]
                
                self._add_log_entry(
                    state,
                    "继续执行遗漏步骤",
                    {
                        "next_step": next_step,
                        "remaining_missed_steps": len(state["missed_steps_to_execute"]),
                        "message": f"下一步将执行遗漏步骤 {next_step + 1}"
                    }
                )
                
                # 更新下一步
                state["current_step"] = next_step
            else:
                # 根据执行结果更新下一步
                next_step = execution_result.get("next_step", current_step + 1)
                if next_step == -1:  # 表示任务完成
                    state["is_complete"] = True
                    if "final_output" in execution_result:
                        state["final_output"] = execution_result["final_output"]
                        
                    # 记录任务完成
                    self._add_log_entry(
                        state,
                        "任务标记为完成",
                        {
                            "final_output": execution_result.get("final_output", "无最终输出"),
                            "executed_steps_count": state["executed_steps_count"],
                            "executed_steps": state["executed_steps"],
                            "total_steps": len(plan)
                        }
                    )
                else:
                    # 更新下一步
                    state["current_step"] = next_step
                    
                    # 记录下一步更新
                    self._add_log_entry(
                        state,
                        "更新下一步",
                        {
                            "current_step": current_step,
                            "next_step": next_step,
                            "executed_steps_count": state["executed_steps_count"],
                            "executed_steps": state["executed_steps"],
                            "missed_steps": state["missed_steps"]
                        }
                    )
            
            # 检查是否完成 - 基于执行的步骤数而不仅仅是当前步骤索引
            is_complete = execution_result.get("is_complete", False)
            # 计算执行率
            execution_ratio = state["executed_steps_count"] / len(plan) if plan else 0
            
            # 计算未执行步骤
            all_steps = set(range(len(plan)))
            executed_steps_set = set(state["executed_steps"])
            unexecuted_steps = list(all_steps - executed_steps_set)
            
            # 检查是否有遗漏步骤
            if unexecuted_steps and not state.get("is_complete", False):
                # 记录遗漏步骤
                state["missed_steps"] = unexecuted_steps
                self._add_log_entry(
                    state,
                    "记录未执行步骤",
                    {
                        "unexecuted_steps": unexecuted_steps,
                        "message": f"检测到 {len(unexecuted_steps)} 个步骤未执行"
                    }
                )
                
                # 如果有遗漏步骤但is_complete标志为true，取消完成标记，等待所有步骤完成
                if is_complete:
                    is_complete = False
                    self._add_log_entry(
                        state,
                        "取消完成标记",
                        {
                            "reason": "存在未执行步骤，需要全部执行完成才能标记为完成",
                            "unexecuted_steps": unexecuted_steps,
                            "unexecuted_steps_count": len(unexecuted_steps)
                        }
                    )
            
            # 只有当所有步骤都已执行完成时，才考虑标记为完成
            if is_complete or (execution_ratio == 1.0 and not unexecuted_steps):
                # 只有在没有遗漏步骤的情况下才标记为完成
                state["is_complete"] = True
                if "final_output" in execution_result:
                    state["final_output"] = execution_result["final_output"]
                
                # 记录任务完成
                completion_reason = "is_complete标志为true且没有遗漏步骤"
                if execution_ratio == 1.0 and not unexecuted_steps:
                    completion_reason = f"已执行{state['executed_steps_count']}/{len(plan)}步骤，达到100%完成率"
                
                self._add_log_entry(
                    state,
                    "任务标记为完成",
                    {
                        "reason": completion_reason,
                        "executed_steps_count": state["executed_steps_count"],
                        "executed_steps": state["executed_steps"],
                        "missed_steps": state["missed_steps"],
                        "total_steps": len(plan),
                        "execution_ratio": f"{execution_ratio:.2f}",
                        "final_output": execution_result.get("final_output", "无最终输出")
                    }
                )
            
            # 记录节点执行完成
            execution_time = time.time() - start_time
            log_node_exit("execution", state_id, execution_time, {
                "status": "completed",
                "current_step": current_step,
                "next_step": state.get("current_step", current_step),
                "executed_steps_count": state["executed_steps_count"],
                "executed_steps": state["executed_steps"],
                "missed_steps": state["missed_steps"],
                "total_steps": len(plan),
                "execution_ratio": f"{execution_ratio:.2f}" if plan else "0.00",
                "requires_tool": requires_tool,
                "is_complete": state.get("is_complete", False),
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            return state
            
        except Exception as e:
            # 记录未捕获的异常
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "execution",
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
                "execution",
                "节点执行过程中发生未捕获的异常",
                {
                    "error": error_message
                }
            )
            
            # 记录节点执行完成（错误）
            execution_time = time.time() - start_time
            log_node_exit("execution", state_id, execution_time, {
                "status": "error",
                "error": error_message,
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            return state 