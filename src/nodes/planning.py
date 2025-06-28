from typing import Dict, Any, List, Optional
import json
import time
import re
import uuid
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

from ..states.state import State
from ..llm import get_llm
from ..tool.registry import tool_registry
from ..tool.registry import ToolGroup
from ..vector_store.chroma_store import ChromaStore
from ..config import CHROMA_COLLECTION_NAME


class PlanningNode:
    """任务规划节点，负责制定处理流程的计划"""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化任务规划节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        self.tool_registry = tool_registry
        
        # 初始化向量存储
        self.vector_store = ChromaStore()
        self.vector_store.create_collection(CHROMA_COLLECTION_NAME)
    
    def _get_planning_prompt(self) -> ChatPromptTemplate:
        """获取规划提示模板
        
        Returns:
            规划提示模板
        """
        return ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的任务规划助手。"""),
            ("user", """ 
                        
            【相关知识】:
            {knowledge}

            【用户历史记录】
            其中每个记忆的类型如下:
             fact: 事实性记忆
             experience: 经验性记忆
             preference: 偏好性记忆
             emotion: 情感性记忆
             task: 任务相关记忆
             conversation: 对话记忆
             user_intent: 用户意图记忆
             other: 其他类型

            具体的记忆信息如下：   
            {memory_records}    

            【执行日志】
            记录系统执行过程中的所有操作和状态变化：
            {execution_log}

            【已完成工具】
            记录已经成功执行的工具调用：
            {completed_tools}

            【工具执行结果】
            记录工具调用的详细结果：
            {tool_results}

            【反思结果】
            记录系统对执行情况的反思分析：
            {reflection_result}

            【人工干预信息】
            记录人工干预的请求和反馈：
            {intervention_info}

            【错误信息】
            记录执行过程中遇到的错误：
            {errors}
        
            【用户需求】: {intent}
             
            参考上述信息，为了完成用户需求，生成详细的接下来需要执行的计划。
            
            重要说明：
            1. 如果某个步骤已经完成（在已完成工具或执行日志中有记录），请不要将其包含在新的计划中
            2. 只规划尚未完成的步骤
            3. 根据反思结果和错误信息，调整计划以解决之前的问题
            4. 考虑人工反馈，优化后续步骤
            
            要求：
            1. step_name 必须是简短的步骤名称，例如："提交出差申请"、"上传火车票"等
            2. step_desc 必须是对步骤执行动作的详细描述，例如："使用出差申请工具提交申请"、"使用上传工具上传火车票"等
            3. 确保JSON格式完全正确，包括所有引号和逗号
            4. 严格按照以下JSON格式输出，不要添加任何额外的字段或注释：

            {{
                "plan": {{
                    "steps": [
                        {{
                            "step_name": "步骤名称",
                            "step_desc": "执行动作描述",
                        }}
                    ]
                }}
            }}
            
            !注意，如果用户只是做咨询，请直接返回空数组[]，不要生成任何计划。
            """)
        ])
    
    def _query_knowledge_base(self, query: str, n_results: int = 5) -> str:
        """查询向量知识库
        
        Args:
            query: 查询语句
            n_results: 返回结果数量
            
        Returns:
            知识库查询结果字符串
        """
        try:
            # 执行向量搜索
            search_results = self.vector_store.search(
                query_texts=[query],
                n_results=n_results,
                similarity_threshold=0.5,  # 设置相似度阈值
                use_llm_similarity=True   # 使用大模型进行相似性判断
            )
            
            # 格式化搜索结果
            knowledge_content = ""
            if search_results and search_results.get("documents"):
                documents = search_results["documents"][0]  # 第一个查询的结果
                metadatas = search_results.get("metadatas", [[]])[0]
                
                for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                    filename = metadata.get("filename", f"文档{i+1}")
                    summary = metadata.get("summary", "")
                    
                    knowledge_content += f"\n--- 知识来源: {filename} ---\n"
                    if summary:
                        knowledge_content += f"摘要: {summary}\n"
                    knowledge_content += f"内容: {doc[:1000]}...\n"  # 限制内容长度
                    knowledge_content += "---\n"
            
            if not knowledge_content.strip():
                knowledge_content = "未找到相关的知识库信息。"
                
            return knowledge_content
            
        except Exception as e:
            print(f"向量知识库查询失败: {e}")
            return "知识库查询失败，将使用默认知识。"
    
    def extract_json_from_response(self, text: str) -> str:
        """从响应中提取JSON部分
        
        Args:
            text: 响应文本
            
        Returns:
            提取的JSON字符串
        """
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
        tool_schemas = self.tool_registry.get_schemas_by_group(ToolGroup.BUSINESS_TRIP)
        
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
            print("--------------------------------------------------------------------------------planning node start----------------------------------------------------------")
            
            # 将用户意图转换为查询语句
            query = self._convert_intent_to_query(state["intent"])

            # 查询向量知识库
            knowledge_content = self._query_knowledge_base(query)
            state["knowledge_content"] = knowledge_content
            
            # 获取可用工具描述
            tools_description = self._get_available_tools_description()
            
            # 格式化各种执行信息
            execution_log = self._format_execution_log(state)
            completed_tools = self._format_completed_tools(state)
            tool_results = self._format_tool_results(state)
            reflection_result = self._format_reflection_result(state)
            intervention_info = self._format_intervention_info(state)
            errors = self._format_errors(state)
            
            # 获取规划提示模板
            prompt = self._get_planning_prompt()
            
            # 准备输入
            inputs = {
                "intent": state["intent"],
                "knowledge": knowledge_content,  # 使用向量知识库查询结果
                "memory_records": state.get("memory_records", "无历史记录"),
                "available_tools": tools_description,
                "execution_log": execution_log,
                "completed_tools": completed_tools,
                "tool_results": tool_results,
                "reflection_result": reflection_result,
                "intervention_info": intervention_info,
                "errors": errors
            }
            
            # 执行规划
            print(f"【PROMPT】:\n{prompt.format_messages(**inputs)}")
            response = self.llm.invoke(prompt.format_messages(**inputs))
            response_text = response.content

            print(f"【RESPONSE】:\n{response_text}")
            
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
            
            # 获取原始计划数据
            original_plan = planning_result.get("plan", {}).get("steps", [])
            state["plan"] = original_plan
            
            # 确保每个步骤都包含必要的信息
            validated_plan = []
            for i, step in enumerate(state["plan"]):
                # 跳过无效的步骤
                if not isinstance(step, dict):
                    print(f"跳过无效步骤 {i}: 不是字典类型")
                    continue
                
                # 创建标准化的步骤对象
                validated_step = {
                    "step_id": str(uuid.uuid4()),  # 使用UUID作为唯一标识
                    "step_name": "",
                    "step_desc": "",
                    "status": "pending",  # 添加状态字段
                    "order": i + 1,  # 添加顺序字段
                    "created_at": time.time()  # 添加创建时间
                }
                
                # 合并现有数据，保留有效字段
                if isinstance(step.get("step_id"), str) and step["step_id"]:
                    validated_step["step_id"] = step["step_id"]
                
                if isinstance(step.get("step_name"), str) and step["step_name"].strip():
                    validated_step["step_name"] = step["step_name"].strip()
                else:
                    validated_step["step_name"] = f"步骤{i+1}"
                
                if isinstance(step.get("step_desc"), str) and step["step_desc"].strip():
                    validated_step["step_desc"] = step["step_desc"].strip()
                else:
                    validated_step["step_desc"] = f"执行步骤{i+1}"
                
                validated_plan.append(validated_step)
            
            # 更新计划为验证后的版本
            state["plan"] = validated_plan
            
            # 根据plan状态设置status
            if not validated_plan or len(validated_plan) == 0:
                state["status"] = "conversation_ready"  # 计划为空，准备进入对话节点
            else:
                state["status"] = "decision_ready"  # 计划不为空，准备进入决策节点
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
            
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"----task planning llm error: {e}")
            
            # 记录错误到状态中
            if "errors" not in state:
                state["errors"] = []
            
            state["errors"].append({
                "node": "planning",
                "error": str(e),
                "error_type": "planning_error",
                "timestamp": str(time.time())
            })
            
            # 出错时设置空计划
            state["plan"] = []
            state["status"] = "conversation_ready"  # 出错时也设置为准备进入对话节点
            
            # 更新时间戳
            state["updated_at"] = datetime.now()
            
            return state

    def _convert_intent_to_query(self, intent: str) -> str:
        """将用户意图转换为查询语句
        
        Args:
            intent: 用户意图
            
        Returns:
            查询语句
        """
        try:
            if isinstance(intent, dict):
                intent = json.dumps(intent, ensure_ascii=False, indent=2)
            else:
                intent = str(intent)
                
            # 创建意图转换查询的提示模板
            intent_to_query_prompt = """你是一个专业的查询助手。你的任务是将用户的意图转换为适合进行知识库查询的语句。
