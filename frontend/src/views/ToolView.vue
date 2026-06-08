<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { toolApi } from '@/api'
import { ElMessage } from 'element-plus'

/** 工具列表 */
const tools = ref<Array<{
  name: string
  description: string
}>>([])

/** 加载状态 */
const loading = ref(false)

/** 调用对话框 */
const invokeDialogVisible = ref(false)

/** 当前选中的工具 */
const currentTool = ref<{ name: string; description: string } | null>(null)

/** 调用参数 */
const invokeParams = ref('')

/** 调用结果 */
const invokeResult = ref('')

/**
 * 加载工具列表
 */
async function loadTools() {
  loading.value = true
  try {
    const res = await toolApi.list()
    tools.value = res.items
  } catch (error) {
    ElMessage.error('获取工具列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 打开调用对话框
 */
function handleInvoke(tool: { name: string; description: string }) {
  currentTool.value = tool
  invokeParams.value = '{}'
  invokeResult.value = ''
  invokeDialogVisible.value = true
}

/**
 * 执行工具调用
 */
async function handleExecuteInvoke() {
  if (!currentTool.value) return

  try {
    const params = JSON.parse(invokeParams.value)
    const result = await toolApi.invoke(currentTool.value.name, params)
    invokeResult.value = JSON.stringify(result, null, 2)
    ElMessage.success('工具调用成功')
  } catch (error) {
    ElMessage.error('工具调用失败')
    invokeResult.value = String(error)
  }
}

onMounted(loadTools)
</script>

<template>
  <div class="tool-view">
    <div class="page-header">
      <h2>工具中心</h2>
      <el-button @click="loadTools">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 工具列表 -->
    <el-row :gutter="20">
      <el-col v-for="tool in tools" :key="tool.name" :span="8">
        <el-card shadow="hover" class="tool-card">
          <div class="tool-icon">
            <el-icon :size="32" color="#409eff"><SetUp /></el-icon>
          </div>
          <h3>{{ tool.name }}</h3>
          <p class="tool-desc">{{ tool.description }}</p>
          <el-button type="primary" link @click="handleInvoke(tool)">
            调用工具
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!tools.length && !loading" description="暂无可用工具" />

    <!-- 调用对话框 -->
    <el-dialog v-model="invokeDialogVisible" :title="`调用工具: ${currentTool?.name}`" width="600px">
      <el-form label-width="80px">
        <el-form-item label="工具">
          <el-input :value="currentTool?.name" disabled />
        </el-form-item>
        <el-form-item label="描述">
          <el-input :value="currentTool?.description" disabled type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="参数">
          <el-input
            v-model="invokeParams"
            type="textarea"
            :rows="4"
            placeholder='请输入JSON格式参数，例如: {"key": "value"}'
          />
        </el-form-item>
        <el-form-item v-if="invokeResult" label="结果">
          <el-input v-model="invokeResult" type="textarea" :rows="6" readonly />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="invokeDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleExecuteInvoke">执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tool-view {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.tool-card {
  margin-bottom: 20px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.tool-card:hover {
  transform: translateY(-4px);
}

.tool-icon {
  margin: 16px 0;
}

.tool-card h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}

.tool-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 16px;
  min-height: 40px;
}
</style>
