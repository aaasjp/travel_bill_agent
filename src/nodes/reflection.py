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
        
        # 定义反思提示模板
        self.reflection_prompt = ChatPromptTemplate.from_template("""你是一个人工智能助手的反思组件。
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
{current_results}

## 工具调用历史
{tool_call_history}

## 历史错误信息
{errors}

请反思当前执行情况，并返回以下JSON格式的评估结果：

```json
{{
    "success_aspects": ["方面1", "方面2"],  // 成功完成的方面
    "missing_aspects": ["方面3"],  // 未完成或需改进的方面
    "action": "replan|waiting_for_human|end",  // 下一步行动：重新规划、人工干预或结束
    "rationale": "反思理由说明",
    "summary_output": "对当前反思结果的总结性输出"
}}
```""")
        
        # 定义反思结果解析器
        self.parser = JsonOutputParser()
        
        # 构建反思链
        self.chain = self.reflection_prompt | self.llm | self.parser
    
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
            # 设置created_at时间戳（如果不存在）
            if "created_at" not in state:
                from datetime import datetime
                state["created_at"] = datetime.now()
            
            # 准备反思输入
            current_results = state.get("current_results")
            if current_results is None:
                results_for_reflection = "暂无执行结果"
            else:
                results_for_reflection = json.dumps(current_results, ensure_ascii=False, indent=2)
                
            inputs = {
                "user_input": state["user_input"],
                "intent": state.get("intent", {}),
                "plan": state.get("plan", []),
                "execution_log": state.get("execution_log", []),
                "current_results": results_for_reflection,
                "tool_call_history": json.dumps(state.get("completed_tools", []), ensure_ascii=False, indent=2),
                "errors": state.get("errors", [])
            }
            
            # 执行反思分析
            reflection_result = await self.chain.ainvoke(inputs)
            
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