# ChromaDB 遥测问题解决方案

## 问题描述

在LangGraph开发环境中，ChromaDB会尝试发送遥测数据，这会导致以下警告：

```
Failed to send telemetry event CollectionQueryEvent: Blocking call to io.BufferedReader.read
```

这是因为ChromaDB在ASGI环境中使用了同步阻塞调用，会影响应用性能。

## 解决方案

### 1. 环境变量设置

在应用启动前设置以下环境变量：

```bash
export CHROMA_TELEMETRY_ENABLED=false
export CHROMA_ANONYMIZED_TELEMETRY=false
export CHROMA_SERVER_TELEMETRY_ENABLED=false
export CHROMA_CLIENT_TELEMETRY_ENABLED=false
```

### 2. 代码层面设置

在ChromaDB客户端初始化时添加设置：

```python
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path=persist_directory,
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True,
        persist_directory=persist_directory
    )
)
```

### 3. 使用启动脚本

使用提供的 `start_dev.py` 脚本启动应用：

```bash
python start_dev.py
```

这个脚本会自动设置所有必要的环境变量。

## 已修复的文件

1. `src/config.py` - 添加环境变量设置
2. `src/vector_store/chroma_store.py` - 更新ChromaDB客户端配置
3. `src/vector_store/view_data.py` - 更新客户端配置
4. `app.py` - 添加环境变量设置
5. `start_dev.py` - 创建专用启动脚本

## 验证

启动应用后，应该不再看到遥测相关的警告信息。如果仍然出现警告，可以：

1. 检查环境变量是否正确设置
2. 重启应用
3. 清除ChromaDB缓存（如果存在）

## 注意事项

- 这些设置只影响遥测功能，不会影响ChromaDB的核心功能
- 在生产环境中，建议也禁用遥测以提高性能
- 如果使用Docker，需要在容器启动时设置环境变量 