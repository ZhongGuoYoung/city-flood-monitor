# server/routes_ezviz.py
import os
import time
from typing import Optional
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/ezviz", tags=["ezviz"])

# 从环境变量读取 appKey / appSecret（推荐）
EZ_APP_KEY = "6fcd33dd976b453284b2134f546f9139"
EZ_APP_SECRET = "51bbbb0bcc8436d7439d724030af351d"

# 简单缓存 accessToken，避免每次都请求
_cached_token: Optional[str] = None
_cached_expire_ms: int = 0  # 毫秒时间戳

# 简单内存缓存
_cached_token: Optional[str] = None
_cached_expire_ms: int = 0  # 毫秒时间戳


async def _fetch_token_from_ezviz() -> None:
    """真正去萤石云拿 token，并更新缓存"""
    global _cached_token, _cached_expire_ms

    url = "https://open.ys7.com/api/lapp/token/get"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={"appKey": EZ_APP_KEY, "appSecret": EZ_APP_SECRET},
            timeout=10.0,
        )

    data = resp.json()
    # 萤石云正常 code 一般是 "200"
    if data.get("code") != "200":
        raise HTTPException(status_code=500, detail=f"获取 accessToken 失败：{data}")

    token = data["data"]["accessToken"]
    expire_time_ms = data["data"]["expireTime"]

    _cached_token = token
    _cached_expire_ms = expire_time_ms


async def _get_token_with_cache() -> str:
    """带缓存的获取 token"""
    now_ms = int(time.time() * 1000)

    # 缓存存在且没过期（提前 60 秒失效）
    if _cached_token and now_ms < _cached_expire_ms - 60_000:
        return _cached_token

    await _fetch_token_from_ezviz()
    return _cached_token


@router.get("/getAccessToken")
async def get_access_token_api():
    """
    给前端 IframePlayer 用的接口，对应 getAccessToken()

    返回结构专门做成：
    {
      "success": true/false,
      "accessToken": "....",
      "expireTime": 1234567890,
      "error": "错误信息（失败时）"
    }
    """
    try:
        token = await _get_token_with_cache()
        return {
            "success": True,
            "accessToken": token,
            "expireTime": _cached_expire_ms,
        }
    except HTTPException as e:
        # 透传 HTTPException
        raise e
    except Exception as e:
        return {
            "success": False,
            "error": f"获取 accessToken 异常：{str(e)}",
        }


@router.get("/health")
async def ezviz_health():
    """简单健康检查，可选"""
    now_ms = int(time.time() * 1000)
    return {
        "status": "ok",
        "now": now_ms,
        "hasToken": _cached_token is not None,
    }


# ============= HLS 接口==================
async def get_access_token() -> str:
    """获取（或复用）accessToken"""
    global _cached_token, _cached_expire_ms

    # if not EZ_APP_KEY or not EZ_APP_SECRET:
    #     raise HTTPException(
    #         status_code=500,
    #         detail="后端未配置 EZVIZ_APP_KEY / EZVIZ_APP_SECRET 环境变量"
    #     )

    now_ms = int(time.time() * 1000)

    # 如果缓存的 token 还没过期（提前 60s 失效）
    if _cached_token and now_ms < _cached_expire_ms - 60_000:
        return _cached_token

    # 请求 token 接口
    # 文档：/api/lapp/token/get
    url = "https://open.ys7.com/api/lapp/token/get"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={
                "appKey": EZ_APP_KEY,
                "appSecret": EZ_APP_SECRET,
            },
            timeout=10.0,
        )

    data = resp.json()
    if data.get("code") != "200":
        raise HTTPException(
            status_code=500,
            detail=f"获取 accessToken 失败：{data}"
        )

    token = data["data"]["accessToken"]
    expire_time_ms = data["data"]["expireTime"]  # 毫秒时间戳

    _cached_token = token
    _cached_expire_ms = expire_time_ms
    return token


@router.get("/hls-url")
async def get_hls_url(
        deviceSerial: str,
        channelNo: int = 1,
        expireSeconds: int = 3600,
):
    """
    前端调用：
    GET /api/ezviz/hls-url?deviceSerial=D37384593&channelNo=1

    返回：
    { "url": "https://open.ys7.com/v3/openlive/...m3u8?accessToken=..." }
    """
    if not deviceSerial:
        raise HTTPException(status_code=400, detail="deviceSerial 不能为空")

    token = await get_access_token()

    # 播放地址接口：v2/live/address/get
    # protocol:
    #   1 -> ezopen
    #   2 -> HLS
    #   3 -> RTMP/FLV 等（按官方文档为准）
    url = "https://open.ys7.com/api/lapp/v2/live/address/get"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={
                "accessToken": token,
                "deviceSerial": deviceSerial,
                "channelNo": channelNo,
                "protocol": 2,  # HLS
                "expireTime": expireSeconds,
            },
            timeout=10.0,
        )

    data = resp.json()
    if data.get("code") != "200":
        raise HTTPException(
            status_code=500,
            detail=f"获取 HLS 地址失败：{data}"
        )

    play_url = data["data"]["url"]
    return JSONResponse({"url": play_url})
