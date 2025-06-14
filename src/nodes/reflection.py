from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import time
import json

from ..models.state import ExpenseState
from ..config import get_llm

class ReflectionNode:
    """
    反思节点，用于评估执行结果并决定后续行动。
    
    这个节点会分析当前状态，评估任务完成度，决定是需要重新规划、继续执行还是结束流程。
    它提供了一种自我评估和校正的机制，使工作流能够更智能地处理复杂任务。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化反思节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        
        # 定义反思提示模板
        self.reflection_prompt = ChatPromptTemplate.from_template("""你是一个专业的差旅报销助手的反思组件。
请分析当前任务的执行情况，评估完成度，并决定下一步操作。

## 用户原始输入
{user_input}

## 当前意图理解
{intent}

## 执行计划
{plan}

## 执行日志
{execution_log}

## 当前结果
{results}

## 工具调用历史
{tool_call_history}

## 错误信息（如有）
{errors}

## 任务完成率
{task_completion_rate}

请特别注意检查是否存在重复调用相同工具、使用相同参数的情况。如果发现重复调用相同工具且没有实质性进展，这可能表明需要转向不同的行动，或者认为任务已经完成。
另外需要注意 任务完成率必须达到100% 才能结束任务
请反思当前执行情况，并返回以下JSON格式的评估结果：

