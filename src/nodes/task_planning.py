from typing import Dict, Any, List, Optional
import json
import time
import re
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..states.state import State
from ..config import get_llm
from ..tool.registry import tool_registry
from ..prompts.process_prompt import prompt as business_process_prompt
from ..prompts.vector_store_prompt import prompt as knowledge_prompt
from ..prompts.memory_prompt import prompt as record_history_prompt

class TaskPlanningNode:
    """任务规划节点，负责制定处理流程的计划"""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化任务规划节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        self.tool_registry = tool_registry
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的差旅报销规划助手。参考报销流程说明和报销政策及用户历史记录和可用工具，针对用户的意图，生成详细的执行计划。
            
            【报销流程说明】:
            {business_process_prompt}
             
            【报销政策说明】:
             {knowledge_prompt}  

            【用户历史记录】:
             {record_history_prompt}    
            
            【可用工具列表】:
             {available_tools}
            
            注意：
            1. step_id 必须按照 "step_1", "step_2" 等格式递增
            2. step_name 必须是简短的步骤名称，例如："提交出差申请"、"上传火车票"等
            3. action 必须是对步骤执行动作的详细描述，例如："使用出差申请工具提交申请"、"使用上传工具上传火车票"等
            4. tool.name 必须是可用工具列表中的工具名称
            5. tool.parameters 必须包含该工具所需的所有参数，参数值必须符合工具要求
            6. 不要添加任何额外的字段或注释
            7. 确保JSON格式完全正确，包括所有引号和逗号
            8. 每个步骤必须包含完整的工具信息
            9. 严格按照以下JSON格式输出，不要添加任何额外的字段或注释：

{{
  "plan": {{
    "steps": [
      {{
        "step_id": "step_1",
        "step_name": "步骤名称",
        "action": "执行动作描述",
        "tool": {{
          "name": "工具名称",
          "parameters": {{
            "参数名": "参数值"
          }}
        }}
      }}
    ]
  }}
}}
```"""),
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
    
    async def __call__(self, state: State) -> State:
        """执行任务规划
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 获取可用工具描述
            tools_description = self._get_available_tools_description()
            
            # 准备输入
            inputs = {
                "intent": state["intent"],
                "context": state.get("context", {}),
                "business_process_prompt": business_process_prompt,
                "knowledge_prompt": knowledge_prompt,
                "record_history_prompt": record_history_prompt,
                "available_tools": tools_description
            }
            
            # 执行规划
            response = await self.llm.ainvoke(self.prompt.format_messages(**inputs))
            response_text = response.content

            print(f"----task planning llm response: {response_text}")
            
            # 提取并解析 JSON
            json_str = self.extract_json_from_response(response_text)
            
            # 解析JSON
            try:
                planning_result = json.loads(json_str)
            except json.JSONDecodeError:
                # 如果解析失败，创建默认结果
                planning_result = {
                    "plan": {
                        "steps": []
                    }
                }
            
            # 更新计划
            state["plan"] = planning_result.get("plan", {}).get("steps", [])
            
            # 确保每个步骤都包含必要的信息
            for i, step in enumerate(state["plan"]):
                if not isinstance(step, dict):
                    continue
                    
                # 确保步骤有唯一ID
                if "step_id" not in step:
                    step["step_id"] = f"step_{i+1}"
                
                # 确保步骤名称存在
                if "step_name" not in step:
                    step["step_name"] = f"步骤{i+1}"
                
                # 确保执行动作描述存在
                if "action" not in step:
                    step["action"] = f"执行步骤{i+1}"
                
                # 确保工具信息格式正确
                if "tool" not in step:
                    step["tool"] = {
                        "name": "",
                        "parameters": {}
                    }
                elif isinstance(step["tool"], dict):
                    if "name" not in step["tool"]:
                        step["tool"]["name"] = ""
                    if "parameters" not in step["tool"]:
                        step["tool"]["parameters"] = {}
            
            # 保存规划结果到状态
            state["planning_result"] = planning_result
            
            return state
            
        except Exception as e:
            print(f"----task planning llm error: {e}")
            # 出错时设置空计划
            state["plan"] = []
            return state 