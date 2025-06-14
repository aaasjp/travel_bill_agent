"""
工具注册表模块
管理和执行工具
"""
from typing import Dict, Any, List, Optional
import time

# 导入基类
from .base import BaseTool

class ToolRegistry:
    """工具注册表，管理所有工具并与LangGraph集成"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool_instance: BaseTool) -> None:
        """注册工具
        
        Args:
            tool_instance: 工具实例
        """
        if not tool_instance.name:
            raise ValueError("工具必须有名称")
        
        self._tools[tool_instance.name] = tool_instance
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回None
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有注册的工具
        
        Returns:
            工具实例列表
        """
        return list(self._tools.values())
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的schema定义
        
        Returns:
            工具schema列表
        """
        schemas = []
        for tool in self._tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": list(tool.parameters.keys())
                }
            }
            schemas.append(schema)
        return schemas
    
    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            name: 工具名称
            parameters: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 工具不存在
            Exception: 工具执行错误
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 不存在")
        
        try:
            return await tool.execute(**parameters)
        except Exception as e:
            raise

# 创建工具注册表实例
tool_registry = ToolRegistry()

# 只注册新的工具
try:
    from .invoice_processing_tool import InvoiceProcessingTool
    tool_registry.register_tool(InvoiceProcessingTool())
except Exception:
    pass

try:
    from .expense_record_management_tool import ExpenseRecordManagementTool
    tool_registry.register_tool(ExpenseRecordManagementTool())
except Exception:
    pass

try:
    from .reimbursement_management_tool import ReimbursementManagementTool
    tool_registry.register_tool(ReimbursementManagementTool())
except Exception:
    pass

try:
    from .reimbursement_submission_tool import ReimbursementSubmissionTool
    tool_registry.register_tool(ReimbursementSubmissionTool())
except Exception:
    pass

try:
    from .status_query_tool import StatusQueryTool
    tool_registry.register_tool(StatusQueryTool())
except Exception:
    pass

try:
    from .travel_application_query_tool import TravelApplicationQueryTool
    tool_registry.register_tool(TravelApplicationQueryTool())
except Exception:
    pass

try:
    from .allowance_processing_tool import AllowanceProcessingTool
    tool_registry.register_tool(AllowanceProcessingTool())
except Exception:
    pass 