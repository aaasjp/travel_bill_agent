"""
工具注册表模块
管理和执行工具
"""
from typing import Dict, Any, List, Optional
import time

# 导入自定义日志工具
from ..utils.logger import log_tool_activity, log_error, log_tool_execution

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
        log_tool_activity(
            tool_instance.name, 
            "注册", 
            {
                "description": tool_instance.description,
                "parameters": tool_instance.parameters,
                "timestamp": time.time()
            }
        )
    
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
            error_msg = f"工具 '{name}' 不存在"
            log_error("工具执行", error_msg, {"requested_tool": name, "available_tools": list(self._tools.keys())})
            raise ValueError(error_msg)
        
        # 记录执行开始时间
        start_time = time.time()
        
        try:
            # 记录开始执行
            log_tool_activity(name, "执行开始", parameters)
            
            # 执行工具
            result = await tool.execute(**parameters)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录详细执行信息
            log_tool_execution(
                name,
                parameters,
                execution_time,
                success=True,
                result=result
            )
            
            # 记录执行成功
            log_tool_activity(
                name, 
                "执行成功", 
                {
                    "parameters": parameters,
                    "execution_time": f"{execution_time:.4f}秒"
                }, 
                result
            )
            
            return result
        except Exception as e:
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录详细执行信息
            log_tool_execution(
                name,
                parameters,
                execution_time,
                success=False,
                error=str(e)
            )
            
            # 记录错误信息
            error_msg = f"执行工具 '{name}' 时出错: {str(e)}"
            log_error(
                "工具执行", 
                error_msg, 
                {
                    "tool": name, 
                    "parameters": parameters,
                    "execution_time": f"{execution_time:.4f}秒"
                }
            )
            
            raise

# 创建工具注册表实例
tool_registry = ToolRegistry()

# 只注册新的工具
try:
    from .invoice_processing_tool import InvoiceProcessingTool
    tool_registry.register_tool(InvoiceProcessingTool())
except Exception as e:
    log_error("工具注册", f"无法注册 InvoiceProcessingTool: {str(e)}")

try:
    from .expense_record_management_tool import ExpenseRecordManagementTool
    tool_registry.register_tool(ExpenseRecordManagementTool())
except Exception as e:
    log_error("工具注册", f"无法注册 ExpenseRecordManagementTool: {str(e)}")

try:
    from .reimbursement_management_tool import ReimbursementManagementTool
    tool_registry.register_tool(ReimbursementManagementTool())
except Exception as e:
    log_error("工具注册", f"无法注册 ReimbursementManagementTool: {str(e)}")

try:
    from .reimbursement_submission_tool import ReimbursementSubmissionTool
    tool_registry.register_tool(ReimbursementSubmissionTool())
except Exception as e:
    log_error("工具注册", f"无法注册 ReimbursementSubmissionTool: {str(e)}")

try:
    from .status_query_tool import StatusQueryTool
    tool_registry.register_tool(StatusQueryTool())
except Exception as e:
    log_error("工具注册", f"无法注册 StatusQueryTool: {str(e)}")

try:
    from .travel_application_query_tool import TravelApplicationQueryTool
    tool_registry.register_tool(TravelApplicationQueryTool())
except Exception as e:
    log_error("工具注册", f"无法注册 TravelApplicationQueryTool: {str(e)}")

try:
    from .allowance_processing_tool import AllowanceProcessingTool
    tool_registry.register_tool(AllowanceProcessingTool())
except Exception as e:
    log_error("工具注册", f"无法注册 AllowanceProcessingTool: {str(e)}") 