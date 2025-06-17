# reimbursement-assistant

基于 LangGraph 框架的reimbursement-assistant，能够处理各种报销相关任务，并与 LangSmith 集成以提供可视化和监控能力。

## 项目结构

```
.
├── src/                   # 源代码
│   ├── app.py             # 主应用入口
│   ├── models/            # 数据模型
│   │   └── state.py       # 状态模型
│   ├── nodes/             # 工作流节点
│   │   ├── analysis.py  # 意图分析节点
│   │   ├── task_planning.py    # 任务规划节点
│   │   ├── execution.py        # 执行节点
│   │   └── tool_execution.py   # 工具执行节点
│   └── tool/              # 工具定义
│       ├── base.py        # 工具基类
│       ├── registry.py    # 工具注册表
│       └── reimbursement_status.py  # 报销状态查询工具
├── tests/                 # 测试代码
├── app.py                 # LangGraph 入口点（用于 langgraph.json）
├── langgraph.json         # LangGraph 配置文件
├── test_tools.py          # 工具测试脚本
├── requirements.txt       # 依赖项
└── README.md              # 项目说明
```

## 配置文件

### langgraph.json

LangGraph 配置文件定义了智能体的部署配置：

```json
{
  "dependencies": ["."],
  "graphs": {
    "expense_agent": "app:workflow"
  },
  "env": ".env",
  "dockerfile_lines": [
    "RUN pip install --no-cache-dir -r requirements.txt"
  ],
  "python_version": "3.11"
}
```

- `dependencies`: 项目依赖路径
- `graphs`: 定义可用的智能体图，`expense_agent` 指向 `app.py` 中的 `workflow`
- `env`: 环境变量文件路径
- `dockerfile_lines`: Docker 构建指令
- `python_version`: Python 版本要求

## 功能特点

- 意图分析：自动识别用户的报销意图和要求
- 任务规划：将复杂的报销任务分解为可执行步骤
- 工具调用：支持多种报销相关工具，如状态查询、表单生成等
- LangSmith 集成：提供工作流可视化和执行监控

## 工具集成

- 报销状态查询工具 (ReimbursementStatusTool)
- 报销表单工具 (ReimbursementFormTool)
- 支出记录工具 (ExpenseRecordTool)
- 报销稽核工具 (AuditReimbursementTool)
- 报销单打印工具 (PrintReimbursementTool)
- 付款处理工具 (PaymentProcessTool)

## 开始使用

### 环境设置

1. 创建 `.env` 文件并设置必要的环境变量：

```bash
# 模型配置
MODEL_NAME=qwen3-235b-a22b
MODEL_BASE_URL=http://10.249.238.52:13206/member3/qwen3-235b-a22b/v1
API_KEY=your_api_key_here

# LangSmith 配置（可选，用于监控和可视化）
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=差旅报销智能体
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install langgraph-cli
```

### 启动方式

#### 方式一：LangGraph 开发服务器（推荐）

使用 LangGraph 开发服务器启动，支持 Studio UI 和 API：

```bash
langgraph dev --port 2024
```

启动后可以访问：
- 🚀 **API 服务**: http://127.0.0.1:2024
- 🎨 **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 **API 文档**: http://127.0.0.1:2024/docs

#### 方式二：传统 FastAPI 服务器

直接运行 FastAPI 应用：

```bash
langgraph dev
```

应用将在 http://localhost:8000 上运行。

## LangGraph Studio 使用

### LangGraph Studio 特性

LangGraph Studio 是一个强大的可视化工具，提供：

- **实时工作流可视化**：查看智能体的执行流程
- **交互式调试**：逐步执行和调试工作流
- **状态检查**：实时查看每个节点的状态变化
- **性能监控**：分析执行时间和资源使用

### 访问 Studio

