<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

/** 登录表单 */
const loginForm = ref({
  username: '',
  password: '',
})

/** 加载状态 */
const loading = ref(false)
const feishuLoading = ref(false)

/**
 * 处理登录
 */
async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    // 模拟登录
    localStorage.setItem('token', 'mock-token')
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

/**
 * 飞书登录
 */
async function handleFeishuLogin() {
  feishuLoading.value = true
  try {
    // 获取飞书登录 URL
    const response = await fetch('/api/v1/auth/login-url')
    const data = await response.json()
    
    if (data.url) {
      // 跳转到飞书授权页面
      window.location.href = data.url
    } else {
      ElMessage.error('获取飞书登录地址失败')
    }
  } catch (error) {
    ElMessage.error('飞书登录失败')
  } finally {
    feishuLoading.value = false
  }
}
</script>

<template>
  <div class="login-view">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="40" color="#409eff"><Cpu /></el-icon>
        <h1>AI Workflow OS</h1>
        <p>企业级AI工作流操作系统</p>
      </div>

      <!-- 飞书登录按钮 -->
      <el-button
        type="primary"
        size="large"
        :loading="feishuLoading"
        @click="handleFeishuLogin"
        class="feishu-btn"
      >
        <template #icon>
          <el-icon><ChatDotRound /></el-icon>
        </template>
        飞书登录
      </el-button>

      <el-divider>或</el-divider>

      <el-form :model="loginForm" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1d1e2c 0%, #2d3a4a 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 24px;
  color: #303133;
  margin: 12px 0 8px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
}

.feishu-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  background: #3370ff;
  border-color: #3370ff;
}

.feishu-btn:hover {
  background: #2860e1;
  border-color: #2860e1;
}

.login-form {
  margin-top: 24px;
}

.login-btn {
  width: 100%;
}
</style>
