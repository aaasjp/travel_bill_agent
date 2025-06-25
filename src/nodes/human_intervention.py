"""
人工干预节点
用于判断是否需要人工干预，并处理人工反馈
"""
from typing import Dict, Any, Optional, List
import time
import json
import asyncio
from enum import Enum
from datetime import datetime

from ..states.state import State

# 介入优先级枚举
class InterventionPriority(str, Enum):
    """人工介入优先级"""
    URGENT = "urgent"  # 紧急介入（立即通知）
    IMPORTANT = "important"  # 重要介入（工作时间通知）
    NORMAL = "normal"  # 一般介入（批量处理）

# 介入类型枚举
class InterventionType(str, Enum):
    """人工介入类型"""
    INFO_SUPPLEMENT = "info_supplement"  # 信息补充型
    DECISION_CONFIRMATION = "decision_confirmation"  # 决策确认型
    EXCEPTION_HANDLING = "exception_handling"  # 异常处理型
    PERMISSION_GRANT = "permission_grant"  # 权限授予型

class HumanInterventionNode:
    """
    人工干预节点，负责判断是否需要人工干预，并处理人工反馈。
    
    该节点会根据当前状态判断是否需要人工干预，如果需要，则等待人工反馈。
    人工反馈可以是继续执行、重新规划、修改状态或结束任务等。
    """
    
    def __init__(self):
        """初始化人工干预节点"""
        self.notification_channels = {
            "urgent": ["email", "sms", "wechat"],
            "important": ["email", "wechat"],
            "normal": ["email"]
        }
        
        self.timeout_config = {
            "urgent": 300,  # 5分钟
            "important": 3600,  # 1小时
            "normal": 86400  # 24小时
        }
        
        # 存储待处理的任务
        self.pending_tasks = {}
        
        # 存储决策历史
        self.decision_history = []
    
    def _determine_intervention_type(self, state: State) -> InterventionType:
        """确定介入类型
        
        Args:
            state: 当前状态
            
        Returns:
            介入类型
        """
        # 检查是否有错误
        if len(state.get("errors", [])) > 0:
            return InterventionType.EXCEPTION_HANDLING
        
        # 检查是否需要额外信息
        reflection_result = state.get("reflection_result", {})
        if reflection_result.get("missing_aspects", []):
            return InterventionType.INFO_SUPPLEMENT
        
        # 检查是否需要重要决策确认
        if reflection_result.get("detected_repetition", False):
            return InterventionType.DECISION_CONFIRMATION
        
        # 检查是否需要权限
        execution_log = state.get("execution_log", [])
        for entry in execution_log[-10:]:
            if "权限不足" in str(entry.get("details", {})) or "需要授权" in str(entry.get("details", {})):
                return InterventionType.PERMISSION_GRANT
        
        # 默认为决策确认
        return InterventionType.DECISION_CONFIRMATION
    
    def _determine_intervention_priority(self, state: State, intervention_type: InterventionType) -> InterventionPriority:
        """确定介入优先级
        
        Args:
            state: 当前状态
            intervention_type: 介入类型
            
        Returns:
            介入优先级
        """
        # 检查是否涉及资金安全或严重错误
        for error in state.get("errors", []):
            error_msg = str(error.get("error", ""))
            if any(kw in error_msg for kw in ["资金", "安全", "异常", "严重", "失败"]):
                return InterventionPriority.URGENT
        
        # 根据介入类型确定基础优先级
        type_priority_map = {
            InterventionType.EXCEPTION_HANDLING: InterventionPriority.IMPORTANT,
            InterventionType.PERMISSION_GRANT: InterventionPriority.IMPORTANT,
            InterventionType.DECISION_CONFIRMATION: InterventionPriority.NORMAL,
            InterventionType.INFO_SUPPLEMENT: InterventionPriority.NORMAL
        }
        
        base_priority = type_priority_map.get(intervention_type, InterventionPriority.NORMAL)
        
        # 上升优先级的条件
        if base_priority == InterventionPriority.NORMAL:
            # 检查任务是否长时间运行
            created_at = state.get("created_at", datetime.now())
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except ValueError:
                    created_at = datetime.now()
            
            time_running = (datetime.now() - created_at).total_seconds()
            if time_running > 1800:  # 30分钟
                return InterventionPriority.IMPORTANT
            
            # 检查是否反复需要介入
            intervention_count = 0
            for entry in state.get("execution_log", []):
                if entry.get("node") == "human_intervention" and entry.get("action") == "需要人工干预":
                    intervention_count += 1
            
            if intervention_count >= 2:  # 第三次需要介入
                return InterventionPriority.IMPORTANT
        
        return base_priority
    
    def _should_request_intervention(self, state: State) -> bool:
        """判断是否需要人工干预
        
        Args:
            state: 当前状态
            
        Returns:
            是否需要人工干预
        """
        # 从反思结果中检查是否检测到重复
        reflection_result = state.get("reflection_result", {})
        detected_repetition = reflection_result.get("detected_repetition", False)
        
        # 检查是否有错误
        has_errors = len(state.get("errors", [])) > 0
        
        # 检查是否执行了过多步骤
        excessive_steps = False
        execution_log = state.get("execution_log", [])
        if len(execution_log) > 30:  # 如果执行日志超过30条，认为可能陷入循环
            excessive_steps = True
        
        # 检查工具调用历史
        tool_calls_count = 0
        for entry in execution_log:
            if entry.get("node") == "tool_execution" and entry.get("action", "").startswith("调用工具:"):
                tool_calls_count += 1
        excessive_tool_calls = tool_calls_count > 10  # 如果工具调用超过10次，考虑人工干预
        
        # 检查是否有限额超出
        has_limit_exceeded = False
        for entry in execution_log:
            if "超出限额" in str(entry.get("details", {})) or "超出标准" in str(entry.get("details", {})):
                has_limit_exceeded = True
                break
        
        # 检查是否存在合规风险
        has_compliance_risk = False
        for entry in execution_log:
            if "合规" in str(entry.get("details", {})) and ("风险" in str(entry.get("details", {})) or "违规" in str(entry.get("details", {}))):
                has_compliance_risk = True
                break
        
        # 综合判断是否需要人工干预
        return (detected_repetition or 
                has_errors or 
                excessive_steps or 
                excessive_tool_calls or 
                has_limit_exceeded or 
                has_compliance_risk)
    
    def _create_intervention_options(self, state: State, intervention_type: InterventionType) -> List[Dict[str, Any]]:
        """根据介入类型创建干预选项
        
        Args:
            state: 当前状态
            intervention_type: 介入类型
            
        Returns:
            干预选项列表
        """
        # 基本选项
        basic_options = [
            {
                "action": "continue",
                "description": "继续执行当前计划"
            },
            {
                "action": "replan",
                "description": "重新制定执行计划"
            },
            {
                "action": "end",
                "description": "结束任务，返回当前结果"
            }
        ]
        
        # 根据介入类型添加特定选项
        if intervention_type == InterventionType.INFO_SUPPLEMENT:
            basic_options.append({
                "action": "modify",
                "description": "提供额外信息后继续",
                "parameters": ["additional_info"]
            })
        
        elif intervention_type == InterventionType.PERMISSION_GRANT:
            basic_options.append({
                "action": "grant",
                "description": "授予执行权限",
                "parameters": ["permission_scope", "duration"]
            })
        
        elif intervention_type == InterventionType.EXCEPTION_HANDLING:
            basic_options.append({
                "action": "modify",
                "description": "修改状态或参数后继续",
                "parameters": ["modifications"]
            })
            basic_options.append({
                "action": "skip",
                "description": "跳过当前步骤",
            })
        
        elif intervention_type == InterventionType.DECISION_CONFIRMATION:
            basic_options.append({
                "action": "confirm",
                "description": "确认执行操作",
                "parameters": ["confirmation_note"]
            })
        
        return basic_options
    
    def _create_intervention_request(self, state: State) -> Dict[str, Any]:
        """创建人工干预请求
        
        Args:
            state: 当前状态
            
        Returns:
            人工干预请求
        """
        # 获取当前执行状态的摘要
        reflection_result = state.get("reflection_result", {})
        
        # 获取最近的执行日志
        recent_logs = state.get("execution_log", [])[-10:] if state.get("execution_log") else []
        
        # 获取最近的工具调用
        recent_tool_calls = []
        for entry in recent_logs:
            if entry.get("node") == "tool_execution" and entry.get("action", "").startswith("调用工具:"):
                tool_name = entry.get("details", {}).get("tool")
                parameters = entry.get("details", {}).get("parameters", {})
                if tool_name and parameters:
                    recent_tool_calls.append({
                        "tool": tool_name,
                        "parameters": parameters
                    })
        
        # 确定介入类型
        intervention_type = self._determine_intervention_type(state)
        
        # 确定介入优先级
        intervention_priority = self._determine_intervention_priority(state, intervention_type)
        
        # 获取干预选项
        intervention_options = self._create_intervention_options(state, intervention_type)
        
        # 创建干预请求
        intervention_request = {
            "task_id": state.get("task_id", "unknown"),
            "user_input": state.get("user_input", ""),
            "detected_repetition": reflection_result.get("detected_repetition", False),
            "task_completion_rate": reflection_result.get("task_completion_rate", 0),
            "success_aspects": reflection_result.get("success_aspects", []),
            "missing_aspects": reflection_result.get("missing_aspects", []),
            "rationale": reflection_result.get("rationale", ""),
            "errors": state.get("errors", []),
            "recent_tool_calls": recent_tool_calls,
            "intervention_type": intervention_type,
            "intervention_priority": intervention_priority,
            "intervention_options": intervention_options,
            "notification_channels": self.notification_channels[intervention_priority],
            "timeout": self.timeout_config[intervention_priority],
            "timestamp": time.time(),
            "status": "pending"
        }
        
        return intervention_request
    
    def _analyze_similar_decisions(self, intervention_request: Dict[str, Any]) -> Optional[str]:
        """分析类似场景的历史决策
        
        Args:
            intervention_request: 当前干预请求
            
        Returns:
            推荐的决策动作，如果没有类似决策则返回None
        """
        if not self.decision_history:
            return None
        
        # 获取当前请求的关键特征
        current_type = intervention_request.get("intervention_type")
        current_rationale = intervention_request.get("rationale", "")
        current_errors = [str(e.get("error", "")) for e in intervention_request.get("errors", [])]
        current_tools = [t.get("tool") for t in intervention_request.get("recent_tool_calls", [])]
        
        # 找出类似的历史决策
        similar_decisions = []
        
        for decision in self.decision_history:
            # 必须是相同的介入类型
            if decision.get("request", {}).get("intervention_type") != current_type:
                continue
                
            # 检查错误相似性
            hist_errors = [str(e.get("error", "")) for e in decision.get("request", {}).get("errors", [])]
            error_similarity = self._calculate_similarity(current_errors, hist_errors)
            
            # 检查工具调用相似性
            hist_tools = [t.get("tool") for t in decision.get("request", {}).get("recent_tool_calls", [])]
            tool_similarity = self._calculate_similarity(current_tools, hist_tools)
            
            # 如果有足够的相似性，添加到相似决策列表
            if error_similarity > 0.5 or tool_similarity > 0.7:
                similar_decisions.append({
                    "decision": decision.get("response", {}).get("action"),
                    "similarity": max(error_similarity, tool_similarity)
                })
        
        # 如果有相似决策，返回相似度最高的
        if similar_decisions:
            similar_decisions.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_decisions[0]["decision"]
        
        return None
    
    def _calculate_similarity(self, list1: List[str], list2: List[str]) -> float:
        """计算两个列表的相似度
        
        Args:
            list1: 第一个列表
            list2: 第二个列表
            
        Returns:
            相似度(0-1)
        """
        if not list1 or not list2:
            return 0
            
        # 计算重叠项数量
        overlap = len(set(list1) & set(list2))
        
        # 计算Jaccard相似度
        return overlap / len(set(list1) | set(list2))
    
    def _should_send_notification(self, channel: str, priority: InterventionPriority) -> bool:
        """判断是否应该通过指定渠道发送通知
        
        Args:
            channel: 通知渠道
            priority: 干预优先级
            
        Returns:
            是否应该发送通知
        """
        # 紧急优先级总是发送所有渠道通知
        if priority == InterventionPriority.URGENT:
            return True
            
        # 重要优先级在工作时间发送
        if priority == InterventionPriority.IMPORTANT:
            # 获取当前时间
            now = datetime.now()
            # 判断是否在工作时间（周一至周五9点至18点）
            is_workday = 0 <= now.weekday() <= 4  # 0=周一，4=周五
            is_workhour = 9 <= now.hour < 18
            
            # 系统通知总是发送，其他渠道只在工作时间发送
            if channel == "system":
                return True
            return is_workday and is_workhour
            
        # 一般优先级只发送系统通知
        return channel == "system"
    
    def _send_notifications(self, intervention_request: Dict[str, Any]) -> None:
        """发送干预通知
        
        Args:
            intervention_request: 干预请求
        """
        task_id = intervention_request.get("task_id", "unknown")
        priority = intervention_request.get("intervention_priority", InterventionPriority.NORMAL)
        channels = intervention_request.get("notification_channels", ["system"])
        
        for channel in channels:
            if self._should_send_notification(channel, priority):
                # 这里实际应用中会调用外部通知服务
                pass
    
    def _learn_from_decision(self, request: Dict[str, Any], response: Dict[str, Any]) -> None:
        """从用户决策中学习
        
        Args:
            request: 干预请求
            response: 用户反馈
        """
        # 记录决策
        self.decision_history.append({
            "request": request,
            "response": response,
            "timestamp": time.time()
        })
        
        # 限制历史记录长度，保留最近的100条决策
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    async def __call__(self, state: State) -> State:
        """执行人工干预判断
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 检查是否已经有干预请求（来自参数验证节点）
            if state.get("needs_human_intervention", False) and state.get("intervention_request"):
                # 已经有干预请求，直接处理
                intervention_request = state["intervention_request"]
                
                # 保存请求到节点
                task_id = state.get("task_id", "unknown")
                self.pending_tasks[task_id] = intervention_request
                
                # 尝试从历史决策中学习推荐动作
                recommended_action = self._analyze_similar_decisions(intervention_request)
                if recommended_action:
                    intervention_request["recommended_action"] = recommended_action
                
                # 发送通知
                self._send_notifications(intervention_request)
                
                # 设置任务状态为等待人工干预
                state["status"] = "waiting_for_human"
                
                # 设置干预响应为空
                state["intervention_response"] = None
                
                return state
            
            # 判断是否需要人工干预
            needs_intervention = self._should_request_intervention(state)
            
            # 更新状态
            state["needs_human_intervention"] = needs_intervention
            
            if needs_intervention:
                # 创建人工干预请求
                intervention_request = self._create_intervention_request(state)
                
                # 保存请求到状态
                state["intervention_request"] = intervention_request
                
                # 保存请求到节点
                task_id = state.get("task_id", "unknown")
                self.pending_tasks[task_id] = intervention_request
                
                # 尝试从历史决策中学习推荐动作
                recommended_action = self._analyze_similar_decisions(intervention_request)
                if recommended_action:
                    intervention_request["recommended_action"] = recommended_action
                
                # 发送通知
                self._send_notifications(intervention_request)
                
                # 设置任务状态为等待人工干预
                state["status"] = "waiting_for_human"
                
                # 设置干预响应为空
                state["intervention_response"] = None
            
            return state
            
        except Exception as e:
            # 记录错误
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "human_intervention",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            return state
    
    async def provide_feedback(self, task_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """提供人工反馈
        
        Args:
            task_id: 任务ID
            feedback: 人工反馈
            
        Returns:
            更新后的请求
        """
        if task_id not in self.pending_tasks:
            raise ValueError(f"任务 {task_id} 不存在或不需要人工干预")
        
        # 获取请求
        request = self.pending_tasks[task_id]
        
        # 更新请求状态
        request["status"] = "resolved"
        request["feedback"] = feedback
        request["resolved_timestamp"] = time.time()
        
        # 学习用户决策
        self._learn_from_decision(request, feedback)
        
        return request
    
    async def handle_parameter_intervention_feedback(self, state: State, feedback: Dict[str, Any]) -> State:
        """处理参数验证的人工干预反馈
        
        Args:
            state: 当前状态
            feedback: 人工反馈
            
        Returns:
            更新后的状态
        """
        try:
            # 获取当前干预请求
            intervention_request = state.get("intervention_request", {})
            intervention_type = intervention_request.get("intervention_type", "")
            
            if intervention_type == "info_supplement":
                # 处理参数补充的反馈
                action = feedback.get("action", "")
                
                if action == "provide_parameters":
                    # 提供参数
                    provided_params = feedback.get("parameters", {})
                    
                    # 更新干预请求
                    intervention_request["feedback"] = feedback
                    intervention_request["status"] = "resolved"
                    intervention_request["resolved_timestamp"] = time.time()
                    
                    # 设置干预响应
                    state["intervention_response"] = {
                        "action": action,
                        "parameters": provided_params,
                        "timestamp": time.time()
                    }
                    
                    # 清除人工干预状态
                    state["needs_human_intervention"] = False
                    state["intervention_request"] = None
                    state["intervention_type"] = None
                    state["intervention_priority"] = None
                    state["status"] = "ready_for_execution"
                    
                elif action == "skip_tool":
                    # 跳过工具
                    intervention_request["feedback"] = feedback
                    intervention_request["status"] = "resolved"
                    intervention_request["resolved_timestamp"] = time.time()
                    
                    # 设置干预响应
                    state["intervention_response"] = {
                        "action": action,
                        "timestamp": time.time()
                    }
                    
                    # 清除人工干预状态
                    state["needs_human_intervention"] = False
                    state["intervention_request"] = None
                    state["intervention_type"] = None
                    state["intervention_priority"] = None
                    state["status"] = "ready_for_execution"
                    
                elif action == "modify_plan":
                    # 修改计划
                    intervention_request["feedback"] = feedback
                    intervention_request["status"] = "resolved"
                    intervention_request["resolved_timestamp"] = time.time()
                    
                    # 设置干预响应
                    state["intervention_response"] = {
                        "action": action,
                        "modifications": feedback.get("modifications", {}),
                        "timestamp": time.time()
                    }
                    
                    # 清除人工干预状态
                    state["needs_human_intervention"] = False
                    state["intervention_request"] = None
                    state["intervention_type"] = None
                    state["intervention_priority"] = None
                    state["status"] = "plan_modified"
            
            return state
            
        except Exception as e:
            # 记录错误
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "human_intervention",
                "action": "handle_parameter_intervention_feedback",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            return state 