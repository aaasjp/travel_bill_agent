#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试决策节点中集成的参数验证功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.states.state import create_state
from src.nodes.decision import DecisionNode
from src.nodes.tool_execution import ToolExecutionNode
from src.nodes.human_intervention import HumanInterventionNode

async def test_decision_with_parameter_validation():
    """测试决策节点中的参数验证功能"""
    print("=== 测试决策节点中的参数验证功能 ===")
    
    # 创建测试状态
    state = create_state(
        task_id="test_task_001",
        user_input="我需要上传发票并查询费用类型字段规则",
        user_info={
            "name": "张三",
            "employee_id": "EMP001",
            "department": "技术部"
        }
    )
    
    # 模拟规划节点的输出
    state["plan"] = [
        {
            "step_id": "step_1",
            "step_name": "上传发票",
            "step_desc": "上传发票文件"
        },
        {
            "step_id": "step_2",
            "step_name": "获取费用类型字段规则",
            "step_desc": "获取费用类型的字段规则"
        }
    ]
    
    # 创建决策节点
    decision_node = DecisionNode()
    
    # 执行决策和参数验证
    print("执行决策和参数验证...")
    state = await decision_node(state)
    
    # 打印结果
    print(f"状态: {state.get('status')}")
    print(f"需要人工干预: {state.get('needs_human_intervention')}")
    
    if state.get("needs_human_intervention"):
        print("需要人工干预，缺失参数:")
        intervention_request = state.get("intervention_request", {})
        missing_params = intervention_request.get("missing_parameters", [])
        for param in missing_params:
            print(f"  - {param}")
    
    # 打印参数验证结果
    validation_results = state.get("parameter_validation_results", {})
    print(f"\n参数验证结果:")
    for key, result in validation_results.items():
        print(f"  {key}: {'有效' if result.get('is_valid') else '无效'}")
        if not result.get('is_valid'):
            print(f"    缺失参数: {result.get('missing_params', [])}")
    
    # 打印待执行工具列表
    pending_tools = state.get("pending_tools", [])
    print(f"\n待执行工具列表:")
    for tool in pending_tools:
        print(f"  - {tool.get('tool_name')}: {tool.get('parameters')}")
    
    return state

async def test_human_intervention_feedback():
    """测试人工干预反馈处理"""
    print("\n=== 测试人工干预反馈处理 ===")
    
    # 使用上一个测试的状态
    state = await test_decision_with_parameter_validation()
    
    if not state.get("needs_human_intervention"):
        print("不需要人工干预")
        return state
    
    # 创建人工干预节点
    intervention_node = HumanInterventionNode()
    
    # 执行人工干预
    print("执行人工干预...")
    state = await intervention_node(state)
    
    print(f"状态: {state.get('status')}")
    
    # 模拟人工反馈
    print("模拟人工反馈...")
    feedback = {
        "action": "provide_parameters",
        "parameters": {
            "file_path": "/path/to/invoice.pdf"
        }
    }
    
    # 处理反馈
    state = await intervention_node.handle_parameter_intervention_feedback(state, feedback)
    
    print(f"反馈处理后状态: {state.get('status')}")
    
    # 如果有干预响应，处理决策节点的反馈
    if state.get("intervention_response"):
        print("处理决策节点的参数反馈...")
        decision_node = DecisionNode()
        state = await decision_node.handle_parameter_feedback(state, state["intervention_response"])
        print(f"决策节点反馈处理后状态: {state.get('status')}")
    
    return state

async def test_tool_execution():
    """测试工具执行"""
    print("\n=== 测试工具执行 ===")
    
    # 创建测试状态（参数完整的工具）
    state = create_state(
        task_id="test_task_002",
        user_input="我需要查询费用类型字段规则",
        user_info={
            "name": "李四",
            "employee_id": "EMP002", 
            "department": "财务部"
        }
    )
    
    # 模拟规划节点的输出
    state["plan"] = [
        {
            "step_id": "step_1",
            "step_name": "获取费用类型字段规则",
            "step_desc": "获取费用类型的字段规则"
        }
    ]
    
    # 创建决策节点
    decision_node = DecisionNode()
    
    # 执行决策
    print("执行决策...")
    state = await decision_node(state)
    
    print(f"决策后状态: {state.get('status')}")
    
    if state.get("status") == "ready_for_execution":
        # 创建工具执行节点
        tool_execution_node = ToolExecutionNode()
        
        # 执行工具
        print("执行工具...")
        state = await tool_execution_node(state)
        
        # 获取执行摘要
        summary = tool_execution_node.get_execution_summary(state)
        print(f"执行摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    return state

async def test_full_workflow():
    """测试完整工作流"""
    print("\n=== 测试完整工作流 ===")
    
    # 创建测试状态
    state = create_state(
        task_id="test_task_003",
        user_input="我需要上传发票并创建报销单",
        user_info={
            "name": "王五",
            "employee_id": "EMP003",
            "department": "销售部"
        }
    )
    
    # 模拟规划节点的输出
    state["plan"] = [
        {
            "step_id": "step_1",
            "step_name": "上传发票",
            "step_desc": "上传发票文件"
        },
        {
            "step_id": "step_2",
            "step_name": "获取费用类型字段规则", 
            "step_desc": "获取费用类型的字段规则"
        }
    ]
    
    # 创建节点
    decision_node = DecisionNode()
    tool_execution_node = ToolExecutionNode()
    intervention_node = HumanInterventionNode()
    
    # 执行决策
    print("执行决策...")
    state = await decision_node(state)
    
    print(f"决策后状态: {state.get('status')}")
    print(f"需要人工干预: {state.get('needs_human_intervention')}")
    
    if state.get("needs_human_intervention"):
        print("需要人工干预，等待人工反馈...")
        
        # 执行人工干预
        state = await intervention_node(state)
        
        # 模拟人工反馈
        feedback = {
            "action": "provide_parameters",
            "parameters": {
                "file_path": "/path/to/invoice.pdf"
            }
        }
        
        # 处理反馈
        state = await intervention_node.handle_parameter_intervention_feedback(state, feedback)
        
        # 处理决策节点的反馈
        if state.get("intervention_response"):
            state = await decision_node.handle_parameter_feedback(state, state["intervention_response"])
        
        print(f"反馈处理后状态: {state.get('status')}")
    
    # 执行工具
    if state.get("status") == "ready_for_execution":
        print("执行工具...")
        state = await tool_execution_node(state)
        
        # 获取执行摘要
        summary = tool_execution_node.get_execution_summary(state)
        print(f"执行摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    return state

async def main():
    """主函数"""
    print("开始测试决策节点中集成的参数验证功能...")
    
    # 测试决策节点中的参数验证
    await test_decision_with_parameter_validation()
    
    # 测试人工干预反馈处理
    await test_human_intervention_feedback()
    
    # 测试工具执行
    await test_tool_execution()
    
    # 测试完整工作流
    await test_full_workflow()
    
    print("\n所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main()) 