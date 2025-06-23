#!/usr/bin/env python3
"""
测试决策节点功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.nodes.decision import DecisionNode
from src.states.state import create_state

async def test_decision_node():
    """测试决策节点功能"""
    
    # 创建测试状态
    test_state = create_state(
        task_id="test_task_001",
        user_input="我需要报销差旅费用，包括机票、住宿和餐饮费用",
        client_id="test_client",
        user_info={
            "姓名": "张三",
            "工号": "EMP001",
            "部门": "技术部",
            "职位": "软件工程师",
            "手机号": "13800138000",
            "邮箱": "zhangsan@company.com"
        }
    )
    
    # 添加模拟的计划
    test_state["plan"] = [
        {
            "step": 1,
            "description": "查询用户差旅申请信息",
            "step_desc": "查询差旅申请"
        },
        {
            "step": 2,
            "description": "上传差旅费用发票",
            "step_desc": "上传发票"
        },
        {
            "step": 3,
            "description": "填写差旅费用明细",
            "step_desc": "填写费用明细"
        },
        {
            "step": 4,
            "description": "提交差旅报销申请",
            "step_desc": "提交报销申请"
        }
    ]
    
    # 添加模拟的意图分析
    test_state["intent"] = {
        "intent": "差旅报销",
        "confidence": 0.95,
        "entities": {
            "expense_type": ["机票", "住宿", "餐饮"],
            "action": "报销"
        }
    }
    
    # 添加模拟的记忆信息
    test_state["memory_records"] = [
        {
            "name": "用户偏好",
            "content": "用户通常选择经济舱机票，住宿标准为300-500元/晚"
        },
        {
            "name": "历史报销",
            "content": "用户上个月报销了北京出差费用，总金额2800元"
        }
    ]
    
    # 添加模拟的对话历史
    test_state["messages"] = [
        {"role": "user", "content": "我想报销差旅费用"},
        {"role": "assistant", "content": "好的，我来帮您处理差旅报销。请告诉我具体的出差信息。"},
        {"role": "user", "content": "我上周去上海出差了，需要报销机票、住宿和餐饮费用"}
    ]
    
    # 创建决策节点
    decision_node = DecisionNode()
    
    print("开始测试决策节点...")
    print("=" * 50)
    
    # 执行决策
    result_state = await decision_node(test_state)
    
    print("决策结果:")
    print("=" * 50)
    
    # 显示步骤工具信息
    step_tools = result_state.get("step_tools", [])
    print(f"步骤工具数量: {len(step_tools)}")
    
    for i, step_tool in enumerate(step_tools):
        print(f"\n步骤 {i+1}:")
        print(f"  步骤索引: {step_tool.get('step_index', 'N/A')}")
        print(f"  步骤描述: {step_tool.get('step_description', 'N/A')}")
        
        tools = step_tool.get("tools", [])
        print(f"  工具数量: {len(tools)}")
        
        for j, tool in enumerate(tools):
            print(f"    工具 {j+1}: {tool.get('name', 'N/A')}")
            print(f"      参数: {json.dumps(tool.get('parameters', {}), ensure_ascii=False, indent=6)}")
            print(f"      推理: {tool.get('reasoning', 'N/A')}")
    
    # 显示工具调用信息
    tool_calls = result_state.get("tool_calls", [])
    print(f"\n总工具调用数量: {len(tool_calls)}")
    
    for i, tool_call in enumerate(tool_calls):
        print(f"\n工具调用 {i+1}:")
        print(f"  名称: {tool_call.get('name', 'N/A')}")
        print(f"  参数: {json.dumps(tool_call.get('parameters', {}), ensure_ascii=False, indent=4)}")
        print(f"  推理: {tool_call.get('reasoning', 'N/A')}")
        print(f"  步骤索引: {tool_call.get('step_index', 'N/A')}")
    
    # 显示完成状态
    print(f"\n任务完成状态: {result_state.get('is_complete', False)}")
    if result_state.get("final_output"):
        print(f"最终输出: {result_state.get('final_output')}")
    
    # 显示错误信息
    errors = result_state.get("errors", [])
    if errors:
        print(f"\n错误信息:")
        for error in errors:
            print(f"  {error}")

if __name__ == "__main__":
    asyncio.run(test_decision_node()) 