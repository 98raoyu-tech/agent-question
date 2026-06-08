"""
平台级异常定义

定义企业级平台的统一异常体系，所有业务异常均继承自PlatformException基类。
"""

from typing import Optional


class PlatformException(Exception):
    """平台基础异常类

    所有业务异常的基类，提供统一的异常信息格式。

    Attributes:
        message: 异常消息
        code: 异常错误码
        detail: 异常详情
        http_status: HTTP状态码
    """

    def __init__(
        self,
        message: str = "",
        code: str = "PLATFORM_ERROR",
        detail: Optional[str] = None,
        http_status: int = 500,
    ):
        self.message = message
        self.code = code
        self.detail = detail
        self.http_status = http_status
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict:
        """转换为字典格式

        Returns:
            异常信息字典
        """
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.detail:
            result["detail"] = self.detail
        return result


# =============================================================================
# 资源相关异常
# =============================================================================


class ResourceNotFoundException(PlatformException):
    """资源未找到异常"""

    def __init__(
        self,
        resource_type: str = "资源",
        resource_id: str = "",
        message: Optional[str] = None,
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        detail = f"{resource_type} [{resource_id}] 未找到" if resource_id else f"{resource_type}未找到"
        super().__init__(
            message=message or detail,
            code="RESOURCE_NOT_FOUND",
            detail=detail,
            http_status=404,
        )


class DuplicateResourceException(PlatformException):
    """资源重复异常"""

    def __init__(
        self,
        resource_type: str = "资源",
        field_name: str = "",
        field_value: str = "",
    ):
        self.resource_type = resource_type
        self.field_name = field_name
        self.field_value = field_value
        detail = f"{resource_type}已存在: {field_name}={field_value}" if field_name else f"{resource_type}已存在"
        super().__init__(
            message=detail,
            code="DUPLICATE_RESOURCE",
            detail=detail,
            http_status=409,
        )


# =============================================================================
# 验证相关异常
# =============================================================================


class ValidationException(PlatformException):
    """数据验证异常"""

    def __init__(
        self,
        message: str = "数据验证失败",
        errors: Optional[list] = None,
    ):
        self.errors = errors or []
        detail = str(errors) if errors else None
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            detail=detail,
            http_status=422,
        )


# =============================================================================
# 业务规则相关异常
# =============================================================================


class BusinessRuleViolationException(PlatformException):
    """业务规则违规异常"""

    def __init__(
        self,
        rule: str = "",
        message: str = "业务规则违规",
    ):
        self.rule = rule
        detail = f"违反业务规则 [{rule}]: {message}" if rule else message
        super().__init__(
            message=detail,
            code="BUSINESS_RULE_VIOLATION",
            detail=detail,
            http_status=400,
        )


# =============================================================================
# 并发控制相关异常
# =============================================================================


class ConcurrencyConflictException(PlatformException):
    """并发冲突异常（乐观锁冲突）"""

    def __init__(
        self,
        resource_type: str = "资源",
        resource_id: str = "",
        expected_version: int = 0,
        actual_version: int = 0,
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        detail = (
            f"{resource_type} [{resource_id}] 版本冲突: "
            f"期望版本={expected_version}, 实际版本={actual_version}"
        )
        super().__init__(
            message=detail,
            code="CONCURRENCY_CONFLICT",
            detail=detail,
            http_status=409,
        )


# =============================================================================
# 租户相关异常
# =============================================================================


class TenantAccessException(PlatformException):
    """租户访问权限异常"""

    def __init__(
        self,
        tenant_id: str = "",
        message: str = "无权访问该租户资源",
    ):
        self.tenant_id = tenant_id
        detail = f"租户 [{tenant_id}] {message}" if tenant_id else message
        super().__init__(
            message=detail,
            code="TENANT_ACCESS_DENIED",
            detail=detail,
            http_status=403,
        )
