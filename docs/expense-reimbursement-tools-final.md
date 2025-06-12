# 差旅报销智能体工具设计文档

## 1. 概述

本文档定义了基于LangGraph的差旅报销智能体所需的工具集设计。工具设计遵循以下原则：

- **工具是执行器，不是决策者**：工具只负责执行具体操作，决策由LLM完成
- **业务完整性**：一个工具完成一个完整的业务操作单元
- **清晰的输入输出**：工具接口简单明确，便于LLM理解和调用

## 2. 工具集设计

### 2.1 发票处理工具（InvoiceProcessingTool）

**功能描述**：处理发票的上传、识别、验证全流程

```python
class InvoiceProcessingTool:
    name = "process_invoices"
    description = "上传发票文件，进行OCR识别和真伪验证，返回可用的发票数据"
    
    parameters = {
        "type": "object",
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
    
    returns = {
        "processed_invoices": [
            {
                "invoice_id": "发票ID",
                "invoice_type": "发票类型",
                "invoice_code": "发票代码",
                "invoice_number": "发票号码",
                "amount": "金额",
                "invoice_date": "开票日期",
                "vendor": "销售方",
                "verify_status": "验证状态",
                "ocr_confidence": "识别置信度"
            }
        ],
        "failed_files": ["处理失败的文件列表"],
        "summary": {
            "total_processed": "处理总数",
            "success_count": "成功数量",
            "total_amount": "总金额"
        }
    }
```

### 2.2 支出记录管理工具（ExpenseRecordManagementTool）

**功能描述**：从发票生成支出记录，包括类型映射和信息补充

```python
class ExpenseRecordManagementTool:
    name = "manage_expense_records"
    description = "根据发票创建支出记录，自动映射费用类型，返回需要补充的字段"
    
    parameters = {
        "type": "object",
        "properties": {
            "invoice_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "已验证的发票ID列表"
            },
            "supplement_data": {
                "type": "object",
                "description": "补充的支出记录信息（可选）"
            },
            "action": {
                "type": "string",
                "enum": ["create", "update", "validate"],
                "default": "create",
                "description": "操作类型"
            }
        },
        "required": ["invoice_ids", "action"]
    }
    
    returns = {
        "expense_records": [
            {
                "record_id": "支出记录ID",
                "invoice_id": "关联发票ID",
                "expense_type": "支出类型",
                "amount": "金额",
                "status": "状态",
                "required_fields": ["需要补充的字段列表"],
                "validation_result": "验证结果"
            }
        ],
        "summary": {
            "total_created": "创建总数",
            "total_amount": "总金额",
            "needs_supplement": "需要补充信息的记录数"
        }
    }
```

### 2.3 报销单管理工具（ReimbursementManagementTool）

**功能描述**：管理报销单的创建、关联和保存

```python
class ReimbursementManagementTool:
    name = "manage_reimbursement"
    description = "创建报销单，关联支出记录、出差申请和借款，保存报销单数据"
    
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "link_travel", "link_loan", "supplement", "save"],
                "description": "操作类型"
            },
            "bill_id": {
                "type": "string",
                "description": "报销单ID（create时不需要）"
            },
            "expense_record_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "支出记录ID列表（create时需要）"
            },
            "link_data": {
                "type": "object",
                "description": "关联数据（link操作时需要）"
            },
            "supplement_data": {
                "type": "object",
                "description": "补充数据（supplement时需要）"
            }
        },
        "required": ["action"]
    }
    
    returns = {
        # 根据action返回不同结果
        "create": {
            "bill_id": "报销单ID",
            "bill_number": "报销单号",
            "total_amount": "总金额",
            "required_fields": "需要补充的字段"
        },
        "link_travel": {
            "linked_trips": "已关联的出差申请",
            "travel_days": "出差天数",
            "allowance_amount": "补助金额"
        },
        "link_loan": {
            "linked_loans": "已关联的借款",
            "repayment_amount": "还款金额"
        },
        "save": {
            "save_status": "保存状态",
            "ready_to_submit": "是否可以提交"
        }
    }
```

### 2.4 报销提交工具（ReimbursementSubmissionTool）

**功能描述**：执行报销单的验证和提交

```python
class ReimbursementSubmissionTool:
    name = "submit_reimbursement"
    description = "验证报销单的完整性和合规性，然后提交审批"
    
    parameters = {
        "type": "object",
        "properties": {
            "bill_id": {
                "type": "string",
                "description": "报销单ID"
            },
            "validate_only": {
                "type": "boolean",
                "default": False,
                "description": "是否只验证不提交"
            }
        },
        "required": ["bill_id"]
    }
    
    returns = {
        "validation_result": {
            "overall_status": "pass/fail",
            "budget_check": "预算检查结果",
            "invoice_check": "发票一致性检查结果",
            "compliance_check": "合规性检查结果",
            "attachment_check": "附件完整性检查结果"
        },
        "submission_result": {
            "submit_status": "提交状态",
            "workflow_id": "流程ID",
            "next_approvers": "下一步审批人",
            "paper_required": "是否需要提交纸质单据"
        }
    }
```

