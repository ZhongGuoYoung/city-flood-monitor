# -*- coding: utf-8 -*-
"""
一体化 GUI：图片/本地视频/摄像头 实时推理（含旧权重自定义层垫片）
使用说明：
1) 修改 MODEL_PATH 为你的 best.pt
2) 运行：python yolo_gui_all_in_one.py
"""

import os, sys, time, threading, types, importlib
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
from PIL import Image, ImageTk



# ========= 兼容旧权重：动态注册 extra_modules.block / attention 垫片 =========
def _install_extra_modules_shims():
    """
    某些老权重会引用：
      - ultralytics.nn.extra_modules.block.Bottleneck_MLCA / C3k2_MLCA / ...
      - ultralytics.nn.extra_modules.attention.MLCA / SE / CBAM / ...
    这里在运行时注入同名模块与类，让反序列化能找到它们。
    注意：这是“占位/近似实现”，可保证能加载运行，但精度可能与原实现有差异。
    """
    # 如果已有就不重复装
    have_block = True
    try:
        import ultralytics.nn.extra_modules.block  # noqa: F401
    except Exception:
        have_block = False

    have_attn = True
    try:
        import ultralytics.nn.extra_modules.attention  # noqa: F401
    except Exception:
        have_attn = False

    if have_block and have_attn:
        return  # 全都有就不用装

    # 导入官方基础模块，作为“近似基类”
    mb = importlib.import_module("ultralytics.nn.modules.block")

    def _get(name, fallbacks=()):
        for n in (name, *fallbacks):
            if hasattr(mb, n):
                return getattr(mb, n)
        # 兜底一个恒等模块
        import torch.nn as nn
        class _Dummy(nn.Module):
            def __init__(self, *a, **k): super().__init__()
            def forward(self, x): return x
        _Dummy.__name__ = "Dummy"
        return _Dummy

    # ---------- block 子模块：把 *_MLCA 类映射到最近的官方基类 ----------
    if not have_block:
        block_mod = types.ModuleType("ultralytics.nn.extra_modules.block")

        _Bottleneck = _get("Bottleneck", ("C3",))
        _C3        = _get("C3", ())
        _C2f       = _get("C2f", ("C3",))
        _C3k2      = _get("C3k2", ("C3",))
        _SPPF      = _get("SPPF", ())
        _Conv      = _get("Conv", ())
        _DWConv    = _get("DWConv", ("Conv",))
        _RepC3     = _get("RepC3", ("C3",))
        _C3Ghost   = _get("C3Ghost", ("C3",))

        _MAP = {
            "Bottleneck_MLCA": _Bottleneck,
            "C3k2_MLCA":       _C3k2,
            "C3_MLCA":         _C3,
            "C2f_MLCA":        _C2f,
            "SPPF_MLCA":       _SPPF,
            "Conv_MLCA":       _Conv,
            "DWConv_MLCA":     _DWConv,
            "RepC3_MLCA":      _RepC3,
            "C3Ghost_MLCA":    _C3Ghost,
        }

        def _mk(name, base_cls):
            class _Shim(base_cls):
                """Compatibility shim '{}' -> {}""".format(name, base_cls.__name__)
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
            _Shim.__name__ = name
            return _Shim

        block_mod.__all__ = []
        for _name, _base in _MAP.items():
            setattr(block_mod, _name, _mk(_name, _base))
            block_mod.__all__.append(_name)

    # ---------- attention 子模块：注意力占位（恒等映射） ----------
    if not have_attn:
        import torch.nn as nn
        class _IdentityAttn(nn.Module):
            def __init__(self, *a, **k): super().__init__(); self.id = nn.Identity()
            def forward(self, x): return self.id(x)

        attention_mod = types.ModuleType("ultralytics.nn.extra_modules.attention")
        for name in ["MLCA", "SE", "CBAM", "ECA", "SK", "CA", "SCA", "PSA", "GAM"]:
            cls = type(name, (_IdentityAttn,), {})
            setattr(attention_mod, name, cls)
        attention_mod.__all__ = ["MLCA","SE","CBAM","ECA","SK","CA","SCA","PSA","GAM"]

    # ---------- 写入 sys.modules ----------
    pkg = sys.modules.get("ultralytics.nn.extra_modules")
    if pkg is None:
        pkg = types.ModuleType("ultralytics.nn.extra_modules")
        pkg.__path__ = []  # 标记为包
        sys.modules["ultralytics.nn.extra_modules"] = pkg

    if not have_block:
        sys.modules["ultralytics.nn.extra_modules.block"] = block_mod
        setattr(pkg, "block", block_mod)

    if not have_attn:
        sys.modules["ultralytics.nn.extra_modules.attention"] = attention_mod
        setattr(pkg, "attention", attention_mod)

