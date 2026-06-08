<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/** Prompt 模板接口 */
interface PromptTemplate {
  id: string
  name: string
  description: string
  content: string
  category: string
  variables: string[]
  version: string
  usageCount: number
  status: 'active' | 'draft' | 'archived'
  createdAt: string
  updatedAt: string
}

/** 分类列表 */
const categories = [
  { value: '', label: '全部' },
  { value: 'system', label: '系统 Prompt' },
  { value: 'user', label: '用户 Prompt' },
  { value: 'function', label: '函数 Prompt' },
  { value: 'template', label: '模板' },
]

/** Prompt 列表 */
const prompts = ref<PromptTemplate[]>([
  {
    id: '1',
    name: '客服系统 Prompt',
    description: '智能客服系统的基础系统 Prompt',
    content: '你是一个专业的客服助手。请根据用户的问题提供准确、友好的回答。\n\n规则：\n1. 保持礼貌和耐心\n2. 如果不确定答案，建议用户联系人工客服\n3. 对于敏感问题，按照公司政策处理',
    category: 'system',
    variables: ['{{user_name}}', '{{product_name}}'],
    version: '1.2.0',
    usageCount: 1256,
    status: 'active',
    createdAt: '2024-01-10',
    updatedAt: '2024-02-15',
  },
  {
    id: '2',
    name: '文案生成 Prompt',
    description: '小红书风格文案生成模板',
    content: '请根据以下主题生成一篇小红书风格的文案：\n\n主题：{{topic}}\n风格：{{style}}\n字数：{{word_count}}\n\n要求：\n1. 标题吸引眼球\n2. 使用 emoji 表情\n3. 分段清晰\n4. 包含热门话题标签',
    category: 'template',
    variables: ['{{topic}}', '{{style}}', '{{word_count}}'],
    version: '2.0.0',
    usageCount: 2340,
    status: 'active',
    createdAt: '2024-01-15',
    updatedAt: '2024-03-01',
  },
  {
    id: '3',
    name: 'SQL 生成 Prompt',
    description: '自然语言转 SQL 的 Prompt 模板',
    content: '你是一个 SQL 专家。请根据用户的自然语言描述生成对应的 SQL 查询语句。\n\n数据库结构：\n{{schema}}\n\n用户需求：{{requirement}}\n\n要求：\n1. 生成标准 SQL 语法\n2. 添加注释说明\n3. 优化查询性能',
    category: 'function',
    variables: ['{{schema}}', '{{requirement}}'],
    version: '1.5.0',
    usageCount: 890,
    status: 'active',
    createdAt: '2024-02-01',
    updatedAt: '2024-02-20',
  },
])

/** 搜索关键词 */
const searchQuery = ref('')

/** 当前分类 */
const currentCategory = ref('')

/** 对话框显示状态 */
const dialogVisible = ref(false)

/** 编辑模式 */
const isEditing = ref(false)

/** 当前编辑的 Prompt */
const currentPrompt = ref<Partial<PromptTemplate>>({})

/** 筛选后的 Prompt 列表 */
const filteredPrompts = computed(() => {
  return prompts.value.filter((prompt) => {
    const matchesSearch = !searchQuery.value || 
      prompt.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      prompt.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesCategory = !currentCategory.value || prompt.category === currentCategory.value
    return matchesSearch && matchesCategory
  })
})

/** 统计数据 */
const stats = computed(() => {
  return {
    total: prompts.value.length,
    active: prompts.value.filter(p => p.status === 'active').length,
    totalUsage: prompts.value.reduce((sum, p) => sum + p.usageCount, 0),
  }
})

/**
 * 获取状态标签类型
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getStatusType(status: string): TagType {
  const map: Record<string, TagType> = {
    'active': 'success',
    'draft': 'info',
    'archived': 'warning',
  }
  return map[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: string) {
  const map: Record<string, string> = {
    'active': '已发布',
    'draft': '草稿',
    'archived': '已归档',
  }
  return map[status] || status
}

/**
 * 获取分类文本
 */
function getCategoryText(category: string) {
  const cat = categories.find(c => c.value === category)
  return cat ? cat.label : category
}

/**
 * 格式化数字
 */
function formatNumber(num: number) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

/**
 * 打开新增对话框
 */
function handleAdd() {
  isEditing.value = false
  currentPrompt.value = {
    name: '',
    description: '',
    content: '',
    category: 'system',
    variables: [],
    status: 'draft',
  }
  dialogVisible.value = true
}

/**
 * 打开编辑对话框
 */
function handleEdit(prompt: PromptTemplate) {
  isEditing.value = true
  currentPrompt.value = { ...prompt }
  dialogVisible.value = true
}

/**
 * 保存 Prompt
 */
