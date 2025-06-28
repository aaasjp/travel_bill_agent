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
from ..llm import get_llm
from langgraph.types import interrupt

from ..memory.memory_store import MemoryStore, MemoryType

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
    PARAMETER_PROVIDER = "parameter_provider"  # 参数提供型

# 通知渠道枚举
class NotificationChannel(str, Enum):
    """通知渠道类型"""
    EMAIL = "email"  # 邮件通知
    SMS = "sms"  # 短信通知
    WECHAT = "wechat"  # 微信通知
    SYSTEM = "system"  # 系统内部通知

class HumanInterventionNode:
    """
    人工干预节点，负责判断是否需要人工干预，并处理人工反馈。
    
    该节点会根据当前状态判断是否需要人工干预，如果需要，则等待人工反馈。
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
        
        # 获取LLM实例
        self.llm = get_llm()

        
        # 创建memory store实例
        self.memory_store = MemoryStore()
    
    async def _generate_intervention_instruction(self, state: State, intervention_request: Dict[str, Any]) -> str:
        """
        使用大模型生成用户操作指导
        
        Args:
            state: 当前状态
            intervention_request: 干预请求数据
            
        Returns:
            用户操作指导文本
        """
        try:
            intervention_type = intervention_request["intervention_type"]
            intervention_priority = intervention_request.get("intervention_priority", "normal")
            reason = intervention_request.get("reason", "")
            
            # 构建干预提示词模板
            base_prompt = f"""
你是一个专业的差旅报销系统助手。当前系统需要人工干预，请根据干预类型和相关信息，生成清晰、友好的用户操作指导。

## 干预类型说明
- info_supplement  # 信息补充型
- decision_confirmation  # 决策确认型
- exception_handling  # 异常处理型
- permission_grant  # 权限授予型
- parameter_provider  # 参数提供型

## 用户原始输入
{state.get('user_input', '')}

## 详细干预请求信息
{json.dumps(intervention_request, ensure_ascii=False, indent=2)}

## 任务要求
请根据不同的干预类型，生成相应的用户操作指导

## 输出要求
请生成一个友好、清晰、结构化的用户操作指导，包含：
1. 说明为什么需要人工干预
2. 具体需要用户做什么
3. 如果需要用户提供信息，请说明需要提供的信息的格式和要求
4. 如果需要用户决策，请说明需要决策的信息和可选选项
5. 如果需要用户处理异常，请说明需要处理异常的信息和处理方案
6. 如果需要用户授予权限，请说明需要授予的权限和申请原因
7. 如果需要用户提供参数，请说明需要提供的参数和参数的格式、描述、要求

请用中文回复，语言要友好、专业、易懂。

"""
            
            # 调用大模型生成指导
            messages = [
                {"role": "system", "content": "你是一个专业的差旅报销系统助手，专门负责生成用户操作指导。"},
                {"role": "user", "content": base_prompt}
            ]
            
            response = self.llm.invoke(messages)
            instruction = response.content.strip()
            
            return instruction
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"生成干预指导失败: {str(e)}")
            
            # 返回默认指导
            return f"""
## 系统需要人工干预

**干预类型**: {intervention_type}
**优先级**: {intervention_priority}
**原因**: {reason}

系统当前无法自动处理您的请求，需要您的人工干预。请根据上述信息提供相应的操作或信息。

如有疑问，请联系系统管理员。
"""
    
    async def __call__(self, state: State) -> State:
        """
        处理来自state的干预请求，根据不同的干预类型分别处理，然后中断等待人工处理
        
        Args:
            state: 当前状态，包含intervention_request字段
            
        Returns:
            更新后的状态
        """
        try:
            # 检查是否有干预请求
            if "intervention_request" not in state or "intervention_type" not in state["intervention_request"] or "intervention_priority" not in state["intervention_request"]:
                state["status"] = "intervention_error"
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "node": "human_intervention",
                    "error": "intervention_request_error",
                    "error_type": "intervention_error",
                    "timestamp": str(time.time()),
                    "intervention_request": state["intervention_request"]
                })
                return state
            
            intervention_request = state["intervention_request"]
            
            intervention_type = intervention_request["intervention_type"]

            # 使用大模型生成用户操作指导
            instruction = await self._generate_intervention_instruction(state, intervention_request)
            
            # 中断等待人工反馈
            
            human_feedback = interrupt({
                "instruction": instruction
            })

            await self._handle_intervention_feedback(state, human_feedback)
            
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"处理干预请求失败: {str(e)}")
            
            # 记录错误
            if "errors" not in state:
                state["errors"] = []
            
            state["errors"].append({
                "node": "human_intervention",
                "error": str(e),
                "error_type": "intervention_error",
                "timestamp": str(time.time()),
                "intervention_request": state.get("intervention_request", {})
            })
            state["status"] = "intervention_error"
            
            return state
    
    async def _handle_intervention_feedback(self, state: State, user_feedback: str):
        """
        处理人工反馈结果
        """
        state["user_feedback"] = user_feedback
        state["status"] = "intervention_completed"
        state["updated_at"] = datetime.now()

        if "memory_records" not in state:
                state["memory_records"] = []

        # 把用户反馈的内容保存到memory中
        try:
            # 获取干预请求信息
            intervention_request = state.get("intervention_request", {})
            # 构建memory内容
            memory_content = {
                "user_feedback": user_feedback,
                "intervention_request": intervention_request,
                "user_input": state.get("user_input", ""),
                "timestamp": datetime.now().isoformat(),
            }
            
            # 添加memory
            memory_unit = self.memory_store.add_memory_by_llm(json.dumps(memory_content, ensure_ascii=False, indent=2))
            state["memory_records"].append(memory_unit.to_dict())
            
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"记录人工干预反馈到memory失败: {str(e)}")
            
            # 记录错误到状态中
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "node": "human_intervention",
                "error": str(e),
                "error_type": "intervention_error",
                "timestamp": str(time.time()),
                "user_feedback": user_feedback
            })
        
        return state


        
