import axios from 'axios'
import type {
  PaginatedResponse,
  Workflow,
  WorkflowExecution,
  Agent,
  Task,
  ClusterStatus,
  MemoryEntry,
  ApprovalRequest,
  WorkflowCreateRequest,
  TaskDispatchRequest,
  WorkflowStatus,
  AgentStatus,
  AgentDefinition,
  AgentVersion,
  AgentRelease,
  AgentDefinitionListRequest,
  KnowledgeSource,
  KnowledgeDocument,
  KnowledgeChunk,
  KnowledgeSourceListRequest,
  KnowledgeDocumentListRequest,
  KnowledgeSearchRequest,
  KnowledgeSearchResult,
  EvaluationDataset,
  EvaluationRun,
  EvaluationScore,
  EvaluationDatasetListRequest,
  EvaluationRunListRequest,
  PromptTemplate,
  PromptVersion,
  PromptABTest,
  PromptTemplateListRequest,
  CostUsage,
  CostBudget,
  CostAlert,
  CostUsageListRequest,
  CostBudgetListRequest,
  CostStatistics,
  PolicyDefinition,
  AuditLog,
  PolicyListRequest,
  AuditLogListRequest,
  ToolDefinition,
  ToolReview,
  ToolMarketplaceListRequest,
  ToolReviewListRequest,
} from '@/types'

/**
 * 获取API基础URL
 * 开发环境使用代理，生产环境使用环境变量配置
 */
const getApiBaseUrl = (): string => {
  // 优先使用环境变量配置
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // 默认使用相对路径（开发环境通过vite代理）
  return '/api/v1'
}

/**
 * 创建axios实例
 */
const http = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 请求拦截器
 */
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 响应拦截器
 */
http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

// ==================== 工作流API ====================

/**
 * 工作流相关API
 */
export const workflowApi = {
  /** 创建工作流 */
  create(data: WorkflowCreateRequest): Promise<Workflow> {
    return http.post('/workflows/workflows', data)
  },

  /** 获取工作流列表 */
  list(params?: {
    page?: number
    page_size?: number
    status?: WorkflowStatus
  }): Promise<PaginatedResponse<Workflow>> {
    return http.get('/workflows/workflows', { params })
  },

  /** 获取工作流详情 */
  get(workflowId: string): Promise<Workflow> {
    return http.get(`/workflows/workflows/${workflowId}`)
  },

  /** 执行工作流 */
  execute(workflowId: string): Promise<WorkflowExecution> {
    return http.post(`/workflows/workflows/${workflowId}/execute`)
  },

  /** 获取执行状态 */
  getExecution(executionId: string): Promise<WorkflowExecution> {
    return http.get(`/workflows/workflows/executions/${executionId}`)
  },

  /** 暂停执行 */
  pauseExecution(executionId: string): Promise<WorkflowExecution> {
    return http.post(`/workflows/workflows/executions/${executionId}/pause`)
  },

  /** 恢复执行 */
  resumeExecution(executionId: string): Promise<WorkflowExecution> {
    return http.post(`/workflows/workflows/executions/${executionId}/resume`)
  },

  /** 取消执行 */
  cancelExecution(executionId: string): Promise<WorkflowExecution> {
    return http.post(`/workflows/workflows/executions/${executionId}/cancel`)
  },
}

// ==================== Agent API ====================

/**
 * Agent相关API
 */
export const agentApi = {
  /** 分派任务 */
  dispatch(data: TaskDispatchRequest): Promise<Task> {
    return http.post('/agents/agents/dispatch', data)
  },

  /** 获取Agent列表 */
  list(params?: {
    status?: AgentStatus
    agent_type?: string
  }): Promise<{ items: Agent[]; total: number }> {
    return http.get('/agents/agents', { params })
  },

  /** 获取Agent详情 */
  get(agentId: string): Promise<Agent> {
    return http.get(`/agents/agents/${agentId}`)
  },

  /** 暂停Agent */
  pause(agentId: string): Promise<Agent> {
    return http.post(`/agents/agents/${agentId}/pause`)
  },

  /** 恢复Agent */
  resume(agentId: string): Promise<Agent> {
    return http.post(`/agents/agents/${agentId}/resume`)
  },

  /** 获取集群状态 */
  getClusterStatus(): Promise<ClusterStatus> {
    return http.get('/agents/agents/cluster/status')
  },
}

