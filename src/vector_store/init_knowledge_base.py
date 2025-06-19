#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库初始化脚本
用于将data/knowledge_data目录下的文件添加到向量库中
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.vector_store.chroma_store import ChromaStore
from src.config import CHROMA_COLLECTION_NAME

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/init_knowledge_base.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KnowledgeBaseInitializer:
    """知识库初始化器"""
    
    def __init__(self):
        """初始化知识库初始化器"""
        self.chroma_store = ChromaStore()
        self.knowledge_data_dir = project_root / "data" / "knowledge_data"
        
    def init_collection(self) -> bool:
        """
        初始化向量库集合
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info(f"正在创建集合: {CHROMA_COLLECTION_NAME}")
            self.chroma_store.create_collection(CHROMA_COLLECTION_NAME)
            logger.info(f"集合 {CHROMA_COLLECTION_NAME} 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            return False
    
    def get_knowledge_files(self) -> List[Path]:
        """
        获取知识库目录下的所有文件
        
        Returns:
            List[Path]: 文件路径列表
        """
        files = []
        
        if not self.knowledge_data_dir.exists():
            logger.error(f"知识库目录不存在: {self.knowledge_data_dir}")
            return files
        
        # 遍历目录下的所有文件
        for file_path in self.knowledge_data_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                files.append(file_path)
                logger.info(f"发现文件: {file_path.name}")
        
        return files
    
    def add_knowledge_files(self, files: List[Path], summarize_content: bool = True) -> Dict[str, Any]:
        """
        将知识库文件添加到向量库
        
        Args:
            files: 文件路径列表
            summarize_content: 是否对文件内容进行总结
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if not files:
            logger.warning("没有找到需要处理的文件")
            return {
                "success": False,
                "message": "没有找到需要处理的文件"
            }
        
        logger.info(f"开始处理 {len(files)} 个文件...")
        
        # 转换为字符串路径列表
        file_paths = [str(file_path) for file_path in files]
        
        # 批量添加文件到向量库
        result = self.chroma_store.add_files_batch(
            file_paths=file_paths,
            summarize_content=summarize_content
        )
        
        # 记录处理结果
        logger.info(f"文件处理完成:")
        logger.info(f"  成功处理: {result['successful_count']} 个文件")
        logger.info(f"  失败处理: {result['failed_count']} 个文件")
        
        if result['successful_files']:
            logger.info("成功处理的文件:")
            for file_path in result['successful_files']:
                logger.info(f"  - {Path(file_path).name}")
        
        if result['failed_files']:
            logger.error("失败处理的文件:")
            for failed_file in result['failed_files']:
                logger.error(f"  - {Path(failed_file['file_path']).name}: {failed_file['error']}")
        
        return result
    
    def check_collection_status(self) -> Dict[str, Any]:
        """
        检查集合状态
        
        Returns:
            Dict[str, Any]: 集合状态信息
        """
        try:
            collections = self.chroma_store.list_collections()
            if CHROMA_COLLECTION_NAME in collections:
                # 获取集合信息
                collection = self.chroma_store.client.get_collection(CHROMA_COLLECTION_NAME)
                count = collection.count()
                logger.info(f"集合 {CHROMA_COLLECTION_NAME} 存在，包含 {count} 个文档")
                return {
                    "exists": True,
                    "collection_name": CHROMA_COLLECTION_NAME,
                    "document_count": count
                }
            else:
                logger.info(f"集合 {CHROMA_COLLECTION_NAME} 不存在")
                return {
                    "exists": False,
                    "collection_name": CHROMA_COLLECTION_NAME,
                    "document_count": 0
                }
        except Exception as e:
            logger.error(f"检查集合状态失败: {str(e)}")
            return {
                "exists": False,
                "error": str(e)
            }
    
    def run_initialization(self, force_reinit: bool = False, summarize_content: bool = True) -> bool:
        """
        运行知识库初始化
        
        Args:
            force_reinit: 是否强制重新初始化（删除现有集合）
            summarize_content: 是否对文件内容进行总结
            
        Returns:
            bool: 初始化是否成功
        """
        logger.info("开始知识库初始化...")
        
        # 检查集合状态
        status = self.check_collection_status()
        
        if status["exists"]:
            if force_reinit:
                logger.info("强制重新初始化，删除现有集合...")
                try:
                    self.chroma_store.delete_collection(CHROMA_COLLECTION_NAME)
                    logger.info("现有集合已删除")
                except Exception as e:
                    logger.error(f"删除集合失败: {str(e)}")
                    return False
            else:
                logger.info(f"集合已存在，包含 {status['document_count']} 个文档")
                user_input = input("集合已存在，是否继续添加新文件？(y/n): ").lower().strip()
                if user_input != 'y':
                    logger.info("用户取消操作")
                    return True
        
        # 创建集合
        if not self.init_collection():
            return False
        
        # 获取知识库文件
        files = self.get_knowledge_files()
        if not files:
            logger.error("没有找到知识库文件")
            return False
        
        # 添加文件到向量库
        result = self.add_knowledge_files(files, summarize_content)
        
        if result['successful_count'] > 0:
            logger.info("知识库初始化完成！")
            return True
        else:
            logger.error("知识库初始化失败，没有成功添加任何文件")
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("知识库初始化工具")
    print("=" * 50)
    
    # 创建logs目录
    os.makedirs('logs', exist_ok=True)
    
    # 创建初始化器
    initializer = KnowledgeBaseInitializer()
    
    # 检查命令行参数
    force_reinit = "--force" in sys.argv
    no_summary = "--no-summary" in sys.argv
    
    if force_reinit:
        print("检测到 --force 参数，将强制重新初始化")
    
    if no_summary:
        print("检测到 --no-summary 参数，将不对文件内容进行总结")
    
    # 运行初始化
    success = initializer.run_initialization(
        force_reinit=force_reinit,
        summarize_content=not no_summary
    )
    
    if success:
        print("\n✅ 知识库初始化成功！")
        # 显示最终状态
        status = initializer.check_collection_status()
        if status["exists"]:
            print(f"📊 集合 '{status['collection_name']}' 包含 {status['document_count']} 个文档")
    else:
        print("\n❌ 知识库初始化失败！")
        sys.exit(1)

if __name__ == "__main__":
    main() 