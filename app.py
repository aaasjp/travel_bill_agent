"""
差旅报销智能体 - LangGraph 入口点
"""

import sys
import os

# 将当前目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 workflow
from src.app import workflow

# 导出 workflow 供 LangGraph API 使用
__all__ = ['workflow'] 