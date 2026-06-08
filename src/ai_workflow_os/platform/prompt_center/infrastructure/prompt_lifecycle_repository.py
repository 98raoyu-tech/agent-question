"""
Prompt生命周期仓储实现

提供Prompt生命周期实体（实验、基准测试、审批、发布、回滚）的内存存储实现。
"""

import logging

from ..domain.prompt_approval import PromptApproval
from ..domain.prompt_benchmark import PromptBenchmark
from ..domain.prompt_experiment import PromptExperiment
from ..domain.prompt_release import PromptRelease
from ..domain.prompt_rollback import PromptRollback

logger = logging.getLogger(__name__)


class PromptLifecycleRepository:
    """Prompt生命周期仓储实现

    基于内存字典的仓储实现，用于开发和测试阶段。

    TODO: 后续替换为数据库实现（如PostgreSQL + SQLAlchemy）
    """

    def __init__(self) -> None:
        """初始化内存存储"""
        self._experiments: dict[str, PromptExperiment] = {}
        self._benchmarks: dict[str, PromptBenchmark] = {}
        self._approvals: dict[str, PromptApproval] = {}
        self._releases: dict[str, PromptRelease] = {}
        self._rollbacks: dict[str, PromptRollback] = {}

    async def save_experiment(self, experiment: PromptExperiment) -> PromptExperiment:
        """保存实验

        Args:
            experiment: 实验实体

        Returns:
            保存后的实验实体
        """
        self._experiments[experiment.id] = experiment
        return experiment

    async def find_experiment_by_id(self, experiment_id: str) -> PromptExperiment | None:
        """根据ID查找实验

        Args:
            experiment_id: 实验标识

        Returns:
            实验实体，未找到返回None
        """
        experiment = self._experiments.get(experiment_id)
        if experiment is not None and experiment.is_deleted:
            return None
        return experiment

    async def find_experiments_by_prompt_id(
        self,
        prompt_id: str,
    ) -> list[PromptExperiment]:
        """根据Prompt ID查找所有实验

        Args:
            prompt_id: Prompt模板标识

        Returns:
            实验列表
        """
        return [
            e for e in self._experiments.values()
            if e.prompt_id == prompt_id and not e.is_deleted
        ]

    async def save_benchmark(self, benchmark: PromptBenchmark) -> PromptBenchmark:
        """保存基准测试

        Args:
            benchmark: 基准测试实体

        Returns:
            保存后的基准测试实体
        """
        self._benchmarks[benchmark.id] = benchmark
        return benchmark

    async def find_benchmark_by_id(self, benchmark_id: str) -> PromptBenchmark | None:
        """根据ID查找基准测试

        Args:
            benchmark_id: 基准测试标识

        Returns:
            基准测试实体，未找到返回None
        """
        benchmark = self._benchmarks.get(benchmark_id)
        if benchmark is not None and benchmark.is_deleted:
            return None
        return benchmark

    async def find_benchmarks_by_prompt_id(
        self,
        prompt_id: str,
    ) -> list[PromptBenchmark]:
        """根据Prompt ID查找所有基准测试

        Args:
            prompt_id: Prompt模板标识

        Returns:
            基准测试列表
        """
        return [
            b for b in self._benchmarks.values()
            if b.prompt_id == prompt_id and not b.is_deleted
        ]

    async def save_approval(self, approval: PromptApproval) -> PromptApproval:
        """保存审批

        Args:
            approval: 审批实体

        Returns:
            保存后的审批实体
        """
        self._approvals[approval.id] = approval
        return approval

    async def find_approval_by_id(self, approval_id: str) -> PromptApproval | None:
        """根据ID查找审批

        Args:
            approval_id: 审批标识

        Returns:
            审批实体，未找到返回None
        """
        approval = self._approvals.get(approval_id)
        if approval is not None and approval.is_deleted:
            return None
        return approval

    async def find_approvals_by_prompt_id(
        self,
        prompt_id: str,
    ) -> list[PromptApproval]:
        """根据Prompt ID查找所有审批

        Args:
            prompt_id: Prompt模板标识

        Returns:
            审批列表
        """
        return [
            a for a in self._approvals.values()
            if a.prompt_id == prompt_id and not a.is_deleted
        ]

    async def save_release(self, release: PromptRelease) -> PromptRelease:
        """保存发布

        Args:
            release: 发布实体

        Returns:
            保存后的发布实体
        """
        self._releases[release.id] = release
        return release

    async def find_release_by_id(self, release_id: str) -> PromptRelease | None:
        """根据ID查找发布

        Args:
            release_id: 发布标识

        Returns:
            发布实体，未找到返回None
        """
        release = self._releases.get(release_id)
        if release is not None and release.is_deleted:
            return None
        return release

    async def find_releases_by_prompt_id(
        self,
        prompt_id: str,
    ) -> list[PromptRelease]:
        """根据Prompt ID查找所有发布

        Args:
            prompt_id: Prompt模板标识

        Returns:
            发布列表
        """
        return [
            r for r in self._releases.values()
            if r.prompt_id == prompt_id and not r.is_deleted
        ]

    async def save_rollback(self, rollback: PromptRollback) -> PromptRollback:
        """保存回滚

        Args:
            rollback: 回滚实体

        Returns:
            保存后的回滚实体
        """
        self._rollbacks[rollback.id] = rollback
        return rollback

    async def find_rollback_by_id(self, rollback_id: str) -> PromptRollback | None:
        """根据ID查找回滚

        Args:
            rollback_id: 回滚标识

        Returns:
            回滚实体，未找到返回None
        """
        rollback = self._rollbacks.get(rollback_id)
        if rollback is not None and rollback.is_deleted:
            return None
        return rollback

    async def find_rollbacks_by_prompt_id(
        self,
        prompt_id: str,
    ) -> list[PromptRollback]:
        """根据Prompt ID查找所有回滚

        Args:
            prompt_id: Prompt模板标识

        Returns:
            回滚列表
        """
        return [
            r for r in self._rollbacks.values()
            if r.prompt_id == prompt_id and not r.is_deleted
        ]
