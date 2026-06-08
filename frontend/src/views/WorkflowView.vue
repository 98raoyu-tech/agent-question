<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const workflowStore = useWorkflowStore()

/** 创建对话框可见性 */
const createDialogVisible = ref(false)

/** 新工作流表单 */
const newWorkflow = ref({
  name: '',
  description: '',
  steps: [] as Array<{
    step_id: string
    name: string
    agent_type: string
    dependencies: string[]
  }>,
})

/**
 * 加载工作流列表
 */
async function loadWorkflows() {
  await workflowStore.fetchWorkflows()
}

/**
 * 创建工作流
 */
async function handleCreate() {
  if (!newWorkflow.value.name) return

  await workflowStore.fetchWorkflows()
  createDialogVisible.value = false
  resetForm()
}

/**
 * 执行工作流
 */
async function handleExecute(workflowId: string) {
  try {
    await ElMessageBox.confirm('确定要执行此工作流吗？', '确认', {
      type: 'info',
    })
    await workflowStore.executeWorkflow(workflowId)
  } catch {
    // 用户取消
  }
}

/**
 * 查看详情
 */
function handleViewDetail(workflowId: string) {
  router.push(`/workflows/${workflowId}`)
}

/**
 * 重置表单
 */
function resetForm() {
  newWorkflow.value = {
    name: '',
    description: '',
    steps: [],
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

onMounted(loadWorkflows)
</script>

<template>
  <div class="workflow-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>工作流管理</h2>
      <el-button type="primary" @click="createDialogVisible = true">
        <el-icon><Plus /></el-icon>
        创建工作流
      </el-button>
    </div>

    <!-- 工作流列表 -->
    <el-card>
      <el-table
        v-loading="workflowStore.loading"
        :data="workflowStore.workflows"
        style="width: 100%"
      >
        <el-table-column prop="workflow_id" label="ID" width="150" />
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="steps" label="步骤数" width="80">
          <template #default="{ row }">
            {{ row.steps?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row.workflow_id)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'draft' || row.status === 'active'"
              type="success"
              link
              size="small"
              @click="handleExecute(row.workflow_id)"
            >
              执行
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建工作流对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建工作流"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="newWorkflow" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="newWorkflow.name" placeholder="请输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newWorkflow.description"
            type="textarea"
            :rows="3"
            placeholder="请输入工作流描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.workflow-view {
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
</style>
