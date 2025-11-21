from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from ultralytics import YOLO
import cv2
import threading
import asyncio
import json
#-------
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
import numpy as np

app = FastAPI()

# 加载训练好的 YOLO 模型
model = YOLO("best.pt")  # 请替换为你的模型路径

# 全局状态管理
clients = set()
stream_running = False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        clients.remove(websocket)


def detect_stream(rtsp_url):
    global stream_running
    stream_running = True
    cap = cv2.VideoCapture(rtsp_url)

    while stream_running:
        ret, frame = cap.read()
        if not ret:
            continue

        # 模型推理
        results = model.predict(frame, imgsz=640, conf=0.4, verbose=False)

        # 解析结果
        detections = []
        for box in results[0].boxes:
            cls = int(box.cls)
            conf = float(box.conf)
            xyxy = box.xyxy[0].tolist()
            detections.append({
                "class": model.names[cls],
                "confidence": round(conf, 2),
                "bbox": xyxy
            })

        # 统计高风险目标
        flood_count = sum(1 for d in detections if "water" in d["class"].lower())

        data = {
            "flood_count": flood_count,
            "detections": detections
        }

        # 通过 WebSocket 广播结果
        broadcast_data(json.dumps(data))

    cap.release()


def broadcast_data(message: str):
    """异步广播检测结果"""
    asyncio.run(send_to_clients(message))


async def send_to_clients(message: str):
    dead_clients = []
    for client in clients:
        try:
            await client.send_text(message)
        except:
            dead_clients.append(client)
    for dc in dead_clients:
        clients.remove(dc)


@app.get("/api/start_stream")
def start_stream(rtsp_url: str):
    """启动摄像头推理线程"""
    threading.Thread(target=detect_stream, args=(rtsp_url,), daemon=True).start()
    return {"status": "stream started"}


@app.get("/api/stop_stream")
def stop_stream():
    """停止推理线程"""
    global stream_running
    stream_running = False
    return {"status": "stream stopped"}


#-------
@app.post("/api/infer_image")
async def infer_image(file: UploadFile = File(...)):
    """上传图片文件进行YOLO识别"""
    contents = await file.read()
    npimg = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    results = model.predict(frame, imgsz=640, conf=0.4, verbose=False)
    detections = []
    for box in results[0].boxes:
        cls = int(box.cls)
        conf = float(box.conf)
        xyxy = box.xyxy[0].tolist()
        detections.append({
            "class": model.names[cls],
            "confidence": round(conf, 2),
            "bbox": xyxy
        })

    # 返回识别结果
    return JSONResponse(content={
        "detections": detections,
        "count": len(detections)
    })
