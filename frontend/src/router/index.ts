import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

/**
 * 路由配置
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      {
        path: 'workflows',
        name: 'Workflows',
        component: () => import('@/views/WorkflowView.vue'),
        meta: { title: '工作流', icon: 'Connection' },
      },
      {
        path: 'workflows/:id',
        name: 'WorkflowDetail',
        component: () => import('@/views/WorkflowDetailView.vue'),
        meta: { title: '工作流详情', hidden: true },
      },
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('@/views/AgentView.vue'),
        meta: { title: 'Agent集群', icon: 'UserFilled' },
      },
      {
        path: 'memory',
        name: 'Memory',
        component: () => import('@/views/MemoryView.vue'),
        meta: { title: '记忆管理', icon: 'Cpu' },
      },
      {
        path: 'tools',
        name: 'Tools',
        component: () => import('@/views/ToolView.vue'),
        meta: { title: '工具中心', icon: 'SetUp' },
      },
      {
        path: 'approvals',
        name: 'Approvals',
        component: () => import('@/views/ApprovalView.vue'),
        meta: { title: '审核中心', icon: 'Checked' },
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/MonitorView.vue'),
        meta: { title: '监控中心', icon: 'DataLine' },
      },
      {
        path: 'llm',
        name: 'LLM',
        component: () => import('@/views/LLMManagementView.vue'),
        meta: { title: 'LLM 管理', icon: 'Cpu' },
      },
      {
        path: 'agent-market',
        name: 'AgentMarket',
        component: () => import('@/views/AgentMarketView.vue'),
        meta: { title: 'Agent 市场', icon: 'Box' },
      },
      {
        path: 'prompts',
        name: 'Prompts',
        component: () => import('@/views/PromptManagementView.vue'),
        meta: { title: 'Prompt 管理', icon: 'Document' },
      },
      {
        path: 'agent-studio',
        name: 'AgentStudio',
        component: () => import('@/views/AgentStudioView.vue'),
        meta: { title: 'Agent Studio', icon: 'MagicStick' },
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/KnowledgeCenterView.vue'),
        meta: { title: '知识中心', icon: 'Collection' },
      },
      {
        path: 'evaluation',
        name: 'Evaluation',
        component: () => import('@/views/EvaluationCenterView.vue'),
        meta: { title: '评估中心', icon: 'DataAnalysis' },
      },
      {
        path: 'prompt-center',
        name: 'PromptCenter',
        component: () => import('@/views/PromptCenterView.vue'),
        meta: { title: 'Prompt 中心', icon: 'EditPen' },
      },
      {
        path: 'cost',
        name: 'Cost',
        component: () => import('@/views/CostCenterView.vue'),
        meta: { title: '成本中心', icon: 'Wallet' },
      },
      {
        path: 'governance',
        name: 'Governance',
        component: () => import('@/views/GovernanceView.vue'),
        meta: { title: '治理中心', icon: 'Shield' },
      },
      {
        path: 'tool-marketplace',
        name: 'ToolMarketplace',
        component: () => import('@/views/ToolMarketplaceView.vue'),
        meta: { title: '工具市场', icon: 'Goods' },
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', hidden: true },
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('@/views/AuthCallbackView.vue'),
    meta: { title: '登录回调', hidden: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '404', hidden: true },
  },
]

/**
 * 创建路由实例
 */
const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 路由前置守卫
 */
router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'AI Workflow OS'} - AI工作流操作系统`
  next()
})

export default router
