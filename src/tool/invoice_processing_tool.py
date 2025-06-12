"""
发票处理工具
提供发票上传、OCR识别和真伪验证功能
"""
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from .base import BaseTool

class InvoiceProcessingTool(BaseTool):
    """发票处理工具，处理发票的上传、识别、验证全流程"""
    
    @property
    def name(self) -> str:
        return "process_invoices"
    
    @property
    def description(self) -> str:
        return "上传发票文件，进行OCR识别和真伪验证，返回可用的发票数据"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "properties": {
                "file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "发票文件路径列表"
                },
                "user_id": {
                    "type": "string",
                    "description": "用户ID"
                },
                "auto_verify": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否自动进行真伪验证"
                }
            },
            "required": ["file_paths", "user_id"]
        }
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """执行发票处理工具
        
        Args:
            file_paths: 发票文件路径列表
            user_id: 用户ID
            auto_verify: 是否自动进行真伪验证，默认为True
            
        Returns:
            发票处理结果
        """
        # 验证参数
        self.validate_parameters(**kwargs)
        
        # 获取参数
        file_paths = kwargs.get("file_paths", [])
        user_id = kwargs.get("user_id")
        auto_verify = kwargs.get("auto_verify", True)
        
        # 处理结果
        processed_invoices = []
        failed_files = []
        total_amount = 0.0
        
        # 处理每个文件
        for file_path in file_paths:
            try:
                # 模拟OCR识别过程
                invoice_data = self._mock_ocr_recognition(file_path)
                
                # 如果OCR成功且需要验证
                if invoice_data and auto_verify:
                    # 模拟验证过程
                    verify_result = self._mock_verify_invoice(invoice_data)
                    invoice_data["verify_status"] = verify_result.get("status", "unknown")
                else:
                    invoice_data["verify_status"] = "unverified"
                
                # 添加到处理结果
                processed_invoices.append(invoice_data)
                
                # 累加金额
                if invoice_data.get("amount"):
                    total_amount += float(invoice_data["amount"])
                
            except Exception as e:
                # 记录处理失败的文件
                failed_files.append({
                    "file_path": file_path,
                    "error": str(e)
                })
        
        # 生成处理摘要
        summary = {
            "total_processed": len(file_paths),
            "success_count": len(processed_invoices),
            "failed_count": len(failed_files),
            "total_amount": total_amount
        }
        
        # 返回处理结果
        return {
            "processed_invoices": processed_invoices,
            "failed_files": failed_files,
            "summary": summary
        }
    
    def _mock_ocr_recognition(self, file_path: str) -> Dict[str, Any]:
        """模拟OCR识别过程
        
        Args:
            file_path: 发票文件路径
            
        Returns:
            OCR识别结果
        """
        # 创建模拟发票数据
        invoice_types = ["增值税专用发票", "增值税普通发票", "电子发票", "火车票", "飞机票", "出租车票"]
        invoice_type = random.choice(invoice_types)
        
        # 生成随机发票代码和号码
        invoice_code = f"{random.randint(1000000000, 9999999999)}"
        invoice_number = f"{random.randint(10000000, 99999999)}"
        
        # 生成开票日期（最近90天内的随机日期）
        invoice_date = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d")
        
        # 生成随机金额（50-5000之间）
        amount = round(random.uniform(50, 5000), 2)
        
        # 随机销售方名称
        vendors = [
            "北京科技有限公司", "上海贸易有限公司", "广州电子科技有限公司",
            "深圳信息技术有限公司", "杭州网络科技有限公司"
        ]
        vendor = random.choice(vendors)
        
        # 生成随机识别置信度(80%-100%)
        ocr_confidence = round(random.uniform(0.8, 1.0), 2)
        
        # 创建发票数据
        invoice_data = {
            "invoice_id": f"INV-{random.randint(10000, 99999)}",
            "invoice_type": invoice_type,
            "invoice_code": invoice_code,
            "invoice_number": invoice_number,
            "amount": amount,
            "invoice_date": invoice_date,
            "vendor": vendor,
            "ocr_confidence": ocr_confidence,
            "file_path": file_path
        }
        
        return invoice_data
    
    def _mock_verify_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, str]:
        """模拟发票验证过程
        
        Args:
            invoice_data: 发票数据
            
        Returns:
            验证结果
        """
        # 随机验证结果，90%概率有效
        is_valid = random.random() < 0.9
        
        if is_valid:
            return {
                "status": "valid",
                "message": "发票验证有效"
            }
        else:
            return {
                "status": "invalid",
                "message": "发票验证无效，可能是伪造发票"
            } 