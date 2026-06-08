<script setup lang="ts">
import { onMounted } from 'vue'
import { useAgentStore } from '@/stores'

const agentStore = useAgentStore()

/**
 * 加载Agent列表
 */
async function loadAgents() {
  await agentStore.fetchAgents()
  await agentStore.fetchClusterStatus()
}

/**
 * 暂停Agent
 */
async function handlePause(agentId: string) {
  await agentStore.pauseAgent(agentId)
}

/**
 * 恢复Agent
 */
async function handleResume(agentId: string) {
  await agentStore.resumeAgent(agentId)
}

/**
 * 获取状态标签类型
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getStatusType(status: string): TagType {
  const map: Record<string, TagType> = {
    idle: 'info',
    busy: 'success',
    paused: 'warning',
    offline: 'info',
    error: 'danger',
  }
  return map[status] || 'info'
}

/**
 * 获取状态中文名
 */
function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    idle: '空闲',
    busy: '忙碌',
    paused: '已暂停',
    offline: '离线',
    error: '错误',
  }
  return map[status] || status
}

onMounted(loadAgents)
</script>

<template>
  <div class="agent-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>Agent集群管理</h2>
      <el-button @click="loadAgents">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 集群状态概览 -->
    <el-row :gutter="20" class="cluster-overview">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="overview-item">
            <div class="overview-number">{{ agentStore.clusterStatus?.total_agents || 0 }}</div>
            <div class="overview-label">Agent总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="overview-item">
            <div class="overview-number success">{{ agentStore.clusterStatus?.active_agents || 0 }}</div>
            <div class="overview-label">活跃Agent</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="overview-item">
            <div class="overview-number warning">{{ agentStore.clusterStatus?.pending_tasks || 0 }}</div>
            <div class="overview-label">待处理任务</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="overview-item">
            <div class="overview-number info">{{ agentStore.clusterStatus?.task_queue_size || 0 }}</div>
            <div class="overview-label">队列长度</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Agent列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Agent列表</span>
          <el-select placeholder="状态筛选" clearable style="width: 120px">
            <el-option label="空闲" value="idle" />
            <el-option label="忙碌" value="busy" />
            <el-option label="已暂停" value="paused" />
            <el-option label="离线" value="offline" />
            <el-option label="错误" value="error" />
          </el-select>
        </div>
      </template>

      <el-table v-loading="agentStore.loading" :data="agentStore.agents" style="width: 100%">
        <el-table-column prop="agent_id" label="Agent ID" width="150" />
        <el-table-column prop="agent_type" label="类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_task" label="当前任务" min-width="150" show-overflow-tooltip />
        <el-table-column prop="capabilities" label="能力" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="cap in row.capabilities" :key="cap" size="small" class="capability-tag">
              {{ cap }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_active" label="最后活跃" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'idle' || row.status === 'busy'"
              type="warning"
              link
              size="small"
              @click="handlePause(row.agent_id)"
            >
              暂停
            </el-button>
            <el-button
              v-if="row.status === 'paused'"
              type="success"
              link
              size="small"
              @click="handleResume(row.agent_id)"
            >
              恢复
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.agent-view {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.cluster-overview {
  margin-bottom: 20px;
}

.overview-item {
  text-align: center;
  padding: 10px 0;
}

.overview-number {
  font-size: 36px;
  font-weight: 600;
  color: #303133;
}

.overview-number.success {
  color: #67c23a;
}

.overview-number.warning {
  color: #e6a23c;
}

.overview-number.info {
  color: #909399;
}

.overview-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.capability-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}
</style>
