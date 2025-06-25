"""
支出记录相关API工具
"""
import json
import time
import random
from typing import Dict, Any, List, Optional
from ..base import BaseTool
import asyncio


class GetExpenseRecordTypeTool(BaseTool):
    """获取支出记录类型工具"""
    
    @property
    def name(self) -> str:
        return "get_expense_record_type"
    
    @property
    def description(self) -> str:
        return "获取支出记录类型"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {}
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（2%的概率）
        if random.random() < 0.02:
            raise Exception("获取支出记录类型失败：系统维护中")
        
        return {
            "success": True,
            "data": {
                "expense_types": [
                    {
                        "type_code": "TRAVEL",
                        "type_name": "差旅费",
                        "description": "出差期间的交通、住宿、餐饮等费用",
                        "is_active": True
                    },
                    {
                        "type_code": "MEAL",
                        "type_name": "餐饮费",
                        "description": "工作餐、商务宴请等餐饮费用",
                        "is_active": True
                    },
                    {
                        "type_code": "TRANSPORT",
                        "type_name": "交通费",
                        "description": "市内交通、出租车等费用",
                        "is_active": True
                    },
                    {
                        "type_code": "ACCOMMODATION",
                        "type_name": "住宿费",
                        "description": "出差住宿费用",
                        "is_active": True
                    }
                ]
            },
            "message": "支出记录类型获取成功"
        }


