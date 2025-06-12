import os
import re

def fix_tool_file(file_path):
    """修改工具文件，将execute方法重命名为_execute
    
    Args:
        file_path: 工具文件路径
    """
    print(f"处理文件: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式替换方法名
    # 正则表达式匹配 "async def execute(" 或 "def execute("
    pattern = r'(async\s+def|def)\s+execute\s*\('
    replacement = r'\1 _execute('
    
    # 执行替换
    new_content = re.sub(pattern, replacement, content)
    
    # 检查是否有变化
    if new_content != content:
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  已修改: {file_path}")
    else:
        print(f"  无需修改: {file_path}")

def main():
    """主函数"""
    # 工具目录
    tool_dir = 'src/tool'
    
    # 获取所有工具文件
    tool_files = [
        f for f in os.listdir(tool_dir) 
        if f.endswith('_tool.py') and f != 'base.py'
    ]
    
    print(f"找到 {len(tool_files)} 个工具文件需要修改")
    
    # 修改每个工具文件
    for tool_file in tool_files:
        fix_tool_file(os.path.join(tool_dir, tool_file))
    
    print("修改完成")

if __name__ == "__main__":
    main() 