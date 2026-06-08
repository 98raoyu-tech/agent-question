import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 应用全局状态
 */
export const useAppStore = defineStore('app', () => {
  /** 侧边栏是否折叠 */
  const sidebarCollapsed = ref(false)

  /** 是否正在加载 */
  const loading = ref(false)

  /** 切换侧边栏折叠状态 */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /** 设置加载状态 */
  function setLoading(value: boolean) {
    loading.value = value
  }

  return {
    sidebarCollapsed,
    loading,
    toggleSidebar,
    setLoading,
  }
})
