<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

/** Agent 模板接口 */
interface AgentTemplate {
  id: string
  name: string
  description: string
  category: string
  icon: string
  version: string
  author: string
  downloads: number
  rating: number
  tags: string[]
  capabilities: string[]
  status: 'official' | 'community' | 'beta'
  createdAt: string
}

/** 分类列表 */
const categories = [
  { value: '', label: '全部', icon: 'Grid' },
  { value: 'customer_service', label: '客服服务', icon: 'Service' },
  { value: 'content', label: '内容生成', icon: 'EditPen' },
  { value: 'data', label: '数据分析', icon: 'DataAnalysis' },
  { value: 'code', label: '代码助手', icon: 'Monitor' },
  { value: 'automation', label: '自动化', icon: 'SetUp' },
  { value: 'knowledge', label: '知识管理', icon: 'Collection' },
]

/** Agent 模板列表 */
const agents = ref<AgentTemplate[]>([
  {
    id: '1',
    name: '智能客服 Agent',
    description: '支持多轮对话、知识库检索、工单创建的智能客服系统',
    category: 'customer_service',
    icon: 'Service',
    version: '1.2.0',
    author: '官方团队',
    downloads: 1256,
    rating: 4.8,
    tags: ['客服', '多轮对话', '知识库'],
    capabilities: ['自然语言理解', '意图识别', '知识检索', '工单管理'],
    status: 'official',
    createdAt: '2024-01-10',
  },
  {
    id: '2',
    name: '文案生成 Agent',
    description: '支持小红书、抖音、公众号等多平台文案生成',
    category: 'content',
    icon: 'EditPen',
    version: '2.0.1',
    author: '官方团队',
    downloads: 2340,
    rating: 4.9,
    tags: ['文案', '社媒', '营销'],
    capabilities: ['文案创作', '风格迁移', '多平台适配', 'SEO 优化'],
    status: 'official',
    createdAt: '2024-01-15',
  },
  {
    id: '3',
    name: 'SQL 分析 Agent',
    description: '自然语言转 SQL，支持复杂查询和数据可视化',
    category: 'data',
    icon: 'DataAnalysis',
    version: '1.5.0',
    author: '数据团队',
    downloads: 890,
    rating: 4.7,
    tags: ['SQL', '数据分析', '可视化'],
    capabilities: ['自然语言转 SQL', '查询优化', '图表生成', '报表导出'],
    status: 'official',
    createdAt: '2024-02-01',
  },
  {
    id: '4',
    name: '代码审查 Agent',
    description: '自动代码审查、Bug 检测、性能优化建议',
    category: 'code',
    icon: 'Monitor',
    version: '1.0.0',
    author: 'DevOps 团队',
    downloads: 567,
    rating: 4.6,
    tags: ['代码审查', 'Bug 检测', 'Code Review'],
    capabilities: ['代码分析', '安全检测', '性能优化', '规范检查'],
    status: 'beta',
    createdAt: '2024-02-15',
  },
  {
    id: '5',
    name: '图片生成 Agent',
    description: '集成 DALL-E、Midjourney，支持文生图、图生图',
    category: 'content',
    icon: 'Picture',
    version: '1.3.0',
    author: '创意团队',
    downloads: 1890,
    rating: 4.8,
    tags: ['图片', 'AI 绘画', '设计'],
    capabilities: ['文生图', '图生图', '风格迁移', '批量生成'],
    status: 'official',
    createdAt: '2024-01-20',
  },
  {
    id: '6',
    name: '知识库 Agent',
    description: '企业知识库管理、文档检索、智能问答',
    category: 'knowledge',
    icon: 'Collection',
    version: '1.1.0',
    author: '知识管理团队',
    downloads: 678,
    rating: 4.5,
    tags: ['知识库', '文档', 'RAG'],
    capabilities: ['文档解析', '向量检索', '智能问答', '知识图谱'],
    status: 'official',
    createdAt: '2024-02-10',
  },
])

/** 搜索关键词 */
const searchQuery = ref('')

/** 当前分类 */
const currentCategory = ref('')

/** 筛选后的 Agent 列表 */
const filteredAgents = computed(() => {
  return agents.value.filter((agent) => {
    const matchesSearch = !searchQuery.value || 
      agent.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      agent.tags.some(tag => tag.includes(searchQuery.value))
    const matchesCategory = !currentCategory.value || agent.category === currentCategory.value
    return matchesSearch && matchesCategory
  })
})

