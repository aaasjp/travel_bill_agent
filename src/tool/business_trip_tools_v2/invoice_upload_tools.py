"""
发票上传相关API工具
"""
import json
import time
import asyncio
import random
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
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 模拟异常情况（5%的概率）
        if random.random() < 0.05:
            raise Exception("发票上传失败：文件格式不支持或文件损坏")
        
        # 模拟参数验证失败
        file_data = kwargs.get("file_data", "")
        file_name = kwargs.get("file_name", "")
        file_type = kwargs.get("file_type", "")
        
        if not file_data:
            raise ValueError("发票文件数据不能为空")
        
        if not file_name:
            raise ValueError("发票文件名不能为空")
        
        if file_type not in ["jpg", "png", "pdf"]:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        # 模拟文件大小限制
        if len(file_data) > 10 * 1024 * 1024:  # 10MB
            raise Exception("文件大小超过限制（最大10MB）")
        
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
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（3%的概率）
        if random.random() < 0.03:
            raise Exception("获取维度数据失败：网络连接超时")
        
        # 模拟参数验证
        if not dimension_code:
            raise ValueError("维度代码不能为空")
        
        # 模拟不支持的维度代码
        if dimension_code not in ["CURRENCY", "EXPENSE_TYPE", "DEPARTMENT", "PROJECT"]:
            raise ValueError(f"不支持的维度代码: {dimension_code}")
        
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
            ],
            "DEPARTMENT": [
                {"code": "IT", "name": "信息技术部"},
                {"code": "HR", "name": "人力资源部"},
                {"code": "FINANCE", "name": "财务部"}
            ],
            "PROJECT": [
                {"code": "PROJ001", "name": "项目A"},
                {"code": "PROJ002", "name": "项目B"},
                {"code": "PROJ003", "name": "项目C"}
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
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（2%的概率）
        if random.random() < 0.02:
            raise Exception("获取业务对象模板失败：模板不存在或已过期")
        
        # 模拟参数验证
        if not object_type:
            raise ValueError("业务对象类型不能为空")
        
        # 模拟不支持的模板类型
        if object_type not in ["INVOICE", "EXPENSE_RECORD", "REIMBURSEMENT_BILL"]:
            raise ValueError(f"不支持的业务对象类型: {object_type}")
        
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
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（4%的概率）
        if random.random() < 0.04:
            raise Exception("获取历史版本格式失败：单据不存在或无历史版本")
        
        # 模拟参数验证
        if not bill_id:
            raise ValueError("单据ID不能为空")
        
        # 模拟无效的单据ID
        if not bill_id.startswith("BILL_"):
            raise ValueError("无效的单据ID格式")
        
        return {
            "success": True,
            "data": {
                "bill_id": bill_id,
                "version": version,
                "format_data": {
                    "template_version": "1.2",
                    "fields": [
                        {"name": "field1", "type": "string", "required": True},
                        {"name": "field2", "type": "number", "required": False}
                    ],
                    "layout": "standard",
                    "created_time": "2024-01-01 10:00:00"
                }
            },
            "message": "历史版本格式获取成功"
        }


class GetUserCurrencyTool(BaseTool):
    """获取用户货币工具"""
    
    @property
    def name(self) -> str:
        return "get_user_currency"
    
    @property
    def description(self) -> str:
        return "获取用户默认货币"
    
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
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（1%的概率）
        if random.random() < 0.01:
            raise Exception("获取用户货币失败：用户不存在")
        
        # 模拟参数验证
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "default_currency": "CNY",
                "available_currencies": ["CNY", "USD", "EUR"],
                "exchange_rate": {
                    "USD": 0.14,
                    "EUR": 0.13
                }
            },
            "message": "用户货币信息获取成功"
        }