# 安装垫片（若环境中不存在这些模块）
_install_extra_modules_shims()

# 现在再导入 YOLO（权重反序列化会用到上面的垫片）
from ultralytics import YOLO

# =================== 可调参数 ===================
MODEL_PATH = r"D:\ultralytics-main\weights\YOLOv8.pt"   # ← 改成你的 best.pt
DEVICE     = 0                                        # GPU=0；CPU="cpu"
IMGSZ      = 640
CONF       = 0.25
HALF       = True                                     # GPU 半精度；CPU 会忽略
INFER_EVERY = 1                                       # 每隔多少帧推理一次（1=每帧；调2/3更快）
SAVE_VIDEO_DEFAULT = True                             # 默认保存带框视频

# =================== 加载模型 ===================
def load_model_or_die():
    try:
        m = YOLO(MODEL_PATH)
        return m
    except Exception as e:
        messagebox.showerror("错误", f"模型加载失败：\n{e}")
        raise SystemExit

model = load_model_or_die()

# =================== GUI 结构 ===================
root = tk.Tk()
root.title("内涝识别 - 图片 / 本地视频 / 摄像头 一体化")
root.geometry("1000x780")

# 顶部工具条
top = tk.Frame(root); top.pack(fill="x", padx=10, pady=6)
btn_img   = tk.Button(top, text="选择图片",   width=12)
btn_video = tk.Button(top, text="打开本地视频", width=14)
btn_cam   = tk.Button(top, text="打开摄像头", width=12)
btn_stop  = tk.Button(top, text="停止",       width=8, state="disabled")
chk_var_save = tk.BooleanVar(value=SAVE_VIDEO_DEFAULT)
chk_save  = tk.Checkbutton(top, text="保存带框视频", variable=chk_var_save)

for w in (btn_img, btn_video, btn_cam, btn_stop, chk_save):
    w.pack(side="left", padx=6)

# 画面区
image_label = tk.Label(root, bg="#222222")
image_label.pack(padx=10, pady=10, fill="both", expand=True)

# 信息区
info_label = tk.Label(root, text="", justify="left", anchor="w",
                      font=("Microsoft YaHei", 10))
info_label.pack(padx=10, pady=6, fill="x")

img_tk = None
cap = None
writer = None
run_flag = False
frame_idx = 0
src_desc = ""

# =================== 工具函数 ===================
def show_bgr(bgr):
    """把 BGR 帧显示到 Tk 标签（自适应缩放）"""
    global img_tk
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    max_w, max_h = 960, 620
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)))
    img = Image.fromarray(rgb)
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)

def set_info(text: str):
    info_label.config(text=text)

def predict_image(path: str):
    """对单张图片推理并显示/保存"""
    try:
        res = model.predict(source=path, imgsz=IMGSZ, conf=CONF,
                            device=DEVICE, half=(HALF and DEVICE!="cpu"),
                            verbose=False)[0]
        annotated = res.plot()
        # 保存
        save_dir = os.path.join(os.path.dirname(path), "pred")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"pred_{os.path.basename(path)}")
        cv2.imwrite(save_path, annotated)

        # 信息
        names = res.names
        counts = {}
        for b in res.boxes:
            cls_id = int(b.cls[0]); name = names.get(cls_id, str(cls_id))
            counts[name] = counts.get(name, 0) + 1
        lines = [
            f"来源: {path}",
            f"已保存: {save_path}",
            "各类别计数: " + (", ".join([f"{k}:{v}" for k,v in counts.items()]) if counts else "无"),
        ]
        set_info("\n".join(lines))
        show_bgr(annotated)
    except Exception as e:
        messagebox.showerror("错误", f"预测失败：\n{e}")

