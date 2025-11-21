import json, time
import matplotlib.pyplot as plt
from websocket import create_connection

WS = "ws://localhost:9000/ws"                 # 如果是查询参数模式：  "ws://localhost:9000/ws?video_url=http://.../video&every_nth=5"
VIDEO_URL = "D:/city-flood-monitor/videos/video_2.mp4"   # 换成你的流或文件路径

ws = create_connection(WS)
ws.send(json.dumps({"type": "start", "url": VIDEO_URL, "fps": 2}))

# 数据缓存
timestamps = []
pct_list = []      # 淹没范围百分比
level_list = []    # 风险等级（0-5）

try:
    while True:
        msg = ws.recv()
        if not msg:
            print("⚠️ 收到空消息，可能结束")
            break
        try:
            data = json.loads(msg)
        except json.JSONDecodeError:
            print("⚠️ 无法解析的消息：", msg)
            continue

        if data.get("type") == "tick":
            ts = data.get("ts")
            pct = data.get("pct", 0)
            level = data.get("level", 0)

            timestamps.append(ts)
            pct_list.append(pct)
            level_list.append(level)
            print(f"t={ts}  pct={pct:.2f}%  level={level}")

        elif data.get("type") == "eof":
            print("✅ 视频结束")
            break
except KeyboardInterrupt:
    print("⏹️ 手动中断")
finally:
    ws.close()

# === 折线图绘制 ===
if timestamps:
    # 把时间戳转成相对秒
    t0 = timestamps[0]
    times = [(t - t0) / 1000.0 for t in timestamps]  # 毫秒→秒

    plt.figure(figsize=(10, 6))
    plt.title("积水识别实时结果")
    plt.xlabel("时间 (s)")
    plt.grid(True, linestyle="--", alpha=0.4)

    # 风险等级（0-5）
    plt.plot(times, level_list, "r-", label="风险等级 (level)", linewidth=2)
    # 淹没范围（百分比）
    plt.plot(times, pct_list, "b-", label="淹没范围 (%)", linewidth=2)

    plt.legend()
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ 没有采集到任何 tick 数据")
