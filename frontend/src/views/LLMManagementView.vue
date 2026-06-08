<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/** 模型配置接口 */
interface ModelConfig {
  id: string
  name: string
  provider: string
  model: string
  apiKey: string
  baseUrl: string
  maxTokens: number
  temperature: number
  status: 'active' | 'inactive' | 'error'
  usage: {
    totalTokens: number
    totalCost: number
    requestCount: number
    avgLatency: number
  }
  createdAt: string
}

/** 模型提供商 */
const providers = [
  { value: 'openai', label: 'OpenAI', models: ['gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'] },
  { value: 'anthropic', label: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] },
  { value: 'zhipu', label: '智谱 AI', models: ['glm-4', 'glm-4-flash', 'glm-3-turbo'] },
  { value: 'qwen', label: '通义千问', models: ['qwen-max', 'qwen-plus', 'qwen-turbo'] },
  { value: 'local', label: '本地模型', models: ['ollama', 'vllm', 'llama-cpp'] },
]

/** 模型列表 */
const models = ref<ModelConfig[]>([
  {
    id: '1',
    name: 'GPT-4o',
    provider: 'openai',
    model: 'gpt-4o',
    apiKey: 'sk-***',
    baseUrl: 'https://api.openai.com/v1',
    maxTokens: 4096,
    temperature: 0.7,
    status: 'active',
    usage: {
      totalTokens: 1250000,
      totalCost: 12.5,
      requestCount: 856,
      avgLatency: 1.2,
    },
    createdAt: '2024-01-15',
  },
  {
    id: '2',
    name: 'Claude 3.5 Sonnet',
    provider: 'anthropic',
    model: 'claude-3-5-sonnet',
    apiKey: 'sk-***',
    baseUrl: 'https://api.anthropic.com',
    maxTokens: 4096,
    temperature: 0.5,
    status: 'active',
    usage: {
      totalTokens: 890000,
      totalCost: 8.9,
      requestCount: 423,
      avgLatency: 1.5,
    },
    createdAt: '2024-02-20',
  },
])

/** 搜索关键词 */
const searchQuery = ref('')

/** 筛选提供商 */
const filterProvider = ref('')

/** 对话框显示状态 */
const dialogVisible = ref(false)

/** 编辑模式 */
const isEditing = ref(false)

/** 当前编辑的模型 */
const currentModel = ref<Partial<ModelConfig>>({})

/** 测试状态 */
const testingStatus = ref<'idle' | 'testing' | 'success' | 'error'>('idle')

/** 筛选后的模型列表 */
const filteredModels = computed(() => {
  return models.value.filter((model) => {
    const matchesSearch = !searchQuery.value || 
      model.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      model.model.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesProvider = !filterProvider.value || model.provider === filterProvider.value
    return matchesSearch && matchesProvider
  })
})

/** 统计数据 */
const stats = computed(() => {
  const total = models.value.length
  const active = models.value.filter(m => m.status === 'active').length
  const totalTokens = models.value.reduce((sum, m) => sum + m.usage.totalTokens, 0)
  const totalCost = models.value.reduce((sum, m) => sum + m.usage.totalCost, 0)
  return { total, active, totalTokens, totalCost }
})

/**
 * 获取提供商信息
 */
function getProviderInfo(provider: string) {
  return providers.find(p => p.value === provider) || { label: provider, models: [] }
}

/**
 * 获取状态标签类型
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getStatusType(status: string): TagType {
  const map: Record<string, TagType> = {
    'active': 'success',
    'inactive': 'info',
    'error': 'danger',
  }
  return map[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: string) {
  const map: Record<string, string> = {
    'active': '运行中',
    'inactive': '已停用',
    'error': '异常',
  }
  return map[status] || status
}

/**
 * 格式化数字
 */
function formatNumber(num: number) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

/**
 * 打开新增对话框
 */
function handleAdd() {
  isEditing.value = false
  currentModel.value = {
    name: '',
    provider: 'openai',
    model: '',
    apiKey: '',
    baseUrl: '',
    maxTokens: 4096,
    temperature: 0.7,
    status: 'active',
  }
  dialogVisible.value = true
}

/**
 * 打开编辑对话框
 */
function handleEdit(model: ModelConfig) {
  isEditing.value = true
  currentModel.value = { ...model }
  dialogVisible.value = true
}

/**
 * 保存模型配置
 */
function handleSave() {
  if (!currentModel.value.name || !currentModel.value.model) {
    ElMessage.warning('请填写模型名称和模型标识')
    return
  }

  if (isEditing.value) {
    const index = models.value.findIndex(m => m.id === currentModel.value.id)
    if (index !== -1) {
      models.value[index] = { ...models.value[index], ...currentModel.value } as ModelConfig
      ElMessage.success('更新成功')
    }
  } else {
    const newModel: ModelConfig = {
      ...currentModel.value as ModelConfig,
      id: Date.now().toString(),
      usage: {
        totalTokens: 0,
        totalCost: 0,
        requestCount: 0,
        avgLatency: 0,
      },
      createdAt: new Date().toISOString().split('T')[0],
    }
    models.value.push(newModel)
    ElMessage.success('添加成功')
  }
  dialogVisible.value = false
}

