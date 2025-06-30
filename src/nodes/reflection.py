from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import time
import json
import uuid

from ..states.state import State
from ..llm import get_llm
from .human_intervention import InterventionType, InterventionPriority, NotificationChannel

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
        
        # 定义反思结果解析器
        self.parser = JsonOutputParser()
    
    def _get_reflection_prompt(self) -> ChatPromptTemplate:
        """获取反思提示模板
        
        Returns:
            反思提示模板
        """
        return ChatPromptTemplate.from_messages([
            ("system", """你是一个人工智能助手的反思组件。你的任务是分析当前任务的执行情况，评估完成度，并决定下一步操作。"""),
            ("user", """
            【用户原始输入】: {user_input}
            
            【用户信息】: {user_info}
            
            【用户记忆】: {user_memories}
            
            【对话历史】: {conversation_history}
            
            【当前意图理解】: {intent}
            
            【执行计划】: {plan}
            
            【执行日志】: {execution_log}
            
            【当前结果】: {current_results}
            
            【工具调用历史】: {tool_call_history}
            
            【历史错误信息】: {errors}
            
            【人工干预请求】: {intervention_request}
            
            【人工反馈结果】: {human_feedback}
            
            请反思当前执行情况，分析以下方面：
            1. 成功完成的方面
            2. 未完成或需要改进的方面
            3. 是否存在错误或异常
            4. 是否需要人工干预
            5. 下一步应该采取的行动
            
            在分析时，请考虑：
            1. 用户原始需求是否得到满足
            2. 执行计划是否按预期进行
            3. 工具调用是否成功
            4. 是否有错误需要处理
            5. 是否需要额外的信息或权限
            6. 人工干预的结果和建议
            
            请返回以下JSON格式的评估结果：

            {{
                "success_aspects": ["方面1", "方面2"],  // 成功完成的方面
                "missing_aspects": ["方面3"],  // 未完成或需改进的方面
                "action": "replan|waiting_for_human|end",  // 下一步行动：重新规划、人工干预或结束
                "rationale": "反思理由说明",
                "summary_output": "对当前反思结果的总结性输出"
            }}
            """)
        ])
    
    def _format_user_info(self, state: State) -> str:
        """格式化用户信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的用户信息字符串
        """
        try:
            user_info = state.get("user_info", {})
            if not user_info:
                return "无用户信息"
            
            # 格式化用户信息
            info_text = "用户信息：\n"
            for key, value in user_info.items():
                info_text += f"{key}: {value}\n"
            
            return info_text
        except Exception as e:
            return f"用户信息格式化出错: {str(e)}"
    
    def _format_user_memories(self, state: State) -> str:
        """格式化用户记忆信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的记忆信息字符串
        """
        try:
            # 获取用户记忆
            memory_records = state.get("memory_records", [])
            if not memory_records:
                return "无相关记忆信息"
            
            # 格式化记忆信息
            memories_text = "用户记忆信息：\n"
            for i, memory in enumerate(memory_records[:5]):  # 限制显示前5条记忆
                memories_text += f"{i+1}. {memory.get('name', '未命名')}: {memory.get('content', '无内容')}\n"
            
            return memories_text
        except Exception as e:
            return f"记忆信息格式化出错: {str(e)}"
    
    def _format_conversation_history(self, state: State) -> str:
        """格式化对话历史
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的对话历史字符串
        """
        try:
            messages = state.get("messages", [])
            if not messages:
                return "无对话历史"
            
            # 格式化对话历史
            history_text = "对话历史：\n"
            for i, message in enumerate(messages[-10:]):  # 显示最近10条消息
                role = message.get("role", "unknown")
                content = message.get("content", "")
                history_text += f"{role}: {content}\n"
            
            return history_text
        except Exception as e:
            return f"对话历史格式化出错: {str(e)}"
    
    def _format_execution_log(self, state: State) -> str:
        """格式化执行日志
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的执行日志字符串
        """
        try:
            execution_log = state.get("execution_log", [])
            if not execution_log:
                return "无执行日志"
            
            # 格式化执行日志
            log_text = "执行日志：\n"
            for i, log_entry in enumerate(execution_log[-10:]):  # 显示最近10条日志
                node = log_entry.get("node", "unknown")
                action = log_entry.get("action", "")
                timestamp = log_entry.get("timestamp", "")
                log_text += f"{i+1}. [{node}] {action} (时间: {timestamp})\n"
            
            return log_text
        except Exception as e:
            return f"执行日志格式化出错: {str(e)}"
    
    def _format_current_results(self, state: State) -> str:
        """格式化当前结果
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的当前结果字符串
        """
        try:
            current_results = state.get("current_results")
            if current_results is None:
                return "暂无执行结果"
            
            # 如果已经是字符串格式，直接返回
            if isinstance(current_results, str):
                return f"当前结果：\n{current_results}"
            
            # 如果是字典或列表，转换为JSON格式
            if isinstance(current_results, (dict, list)):
                return f"当前结果：\n{json.dumps(current_results, ensure_ascii=False, indent=2)}"
            
            # 其他情况，转换为字符串
            return f"当前结果：\n{str(current_results)}"
        except Exception as e:
            return f"当前结果格式化出错: {str(e)}"
    
    def _format_tool_call_history(self, state: State) -> str:
        """格式化工具调用历史
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的工具调用历史字符串
        """
        try:
            completed_tools = state.get("completed_tools", [])
            if not completed_tools:
                return "无工具调用历史"
            
            # 格式化工具调用历史
            history_text = "工具调用历史：\n"
            for i, tool_call in enumerate(completed_tools[-10:]):  # 显示最近10次工具调用
                tool_name = tool_call.get("tool_name", "unknown")
                parameters = tool_call.get("parameters", {})
                result = tool_call.get("result", {})
                status = tool_call.get("status", "unknown")
                history_text += f"{i+1}. {tool_name} (状态: {status})\n"
                history_text += f"   参数: {json.dumps(parameters, ensure_ascii=False, indent=2)}\n"
                history_text += f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n"
            
            return history_text
        except Exception as e:
            return f"工具调用历史格式化出错: {str(e)}"
    
    def _format_errors(self, state: State) -> str:
        """格式化错误信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的错误信息字符串
        """
        try:
            errors = state.get("errors", [])
            if not errors:
                return "无错误信息"
            
            # 格式化错误信息
            errors_text = "历史错误信息：\n"
            for i, error in enumerate(errors[-5:]):  # 显示最近5条错误
                node = error.get("node", "unknown")
                error_msg = error.get("error", "")
                error_type = error.get("error_type", "")
                timestamp = error.get("timestamp", "")
                errors_text += f"{i+1}. [{node}] {error_type}: {error_msg} (时间: {timestamp})\n"
            
            return errors_text
        except Exception as e:
            return f"错误信息格式化出错: {str(e)}"
    
    def _format_intervention_request(self, state: State) -> str:
        """格式化人工干预请求
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的干预请求字符串
        """
        try:
            intervention_request = state.get("intervention_request", {})
            if not intervention_request:
                return "无人工干预请求"
            
            # 如果已经是字符串格式，直接返回
            if isinstance(intervention_request, str):
                return f"人工干预请求：\n{intervention_request}"
            
            # 如果是字典或列表，转换为JSON格式
            if isinstance(intervention_request, (dict, list)):
                return f"人工干预请求：\n{json.dumps(intervention_request, ensure_ascii=False, indent=2)}"
            
            # 其他情况，转换为字符串
            return f"人工干预请求：\n{str(intervention_request)}"
        except Exception as e:
            return f"人工干预请求格式化出错: {str(e)}"
    
    def _format_human_feedback(self, state: State) -> str:
        """格式化人工反馈结果
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的反馈结果字符串
        """
        try:
            human_feedback = state.get("human_feedback", {})
            if not human_feedback:
                return "无人工反馈结果"
            
            # 如果已经是字符串格式，直接返回
            if isinstance(human_feedback, str):
                return f"人工反馈结果：\n{human_feedback}"
            
            # 如果是字典或列表，转换为JSON格式
            if isinstance(human_feedback, (dict, list)):
                return f"人工反馈结果：\n{json.dumps(human_feedback, ensure_ascii=False, indent=2)}"
            
            # 其他情况，转换为字符串
            return f"人工反馈结果：\n{str(human_feedback)}"
        except Exception as e:
            return f"人工反馈结果格式化出错: {str(e)}"
    
    def _create_intervention_request_for_reflection(self, state: State, reflection_result: Dict[str, Any]) -> Dict[str, Any]:
        """为反思结果创建人工干预请求
        
        Args:
            state: 当前状态
            reflection_result: 反思结果
            
        Returns:
            人工干预请求对象
        """
        # 确定介入类型
        intervention_type = self._determine_intervention_type(state, reflection_result)
        
        # 确定介入优先级
        intervention_priority = self._determine_intervention_priority(state, intervention_type)
        
        # 创建干预请求对象
        intervention_request = {
            "intervention_id": str(uuid.uuid4()),
            "intervention_type": intervention_type,
            "intervention_priority": intervention_priority,
            "request_source": "reflection_node",  # 请求来源：反思节点
            "notification_channels": [NotificationChannel.SYSTEM],  # 使用系统通知
            "timeout": 3600,  # 1小时
            "timestamp": time.time(),
            "status": "pending",
            "meta_data": {
                "task_id": state.get("task_id", "unknown"),
                "user_input": state.get("user_input", ""),
                "reflection_result": reflection_result,
                "execution_log": state.get("execution_log", []),
                "errors": state.get("errors", [])
            }
        }
        
        return intervention_request
    
    def _determine_intervention_type(self, state: State, reflection_result: Dict[str, Any]) -> InterventionType:
        """确定介入类型
        
        Args:
            state: 当前状态
            reflection_result: 反思结果
            
        Returns:
            介入类型
        """
        # 检查 current_results 中是否有错误
        current_results = state.get("current_results")
        if current_results:
            # 检查 current_results 是否包含错误信息
            if isinstance(current_results, dict):
                # 检查常见的错误字段
                error_fields = ["error", "errors", "exception", "failure", "failed", "status"]
                for field in error_fields:
                    if field in current_results:
                        error_value = current_results[field]
                        if error_value and error_value != "success" and error_value != "completed":
                            return InterventionType.EXCEPTION_HANDLING
                
                # 检查是否有错误状态
                if "status" in current_results and current_results["status"] in ["error", "failed", "exception"]:
                    return InterventionType.EXCEPTION_HANDLING
            elif isinstance(current_results, str):
                # 如果是字符串，检查是否包含错误关键词
                error_keywords = ["错误", "失败", "异常", "error", "failed", "exception", "失败"]
                if any(keyword in current_results for keyword in error_keywords):
                    return InterventionType.EXCEPTION_HANDLING
        
        # 检查是否需要额外信息
        missing_aspects = reflection_result.get("missing_aspects", [])
        if missing_aspects:
            return InterventionType.INFO_SUPPLEMENT
        
        # 检查是否需要权限授予
        rationale = reflection_result.get("rationale", "")
        user_input = state.get("user_input", "")
        
        # 权限相关关键词检查
        permission_keywords = ["权限", "授权", "批准", "审批", "同意", "许可", "允许", "授权人", "主管", "领导"]
        if any(keyword in rationale for keyword in permission_keywords):
            return InterventionType.PERMISSION_GRANT
        
        # 参数相关关键词检查
        parameter_keywords = ["参数", "parameters", "parameter"]
        if any(keyword in rationale for keyword in parameter_keywords):
            return InterventionType.PARAMETER_PROVIDER
        
        # 检查是否需要重要决策确认
        if "重复" in rationale or "循环" in rationale or "无法确定" in rationale:
            return InterventionType.DECISION_CONFIRMATION
        
        # 默认为补充信息
        return InterventionType.INFO_SUPPLEMENT
    
    def _determine_intervention_priority(self, state: State, intervention_type: InterventionType) -> InterventionPriority:
        """确定介入优先级
        
        Args:
            state: 当前状态
            intervention_type: 介入类型
            
        Returns:
            介入优先级
        """
        # 检查 current_results 中是否有严重错误
        current_results = state.get("current_results")
        if current_results:
            if isinstance(current_results, dict):
                # 检查是否有严重错误状态
                if "status" in current_results and current_results["status"] in ["error", "failed", "exception"]:
                    return InterventionPriority.URGENT
                
                # 检查错误信息中是否包含严重关键词
                for field in ["error", "errors", "exception", "failure", "failed"]:
                    if field in current_results:
                        error_msg = str(current_results[field])
                        if any(kw in error_msg for kw in ["资金", "安全", "异常", "严重", "失败", "紧急", "critical", "urgent"]):
                            return InterventionPriority.URGENT
            elif isinstance(current_results, str):
                # 如果是字符串，检查是否包含严重错误关键词
                urgent_keywords = ["资金", "安全", "异常", "严重", "失败", "紧急", "critical", "urgent"]
                if any(kw in current_results for kw in urgent_keywords):
                    return InterventionPriority.URGENT
        
        # 检查是否涉及资金安全或严重错误
        for error in state.get("errors", []):
            error_msg = str(error.get("error", ""))
            if any(kw in error_msg for kw in ["资金", "安全", "异常", "严重", "失败"]):
                return InterventionPriority.URGENT
        
        # 根据介入类型确定基础优先级
        type_priority_map = {
            InterventionType.EXCEPTION_HANDLING: InterventionPriority.IMPORTANT,
            InterventionType.PERMISSION_GRANT: InterventionPriority.IMPORTANT,
            InterventionType.PARAMETER_PROVIDER: InterventionPriority.NORMAL,
            InterventionType.DECISION_CONFIRMATION: InterventionPriority.NORMAL,
            InterventionType.INFO_SUPPLEMENT: InterventionPriority.NORMAL
        }
        
        base_priority = type_priority_map.get(intervention_type, InterventionPriority.NORMAL)
        
        return base_priority
    
    async def __call__(self, state: State) -> State:
        """执行反思操作
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            print("--------------------------------反思节点开始执行--------------------------------")
            # 设置created_at时间戳（如果不存在）
            if "created_at" not in state:
                from datetime import datetime
                state["created_at"] = datetime.now()
            
            # 准备反思所需的上下文
            user_info = self._format_user_info(state)
            user_memories = self._format_user_memories(state)
            conversation_history = self._format_conversation_history(state)
            execution_log = self._format_execution_log(state)
            current_results = self._format_current_results(state)
            tool_call_history = self._format_tool_call_history(state)
            errors = self._format_errors(state)
            intervention_request = self._format_intervention_request(state)
            human_feedback = self._format_human_feedback(state)
            
            # 获取反思提示模板
            prompt = self._get_reflection_prompt()
            
            # 准备输入
            inputs = {
                "user_input": state.get("user_input", ""),
                "user_info": user_info,
                "user_memories": user_memories,
                "conversation_history": conversation_history,
                "intent": json.dumps(state.get("intent", {}), ensure_ascii=False, indent=2),
                "plan": json.dumps(state.get("plan", []), ensure_ascii=False, indent=2),
                "execution_log": execution_log,
                "current_results": current_results,
                "tool_call_history": tool_call_history,
                "errors": errors,
                "intervention_request": intervention_request,
                "human_feedback": human_feedback
            }
            
            # 执行反思分析
            print(f"【REFLECTION PROMPT】:\n{prompt.format_messages(**inputs)}")
            response = await self.llm.ainvoke(prompt.format_messages(**inputs))
            response_text = response.content
            print(f"【REFLECTION RESPONSE】:\n{response_text}")
            
            # 解析反思结果
            try:
                reflection_result = self.parser.parse(response_text)
            except Exception as e:
                import traceback
                traceback.print_exc()
                # 如果解析失败，创建默认的反思结果
                reflection_result = {
                    "success_aspects": [],
                    "missing_aspects": ["反思分析失败"],
                    "action": "end",
                    "rationale": f"反思分析失败: {str(e)}",
                    "summary_output": "反思分析出现错误，建议结束流程"
                }
            
            # 更新状态
            # 添加时间戳到reflection_result
            reflection_result["timestamp"] = str(time.time())
            state["reflection_result"] = reflection_result
            
            # 检查是否需要人工干预
            action = reflection_result.get("action", "end")
            if action == "waiting_for_human":
                # 创建人工干预请求
                intervention_request = self._create_intervention_request_for_reflection(state, reflection_result)
                state["intervention_request"] = intervention_request
                
                # 记录需要人工干预
                if "execution_log" not in state:
                    state["execution_log"] = []
                state["execution_log"].append({
                    "node": "reflection",
                    "action": "需要人工干预",
                    "timestamp": str(time.time()),
                    "intervention_request": intervention_request
                })
            
            # 使用status存放action用于节点流转
            state["status"] = action
            
            # 更新时间戳
            from datetime import datetime
            state["updated_at"] = datetime.now()    
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # 捕获所有异常并创建默认的反思结果
            error_message = str(e)
            
            # 记录错误
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "reflection",
                "error": error_message,
                "error_type": "reflection_error",
                "timestamp": str(time.time())
            })
            
            state["status"] = "end"
            
            # 更新时间戳
            from datetime import datetime
            state["updated_at"] = datetime.now()
            
            return state 