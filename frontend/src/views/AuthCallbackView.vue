<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

/** 加载状态 */
const loading = ref(true)
const error = ref('')

/**
 * 处理回调
 */
onMounted(() => {
  const token = route.query.token as string
  const userId = route.query.user_id as string

  if (token) {
    // 保存 Token
    localStorage.setItem('token', token)
    localStorage.setItem('user_id', userId || '')

    ElMessage.success('登录成功')
    
    // 跳转到首页
    setTimeout(() => {
      router.push('/dashboard')
    }, 1000)
  } else {
    error.value = '登录失败：未获取到 Token'
    loading.value = false
    ElMessage.error('登录失败')
  }
})
</script>

<template>
  <div class="callback-view">
    <div class="callback-card">
      <div v-if="loading" class="loading-state">
        <el-icon :size="48" color="#409eff" class="loading-icon"><Loading /></el-icon>
        <h2>正在登录...</h2>
        <p>请稍候，正在处理飞书授权</p>
      </div>

      <div v-else-if="error" class="error-state">
        <el-icon :size="48" color="#f56c6c"><CircleCloseFilled /></el-icon>
        <h2>登录失败</h2>
        <p>{{ error }}</p>
        <el-button type="primary" @click="router.push('/login')">返回登录</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.callback-view {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1d1e2c 0%, #2d3a4a 100%);
}

.callback-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

h2 {
  font-size: 20px;
  color: #303133;
  margin: 0;
}

p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}
</style>
