<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'

const videoElement = ref(null)
const captureCanvas = ref(null)
const overlayCanvas = ref(null)

const cameraStream = ref(null)
const cameraDevices = ref([])
const selectedCameraId = ref('')
const isCameraActive = ref(false)
const isStarting = ref(false)
const socketStatus = ref('idle')
const errorMessage = ref('')
const detections = ref([])
const inferenceTime = ref(null)
const targetFps = ref(5)
const processedFps = ref(0)
const frameSize = ref({ width: 640, height: 360 })

let socket = null
let captureTimer = null
let reconnectTimer = null
let awaitingResponse = false
let shouldReconnect = false
let processedFrames = []

const violationPattern = /^NO[-_ ]/i
const compliantPattern = /^(Hardhat|Mask|Safety Vest)$/i

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
const connectionLabel = computed(() => {
  if (socketStatus.value === 'online') return 'Đã kết nối AI'
  if (socketStatus.value === 'connecting') return 'Đang kết nối'
  if (socketStatus.value === 'offline') return 'Mất kết nối'
  return 'Chưa kết nối'
})

function getWebSocketUrl() {
  const configuredUrl = import.meta.env.VITE_WS_URL?.trim()
  if (configuredUrl) return configuredUrl

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/ws/detect`
}

async function listCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices()
  cameraDevices.value = devices.filter((device) => device.kind === 'videoinput')

  if (!selectedCameraId.value && cameraDevices.value.length) {
    selectedCameraId.value = cameraDevices.value[0].deviceId
  }
}

async function startCamera() {
  if (isStarting.value || isCameraActive.value) return

  isStarting.value = true
  errorMessage.value = ''

  try {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('Trình duyệt không hỗ trợ truy cập camera.')
    }

    const videoConstraints = selectedCameraId.value
      ? {
          deviceId: { exact: selectedCameraId.value },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        }
      : {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        }

    cameraStream.value = await navigator.mediaDevices.getUserMedia({
      video: videoConstraints,
      audio: false,
    })

    isCameraActive.value = true
    shouldReconnect = true
    await nextTick()

    videoElement.value.srcObject = cameraStream.value
    await videoElement.value.play()

    const width = videoElement.value.videoWidth || 1280
    const height = videoElement.value.videoHeight || 720
    frameSize.value = { width, height }

    await listCameras()
    connectWebSocket()
    startCaptureLoop()
  } catch (error) {
    stopTracks()
    errorMessage.value = cameraErrorMessage(error)
  } finally {
    isStarting.value = false
  }
}

function cameraErrorMessage(error) {
  if (error.name === 'NotAllowedError') {
    return 'Quyền truy cập camera đã bị từ chối. Hãy cho phép camera trong trình duyệt.'
  }
  if (error.name === 'NotFoundError') {
    return 'Không tìm thấy camera trên thiết bị.'
  }
  if (error.name === 'NotReadableError') {
    return 'Camera đang được ứng dụng khác sử dụng.'
  }
  return error.message || 'Không thể mở camera.'
}

async function changeCamera() {
  if (!isCameraActive.value) return
  stopCamera(false)
  await startCamera()
}

function connectWebSocket() {
  clearTimeout(reconnectTimer)

  if (!isCameraActive.value || !shouldReconnect) return
  if (socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) return

  socketStatus.value = 'connecting'
  socket = new WebSocket(getWebSocketUrl())

  socket.onopen = () => {
    socketStatus.value = 'online'
    errorMessage.value = ''
    awaitingResponse = false
  }

  socket.onmessage = (event) => {
    awaitingResponse = false

    try {
      const payload = JSON.parse(event.data)

      if (payload.error) {
        throw new Error(payload.error)
      }

      if (payload.width && payload.height) {
        frameSize.value = {
          width: payload.width,
          height: payload.height,
        }
      }

      detections.value = (payload.detections ?? []).map(normalizeDetection)
      inferenceTime.value = payload.inference_ms ?? null
      updateProcessedFps()
      nextTick(drawDetections)
    } catch (error) {
      errorMessage.value = `Dữ liệu từ AI không hợp lệ: ${error.message}`
    }
  }

  socket.onerror = () => {
    socketStatus.value = 'offline'
  }

  socket.onclose = () => {
    socketStatus.value = isCameraActive.value ? 'offline' : 'idle'
    awaitingResponse = false
    socket = null

    if (shouldReconnect && isCameraActive.value) {
      reconnectTimer = setTimeout(connectWebSocket, 1500)
    }
  }
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

function startCaptureLoop() {
  clearInterval(captureTimer)
  captureTimer = setInterval(captureAndSend, 1000 / targetFps.value)
}

function updateCaptureRate() {
  if (isCameraActive.value) startCaptureLoop()
}

function captureAndSend() {
  const video = videoElement.value
  const canvas = captureCanvas.value

  if (
    !video
    || !canvas
    || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA
    || !socket
    || socket.readyState !== WebSocket.OPEN
    || awaitingResponse
  ) {
    return
  }

  const sourceWidth = video.videoWidth
  const sourceHeight = video.videoHeight
  if (!sourceWidth || !sourceHeight) return

  const outputWidth = Math.min(sourceWidth, 640)
  const outputHeight = Math.round(sourceHeight * (outputWidth / sourceWidth))
  canvas.width = outputWidth
  canvas.height = outputHeight

  const context = canvas.getContext('2d', { alpha: false })
  context.drawImage(video, 0, 0, outputWidth, outputHeight)

  awaitingResponse = true
  canvas.toBlob(
    (blob) => {
      if (!blob || !socket || socket.readyState !== WebSocket.OPEN) {
        awaitingResponse = false
        return
      }
      socket.send(blob)
    },
    'image/jpeg',
    0.72,
  )
}

function drawDetections() {
  const canvas = overlayCanvas.value
  if (!canvas) return

  const width = frameSize.value.width
  const height = frameSize.value.height
  canvas.width = width
  canvas.height = height

  const context = canvas.getContext('2d')
  context.clearRect(0, 0, width, height)

  detections.value.forEach((detection) => {
    if (!detection.bbox || detection.bbox.some((value) => !Number.isFinite(value))) return

    const [x1, y1, x2, y2] = detection.bbox
    const color = detection.status === 'violation'
      ? '#ff5a52'
      : detection.status === 'safe'
        ? '#42d392'
        : '#f6a83b'
    const label = `${detection.label} ${Math.round(detection.confidence * 100)}%`

    context.strokeStyle = color
    context.lineWidth = Math.max(2, width / 320)
    context.strokeRect(x1, y1, x2 - x1, y2 - y1)

    context.font = `600 ${Math.max(13, width / 48)}px DM Sans, Arial`
    const textWidth = context.measureText(label).width
    const labelHeight = Math.max(24, width / 26)
    const labelY = Math.max(0, y1 - labelHeight)

    context.fillStyle = color
    context.fillRect(x1, labelY, textWidth + 14, labelHeight)
    context.fillStyle = '#0c1720'
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

function stopTracks() {
  cameraStream.value?.getTracks().forEach((track) => track.stop())
  cameraStream.value = null
}

function stopCamera(resetResults = true) {
  shouldReconnect = false
  clearInterval(captureTimer)
  clearTimeout(reconnectTimer)
  captureTimer = null
  reconnectTimer = null
  awaitingResponse = false

  if (socket) {
    socket.onclose = null
    socket.close()
    socket = null
  }

  stopTracks()
  if (videoElement.value) videoElement.value.srcObject = null

  isCameraActive.value = false
  socketStatus.value = 'idle'
  processedFps.value = 0
  processedFrames = []

  if (resetResults) {
    detections.value = []
    inferenceTime.value = null
    const context = overlayCanvas.value?.getContext('2d')
    context?.clearRect(0, 0, overlayCanvas.value.width, overlayCanvas.value.height)
  }
}

onBeforeUnmount(() => stopCamera())
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#" aria-label="PPE Vision home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 28 28" fill="none">
            <path d="M5.5 15.2V12a8.5 8.5 0 0 1 17 0v3.2" />
            <path d="M3.5 15.2h21v3.5h-21zM9 11.5V7.2M19 11.5V7.2" />
          </svg>
        </span>
        <span>
          <strong>PPE VISION</strong>
          <small>LIVE SAFETY MONITOR</small>
        </span>
      </a>

      <div class="connection-status" :class="socketStatus">
        <span class="status-dot"></span>
        <span>{{ connectionLabel }}</span>
      </div>
    </header>

    <main>
      <section class="hero">
        <div>
          <p class="eyebrow">YOLOV8 · LIVE MONITORING</p>
          <h1>Giám sát PPE.<br /><em>Theo thời gian thực.</em></h1>
        </div>
        <p class="hero-copy">
          Camera gửi từng khung hình đến mô hình YOLO và hiển thị cảnh báo PPE
          ngay trên video — không lưu hình ảnh tại trình duyệt.
        </p>
      </section>

      <section class="workspace-grid">
        <article class="panel camera-panel">
          <div class="panel-heading">
            <div>
              <span class="step-number">LIVE</span>
              <h2>Camera hiện trường</h2>
            </div>
            <span v-if="isCameraActive" class="live-pill"><i></i> Đang ghi hình</span>
          </div>

          <div class="camera-stage" :class="{ active: isCameraActive }" :style="stageStyle">
            <template v-if="isCameraActive">
              <video ref="videoElement" autoplay muted playsinline></video>
              <canvas ref="overlayCanvas" class="overlay-canvas"></canvas>

              <div class="camera-hud top-left">
                <span>CAM 01</span>
                <span>{{ frameSize.width }} × {{ frameSize.height }}</span>
              </div>
              <div class="camera-hud top-right">
                <span :class="['hud-dot', socketStatus]"></span>
                {{ socketStatus === 'online' ? 'AI ONLINE' : 'AI OFFLINE' }}
              </div>
              <div class="corner-marker marker-tl"></div>
              <div class="corner-marker marker-tr"></div>
              <div class="corner-marker marker-bl"></div>
              <div class="corner-marker marker-br"></div>
            </template>

            <div v-else class="camera-placeholder">
              <div class="camera-icon">
                <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
                  <rect x="3" y="7" width="20" height="18" rx="3" />
                  <path d="m23 13 6-3v12l-6-3M9 7l2-3h5l2 3" />
                  <circle cx="13" cy="16" r="5" />
                </svg>
              </div>
              <strong>Camera chưa được bật</strong>
              <p>Cho phép truy cập camera để bắt đầu phát hiện PPE.</p>
              <button class="primary-button compact" type="button" :disabled="isStarting" @click="startCamera">
                <span>{{ isStarting ? 'Đang mở camera...' : 'Bật camera' }}</span>
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M5 12h14m-5-5 5 5-5 5" />
                </svg>
              </button>
            </div>
          </div>

          <canvas ref="captureCanvas" class="hidden-canvas"></canvas>

          <div v-if="errorMessage" class="error-message" role="alert">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 8v4m0 4h.01M10.3 3.9 2.4 17.5A2 2 0 0 0 4.1 20h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
            </svg>
            <span>{{ errorMessage }}</span>
          </div>

          <div class="camera-controls">
            <label class="field-control">
              <span>Nguồn camera</span>
              <select v-model="selectedCameraId" :disabled="!cameraDevices.length" @change="changeCamera">
                <option v-if="!cameraDevices.length" value="">Camera mặc định</option>
                <option
                  v-for="(camera, index) in cameraDevices"
                  :key="camera.deviceId"
                  :value="camera.deviceId"
                >
                  {{ camera.label || `Camera ${index + 1}` }}
                </option>
              </select>
            </label>

            <label class="field-control fps-control">
              <span>Tần suất gửi</span>
              <select v-model.number="targetFps" @change="updateCaptureRate">
                <option :value="3">3 FPS</option>
                <option :value="5">5 FPS</option>
                <option :value="8">8 FPS</option>
              </select>
            </label>

            <button
              v-if="isCameraActive"
              class="stop-button"
              type="button"
              @click="stopCamera()"
            >
              Dừng camera
            </button>
          </div>
        </article>

        <aside class="panel result-panel">
          <div class="panel-heading">
            <div>
              <span class="step-number">AI</span>
              <h2>Phân tích trực tiếp</h2>
            </div>
            <span class="model-name">YOLOv8</span>
          </div>

          <div class="metric-strip">
            <div>
              <span>AI FPS</span>
              <strong>{{ processedFps || '—' }}</strong>
            </div>
            <div>
              <span>Độ trễ</span>
              <strong>{{ inferenceTime !== null ? `${inferenceTime} ms` : '—' }}</strong>
            </div>
          </div>

          <div class="summary-grid">
            <div class="summary-card neutral">
              <span>Người</span>
              <strong>{{ peopleCount }}</strong>
            </div>
            <div class="summary-card safe">
              <span>PPE đạt</span>
              <strong>{{ compliantCount }}</strong>
            </div>
            <div class="summary-card violation">
              <span>Vi phạm</span>
              <strong>{{ violationCount }}</strong>
            </div>
          </div>

          <div v-if="detections.length" class="detection-list">
            <div class="list-title">
              <span>Đối tượng trong frame</span>
              <span>{{ detections.length }}</span>
            </div>
            <div
              v-for="detection in detections"
              :key="detection.id"
              class="detection-item"
            >
              <span class="result-indicator" :class="detection.status"></span>
              <div>
                <strong>{{ detection.label }}</strong>
                <span v-if="detection.status === 'violation'">Cần kiểm tra</span>
                <span v-else-if="detection.status === 'safe'">Thiết bị bảo hộ</span>
                <span v-else>Đối tượng</span>
              </div>
              <strong>{{ Math.round(detection.confidence * 100) }}%</strong>
            </div>
          </div>

          <div v-else class="empty-result">
            <div class="radar-icon">
              <span></span>
              <span></span>
              <i></i>
            </div>
            <strong>{{ isCameraActive ? 'Đang chờ kết quả' : 'Chưa bắt đầu giám sát' }}</strong>
            <p>
              {{ isCameraActive
                ? 'Kết quả PPE sẽ xuất hiện khi backend nhận được frame từ camera.'
                : 'Bật camera để bắt đầu phát hiện thiết bị bảo hộ.' }}
            </p>
          </div>

          <div class="legend">
            <span><i class="safe"></i> PPE đạt</span>
            <span><i class="violation"></i> Vi phạm</span>
            <span><i class="neutral"></i> Đối tượng</span>
          </div>
        </aside>
      </section>
    </main>

    <footer>
      <span>PPE Vision · Realtime MVP</span>
      <span>Frame được xử lý trực tiếp · Không lưu tại frontend</span>
    </footer>
  </div>
</template>