function handleSave() {
  if (!currentPrompt.value.name || !currentPrompt.value.content) {
    ElMessage.warning('请填写 Prompt 名称和内容')
    return
  }

  // 提取变量
  const variables = currentPrompt.value.content.match(/\{\{[^}]+\}\}/g) || []
  currentPrompt.value.variables = [...new Set(variables)]

  if (isEditing.value) {
    const index = prompts.value.findIndex(p => p.id === currentPrompt.value.id)
    if (index !== -1) {
      prompts.value[index] = { 
        ...prompts.value[index], 
        ...currentPrompt.value,
        updatedAt: new Date().toISOString().split('T')[0],
      } as PromptTemplate
      ElMessage.success('更新成功')
    }
  } else {
    const newPrompt: PromptTemplate = {
      ...currentPrompt.value as PromptTemplate,
      id: Date.now().toString(),
      version: '1.0.0',
      usageCount: 0,
      createdAt: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString().split('T')[0],
    }
    prompts.value.push(newPrompt)
    ElMessage.success('添加成功')
  }
  dialogVisible.value = false
}

/**
 * 删除 Prompt
 */
async function handleDelete(prompt: PromptTemplate) {
  try {
    await ElMessageBox.confirm('确定要删除该 Prompt 模板吗？', '删除确认', {
      type: 'warning',
    })
    prompts.value = prompts.value.filter(p => p.id !== prompt.id)
    ElMessage.success('删除成功')
  } catch {
    // 取消操作
  }
}

/**
 * 复制 Prompt
 */
function handleCopy(prompt: PromptTemplate) {
  navigator.clipboard.writeText(prompt.content)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <div class="prompt-management-view">
    <div class="page-header">
      <h2>Prompt 管理</h2>
      <p>管理和优化 Prompt 模板，提升 AI 应用效果</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#409eff"><Document /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">模板总数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#67c23a"><CircleCheckFilled /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.active }}</div>
            <div class="stat-label">已发布</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#e6a23c"><DataLine /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(stats.totalUsage) }}</div>
            <div class="stat-label">总使用次数</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 操作栏 -->
    <el-card class="action-card" shadow="never">
      <div class="action-bar">
        <div class="action-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索 Prompt 名称..."
            prefix-icon="Search"
            clearable
            style="width: 300px"
          />
          <el-select v-model="currentCategory" placeholder="筛选分类" clearable style="width: 150px">
            <el-option
              v-for="cat in categories"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </div>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新建 Prompt
        </el-button>
      </div>
    </el-card>

    <!-- Prompt 列表 -->
    <el-card class="list-card" shadow="never">
      <el-table :data="filteredPrompts" stripe>
        <el-table-column prop="name" label="Prompt 名称" min-width="180">
          <template #default="{ row }">
            <div class="prompt-name">
              <el-icon :size="20" color="#409eff"><Document /></el-icon>
              <div>
                <div class="name-text">{{ row.name }}</div>
                <div class="name-desc">{{ row.description }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryText(row.category) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="version" label="版本" width="100" />

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="usageCount" label="使用次数" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.usageCount) }}
          </template>
        </el-table-column>

        <el-table-column prop="variables" label="变量" min-width="150">
          <template #default="{ row }">
            <div class="variables-list">
              <el-tag v-for="v in row.variables.slice(0, 3)" :key="v" size="small" type="info">
                {{ v }}
              </el-tag>
              <el-tag v-if="row.variables.length > 3" size="small" type="info">
                +{{ row.variables.length - 3 }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="updatedAt" label="更新时间" width="120" />

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row as unknown as PromptTemplate)">
              编辑
            </el-button>
            <el-button type="success" link size="small" @click="handleCopy(row as unknown as PromptTemplate)">
              复制
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row as unknown as PromptTemplate)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑 Prompt' : '新建 Prompt'"
      width="800px"
    >
      <el-form :model="currentPrompt" label-width="100px">
        <el-form-item label="Prompt 名称" required>
          <el-input v-model="currentPrompt.name" placeholder="如：客服系统 Prompt" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="currentPrompt.description" placeholder="简要描述 Prompt 的用途" />
        </el-form-item>

        <el-form-item label="分类">
          <el-select v-model="currentPrompt.category" style="width: 100%">
            <el-option
              v-for="cat in categories.filter(c => c.value)"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-radio-group v-model="currentPrompt.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="active">已发布</el-radio>
            <el-radio value="archived">已归档</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="Prompt 内容" required>
          <el-input 
            v-model="currentPrompt.content" 
            type="textarea" 
            :rows="12"
            placeholder="输入 Prompt 内容，使用 {{变量名}} 定义变量"
          />
        </el-form-item>

        <el-form-item label="变量">
          <div class="variables-preview">
            <el-tag 
              v-for="v in (currentPrompt.content?.match(/\{\{[^}]+\}\}/g) || [])" 
              :key="v" 
              type="primary"
            >
              {{ v }}
            </el-tag>
            <span v-if="!(currentPrompt.content?.match(/\{\{[^}]+\}\}/g)?.length)" class="no-variables">
              暂无变量
            </span>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.prompt-management-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  color: #303133;
  margin: 0 0 8px;
}

.page-header p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border: none;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.action-card {
  margin-bottom: 20px;
  border: none;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-left {
  display: flex;
  gap: 12px;
}

.list-card {
  border: none;
}

.prompt-name {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.name-text {
  font-weight: 500;
  color: #303133;
}

.name-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.variables-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.variables-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  min-height: 40px;
}

.no-variables {
  color: #909399;
  font-size: 14px;
}
</style>
