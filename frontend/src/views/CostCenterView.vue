<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { costApi } from '@/api'
import type { CostUsage, CostBudget, CostAlert, CostStatistics } from '@/types'

const loading = ref(false)
const usageList = ref<CostUsage[]>([])
const budgetList = ref<CostBudget[]>([])
const alertList = ref<CostAlert[]>([])
const statistics = ref<CostStatistics | null>(null)
const createBudgetDialogVisible = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const budgetPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const createBudgetForm = reactive({
  name: '',
  description: '',
  amount: 0,
  currency: 'CNY',
  period: 'monthly',
  alert_threshold: 80,
})

async function loadData() {
  loading.value = true
  try {
    await Promise.all([
      loadUsageList(),
      loadBudgetList(),
      loadAlerts(),
      loadStatistics(),
    ])
  } finally {
    loading.value = false
  }
}

async function loadUsageList() {
  try {
    const res = await costApi.listUsage({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    usageList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载使用记录失败:', error)
  }
}

async function loadBudgetList() {
  try {
    const res = await costApi.listBudgets({
      page: budgetPagination.page,
      page_size: budgetPagination.pageSize,
    })
    budgetList.value = res.items
    budgetPagination.total = res.total
  } catch (error) {
    console.error('加载预算列表失败:', error)
  }
}

async function loadAlerts() {
  try {
    const res = await costApi.listAlerts()
    alertList.value = res.items
  } catch (error) {
    console.error('加载告警列表失败:', error)
  }
}

async function loadStatistics() {
  try {
    statistics.value = await costApi.getStatistics()
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

async function handleCreateBudget() {
  try {
    await costApi.createBudget(createBudgetForm)
    ElMessage.success('创建成功')
    createBudgetDialogVisible.value = false
    loadBudgetList()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function handleDeleteBudget(budget: CostBudget) {
  try {
    await ElMessageBox.confirm(`确定要删除预算 "${budget.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await costApi.deleteBudget(budget.budget_id)
    ElMessage.success('删除成功')
    loadBudgetList()
  } catch {}
}

async function handleMarkAlertRead(alert: CostAlert) {
  try {
    await costApi.markAlertRead(alert.alert_id)
    ElMessage.success('已标记已读')
    loadAlerts()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function formatCurrency(amount: number, currency: string = 'CNY') {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
  }).format(amount)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getBudgetUsagePercentage(budget: CostBudget) {
  if (budget.amount === 0) return 0
  return Math.round((budget.used_amount / budget.amount) * 100)
}

function getBudgetStatusColor(budget: CostBudget) {
  const percentage = getBudgetUsagePercentage(budget)
  if (percentage >= 100) return '#f56c6c'
  if (percentage >= budget.alert_threshold) return '#e6a23c'
  return '#67c23a'
}

onMounted(loadData)
</script>

<template>
  <div class="cost-center-view">
    <div class="page-header">
      <h2>成本中心</h2>
      <el-button type="primary" @click="createBudgetDialogVisible = true">
        <el-icon><Plus /></el-icon>
        创建预算
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6f7ff">
            <el-icon :size="28" color="#1890ff"><Wallet /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatCurrency(statistics?.total_cost || 0) }}</div>
            <div class="stat-label">总成本</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f6ffed">
            <el-icon :size="28" color="#52c41a"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatCurrency(statistics?.period_cost || 0) }}</div>
            <div class="stat-label">本月成本</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fff7e6">
            <el-icon :size="28" color="#fa8c16"><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ alertList.filter(a => a.is_triggered).length }}</div>
            <div class="stat-label">触发告警</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 预算管理 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <span>预算管理</span>
          </template>

          <div class="budget-list">
            <div v-for="budget in budgetList" :key="budget.budget_id" class="budget-item">
              <div class="budget-header">
                <span class="budget-name">{{ budget.name }}</span>
                <el-button type="danger" link size="small" @click="handleDeleteBudget(budget)">删除</el-button>
              </div>
              <div class="budget-progress">
                <el-progress
                  :percentage="getBudgetUsagePercentage(budget)"
                  :color="getBudgetStatusColor(budget)"
                  :stroke-width="10"
                />
              </div>
              <div class="budget-meta">
                <span>{{ formatCurrency(budget.used_amount) }} / {{ formatCurrency(budget.amount) }}</span>
                <span>{{ budget.period === 'monthly' ? '月度' : '年度' }}</span>
              </div>
            </div>
            <el-empty v-if="budgetList.length === 0" description="暂无预算" />
          </div>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="budgetPagination.page"
              v-model:page-size="budgetPagination.pageSize"
              :total="budgetPagination.total"
              layout="total, prev, pager, next"
              small
              @current-change="loadBudgetList"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 成本告警 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <span>成本告警</span>
          </template>

          <div class="alert-list">
            <div
              v-for="alert in alertList"
              :key="alert.alert_id"
              class="alert-item"
              :class="{ triggered: alert.is_triggered }"
            >
              <div class="alert-header">
                <span class="alert-name">{{ alert.budget_name }}</span>
                <el-tag :type="alert.is_triggered ? 'danger' : 'info'" size="small">
                  {{ alert.is_triggered ? '已触发' : '正常' }}
                </el-tag>
              </div>
              <div class="alert-meta">
                <span>阈值: {{ alert.threshold_percentage }}%</span>
                <span>当前: {{ alert.current_percentage }}%</span>
                <el-button
                  v-if="alert.is_triggered && !alert.notified"
                  type="primary"
                  link
                  size="small"
                  @click="handleMarkAlertRead(alert)"
                >标记已读</el-button>
              </div>
            </div>
            <el-empty v-if="alertList.length === 0" description="暂无告警" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 使用记录 -->
    <el-card class="table-card">
      <template #header>
        <span>Token 使用记录</span>
      </template>

      <el-table :data="usageList" style="width: 100%">
        <el-table-column prop="agent_name" label="Agent" width="120" />
        <el-table-column prop="model" label="模型" width="120" />
        <el-table-column prop="input_tokens" label="输入Token" width="100" />
        <el-table-column prop="output_tokens" label="输出Token" width="100" />
        <el-table-column prop="cost" label="成本" width="100">
          <template #default="{ row }">{{ formatCurrency(row.cost, row.currency) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadUsageList"
        />
      </div>
    </el-card>

    <!-- 创建预算对话框 -->
    <el-dialog v-model="createBudgetDialogVisible" title="创建预算" width="500px">
      <el-form :model="createBudgetForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="createBudgetForm.name" placeholder="请输入预算名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createBudgetForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="createBudgetForm.amount" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="周期">
          <el-select v-model="createBudgetForm.period">
            <el-option label="月度" value="monthly" />
            <el-option label="年度" value="yearly" />
          </el-select>
        </el-form-item>
        <el-form-item label="告警阈值">
          <el-slider v-model="createBudgetForm.alert_threshold" :max="100" :format-tooltip="(val: number) => `${val}%`" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createBudgetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateBudget">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.cost-center-view {
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

.stats-row {
  margin-bottom: 20px;
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

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.section-card {
  height: 400px;
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.section-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
}

.budget-list,
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.budget-item,
.alert-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.alert-item.triggered {
  border-color: #f56c6c;
  background: #fef0f0;
}

.budget-header,
.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.budget-name,
.alert-name {
  font-weight: 500;
  color: #303133;
}

.budget-progress {
  margin-bottom: 8px;
}

.budget-meta,
.alert-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
