"""
评估门控服务

提供质量门控的CRUD、目标评估、报告管理和发布检查等业务逻辑。
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import EvaluationTargetType, GateStatus
from ..domain.evaluation_report import EvaluationReport
from ..domain.quality_gate import QualityGate
from ..infrastructure.evaluation_gate_repository import EvaluationGateRepository

logger = logging.getLogger(__name__)


class EvaluationGateService:
    """评估门控业务服务

    提供质量门控的完整生命周期管理，包括CRUD、评估执行和发布检查。

    Attributes:
        repository: 评估门控仓储实例
    """

    def __init__(self, repository: EvaluationGateRepository) -> None:
        """初始化评估门控服务

        Args:
            repository: 评估门控仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 门控CRUD
    # =========================================================================

    async def create_gate(
        self,
        gate: QualityGate,
        operator: Optional[str] = None,
    ) -> QualityGate:
        """创建质量门控

        Args:
            gate: 门控实体
            operator: 操作者标识

        Returns:
            创建后的门控实体

        Raises:
            ValidationException: 名称为空或指标阈值无效
        """
        if not gate.name or not gate.name.strip():
            raise ValidationException(message="门控名称不能为空")

        self._validate_metrics_thresholds(gate.metrics_thresholds)

        gate.created_by = operator
        gate.updated_by = operator

        saved_gate = await self.repository.save_gate(gate)
        logger.info("质量门控创建成功: id=%s, name=%s", saved_gate.id, saved_gate.name)

        return saved_gate

    async def get_gate(self, gate_id: str) -> QualityGate:
        """获取质量门控详情

        Args:
            gate_id: 门控标识

        Returns:
            门控实体

        Raises:
            ResourceNotFoundException: 门控不存在
        """
        gate = await self.repository.find_gate_by_id(gate_id)
        if gate is None:
            raise ResourceNotFoundException(resource_type="质量门控", resource_id=gate_id)
        return gate

    async def list_gates(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[QualityGate]:
        """分页查询门控列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_gates(pagination, tenant_id)

    async def delete_gate(self, gate_id: str, operator: Optional[str] = None) -> bool:
        """删除质量门控（软删除）

        Args:
            gate_id: 门控标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 门控不存在
        """
        gate = await self.repository.find_gate_by_id(gate_id)
        if gate is None:
            raise ResourceNotFoundException(resource_type="质量门控", resource_id=gate_id)

        gate.mark_deleted(operator)
        await self.repository.save_gate(gate)
        logger.info("质量门控删除成功: id=%s", gate_id)

        return True

    # =========================================================================
    # 评估执行
    # =========================================================================

    async def evaluate_target(
        self,
        target_id: str,
        target_type: EvaluationTargetType,
        metric_scores: dict[str, float],
        operator: Optional[str] = None,
    ) -> list[EvaluationReport]:
        """对目标执行门控评估

        查找适用于目标类型的所有门控，逐一执行评估并生成报告。

        Args:
            target_id: 评估目标标识
            target_type: 评估目标类型
            metric_scores: 指标评分映射（MetricType值 -> 评分）
            operator: 操作者标识

        Returns:
            评估报告列表

        Raises:
            ValidationException: 评分数据为空
        """
        if not metric_scores:
            raise ValidationException(message="评分数据不能为空")

        applicable_gates = await self.repository.find_gates_by_target_type(target_type)

        if not applicable_gates:
            logger.info(
                "目标 [%s] 类型 [%s] 无适用门控，跳过评估",
                target_id,
                target_type.value,
            )
            return []

        reports: list[EvaluationReport] = []
        for gate in applicable_gates:
            report = await self._evaluate_single_gate(
                gate=gate,
                target_id=target_id,
                target_type=target_type,
                metric_scores=metric_scores,
                operator=operator,
            )
            reports.append(report)

        passed_count = sum(1 for r in reports if r.passed)
        logger.info(
            "目标 [%s] 评估完成: 总门控=%d, 通过=%d",
            target_id,
            len(reports),
            passed_count,
        )

        return reports

    async def get_reports_by_target(self, target_id: str) -> list[EvaluationReport]:
        """获取目标的所有评估报告

        Args:
            target_id: 评估目标标识

        Returns:
            评估报告列表
        """
        return await self.repository.find_reports_by_target(target_id)

    async def get_reports_by_gate(self, gate_id: str) -> list[EvaluationReport]:
        """获取门控的所有评估报告

        Args:
            gate_id: 门控标识

        Returns:
            评估报告列表
        """
        return await self.repository.find_reports_by_gate(gate_id)

    async def get_report_by_id(self, report_id: str) -> EvaluationReport:
        """获取评估报告详情

        Args:
            report_id: 报告标识

        Returns:
            评估报告实体

        Raises:
            ResourceNotFoundException: 报告不存在
        """
        report = await self.repository.find_report_by_id(report_id)
        if report is None:
            raise ResourceNotFoundException(resource_type="评估报告", resource_id=report_id)
        return report

    # =========================================================================
    # 门控豁免
    # =========================================================================

    async def waive_gate(
        self,
        gate_id: str,
        operator: str,
        reason: str,
    ) -> QualityGate:
        """豁免门控

        将门控状态设置为WAIVED，使其不再阻断发布。

        Args:
            gate_id: 门控标识
            operator: 操作者标识
            reason: 豁免原因

        Returns:
            更新后的门控实体

        Raises:
            ResourceNotFoundException: 门控不存在
            ValidationException: 操作者或原因为空
            BusinessRuleViolationException: 门控非阻断类型不可豁免
        """
        if not operator or not operator.strip():
            raise ValidationException(message="操作者标识不能为空")

        if not reason or not reason.strip():
            raise ValidationException(message="豁免原因不能为空")

        gate = await self.repository.find_gate_by_id(gate_id)
        if gate is None:
            raise ResourceNotFoundException(resource_type="质量门控", resource_id=gate_id)

        if not gate.is_blocking:
            raise BusinessRuleViolationException(
                rule="GATE_WAIVE_NON_BLOCKING",
                message="非阻断门控无需豁免",
            )

        gate.gate_status = GateStatus.WAIVED
        gate.metadata["waive_reason"] = reason
        gate.metadata["waived_by"] = operator
        gate.metadata["waived_at"] = datetime.now(timezone.utc).isoformat()
        gate.touch(operator)

        saved_gate = await self.repository.save_gate(gate)
        logger.info("质量门控已豁免: id=%s, operator=%s", gate_id, operator)

        return saved_gate

    # =========================================================================
    # 发布检查
    # =========================================================================

    async def check_publishable(
        self,
        target_id: str,
        target_type: EvaluationTargetType,
    ) -> bool:
        """检查目标是否可以发布

        遍历目标类型的所有阻断门控，检查是否全部通过或已豁免。

        Args:
            target_id: 评估目标标识
            target_type: 评估目标类型

        Returns:
            是否可以发布
        """
        applicable_gates = await self.repository.find_gates_by_target_type(target_type)
        blocking_gates = [g for g in applicable_gates if g.is_blocking]

        if not blocking_gates:
            return True

        target_reports = await self.repository.find_reports_by_target(target_id)
        reports_by_gate = {r.gate_id: r for r in target_reports}

        for gate in blocking_gates:
            report = reports_by_gate.get(gate.id)
            if report is None:
                logger.info(
                    "目标 [%s] 缺少门控 [%s] 的评估报告，不可发布",
                    target_id,
                    gate.id,
                )
                return False

            if report.status not in (GateStatus.PASSED, GateStatus.WAIVED):
                logger.info(
                    "目标 [%s] 门控 [%s] 状态为 [%s]，不可发布",
                    target_id,
                    gate.id,
                    report.status.value,
                )
                return False

        return True

    # =========================================================================
    # 内部方法
    # =========================================================================

    async def _evaluate_single_gate(
        self,
        gate: QualityGate,
        target_id: str,
        target_type: EvaluationTargetType,
        metric_scores: dict[str, float],
        operator: Optional[str] = None,
    ) -> EvaluationReport:
        """对单个门控执行评估

        Args:
            gate: 质量门控实体
            target_id: 评估目标标识
            target_type: 评估目标类型
            metric_scores: 指标评分映射
            operator: 操作者标识

        Returns:
            评估报告实体
        """
        gate_status = gate.evaluate(metric_scores)

        failing_metrics = gate.get_failing_metrics(metric_scores)

        report = EvaluationReport(
            target_id=target_id,
            target_type=target_type,
            gate_id=gate.id,
            gate_name=gate.name,
            status=gate_status,
            metric_scores=metric_scores,
            passed=(gate_status == GateStatus.PASSED),
            evaluated_at=datetime.now(timezone.utc),
            evaluator=operator or "auto",
            details={
                "failing_metrics": failing_metrics,
                "thresholds": gate.metrics_thresholds,
                "is_blocking": gate.is_blocking,
            },
        )

        report.calculate_overall_score()

        if failing_metrics:
            for metric_name in failing_metrics:
                threshold = gate.metrics_thresholds.get(metric_name, 0.0)
                score = metric_scores.get(metric_name, 0.0)
                report.add_recommendation(
                    f"指标 [{metric_name}] 未达标: 评分={score}, 阈值={threshold}",
                    operator,
                )

        saved_report = await self.repository.save_report(report)
        logger.info(
            "门控评估完成: gate=%s, target=%s, status=%s",
            gate.id,
            target_id,
            gate_status.value,
        )

        return saved_report

    @staticmethod
    def _validate_metrics_thresholds(thresholds: dict[str, float]) -> None:
        """校验指标阈值配置

        Args:
            thresholds: 指标阈值映射

        Raises:
            ValidationException: 阈值配置无效
        """
        for metric_name, threshold in thresholds.items():
            if not (0.0 <= threshold <= 1.0):
                raise ValidationException(
                    message=f"指标 [{metric_name}] 的阈值必须在 0.0 到 1.0 之间，当前值={threshold}"
                )
