"""
Prompt生命周期服务

提供Prompt模板的实验、基准测试、审批和发布的完整生命周期管理。
"""

import logging
from collections.abc import Callable, Coroutine
from datetime import UTC
from typing import Any

from ...common.exceptions import ResourceNotFoundException, ValidationException
from ..domain.prompt_approval import PromptApproval
from ..domain.prompt_benchmark import PromptBenchmark
from ..domain.prompt_experiment import PromptExperiment
from ..domain.prompt_release import PromptRelease
from ..domain.prompt_rollback import PromptRollback
from ..infrastructure.prompt_lifecycle_repository import PromptLifecycleRepository

logger = logging.getLogger(__name__)


class PromptLifecycleService:
    """Prompt生命周期服务

    管理Prompt模板的实验、基准测试、审批和发布的完整生命周期。

    Attributes:
        repository: 生命周期仓储实例
    """

    def __init__(self, repository: PromptLifecycleRepository) -> None:
        """初始化生命周期服务

        Args:
            repository: 生命周期仓储实例
        """
        self.repository = repository

    async def create_experiment(
        self,
        prompt_id: str,
        variant_a_id: str,
        variant_b_id: str,
        traffic_split: float = 0.5,
        experiment_name: str = "",
        sample_size: int = 1000,
        operator: str | None = None,
    ) -> PromptExperiment:
        """创建实验

        Args:
            prompt_id: Prompt模板标识
            variant_a_id: 变体A版本标识
            variant_b_id: 变体B版本标识
            traffic_split: 变体A流量比例
            experiment_name: 实验名称
            sample_size: 样本大小
            operator: 操作者标识

        Returns:
            创建的实验实体

        Raises:
            ValidationException: 参数验证失败
        """
        if not prompt_id or not prompt_id.strip():
            raise ValidationException(message="Prompt模板标识不能为空")

        if not variant_a_id or not variant_a_id.strip():
            raise ValidationException(message="变体A版本标识不能为空")

        if not variant_b_id or not variant_b_id.strip():
            raise ValidationException(message="变体B版本标识不能为空")

        if not 0 <= traffic_split <= 1:
            raise ValidationException(message="流量分割比例必须在0到1之间")

        experiment = PromptExperiment(
            prompt_id=prompt_id,
            experiment_name=experiment_name,
            variant_a_version_id=variant_a_id,
            variant_b_version_id=variant_b_id,
            traffic_split=traffic_split,
            sample_size=sample_size,
        )
        experiment.created_by = operator
        experiment.updated_by = operator

        saved = await self.repository.save_experiment(experiment)
        logger.info(
            "实验创建成功: id=%s, prompt_id=%s, name=%s",
            saved.id,
            prompt_id,
            experiment_name,
        )

        return saved

    async def start_experiment(
        self,
        experiment_id: str,
        operator: str | None = None,
    ) -> PromptExperiment:
        """启动实验

        Args:
            experiment_id: 实验标识
            operator: 操作者标识

        Returns:
            更新后的实验实体

        Raises:
            ResourceNotFoundException: 实验不存在
        """
        experiment = await self.repository.find_experiment_by_id(experiment_id)
        if experiment is None:
            raise ResourceNotFoundException(resource_type="实验", resource_id=experiment_id)

        experiment.start(operator)
        saved = await self.repository.save_experiment(experiment)
        logger.info("实验启动成功: id=%s", experiment_id)

        return saved

    async def complete_experiment(
        self,
        experiment_id: str,
        winner_id: str,
        operator: str | None = None,
    ) -> PromptExperiment:
        """完成实验

        Args:
            experiment_id: 实验标识
            winner_id: 获胜版本标识
            operator: 操作者标识

        Returns:
            更新后的实验实体

        Raises:
            ResourceNotFoundException: 实验不存在
        """
        experiment = await self.repository.find_experiment_by_id(experiment_id)
        if experiment is None:
            raise ResourceNotFoundException(resource_type="实验", resource_id=experiment_id)

        experiment.complete(winner_id, operator)
        saved = await self.repository.save_experiment(experiment)
        logger.info("实验完成成功: id=%s, winner=%s", experiment_id, winner_id)

        return saved

    async def run_benchmark(
        self,
        prompt_id: str,
        version_id: str,
        benchmark_name: str,
        test_cases: list[dict[str, Any]],
        test_executor: Callable[..., Coroutine[Any, Any, list[dict[str, Any]]]] | None = None,
        operator: str | None = None,
    ) -> PromptBenchmark:
        """运行基准测试

        Args:
            prompt_id: Prompt模板标识
            version_id: 版本标识
            benchmark_name: 基准测试名称
            test_cases: 测试用例列表
            test_executor: 测试执行器
            operator: 操作者标识

        Returns:
            创建的基准测试实体

        Raises:
            ValidationException: 参数验证失败
        """
        if not prompt_id or not prompt_id.strip():
            raise ValidationException(message="Prompt模板标识不能为空")

        if not version_id or not version_id.strip():
            raise ValidationException(message="版本标识不能为空")

        if not test_cases:
            raise ValidationException(message="测试用例不能为空")

        benchmark = PromptBenchmark(
            prompt_id=prompt_id,
            version_id=version_id,
            benchmark_name=benchmark_name,
            test_cases=test_cases,
        )
        benchmark.created_by = operator
        benchmark.updated_by = operator

        saved = await self.repository.save_benchmark(benchmark)
        logger.info(
            "基准测试创建成功: id=%s, prompt_id=%s, name=%s",
            saved.id,
            prompt_id,
            benchmark_name,
        )

        if test_executor is not None:
            try:
                await saved.run(test_executor, operator)
                saved = await self.repository.save_benchmark(saved)
                logger.info("基准测试运行完成: id=%s", saved.id)
            except Exception as error:
                logger.error("基准测试运行失败: id=%s, error=%s", saved.id, str(error))
                raise

        return saved

    async def submit_approval(
        self,
        prompt_id: str,
        version_id: str,
        operator: str | None = None,
    ) -> PromptApproval:
        """提交审批申请

        Args:
            prompt_id: Prompt模板标识
            version_id: 版本标识
            operator: 操作者标识

        Returns:
            创建的审批实体

        Raises:
            ValidationException: 参数验证失败
        """
        from datetime import datetime

        if not prompt_id or not prompt_id.strip():
            raise ValidationException(message="Prompt模板标识不能为空")

        if not version_id or not version_id.strip():
            raise ValidationException(message="版本标识不能为空")

        approval = PromptApproval(
            prompt_id=prompt_id,
            version_id=version_id,
            requested_by=operator or "",
            requested_at=datetime.now(UTC),
        )
        approval.created_by = operator
        approval.updated_by = operator

        saved = await self.repository.save_approval(approval)
        logger.info(
            "审批申请提交成功: id=%s, prompt_id=%s, version_id=%s",
            saved.id,
            prompt_id,
            version_id,
        )

        return saved

    async def approve_version(
        self,
        approval_id: str,
        approver: str,
        notes: str | None = None,
        operator: str | None = None,
    ) -> PromptApproval:
        """批准版本

        Args:
            approval_id: 审批标识
            approver: 审批人标识
            notes: 审批备注
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 审批不存在
        """
        approval = await self.repository.find_approval_by_id(approval_id)
        if approval is None:
            raise ResourceNotFoundException(resource_type="审批", resource_id=approval_id)

        approval.approve(approver, notes, operator)
        saved = await self.repository.save_approval(approval)
        logger.info("版本批准成功: id=%s, approver=%s", approval_id, approver)

        return saved

    async def reject_version(
        self,
        approval_id: str,
        approver: str,
        reason: str,
        operator: str | None = None,
    ) -> PromptApproval:
        """拒绝版本

        Args:
            approval_id: 审批标识
            approver: 审批人标识
            reason: 拒绝原因
            operator: 操作者标识

        Returns:
            更新后的审批实体

        Raises:
            ResourceNotFoundException: 审批不存在
        """
        approval = await self.repository.find_approval_by_id(approval_id)
        if approval is None:
            raise ResourceNotFoundException(resource_type="审批", resource_id=approval_id)

        approval.reject(approver, reason, operator)
        saved = await self.repository.save_approval(approval)
        logger.info("版本拒绝成功: id=%s, approver=%s", approval_id, approver)

        return saved

    async def release_version(
        self,
        prompt_id: str,
        version_id: str,
        release_name: str,
        environment: str,
        release_notes: str = "",
        operator: str | None = None,
    ) -> PromptRelease:
        """发布版本

        Args:
            prompt_id: Prompt模板标识
            version_id: 版本标识
            release_name: 发布名称
            environment: 部署环境
            release_notes: 发布说明
            operator: 操作者标识

        Returns:
            创建的发布实体

        Raises:
            ValidationException: 参数验证失败
        """
        if not prompt_id or not prompt_id.strip():
            raise ValidationException(message="Prompt模板标识不能为空")

        if not version_id or not version_id.strip():
            raise ValidationException(message="版本标识不能为空")

        if not release_name or not release_name.strip():
            raise ValidationException(message="发布名称不能为空")

        if not environment or not environment.strip():
            raise ValidationException(message="部署环境不能为空")

        release = PromptRelease(
            prompt_id=prompt_id,
            version_id=version_id,
            release_name=release_name,
            release_notes=release_notes,
            environment=environment,
        )
        release.created_by = operator
        release.updated_by = operator

        release.deploy(operator)
        saved = await self.repository.save_release(release)
        logger.info(
            "版本发布成功: id=%s, prompt_id=%s, version_id=%s, env=%s",
            saved.id,
            prompt_id,
            version_id,
            environment,
        )

        return saved

    async def rollback_release(
        self,
        release_id: str,
        to_version_id: str,
        reason: str,
        operator: str | None = None,
    ) -> PromptRollback:
        """回滚发布

        Args:
            release_id: 发布标识
            to_version_id: 目标版本标识
            reason: 回滚原因
            operator: 操作者标识

        Returns:
            创建的回滚实体

        Raises:
            ResourceNotFoundException: 发布不存在
            ValidationException: 参数验证失败
        """
        release = await self.repository.find_release_by_id(release_id)
        if release is None:
            raise ResourceNotFoundException(resource_type="发布", resource_id=release_id)

        if not reason or not reason.strip():
            raise ValidationException(message="回滚原因不能为空")

        release.rollback(operator)
        await self.repository.save_release(release)

        rollback = PromptRollback(
            prompt_id=release.prompt_id,
            from_version_id=release.version_id,
            to_version_id=to_version_id,
            reason=reason,
            initiated_by=operator or "",
        )
        rollback.created_by = operator
        rollback.updated_by = operator

        rollback.start(operator)
        rollback.complete(operator)
        saved = await self.repository.save_rollback(rollback)
        logger.info(
            "版本回滚成功: id=%s, from=%s, to=%s",
            saved.id,
            release.version_id,
            to_version_id,
        )

        return saved

    async def get_experiments(self, prompt_id: str) -> list[PromptExperiment]:
        """获取Prompt的所有实验

        Args:
            prompt_id: Prompt模板标识

        Returns:
            实验列表
        """
        return await self.repository.find_experiments_by_prompt_id(prompt_id)

    async def get_benchmarks(self, prompt_id: str) -> list[PromptBenchmark]:
        """获取Prompt的所有基准测试

        Args:
            prompt_id: Prompt模板标识

        Returns:
            基准测试列表
        """
        return await self.repository.find_benchmarks_by_prompt_id(prompt_id)

    async def get_approvals(self, prompt_id: str) -> list[PromptApproval]:
        """获取Prompt的所有审批

        Args:
            prompt_id: Prompt模板标识

        Returns:
            审批列表
        """
        return await self.repository.find_approvals_by_prompt_id(prompt_id)

    async def get_releases(self, prompt_id: str) -> list[PromptRelease]:
        """获取Prompt的所有发布

        Args:
            prompt_id: Prompt模板标识

        Returns:
            发布列表
        """
        return await self.repository.find_releases_by_prompt_id(prompt_id)
