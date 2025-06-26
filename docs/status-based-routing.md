# 基于Status的节点流转逻辑

## 概述

智能体系统采用基于`status`字段的节点流转逻辑，每个节点执行完成后会根据当前状态的`status`字段来决定下一步应该执行哪个节点。本文档只包含节点中实际设置的status值。

## 各节点实际设置的Status状态

### 规划节点 (Planning)
- `conversation_ready`: 计划为空，准备进入对话模式
- `decision_ready`: 计划不为空，准备进入决策模式

### 决策节点 (Decision)
- `ready_for_execution`: 准备执行工具
- `waiting_for_human`: 等待人工干预

### 工具执行节点 (Tool Execution)
- `tools_completed`: 工具执行完成
- `tool_execution_failed`: 工具执行失败

### 对话节点 (Conversation)
- `conversation_completed`: 对话已完成
- `conversation_error`: 对话执行出错

### 人工干预节点 (Human Intervention)
- `waiting_for_human`: 等待人工反馈
- `ready_for_execution`: 准备执行工具（处理参数反馈后）
- `plan_modified`: 计划已修改

## 节点流转逻辑

### 1. 分析节点 (Analysis)
- **输入**: 用户输入
- **输出**: 意图分析结果
- **流转**: 固定流转到规划节点

### 2. 规划节点 (Planning)
- **输入**: 意图分析结果
- **输出**: 执行计划
- **流转逻辑**:
  - `status == "conversation_ready"` → 对话节点
  - `status == "decision_ready"` → 决策节点
  - 默认 → 决策节点

### 3. 对话节点 (Conversation)
- **输入**: 用户输入和上下文
- **输出**: 对话响应
- **流转逻辑**:
  - `status == "conversation_completed"` → 结束
  - `status == "conversation_error"` → 人工干预节点
  - 默认 → 结束

### 4. 决策节点 (Decision)
- **输入**: 执行计划
- **输出**: 工具调用决策
- **流转逻辑**:
  - `status == "waiting_for_human"` → 人工干预节点
  - `status == "ready_for_execution"` 且 `pending_tools` 不为空 → 工具执行节点
  - 默认 → 反思节点

### 5. 工具执行节点 (Tool Execution)
- **输入**: 待执行的工具列表
- **输出**: 工具执行结果
- **流转逻辑**:
  - 工具执行完成后直接流转到反思节点

### 6. 反思节点 (Reflection)
- **输入**: 执行结果和错误信息
- **输出**: 反思结果和下一步建议
- **流转逻辑**:
  - 检测到重复调用或错误 → 人工干预节点
  - `reflection_result.action == "replan"` → 规划节点
  - `reflection_result.action == "continue"` → 决策节点
  - 默认 → 结束

### 7. 人工干预节点 (Human Intervention)
- **输入**: 干预请求
- **输出**: 人工反馈
- **流转逻辑**:
  - `status == "waiting_for_human"` → 继续等待（保持在人工干预节点）
  - `intervention_response.action == "replan"` → 规划节点
  - `intervention_response.action == "continue"` 或 `"modify"` → 决策节点
  - 默认 → 结束

## 状态转换示例

### 正常对话流程
```
running → conversation_ready → conversation_completed → END
```

### 需要工具执行的流程
```
running → decision_ready → ready_for_execution → tools_completed → reflection → continue → decision → ready_for_execution → tools_completed → reflection → END
```

### 错误处理流程
```
running → tool_execution_failed → reflection → human_intervention → waiting_for_human → (人工反馈) → replan → planning → decision_ready → ...
```

### 人工干预流程
```
running → waiting_for_human → human_intervention → waiting_for_human → (人工反馈) → continue → decision → ready_for_execution → ...
```

## 实现优势

1. **准确性**: 只使用节点中实际存在的status值，避免无效状态
2. **可观测性**: 通过status字段可以清楚地了解当前任务的执行状态
3. **错误处理**: 统一的错误处理机制，自动转向人工干预
4. **调试友好**: 状态转换清晰，便于调试和问题排查
5. **简化逻辑**: 使用单一的`waiting_for_human`状态来判断是否需要人工干预

## 注意事项

1. 每个节点都应该正确设置`status`字段
2. 人工干预节点需要正确处理`waiting_for_human`状态
3. 错误状态应该及时触发人工干预
4. 状态转换应该是幂等的，避免无限循环
5. 路由逻辑只使用节点中实际设置的status值 