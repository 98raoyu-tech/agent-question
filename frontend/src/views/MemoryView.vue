<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { memoryApi } from '@/api'
import { ElMessage } from 'element-plus'

/** 搜索查询 */
const searchQuery = ref('')

/** 记忆类型 */
const memoryType = ref('')

/** 搜索结果 */
const searchResults = ref<Array<{
  key: string
  value: unknown
  memory_type: string
  created_at: string
}>>([])

/** 加载状态 */
const loading = ref(false)

/**
 * 搜索记忆
 */
async function handleSearch() {
  if (!searchQuery.value) return

  loading.value = true
  try {
    const res = await memoryApi.recall({
      query: searchQuery.value,
      memory_types: memoryType.value ? [memoryType.value] : undefined,
      top_k: 10,
    })
    searchResults.value = res.results as any
  } catch (error) {
    ElMessage.error('搜索记忆失败')
  } finally {
    loading.value = false
  }
}

/**
 * 删除记忆
 */
async function handleDelete(key: string) {
  try {
    await memoryApi.forget(key)
    ElMessage.success('记忆已删除')
    searchResults.value = searchResults.value.filter((r) => r.key !== key)
  } catch (error) {
    ElMessage.error('删除记忆失败')
  }
}

onMounted(() => {
  // 初始化
})
</script>

<template>
  <div class="memory-view">
    <div class="page-header">
      <h2>记忆管理</h2>
    </div>

    <!-- 搜索区域 -->
    <el-card class="search-card">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="查询">
          <el-input
            v-model="searchQuery"
            placeholder="输入搜索内容"
            clearable
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="memoryType" placeholder="选择类型" clearable style="width: 150px">
            <el-option label="向量" value="vector" />
            <el-option label="图" value="graph" />
            <el-option label="KV" value="kv" />
            <el-option label="事件" value="event" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 搜索结果 -->
    <el-card>
      <template #header>
        <span>搜索结果</span>
      </template>

      <el-table :data="searchResults" style="width: 100%">
        <el-table-column prop="key" label="Key" width="200" />
        <el-table-column prop="memory_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.memory_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="值" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link size="small" @click="handleDelete(row.key)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!searchResults.length && !loading" description="暂无数据" />
    </el-card>
  </div>
</template>

<style scoped>
.memory-view {
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

.search-card {
  margin-bottom: 20px;
}
</style>