启动 LangGraph 开发服务器后，访问：
```
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

### Studio 使用步骤

1. **启动服务**：
   ```bash
   langgraph dev --port 2024
   ```

2. **打开 Studio**：在浏览器中访问 Studio URL

3. **选择智能体**：选择 `expense_agent` 智能体

4. **开始对话**：在 Studio 界面中输入测试消息

5. **观察执行**：实时查看工作流的执行过程

## LangSmith 集成使用

### 设置 LangSmith

1. 访问 [LangSmith](https://smith.langchain.com/) 并创建账户
2. 获取 API 密钥并设置在 `.env` 文件中
3. 启动应用，确认 LangSmith 集成已启用

### 监控和追踪

启用 LangSmith 后，您可以：

1. **查看项目页面**：
   - 访问 https://smith.langchain.com/projects/差旅报销智能体
   - 查看所有执行追踪记录

2. **分析执行轨迹**：
   - 查看每次对话的完整执行路径
   - 分析节点执行时间和状态转换
   - 识别性能瓶颈和错误

3. **调试和优化**：
   - 深入查看每个节点的输入输出
   - 分析工具调用的成功率
   - 优化工作流性能

### LangSmith 的优势

- **完整追踪**：记录每次执行的完整轨迹
- **性能分析**：识别瓶颈和优化机会
- **错误诊断**：快速定位和解决问题
- **团队协作**：共享和讨论执行结果

## 本地可视化

如果不使用 LangSmith，您也可以通过本地可视化工具查看工作流图：

```bash
python src/visualize_graph.py
```

这将生成工作流图的静态图像 `workflow_graph.png`。

## API 端点

### LangGraph API 端点（推荐）

当使用 `langgraph dev` 启动时，可以使用以下端点：

- **GET /assistants**: 获取可用的智能体列表
- **POST /assistants/{assistant_id}/threads**: 创建新的对话线程
- **POST /assistants/{assistant_id}/threads/{thread_id}/runs**: 运行智能体
- **GET /assistants/{assistant_id}/threads/{thread_id}/runs/{run_id}**: 获取运行状态
- **GET /assistants/{assistant_id}/graph**: 获取智能体工作流图

### 传统 FastAPI 端点

当使用 `python -m src.app` 启动时，可以使用：

- **POST /process**: 处理报销请求
- **GET /status/{task_id}**: 获取任务状态
- **GET /tools**: 获取可用工具列表
- **GET /**: 获取应用基本信息

### 使用示例

#### LangGraph API 使用示例

```bash
# 获取智能体列表
curl http://127.0.0.1:2024/assistants

# 创建对话线程
curl -X POST http://127.0.0.1:2024/assistants/expense_agent/threads \
  -H "Content-Type: application/json" \
  -d '{}'

# 运行智能体
curl -X POST http://127.0.0.1:2024/assistants/expense_agent/threads/{thread_id}/runs \
  -H "Content-Type: application/json" \
  -d '{"input": {"user_input": "我要查询报销状态"}}'
```

#### 传统 API 使用示例

```bash
# 处理报销请求
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"input": "我要查询报销状态", "client_id": "test_client"}'
```

## 工作流架构

reimbursement-assistant使用 LangGraph 构建，包含以下主要节点：

1. **意图分析节点 (IntentAnalysisNode)**：解析用户输入，识别意图和工具调用需求
2. **任务规划节点 (TaskPlanningNode)**：根据意图制定执行计划
3. **执行节点 (ExecutionNode)**：执行规划生成的计划
4. **工具执行节点 (ToolExecutionNode)**：处理特定工具调用

## 故障排除

### 常见问题

#### 1. TypedDict 错误

如果遇到 `Please use typing_extensions.TypedDict instead of typing.TypedDict` 错误：

```bash
# 确保安装了 typing_extensions
pip install typing_extensions>=4.8.0
```

#### 2. 端口被占用

如果端口 2024 被占用：

```bash
# 使用其他端口
langgraph dev --port 2025

# 或者杀死占用端口的进程
lsof -ti:2024 | xargs kill -9
```

#### 3. 模块导入错误

如果遇到模块导入错误：

```bash
# 确保在项目根目录
cd /path/to/baoxiao-assistant

# 激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

#### 4. LangSmith 连接问题

如果 LangSmith 无法连接：

1. 检查 `.env` 文件中的 `LANGCHAIN_API_KEY` 是否正确
2. 确认网络连接正常
3. 验证 LangSmith 服务状态

### 调试模式

启用详细日志：

```bash
# 设置环境变量
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_DEBUG=true

# 启动服务
langgraph dev --port 2024
```

## 贡献

欢迎贡献代码、报告问题或提出建议。请遵循以下步骤：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT
