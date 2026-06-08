<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

/** 模拟指标数据 */
const metrics = ref({
  cpu: 45,
  memory: 62,
  requests: 1234,
  errors: 5,
  avgLatency: 120,
  activeConnections: 89,
})

/** 模拟日志数据 */
const logs = ref<Array<{
  time: string
  level: string
  message: string
}>>([])

/** 定时器 */
let timer: ReturnType<typeof setInterval> | null = null

/**
 * 生成模拟日志
 */
function generateLogs() {
  const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
  const messages = [
    '工作流执行完成',
    'Agent任务调度成功',
    '记忆检索完成',
    '工具调用超时',
    '连接池状态正常',
    '缓存命中率: 85%',
  ]

  const newLogs = Array.from({ length: 5 }, () => ({
    time: new Date().toLocaleTimeString(),
    level: levels[Math.floor(Math.random() * levels.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
  }))

  logs.value = [...newLogs, ...logs.value].slice(0, 50)
}

/**
 * 获取日志级别颜色
 */
type TagType = 'info' | 'warning' | 'primary' | 'success' | 'danger'

function getLogLevelType(level: string): TagType {
  const map: Record<string, TagType> = {
    INFO: 'info',
    WARN: 'warning',
    ERROR: 'danger',
    DEBUG: 'info',
  }
  return map[level] || 'info'
}

onMounted(() => {
  generateLogs()
  timer = setInterval(() => {
    // 模拟指标更新
    metrics.value.cpu = Math.min(100, Math.max(0, metrics.value.cpu + (Math.random() - 0.5) * 10))
    metrics.value.memory = Math.min(100, Math.max(0, metrics.value.memory + (Math.random() - 0.5) * 5))
    metrics.value.requests += Math.floor(Math.random() * 10)
    metrics.value.avgLatency = Math.max(50, metrics.value.avgLatency + (Math.random() - 0.5) * 20)

    if (Math.random() > 0.7) {
      generateLogs()
    }
  }, 3000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<template>
  <div class="monitor-view">
    <div class="page-header">
      <h2>监控中心</h2>
    </div>

    <!-- 指标卡片 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <el-progress type="dashboard" :percentage="Math.round(metrics.cpu)" :width="80" />
          <div class="metric-label">CPU使用率</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <el-progress type="dashboard" :percentage="Math.round(metrics.memory)" :width="80" />
          <div class="metric-label">内存使用率</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-value">{{ metrics.requests }}</div>
          <div class="metric-label">总请求数</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-value error">{{ metrics.errors }}</div>
          <div class="metric-label">错误数</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-value">{{ Math.round(metrics.avgLatency) }}ms</div>
          <div class="metric-label">平均延迟</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-value success">{{ metrics.activeConnections }}</div>
          <div class="metric-label">活跃连接</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时日志 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>实时日志</span>
          <el-tag type="info" size="small">自动刷新</el-tag>
        </div>
      </template>

      <div class="log-container">
        <div v-for="(log, index) in logs" :key="index" class="log-item">
          <span class="log-time">{{ log.time }}</span>
          <el-tag :type="getLogLevelType(log.level)" size="small" class="log-level">
            {{ log.level }}
          </el-tag>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.monitor-view {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.metrics-row {
  margin-bottom: 20px;
}

.metric-card {
  text-align: center;
  padding: 20px 0;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.metric-value.error {
  color: #f56c6c;
}

.metric-value.success {
  color: #67c23a;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-container {
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  background: #1d1e2c;
  color: #a3a6b4;
  padding: 16px;
  border-radius: 4px;
}

.log-item {
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-time {
  color: #67c23a;
  margin-right: 8px;
}

.log-level {
  margin-right: 8px;
}

.log-message {
  color: #e4e7ed;
}
</style>
