"""
测试差旅报销智能体
"""
import asyncio
from src.reimbursement_agent import ReimbursementAgent

async def test_agent():
    """测试智能体"""
    agent = ReimbursementAgent()
    
    # 测试场景1：上传发票
    print("\n=== 测试场景1：上传发票 ===")
    response = await agent.run("我有3张发票需要报销，分别是火车票、住宿费和餐饮费，请帮我处理")
    print(response)
    
    # 测试场景2：查询报销状态
    print("\n=== 测试场景2：查询报销状态 ===")
    response = await agent.run("我想查询我的报销单REIM-12345的审批进度")
    print(response)
    
    # 测试场景3：补助申请
    print("\n=== 测试场景3：补助申请 ===")
    response = await agent.run("我想申请出差补助，我的出差申请单号是TA-67890")
    print(response)
    
    # 测试场景4：多轮对话
    print("\n=== 测试场景4：多轮对话 ===")
    messages = [
        {"role": "user", "content": "我需要创建一个新的报销单，包含我上周出差的费用"},
        {"role": "assistant", "content": "我可以帮您创建报销单。请问您有哪些支出记录需要包含在内？"},
        {"role": "user", "content": "我有两张发票，一张是机票3000元，一张是住宿费1500元"}
    ]
    response = await agent.chat(messages)
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent()) 