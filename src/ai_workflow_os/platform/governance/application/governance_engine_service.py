"""
治理引擎业务服务

提供PII检测、注入检测、数据泄露检测、风险评估和合规管理的完整业务逻辑。
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ..domain.compliance_record import ComplianceFramework, ComplianceRecord, ComplianceStatus
from ..domain.data_leakage_detection import DataLeakageDetection, LeakageType
from ..domain.pii_detection import PIIDetection, PIIType, RiskLevel
from ..domain.prompt_injection_detection import InjectionType, PromptInjectionDetection
from ..domain.risk_engine import RiskAssessment
from ..infrastructure.governance_engine_repository import GovernanceEngineRepository

logger = logging.getLogger(__name__)

_PII_PATTERNS: dict[str, str] = {
    PIIType.EMAIL.value: r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    PIIType.PHONE.value: r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    PIIType.SSN.value: r"\b\d{3}-\d{2}-\d{4}\b",
    PIIType.CREDIT_CARD.value: r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}

_INJECTION_KEYWORDS: dict[str, list[str]] = {
    InjectionType.DIRECT.value: [
        "ignore previous instructions",
        "disregard all prior",
        "forget your instructions",
        "override system prompt",
    ],
    InjectionType.JAILBREAK.value: [
        "DAN mode",
        "jailbreak",
        "developer mode",
        "pretend you are",
    ],
    InjectionType.INDIRECT.value: [
        "embedded instruction",
        "hidden command",
        "encoded directive",
    ],
    InjectionType.CONTEXT_MANIPULATION.value: [
        "new context",
        "reset conversation",
        "clear memory",
        "start fresh",
    ],
}

_COMPLIANCE_FRAMEWORK_MAP: dict[str, ComplianceFramework] = {
    "GDPR": ComplianceFramework.GDPR,
    "SOC2": ComplianceFramework.SOC2,
    "HIPAA": ComplianceFramework.HIPAA,
    "CUSTOM": ComplianceFramework.CUSTOM,
}


class GovernanceEngineService:
    """治理引擎业务服务

    提供全面的AI治理检测和管理能力，涵盖PII检测、
    提示注入检测、数据泄露检测、风险评估和合规管理。

    Attributes:
        repository: 治理引擎仓储实例
    """

    def __init__(self, repository: GovernanceEngineRepository) -> None:
        """初始化治理引擎服务

        Args:
            repository: 治理引擎仓储实例
        """
        self.repository = repository

    # =========================================================================
    # PII检测
    # =========================================================================

    async def scan_for_pii(
        self,
        content: str,
        target_id: str,
        target_type: str,
        operator: Optional[str] = None,
    ) -> PIIDetection:
        """扫描内容中的PII信息

        使用模式匹配检测常见的PII类型，评估风险等级，
        并持久化检测结果。

        Args:
            content: 待扫描的内容
            target_id: 目标标识
            target_type: 目标类型
            operator: 操作者标识

        Returns:
            PII检测实体

        Raises:
            ValidationException: 内容为空
        """
        if not content or not content.strip():
            raise ValidationException(message="扫描内容不能为空")

        import re

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        detected_types: list[str] = []
        detection_results: list[dict[str, Any]] = []

        for pii_type, pattern in _PII_PATTERNS.items():
            for match in re.finditer(pattern, content):
                detected_types.append(pii_type)
                detection_results.append({
                    "type": pii_type,
                    "position": {
                        "start": match.start(),
                        "end": match.end(),
                    },
                    "confidence": 0.95,
                    "matched_text": match.group(),
                })

        unique_types = list(dict.fromkeys(detected_types))
        risk_level = self._assess_pii_risk_level(unique_types)

        detection = PIIDetection(
            target_id=target_id,
            target_type=target_type,
            content_hash=content_hash,
            detected_pii_types=unique_types,
            risk_level=risk_level,
            detection_results=detection_results,
        )
        detection.created_by = operator
        detection.updated_by = operator

        saved = await self.repository.save_pii_detection(detection)
        logger.info(
            "PII扫描完成: target_id=%s, types=%s, risk=%s",
            target_id, unique_types, risk_level.value,
        )

        return saved

    async def get_pii_detections(self, target_id: str) -> list[PIIDetection]:
        """获取目标的PII检测记录

        Args:
            target_id: 目标标识

        Returns:
            PII检测记录列表
        """
        return await self.repository.find_pii_detections_by_target(target_id)

    # =========================================================================
    # 提示注入检测
    # =========================================================================

    async def detect_prompt_injection(
        self,
        prompt: str,
        target_id: str,
        operator: Optional[str] = None,
    ) -> PromptInjectionDetection:
        """检测提示注入攻击

        分析提示内容是否存在注入攻击特征，评估置信度
        并记录检测结果。

        Args:
            prompt: 提示内容
            target_id: 目标标识
            operator: 操作者标识

        Returns:
            提示注入检测实体

        Raises:
            ValidationException: 提示内容为空
        """
        if not prompt or not prompt.strip():
            raise ValidationException(message="提示内容不能为空")

        prompt_lower = prompt.lower()
        best_match_type: Optional[str] = None
        best_confidence: float = 0.0
        matched_keywords: list[str] = []

        for injection_type, keywords in _INJECTION_KEYWORDS.items():
            type_matches = [kw for kw in keywords if kw.lower() in prompt_lower]
            if type_matches:
                confidence = min(0.5 + len(type_matches) * 0.15, 1.0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match_type = injection_type
                    matched_keywords = type_matches

        is_detected = best_match_type is not None
        final_type = best_match_type or InjectionType.DIRECT.value

        detection = PromptInjectionDetection(
            target_id=target_id,
            prompt_content=prompt,
            is_injection_detected=is_detected,
            injection_type=final_type,
            confidence_score=best_confidence,
            detection_details={
                "matched_keywords": matched_keywords,
                "prompt_length": len(prompt),
            },
        )
        detection.created_by = operator
        detection.updated_by = operator

        if is_detected and best_confidence >= 0.8:
            detection.block(operator)

        saved = await self.repository.save_injection_detection(detection)
        logger.info(
            "注入检测完成: target_id=%s, detected=%s, type=%s, confidence=%.2f",
            target_id, is_detected, final_type, best_confidence,
        )

        return saved

    async def get_injection_detections(
        self, target_id: str,
    ) -> list[PromptInjectionDetection]:
        """获取目标的注入检测记录

        Args:
            target_id: 目标标识

        Returns:
            注入检测记录列表
        """
        return await self.repository.find_injection_detections_by_target(target_id)

    # =========================================================================
    # 数据泄露检测
    # =========================================================================

    async def detect_data_leakage(
        self,
        source: str,
        output: str,
        target_id: str,
        operator: Optional[str] = None,
    ) -> DataLeakageDetection:
        """检测数据泄露

        比对源内容和输出内容，检测是否存在数据泄露。

        Args:
            source: 源内容（如训练数据或上下文）
            output: 输出内容（如AI生成的响应）
            target_id: 目标标识
            operator: 操作者标识

        Returns:
            数据泄露检测实体

        Raises:
            ValidationException: 输入内容为空
        """
        if not source or not source.strip():
            raise ValidationException(message="源内容不能为空")
        if not output or not output.strip():
            raise ValidationException(message="输出内容不能为空")

        matched_segments = self._find_leaked_segments(source, output)
        confidence = self._calculate_leakage_confidence(matched_segments, source, output)
        leakage_type = self._determine_leakage_type(matched_segments)

        detection = DataLeakageDetection(
            target_id=target_id,
            target_type="agent_output",
            source_content=source,
            output_content=output,
            leakage_type=leakage_type,
            confidence_score=confidence,
            matched_segments=matched_segments,
        )
        detection.created_by = operator
        detection.updated_by = operator

        if confidence >= 0.7 and matched_segments:
            detection.block(operator)

        saved = await self.repository.save_leakage_detection(detection)
        logger.info(
            "数据泄露检测完成: target_id=%s, confidence=%.2f, segments=%d",
            target_id, confidence, len(matched_segments),
        )

        return saved

    async def get_leakage_detections(
        self, target_id: str,
    ) -> list[DataLeakageDetection]:
        """获取目标的泄露检测记录

        Args:
            target_id: 目标标识

        Returns:
            泄露检测记录列表
        """
        return await self.repository.find_leakage_detections_by_target(target_id)

    # =========================================================================
    # 风险评估
    # =========================================================================

    async def assess_risk(
        self,
        target_id: str,
        target_type: str,
        operator: Optional[str] = None,
    ) -> RiskAssessment:
        """评估目标的综合风险

        汇总PII、注入和泄露检测结果，计算综合风险分数。

        Args:
            target_id: 目标标识
            target_type: 目标类型
            operator: 操作者标识

        Returns:
            风险评估实体
        """
        risk_factors: list[dict[str, Any]] = []
        recommendations: list[str] = []

        # 收集PII风险因素
        pii_records = await self.repository.find_pii_detections_by_target(target_id)
        if pii_records:
            latest_pii = max(pii_records, key=lambda p: p.updated_at)
            pii_score = self._risk_level_to_score(latest_pii.risk_level)
            risk_factors.append({
                "factor_name": "PII_DETECTION",
                "score": pii_score,
                "weight": 0.3,
                "description": f"检测到 {len(latest_pii.detected_pii_types)} 类PII数据",
            })
            if not latest_pii.is_masked:
                recommendations.append("建议对PII数据进行脱敏处理")

        # 收集注入风险因素
        injection_records = await self.repository.find_injection_detections_by_target(target_id)
        if injection_records:
            latest_injection = max(injection_records, key=lambda i: i.updated_at)
            injection_score = latest_injection.confidence_score * 100
            risk_factors.append({
                "factor_name": "INJECTION_DETECTION",
                "score": injection_score,
                "weight": 0.4,
                "description": f"注入类型: {latest_injection.injection_type}",
            })
            if not latest_injection.blocked and latest_injection.is_injection_detected:
                recommendations.append("检测到注入攻击但未阻止，建议审查并阻止")

        # 收集泄露风险因素
        leakage_records = await self.repository.find_leakage_detections_by_target(target_id)
        if leakage_records:
            latest_leakage = max(leakage_records, key=lambda l: l.updated_at)
            leakage_score = latest_leakage.confidence_score * 100
            risk_factors.append({
                "factor_name": "DATA_LEAKAGE",
                "score": leakage_score,
                "weight": 0.3,
                "description": f"泄露类型: {latest_leakage.leakage_type}",
            })
            if not latest_leakage.is_blocked:
                recommendations.append("检测到数据泄露但未阻止，建议立即处理")

        # 计算综合风险分数
        total_weight = sum(f.get("weight", 0) for f in risk_factors)
        if total_weight > 0:
            risk_score = sum(
                f.get("score", 0) * f.get("weight", 0) for f in risk_factors
            ) / total_weight
        else:
            risk_score = 0.0

        risk_score = round(risk_score, 2)
        risk_level = RiskAssessment._determine_risk_level(risk_score)

        if not recommendations:
            recommendations.append("当前风险等级可接受，建议定期复查")

        assessment = RiskAssessment(
            target_id=target_id,
            target_type=target_type,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations,
            assessor=operator or "system",
        )
        assessment.created_by = operator
        assessment.updated_by = operator

        saved = await self.repository.save_risk_assessment(assessment)
        logger.info(
            "风险评估完成: target_id=%s, score=%.2f, level=%s",
            target_id, risk_score, risk_level.value,
        )

        return saved

    async def get_risk_assessments(self, target_id: str) -> list[RiskAssessment]:
        """获取目标的风险评估记录

        Args:
            target_id: 目标标识

        Returns:
            风险评估记录列表
        """
        return await self.repository.find_risk_assessments_by_target(target_id)

    # =========================================================================
    # 合规管理
    # =========================================================================

    async def create_compliance_record(
        self,
        target_id: str,
        target_type: str,
        framework: str,
        operator: Optional[str] = None,
    ) -> ComplianceRecord:
        """创建合规记录

        Args:
            target_id: 目标标识
            target_type: 目标类型
            framework: 合规框架名称
            operator: 操作者标识

        Returns:
            合规记录实体

        Raises:
            ValidationException: 不支持的合规框架
        """
        if framework not in _COMPLIANCE_FRAMEWORK_MAP:
            raise ValidationException(
                message=f"不支持的合规框架: {framework}，"
                        f"支持的框架: {', '.join(_COMPLIANCE_FRAMEWORK_MAP.keys())}",
            )

        record = ComplianceRecord(
            target_id=target_id,
            target_type=target_type,
            compliance_framework=framework,
            status=ComplianceStatus.UNDER_REVIEW.value,
        )
        record.created_by = operator
        record.updated_by = operator

        saved = await self.repository.save_compliance_record(record)
        logger.info(
            "合规记录创建成功: target_id=%s, framework=%s",
            target_id, framework,
        )

        return saved

    async def get_compliance_status(
        self,
        target_id: str,
        target_type: Optional[str] = None,
    ) -> list[ComplianceRecord]:
        """获取目标的合规状态

        Args:
            target_id: 目标标识
            target_type: 目标类型（可选过滤条件）

        Returns:
            合规记录列表
        """
        return await self.repository.find_compliance_records_by_target(
            target_id, target_type,
        )

    # =========================================================================
    # 综合治理检查
    # =========================================================================

    async def run_full_governance_check(
        self,
        target_id: str,
        target_type: str,
        content: str,
        operator: Optional[str] = None,
    ) -> dict[str, Any]:
        """运行全面的治理检查

        依次执行PII检测、注入检测、风险评估，并汇总结果。

        Args:
            target_id: 目标标识
            target_type: 目标类型
            content: 待检查的内容
            operator: 操作者标识

        Returns:
            综合检查结果字典，包含各项检测的摘要
        """
        # PII检测
        pii_result = await self.scan_for_pii(content, target_id, target_type, operator)
        pii_summary = pii_result.get_detection_summary()

        # 注入检测
        injection_result = await self.detect_prompt_injection(content, target_id, operator)
        injection_summary = injection_result.get_risk_assessment()

        # 风险评估
        risk_result = await self.assess_risk(target_id, target_type, operator)

        overall_status = "PASS"
        if risk_result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            overall_status = "FAIL"
        elif risk_result.risk_level == RiskLevel.MEDIUM:
            overall_status = "WARNING"

        return {
            "target_id": target_id,
            "target_type": target_type,
            "overall_status": overall_status,
            "risk_score": risk_result.risk_score,
            "risk_level": risk_result.risk_level.value,
            "pii_detection": pii_summary,
            "injection_detection": injection_summary,
            "recommendations": risk_result.recommendations,
            "assessed_at": risk_result.assessed_at.isoformat(),
        }

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    @staticmethod
    def _assess_pii_risk_level(detected_types: list[str]) -> RiskLevel:
        """根据检测到的PII类型评估风险等级

        Args:
            detected_types: 检测到的PII类型列表

        Returns:
            风险等级
        """
        critical_types = {PIIType.SSN.value, PIIType.CREDIT_CARD.value}
        high_types = {PIIType.EMAIL.value, PIIType.PHONE.value}

        if any(t in critical_types for t in detected_types):
            return RiskLevel.CRITICAL
        if any(t in high_types for t in detected_types):
            return RiskLevel.HIGH
        if detected_types:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _find_leaked_segments(
        source: str, output: str,
    ) -> list[dict[str, Any]]:
        """查找输出中与源内容匹配的片段

        使用滑动窗口策略检测连续文本匹配。

        Args:
            source: 源内容
            output: 输出内容

        Returns:
            匹配片段列表
        """
        segments: list[dict[str, Any]] = []
        min_match_length = 30

        source_lower = source.lower()
        output_lower = output.lower()

        source_words = source_lower.split()
        output_words = output_lower.split()

        for win_size in range(min(len(source_words), 20), max(min_match_length // 5, 3), -1):
            for i in range(len(source_words) - win_size + 1):
                window = " ".join(source_words[i:i + win_size])
                if window in output_lower and len(window) >= min_match_length:
                    output_start = output_lower.index(window)
                    segments.append({
                        "source_position": {
                            "start": sum(len(w) + 1 for w in source_words[:i]),
                            "end": sum(len(w) + 1 for w in source_words[:i + win_size]),
                        },
                        "output_position": {
                            "start": output_start,
                            "end": output_start + len(window),
                        },
                        "matched_length": len(window),
                        "segment_text": window[:100],
                    })

        unique_segments = []
        seen_positions: set[int] = set()
        for seg in sorted(segments, key=lambda s: s["matched_length"], reverse=True):
            out_start = seg["output_position"]["start"]
            if out_start not in seen_positions:
                seen_positions.add(out_start)
                unique_segments.append(seg)

        return unique_segments

    @staticmethod
    def _calculate_leakage_confidence(
        matched_segments: list[dict[str, Any]],
        source: str,
        output: str,
    ) -> float:
        """计算泄露置信度

        根据匹配片段的长度和数量综合评估。

        Args:
            matched_segments: 匹配片段列表
            source: 源内容
            output: 输出内容

        Returns:
            置信度分数（0-1）
        """
        if not matched_segments:
            return 0.0

        total_matched = sum(s.get("matched_length", 0) for s in matched_segments)
        source_ratio = total_matched / max(len(source), 1)
        output_ratio = total_matched / max(len(output), 1)

        confidence = min((source_ratio + output_ratio) / 2 * 1.5, 1.0)
        return round(confidence, 2)

    @staticmethod
    def _determine_leakage_type(
        matched_segments: list[dict[str, Any]],
    ) -> str:
        """根据匹配片段特征推断泄露类型

        Args:
            matched_segments: 匹配片段列表

        Returns:
            泄露类型字符串
        """
        if not matched_segments:
            return LeakageType.TRAINING_DATA.value

        avg_length = sum(
            s.get("matched_length", 0) for s in matched_segments
        ) / len(matched_segments)

        if avg_length > 200:
            return LeakageType.TRAINING_DATA.value
        if avg_length > 80:
            return LeakageType.MEMORY_LEAK.value
        return LeakageType.CONTEXT_LEAK.value

    @staticmethod
    def _risk_level_to_score(level: RiskLevel) -> float:
        """将风险等级转换为数值分数

        Args:
            level: 风险等级

        Returns:
            对应的数值分数
        """
        level_score_map = {
            RiskLevel.LOW: 20.0,
            RiskLevel.MEDIUM: 50.0,
            RiskLevel.HIGH: 75.0,
            RiskLevel.CRITICAL: 95.0,
        }
        return level_score_map.get(level, 0.0)
