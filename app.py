#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能体主应用
"""

import os
import sys
from pathlib import Path

# 设置环境变量禁用ChromaDB遥测
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["CHROMA_ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_SERVER_TELEMETRY_ENABLED"] = "false"

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.app import create_app, workflow

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8000) 