import os
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
import docx
from .chroma_store import ChromaStore

def read_pdf(file_path: str) -> str:
    """读取PDF文件内容"""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def read_doc(file_path: str) -> str:
    """读取DOC文件内容"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise ValueError(f"无法读取文件 {file_path}: {str(e)}")

def process_file(file_path: str) -> str:
    """根据文件类型处理文件内容"""
    file_extension = Path(file_path).suffix.lower()
    if file_extension == '.pdf':
        return read_pdf(file_path)
    elif file_extension in ['.doc', '.docx']:
        return read_doc(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_extension}")

def is_valid_file(file_path: Path) -> bool:
    """检查文件是否有效（不是临时文件或隐藏文件）"""
    # 排除以.开头的文件（隐藏文件）
    if file_path.name.startswith('.'):
        return False
    # 排除以~开头的文件（临时文件）
    if file_path.name.startswith('~'):
        return False
    # 排除以.~开头的文件（某些编辑器的临时文件）
    if file_path.name.startswith('.~'):
        return False
    return True

def load_knowledge_to_vector_store():
    """将知识数据加载到向量库中"""
    # 初始化向量存储
    vector_store = ChromaStore()
    
    # 创建集合
    collection_name = "travel_policy"
    vector_store.create_collection(collection_name)
    
    # 知识数据目录
    knowledge_dir = Path("data/knowledge_data")
    
    # 检查目录是否存在，如果不存在则创建
    if not knowledge_dir.exists():
        print(f"创建目录: {knowledge_dir}")
        knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查目录是否为空
    files = [f for f in knowledge_dir.glob("*") if is_valid_file(f)]
    if not files:
        print(f"警告: 目录 {knowledge_dir} 是空的或只包含临时文件，请先添加文档文件")
        return
    
    # 处理目录下的所有文件
    documents = []
    metadatas = []
    ids = []
    
    for file_path in files:
        if file_path.suffix.lower() in ['.pdf', '.doc', '.docx']:
            try:
                # 读取文件内容
                content = process_file(str(file_path))
                
                # 准备元数据
                metadata = {
                    "filename": file_path.name,
                    "file_type": file_path.suffix[1:],
                    "file_size": file_path.stat().st_size
                }
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(file_path.stem)
                
                print(f"成功处理文件: {file_path.name}")
                
            except Exception as e:
                # 打印完整错误信息
                import traceback
                print("错误堆栈:")
                traceback.print_exc()
                print(f"处理文件 {file_path.name} 时出错: {str(e)}")
    
    if documents:
        # 将文档添加到向量库
        vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"成功将 {len(documents)} 个文档加载到向量库中")
    else:
        print("没有找到可处理的文档")

if __name__ == "__main__":
    load_knowledge_to_vector_store() 