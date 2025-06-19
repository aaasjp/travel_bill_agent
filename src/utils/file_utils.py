# 文件处理工具

import os
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
import docx

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
