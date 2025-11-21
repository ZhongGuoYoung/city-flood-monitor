import axios from 'axios'

class EzvizService {
  constructor() {
    this.accessToken = null
    this.tokenExpireTime = null
    this.appKey = process.env.VUE_APP_EZVIZ_APP_KEY // 从环境变量获取
    this.appSecret = process.env.VUE_APP_EZVIZ_APP_SECRET // 从环境变量获取
    this.apiBase = 'https://open.ys7.com/api/lapp'
  }

  // 获取访问令牌
  async getAccessToken() {
    // 检查token是否还有效（提前5分钟刷新）
    if (this.accessToken && this.tokenExpireTime && 
        Date.now() < this.tokenExpireTime - 5 * 60 * 1000) {
      return this.accessToken
    }

    try {
      const response = await axios.post(`${this.apiBase}/token/get`, {
        appKey: this.appKey,
        appSecret: this.appSecret
      })

      if (response.data.code === '200') {
        this.accessToken = response.data.data.accessToken
        // 设置token过期时间（萤石云token有效期为7天）
        this.tokenExpireTime = Date.now() + 7 * 24 * 60 * 60 * 1000
        return this.accessToken
      } else {
        throw new Error(`获取token失败: ${response.data.msg}`)
      }
    } catch (error) {
      console.error('获取萤石云访问令牌失败:', error)
      throw error
    }
  }

  // 获取设备列表
  async getDeviceList(pageStart = 0, pageSize = 50) {
    try {
      const token = await this.getAccessToken()
      const response = await axios.post(`${this.apiBase}/device/list`, {
        accessToken: token,
        pageStart,
        pageSize
      })

      if (response.data.code === '200') {
        return response.data.data
      } else {
        throw new Error(`获取设备列表失败: ${response.data.msg}`)
      }
    } catch (error) {
      console.error('获取设备列表失败:', error)
      throw error
    }
  }

  // 获取摄像头列表
  async getCameraList(deviceSerial) {
    try {
      const token = await this.getAccessToken()
      const response = await axios.post(`${this.apiBase}/device/camera/list`, {
        accessToken: token,
        deviceSerial
      })

      if (response.data.code === '200') {
        return response.data.data
      } else {
        throw new Error(`获取摄像头列表失败: ${response.data.msg}`)
      }
    } catch (error) {
      console.error('获取摄像头列表失败:', error)
      throw error
    }
  }

  // 获取设备信息
  async getDeviceInfo(deviceSerial) {
    try {
      const token = await this.getAccessToken()
      const response = await axios.post(`${this.apiBase}/device/info`, {
        accessToken: token,
        deviceSerial
      })

      if (response.data.code === '200') {
        return response.data.data
      } else {
        throw new Error(`获取设备信息失败: ${response.data.msg}`)
      }
    } catch (error) {
      console.error('获取设备信息失败:', error)
      throw error
    }
  }
}

export const ezvizService = new EzvizService()