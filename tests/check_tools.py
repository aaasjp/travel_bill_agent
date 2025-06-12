import glob
import os

def check_tool_files():
    """检查所有工具文件是否包含_execute方法"""
    # 获取所有工具文件
    tool_files = glob.glob('src/tool/*_tool.py')
    
    for file in tool_files:
        # 读取文件内容
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含_execute方法
        if 'async def _execute' in content:
            print(f'{file}: OK - 有_execute方法')
        else:
            print(f'{file}: ERROR - 缺少_execute方法')

if __name__ == "__main__":
    check_tool_files() 