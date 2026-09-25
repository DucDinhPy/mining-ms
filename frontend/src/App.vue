<script setup>
import { computed, ref } from 'vue'

import AppSidebar from './components/AppSidebar.vue'
import AppTopbar from './components/AppTopbar.vue'
import PpeRealtime from './features/ppe/PpeRealtime.vue'
import { navigationGroups } from './config/navigation'

const sidebarCollapsed = ref(false)
const mobileSidebarOpen = ref(false)
const activeFeature = ref('ppe')

const allNavigationItems = navigationGroups.flatMap((group) => group.items)
const currentFeature = computed(
  () => allNavigationItems.find((item) => item.id === activeFeature.value) ?? allNavigationItems[0],
)

function selectFeature(featureId) {
  activeFeature.value = featureId
  mobileSidebarOpen.value = false
}
</script>

<template>
  <div class="admin-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <AppSidebar
      :active-feature="activeFeature"
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileSidebarOpen"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
      @close-mobile="mobileSidebarOpen = false"
      @select="selectFeature"
    />

    <button
      v-if="mobileSidebarOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Close menu"
      @click="mobileSidebarOpen = false"
    ></button>

    <div class="app-workspace">
      <AppTopbar @open-menu="mobileSidebarOpen = true" />

      <main class="page-content">
        <div class="page-heading">
          <div>
            <div class="breadcrumb">
              <span>MineOps</span>
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="m7.5 4.5 5 5-5 5" />
              </svg>
              <span>Safety Operations</span>
            </div>
            <h1>{{ currentFeature.label }}</h1>
            <p>{{ currentFeature.description }}</p>
          </div>

          <div class="page-heading-meta">
            <span class="workspace-badge">
              <i></i>
              Site 01 · Sydney
            </span>
            <span>Live updates</span>
          </div>
        </div>

        <PpeRealtime v-if="activeFeature === 'ppe'" />
      </main>
    </div>
  </div>
</template>
