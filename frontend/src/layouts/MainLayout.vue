<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

/** 当前激活的菜单 */
const activeMenu = computed(() => route.path)

/** 侧边栏折叠状态 */
const isCollapse = computed(() => appStore.sidebarCollapsed)

/**
 * 菜单分组配置
 */
const menuGroups = [
  {
    title: '核心平台',
    items: [
      { path: '/dashboard', title: '仪表盘', icon: 'Odometer' },
    ],
  },
  {
    title: '开发中心',
    items: [
      { path: '/agent-studio', title: 'Agent Studio', icon: 'MagicStick' },
      { path: '/workflows', title: 'Workflow Studio', icon: 'Connection' },
      { path: '/prompt-center', title: 'Prompt 中心', icon: 'EditPen' },
      { path: '/knowledge', title: '知识中心', icon: 'Collection' },
    ],
  },
  {
    title: '运营中心',
    items: [
      { path: '/tool-marketplace', title: '工具市场', icon: 'Goods' },
      { path: '/agent-market', title: 'Agent 市场', icon: 'Box' },
      { path: '/evaluation', title: '评估中心', icon: 'DataAnalysis' },
    ],
  },
  {
    title: '管理中心',
    items: [
      { path: '/cost', title: '成本中心', icon: 'Wallet' },
      { path: '/governance', title: '治理中心', icon: 'Shield' },
      { path: '/monitor', title: '监控中心', icon: 'DataLine' },
    ],
  },
  {
    title: '系统',
    items: [
      { path: '/llm', title: 'LLM 管理', icon: 'Cpu' },
      { path: '/approvals', title: '审核中心', icon: 'Checked' },
    ],
  },
]

/**
 * 处理菜单点击
 */
function handleMenuClick(path: string) {
  router.push(path)
}
</script>

<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="router.push('/dashboard')">
        <el-icon :size="28"><Cpu /></el-icon>
        <span v-if="!isCollapse" class="logo-text">AI Workflow OS</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        class="sidebar-menu"
        background-color="#1d1e2c"
        text-color="#a3a6b4"
        active-text-color="#409eff"
        @select="handleMenuClick"
      >
        <template v-for="group in menuGroups" :key="group.title">
          <div v-if="!isCollapse" class="menu-group-title">{{ group.title }}</div>
          <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 头部 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            :size="20"
            @click="appStore.toggleSidebar()"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">
              {{ route.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-badge :value="3" :max="99" class="notification-badge">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <el-dropdown>
            <el-avatar :size="32" class="user-avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #1d1e2c;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.menu-group-title {
  padding: 16px 20px 8px;
  font-size: 12px;
  color: #6c6e72;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.main-container {
  background: #f5f7fa;
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #606266;
}

.collapse-btn:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notification-badge {
  cursor: pointer;
  color: #606266;
}

.user-avatar {
  cursor: pointer;
  background: #409eff;
}

.content {
  padding: 20px;
  overflow-y: auto;
}

/* 路由切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
