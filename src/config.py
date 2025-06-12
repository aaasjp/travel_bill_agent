from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 模型配置
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen3-235b-a22b")
MODEL_BASE_URL = os.environ.get("MODEL_BASE_URL", "http://10.249.238.52:13206/member3/qwen3-235b-a22b/v1")
API_KEY = os.environ.get("API_KEY", "EMPTY")

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

# 应用配置
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

# LangSmith配置
LANGSMITH_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "")
LANGSMITH_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "差旅报销智能体")
LANGSMITH_ENDPOINT = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# 工具配置
TOOLS_ENABLED = os.environ.get("TOOLS_ENABLED", "true").lower() == "true" 