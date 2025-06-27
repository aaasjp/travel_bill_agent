# 人工干预功能使用指南

本文档介绍如何使用LangGraph的interrupt功能实现人工干预，在差旅报销系统中处理需要人工决策的场景。

## 功能概述

人工干预功能允许系统在特定情况下暂停自动处理流程，等待人工输入或决策，然后继续执行。该功能还包含完整的memory记录系统，将所有人工干预的反馈信息持久化存储，便于后续分析和学习。

### 主要特性

- **中断等待**：使用LangGraph的interrupt功能暂停流程等待人工输入
- **Memory记录**：自动将人工反馈记录到memory系统中
- **类型分类**：根据干预类型自动分类memory
- **元数据管理**：记录详细的上下文信息
- **错误处理**：完善的错误处理和日志记录

## 核心组件

### 1. 干预类型枚举

```python
from src.nodes.human_intervention import InterventionType, InterventionPriority

# 干预类型
InterventionType.INFO_SUPPLEMENT        # 信息补充型
InterventionType.DECISION_CONFIRMATION  # 决策确认型
InterventionType.EXCEPTION_HANDLING     # 异常处理型
InterventionType.PERMISSION_GRANT       # 权限授予型
InterventionType.PARAMETER_PROVIDER     # 参数提供型

# 优先级
InterventionPriority.URGENT     # 紧急（5分钟超时）
InterventionPriority.IMPORTANT  # 重要（1小时超时）
InterventionPriority.NORMAL     # 一般（24小时超时）
```

### 2. 人工干预节点

```python
from src.nodes.human_intervention import HumanInterventionNode

# 创建人工干预节点
human_intervention_node = HumanInterventionNode()
```

## Memory记录功能

### Memory类型映射

系统会根据干预类型自动选择合适的memory类型：

```python
memory_type_mapping = {
    "info_supplement": MemoryType.FACT,           # 事实性记忆
    "decision_confirmation": MemoryType.EXPERIENCE, # 经验性记忆
    "exception_handling": MemoryType.EXPERIENCE,   # 经验性记忆
    "permission_grant": MemoryType.TASK,          # 任务相关记忆
    "parameter_provider": MemoryType.TASK          # 任务相关记忆
}
```

### Memory内容结构

每次人工干预都会记录以下信息：

```python
{
    "user_feedback": "用户的具体反馈内容",
    "intervention_type": "干预类型",
    "intervention_priority": "优先级",
    "reason": "干预原因",
    "request_source": "请求来源",
    "user_input": "用户原始输入",
    "timestamp": "时间戳",
    "status": "状态"
}
```

### 元数据记录

```python
{
    "node": "human_intervention",
    "intervention_type": "干预类型",
    "intervention_priority": "优先级",
    "request_source": "请求来源",
    "user_id": "用户ID",
    "session_id": "会话ID",
    "thread_id": "线程ID"
}
```

## 使用方法

### 1. 在状态中设置干预请求

```python
# 在需要人工干预的节点中设置干预请求
state["intervention_request"] = {
    "intervention_type": InterventionType.DECISION_CONFIRMATION,
    "intervention_priority": InterventionPriority.URGENT,
    "reason": "差旅费用超过5000元，需要经理审批",
    "amount": 6500.00,
    "threshold": 5000.00,
    "context": "用户提交的报销申请",
    "request_source": "user"  # 或 "system"
}
```

### 2. 在图中添加人工干预节点

```python
from langgraph.graph import StateGraph
from langgraph.constants import START
from langgraph.checkpoint.memory import MemorySaver

# 构建图
builder = StateGraph(State)
builder.add_node("human_intervention", human_intervention_node.handle_intervention_request)
builder.add_edge("previous_node", "human_intervention")
builder.add_edge("human_intervention", "next_node")

# 使用检查点器（必需）
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

### 3. 执行图和处理中断

```python
from langgraph.types import Command

# 配置线程ID
config = {
    "configurable": {
        "thread_id": "unique_thread_id"
    }
}

# 执行图
try:
    result = graph.invoke(initial_state, config=config)
except Exception as e:
    # 处理中断
    if "interrupt" in str(e).lower():
        # 等待人工反馈
        human_feedback = {
            "action": "approve",
            "approval_reason": "费用合理，符合公司政策"
        }
        
        # 使用Command恢复执行
        result = graph.invoke(
            Command(resume=human_feedback), 
            config=config
        )
```

### 4. 使用流式模式

```python
# 使用stream模式可以更好地处理中断
for chunk in graph.stream(initial_state, config=config):
    if "__interrupt__" in chunk:
        # 检测到中断
        interrupt_data = chunk["__interrupt__"]
        print(f"需要人工干预: {interrupt_data}")
        
        # 提供人工反馈
        human_feedback = {
            "action": "provide_info",
            "info_type": "invoice_details",
            "info_content": {
                "invoice_number": "INV-2024-001234",
                "invoice_date": "2024-01-15"
            }
        }
        
        # 恢复执行
        for resume_chunk in graph.stream(
            Command(resume=human_feedback), 
            config=config
        ):
            print(f"恢复输出: {resume_chunk}")
        break
    else:
        print(f"正常输出: {chunk}")
