from typing import Dict, Any, List, Optional, Tuple
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import time
import uuid
from datetime import datetime

from ..states.state import State
from ..llm import get_llm
from ..tool.registry import tool_registry, ToolGroup
from ..memory.memory_store import MemoryStore
from .human_intervention import InterventionType, InterventionPriority, NotificationChannel

class DecisionNode:
    """
    决策节点，负责为计划中的每个步骤选择合适的工具并填写参数。
    
    根据任务计划、用户信息、记忆和对话历史，为每个步骤选择最合适的工具，
    并为工具填写所需的参数。同时验证参数是否满足要求，如果参数不足则请求人工干预。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化决策节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        self.tool_registry = tool_registry
        self.memory_store = MemoryStore()
        
        # 定义解析器
        self.parser = JsonOutputParser()
    
    def _get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的schema定义
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具的schema定义，如果不存在则返回None
        """
        # 在所有工具组中查找工具
        for group in ToolGroup:
            schemas = self.tool_registry.get_schemas_by_group(group)
            for schema in schemas:
                if schema["name"] == tool_name:
                    return schema
        return None
    
    def _validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """验证工具参数是否满足要求
        
        Args:
            tool_name: 工具名称
            parameters: 提供的参数
            
        Returns:
            (是否满足要求, 缺失的必需参数列表, 工具schema)
        """
        # 获取工具schema
        schema = self._get_tool_schema(tool_name)
        if not schema:
            return False, [f"工具 {tool_name} 不存在"], {}
        
        # 获取必需参数列表
        required_params = schema["parameters"].get("required", [])
        properties = schema["parameters"].get("properties", {})
        
        # 检查缺失的必需参数
        missing_params = []
        for param in required_params:
            if param not in parameters or parameters[param] is None or parameters[param] == "":
                missing_params.append(param)
        
        # 检查参数值是否为"未知"
        unknown_params = []
        for param, value in parameters.items():
            if value == "未知" and param in required_params:
                unknown_params.append(param)
        
        # 合并缺失和未知的参数
        all_missing = list(set(missing_params + unknown_params))
        
        return len(all_missing) == 0, all_missing, schema
    
    def _check_previous_results_for_parameters(self, state: State, missing_params: List[str]) -> Dict[str, Any]:
        """检查之前的执行结果是否包含需要的参数
        
        Args:
            state: 当前状态
            missing_params: 缺失的参数列表
            
        Returns:
            从之前结果中找到的参数
        """
        found_params = {}
        
        # 检查工具执行结果
        tool_results = state.get("tool_results", {})
        for tool_name, result in tool_results.items():
            if result.get("status") == "success":
                result_data = result.get("result", {})
                if isinstance(result_data, dict):
                    for param in missing_params:
                        if param in result_data and result_data[param] not in [None, "", "未知"]:
                            found_params[param] = result_data[param]
        
        return found_params
    
    def _create_intervention_request_for_parameters(self, state: State, step_info: Dict[str, Any], 
                                                   tool_info: Dict[str, Any], missing_params: List[str], 
                                                   schema: Dict[str, Any]) -> Dict[str, Any]:
        """为参数缺失创建人工干预请求
        
        Args:
            state: 当前状态
            step_info: 步骤信息
            tool_info: 工具信息
            missing_params: 缺失的参数列表
            schema: 工具schema
            
        Returns:
            人工干预请求对象
        """
        # 获取参数描述
        properties = schema["parameters"].get("properties", {})
        param_descriptions = {}
        for param in missing_params:
            if param in properties:
                param_descriptions[param] = properties[param].get("description", param)
            else:
                param_descriptions[param] = param
        
        # 创建干预请求对象
        intervention_request = {
            "intervention_id": str(uuid.uuid4()),
            "intervention_type": InterventionType.PARAMETER_PROVIDER,
            "intervention_priority": InterventionPriority.NORMAL,
            "request_source": "decision_node",  # 请求来源：决策节点
            "notification_channels": [NotificationChannel.SYSTEM],
            "timeout": 3600,  # 1小时
            "timestamp": time.time(),
            "status": "pending",
            "meta_data": {
                "task_id": state.get("task_id", "unknown"),
                "user_input": state.get("user_input", ""),
                "step_id": step_info.get("step_id", ""),
                "step_name": step_info.get("step_name", ""),
                "step_desc": step_info.get("step_desc", ""),
                "tool_name": tool_info.get("name", ""),
                "tool_description": schema.get("description", ""),
                "missing_parameters": missing_params,
                "parameter_descriptions": param_descriptions,
                "current_parameters": tool_info.get("parameters", {})
            }
        }
        
        return intervention_request
    
    def _get_decision_prompt(self) -> ChatPromptTemplate:
        """获取决策提示模板
        
        Returns:
            决策提示模板
        """
        return ChatPromptTemplate.from_template("""你是一个专业助手的决策组件。
你的任务是为计划中的每个步骤选择合适的工具，并为工具填写所需的参数。

## 用户输入
{user_input}

## 用户信息
{user_info}

## 用户记忆
{user_memories}

## 对话历史
{conversation_history}

## 意图分析
{intent}

## 任务计划
{plan}

## 可用工具列表
{available_tools}

## 任务说明
请仔细分析每个计划步骤，为每个步骤选择最合适的工具。每个步骤可能需要一个或多个工具来完成。
在填写工具参数时，请根据以下信息进行判断：
1. 用户输入中的具体信息
2. 用户基本信息（姓名、工号、部门等）
3. 用户的历史记忆和偏好
4. 对话历史中的相关信息
5. 意图分析结果

请返回JSON格式的结果：

```json
{{
    "step_tools": [
        {{
            "step_id": "步骤ID",
            "step_name": "步骤名称",
            "step_desc": "步骤描述",
            "tools": [
                {{
                    "name": "工具名称",
                    "parameters": {{
                        "参数1": "值1",
                        "参数2": "值2"
                    }},
                    "reasoning": "选择该工具的原因"
                }}
            ]
        }}
    ]
}}
```

注意：
1. 每个步骤可以包含一个或多个工具调用
2. 工具参数必须与工具定义中的参数名称和类型匹配
3. 如果找不到对应的参数值，设置为"未知"
4. 请根据用户信息、记忆和对话历史来推断参数值
5. 只能使用上面列出的可用工具
6. 为每个工具选择提供合理的推理说明
7. step_id、step_name、step_desc需要严格来自plan中的step_id、step_name、step_desc。""")
    
    def _get_available_tools_description(self) -> Tuple[str, List[Dict[str, Any]]]:
        """获取可用工具的描述
        
        Returns:
            工具描述字符串和工具模式列表
        """
        # 获取所有工具模式
        tool_schemas = self.tool_registry.get_schemas_by_group(ToolGroup.BUSINESS_TRIP_V2)
        
        # 格式化工具描述
        tools_description = ""
        for idx, tool in enumerate(tool_schemas):
            tool_desc = f"{idx+1}. {tool['name']}\n"
            tool_desc += f"   描述: {tool['description']}\n"
            tool_desc += f"   参数: {json.dumps(tool['parameters']['properties'], ensure_ascii=False, indent=2)}\n"
            tools_description += tool_desc + "\n"
        
        return tools_description, tool_schemas
    
    def _format_user_memories(self, state: State) -> str:
        """格式化用户记忆信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的记忆信息字符串
        """
        try:
            # 获取用户记忆
            memory_records = state.get("memory_records", [])
            if not memory_records:
                return "无相关记忆信息"
            
            # 格式化记忆信息
            memories_text = "用户记忆信息：\n"
            for i, memory in enumerate(memory_records[:5]):  # 限制显示前5条记忆
                memories_text += f"{i+1}. {memory.get('name', '未命名')}: {memory.get('content', '无内容')}\n"
            
            return memories_text
        except Exception as e:
            return f"记忆信息格式化出错: {str(e)}"
    
    def _format_conversation_history(self, state: State) -> str:
        """格式化对话历史
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的对话历史字符串
        """
        try:
            messages = state.get("messages", [])
            if not messages:
                return "无对话历史"
            
            # 格式化对话历史
            history_text = "对话历史：\n"
            for i, message in enumerate(messages[-10:]):  # 显示最近10条消息
                role = message.get("role", "unknown")
                content = message.get("content", "")
                history_text += f"{role}: {content}\n"
            
            return history_text
        except Exception as e:
            return f"对话历史格式化出错: {str(e)}"
    
    def _format_user_info(self, state: State) -> str:
        """格式化用户信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的用户信息字符串
        """
        try:
            user_info = state.get("user_info", {})
            if not user_info:
                return "无用户信息"
            
            # 格式化用户信息
            info_text = "用户信息：\n"
            for key, value in user_info.items():
                info_text += f"{key}: {value}\n"
            
            return info_text
        except Exception as e:
            return f"用户信息格式化出错: {str(e)}"
    
    async def __call__(self, state: State) -> State:
        """执行决策操作
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 设置created_at时间戳（如果不存在）
            if "created_at" not in state:
                state["created_at"] = datetime.now()
            
            plan = state.get("plan", [])
            
            # 检查是否有计划可执行
            if not plan:
                return state
            
            # 准备决策所需的上下文
            tools_description, _ = self._get_available_tools_description()
            user_memories = self._format_user_memories(state)
            conversation_history = self._format_conversation_history(state)
            user_info = self._format_user_info(state)
            
            # 获取决策提示模板并构建决策链
            decision_prompt = self._get_decision_prompt()
            chain = decision_prompt | self.llm | self.parser
            
            # 执行决策
            decision_result = await chain.ainvoke({
                "user_input": state.get("user_input", ""),
                "user_info": user_info,
                "user_memories": user_memories,
                "conversation_history": conversation_history,
                "intent": json.dumps(state.get("intent", {}), ensure_ascii=False, indent=2),
                "plan": json.dumps(plan, ensure_ascii=False, indent=2),
                "available_tools": tools_description
            })
            
            # 处理决策结果
            step_tools = decision_result.get("step_tools", [])
            
            # 将步骤工具信息存储到状态中（提前设置，确保人工干预时可用）
            state["step_tools"] = step_tools
            
            # 初始化参数验证结果
            if "parameter_validation_results" not in state:
                state["parameter_validation_results"] = {}
            
            # 初始化待执行的工具列表
            if "pending_tools" not in state:
                state["pending_tools"] = []
            
            # 初始化已完成参数验证的工具列表
            if "validated_tools" not in state:
                state["validated_tools"] = []
            
            # 处理每个步骤中的工具，进行参数验证
            for step in step_tools:
                step_id = step.get("step_id", "")
                step_name = step.get("step_name", "")
                step_desc = step.get("step_desc", "")
                tools = step.get("tools", [])
                
                for tool_info in tools:
                    tool_name = tool_info.get("name", "")
                    parameters = tool_info.get("parameters", {})
                    reasoning = tool_info.get("reasoning", "")
                    
                    if not tool_name:
                        continue
                    
                    # 验证工具参数
                    is_valid, missing_params, schema = self._validate_tool_parameters(tool_name, parameters)
                    
                    # 记录验证结果
                    validation_key = f"{step_id}_{tool_name}"
                    state["parameter_validation_results"][validation_key] = {
                        "step_id": step_id,
                        "step_name": step_name,
                        "step_desc": step_desc,
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "reasoning": reasoning,
                        "is_valid": is_valid,
                        "missing_params": missing_params,
                        "schema": schema,
                        "timestamp": time.time()
                    }
                    
                    if is_valid:
                        # 参数满足要求，添加到待执行列表
                        state["pending_tools"].append({
                            "step_id": step_id,
                            "step_name": step_name,
                            "step_desc": step_desc,
                            "tool_name": tool_name,
                            "parameters": parameters,
                            "reasoning": reasoning
                        })
                        state["validated_tools"].append(validation_key)
                    else:
                        # 参数不满足要求，检查之前的执行结果
                        found_params = self._check_previous_results_for_parameters(state, missing_params)
                        
                        if found_params:
                            # 找到了部分参数，更新参数并重新验证
                            updated_parameters = {**parameters, **found_params}
                            tool_info["parameters"] = updated_parameters
                            
                            # 重新验证
                            is_valid_updated, missing_params_updated, _ = self._validate_tool_parameters(tool_name, updated_parameters)
                            
                            if is_valid_updated:
                                # 更新后参数满足要求
                                state["parameter_validation_results"][validation_key]["parameters"] = updated_parameters
                                state["parameter_validation_results"][validation_key]["is_valid"] = True
                                state["parameter_validation_results"][validation_key]["missing_params"] = []
                                state["parameter_validation_results"][validation_key]["found_params"] = found_params
                                
                                state["pending_tools"].append({
                                    "step_id": step_id,
                                    "step_name": step_name,
                                    "step_desc": step_desc,
                                    "tool_name": tool_name,
                                    "parameters": updated_parameters,
                                    "reasoning": reasoning
                                })
                                state["validated_tools"].append(validation_key)
                            else:
                                # 更新后仍有缺失参数，需要人工干预
                                missing_params = missing_params_updated
                                state["parameter_validation_results"][validation_key]["missing_params"] = missing_params
                                state["parameter_validation_results"][validation_key]["found_params"] = found_params
                        else:
                            # 没有找到参数，需要人工干预
                            pass
                        
                        # 如果仍有缺失参数，创建人工干预请求
                        if missing_params:
                            intervention_request = self._create_intervention_request_for_parameters(
                                state, step, tool_info, missing_params, schema
                            )
                            
                            # 初始化干预请求列表（如果不存在）
                            if "intervention_request" not in state:
                                state["intervention_request"] = []
                            
                            # 添加新的干预请求到列表
                            state["intervention_request"].append(intervention_request)
                            
                            # 设置状态为等待人工干预
                            state["status"] = "waiting_for_human"
                            
                            # 更新时间戳
                            state["updated_at"] = datetime.now()
                            
                            return state
            
            # 如果没有需要人工干预的情况，设置状态为可以执行工具
            if state.get("status") != "waiting_for_human":
                state["status"] = "ready_for_execution"
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"决策节点执行失败: {str(e)}")
            
            # 记录错误到状态中
            if "errors" not in state:
                state["errors"] = []
            
            state["errors"].append({
                "node": "decision",
                "error": str(e),
                "error_type": "decision_error",
                "timestamp": str(time.time())
            })
            
            # 统一的异常处理：设置默认的决策结果
            # 如果决策失败，并且没有step_tools，则设置为空数组
            if not state.get("step_tools", []):
                state["step_tools"] = []
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
                            
            return state
    
