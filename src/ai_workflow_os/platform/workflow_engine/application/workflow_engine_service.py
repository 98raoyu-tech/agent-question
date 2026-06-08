"""
工作流引擎服务

提供工作流的创建、执行、节点推进等完整业务逻辑。
"""

import logging
from typing import Any

from ...common.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
)
from ...common.pagination import PaginatedRequest, PaginatedResponse
from ..domain.enums import NodeStatus, WorkflowStatus
from ..domain.workflow_definition import WorkflowDefinition
from ..domain.workflow_execution import WorkflowExecution
from ..domain.workflow_node import WorkflowNode
from ..infrastructure.workflow_repository import WorkflowRepository

logger = logging.getLogger(__name__)


class WorkflowEngineService:
    """工作流引擎业务服务

    提供工作流定义的管理和工作流执行的完整生命周期控制。

    Attributes:
        repository: 工作流仓储实例
    """

    def __init__(self, repository: WorkflowRepository) -> None:
        """初始化工作流引擎服务

        Args:
            repository: 工作流仓储实例
        """
        self.repository = repository

    # =========================================================================
    # 工作流定义管理
    # =========================================================================

    async def create_workflow(
        self,
        definition: WorkflowDefinition,
        operator: str | None = None,
    ) -> WorkflowDefinition:
        """创建工作流定义

        Args:
            definition: 工作流定义实体
            operator: 操作者标识

        Returns:
            保存后的工作流定义
        """
        definition.created_by = operator
        definition.updated_by = operator

        # 保存工作流定义及其节点和边
        saved_definition = await self.repository.save_workflow(definition)

        if definition.nodes:
            await self.repository.save_nodes(definition.nodes)
        if definition.edges:
            await self.repository.save_edges(definition.edges)

        logger.info(
            "工作流定义已创建: id=%s, name=%s, operator=%s",
            saved_definition.id,
            saved_definition.name,
            operator,
        )

        return saved_definition

    async def get_workflow(self, workflow_id: str) -> WorkflowDefinition:
        """获取工作流定义详情

        Args:
            workflow_id: 工作流标识

        Returns:
            工作流定义实体

        Raises:
            ResourceNotFoundException: 工作流不存在
        """
        workflow = await self.repository.find_workflow_by_id(workflow_id)
        if workflow is None:
            raise ResourceNotFoundException(
                resource_type="WorkflowDefinition",
                resource_id=workflow_id,
            )

        # 加载节点和边
        workflow.nodes = await self.repository.find_nodes_by_workflow_id(workflow_id)
        workflow.edges = await self.repository.find_edges_by_workflow_id(workflow_id)
        return workflow

    async def list_workflows(
        self,
        pagination: PaginatedRequest,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[WorkflowDefinition]:
        """分页查询工作流定义列表

        Args:
            pagination: 分页参数
            tenant_id: 租户标识

        Returns:
            分页响应结果
        """
        return await self.repository.find_all_workflows(pagination, tenant_id)

    # =========================================================================
    # 工作流执行管理
    # =========================================================================

    async def start_execution(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
        operator: str | None = None,
    ) -> WorkflowExecution:
        """启动工作流执行

        校验工作流状态，创建执行记录并从起始节点开始执行。

        Args:
            workflow_id: 工作流标识
            input_data: 执行输入数据
            operator: 操作者标识

        Returns:
            创建的执行记录

        Raises:
            ResourceNotFoundException: 工作流不存在
            BusinessRuleViolationException: 工作流状态不允许执行
        """
        # 获取工作流定义
        workflow = await self.get_workflow(workflow_id)

        # 校验工作流状态
        if workflow.status != WorkflowStatus.ACTIVE:
            raise BusinessRuleViolationException(
                rule="WORKFLOW_NOT_ACTIVE",
                message=f"工作流状态为 {workflow.status.value}，只有激活状态的工作流才能执行",
            )

        # 查找起始节点
        start_node = self._find_start_node(workflow)

        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            input_data=input_data,
            created_by=operator,
        )
        execution.advance_to_node(start_node.id, operator)

        # 初始化所有节点状态为待执行
        for node in workflow.nodes:
            execution.node_states[node.id] = NodeStatus.PENDING
        execution.node_states[start_node.id] = NodeStatus.PENDING

        saved_execution = await self.repository.save_execution(execution)

        logger.info(
            "工作流执行已启动: execution_id=%s, workflow_id=%s, start_node=%s",
            saved_execution.id,
            workflow_id,
            start_node.id,
        )

        return saved_execution

    async def execute_node(
        self,
        execution_id: str,
        node_id: str,
        result_data: dict[str, Any],
        operator: str | None = None,
    ) -> WorkflowExecution:
        """执行指定节点

        标记节点完成，并根据边条件自动推进到下一节点。

        Args:
            execution_id: 执行记录标识
            node_id: 节点标识
            result_data: 节点执行结果数据
            operator: 操作者标识

        Returns:
            更新后的执行记录

        Raises:
            ResourceNotFoundException: 执行记录或节点不存在
            BusinessRuleViolationException: 执行状态不允许操作
        """
        execution = await self.get_execution(execution_id)

        # 校验当前节点
        if execution.current_node_id != node_id:
            raise BusinessRuleViolationException(
                rule="EXECUTION_NODE_MISMATCH",
                message=f"当前执行节点为 {execution.current_node_id}，非目标节点 {node_id}",
            )

        # 标记节点完成
        execution.complete_node(node_id, result_data, operator)

        # 尝试自动推进到下一节点
        await self._auto_advance(execution, operator)

        saved_execution = await self.repository.save_execution(execution)

        logger.info(
            "节点执行完成: execution_id=%s, node_id=%s",
            execution_id,
            node_id,
        )

        return saved_execution

    async def advance_execution(
        self,
        execution_id: str,
        operator: str | None = None,
    ) -> WorkflowExecution:
        """手动推进执行

        在自动推进失败或需要人工干预时使用。

        Args:
            execution_id: 执行记录标识
            operator: 操作者标识

        Returns:
            更新后的执行记录

        Raises:
            ResourceNotFoundException: 执行记录不存在
        """
        execution = await self.get_execution(execution_id)
        await self._auto_advance(execution, operator)
        saved_execution = await self.repository.save_execution(execution)

        logger.info("执行已推进: execution_id=%s", execution_id)
        return saved_execution

    async def get_execution(self, execution_id: str) -> WorkflowExecution:
        """获取执行记录详情

        Args:
            execution_id: 执行记录标识

        Returns:
            执行记录实体

        Raises:
            ResourceNotFoundException: 执行记录不存在
        """
        execution = await self.repository.find_execution_by_id(execution_id)
        if execution is None:
            raise ResourceNotFoundException(
                resource_type="WorkflowExecution",
                resource_id=execution_id,
            )
        return execution

    async def list_executions(
        self,
        workflow_id: str,
        pagination: PaginatedRequest,
    ) -> PaginatedResponse[WorkflowExecution]:
        """分页查询执行记录列表

        Args:
            workflow_id: 工作流标识
            pagination: 分页参数

        Returns:
            分页响应结果
        """
        return await self.repository.find_executions_by_workflow_id(workflow_id, pagination)

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    def _find_start_node(self, workflow: WorkflowDefinition) -> WorkflowNode:
        """查找工作流的起始节点

        Args:
            workflow: 工作流定义

        Returns:
            起始节点

        Raises:
            BusinessRuleViolationException: 工作流无起始节点
        """
        from ..domain.enums import NodeType

        for node in workflow.nodes:
            if node.node_type == NodeType.START:
                return node

        raise BusinessRuleViolationException(
            rule="WORKFLOW_NO_START_NODE",
            message=f"工作流 [{workflow.id}] 缺少起始节点",
        )

    async def _auto_advance(
        self,
        execution: WorkflowExecution,
        operator: str | None = None,
    ) -> None:
        """自动推进执行

        根据当前已完成节点查找后续可达节点，并更新执行状态。
        如果无后续节点且当前节点为终止节点，则标记执行完成。

        Args:
            execution: 执行记录
            operator: 操作者标识
        """
        from ..domain.enums import EdgeConditionType, NodeType

        current_node_id = execution.current_node_id
        if current_node_id is None:
            return

        # 获取工作流定义以查找边关系
        workflow = await self.repository.find_workflow_by_id(execution.workflow_id)
        if workflow is None:
            return

        edges = await self.repository.find_edges_by_workflow_id(execution.workflow_id)
        nodes = await self.repository.find_nodes_by_workflow_id(execution.workflow_id)

        # 查找当前节点
        current_node = None
        for node in nodes:
            if node.id == current_node_id:
                current_node = node
                break

        # 当前节点为终止节点，标记执行完成
        if current_node and current_node.node_type == NodeType.END:
            execution.complete(operator=operator)
            return

        # 查找符合条件的后续边
        next_edges = [
            edge for edge in edges
            if edge.source_node_id == current_node_id
        ]

        # 根据条件类型筛选
        matching_edges = []
        for edge in next_edges:
            if edge.condition_type == EdgeConditionType.ALWAYS:
                matching_edges.append(edge)
            elif edge.condition_type == EdgeConditionType.SUCCESS:
                node_state = execution.node_states.get(current_node_id)
                if node_state == NodeStatus.COMPLETED:
                    matching_edges.append(edge)
            elif edge.condition_type == EdgeConditionType.FAILURE:
                node_state = execution.node_states.get(current_node_id)
                if node_state == NodeStatus.FAILED:
                    matching_edges.append(edge)
            elif edge.condition_type == EdgeConditionType.EXPRESSION:
                # 表达式条件暂按无条件处理
                # TODO: 实现表达式求值引擎
                matching_edges.append(edge)

        # 按优先级排序
        matching_edges.sort(key=lambda e: e.priority, reverse=True)

        if matching_edges:
            # 推进到第一个匹配边的目标节点
            next_node_id = matching_edges[0].target_node_id
            execution.advance_to_node(next_node_id, operator)
            logger.debug("执行推进: %s -> %s", current_node_id, next_node_id)
        else:
            # 无后续节点且非终止节点，执行完成
            execution.complete(operator=operator)
