/**
 * 工作流状态枚举
 */
export enum WorkflowStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * 执行状态枚举
 */
export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

/**
 * Agent状态枚举
 */
export enum AgentStatus {
  IDLE = 'idle',
  BUSY = 'busy',
  PAUSED = 'paused',
  OFFLINE = 'offline',
  ERROR = 'error',
}

/**
 * 任务优先级枚举
 */
export enum TaskPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

/**
 * 任务状态枚举
 */
export enum TaskStatus {
  PENDING = 'pending',
  ASSIGNED = 'assigned',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * 记忆类型枚举
 */
export enum MemoryType {
  VECTOR = 'vector',
  GRAPH = 'graph',
  KV = 'kv',
  EVENT = 'event',
}

/**
 * 工作流步骤
 */
export interface WorkflowStep {
  step_id: string
  name: string
  agent_type: string
  config: Record<string, unknown>
  dependencies: string[]
}

/**
 * 工作流
 */
export interface Workflow {
  workflow_id: string
  name: string
  description?: string
  status: WorkflowStatus
  steps: WorkflowStep[]
  created_at: string
  updated_at: string
}

/**
 * 工作流执行
 */
export interface WorkflowExecution {
  execution_id: string
  workflow_id: string
  status: ExecutionStatus
  current_step?: string
  progress: number
  started_at?: string
  completed_at?: string
  error?: string
}

/**
 * Agent
 */
export interface Agent {
  agent_id: string
  agent_type: string
  status: AgentStatus
  current_task?: string
  capabilities: string[]
  last_active?: string
}

/**
 * 任务
 */
export interface Task {
  task_id: string
  task_type: string
  status: TaskStatus
  assigned_agent?: string
  priority: TaskPriority
  created_at: string
  started_at?: string
  completed_at?: string
  result?: Record<string, unknown>
  error?: string
}

/**
 * 集群状态
 */
export interface ClusterStatus {
  total_agents: number
  active_agents: number
  pending_tasks: number
  task_queue_size: number
}

/**
 * 记忆条目
 */
export interface MemoryEntry {
  key: string
  value: unknown
  memory_type: MemoryType
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/**
 * API响应
 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data?: T
}

/**
 * 创建工作流请求
 */
export interface WorkflowCreateRequest {
  name: string
  description?: string
  steps: WorkflowStep[]
  timeout?: number
}

/**
 * 任务分派请求
 */
export interface TaskDispatchRequest {
  task_type: string
  payload?: Record<string, unknown>
  priority?: TaskPriority
  timeout?: number
}

/**
 * 审核请求
 */
export interface ApprovalRequest {
  request_id: string
  execution_id: string
  step_id: string
  action_description: string
  risk_level: string
  context: Record<string, unknown>
  status: string
  created_at: string
  expires_at: string
}

// ==================== Agent Studio 类型 ====================

/**
 * Agent定义类型枚举
 */
export enum AgentDefinitionType {
  CHATBOT = 'chatbot',
  WORKFLOW = 'workflow',
  TOOL_USE = 'tool_use',
  RAG = 'rag',
  MULTI_AGENT = 'multi_agent',
}

/**
 * Agent发布状态枚举
 */
export enum ReleaseStatus {
  DRAFT = 'draft',
  REVIEWING = 'reviewing',
  APPROVED = 'approved',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

/**
 * Agent定义
 */
export interface AgentDefinition {
  agent_id: string
  name: string
  description: string
  definition_type: AgentDefinitionType
  system_prompt: string
  model_config: Record<string, unknown>
  tools: string[]
  knowledge_sources: string[]
  metadata: Record<string, unknown>
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * Agent版本
 */
export interface AgentVersion {
  version_id: string
  agent_id: string
  version_number: string
  change_log: string
  definition_snapshot: AgentDefinition
  is_current: boolean
  created_at: string
}

/**
 * Agent发布
 */
export interface AgentRelease {
  release_id: string
  agent_id: string
  version_id: string
  status: ReleaseStatus
  release_notes: string
  reviewer?: string
  reviewed_at?: string
  published_at?: string
  created_at: string
}

/**
 * Agent定义分页请求
 */
export interface AgentDefinitionListRequest {
  page?: number
  page_size?: number
  definition_type?: AgentDefinitionType
  keyword?: string
}

// ==================== 知识中心类型 ====================

/**
 * 知识源类型枚举
 */
export enum KnowledgeSourceType {
  FILE = 'file',
  URL = 'url',
  DATABASE = 'database',
  API = 'api',
  MANUAL = 'manual',
}

/**
 * 文档状态枚举
 */
export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * 知识源
 */
export interface KnowledgeSource {
  source_id: string
  name: string
  source_type: KnowledgeSourceType
  config: Record<string, unknown>
  document_count: number
  total_chunks: number
  last_synced_at?: string
  created_at: string
  updated_at: string
}

/**
 * 知识文档
 */
export interface KnowledgeDocument {
  document_id: string
  source_id: string
  name: string
  file_path?: string
  file_size?: number
  mime_type?: string
  status: DocumentStatus
  chunk_count: number
  error_message?: string
  created_at: string
  updated_at: string
}

/**
 * 知识块
 */
export interface KnowledgeChunk {
  chunk_id: string
  document_id: string
  content: string
  embedding?: number[]
  metadata: Record<string, unknown>
  token_count: number
  created_at: string
}

/**
 * 知识源分页请求
 */
export interface KnowledgeSourceListRequest {
  page?: number
  page_size?: number
  source_type?: KnowledgeSourceType
  keyword?: string
}

/**
 * 知识文档分页请求
 */
export interface KnowledgeDocumentListRequest {
  page?: number
  page_size?: number
  source_id?: string
  status?: DocumentStatus
}

/**
 * 知识搜索请求
 */
export interface KnowledgeSearchRequest {
  query: string
  source_ids?: string[]
  top_k?: number
  score_threshold?: number
}

/**
 * 知识搜索结果
 */
export interface KnowledgeSearchResult {
  chunk: KnowledgeChunk
  document_name: string
  source_name: string
  score: number
}

// ==================== 评估中心类型 ====================

/**
 * 评估指标类型枚举
 */
export enum EvaluationMetricType {
  ACCURACY = 'accuracy',
  PRECISION = 'precision',
  RECALL = 'recall',
  F1_SCORE = 'f1_score',
  LATENCY = 'latency',
  COST = 'cost',
  SATISFACTION = 'satisfaction',
  CUSTOM = 'custom',
}

/**
 * 评估运行状态枚举
 */
export enum EvaluationRunStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

/**
 * 评测数据集
 */
export interface EvaluationDataset {
  dataset_id: string
  name: string
  description: string
  item_count: number
  schema: Record<string, unknown>
  sample_data: Record<string, unknown>[]
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * 评测运行
 */
export interface EvaluationRun {
  run_id: string
  dataset_id: string
  agent_id: string
  status: EvaluationRunStatus
  metrics: EvaluationScore[]
  config: Record<string, unknown>
  started_at?: string
  completed_at?: string
  error?: string
  created_at: string
}

/**
 * 评测评分
 */
export interface EvaluationScore {
  metric_type: EvaluationMetricType
  metric_name: string
  value: number
  unit?: string
  details?: Record<string, unknown>
}

/**
 * 评测数据集分页请求
 */
export interface EvaluationDatasetListRequest {
  page?: number
  page_size?: number
  keyword?: string
}

/**
 * 评测运行分页请求
 */
export interface EvaluationRunListRequest {
  page?: number
  page_size?: number
  dataset_id?: string
  agent_id?: string
  status?: EvaluationRunStatus
}

// ==================== Prompt中心类型 ====================

/**
 * Prompt模板
 */
export interface PromptTemplate {
  template_id: string
  name: string
  description: string
  content: string
  variables: string[]
  tags: string[]
  category: string
  is_public: boolean
  usage_count: number
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * Prompt版本
 */
export interface PromptVersion {
  version_id: string
  template_id: string
  version_number: string
  content: string
  variables: string[]
  change_log: string
  is_current: boolean
  created_at: string
}

/**
 * Prompt AB测试配置
 */
export interface PromptABTest {
  test_id: string
  template_id: string
  name: string
  description: string
  variants: PromptABTestVariant[]
  traffic_split: Record<string, number>
  status: string
  started_at?: string
  ended_at?: string
  results?: Record<string, unknown>
  created_at: string
}

/**
 * Prompt AB测试变体
 */
export interface PromptABTestVariant {
  variant_id: string
  version_id: string
  name: string
  weight: number
}

/**
 * Prompt模板分页请求
 */
export interface PromptTemplateListRequest {
  page?: number
  page_size?: number
  category?: string
  keyword?: string
  is_public?: boolean
}

// ==================== 成本中心类型 ====================

/**
 * 成本使用记录
 */
export interface CostUsage {
  usage_id: string
  agent_id: string
  agent_name: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost: number
  currency: string
  request_id: string
  created_at: string
}

/**
 * 成本预算
 */
export interface CostBudget {
  budget_id: string
  name: string
  description: string
  amount: number
  currency: string
  period: string
  start_date: string
  end_date: string
  used_amount: number
  alert_threshold: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 成本告警
 */
export interface CostAlert {
  alert_id: string
  budget_id: string
  budget_name: string
  threshold_percentage: number
  current_percentage: number
  is_triggered: boolean
  triggered_at?: string
  notified: boolean
  created_at: string
}

/**
 * 成本使用分页请求
 */
export interface CostUsageListRequest {
  page?: number
  page_size?: number
  agent_id?: string
  model?: string
  start_date?: string
  end_date?: string
}

/**
 * 成本预算分页请求
 */
export interface CostBudgetListRequest {
  page?: number
  page_size?: number
  is_active?: boolean
}

/**
 * 成本统计
 */
export interface CostStatistics {
  total_cost: number
  period_cost: number
  daily_costs: Array<{ date: string; cost: number }>
  agent_costs: Array<{ agent_id: string; agent_name: string; cost: number }>
  model_costs: Array<{ model: string; cost: number }>
}

// ==================== 治理中心类型 ====================

/**
 * 策略类型枚举
 */
export enum PolicyType {
  ACCESS_CONTROL = 'access_control',
  DATA_PRIVACY = 'data_privacy',
  CONTENT_FILTER = 'content_filter',
  RATE_LIMIT = 'rate_limit',
  COST_CONTROL = 'cost_control',
  CUSTOM = 'custom',
}

/**
 * 策略状态枚举
 */
export enum PolicyStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DRAFT = 'draft',
}

/**
 * 审计日志级别枚举
 */
export enum AuditLogLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

/**
 * 策略定义
 */
export interface PolicyDefinition {
  policy_id: string
  name: string
  description: string
  policy_type: PolicyType
  rules: Record<string, unknown>
  status: PolicyStatus
  priority: number
  applies_to: string[]
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * 审计日志
 */
export interface AuditLog {
  log_id: string
  level: AuditLogLevel
  action: string
  resource_type: string
  resource_id: string
  user_id: string
  user_name: string
  details: Record<string, unknown>
  ip_address: string
  user_agent: string
  created_at: string
}

/**
 * 策略分页请求
 */
export interface PolicyListRequest {
  page?: number
  page_size?: number
  policy_type?: PolicyType
  status?: PolicyStatus
  keyword?: string
}

/**
 * 审计日志分页请求
 */
export interface AuditLogListRequest {
  page?: number
  page_size?: number
  level?: AuditLogLevel
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
}

// ==================== 工具市场类型 ====================

/**
 * 工具状态枚举
 */
export enum ToolStatus {
  DRAFT = 'draft',
  REVIEWING = 'reviewing',
  PUBLISHED = 'published',
  DEPRECATED = 'deprecated',
}

/**
 * 工具安装状态枚举
 */
export enum ToolInstallStatus {
  NOT_INSTALLED = 'not_installed',
  INSTALLING = 'installing',
  INSTALLED = 'installed',
  FAILED = 'failed',
}

/**
 * 工具定义（扩展版）
 */
export interface ToolDefinition {
  tool_id: string
  name: string
  description: string
  version: string
  author: string
  category: string
  tags: string[]
  icon?: string
  schema: Record<string, unknown>
  config_schema?: Record<string, unknown>
  status: ToolStatus
  download_count: number
  rating: number
  rating_count: number
  install_status?: ToolInstallStatus
  installed_version?: string
  created_at: string
  updated_at: string
}

/**
 * 工具审核
 */
export interface ToolReview {
  review_id: string
  tool_id: string
  tool_name: string
  version: string
  status: string
  reviewer?: string
  review_comment?: string
  submitted_by: string
  submitted_at: string
  reviewed_at?: string
}

/**
 * 工具市场分页请求
 */
export interface ToolMarketplaceListRequest {
  page?: number
  page_size?: number
  category?: string
  keyword?: string
  status?: ToolStatus
}

/**
 * 工具审核分页请求
 */
export interface ToolReviewListRequest {
  page?: number
  page_size?: number
  status?: string
}
