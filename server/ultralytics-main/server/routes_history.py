# server/routes_history.py  —— 历史视频查看（MySQL detect_session）

from fastapi import APIRouter, Query, Request, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from .db_detect import list_detect_sessions, delete_detect_session, list_detect_ticks

router = APIRouter(prefix="/api/detect", tags=["detect"])


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    """
    支持几种常见格式：
    - YYYY-MM-DD
    - YYYY-MM-DDTHH:MM
    - YYYY-MM-DD HH:MM:SS
    """
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# 查询历史数据接口
@router.get("/sessions")
async def api_list_sessions(
        start: Optional[str] = Query(None, description="开始日期，例如 2025-11-18"),
        end: Optional[str] = Query(None, description="结束日期，例如 2025-11-18"),
        camera_id: Optional[str] = Query(None),
        limit: int = Query(100, ge=1, le=500),
        request: Request = None,
):
    # 1. 解析时间
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)

    # 只传了一边的情况，给个兜底：另一边补成同一天
    if start_dt and not end_dt:
        end_dt = start_dt
    elif end_dt and not start_dt:
        start_dt = end_dt

    # 如果都有，则把 end 扩展到“结束那天的次日 00:00”，方便包含整天
    if start_dt and end_dt:
        end_dt = end_dt + timedelta(days=1)

    # 2. 调用 MySQL 查询（不传 start/end 时，就是查全部，按 limit 限制条数）
    rows = list_detect_sessions(
        camera_id=camera_id,
        start=start_dt,
        end=end_dt,
        limit=limit,
    )

    base_url = str(request.base_url).rstrip("/")  # 例如 http://localhost:9000

    items = []

    def to_iso(v):
        if isinstance(v, datetime):
            return v.isoformat(timespec="seconds")
        return v

    # 3. 转成前端友好的结构 + 每条记录单独算 playUrl
    for r in rows:
        started_at = r.get("started_at")
        ended_at = r.get("ended_at")

        # 记录时间：你可以用 started_at 或 ended_at，这里用 started_at
        record_time = to_iso(started_at)

        # 每条记录自己的录像相对路径
        raw_path = (r.get("record_path") or "").strip()

        # ⭐ 在循环里为当前这条记录单独算 play_url
        play_url = None
        if raw_path:
            # 把 Windows 反斜杠转成正斜杠，并去掉开头的 ./ 等
            web_path = raw_path.replace("\\", "/").lstrip("./")

            if web_path.startswith("http://") or web_path.startswith("https://"):
                play_url = web_path
            elif web_path.startswith("/"):
                play_url = f"{base_url}{web_path}"
            else:
                # 如果路径里不带 /records，就自动补上
                if not web_path.startswith("records/"):
                    web_path = f"records/{web_path}"
                play_url = f"{base_url}/{web_path}"

        item = {
            "id": r["id"],
            "cameraId": r.get("camera_id"),
            "name": r.get("camera_name") or r.get("camera_id") or f"会话#{r['id']}",
            "location": r.get("location"),
            "status": r.get("status"),
            "sourceType": r.get("source_type"),
            "sourceUrl": r.get("source_url"),

            "recordPath": raw_path,  # 原始路径
            "playUrl": play_url,  # 这条记录自己的播放 URL

            "recordTime": record_time,
            "startedAt": to_iso(started_at),
            "finishedAt": to_iso(ended_at),
        }
        items.append(item)

    return {"items": items}


# 删除历史数据
@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: int):
    """
    删除一条 detect_session 历史记录（以及对应的 detect_tick 记录）
    URL: DELETE /api/detect/sessions/{session_id}
    """
    ok = delete_detect_session(session_id)
    if not ok:
        # 没有这条记录
        raise HTTPException(status_code=404, detail="detect_session not found")

    return {"success": True, "id": session_id}


# 查询 detect_tick
@router.get("/ticks")
async def api_list_ticks(
        session_id: int = Query(..., description="detect_session.id"),
        limit: int = Query(0, ge=0, le=20000, description="最多返回多少条记录，0 表示不限制")
):
    """
    查询某个 session 对应的 detect_tick 时序数据。

    前端调用：
      GET /api/detect/ticks?session_id=123

    返回字段：
      - id
      - session_id
      - ts_ms
      - video_sec
      - water_percent
      - risk_level
      - mask_h
      - mask_w
      - water_polys   (TEXT: JSON 字符串，前端自己 JSON.parse)
      - risk_boxes    (TEXT: JSON 字符串，前端自己 JSON.parse)
    """
    # 调用 db_detect 的查询函数
    rows = list_detect_ticks(session_id=session_id, limit=(limit or None))

    # 统一包装成 { items: [...] } 结构，跟 /sessions 风格一致
    items = [dict(r) for r in rows]

    return {
        "items": items,
        "count": len(items),
    }

