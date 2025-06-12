"""
测试新创建的LangGraph工具
"""
import asyncio
import json
from src.tool import (
    InvoiceProcessingTool,
    ExpenseRecordManagementTool,
    ReimbursementManagementTool,
    ReimbursementSubmissionTool,
    StatusQueryTool,
    TravelApplicationQueryTool,
    AllowanceProcessingTool
)

async def test_invoice_processing_tool():
    """测试发票处理工具"""
    print("\n=== 测试发票处理工具 ===")
    tool = InvoiceProcessingTool()
    result = await tool.execute(
        file_paths=["发票1.pdf", "发票2.jpg", "发票3.png"],
        user_id="user-001",
        auto_verify=True
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

async def test_expense_record_management_tool():
    """测试支出记录管理工具"""
    print("\n=== 测试支出记录管理工具 ===")
    tool = ExpenseRecordManagementTool()
    
    # 测试创建支出记录
    create_result = await tool.execute(
        action="create",
        invoice_ids=["INV-12345", "INV-67890"],
        supplement_data={
            "trip_purpose": "客户拜访",
            "destination": "上海"
        }
    )
    print("创建支出记录:")
    print(json.dumps(create_result, ensure_ascii=False, indent=2))
    
    # 保存第一个记录ID用于后续测试
    if create_result.get("expense_records"):
        record_id = create_result["expense_records"][0]["record_id"]
        
        # 测试更新支出记录
        update_result = await tool.execute(
            action="update",
            invoice_ids=[record_id],
            supplement_data={
                "start_date": "2023-05-01",
                "end_date": "2023-05-03"
            }
        )
        print("\n更新支出记录:")
        print(json.dumps(update_result, ensure_ascii=False, indent=2))
        
        # 测试验证支出记录
        validate_result = await tool.execute(
            action="validate",
            invoice_ids=[record_id]
        )
        print("\n验证支出记录:")
        print(json.dumps(validate_result, ensure_ascii=False, indent=2))

async def test_reimbursement_management_tool():
    """测试报销单管理工具"""
    print("\n=== 测试报销单管理工具 ===")
    tool = ReimbursementManagementTool()
    
    # 测试创建报销单
    create_result = await tool.execute(
        action="create",
        expense_record_ids=["ER-12345", "ER-67890"]
    )
    print("创建报销单:")
    print(json.dumps(create_result, ensure_ascii=False, indent=2))
    
    # 保存报销单ID用于后续测试
    bill_id = create_result.get("bill_id")
    
    if bill_id:
        # 测试关联出差申请
        link_travel_result = await tool.execute(
            action="link_travel",
            bill_id=bill_id,
            link_data={
                "trip_ids": ["TA-12345", "TA-67890"]
            }
        )
        print("\n关联出差申请:")
        print(json.dumps(link_travel_result, ensure_ascii=False, indent=2))
        
        # 测试关联借款
        link_loan_result = await tool.execute(
            action="link_loan",
            bill_id=bill_id,
            link_data={
                "loan_ids": ["LN-12345"]
            }
        )
        print("\n关联借款:")
        print(json.dumps(link_loan_result, ensure_ascii=False, indent=2))
        
        # 测试补充数据
        supplement_result = await tool.execute(
            action="supplement",
            bill_id=bill_id,
            supplement_data={
                "reimbursement_type": "差旅报销",
                "department": "技术部",
                "applicant": "张三",
                "payment_method": "银行转账",
                "bank_account": "6222021234567890123"
            }
        )
        print("\n补充数据:")
        print(json.dumps(supplement_result, ensure_ascii=False, indent=2))
        
        # 测试保存报销单
        save_result = await tool.execute(
            action="save",
            bill_id=bill_id
        )
        print("\n保存报销单:")
        print(json.dumps(save_result, ensure_ascii=False, indent=2))

async def test_reimbursement_submission_tool():
    """测试报销提交工具"""
    print("\n=== 测试报销提交工具 ===")
    tool = ReimbursementSubmissionTool()
    
    # 测试只验证不提交
    validate_result = await tool.execute(
        bill_id="REIM-12345",
        validate_only=True
    )
    print("只验证不提交:")
    print(json.dumps(validate_result, ensure_ascii=False, indent=2))
    
    # 测试验证并提交
    submit_result = await tool.execute(
        bill_id="REIM-67890",
        validate_only=False
    )
    print("\n验证并提交:")
    print(json.dumps(submit_result, ensure_ascii=False, indent=2))

async def test_status_query_tool():
    """测试状态查询工具"""
    print("\n=== 测试状态查询工具 ===")
    tool = StatusQueryTool()
    
    # 测试查询权限
    permission_result = await tool.execute(
        query_type="permission",
        user_id="user-001"
    )
    print("查询权限:")
    print(json.dumps(permission_result, ensure_ascii=False, indent=2))
    
    # 测试查询报销单列表
    bill_list_result = await tool.execute(
        query_type="bill_list",
        user_id="user-001",
        filters={
            "status": "all",
            "date_range": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        }
    )
    print("\n查询报销单列表:")
    print(json.dumps(bill_list_result, ensure_ascii=False, indent=2))
    
    # 测试查询审批进度
    approval_result = await tool.execute(
        query_type="approval",
        user_id="user-001",
        bill_id="REIM-12345"
    )
    print("\n查询审批进度:")
    print(json.dumps(approval_result, ensure_ascii=False, indent=2))
    
    # 测试查询支付状态
    payment_result = await tool.execute(
        query_type="payment",
        user_id="user-001",
        bill_id="REIM-67890"
    )
    print("\n查询支付状态:")
    print(json.dumps(payment_result, ensure_ascii=False, indent=2))

async def test_travel_application_query_tool():
    """测试差旅申请查询工具"""
    print("\n=== 测试差旅申请查询工具 ===")
    tool = TravelApplicationQueryTool()
    
    # 测试查询差旅申请
    result = await tool.execute(
        user_id="user-001",
        date_range={
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        },
        status_filter="reimbursable"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

async def test_allowance_processing_tool():
    """测试补助处理工具"""
    print("\n=== 测试补助处理工具 ===")
    tool = AllowanceProcessingTool()
    
    # 测试检查补助资格
    eligibility_result = await tool.execute(
        action="check_eligibility",
        user_id="user-001",
        trip_order_id="TA-12345"
    )
    print("检查补助资格:")
    print(json.dumps(eligibility_result, ensure_ascii=False, indent=2))
    
    # 测试申请补助
    apply_result = await tool.execute(
        action="apply_manual",
        user_id="user-001",
        trip_order_id="TA-67890"
    )
    print("\n申请补助:")
    print(json.dumps(apply_result, ensure_ascii=False, indent=2))

async def main():
    """运行所有测试"""
    await test_invoice_processing_tool()
    await test_expense_record_management_tool()
    await test_reimbursement_management_tool()
    await test_reimbursement_submission_tool()
    await test_status_query_tool()
    await test_travel_application_query_tool()
    await test_allowance_processing_tool()

if __name__ == "__main__":
    asyncio.run(main()) 