# server/app.py，，，挂载启动逻辑 + 引入 router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .startup import init_model_on_startup
from .routes_infer import router as infer_router
from .routes_ws import router as ws_router
from .routes_cameras import router as cameras_router
from .routes_export import router as export_router
from .routes_ezviz import router as ezviz_router
from pathlib import Path
from .routes_history import router as history_router
import mimetypes
import uvicorn

app = FastAPI(title="Ultralytics FastAPI", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent

RECORD_DIR = Path(__file__).resolve().parent / "records"

app.mount(
    "/records",
    StaticFiles(directory=RECORD_DIR, html=False),
    name="records"
)


@app.middleware("http")
async def disable_cache(request: Request, call_next):
    response = await call_next(request)
    # 禁用缓存，防止返回304
    response.headers["Cache-Control"] = "no-store"
    return response


# 修复 MIME 类型，确保返回视频头
mimetypes.add_type("video/mp4", ".mp4")

# CORS：开发阶段允许前端跨域访问（或改用 Vite 反向代理）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 以后可以改成你的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    # 启动即加载模型，避免首请求卡顿
    init_model_on_startup()


# 挂载REST推理接口
app.include_router(infer_router)

# 挂载WebSocket实时接口
app.include_router(ws_router)

# 挂载监控摄像头信息接口
app.include_router(cameras_router)

# 挂载导出
app.include_router(export_router)

# 挂载萤石
app.include_router(ezviz_router)

# 挂载历史视频查看
app.include_router(history_router)

# if __name__ == "__main__":
#     uvicorn.run(
#         "server.app:app",   # 模块名:app实例
#         host="0.0.0.0",
#         port=9000,
#         reload=True
#     )