```

## 支持的反馈操作

### 1. 信息补充 (INFO_SUPPLEMENT)

```python
{
    "action": "provide_info",
    "info_type": "invoice_details",
    "info_content": {
        "invoice_number": "INV-2024-001234",
        "invoice_date": "2024-01-15",
        "invoice_amount": "1500.00"
    }
}
```

### 2. 决策确认 (DECISION_CONFIRMATION)

```python
# 批准
{
    "action": "approve",
    "approval_reason": "费用合理，符合公司政策"
}

# 拒绝
{
    "action": "reject",
    "rejection_reason": "费用超出预算范围"
}

# 修改后批准
{
    "action": "modify",
    "modifications": {
        "amount": 4800.00,
        "description": "调整后的费用"
    },
    "approval_reason": "调整后费用合理"
}
```

### 3. 异常处理 (EXCEPTION_HANDLING)

```python
# 解决异常
{
    "action": "resolve",
    "resolution_method": "manual_verification",
    "resolution_details": "已人工核实发票真实性"
}

# 升级处理
{
    "action": "escalate",
    "escalation_reason": "需要高级经理审批",
    "escalation_level": "senior_manager"
}
```

### 4. 权限授予 (PERMISSION_GRANT)

```python
{
    "action": "grant",
    "permission_level": "manager_approval",
    "grant_reason": "特殊情况需要经理权限"
}
```

### 5. 参数提供 (PARAMETER_PROVIDER)

```python
{
    "action": "provide_parameters",
    "parameters": {
        "budget_limit": 10000.00,
        "approval_chain": ["manager", "director"],
        "special_notes": "项目紧急，需要快速审批"
    }
}
```

## 状态更新

人工干预完成后，状态会包含以下信息：

```python
{
    "status": "intervention_completed",
    "intervention_feedback": "用户反馈内容",
    "user_input": "更新后的用户输入",
    "memory_ids": ["memory_id_1", "memory_id_2"],  # 记录的memory ID列表
    "updated_at": "2024-01-15T10:30:00"
}
```

## Memory查询和管理

### 1. 查询特定类型的Memory

```python
from src.memory.memory_store import MemoryStore, MemoryType

memory_store = MemoryStore()

# 查询经验性记忆
experience_memories = memory_store.search_by_type(MemoryType.EXPERIENCE)

# 查询事实性记忆
fact_memories = memory_store.search_by_type(MemoryType.FACT)
```

### 2. 按内容搜索Memory

```python
# 搜索包含特定关键词的memory
invoice_memories = memory_store.search_by_content("发票")
approval_memories = memory_store.search_by_content("审批")
```

### 3. 按元数据搜索Memory

```python
# 搜索特定用户的memory
user_memories = memory_store.search_by_metadata({
    "user_id": "user_001"
})

# 搜索特定干预类型的memory
intervention_memories = memory_store.search_by_metadata({
    "intervention_type": "decision_confirmation"
})
```

### 4. 获取最新Memory

```python
# 获取最新的10个memory
latest_memories = memory_store.get_latest_memories(10)

# 获取最早的5个memory
earliest_memories = memory_store.get_earliest_memories(5)
```

## 错误处理

系统会自动处理各种错误情况：

1. **干预请求格式错误**：记录错误并设置状态为 `intervention_error`
2. **反馈处理失败**：记录错误并继续执行
3. **Memory记录失败**：记录错误但不影响主流程
4. **超时处理**：根据优先级设置超时时间

## 最佳实践

1. **合理设置优先级**：根据业务紧急程度设置合适的优先级
2. **提供清晰的指导**：在干预请求中包含详细的原因和上下文
3. **记录反馈历史**：系统会自动记录所有人工反馈，便于审计
4. **错误处理**：始终包含适当的错误处理逻辑
5. **超时管理**：考虑设置合理的超时时间，避免流程卡死
6. **Memory管理**：定期清理和归档旧的memory记录
7. **数据分析**：利用memory记录进行用户行为分析和系统优化

## 示例场景

### 场景1：发票信息不完整

```python
# 设置干预请求
state["intervention_request"] = {
    "intervention_type": InterventionType.INFO_SUPPLEMENT,
    "intervention_priority": InterventionPriority.IMPORTANT,
    "reason": "发票信息不完整，需要补充发票号码和开票日期",
    "required_info": ["invoice_number", "invoice_date"],
    "context": "用户提交的发票缺少关键信息",
    "request_source": "user"
}

# 人工反馈
{
    "action": "provide_info",
    "info_type": "invoice_details",
    "info_content": {
        "invoice_number": "INV-2024-001234",
        "invoice_date": "2024-01-15"
    }
}
```

### 场景2：大额费用审批

```python
# 设置干预请求
state["intervention_request"] = {
    "intervention_type": InterventionType.DECISION_CONFIRMATION,
    "intervention_priority": InterventionPriority.URGENT,
    "reason": "差旅费用超过5000元，需要经理审批",
    "amount": 6500.00,
    "threshold": 5000.00,
    "request_source": "system"
}

# 人工反馈
{
    "action": "approve",
    "approval_reason": "费用合理，符合公司政策"
}
```

通过这种方式，系统可以在需要人工决策的关键节点暂停，等待人工输入，然后继续执行后续流程，同时将所有交互信息记录到memory中，确保业务流程的完整性和可追溯性。 