from memory_store import MemoryStore, MemoryType
import time

def main():
    # 初始化记忆存储
    memory_store = MemoryStore("memory_data")
    
    print("=== 开始记忆存储示例 ===")
    
    # 1. 存储出差申请记忆
    print("\n1. 存储出差申请")
    trip_application_id = memory_store.add_memory(
        name="出差申请",
        content="小宋提交了出差申请，出差地点为北京，出差时间为2025年6月8日-2025年6月10日，出差事由为参加会议",
        memory_type=MemoryType.TASK,
        meta_data={
            "applicant": "小宋",
            "destination": "北京",
            "start_date": "2025-06-08",
            "end_date": "2025-06-10",
            "purpose": "参加会议",
            "status": "已提交"
        }
    )
    print(f"已存储出差申请，ID: {trip_application_id}")
    
    # 2. 存储火车票信息
    print("\n2. 存储火车票信息")
    train_ticket_id = memory_store.add_memory(
        name="火车票信息",
        content="小宋上传了火车票，车次G212，青岛到北京，出发时间2025年6月8日，到达时间2025年6月8日，票价330元",
        memory_type=MemoryType.FACT,
        meta_data={
            "train_number": "G212",
            "departure": "青岛",
            "arrival": "北京",
            "departure_time": "2025-06-08",
            "arrival_time": "2025-06-08",
            "price": 330,
            "currency": "CNY"
        }
    )
    print(f"已存储火车票信息，ID: {train_ticket_id}")
    
    # 等待一小段时间，确保时间戳不同
    time.sleep(1)
    
    print("\n=== 开始记忆检索示例 ===")
    
    # 3. 检索出差申请
    print("\n3. 检索出差申请")
    trip_application = memory_store.get_memory(trip_application_id)
    print(f"出差申请内容: {trip_application.content}")
    print(f"元数据: {trip_application.meta_data}")
    
    # 4. 按类型搜索记忆
    print("\n4. 搜索所有任务类型记忆")
    task_memories = memory_store.search_by_type(MemoryType.TASK)
    for task in task_memories:
        print(f"- {task.name}: {task.content}")
        print(f"  元数据: {task.meta_data}")
    
    # 5. 按内容搜索记忆
    print("\n5. 搜索包含'北京'的记忆")
    beijing_memories = memory_store.search_by_content("北京")
    for memory in beijing_memories:
        print(f"- {memory.name} ({memory.memory_type.value}): {memory.content}")
    
    # 6. 按元数据搜索记忆
    print("\n6. 搜索目的地为北京的记忆")
    beijing_trip_memories = memory_store.search_by_metadata({"destination": "北京"})
    for memory in beijing_trip_memories:
        print(f"- {memory.name}: {memory.content}")
        print(f"  元数据: {memory.meta_data}")
    
    # 7. 获取最新记忆
    print("\n7. 获取最新的两条记忆")
    latest_memories = memory_store.get_latest_memories(2)
    for memory in latest_memories:
        print(f"- {memory.name} ({memory.create_time}): {memory.content}")
    
    # 8. 更新出差申请状态
    print("\n8. 更新出差申请状态")
    memory_store.update_memory(
        trip_application_id,
        content="小宋提交了出差申请，出差地点为北京，出差时间为2025年6月8日-2025年6月10日，出差事由为参加会议，已审批通过",
        meta_data={
            "applicant": "小宋",
            "destination": "北京",
            "start_date": "2025-06-08",
            "end_date": "2025-06-10",
            "purpose": "参加会议",
            "status": "已审批通过",
            "approval_time": "2025-06-07"
        }
    )
    
    # 验证更新
    updated_application = memory_store.get_memory(trip_application_id)
    print(f"更新后的出差申请: {updated_application.content}")
    print(f"更新后的元数据: {updated_application.meta_data}")

if __name__ == "__main__":
    main() 