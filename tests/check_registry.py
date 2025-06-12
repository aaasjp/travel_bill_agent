#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.tool.registry import tool_registry
import json

def main():
    # 获取已注册工具
    tools = tool_registry.get_all_tools()
    
    # 准备输出内容
    output = []
    output.append(f"Registered tools count: {len(tools)}")
    output.append("Registered tools list:")
    
    for tool in tools:
        output.append(f"- {tool.name}: {tool.description}")
    
    output.append("\nAvailable tool schemas:")
    schemas = tool_registry.get_all_schemas()
    for schema in schemas:
        output.append(f"- {schema['name']}")
    
    # 准备工具详细信息
    tool_details = []
    for tool in tools:
        tool_details.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        })
    
    # 打印到控制台
    for line in output:
        print(line)
    
    # 保存到文件
    with open("tool_registry_output.txt", "w", encoding="utf-8") as f:
        for line in output:
            f.write(line + "\n")
    
    # 保存详细信息到JSON文件
    with open("tool_registry_details.json", "w", encoding="utf-8") as f:
        json.dump(tool_details, f, ensure_ascii=False, indent=2)
    
    print("\nOutput saved to tool_registry_output.txt")
    print("Details saved to tool_registry_details.json")

if __name__ == "__main__":
    main() 