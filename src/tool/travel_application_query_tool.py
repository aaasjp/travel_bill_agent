"""
差旅申请查询工具
查询用户的差旅申请单，包括可报销次数等信息
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from .base import BaseTool

class TravelApplicationQueryTool(BaseTool):
    """差旅申请查询工具，提供差旅申请信息查询"""
    
    @property
    def name(self) -> str:
        return "query_travel_applications"
    
    @property
    def description(self) -> str:
        return "查询用户的差旅申请单，包括可报销次数等信息"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"}
                    },
                    "description": "日期范围"
                },
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "reimbursable", "partially_reimbursed"],
                    "description": "状态过滤"
                }
            },
            "required": ["user_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行差旅申请查询工具
        
        Args:
            user_id: 用户ID
            date_range: 日期范围，包含start_date和end_date
            status_filter: 状态过滤，可选值为all, reimbursable, partially_reimbursed
            
        Returns:
            查询结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        user_id = kwargs.get("user_id")
        date_range = kwargs.get("date_range", {})
        status_filter = kwargs.get("status_filter", "all")
        
        # 查询差旅申请
        applications = await self._query_travel_applications(user_id, date_range, status_filter)
        
        # 返回查询结果
        return {
            "applications": applications
        }
    
    async def _query_travel_applications(self, user_id: str, date_range: Dict[str, str], status_filter: str) -> List[Dict[str, Any]]:
        """查询差旅申请
        
        Args:
            user_id: 用户ID
            date_range: 日期范围
            status_filter: 状态过滤
            
        Returns:
            差旅申请列表
        """
        # 处理日期范围
        start_date = date_range.get("start_date")
        end_date = date_range.get("end_date")
        
        # 模拟生成差旅申请列表
        application_count = random.randint(0, 5)
        applications = []
        
        # 目的地列表
        destinations = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安", "武汉", "南京"]
        
        for i in range(application_count):
            # 生成随机日期（过去180天内的出差）
            base_date = datetime.now() - timedelta(days=random.randint(0, 180))
            trip_start_date = base_date
            trip_end_date = base_date + timedelta(days=random.randint(1, 7))
            
            # 如果有日期过滤，检查是否在范围内
            if start_date and end_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                if trip_end_date < start_date_obj or trip_start_date > end_date_obj:
                    continue
            
            # 生成可报销和已报销次数
            max_reimbursable_times = random.randint(1, 3)
            reimbursed_times = random.randint(0, max_reimbursable_times)
            
            # 如果有状态过滤，检查是否匹配
            if status_filter == "reimbursable" and reimbursed_times >= max_reimbursable_times:
                continue
            elif status_filter == "partially_reimbursed" and (reimbursed_times == 0 or reimbursed_times >= max_reimbursable_times):
                continue
            
            # 生成差旅申请
            application = {
                "application_id": f"TA-{random.randint(10000, 99999)}",
                "trip_number": f"CC-{base_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                "destination": random.choice(destinations),
                "start_date": trip_start_date.strftime("%Y-%m-%d"),
                "end_date": trip_end_date.strftime("%Y-%m-%d"),
                "purpose": self._generate_random_purpose(),
                "reimbursable_times": max_reimbursable_times,
                "reimbursed_times": reimbursed_times,
                "status": "approved" if random.random() < 0.9 else "completed"
            }
            
            applications.append(application)
        
        # 返回差旅申请列表
        return applications
    
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