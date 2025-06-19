# 大模型方法调用
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from .config import MODEL_NAME, MODEL_BASE_URL, API_KEY

def get_llm() -> BaseChatModel:
    """获取默认语言模型实例
    
    Returns:
        配置好的语言模型实例
    """
    return ChatOpenAI(
        model_name=MODEL_NAME,
        base_url=MODEL_BASE_URL,
        api_key=API_KEY,
        temperature=0.7,
        streaming=True
    )