### 2.5 状态查询工具（StatusQueryTool）

**功能描述**：查询各种状态信息

```python
class StatusQueryTool:
    name = "query_status"
    description = "查询用户权限、报销单状态、审批进度、支付状态等信息"
    
    parameters = {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "enum": ["permission", "bill_list", "approval", "payment"],
                "description": "查询类型"
            },
            "user_id": {
                "type": "string",
                "description": "用户ID"
            },
            "bill_id": {
                "type": "string",
                "description": "报销单ID（查询特定单据时需要）"
            },
            "filters": {
                "type": "object",
                "description": "查询过滤条件"
            }
        },
        "required": ["query_type", "user_id"]
    }
    
    returns = {
        # 根据query_type返回不同结果
        "permission": {
            "has_ees_permission": "是否有EES权限",
            "need_exam": "是否需要考试",
            "exam_link": "考试链接"
        },
        "bill_list": {
            "bills": "报销单列表",
            "total_count": "总数"
        },
        "approval": {
            "current_status": "当前状态",
            "approval_history": "审批历史",
            "next_steps": "下一步"
        },
        "payment": {
            "payment_status": "支付状态",
            "payment_date": "支付日期",
            "amount": "金额"
        }
    }
```

### 2.6 差旅申请查询工具（TravelApplicationQueryTool）

**功能描述**：查询可报销的差旅申请

```python
class TravelApplicationQueryTool:
    name = "query_travel_applications"
    description = "查询用户的差旅申请单，包括可报销次数等信息"
    
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "用户ID"
            },
            "date_range": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"}
                }
            },
            "status_filter": {
                "type": "string",
                "enum": ["all", "reimbursable", "partially_reimbursed"]
            }
        },
        "required": ["user_id"]
    }
    
    returns = {
        "applications": [
            {
                "application_id": "申请单ID",
                "trip_number": "出差单号",
                "destination": "目的地",
                "start_date": "开始日期",
                "end_date": "结束日期",
                "purpose": "出差事由",
                "reimbursable_times": "可报销次数",
                "reimbursed_times": "已报销次数"
            }
        ]
    }
```

### 2.7 补助处理工具（AllowanceProcessingTool）

**功能描述**：处理差旅补助相关操作

```python
class AllowanceProcessingTool:
    name = "process_allowance"
    description = "检查和申请差旅补助"
    
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["check_eligibility", "apply_manual"],
                "description": "操作类型"
            },
            "user_id": {
                "type": "string",
                "description": "用户ID"
            },
            "trip_order_id": {
                "type": "string",
                "description": "出差申请单ID"
            }
        },
        "required": ["action", "user_id", "trip_order_id"]
    }
    
    returns = {
        "check_eligibility": {
            "eligible": "是否符合条件",
            "auto_process": "是否自动处理",
            "allowance_amount": "补助金额",
            "reason": "原因说明"
        },
        "apply_manual": {
            "application_id": "申请ID",
            "status": "申请状态",
            "amount": "补助金额"
        }
    }
```

## 3. 工具与API映射关系