/** 统计数据 */
const stats = computed(() => {
  return {
    total: agents.value.length,
    official: agents.value.filter(a => a.status === 'official').length,
    totalDownloads: agents.value.reduce((sum, a) => sum + a.downloads, 0),
    avgRating: (agents.value.reduce((sum, a) => sum + a.rating, 0) / agents.value.length).toFixed(1),
  }
})

/**
 * 获取状态标签类型
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getStatusType(status: string): TagType {
  const map: Record<string, TagType> = {
    'official': 'success',
    'community': 'primary',
    'beta': 'warning',
  }
  return map[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: string) {
  const map: Record<string, string> = {
    'official': '官方',
    'community': '社区',
    'beta': '测试',
  }
  return map[status] || status
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
 * 安装 Agent
 */
function handleInstall(agent: AgentTemplate) {
  ElMessage.success(`已安装: ${agent.name}`)
}

/**
 * 查看详情
 */
function handleDetail(agent: AgentTemplate) {
  ElMessage.info(`查看详情: ${agent.name}`)
}
</script>

<template>
  <div class="agent-market-view">
    <div class="page-header">
      <h2>Agent 市场</h2>
      <p>浏览和安装预制 Agent 模板，快速构建 AI 应用</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#409eff"><Box /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">Agent 模板</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#67c23a"><Medal /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.official }}</div>
            <div class="stat-label">官方模板</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#e6a23c"><Download /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(stats.totalDownloads) }}</div>
            <div class="stat-label">总安装量</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon :size="32" color="#f56c6c"><Star /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avgRating }}</div>
            <div class="stat-label">平均评分</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索 Agent 名称、描述或标签..."
          prefix-icon="Search"
          clearable
          style="width: 400px"
        />
        <div class="category-tags">
          <el-tag
            v-for="cat in categories"
            :key="cat.value"
            :type="currentCategory === cat.value ? 'primary' : 'info'"
            :effect="currentCategory === cat.value ? 'dark' : 'plain'"
            @click="currentCategory = cat.value"
            class="category-tag"
          >
            <el-icon><component :is="cat.icon" /></el-icon>
            {{ cat.label }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- Agent 列表 -->
    <div class="agent-grid">
      <el-card 
        v-for="agent in filteredAgents" 
        :key="agent.id" 
        class="agent-card"
        shadow="hover"
      >
        <div class="agent-header">
          <div class="agent-icon">
            <el-icon :size="32"><component :is="agent.icon" /></el-icon>
          </div>
          <el-tag :type="getStatusType(agent.status)" size="small">
            {{ getStatusText(agent.status) }}
          </el-tag>
        </div>

        <h3 class="agent-name">{{ agent.name }}</h3>
        <p class="agent-desc">{{ agent.description }}</p>

        <div class="agent-tags">
          <el-tag v-for="tag in agent.tags" :key="tag" size="small" type="info">
            {{ tag }}
          </el-tag>
        </div>

        <div class="agent-capabilities">
          <div class="capability-title">核心能力：</div>
          <div class="capability-list">
            <span v-for="cap in agent.capabilities" :key="cap" class="capability-item">
              {{ cap }}
            </span>
          </div>
        </div>

        <div class="agent-meta">
          <div class="meta-left">
            <span class="meta-item">
              <el-icon><Download /></el-icon>
              {{ formatNumber(agent.downloads) }}
            </span>
            <span class="meta-item">
              <el-icon><Star /></el-icon>
              {{ agent.rating }}
            </span>
          </div>
          <span class="meta-version">v{{ agent.version }}</span>
        </div>

        <div class="agent-actions">
          <el-button type="primary" @click="handleInstall(agent)">
            安装使用
          </el-button>
          <el-button @click="handleDetail(agent)">
            查看详情
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty 
      v-if="filteredAgents.length === 0" 
      description="没有找到匹配的 Agent"
    />
  </div>
</template>

<style scoped>
.agent-market-view {
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

.filter-card {
  margin-bottom: 20px;
  border: none;
}

.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-tag {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.category-tag:hover {
  opacity: 0.8;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.agent-card {
  border: none;
  transition: transform 0.2s;
}

.agent-card:hover {
  transform: translateY(-4px);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.agent-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.agent-name {
  font-size: 18px;
  color: #303133;
  margin: 0 0 8px;
}

.agent-desc {
  font-size: 14px;
  color: #606266;
  margin: 0 0 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.agent-capabilities {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.capability-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.capability-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.capability-item {
  font-size: 12px;
  color: #409eff;
  background: #ecf5ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.agent-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.meta-left {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #606266;
}

.meta-version {
  font-size: 12px;
  color: #909399;
}

.agent-actions {
  display: flex;
  gap: 12px;
}

.agent-actions .el-button {
  flex: 1;
}
</style>
