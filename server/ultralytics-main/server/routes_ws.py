# server/routes_ws.py  —— WebSocket 实时监控接口
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pathlib import Path
import asyncio, json, cv2, time, subprocess
import numpy as np
from datetime import datetime
from .pipeline_dual import infer_dual_on_frame
from .db_detect import (
    create_detect_session,
    save_detect_tick,
    finish_detect_session,
    update_detect_session_record_path,

)

router = APIRouter(tags=["ws"])

RECORD_ROOT = Path(__file__).resolve().parent / "records"
RECORD_ROOT.mkdir(parents=True, exist_ok=True)

# HLS 转帧的目标分辨率（可以按需调整）
HLS_WIDTH = 640
HLS_HEIGHT = 360

# 允许更新的参数白名单
ALLOWED_KEYS = {
    "fps", "conf_water", "iou_water", "conf_risk", "iou_risk",
    "send_mask_every", "imgsz_water", "imgsz_risk"
}


def _get(params: dict, key: str, default):
    v = params.get(key, default)
    return type(default)(v) if v is not None else default


VIDEO_ROOT = Path(__file__).resolve().parent / "demo_video/videos"


def map_url_to_path(url: str) -> str:
    """
    把前端的 url 映射为后端本地可打开的路径：
    /video/xxx → demo_video/videos/xxx
    非 http 相对路径 → demo_video/videos 下
    绝对路径 / http(s) 保持原样
    """
    url = (url or "").strip()
    if not url:
        return ""

    # 1) /video/xxx 或 /videos/xxx
    if url.startswith("/video/") or url.startswith("/videos/"):
        return str(VIDEO_ROOT / Path(url).name)

    # 2) 非 http 且不是绝对路径，当成 demo_video 下的文件名
    if not url.startswith("http"):
        p = Path(url)
        if not p.is_absolute():
            return str(VIDEO_ROOT / p.name)
        return str(p)

    # 3) http/https，直接给 OpenCV 用
    return url


async def ws_safe_send(ws: WebSocket, payload: dict) -> bool:
    """
    安全发送：连接关闭/异常时不再抛 RuntimeError，而是返回 False
    """
    try:
        await ws.send_text(json.dumps(payload))
        return True
    except Exception:
        return False


def start_ffmpeg_hls(url: str, width: int, height: int) -> subprocess.Popen:
    """
    用 ffmpeg 拉取 HLS(m3u8)，输出 BGR24 rawvideo 到 stdout
    ffmpeg -i <url> -f rawvideo -pix_fmt bgr24 -vf scale=WxH -
    """
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-i", url,
        "-an",  # 不要音频
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-vf", f"scale={width}:{height}",
        "-"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def start_ffmpeg_recorder(input_url: str, out_path: str, fps: Optional[float] = None) -> subprocess.Popen:
    """
    用 ffmpeg 录制一份 H.264 + AAC 的 MP4 文件

    示例等价命令：
    ffmpeg -y -i <input> -r <fps?> -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4
    """
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-y",               # 覆盖已有文件
        "-i", input_url,
    ]

    # 可选：根据参数控制输出帧率（和前端设置的 fps 对齐）
    if fps and fps > 0:
        cmd += ["-r", str(float(fps))]

    cmd += [
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        out_path,
    ]

    # 录制只要后台安静跑，不需要 stdout/stderr
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_ffmpeg_frame(proc: subprocess.Popen, width: int, height: int):
    """
    从 ffmpeg stdout 读一帧 rawvideo，返回 (ok, frame)
    """
    frame_size = width * height * 3
    if proc.stdout is None:
        return False, None
    data = proc.stdout.read(frame_size)
    if not data or len(data) < frame_size:
        return False, None
    frame = np.frombuffer(data, dtype=np.uint8)
    if frame.size != frame_size:
        return False, None
    frame = frame.reshape((height, width, 3))
    return True, frame


