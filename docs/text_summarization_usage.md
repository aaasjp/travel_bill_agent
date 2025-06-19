# 文本总结功能使用说明

## 概述

`ChromaStore` 类新增了使用大模型来总结文本内容的功能。这个功能可以直接对文本内容进行智能总结，帮助用户快速了解文本的核心信息。

## 功能特性

- **单个文本总结**：对单个文本内容进行智能总结
- **批量文本总结**：同时处理多个文本内容
- **可配置总结长度**：支持自定义总结文本的最大长度
- **内容类型识别**：支持指定内容类型，帮助大模型更好地理解内容
- **错误处理**：完善的错误处理和状态反馈

## 方法说明

### 1. summarize_text_content()

单个文本总结方法

```python
def summarize_text_content(self, content: str, max_length: int = 1000, content_type: str = "text") -> Dict[str, Any]:
```

**参数：**
- `content` (str): 要总结的文本内容
- `max_length` (int): 总结文本的最大长度，默认为1000字符
- `content_type` (str): 内容类型，用于提示大模型更好地理解内容，默认为"text"

**返回值：**
```python
{
    "success": bool,                    # 是否成功
    "original_content_length": int,     # 原始内容长度
    "summary": str,                     # 总结内容
    "summary_length": int,              # 总结长度
    "content_type": str,                # 内容类型
    "error": str                        # 错误信息（如果失败）
}
```

### 2. summarize_texts_batch()

批量文本总结方法

```python
def summarize_texts_batch(self, contents: List[str], max_length: int = 1000) -> Dict[str, Any]:
```

**参数：**
- `contents` (List[str]): 文本内容列表
- `max_length` (int): 总结文本的最大长度，默认为1000字符

**返回值：**
```python
{
    "successful_summaries": List[Dict],  # 成功总结的内容列表
    "failed_contents": List[Dict],       # 失败的内容列表
    "total_contents": int,               # 总内容数
    "successful_count": int,             # 成功数量
    "failed_count": int                  # 失败数量
}
```

## 使用示例

### 基本使用

```python
from src.vector_store.chroma_store import ChromaStore

# 初始化ChromaStore
store = ChromaStore()

# 要总结的文本内容
text_content = """
这是一个关于差旅报销政策的详细说明文档。
包含了报销标准、流程、注意事项等重要信息。
"""

# 总结单个文本
result = store.summarize_text_content(text_content, max_length=500, content_type="政策文档")

if result["success"]:
    print(f"总结内容: {result['summary']}")
    print(f"总结长度: {result['summary_length']} 字符")
else:
    print(f"总结失败: {result['error']}")
```

### 批量处理

```python
# 多个文本内容
text_contents = [
    "第一个文本内容...",
    "第二个文本内容...",
    "第三个文本内容..."
]

# 批量总结
result = store.summarize_texts_batch(text_contents, max_length=300)

print(f"总内容数: {result['total_contents']}")
print(f"成功总结: {result['successful_count']}")
print(f"失败内容: {result['failed_count']}")

# 处理成功的结果
for summary in result['successful_summaries']:
    print(f"内容类型: {summary['content_type']}")
    print(f"总结: {summary['summary']}")
    print("-" * 50)
```

### 在差旅报销系统中的应用

```python
# 总结报销政策文本
policy_text = """
差旅报销政策详细说明...
"""

policy_result = store.summarize_text_content(
    policy_text, 
    max_length=800, 
    content_type="政策文档"
)

if policy_result["success"]:
    # 将总结内容添加到知识库
    store.add_documents(
        documents=[policy_result["summary"]],
        metadatas=[{
            "type": "policy_summary",
            "content_type": policy_result["content_type"],
            "summary_length": policy_result["summary_length"]
        }],
        ids=[f"policy_summary_{uuid.uuid4()}"]
    )

# 批量总结多个文档内容
document_contents = [
    "发票处理说明文档内容...",
    "报销流程详细说明...",
    "费用标准规定..."
]

document_types = ["发票说明", "流程文档", "费用标准"]

summaries_result = store.summarize_texts_batch(
    document_contents, 
    max_length=400, 
    content_types=document_types
)

# 将总结内容用于快速检索
for summary in summaries_result['successful_summaries']:
    store.add_documents(
        documents=[summary["summary"]],
        metadatas=[{
            "type": "document_summary",
            "content_type": summary["content_type"],
            "category": "reimbursement_guide"
        }],
        ids=[f"doc_summary_{uuid.uuid4()}"]
    )
```

### 不同内容类型的总结

```python
# 技术文档总结
tech_content = """
Python编程语言基础教程...
"""

tech_result = store.summarize_text_content(
    tech_content, 
    max_length=200, 
    content_type="技术文档"
)

# 表格数据总结
table_content = """
销售数据报表
产品A  100  50  5000
产品B  200  30  6000
...
"""

table_result = store.summarize_text_content(
    table_content, 
    max_length=150, 
    content_type="数据表格"
)

# 政策文档总结
policy_content = """
公司差旅报销政策...
"""

policy_result = store.summarize_text_content(
    policy_content, 
    max_length=300, 
    content_type="政策文档"
)
```

## 内容类型建议

系统支持多种内容类型，建议根据实际内容选择合适的类型：

- **"text"**: 通用文本内容（默认）
- **"政策文档"**: 政策、规定、制度等文档
- **"技术文档"**: 技术说明、操作手册等
- **"数据表格"**: 表格数据、报表等
- **"发票说明"**: 发票相关说明文档
- **"流程文档"**: 操作流程、工作流程等
- **"费用标准"**: 费用标准、报销标准等
- **"操作指南"**: 操作步骤、使用说明等

## 总结提示模板

系统使用以下提示模板来指导大模型进行总结：

```
请对以下{content_type}内容进行总结，要求：
1. 总结要简洁明了，突出重点信息
2. 总结长度控制在{max_length}字符以内
3. 保留关键的业务信息、数据、结论等
4. 如果是表格或结构化数据，提取主要数据点
5. 如果是政策文档，提取核心条款和要求
6. 如果是技术文档，提取主要概念和步骤

内容类型: {content_type}
内容长度: {len(content)} 字符

内容:
{content}

请提供总结：
```

## 错误处理

系统会处理以下类型的错误：

1. **文本内容为空**：检查输入内容是否为空
2. **大模型调用失败**：处理网络和API调用错误
3. **总结结果为空**：检查大模型返回的结果
4. **参数错误**：检查输入参数的有效性

## 性能考虑

- **大文本处理**：对于非常大的文本，建议先进行内容预处理
- **批量处理**：批量处理时注意内存使用，避免同时处理过多内容
- **网络延迟**：大模型调用可能有网络延迟，建议添加超时处理
- **并发处理**：可以考虑使用异步处理来提高批量处理的效率

## 最佳实践

1. **合理设置总结长度**：根据实际需求设置合适的总结长度
2. **选择合适的内容类型**：根据内容特点选择合适的内容类型
3. **错误监控**：监控总结失败的内容，及时处理问题
4. **结果验证**：对重要的总结结果进行人工验证
5. **缓存机制**：对于重复处理的内容，可以考虑添加缓存机制

## 注意事项

- 确保大模型服务正常运行
- 检查网络连接和API密钥配置
- 注意文本编码格式，建议使用UTF-8编码
- 对于敏感内容，注意总结内容的安全性
- 合理控制总结长度，避免信息丢失 