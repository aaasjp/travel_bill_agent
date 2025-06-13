from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
import json
import re
import time

from ..models.state import ExpenseState
from config.config import MODEL_NAME, MODEL_BASE_URL, API_KEY
from ..prompts.process_prompt import prompt as business_process_prompt
from ..prompts.vector_store_prompt import prompt as knowledge_prompt
from ..prompts.memory_prompt import prompt as record_history_prompt
from ..tool.registry import tool_registry
from ..utils.logger import log_node_activity, log_error, log_node_entry, log_node_exit

class TaskPlanningNode:
    """任务规划节点，负责制定处理流程的计划"""
    
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = ChatOpenAI(model_name=model_name,base_url=MODEL_BASE_URL,api_key=API_KEY)
        self.tool_registry = tool_registry
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销规划助手。参考报销流程说明，基于用户的意图和上下文，请生成针对此用户报销的详细的执行计划。
            
            【报销流程说明】:
            {business_process_prompt}
             
             【报销政策说明】:
             {knowledge_prompt}  

             【用户历史记录】:
             {record_history_prompt}    
            
             【可用工具列表】:
             {available_tools}
            
            要求：
            1. 根据报销流程说明，生成针对此用户报销的详细的执行计划。
            2. 如果用户已经提交过出差申请，执行计划不需要包含出差申请的步骤。
            3. 如果用户已经上传过火车票，执行计划不需要包含火车票的步骤。
            4. 如果用户已经上传过机票，执行计划不需要包含机票的步骤。
            5. 如果用户已经上传过住宿发票，执行计划不需要包含住宿发票的步骤。
            6. 如果用户已经上传过餐饮发票，执行计划不需要包含餐饮发票的步骤。
            7. 如果用户已经上传过其他发票，执行计划不需要包含其他发票的步骤。
            8. 为每个步骤分配适当的工具，只能使用上述可用工具列表中的工具。

            
            请以JSON格式输出，包含以下字段：
            - steps: 执行步骤列表，每个步骤包含步骤描述和需要执行的操作
            - tools_needed: 每个步骤需要的工具，格式为 {{"步骤索引": {{"tool_name": "工具名称", "parameters": "参数描述"}}}}
            - dependencies: 步骤间的依赖关系
            - estimated_time: 预计完成时间
            """),
            ("user", "意图: {intent}\n上下文: {context}")
        ])
    
    def extract_json_from_response(self, text):
        """从响应中提取JSON部分"""
        # 尝试找到JSON块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, text)
        
        if json_match:
            # 找到了JSON块
            return json_match.group(1).strip()
        
        # 如果没有找到JSON块，尝试直接解析为JSON
        # 移除<think>标签块
        text = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()
        
        # 尝试找到完整的JSON对象
        try:
            # 查找可能的JSON开始位置
            start_pos = text.find('{')
            if start_pos >= 0:
                # 尝试逐字符解析，找到有效的JSON
                for end_pos in range(len(text), start_pos, -1):
                    try:
                        json_candidate = text[start_pos:end_pos]
                        # 尝试解析
                        json.loads(json_candidate)
                        # 如果成功解析，返回这个JSON字符串
                        return json_candidate
                    except json.JSONDecodeError:
                        # 解析失败，继续尝试
                        continue
        except Exception:
            # 发生其他异常，忽略并继续
            pass
            
        # 如果上述方法都失败，使用正则表达式查找JSON对象
        # 这个更宽松的模式可能会找到不完整的JSON
        json_pattern = r'({[\s\S]*?})'
        json_match = re.search(json_pattern, text)
        
        if json_match:
            return json_match.group(1).strip()
            
        # 最后尝试查找任何花括号包围的内容
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < end:
                return text[start:end]
        
        # 如果都失败了，返回一个有效的空JSON对象
        return '{}'
    
    def _get_available_tools_description(self) -> str:
        """获取可用工具的描述
        
        Returns:
            工具描述字符串
        """
        # 获取所有工具模式
        tool_schemas = self.tool_registry.get_all_schemas()
        
        # 格式化工具描述
        tools_description = ""
        for idx, tool in enumerate(tool_schemas):
            tool_desc = f"{idx+1}. {tool['name']}\n"
            tool_desc += f"   描述: {tool['description']}\n"
            tool_desc += f"   参数: {json.dumps(tool['parameters']['properties'], ensure_ascii=False, indent=2)}\n"
            tools_description += tool_desc + "\n"
        
        return tools_description
    
    def _add_log_entry(self, state: ExpenseState, action: str, details: Dict[str, Any]) -> None:
        """添加日志条目
        
        Args:
            state: 当前状态
            action: 执行的动作
            details: 详细信息
        """
        if "execution_log" not in state:
            state["execution_log"] = []
        
        # 获取当前时间戳
        timestamp = str(state["updated_at"])
        
        # 创建日志条目
        log_entry = {
            "node": "task_planning",
            "action": action,
            "timestamp": timestamp,
            "details": details
        }
        
        # 添加日志到状态
        state["execution_log"].append(log_entry)
        
        # 同时记录到文件日志
        log_node_activity("task_planning", action, details)
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行任务规划
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        # 记录节点开始执行
        state_id = state.get("id", "unknown")
        start_time = time.time()
        log_node_entry("task_planning", state_id, {
            "user_input": state.get("user_input", ""),
            "intent": state.get("intent", {}),
            "context_keys": list(state.get("context", {}).keys())
        })
        
        try:
            # 获取可用工具描述
            tools_description = self._get_available_tools_description()
            
            # 记录工具信息
            self._add_log_entry(
                state,
                "获取可用工具",
                {
                    "tools_count": len(self.tool_registry.get_all_schemas()),
                    "tools": [tool["name"] for tool in self.tool_registry.get_all_schemas()]
                }
            )
            
            # 准备输入
            inputs = {
                "intent": state["intent"],
                "context": state.get("context", {}),
                "business_process_prompt": business_process_prompt,
                "knowledge_prompt": knowledge_prompt,
                "record_history_prompt": record_history_prompt,
                "available_tools": tools_description
            }
            
            # 记录开始规划
            self._add_log_entry(
                state,
                "开始任务规划",
                {"message": "根据用户意图和上下文开始规划任务"}
            )
            
            # 记录模型调用开始
            llm_call_start_time = time.time()
            self._add_log_entry(
                state,
                "调用大模型",
                {
                    "model": MODEL_NAME,
                    "input_intent_length": len(json.dumps(state["intent"], ensure_ascii=False)),
                    "input_context_length": len(json.dumps(state.get("context", {}), ensure_ascii=False))
                }
            )
            
            # 执行规划
            response = await self.model.ainvoke(self.prompt.format_messages(**inputs))
            response_text = response.content

            print(f"response_text: {response_text}")
            
            # 计算模型调用执行时间
            llm_execution_time = time.time() - llm_call_start_time

            # 记录LLM响应
            self._add_log_entry(
                state,
                "大模型规划完成",
                {
                    "response_length": len(response_text),
                    "execution_time": f"{llm_execution_time:.4f}秒"
                }
            )
            
            # 提取并解析 JSON
            json_str = self.extract_json_from_response(response_text)
            
            # 记录JSON提取
            self._add_log_entry(
                state,
                "提取JSON",
                {
                    "extracted_json_length": len(json_str)
                }
            )
            
            # 解析JSON
            try:
                planning_result = json.loads(json_str)
                
                # 记录解析成功
                self._add_log_entry(
                    state,
                    "解析规划结果",
                    {
                        "steps_count": len(planning_result.get("steps", [])),
                        "has_tools": "tools_needed" in planning_result,
                        "tools_needed_count": len(planning_result.get("tools_needed", {}))
                    }
                )
            except json.JSONDecodeError as e:
                # 记录解析失败的更详细信息
                error_msg = str(e)
                log_error("task_planning", f"解析JSON失败: {error_msg}", {
                    "json_str": json_str,
                    "json_length": len(json_str),
                    "error_position": str(e.pos) if hasattr(e, 'pos') else "未知",
                    "error_line": str(e.lineno) if hasattr(e, 'lineno') else "未知",
                    "error_column": str(e.colno) if hasattr(e, 'colno') else "未知"
                })
                
                # 尝试保存原始响应进行调试
                try:
                    with open('debug_response.txt', 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    with open('debug_json.txt', 'w', encoding='utf-8') as f:
                        f.write(json_str)
                    log_error("task_planning", "已保存调试信息到文件", {
                        "response_file": "debug_response.txt",
                        "json_file": "debug_json.txt"
                    })
                except Exception as file_error:
                    log_error("task_planning", f"保存调试文件失败: {str(file_error)}", {})
                
                # 如果解析失败，创建默认结果
                planning_result = {
                    "steps": [],
                    "tools_needed": {},
                    "dependencies": {},
                    "estimated_time": "未知"
                }
                
                # 记录使用默认结果
                self._add_log_entry(
                    state,
                    "使用默认规划结果",
                    {"error": error_msg}
                )
            
            # 更新计划
            state["plan"] = planning_result.get("steps", [])
            
            # 保存工具需求到每个步骤
            tools_needed = planning_result.get("tools_needed", {})
            
            # 确保每个步骤都包含工具信息
            for i, step in enumerate(state["plan"]):
                step_idx = str(i)
                if step_idx in tools_needed:
                    # 添加工具信息到步骤
                    if isinstance(step, dict):
                        step["tool"] = tools_needed[step_idx]
                    else:
                        # 如果步骤只是字符串，将其转换为字典
                        state["plan"][i] = {
                            "description": step,
                            "tool": tools_needed[step_idx]
                        }
            
            # 设置是否需要检索
            state["need_retrieval"] = planning_result.get("needs_retrieval", False)
            
            # 如果需要检索，添加到上下文
            if state["need_retrieval"] and "context" in state:
                state["context"]["retrieval_reason"] = planning_result.get("retrieval_reason", "")
            
            # 保存规划结果到状态
            state["planning_result"] = planning_result
            
            # 记录规划日志
            self._add_log_entry(
                state,
                "制定任务计划完成",
                {
                    "plan_steps": len(state["plan"]),
                    "needs_retrieval": state.get("need_retrieval", False),
                    "has_tools_info": bool(tools_needed)
                }
            )
            
            # 记录节点执行完成
            execution_time = time.time() - start_time
            log_node_exit("task_planning", state_id, execution_time, {
                "status": "completed",
                "steps_count": len(state["plan"]),
                "tools_needed_count": len(tools_needed),
                "needs_retrieval": state.get("need_retrieval", False),
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            return state
            
        except Exception as e:
            # 记录错误
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "task_planning",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            # 记录错误日志
            log_error("task_planning", "规划过程中发生未捕获的异常", {"error": error_message})
            
            # 记录节点执行完成（错误）
            execution_time = time.time() - start_time
            log_node_exit("task_planning", state_id, execution_time, {
                "status": "error",
                "error": error_message,
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            # 出错时设置空计划
            state["plan"] = []
            return state 