# server/db_detect.py
import json
import pymysql
from contextlib import contextmanager
from typing import List, Optional, Dict
from datetime import datetime

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "city_flood_monitor",  # 比如 flood_monitor
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


@contextmanager
def get_conn():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def create_detect_session(camera_id: str,
                          camera_name: str,
                          location: str,
                          source_type: str,
                          source_url: str,
                          params: dict) -> int:
    """
    插入一条 detect_session，返回自增 id
    """
    sql = """
    INSERT INTO detect_session (
      camera_id, camera_name, location,
      source_type, source_url,
      fps, conf_water, iou_water, conf_risk, iou_risk,
      send_mask_every, imgsz_water, imgsz_risk
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    fps = params.get("fps")
    conf_water = params.get("conf_water")
    iou_water = params.get("iou_water")
    conf_risk = params.get("conf_risk")
    iou_risk = params.get("iou_risk")
    send_mask_every = params.get("send_mask_every")
    imgsz_water = params.get("imgsz_water")
    imgsz_risk = params.get("imgsz_risk")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                camera_id, camera_name, location,
                source_type, source_url,
                fps, conf_water, iou_water, conf_risk, iou_risk,
                send_mask_every, imgsz_water, imgsz_risk
            ))
            conn.commit()
            return cur.lastrowid


def save_detect_tick(session_id: int,
                     ts_ms: int,
                     video_sec: float,
                     result: dict,
                     water: dict,
                     risk: dict):
    if not session_id:
        return

    water_percent = int(round(result.get("pct", 0.0)))
    risk_level = int(result.get("level", 0))

    # 对齐 pipeline_dual.py 的字段名 image_h / image_w / polygons
    mask_h = water.get("image_h")
    mask_w = water.get("image_w")
    polys = water.get("polygons")
    polys_json = json.dumps(polys, ensure_ascii=False) if polys else None

    det = (risk or {}).get("det") or {}
    boxes_norm = det.get("boxes_norm") or []
    boxes_json = json.dumps(boxes_norm, ensure_ascii=False) if boxes_norm else None

    sql = """
    INSERT INTO detect_tick (
      session_id, ts_ms, video_sec,
      water_percent, risk_level,
      mask_h, mask_w, water_polys, risk_boxes
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                session_id, ts_ms, video_sec,
                water_percent, risk_level,
                mask_h, mask_w, polys_json, boxes_json
            ))
            conn.commit()


def update_detect_record_path(session_id: int, record_path: str) -> None:
    """
    识别开始后，补充这次会话对应的录像相对路径（/records/xxx/xxx.mp4）
    """
    if not session_id:
        return

    sql = "UPDATE detect_session SET record_path = %s WHERE id = %s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (record_path, session_id))
        conn.commit()


def finish_detect_session(session_id: int, status: str = "done"):
    """
    更新 detect_session 的状态 + 结束时间
    """
    if not session_id:
        return

    sql = "UPDATE detect_session SET status=%s, ended_at=NOW() WHERE id=%s"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (status, session_id))
            conn.commit()


def update_detect_session_record_path(session_id: int, record_path: str):
    """
    更新一次 detect_session 的录像路径
    """
    if not session_id or not record_path:
        return

    sql = "UPDATE detect_session SET record_path=%s WHERE id=%s"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (record_path, session_id))
            conn.commit()


# 查询数据detect_session
def list_detect_sessions(
        camera_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
) -> List[Dict]:
    """
    查询 detect_session 列表，用于历史界面。
    """
    sql = """
    SELECT
        id,
        camera_id,
        camera_name,
        location,
        source_type,
        source_url,
        record_path,
        status,
        started_at,
        ended_at
    FROM detect_session
    WHERE 1=1
    """
    params = []

    if camera_id:
        sql += " AND camera_id = %s"
        params.append(camera_id)

    if start:
        sql += " AND started_at >= %s"
        params.append(start)

    if end:
        sql += " AND started_at <= %s"
        params.append(end)

    sql += " ORDER BY started_at DESC LIMIT %s"
    params.append(limit)

    rows: List[Dict] = []
    with get_conn() as conn:
        # ★ 这里不要 dictionary=True，DB_CONFIG 里已经用了 DictCursor
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for r in cur.fetchall():
                rows.append(r)
    return rows


# 删除数据
def delete_detect_session(session_id: int) -> bool:
    """
    删除一条 detect_session 记录及其对应的 detect_tick 记录。
    返回 True 表示确实删掉了 session 记录，False 表示没有找到该 id。
    """
    if not session_id:
        return False

    sql_tick = "DELETE FROM detect_tick WHERE session_id = %s"
    sql_sess = "DELETE FROM detect_session WHERE id = %s"

    with get_conn() as conn:
        with conn.cursor() as cur:
            # 先删子表，避免外键约束问题
            cur.execute(sql_tick, (session_id,))
            cur.execute(sql_sess, (session_id,))
            affected = cur.rowcount  # 只看删 session 的结果
        conn.commit()

    return affected > 0


# 查询 detect_tick
def list_detect_ticks(session_id: int, limit: Optional[int] = None) -> List[Dict]:
    """
    按 session_id 查询 detect_tick 表，按 video_sec / ts_ms 排序。
    limit 为 0 或 None 表示不限制数量。
    """
    sql = """
        SELECT
            id,
            session_id,
            ts_ms,
            video_sec,
            water_percent,
            risk_level,
            mask_h,
            mask_w,
            water_polys,
            risk_boxes
        FROM detect_tick
        WHERE session_id = %s
        ORDER BY video_sec ASC, ts_ms ASC
    """
    params = [session_id]
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    rows: List[Dict] = []
    # 这里用 with get_conn() as conn
    with get_conn() as conn:
        # DB_CONFIG 里已经设置了 DictCursor，这里直接 cursor() 即可
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for r in cur.fetchall():
                rows.append(r)

    return rows