/**
 * 测试模型连接
 */
async function handleTest() {
  testingStatus.value = 'testing'
  try {
    // 模拟测试
    await new Promise(resolve => setTimeout(resolve, 1500))
    testingStatus.value = 'success'
    ElMessage.success('连接测试成功')
  } catch (error) {
    testingStatus.value = 'error'
    ElMessage.error('连接测试失败')
  }
}

/**
 * 切换模型状态
 */
function handleToggleStatus(model: ModelConfig) {
  const newStatus = model.status === 'active' ? 'inactive' : 'active'
  model.status = newStatus
  ElMessage.success(`模型已${newStatus === 'active' ? '启用' : '停用'}`)
}

/**
 * 删除模型
 */
async function handleDelete(model: ModelConfig) {
  try {
    await ElMessageBox.confirm('确定要删除该模型配置吗？', '删除确认', {
      type: 'warning',
    })
    models.value = models.value.filter(m => m.id !== model.id)
    ElMessage.success('删除成功')
  } catch {
    // 取消操作
  }
}
</script>

<template>
  <div class="llm-management-view">
    <div class="page-header">
      <h2>LLM 管理中心</h2>
      <p>管理大语言模型配置、监控使用情况和成本</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #e6f7ff; color: #1890ff">
            <el-icon :size="24"><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">模型总数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #f6ffed; color: #52c41a">
            <el-icon :size="24"><CircleCheckFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.active }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #fff7e6; color: #fa8c16">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(stats.totalTokens) }}</div>
            <div class="stat-label">总 Token 数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon" style="background: #fff1f0; color: #f5222d">
            <el-icon :size="24"><Wallet /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">${{ stats.totalCost.toFixed(2) }}</div>
            <div class="stat-label">总费用</div>
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
            placeholder="搜索模型名称..."
            prefix-icon="Search"
            clearable
            style="width: 250px"
          />
          <el-select v-model="filterProvider" placeholder="筛选提供商" clearable style="width: 150px">
            <el-option
              v-for="p in providers"
              :key="p.value"
              :label="p.label"
              :value="p.value"
            />
          </el-select>
        </div>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加模型
        </el-button>
      </div>
    </el-card>

    <!-- 模型列表 -->
    <el-card class="list-card" shadow="never">
      <el-table :data="filteredModels" stripe>
        <el-table-column prop="name" label="模型名称" min-width="150">
          <template #default="{ row }">
            <div class="model-name">
              <el-icon :size="20" color="#409eff"><Cpu /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getProviderInfo(row.provider).label }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="model" label="模型标识" width="180" />

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="使用统计" min-width="200">
          <template #default="{ row }">
            <div class="usage-stats">
              <span>Token: {{ formatNumber(row.usage.totalTokens) }}</span>
              <span>调用: {{ row.usage.requestCount }}</span>
              <span>延迟: {{ row.usage.avgLatency }}s</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="usage.totalCost" label="费用" width="100">
          <template #default="{ row }">
            <span class="cost">${{ row.usage.totalCost.toFixed(2) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row as unknown as ModelConfig)">
              编辑
            </el-button>
            <el-button 
              :type="row.status === 'active' ? 'warning' : 'success'" 
              link 
              size="small" 
              @click="handleToggleStatus(row as unknown as ModelConfig)"
            >
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row as unknown as ModelConfig)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑模型' : '添加模型'"
      width="600px"
    >
      <el-form :model="currentModel" label-width="100px">
        <el-form-item label="模型名称" required>
          <el-input v-model="currentModel.name" placeholder="如：GPT-4o 生产环境" />
        </el-form-item>

        <el-form-item label="提供商" required>
          <el-select v-model="currentModel.provider" style="width: 100%">
            <el-option
              v-for="p in providers"
              :key="p.value"
              :label="p.label"
              :value="p.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="模型标识" required>
          <el-select 
            v-model="currentModel.model" 
            style="width: 100%"
            filterable
            allow-create
          >
            <el-option
              v-for="m in getProviderInfo(currentModel.provider || '').models"
              :key="m"
              :label="m"
              :value="m"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="API Key">
          <el-input 
            v-model="currentModel.apiKey" 
            type="password" 
            show-password
            placeholder="输入 API Key"
          />
        </el-form-item>

        <el-form-item label="Base URL">
          <el-input 
            v-model="currentModel.baseUrl" 
            placeholder="如：https://api.openai.com/v1"
          />
        </el-form-item>

        <el-form-item label="Max Tokens">
          <el-input-number 
            v-model="currentModel.maxTokens" 
            :min="1" 
            :max="128000"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="Temperature">
          <el-slider 
            v-model="currentModel.temperature" 
            :min="0" 
            :max="2" 
            :step="0.1"
            show-input
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="handleTest" :loading="testingStatus === 'testing'">
          测试连接
        </el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.llm-management-view {
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
  grid-template-columns: repeat(4, 1fr);
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

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.model-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.usage-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.cost {
  color: #f56c6c;
  font-weight: 600;
}
</style>
