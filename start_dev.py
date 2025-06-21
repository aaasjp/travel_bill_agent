#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境启动脚本
禁用所有遥测功能以避免阻塞调用警告
"""

import os
import sys
from pathlib import Path

# 设置环境变量禁用所有遥测
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["CHROMA_ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_SERVER_TELEMETRY_ENABLED"] = "false"
os.environ["CHROMA_CLIENT_TELEMETRY_ENABLED"] = "false"

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入并启动应用
from src.app import create_app

if __name__ == "__main__":
    print("启动差旅报销智能体...")
    print("已禁用ChromaDB遥测功能")
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8000) 