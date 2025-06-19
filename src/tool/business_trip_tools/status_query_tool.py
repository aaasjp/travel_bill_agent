"""
状态查询工具
查询用户权限、报销单状态、审批进度、支付状态等信息
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from ..base import BaseTool

class StatusQueryTool(BaseTool):
    """状态查询工具，提供各种状态信息查询"""
    
    @property
    def name(self) -> str:
        return "query_status"
    
    @property
    def description(self) -> str:
        return "查询用户权限、报销单状态、审批进度、支付状态等信息"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["permission", "bill_list", "approval", "payment"],
                    "description": "查询类型"
                },
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "bill_id": {
                    "type": "string",
                    "description": "报销单ID（查询特定单据时需要）"
                },
                "filters": {
                    "type": "object",
                    "description": "查询过滤条件"
                }
            },
            "required": ["query_type", "user_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行状态查询工具
        
        Args:
            query_type: 查询类型
            user_id: 用户ID
            bill_id: 报销单ID（查询特定单据时需要）
            filters: 查询过滤条件
            
        Returns:
            查询结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        query_type = kwargs.get("query_type")
        user_id = kwargs.get("user_id")
        bill_id = kwargs.get("bill_id")
        filters = kwargs.get("filters", {})
        
        # 根据查询类型执行相应的函数
        if query_type == "permission":
            return await self._query_permission(user_id)
        elif query_type == "bill_list":
            return await self._query_bill_list(user_id, filters)
        elif query_type == "approval":
            if not bill_id:
                raise ValueError("查询审批进度需要报销单ID")
            return await self._query_approval(user_id, bill_id)
        elif query_type == "payment":
            if not bill_id:
                raise ValueError("查询支付状态需要报销单ID")
            return await self._query_payment(user_id, bill_id)
        else:
            raise ValueError(f"不支持的查询类型: {query_type}")
    
    async def _query_permission(self, user_id: str) -> Dict[str, Any]:
        """查询用户权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限查询结果
        """
        # 模拟用户权限查询
        has_permission = random.random() < 0.95  # 95%概率有权限
        need_exam = random.random() < 0.2  # 20%概率需要考试
        
        if has_permission:
            result = {
                "has_ees_permission": True,
                "need_exam": need_exam
            }
            
            if need_exam:
                result["exam_link"] = "https://example.com/exam/ees-training"
                result["exam_expiry"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            result = {
                "has_ees_permission": False,
                "reason": "尚未完成权限申请流程",
                "application_link": "https://example.com/apply/ees-permission"
            }
        
        return result
    
    async def _query_bill_list(self, user_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """查询报销单列表
        
        Args:
            user_id: 用户ID
            filters: 过滤条件
            
        Returns:
            报销单列表查询结果
        """
        # 处理过滤条件
        status_filter = filters.get("status", "all")
        date_range = filters.get("date_range", {})
        start_date = date_range.get("start_date")
        end_date = date_range.get("end_date")
        
        # 模拟生成报销单列表
        bill_count = random.randint(0, 10)
        bills = []
        
        for i in range(bill_count):
            # 生成随机日期（过去90天内）
            created_date = datetime.now() - timedelta(days=random.randint(0, 90))
            
            # 如果有日期过滤，检查是否在范围内
            if start_date and end_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                if created_date < start_date_obj or created_date > end_date_obj:
                    continue
            
            # 生成随机金额（100-10000之间）
            amount = round(random.uniform(100, 10000), 2)
            
            # 生成随机状态
            statuses = ["draft", "submitted", "approving", "approved", "rejected", "paid"]
            weights = [0.1, 0.2, 0.3, 0.2, 0.1, 0.1]
            status = random.choices(statuses, weights=weights, k=1)[0]
            
            # 如果有状态过滤，检查是否匹配
            if status_filter != "all" and status != status_filter:
                continue
            
            # 创建报销单对象
            reimbursement_types = ["差旅报销", "日常报销", "招待报销", "会议报销"]
            bill = {
                "bill_id": f"REIM-{random.randint(10000, 99999)}",
                "bill_number": f"BX-{created_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                "title": f"{random.choice(reimbursement_types)}-{created_date.strftime('%Y%m%d')}",
                "reimbursement_type": random.choice(reimbursement_types),
                "amount": amount,
                "status": status,
                "created_at": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": (created_date + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            bills.append(bill)
        
        # 返回查询结果
        return {
            "bills": bills,
            "total_count": len(bills)
        }
    
    async def _query_approval(self, user_id: str, bill_id: str) -> Dict[str, Any]:
        """查询审批进度
        
        Args:
            user_id: 用户ID
            bill_id: 报销单ID
            
        Returns:
            审批进度查询结果
        """
        # 模拟获取报销单
        bill = self._mock_get_reimbursement(bill_id)
        
        if not bill:
            return {
                "error": f"找不到报销单: {bill_id}"
            }
        
        # 获取审批状态
        status = bill.get("status", "unknown")
        
        # 创建审批历史
        approval_history = []
        
        if status in ["submitted", "approving", "approved", "rejected", "paid"]:
            # 已提交
            submit_time = datetime.strptime(bill.get("created_at", ""), "%Y-%m-%d %H:%M:%S")
            approval_history.append({
                "step": "提交申请",
                "operator": "张三",
                "operator_id": user_id,
                "action": "submit",
                "time": submit_time.strftime("%Y-%m-%d %H:%M:%S"),
                "comment": "提交报销申请"
            })
            
            # 部门经理审批
            if status in ["approving", "approved", "rejected", "paid"]:
                dept_time = submit_time + timedelta(hours=random.randint(1, 24))
                dept_action = "approve"
                dept_comment = "同意报销"
                
                if status == "rejected" and random.random() < 0.5:
                    dept_action = "reject"
                    dept_comment = "不符合部门报销规定，请修改后重新提交"
                
                approval_history.append({
                    "step": "部门经理审批",
                    "operator": "李四",
                    "operator_id": "M001",
                    "action": dept_action,
                    "time": dept_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "comment": dept_comment
                })
                
                # 如果部门经理拒绝，就没有后续步骤了
                if dept_action == "reject":
                    status = "rejected"
            
            # 财务审批
            if status in ["approved", "paid"]:
                finance_time = submit_time + timedelta(hours=random.randint(25, 48))
                approval_history.append({
                    "step": "财务审批",
                    "operator": "赵六",
                    "operator_id": "F001",
                    "action": "approve",
                    "time": finance_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "comment": "财务审核通过"
                })
            
            # 支付
            if status == "paid":
                payment_time = submit_time + timedelta(hours=random.randint(49, 72))
                approval_history.append({
                    "step": "财务支付",
                    "operator": "钱七",
                    "operator_id": "F003",
                    "action": "pay",
                    "time": payment_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "comment": "已完成支付"
                })
        
        # 确定下一步
        next_steps = []
        if status == "draft":
            next_steps = ["提交申请"]
        elif status == "submitted":
            next_steps = ["部门经理审批"]
        elif status == "approving":
            next_steps = ["财务审批"]
        elif status == "approved":
            next_steps = ["财务支付"]
        elif status in ["rejected", "paid"]:
            next_steps = []
        
        # 返回查询结果
        return {
            "bill_id": bill_id,
            "current_status": status,
            "approval_history": approval_history,
            "next_steps": next_steps
        }
    
    async def _query_payment(self, user_id: str, bill_id: str) -> Dict[str, Any]:
        """查询支付状态
        
        Args:
            user_id: 用户ID
            bill_id: 报销单ID
            
        Returns:
            支付状态查询结果
        """
        # 模拟获取报销单
        bill = self._mock_get_reimbursement(bill_id)
        
        if not bill:
            return {
                "error": f"找不到报销单: {bill_id}"
            }
        
        # 获取状态
        status = bill.get("status", "unknown")
        
        # 支付信息
        payment_info = {}
        
        if status == "paid":
            # 生成随机支付日期（过去7天内）
            payment_date = datetime.now() - timedelta(days=random.randint(0, 7))
            
            # 支付方式
            payment_methods = ["银行转账", "支付宝", "微信支付"]
            
            payment_info = {
                "payment_status": "已支付",
                "payment_date": payment_date.strftime("%Y-%m-%d"),
                "payment_time": payment_date.strftime("%H:%M:%S"),
                "amount": bill.get("amount", 0.0),
                "payment_method": random.choice(payment_methods),
                "transaction_id": f"TX-{random.randint(100000, 999999)}",
                "payee": "张三"
            }
        elif status == "approved":
            payment_info = {
                "payment_status": "待支付",
                "estimated_payment_date": (datetime.now() + timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d"),
                "amount": bill.get("amount", 0.0),
                "pending_reason": "已审批，等待财务处理"
            }
        else:
            payment_info = {
                "payment_status": "未支付",
                "amount": bill.get("amount", 0.0),
                "pending_reason": f"当前状态为\"{status}\"，尚未到支付环节"
            }
        
        # 返回查询结果
        return {
            "bill_id": bill_id,
            "bill_number": bill.get("bill_number", ""),
            "bill_status": status,
            **payment_info
        }
    
    def _mock_get_reimbursement(self, bill_id: str) -> Dict[str, Any]:
        """模拟获取报销单
        
        Args:
            bill_id: 报销单ID
            
        Returns:
            报销单
        """
        # 生成创建时间（过去90天内）
        created_at = datetime.now() - timedelta(days=random.randint(0, 90))
        
        # 生成随机金额（100-10000之间）
        amount = round(random.uniform(100, 10000), 2)
        
        # 生成随机状态
        statuses = ["draft", "submitted", "approving", "approved", "rejected", "paid"]
        weights = [0.1, 0.2, 0.3, 0.2, 0.1, 0.1]
        status = random.choices(statuses, weights=weights, k=1)[0]
        
        # 创建报销单对象
        reimbursement_types = ["差旅报销", "日常报销", "招待报销", "会议报销"]
        bill = {
            "bill_id": bill_id,
            "bill_number": f"BX-{created_at.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "title": f"{random.choice(reimbursement_types)}-{created_at.strftime('%Y%m%d')}",
            "reimbursement_type": random.choice(reimbursement_types),
            "amount": amount,
            "status": status,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (created_at + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return bill 