from typing import TypedDict, Dict, List, Optional
from datetime import datetime

class ExpenseState(TypedDict):
    """差旅报销智能体的状态管理模型"""
    task_id: str                    # 任务ID
    user_input: str                 # 原始输入
    intent: Dict                    # 识别的意图
    plan: List[Dict]               # 执行计划
    context: Dict                  # 业务上下文
    execution_log: List            # 执行日志
    current_step: int              # 当前步骤
    results: Dict                  # 执行结果
    errors: List                   # 错误记录
    reflection: Dict               # 反思结果
    final_output: str              # 最终输出
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间 