class GetExpenseTypeFieldRuleTool(BaseTool):
    """获取费用类型字段列表和规则工具"""
    
    @property
    def name(self) -> str:
        return "get_expense_type_field_rule"
    
    @property
    def description(self) -> str:
        return "获取费用类型字段列表和规则"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "expense_type": {
                    "type": "string",
                    "description": "费用类型代码"
                }
            },
            "required": ["expense_type"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        expense_type = kwargs.get("expense_type", "TRAVEL")
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（3%的概率）
        if random.random() < 0.03:
            raise Exception("获取费用类型字段规则失败：配置数据不存在")
        
        # 模拟参数验证
        if not expense_type:
            raise ValueError("费用类型代码不能为空")
        
        # 模拟不支持的费用类型
        if expense_type not in ["TRAVEL", "MEAL", "TRANSPORT", "ACCOMMODATION"]:
            raise ValueError(f"不支持的费用类型: {expense_type}")
        
        field_rules = {
            "TRAVEL": {
                "fields": [
                    {"name": "travel_date", "type": "date", "required": True, "description": "出差日期"},
                    {"name": "destination", "type": "string", "required": True, "description": "目的地"},
                    {"name": "purpose", "type": "string", "required": True, "description": "出差目的"},
                    {"name": "amount", "type": "decimal", "required": True, "description": "费用金额"}
                ],
                "rules": [
                    {"rule_id": "R001", "rule_name": "金额限制", "rule_type": "AMOUNT_LIMIT", "value": 5000},
                    {"rule_id": "R002", "rule_name": "需要审批", "rule_type": "APPROVAL_REQUIRED", "value": True}
                ]
            },
            "MEAL": {
                "fields": [
                    {"name": "meal_date", "type": "date", "required": True, "description": "用餐日期"},
                    {"name": "meal_type", "type": "string", "required": True, "description": "用餐类型"},
                    {"name": "amount", "type": "decimal", "required": True, "description": "费用金额"}
                ],
                "rules": [
                    {"rule_id": "R003", "rule_name": "单次限额", "rule_type": "SINGLE_LIMIT", "value": 200}
                ]
            },
            "TRANSPORT": {
                "fields": [
                    {"name": "transport_date", "type": "date", "required": True, "description": "交通日期"},
                    {"name": "transport_type", "type": "string", "required": True, "description": "交通方式"},
                    {"name": "amount", "type": "decimal", "required": True, "description": "费用金额"}
                ],
                "rules": [
                    {"rule_id": "R004", "rule_name": "交通费限额", "rule_type": "TRANSPORT_LIMIT", "value": 100}
                ]
            },
            "ACCOMMODATION": {
                "fields": [
                    {"name": "check_in_date", "type": "date", "required": True, "description": "入住日期"},
                    {"name": "check_out_date", "type": "date", "required": True, "description": "退房日期"},
                    {"name": "hotel_name", "type": "string", "required": True, "description": "酒店名称"},
                    {"name": "amount", "type": "decimal", "required": True, "description": "费用金额"}
                ],
                "rules": [
                    {"rule_id": "R005", "rule_name": "住宿费限额", "rule_type": "ACCOMMODATION_LIMIT", "value": 500}
                ]
            }
        }
        
        return {
            "success": True,
            "data": field_rules.get(expense_type, {}),
            "message": "费用类型字段和规则获取成功"
        }


class GetControlStandardTool(BaseTool):
    """通过ID获取支出记录控制标准工具"""
    
    @property
    def name(self) -> str:
        return "get_control_standard"
    
    @property
    def description(self) -> str:
        return "通过ID获取支出记录控制标准"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "standard_id": {
                    "type": "string",
                    "description": "控制标准ID"
                }
            },
            "required": ["standard_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        standard_id = kwargs.get("standard_id")
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（4%的概率）
        if random.random() < 0.04:
            raise Exception("获取控制标准失败：标准不存在或已过期")
        
        # 模拟参数验证
        if not standard_id:
            raise ValueError("控制标准ID不能为空")
        
        # 模拟无效的标准ID
        if not standard_id.startswith("STD_"):
            raise ValueError("无效的控制标准ID格式")
        
        return {
            "success": True,
            "data": {
                "standard_id": standard_id,
                "standard_name": "差旅费控制标准",
                "standard_type": "TRAVEL_EXPENSE",
                "model": {
                    "daily_limit": 500,
                    "total_limit": 5000,
                    "approval_threshold": 1000
                },
                "values": {
                    "currency": "CNY",
                    "effective_date": "2024-01-01",
                    "expiry_date": "2024-12-31"
                }
            },
            "message": "控制标准获取成功"
        }


class AddInvoiceToExpenseRecordTool(BaseTool):
    """支出记录添加发票工具"""
    
    @property
    def name(self) -> str:
        return "add_invoice_to_expense_record"
    
    @property
    def description(self) -> str:
        return "支出记录添加发票"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "expense_record_id": {
                    "type": "string",
                    "description": "支出记录ID"
                },
                "invoice_id": {
                    "type": "string",
                    "description": "发票ID"
                }
            },
            "required": ["expense_record_id", "invoice_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        expense_record_id = kwargs.get("expense_record_id")
        invoice_id = kwargs.get("invoice_id")
        
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 模拟异常情况（6%的概率）
        if random.random() < 0.06:
            raise Exception("添加发票到支出记录失败：发票已被其他记录使用")
        
        # 模拟参数验证
        if not expense_record_id:
            raise ValueError("支出记录ID不能为空")
        
        if not invoice_id:
            raise ValueError("发票ID不能为空")
        
        # 模拟无效的ID格式
        if not expense_record_id.startswith("EXP_"):
            raise ValueError("无效的支出记录ID格式")
        
        if not invoice_id.startswith("INV_"):
            raise ValueError("无效的发票ID格式")
        
        # 模拟重复添加
        if expense_record_id == "EXP_001" and invoice_id == "INV_001":
            raise Exception("发票已添加到该支出记录中")
        
        return {
            "success": True,
            "data": {
                "expense_record_id": expense_record_id,
                "invoice_id": invoice_id,
                "add_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "ADDED"
            },
            "message": "发票添加成功"
        }


class ExpenseRecordRuleExecuteTool(BaseTool):
    """支出记录规则执行工具"""
    
    @property
    def name(self) -> str:
        return "expense_record_rule_execute"
    
    @property
    def description(self) -> str:
        return "执行支出记录规则检查"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "expense_record_id": {
                    "type": "string",
                    "description": "支出记录ID"
                },
                "rule_ids": {
                    "type": "array",
                    "description": "规则ID列表"
                }
            },
            "required": ["expense_record_id", "rule_ids"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        expense_record_id = kwargs.get("expense_record_id")
        rule_ids = kwargs.get("rule_ids", [])
        
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 模拟异常情况（5%的概率）
        if random.random() < 0.05:
            raise Exception("规则执行失败：规则引擎异常")
        
        # 模拟参数验证
        if not expense_record_id:
            raise ValueError("支出记录ID不能为空")
        
        if not rule_ids:
            raise ValueError("规则ID列表不能为空")
        
        # 模拟规则执行结果
        execution_results = []
        for rule_id in rule_ids:
            # 模拟某些规则失败
            if rule_id == "R_FAIL":
                execution_results.append({
                    "rule_id": rule_id,
                    "status": "FAILED",
                    "message": "规则执行失败：金额超限",
                    "details": {"limit": 1000, "actual": 1500}
                })
            else:
                execution_results.append({
                    "rule_id": rule_id,
                    "status": "PASSED",
                    "message": "规则执行通过",
                    "details": {}
                })
        
        return {
            "success": True,
            "data": {
                "expense_record_id": expense_record_id,
                "execution_results": execution_results,
                "overall_status": "PASSED" if all(r["status"] == "PASSED" for r in execution_results) else "FAILED",
                "execution_time": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "message": "规则执行完成"
        }


class ExpenseRecordStandardCheckTool(BaseTool):
    """支出记录标准检查工具"""
    
    @property
    def name(self) -> str:
        return "expense_record_standard_check"
    
    @property
    def description(self) -> str:
        return "检查支出记录是否符合标准"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "expense_record_id": {
                    "type": "string",
                    "description": "支出记录ID"
                },
                "standard_id": {
                    "type": "string",
                    "description": "标准ID"
                }
            },
            "required": ["expense_record_id", "standard_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        expense_record_id = kwargs.get("expense_record_id")
        standard_id = kwargs.get("standard_id")
        
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 模拟异常情况（3%的概率）
        if random.random() < 0.03:
            raise Exception("标准检查失败：标准配置错误")
        
        # 模拟参数验证
        if not expense_record_id:
            raise ValueError("支出记录ID不能为空")
        
        if not standard_id:
            raise ValueError("标准ID不能为空")
        
        # 模拟检查结果
        check_results = {
            "amount_check": {
                "status": "PASSED",
                "message": "金额符合标准",
                "details": {"limit": 5000, "actual": 3000}
            },
            "date_check": {
                "status": "PASSED",
                "message": "日期符合标准",
                "details": {"within_period": True}
            },
            "document_check": {
                "status": "PASSED",
                "message": "单据完整",
                "details": {"required_docs": 3, "provided_docs": 3}
            }
        }
        
        # 模拟某些检查失败
        if expense_record_id == "EXP_FAIL":
            check_results["amount_check"]["status"] = "FAILED"
            check_results["amount_check"]["message"] = "金额超过标准限制"
        
        overall_status = "PASSED" if all(r["status"] == "PASSED" for r in check_results.values()) else "FAILED"
        
        return {
            "success": True,
            "data": {
                "expense_record_id": expense_record_id,
                "standard_id": standard_id,
                "check_results": check_results,
                "overall_status": overall_status,
                "check_time": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "message": "标准检查完成"
        }


class GetBillDefineListTool(BaseTool):
    """获取单据定义列表工具"""
    
    @property
    def name(self) -> str:
        return "get_bill_define_list"
    
    @property
    def description(self) -> str:
        return "获取单据定义列表"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "bill_type": {
                    "type": "string",
                    "description": "单据类型"
                },
                "status": {
                    "type": "string",
                    "description": "状态"
                }
            },
            "required": []
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        bill_type = kwargs.get("bill_type", "TRAVEL_REIMBURSEMENT")
        status = kwargs.get("status", "ACTIVE")
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（2%的概率）
        if random.random() < 0.02:
            raise Exception("获取单据定义列表失败：权限不足")
        
        # 模拟参数验证
        if bill_type and bill_type not in ["TRAVEL_REIMBURSEMENT", "EXPENSE_REPORT", "ADVANCE_APPLICATION"]:
            raise ValueError(f"不支持的单据类型: {bill_type}")
        
        if status and status not in ["ACTIVE", "INACTIVE", "DRAFT"]:
            raise ValueError(f"不支持的状态: {status}")
        
        # 模拟数据
        bill_defines = [
            {
                "define_id": "DEF_001",
                "define_name": "差旅费报销单",
                "bill_type": "TRAVEL_REIMBURSEMENT",
                "status": "ACTIVE",
                "version": "1.0",
                "create_time": "2024-01-01 10:00:00"
            },
            {
                "define_id": "DEF_002",
                "define_name": "费用报销单",
                "bill_type": "EXPENSE_REPORT",
                "status": "ACTIVE",
                "version": "1.0",
                "create_time": "2024-01-01 10:00:00"
            },
            {
                "define_id": "DEF_003",
                "define_name": "借款申请单",
                "bill_type": "ADVANCE_APPLICATION",
                "status": "ACTIVE",
                "version": "1.0",
                "create_time": "2024-01-01 10:00:00"
            }
        ]
        
        # 根据参数过滤
        if bill_type:
            bill_defines = [b for b in bill_defines if b["bill_type"] == bill_type]
        
        if status:
            bill_defines = [b for b in bill_defines if b["status"] == status]
        
        return {
            "success": True,
            "data": {
                "bill_defines": bill_defines,
                "total": len(bill_defines)
            },
            "message": "单据定义列表获取成功"
        }


class CheckExpensePermissionTool(BaseTool):
    """检查费用权限工具"""
    
    @property
    def name(self) -> str:
        return "check_expense_permission"
    
    @property
    def description(self) -> str:
        return "检查用户是否有费用相关权限"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "permission_type": {
                    "type": "string",
                    "description": "权限类型"
                },
                "amount": {
                    "type": "number",
                    "description": "金额"
                }
            },
            "required": ["user_id", "permission_type"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        user_id = kwargs.get("user_id")
        permission_type = kwargs.get("permission_type")
        amount = kwargs.get("amount", 0)
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（4%的概率）
        if random.random() < 0.04:
            raise Exception("权限检查失败：用户信息不存在")
        
        # 模拟参数验证
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if not permission_type:
            raise ValueError("权限类型不能为空")
        
        if permission_type not in ["EXPENSE_SUBMIT", "EXPENSE_APPROVE", "EXPENSE_VIEW"]:
            raise ValueError(f"不支持的权限类型: {permission_type}")
        
        # 模拟权限检查结果
        permission_result = {
            "user_id": user_id,
            "permission_type": permission_type,
            "has_permission": True,
            "permission_level": "FULL",
            "amount_limit": 10000,
            "details": {
                "role": "员工",
                "department": "信息技术部",
                "approval_level": 1
            }
        }
        
        # 模拟某些权限不足的情况
        if user_id == "USER_NO_PERMISSION":
            permission_result["has_permission"] = False
            permission_result["permission_level"] = "NONE"
            permission_result["details"]["reason"] = "用户权限不足"
        
        # 模拟金额超限
        if amount > permission_result["amount_limit"]:
            permission_result["has_permission"] = False
            permission_result["details"]["reason"] = "金额超过权限限制"
        
        return {
            "success": True,
            "data": permission_result,
            "message": "权限检查完成"
        }


class GenerateBillByExpenseIdTool(BaseTool):
    """根据支出记录ID生成单据工具"""
    
    @property
    def name(self) -> str:
        return "generate_bill_by_expense_id"
    
    @property
    def description(self) -> str:
        return "根据支出记录ID生成报销单据"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "expense_record_id": {
                    "type": "string",
                    "description": "支出记录ID"
                },
                "bill_type": {
                    "type": "string",
                    "description": "单据类型"
                }
            },
            "required": ["expense_record_id", "bill_type"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        expense_record_id = kwargs.get("expense_record_id")
        bill_type = kwargs.get("bill_type")
        
        # 模拟网络延迟
        await asyncio.sleep(0.2)
        
        # 模拟异常情况（7%的概率）
        if random.random() < 0.07:
            raise Exception("生成单据失败：支出记录状态异常")
        
        # 模拟参数验证
        if not expense_record_id:
            raise ValueError("支出记录ID不能为空")
        
        if not bill_type:
            raise ValueError("单据类型不能为空")
        
        if bill_type not in ["TRAVEL_REIMBURSEMENT", "EXPENSE_REPORT"]:
            raise ValueError(f"不支持的单据类型: {bill_type}")
        
        # 模拟无效的支出记录ID
        if not expense_record_id.startswith("EXP_"):
            raise ValueError("无效的支出记录ID格式")
        
        # 模拟支出记录不存在
        if expense_record_id == "EXP_NOT_EXIST":
            raise Exception("支出记录不存在")
        
        # 模拟支出记录状态不正确
        if expense_record_id == "EXP_INVALID_STATUS":
            raise Exception("支出记录状态不正确，无法生成单据")
        
        return {
            "success": True,
            "data": {
                "expense_record_id": expense_record_id,
                "bill_id": f"BILL_{int(time.time())}",
                "bill_type": bill_type,
                "bill_name": f"{bill_type}单据",
                "status": "DRAFT",
                "total_amount": 3000.00,
                "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "details": {
                    "expense_count": 3,
                    "invoice_count": 5,
                    "approval_required": True
                }
            },
            "message": "单据生成成功"
        } 