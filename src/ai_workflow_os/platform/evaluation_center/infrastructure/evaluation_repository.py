"""
评估仓储实现

提供评测数据集和运行实体的内存存储实现。
"""

import logging
from typing import Optional

from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.evaluation_dataset import EvaluationDataset
from ..domain.evaluation_run import EvaluationRun
from ..domain.evaluation_score import EvaluationScore

logger = logging.getLogger(__name__)


class EvaluationRepository:
    """评估仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._datasets: dict[str, EvaluationDataset] = {}
        self._runs: dict[str, EvaluationRun] = {}
        self._scores: dict[str, EvaluationScore] = {}

    # =========================================================================
    # 数据集操作
    # =========================================================================

    async def find_dataset_by_id(self, dataset_id: str) -> Optional[EvaluationDataset]:
        """根据ID查找数据集

        Args:
            dataset_id: 数据集标识

        Returns:
            数据集实体，未找到返回None
        """
        dataset = self._datasets.get(dataset_id)
        if dataset is not None and dataset.is_deleted:
            return None
        return dataset

    async def find_all_datasets(
        self,
        pagination: PaginatedRequest,
        tenant_id: Optional[str] = None,
    ) -> PaginatedResponse[EvaluationDataset]:
        """分页查询数据集列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        datasets = [d for d in self._datasets.values() if not d.is_deleted]

        if tenant_id is not None:
            datasets = [d for d in datasets if d.tenant_id == tenant_id]

        datasets.sort(key=lambda d: d.created_at, reverse=True)

        total = len(datasets)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = datasets[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_dataset(self, dataset: EvaluationDataset) -> EvaluationDataset:
        """保存数据集

        Args:
            dataset: 数据集实体

        Returns:
            保存后的数据集实体
        """
        self._datasets[dataset.id] = dataset
        return dataset

    # =========================================================================
    # 运行操作
    # =========================================================================

    async def find_run_by_id(self, run_id: str) -> Optional[EvaluationRun]:
        """根据ID查找运行

        Args:
            run_id: 运行标识

        Returns:
            运行实体，未找到返回None
        """
        return self._runs.get(run_id)

    async def find_runs(
        self,
        dataset_id: Optional[str],
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[EvaluationRun]:
        """查询运行列表

        Args:
            dataset_id: 数据集标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        runs = list(self._runs.values())

        if dataset_id is not None:
            runs = [r for r in runs if r.dataset_id == dataset_id]

        runs.sort(key=lambda r: r.created_at, reverse=True)

        total = len(runs)
        start = pagination.offset
        end = start + pagination.page_size
        page_items = runs[start:end]

        return PaginatedResponse.create(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def save_run(self, run: EvaluationRun) -> EvaluationRun:
        """保存运行

        Args:
            run: 运行实体

        Returns:
            保存后的运行实体
        """
        self._runs[run.id] = run
        return run

    # =========================================================================
    # 评分操作
    # =========================================================================

    async def save_scores(self, scores: list[EvaluationScore]) -> list[EvaluationScore]:
        """批量保存评分

        Args:
            scores: 评分列表

        Returns:
            保存后的评分列表
        """
        for score in scores:
            self._scores[score.id] = score
        return scores

    async def find_scores_by_run(self, run_id: str) -> list[EvaluationScore]:
        """查询运行下的评分列表

        Args:
            run_id: 运行标识

        Returns:
            评分列表
        """
        return [s for s in self._scores.values() if s.run_id == run_id]
