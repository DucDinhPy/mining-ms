<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { getCameras } from '../../services/cameraApi'

const overlayCanvas = ref(null)
const cameras = ref([])
const selectedCameraId = ref('')
const frameUrl = ref('')
const isCameraActive = ref(false)
const isStarting = ref(false)
const isLoadingCameras = ref(false)
const socketStatus = ref('idle')
const cameraRuntimeStatus = ref('offline')
const errorMessage = ref('')
const detections = ref([])
const processedFps = ref(0)
const frameSize = ref({ width: 640, height: 360 })
const lastUpdated = ref(null)

let socket = null
let reconnectTimer = null
let shouldReconnect = false
let processedFrames = []
let pendingMetadata = null

const violationPattern = /^NO[-_ ]/i
const compliantPattern = /^(Hardhat|Mask|Safety Vest)$/i

const selectedCamera = computed(
  () => cameras.value.find((camera) => camera.id === selectedCameraId.value) ?? null,
)
const selectedCameraIsOnline = computed(
  () => String(selectedCamera.value?.status ?? '').toLowerCase() === 'online',
)
const peopleCount = computed(
  () => detections.value.filter((item) => /^Person$/i.test(item.label)).length,
)
const compliantCount = computed(
  () => detections.value.filter((item) => item.status === 'safe').length,
)
const violationCount = computed(
  () => detections.value.filter((item) => item.status === 'violation').length,
)
const stageStyle = computed(() => ({
  aspectRatio: `${frameSize.value.width} / ${frameSize.value.height}`,
}))
const isLive = computed(
  () => isCameraActive.value && cameraRuntimeStatus.value === 'online' && Boolean(frameUrl.value),
)
const connectionLabel = computed(() => {
  if (socketStatus.value === 'connecting') return 'Connecting'
  if (socketStatus.value === 'offline') return 'Connection lost'
  if (socketStatus.value === 'online' && cameraRuntimeStatus.value === 'connecting') {
    return 'Camera connecting'
  }
  if (socketStatus.value === 'online' && cameraRuntimeStatus.value === 'offline') {
    return 'Camera offline'
  }
  if (socketStatus.value === 'online') return 'AI connected'
  return 'Not connected'
})
const lastUpdatedLabel = computed(() => (
  lastUpdated.value
    ? lastUpdated.value.toLocaleTimeString('en-AU', { hour12: false })
    : '—'
))

