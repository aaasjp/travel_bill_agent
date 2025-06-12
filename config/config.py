import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 模型配置
MODEL_NAME = os.getenv('MODEL_NAME', 'qwen3-235b-a22b')
MODEL_BASE_URL = os.getenv('MODEL_BASE_URL', 'http://10.249.238.52:13206/member3/qwen3-235b-a22b/v1')
API_KEY = os.getenv('API_KEY', 'sk-OUw7aKzO6oeUiMBK157e4347B6C941108f29BcCbFaEc8c00') 

print(f'MODEL_NAME: {MODEL_NAME}    ')
print(f'MODEL_BASE_URL: {MODEL_BASE_URL}')
print(f'API_KEY: {API_KEY}')