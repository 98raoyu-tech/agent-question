"""
知识血缘实体

定义知识版本间的血缘关系实体，追踪知识的演变过程。
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...common.base_entity import BaseEntity


@dataclass
class KnowledgeLineage(BaseEntity):
    """知识血缘实体

    记录知识版本之间的父子关系和转换详情。

    Attributes:
        source_id: 所属知识源标识
        parent_version_id: 父版本标识
        child_version_id: 子版本标识
        transformation_type: 转换类型（如 chunk_update / embedding_refresh / source_update）
        transformation_details: 转换详情
    """

    source_id: str = ""
    parent_version_id: str = ""
    child_version_id: str = ""
    transformation_type: str = ""
    transformation_details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def link(
        cls,
        parent_id: str,
        child_id: str,
        source_id: str = "",
        transformation_type: str = "",
        transformation_details: Optional[dict[str, Any]] = None,
        operator: Optional[str] = None,
    ) -> "KnowledgeLineage":
        """创建血缘关联

        建立父版本到子版本的血缘关系。

        Args:
            parent_id: 父版本标识
            child_id: 子版本标识
            source_id: 所属知识源标识
            transformation_type: 转换类型
            transformation_details: 转换详情
            operator: 操作者标识

        Returns:
            新建的血缘实体
        """
        lineage = cls(
            source_id=source_id,
            parent_version_id=parent_id,
            child_version_id=child_id,
            transformation_type=transformation_type,
            transformation_details=transformation_details or {},
        )
        lineage.created_by = operator
        lineage.updated_by = operator
        return lineage
