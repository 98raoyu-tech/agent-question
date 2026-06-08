"""
工作流引擎FastAPI路由

提供工作流定义管理和工作流执行管理的RESTful API端点。
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from ...common.exceptions import (
    BusinessRuleViolationException,
    PlatformException,
    ResourceNotFoundException,
    ValidationException,
)
from ...common.pagination import PaginatedRequest
from ..application.workflow_engine_service import WorkflowEngineService
from ..domain.workflow_definition import WorkflowDefinition
from ..domain.workflow_edge import WorkflowEdge
from ..domain.workflow_execution import WorkflowExecution
from ..domain.workflow_node import WorkflowNode
from ..infrastructure.workflow_repository import WorkflowRepository
from .schemas import (
    AdvanceExecutionRequest,
    CreateWorkflowRequest,
    ExecuteNodeRequest,
    ExecutionListResponse,
    StartExecutionRequest,
    WorkflowDefinitionResponse,
    WorkflowEdgeResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowNodeResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflow-engine", tags=["Workflow Engine"])

# 依赖注入：创建仓储和服务实例
# TODO: 后续替换为依赖注入容器管理
_workflow_repository = WorkflowRepository()
_workflow_engine_service = WorkflowEngineService(_workflow_repository)


# =============================================================================
# 工作流定义端点
# =============================================================================


@router.post(
    "/workflows",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建工作流定义",
    description="创建一个新的工作流定义，包含节点和边",
)
async def create_workflow(request: CreateWorkflowRequest) -> WorkflowDefinitionResponse:
    """创建工作流定义"""
    try:
        # 构建领域实体
        definition = WorkflowDefinition(
            name=request.name,
            description=request.description,
            variables=request.variables,
            version=request.version,
            tenant_id=request.tenant_id,
        )

        # 构建节点
        for node_req in request.nodes:
            node = WorkflowNode(
                workflow_id=definition.id,
                node_type=node_req.node_type,
                name=node_req.name,
                config=node_req.config,
                position_x=node_req.position_x,
                position_y=node_req.position_y,
                timeout_seconds=node_req.timeout_seconds,
                retry_count=node_req.retry_count,
            )
            definition.nodes.append(node)

        # 构建边
        for edge_req in request.edges:
            edge = WorkflowEdge(
                workflow_id=definition.id,
                source_node_id=edge_req.source_node_id,
                target_node_id=edge_req.target_node_id,
                condition_type=edge_req.condition_type,
                condition_expression=edge_req.condition_expression,
                priority=edge_req.priority,
            )
            definition.edges.append(edge)

        saved_definition = await _workflow_engine_service.create_workflow(
            definition=definition,
            operator=request.operator,
        )

        return _to_workflow_response(saved_definition)

    except ValidationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except PlatformException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowDefinitionResponse,
    summary="获取工作流定义详情",
    description="根据ID获取工作流定义的详细信息",
)
async def get_workflow(workflow_id: str) -> WorkflowDefinitionResponse:
    """获取工作流定义详情"""
    try:
        workflow = await _workflow_engine_service.get_workflow(workflow_id)
        return _to_workflow_response(workflow)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/workflows",
    response_model=WorkflowListResponse,
    summary="查询工作流定义列表",
    description="分页查询工作流定义列表",
)
async def list_workflows(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    tenant_id: str | None = Query(default=None, description="租户标识"),
) -> WorkflowListResponse:
    """查询工作流定义列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)

    result = await _workflow_engine_service.list_workflows(pagination, tenant_id)

    return WorkflowListResponse(
        items=[_to_workflow_response(w) for w in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post(
    "/workflows/{workflow_id}/activate",
    response_model=WorkflowDefinitionResponse,
    summary="激活工作流",
    description="将草稿状态的工作流激活",
)
async def activate_workflow(workflow_id: str) -> WorkflowDefinitionResponse:
    """激活工作流"""
    try:
        workflow = await _workflow_engine_service.get_workflow(workflow_id)
        workflow.activate()
        await _workflow_repository.save_workflow(workflow)
        return _to_workflow_response(workflow)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.post(
    "/workflows/{workflow_id}/deactivate",
    response_model=WorkflowDefinitionResponse,
    summary="停用工作流",
    description="将激活状态的工作流停用",
)
async def deactivate_workflow(workflow_id: str) -> WorkflowDefinitionResponse:
    """停用工作流"""
    try:
        workflow = await _workflow_engine_service.get_workflow(workflow_id)
        workflow.deactivate()
        await _workflow_repository.save_workflow(workflow)
        return _to_workflow_response(workflow)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


# =============================================================================
# 工作流执行端点
# =============================================================================


@router.post(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="启动工作流执行",
    description="启动一次工作流执行",
)
async def start_execution(
    workflow_id: str,
    request: StartExecutionRequest,
) -> WorkflowExecutionResponse:
    """启动工作流执行"""
    try:
        execution = await _workflow_engine_service.start_execution(
            workflow_id=workflow_id,
            input_data=request.input_data,
            operator=request.operator,
        )
        return _to_execution_response(execution)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="获取执行记录详情",
    description="根据ID获取执行记录的详细信息",
)
async def get_execution(execution_id: str) -> WorkflowExecutionResponse:
    """获取执行记录详情"""
    try:
        execution = await _workflow_engine_service.get_execution(execution_id)
        return _to_execution_response(execution)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.post(
    "/executions/{execution_id}/execute-node",
    response_model=WorkflowExecutionResponse,
    summary="执行节点",
    description="标记指定节点完成并自动推进到下一节点",
)
async def execute_node(
    execution_id: str,
    request: ExecuteNodeRequest,
) -> WorkflowExecutionResponse:
    """执行节点"""
    try:
        execution = await _workflow_engine_service.execute_node(
            execution_id=execution_id,
            node_id=request.node_id,
            result_data=request.result_data,
            operator=request.operator,
        )
        return _to_execution_response(execution)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.post(
    "/executions/{execution_id}/advance",
    response_model=WorkflowExecutionResponse,
    summary="手动推进执行",
    description="手动推进工作流执行到下一节点",
)
async def advance_execution(
    execution_id: str,
    request: AdvanceExecutionRequest,
) -> WorkflowExecutionResponse:
    """手动推进执行"""
    try:
        execution = await _workflow_engine_service.advance_execution(
            execution_id=execution_id,
            operator=request.operator,
        )
        return _to_execution_response(execution)

    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc
    except BusinessRuleViolationException as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc


@router.get(
    "/workflows/{workflow_id}/executions",
    response_model=ExecutionListResponse,
    summary="查询执行记录列表",
    description="分页查询指定工作流的执行记录列表",
)
async def list_executions(
    workflow_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
) -> ExecutionListResponse:
    """查询执行记录列表"""
    pagination = PaginatedRequest(page=page, page_size=page_size)

    result = await _workflow_engine_service.list_executions(workflow_id, pagination)

    return ExecutionListResponse(
        items=[_to_execution_response(ex) for ex in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


# =============================================================================
# 辅助函数
# =============================================================================


def _to_node_response(node: WorkflowNode) -> WorkflowNodeResponse:
    """将节点实体转换为响应Schema

    Args:
        node: 节点实体

    Returns:
        节点响应
    """
    return WorkflowNodeResponse(
        id=node.id,
        workflow_id=node.workflow_id,
        node_type=node.node_type,
        name=node.name,
        config=node.config,
        position_x=node.position_x,
        position_y=node.position_y,
        timeout_seconds=node.timeout_seconds,
        retry_count=node.retry_count,
        status=node.status,
        started_at=node.started_at,
        completed_at=node.completed_at,
        error_message=node.error_message,
        duration_ms=node.duration_ms,
        created_at=node.created_at,
        updated_at=node.updated_at,
        tenant_id=node.tenant_id,
    )


def _to_edge_response(edge: WorkflowEdge) -> WorkflowEdgeResponse:
    """将边实体转换为响应Schema

    Args:
        edge: 边实体

    Returns:
        边响应
    """
    return WorkflowEdgeResponse(
        id=edge.id,
        workflow_id=edge.workflow_id,
        source_node_id=edge.source_node_id,
        target_node_id=edge.target_node_id,
        condition_type=edge.condition_type,
        condition_expression=edge.condition_expression,
        priority=edge.priority,
        created_at=edge.created_at,
        updated_at=edge.updated_at,
        tenant_id=edge.tenant_id,
    )


def _to_workflow_response(workflow: WorkflowDefinition) -> WorkflowDefinitionResponse:
    """将工作流定义实体转换为响应Schema

    Args:
        workflow: 工作流定义实体

    Returns:
        工作流定义响应
    """
    return WorkflowDefinitionResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        nodes=[_to_node_response(n) for n in workflow.nodes],
        edges=[_to_edge_response(e) for e in workflow.edges],
        variables=workflow.variables,
        workflow_version=workflow.workflow_version,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        tenant_id=workflow.tenant_id,
    )


def _to_execution_response(execution: WorkflowExecution) -> WorkflowExecutionResponse:
    """将执行记录实体转换为响应Schema

    Args:
        execution: 执行记录实体

    Returns:
        执行记录响应
    """
    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        current_node_id=execution.current_node_id,
        node_states=execution.node_states,
        input_data=execution.input_data,
        output_data=execution.output_data,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        error_message=execution.error_message,
        duration_ms=execution.duration_ms,
        completed_node_count=execution.completed_node_count,
        failed_node_count=execution.failed_node_count,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        tenant_id=execution.tenant_id,
    )
