<script setup>
defineEmits(['open-menu'])
</script>

<template>
  <header class="app-topbar">
    <button class="mobile-menu-button" type="button" aria-label="Open menu" @click="$emit('open-menu')">
      <svg viewBox="0 0 20 20" fill="none"><path d="M3 5h14M3 10h14M3 15h14" /></svg>
    </button>

    <div class="topbar-search">
      <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <circle cx="8.5" cy="8.5" r="5.5" />
        <path d="m13 13 4 4" />
      </svg>
      <input type="search" placeholder="Search modules and reports..." aria-label="Search" />
      <kbd>⌘ K</kbd>
    </div>

    <div class="topbar-actions">
      <div class="shift-status">
        <span>Current shift</span>
        <strong>Morning · 06:00–14:00</strong>
      </div>

      <button class="icon-button notification-button" type="button" aria-label="Notifications">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4" />
        </svg>
        <i></i>
      </button>

      <button class="user-menu" type="button">
        <span class="user-avatar">DA</span>
        <span class="user-copy">
          <strong>Site Admin</strong>
          <small>Administrator</small>
        </span>
        <svg viewBox="0 0 20 20" fill="none"><path d="m6 8 4 4 4-4" /></svg>
      </button>
    </div>
  </header>
</template>
