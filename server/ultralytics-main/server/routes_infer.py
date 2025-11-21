# server/routes_infer.py，REST 推理接口
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
import os, tempfile, shutil
import cv2, numpy as np
from anyio import to_thread
from .infer import load_model, infer_image, infer_video, _MODEL_NAME

router = APIRouter(
    prefix="/api",  # 所有接口统一加 /api
    tags=["infer"]  # Swagger 文档里的分组名
)


@router.get("/model")
def model_info():
    m = load_model()
    names = getattr(m.model, "names", {})
    return {
        "weights": _MODEL_NAME,
        "num_classes": len(names),
        "names": names,
    }


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/infer/image")
async def api_infer_image(
        file: UploadFile = File(...),
        min_conf: float = Form(0.25)
):
    # 读入为 numpy（BGR）
    data = await file.read()
    img_array = np.frombuffer(data, dtype=np.uint8)
    img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return JSONResponse({"error": "bad image"}, status_code=400)

    # 丢到线程池，避免阻塞事件循环
    result = await to_thread.run_sync(infer_image, img_bgr, min_conf)
    return result


@router.post("/infer/video")
async def api_infer_video(
        file: Optional[UploadFile] = File(None),
        video_url: Optional[str] = Form(None),
        every_nth: int = Form(5),
        min_conf: float = Form(0.25),
):
    """
    1) 可以直接上传视频文件；
    2) 或者给一个 video_url（本机/公网可达），后端用 OpenCV 读。
    """
    if not file and not video_url:
        return JSONResponse(
            {"error": "need file or video_url"},
            status_code=400
        )

    tmp_path = None
    try:
        # 2) 准备本地路径
        if file:
            suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                shutil.copyfileobj(file.file, f)
                tmp_path = f.name
            path = tmp_path
        else:
            # 让后端能直接读这个 URL（本机/公网可达）
            path = video_url

        # 3) 推理（线程池）
        result = await to_thread.run_sync(infer_video, path, every_nth, min_conf)
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
