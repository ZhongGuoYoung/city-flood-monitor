# realtime_client_with_params.py
# -*- coding: utf-8 -*-
"""
实时识别客户端（带运行时参数控制）
依赖:
pip install -U opencv-python pillow matplotlib websocket-client
运行:
python realtime_client_with_params.py
说明:
- 启动后选择本地视频或填 URL，设置 FPS/conf_water/conf_risk/send_mask_every，
  点击“开始识别”后脚本会建立 WebSocket 到 WS_URL 并发送 start 包。
- 运行中调整滑块会在 300ms 防抖后发送 set_params 到后端（如果连接已建立）。
"""
import os
import threading
import json
import time
import cv2
import numpy as np
from websocket import create_connection, WebSocketConnectionClosedException

import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ====================== 配置区 ======================
WS_URL = "ws://localhost:9000/ws"  # ← 修改为你的后端 WebSocket 地址
# 可调整默认值
DEFAULT_FPS = 5
DEFAULT_CONF_WATER = 0.25
DEFAULT_CONF_RISK = 0.25
DEFAULT_SEND_MASK_EVERY = 0  # 0 表示不每帧传掩膜；>0 表示每 N 帧带一次掩膜
OVERLAY_COLOR = (255, 0, 0)   # BGR：掩膜填充色
OVERLAY_ALPHA = 0.35
PARAM_DEBOUNCE_MS = 300       # 调参防抖（毫秒）
# ===================================================


class RealtimeClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("实时识别（可调 FPS / 阈值 / 掩膜频率）")

        # --- 顶部工具条（URL + 选择 + 控件） ---
        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        tk.Label(top, text="视频路径/URL:").grid(row=0, column=0, sticky="w")
        self.entry = tk.Entry(top, width=60)
        self.entry.grid(row=0, column=1, columnspan=3, padx=6, sticky="w")
        tk.Button(top, text="选择本地视频", command=self.choose_file).grid(row=0, column=4, padx=6)

        # 参数控件：fps / conf_water / conf_risk / send_mask_every
        tk.Label(top, text="FPS(每秒tick):").grid(row=1, column=0, sticky="w", pady=6)
        self.fps_var = tk.IntVar(value=DEFAULT_FPS)
        self.fps_scale = tk.Scale(top, from_=1, to=30, orient=tk.HORIZONTAL, variable=self.fps_var,
                                  command=lambda v: self.schedule_send_params())
        self.fps_scale.grid(row=1, column=1, sticky="we", padx=6)

        tk.Label(top, text="conf_water:").grid(row=1, column=2, sticky="w")
        self.conf_water_var = tk.DoubleVar(value=DEFAULT_CONF_WATER)
        self.cw_scale = tk.Scale(top, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL,
                                 variable=self.conf_water_var, command=lambda v: self.schedule_send_params())
        self.cw_scale.grid(row=1, column=3, sticky="we", padx=6)

        tk.Label(top, text="conf_risk:").grid(row=2, column=0, sticky="w", pady=6)
        self.conf_risk_var = tk.DoubleVar(value=DEFAULT_CONF_RISK)
        self.cr_scale = tk.Scale(top, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL,
                                 variable=self.conf_risk_var, command=lambda v: self.schedule_send_params())
        self.cr_scale.grid(row=2, column=1, sticky="we", padx=6)

        tk.Label(top, text="send_mask_every:").grid(row=2, column=2, sticky="w")
        self.send_mask_var = tk.IntVar(value=DEFAULT_SEND_MASK_EVERY)
        self.send_mask_spin = tk.Spinbox(top, from_=0, to=300, width=6, textvariable=self.send_mask_var,
                                         command=self.schedule_send_params)
        self.send_mask_spin.grid(row=2, column=3, sticky="w", padx=6)

        # Control buttons
        tk.Button(top, text="开始识别", command=self.start).grid(row=0, column=5, padx=6)
        tk.Button(top, text="停止", command=self.stop).grid(row=0, column=6, padx=6)

        # 状态栏
        self.status_label = tk.Label(root, text="状态：就绪", anchor="w")
        self.status_label.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0,6))

        # --- 主区域：左视频 + 右折线 ---
        main = tk.Frame(root)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=6)

        # 左：视频区域
        left = tk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(left, bg="#000000")
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # HUD (右上 of video)
        self.hud = tk.Label(left, text="", fg="#EEEEEE", bg="#000000")
        self.hud.place(relx=1.0, rely=0.0, anchor="ne")  # 右上角

        # 右：折线区域（Matplotlib）
        right = tk.Frame(main, width=380)
        right.pack(side=tk.LEFT, fill=tk.BOTH)

        self.fig = Figure(figsize=(4.0, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("实时曲线：pct(%) / level")
        self.ax.set_xlabel("time (s)")
        self.ax.grid(True, linestyle="--", alpha=0.4)

        (self.line_pct,)   = self.ax.plot([], [], label="pct(%)", linewidth=2)
        (self.line_level,) = self.ax.plot([], [], label="level(0-5)", linewidth=2)
        self.ax.legend(loc="upper left")

        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 状态
        self.cap = None
        self.playing = False
        self.frame_timer_ms = 33
        self.lock = threading.Lock()

        # WebSocket
        self.ws_thread = None
        self.ws = None
        self.ws_running = False

        # 数据共享（来自 WS）
        self.last_polys = []  # List[List[[x,y],...]]
        self.image_w = 0
        self.image_h = 0
        self.last_ts = 0
        self.last_pct = 0.0
        self.last_level = 0

        # 曲线缓存
        self.t0 = None
        self.ts_list = []
        self.pct_list = []
        self.level_list = []

        # 参数防抖句柄
        self._param_debounce_id = None

        # 更新曲线定时器
        self.root.after(200, self.update_plot_timer)

    # ========== UI 事件 ==========
    def choose_file(self):
        path = filedialog.askopenfilename(title="选择视频文件",
                                          filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv;*.flv;*.ts"),
                                                     ("All Files", "*.*")])
        if path:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, path)

    def start(self):
        if self.playing:
            return
        path = self.entry.get().strip()
        if not path:
            messagebox.showerror("错误", "请先选择视频或填写 URL")
            return

        # 打开本地/网络视频用于显示（OpenCV）
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            messagebox.showerror("错误", "OpenCV 无法打开该视频/流，请检查路径或解码器。")
            self.cap = None
            return

        # 估算显示帧率（仅用于本地前端播放）
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 1e-2:
            fps = 25.0
        self.frame_timer_ms = int(1000.0 / fps)

        # 清空曲线数据
        self.t0 = None
        self.ts_list.clear()
        self.pct_list.clear()
        self.level_list.clear()

        # 打开 WebSocket（后端拉同一个地址/路径做识别）
        self.open_ws(path)

        self.playing = True
        self.read_frame_loop()

    def stop(self):
        self.playing = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.close_ws()
        self.status_label.config(text="状态：已停止")

    def on_close(self):
        self.stop()
        self.root.destroy()

    # ========== WebSocket ==========
    def open_ws(self, video_url: str):
        if self.ws_running:
            return

        def run():
            self.ws_running = True
            try:
                self.ws = create_connection(WS_URL, timeout=10)
                # 发送启动包（把当前参数一起传给后端）
                start = {
                    "type": "start",
                    "url": video_url,
                    "fps": int(self.fps_var.get()),
                    "conf_water": float(self.conf_water_var.get()),
                    "conf_risk": float(self.conf_risk_var.get()),
                    "send_mask_every": int(self.send_mask_var.get())
                }
                try:
                    self.ws.send(json.dumps(start))
                except Exception as e:
                    print("WS send start error:", e)

                # 更新状态栏
                self.root.after(0, lambda: self.status_label.config(text="状态：WS 已连接，等待数据..."))

                while self.ws_running:
                    try:
                        msg = self.ws.recv()
                    except WebSocketConnectionClosedException:
                        break
                    if not msg:
                        break
                    try:
                        data = json.loads(msg)
                    except json.JSONDecodeError:
                        continue

                    # 处理消息：tick / ack / eof
                    if data.get("type") == "tick":
                        ts   = int(data.get("ts", 0))
                        pct  = float(data.get("pct", 0.0))
                        lvl  = int(data.get("level", 0))
                        water= data.get("water") or {}

                        polys = []
                        objs = water.get("objects") or []
                        for obj in objs:
                            poly = obj.get("poly")
                            if isinstance(poly, list) and len(poly) >= 3:
                                polys.append(poly)

                        with self.lock:
                            self.last_ts = ts
                            self.last_pct = pct
                            self.last_level = lvl
                            self.last_polys = polys
                            self.image_w = int(water.get("image_w") or 0)
                            self.image_h = int(water.get("image_h") or 0)

                        # 累计曲线
                        if self.t0 is None:
                            self.t0 = ts
                        tsec = max(0.0, (ts - self.t0) / 1000.0)
                        self.ts_list.append(tsec)
                        self.pct_list.append(pct)
                        self.level_list.append(lvl)

                        # 更新状态显示（主线程）
                        self.root.after(0, lambda: self.status_label.config(text=f"状态：收到 tick t={ts}ms pct={pct:.2f}% level={lvl}"))

                    elif data.get("type") == "ack":
                        updated = data.get("updated", [])
                        self.root.after(0, lambda: self.status_label.config(text=f"状态：参数已更新 {updated}"))

                    elif data.get("type") == "eof":
                        self.root.after(0, lambda: self.status_label.config(text="状态：视频流结束 (eof)"))
                        break

            except Exception as e:
                print("WS error:", e)
                self.root.after(0, lambda: self.status_label.config(text=f"状态：WS 错误 {e}"))
            finally:
                try:
                    if self.ws is not None:
                        self.ws.close()
                except Exception:
                    pass
                self.ws = None
                self.ws_running = False
                self.root.after(0, lambda: self.status_label.config(text="状态：WS 断开"))

        self.ws_thread = threading.Thread(target=run, daemon=True)
        self.ws_thread.start()

    def close_ws(self):
        # 主动发送 stop
        try:
            if self.ws is not None:
                try:
                    self.ws.send(json.dumps({"type": "stop"}))
                except Exception:
                    pass
                self.ws.close()
        except Exception:
            pass
        self.ws = None
        self.ws_running = False

    def schedule_send_params(self):
        # 防抖：若在 300ms 内多次改动，仅发送最后一次
        if self._param_debounce_id:
            self.root.after_cancel(self._param_debounce_id)
            self._param_debounce_id = None
        self._param_debounce_id = self.root.after(PARAM_DEBOUNCE_MS, self.send_set_params)

    def send_set_params(self):
        # 把当前参数打包成 set_params 并发送（如果 ws 存在）
        if not self.ws:
            return
        params = {
            "type": "set_params",
            "fps": int(self.fps_var.get()),
            "conf_water": float(self.conf_water_var.get()),
            "conf_risk": float(self.conf_risk_var.get()),
            "send_mask_every": int(self.send_mask_var.get())
        }
        try:
            self.ws.send(json.dumps(params))
        except Exception as e:
            print("send_set_params error:", e)

    # ========== 视频读取与叠加 ==========
    def read_frame_loop(self):
        if not self.playing or self.cap is None:
            return

        ok, frame = self.cap.read()
        if not ok:
            self.playing = False
            self.close_ws()
            self.status_label.config(text="状态：本地播放结束")
            return

        # 叠加多边形（来自后端）
        with self.lock:
            polys = [np.asarray(p, dtype=np.int32) for p in self.last_polys]
            ts = self.last_ts
            pct = self.last_pct
            lvl = self.last_level

        if polys:
            overlay = frame.copy()
            # 填充半透明掩膜
            cv2.fillPoly(overlay, polys, OVERLAY_COLOR)
            frame = cv2.addWeighted(overlay, OVERLAY_ALPHA, frame, 1.0 - OVERLAY_ALPHA, 0)
            # 再描边
            for pts in polys:
                cv2.polylines(frame, [pts], isClosed=True, color=(255, 80, 0), thickness=2)

        # HUD
        hud_text = f"t={ts}ms   pct={pct:.2f}%   level={lvl}"
        cv2.rectangle(frame, (10, 10), (480, 45), (0, 0, 0), thickness=-1)
        cv2.putText(frame, hud_text, (16, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        self.hud.config(text=hud_text)

        # 显示到 Tk
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        imtk = ImageTk.PhotoImage(image=im)
        self.video_label.configure(image=imtk)
        self.video_label.image = imtk  # 防止被垃圾回收

        # 下一帧
        self.root.after(self.frame_timer_ms, self.read_frame_loop)

    # ========== 实时画图更新 ==========
    def update_plot_timer(self):
        if self.ts_list:
            # 只保留最近 N 秒数据（防止无限增长）
            N_SEC = 120
            tmax = self.ts_list[-1]
            tmin = max(0.0, tmax - N_SEC)
            # 切片
            idx0 = 0
            for i, t in enumerate(self.ts_list):
                if t >= tmin:
                    idx0 = i
                    break
            xs = self.ts_list[idx0:]
            ys1 = self.pct_list[idx0:]
            ys2 = self.level_list[idx0:]

            self.line_pct.set_data(xs, ys1)
            self.line_level.set_data(xs, ys2)
            self.ax.set_xlim(max(0, tmin), max(5, tmax))
            # y 轴上限动态一点
            y1max = max(60, (max(ys1) if ys1 else 60) * 1.2)
            self.ax.set_ylim(0, max(5, y1max))
            self.canvas.draw_idle()

        self.root.after(200, self.update_plot_timer)


def main():
    root = tk.Tk()
    app = RealtimeClientApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.geometry("1200x700")
    root.mainloop()


if __name__ == "__main__":
    main()
