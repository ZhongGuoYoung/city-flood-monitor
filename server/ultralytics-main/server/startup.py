# server/startup.py,启动加载模型
import os
from .infer import load_model


def init_model_on_startup():
    """
    应用启动时调用，预加载 YOLO 模型，避免首请求卡顿。
    """
    weights = os.getenv("YOLO_WEIGHTS")  # 例如 set YOLO_WEIGHTS=weights/best.pt
    device = os.getenv("YOLO_DEVICE")  # 例如 CUDA: "cuda:0"
    load_model(weights=weights, device=device)
