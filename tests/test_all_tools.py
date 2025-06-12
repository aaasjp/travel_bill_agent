import json
from src.tool.registry import tool_registry

def test_all_tools():
    """测试所有注册的工具"""
    print(f"测试所有工具 ({len(tool_registry.get_all_tools())}个)...")
    
    # 获取所有工具的schema
    schemas = tool_registry.get_all_schemas()
    print(f"工具schema数量: {len(schemas)}\n")
    
    # 打印所有工具的名称和描述
    print("已注册的工具:")
    for i, tool in enumerate(tool_registry.get_all_tools(), 1):
        print(f"{i}. {tool.name}: {tool.description}")
    print()
    
    # 测试ReimbursementStatusTool
    test_reimbursement_status_tool()
    
    # 测试ExpenseRecordTool
    test_expense_record_tool()
    
    # 测试ReimbursementFormTool
    test_reimbursement_form_tool()
    
    # 测试AuditReimbursementTool
    test_audit_reimbursement_tool()
    
    # 测试PrintReimbursementTool
    test_print_reimbursement_tool()
    
    # 测试PaymentProcessTool
    test_payment_process_tool()
    
    print("所有测试完成!")

def test_reimbursement_status_tool():
    """测试报销状态查询工具"""
    print("\n========== 测试报销状态查询工具 ==========")
    
    # 获取工具
    tool = tool_registry.get_tool("reimbursement_status")
    if not tool:
        print("工具不存在!")
        return
    
    # 准备参数
    params = {
        "reimbursement_id": "EXP123456",
        "employee_id": "EMP789"
    }
    
    # 执行工具
    try:
        result = tool.execute(**params)
        print_result("报销状态查询", result)
    except Exception as e:
        print(f"执行失败: {e}")

def test_expense_record_tool():
    """测试支出记录工具"""
    print("\n========== 测试支出记录工具 ==========")
    
    # 获取工具
    tool = tool_registry.get_tool("expense_record")
    if not tool:
        print("工具不存在!")
        return
    
    # 准备参数
    params = {
        "expense_type": "报销",
        "description": "北京出差住宿费",
        "category": "差旅费",
        "department": "研发部",
        "amount": 850.00,
        "date": "2023-06-15"
    }
    
    # 执行工具
    try:
        result = tool.execute(**params)
        print_result("支出记录", result)
    except Exception as e:
        print(f"执行失败: {e}")

def test_reimbursement_form_tool():
    """测试报销表单工具"""
    print("\n========== 测试报销表单工具 ==========")
    
    # 获取工具
    tool = tool_registry.get_tool("reimbursement_form")
    if not tool:
        print("工具不存在!")
        return
    
    # 准备参数
    params = {
        "title": "北京出差报销",
        "reason": "参加行业研讨会",
        "submitter": "张三",
        "department": "研发部",
        "expense_record_ids": ["exp-123", "exp-456"]
    }
    
    # 执行工具
    try:
        result = tool.execute(**params)
        print_result("报销表单", result)
    except Exception as e:
        print(f"执行失败: {e}")

def test_audit_reimbursement_tool():
    """测试报销稽核工具"""
    print("\n========== 测试报销稽核工具 ==========")
    
    # 获取工具
    tool = tool_registry.get_tool("audit_reimbursement")
    if not tool:
        print("工具不存在!")
        return
    
    # 准备参数
    params = {
        "form_id": "form-123",
        "auditor_name": "李财务",
        "comments": "费用符合公司规定"
    }
    
    # 执行工具
    try:
        result = tool.execute(**params)
        print_result("报销稽核", result)
    except Exception as e:
        print(f"执行失败: {e}")

def test_print_reimbursement_tool():
    """测试报销单打印工具"""
    print("\n========== 测试报销单打印工具 ==========")
    
    # 获取工具
    tool = tool_registry.get_tool("print_reimbursement")
    if not tool:
        print("工具不存在!")
        return
    
    # 准备参数
    params = {
        "form_id": "form-123",
        "format": "pdf",
        "include_instructions": True
    }
    
    # 执行工具
    try:
        result = tool.execute(**params)
        print_result("报销单打印", result)
    except Exception as e:
        print(f"执行失败: {e}")

def test_payment_process_tool():
    """测试付款处理工具"""
    print("\n========== 测试付款处理工具 ==========")
    
    # 获取工具
    tool = tool_registry.get_tool("payment_process")
    if not tool:
        print("工具不存在!")
        return
    
    # 准备参数
    params = {
        "form_id": "form-123",
        "payment_method": "bank_transfer",
        "operator_name": "王出纳"
    }
    
    # 执行工具
    try:
        result = tool.execute(**params)
        print_result("付款处理", result)
    except Exception as e:
        print(f"执行失败: {e}")

def print_result(title, result):
    """打印工具执行结果"""
    print(f"【{title}】执行结果:")
    formatted_json = json.dumps(result, ensure_ascii=False, indent=2)
    print(formatted_json)
    print()

if __name__ == "__main__":
    test_all_tools() 