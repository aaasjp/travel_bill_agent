import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from config.config import MODEL_NAME, MODEL_BASE_URL, API_KEY
def test_qwen_model():
    # 配置模型参数
    model = MODEL_NAME
    url = MODEL_BASE_URL
    
    # 初始化 ChatOpenAI 实例
    chat = ChatOpenAI(
        model_name=model,
        openai_api_base=url,
        openai_api_key=API_KEY,  
        temperature=0.7,
        max_tokens=1000
    )
    
    # 创建测试消息
    messages = [
        HumanMessage(content="你好，请做个简单的自我介绍。")
    ]
    
    try:
        # 调用模型
        response = chat(messages)
        print("模型响应成功！")
        print("响应内容:", response.content)
        return True
    except Exception as e:
        print("模型调用失败！")
        print("错误信息:", str(e))
        return False

if __name__ == "__main__":
    test_qwen_model()
