# server/pipeline_dual.py
from typing import Dict, Any, Optional, Tuple
import os, cv2, numpy as np
from ultralytics import YOLO
from .infer import _results_to_objects  # 复用你已有的统一结果转换函数
import base64
from pathlib import Path


# 懒加载为单例，避免重复占显存
_WATER_MODEL: Optional[YOLO] = None
_RISK_MODEL: Optional[YOLO] = None
BASE_DIR = Path(__file__).resolve().parent.parent

def load_dual_models() -> Tuple[YOLO, YOLO]:
    """
    两个模型：
    - WATER_WEIGHTS：积水覆盖（分割/检测）
    - RISK_WEIGHTS ：基于车辆高度估计风险（分类/检测/回归）
    """
    global _WATER_MODEL, _RISK_MODEL
    if _WATER_MODEL is None:
        w = os.getenv("WATER_WEIGHTS") or str(BASE_DIR / "weights" / "best.pt")
        _WATER_MODEL = YOLO(w)
    if _RISK_MODEL is None:
        w2 = os.getenv("RISK_WEIGHTS") or str(BASE_DIR / "weights" / "YOLOv8.pt")
        _RISK_MODEL = YOLO(w2)
    return _WATER_MODEL, _RISK_MODEL


def _predict(model: YOLO, frame_bgr: np.ndarray, *, imgsz=640, conf=0.25, iou=0.45, retina_masks=True):
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return model.predict(rgb, imgsz=imgsz, conf=conf, iou=iou, retina_masks=retina_masks, verbose=False)[0]


def _water_coverage_pct(result, h: int, w: int) -> float:
    """把分割多边形填充成二值图，计算覆盖百分比"""
    mask = np.zeros((h, w), dtype=np.uint8)
    polys = getattr(result, "masks", None)
    if polys is not None and getattr(polys, "xy", None) is not None:
        pts = [np.asarray(p, dtype=np.int32) for p in polys.xy if p is not None]
        if pts:
            cv2.fillPoly(mask, pts, 255)
    return float(mask.mean() / 255.0 * 100.0)


def _risk_level_from_result(result) -> Tuple[int, Dict[str, Any]]:
    """
    计算“本帧风险等级”= 该帧所有候选的最大等级。
    同时返回每个检测框的归一化坐标 boxes_norm:
      boxes_norm = [[x1, y1, x2, y2, level], ...]  均为 0~1
    """
    import numpy as np
    detail: Dict[str, Any] = {}

    levels = []

    # 1) 分类输出（result.probs）
    if getattr(result, "probs", None) is not None:
        idx = int(result.probs.top1)
        score = float(result.probs.top1conf)
        names = result.names or {}
        ncls = max(1, int(getattr(result.probs, "data", np.empty((1,))).shape[-1]))
        level_cls = int(np.interp(idx, [0, ncls - 1], [0, 5]))
        levels.append(level_cls)
        detail["cls"] = {
            "label": names.get(idx, str(idx)),
            "score": score,
            "level": level_cls
        }

    # 2) 检测输出（result.boxes）
    boxes = getattr(result, "boxes", None)
    if boxes is not None and getattr(boxes, "cls", None) is not None:
        names = result.names or {}
        cls_ids = boxes.cls.detach().cpu().numpy().astype(int)  # 每个框的类别

        # a) 若类别名就是风险档（low/med/high/...）：
        risk_map = {
            "low": 1,
            "medium": 3,
            "high": 5,
            "very_high": 5,
            "critical": 5,
        }

        # b) 若类别是索引(0..N-1)，线性映射到 0..5：
        def idx_to_level(i, n):
            return int(np.interp(i, [0, max(1, n - 1)], [0, 5]))

        ncls = len(names) if isinstance(names, dict) else (max(cls_ids) + 1 if len(cls_ids) else 1)

        box_levels = []
        boxes_norm = []

        # Ultralytics v8: boxes.xyxyn 为归一化后的 [x1,y1,x2,y2]
        xyxyn = getattr(boxes, "xyxyn", None)
        if xyxyn is not None:
            xyxyn = xyxyn.detach().cpu().numpy()
        else:
            xyxyn = None

        for i, cls_i in enumerate(cls_ids):
            name_i = names.get(cls_i, str(cls_i)) if isinstance(names, dict) else str(cls_i)
            if name_i in risk_map:
                lv = risk_map[name_i]
            else:
                lv = idx_to_level(cls_i, ncls)
            box_levels.append(lv)

            if xyxyn is not None and i < xyxyn.shape[0]:
                x1, y1, x2, y2 = xyxyn[i].tolist()
                boxes_norm.append([float(x1), float(y1), float(x2), float(y2), int(lv)])

        if box_levels:
            level_det = int(max(box_levels))
            levels.append(level_det)
            detail["det"] = {
                "levels": box_levels,
                "level_max": level_det,
                "boxes_norm": boxes_norm,
            }

    # 3) 兜底
    level_max = int(max(levels)) if levels else 0
    return level_max, detail


