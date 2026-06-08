import { defineStore } from 'pinia'
import { ref } from 'vue'
import { agentApi } from '@/api'
import type { Agent, AgentStatus, ClusterStatus } from '@/types'
import { ElMessage } from 'element-plus'

/**
 * Agent状态管理
 */
export const useAgentStore = defineStore('agent', () => {
  /** Agent列表 */
  const agents = ref<Agent[]>([])

  /** 集群状态 */
  const clusterStatus = ref<ClusterStatus | null>(null)

  /** 加载状态 */
  const loading = ref(false)

  /**
   * 获取Agent列表
   */
  async function fetchAgents(params?: { status?: AgentStatus; agent_type?: string }) {
    loading.value = true
    try {
      const res = await agentApi.list(params)
      agents.value = res.items
    } catch (error) {
      ElMessage.error('获取Agent列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取集群状态
   */
  async function fetchClusterStatus() {
    try {
      clusterStatus.value = await agentApi.getClusterStatus()
    } catch (error) {
      console.error('获取集群状态失败:', error)
    }
  }

  /**
   * 暂停Agent
   */
  async function pauseAgent(agentId: string) {
    try {
      await agentApi.pause(agentId)
      ElMessage.success('Agent已暂停')
      await fetchAgents()
    } catch (error) {
      ElMessage.error('暂停Agent失败')
    }
  }

  /**
   * 恢复Agent
   */
  async function resumeAgent(agentId: string) {
    try {
      await agentApi.resume(agentId)
      ElMessage.success('Agent已恢复')
      await fetchAgents()
    } catch (error) {
      ElMessage.error('恢复Agent失败')
    }
  }

  return {
    agents,
    clusterStatus,
    loading,
    fetchAgents,
    fetchClusterStatus,
    pauseAgent,
    resumeAgent,
  }
})
