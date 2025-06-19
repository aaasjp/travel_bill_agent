## 记忆搜索示例

from .memory_store import MemoryStore

def main():
    # 初始化记忆存储
    memory_store = MemoryStore()
    
    # 添加记忆
    memory_store.add_memory_by_llm("用户小宋在2025年6月8日10:00:00提交了出差申请，出差地点为北京，出差时间为2025年6月8日-2025年6月10日，出差事由为参加会议。")
    memory_store.add_memory_by_llm("用户小宋在2025年6月11日上传了一张火车票，火车车次是G212,出发地为青岛，目的地为北京，出发时间为2025年6月8日，到达时间为2025年6月8日，票价为330元。")

    # 搜索记忆
    memories = memory_store.search_by_llm("把我去北京出差的火车票报销了",top_k=1)
    for memory in memories:
        print(memory.to_dict())


if __name__ == "__main__":
    main()