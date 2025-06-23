"""
发票上传相关API工具
"""
import json
import time
from typing import Dict, Any, List, Optional
from ..base import BaseTool


class InvoiceUploadTool(BaseTool):
    """上传发票工具"""
    
    @property
    def name(self) -> str:
        return "invoice_upload"
    
    @property
    def description(self) -> str:
        return "上传发票并进行OCR识别"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "file_data": {
                    "type": "string",
                    "description": "发票文件数据（base64编码）"
                },
                "file_name": {
                    "type": "string", 
                    "description": "发票文件名"
                },
                "file_type": {
                    "type": "string",
                    "description": "文件类型（jpg/png/pdf等）"
                }
            },
            "required": ["file_data", "file_name", "file_type"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        # Mock实现
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        return {
            "success": True,
            "data": {
                "invoice_id": f"INV_{int(time.time())}",
                "ocr_result": {
                    "invoice_code": "12345678901234567890",
                    "invoice_number": "12345678",
                    "invoice_date": "2024-01-15",
                    "amount": 1000.00,
                    "tax_amount": 130.00,
                    "total_amount": 1130.00,
                    "seller_name": "测试公司",
                    "buyer_name": "海尔集团"
                },
                "upload_time": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "message": "发票上传成功"
        }


class GetDimensionDataTool(BaseTool):
    """获取维度数据工具"""
    
    @property
    def name(self) -> str:
        return "get_dimension_data"
    
    @property
    def description(self) -> str:
        return "获取货币维度等维度数据"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "dimension_code": {
                    "type": "string",
                    "description": "维度代码"
                }
            },
            "required": ["dimension_code"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        dimension_code = kwargs.get("dimension_code", "CURRENCY")
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        mock_data = {
            "CURRENCY": [
                {"code": "CNY", "name": "人民币", "symbol": "¥"},
                {"code": "USD", "name": "美元", "symbol": "$"},
                {"code": "EUR", "name": "欧元", "symbol": "€"}
            ],
            "EXPENSE_TYPE": [
                {"code": "TRAVEL", "name": "差旅费"},
                {"code": "MEAL", "name": "餐饮费"},
                {"code": "TRANSPORT", "name": "交通费"}
            ]
        }
        
        return {
            "success": True,
            "data": mock_data.get(dimension_code, []),
            "message": "维度数据获取成功"
        }


class GetBusinessObjectTemplateTool(BaseTool):
    """获取业务对象模板的上下文数据工具"""
    
    @property
    def name(self) -> str:
        return "get_business_object_template"
    
    @property
    def description(self) -> str:
        return "获取发票对象模板上下文数据"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "object_type": {
                    "type": "string",
                    "description": "业务对象类型"
                }
            },
            "required": ["object_type"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        object_type = kwargs.get("object_type", "INVOICE")
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        return {
            "success": True,
            "data": {
                "template_id": f"TPL_{object_type}_{int(time.time())}",
                "fields": [
                    {"name": "invoice_code", "type": "string", "required": True},
                    {"name": "invoice_number", "type": "string", "required": True},
                    {"name": "amount", "type": "decimal", "required": True},
                    {"name": "tax_amount", "type": "decimal", "required": False}
                ],
                "context": {
                    "company_code": "HAIER",
                    "system_version": "V12.0"
                }
            },
            "message": "业务对象模板获取成功"
        }


class GetHistoryVersionFormatTool(BaseTool):
    """审批时查询历史版本格式设计工具"""
    
    @property
    def name(self) -> str:
        return "get_history_version_format"
    
    @property
    def description(self) -> str:
        return "审批时查询历史版本格式设计"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "bill_id": {
                    "type": "string",
                    "description": "单据ID"
                },
                "version": {
                    "type": "string",
                    "description": "版本号"
                }
            },
            "required": ["bill_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        bill_id = kwargs.get("bill_id")
        version = kwargs.get("version", "1.0")
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        return {
            "success": True,
            "data": {
                "bill_id": bill_id,
                "version": version,
                "format_design": {
                    "layout": "standard",
                    "sections": ["header", "body", "footer"],
                    "fields": ["title", "amount", "date", "approver"]
                },
                "history_changes": [
                    {"version": "1.0", "change_date": "2024-01-01", "description": "初始版本"},
                    {"version": "1.1", "change_date": "2024-01-15", "description": "增加字段"}
                ]
            },
            "message": "历史版本格式设计获取成功"
        }


class GetUserCurrencyTool(BaseTool):
    """获取用户所属维度账户架构货币工具"""
    
    @property
    def name(self) -> str:
        return "get_user_currency"
    
    @property
    def description(self) -> str:
        return "获取用户所属维度账户架构货币"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                }
            },
            "required": ["user_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        user_id = kwargs.get("user_id")
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "currency": {
                    "code": "CNY",
                    "name": "人民币",
                    "symbol": "¥",
                    "exchange_rate": 1.0
                },
                "account_architecture": {
                    "org_code": "HAIER_CN",
                    "org_name": "海尔集团中国区",
                    "dimension_path": "/HAIER/CN"
                }
            },
            "message": "用户货币信息获取成功"
        }


