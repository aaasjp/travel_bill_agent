"""测试工具注册"""
from src.tool.registry import tool_registry

def main():
    """主函数"""
    # 获取所有已注册工具
    tools = tool_registry.get_all_tools()
    
    # 打印工具数量
    print(f"已注册工具数量: {len(tools)}")
    
    # 打印工具列表
    if tools:
        print("已注册工具列表:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
    else:
        print("没有已注册的工具")

if __name__ == "__main__":
    main() 