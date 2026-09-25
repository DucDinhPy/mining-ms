# PPE Vision Realtime Frontend

A Vue 3 + Vite administration interface for near real-time PPE detection using a
browser camera and WebSocket connection.

## Run locally

The backend must expose a WebSocket endpoint at
`ws://localhost:8000/api/ws/detect`.

```powershell
cd "D:\AI project\mining_project\frontend"
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`, select **Start camera**, and grant camera access in
the browser. Vite proxies `/api/ws/detect` to the backend on port `8000`.

## WebSocket contract

The frontend sends each camera frame as a binary JPEG. It waits for the response
before sending the next frame, preventing stale frames from building up when
inference is slower than capture.

The backend should return:

```json
{
  "width": 640,
  "height": 360,
  "detections": [
    {
      "class_name": "NO-Safety Vest",
      "confidence": 0.87,
      "bbox": [120.5, 80.2, 330.8, 350.1]
    }
  ],
  "inference_ms": 42
}
```

`inference_ms` is optional. `bbox` uses the `[x1, y1, x2, y2]` format based on
the frame dimensions returned in the response.

## Configuration

No `.env.local` file is required during development. When the frontend is not
served through the Vite proxy, create `.env.local`:

```env
VITE_WS_URL=ws://localhost:8000/api/ws/detect
```

Production deployments must use HTTPS/WSS for browsers to permit camera access
outside `localhost`:

```env
VITE_WS_URL=wss://api.example.com/api/ws/detect
```

## Production build

```powershell
npm.cmd run build
```

The output is written to `dist`.

## Module structure

```text
src/
├── components/
│   ├── AppSidebar.vue
│   └── AppTopbar.vue
├── config/
│   └── navigation.js
├── features/
│   └── ppe/
│       └── PpeRealtime.vue
└── App.vue
```

To add a feature:

1. Create its component under `src/features/<feature-name>/`.
2. Add a navigation entry in `src/config/navigation.js` and set
   `available: true`.
3. Import and render the new component in `App.vue`.

As the feature set grows, the conditional rendering in `App.vue` can be replaced
with Vue Router without changing the administration shell or sidebar.
