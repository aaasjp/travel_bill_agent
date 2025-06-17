import re

def extract_json_from_response(text: str) -> str:
    """从响应文本中提取JSON部分
    
    Args:
        text: 包含JSON的响应文本
        
    Returns:
        str: 提取出的JSON字符串
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
    
    # 尝试找到完整的JSON对象，使用更精确的匹配
    # 找到第一个{，然后匹配到对应的}
    start_idx = text.find('{')
    if start_idx != -1:
        # 从第一个{开始，计算括号匹配
        brace_count = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(text)):
            char = text[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if brace_count == 0:  # 找到了匹配的括号
            json_str = text[start_idx:end_idx + 1]
            return json_str.strip()
    
    # 如果还是没找到，使用正则表达式作为备用方案
    json_pattern = r'({[\s\S]*})'
    json_match = re.search(json_pattern, text, re.DOTALL)
    
    if json_match:
        return json_match.group(1).strip()
    
    return text  # 如果无法提取，返回原始文本 