// ==================== 记忆API ====================

/**
 * 记忆相关API
 */
export const memoryApi = {
  /** 存储记忆 */
  store(data: {
    key: string
    value: unknown
    memory_type?: string
    metadata?: Record<string, unknown>
  }): Promise<MemoryEntry> {
    return http.post('/memory/store', data)
  },

  /** 检索记忆 */
  recall(data: {
    query: string
    memory_types?: string[]
    top_k?: number
  }): Promise<{ results: MemoryEntry[] }> {
    return http.post('/memory/recall', data)
  },

  /** 删除记忆 */
  forget(key: string): Promise<void> {
    return http.delete(`/memory/${key}`)
  },

  /** 获取记忆统计 */
  getStats(): Promise<Record<string, unknown>> {
    return http.get('/memory/stats')
  },
}

// ==================== 工具API ====================

/**
 * 工具相关API
 */
export const toolApi = {
  /** 获取工具列表 */
  list(): Promise<{ items: Array<{ name: string; description: string }> }> {
    return http.get('/tools')
  },

  /** 获取工具详情 */
  get(toolName: string): Promise<{ name: string; description: string; schema: unknown }> {
    return http.get(`/tools/${toolName}`)
  },

  /** 调用工具 */
  invoke(toolName: string, params: Record<string, unknown>): Promise<unknown> {
    return http.post(`/tools/${toolName}/invoke`, params)
  },
}

// ==================== 审核API ====================

/**
 * 审核相关API
 */
export const approvalApi = {
  /** 获取待审核列表 */
  list(): Promise<{ items: ApprovalRequest[] }> {
    return http.get('/approvals')
  },

  /** 审核通过 */
  approve(requestId: string, data?: { approver_id?: string; comment?: string }): Promise<void> {
    return http.post(`/approvals/${requestId}/approve`, data)
  },

  /** 审核拒绝 */
  reject(requestId: string, data?: { approver_id?: string; reason?: string }): Promise<void> {
    return http.post(`/approvals/${requestId}/reject`, data)
  },

  /** 获取审核详情 */
  get(requestId: string): Promise<ApprovalRequest> {
    return http.get(`/approvals/${requestId}`)
  },
}

// ==================== Agent Studio API ====================

/**
 * Agent Studio相关API
 */
export const agentStudioApi = {
  /** 获取Agent定义列表 */
  list(params?: AgentDefinitionListRequest): Promise<PaginatedResponse<AgentDefinition>> {
    return http.get('/agent-studio/agents', { params })
  },

  /** 获取Agent定义详情 */
  get(agentId: string): Promise<AgentDefinition> {
    return http.get(`/agent-studio/agents/${agentId}`)
  },

  /** 创建Agent定义 */
  create(data: Partial<AgentDefinition>): Promise<AgentDefinition> {
    return http.post('/agent-studio/agents', data)
  },

  /** 更新Agent定义 */
  update(agentId: string, data: Partial<AgentDefinition>): Promise<AgentDefinition> {
    return http.put(`/agent-studio/agents/${agentId}`, data)
  },

  /** 删除Agent定义 */
  delete(agentId: string): Promise<void> {
    return http.delete(`/agent-studio/agents/${agentId}`)
  },

  /** 获取Agent版本列表 */
  listVersions(agentId: string): Promise<{ items: AgentVersion[] }> {
    return http.get(`/agent-studio/agents/${agentId}/versions`)
  },

  /** 创建Agent版本 */
  createVersion(agentId: string, data: { change_log: string }): Promise<AgentVersion> {
    return http.post(`/agent-studio/agents/${agentId}/versions`, data)
  },

  /** 获取Agent发布列表 */
  listReleases(agentId: string): Promise<{ items: AgentRelease[] }> {
    return http.get(`/agent-studio/agents/${agentId}/releases`)
  },

  /** 创建Agent发布 */
  createRelease(agentId: string, data: { version_id: string; release_notes: string }): Promise<AgentRelease> {
    return http.post(`/agent-studio/agents/${agentId}/releases`, data)
  },

  /** 审核Agent发布 */
  reviewRelease(releaseId: string, data: { approved: boolean; comment?: string }): Promise<AgentRelease> {
    return http.post(`/agent-studio/releases/${releaseId}/review`, data)
  },

  /** 发布Agent */
  publishRelease(releaseId: string): Promise<AgentRelease> {
    return http.post(`/agent-studio/releases/${releaseId}/publish`)
  },
}