# =================== 视频线程 ===================
def video_loop():
    """读取视频 → 推理 → 显示/保存（后台线程）"""
    global frame_idx, cap, writer, run_flag
    frame_idx = 0
    t_last = time.time()
    while run_flag and cap and cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        annotated = frame

        # 每 INFER_EVERY 帧推理一次
        if frame_idx % INFER_EVERY == 0:
            try:
                res = model.predict(source=frame, imgsz=IMGSZ, conf=CONF,
                                    device=DEVICE, half=(HALF and DEVICE!="cpu"),
                                    verbose=False)[0]
                annotated = res.plot()
                # 文本信息
                names = res.names
                counts = {}
                for b in res.boxes:
                    cls_id = int(b.cls[0]); name = names.get(cls_id, str(cls_id))
                    counts[name] = counts.get(name, 0) + 1
                lines = [
                    f"来源: {src_desc}",
                    f"帧: {frame_idx}",
                    "各类别计数: " + (", ".join([f"{k}:{v}" for k,v in counts.items()]) if counts else "无"),
                ]
                root.after(0, set_info, "\n".join(lines))
            except Exception as e:
                root.after(0, set_info, f"推理异常: {e}")

        # 保存（原尺寸）
        if writer is not None:
            writer.write(annotated)

        # 显示
        root.after(0, show_bgr, annotated)

        # 轻微节流
        now = time.time()
        if now - t_last < 0.001:
            time.sleep(0.001)
        t_last = now

    # 清理
    if cap:
        cap.release()
    if writer:
        writer.release()
    writer = None
    run_flag = False
    root.after(0, btn_stop.config, {"state": "disabled"})
    root.after(0, set_info, f"{src_desc} 已结束。")

def start_from_source(source: str):
    """打开视频源并启动后台线程（source: 文件路径 或 '0' 为摄像头）"""
    global cap, writer, run_flag, src_desc
    if run_flag:
        return
    # 打开
    cap_src = 0 if source == "0" else source
    if isinstance(source, str) and source != "0" and not os.path.exists(source):
        messagebox.showerror("错误", f"找不到视频文件：\n{source}")
        return
    cap_ = cv2.VideoCapture(cap_src)
    if not cap_.isOpened():
        messagebox.showerror("错误", "无法打开视频源")
        return

    # 保存设置
    out_writer = None
    if chk_var_save.get():
        if source == "0":
            out_dir = os.path.join(os.getcwd(), "pred")
            base = "camera.mp4"
        else:
            out_dir = os.path.join(os.path.dirname(source), "pred")
            base = os.path.splitext(f"pred_{os.path.basename(source)}")[0] + ".mp4"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, base)

        fps = cap_.get(cv2.CAP_PROP_FPS) or 25
        w = int(cap_.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap_.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        set_info(f"保存到：{out_path}")

    # 切换状态并开线程
    src_desc = "摄像头(0)" if source == "0" else source
    cap = cap_
    writer = out_writer
    run_flag = True
    btn_stop.config(state="normal")
    threading.Thread(target=video_loop, daemon=True).start()

# =================== 事件绑定 ===================
def on_open_image():
    p = filedialog.askopenfilename(
        title="选择图片",
        filetypes=[("Image", "*.jpg;*.jpeg;*.png;*.bmp;*.webp")]
    )
    if p:
        predict_image(p)

def on_open_video():
    p = filedialog.askopenfilename(
        title="选择本地视频",
        filetypes=[("Video", "*.mp4;*.avi;*.mov;*.mkv;*.flv;*.wmv")]
    )
    if p:
        start_from_source(p)

def on_open_cam():
    start_from_source("0")

def on_stop():
    global run_flag
    run_flag = False

def on_close():
    on_stop()
    root.after(100, root.destroy)

btn_img.config(command=on_open_image)
btn_video.config(command=on_open_video)
btn_cam.config(command=on_open_cam)
btn_stop.config(command=on_stop)
root.protocol("WM_DELETE_WINDOW", on_close)

# =================== 启动 ===================
root.mainloop()
