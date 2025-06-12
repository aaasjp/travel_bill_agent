import asyncio
import json
from src.tool.registry import tool_registry
from src.tool.reimbursement_status import ReimbursementStatusTool

def test_reimbursement_status_tool():
    """测试报销状态查询工具"""
    print("测试报销状态查询工具...")
    
    # 测试参数
    test_args = {
        "reimbursement_id": "EXP123456",
        "employee_id": "EMP789"
    }
    
    # 直接使用工具实例
    tool = ReimbursementStatusTool()
    result = tool.execute(**test_args)
    
    # 打印结果
    print(f"工具名称: {tool.name}")
    print(f"工具描述: {tool.description}")
    print(f"工具参数: {json.dumps(tool.parameters, ensure_ascii=False, indent=2)}")
    print(f"执行结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 验证结果
    assert result is not None
    assert "status" in result
    assert "reimbursement_id" in result
    assert result["reimbursement_id"] == test_args["reimbursement_id"]
    
    print("报销状态查询工具测试通过!\n")

def test_tool_registry():
    """测试工具注册表"""
    print("测试工具注册表...")
    
    # 获取所有工具
    tools = tool_registry.get_all_tools()
    print(f"已注册工具数量: {len(tools)}")
    
    # 获取工具schema
    schemas = tool_registry.get_all_schemas()
    print(f"工具schema数量: {len(schemas)}")
    
    # 遍历所有工具
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    
    # 测试工具注册
    test_tool = ReimbursementStatusTool()
    tool_registry.register(test_tool)
    
    # 测试通过注册表执行工具
    test_args = {
        "reimbursement_id": "EXP123456",
        "employee_id": "EMP789"
    }
    
    result = tool_registry.execute_tool("reimbursement_status", test_args)
    assert result is not None
    assert "status" in result
    
    print("工具注册表测试通过!\n")

if __name__ == "__main__":
    # 运行测试
    test_reimbursement_status_tool()
    test_tool_registry()
    
    print("所有测试通过!") 