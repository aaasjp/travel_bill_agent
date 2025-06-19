"""
补助处理工具
检查和申请差旅补助
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from ..base import BaseTool

class AllowanceProcessingTool(BaseTool):
    """补助处理工具，检查和申请差旅补助"""
    
    @property
    def name(self) -> str:
        return "process_allowance"
    
    @property
    def description(self) -> str:
        return "检查和申请差旅补助"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_eligibility", "apply_manual"],
                    "description": "操作类型"
                },
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "trip_order_id": {
                    "type": "string",
                    "description": "出差申请单ID"
                }
            },
            "required": ["action", "user_id", "trip_order_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行补助处理工具
        
        Args:
            action: 操作类型，可选值为check_eligibility, apply_manual
            user_id: 用户ID
            trip_order_id: 出差申请单ID
            
        Returns:
            操作结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        action = kwargs.get("action")
        user_id = kwargs.get("user_id")
        trip_order_id = kwargs.get("trip_order_id")
        
        # 根据操作类型执行相应的函数
        if action == "check_eligibility":
            return await self._check_eligibility(user_id, trip_order_id)
        elif action == "apply_manual":
            return await self._apply_manual(user_id, trip_order_id)
        else:
            raise ValueError(f"不支持的操作类型: {action}")
    
    async def _check_eligibility(self, user_id: str, trip_order_id: str) -> Dict[str, Any]:
        """检查补助资格
        
        Args:
            user_id: 用户ID
            trip_order_id: 出差申请单ID
            
        Returns:
            检查结果
        """
        # 模拟获取出差申请
        trip = self._mock_get_travel_application(trip_order_id)
        
        if not trip:
            return {
                "eligible": False,
                "auto_process": False,
                "allowance_amount": 0.0,
                "reason": f"找不到出差申请单: {trip_order_id}"
            }
        
        # 检查是否已经确认行程
        trip_confirmed = trip.get("status") == "completed"
        
        # 检查是否是国内出差
        is_domestic = "destination_type" in trip and trip["destination_type"] == "domestic"
        
        # 检查出差天数（至少2天）
        start_date = datetime.strptime(trip.get("start_date", ""), "%Y-%m-%d")
        end_date = datetime.strptime(trip.get("end_date", ""), "%Y-%m-%d")
        days = (end_date - start_date).days + 1
        min_days_required = 2
        
        # 判断是否符合自动处理条件
        eligible = days >= min_days_required and is_domestic
        auto_process = eligible and trip_confirmed
        
        # 计算补助金额（假设每天100元）
        allowance_amount = days * 100.0 if eligible else 0.0
        
        # 生成原因说明
        if not eligible:
            if days < min_days_required:
                reason = f"出差天数不足，要求至少{min_days_required}天，实际{days}天"
            elif not is_domestic:
                reason = "国际出差需要单独申请补助"
            else:
                reason = "不符合补助条件"
        else:
            if not trip_confirmed:
                reason = "符合补助条件，但需要先确认行程"
            else:
                reason = "符合自动处理条件"
        
        # 返回检查结果
        return {
            "eligible": eligible,
            "auto_process": auto_process,
            "allowance_amount": allowance_amount,
            "days": days,
            "reason": reason
        }
    
    async def _apply_manual(self, user_id: str, trip_order_id: str) -> Dict[str, Any]:
        """手动申请补助
        
        Args:
            user_id: 用户ID
            trip_order_id: 出差申请单ID
            
        Returns:
            申请结果
        """
        # 检查补助资格
        eligibility_result = await self._check_eligibility(user_id, trip_order_id)
        
        if not eligibility_result.get("eligible", False):
            return {
                "application_id": None,
                "status": "failed",
                "amount": 0.0,
                "reason": eligibility_result.get("reason", "不符合补助条件")
            }
        
        # 模拟获取出差申请
        trip = self._mock_get_travel_application(trip_order_id)
        
        # 如果行程未确认，尝试确认行程
        if trip.get("status") != "completed":
            confirm_result = self._mock_confirm_trip(trip_order_id)
            if not confirm_result.get("success", False):
                return {
                    "application_id": None,
                    "status": "failed",
                    "amount": 0.0,
                    "reason": "行程确认失败，请稍后再试"
                }
        
        # 模拟申请补助
        application_id = f"AL-{random.randint(10000, 99999)}"
        amount = eligibility_result.get("allowance_amount", 0.0)
        
        # 返回申请结果
        return {
            "application_id": application_id,
            "status": "success",
            "amount": amount,
            "days": eligibility_result.get("days", 0),
            "trip_info": {
                "trip_order_id": trip_order_id,
                "destination": trip.get("destination", ""),
                "start_date": trip.get("start_date", ""),
                "end_date": trip.get("end_date", "")
            },
            "payment_status": "pending",
            "estimated_payment_date": (datetime.now() + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d")
        }
    
    def _mock_get_travel_application(self, trip_id: str) -> Dict[str, Any]:
        """模拟获取出差申请
        
        Args:
            trip_id: 出差申请ID
            
        Returns:
            出差申请
        """
        # 生成随机日期（过去180天内的出差）
        base_date = datetime.now() - timedelta(days=random.randint(0, 180))
        trip_start_date = base_date
        trip_end_date = base_date + timedelta(days=random.randint(1, 7))
        
        # 目的地列表
        domestic_destinations = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安", "武汉", "南京"]
        international_destinations = ["东京", "首尔", "新加坡", "伦敦", "纽约", "巴黎", "悉尼", "柏林", "莫斯科", "迪拜"]
        
        # 随机选择国内/国际
        is_domestic = random.random() < 0.8  # 80%概率是国内出差
        
        if is_domestic:
            destination = random.choice(domestic_destinations)
            destination_type = "domestic"
        else:
            destination = random.choice(international_destinations)
            destination_type = "international"
        
        # 随机选择状态
        status = random.choice(["approved", "completed"])
        
        # 创建出差申请
        trip = {
            "trip_id": trip_id,
            "trip_number": f"CC-{base_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "destination": destination,
            "destination_type": destination_type,
            "start_date": trip_start_date.strftime("%Y-%m-%d"),
            "end_date": trip_end_date.strftime("%Y-%m-%d"),
            "purpose": self._generate_random_purpose(),
            "status": status
        }
        
        return trip
    
    def _mock_confirm_trip(self, trip_id: str) -> Dict[str, Any]:
        """模拟确认行程
        
        Args:
            trip_id: 出差申请ID
            
        Returns:
            确认结果
        """
        # 90%概率成功
        success = random.random() < 0.9
        
        if success:
            return {
                "success": True,
                "trip_id": trip_id,
                "message": "行程确认成功"
            }
        else:
            return {
                "success": False,
                "trip_id": trip_id,
                "message": "行程确认失败，系统繁忙，请稍后再试"
            }
    
    def _generate_random_purpose(self) -> str:
        """生成随机出差事由
        
        Returns:
            出差事由
        """
        purposes = [
            "客户拜访",
            "项目调研",
            "技术交流",
            "参加会议",
            "项目验收",
            "产品培训",
            "市场调研",
            "供应商洽谈",
            "展会参展",
            "分支机构检查"
        ]
        
        return random.choice(purposes) 