| 工具名称 | 功能模块 | 封装的API | API状态 | 备注 |
|---------|---------|-----------|---------|------|
| **InvoiceProcessingTool** | 发票上传 | `/fssc/ocr/expenseClaim/expenseRecordInvoice/invoiceUploadMultOcr` | ✅ 已有 | |
| | 发票修正 | `/fssc/invoice/updateOCRResult` | ❌ 缺失 | 需要新增 |
| | 发票验证 | `/fssc/ocr/expenseClaim/expenseRecordInvoice/saveBoDataAndInspection` | ✅ 已有 | |
| | 影像验签 | `/fssc/image/verifySignature` | ❌ 缺失 | 需要新增 |
| | 税务验真 | `/fssc/tax/verifyInvoice` | ❌ 缺失 | 需要新增 |
| **ExpenseRecordManagementTool** | 类型映射 | `/fssc/bill/BillDimensionMapping/getExpenseTypeInvoiceItemDimList` | ✅ 已有 | |
| | 类型查询 | `/fssc/controlStandard/expenseTypeDim/getAllExpenseTypeTree` | ✅ 已有 | |
| | 记录创建 | `/fssc/expenseClaim/expenseRecordRuleExecute/ruleExecute` | ✅ 已有 | |
| | 发票关联 | `/fssc/expenseClaim/expenseRecordRuleExecute/addInvoiceExecute` | ✅ 已有 | |
| | 字段规则 | `/fssc/controlStandard/expenseTypeField/getExpenseTypeFieldListAndRule` | ✅ 已有 | |
| | 记录更新 | `/fssc/expenseRecord/updateFields` | ❌ 缺失 | 需要新增 |
| | 标准验证 | `/fssc/controlStandard/controlStandardValue/standardCheck` | ✅ 已有 | |
| **ReimbursementManagementTool** | 单据类型 | `/fssc/bill/define/getExpenseRecordBillDefineList` | ✅ 已有 | |
| | 权限检查 | `/fssc/bill/billDefine/checkReimburseBillExpensePermission` | ✅ 已有 | |
| | 创建单据 | `/fssc/expenseClaim/billData/createBillDataAndTemplateByExpenseIdList` | ✅ 已有 | |
| | 差旅归集 | `/fssc/newTravelController/collectNewTravelInfo` | ✅ 已有 | |
| | 借款查询 | `/fssc/billDataExcel/debtBill/countUnFinishDebitBill` | ✅ 已有 | |
| | 借款详情 | `/fssc/bill/getUnrepairedLoanInfoByApplicantId` | ✅ 已有 | |
| | 字段联动 | `/fssc/expenseClaim/billChangeButterflyEffect/fieldValueChange` | ✅ 已有 | |
| | 保存单据 | `/fssc/bill/billDataOverride/saveBillData` | ✅ 已有 | |
| **ReimbursementSubmissionTool** | 预算查询 | `/fssc/api/budget/queryBudget` | ✅ 已有 | |
| | 差旅验证 | `/fssc/billTravelExpense/verifyNewTravelExpense` | ✅ 已有 | |
| | 附件检查 | `/fssc/xiaoWeiController/checkTravelAndFileReason` | ✅ 已有 | |
| | 规则执行 | `/fssc/bill/billRuleExecute/executeRuleList` | ✅ 已有 | |
| | 提交审批 | `/fssc/flow/runtime/executeWork` | ✅ 已有 | |
| | 纸质检查 | `/fssc/bill/checkPaperRequirement` | ❌ 缺失 | 需要新增 |
| | 封面生成 | `/fssc/bill/generateCoverSheet` | ❌ 缺失 | 需要新增 |
| **StatusQueryTool** | 用户查询 | `/fssc/dim/dimObject/queryUserOfFullUserList` | ✅ 已有 | |
| | 权限检查 | `/fssc/permission/checkEESAccess` | ❌ 缺失 | 需要新增 |
| | 考试链接 | `/fssc/exam/getExamLink` | ❌ 缺失 | 需要新增 |
| | 单据查询 | `/fssc/myBill/getAuditBillListBySearchVO` | ✅ 已有 | |
| | 支付查询 | `/fssc/payment/queryStatus` | ❌ 缺失 | 需要新增 |
| **TravelApplicationQueryTool** | 申请查询 | `/fssc/newTravelController/queryNewTravelPageInfo` | ✅ 已有 | |
| | 报销次数 | `/fssc/newTravelController/queryReimburseNumByTripOrder` | ✅ 已有 | |
| | 维度查询 | `/fssc/travel/getReimburseNumByDim` | ✅ 已有 | |
| **AllowanceProcessingTool** | 资格检查 | `/fssc/allowance/checkAutoEligibility` | ❌ 缺失 | 需要新增 |
| | 行程确认 | `/fssc/travel/confirmTrip` | ❌ 缺失 | 需要新增 |
| | 手动申请 | `/fssc/allowance/manualApply` | ❌ 缺失 | 需要新增 |

## 4. API状态统计

### 4.1 总体统计
- **API总数**：37个
- **已有API**：25个（67.6%）
- **缺失API**：12个（32.4%）

### 4.2 缺失API优先级

#### 高优先级（影响核心流程）
1. `/fssc/permission/checkEESAccess` - EES权限检查
2. `/fssc/invoice/updateOCRResult` - OCR结果修正
3. `/fssc/expenseRecord/updateFields` - 更新支出记录
4. `/fssc/payment/queryStatus` - 支付状态查询

#### 中优先级（影响用户体验）
1. `/fssc/image/verifySignature` - 影像系统验签
2. `/fssc/tax/verifyInvoice` - 税务系统验真
3. `/fssc/bill/checkPaperRequirement` - 纸质单据检查
4. `/fssc/bill/generateCoverSheet` - 封面生成

#### 低优先级（辅助功能）
1. `/fssc/exam/getExamLink` - 考试链接获取
2. `/fssc/allowance/checkAutoEligibility` - 自动补助检查
3. `/fssc/travel/confirmTrip` - 行程确认
4. `/fssc/allowance/manualApply` - 手动申请补助
