<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { workflowApi, agentApi } from '@/api'
import type { ClusterStatus } from '@/types'

/** 集群状态 */
const clusterStatus = ref<ClusterStatus | null>(null)

/** 统计数据 */
const stats = ref({
  totalWorkflows: 0,
  activeWorkflows: 0,
  totalAgents: 0,
  activeAgents: 0,
})

/** 最近工作流 */
const recentWorkflows = ref<Array<{
  id: string
  name: string
  status: string
  updated_at: string
}>>([])

/**
 * 加载数据
 */
async function loadData() {
  try {
    const [clusterRes, workflowRes] = await Promise.all([
      agentApi.getClusterStatus(),
      workflowApi.list({ page: 1, page_size: 5 }),
    ])

    clusterStatus.value = clusterRes
    stats.value = {
      totalWorkflows: workflowRes.total,
      activeWorkflows: workflowRes.items.filter((w) => w.status === 'active').length,
      totalAgents: clusterRes.total_agents,
      activeAgents: clusterRes.active_agents,
    }

    recentWorkflows.value = workflowRes.items.map((w) => ({
      id: w.workflow_id,
      name: w.name,
      status: w.status,
      updated_at: w.updated_at,
    }))
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  }
}

/**
 * 获取状态标签类型
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getStatusType(status: string): TagType {
  const map: Record<string, TagType> = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

/**
 * 获取状态中文名
 */
function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

onMounted(loadData)
</script>

<template>
  <div class="dashboard-view">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6f7ff">
            <el-icon :size="28" color="#1890ff"><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalWorkflows }}</div>
            <div class="stat-label">工作流总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f6ffed">
            <el-icon :size="28" color="#52c41a"><CircleCheckFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.activeWorkflows }}</div>
            <div class="stat-label">运行中工作流</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fff7e6">
            <el-icon :size="28" color="#fa8c16"><UserFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalAgents }}</div>
            <div class="stat-label">Agent总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fff1f0">
            <el-icon :size="28" color="#f5222d"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.activeAgents }}</div>
            <div class="stat-label">活跃Agent</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 最近工作流 -->
      <el-col :span="14">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>最近工作流</span>
              <el-button type="primary" link>查看全部</el-button>
            </div>
          </template>

          <el-table :data="recentWorkflows" style="width: 100%">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="180" />
            <el-table-column label="操作" width="120">
              <template #default>
                <el-button type="primary" link size="small">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 集群状态 -->
      <el-col :span="10">
        <el-card class="content-card">
          <template #header>
            <span>集群状态</span>
          </template>

          <div class="cluster-stats">
            <div class="cluster-item">
              <el-progress
                type="dashboard"
                :percentage="clusterStatus ? Math.round((clusterStatus.active_agents / Math.max(clusterStatus.total_agents, 1)) * 100) : 0"
                :width="100"
              />
              <div class="cluster-label">Agent活跃率</div>
            </div>
            <div class="cluster-item">
              <div class="cluster-number">{{ clusterStatus?.pending_tasks || 0 }}</div>
              <div class="cluster-label">待处理任务</div>
            </div>
            <div class="cluster-item">
              <div class="cluster-number">{{ clusterStatus?.task_queue_size || 0 }}</div>
              <div class="cluster-label">队列长度</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard-view {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.content-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cluster-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px 0;
}

.cluster-item {
  text-align: center;
}

.cluster-number {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
}

.cluster-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}
</style>
