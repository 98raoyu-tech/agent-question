<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { evaluationApi } from '@/api'
import type { EvaluationDataset, EvaluationRun, EvaluationScore } from '@/types'
import { EvaluationRunStatus } from '@/types'

const loading = ref(false)
const datasetList = ref<EvaluationDataset[]>([])
const runList = ref<EvaluationRun[]>([])
const createDatasetDialogVisible = ref(false)
const createRunDialogVisible = ref(false)
const scoresDialogVisible = ref(false)
const currentScores = ref<EvaluationScore[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const runPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const createDatasetForm = reactive({
  name: '',
  description: '',
})

const createRunForm = reactive({
  dataset_id: '',
  agent_id: '',
})

async function loadDatasetList() {
  loading.value = true
  try {
    const res = await evaluationApi.listDatasets({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    datasetList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载数据集列表失败:', error)
    ElMessage.error('加载数据集列表失败')
  } finally {
    loading.value = false
  }
}

async function loadRunList() {
  try {
    const res = await evaluationApi.listRuns({
      page: runPagination.page,
      page_size: runPagination.pageSize,
    })
    runList.value = res.items
    runPagination.total = res.total
  } catch (error) {
    console.error('加载评测运行列表失败:', error)
  }
}

async function handleCreateDataset() {
  try {
    await evaluationApi.createDataset(createDatasetForm)
    ElMessage.success('创建成功')
    createDatasetDialogVisible.value = false
    loadDatasetList()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function handleDeleteDataset(dataset: EvaluationDataset) {
  try {
    await ElMessageBox.confirm(`确定要删除数据集 "${dataset.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await evaluationApi.deleteDataset(dataset.dataset_id)
    ElMessage.success('删除成功')
    loadDatasetList()
  } catch {}
}

async function handleCreateRun() {
  try {
    await evaluationApi.createRun(createRunForm)
    ElMessage.success('评测任务已提交')
    createRunDialogVisible.value = false
    loadRunList()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function handleCancelRun(run: EvaluationRun) {
  try {
    await ElMessageBox.confirm('确定要取消该评测运行吗？', '取消确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await evaluationApi.cancelRun(run.run_id)
    ElMessage.success('已取消')
    loadRunList()
  } catch {}
}

async function handleViewScores(run: EvaluationRun) {
  try {
    const res = await evaluationApi.getScores(run.run_id)
    currentScores.value = res.items
    scoresDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取评分失败')
  }
}

function getRunStatusLabel(status: EvaluationRunStatus) {
  const map: Record<string, string> = {
    [EvaluationRunStatus.PENDING]: '待执行',
    [EvaluationRunStatus.RUNNING]: '运行中',
    [EvaluationRunStatus.COMPLETED]: '已完成',
    [EvaluationRunStatus.FAILED]: '失败',
    [EvaluationRunStatus.CANCELLED]: '已取消',
  }
  return map[status] || status
}

function getRunStatusType(status: EvaluationRunStatus): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [EvaluationRunStatus.PENDING]: 'info',
    [EvaluationRunStatus.RUNNING]: 'warning',
    [EvaluationRunStatus.COMPLETED]: 'success',
    [EvaluationRunStatus.FAILED]: 'danger',
    [EvaluationRunStatus.CANCELLED]: 'info',
  }
  return map[status] || 'info'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadDatasetList()
  loadRunList()
})
</script>

<template>
  <div class="evaluation-center-view">
    <div class="page-header">
      <h2>评估中心</h2>
      <div class="header-actions">
        <el-button type="primary" @click="createDatasetDialogVisible = true">
          <el-icon><Plus /></el-icon>
          创建数据集
        </el-button>
        <el-button type="success" @click="createRunDialogVisible = true">
          <el-icon><VideoPlay /></el-icon>
          创建评测
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 评测数据集 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <span>评测数据集</span>
          </template>

          <el-table :data="datasetList" v-loading="loading" style="width: 100%">
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="item_count" label="条目数" width="80" />
            <el-table-column prop="created_at" label="创建时间" width="150">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="danger" link size="small" @click="handleDeleteDataset(row as EvaluationDataset)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              layout="total, prev, pager, next"
              small
              @current-change="loadDatasetList"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 评测运行列表 -->
      <el-col :span="12">
        <el-card class="section-card">
          <template #header>
            <span>评测运行</span>
          </template>

          <el-table :data="runList" style="width: 100%">
            <el-table-column prop="run_id" label="运行ID" width="100" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getRunStatusType(row.status)" size="small">
                  {{ getRunStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="150">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleViewScores(row as EvaluationRun)">评分</el-button>
                <el-button
                  v-if="row.status === EvaluationRunStatus.PENDING || row.status === EvaluationRunStatus.RUNNING"
                  type="warning"
                  link
                  size="small"
                  @click="handleCancelRun(row as EvaluationRun)"
                >取消</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="runPagination.page"
              v-model:page-size="runPagination.pageSize"
              :total="runPagination.total"
              layout="total, prev, pager, next"
              small
              @current-change="loadRunList"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建数据集对话框 -->
    <el-dialog v-model="createDatasetDialogVisible" title="创建数据集" width="500px">
      <el-form :model="createDatasetForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createDatasetForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createDatasetForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDatasetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateDataset">确定</el-button>
      </template>
    </el-dialog>

    <!-- 创建评测对话框 -->
    <el-dialog v-model="createRunDialogVisible" title="创建评测运行" width="500px">
      <el-form :model="createRunForm" label-width="80px">
        <el-form-item label="数据集" required>
          <el-select v-model="createRunForm.dataset_id" placeholder="选择数据集">
            <el-option
              v-for="ds in datasetList"
              :key="ds.dataset_id"
              :label="ds.name"
              :value="ds.dataset_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Agent ID" required>
          <el-input v-model="createRunForm.agent_id" placeholder="请输入Agent ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createRunDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateRun">确定</el-button>
      </template>
    </el-dialog>

    <!-- 评分详情对话框 -->
    <el-dialog v-model="scoresDialogVisible" title="评测评分" width="600px">
      <el-table :data="currentScores" style="width: 100%">
        <el-table-column prop="metric_name" label="指标名称" />
        <el-table-column prop="value" label="得分" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.value >= 0.8 ? '#67c23a' : row.value >= 0.6 ? '#e6a23c' : '#f56c6c' }">
              {{ (row.value * 100).toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="80" />
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.evaluation-center-view {
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

.section-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.section-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
