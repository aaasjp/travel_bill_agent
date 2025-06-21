# 大模型相似性判断功能

## 概述

在 `ChromaStore` 类中新增了 `use_llm_similarity` 参数，允许使用大模型在向量相似度过滤之后进行进一步的相似性判断和排序优化。

## 功能特点

1. **两阶段过滤**: 首先进行向量相似度阈值过滤，然后使用大模型进行排序优化
2. **智能排序**: 使用大模型分析查询内容与文档摘要、文件名的语义相关性，重新排序结果
3. **多维度评估**: 考虑内容主题匹配度、关键词匹配度、语义相关性和业务场景匹配度
4. **回退机制**: 当大模型不可用时，保持原始向量相似度排序
5. **阈值控制**: 支持设置相似度阈值，过滤低相关性文档

## 工作原理

### 1. 向量相似度过滤（第一阶段）
首先通过向量搜索获取候选文档，并根据 `similarity_threshold` 进行初步过滤：
- 计算向量距离并转换为相似度
- 过滤掉相似度低于阈值的文档
- 保留指定数量的候选文档

### 2. 大模型排序优化（第二阶段）
对通过向量过滤的文档进行大模型判断和排序优化：
- 提取文档ID、文件名、摘要等信息
- 使用大模型评估文档与查询的相关性
- 根据大模型判断重新排序结果
- 返回优化后的文档列表

## 使用方法

### 基本用法

```python
from src.vector_store.chroma_store import ChromaStore

# 初始化向量存储
chroma_store = ChromaStore()
chroma_store.create_collection("your_collection_name")

# 使用大模型进行相似性搜索和排序优化
results = chroma_store.search(
    query_texts=["差旅报销流程"],
    n_results=5,
    use_llm_similarity=True,  # 启用大模型相似性判断
    similarity_threshold=0.7   # 设置相似度阈值
)
```

### 参数说明

- `query_texts`: 查询文本列表
- `n_results`: 返回结果数量
- `where`: 过滤条件（可选）
- `similarity_threshold`: 相似度阈值，范围0-1（可选，默认0.0）
- `use_llm_similarity`: 是否使用大模型进行相似性判断（可选，默认False）

### 返回结果

返回结果格式与普通搜索相同：

```python
{
    "ids": [["doc_id_1", "doc_id_2", ...]],
    "distances": [[0.1, 0.2, ...]],
    "metadatas": [[{"filename": "...", "summary": "...", ...}, ...]],
    "documents": [["文档内容1", "文档内容2", ...]]
}
```

## 使用场景

### 场景1: 高精度搜索
```python
# 先进行严格的向量过滤，再用大模型优化排序
results = chroma_store.search(
    query_texts=["如何申请差旅报销？"],
    n_results=3,
    use_llm_similarity=True,
    similarity_threshold=0.8  # 高阈值确保基础相关性
)
```

### 场景2: 语义优化搜索
```python
# 使用较低的向量阈值，主要依赖大模型进行语义判断
results = chroma_store.search(
    query_texts=["报销标准是什么？"],
    n_results=5,
    use_llm_similarity=True,
    similarity_threshold=0.3  # 低阈值，让大模型发挥更大作用
)
```

### 场景3: 纯大模型优化
```python
# 不使用向量阈值过滤，完全依赖大模型判断
results = chroma_store.search(
    query_texts=["差旅政策"],
    n_results=5,
    use_llm_similarity=True,
    similarity_threshold=0.0  # 不进行向量阈值过滤
)
```

## 性能考虑

1. **响应时间**: 使用大模型会增加响应时间，因为需要调用LLM API
2. **成本**: 每次大模型判断都会消耗API调用次数
3. **准确性**: 两阶段过滤通常比单一方法更准确
4. **效率**: 向量过滤减少了候选文档数量，降低了大模型处理成本

## 最佳实践

1. **合理设置阈值**: 
   - 高阈值（0.7-0.9）：确保基础相关性，大模型主要用于排序优化
   - 中等阈值（0.4-0.6）：平衡向量过滤和大模型判断
   - 低阈值（0.1-0.3）：主要依赖大模型进行语义判断

2. **文档摘要**: 确保文档有高质量的摘要，提高大模型判断准确性

3. **错误处理**: 代码中已包含回退机制，但仍建议在应用层处理可能的异常

4. **缓存策略**: 对于频繁查询，可以考虑缓存大模型判断结果

## 测试

运行测试脚本验证功能：

```bash
cd src/vector_store
python test_llm_similarity.py
```

测试脚本会对比：
- 只使用向量相似度过滤的结果
- 向量过滤 + 大模型优化的结果
- 检查文档集合和排序的差异

## 注意事项

1. 确保大模型服务可用
2. 文档需要有摘要信息才能发挥大模型判断的优势
3. 相似度阈值设置过高可能导致结果为空
4. 建议在开发环境中充分测试后再部署到生产环境
5. 大模型判断是在向量过滤之后进行的，不会增加候选文档数量 