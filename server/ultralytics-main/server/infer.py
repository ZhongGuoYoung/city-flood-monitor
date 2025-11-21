# server/infer.py
from typing import List, Dict, Any, Optional
import os, cv2, numpy as np
from ultralytics import YOLO
from pathlib import Path

# 单例模型：进程内只加载一次
_MODEL: Optional[YOLO] = None
_MODEL_NAME: Optional[str] = None
TARGET_CLASS_NAMES = None
IMGSZ = int(os.getenv("YOLO_IMGSZ", "640"))
CONF = float(os.getenv("YOLO_CONF", "0.25"))
IOU = float(os.getenv("YOLO_IOU", "0.45"))
RETINA = (os.getenv("YOLO_RETINA", "1") == "1")  # 默认 True
BASE_DIR = Path(__file__).resolve().parent.parent


def load_model(weights: Optional[str] = None, device: Optional[str] = None) -> YOLO:
    """
    在服务启动时加载模型。weights 可用环境变量 YOLO_WEIGHTS 覆盖。
    device: "cuda:0" / "cpu"；不传则由 ultralytics 自动选择。
    """
    global _MODEL, _MODEL_NAME
    if _MODEL is not None:
        return _MODEL

    # 优先取环境变量
    weights = weights or str(BASE_DIR / "weights" / "best.pt")

    # 给一个兜底：新版本通常是 yolo11n.pt；旧版本常见 yolov8n.pt
    candidates = [weights, str(BASE_DIR / "weights" / "best.pt")]
    candidates = [w for w in candidates if w]  # 去掉 None
    last_err = None
    for w in candidates:
        try:
            _MODEL = YOLO(w)
            _MODEL_NAME = w
            break
        except Exception as e:
            last_err = e
            _MODEL = None
    if _MODEL is None:
        raise RuntimeError(f"Failed to load model: {last_err}")

    # 把模型放到指定 device（可选）
    try:
        if device:
            _MODEL.to(device)
    except Exception:
        pass

    # 轻量 warmup（32x32 的空帧）
    try:
        _MODEL.predict(np.zeros((32, 32, 3), dtype=np.uint8), verbose=False)
    except Exception:
        pass

    return _MODEL


def _predict_frame(model: YOLO, frame_bgr: np.ndarray):
    # 1) 统一色彩空间
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    # 2) 统一推理超参（与 GUI 对齐）
    return model.predict(
        frame_rgb, imgsz=IMGSZ, conf=CONF, iou=IOU,
        retina_masks=RETINA, verbose=False
    )[0]


def _results_to_objects(result, min_conf: float = 0.25):
    """
        统一把 result 转成 [{cls, conf, bbox?, poly?}, ...]
        - bbox: [x1,y1,x2,y2] 像素坐标
        - poly: [[x,y], [x,y], ...] 像素坐标（分割时提供）
        """
    objs = []
    names = result.names
    # boxes
    xyxy = result.boxes.xyxy.detach().cpu().numpy() if result.boxes is not None else None
    conf = result.boxes.conf.detach().cpu().numpy() if result.boxes is not None else None
    cls = result.boxes.cls.detach().cpu().numpy().astype(int) if result.boxes is not None else None
    # masks（seg 模型时）
    polys = result.masks.xy if getattr(result, "masks", None) is not None else None  # 已是原图坐标

    n = 0
    if xyxy is not None:
        n = len(xyxy)
    elif polys is not None:
        n = len(polys)

    for i in range(n):
        cf = float(conf[i]) if conf is not None else 1.0
        if cf < min_conf: continue
        c = int(cls[i]) if cls is not None else 0
        item = {"cls": names.get(c, str(c)), "conf": cf}
        if xyxy is not None:
            x1, y1, x2, y2 = map(float, xyxy[i])
            item["bbox"] = [x1, y1, x2, y2]
        if polys is not None and i < len(polys) and polys[i] is not None:
            # ★ 不要 round，保留完整多边形点，边缘更顺滑
            item["poly"] = polys[i].tolist()
        objs.append(item)
    return objs


def infer_image(img_bgr: np.ndarray, min_conf: float = 0.25) -> Dict[str, Any]:
    model = load_model()
    res = model.predict(img_bgr, verbose=False)[0]
    objs = _results_to_objects(res, min_conf=min_conf)
    h, w = img_bgr.shape[:2]
    return {"image_meta": {"width": w, "height": h}, "objects": objs}


def infer_video(path: str, every_nth: int = 5, min_conf: float = 0.25):
    model = load_model()
    cap = cv2.VideoCapture(path)
    if not cap.isOpened(): raise RuntimeError("cannot open video")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = int((cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps) * 1000)

    frames, idx = [], 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        if idx % max(1, every_nth) != 0: idx += 1; continue
        t_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
        res = _predict_frame(model, frame)
        objs = _results_to_objects(res, min_conf=min_conf)
        frames.append({"t_ms": t_ms, "objects": objs})
        idx += 1
    cap.release()
    return {"video_meta": {"fps": fps, "duration_ms": dur, "width": w, "height": h}, "frames": frames}
