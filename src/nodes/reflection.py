from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import time
import json

from ..states.state import State
from ..llm import get_llm

class ReflectionNode:
    """
    反思节点，用于评估执行结果并决定后续行动。
    
    这个节点会分析当前状态，评估任务完成度，决定是需要重新规划、继续执行还是结束流程。
    它提供了一种自我评估和校正的机制，使工作流能够更智能地处理复杂任务。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化反思节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        
        # 定义反思提示模板
        self.reflection_prompt = ChatPromptTemplate.from_template("""你是一个人工智能助手的反思组件。
请分析当前任务的执行情况，评估完成度，并决定下一步操作。

## 用户原始输入
{user_input}

## 当前意图理解
{intent}

## 执行计划
{plan}

## 执行日志
{execution_log}

## 当前结果
{current_results}

## 工具调用历史
{tool_call_history}

## 错误信息（如有）
{errors}

请反思当前执行情况，并返回以下JSON格式的评估结果：

```json
{{
    "success_aspects": ["方面1", "方面2"],  // 成功完成的方面
    "missing_aspects": ["方面3"],  // 未完成或需改进的方面
    "action": "replan|waiting_for_human|end",  // 下一步行动：重新规划、人工干预或结束
    "rationale": "反思理由说明",
    "summary_output": "对当前反思结果的总结性输出"
}}
```""")
        
        # 定义反思结果解析器
        self.parser = JsonOutputParser()
        
        # 构建反思链
        self.chain = self.reflection_prompt | self.llm | self.parser
    
    async def __call__(self, state: State) -> State:
        """执行反思操作
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 准备反思输入
            current_results = state.get("current_results")
            if current_results is None:
                results_for_reflection = "暂无执行结果"
            else:
                results_for_reflection = json.dumps(current_results, ensure_ascii=False, indent=2)
                
            inputs = {
                "user_input": state["user_input"],
                "intent": state.get("intent", {}),
                "plan": state.get("plan", []),
                "execution_log": state.get("execution_log", []),
                "current_results": results_for_reflection,
                "tool_call_history": json.dumps(state.get("completed_tools", []), ensure_ascii=False, indent=2),
                "errors": state.get("errors", [])
            }
            
            # 执行反思分析
            reflection_result = await self.chain.ainvoke(inputs)
            
            # 更新状态
            # 添加时间戳到reflection_result
            reflection_result["timestamp"] = str(state.get("updated_at", time.time()))
            state["reflection_result"] = reflection_result
            
            # 使用status存放action用于节点流转
            state["status"] = reflection_result.get("action", "end")
            
            return state
            
        except Exception as e:
            # 捕获所有异常并创建默认的反思结果
            error_message = str(e)
            
            # 记录错误
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "reflection",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            # 创建默认的反思结果
            action = "end"
            reflection_result = {
                "success_aspects": ["由于反思组件错误，无法详细分析成功部分"],
                "missing_aspects": ["由于反思组件错误，无法详细分析缺失部分"],
                "action": action,
                "rationale": f"反思分析失败: {error_message}，直接结束流程",
                "summary_output": f"反思分析失败: {error_message}，直接结束流程",
                "timestamp": str(state.get("updated_at", time.time()))
            }
            
            # 更新状态
            state["reflection_result"] = reflection_result
            state["status"] = reflection_result.get("action", "end")
            
            return state 