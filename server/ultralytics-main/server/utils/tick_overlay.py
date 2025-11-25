# server/tick_overlay.py 处理视频
from dataclasses import dataclass
from typing import List, Optional
import json


@dataclass
class TickOverlay:
    t: float
    water_polys: list
    risk_boxes: list
    water_percent: Optional[float] = None
    risk_level: Optional[int] = None


def _get(row, key, default=None):
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def parse_tick_row(row) -> TickOverlay:
    # video_sec 如果是毫秒就 /1000.0，这里先按“秒”写
    t = float(_get(row, "video_sec", 0.0))

    water_polys = []
    raw_wp = _get(row, "water_polys")
    if raw_wp:
        try:
            parsed = json.loads(raw_wp)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "outer" in item:
                        water_polys.append(item["outer"])
                    elif isinstance(item, list):
                        water_polys.append(item)
        except Exception:
            pass

    risk_boxes = []
    raw_rb = _get(row, "risk_boxes")
    if raw_rb:
        try:
            parsed = json.loads(raw_rb)
            if isinstance(parsed, list):
                risk_boxes = parsed
        except Exception:
            pass

    return TickOverlay(
        t=t,
        water_polys=water_polys,
        risk_boxes=risk_boxes,
        water_percent=_get(row, "water_percent"),
        risk_level=_get(row, "risk_level"),
    )
