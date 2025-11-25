# server/export_video.py------导出带掩膜的视频
from pathlib import Path
from typing import List, Optional
import cv2
import numpy as np
from ..database import get_conn
from .tick_overlay import parse_tick_row, TickOverlay


def draw_overlay_cv2(frame, ov: TickOverlay):
    """
    在单帧上画 water_polys + risk_boxes + 文本。
    ov 水平是 TickOverlay。
    """
    if ov is None:
        return

    h, w = frame.shape[:2]

    # ----- 掩膜多边形 -----
    polys = []
    for poly in ov.water_polys:
        if not poly:
            continue
        pts = []
        for pt in poly:
            if pt is None or len(pt) < 2:
                continue
            nx = max(0.0, min(1.0, float(pt[0])))
            ny = max(0.0, min(1.0, float(pt[1])))
            x = int(nx * w)
            y = int(ny * h)
            pts.append([x, y])
        if pts:
            polys.append(pts)

    if polys:
        pts_arr = [np.array(p, dtype=np.int32) for p in polys]
        # 半透明蓝色区域
        mask = frame.copy()
        cv2.fillPoly(mask, pts_arr, (255, 0, 0))  # BGR: 蓝
        frame[:] = cv2.addWeighted(frame, 0.6, mask, 0.4, 0)

        for p in pts_arr:
            cv2.polylines(frame, [p], isClosed=True, color=(255, 0, 0), thickness=2)

    # ----- 风险框 -----
    for box in ov.risk_boxes:
        if not box or len(box) < 4:
            continue

        nx1 = max(0.0, min(1.0, float(box[0])))
        ny1 = max(0.0, min(1.0, float(box[1])))
        nx2 = max(0.0, min(1.0, float(box[2])))
        ny2 = max(0.0, min(1.0, float(box[3])))

        x1 = int(nx1 * w)
        y1 = int(ny1 * h)
        x2 = int(nx2 * w)
        y2 = int(ny2 * h)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # ----- 左上角文字 -----
    texts = []
    if ov.water_percent is not None:
        texts.append(f"pct={ov.water_percent:.2f}%")
    if ov.risk_level is not None:
        texts.append(f"level={ov.risk_level}")
    if texts:
        cv2.putText(
            frame,
            "  ".join(texts),
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )


def load_ticks_for_session(session_id: int) -> List[TickOverlay]:
    """
    用 pymysql 直接查 detect_tick 表，不再用 SQLAlchemy 模型
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    video_sec,
                    water_polys,
                    risk_boxes,
                    water_percent,
                    risk_level
                FROM detect_tick
                WHERE session_id = %s
                ORDER BY video_sec
            """
            cur.execute(sql, (session_id,))
            rows = cur.fetchall()  # list[dict]，因为用了 DictCursor
        return [parse_tick_row(r) for r in rows]
    finally:
        conn.close()


def export_video_with_ticks(
    session_id: int,
    src_path: str,
    out_path: str,
):
    """
    使用 detect_tick 表，而不是重跑模型。
    """
    overlays: List[TickOverlay] = load_ticks_for_session(session_id)
    if not overlays:
        raise RuntimeError("该 session 没有 detect_tick 数据")

    cap = cv2.VideoCapture(src_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {src_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 5.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"无法创建输出视频: {out_path}")

    cur_idx = 0
    n_tick = len(overlays)
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # 当前帧时间（秒）
        t = frame_idx / fps

        # 找 t 之前最后一个 tick
        while cur_idx + 1 < n_tick and overlays[cur_idx + 1].t <= t:
            cur_idx += 1

        ov: Optional[TickOverlay] = overlays[cur_idx] if n_tick > 0 else None
        if ov:
            draw_overlay_cv2(frame, ov)

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()

