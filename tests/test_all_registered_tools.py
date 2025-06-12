#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from src.tool.registry import tool_registry

async def test_tool(tool_name, test_params):
    """测试指定的工具
    
    Args:
        tool_name: 工具名称
        test_params: 测试参数
        
    Returns:
        测试结果
    """
    print(f"\n测试工具: {tool_name}")
    print(f"参数: {json.dumps(test_params, ensure_ascii=False, indent=2)}")
    
    try:
        # 执行工具
        result = await tool_registry.execute_tool(tool_name, test_params)
        
        # 打印结果
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}..." if len(json.dumps(result)) > 200 else f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 返回成功结果
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        print(f"错误: {str(e)}")
        
        # 返回错误结果
        return {
            "success": False,
            "error": str(e)
        }

async def main():
    """主函数"""
    print("开始测试所有注册的工具...")
    
    # 获取所有工具
    tools = tool_registry.get_all_tools()
    print(f"找到 {len(tools)} 个已注册工具\n")
    
    # 创建测试结果目录
    result_dir = "tool_test_results"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    # 测试参数
    test_params = {
        "process_invoices": {
            "file_paths": ["data/invoices/test1.jpg", "data/invoices/test2.pdf"],
            "user_id": "test_user_001",
            "auto_verify": True
        },
        "manage_expense_records": {
            "invoice_ids": ["INV-20250501-001", "INV-20250501-002"],
            "action": "create",
            "supplement_data": {
                "category": "差旅费",
                "project_code": "PRJ-2025-001"
            }
        },
        "manage_reimbursement": {
            "action": "create",
            "expense_record_ids": ["EXP-001", "EXP-002"]
        },
        "submit_reimbursement": {
            "bill_id": "BILL-20250601-001",
            "validate_only": True
        },
        "query_status": {
            "query_type": "bill_list",
            "user_id": "test_user_001",
            "filters": {
                "status": "pending"
            }
        },
        "query_travel_applications": {
            "user_id": "test_user_001",
            "date_range": {
                "start_date": "2025-01-01",
                "end_date": "2025-06-30"
            },
            "status_filter": "all"
        },
        "process_allowance": {
            "action": "check_eligibility",
            "user_id": "test_user_001",
            "trip_order_id": "TA-12345"
        }
    }
    
    # 记录测试结果
    results = {}
    
    # 测试每个工具
    for tool in tools:
        tool_name = tool.name
        
        if tool_name in test_params:
            # 测试工具
            result = await test_tool(tool_name, test_params[tool_name])
            
            # 记录结果
            results[tool_name] = result
            
            # 保存结果到文件
            with open(f"{result_dir}/{tool_name}_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            print(f"\n跳过工具 {tool_name}，未找到测试参数")
    
    # 保存汇总结果
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_tools": len(tools),
        "tested_tools": len(results),
        "success_count": sum(1 for r in results.values() if r["success"]),
        "fail_count": sum(1 for r in results.values() if not r["success"]),
        "results": results
    }
    
    with open(f"{result_dir}/test_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # 打印汇总信息
    print("\n测试完成！")
    print(f"总计: {summary['total_tools']} 个工具")
    print(f"已测试: {summary['tested_tools']} 个工具")
    print(f"成功: {summary['success_count']} 个工具")
    print(f"失败: {summary['fail_count']} 个工具")
    print(f"\n详细结果已保存到 {result_dir}/test_summary.json")

if __name__ == "__main__":
    asyncio.run(main()) 