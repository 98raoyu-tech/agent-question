"""
评估门控仓储实现

提供质量门控和评估报告实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.evaluation_report import EvaluationReport
from ..domain.enums import EvaluationTargetType
from ..domain.quality_gate import QualityGate

logger = logging.getLogger(__name__)


class EvaluationGateRepository:
    """评估门控仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._gates: dict[str, QualityGate] = {}
        self._reports: dict[str, EvaluationReport] = {}

    # =========================================================================
    # 门控操作
    # =========================================================================

    async def find_gate_by_id(self, gate_id: str) -> Optional[QualityGate]:
        """根据ID查找门控

        Args:
            gate_id: 门控标识

        Returns:
            门控实体，未找到返回None
        """
        gate = self._gates.get(gate_id)
        if gate is not None and gate.is_deleted:
            return None
        return gate

    async def find_all_gates(
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
        gates = [g for g in self._gates.values() if not g.is_deleted]

        if tenant_id is not None:
            gates = [g for g in gates if g.tenant_id == tenant_id]

        gates.sort(key=lambda g: g.priority)

        total = len(gates)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = gates[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def find_gates_by_target_type(
        self,
        target_type: EvaluationTargetType,
    ) -> list[QualityGate]:
        """根据目标类型查找所有有效门控

        Args:
            target_type: 评估目标类型

        Returns:
            匹配的门控列表（按优先级排序）
        """
        gates = [
            g for g in self._gates.values()
            if not g.is_deleted and g.target_type == target_type
        ]
        gates.sort(key=lambda g: g.priority)
        return gates

    async def save_gate(self, gate: QualityGate) -> QualityGate:
        """保存门控

        Args:
            gate: 门控实体

        Returns:
            保存后的门控实体
        """
        self._gates[gate.id] = gate
        return gate

    async def delete_gate(self, gate_id: str) -> bool:
        """删除门控（从存储中移除）

        Args:
            gate_id: 门控标识

        Returns:
            是否删除成功
        """
        if gate_id in self._gates:
            del self._gates[gate_id]
            return True
        return False

    # =========================================================================
    # 报告操作
    # =========================================================================

    async def save_report(self, report: EvaluationReport) -> EvaluationReport:
        """保存评估报告

        Args:
            report: 评估报告实体

        Returns:
            保存后的评估报告实体
        """
        self._reports[report.id] = report
        return report

    async def find_report_by_id(self, report_id: str) -> Optional[EvaluationReport]:
        """根据ID查找评估报告

        Args:
            report_id: 报告标识

        Returns:
            评估报告实体，未找到返回None
        """
        return self._reports.get(report_id)

    async def find_reports_by_target(self, target_id: str) -> list[EvaluationReport]:
        """根据目标标识查找评估报告列表

        Args:
            target_id: 评估目标标识

        Returns:
            评估报告列表（按创建时间倒序）
        """
        reports = [r for r in self._reports.values() if r.target_id == target_id]
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports

    async def find_reports_by_gate(self, gate_id: str) -> list[EvaluationReport]:
        """根据门控标识查找评估报告列表

        Args:
            gate_id: 门控标识

        Returns:
            评估报告列表（按创建时间倒序）
        """
        reports = [r for r in self._reports.values() if r.gate_id == gate_id]
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports
