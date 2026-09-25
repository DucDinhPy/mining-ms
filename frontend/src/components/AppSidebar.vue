<script setup>
import { navigationGroups } from '../config/navigation'

defineProps({
  activeFeature: {
    type: String,
    required: true,
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
  mobileOpen: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['toggle', 'select', 'close-mobile'])

function selectItem(item) {
  if (!item.available) return
  emit('select', item.id)
}
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed, 'mobile-open': mobileOpen }">
    <div class="sidebar-brand">
      <div class="sidebar-logo" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <path d="M5 18.5 12.5 7H27l-7.5 11.5H5Z" />
          <path d="m5 18.5 7.5 6.5H27l-7.5-6.5H5Z" />
        </svg>
      </div>
      <div class="brand-copy">
        <strong>MINEOPS</strong>
        <span>INTELLIGENCE</span>
      </div>
      <button class="mobile-close" type="button" aria-label="Đóng menu" @click="emit('close-mobile')">
        <svg viewBox="0 0 20 20" fill="none"><path d="m5 5 10 10M15 5 5 15" /></svg>
      </button>
    </div>

    <nav class="sidebar-navigation" aria-label="Điều hướng chính">
      <section v-for="group in navigationGroups" :key="group.label" class="nav-group">
        <p class="nav-group-label">{{ group.label }}</p>

        <button
          v-for="item in group.items"
          :key="item.id"
          class="nav-item"
          :class="{ active: activeFeature === item.id, disabled: !item.available }"
          :title="collapsed ? item.label : undefined"
          type="button"
          @click="selectItem(item)"
        >
          <span class="nav-icon">
            <svg v-if="item.icon === 'dashboard'" viewBox="0 0 24 24" fill="none">
              <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" />
            </svg>
            <svg v-else-if="item.icon === 'shield'" viewBox="0 0 24 24" fill="none">
              <path d="M12 3 5 6v5c0 4.6 2.9 8.4 7 10 4.1-1.6 7-5.4 7-10V6l-7-3Z" />
              <path d="m9 12 2 2 4-5" />
            </svg>
            <svg v-else-if="item.icon === 'truck'" viewBox="0 0 24 24" fill="none">
              <path d="M3 6h11v11H3zM14 10h4l3 3v4h-7zM7 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM18 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
            </svg>
            <svg v-else-if="item.icon === 'maintenance'" viewBox="0 0 24 24" fill="none">
              <path d="m14 6 4-4 4 4-4 4M16 8l-7 7M8 14l2 2-5 5H3v-2l5-5Z" />
            </svg>
            <svg v-else-if="item.icon === 'environment'" viewBox="0 0 24 24" fill="none">
              <path d="M20 4C10 4 5 9 5 15c0 3 2 5 5 5 6 0 10-6 10-16Z" />
              <path d="M4 21c2-5 6-8 11-11" />
            </svg>
            <svg v-else-if="item.icon === 'incident'" viewBox="0 0 24 24" fill="none">
              <path d="m12 3 10 18H2L12 3Z" />
              <path d="M12 9v5M12 18h.01" />
            </svg>
            <svg v-else-if="item.icon === 'report'" viewBox="0 0 24 24" fill="none">
              <path d="M5 3h14v18H5zM9 16V9M12 16v-4M15 16V7" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
            </svg>
          </span>

          <span class="nav-label">{{ item.label }}</span>
          <span v-if="!item.available" class="coming-soon">Sắp có</span>
        </button>
      </section>
    </nav>

    <div class="sidebar-footer">
      <div class="site-health">
        <span class="health-icon"><i></i></span>
        <div>
          <strong>Hệ thống hoạt động</strong>
          <span>1 module khả dụng</span>
        </div>
      </div>
      <button class="collapse-button" type="button" @click="emit('toggle')">
        <svg viewBox="0 0 20 20" fill="none"><path d="m12 4-6 6 6 6" /></svg>
        <span>Thu gọn</span>
      </button>
    </div>
  </aside>
</template>