# ----掩膜→多边形（outer + holes），坐标归一化到 [0,1] ----
def mask_to_polygons(mask_bin: "np.ndarray", *, min_area_px: int = 64, epsilon_px: float = 2.0):
    """
    mask_bin: 二值(0/255)或(0/1)的 HxW 掩膜
    min_area_px: 过滤小碎片
    epsilon_px: 多边形简化强度（像素单位）
    return: [{ "outer": [[x,y],...], "holes": [ [[x,y],...], ... ] }, ...]  均为归一化坐标
    """
    import cv2, numpy as np

    m = (mask_bin > 0).astype("uint8")
    h, w = m.shape[:2]
    if h == 0 or w == 0:
        return []

    contours, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return []
    hier = hier[0]  # [next, prev, child, parent]

    polys = []
    outers = [i for i, h4 in enumerate(hier) if h4[3] == -1]  # parent == -1

    for oi in outers:
        cnt = contours[oi]
        if cv2.contourArea(cnt) < min_area_px:
            continue
        # 简化外轮廓
        cnt = cv2.approxPolyDP(cnt, epsilon_px, True)
        outer = [[float(x) / w, float(y) / h] for [[x, y]] in cnt]

        # 收集该外轮廓的所有子洞
        holes = []
        for ci, h4 in enumerate(hier):
            if h4[3] == oi:  # parent == oi
                c = contours[ci]
                if cv2.contourArea(c) < min_area_px:
                    continue
                c = cv2.approxPolyDP(c, epsilon_px, True)
                hole = [[float(x) / w, float(y) / h] for [[x, y]] in c]
                holes.append(hole)

        polys.append({"outer": outer, "holes": holes})

    return polys


def encode_mask_png_b64(mask_rgba):
    # 建议先缩小后编码：例如最长边 <= 640
    import cv2, base64
    h, w = mask_rgba.shape[:2]
    scale = 640.0 / max(h, w)
    if scale < 1.0:
        mask_rgba = cv2.resize(mask_rgba, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_NEAREST)
    ok, buf = cv2.imencode(".png", mask_rgba, [cv2.IMWRITE_PNG_COMPRESSION, 3])  # 压缩等级 3~4 较快
    if not ok:
        return None
    return base64.b64encode(buf).decode()


def infer_dual_on_frame(frame_bgr: "np.ndarray", params: dict = None) -> Dict[str, Any]:
    """
    单帧双模型推理（适配 WebSocket 调参）
    params 来自 WS，可包含：
      - conf_water / iou_water / conf_risk / imgsz_water / imgsz_risk ...
    """
    params = params or {}

    # === 从 params 中取参数（否则用默认值） ===
    conf_water = float(params.get("conf_water", 0.25))
    conf_risk = float(params.get("conf_risk", 0.25))
    return_mask = bool(params.get("return_mask", True))

    # 新增：模型输入尺寸，前端滑块可控
    imgsz_water = int(params.get("imgsz_water", 640) or 640)
    imgsz_risk = int(params.get("imgsz_risk", 640) or 640)

    # === 加载两套模型 ===
    water_m, risk_m = load_dual_models()

    h, w = frame_bgr.shape[:2]

    # === 积水分割 ===
    res_water = _predict(
        water_m, frame_bgr,
        imgsz=imgsz_water,  # 尺寸
        conf=conf_water,
        retina_masks=True
    )
    water_objs = _results_to_objects(res_water, min_conf=conf_water)
    water_mask, pct = _water_mask_and_pct(res_water, h, w)

    # === 风险等级 ===
    res_risk = _predict(
        risk_m, frame_bgr,
        imgsz=imgsz_risk,
        conf=conf_risk,
        retina_masks=False
    )

    level, risk_detail = _risk_level_from_result(res_risk)
    polys = mask_to_polygons(water_mask, min_area_px=64, epsilon_px=2.0)

    out = {
        "pct": pct,
        "level": level,
        "water": {
            "objects": water_objs,
            "image_h": h,
            "image_w": w,
            "polygons": polys,
        },
        "risk": risk_detail,
    }

    if return_mask:
        out["water"]["mask_png_b64"] = encode_mask_png_b64(water_mask)

    return out


def _water_mask_and_pct(result, h: int, w: int):
    """把分割结果栅格化到原图尺寸，得到 0/255 的二值掩膜和覆盖百分比"""
    import numpy as np, cv2
    mask = np.zeros((h, w), dtype=np.uint8)
    polys = getattr(result, "masks", None)

    # 1) 优先用多边形
    if polys is not None and getattr(polys, "xy", None) is not None:
        pts = [np.asarray(p, dtype=np.int32) for p in polys.xy if p is not None]
        if pts:
            cv2.fillPoly(mask, pts, 255)

    # 2) 若没有 xy，退化用 data（需 resize 回原图）
    elif polys is not None and getattr(polys, "data", None) is not None:
        m = polys.data
        try:
            m = m.cpu().numpy()  # (N, Hm, Wm)
            m = (m.max(axis=0) > 0.5).astype("uint8") * 255
            if m.shape[:2] != (h, w):
                m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
            mask = m
        except Exception:
            pass

    pct = float(mask.mean() / 255.0 * 100.0)
    return mask, pct