function getWebSocketUrl(cameraId) {
  const configuredBaseUrl = import.meta.env.VITE_PPE_WS_BASE_URL?.trim().replace(/\/$/, '')
  if (configuredBaseUrl) {
    return `${configuredBaseUrl}/api/ws/cameras/${encodeURIComponent(cameraId)}`
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/ws/cameras/${encodeURIComponent(cameraId)}`
}

async function loadCameras() {
  isLoadingCameras.value = true
  errorMessage.value = ''

  try {
    const response = await getCameras({ page: 1, pageSize: 100 })
    cameras.value = response?.items ?? []

    const selectionStillExists = cameras.value.some(
      (camera) => camera.id === selectedCameraId.value,
    )

    if (!selectionStillExists) {
      const onlineCamera = cameras.value.find(
        (camera) => String(camera.status).toLowerCase() === 'online',
      )
      selectedCameraId.value = onlineCamera?.id ?? cameras.value[0]?.id ?? ''
    }
  } catch (error) {
    cameras.value = []
    selectedCameraId.value = ''
    errorMessage.value = error.message || 'Unable to load cameras.'
  } finally {
    isLoadingCameras.value = false
  }
}

function startCamera() {
  if (isStarting.value || isCameraActive.value) return

  if (!selectedCamera.value) {
    errorMessage.value = 'Select a camera before starting monitoring.'
    return
  }

  if (!selectedCameraIsOnline.value) {
    errorMessage.value = 'The selected camera is not marked Online.'
    return
  }

  isStarting.value = true
  errorMessage.value = ''
  isCameraActive.value = true
  shouldReconnect = true
  cameraRuntimeStatus.value = 'connecting'
  connectWebSocket()
  isStarting.value = false
}

function changeCamera() {
  if (!isCameraActive.value) {
    errorMessage.value = ''
    return
  }

  stopCamera()
  startCamera()
}

function connectWebSocket() {
  clearTimeout(reconnectTimer)

  if (!isCameraActive.value || !shouldReconnect || !selectedCameraId.value) return
  if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) return

  socketStatus.value = 'connecting'
  socket = new WebSocket(getWebSocketUrl(selectedCameraId.value))
  socket.binaryType = 'blob'

  socket.onopen = () => {
    socketStatus.value = 'online'
    errorMessage.value = ''
  }

  socket.onmessage = (event) => {
    if (typeof event.data === 'string') {
      handleJsonMessage(event.data)
      return
    }

    if (event.data instanceof Blob) {
      handleFrame(event.data)
    }
  }

  socket.onerror = () => {
    socketStatus.value = 'offline'
  }

  socket.onclose = () => {
    socketStatus.value = isCameraActive.value ? 'offline' : 'idle'
    socket = null

    if (shouldReconnect && isCameraActive.value) {
      reconnectTimer = setTimeout(connectWebSocket, 1500)
    }
  }
}

function handleJsonMessage(message) {
  try {
    const payload = JSON.parse(message)

    if (payload.type === 'error') {
      errorMessage.value = payload.message || 'Camera stream error.'
      cameraRuntimeStatus.value = 'offline'
      return
    }

    if (payload.type === 'camera_status') {
      cameraRuntimeStatus.value = payload.status || 'offline'

      if (payload.status === 'offline' && payload.last_error) {
        errorMessage.value = payload.last_error
      }
      return
    }

    if (payload.type !== 'frame_metadata') return

    pendingMetadata = payload
    cameraRuntimeStatus.value = 'online'
    errorMessage.value = ''

    if (payload.width && payload.height) {
      frameSize.value = {
        width: payload.width,
        height: payload.height,
      }
    }

    detections.value = (payload.detections ?? []).map(normalizeDetection)
    lastUpdated.value = payload.captured_at
      ? new Date(payload.captured_at)
      : new Date()
  } catch (error) {
    errorMessage.value = `Invalid AI response: ${error.message}`
  }
}

function handleFrame(blob) {
  if (!pendingMetadata) return

  if (frameUrl.value) URL.revokeObjectURL(frameUrl.value)
  frameUrl.value = URL.createObjectURL(blob)
  pendingMetadata = null
  updateProcessedFps()
  nextTick(drawDetections)
}

function normalizeDetection(item, index) {
  const label = String(item.class_name ?? item.class ?? item.label ?? `Class ${index}`)
  const confidence = Number(item.confidence ?? item.conf ?? item.score ?? 0)
  const bbox = item.bbox ?? item.xyxy ?? null

  let status = 'neutral'
  if (violationPattern.test(label)) status = 'violation'
  else if (compliantPattern.test(label)) status = 'safe'

  return {
    id: `${label}-${index}`,
    label: label.replaceAll('_', ' '),
    confidence: Math.min(Math.max(confidence, 0), 1),
    bbox: Array.isArray(bbox) && bbox.length === 4 ? bbox.map(Number) : null,
    status,
  }
}

function drawDetections() {
  const canvas = overlayCanvas.value
  if (!canvas) return

  const { width, height } = frameSize.value
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  context.clearRect(0, 0, width, height)

  detections.value.forEach((detection) => {
    if (!detection.bbox || detection.bbox.some((value) => !Number.isFinite(value))) return

    const [x1, y1, x2, y2] = detection.bbox
    const color = detection.status === 'violation'
      ? '#ef5350'
      : detection.status === 'safe'
        ? '#42b883'
        : '#3d9cdb'
    const label = `${detection.label} ${Math.round(detection.confidence * 100)}%`

    context.strokeStyle = color
    context.lineWidth = Math.max(2, width / 320)
    context.strokeRect(x1, y1, x2 - x1, y2 - y1)

    context.font = `600 ${Math.max(13, width / 48)}px Inter, Arial`
    const textWidth = context.measureText(label).width
    const labelHeight = Math.max(24, width / 26)
    const labelY = Math.max(0, y1 - labelHeight)

    context.fillStyle = color
    context.fillRect(x1, labelY, textWidth + 14, labelHeight)
    context.fillStyle = '#07131d'
    context.textBaseline = 'middle'
    context.fillText(label, x1 + 7, labelY + labelHeight / 2)
  })
}

function updateProcessedFps() {
  const now = performance.now()
  processedFrames.push(now)
  processedFrames = processedFrames.filter((time) => now - time <= 2000)

  if (processedFrames.length > 1) {
    const duration = (processedFrames.at(-1) - processedFrames[0]) / 1000
    processedFps.value = duration > 0
      ? Math.round(((processedFrames.length - 1) / duration) * 10) / 10
      : 0
  }
}

function stopCamera(resetResults = true) {
  shouldReconnect = false
  clearTimeout(reconnectTimer)
  reconnectTimer = null
  pendingMetadata = null

  if (socket) {
    socket.onclose = null
    socket.close()
    socket = null
  }

  isCameraActive.value = false
  socketStatus.value = 'idle'
  cameraRuntimeStatus.value = 'offline'
  processedFps.value = 0
  processedFrames = []

  if (resetResults) {
    if (frameUrl.value) URL.revokeObjectURL(frameUrl.value)
    frameUrl.value = ''
    detections.value = []
    lastUpdated.value = null
    const context = overlayCanvas.value?.getContext('2d')
    context?.clearRect(0, 0, overlayCanvas.value.width, overlayCanvas.value.height)
  }
}

onMounted(loadCameras)
onBeforeUnmount(() => stopCamera())
</script>

<template>
  <div class="ppe-module">
    <section class="metric-grid">
      <article class="metric-card">
        <div class="metric-icon connection" :class="socketStatus">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12.5a10 10 0 0 1 14 0M8 16a6 6 0 0 1 8 0M11 19.5a2 2 0 0 1 2 0" /></svg>
        </div>
        <div>
          <span>AI connection</span>
          <strong>{{ connectionLabel }}</strong>
        </div>
        <i class="metric-status-dot" :class="socketStatus"></i>
      </article>

      <article class="metric-card">
        <div class="metric-icon speed">
          <svg viewBox="0 0 24 24" fill="none"><path d="M4 14a8 8 0 1 1 16 0M12 14l4-5M6 18h12" /></svg>
        </div>
        <div>
          <span>Processing speed</span>
          <strong>{{ processedFps || '—' }} <small>FPS</small></strong>
        </div>
      </article>

      <article class="metric-card">
        <div class="metric-icon people">
          <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="3" /><path d="M5 21c0-4 3-7 7-7s7 3 7 7" /></svg>
        </div>
        <div>
          <span>People in frame</span>
          <strong>{{ peopleCount }}</strong>
        </div>
      </article>

      <article class="metric-card" :class="{ alert: violationCount > 0 }">
        <div class="metric-icon violations">
          <svg viewBox="0 0 24 24" fill="none"><path d="m12 3 10 18H2L12 3Z" /><path d="M12 9v5M12 18h.01" /></svg>
        </div>
        <div>
          <span>PPE violations</span>
          <strong>{{ violationCount }}</strong>
        </div>
      </article>
    </section>

    <section class="module-toolbar">
      <div class="toolbar-left">
        <label class="control-field camera-select">
          <span>Camera</span>
          <select v-model="selectedCameraId" :disabled="isLoadingCameras || !cameras.length" @change="changeCamera">
            <option v-if="!cameras.length" value="">No cameras available</option>
            <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
              {{ camera.name }} · {{ camera.location || 'No location' }} · {{ camera.status }}
            </option>
          </select>
        </label>

        <button class="secondary-action" type="button" :disabled="isLoadingCameras" @click="loadCameras">
          {{ isLoadingCameras ? 'Refreshing...' : 'Refresh cameras' }}
        </button>
      </div>

      <div class="toolbar-actions">
        <span v-if="lastUpdated" class="last-update">Updated: {{ lastUpdatedLabel }}</span>
        <button
          v-if="!isCameraActive"
          class="primary-action"
          type="button"
          :disabled="isStarting || !selectedCameraId || !selectedCameraIsOnline"
          @click="startCamera"
        >
          <svg viewBox="0 0 24 24" fill="none"><path d="M3 7h14v12H3zM17 11l4-2v8l-4-2" /></svg>
          {{ isStarting ? 'Starting...' : 'Start camera' }}
        </button>
        <button v-else class="danger-action" type="button" @click="stopCamera()">
          <span></span>
          Stop camera
        </button>
      </div>
    </section>

    <div v-if="errorMessage" class="module-alert" role="alert">
      <svg viewBox="0 0 24 24" fill="none"><path d="m12 3 10 18H2L12 3Z" /><path d="M12 9v5M12 18h.01" /></svg>
      <span>{{ errorMessage }}</span>
    </div>

    <section class="monitor-grid">
      <article class="content-card camera-card">
        <header class="card-header">
          <div>
            <span class="card-kicker">LIVE VIEW</span>
            <h2>Live camera</h2>
          </div>
          <div class="camera-state" :class="{ live: isLive }">
            <i></i>
            {{ isLive ? 'LIVE' : cameraRuntimeStatus.toUpperCase() }}
          </div>
        </header>

        <div class="camera-stage" :style="stageStyle">
          <template v-if="isCameraActive">
            <img v-if="frameUrl" class="camera-frame" :src="frameUrl" alt="Live camera stream" />
            <div v-else class="stream-waiting">
              <span></span>
              <strong>{{ connectionLabel }}</strong>
              <p>Waiting for the Python worker to publish a frame.</p>
            </div>
            <canvas ref="overlayCanvas" class="overlay-canvas"></canvas>
            <div class="camera-hud hud-left">
              {{ selectedCamera?.name || 'Camera' }} · {{ frameSize.width }}×{{ frameSize.height }}
            </div>
            <div class="camera-hud hud-right" :class="socketStatus">{{ connectionLabel }}</div>
            <div class="scan-line"></div>
          </template>

          <div v-else class="camera-placeholder">
            <div class="placeholder-grid"></div>
            <div class="camera-placeholder-icon">
              <svg viewBox="0 0 32 32" fill="none"><rect x="3" y="7" width="20" height="18" rx="3" /><path d="m23 13 6-3v12l-6-3M9 7l2-3h5l2 3" /><circle cx="13" cy="16" r="5" /></svg>
            </div>
            <strong>Camera is offline</strong>
            <p>Select “Start camera” to begin server-side PPE monitoring.</p>
          </div>
        </div>
      </article>

      <article class="content-card detections-card">
        <header class="card-header detection-header">
          <div>
            <span class="card-kicker">CURRENT FRAME</span>
            <h2>Latest detections</h2>
          </div>
          <span class="detection-count">{{ detections.length }}</span>
        </header>

        <div class="compliance-summary">
          <div><i class="safe"></i><span>Compliant PPE</span><strong>{{ compliantCount }}</strong></div>
          <div><i class="violation"></i><span>Violations</span><strong>{{ violationCount }}</strong></div>
        </div>

        <div v-if="detections.length" class="detection-table">
          <div class="detection-table-head">
            <span>Object</span>
            <span>Status</span>
            <span>Confidence</span>
          </div>
          <div v-for="detection in detections" :key="detection.id" class="detection-row">
            <div class="detection-name">
              <i :class="detection.status"></i>
              <strong>{{ detection.label }}</strong>
            </div>
            <span class="status-chip" :class="detection.status">
              {{ detection.status === 'violation' ? 'Violation' : detection.status === 'safe' ? 'Compliant' : 'Object' }}
            </span>
            <strong>{{ Math.round(detection.confidence * 100) }}%</strong>
          </div>
        </div>

        <div v-else class="empty-detections">
          <div class="empty-radar"><span></span><i></i></div>
          <strong>No detections yet</strong>
          <p>Model results will appear here as each frame is processed.</p>
        </div>
      </article>
    </section>
  </div>
</template>
