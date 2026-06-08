<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { agentStudioApi } from '@/api'
import type { AgentDefinition, AgentVersion, AgentRelease } from '@/types'
import { AgentDefinitionType, ReleaseStatus } from '@/types'

/** 加载状态 */
const loading = ref(false)

/** Agent列表 */
const agentList = ref<AgentDefinition[]>([])

/** 分页参数 */
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

/** 搜索关键词 */
const searchKeyword = ref('')

/** 类型过滤 */
const typeFilter = ref<AgentDefinitionType | ''>('')

/** 创建对话框可见性 */
const createDialogVisible = ref(false)

/** 详情对话框可见性 */
const detailDialogVisible = ref(false)

/** 当前选中的Agent */
const currentAgent = ref<AgentDefinition | null>(null)

/** 版本列表 */
const versionList = ref<AgentVersion[]>([])

/** 发布列表 */
const releaseList = ref<AgentRelease[]>([])

/** 创建表单 */
const createForm = reactive({
  name: '',
  description: '',
  definition_type: AgentDefinitionType.CHATBOT,
  system_prompt: '',
  model_config: {},
})

/** 加载Agent列表 */
async function loadAgentList() {
  loading.value = true
  try {
    const res = await agentStudioApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchKeyword.value || undefined,
      definition_type: typeFilter.value || undefined,
    })
    agentList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载Agent列表失败:', error)
    ElMessage.error('加载Agent列表失败')
  } finally {
    loading.value = false
  }
}

/** 处理搜索 */
function handleSearch() {
  pagination.page = 1
  loadAgentList()
}

/** 处理分页变化 */
function handlePageChange(page: number) {
  pagination.page = page
  loadAgentList()
}

/** 处理每页条数变化 */
function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadAgentList()
}

/** 打开创建对话框 */
function handleOpenCreateDialog() {
  createForm.name = ''
  createForm.description = ''
  createForm.definition_type = AgentDefinitionType.CHATBOT
  createForm.system_prompt = ''
  createForm.model_config = {}
  createDialogVisible.value = true
}

/** 创建Agent */
async function handleCreateAgent() {
  try {
    await agentStudioApi.create(createForm)
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    loadAgentList()
  } catch (error) {
    console.error('创建Agent失败:', error)
    ElMessage.error('创建失败')
  }
}

/** 查看Agent详情 */
async function handleViewDetail(agent: AgentDefinition) {
  currentAgent.value = agent
  detailDialogVisible.value = true
  await Promise.all([
    loadVersions(agent.agent_id),
    loadReleases(agent.agent_id),
  ])
}

/** 加载版本列表 */
async function loadVersions(agentId: string) {
  try {
    const res = await agentStudioApi.listVersions(agentId)
    versionList.value = res.items
  } catch (error) {
    console.error('加载版本列表失败:', error)
  }
}

/** 加载发布列表 */
async function loadReleases(agentId: string) {
  try {
    const res = await agentStudioApi.listReleases(agentId)
    releaseList.value = res.items
  } catch (error) {
    console.error('加载发布列表失败:', error)
  }
}

/** 创建版本 */
async function handleCreateVersion() {
  if (!currentAgent.value) return
  try {
    await ElMessageBox.prompt('请输入版本变更说明', '创建版本', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    }).then(async ({ value }) => {
      await agentStudioApi.createVersion(currentAgent!.value!.agent_id, { change_log: value })
      ElMessage.success('版本创建成功')
      await loadVersions(currentAgent!.value!.agent_id)
    })
  } catch {
    // 用户取消
  }
}