请根据用户的意图，生成一个查询语句，用于在相关的知识库中搜索相关信息。

要求：
1. 查询语句应该包含关键信息，有利于更详细的信息查询
2. 查询语句应该涵盖用户意图的核心内容
3. 如果用户意图涉及具体流程或政策，查询语句应该包含相关关键词
4. 返回格式：直接返回查询语句，不要添加任何额外的格式或说明

用户意图: {intent}"""
            
            # 准备输入
            inputs = {
                "intent": intent
            }
            print(f"【PROMPT】:\n{intent_to_query_prompt.format(**inputs)}")
            
            # 执行转换
            response = self.llm.invoke(intent_to_query_prompt.format(**inputs))
            response_text = response.content.strip()
            
            # 只输出</think>后面的内容
            query = response_text.split('</think>')[1].strip()
            print(f"【RESPONSE】:\n{query}")
            return query
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"----intent to query conversion error: {e}")
            # 出错时返回原始意图作为查询
            return intent

    def _format_execution_log(self, state: State) -> str:
        """格式化执行日志
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的执行日志字符串
        """
        try:
            execution_log = state.get("execution_log", [])
            if not execution_log:
                return "无执行日志"
            
            # 如果是字符串类型，直接返回
            if isinstance(execution_log, str):
                return execution_log
            
            # 如果是列表或字典，转换为JSON格式字符串
            if isinstance(execution_log, (list, dict)):
                return json.dumps(execution_log, ensure_ascii=False, indent=2)
            
            # 其他类型转换为字符串
            return str(execution_log)
            
        except Exception as e:
            return f"执行日志格式化出错: {str(e)}"

    def _format_completed_tools(self, state: State) -> str:
        """格式化已完成工具
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的已完成工具字符串
        """
        try:
            completed_tools = state.get("completed_tools", [])
            if not completed_tools:
                return "无已完成工具"
            
            # 如果是字符串类型，直接返回
            if isinstance(completed_tools, str):
                return completed_tools
            
            # 如果是列表或字典，转换为JSON格式字符串
            if isinstance(completed_tools, (list, dict)):
                return json.dumps(completed_tools, ensure_ascii=False, indent=2)
            
            # 其他类型转换为字符串
            return str(completed_tools)
            
        except Exception as e:
            return f"已完成工具格式化出错: {str(e)}"

    def _format_tool_results(self, state: State) -> str:
        """格式化工具执行结果
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的工具执行结果字符串
        """
        try:
            tool_results = state.get("tool_results", {})
            if not tool_results:
                return "无工具执行结果"
            
            # 如果是字符串类型，直接返回
            if isinstance(tool_results, str):
                return tool_results
            
            # 如果是列表或字典，转换为JSON格式字符串
            if isinstance(tool_results, (list, dict)):
                return json.dumps(tool_results, ensure_ascii=False, indent=2)
            
            # 其他类型转换为字符串
            return str(tool_results)
            
        except Exception as e:
            return f"工具执行结果格式化出错: {str(e)}"

    def _format_reflection_result(self, state: State) -> str:
        """格式化反思结果
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的反思结果字符串
        """
        try:
            reflection_result = state.get("reflection_result", {})
            if not reflection_result:
                return "无反思结果"
            
            # 如果是字符串类型，直接返回
            if isinstance(reflection_result, str):
                return reflection_result
            
            # 如果是列表或字典，转换为JSON格式字符串
            if isinstance(reflection_result, (list, dict)):
                return json.dumps(reflection_result, ensure_ascii=False, indent=2)
            
            # 其他类型转换为字符串
            return str(reflection_result)
            
        except Exception as e:
            return f"反思结果格式化出错: {str(e)}"

    def _format_intervention_info(self, state: State) -> str:
        """格式化人工干预信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的人工干预信息字符串
        """
        try:
            intervention_request = state.get("intervention_request", {})
            intervention_response = state.get("intervention_response", {})
            
            # 合并干预信息
            intervention_info = {}
            if intervention_request:
                intervention_info["intervention_request"] = intervention_request
            if intervention_response:
                intervention_info["intervention_response"] = intervention_response
            
            if not intervention_info:
                return "无人工干预信息"
            
            # 如果是字符串类型，直接返回
            if isinstance(intervention_info, str):
                return intervention_info
            
            # 如果是列表或字典，转换为JSON格式字符串
            if isinstance(intervention_info, (list, dict)):
                return json.dumps(intervention_info, ensure_ascii=False, indent=2)
            
            # 其他类型转换为字符串
            return str(intervention_info)
            
        except Exception as e:
            return f"人工干预信息格式化出错: {str(e)}"

    def _format_errors(self, state: State) -> str:
        """格式化错误信息
        
        Args:
            state: 当前状态
            
        Returns:
            格式化的错误信息字符串
        """
        try:
            errors = state.get("errors", [])
            if not errors:
                return "无错误信息"
            
            # 如果是字符串类型，直接返回
            if isinstance(errors, str):
                return errors
            
            # 如果是列表或字典，转换为JSON格式字符串
            if isinstance(errors, (list, dict)):
                return json.dumps(errors, ensure_ascii=False, indent=2)
            
            # 其他类型转换为字符串
            return str(errors)
            
        except Exception as e:
            return f"错误信息格式化出错: {str(e)}"