# MineOps Frontend

A Vue 3 + Vite administration interface for camera management and server-side
PPE detection.

## Run locally

Start MediaMTX, the .NET API, and the Python API before the frontend:

- .NET Camera API: `http://localhost:5057`
- Python PPE API: `http://127.0.0.1:8002`
- Camera WebSocket: `ws://127.0.0.1:8002/api/ws/cameras/{camera_id}`

```powershell
cd "D:\AI project\mining_project\frontend"
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`. Vite proxies `/api/cameras` to the .NET API and
`/api/ws` to the Python backend.

## PPE stream flow

The PPE page loads registered cameras from the .NET API. After a camera is
selected, it connects to the Python WebSocket by camera ID. Python opens the
camera RTSP stream and runs YOLO independently from the browser.

Each processed frame arrives as two ordered WebSocket messages:

1. A JSON `frame_metadata` message containing dimensions and detections.
2. A binary JPEG containing the corresponding camera frame.

Example metadata:

```json
{
  "type": "frame_metadata",
  "camera_id": "284255ea-c1e0-49c3-8c38-d06a5eac40c6",
  "camera_name": "Camera Test",
  "sequence": 12,
  "captured_at": "2026-09-27T00:00:00+00:00",
  "width": 1920,
  "height": 1080,
  "detections": [
    {
      "class_name": "NO-Safety Vest",
      "confidence": 0.87,
      "bbox": [120.5, 80.2, 330.8, 350.1]
    }
  ]
}
```

The backend can also send `camera_status` and `error` JSON messages.

## Configuration

No `.env.local` file is required during development. When the frontend is not
served through the Vite proxy, create `.env.local`:

```env
VITE_PPE_WS_BASE_URL=ws://127.0.0.1:8002
VITE_CAMERA_API_URL=http://localhost:5057/api/cameras
```

For an HTTPS deployment, use secure API and WebSocket origins:

```env
VITE_PPE_WS_BASE_URL=wss://ppe-api.example.com
VITE_CAMERA_API_URL=https://camera-api.example.com/api/cameras
```

## Production build

```powershell
npm.cmd run build
```

The output is written to `dist`.

## Module structure

```text
src/
|-- components/
|   |-- AppSidebar.vue
|   `-- AppTopbar.vue
|-- config/
|   `-- navigation.js
|-- features/
|   |-- cameras/
|   |   `-- CameraManagement.vue
|   `-- ppe/
|       `-- PpeRealtime.vue
|-- services/
|   `-- cameraApi.js
`-- App.vue
```

To add a feature:

1. Create its component under `src/features/<feature-name>/`.
2. Add a navigation entry in `src/config/navigation.js` and set
   `available: true`.
3. Import and render the component in `App.vue`.
