# 差旅报销智能体

基于LangGraph和Qwen3 API构建的智能差旅报销助手，实现从意图识别到任务完成的全自动化流程。

## 功能特点

- 智能意图识别：自动识别用户报销需求
- 任务自动规划：生成最优执行计划
- 多步骤执行：支持复杂报销流程
- 状态管理：完整的执行状态追踪
- RESTful API：提供标准接口

## 技术架构

- LangGraph：工作流编排
- Qwen3 API：大语言模型服务
- FastAPI：Web服务框架
- Pydantic：数据验证
- LangChain：LLM应用框架

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，设置必要的环境变量
```

3. 启动服务：
```bash
python -m src.app
```

4. 访问API文档：
```
http://localhost:8000/docs
```

## API接口

### 处理报销请求
```http
POST /process
Content-Type: application/json

{
    "input": "我要申请3月15-17日北京出差的报销"
}
```

### 查询任务状态
```http
GET /status/{task_id}
```

## 项目结构

```
travel_bill_agent/
├── src/
│   ├── models/
│   │   └── state.py
│   ├── nodes/
│   │   ├── intent_analysis.py
│   │   ├── task_planning.py
│   │   └── execution.py
│   └── app.py
├── tests/
├── docs/
├── config/
├── requirements.txt
└── README.md
```

## 开发计划

- [ ] 实现状态持久化
- [ ] 添加更多工具集成
- [ ] 优化提示工程
- [ ] 添加单元测试
- [ ] 实现监控和日志
- [ ] 支持更多报销场景

## 贡献指南

欢迎提交Issue和Pull Request。

## 许可证

MIT License
