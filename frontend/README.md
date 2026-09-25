# PPE Vision Realtime Frontend

Frontend Vue 3 + Vite dùng webcam và WebSocket để phát hiện PPE gần thời gian thực.

## Chạy local

Backend phải lắng nghe WebSocket tại `ws://localhost:8000/api/ws/detect`.

```powershell
cd "D:\AI project\mining_project\frontend"
npm.cmd install
npm.cmd run dev
```

Mở `http://localhost:5173`, nhấn **Bật camera** và cho phép trình duyệt truy cập camera.
Vite sẽ proxy `/api/ws/detect` tới backend port `8000`.

## WebSocket contract

Frontend gửi từng frame dưới dạng binary JPEG. Frontend chỉ gửi frame kế tiếp sau khi
đã nhận kết quả frame trước, vì vậy frame cũ không bị xếp hàng khi inference chậm.

Backend cần trả JSON:

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

`inference_ms` là tùy chọn. `bbox` sử dụng định dạng `[x1, y1, x2, y2]` theo kích
thước frame trong response.

## Cấu hình

Trong development không cần tạo `.env.local`. Khi frontend không được phục vụ qua
Vite proxy, tạo `.env.local`:

```env
VITE_WS_URL=ws://localhost:8000/api/ws/detect
```

Production phải sử dụng HTTPS/WSS để trình duyệt cho phép camera ngoài `localhost`:

```env
VITE_WS_URL=wss://api.example.com/api/ws/detect
```

## Build production

```powershell
npm.cmd run build
```

Output nằm trong thư mục `dist`.