/** 删除Agent */
async function handleDeleteAgent(agent: AgentDefinition) {
  try {
    await ElMessageBox.confirm(`确定要删除Agent "${agent.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await agentStudioApi.delete(agent.agent_id)
    ElMessage.success('删除成功')
    loadAgentList()
  } catch {
    // 用户取消
  }
}

/** 获取类型标签 */
function getTypeLabel(type: AgentDefinitionType) {
  const map: Record<string, string> = {
    [AgentDefinitionType.CHATBOT]: '聊天机器人',
    [AgentDefinitionType.WORKFLOW]: '工作流',
    [AgentDefinitionType.TOOL_USE]: '工具使用',
    [AgentDefinitionType.RAG]: 'RAG',
    [AgentDefinitionType.MULTI_AGENT]: '多Agent',
  }
  return map[type] || type
}

/** 获取类型标签颜色 */
function getTypeTagType(type: AgentDefinitionType): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [AgentDefinitionType.CHATBOT]: 'info',
    [AgentDefinitionType.WORKFLOW]: 'success',
    [AgentDefinitionType.TOOL_USE]: 'warning',
    [AgentDefinitionType.RAG]: 'info',
    [AgentDefinitionType.MULTI_AGENT]: 'danger',
  }
  return map[type] || 'info'
}

/** 获取发布状态标签 */
function getReleaseStatusLabel(status: ReleaseStatus) {
  const map: Record<string, string> = {
    [ReleaseStatus.DRAFT]: '草稿',
    [ReleaseStatus.REVIEWING]: '审核中',
    [ReleaseStatus.APPROVED]: '已批准',
    [ReleaseStatus.PUBLISHED]: '已发布',
    [ReleaseStatus.ARCHIVED]: '已归档',
  }
  return map[status] || status
}

/** 获取发布状态颜色 */
function getReleaseStatusType(status: ReleaseStatus): 'info' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    [ReleaseStatus.DRAFT]: 'info',
    [ReleaseStatus.REVIEWING]: 'warning',
    [ReleaseStatus.APPROVED]: 'success',
    [ReleaseStatus.PUBLISHED]: 'success',
    [ReleaseStatus.ARCHIVED]: 'info',
  }
  return map[status] || 'info'
}

/** 格式化日期 */
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(loadAgentList)
</script>

<template>
  <div class="agent-studio-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>Agent Studio</h2>
      <el-button type="primary" @click="handleOpenCreateDialog">
        <el-icon><Plus /></el-icon>
        创建 Agent
      </el-button>
    </div>

    <!-- 搜索和过滤区域 -->
    <el-card class="filter-card">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索Agent名称或描述"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="typeFilter" placeholder="选择类型" clearable @change="handleSearch">
            <el-option
              v-for="type in Object.values(AgentDefinitionType)"
              :key="type"
              :label="getTypeLabel(type)"
              :value="type"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Agent列表 -->
    <el-card class="table-card">
      <el-table :data="agentList" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="definition_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.definition_type)" size="small">
              {{ getTypeLabel(row.definition_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row as AgentDefinition)">
              详情
            </el-button>
            <el-button type="danger" link size="small" @click="handleDeleteAgent(row as AgentDefinition)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 创建Agent对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建 Agent" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入Agent名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入Agent描述"
          />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="createForm.definition_type" placeholder="选择Agent类型">
            <el-option
              v-for="type in Object.values(AgentDefinitionType)"
              :key="type"
              :label="getTypeLabel(type)"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input
            v-model="createForm.system_prompt"
            type="textarea"
            :rows="5"
            placeholder="请输入系统提示词"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateAgent">确定</el-button>
      </template>
    </el-dialog>

    <!-- Agent详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="Agent 详情" width="800px">
      <template v-if="currentAgent">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentAgent.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getTypeTagType(currentAgent.definition_type)" size="small">
              {{ getTypeLabel(currentAgent.definition_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentAgent.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建者">{{ currentAgent.created_by }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentAgent.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 版本管理 -->
        <div class="section-title">
          <span>版本管理</span>
          <el-button type="primary" size="small" @click="handleCreateVersion">创建版本</el-button>
        </div>
        <el-table :data="versionList" size="small">
          <el-table-column prop="version_number" label="版本号" width="100" />
          <el-table-column prop="change_log" label="变更说明" />
          <el-table-column prop="is_current" label="当前版本" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.is_current" type="success" size="small">是</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 发布管理 -->
        <div class="section-title">发布管理</div>
        <el-table :data="releaseList" size="small">
          <el-table-column prop="version_id" label="版本ID" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getReleaseStatusType(row.status)" size="small">
                {{ getReleaseStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="release_notes" label="发布说明" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.agent-studio-view {
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

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
</style>