class GetInvoiceBusinessObjectTool(BaseTool):
    """获取发票业务对象工具"""
    
    @property
    def name(self) -> str:
        return "get_invoice_business_object"
    
    @property
    def description(self) -> str:
        return "获取发票业务对象信息"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "发票ID"
                }
            },
            "required": ["invoice_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        invoice_id = kwargs.get("invoice_id")
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（6%的概率）
        if random.random() < 0.06:
            raise Exception("获取发票业务对象失败：发票不存在或已被删除")
        
        # 模拟参数验证
        if not invoice_id:
            raise ValueError("发票ID不能为空")
        
        # 模拟无效的发票ID
        if not invoice_id.startswith("INV_"):
            raise ValueError("无效的发票ID格式")
        
        return {
            "success": True,
            "data": {
                "invoice_id": invoice_id,
                "business_object": {
                    "object_type": "INVOICE",
                    "object_id": f"OBJ_{invoice_id}",
                    "status": "ACTIVE",
                    "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "metadata": {
                    "company": "海尔集团",
                    "department": "财务部",
                    "user": "张三"
                }
            },
            "message": "发票业务对象获取成功"
        }


class InvoiceVerificationTool(BaseTool):
    """发票验证工具"""
    
    @property
    def name(self) -> str:
        return "invoice_verification"
    
    @property
    def description(self) -> str:
        return "验证发票真伪和有效性"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "invoice_code": {
                    "type": "string",
                    "description": "发票代码"
                },
                "invoice_number": {
                    "type": "string",
                    "description": "发票号码"
                }
            },
            "required": ["invoice_code", "invoice_number"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        invoice_code = kwargs.get("invoice_code")
        invoice_number = kwargs.get("invoice_number")
        
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 模拟异常情况（8%的概率）
        if random.random() < 0.08:
            raise Exception("发票验证失败：税务系统连接超时")
        
        # 模拟参数验证
        if not invoice_code:
            raise ValueError("发票代码不能为空")
        
        if not invoice_number:
            raise ValueError("发票号码不能为空")
        
        # 模拟无效的发票代码格式
        if len(invoice_code) != 20:
            raise ValueError("发票代码格式不正确（应为20位）")
        
        # 模拟重复发票
        if invoice_code == "12345678901234567890" and invoice_number == "12345678":
            raise Exception("发票已存在，不能重复上传")
        
        return {
            "success": True,
            "data": {
                "invoice_code": invoice_code,
                "invoice_number": invoice_number,
                "verification_result": "VALID",
                "verification_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "details": {
                    "is_valid": True,
                    "is_duplicate": False,
                    "tax_authority": "国家税务总局",
                    "verification_source": "税务系统"
                }
            },
            "message": "发票验证成功"
        }


class GetPendingInvoiceTool(BaseTool):
    """获取待处理发票工具"""
    
    @property
    def name(self) -> str:
        return "get_pending_invoice"
    
    @property
    def description(self) -> str:
        return "获取待处理的发票列表"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "status": {
                    "type": "string",
                    "description": "发票状态"
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
        status = kwargs.get("status", "PENDING")
        page = kwargs.get("page", 1)
        size = kwargs.get("size", 10)
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（3%的概率）
        if random.random() < 0.03:
            raise Exception("获取待处理发票失败：用户权限不足")
        
        # 模拟参数验证
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if page < 1:
            raise ValueError("页码必须大于0")
        
        if size < 1 or size > 100:
            raise ValueError("每页大小必须在1-100之间")
        
        # 模拟数据
        mock_invoices = []
        for i in range(min(size, 5)):
            mock_invoices.append({
                "invoice_id": f"INV_{int(time.time())}_{i}",
                "invoice_code": f"1234567890123456789{i}",
                "invoice_number": f"1234567{i}",
                "amount": 1000.00 * (i + 1),
                "status": status,
                "upload_time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "success": True,
            "data": {
                "invoices": mock_invoices,
                "total": len(mock_invoices),
                "page": page,
                "size": size,
                "has_more": len(mock_invoices) == size
            },
            "message": "待处理发票列表获取成功"
        }


class GetExpenseTypeMappingTool(BaseTool):
    """获取费用类型映射工具"""
    
    @property
    def name(self) -> str:
        return "get_expense_type_mapping"
    
    @property
    def description(self) -> str:
        return "获取费用类型映射关系"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "properties": {
                "source_type": {
                    "type": "string",
                    "description": "源费用类型"
                }
            },
            "required": ["source_type"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        source_type = kwargs.get("source_type")
        
        # 模拟网络延迟
        await asyncio.sleep(0.05)
        
        # 模拟异常情况（2%的概率）
        if random.random() < 0.02:
            raise Exception("获取费用类型映射失败：映射规则不存在")
        
        # 模拟参数验证
        if not source_type:
            raise ValueError("源费用类型不能为空")
        
        # 模拟映射数据
        mapping_data = {
            "TRAVEL": {
                "target_type": "差旅费",
                "category": "TRAVEL_EXPENSE",
                "rules": ["需要出差申请", "需要住宿发票"]
            },
            "MEAL": {
                "target_type": "餐饮费",
                "category": "MEAL_EXPENSE",
                "rules": ["需要用餐发票", "单次限额200元"]
            },
            "TRANSPORT": {
                "target_type": "交通费",
                "category": "TRANSPORT_EXPENSE",
                "rules": ["需要交通发票", "需要行程记录"]
            }
        }
        
        if source_type not in mapping_data:
            raise ValueError(f"不支持的源费用类型: {source_type}")
        
        return {
            "success": True,
            "data": mapping_data[source_type],
            "message": "费用类型映射获取成功"
        } 