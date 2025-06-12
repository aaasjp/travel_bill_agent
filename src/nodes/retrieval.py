from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import time
import json

from ..models.state import ExpenseState
from ..config import get_llm
from ..utils.logger import log_node_activity, log_error, log_node_entry, log_node_exit

class RetrievalNode:
    """
    检索节点，用于获取相关背景信息以支持任务规划。
    
    这个节点会根据当前状态和任务需求，从知识库或其他数据源检索相关信息，
    并将检索到的信息添加到状态上下文中，以便后续任务规划使用。
    """
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """初始化检索节点
        
        Args:
            llm: 可选的语言模型，如果不提供则使用配置中的默认模型
        """
        self.llm = llm or get_llm()
        
        # 定义检索分析提示模板
        self.retrieval_prompt = ChatPromptTemplate.from_template("""
        你是一个专业的差旅报销助手的检索组件。
        根据用户的问题和当前的任务，分析需要检索哪些信息来支持后续处理。
        
        ## 用户输入
        {user_input}
        
        ## 当前意图
        {intent}
        
        ## 当前计划
        {plan}
        
        请分析需要从知识库中检索哪些信息，以便更好地完成任务。以JSON格式返回结果：
        
        ```json
        {
            "query_keywords": ["关键词1", "关键词2"...],
            "information_types": ["政策", "表格", "流程"...],
            "rationale": "为什么需要检索这些信息的解释"
        }
        ```
        """)
        
        # 定义查询解析器
        self.parser = JsonOutputParser()
        
        # 构建检索链
        self.chain = self.retrieval_prompt | self.llm | self.parser
    
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
        timestamp = str(state.get("updated_at", time.time()))
        
        # 创建日志条目
        log_entry = {
            "node": "retrieval",
            "action": action,
            "timestamp": timestamp,
            "details": details
        }
        
        # 添加日志到状态
        state["execution_log"].append(log_entry)
        
        # 同时记录到文件日志
        log_node_activity("retrieval", action, details)
    
    async def __call__(self, state: ExpenseState) -> ExpenseState:
        """执行检索操作
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        # 记录节点开始执行
        state_id = state.get("id", "unknown")
        start_time = time.time()
        log_node_entry("retrieval", state_id, {
            "user_input": state.get("user_input", ""),
            "intent": state.get("intent", {}),
            "plan_steps": len(state.get("plan", [])),
            "need_retrieval": state.get("need_retrieval", False)
        })
        
        # 记录开始检索
        self._add_log_entry(
            state,
            "开始检索分析",
            {"message": "开始分析需要检索的信息"}
        )
        
        try:
            # 准备检索分析输入
            inputs = {
                "user_input": state["user_input"],
                "intent": state["intent"],
                "plan": state["plan"]
            }
            
            # 记录LLM调用开始
            llm_call_start_time = time.time()
            self._add_log_entry(
                state,
                "调用大模型",
                {
                    "input_keys": list(inputs.keys()),
                    "input_intent_length": len(json.dumps(inputs["intent"], ensure_ascii=False)),
                    "input_plan_length": len(json.dumps(inputs["plan"], ensure_ascii=False))
                }
            )
            
            # 分析需要检索的内容
            retrieval_analysis = await self.chain.ainvoke(inputs)
            
            # 计算LLM调用执行时间
            llm_execution_time = time.time() - llm_call_start_time
            
            # 记录LLM响应
            self._add_log_entry(
                state,
                "大模型检索分析完成",
                {
                    "result_keys": list(retrieval_analysis.keys()),
                    "query_keywords_count": len(retrieval_analysis.get("query_keywords", [])),
                    "information_types_count": len(retrieval_analysis.get("information_types", [])),
                    "execution_time": f"{llm_execution_time:.4f}秒"
                }
            )
            
            # 这里是模拟检索操作
            # 在实际应用中，应该根据 retrieval_analysis 的内容
            # 从向量数据库或其他知识库中检索实际信息
            retrieval_start_time = time.time()
            
            # 记录开始实际检索
            self._add_log_entry(
                state,
                "开始实际检索",
                {
                    "query_keywords": retrieval_analysis.get("query_keywords", []),
                    "information_types": retrieval_analysis.get("information_types", [])
                }
            )
            
            # 模拟的检索结果
            retrieval_results = {
                "policy_info": {
                    "max_meal_allowance": "每日100元",
                    "hotel_limit": "四星级以下",
                    "transportation": "经济舱/二等座"
                },
                "form_templates": ["标准报销单", "出差申请单", "交通费报销明细"],
                "process_info": {
                    "approval_flow": ["部门经理", "财务审核", "财务经理"],
                    "time_requirement": "报销需在出差结束后30天内提交"
                }
            }
            
            # 计算实际检索时间
            retrieval_execution_time = time.time() - retrieval_start_time
            
            # 记录检索结果
            self._add_log_entry(
                state,
                "检索结果",
                {
                    "result_keys": list(retrieval_results.keys()),
                    "result_count": sum(len(value) if isinstance(value, list) else 1 for value in retrieval_results.values()),
                    "execution_time": f"{retrieval_execution_time:.4f}秒"
                }
            )
            
            # 更新状态中的上下文
            if "context" not in state:
                state["context"] = {}
                
            state["context"].update({
                "retrieval_analysis": retrieval_analysis,
                "retrieval_results": retrieval_results
            })
            
            # 记录上下文更新
            self._add_log_entry(
                state,
                "更新上下文",
                {
                    "context_keys": list(state["context"].keys()),
                    "retrieval_keys": list(retrieval_results.keys())
                }
            )
            
            # 记录检索日志
            self._add_log_entry(
                state,
                "检索相关信息",
                {
                    "query": retrieval_analysis.get("query_keywords", []),
                    "result_summary": "检索到政策信息、表单模板和流程信息"
                }
            )
            
            # 设置检索完成标志
            state["need_retrieval"] = False
            
            # 记录节点执行完成
            execution_time = time.time() - start_time
            log_node_exit("retrieval", state_id, execution_time, {
                "status": "completed",
                "query_keywords_count": len(retrieval_analysis.get("query_keywords", [])),
                "retrieval_results_keys": list(retrieval_results.keys()),
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            return state
            
        except Exception as e:
            # 记录错误
            error_message = str(e)
            if "errors" not in state:
                state["errors"] = []
                
            state["errors"].append({
                "node": "retrieval",
                "error": error_message,
                "timestamp": str(state.get("updated_at", time.time()))
            })
            
            # 记录错误日志
            self._add_log_entry(
                state,
                "检索失败",
                {
                    "error": error_message
                }
            )
            
            # 记录详细错误日志
            log_error(
                "retrieval",
                "检索过程中发生未捕获的异常",
                {
                    "error": error_message
                }
            )
            
            # 记录节点执行完成（错误）
            execution_time = time.time() - start_time
            log_node_exit("retrieval", state_id, execution_time, {
                "status": "error",
                "error": error_message,
                "execution_time": f"{execution_time:.4f}秒"
            })
            
            # 即使出错也继续流程
            state["need_retrieval"] = False
            return state 