class GetInvoiceBusinessObjectTool(BaseTool):
    """获取发票业务对象数据工具"""
    
    @property
    def name(self) -> str:
        return "get_invoice_business_object"
    
    @property
    def description(self) -> str:
        return "获取发票业务对象数据"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "data_id": {
                    "type": "string",
                    "description": "数据ID"
                }
            },
            "required": ["data_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        data_id = kwargs.get("data_id")
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        return {
            "success": True,
            "data": {
                "data_id": data_id,
                "invoice_info": {
                    "invoice_code": "12345678901234567890",
                    "invoice_number": "12345678",
                    "invoice_date": "2024-01-15",
                    "amount": 1000.00,
                    "tax_amount": 130.00,
                    "total_amount": 1130.00
                },
                "business_object": {
                    "object_type": "INVOICE",
                    "object_id": f"BO_{data_id}",
                    "status": "VERIFIED",
                    "create_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            "message": "发票业务对象数据获取成功"
        }


class InvoiceVerificationTool(BaseTool):
    """发票查验并保存业务对象工具"""
    
    @property
    def name(self) -> str:
        return "invoice_verification"
    
    @property
    def description(self) -> str:
        return "发票查验并保存业务对象"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "invoice_data": {
                    "type": "object",
                    "description": "发票数据"
                }
            },
            "required": ["invoice_data"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        invoice_data = kwargs.get("invoice_data", {})
        
        # Mock实现
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "data": {
                "verification_result": {
                    "is_valid": True,
                    "verification_code": "SUCCESS",
                    "verification_message": "发票查验通过"
                },
                "saved_object": {
                    "object_id": f"BO_{int(time.time())}",
                    "object_type": "INVOICE",
                    "save_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "SAVED"
                }
            },
            "message": "发票查验并保存成功"
        }


class GetPendingInvoiceTool(BaseTool):
    """获取待处理的支出记录发票工具"""
    
    @property
    def name(self) -> str:
        return "get_pending_invoice"
    
    @property
    def description(self) -> str:
        return "获取待处理的支出记录发票"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "page": {
                    "type": "integer",
                    "description": "页码"
                },
                "size": {
                    "type": "integer",
                    "description": "每页大小"
                }
            },
            "required": ["user_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        user_id = kwargs.get("user_id")
        page = kwargs.get("page", 1)
        size = kwargs.get("size", 10)
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        mock_invoices = []
        for i in range(min(size, 5)):  # 最多返回5条记录
            mock_invoices.append({
                "invoice_id": f"INV_{int(time.time())}_{i}",
                "invoice_code": f"1234567890123456789{i}",
                "invoice_number": f"1234567{i}",
                "amount": 100.00 * (i + 1),
                "status": "PENDING",
                "upload_time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "success": True,
            "data": {
                "invoices": mock_invoices,
                "total": len(mock_invoices),
                "page": page,
                "size": size
            },
            "message": "待处理发票获取成功"
        }


class GetExpenseTypeMappingTool(BaseTool):
    """发票事项集合到支出类型维度映射工具"""
    
    @property
    def name(self) -> str:
        return "get_expense_type_mapping"
    
    @property
    def description(self) -> str:
        return "发票事项集合到支出类型维度映射"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "invoice_items": {
                    "type": "array",
                    "description": "发票事项列表"
                }
            },
            "required": ["invoice_items"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        invoice_items = kwargs.get("invoice_items", [])
        
        # Mock实现
        await asyncio.sleep(0.05)
        
        mapping_result = []
        for item in invoice_items:
            mapping_result.append({
                "invoice_item": item,
                "expense_type": "TRAVEL",
                "dimension_code": "EXPENSE_TYPE",
                "dimension_value": "差旅费",
                "mapping_confidence": 0.95
            })
        
        return {
            "success": True,
            "data": {
                "mappings": mapping_result,
                "total_mapped": len(mapping_result)
            },
            "message": "支出类型维度映射获取成功"
        }


# 导入asyncio模块
import asyncio 