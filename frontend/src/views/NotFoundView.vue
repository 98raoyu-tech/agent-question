<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="not-found-view">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>页面未找到</h2>
      <p>抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="router.push('/dashboard')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found-view {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.not-found-content {
  text-align: center;
}

.not-found-content h1 {
  font-size: 120px;
  font-weight: 700;
  color: #409eff;
  line-height: 1;
  margin-bottom: 16px;
}

.not-found-content h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.not-found-content p {
  font-size: 16px;
  color: #909399;
  margin-bottom: 32px;
}
</style>
