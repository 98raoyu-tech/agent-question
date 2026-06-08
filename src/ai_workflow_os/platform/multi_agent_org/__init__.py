"""
多智能体组织模块

提供动态多智能体协作支持：Agent注册表、发现、通信、委托和团队组建。
支持Agent注册/注销、消息传递、任务委托、团队管理和任务生命周期管理。
"""

from .api import *
from .application import *
from .domain import *
from .infrastructure import *
