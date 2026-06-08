<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { approvalApi } from '@/api'
import type { ApprovalRequest } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'

/** 待审核列表 */
const approvals = ref<ApprovalRequest[]>([])

/** 加载状态 */
const loading = ref(false)

/**
 * 加载待审核列表
 */
async function loadApprovals() {
  loading.value = true
  try {
    const res = await approvalApi.list()
    approvals.value = res.items
  } catch (error) {
    ElMessage.error('获取审核列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 审核通过
 */
async function handleApprove(requestId: string) {
  try {
    await ElMessageBox.confirm('确定要通过此审核吗？', '确认', { type: 'info' })
    await approvalApi.approve(requestId)
    ElMessage.success('审核已通过')
    await loadApprovals()
  } catch {
    // 用户取消
  }
}

/**
 * 审核拒绝
 */
async function handleReject(requestId: string) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝审核', {
      inputType: 'textarea',
      inputPlaceholder: '请输入拒绝原因',
    })
    await approvalApi.reject(requestId, { reason: value })
    ElMessage.success('审核已拒绝')
    await loadApprovals()
  } catch {
    // 用户取消
  }
}

/**
 * 获取风险等级标签类型
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getRiskLevelType(level: string): TagType {
  const map: Record<string, TagType> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger',
  }
  return map[level] || 'info'
}

onMounted(loadApprovals)
</script>

<template>
  <div class="approval-view">
    <div class="page-header">
      <h2>审核中心</h2>
      <el-button @click="loadApprovals">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-card>
      <el-table v-loading="loading" :data="approvals" style="width: 100%">
        <el-table-column prop="request_id" label="请求ID" width="150" />
        <el-table-column prop="action_description" label="操作描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getRiskLevelType(row.risk_level)" size="small">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="execution_id" label="执行ID" width="150" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="expires_at" label="过期时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link size="small" @click="handleApprove(row.request_id)">
              通过
            </el-button>
            <el-button type="danger" link size="small" @click="handleReject(row.request_id)">
              拒绝
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!approvals.length && !loading" description="暂无待审核项目" />
    </el-card>
  </div>
</template>

<style scoped>
.approval-view {
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
