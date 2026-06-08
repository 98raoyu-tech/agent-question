<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { governanceApi } from '@/api'
import type { PolicyDefinition, AuditLog } from '@/types'
import { PolicyType, PolicyStatus, AuditLogLevel } from '@/types'

const loading = ref(false)
const policyList = ref<PolicyDefinition[]>([])
const auditLogList = ref<AuditLog[]>([])
const activeTab = ref('policies')
const createPolicyDialogVisible = ref(false)

const policyPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const logPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const createPolicyForm = reactive({
  name: '',
  description: '',
  policy_type: PolicyType.ACCESS_CONTROL,
  rules: {},
  priority: 0,
  applies_to: [] as string[],
})

async function loadData() {
  loading.value = true
  try {
    await Promise.all([
      loadPolicyList(),
      loadAuditLogList(),
    ])
  } finally {
    loading.value = false
  }
}

async function loadPolicyList() {
  try {
    const res = await governanceApi.listPolicies({
      page: policyPagination.page,
      page_size: policyPagination.pageSize,
    })
    policyList.value = res.items
    policyPagination.total = res.total
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

async function loadAuditLogList() {
  try {
    const res = await governanceApi.listAuditLogs({
      page: logPagination.page,
      page_size: logPagination.pageSize,
    })
    auditLogList.value = res.items
    logPagination.total = res.total
  } catch (error) {
    console.error('加载审计日志失败:', error)
  }
}

async function handleCreatePolicy() {
  try {
    await governanceApi.createPolicy(createPolicyForm)
    ElMessage.success('创建成功')
    createPolicyDialogVisible.value = false
    loadPolicyList()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function handleTogglePolicy(policy: PolicyDefinition) {
  try {
    const newStatus = policy.status === PolicyStatus.ACTIVE ? false : true
    await governanceApi.togglePolicy(policy.policy_id, newStatus)
    ElMessage.success('操作成功')
    loadPolicyList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleDeletePolicy(policy: PolicyDefinition) {
  try {
    await ElMessageBox.confirm(`确定要删除策略 "${policy.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await governanceApi.deletePolicy(policy.policy_id)
    ElMessage.success('删除成功')
    loadPolicyList()
  } catch {}
}

async function handleExportAuditLogs() {
  try {
    await governanceApi.exportAuditLogs()
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

function getPolicyTypeLabel(type: PolicyType) {
  const map: Record<string, string> = {
    [PolicyType.ACCESS_CONTROL]: '访问控制',
    [PolicyType.DATA_PRIVACY]: '数据隐私',
    [PolicyType.CONTENT_FILTER]: '内容过滤',
    [PolicyType.RATE_LIMIT]: '速率限制',
    [PolicyType.COST_CONTROL]: '成本控制',
    [PolicyType.CUSTOM]: '自定义',
  }
  return map[type] || type
}

function getPolicyStatusLabel(status: PolicyStatus) {
  const map: Record<string, string> = {
    [PolicyStatus.ACTIVE]: '启用',
    [PolicyStatus.INACTIVE]: '禁用',
    [PolicyStatus.DRAFT]: '草稿',
  }
  return map[status] || status
}

function getPolicyStatusType(status: PolicyStatus): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [PolicyStatus.ACTIVE]: 'success',
    [PolicyStatus.INACTIVE]: 'info',
    [PolicyStatus.DRAFT]: 'warning',
  }
  return map[status] || 'info'
}

function getLogLevelLabel(level: AuditLogLevel) {
  const map: Record<string, string> = {
    [AuditLogLevel.INFO]: '信息',
    [AuditLogLevel.WARNING]: '警告',
    [AuditLogLevel.ERROR]: '错误',
    [AuditLogLevel.CRITICAL]: '严重',
  }
  return map[level] || level
}

function getLogLevelType(level: AuditLogLevel): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [AuditLogLevel.INFO]: 'info',
    [AuditLogLevel.WARNING]: 'warning',
    [AuditLogLevel.ERROR]: 'danger',
    [AuditLogLevel.CRITICAL]: 'danger',
  }
  return map[level] || 'info'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(loadData)
</script>

<template>
  <div class="governance-view">
    <div class="page-header">
      <h2>治理中心</h2>
      <div class="header-actions">
        <el-button @click="handleExportAuditLogs">
          <el-icon><Download /></el-icon>
          导出日志
        </el-button>
        <el-button type="primary" @click="createPolicyDialogVisible = true">
          <el-icon><Plus /></el-icon>
          创建策略
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="governance-tabs">
      <!-- 策略管理 -->
      <el-tab-pane label="策略管理" name="policies">
        <el-card>
          <el-table :data="policyList" v-loading="loading" style="width: 100%">
            <el-table-column prop="name" label="策略名称" min-width="150" />
            <el-table-column prop="policy_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getPolicyTypeLabel(row.policy_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getPolicyStatusType(row.status)" size="small">
                  {{ getPolicyStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80" />
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  :type="row.status === PolicyStatus.ACTIVE ? 'warning' : 'success'"
                  link
                  size="small"
                  @click="handleTogglePolicy(row as PolicyDefinition)"
                >
                  {{ row.status === PolicyStatus.ACTIVE ? '禁用' : '启用' }}
                </el-button>
                <el-button type="danger" link size="small" @click="handleDeletePolicy(row as PolicyDefinition)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="policyPagination.page"
              v-model:page-size="policyPagination.pageSize"
              :page-sizes="[10, 20, 50]"
              :total="policyPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="loadPolicyList"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 审计日志 -->
      <el-tab-pane label="审计日志" name="audit-logs">
        <el-card>
          <el-table :data="auditLogList" style="width: 100%">
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getLogLevelType(row.level)" size="small">
                  {{ getLogLevelLabel(row.level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="操作" width="150" />
            <el-table-column prop="resource_type" label="资源类型" width="120" />
            <el-table-column prop="user_name" label="用户" width="120" />
            <el-table-column prop="ip_address" label="IP地址" width="140" />
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="logPagination.page"
              v-model:page-size="logPagination.pageSize"
              :page-sizes="[10, 20, 50]"
              :total="logPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="loadAuditLogList"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建策略对话框 -->
    <el-dialog v-model="createPolicyDialogVisible" title="创建策略" width="600px">
      <el-form :model="createPolicyForm" label-width="100px">
        <el-form-item label="策略名称" required>
          <el-input v-model="createPolicyForm.name" placeholder="请输入策略名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createPolicyForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="策略类型" required>
          <el-select v-model="createPolicyForm.policy_type" placeholder="选择策略类型">
            <el-option
              v-for="type in Object.values(PolicyType)"
              :key="type"
              :label="getPolicyTypeLabel(type)"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="createPolicyForm.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createPolicyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreatePolicy">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.governance-view {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.governance-tabs {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
