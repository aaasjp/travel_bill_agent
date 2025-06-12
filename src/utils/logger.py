"""
日志工具模块
管理和配置应用程序的日志记录
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 配置日志文件路径
APP_LOG_FILE = LOG_DIR / "app.log"
TOOL_LOG_FILE = LOG_DIR / "tool.log"
NODE_LOG_FILE = LOG_DIR / "node.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
WORKFLOW_LOG_FILE = LOG_DIR / "workflow.log"
DETAILED_TOOL_LOG_FILE = LOG_DIR / "detailed_tool.log"
DETAILED_NODE_LOG_FILE = LOG_DIR / "detailed_node.log"

# 配置日志级别
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 配置日志滚动
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 10

# 设置格式化器
formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

# 主应用日志记录器
app_logger = logging.getLogger("app")
app_logger.setLevel(LOG_LEVEL)

# 工具日志记录器
tool_logger = logging.getLogger("tool")
tool_logger.setLevel(LOG_LEVEL)

# 节点日志记录器
node_logger = logging.getLogger("node")
node_logger.setLevel(LOG_LEVEL)

# 错误日志记录器
error_logger = logging.getLogger("error")
error_logger.setLevel(logging.ERROR)

# 工作流日志记录器
workflow_logger = logging.getLogger("workflow")
workflow_logger.setLevel(LOG_LEVEL)

# 详细工具日志记录器
detailed_tool_logger = logging.getLogger("detailed_tool")
detailed_tool_logger.setLevel(LOG_LEVEL)

# 详细节点日志记录器
detailed_node_logger = logging.getLogger("detailed_node")
detailed_node_logger.setLevel(LOG_LEVEL)

# 配置处理器
def setup_handler(log_file: Path, logger: logging.Logger):
    """为日志记录器设置文件处理器"""
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # 防止重复日志
    logger.propagate = False

# 设置各个日志记录器的处理器
setup_handler(APP_LOG_FILE, app_logger)
setup_handler(TOOL_LOG_FILE, tool_logger)
setup_handler(NODE_LOG_FILE, node_logger)
setup_handler(ERROR_LOG_FILE, error_logger)
setup_handler(WORKFLOW_LOG_FILE, workflow_logger)
setup_handler(DETAILED_TOOL_LOG_FILE, detailed_tool_logger)
setup_handler(DETAILED_NODE_LOG_FILE, detailed_node_logger)

# 添加控制台处理器（仅用于错误日志）
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.ERROR)
error_logger.addHandler(console_handler)

def _format_json(obj: Any) -> str:
    """格式化对象为JSON字符串
    
    Args:
        obj: 要格式化的对象
        
    Returns:
        格式化后的JSON字符串
    """
    try:
        if obj is None:
            return "null"
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"<无法序列化的对象: {str(e)}>"

def log_node_activity(node_name: str, action: str, details: Optional[Dict[str, Any]] = None):
    """记录节点活动
    
    Args:
        node_name: 节点名称
        action: 动作
        details: 详细信息
    """
    # 基础日志记录
    node_logger.info(f"{node_name} - {action} - {details or {}}")
    
    # 详细日志记录
    timestamp = datetime.now().strftime(LOG_DATE_FORMAT)
    log_entry = {
        "timestamp": timestamp,
        "node": node_name,
        "action": action,
        "details": details or {}
    }
    detailed_node_logger.info(_format_json(log_entry))

def log_node_entry(node_name: str, state_id: str, input_data: Optional[Dict[str, Any]] = None):
    """记录节点开始执行
    
    Args:
        node_name: 节点名称
        state_id: 状态ID
        input_data: 输入数据
    """
    timestamp = datetime.now().strftime(LOG_DATE_FORMAT)
    log_entry = {
        "timestamp": timestamp,
        "node": node_name,
        "action": "节点开始执行",
        "state_id": state_id,
        "input_data": input_data or {}
    }
    detailed_node_logger.info(_format_json(log_entry))

def log_node_exit(node_name: str, state_id: str, execution_time: float, output_data: Optional[Dict[str, Any]] = None):
    """记录节点执行完成
    
    Args:
        node_name: 节点名称
        state_id: 状态ID
        execution_time: 执行时间（秒）
        output_data: 输出数据
    """
    timestamp = datetime.now().strftime(LOG_DATE_FORMAT)
    log_entry = {
        "timestamp": timestamp,
        "node": node_name,
        "action": "节点执行完成",
        "state_id": state_id,
        "execution_time": f"{execution_time:.4f}秒",
        "output_data": output_data or {}
    }
    detailed_node_logger.info(_format_json(log_entry))

def log_tool_activity(tool_name: str, action: str, parameters: Optional[Dict[str, Any]] = None, result: Any = None):
    """记录工具活动
    
    Args:
        tool_name: 工具名称
        action: 动作
        parameters: 参数
        result: 结果
    """
    # 基础日志记录
    tool_logger.info(f"{tool_name} - {action} - 参数: {parameters or {}} - 结果: {result}")
    
    # 详细日志记录
    timestamp = datetime.now().strftime(LOG_DATE_FORMAT)
    log_entry = {
        "timestamp": timestamp,
        "tool": tool_name,
        "action": action,
        "parameters": parameters or {},
        "result": result
    }
    detailed_tool_logger.info(_format_json(log_entry))

def log_tool_execution(tool_name: str, parameters: Dict[str, Any], execution_time: float, success: bool, result: Any = None, error: Optional[str] = None):
    """记录工具执行详细信息
    
    Args:
        tool_name: 工具名称
        parameters: 参数
        execution_time: 执行时间（秒）
        success: 是否成功
        result: 结果（如果成功）
        error: 错误信息（如果失败）
    """
    timestamp = datetime.now().strftime(LOG_DATE_FORMAT)
    log_entry = {
        "timestamp": timestamp,
        "tool": tool_name,
        "action": "执行",
        "parameters": parameters,
        "execution_time": f"{execution_time:.4f}秒",
        "success": success,
        "result": result if success else None,
        "error": error if not success else None
    }
    detailed_tool_logger.info(_format_json(log_entry))

def log_workflow_transition(from_state: str, to_state: str, reason: str):
    """记录工作流状态转换"""
    workflow_logger.info(f"状态转换: {from_state} -> {to_state} - 原因: {reason}")

def log_error(source: str, error_message: str, details: Optional[Dict[str, Any]] = None):
    """记录错误"""
    # 获取堆栈信息
    stack_trace = traceback.format_exc()
    
    error_info = {
        "timestamp": datetime.now().strftime(LOG_DATE_FORMAT),
        "source": source,
        "message": error_message,
        "details": details or {},
        "stack_trace": stack_trace
    }
    
    # 记录基本错误信息
    error_logger.error(f"{source} - {error_message} - {details or {}}")
    
    # 记录详细错误信息
    error_logger.error(_format_json(error_info))

def log_app_info(message: str):
    """记录应用信息"""
    app_logger.info(message)

def log_app_debug(message: str):
    """记录应用调试信息"""
    app_logger.debug(message)

def get_loggers():
    """获取所有日志记录器"""
    return {
        "app": app_logger,
        "tool": tool_logger,
        "node": node_logger,
        "error": error_logger,
        "workflow": workflow_logger,
        "detailed_tool": detailed_tool_logger,
        "detailed_node": detailed_node_logger
    } 