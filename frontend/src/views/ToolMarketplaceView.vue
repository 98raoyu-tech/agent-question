<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { toolMarketplaceApi } from '@/api'
import type { ToolDefinition, ToolReview } from '@/types'
import { ToolStatus, ToolInstallStatus } from '@/types'

const loading = ref(false)
const toolList = ref<ToolDefinition[]>([])
const reviewList = ref<ToolReview[]>([])
const activeTab = ref('marketplace')
const detailDialogVisible = ref(false)
const currentTool = ref<ToolDefinition | null>(null)

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0,
})

const reviewPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const searchKeyword = ref('')
const categoryFilter = ref('')

async function loadToolList() {
  loading.value = true
  try {
    const res = await toolMarketplaceApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchKeyword.value || undefined,
      category: categoryFilter.value || undefined,
    })
    toolList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

async function loadReviewList() {
  try {
    const res = await toolMarketplaceApi.listReviews({
      page: reviewPagination.page,
      page_size: reviewPagination.pageSize,
    })
    reviewList.value = res.items
    reviewPagination.total = res.total
  } catch (error) {
    console.error('加载审核列表失败:', error)
  }
}

function handleSearch() {
  pagination.page = 1
  loadToolList()
}

function handleViewDetail(tool: ToolDefinition) {
  currentTool.value = tool
  detailDialogVisible.value = true
}

async function handleInstallTool(tool: ToolDefinition) {
  try {
    await ElMessageBox.confirm(`确定要安装工具 "${tool.name}" 吗？`, '安装确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await toolMarketplaceApi.install(tool.tool_id)
    ElMessage.success('安装成功')
    loadToolList()
  } catch {}
}

async function handleUninstallTool(tool: ToolDefinition) {
  try {
    await ElMessageBox.confirm(`确定要卸载工具 "${tool.name}" 吗？`, '卸载确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await toolMarketplaceApi.uninstall(tool.tool_id)
    ElMessage.success('卸载成功')
    loadToolList()
  } catch {}
}

async function handleReviewTool(review: ToolReview, approved: boolean) {
  try {
    await ElMessageBox.prompt(
      approved ? '请输入审核意见（可选）' : '请输入拒绝原因',
      approved ? '审核通过' : '审核拒绝',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      }
    ).then(async ({ value }) => {
      await toolMarketplaceApi.reviewTool(review.review_id, {
        approved,
        comment: value,
      })
      ElMessage.success('审核完成')
      loadReviewList()
    })
  } catch {}
}

function getStatusLabel(status: ToolStatus) {
  const map: Record<string, string> = {
    [ToolStatus.DRAFT]: '草稿',
    [ToolStatus.REVIEWING]: '审核中',
    [ToolStatus.PUBLISHED]: '已发布',
    [ToolStatus.DEPRECATED]: '已弃用',
  }
  return map[status] || status
}

function getStatusType(status: ToolStatus): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [ToolStatus.DRAFT]: 'info',
    [ToolStatus.REVIEWING]: 'warning',
    [ToolStatus.PUBLISHED]: 'success',
    [ToolStatus.DEPRECATED]: 'info',
  }
  return map[status] || 'info'
}

function getInstallStatusLabel(status?: ToolInstallStatus) {
  const map: Record<string, string> = {
    [ToolInstallStatus.NOT_INSTALLED]: '未安装',
    [ToolInstallStatus.INSTALLING]: '安装中',
    [ToolInstallStatus.INSTALLED]: '已安装',
    [ToolInstallStatus.FAILED]: '安装失败',
  }
  return status ? map[status] || '未安装' : '未安装'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadToolList()
  loadReviewList()
})
</script>

