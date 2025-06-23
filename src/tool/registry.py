"""
工具注册表模块
管理和执行工具
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import time

# 导入基类
from .base import BaseTool

class ToolGroup(Enum):
    """工具组枚举"""
    BUSINESS_TRIP = "business_trip"
    BUSINESS_TRIP_V2 = "business_trip_v2"
    DEFAULT = "default"

class ToolRegistry:
    """工具注册表，管理所有工具并与LangGraph集成"""
    
    def __init__(self):
        # 使用嵌套字典结构：{group_name: {tool_name: tool_instance}}
        self._tool_groups: Dict[str, Dict[str, BaseTool]] = {}
    
    def register_tool(self, tool_instance: BaseTool, group_name: ToolGroup = ToolGroup.DEFAULT) -> None:
        """注册工具到指定组
        
        Args:
            tool_instance: 工具实例
            group_name: 工具组枚举，默认为DEFAULT
        """
        if not tool_instance.name:
            raise ValueError("工具必须有名称")
        
        # 获取枚举值作为组名
        group_key = group_name.value
        
        # 如果组不存在，创建新组
        if group_key not in self._tool_groups:
            self._tool_groups[group_key] = {}
        
        self._tool_groups[group_key][tool_instance.name] = tool_instance
    
    def register_tools_to_group(self, tools: List[BaseTool], group_name: ToolGroup) -> None:
        """批量注册工具到指定组
        
        Args:
            tools: 工具实例列表
            group_name: 工具组枚举
        """
        for tool in tools:
            self.register_tool(tool, group_name)
    
    def get_tool(self, name: str, group_name: Optional[ToolGroup] = None) -> Optional[BaseTool]:
        """获取工具
        
        Args:
            name: 工具名称
            group_name: 工具组枚举，如果为None则在所有组中查找
            
        Returns:
            工具实例，如果不存在则返回None
        """
        if group_name:
            # 在指定组中查找
            group_key = group_name.value
            return self._tool_groups.get(group_key, {}).get(name)
        else:
            # 在所有组中查找
            for group in self._tool_groups.values():
                if name in group:
                    return group[name]
            return None
    
    def get_tools_by_group(self, group_name: ToolGroup) -> List[BaseTool]:
        """获取指定组的所有工具
        
        Args:
            group_name: 工具组枚举
            
        Returns:
            工具实例列表
        """
        group_key = group_name.value
        return list(self._tool_groups.get(group_key, {}).values())
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有注册的工具
        
        Returns:
            工具实例列表
        """
        all_tools = []
        for group in self._tool_groups.values():
            all_tools.extend(group.values())
        return all_tools
    
    def get_all_groups(self) -> List[str]:
        """获取所有工具组名称
        
        Returns:
            工具组名称列表
        """
        return list(self._tool_groups.keys())
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的schema定义
        
        Returns:
            工具schema列表
        """
        schemas = []
        for group_name, group_tools in self._tool_groups.items():
            for tool in group_tools.values():
                schema = {
                    "name": tool.name,
                    "description": tool.description,
                    "group": group_name,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys())
                    }
                }
                schemas.append(schema)
        return schemas
    
    def get_schemas_by_group(self, group_name: ToolGroup) -> List[Dict[str, Any]]:
        """获取指定组的所有工具schema定义
        
        Args:
            group_name: 工具组枚举
            
        Returns:
            工具schema列表
        """
        schemas = []
        group_key = group_name.value
        group_tools = self._tool_groups.get(group_key, {})
        for tool in group_tools.values():
            # 获取工具的参数定义
            tool_params = tool.parameters
            properties = tool_params.get("properties", {})
            required = tool_params.get("required", [])
            
            schema = {
                "name": tool.name,
                "description": tool.description,
                "group": group_key,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            schemas.append(schema)
        return schemas
    
    async def execute_tool(self, name: str, parameters: Dict[str, Any], group_name: Optional[ToolGroup] = None) -> Any:
        """执行工具
        
        Args:
            name: 工具名称
            parameters: 工具参数
            group_name: 工具组枚举，如果为None则在所有组中查找
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 工具不存在
            Exception: 工具执行错误
        """
        tool = self.get_tool(name, group_name)
        if not tool:
            if group_name:
                raise ValueError(f"工具 '{name}' 在组 '{group_name.value}' 中不存在")
            else:
                raise ValueError(f"工具 '{name}' 不存在")
        
        try:
            return await tool.execute(**parameters)
        except Exception as e:
            raise

# 创建工具注册表实例
tool_registry = ToolRegistry()

# 注册business_trip工具组
try:
    from .business_trip_tools.invoice_processing_tool import InvoiceProcessingTool
    from .business_trip_tools.expense_record_management_tool import ExpenseRecordManagementTool
    from .business_trip_tools.reimbursement_management_tool import ReimbursementManagementTool
    from .business_trip_tools.reimbursement_submission_tool import ReimbursementSubmissionTool
    from .business_trip_tools.status_query_tool import StatusQueryTool
    from .business_trip_tools.travel_application_query_tool import TravelApplicationQueryTool
    from .business_trip_tools.allowance_processing_tool import AllowanceProcessingTool
    
    # 批量注册business_trip工具组
    business_trip_tools = [
        InvoiceProcessingTool(),
        ExpenseRecordManagementTool(),
        ReimbursementManagementTool(),
        ReimbursementSubmissionTool(),
        StatusQueryTool(),
        TravelApplicationQueryTool(),
        AllowanceProcessingTool()
    ]
    
    tool_registry.register_tools_to_group(business_trip_tools, ToolGroup.BUSINESS_TRIP)
    
except Exception as e:
    print(f"注册business_trip工具组时出错: {e}")
    pass

# 注册business_trip_v2工具组
try:
    from .business_trip_tools_v2.invoice_upload_tools import (
        InvoiceUploadTool,
        GetDimensionDataTool,
        GetBusinessObjectTemplateTool,
        GetHistoryVersionFormatTool,
        GetUserCurrencyTool,
        GetInvoiceBusinessObjectTool,
        InvoiceVerificationTool,
        GetPendingInvoiceTool,
        GetExpenseTypeMappingTool
    )
    
    from .business_trip_tools_v2.expense_record_tools import (
        GetExpenseRecordTypeTool,
        GetExpenseTypeFieldRuleTool,
        GetControlStandardTool,
        AddInvoiceToExpenseRecordTool,
        ExpenseRecordRuleExecuteTool,
        ExpenseRecordStandardCheckTool,
        GetBillDefineListTool,
        CheckExpensePermissionTool,
        GenerateBillByExpenseIdTool
    )
    
    from .business_trip_tools_v2.reimbursement_bill_tools import (
        GetMyRectificationBillListTool,
        GetUnfinishedDebtBillTool,
        GetAreaFieldByBillDefineIdTool,
        GetBillDataAndTemplateTool,
        CollectExpenseRecordInfoTool,
        QueryTravelDaysTool,
        JudgeNCLandPermissionTool,
        DataFillTool,
        GetSettlementUnitInfoTool,
        GetExpenseProjectListTool,
        GetHaiNaYunContractListTool,
        IsShowXiaoWeiFieldTool,
        GetBankAccountInfoTool,
        JudgeCompanyInfoTool,
        GetDimensionListDataTool,
        JudgeUserIsNewTravelTool,
        QueryDimObjectValueListTool,
        QueryNewTravelPageInfoTool,
        GetReimburseNumByDimTool,
        QueryReimburseNumByTripOrderTool,
        DeleteRowTool,
        SaveBillDataTool,
        QueryUserListTool,
        BudgetOrgQueryTool,
        BudgetQueryTool
    )
    
    # 批量注册business_trip_v2工具组
    business_trip_v2_tools = [
        # 发票上传相关工具
        InvoiceUploadTool(),
        GetDimensionDataTool(),
        GetBusinessObjectTemplateTool(),
        GetHistoryVersionFormatTool(),
        GetUserCurrencyTool(),
        GetInvoiceBusinessObjectTool(),
        InvoiceVerificationTool(),
        GetPendingInvoiceTool(),
        GetExpenseTypeMappingTool(),
        
        # 支出记录相关工具
        GetExpenseRecordTypeTool(),
        GetExpenseTypeFieldRuleTool(),
        GetControlStandardTool(),
        AddInvoiceToExpenseRecordTool(),
        ExpenseRecordRuleExecuteTool(),
        ExpenseRecordStandardCheckTool(),
        GetBillDefineListTool(),
        CheckExpensePermissionTool(),
        GenerateBillByExpenseIdTool(),
        
        # 报销单相关工具
        GetMyRectificationBillListTool(),
        GetUnfinishedDebtBillTool(),
        GetAreaFieldByBillDefineIdTool(),
        GetBillDataAndTemplateTool(),
        CollectExpenseRecordInfoTool(),
        QueryTravelDaysTool(),
        JudgeNCLandPermissionTool(),
        DataFillTool(),
        GetSettlementUnitInfoTool(),
        GetExpenseProjectListTool(),
        GetHaiNaYunContractListTool(),
        IsShowXiaoWeiFieldTool(),
        GetBankAccountInfoTool(),
        JudgeCompanyInfoTool(),
        GetDimensionListDataTool(),
        JudgeUserIsNewTravelTool(),
        QueryDimObjectValueListTool(),
        QueryNewTravelPageInfoTool(),
        GetReimburseNumByDimTool(),
        QueryReimburseNumByTripOrderTool(),
        DeleteRowTool(),
        SaveBillDataTool(),
        QueryUserListTool(),
        BudgetOrgQueryTool(),
        BudgetQueryTool()
    ]
    
    tool_registry.register_tools_to_group(business_trip_v2_tools, ToolGroup.BUSINESS_TRIP_V2)
    
except Exception as e:
    print(f"注册business_trip_v2工具组时出错: {e}")
    pass 