"""
治理引擎仓储实现

提供治理引擎相关实体的内存存储实现。
"""

import logging
from typing import Optional

from ..domain.compliance_record import ComplianceRecord
from ..domain.data_leakage_detection import DataLeakageDetection
from ..domain.pii_detection import PIIDetection
from ..domain.prompt_injection_detection import PromptInjectionDetection
from ..domain.risk_engine import RiskAssessment

logger = logging.getLogger(__name__)


class GovernanceEngineRepository:
    """治理引擎仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._pii_detections: dict[str, PIIDetection] = {}
        self._injection_detections: dict[str, PromptInjectionDetection] = {}
        self._leakage_detections: dict[str, DataLeakageDetection] = {}
        self._risk_assessments: dict[str, RiskAssessment] = {}
        self._compliance_records: dict[str, ComplianceRecord] = {}

    # =========================================================================
    # PII检测操作
    # =========================================================================

    async def save_pii_detection(self, detection: PIIDetection) -> PIIDetection:
        """保存PII检测记录

        Args:
            detection: PII检测实体

        Returns:
            保存后的PII检测实体
        """
        self._pii_detections[detection.id] = detection
        return detection

    async def find_pii_detections_by_target(self, target_id: str) -> list[PIIDetection]:
        """根据目标ID查询PII检测记录

        Args:
            target_id: 目标标识

        Returns:
            PII检测记录列表
        """
        return [
            d for d in self._pii_detections.values()
            if d.target_id == target_id and not d.is_deleted
        ]

    # =========================================================================
    # 注入检测操作
    # =========================================================================

    async def save_injection_detection(
        self, detection: PromptInjectionDetection,
    ) -> PromptInjectionDetection:
        """保存注入检测记录

        Args:
            detection: 注入检测实体

        Returns:
            保存后的注入检测实体
        """
        self._injection_detections[detection.id] = detection
        return detection

    async def find_injection_detections_by_target(
        self, target_id: str,
    ) -> list[PromptInjectionDetection]:
        """根据目标ID查询注入检测记录

        Args:
            target_id: 目标标识

        Returns:
            注入检测记录列表
        """
        return [
            d for d in self._injection_detections.values()
            if d.target_id == target_id and not d.is_deleted
        ]

    # =========================================================================
    # 泄露检测操作
    # =========================================================================

    async def save_leakage_detection(
        self, detection: DataLeakageDetection,
    ) -> DataLeakageDetection:
        """保存泄露检测记录

        Args:
            detection: 泄露检测实体

        Returns:
            保存后的泄露检测实体
        """
        self._leakage_detections[detection.id] = detection
        return detection

    async def find_leakage_detections_by_target(
        self, target_id: str,
    ) -> list[DataLeakageDetection]:
        """根据目标ID查询泄露检测记录

        Args:
            target_id: 目标标识

        Returns:
            泄露检测记录列表
        """
        return [
            d for d in self._leakage_detections.values()
            if d.target_id == target_id and not d.is_deleted
        ]

    # =========================================================================
    # 风险评估操作
    # =========================================================================

    async def save_risk_assessment(self, assessment: RiskAssessment) -> RiskAssessment:
        """保存风险评估记录

        Args:
            assessment: 风险评估实体

        Returns:
            保存后的风险评估实体
        """
        self._risk_assessments[assessment.id] = assessment
        return assessment

    async def find_risk_assessments_by_target(
        self, target_id: str,
    ) -> list[RiskAssessment]:
        """根据目标ID查询风险评估记录

        Args:
            target_id: 目标标识

        Returns:
            风险评估记录列表
        """
        return [
            a for a in self._risk_assessments.values()
            if a.target_id == target_id and not a.is_deleted
        ]

    # =========================================================================
    # 合规记录操作
    # =========================================================================

    async def save_compliance_record(self, record: ComplianceRecord) -> ComplianceRecord:
        """保存合规记录

        Args:
            record: 合规记录实体

        Returns:
            保存后的合规记录实体
        """
        self._compliance_records[record.id] = record
        return record

    async def find_compliance_records_by_target(
        self,
        target_id: str,
        target_type: Optional[str] = None,
    ) -> list[ComplianceRecord]:
        """根据目标ID查询合规记录

        Args:
            target_id: 目标标识
            target_type: 目标类型（可选过滤条件）

        Returns:
            合规记录列表
        """
        records = [
            r for r in self._compliance_records.values()
            if r.target_id == target_id and not r.is_deleted
        ]

        if target_type is not None:
            records = [r for r in records if r.target_type == target_type]

        return records
