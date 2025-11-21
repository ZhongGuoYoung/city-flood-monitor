<template>
  <div class="ezviz-device-manager">
    <div class="manager-header">
      <h3><i class="fas fa-video"></i> 萤石云设备管理</h3>
      <button @click="refreshDevices" class="refresh-btn" :disabled="loading">
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        刷新设备
      </button>
    </div>
    
    <div class="device-list">
      <div 
        v-for="device in devices" 
        :key="device.deviceSerial"
        class="device-item"
        :class="{ 'active': selectedDevice === device.deviceSerial }"
        @click="selectDevice(device)"
      >
        <div class="device-icon">
          <i class="fas fa-camera"></i>
        </div>
        <div class="device-info">
          <div class="device-name">{{ device.deviceName }}</div>
          <div class="device-status">
            <span class="status-indicator" :class="getStatusClass(device)"></span>
            {{ getStatusText(device) }}
          </div>
          <div class="device-serial">{{ device.deviceSerial }}</div>
        </div>
      </div>
      
      <div v-if="devices.length === 0 && !loading" class="no-devices">
        <i class="fas fa-camera-slash"></i>
        <p>未找到萤石云设备</p>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>正在加载设备列表...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="refreshDevices" class="retry-btn">
        <i class="fas fa-redo"></i>
        重试
      </button>
    </div>
  </div>
</template>

<script>
import { ezvizService } from '@/services/ezvizService'

export default {
  name: 'EzvizDeviceManager',
  emits: ['device-selected'],
  data() {
    return {
      devices: [],
      loading: false,
      error: null,
      selectedDevice: null
    }
  },
  methods: {
    // 加载设备列表
    async loadDevices() {
      this.loading = true
      this.error = null
      
      try {
        const deviceData = await ezvizService.getDeviceList()
        this.devices = deviceData || []
      } catch (error) {
        console.error('加载设备列表失败:', error)
        this.error = '加载设备列表失败: ' + error.message
      } finally {
        this.loading = false
      }
    },
    
    // 刷新设备列表
    refreshDevices() {
      this.loadDevices()
    },
    
    // 选择设备
    selectDevice(device) {
      this.selectedDevice = device.deviceSerial
      this.$emit('device-selected', device)
    },
    
    // 获取设备状态类
    getStatusClass(device) {
      if (device.status === 1) {
        return 'status-online'
      } else if (device.status === 2) {
        return 'status-offline'
      } else {
        return 'status-unknown'
      }
    },
    
    // 获取设备状态文本
    getStatusText(device) {
      if (device.status === 1) {
        return '在线'
      } else if (device.status === 2) {
        return '离线'
      } else {
        return '未知'
      }
    }
  },
  
  mounted() {
    this.loadDevices()
  }
}
</script>

<style scoped>
.ezviz-device-manager {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.manager-header {
  padding: 15px 20px;
  background: linear-gradient(to right, #1e3c72, #2a5298);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.manager-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.refresh-btn {
  padding: 6px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8rem;
}

.refresh-btn:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.3);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.device-list {
  max-height: 400px;
  overflow-y: auto;
}

.device-item {
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: background-color 0.2s;
}

.device-item:hover {
  background-color: #f5f7fa;
}

.device-item.active {
  background-color: #e3f2fd;
  border-left: 4px solid #1e3c72;
}

.device-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #1e3c72, #2a5298);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.device-info {
  flex: 1;
}

.device-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.device-status {
  font-size: 0.8rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.device-serial {
  font-size: 0.7rem;
  color: #999;
}

.status-indicator {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-online {
  background-color: #4caf50;
}

.status-offline {
  background-color: #f44336;
}

.status-unknown {
  background-color: #ff9800;
}

.no-devices,
.loading-state,
.error-state {
  padding: 40px 20px;
  text-align: center;
  color: #666;
}

.no-devices i,
.loading-state i,
.error-state i {
  font-size: 2rem;
  margin-bottom: 10px;
  display: block;
}

.error-state {
  color: #f44336;
}

.retry-btn {
  padding: 8px 16px;
  background-color: #1e3c72;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
}

.retry-btn:hover {
  background-color: #2a5298;
}
</style>