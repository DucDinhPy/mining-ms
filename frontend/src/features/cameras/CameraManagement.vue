<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { createCamera, getCameraById, getCameras } from '../../services/cameraApi'

const cameras = ref([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = 10
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const createOpen = ref(false)
const isSubmitting = ref(false)
const selectedCamera = ref(null)
const detailOpen = ref(false)
const detailLoading = ref(false)

const form = reactive({
  name: '',
  location: '',
  streamUrl: 'rtsp://localhost:8554/',
  status: 'Offline',
  description: '',
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize)))
const onlineOnPage = computed(
  () => cameras.value.filter((camera) => camera.status === 'Online').length,
)
const offlineOnPage = computed(
  () => cameras.value.filter((camera) => camera.status === 'Offline').length,
)
const maintenanceOnPage = computed(
  () => cameras.value.filter((camera) => camera.status === 'Maintenance').length,
)
const resultRange = computed(() => {
  if (!totalCount.value) return '0 results'
  const first = (page.value - 1) * pageSize + 1
  const last = Math.min(page.value * pageSize, totalCount.value)
  return `${first}-${last} of ${totalCount.value}`
})

async function loadCameras() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await getCameras({ page: page.value, pageSize })
    cameras.value = response?.items ?? []
    totalCount.value = response?.totalCount ?? 0
  } catch (error) {
    errorMessage.value = error.message || 'Unable to load cameras.'
  } finally {
    isLoading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    name: '',
    location: '',
    streamUrl: 'rtsp://localhost:8554/',
    status: 'Offline',
    description: '',
  })
  errorMessage.value = ''
  successMessage.value = ''
  createOpen.value = true
}

function closeCreate() {
  if (!isSubmitting.value) createOpen.value = false
}

async function submitCamera() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const created = await createCamera({
      name: form.name.trim(),
      location: form.location.trim(),
      streamUrl: form.streamUrl.trim(),
      status: form.status,
      description: form.description.trim() || null,
    })

    createOpen.value = false
    page.value = 1
    successMessage.value = `${created.name} was added to the camera registry.`
    await loadCameras()
  } catch (error) {
    errorMessage.value = error.message || 'Unable to create camera.'
  } finally {
    isSubmitting.value = false
  }
}

async function openDetails(camera) {
  selectedCamera.value = camera
  detailOpen.value = true
  detailLoading.value = true
  errorMessage.value = ''

  try {
    selectedCamera.value = await getCameraById(camera.id)
  } catch (error) {
    errorMessage.value = error.message || 'Unable to load camera details.'
  } finally {
    detailLoading.value = false
  }
}

async function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
  page.value = nextPage
  await loadCameras()
}

