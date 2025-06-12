"""
支出记录管理工具
实现从发票生成支出记录，管理支出类型映射和补充信息
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from .base import BaseTool

class ExpenseRecordManagementTool(BaseTool):
    """支出记录管理工具，从发票生成支出记录"""
    
    @property
    def name(self) -> str:
        return "manage_expense_records"
    
    @property
    def description(self) -> str:
        return "根据发票创建支出记录，自动映射费用类型，返回需要补充的字段"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "invoice_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "已验证的发票ID列表"
                },
                "supplement_data": {
                    "type": "object",
                    "description": "补充的支出记录信息（可选）"
                },
                "action": {
                    "type": "string",
                    "enum": ["create", "update", "validate"],
                    "default": "create",
                    "description": "操作类型"
                }
            },
            "required": ["invoice_ids", "action"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行支出记录管理工具
        
        Args:
            invoice_ids: 已验证的发票ID列表
            supplement_data: 补充的支出记录信息（可选）
            action: 操作类型，可选值为 create, update, validate
            
        Returns:
            支出记录处理结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        invoice_ids = kwargs.get("invoice_ids", [])
        supplement_data = kwargs.get("supplement_data", {})
        action = kwargs.get("action", "create")
        
        # 根据操作类型执行相应的函数
        if action == "create":
            return await self._create_expense_records(invoice_ids, supplement_data)
        elif action == "update":
            return await self._update_expense_records(invoice_ids, supplement_data)
        elif action == "validate":
            return await self._validate_expense_records(invoice_ids)
        else:
            raise ValueError(f"不支持的操作类型: {action}")
    
    async def _create_expense_records(self, invoice_ids: List[str], supplement_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建支出记录
        
        Args:
            invoice_ids: 发票ID列表
            supplement_data: 补充数据
            
        Returns:
            创建结果
        """
        # 处理结果
        expense_records = []
        total_amount = 0.0
        needs_supplement_count = 0
        
        # 处理每个发票
        for invoice_id in invoice_ids:
            # 模拟获取发票数据
            invoice_data = self._mock_get_invoice_data(invoice_id)
            
            if not invoice_data:
                continue
            
            # 模拟映射支出类型
            expense_type = self._mock_map_expense_type(invoice_data)
            
            # 创建支出记录
            record_id = f"ER-{random.randint(10000, 99999)}"
            
            # 确定需要补充的字段
            required_fields = self._get_required_fields(expense_type)
            
            # 检查是否已提供这些字段
            for field in list(required_fields):
                if field in supplement_data:
                    required_fields.remove(field)
            
            # 创建记录
            expense_record = {
                "record_id": record_id,
                "invoice_id": invoice_id,
                "expense_type": expense_type,
                "amount": invoice_data.get("amount", 0.0),
                "status": "draft" if required_fields else "complete",
                "required_fields": required_fields,
                "validation_result": "pending"
            }
            
            # 添加补充数据
            for key, value in supplement_data.items():
                expense_record[key] = value
            
            # 添加到结果
            expense_records.append(expense_record)
            
            # 累加金额
            if invoice_data.get("amount"):
                total_amount += float(invoice_data["amount"])
            
            # 计算需要补充信息的记录数
            if required_fields:
                needs_supplement_count += 1
        
        # 生成处理摘要
        summary = {
            "total_created": len(expense_records),
            "total_amount": total_amount,
            "needs_supplement": needs_supplement_count
        }
        
        # 返回处理结果
        return {
            "expense_records": expense_records,
            "summary": summary
        }
    
    async def _update_expense_records(self, record_ids: List[str], supplement_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新支出记录
        
        Args:
            record_ids: 记录ID列表
            supplement_data: 补充数据
            
        Returns:
            更新结果
        """
        # 处理结果
        updated_records = []
        
        # 处理每个记录
        for record_id in record_ids:
            # 模拟获取记录数据
            record_data = self._mock_get_expense_record(record_id)
            
            if not record_data:
                continue
            
            # 更新记录
            for key, value in supplement_data.items():
                record_data[key] = value
            
            # 更新必填字段状态
            required_fields = record_data.get("required_fields", [])
            for field in list(required_fields):
                if field in supplement_data:
                    required_fields.remove(field)
            
            record_data["required_fields"] = required_fields
            record_data["status"] = "complete" if not required_fields else "draft"
            
            # 添加到结果
            updated_records.append(record_data)
        
        # 生成处理摘要
        summary = {
            "total_updated": len(updated_records),
            "still_needs_supplement": sum(1 for r in updated_records if r.get("required_fields"))
        }
        
        # 返回处理结果
        return {
            "expense_records": updated_records,
            "summary": summary
        }
    
    async def _validate_expense_records(self, record_ids: List[str]) -> Dict[str, Any]:
        """验证支出记录
        
        Args:
            record_ids: 记录ID列表
            
        Returns:
            验证结果
        """
        # 处理结果
        validated_records = []
        
        # 处理每个记录
        for record_id in record_ids:
            # 模拟获取记录数据
            record_data = self._mock_get_expense_record(record_id)
            
            if not record_data:
                continue
            
            # 检查是否有必填字段未填写
            required_fields = record_data.get("required_fields", [])
            if required_fields:
                validation_result = "incomplete"
                validation_message = "必填字段未填写完整"
            else:
                # 模拟验证过程，90%概率通过
                is_valid = random.random() < 0.9
                validation_result = "valid" if is_valid else "invalid"
                validation_message = "验证通过" if is_valid else "验证未通过，请检查数据"
            
            # 更新验证结果
            record_data["validation_result"] = validation_result
            record_data["validation_message"] = validation_message
            
            # 添加到结果
            validated_records.append(record_data)
        
        # 生成处理摘要
        valid_count = sum(1 for r in validated_records if r.get("validation_result") == "valid")
        
        summary = {
            "total_validated": len(validated_records),
            "valid_count": valid_count,
            "invalid_count": len(validated_records) - valid_count
        }
        
        # 返回处理结果
        return {
            "expense_records": validated_records,
            "summary": summary
        }
    
    def _mock_get_invoice_data(self, invoice_id: str) -> Dict[str, Any]:
        """模拟获取发票数据
        
        Args:
            invoice_id: 发票ID
            
        Returns:
            发票数据
        """
        # 创建模拟发票数据
        invoice_types = ["增值税专用发票", "增值税普通发票", "电子发票", "火车票", "飞机票", "出租车票"]
        invoice_type = random.choice(invoice_types)
        
        # 生成随机金额（50-5000之间）
        amount = round(random.uniform(50, 5000), 2)
        
        # 随机销售方名称
        vendors = [
            "北京科技有限公司", "上海贸易有限公司", "广州电子科技有限公司",
            "深圳信息技术有限公司", "杭州网络科技有限公司"
        ]
        vendor = random.choice(vendors)
        
        # 创建发票数据
        invoice_data = {
            "invoice_id": invoice_id,
            "invoice_type": invoice_type,
            "amount": amount,
            "vendor": vendor,
            "verify_status": "valid"
        }
        
        return invoice_data
    
    def _mock_get_expense_record(self, record_id: str) -> Dict[str, Any]:
        """模拟获取支出记录数据
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录数据
        """
        # 创建模拟记录数据
        expense_types = ["差旅费", "办公用品", "招待费", "会议费", "交通费"]
        expense_type = random.choice(expense_types)
        
        # 生成随机金额（50-5000之间）
        amount = round(random.uniform(50, 5000), 2)
        
        # 创建记录数据
        record_data = {
            "record_id": record_id,
            "invoice_id": f"INV-{random.randint(10000, 99999)}",
            "expense_type": expense_type,
            "amount": amount,
            "status": "draft",
            "required_fields": self._get_required_fields(expense_type),
            "validation_result": "pending"
        }
        
        return record_data
    
    def _mock_map_expense_type(self, invoice_data: Dict[str, Any]) -> str:
        """模拟映射支出类型
        
        Args:
            invoice_data: 发票数据
            
        Returns:
            支出类型
        """
        # 根据发票类型和供应商名称映射支出类型
        invoice_type = invoice_data.get("invoice_type", "")
        vendor = invoice_data.get("vendor", "").lower()
        
        if "火车票" in invoice_type or "飞机票" in invoice_type or "出租车票" in invoice_type:
            return "交通费"
        elif "酒店" in vendor or "宾馆" in vendor:
            return "住宿费"
        elif "餐厅" in vendor or "食品" in vendor:
            return "餐饮费"
        elif "办公" in vendor:
            return "办公用品"
        else:
            # 随机选择一个类型
            expense_types = ["差旅费", "办公用品", "招待费", "会议费", "交通费"]
            return random.choice(expense_types)
    
    def _get_required_fields(self, expense_type: str) -> List[str]:
        """获取指定支出类型的必填字段
        
        Args:
            expense_type: 支出类型
            
        Returns:
            必填字段列表
        """
        # 根据支出类型返回必填字段
        if expense_type == "差旅费":
            return ["trip_purpose", "destination", "start_date", "end_date"]
        elif expense_type == "交通费":
            return ["trip_purpose", "origin", "destination"]
        elif expense_type == "招待费":
            return ["guest_name", "guest_company", "purpose"]
        elif expense_type == "会议费":
            return ["meeting_name", "meeting_date", "attendees"]
        else:
            return ["usage_purpose"] 