<template>
  <div class="tool-marketplace-view">
    <div class="page-header">
      <h2>工具市场</h2>
    </div>

    <el-tabs v-model="activeTab" class="marketplace-tabs">
      <!-- 工具市场 -->
      <el-tab-pane label="工具市场" name="marketplace">
        <!-- 搜索和过滤 -->
        <el-card class="filter-card">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索工具名称或描述"
                clearable
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-input v-model="categoryFilter" placeholder="输入分类" clearable @change="handleSearch" />
            </el-col>
            <el-col :span="4">
              <el-button type="primary" @click="handleSearch">搜索</el-button>
            </el-col>
          </el-row>
        </el-card>

        <!-- 工具卡片列表 -->
        <div v-loading="loading" class="tool-grid">
          <el-card
            v-for="tool in toolList"
            :key="tool.tool_id"
            class="tool-card"
            shadow="hover"
            @click="handleViewDetail(tool)"
          >
            <div class="tool-header">
              <div class="tool-icon">
                <el-icon :size="32"><SetUp /></el-icon>
              </div>
              <div class="tool-info">
                <div class="tool-name">{{ tool.name }}</div>
                <div class="tool-author">{{ tool.author }}</div>
              </div>
            </div>
            <div class="tool-description">{{ tool.description }}</div>
            <div class="tool-meta">
              <div class="tool-stats">
                <span><el-icon><Download /></el-icon> {{ tool.download_count }}</span>
                <span><el-icon><Star /></el-icon> {{ tool.rating.toFixed(1) }}</span>
              </div>
              <div class="tool-actions">
                <el-button
                  v-if="tool.install_status === ToolInstallStatus.INSTALLED"
                  type="danger"
                  size="small"
                  @click.stop="handleUninstallTool(tool)"
                >卸载</el-button>
                <el-button
                  v-else
                  type="primary"
                  size="small"
                  @click.stop="handleInstallTool(tool)"
                >安装</el-button>
              </div>
            </div>
          </el-card>
        </div>

        <el-empty v-if="!loading && toolList.length === 0" description="暂无工具" />

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[12, 24, 48]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="loadToolList"
          />
        </div>
      </el-tab-pane>

      <!-- 工具审核 -->
      <el-tab-pane label="工具审核" name="reviews">
        <el-card>
          <el-table :data="reviewList" style="width: 100%">
            <el-table-column prop="tool_name" label="工具名称" min-width="150" />
            <el-table-column prop="version" label="版本" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'" size="small">
                  {{ row.status === 'approved' ? '已通过' : row.status === 'rejected' ? '已拒绝' : '待审核' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="submitted_by" label="提交者" width="120" />
            <el-table-column prop="submitted_at" label="提交时间" width="180">
              <template #default="{ row }">{{ formatDate(row.submitted_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button type="success" link size="small" @click="handleReviewTool(row as ToolReview, true)">通过</el-button>
                  <el-button type="danger" link size="small" @click="handleReviewTool(row as ToolReview, false)">拒绝</el-button>
                </template>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="reviewPagination.page"
              v-model:page-size="reviewPagination.pageSize"
              :total="reviewPagination.total"
              layout="total, prev, pager, next"
              @current-change="loadReviewList"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 工具详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="工具详情" width="600px">
      <template v-if="currentTool">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentTool.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ currentTool.version }}</el-descriptions-item>
          <el-descriptions-item label="作者">{{ currentTool.author }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ currentTool.category }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTool.status)" size="small">
              {{ getStatusLabel(currentTool.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="安装状态">
            {{ getInstallStatusLabel(currentTool.install_status) }}
          </el-descriptions-item>
          <el-descriptions-item label="下载量">{{ currentTool.download_count }}</el-descriptions-item>
          <el-descriptions-item label="评分">{{ currentTool.rating.toFixed(1) }} ({{ currentTool.rating_count }}条评价)</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentTool.description }}</el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag v-for="tag in currentTool.tags" :key="tag" size="small" class="tag-item">{{ tag }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <template v-if="currentTool">
          <el-button
            v-if="currentTool.install_status === ToolInstallStatus.INSTALLED"
            type="danger"
            @click="handleUninstallTool(currentTool); detailDialogVisible = false"
          >卸载</el-button>
          <el-button
            v-else
            type="primary"
            @click="handleInstallTool(currentTool); detailDialogVisible = false"
          >安装</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tool-marketplace-view {
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

.marketplace-tabs {
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.tool-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.tool-card:hover {
  transform: translateY(-2px);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.tool-icon {
  width: 48px;
  height: 48px;
  background: #ecf5ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
}

.tool-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.tool-author {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.tool-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tool-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.tool-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
