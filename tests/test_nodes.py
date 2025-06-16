import sys
import os
import json
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.nodes.analysis import AnalysisNode
from src.states.state import State
from datetime import datetime

async def test_intent_node():
    # 初始化节点
    intent_node = AnalysisNode()
    
    # 创建初始状态
    state = State(
        task_id="test_task",
        user_input="我要申请3月15-17日北京出差的报销",
        intent={},
        plan=[],
        context={},
        execution_log=[],
        current_step=0,
        results={},
        errors=[],
        reflection={},
        final_output="",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 调用节点
    print("开始处理意图...")
    try:
        updated_state = await intent_node(state)
        
        # 打印结果
        print("\n意图识别结果:")
        print(json.dumps(updated_state["intent"], ensure_ascii=False, indent=2))
        
        print("\n上下文:")
        print(json.dumps(updated_state["context"], ensure_ascii=False, indent=2))
        
        if updated_state["errors"]:
            print("\n错误:")
            print(json.dumps(updated_state["errors"], ensure_ascii=False, indent=2))
            
        return True
    except Exception as e:
        print(f"节点处理失败: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_intent_node()) 