"""
评测数据集实体

定义评测数据集的核心业务实体。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity


@dataclass
class EvaluationDataset(BaseEntity):
    """评测数据集实体

    评测数据集包含一组测试用例，用于评估Agent的性能。

    Attributes:
        name: 数据集名称
        description: 数据集描述
        agent_id: 关联的Agent标识
        test_cases: 测试用例列表
        metrics: 评测指标列表
        tags: 标签列表
        metadata: 扩展元数据
    """

    name: str = ""
    description: str = ""
    agent_id: str = ""
    test_cases: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_test_case(self, test_case: dict[str, Any], operator: Optional[str] = None) -> None:
        """添加测试用例

        Args:
            test_case: 测试用例数据
            operator: 操作者标识
        """
        self.test_cases.append(test_case)
        self.touch(operator)

    def remove_test_case(self, index: int, operator: Optional[str] = None) -> None:
        """移除测试用例

        Args:
            index: 测试用例索引
            operator: 操作者标识
        """
        if 0 <= index < len(self.test_cases):
            self.test_cases.pop(index)
            self.touch(operator)

    def get_test_case_count(self) -> int:
        """获取测试用例数量

        Returns:
            测试用例数量
        """
        return len(self.test_cases)
