from typing import Dict, Any, List, Optional, Tuple
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import time

from ..states.state import State
from ..llm import get_llm
from ..tool.registry import tool_registry

class DecisionNode:
    """
    执行节点，负责执行任务计划中的具体步骤。
    
    根据任务计划，执行当前步骤，更新状态，并决定是否需要调用工具。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化执行节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        self.tool_registry = tool_registry
        
        # 定义执行提示模板
        self.decision_prompt = ChatPromptTemplate.from_template("""你是一个专业的差旅报销助手的执行组件。
根据当前的任务计划和状态，你需要执行当前步骤。

## 用户输入
{user_input}

## 意图分析
{intent}

## 任务计划
{plan}

## 当前执行步骤: {current_step}

## 当前步骤详情
{current_step_details}

## 上下文信息
{context}

## 执行日志
{execution_log}

## 已执行的行动
{action_taken}

## 可用工具列表
{available_tools}

请执行当前步骤，并返回JSON格式的结果：

```json
{{
    "action_taken": "执行的具体操作",
    "result": "操作结果或生成的内容",
    "requires_tool": true/false,
    "tool_calls": [
        {{
            "name": "工具名称",
            "parameters": {{"参数1": "值1", "参数2": "值2"}}
        }}
    ],
    "next_step": 2,  // 下一步骤编号，如果是最后一步则为-1
    "is_complete": true/false,  // 整个任务是否完成
    "final_output": "如果任务完成，提供最终输出内容"
}}
```

注意：
1. 如果需要调用工具，设置 requires_tool 为 true，并在 tool_calls 中指定工具名称和参数。
2. 如果是最后一步或任务已完成，设置 is_complete 为 true。
3. 如果不需要调用工具，直接执行操作并返回结果。
4. 只能使用上面列出的可用工具，不要尝试调用不存在的工具。
5. 工具调用时，确保参数名称和类型与工具定义匹配。
6. 请尽可能使用任务规划中为当前步骤推荐的工具，这样能更好地完成任务。""")
        
        # 定义解析器
        self.parser = JsonOutputParser()
        
        # 构建执行链
        self.chain = self.decision_prompt | self.llm | self.parser
    
    def _get_available_tools_description(self) -> Tuple[str, List[Dict[str, Any]]]:
        """获取可用工具的描述
        
        Returns:
            工具描述字符串和工具模式列表
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
        
        return tools_description, tool_schemas
    
    async def __call__(self, state: State) -> State:
        """执行当前步骤
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 获取当前步骤
            current_step = state.get("current_step", 0)
            plan = state.get("plan", [])
            
            # 检查是否还有步骤可执行
            if not plan or current_step >= len(plan):
                return state
            
            # 获取当前步骤详情
            current_step_details = plan[current_step]
            
            # 检查步骤中是否包含推荐工具信息
            step_tool_info = None
            if isinstance(current_step_details, dict) and "tool" in current_step_details:
                step_tool_info = current_step_details.get("tool")
            
            # 准备执行当前步骤所需的上下文
            tools_description, _ = self._get_available_tools_description()
            
            # 准备执行上下文
            context = state.get("context", {})
            context_description = json.dumps(context, ensure_ascii=False, indent=2)
            
            # 准备执行日志
            execution_log = state.get("execution_log", [])
            if len(execution_log) > 5:
                execution_log = execution_log[-5:]  # 只保留最近的5条日志
            execution_log_description = json.dumps(execution_log, ensure_ascii=False, indent=2)
            
            # 准备已执行的行动
            action_taken = state.get("action_taken", [])
            if len(action_taken) > 3:
                action_taken = action_taken[-3:]  # 只保留最近的3条行动
            action_taken_description = json.dumps(action_taken, ensure_ascii=False, indent=2)
            
            # 执行当前步骤
            try:
                execution_result = await self.chain.ainvoke({
                    "user_input": state.get("user_input", ""),
                    "intent": json.dumps(state.get("intent", {}), ensure_ascii=False, indent=2),
                    "plan": json.dumps(plan, ensure_ascii=False, indent=2),
                    "current_step": current_step + 1,  # 1-indexed for human readability
                    "current_step_details": json.dumps(current_step_details, ensure_ascii=False, indent=2),
                    "context": context_description,
                    "execution_log": execution_log_description,
                    "action_taken": action_taken_description,
                    "available_tools": tools_description
                })
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                # 创建基本的执行结果
                execution_result = {
                    "action_taken": f"执行步骤 {current_step+1} 时出错: {str(e)}",
                    "result": f"执行出错: {str(e)}",
                    "requires_tool": False,
                    "tool_calls": [],
                    "next_step": current_step + 1,  # 保持在当前步骤
                    "is_complete": False
                }
            
            # 更新状态
            if "action_taken" not in state:
                state["action_taken"] = []
                
            # 添加当前步骤的执行结果
            state["action_taken"].append({
                "step": current_step + 1,
                "action": execution_result.get("action_taken", "未指定动作"),
                "result": execution_result.get("result", "未返回结果")
            })
            
            # 判断是否需要工具调用
            requires_tool = execution_result.get("requires_tool", False)
            if requires_tool:
                tool_calls = execution_result.get("tool_calls", [])
                state["tool_calls"] = tool_calls
            else:
                state["tool_calls"] = []
            
            # 根据执行结果更新下一步
            next_step = execution_result.get("next_step", current_step + 1)
            if next_step == -1:  # 表示任务完成
                state["is_complete"] = True
                if "final_output" in execution_result:
                    state["final_output"] = execution_result["final_output"]
            else:
                state["current_step"] = next_step
            
            # 检查是否完成
            is_complete = execution_result.get("is_complete", False)
            if is_complete:
                state["is_complete"] = True
                if "final_output" in execution_result:
                    state["final_output"] = execution_result["final_output"]
            
            return state
            
        except Exception as e:
            # 记录未捕获的异常
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "decision",
                "error": str(e),
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            return state 