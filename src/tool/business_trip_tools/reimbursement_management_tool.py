"""
报销单管理工具
创建报销单，关联支出记录、出差申请和借款，保存报销单数据
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from ..base import BaseTool

class ReimbursementManagementTool(BaseTool):
    """报销单管理工具，创建和管理报销单"""
    
    @property
    def name(self) -> str:
        return "manage_reimbursement"
    
    @property
    def description(self) -> str:
        return "创建报销单，关联支出记录、出差申请和借款，保存报销单数据"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "link_travel", "link_loan", "supplement", "save"],
                    "description": "操作类型"
                },
                "bill_id": {
                    "type": "string",
                    "description": "报销单ID（create时不需要）"
                },
                "expense_record_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "支出记录ID列表（create时需要）"
                },
                "link_data": {
                    "type": "object",
                    "description": "关联数据（link操作时需要）"
                },
                "supplement_data": {
                    "type": "object",
                    "description": "补充数据（supplement时需要）"
                }
            },
            "required": ["action"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行报销单管理工具
        
        Args:
            action: 操作类型
            bill_id: 报销单ID（create时不需要）
            expense_record_ids: 支出记录ID列表（create时需要）
            link_data: 关联数据（link操作时需要）
            supplement_data: 补充数据（supplement时需要）
            
        Returns:
            操作结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        action = kwargs.get("action")
        
        # 根据操作类型执行相应的函数
        if action == "create":
            expense_record_ids = kwargs.get("expense_record_ids", [])
            return await self._create_reimbursement(expense_record_ids)
        elif action == "link_travel":
            bill_id = kwargs.get("bill_id")
            link_data = kwargs.get("link_data", {})
            return await self._link_travel(bill_id, link_data)
        elif action == "link_loan":
            bill_id = kwargs.get("bill_id")
            link_data = kwargs.get("link_data", {})
            return await self._link_loan(bill_id, link_data)
        elif action == "supplement":
            bill_id = kwargs.get("bill_id")
            supplement_data = kwargs.get("supplement_data", {})
            return await self._supplement_data(bill_id, supplement_data)
        elif action == "save":
            bill_id = kwargs.get("bill_id")
            return await self._save_bill(bill_id)
        else:
            raise ValueError(f"不支持的操作类型: {action}")
    
    async def _create_reimbursement(self, expense_record_ids: List[str]) -> Dict[str, Any]:
        """创建报销单
        
        Args:
            expense_record_ids: 支出记录ID列表
            
        Returns:
            创建结果
        """
        # 验证支出记录ID
        if not expense_record_ids:
            raise ValueError("创建报销单需要至少一个支出记录ID")
        
        # 模拟创建报销单
        bill_id = f"REIM-{random.randint(10000, 99999)}"
        bill_number = f"BX-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        # 获取支出记录金额总和
        total_amount = 0.0
        for record_id in expense_record_ids:
            # 模拟获取支出记录
            record = self._mock_get_expense_record(record_id)
            if record:
                total_amount += float(record.get("amount", 0.0))
        
        # 确定需要补充的字段
        required_fields = [
            "reimbursement_type",
            "department",
            "applicant",
            "payment_method",
            "bank_account"
        ]
        
        # 返回创建结果
        return {
            "bill_id": bill_id,
            "bill_number": bill_number,
            "total_amount": total_amount,
            "expense_records": expense_record_ids,
            "required_fields": required_fields,
            "status": "draft"
        }
    
    async def _link_travel(self, bill_id: str, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """关联出差申请
        
        Args:
            bill_id: 报销单ID
            link_data: 关联数据
            
        Returns:
            关联结果
        """
        # 验证参数
        if not bill_id:
            raise ValueError("关联出差申请需要报销单ID")
        
        # 获取关联的出差申请ID
        trip_ids = link_data.get("trip_ids", [])
        
        if not trip_ids:
            raise ValueError("关联出差申请需要至少一个出差申请ID")
        
        # 模拟关联出差申请
        linked_trips = []
        total_days = 0
        allowance_amount = 0.0
        
        for trip_id in trip_ids:
            # 模拟获取出差申请
            trip = self._mock_get_travel_application(trip_id)
            if trip:
                # 计算出差天数
                start_date = datetime.strptime(trip.get("start_date"), "%Y-%m-%d")
                end_date = datetime.strptime(trip.get("end_date"), "%Y-%m-%d")
                days = (end_date - start_date).days + 1
                
                # 计算补助金额（假设每天100元）
                trip_allowance = days * 100.0
                
                linked_trips.append({
                    "trip_id": trip_id,
                    "destination": trip.get("destination"),
                    "days": days,
                    "allowance": trip_allowance
                })
                
                total_days += days
                allowance_amount += trip_allowance
        
        # 返回关联结果
        return {
            "bill_id": bill_id,
            "linked_trips": linked_trips,
            "travel_days": total_days,
            "allowance_amount": allowance_amount
        }
    
    async def _link_loan(self, bill_id: str, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """关联借款
        
        Args:
            bill_id: 报销单ID
            link_data: 关联数据
            
        Returns:
            关联结果
        """
        # 验证参数
        if not bill_id:
            raise ValueError("关联借款需要报销单ID")
        
        # 获取关联的借款ID
        loan_ids = link_data.get("loan_ids", [])
        
        if not loan_ids:
            raise ValueError("关联借款需要至少一个借款ID")
        
        # 模拟关联借款
        linked_loans = []
        total_loan_amount = 0.0
        
        for loan_id in loan_ids:
            # 模拟获取借款
            loan = self._mock_get_loan(loan_id)
            if loan:
                linked_loans.append({
                    "loan_id": loan_id,
                    "loan_number": loan.get("loan_number"),
                    "amount": loan.get("amount"),
                    "unpaid_amount": loan.get("unpaid_amount")
                })
                
                total_loan_amount += float(loan.get("unpaid_amount", 0.0))
        
        # 返回关联结果
        return {
            "bill_id": bill_id,
            "linked_loans": linked_loans,
            "total_loan_amount": total_loan_amount,
            "repayment_amount": total_loan_amount
        }
    
    async def _supplement_data(self, bill_id: str, supplement_data: Dict[str, Any]) -> Dict[str, Any]:
        """补充报销单数据
        
        Args:
            bill_id: 报销单ID
            supplement_data: 补充数据
            
        Returns:
            补充结果
        """
        # 验证参数
        if not bill_id:
            raise ValueError("补充数据需要报销单ID")
        
        # 模拟获取报销单
        bill = self._mock_get_reimbursement(bill_id)
        
        if not bill:
            raise ValueError(f"找不到报销单: {bill_id}")
        
        # 更新报销单数据
        for key, value in supplement_data.items():
            bill[key] = value
        
        # 更新必填字段状态
        required_fields = bill.get("required_fields", [])
        for field in list(required_fields):
            if field in supplement_data:
                required_fields.remove(field)
        
        bill["required_fields"] = required_fields
        
        # 返回补充结果
        return {
            "bill_id": bill_id,
            "updated_fields": list(supplement_data.keys()),
            "remaining_required_fields": required_fields,
            "is_complete": len(required_fields) == 0
        }
    
    async def _save_bill(self, bill_id: str) -> Dict[str, Any]:
        """保存报销单
        
        Args:
            bill_id: 报销单ID
            
        Returns:
            保存结果
        """
        # 验证参数
        if not bill_id:
            raise ValueError("保存报销单需要报销单ID")
        
        # 模拟获取报销单
        bill = self._mock_get_reimbursement(bill_id)
        
        if not bill:
            raise ValueError(f"找不到报销单: {bill_id}")
        
        # 检查必填字段
        required_fields = bill.get("required_fields", [])
        
        # 返回保存结果
        return {
            "bill_id": bill_id,
            "save_status": "success",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ready_to_submit": len(required_fields) == 0,
            "remaining_required_fields": required_fields
        }
    
    def _mock_get_expense_record(self, record_id: str) -> Dict[str, Any]:
        """模拟获取支出记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            支出记录
        """
        # 生成随机金额（50-5000之间）
        amount = round(random.uniform(50, 5000), 2)
        
        # 创建模拟支出记录
        expense_types = ["差旅费", "办公用品", "招待费", "会议费", "交通费"]
        
        record = {
            "record_id": record_id,
            "expense_type": random.choice(expense_types),
            "amount": amount,
            "status": "complete"
        }
        
        return record
    
    def _mock_get_travel_application(self, trip_id: str) -> Dict[str, Any]:
        """模拟获取出差申请
        
        Args:
            trip_id: 出差申请ID
            
        Returns:
            出差申请
        """
        # 生成随机日期（过去30天内）
        start_date = datetime.now() - timedelta(days=random.randint(1, 30))
        end_date = start_date + timedelta(days=random.randint(1, 7))
        
        # 创建模拟出差申请
        destinations = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆"]
        
        trip = {
            "trip_id": trip_id,
            "trip_number": f"CC-{random.randint(10000, 99999)}",
            "destination": random.choice(destinations),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "purpose": "业务洽谈",
            "status": "approved"
        }
        
        return trip
    
    def _mock_get_loan(self, loan_id: str) -> Dict[str, Any]:
        """模拟获取借款
        
        Args:
            loan_id: 借款ID
            
        Returns:
            借款
        """
        # 生成随机金额（1000-10000之间）
        amount = round(random.uniform(1000, 10000), 2)
        unpaid_amount = round(amount * random.uniform(0.3, 1.0), 2)
        
        # 创建模拟借款
        loan = {
            "loan_id": loan_id,
            "loan_number": f"JK-{random.randint(10000, 99999)}",
            "amount": amount,
            "unpaid_amount": unpaid_amount,
            "loan_date": (datetime.now() - timedelta(days=random.randint(10, 60))).strftime("%Y-%m-%d"),
            "status": "active"
        }
        
        return loan
    
    def _mock_get_reimbursement(self, bill_id: str) -> Dict[str, Any]:
        """模拟获取报销单
        
        Args:
            bill_id: 报销单ID
            
        Returns:
            报销单
        """
        # 生成随机金额（100-10000之间）
        total_amount = round(random.uniform(100, 10000), 2)
        
        # 创建模拟报销单
        bill = {
            "bill_id": bill_id,
            "bill_number": f"BX-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "total_amount": total_amount,
            "expense_records": [f"ER-{random.randint(10000, 99999)}" for _ in range(random.randint(1, 5))],
            "required_fields": ["reimbursement_type", "department", "applicant"],
            "status": "draft",
            "create_time": (datetime.now() - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return bill 