<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { workflowApi } from '@/api'
import type { Workflow, WorkflowExecution } from '@/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

/** 工作流详情 */
const workflow = ref<Workflow | null>(null)

/** 执行状态 */
const execution = ref<WorkflowExecution | null>(null)

/** 加载状态 */
const loading = ref(false)

/**
 * 加载工作流详情
 */
async function loadWorkflow() {
  const workflowId = route.params.id as string
  if (!workflowId) return

  loading.value = true
  try {
    workflow.value = await workflowApi.get(workflowId)
  } catch (error) {
    ElMessage.error('获取工作流详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 执行工作流
 */
async function handleExecute() {
  if (!workflow.value) return

  try {
    execution.value = await workflowApi.execute(workflow.value.workflow_id)
    ElMessage.success('工作流已开始执行')
  } catch (error) {
    ElMessage.error('执行工作流失败')
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
    completed: 'info',
    failed: 'danger',
    running: 'success',
    pending: 'info',
    cancelled: 'warning',
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
    running: '执行中',
    pending: '待执行',
    cancelled: '已取消',
  }
  return map[status] || status
}

onMounted(loadWorkflow)
</script>

<template>
  <div class="workflow-detail-view">
    <div class="page-header">
      <el-button @click="router.push('/workflows')">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>工作流详情</h2>
      <el-button
        v-if="workflow?.status === 'draft' || workflow?.status === 'active'"
        type="primary"
        @click="handleExecute"
      >
        执行工作流
      </el-button>
    </div>

    <el-row :gutter="20">
      <!-- 基本信息 -->
      <el-col :span="12">
        <el-card v-loading="loading">
          <template #header>
            <span>基本信息</span>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="ID">{{ workflow?.workflow_id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ workflow?.name }}</el-descriptions-item>
            <el-descriptions-item label="描述">{{ workflow?.description || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(workflow?.status || '')" size="small">
                {{ getStatusLabel(workflow?.status || '') }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ workflow?.created_at }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ workflow?.updated_at }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 执行状态 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>执行状态</span>
          </template>

          <div v-if="execution">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="执行ID">{{ execution.execution_id }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(execution.status)" size="small">
                  {{ getStatusLabel(execution.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="当前步骤">{{ execution.current_step || '-' }}</el-descriptions-item>
              <el-descriptions-item label="进度">
                <el-progress :percentage="execution.progress" />
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ execution.started_at || '-' }}</el-descriptions-item>
              <el-descriptions-item label="完成时间">{{ execution.completed_at || '-' }}</el-descriptions-item>
              <el-descriptions-item v-if="execution.error" label="错误信息">
                <el-text type="danger">{{ execution.error }}</el-text>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="暂无执行记录" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 工作流步骤 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>工作流步骤</span>
      </template>

      <el-table :data="workflow?.steps || []" style="width: 100%">
        <el-table-column prop="step_id" label="步骤ID" width="150" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="agent_type" label="Agent类型" width="120" />
        <el-table-column prop="dependencies" label="依赖" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="dep in row.dependencies" :key="dep" size="small" class="dep-tag">
              {{ dep }}
            </el-tag>
            <span v-if="!row.dependencies?.length">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.workflow-detail-view {
  padding: 0;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  flex: 1;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.dep-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}
</style>
