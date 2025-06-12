import requests
import json

def test_process_api():
    url = "http://localhost:8000/process"
    headers = {"Content-Type": "application/json"}
    
    # 测试用例
    test_cases = [
        {"input": "我要申请3月15-17日北京出差的报销"},
        {"input": "查询我上个月的报销状态"},
        {"input": "test expense request"}
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试 #{i+1}: {test_case['input']}")
        try:
            response = requests.post(url, headers=headers, json=test_case)
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_process_api() 