// ==================== 知识中心 API ====================

/**
 * 知识中心API
 */
export const knowledgeApi = {
  /** 获取知识源列表 */
  listSources(params?: KnowledgeSourceListRequest): Promise<PaginatedResponse<KnowledgeSource>> {
    return http.get('/knowledge/sources', { params })
  },

  /** 获取知识源详情 */
  getSource(sourceId: string): Promise<KnowledgeSource> {
    return http.get(`/knowledge/sources/${sourceId}`)
  },

  /** 创建知识源 */
  createSource(data: Partial<KnowledgeSource>): Promise<KnowledgeSource> {
    return http.post('/knowledge/sources', data)
  },

  /** 更新知识源 */
  updateSource(sourceId: string, data: Partial<KnowledgeSource>): Promise<KnowledgeSource> {
    return http.put(`/knowledge/sources/${sourceId}`, data)
  },

  /** 删除知识源 */
  deleteSource(sourceId: string): Promise<void> {
    return http.delete(`/knowledge/sources/${sourceId}`)
  },

  /** 同步知识源 */
  syncSource(sourceId: string): Promise<void> {
    return http.post(`/knowledge/sources/${sourceId}/sync`)
  },

  /** 获取文档列表 */
  listDocuments(params?: KnowledgeDocumentListRequest): Promise<PaginatedResponse<KnowledgeDocument>> {
    return http.get('/knowledge/documents', { params })
  },

  /** 上传文档 */
  uploadDocument(sourceId: string, file: File): Promise<KnowledgeDocument> {
    const formData = new FormData()
    formData.append('file', file)
    return http.post(`/knowledge/sources/${sourceId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 删除文档 */
  deleteDocument(documentId: string): Promise<void> {
    return http.delete(`/knowledge/documents/${documentId}`)
  },

  /** 获取文档块列表 */
  listChunks(documentId: string): Promise<{ items: KnowledgeChunk[] }> {
    return http.get(`/knowledge/documents/${documentId}/chunks`)
  },

  /** 知识搜索 */
  search(data: KnowledgeSearchRequest): Promise<{ results: KnowledgeSearchResult[] }> {
    return http.post('/knowledge/search', data)
  },
}

// ==================== 评估中心 API ====================

/**
 * 评估中心API
 */
export const evaluationApi = {
  /** 获取评测数据集列表 */
  listDatasets(params?: EvaluationDatasetListRequest): Promise<PaginatedResponse<EvaluationDataset>> {
    return http.get('/evaluation/datasets', { params })
  },

  /** 获取评测数据集详情 */
  getDataset(datasetId: string): Promise<EvaluationDataset> {
    return http.get(`/evaluation/datasets/${datasetId}`)
  },

  /** 创建评测数据集 */
  createDataset(data: Partial<EvaluationDataset>): Promise<EvaluationDataset> {
    return http.post('/evaluation/datasets', data)
  },

  /** 更新评测数据集 */
  updateDataset(datasetId: string, data: Partial<EvaluationDataset>): Promise<EvaluationDataset> {
    return http.put(`/evaluation/datasets/${datasetId}`, data)
  },

  /** 删除评测数据集 */
  deleteDataset(datasetId: string): Promise<void> {
    return http.delete(`/evaluation/datasets/${datasetId}`)
  },

  /** 获取评测运行列表 */
  listRuns(params?: EvaluationRunListRequest): Promise<PaginatedResponse<EvaluationRun>> {
    return http.get('/evaluation/runs', { params })
  },

  /** 获取评测运行详情 */
  getRun(runId: string): Promise<EvaluationRun> {
    return http.get(`/evaluation/runs/${runId}`)
  },

  /** 创建评测运行 */
  createRun(data: { dataset_id: string; agent_id: string; config?: Record<string, unknown> }): Promise<EvaluationRun> {
    return http.post('/evaluation/runs', data)
  },

  /** 取消评测运行 */
  cancelRun(runId: string): Promise<void> {
    return http.post(`/evaluation/runs/${runId}/cancel`)
  },

  /** 获取评测评分 */
  getScores(runId: string): Promise<{ items: EvaluationScore[] }> {
    return http.get(`/evaluation/runs/${runId}/scores`)
  },
}

// ==================== Prompt中心 API ====================

/**
 * Prompt中心API
 */
export const promptCenterApi = {
  /** 获取Prompt模板列表 */
  list(params?: PromptTemplateListRequest): Promise<PaginatedResponse<PromptTemplate>> {
    return http.get('/prompt-center/templates', { params })
  },

  /** 获取Prompt模板详情 */
  get(templateId: string): Promise<PromptTemplate> {
    return http.get(`/prompt-center/templates/${templateId}`)
  },

  /** 创建Prompt模板 */
  create(data: Partial<PromptTemplate>): Promise<PromptTemplate> {
    return http.post('/prompt-center/templates', data)
  },

  /** 更新Prompt模板 */
  update(templateId: string, data: Partial<PromptTemplate>): Promise<PromptTemplate> {
    return http.put(`/prompt-center/templates/${templateId}`, data)
  },

  /** 删除Prompt模板 */
  delete(templateId: string): Promise<void> {
    return http.delete(`/prompt-center/templates/${templateId}`)
  },

  /** 获取Prompt版本列表 */
  listVersions(templateId: string): Promise<{ items: PromptVersion[] }> {
    return http.get(`/prompt-center/templates/${templateId}/versions`)
  },

  /** 创建Prompt版本 */
  createVersion(templateId: string, data: { content: string; change_log: string }): Promise<PromptVersion> {
    return http.post(`/prompt-center/templates/${templateId}/versions`, data)
  },

  /** 获取AB测试列表 */
  listABTests(templateId: string): Promise<{ items: PromptABTest[] }> {
    return http.get(`/prompt-center/templates/${templateId}/ab-tests`)
  },

  /** 创建AB测试 */
  createABTest(templateId: string, data: Partial<PromptABTest>): Promise<PromptABTest> {
    return http.post(`/prompt-center/templates/${templateId}/ab-tests`, data)
  },

  /** 停止AB测试 */
  stopABTest(testId: string): Promise<void> {
    return http.post(`/prompt-center/ab-tests/${testId}/stop`)
  },
}

// ==================== 成本中心 API ====================

/**
 * 成本中心API
 */
export const costApi = {
  /** 获取成本使用列表 */
  listUsage(params?: CostUsageListRequest): Promise<PaginatedResponse<CostUsage>> {
    return http.get('/cost/usage', { params })
  },

  /** 获取成本统计 */
  getStatistics(params?: { start_date?: string; end_date?: string }): Promise<CostStatistics> {
    return http.get('/cost/statistics', { params })
  },

  /** 获取成本预算列表 */
  listBudgets(params?: CostBudgetListRequest): Promise<PaginatedResponse<CostBudget>> {
    return http.get('/cost/budgets', { params })
  },

  /** 获取成本预算详情 */
  getBudget(budgetId: string): Promise<CostBudget> {
    return http.get(`/cost/budgets/${budgetId}`)
  },

  /** 创建成本预算 */
  createBudget(data: Partial<CostBudget>): Promise<CostBudget> {
    return http.post('/cost/budgets', data)
  },

  /** 更新成本预算 */
  updateBudget(budgetId: string, data: Partial<CostBudget>): Promise<CostBudget> {
    return http.put(`/cost/budgets/${budgetId}`, data)
  },

  /** 删除成本预算 */
  deleteBudget(budgetId: string): Promise<void> {
    return http.delete(`/cost/budgets/${budgetId}`)
  },

  /** 获取成本告警列表 */
  listAlerts(): Promise<{ items: CostAlert[] }> {
    return http.get('/cost/alerts')
  },

  /** 标记告警已读 */
  markAlertRead(alertId: string): Promise<void> {
    return http.post(`/cost/alerts/${alertId}/read`)
  },
}

// ==================== 治理中心 API ====================

/**
 * 治理中心API
 */
export const governanceApi = {
  /** 获取策略列表 */
  listPolicies(params?: PolicyListRequest): Promise<PaginatedResponse<PolicyDefinition>> {
    return http.get('/governance/policies', { params })
  },

  /** 获取策略详情 */
  getPolicy(policyId: string): Promise<PolicyDefinition> {
    return http.get(`/governance/policies/${policyId}`)
  },

  /** 创建策略 */
  createPolicy(data: Partial<PolicyDefinition>): Promise<PolicyDefinition> {
    return http.post('/governance/policies', data)
  },

  /** 更新策略 */
  updatePolicy(policyId: string, data: Partial<PolicyDefinition>): Promise<PolicyDefinition> {
    return http.put(`/governance/policies/${policyId}`, data)
  },

  /** 删除策略 */
  deletePolicy(policyId: string): Promise<void> {
    return http.delete(`/governance/policies/${policyId}`)
  },

  /** 启用/禁用策略 */
  togglePolicy(policyId: string, active: boolean): Promise<void> {
    return http.post(`/governance/policies/${policyId}/toggle`, { active })
  },

  /** 获取审计日志列表 */
  listAuditLogs(params?: AuditLogListRequest): Promise<PaginatedResponse<AuditLog>> {
    return http.get('/governance/audit-logs', { params })
  },

  /** 导出审计日志 */
  exportAuditLogs(params?: AuditLogListRequest): Promise<Blob> {
    return http.get('/governance/audit-logs/export', { params, responseType: 'blob' })
  },
}

// ==================== 工具市场 API ====================

/**
 * 工具市场API
 */
export const toolMarketplaceApi = {
  /** 获取工具列表 */
  list(params?: ToolMarketplaceListRequest): Promise<PaginatedResponse<ToolDefinition>> {
    return http.get('/tool-marketplace/tools', { params })
  },

  /** 获取工具详情 */
  get(toolId: string): Promise<ToolDefinition> {
    return http.get(`/tool-marketplace/tools/${toolId}`)
  },

  /** 安装工具 */
  install(toolId: string): Promise<void> {
    return http.post(`/tool-marketplace/tools/${toolId}/install`)
  },

  /** 卸载工具 */
  uninstall(toolId: string): Promise<void> {
    return http.post(`/tool-marketplace/tools/${toolId}/uninstall`)
  },

  /** 提交工具审核 */
  submitForReview(toolId: string, data: { version: string }): Promise<ToolReview> {
    return http.post(`/tool-marketplace/tools/${toolId}/submit`, data)
  },

  /** 获取审核列表 */
  listReviews(params?: ToolReviewListRequest): Promise<PaginatedResponse<ToolReview>> {
    return http.get('/tool-marketplace/reviews', { params })
  },

  /** 审核工具 */
  reviewTool(reviewId: string, data: { approved: boolean; comment?: string }): Promise<ToolReview> {
    return http.post(`/tool-marketplace/reviews/${reviewId}/review`, data)
  },
}

export default http
