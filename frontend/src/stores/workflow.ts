import { defineStore } from 'pinia'
import { ref } from 'vue'
import { workflowApi } from '@/api'
import type { Workflow, WorkflowExecution } from '@/types'
import { ElMessage } from 'element-plus'

/**
 * 工作流状态管理
 */
export const useWorkflowStore = defineStore('workflow', () => {
  /** 工作流列表 */
  const workflows = ref<Workflow[]>([])

  /** 当前工作流详情 */
  const currentWorkflow = ref<Workflow | null>(null)

  /** 当前执行 */
  const currentExecution = ref<WorkflowExecution | null>(null)

  /** 总数 */
  const total = ref(0)

  /** 加载状态 */
  const loading = ref(false)

  /**
   * 获取工作流列表
   */
  async function fetchWorkflows(params?: { page?: number; page_size?: number }) {
    loading.value = true
    try {
      const res = await workflowApi.list(params)
      workflows.value = res.items
      total.value = res.total
    } catch (error) {
      ElMessage.error('获取工作流列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取工作流详情
   */
  async function fetchWorkflowDetail(workflowId: string) {
    loading.value = true
    try {
      currentWorkflow.value = await workflowApi.get(workflowId)
    } catch (error) {
      ElMessage.error('获取工作流详情失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 执行工作流
   */
  async function executeWorkflow(workflowId: string) {
    try {
      const execution = await workflowApi.execute(workflowId)
      currentExecution.value = execution
      ElMessage.success('工作流已开始执行')
      return execution
    } catch (error) {
      ElMessage.error('执行工作流失败')
      throw error
    }
  }

  return {
    workflows,
    currentWorkflow,
    currentExecution,
    total,
    loading,
    fetchWorkflows,
    fetchWorkflowDetail,
    executeWorkflow,
  }
})
