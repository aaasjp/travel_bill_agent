import sys
import os
import json
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config.config import MODEL_NAME, MODEL_BASE_URL, API_KEY

async def test_model_response():
    # 初始化模型
    model = ChatOpenAI(
        model_name=MODEL_NAME,
        base_url=MODEL_BASE_URL,
        api_key=API_KEY
    )
    
    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的差旅报销助手。请分析用户的输入，识别以下信息：
        1. 业务类型（差旅报销申请/查询/修改等）
        2. 时间范围
        3. 出差地点
        4. 申请类型
        5. 其他关键信息
        
        请以JSON格式输出，包含以下字段：
        - business_type: 业务类型
        - time_range: 时间范围
        - location: 出差地点
        - application_type: 申请类型
        - other_info: 其他信息
        """),
        ("user", "{input}")
    ])
    
    # 构建链
    chain = prompt | model
    
    # 测试输入
    test_input = "我要申请3月15-17日北京出差的报销"
    
    # 调用模型
    print(f"发送请求: {test_input}")
    result = await chain.ainvoke({"input": test_input})
    
    # 打印原始响应
    print("\n原始响应类型:", type(result))
    print("原始响应内容:", result)
    
    # 检查content属性
    if hasattr(result, 'content'):
        print("\ncontent属性:", result.content)
        try:
            # 尝试解析JSON
            data = json.loads(result.content)
            print("\n解析后的JSON:", json.dumps(data, ensure_ascii=False, indent=2))
        except json.JSONDecodeError as e:
            print(f"\nJSON解析错误: {str(e)}")
    else:
        print("\n没有content属性")
        # 尝试其他可能的属性
        print("所有属性:", dir(result))

if __name__ == "__main__":
    asyncio.run(test_model_response()) 