@router.websocket("/ws")
async def ws_realtime(ws: WebSocket):
    await ws.accept()

    session_id = None
    session_status = "running"
    save_to_db = False

    # 录像相关
    record_video = False    # 是否录制本次视频
    record_proc = None      # ffmpeg 录制子进程
    record_path = None      # 实际保存的文件路径（绝对路径）

    # ===== 1. 收启动包（前端第一次 send） =====
    try:
        cfg_raw = await ws.receive_text()
        cfg = json.loads(cfg_raw)
    except Exception:
        await ws_safe_send(ws, {"type": "error", "msg": "invalid start message"})
        await ws.close()
        return

    # 兼容 video_url / url 两种字段：优先 video_url
    raw_url = (cfg.get("video_url") or cfg.get("url") or "").strip()
    if not raw_url:
        await ws_safe_send(ws, {"type": "error", "msg": "missing video_url"})
        await ws.close()
        return

    video_url = map_url_to_path(raw_url)
    print("ws_realtime: raw_url =", repr(raw_url), "=> mapped =", repr(video_url))

    # ==== 摄像头信息 & 是否存库 ====
    save_to_db = bool(cfg.get("save_to_db"))
    camera_id = (cfg.get("camera_id") or "").strip()
    camera_name = (cfg.get("camera_name") or "").strip()
    location = (cfg.get("location") or "").strip()
    source_type = (cfg.get("source_type") or "video").strip()

    # 是否录像：可以前端传，也可以后端根据 source_type 默认打开
    record_video = bool(cfg.get("record_video"))
    if "record_video" not in cfg:
        # HLS / MJPEG 默认录制，其它默认不录
        if source_type in ("hls", "mjpeg"):
            record_video = True
        else:
            record_video = False

    # 默认参数 + 前端传来的
    params = {
        "fps": int(cfg.get("fps") or 10),
        "conf_water": float(cfg.get("conf_water") or 0.25),
        "iou_water": float(cfg.get("iou_water") or 0.45),
        "conf_risk": float(cfg.get("conf_risk") or 0.25),
        "iou_risk": float(cfg.get("iou_risk") or 0.45),
        "send_mask_every": int(cfg.get("send_mask_every") or 1),
        "imgsz_water": int(cfg.get("imgsz_water") or 640),
        "imgsz_risk": int(cfg.get("imgsz_risk") or 640),
    }
    # 简单裁剪
    params["fps"] = max(1, min(30, params["fps"]))
    for k in ("conf_water", "conf_risk", "iou_water", "iou_risk"):
        params[k] = max(0.0, min(1.0, params[k]))
    params["send_mask_every"] = max(0, params["send_mask_every"])
    params["imgsz_water"] = max(64, params["imgsz_water"])
    params["imgsz_risk"] = max(64, params["imgsz_risk"])

    # ==== 如需存库，先建一条 detect_session ====
    if save_to_db:
        try:
            session_id = create_detect_session(
                camera_id=camera_id,
                camera_name=camera_name,
                location=location,
                source_type=source_type,
                source_url=raw_url,  # 存原始地址方便回看
                params=params
            )
            await ws_safe_send(ws, {
                "type": "session_created",
                "session_id": session_id
            })
            print("[DB] create_detect_session OK, id =", session_id)
        except Exception as e:
            print("[DB] create_detect_session error:", e)
            save_to_db = False
            session_id = None

    # 是否 HLS 流（萤石云 HLS）
    is_hls = video_url.startswith("http") and ".m3u8" in video_url.lower()
    stop_flag = False

    # ===== 2. 后台接收 set_params / stop =====
    async def receiver():
        nonlocal stop_flag, session_status
        while not stop_flag:
            try:
                raw = await ws.receive_text()
            except Exception:
                break
            try:
                data = json.loads(raw)
            except Exception:
                continue

            if data.get("type") == "set_params":
                updated = []
                for key in ALLOWED_KEYS:
                    if key in data:
                        params[key] = _get(data, key, params[key])
                        updated.append(key)

                params["fps"] = max(1, min(30, int(params["fps"])))

                await ws_safe_send(ws, {
                    "type": "ack",
                    "updated": updated,
                    "params": params,
                })

            elif data.get("type") == "stop":
                stop_flag = True
                session_status = "stopped"
                break

    recv_task = asyncio.create_task(receiver())

    # 统计用
    avg_read_ms = avg_infer_ms = avg_send_ms = 0.0
    ema = 0.2
    last_mask_b64 = None
    t_start = time.perf_counter()
    tick_idx = 0
    frame_idx = 0

    try:
        # ======================  HLS via FFmpeg 模式  ======================
        if is_hls:
            proc = start_ffmpeg_hls(video_url, HLS_WIDTH, HLS_HEIGHT)
            if proc.stdout is None:
                await ws_safe_send(ws, {"type": "error", "msg": "ffmpeg start failed"})
                session_status = "error"
            else:
                print("[HLS] using ffmpeg pipeline")

                # ===== 只要需要录像，就单独启一个 ffmpeg 录制进程 =====
                if record_video and record_proc is None:
                    try:
                        cam_dir = RECORD_ROOT / (camera_id or "unknown")
                        cam_dir.mkdir(parents=True, exist_ok=True)
                        ts_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                        file_name = f"{ts_str}.mp4"
                        record_path = str(cam_dir / file_name)

                        record_proc = start_ffmpeg_recorder(
                            video_url,
                            record_path,
                            fps=params.get("fps"),
                        )
                        print("[REC] ffmpeg record start =>", record_path)
                    except Exception as re:
                        print("[REC] ffmpeg start error:", re)
                        record_proc = None
                        record_path = None

                # ===== 原来的推理循环保持不变 =====
                while not stop_flag:
                    # 1) 读一帧
                    t0 = time.perf_counter()
                    ok, frame = read_ffmpeg_frame(proc, HLS_WIDTH, HLS_HEIGHT)
                    frame_idx += 1
                    if not ok:
                        await ws_safe_send(ws, {"type": "eof"})
                        session_status = "done"
                        break
                    read_ms = (time.perf_counter() - t0) * 1000.0


                    # 4) 推理
                    t1 = time.perf_counter()
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        infer_dual_on_frame,
                        frame,
                        {**params, "return_mask": True},  # HLS 下每帧都算 mask，再由 send_mask_every 控制发不发
                    )
                    infer_ms = (time.perf_counter() - t1) * 1000.0

                    # 5) 掩膜缓存 & send_mask_every
                    water = (result.get("water") or {}).copy()
                    send_every = max(0, int(params.get("send_mask_every", 0)))
                    if send_every <= 0:
                        last_mask_b64 = None
                        water.pop("mask_png_b64", None)
                    else:
                        cur_mask = water.get("mask_png_b64")
                        if cur_mask:
                            last_mask_b64 = cur_mask
                        elif last_mask_b64:
                            water["mask_png_b64"] = last_mask_b64
                        # 控制“发不发”
                        if tick_idx % send_every != 0:
                            water.pop("mask_png_b64", None)

                    # 6) 时间戳：用相对时间
                    elapsed = time.perf_counter() - t_start
                    video_sec = elapsed
                    ts_ms = int(video_sec * 1000)

                    payload = {
                        "type": "tick",
                        "tick_idx": tick_idx,
                        "ts": ts_ms,
                        "pct": result.get("pct", 0.0),
                        "level": result.get("level", 0),
                        "water": water,
                        "risk": result.get("risk", {}),
                        "params": params,
                    }

                    # 7) 写 detect_tick
                    if session_id:
                        try:
                            save_detect_tick(
                                session_id=session_id,
                                ts_ms=ts_ms,
                                video_sec=video_sec,
                                result=result,
                                water=water,
                                risk=result.get("risk", {}),
                            )
                        except Exception as e:
                            print("[DB] save_detect_tick error:", e)

                    # 8) 发给前端
                    t2 = time.perf_counter()
                    ok = await ws_safe_send(ws, payload)
                    send_ms = (time.perf_counter() - t2) * 1000.0
                    if not ok:
                        session_status = "stopped"
                        break

                    # 9) 打印性能
                    avg_read_ms = (1 - ema) * avg_read_ms + ema * read_ms
                    avg_infer_ms = (1 - ema) * avg_infer_ms + ema * infer_ms
                    avg_send_ms = (1 - ema) * avg_send_ms + ema * send_ms
                    if tick_idx % max(1, params["fps"]) == 0:
                        print(
                            f"[WS-HLS] fps~{params['fps']} read={avg_read_ms:.1f}ms "
                            f"infer={avg_infer_ms:.1f}ms send={avg_send_ms:.1f}ms"
                        )

                    tick_idx += 1

        # ======================  非 HLS：原 OpenCV 模式  ======================
        else:
            cap = cv2.VideoCapture(video_url)
            if not cap.isOpened():
                await ws_safe_send(ws, {"type": "error", "msg": "video open failed"})
                if session_id:
                    try:
                        finish_detect_session(session_id, status="error")
                    except Exception as e:
                        print("[DB] finish_detect_session on open error:", e)
                await ws.close()
                return

            # 打开成功后，如果需要录像，就启动 ffmpeg 录制进程（只启动一次）
            if record_video and record_proc is None:
                try:
                    cam_dir = RECORD_ROOT / (camera_id or "unknown")
                    cam_dir.mkdir(parents=True, exist_ok=True)
                    ts_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                    file_name = f"{ts_str}.mp4"
                    record_path = str(cam_dir / file_name)

                    record_proc = start_ffmpeg_recorder(
                        video_url,
                        record_path,
                        fps=params.get("fps"),
                    )
                    print("[REC] ffmpeg record start =>", record_path)
                except Exception as re:
                    print("[REC] ffmpeg start error:", re)
                    record_proc = None
                    record_path = None

            src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            tick_period = 1.0 / params["fps"]
            next_wall = time.perf_counter()
            frames_per_tick = max(1, int(round(src_fps / params["fps"])))

            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            except Exception:
                pass

            while not stop_flag:
                ...

                # 1) 按墙钟限速
                now = time.perf_counter()
                if now < next_wall:
                    await asyncio.sleep(next_wall - now)

                # 2) 丢帧
                t0 = time.perf_counter()
                skips = max(0, frames_per_tick - 1)
                for _ in range(skips):
                    if not cap.grab():
                        await ws_safe_send(ws, {"type": "eof"})
                        stop_flag = True
                        session_status = "done"
                        break
                    frame_idx += 1
                if stop_flag:
                    break

                ok, frame = cap.read()
                frame_idx += 1
                if not ok:
                    await ws_safe_send(ws, {"type": "eof"})
                    session_status = "done"
                    break

                read_ms = (time.perf_counter() - t0) * 1000.0


                # 3) 控制是否算掩膜
                send_every = max(0, int(params.get("send_mask_every", 0)))
                need_mask = send_every > 0 and (tick_idx % send_every == 0)

                # 4) 推理
                t1 = time.perf_counter()
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    infer_dual_on_frame,
                    frame,
                    {**params, "return_mask": need_mask},
                )
                infer_ms = (time.perf_counter() - t1) * 1000.0

                water = (result.get("water") or {}).copy()
                if send_every <= 0:
                    last_mask_b64 = None
                    water.pop("mask_png_b64", None)
                else:
                    cur_mask = water.get("mask_png_b64")
                    if cur_mask:
                        last_mask_b64 = cur_mask
                    elif last_mask_b64:
                        water["mask_png_b64"] = last_mask_b64

                video_sec = frame_idx / max(1.0, float(src_fps))
                ts_ms = int(video_sec * 1000)

                payload = {
                    "type": "tick",
                    "tick_idx": tick_idx,
                    "ts": ts_ms,
                    "pct": result.get("pct", 0.0),
                    "level": result.get("level", 0),
                    "water": water,
                    "risk": result.get("risk", {}),
                    "params": params,
                }

                if session_id:
                    try:
                        save_detect_tick(
                            session_id=session_id,
                            ts_ms=ts_ms,
                            video_sec=video_sec,
                            result=result,
                            water=water,
                            risk=result.get("risk", {}),
                        )
                    except Exception as e:
                        print("[DB] save_detect_tick error:", e)

                t2 = time.perf_counter()
                ok = await ws_safe_send(ws, payload)
                send_ms = (time.perf_counter() - t2) * 1000.0
                if not ok:
                    session_status = "stopped"
                    break

                avg_read_ms = (1 - ema) * avg_read_ms + ema * read_ms
                avg_infer_ms = (1 - ema) * avg_infer_ms + ema * infer_ms
                avg_send_ms = (1 - ema) * avg_send_ms + ema * send_ms
                if tick_idx % max(1, params["fps"]) == 0:
                    print(
                        f"[WS] fps={params['fps']} read={avg_read_ms:.1f}ms "
                        f"infer={avg_infer_ms:.1f}ms send={avg_send_ms:.1f}ms "
                        f"need_mask={need_mask}"
                    )

                tick_idx += 1
                next_wall += tick_period
                if next_wall < time.perf_counter() - tick_period:
                    next_wall = time.perf_counter()

            cap.release()

    except WebSocketDisconnect:
        session_status = "stopped"
    except Exception as e:
        session_status = "error"
        print("[WS] runtime error:", e)
    finally:
        stop_flag = True
        recv_task.cancel()

        # 关闭 ffmpeg 录制进程
        if record_proc is not None:
            try:
                record_proc.terminate()
                record_proc.wait(timeout=3)
                print("[REC] ffmpeg record stop, path =", record_path)
            except Exception as e:
                print("[REC] ffmpeg terminate error:", e)
                try:
                    record_proc.kill()
                except Exception:
                    pass

        # 关闭 HLS ffmpeg 解码进程（start_ffmpeg_hls 用的那个 proc）
        if "proc" in locals():
            try:
                proc.kill()
            except Exception:
                pass

        try:
            await ws.close()
        except Exception:
            pass

        # 结束时更新 detect_session 状态 & record_path
        if session_id:
            try:
                if record_path:
                    rel_path = str(Path(record_path).relative_to(RECORD_ROOT.parent))
                    update_detect_session_record_path(session_id, rel_path)
                    print("[DB] update_record_path:", rel_path)
                finish_detect_session(session_id, session_status)
                print("[DB] finish_detect_session", session_id, "=>", session_status)
            except Exception as e:
                print("[DB] finish_detect_session error:", e)

