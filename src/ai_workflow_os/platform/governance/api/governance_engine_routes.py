"""
治理引擎 FastAPI路由

提供PII检测、注入检测、数据泄露检测、风险评估和合规管理的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, status

from ...common.exceptions import PlatformException, ValidationException
from ..application.governance_engine_service import GovernanceEngineService
from ..infrastructure.governance_engine_repository import GovernanceEngineRepository
from .governance_engine_schemas import (
    AssessRiskRequest,
    ComplianceRecordListResponse,
    ComplianceRecordResponse,
    CreateComplianceRecordRequest,
    DetectionPositionResponse,
    DetectionResultResponse,
    FindingResponse,
    FullGovernanceCheckRequest,
    FullGovernanceCheckResponse,
    InjectionDetectionListResponse,
    InjectionDetectionResponse,
    LeakageDetectionListResponse,
    LeakageDetectionResponse,
    MatchedSegmentResponse,
    PIIDetectionListResponse,
    PIIDetectionResponse,
    RemediationActionResponse,
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
    RiskFactorResponse,
    ScanInjectionRequest,
    ScanLeakageRequest,
    ScanPIIRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/governance-engine", tags=["治理引擎"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_governance_engine_repository = GovernanceEngineRepository()
_governance_engine_service = GovernanceEngineService(_governance_engine_repository)


# =============================================================================
# PII检测端点
# =============================================================================


@router.post(
    "/scan/pii",
    response_model=PIIDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="PII扫描",
    description="扫描内容中的个人可识别信息(PII)",
)
async def scan_pii(request: ScanPIIRequest) -> PIIDetectionResponse:
    """扫描PII"""
    try:
        result = await _governance_engine_service.scan_for_pii(
            content=request.content,
            target_id=request.target_id,
            target_type=request.target_type,
        )
        return _to_pii_detection_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/detections/pii/{target_id}",
    response_model=PIIDetectionListResponse,
    summary="获取PII检测记录",
    description="根据目标ID获取PII检测记录列表",
)
async def get_pii_detections(target_id: str) -> PIIDetectionListResponse:
    """获取PII检测记录"""
    detections = await _governance_engine_service.get_pii_detections(target_id)

    return PIIDetectionListResponse(
        items=[_to_pii_detection_response(d) for d in detections],
        total=len(detections),
    )


# =============================================================================
# 注入检测端点
# =============================================================================


@router.post(
    "/scan/injection",
    response_model=InjectionDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="注入检测",
    description="检测提示内容是否存在Prompt注入攻击",
)
async def scan_injection(request: ScanInjectionRequest) -> InjectionDetectionResponse:
    """检测注入"""
    try:
        result = await _governance_engine_service.detect_prompt_injection(
            prompt=request.prompt,
            target_id=request.target_id,
        )
        return _to_injection_detection_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/detections/injection/{target_id}",
    response_model=InjectionDetectionListResponse,
    summary="获取注入检测记录",
    description="根据目标ID获取注入检测记录列表",
)
async def get_injection_detections(target_id: str) -> InjectionDetectionListResponse:
    """获取注入检测记录"""
    detections = await _governance_engine_service.get_injection_detections(target_id)

    return InjectionDetectionListResponse(
        items=[_to_injection_detection_response(d) for d in detections],
        total=len(detections),
    )


# =============================================================================
# 数据泄露检测端点
# =============================================================================


@router.post(
    "/scan/leakage",
    response_model=LeakageDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="数据泄露检测",
    description="检测输出内容是否存在数据泄露",
)
async def scan_leakage(request: ScanLeakageRequest) -> LeakageDetectionResponse:
    """检测数据泄露"""
    try:
        result = await _governance_engine_service.detect_data_leakage(
            source=request.source,
            output=request.output,
            target_id=request.target_id,
        )
        return _to_leakage_detection_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/detections/leakage/{target_id}",
    response_model=LeakageDetectionListResponse,
    summary="获取泄露检测记录",
    description="根据目标ID获取数据泄露检测记录列表",
)
async def get_leakage_detections(target_id: str) -> LeakageDetectionListResponse:
    """获取泄露检测记录"""
    detections = await _governance_engine_service.get_leakage_detections(target_id)

    return LeakageDetectionListResponse(
        items=[_to_leakage_detection_response(d) for d in detections],
        total=len(detections),
    )


# =============================================================================
# 风险评估端点
# =============================================================================


@router.post(
    "/risk/assess",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="风险评估",
    description="评估目标的综合风险",
)
async def assess_risk(request: AssessRiskRequest) -> RiskAssessmentResponse:
    """评估风险"""
    try:
        result = await _governance_engine_service.assess_risk(
            target_id=request.target_id,
            target_type=request.target_type,
        )
        return _to_risk_assessment_response(result)

    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/risk/{target_id}",
    response_model=RiskAssessmentListResponse,
    summary="获取风险评估记录",
    description="根据目标ID获取风险评估记录列表",
)
async def get_risk_assessments(target_id: str) -> RiskAssessmentListResponse:
    """获取风险评估记录"""
    assessments = await _governance_engine_service.get_risk_assessments(target_id)

    return RiskAssessmentListResponse(
        items=[_to_risk_assessment_response(a) for a in assessments],
        total=len(assessments),
    )


# =============================================================================
# 合规管理端点
# =============================================================================


@router.post(
    "/compliance",
    response_model=ComplianceRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建合规记录",
    description="创建新的合规检查记录",
)
async def create_compliance_record(
    request: CreateComplianceRecordRequest,
) -> ComplianceRecordResponse:
    """创建合规记录"""
    try:
        result = await _governance_engine_service.create_compliance_record(
            target_id=request.target_id,
            target_type=request.target_type,
            framework=request.framework,
        )
        return _to_compliance_record_response(result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/compliance/{target_id}",
    response_model=ComplianceRecordListResponse,
    summary="获取合规状态",
    description="根据目标ID获取合规记录列表",
)
async def get_compliance_status(target_id: str) -> ComplianceRecordListResponse:
    """获取合规状态"""
    records = await _governance_engine_service.get_compliance_status(target_id)

    return ComplianceRecordListResponse(
        items=[_to_compliance_record_response(r) for r in records],
        total=len(records),
    )


# =============================================================================
# 综合治理检查端点
# =============================================================================


@router.post(
    "/full-check",
    response_model=FullGovernanceCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="综合治理检查",
    description="运行PII检测、注入检测和风险评估的全面检查",
)
async def run_full_check(
    request: FullGovernanceCheckRequest,
) -> FullGovernanceCheckResponse:
    """运行综合治理检查"""
    try:
        result = await _governance_engine_service.run_full_governance_check(
            target_id=request.target_id,
            target_type=request.target_type,
            content=request.content,
        )
        return FullGovernanceCheckResponse(**result)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


# =============================================================================
# 辅助函数
# =============================================================================


def _to_pii_detection_response(detection) -> PIIDetectionResponse:
    """将PII检测实体转换为响应Schema"""
    return PIIDetectionResponse(
        id=detection.id,
        target_id=detection.target_id,
        target_type=detection.target_type,
        content_hash=detection.content_hash,
        detected_pii_types=detection.detected_pii_types,
        risk_level=detection.risk_level.value,
        detection_results=[
            DetectionResultResponse(
                type=r.get("type", ""),
                position=DetectionPositionResponse(
                    start=r.get("position", {}).get("start", 0),
                    end=r.get("position", {}).get("end", 0),
                ),
                confidence=r.get("confidence", 0.0),
                matched_text=r.get("matched_text", ""),
            )
            for r in detection.detection_results
        ],
        is_masked=detection.is_masked,
        masked_content=detection.masked_content,
        created_at=detection.created_at,
        updated_at=detection.updated_at,
        tenant_id=detection.tenant_id,
    )


def _to_injection_detection_response(detection) -> InjectionDetectionResponse:
    """将注入检测实体转换为响应Schema"""
    return InjectionDetectionResponse(
        id=detection.id,
        target_id=detection.target_id,
        prompt_content=detection.prompt_content,
        is_injection_detected=detection.is_injection_detected,
        injection_type=detection.injection_type,
        confidence_score=detection.confidence_score,
        detection_details=detection.detection_details,
        blocked=detection.blocked,
        mitigation_action=detection.mitigation_action,
        created_at=detection.created_at,
        updated_at=detection.updated_at,
        tenant_id=detection.tenant_id,
    )


def _to_leakage_detection_response(detection) -> LeakageDetectionResponse:
    """将泄露检测实体转换为响应Schema"""
    return LeakageDetectionResponse(
        id=detection.id,
        target_id=detection.target_id,
        target_type=detection.target_type,
        source_content=detection.source_content,
        output_content=detection.output_content,
        leakage_type=detection.leakage_type,
        confidence_score=detection.confidence_score,
        matched_segments=[
            MatchedSegmentResponse(
                source_position=s.get("source_position", {}),
                output_position=s.get("output_position", {}),
                matched_length=s.get("matched_length", 0),
                segment_text=s.get("segment_text", ""),
            )
            for s in detection.matched_segments
        ],
        is_blocked=detection.is_blocked,
        created_at=detection.created_at,
        updated_at=detection.updated_at,
        tenant_id=detection.tenant_id,
    )


def _to_risk_assessment_response(assessment) -> RiskAssessmentResponse:
    """将风险评估实体转换为响应Schema"""
    return RiskAssessmentResponse(
        id=assessment.id,
        target_id=assessment.target_id,
        target_type=assessment.target_type,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level.value,
        risk_factors=[
            RiskFactorResponse(
                factor_name=f.get("factor_name", ""),
                score=f.get("score", 0.0),
                weight=f.get("weight", 0.0),
                description=f.get("description", ""),
            )
            for f in assessment.risk_factors
        ],
        recommendations=assessment.recommendations,
        assessed_at=assessment.assessed_at,
        assessor=assessment.assessor,
        is_accepted=assessment.is_accepted,
        accepted_by=assessment.accepted_by,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        tenant_id=assessment.tenant_id,
    )


def _to_compliance_record_response(record) -> ComplianceRecordResponse:
    """将合规记录实体转换为响应Schema"""
    return ComplianceRecordResponse(
        id=record.id,
        target_id=record.target_id,
        target_type=record.target_type,
        compliance_framework=record.compliance_framework,
        status=record.status,
        findings=[
            FindingResponse(
                finding_id=f.get("finding_id", ""),
                severity=f.get("severity", ""),
                description=f.get("description", ""),
                category=f.get("category", ""),
            )
            for f in record.findings
        ],
        remediation_actions=[
            RemediationActionResponse(
                action_id=a.get("action_id", ""),
                description=a.get("description", ""),
                assignee=a.get("assignee", ""),
                due_date=a.get("due_date", ""),
                status=a.get("status", ""),
            )
            for a in record.remediation_actions
        ],
        assessed_at=record.assessed_at,
        next_review_at=record.next_review_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
        tenant_id=record.tenant_id,
    )
