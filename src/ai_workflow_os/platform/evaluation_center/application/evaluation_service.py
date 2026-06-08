"""
评估服务

提供评测数据集和运行的CRUD等业务逻辑。
"""

import logging
from typing import Optional

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.evaluation_dataset import EvaluationDataset
from ..domain.evaluation_run import EvaluationRun
from ..infrastructure.evaluation_repository import EvaluationRepository

logger = logging.getLogger(__name__)


class EvaluationService:
    """评估中心业务服务

    提供评测数据集和运行的完整生命周期管理。

    Attributes:
        repository: 评估仓储实例
    """

    def __init__(self, repository: EvaluationRepository) -> None:
        """初始化评估服务

        Args:
            repository: 评估仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 数据集管理
    # =========================================================================

    async def create_dataset(
        self,
        dataset: EvaluationDataset,
        operator: Optional[str] = None,
    ) -> EvaluationDataset:
        """创建评测数据集

        Args:
            dataset: 数据集实体
            operator: 操作者标识

        Returns:
            创建后的数据集实体

        Raises:
            ValidationException: 名称为空
        """
        if not dataset.name or not dataset.name.strip():
            raise ValidationException(message="数据集名称不能为空")

        dataset.created_by = operator
        dataset.updated_by = operator

        saved_dataset = await self.repository.save_dataset(dataset)
        logger.info("评测数据集创建成功: id=%s, name=%s", saved_dataset.id, saved_dataset.name)

        return saved_dataset

    async def get_dataset(self, dataset_id: str) -> EvaluationDataset:
        """获取评测数据集详情

        Args:
            dataset_id: 数据集标识

        Returns:
            数据集实体

        Raises:
            ResourceNotFoundException: 数据集不存在
        """
        dataset = await self.repository.find_dataset_by_id(dataset_id)
        if dataset is None:
            raise ResourceNotFoundException(resource_type="评测数据集", resource_id=dataset_id)
        return dataset

    async def list_datasets(
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
        return await self.repository.find_all_datasets(pagination, tenant_id)

    async def delete_dataset(self, dataset_id: str, operator: Optional[str] = None) -> bool:
        """删除数据集（软删除）

        Args:
            dataset_id: 数据集标识
            operator: 操作者标识

        Returns:
            是否删除成功

        Raises:
            ResourceNotFoundException: 数据集不存在
        """
        dataset = await self.repository.find_dataset_by_id(dataset_id)
        if dataset is None:
            raise ResourceNotFoundException(resource_type="评测数据集", resource_id=dataset_id)

        dataset.mark_deleted(operator)
        await self.repository.save_dataset(dataset)
        logger.info("评测数据集删除成功: id=%s", dataset_id)

        return True

    # =========================================================================
    # 运行管理
    # =========================================================================

    async def create_run(
        self,
        run: EvaluationRun,
        operator: Optional[str] = None,
    ) -> EvaluationRun:
        """创建评测运行

        Args:
            run: 运行实体
            operator: 操作者标识

        Returns:
            创建后的运行实体

        Raises:
            ResourceNotFoundException: 数据集不存在
        """
        # 检查数据集是否存在
        dataset = await self.repository.find_dataset_by_id(run.dataset_id)
        if dataset is None:
            raise ResourceNotFoundException(resource_type="评测数据集", resource_id=run.dataset_id)

        # 设置测试用例总数
        run.total_cases = dataset.get_test_case_count()
        run.created_by = operator
        run.updated_by = operator

        saved_run = await self.repository.save_run(run)
        logger.info("评测运行创建成功: id=%s, dataset_id=%s", saved_run.id, run.dataset_id)

        return saved_run

    async def get_run(self, run_id: str) -> EvaluationRun:
        """获取评测运行详情

        Args:
            run_id: 运行标识

        Returns:
            运行实体

        Raises:
            ResourceNotFoundException: 运行不存在
        """
        run = await self.repository.find_run_by_id(run_id)
        if run is None:
            raise ResourceNotFoundException(resource_type="评测运行", resource_id=run_id)
        return run

    async def list_runs(
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
        return await self.repository.find_runs(dataset_id, pagination)
