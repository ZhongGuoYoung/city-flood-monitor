// src/services/api.js
import axios from 'axios'

// 这里 baseURL 改成你 FastAPI 的地址
const api = axios.create({
  baseURL: 'http://localhost:9000/api/ezviz',
  timeout: 10000
})

// IframePlayer 调用的 getAccessToken
export async function getAccessToken() {
  try {
    const res = await api.get('/getAccessToken')
    // 后端已经返回 { success, accessToken, expireTime, error }
    return res.data
  } catch (err) {
    console.error('getAccessToken 请求失败:', err)
    return {
      success: false,
      error: err.message || '网络错误'
    }
  }
}

// （可选）健康检查
export async function healthCheck() {
  try {
    const res = await api.get('/health')
    return res.data
  } catch (err) {
    return {
      status: 'error',
      error: err.message || '网络错误'
    }
  }
}
