<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '@/api'
import type { KnowledgeSource, KnowledgeDocument, KnowledgeSearchResult } from '@/types'
import { KnowledgeSourceType, DocumentStatus } from '@/types'

/** 加载状态 */
const loading = ref(false)

/** 知识源列表 */
const sourceList = ref<KnowledgeSource[]>([])

/** 文档列表 */
const documentList = ref<KnowledgeDocument[]>([])

/** 当前选中的知识源 */
const currentSource = ref<KnowledgeSource | null>(null)

/** 分页参数 */
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

/** 文档分页参数 */
const documentPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

/** 创建知识源对话框可见性 */
const createSourceDialogVisible = ref(false)

/** 上传文档对话框可见性 */
const uploadDialogVisible = ref(false)

/** 搜索测试对话框可见性 */
const searchDialogVisible = ref(false)

/** 创建知识源表单 */
const createSourceForm = reactive({
  name: '',
  source_type: KnowledgeSourceType.FILE,
  config: {},
})

/** 搜索关键词 */
const searchKeyword = ref('')

/** 搜索结果 */
const searchResults = ref<KnowledgeSearchResult[]>([])

/** 搜索加载状态 */
const searchLoading = ref(false)

/** 加载知识源列表 */
async function loadSourceList() {
  loading.value = true
  try {
    const res = await knowledgeApi.listSources({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    sourceList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载知识源列表失败:', error)
    ElMessage.error('加载知识源列表失败')
  } finally {
    loading.value = false
  }
}

/** 加载文档列表 */
async function loadDocumentList(sourceId: string) {
  try {
    const res = await knowledgeApi.listDocuments({
      source_id: sourceId,
      page: documentPagination.page,
      page_size: documentPagination.pageSize,
    })
    documentList.value = res.items
    documentPagination.total = res.total
  } catch (error) {
    console.error('加载文档列表失败:', error)
  }
}

/** 选择知识源 */
function handleSelectSource(source: KnowledgeSource) {
  currentSource.value = source
  documentPagination.page = 1
  loadDocumentList(source.source_id)
}

/** 打开创建知识源对话框 */
function handleOpenCreateSourceDialog() {
  createSourceForm.name = ''
  createSourceForm.source_type = KnowledgeSourceType.FILE
  createSourceForm.config = {}
  createSourceDialogVisible.value = true
}

/** 创建知识源 */
async function handleCreateSource() {
  try {
    await knowledgeApi.createSource(createSourceForm)
    ElMessage.success('创建成功')
    createSourceDialogVisible.value = false
    loadSourceList()
  } catch (error) {
    console.error('创建知识源失败:', error)
    ElMessage.error('创建失败')
  }
}

/** 同步知识源 */
async function handleSyncSource(source: KnowledgeSource) {
  try {
    await knowledgeApi.syncSource(source.source_id)
    ElMessage.success('同步任务已提交')
    loadSourceList()
  } catch (error) {
    console.error('同步失败:', error)
    ElMessage.error('同步失败')
  }
}

/** 删除知识源 */
async function handleDeleteSource(source: KnowledgeSource) {
  try {
    await ElMessageBox.confirm(`确定要删除知识源 "${source.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await knowledgeApi.deleteSource(source.source_id)
    ElMessage.success('删除成功')
    if (currentSource.value?.source_id === source.source_id) {
      currentSource.value = null
      documentList.value = []
    }
    loadSourceList()
  } catch {
    // 用户取消
  }
}

/** 打开上传文档对话框 */
function handleOpenUploadDialog() {
  if (!currentSource.value) {
    ElMessage.warning('请先选择知识源')
    return
  }
  uploadDialogVisible.value = true
}

/** 上传文档 */
async function handleUploadDocument(file: File) {
  if (!currentSource.value) return
  try {
    await knowledgeApi.uploadDocument(currentSource.value.source_id, file)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    loadDocumentList(currentSource.value.source_id)
  } catch (error) {
    console.error('上传文档失败:', error)
    ElMessage.error('上传失败')
  }
}

/** 删除文档 */
async function handleDeleteDocument(doc: KnowledgeDocument) {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${doc.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await knowledgeApi.deleteDocument(doc.document_id)
    ElMessage.success('删除成功')
    if (currentSource.value) {
      loadDocumentList(currentSource.value.source_id)
    }
  } catch {
    // 用户取消
  }
}

/** 打开搜索测试对话框 */
function handleOpenSearchDialog() {
  searchKeyword.value = ''
  searchResults.value = []
  searchDialogVisible.value = true
}

/** 执行知识搜索 */
async function handleSearch() {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  searchLoading.value = true
  try {
    const res = await knowledgeApi.search({
      query: searchKeyword.value,
      top_k: 10,
    })
    searchResults.value = res.results
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

/** 获取知识源类型标签 */
function getSourceTypeLabel(type: KnowledgeSourceType) {
  const map: Record<string, string> = {
    [KnowledgeSourceType.FILE]: '文件',
    [KnowledgeSourceType.URL]: 'URL',
    [KnowledgeSourceType.DATABASE]: '数据库',
    [KnowledgeSourceType.API]: 'API',
    [KnowledgeSourceType.MANUAL]: '手动',
  }
  return map[type] || type
}

/** 获取文档状态标签 */
function getDocumentStatusLabel(status: DocumentStatus) {
  const map: Record<string, string> = {
    [DocumentStatus.PENDING]: '待处理',
    [DocumentStatus.PROCESSING]: '处理中',
    [DocumentStatus.COMPLETED]: '已完成',
    [DocumentStatus.FAILED]: '失败',
  }
  return map[status] || status
}

/** 获取文档状态颜色 */
function getDocumentStatusType(status: DocumentStatus): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [DocumentStatus.PENDING]: 'info',
    [DocumentStatus.PROCESSING]: 'warning',
    [DocumentStatus.COMPLETED]: 'success',
    [DocumentStatus.FAILED]: 'danger',
  }
  return map[status] || 'info'
}

/** 格式化文件大小 */
function formatFileSize(size?: number) {
  if (!size) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

/** 格式化日期 */
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(loadSourceList)
</script>

<template>
  <div class="knowledge-center-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>知识中心</h2>
      <div class="header-actions">
        <el-button @click="handleOpenSearchDialog">
          <el-icon><Search /></el-icon>
          搜索测试
        </el-button>
        <el-button type="primary" @click="handleOpenCreateSourceDialog">
          <el-icon><Plus /></el-icon>
          创建知识源
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 知识源列表 -->
      <el-col :span="8">
        <el-card class="source-card">
          <template #header>
            <div class="card-header">
              <span>知识源列表</span>
              <el-tag>{{ sourceList.length }}</el-tag>
            </div>
          </template>

          <div v-loading="loading" class="source-list">
            <div
              v-for="source in sourceList"
              :key="source.source_id"
              class="source-item"
              :class="{ active: currentSource?.source_id === source.source_id }"
              @click="handleSelectSource(source)"
            >
              <div class="source-info">
                <div class="source-name">{{ source.name }}</div>
                <div class="source-meta">
                  <el-tag size="small" type="info">{{ getSourceTypeLabel(source.source_type) }}</el-tag>
                  <span>{{ source.document_count }} 个文档</span>
                </div>
              </div>
              <div class="source-actions">
                <el-button type="primary" link size="small" @click.stop="handleSyncSource(source)">
                  同步
                </el-button>
                <el-button type="danger" link size="small" @click.stop="handleDeleteSource(source)">
                  删除
                </el-button>
              </div>
            </div>

            <el-empty v-if="!loading && sourceList.length === 0" description="暂无知识源" />
          </div>

          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50]"
              :total="pagination.total"
              layout="total, prev, pager, next"
              small
              @current-change="loadSourceList"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 文档列表 -->
      <el-col :span="16">
        <el-card class="document-card">
          <template #header>
            <div class="card-header">
              <span>{{ currentSource ? `${currentSource.name} - 文档列表` : '文档列表' }}</span>
              <el-button
                type="primary"
                size="small"
                :disabled="!currentSource"
                @click="handleOpenUploadDialog"
              >
                <el-icon><Upload /></el-icon>
                上传文档
              </el-button>
            </div>
          </template>

          <el-table :data="documentList" style="width: 100%">
            <el-table-column prop="name" label="文档名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getDocumentStatusType(row.status)" size="small">
                  {{ getDocumentStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="块数量" width="80" />
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="danger" link size="small" @click="handleDeleteDocument(row as KnowledgeDocument)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!currentSource" description="请先选择知识源" />

          <!-- 分页 -->
          <div v-if="currentSource" class="pagination-wrapper">
            <el-pagination
              v-model:current-page="documentPagination.page"
              v-model:page-size="documentPagination.pageSize"
              :page-sizes="[10, 20, 50]"
              :total="documentPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="loadDocumentList(currentSource!.source_id)"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建知识源对话框 -->
    <el-dialog v-model="createSourceDialogVisible" title="创建知识源" width="500px">
      <el-form :model="createSourceForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="createSourceForm.name" placeholder="请输入知识源名称" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="createSourceForm.source_type" placeholder="选择知识源类型">
            <el-option
              v-for="type in Object.values(KnowledgeSourceType)"
              :key="type"
              :label="getSourceTypeLabel(type)"
              :value="type"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createSourceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSource">确定</el-button>
      </template>
    </el-dialog>

    <!-- 上传文档对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档" width="500px">
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :on-change="(file: any) => handleUploadDocument(file.raw)"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、TXT、Markdown 等格式文件</div>
        </template>
      </el-upload>
    </el-dialog>

    <!-- 搜索测试对话框 -->
    <el-dialog v-model="searchDialogVisible" title="知识搜索测试" width="700px">
      <div class="search-panel">
        <el-input
          v-model="searchKeyword"
          placeholder="输入搜索内容"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch" :loading="searchLoading">搜索</el-button>
          </template>
        </el-input>

        <div class="search-results">
          <div
            v-for="result in searchResults"
            :key="result.chunk.chunk_id"
            class="search-result-item"
          >
            <div class="result-header">
              <span class="result-source">{{ result.source_name }}</span>
              <span class="result-doc">{{ result.document_name }}</span>
              <el-tag size="small">相关度: {{ (result.score * 100).toFixed(1) }}%</el-tag>
            </div>
            <div class="result-content">{{ result.chunk.content }}</div>
          </div>

          <el-empty v-if="searchResults.length === 0 && !searchLoading" description="输入关键词开始搜索" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.knowledge-center-view {
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

.source-card,
.document-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.source-card :deep(.el-card__body),
.document-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.source-list {
  flex: 1;
  overflow-y: auto;
}

.source-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.source-item:hover {
  background-color: #f5f7fa;
}

.source-item.active {
  background-color: #ecf5ff;
  border-color: #409eff;
}

.source-info {
  flex: 1;
}

.source-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.source-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.source-actions {
  display: flex;
  gap: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.search-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-results {
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 8px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.result-source {
  color: #409eff;
  font-weight: 500;
}

.result-doc {
  color: #909399;
}

.result-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  word-break: break-all;
}
</style>
