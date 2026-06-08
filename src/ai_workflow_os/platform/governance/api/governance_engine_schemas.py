"""
治理引擎请求/响应Schema

定义治理引擎相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO


# =============================================================================
# PII检测Schema
# =============================================================================


class ScanPIIRequest(CreateDTO):
    """PII扫描请求"""

    content: str = Field(min_length=1, description="待扫描的内容")
    target_id: str = Field(min_length=1, description="目标标识")
    target_type: str = Field(min_length=1, description="目标类型")


class DetectionPositionResponse(BaseModel):
    """检测位置响应"""

    start: int = Field(description="起始位置")
    end: int = Field(description="结束位置")


class DetectionResultResponse(BaseModel):
    """检测结果项响应"""

    type: str = Field(description="PII类型")
    position: DetectionPositionResponse = Field(description="检测位置")
    confidence: float = Field(description="置信度")
    matched_text: str = Field(default="", description="匹配文本")


class PIIDetectionResponse(BaseDTO):
    """PII检测响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    content_hash: str = Field(description="内容哈希值")
    detected_pii_types: list[str] = Field(description="检测到的PII类型列表")
    risk_level: str = Field(description="风险等级")
    detection_results: list[DetectionResultResponse] = Field(description="检测结果列表")
    is_masked: bool = Field(description="是否已脱敏")
    masked_content: str = Field(description="脱敏后的内容")


class PIIDetectionListResponse(BaseModel):
    """PII检测列表响应"""

    items: list[PIIDetectionResponse] = Field(description="PII检测记录列表")
    total: int = Field(description="总数")


# =============================================================================
# 提示注入检测Schema
# =============================================================================


class ScanInjectionRequest(CreateDTO):
    """注入扫描请求"""

    prompt: str = Field(min_length=1, description="提示内容")
    target_id: str = Field(min_length=1, description="目标标识")


class InjectionDetectionResponse(BaseDTO):
    """注入检测响应"""

    target_id: str = Field(description="目标标识")
    prompt_content: str = Field(description="提示内容")
    is_injection_detected: bool = Field(description="是否检测到注入")
    injection_type: str = Field(description="注入类型")
    confidence_score: float = Field(description="置信度分数")
    detection_details: dict[str, Any] = Field(description="检测详情")
    blocked: bool = Field(description="是否已阻止")
    mitigation_action: str = Field(description="缓解措施")


class InjectionDetectionListResponse(BaseModel):
    """注入检测列表响应"""

    items: list[InjectionDetectionResponse] = Field(description="注入检测记录列表")
    total: int = Field(description="总数")


# =============================================================================
# 数据泄露检测Schema
# =============================================================================


class ScanLeakageRequest(CreateDTO):
    """泄露扫描请求"""

    source: str = Field(min_length=1, description="源内容")
    output: str = Field(min_length=1, description="输出内容")
    target_id: str = Field(min_length=1, description="目标标识")


class MatchedSegmentResponse(BaseModel):
    """匹配片段响应"""

    source_position: dict[str, int] = Field(description="源内容中的位置")
    output_position: dict[str, int] = Field(description="输出内容中的位置")
    matched_length: int = Field(description="匹配长度")
    segment_text: str = Field(description="片段文本")


class LeakageDetectionResponse(BaseDTO):
    """数据泄露检测响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    source_content: str = Field(description="源内容")
    output_content: str = Field(description="输出内容")
    leakage_type: str = Field(description="泄露类型")
    confidence_score: float = Field(description="置信度分数")
    matched_segments: list[MatchedSegmentResponse] = Field(description="匹配片段列表")
    is_blocked: bool = Field(description="是否已阻止")


class LeakageDetectionListResponse(BaseModel):
    """数据泄露检测列表响应"""

    items: list[LeakageDetectionResponse] = Field(description="泄露检测记录列表")
    total: int = Field(description="总数")


# =============================================================================
# 风险评估Schema
# =============================================================================


class AssessRiskRequest(CreateDTO):
    """风险评估请求"""

    target_id: str = Field(min_length=1, description="目标标识")
    target_type: str = Field(min_length=1, description="目标类型")


class RiskFactorResponse(BaseModel):
    """风险因素响应"""

    factor_name: str = Field(description="因素名称")
    score: float = Field(description="因素分数")
    weight: float = Field(description="权重")
    description: str = Field(description="因素描述")


class RiskAssessmentResponse(BaseDTO):
    """风险评估响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    risk_score: float = Field(description="风险分数")
    risk_level: str = Field(description="风险等级")
    risk_factors: list[RiskFactorResponse] = Field(description="风险因素列表")
    recommendations: list[str] = Field(description="改进建议列表")
    assessed_at: datetime = Field(description="评估时间")
    assessor: str = Field(description="评估者")
    is_accepted: bool = Field(description="是否已接受风险")
    accepted_by: Optional[str] = Field(default=None, description="风险接受者")


class RiskAssessmentListResponse(BaseModel):
    """风险评估列表响应"""

    items: list[RiskAssessmentResponse] = Field(description="风险评估记录列表")
    total: int = Field(description="总数")


# =============================================================================
# 合规记录Schema
# =============================================================================


class CreateComplianceRecordRequest(CreateDTO):
    """创建合规记录请求"""

    target_id: str = Field(min_length=1, description="目标标识")
    target_type: str = Field(min_length=1, description="目标类型")
    framework: str = Field(min_length=1, description="合规框架名称")


class FindingResponse(BaseModel):
    """合规检查发现响应"""

    finding_id: str = Field(description="发现标识")
    severity: str = Field(description="严重程度")
    description: str = Field(description="发现描述")
    category: str = Field(description="分类")


class RemediationActionResponse(BaseModel):
    """整改措施响应"""

    action_id: str = Field(description="措施标识")
    description: str = Field(description="措施描述")
    assignee: str = Field(description="负责人")
    due_date: str = Field(description="截止日期")
    status: str = Field(description="措施状态")


class ComplianceRecordResponse(BaseDTO):
    """合规记录响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    compliance_framework: str = Field(description="合规框架")
    status: str = Field(description="合规状态")
    findings: list[FindingResponse] = Field(description="检查发现列表")
    remediation_actions: list[RemediationActionResponse] = Field(description="整改措施列表")
    assessed_at: datetime = Field(description="评估时间")
    next_review_at: Optional[datetime] = Field(default=None, description="下次审查时间")


class ComplianceRecordListResponse(BaseModel):
    """合规记录列表响应"""

    items: list[ComplianceRecordResponse] = Field(description="合规记录列表")
    total: int = Field(description="总数")


# =============================================================================
# 综合治理检查Schema
# =============================================================================


class FullGovernanceCheckRequest(CreateDTO):
    """综合治理检查请求"""

    target_id: str = Field(min_length=1, description="目标标识")
    target_type: str = Field(min_length=1, description="目标类型")
    content: str = Field(min_length=1, description="待检查的内容")


class FullGovernanceCheckResponse(BaseModel):
    """综合治理检查响应"""

    target_id: str = Field(description="目标标识")
    target_type: str = Field(description="目标类型")
    overall_status: str = Field(description="整体状态")
    risk_score: float = Field(description="风险分数")
    risk_level: str = Field(description="风险等级")
    pii_detection: dict[str, Any] = Field(description="PII检测摘要")
    injection_detection: dict[str, Any] = Field(description="注入检测摘要")
    recommendations: list[str] = Field(description="改进建议")
    assessed_at: str = Field(description="评估时间")
