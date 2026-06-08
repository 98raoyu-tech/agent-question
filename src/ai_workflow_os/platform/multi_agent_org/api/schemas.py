"""
多智能体组织请求/响应Schema

定义Agent注册、消息通信、任务委托、团队管理和任务管理相关的API请求和响应数据模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ...common.base_dto import BaseDTO, CreateDTO
from ..domain.enums import (
    AgentOrgStatus,
    AgentRole,
    CommunicationType,
    MessageStatus,
    TaskStatus,
    TeamStatus,
)

# =============================================================================
# Agent注册Schema
# =============================================================================


class RegisterAgentRequest(CreateDTO):
    """注册Agent请求"""

    agent_id: str = Field(min_length=1, max_length=128, description="Agent唯一标识")
    agent_name: str = Field(min_length=1, max_length=200, description="Agent名称")
    agent_role: AgentRole = Field(description="Agent角色")
    capabilities: list[str] = Field(default_factory=list, description="Agent能力列表")
    endpoint_url: str = Field(default="", max_length=500, description="Agent通信端点")
    max_concurrent_tasks: int = Field(default=5, ge=1, description="最大并发任务数")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class AgentRegistryResponse(BaseDTO):
    """Agent注册响应"""

    agent_id: str = Field(description="Agent唯一标识")
    agent_name: str = Field(description="Agent名称")
    agent_role: AgentRole = Field(description="Agent角色")
    capabilities: list[str] = Field(description="Agent能力列表")
    status: AgentOrgStatus = Field(description="Agent组织状态")
    endpoint_url: str = Field(description="Agent通信端点")
    max_concurrent_tasks: int = Field(description="最大并发任务数")
    current_task_count: int = Field(description="当前任务数")
    metadata: dict[str, Any] = Field(description="扩展元数据")


class AgentRegistryListResponse(BaseModel):
    """Agent注册列表响应"""

    items: list[AgentRegistryResponse] = Field(description="Agent注册列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 消息通信Schema
# =============================================================================


class SendMessageRequest(CreateDTO):
    """发送消息请求"""

    sender_agent_id: str = Field(min_length=1, max_length=128, description="发送方Agent标识")
    receiver_agent_id: str = Field(min_length=1, max_length=128, description="接收方Agent标识")
    communication_type: CommunicationType = Field(description="通信类型")
    subject: str = Field(default="", max_length=500, description="消息主题")
    content: dict[str, Any] = Field(default_factory=dict, description="消息内容")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    correlation_id: Optional[str] = Field(default=None, max_length=64, description="关联ID")
    reply_to_id: Optional[str] = Field(default=None, description="回复目标消息ID")


class AgentMessageResponse(BaseDTO):
    """Agent消息响应"""

    sender_agent_id: str = Field(description="发送方Agent标识")
    receiver_agent_id: str = Field(description="接收方Agent标识")
    communication_type: CommunicationType = Field(description="通信类型")
    subject: str = Field(description="消息主题")
    content: dict[str, Any] = Field(description="消息内容")
    priority: int = Field(description="优先级")
    correlation_id: Optional[str] = Field(default=None, description="关联ID")
    status: MessageStatus = Field(description="消息状态")
    sent_at: datetime = Field(description="发送时间")
    delivered_at: Optional[datetime] = Field(default=None, description="投递时间")
    read_at: Optional[datetime] = Field(default=None, description="已读时间")
    reply_to_id: Optional[str] = Field(default=None, description="回复目标消息ID")


class AgentMessageListResponse(BaseModel):
    """Agent消息列表响应"""

    items: list[AgentMessageResponse] = Field(description="消息列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 委托Schema
# =============================================================================


class DelegateTaskRequest(CreateDTO):
    """委托任务请求"""

    delegator_agent_id: str = Field(min_length=1, max_length=128, description="委托方Agent标识")
    delegate_agent_id: str = Field(min_length=1, max_length=128, description="被委托方Agent标识")
    task_description: str = Field(min_length=1, max_length=5000, description="任务描述")
    task_context: dict[str, Any] = Field(default_factory=dict, description="任务上下文")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")


class CompleteDelegationRequest(BaseModel):
    """完成委托请求"""

    result: dict[str, Any] = Field(default_factory=dict, description="执行结果")


class AgentDelegationResponse(BaseDTO):
    """Agent委托响应"""

    delegator_agent_id: str = Field(description="委托方Agent标识")
    delegate_agent_id: str = Field(description="被委托方Agent标识")
    task_description: str = Field(description="任务描述")
    task_context: dict[str, Any] = Field(description="任务上下文")
    status: TaskStatus = Field(description="委托状态")
    delegated_at: datetime = Field(description="委托时间")
    accepted_at: Optional[datetime] = Field(default=None, description="接受时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    result: dict[str, Any] = Field(description="执行结果")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    priority: int = Field(description="优先级")


# =============================================================================
# 团队Schema
# =============================================================================


class CreateTeamRequest(CreateDTO):
    """创建团队请求"""

    name: str = Field(min_length=1, max_length=200, description="团队名称")
    description: str = Field(default="", max_length=2000, description="团队描述")
    capabilities: list[str] = Field(default_factory=list, description="团队能力列表")
    max_members: int = Field(default=20, ge=1, description="最大成员数")


class AddTeamMemberRequest(BaseModel):
    """添加团队成员请求"""

    agent_id: str = Field(min_length=1, max_length=128, description="Agent标识")
    role: AgentRole = Field(description="Agent角色")


class AgentTeamResponse(BaseDTO):
    """Agent团队响应"""

    name: str = Field(description="团队名称")
    description: str = Field(description="团队描述")
    team_status: TeamStatus = Field(description="团队状态")
    leader_agent_id: str = Field(description="团队领导Agent标识")
    member_ids: list[str] = Field(description="成员Agent标识列表")
    member_roles: dict[str, AgentRole] = Field(description="成员角色映射")
    capabilities: list[str] = Field(description="团队聚合能力列表")
    max_members: int = Field(description="最大成员数")
    active_delegation_ids: list[str] = Field(description="活跃委托标识列表")


class AgentTeamListResponse(BaseModel):
    """Agent团队列表响应"""

    items: list[AgentTeamResponse] = Field(description="团队列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")


# =============================================================================
# 任务Schema
# =============================================================================


class CreateTaskRequest(CreateDTO):
    """创建任务请求"""

    title: str = Field(min_length=1, max_length=500, description="任务标题")
    description: str = Field(default="", max_length=5000, description="任务描述")
    team_id: Optional[str] = Field(default=None, description="所属团队标识")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    context: dict[str, Any] = Field(default_factory=dict, description="任务上下文")
    parent_task_id: Optional[str] = Field(default=None, description="父任务标识")
    deadline: Optional[datetime] = Field(default=None, description="截止时间")


class AssignTaskRequest(BaseModel):
    """分配任务请求"""

    agent_id: str = Field(min_length=1, max_length=128, description="Agent标识")


class CompleteTaskRequest(BaseModel):
    """完成任务请求"""

    result: dict[str, Any] = Field(default_factory=dict, description="执行结果")


class AgentTaskResponse(BaseDTO):
    """Agent任务响应"""

    title: str = Field(description="任务标题")
    description: str = Field(description="任务描述")
    assigned_agent_id: Optional[str] = Field(default=None, description="分配的Agent标识")
    team_id: Optional[str] = Field(default=None, description="所属团队标识")
    status: TaskStatus = Field(description="任务状态")
    priority: int = Field(description="优先级")
    context: dict[str, Any] = Field(description="任务上下文")
    result: dict[str, Any] = Field(description="执行结果")
    parent_task_id: Optional[str] = Field(default=None, description="父任务标识")
    sub_task_ids: list[str] = Field(description="子任务标识列表")
    deadline: Optional[datetime] = Field(default=None, description="截止时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")
