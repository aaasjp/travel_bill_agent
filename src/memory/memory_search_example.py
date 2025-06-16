## 记忆搜索示例

from memory_store import MemoryStore, MemoryType

def main():
    # 初始化记忆存储
    memory_store = MemoryStore("memory_data")
    
    # 搜索记忆
    memories = memory_store.search_by_llm("把我去北京出差的火车票报销了",top_k=1)
    for memory in memories:
        print(memory.to_dict())

if __name__ == "__main__":
    main()