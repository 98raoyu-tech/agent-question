"""
基础DTO类

定义数据传输对象的公共结构，用于API层与应用层之间的数据传递。
"""

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseDTO(BaseModel):
    """数据传输对象基类

    所有请求/响应DTO必须继承此类，提供统一的序列化配置。

    Attributes:
        id: 实体唯一标识（响应DTO使用）
        created_at: 创建时间（响应DTO使用）
        updated_at: 最后更新时间（响应DTO使用）
        tenant_id: 租户标识
    """

    id: Optional[str] = Field(default=None, description="实体唯一标识")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="最后更新时间")
    tenant_id: Optional[str] = Field(default=None, description="租户标识")

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
        },
    }


class CreateDTO(BaseModel):
    """创建操作DTO基类

    用于创建操作的请求数据，不包含id和审计字段。

    Attributes:
        tenant_id: 租户标识
    """

    tenant_id: Optional[str] = Field(default=None, description="租户标识")

    model_config = {"from_attributes": True}


class UpdateDTO(BaseModel):
    """更新操作DTO基类

    用于更新操作的请求数据，包含版本号用于乐观锁控制。

    Attributes:
        version: 乐观锁版本号
    """

    version: int = Field(description="乐观锁版本号，用于并发控制")

    model_config = {"from_attributes": True}