```json
{{
    "task_completion_rate": 0.85,  // 任务完成度，0-1之间的数值
    "success_aspects": ["方面1", "方面2"],  // 成功完成的方面
    "missing_aspects": ["方面3"],  // 未完成或需改进的方面
    "detected_repetition": true/false,  // 是否检测到重复调用工具
    "action": "replan|continue|end",  // 下一步行动：重新规划、继续执行或结束
    "rationale": "决策理由说明",
    "final_output": "如果任务已完成，提供最终输出内容"
}}
```""")
        
        # 定义反思结果解析器
        self.parser = JsonOutputParser()
        
        # 构建反思链
        self.chain = self.reflection_prompt | self.llm | self.parser
    
    def _analyze_tool_call_history(self, state: ExpenseState) -> Dict[str, Any]:
        """分析工具调用历史，检测重复模式
        
        Args:
            state: 当前状态
            
        Returns:
            分析结果
        """
        # 获取工具调用历史
        tool_results = state.get("tool_results", {})
        execution_log = state.get("execution_log", [])
        
        # 提取工具调用记录
        tool_calls = []
        for entry in execution_log:
            if entry.get("node") == "tool_execution" and entry.get("action", "").startswith("调用工具:"):
                tool_name = entry.get("details", {}).get("tool")
                parameters = entry.get("details", {}).get("parameters", {})
                if tool_name and parameters:
                    tool_calls.append({
                        "tool": tool_name,
                        "parameters": parameters,
                        "timestamp": entry.get("timestamp")
                    })
        
        # 检测重复模式
        repetition_detected = False
        repetition_count = 0
        last_tool = None
        last_params = None
        repeated_tools = []
        
        for call in tool_calls:
            tool = call["tool"]
            params = json.dumps(call["parameters"], sort_keys=True)
            
            if tool == last_tool and params == last_params:
                repetition_count += 1
                if repetition_count >= 2 and tool not in repeated_tools:
                    repeated_tools.append(tool)
                    repetition_detected = True
            else:
                repetition_count = 0
            
            last_tool = tool
            last_params = params
        
        return {
            "tool_call_count": len(tool_calls),
            "repetition_detected": repetition_detected,
            "repeated_tools": repeated_tools
        }
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行反思操作
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 分析工具调用历史
            tool_history_analysis = self._analyze_tool_call_history(state)
            
            # 如果检测到重复调用工具且至少循环了3次，强制结束任务
            if tool_history_analysis["repetition_detected"] and tool_history_analysis["tool_call_count"] >= 6:
                # 创建反思结果
                reflection_result = {
                    "success_aspects": ["成功创建了报销单"],
                    "missing_aspects": ["可能有部分细节未完善"],
                    "detected_repetition": True,
                    "action": "end",
                    "rationale": "检测到重复调用相同工具，表明当前流程已经无法取得更多进展，认为任务已基本完成。",
                    "final_output": f"已完成报销单创建。最后一次工具调用的结果是: {json.dumps(state.get('tool_results', {}).get(tool_history_analysis['repeated_tools'][0], {}).get('result', {}), ensure_ascii=False)}"
                }
                
                # 更新状态
                state["reflection_result"] = reflection_result
                state["final_output"] = reflection_result["final_output"]
                
                # 更新反思记录
                if "reflection" not in state:
                    state["reflection"] = {}
                    
                state["reflection"] = {
                    "success_aspects": reflection_result["success_aspects"],
                    "missing_aspects": reflection_result["missing_aspects"],
                    "action": reflection_result["action"],
                    "detected_repetition": True,
                    "timestamp": str(state.get("updated_at", time.time()))
                }
                
                return state
            
            # 准备反思输入
            inputs = {
                "user_input": state["user_input"],
                "intent": state.get("intent", {}),
                "plan": state.get("plan", []),
                "execution_log": state.get("execution_log", []),
                "results": state.get("results", {}),
                "tool_call_history": json.dumps(tool_history_analysis, ensure_ascii=False, indent=2),
                "errors": state.get("errors", []),
                "task_completion_rate": state.get("reflection", {}).get("task_completion_rate", 0)
            }
            
            # 执行反思分析
            try:
                reflection_result = await self.chain.ainvoke(inputs)
                
                # 检查是否检测到重复
                detected_repetition = reflection_result.get("detected_repetition", False)
                
                # 检查已执行步骤数量与任务完成度的关系
                if "executed_steps_count" in state and "plan" in state and state["plan"]:
                    total_steps = len(state["plan"])
                    executed_steps = state["executed_steps_count"]
                    execution_ratio = executed_steps / total_steps if total_steps > 0 else 0
                    
                    # 如果有执行步骤列表，检查是否有遗漏步骤
                    if "executed_steps" in state:
                        executed_steps_set = set(state["executed_steps"])
                        all_steps = set(range(total_steps))
                        missed_steps = list(all_steps - executed_steps_set)
                        
                        # 无论执行率如何，只要有遗漏步骤，就安排重新执行
                        if missed_steps and reflection_result.get("action") != "end":
                            # 更新遗漏步骤列表
                            state["missed_steps"] = missed_steps
                            
                            # 安排重新执行遗漏步骤
                            state["missed_steps_to_execute"] = missed_steps
                            
                            # 修改反思结果
                            original_action = reflection_result.get("action", "continue")
                            reflection_result["action"] = "continue"  # 继续执行遗漏步骤
                            
                            # 添加未执行步骤到missing_aspects
                            missing_step_descriptions = []
                            for step_idx in missed_steps:
                                if step_idx < len(state["plan"]):
                                    step_info = state["plan"][step_idx]
                                    step_desc = f"步骤 {step_idx + 1}: {json.dumps(step_info, ensure_ascii=False)[:100]}..."
                                    missing_step_descriptions.append(step_desc)
                            
                            if "missing_aspects" not in reflection_result:
                                reflection_result["missing_aspects"] = []
                            
                            # 添加遗漏步骤说明
                            for desc in missing_step_descriptions:
                                if desc not in reflection_result["missing_aspects"]:
                                    reflection_result["missing_aspects"].append(desc)
                            
                            # 更新理由
                            reflection_result["rationale"] = f"检测到 {len(missed_steps)} 个步骤尚未执行，需要重新执行这些步骤以确保任务完整性。要求所有步骤都必须执行完成才能标记任务为完成。" + (reflection_result.get("rationale", "") or "")
                            
                            # 调整任务完成率，确保未执行所有步骤时完成率不会达到100%
                            if reflection_result.get("task_completion_rate", 0) > 0.95:
                                # 根据未执行步骤比例调整完成率
                                missed_ratio = len(missed_steps) / total_steps
                                adjusted_rate = max(0.5, 1.0 - missed_ratio) 
                                reflection_result["task_completion_rate"] = adjusted_rate
                        
                        # 如果没有遗漏步骤且执行率为100%，考虑将完成率调整为100%
                        elif not missed_steps and execution_ratio == 1.0 and reflection_result.get("task_completion_rate", 0) < 1.0:
                            reflection_result["task_completion_rate"] = 1.0
                    
                    # 如果执行率超过80%，但完成率评估低于0.7，调整完成率但不超过0.9
                    if execution_ratio >= 0.8 and reflection_result.get("task_completion_rate", 0) < 0.7:
                        original_rate = reflection_result.get("task_completion_rate", 0)
                        # 根据执行率调整完成率，但最高不超过0.9
                        adjusted_rate = min(0.9, max(original_rate, 0.7))
                        reflection_result["task_completion_rate"] = adjusted_rate
                    
                    # 如果已执行全部步骤且评估为replan，检查完成率
                    if state.get("steps_completed", False) and reflection_result.get("action") == "replan":
                        # 检查是否有遗漏步骤
                        if "missed_steps" in state and state["missed_steps"]:
                            # 如果有遗漏步骤，而且没有安排执行，安排执行
                            if "missed_steps_to_execute" not in state or not state["missed_steps_to_execute"]:
                                state["missed_steps_to_execute"] = state["missed_steps"]
                                original_action = reflection_result["action"]
                                reflection_result["action"] = "continue"
                                reflection_result["rationale"] = f"虽然计划步骤已全部执行过，但仍有 {len(state['missed_steps'])} 个步骤未执行或需要重新执行，安排执行这些遗漏步骤。原建议为'{original_action}'。"
                        else:
                            # 所有步骤都已执行，检查完成率是否达到100%
                            completion_rate = reflection_result.get("task_completion_rate", 0)
                            if completion_rate >= 0.99:  # 允许0.99以上视为100%
                                # 检查是否有明确的缺失方面
                                missing_aspects = reflection_result.get("missing_aspects", [])
                                if not missing_aspects or all(aspect.startswith("可能") for aspect in missing_aspects):
                                    original_action = reflection_result["action"]
                                    reflection_result["action"] = "end"
                                    reflection_result["rationale"] = f"已执行全部计划步骤，完成率达到{completion_rate}，无明确缺失方面，可以结束任务。原建议为'{original_action}'。"
                                    
                                    # 如果没有最终输出，生成一个
                                    if "final_output" not in reflection_result or not reflection_result["final_output"]:
                                        reflection_result["final_output"] = f"已完成任务，执行了{executed_steps}/{total_steps}个步骤，完成率{completion_rate:.2f}。"
            except Exception as parse_error:
                # 捕获反思分析过程中的错误
                parse_error_message = str(parse_error)
                
                # 创建默认的反思结果
                action = "replan" if state.get("steps_completed", False) else "continue"
                
                reflection_result = {
                    "task_completion_rate": 0.5,  # 默认值
                    "success_aspects": ["部分任务已完成"],
                    "missing_aspects": ["由于反思组件错误，无法详细分析缺失部分"],
                    "detected_repetition": False,
                    "action": action,
                    "rationale": f"反思分析失败: {parse_error_message}，建议{action}以尝试完成任务",
                    "final_output": None
                }
            
            # 如果检测到重复且建议继续，改为结束任务
            if detected_repetition and reflection_result.get("action") == "continue":
                reflection_result["action"] = "end"
                reflection_result["rationale"] += " 由于检测到重复调用相同工具，决定结束任务。"
                if "final_output" not in reflection_result:
                    # 从最近的工具结果中获取信息
                    tool_results = state.get("tool_results", {})
                    if tool_results:
                        last_tool = list(tool_results.keys())[-1]
                        last_result = tool_results[last_tool].get("result", {})
                        reflection_result["final_output"] = f"已完成报销单创建。最后一次工具调用的结果是: {json.dumps(last_result, ensure_ascii=False)}"
                    else:
                        reflection_result["final_output"] = "已完成报销单创建流程。"
            
            # 更新状态
            state["reflection_result"] = reflection_result
            
            # 如果任务已完成，设置最终输出
            if reflection_result.get("action") == "end" and "final_output" in reflection_result:
                state["final_output"] = reflection_result["final_output"]
            
            # 更新反思记录
            if "reflection" not in state:
                state["reflection"] = {}
                
            state["reflection"] = {
                "task_completion_rate": reflection_result.get("task_completion_rate", 0),
                "success_aspects": reflection_result.get("success_aspects", []),
                "missing_aspects": reflection_result.get("missing_aspects", []),
                "action": reflection_result.get("action", "end"),
                "detected_repetition": reflection_result.get("detected_repetition", False),
                "timestamp": str(state.get("updated_at", time.time()))
            }
            
            return state
            
        except Exception as e:
            # 记录错误
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "reflection",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            return state 