function formatDate(value) {
  if (!value) return 'Never'
  return new Intl.DateTimeFormat('en-AU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function statusClass(status) {
  return String(status || 'Offline').toLowerCase()
}

onMounted(loadCameras)
</script>

<template>
  <div class="camera-management">
    <section class="camera-summary-grid">
      <article class="camera-summary-card">
        <span class="summary-icon total">
          <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="14" height="12" rx="2" /><path d="m17 10 4-2v8l-4-2" /></svg>
        </span>
        <div><span>Total registered</span><strong>{{ totalCount }}</strong></div>
      </article>
      <article class="camera-summary-card">
        <span class="summary-icon online"><i></i></span>
        <div><span>Online on page</span><strong>{{ onlineOnPage }}</strong></div>
      </article>
      <article class="camera-summary-card">
        <span class="summary-icon maintenance">
          <svg viewBox="0 0 24 24" fill="none"><path d="m14 6 4-4 4 4-4 4M16 8l-7 7M8 14l2 2-5 5H3v-2l5-5Z" /></svg>
        </span>
        <div><span>Maintenance</span><strong>{{ maintenanceOnPage }}</strong></div>
      </article>
      <article class="camera-summary-card">
        <span class="summary-icon offline"><i></i></span>
        <div><span>Offline on page</span><strong>{{ offlineOnPage }}</strong></div>
      </article>
    </section>

    <div v-if="errorMessage" class="module-alert" role="alert">
      <svg viewBox="0 0 24 24" fill="none"><path d="m12 3 10 18H2L12 3Z" /><path d="M12 9v5M12 18h.01" /></svg>
      <span>{{ errorMessage }}</span>
    </div>

    <div v-if="successMessage" class="camera-success" role="status">
      <span>✓</span>{{ successMessage }}
    </div>

    <section class="content-card camera-registry-card">
      <header class="camera-registry-header">
        <div>
          <span class="card-kicker">VIDEO SOURCES</span>
          <h2>Camera registry</h2>
          <p>Sources available to PPE detection and future monitoring modules.</p>
        </div>
        <div class="registry-actions">
          <button class="secondary-action" type="button" :disabled="isLoading" @click="loadCameras">
            <svg viewBox="0 0 20 20" fill="none"><path d="M16 7a7 7 0 1 0 1 5M16 3v4h-4" /></svg>
            Refresh
          </button>
          <button class="primary-action" type="button" @click="openCreate">
            <svg viewBox="0 0 20 20" fill="none"><path d="M10 4v12M4 10h12" /></svg>
            Add camera
          </button>
        </div>
      </header>

      <div class="camera-table-wrap">
        <table class="camera-table">
          <thead>
            <tr>
              <th>Camera</th>
              <th>Location</th>
              <th>Stream source</th>
              <th>Status</th>
              <th>Last change</th>
              <th><span class="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="6"><div class="table-state"><span class="loading-spinner"></span>Loading cameras...</div></td>
            </tr>
            <tr v-else-if="!cameras.length">
              <td colspan="6">
                <div class="table-empty">
                  <span class="empty-camera-icon">
                    <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="14" height="12" rx="2" /><path d="m17 10 4-2v8l-4-2" /></svg>
                  </span>
                  <strong>No cameras registered</strong>
                  <p>Add your MediaMTX stream to make it available to MineOps.</p>
                  <button class="primary-action" type="button" @click="openCreate">Add first camera</button>
                </div>
              </td>
            </tr>
            <tr v-for="camera in cameras" v-else :key="camera.id" class="camera-row" @click="openDetails(camera)">
              <td>
                <div class="camera-name-cell">
                  <span class="camera-avatar">
                    <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="14" height="12" rx="2" /><path d="m17 10 4-2v8l-4-2" /></svg>
                  </span>
                  <div><strong>{{ camera.name }}</strong><small>{{ camera.id.slice(0, 8) }}</small></div>
                </div>
              </td>
              <td>{{ camera.location || 'Unassigned' }}</td>
              <td><code class="stream-url">{{ camera.streamUrl }}</code></td>
              <td><span class="camera-status" :class="statusClass(camera.status)"><i></i>{{ camera.status }}</span></td>
              <td>{{ formatDate(camera.updatedAtUtc || camera.createdAtUtc) }}</td>
              <td><button class="row-action" type="button" aria-label="View camera details" @click.stop="openDetails(camera)">→</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="camera-table-footer">
        <span>{{ resultRange }}</span>
        <div class="pagination-controls">
          <button type="button" :disabled="page === 1 || isLoading" @click="changePage(page - 1)">Previous</button>
          <span>Page {{ page }} of {{ totalPages }}</span>
          <button type="button" :disabled="page === totalPages || isLoading" @click="changePage(page + 1)">Next</button>
        </div>
      </footer>
    </section>

    <div v-if="createOpen" class="camera-modal-backdrop" @mousedown.self="closeCreate">
      <section class="camera-modal" role="dialog" aria-modal="true" aria-labelledby="create-camera-title">
        <header>
          <div><span class="card-kicker">CAMERA REGISTRY</span><h2 id="create-camera-title">Add camera</h2></div>
          <button type="button" aria-label="Close" :disabled="isSubmitting" @click="closeCreate">×</button>
        </header>
        <form @submit.prevent="submitCamera">
          <div class="camera-form-grid">
            <label class="camera-form-field">
              <span>Name <b>*</b></span>
              <input v-model="form.name" required maxlength="150" placeholder="Camera 01" />
            </label>
            <label class="camera-form-field">
              <span>Location <b>*</b></span>
              <input v-model="form.location" required maxlength="250" placeholder="Main Gate" />
            </label>
            <label class="camera-form-field full-width">
              <span>RTSP stream URL <b>*</b></span>
              <input v-model="form.streamUrl" required maxlength="2000" placeholder="rtsp://localhost:8554/camera01" />
              <small>Use the MediaMTX read URL, not the OBS publish URL.</small>
            </label>
            <label class="camera-form-field">
              <span>Status</span>
              <select v-model="form.status">
                <option value="Offline">Offline</option>
                <option value="Online">Online</option>
                <option value="Maintenance">Maintenance</option>
              </select>
            </label>
            <label class="camera-form-field full-width">
              <span>Description</span>
              <textarea v-model="form.description" maxlength="1000" rows="4" placeholder="Purpose, coverage area, or installation notes"></textarea>
            </label>
          </div>
          <footer>
            <button class="secondary-action" type="button" :disabled="isSubmitting" @click="closeCreate">Cancel</button>
            <button class="primary-action" type="submit" :disabled="isSubmitting">
              {{ isSubmitting ? 'Saving...' : 'Save camera' }}
            </button>
          </footer>
        </form>
      </section>
    </div>

    <div v-if="detailOpen" class="camera-modal-backdrop" @mousedown.self="detailOpen = false">
      <aside class="camera-detail-panel" role="dialog" aria-modal="true" aria-labelledby="camera-detail-title">
        <header>
          <div><span class="card-kicker">CAMERA DETAILS</span><h2 id="camera-detail-title">{{ selectedCamera?.name }}</h2></div>
          <button type="button" aria-label="Close" @click="detailOpen = false">×</button>
        </header>
        <div v-if="detailLoading" class="table-state"><span class="loading-spinner"></span>Loading details...</div>
        <div v-else-if="selectedCamera" class="camera-detail-content">
          <div class="detail-hero">
            <span class="camera-avatar large"><svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="14" height="12" rx="2" /><path d="m17 10 4-2v8l-4-2" /></svg></span>
            <div><strong>{{ selectedCamera.name }}</strong><span class="camera-status" :class="statusClass(selectedCamera.status)"><i></i>{{ selectedCamera.status }}</span></div>
          </div>
          <dl class="camera-detail-list">
            <div><dt>Location</dt><dd>{{ selectedCamera.location || 'Unassigned' }}</dd></div>
            <div><dt>Stream URL</dt><dd><code>{{ selectedCamera.streamUrl }}</code></dd></div>
            <div><dt>Description</dt><dd>{{ selectedCamera.description || 'No description' }}</dd></div>
            <div><dt>Created</dt><dd>{{ formatDate(selectedCamera.createdAtUtc) }}</dd></div>
            <div><dt>Last updated</dt><dd>{{ formatDate(selectedCamera.updatedAtUtc) }}</dd></div>
            <div><dt>Camera ID</dt><dd><code>{{ selectedCamera.id }}</code></dd></div>
          </dl>
        </div>
      </aside>
    </div>
  </div>
</template>
