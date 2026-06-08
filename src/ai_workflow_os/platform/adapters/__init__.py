"""
适配器层模块

提供统一的Agent框架适配器接口，支持LangChain、LangGraph、CrewAI、AutoGen、MCP等多种框架。
"""

from .api import *
from .application import *
from .domain import *
from .infrastructure import *
