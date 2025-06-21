#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试大模型相似性判断功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.vector_store.chroma_store import ChromaStore
from src.config import CHROMA_COLLECTION_NAME

def test_llm_similarity_search():
    """测试使用大模型进行相似性搜索"""
    
    # 初始化向量存储
    chroma_store = ChromaStore()
    
    # 创建或获取集合
    try:
        chroma_store.create_collection(CHROMA_COLLECTION_NAME)
        print(f"成功创建/获取集合: {CHROMA_COLLECTION_NAME}")
    except Exception as e:
        print(f"创建集合失败: {str(e)}")
        return
    
    # 检查集合中是否有数据
    try:
        # 先进行普通搜索查看是否有数据
        results = chroma_store.search(
            query_texts=["差旅报销"],
            n_results=5,
            use_llm_similarity=False
        )
        
        if not results["ids"] or not results["ids"][0]:
            print("集合中没有数据，请先添加一些文档")
            return
        
        print(f"集合中有 {len(results['ids'][0])} 个文档")
        
        # 测试1: 只使用向量相似度过滤
        print("\n=== 测试1: 只使用向量相似度过滤 ===")
        vector_results = chroma_store.search(
            query_texts=["差旅报销流程"],
            n_results=3,
            use_llm_similarity=False,
            similarity_threshold=0.5
        )
        
        print(f"向量相似度过滤结果数量: {len(vector_results['ids'][0])}")
        
        # 测试2: 向量过滤 + 大模型优化
        print("\n=== 测试2: 向量过滤 + 大模型优化 ===")
        llm_results = chroma_store.search(
            query_texts=["差旅报销流程"],
            n_results=3,
            use_llm_similarity=True,
            similarity_threshold=0.5
        )
        
        print(f"大模型优化结果数量: {len(llm_results['ids'][0])}")
        
        # 显示大模型优化结果
        for i, (doc_id, metadata, distance) in enumerate(zip(
            llm_results["ids"][0], 
            llm_results["metadatas"][0], 
            llm_results["distances"][0]
        )):
            print(f"\n结果 {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  文件名: {metadata.get('filename', 'N/A')}")
            print(f"  距离: {distance:.4f}")
            if "summary" in metadata:
                print(f"  摘要: {metadata['summary'][:100]}...")
        
        # 对比两种方法的结果
        print("\n=== 对比搜索结果 ===")
        print(f"向量相似度过滤结果数量: {len(vector_results['ids'][0])}")
        print(f"大模型优化结果数量: {len(llm_results['ids'][0])}")
        
        # 检查结果是否有差异
        vector_ids = set(vector_results["ids"][0])
        llm_ids = set(llm_results["ids"][0])
        
        if vector_ids == llm_ids:
            print("两种方法返回相同的文档集合")
            
            # 检查排序是否有差异
            vector_order = vector_results["ids"][0]
            llm_order = llm_results["ids"][0]
            
            if vector_order == llm_order:
                print("文档排序也相同")
            else:
                print("文档排序不同，大模型重新排序了结果")
                print(f"向量排序: {vector_order}")
                print(f"大模型排序: {llm_order}")
        else:
            print("两种方法返回不同的文档集合")
            print(f"向量过滤独有: {vector_ids - llm_ids}")
            print(f"大模型优化独有: {llm_ids - vector_ids}")
        
        # 测试3: 不使用相似度阈值，只使用大模型优化
        print("\n=== 测试3: 不使用相似度阈值，只使用大模型优化 ===")
        llm_only_results = chroma_store.search(
            query_texts=["差旅报销流程"],
            n_results=3,
            use_llm_similarity=True,
            similarity_threshold=0.0  # 不使用阈值过滤
        )
        
        print(f"大模型优化结果数量: {len(llm_only_results['ids'][0])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_similarity_search() 