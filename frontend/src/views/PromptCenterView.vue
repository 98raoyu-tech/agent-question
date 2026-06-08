<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { promptCenterApi } from '@/api'
import type { PromptTemplate, PromptVersion, PromptABTest } from '@/types'

const loading = ref(false)
const templateList = ref<PromptTemplate[]>([])
const currentTemplate = ref<PromptTemplate | null>(null)
const versionList = ref<PromptVersion[]>([])
const abTestList = ref<PromptABTest[]>([])
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const createForm = reactive({
  name: '',
  description: '',
  content: '',
  category: '',
  is_public: false,
})

const editForm = reactive({
  name: '',
  description: '',
  content: '',
  category: '',
})

async function loadTemplateList() {
  loading.value = true
  try {
    const res = await promptCenterApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    templateList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('加载模板列表失败:', error)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreateTemplate() {
  try {
    await promptCenterApi.create(createForm)
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    loadTemplateList()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function handleViewDetail(template: PromptTemplate) {
  currentTemplate.value = template
  detailDialogVisible.value = true
  await Promise.all([
    loadVersions(template.template_id),
    loadABTests(template.template_id),
  ])
}

async function loadVersions(templateId: string) {
  try {
    const res = await promptCenterApi.listVersions(templateId)
    versionList.value = res.items
  } catch (error) {
    console.error('加载版本列表失败:', error)
  }
}

async function loadABTests(templateId: string) {
  try {
    const res = await promptCenterApi.listABTests(templateId)
    abTestList.value = res.items
  } catch (error) {
    console.error('加载AB测试列表失败:', error)
  }
}

async function handleCreateVersion() {
  if (!currentTemplate.value) return
  try {
    await ElMessageBox.prompt('请输入版本变更说明', '创建版本', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    }).then(async ({ value }) => {
      await promptCenterApi.createVersion(currentTemplate!.value!.template_id, {
        content: currentTemplate!.value!.content,
        change_log: value,
      })
      ElMessage.success('版本创建成功')
      await loadVersions(currentTemplate!.value!.template_id)
    })
  } catch {}
}

function handleEditTemplate(template: PromptTemplate) {
  editForm.name = template.name
  editForm.description = template.description
  editForm.content = template.content
  editForm.category = template.category
  editDialogVisible.value = true
}

async function handleUpdateTemplate() {
  if (!currentTemplate.value) return
  try {
    await promptCenterApi.update(currentTemplate.value.template_id, editForm)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadTemplateList()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

async function handleDeleteTemplate(template: PromptTemplate) {
  try {
    await ElMessageBox.confirm(`确定要删除模板 "${template.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await promptCenterApi.delete(template.template_id)
    ElMessage.success('删除成功')
    loadTemplateList()
  } catch {}
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(loadTemplateList)
</script>

<template>
  <div class="prompt-center-view">
    <div class="page-header">
      <h2>Prompt 中心</h2>
      <el-button type="primary" @click="createDialogVisible = true">
        <el-icon><Plus /></el-icon>
        创建模板
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table :data="templateList" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="usage_count" label="使用次数" width="100" />
        <el-table-column prop="is_public" label="公开" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
              {{ row.is_public ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row as PromptTemplate)">详情</el-button>
            <el-button type="warning" link size="small" @click="handleEditTemplate(row as PromptTemplate)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDeleteTemplate(row as PromptTemplate)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadTemplateList"
        />
      </div>
    </el-card>

    <!-- 创建模板对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建 Prompt 模板" width="700px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="createForm.category" placeholder="请输入分类" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="createForm.content" type="textarea" :rows="8" placeholder="请输入Prompt内容" />
        </el-form-item>
        <el-form-item label="公开">
          <el-switch v-model="createForm.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTemplate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 模板详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="Prompt 模板详情" width="800px">
      <template v-if="currentTemplate">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ currentTemplate.category || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentTemplate.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ currentTemplate.usage_count }}</el-descriptions-item>
          <el-descriptions-item label="公开">{{ currentTemplate.is_public ? '是' : '否' }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">
          <span>Prompt 内容</span>
        </div>
        <el-input
          v-model="currentTemplate.content"
          type="textarea"
          :rows="6"
          readonly
        />

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
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>

        <div class="section-title">AB 测试</div>
        <el-table :data="abTestList" size="small">
          <el-table-column prop="name" label="测试名称" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'running' ? 'success' : 'info'" size="small">
                {{ row.status === 'running' ? '运行中' : '已停止' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>

    <!-- 编辑模板对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑 Prompt 模板" width="700px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="editForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="editForm.category" placeholder="请输入分类" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="editForm.content" type="textarea" :rows="8" placeholder="请输入Prompt内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateTemplate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.prompt-center-view {
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
