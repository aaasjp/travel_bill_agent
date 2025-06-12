"""
工具基类，定义了工具的基本接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
import json
import uuid
import inspect
import time
from ..utils.logger import log_tool_activity

class BaseTool(ABC):
    """工具基类，所有工具需要继承此类"""
    
    def __init__(self):
        self._id = str(uuid.uuid4())
    
    @property
    def id(self) -> str:
        """获取工具唯一ID"""
        return self._id
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """工具参数定义"""
        pass
    
    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """实际执行工具操作，由子类实现"""
        pass
    
    async def execute(self, **kwargs) -> Any:
        """执行工具操作，添加日志记录功能
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        # 记录工具执行开始
        start_time = time.time()
        log_tool_activity(self.name, "执行开始", kwargs)
        
        try:
            # 执行工具操作
            result = await self._execute(**kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录工具执行成功
            log_tool_activity(
                self.name, 
                "执行成功", 
                {
                    "parameters": kwargs,
                    "execution_time": f"{execution_time:.4f}秒"
                }, 
                result
            )
            
            return result
        except Exception as e:
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录工具执行失败
            log_tool_activity(
                self.name, 
                "执行失败", 
                {
                    "parameters": kwargs,
                    "execution_time": f"{execution_time:.4f}秒",
                    "error": str(e)
                }
            )
            
            # 重新抛出异常
            raise
    
    def to_schema(self) -> Dict[str, Any]:
        """将工具转换为schema格式
        
        Returns:
            工具的schema表示
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def validate_parameters(self, **kwargs) -> None:
        """验证参数是否符合要求
        
        Args:
            **kwargs: 要验证的参数
            
        Raises:
            ValueError: 如果参数不符合要求
        """
        # 获取工具的参数定义
        required_params = []
        param_types = {}
        
        for param_name, param_def in self.parameters.get("properties", {}).items():
            if param_name in self.parameters.get("required", []):
                required_params.append(param_name)
            
            if "type" in param_def:
                param_types[param_name] = param_def["type"]
        
        # 检查必需参数
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"缺少必需参数: {param}")
        
        # 检查参数类型（简单检查）
        for param, value in kwargs.items():
            if param in param_types:
                expected_type = param_types[param]
                
                # 简单类型检查
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"参数 {param} 应为字符串类型")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"参数 {param} 应为数值类型")
                elif expected_type == "integer" and not isinstance(value, int):
                    raise ValueError(f"参数 {param} 应为整数类型")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"参数 {param} 应为布尔类型")
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"参数 {param} 应为数组类型")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"参数 {param} 应为对象类型")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON模式描述
        
        Returns:
            Dict[str, Any]: 描述工具的JSON模式
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": [k for k, v in self.parameters.items() 
                            if v.get("required", False)]
            }
        }
        
    def __str__(self) -> str:
        return f"{self.name}: {self.description}" 