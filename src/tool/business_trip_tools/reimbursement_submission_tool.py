"""
报销提交工具
验证报销单的完整性和合规性，然后提交审批
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from ..base import BaseTool

class ReimbursementSubmissionTool(BaseTool):
    """报销提交工具，验证并提交报销单"""
    
    @property
    def name(self) -> str:
        return "submit_reimbursement"
    
    @property
    def description(self) -> str:
        return "验证报销单的完整性和合规性，然后提交审批"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "bill_id": {
                    "type": "string",
                    "description": "报销单ID"
                },
                "validate_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否只验证不提交"
                }
            },
            "required": ["bill_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行报销提交工具
        
        Args:
            bill_id: 报销单ID
            validate_only: 是否只验证不提交，默认为False
            
        Returns:
            验证和提交结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        bill_id = kwargs.get("bill_id")
        validate_only = kwargs.get("validate_only", False)
        
        # 验证报销单
        validation_result = await self._validate_reimbursement(bill_id)
        
        # 如果只验证或验证未通过，则只返回验证结果
        if validate_only or validation_result["overall_status"] != "pass":
            return {
                "validation_result": validation_result,
                "submission_result": None
            }
        
        # 提交报销单
        submission_result = await self._submit_reimbursement(bill_id)
        
        # 返回验证和提交结果
        return {
            "validation_result": validation_result,
            "submission_result": submission_result
        }
    
    async def _validate_reimbursement(self, bill_id: str) -> Dict[str, Any]:
        """验证报销单
        
        Args:
            bill_id: 报销单ID
            
        Returns:
            验证结果
        """
        # 模拟获取报销单
        bill = self._mock_get_reimbursement(bill_id)
        
        if not bill:
            return {
                "overall_status": "fail",
                "error_message": f"找不到报销单: {bill_id}"
            }
        
        # 预算检查
        budget_check = self._mock_budget_check(bill)
        
        # 发票一致性检查
        invoice_check = self._mock_invoice_check(bill)
        
        # 合规性检查
        compliance_check = self._mock_compliance_check(bill)
        
        # 附件完整性检查
        attachment_check = self._mock_attachment_check(bill)
        
        # 确定整体状态
        if (budget_check["status"] == "pass" and 
            invoice_check["status"] == "pass" and 
            compliance_check["status"] == "pass" and 
            attachment_check["status"] == "pass"):
            overall_status = "pass"
        else:
            overall_status = "fail"
        
        # 返回验证结果
        return {
            "overall_status": overall_status,
            "budget_check": budget_check,
            "invoice_check": invoice_check,
            "compliance_check": compliance_check,
            "attachment_check": attachment_check
        }
    
    async def _submit_reimbursement(self, bill_id: str) -> Dict[str, Any]:
        """提交报销单
        
        Args:
            bill_id: 报销单ID
            
        Returns:
            提交结果
        """
        # 模拟获取报销单
        bill = self._mock_get_reimbursement(bill_id)
        
        if not bill:
            return {
                "submit_status": "fail",
                "error_message": f"找不到报销单: {bill_id}"
            }
        
        # 模拟提交过程
        workflow_id = f"WF-{random.randint(100000, 999999)}"
        
        # 模拟获取下一步审批人
        next_approvers = self._mock_get_next_approvers(bill)
        
        # 检查是否需要提交纸质单据
        paper_required = self._is_paper_required(bill)
        
        # 返回提交结果
        return {
            "submit_status": "success",
            "workflow_id": workflow_id,
            "submit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_approvers": next_approvers,
            "paper_required": paper_required
        }
    
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
        reimbursement_types = ["差旅报销", "日常报销", "招待报销", "会议报销"]
        departments = ["技术部", "市场部", "财务部", "人力资源部", "销售部"]
        
        bill = {
            "bill_id": bill_id,
            "bill_number": f"BX-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "reimbursement_type": random.choice(reimbursement_types),
            "department": random.choice(departments),
            "applicant": "张三",
            "total_amount": total_amount,
            "expense_records": [f"ER-{random.randint(10000, 99999)}" for _ in range(random.randint(1, 5))],
            "required_fields": [],
            "status": "draft",
            "create_time": (datetime.now() - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return bill
    
    def _mock_budget_check(self, bill: Dict[str, Any]) -> Dict[str, Any]:
        """模拟预算检查
        
        Args:
            bill: 报销单
            
        Returns:
            预算检查结果
        """
        # 部门预算金额（模拟）
        department_budget = {
            "技术部": 100000,
            "市场部": 80000,
            "财务部": 50000,
            "人力资源部": 30000,
            "销售部": 120000
        }
        
        # 部门已使用预算（模拟）
        department_used = {
            "技术部": random.uniform(10000, 90000),
            "市场部": random.uniform(10000, 70000),
            "财务部": random.uniform(5000, 40000),
            "人力资源部": random.uniform(5000, 25000),
            "销售部": random.uniform(20000, 100000)
        }
        
        # 获取部门
        department = bill.get("department", "未知部门")
        
        # 如果部门存在预算
        if department in department_budget:
            budget = department_budget[department]
            used = department_used[department]
            remaining = budget - used
            amount = bill.get("total_amount", 0.0)
            
            # 检查是否超预算
            if amount <= remaining:
                status = "pass"
                message = f"预算充足，剩余预算: {remaining:.2f}"
            else:
                status = "warn"
                message = f"预算不足，超出: {(amount - remaining):.2f}"
        else:
            status = "warn"
            message = "未找到部门预算信息"
        
        return {
            "status": status,
            "message": message,
            "details": {
                "department": department,
                "budget": department_budget.get(department, 0.0),
                "used": department_used.get(department, 0.0),
                "remaining": remaining if department in department_budget else 0.0,
                "amount": bill.get("total_amount", 0.0)
            }
        }
    
    def _mock_invoice_check(self, bill: Dict[str, Any]) -> Dict[str, Any]:
        """模拟发票一致性检查
        
        Args:
            bill: 报销单
            
        Returns:
            发票检查结果
        """
        # 90%概率通过
        if random.random() < 0.9:
            status = "pass"
            message = "发票信息一致"
            issues = []
        else:
            status = "fail"
            message = "发票信息不一致"
            
            # 随机生成问题
            possible_issues = [
                "发票抬头不符",
                "发票金额与申报金额不一致",
                "发票已过期",
                "发票税率不正确",
                "发票类型不符合报销要求"
            ]
            
            # 随机选择1-2个问题
            issue_count = random.randint(1, min(2, len(possible_issues)))
            issues = random.sample(possible_issues, issue_count)
        
        return {
            "status": status,
            "message": message,
            "issues": issues
        }
    
    def _mock_compliance_check(self, bill: Dict[str, Any]) -> Dict[str, Any]:
        """模拟合规性检查
        
        Args:
            bill: 报销单
            
        Returns:
            合规性检查结果
        """
        # 95%概率通过
        if random.random() < 0.95:
            status = "pass"
            message = "符合公司报销政策"
            issues = []
        else:
            status = "fail"
            message = "存在不符合公司报销政策的问题"
            
            # 随机生成问题
            possible_issues = [
                "单笔餐饮费用超过限额",
                "交通费用未选择经济舱/二等座",
                "住宿费用超过标准",
                "未提供必要的审批文件",
                "缺少详细的费用说明"
            ]
            
            # 随机选择1-2个问题
            issue_count = random.randint(1, min(2, len(possible_issues)))
            issues = random.sample(possible_issues, issue_count)
        
        return {
            "status": status,
            "message": message,
            "issues": issues
        }
    
    def _mock_attachment_check(self, bill: Dict[str, Any]) -> Dict[str, Any]:
        """模拟附件完整性检查
        
        Args:
            bill: 报销单
            
        Returns:
            附件检查结果
        """
        # 95%概率通过
        if random.random() < 0.95:
            status = "pass"
            message = "附件完整"
            issues = []
        else:
            status = "fail"
            message = "附件不完整"
            
            # 随机生成问题
            possible_issues = [
                "缺少发票原件",
                "缺少出差审批单",
                "缺少会议议程",
                "缺少参会人员名单",
                "缺少招待客户信息"
            ]
            
            # 随机选择1-2个问题
            issue_count = random.randint(1, min(2, len(possible_issues)))
            issues = random.sample(possible_issues, issue_count)
        
        return {
            "status": status,
            "message": message,
            "issues": issues
        }
    
    def _mock_get_next_approvers(self, bill: Dict[str, Any]) -> List[Dict[str, Any]]:
        """模拟获取下一步审批人
        
        Args:
            bill: 报销单
            
        Returns:
            审批人列表
        """
        # 部门经理审批
        department = bill.get("department", "未知部门")
        department_managers = {
            "技术部": {"id": "M001", "name": "李四", "title": "技术经理"},
            "市场部": {"id": "M002", "name": "王五", "title": "市场经理"},
            "财务部": {"id": "M003", "name": "赵六", "title": "财务经理"},
            "人力资源部": {"id": "M004", "name": "钱七", "title": "人力资源经理"},
            "销售部": {"id": "M005", "name": "孙八", "title": "销售经理"}
        }
        
        # 财务审批
        finance_approvers = [
            {"id": "F001", "name": "周九", "title": "财务主管"},
            {"id": "F002", "name": "吴十", "title": "财务总监"}
        ]
        
        # 获取审批人
        approvers = []
        
        # 添加部门经理
        if department in department_managers:
            approvers.append(department_managers[department])
        
        # 金额大于5000，需要财务总监审批
        if bill.get("total_amount", 0.0) > 5000:
            approvers.append(finance_approvers[1])
        else:
            approvers.append(finance_approvers[0])
        
        return approvers
    
    def _is_paper_required(self, bill: Dict[str, Any]) -> bool:
        """检查是否需要提交纸质单据
        
        Args:
            bill: 报销单
            
        Returns:
            是否需要提交纸质单据
        """
        # 判断条件：
        # 1. 金额大于5000
        # 2. 报销类型为招待报销
        amount = bill.get("total_amount", 0.0)
        reimb_type = bill.get("reimbursement_type", "")
        
        return amount > 5000 or reimb_type == "招待报销" 