"""
成本中心枚举定义

定义成本类型和预算状态等枚举。
"""

from enum import Enum


class CostType(str, Enum):
    """成本类型枚举"""

    LLM_TOKEN = "llm_token"
    """LLM Token消耗"""

    API_CALL = "api_call"
    """API调用"""

    STORAGE = "storage"
    """存储"""

    COMPUTE = "compute"
    """计算资源"""

    NETWORK = "network"
    """网络流量"""


class BudgetStatus(str, Enum):
    """预算状态枚举"""

    ACTIVE = "active"
    """激活状态"""

    EXCEEDED = "exceeded"
    """已超出"""

    SUSPENDED = "suspended"
    """已暂停"""


class QuotaStatus(str, Enum):
    """配额状态枚举"""

    ACTIVE = "active"
    """激活状态"""

    EXCEEDED = "exceeded"
    """已超出"""

    SUSPENDED = "suspended"
    """已暂停"""


class AlertSeverity(str, Enum):
    """告警严重级别枚举"""

    INFO = "info"
    """信息"""

    WARNING = "warning"
    """警告"""

    CRITICAL = "critical"
    """严重"""
