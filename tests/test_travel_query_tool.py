#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
from src.tool.registry import tool_registry

async def main():
    print("开始测试差旅申请查询工具...")
    
    # 获取工具
    tool = tool_registry.get_tool("query_travel_applications")
    if not tool:
        print("错误：差旅申请查询工具未注册")
        return
    
    print(f"找到工具: {tool.name}")
    print(f"描述: {tool.description}")
    
    # 测试参数
    test_params = {
        "user_id": "test_user_001",
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-06-30"
        },
        "status_filter": "all"
    }
    
    print(f"\n测试参数: {json.dumps(test_params, ensure_ascii=False, indent=2)}")
    
    try:
        # 执行工具
        result = await tool_registry.execute_tool("query_travel_applications", test_params)
        
        # 打印结果
        print("\n查询结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 保存结果到文件
        with open("travel_query_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\n结果已保存到 travel_query_result.json")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 