#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试相似度阈值功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector_store.chroma_store import ChromaStore

def test_similarity_threshold():
    """测试相似度阈值功能"""
    
    # 初始化向量存储
    store = ChromaStore()
    
    # 创建测试集合
    test_collection_name = "test_similarity_threshold"
    store.create_collection(test_collection_name)
    
    try:
        # 添加一些测试文档
        test_documents = [
            "需要提供发票和行程单",
            "住宿费用报销标准是每天300元",
            "交通费用包括机票、火车票和出租车费",
            "餐饮费用按实际发生金额报销",
            "差旅申请需要提前3天提交"
        ]
        
        test_metadatas = [
            {"type": "policy", "category": "reimbursement"},
            {"type": "policy", "category": "accommodation"},
            {"type": "policy", "category": "transportation"},
            {"type": "policy", "category": "meals"},
            {"type": "policy", "category": "application"}
        ]
        
        store.add_documents(
            documents=test_documents,
            metadatas=test_metadatas
        )
        
        print("✅ 测试文档添加成功")
        
        # 测试不同相似度阈值
        query = "流程"
        
        print(f"\n🔍 查询: {query}")
        print("-" * 50)
        
        # 测试1: 无阈值限制
        print("1. 无阈值限制 (similarity_threshold=0.0):")
        results1 = store.search(
            query_texts=[query],
            n_results=5,
            similarity_threshold=0.0
        )
        print(f"   返回结果数量: {len(results1['documents'][0])}")
        for i, (doc, distance) in enumerate(zip(results1['documents'][0], results1['distances'][0])):
            similarity = 1.0 - distance
            print(f"   {i+1}. 相似度: {similarity:.3f}, 距离: {distance:.3f}")
            print(f"      文档: {doc[:50]}...")
        
        # 测试2: 中等阈值
        print("\n2. 中等阈值 (similarity_threshold=0.5):")
        results2 = store.search(
            query_texts=[query],
            n_results=5,
            similarity_threshold=0.5
        )
        print(f"   返回结果数量: {len(results2['documents'][0])}")
        for i, (doc, distance) in enumerate(zip(results2['documents'][0], results2['distances'][0])):
            similarity = 1.0 - distance
            print(f"   {i+1}. 相似度: {similarity:.3f}, 距离: {distance:.3f}")
            print(f"      文档: {doc[:50]}...")
        
        # 测试3: 高阈值
        print("\n3. 高阈值 (similarity_threshold=0.8):")
        results3 = store.search(
            query_texts=[query],
            n_results=5,
            similarity_threshold=0.8
        )
        print(f"   返回结果数量: {len(results3['documents'][0])}")
        for i, (doc, distance) in enumerate(zip(results3['documents'][0], results3['distances'][0])):
            similarity = 1.0 - distance
            print(f"   {i+1}. 相似度: {similarity:.3f}, 距离: {distance:.3f}")
            print(f"      文档: {doc[:50]}...")
        
        # 测试4: 验证阈值过滤是否正确
        print("\n4. 验证阈值过滤:")
        all_results = store.search(
            query_texts=[query],
            n_results=10,
            similarity_threshold=0.0
        )
        
        # 手动过滤
        manual_filtered = []
        for doc, distance in zip(all_results['documents'][0], all_results['distances'][0]):
            similarity = 1.0 - distance
            if similarity >= 0.5:
                manual_filtered.append((doc, distance, similarity))
        
        print(f"   手动过滤结果数量: {len(manual_filtered)}")
        print(f"   自动过滤结果数量: {len(results2['documents'][0])}")
        
        if len(manual_filtered) == len(results2['documents'][0]):
            print("   ✅ 阈值过滤功能正常")
        else:
            print("   ❌ 阈值过滤功能异常")
        
        print("\n✅ 相似度阈值测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试集合
        try:
            store.delete_collection(test_collection_name)
            print("🧹 测试集合已清理")
        except:
            pass

if __name__ == "__main__":
    test_similarity_threshold() 