<template>
  <div class="cameras-grid">
    <div 
      v-for="camera in cameras" 
      :key="camera.id"
      class="camera-card"
      @click="selectCamera(camera)"
    >
      <div class="camera-card-header">
        <div class="camera-card-title">
          <i class="fas fa-video"></i>
          <span>{{ camera.name }}</span>
          <span v-if="camera.ezvizDevice" class="ezviz-badge">
            <i class="fas fa-cloud"></i>
          </span>
        </div>
        <div class="camera-card-status">
          <span class="status-indicator" :class="getStatusClass(camera)"></span>
          {{ camera.status }}
        </div>
      </div>
      
      <div class="camera-card-content">
        <!-- 萤石云实时视频流 -->
        <div v-if="camera.ezvizDevice && showEzvizStreams" class="ezviz-stream-container">
          <EzvizPlayer
            :deviceSerial="camera.ezvizDevice.deviceSerial"
            :cameraNo="camera.ezvizDevice.cameraNo || 1"
            :width="'100%'"
            :height="'100%'"
            :autoplay="false" 
            :controls="false" 
            @play="onVideoPlay(camera.id)"
            @error="onVideoError(camera.id)"
            class="ezviz-mini-player"
          />
          <div class="stream-overlay">
            <button 
              class="play-btn"
              @click.stop="toggleStreamPlay(camera.id)"
              :title="isStreamPlaying(camera.id) ? '暂停' : '播放'"
            >
              <i class="fas" :class="isStreamPlaying(camera.id) ? 'fa-pause' : 'fa-play'"></i>
            </button>
          </div>
        </div>
        
        <!-- 静态图片显示 -->
        <div v-else class="camera-image-container">
          <img 
            v-if="camera.imageUrl"
            :src="camera.imageUrl" 
            :alt="camera.name"
            class="camera-image"
            @error="handleImageError"
          />
          <div v-else class="video-placeholder">
            <i class="fas fa-video"></i>
            <p>实时监控画面</p>
          </div>
          
          <!-- 洪涝标识 -->
          <div v-if="camera.floodLevel" class="flood-indicator" :class="getFloodClass(camera)">
            <i class="fas fa-exclamation-triangle"></i>
            {{ getFloodText(camera) }}
          </div>
          
          <!-- 摄像头水印 -->
          <div class="video-watermark">监控ID: {{ camera.id }}</div>
          
          <!-- 在线状态指示器 -->
          <div class="live-indicator" :class="getStatusClass(camera)">
            <i class="fas fa-circle"></i>
            <span>实时</span>
          </div>
        </div>
      </div>
      
      <div class="camera-card-footer">
        <div class="camera-location">{{ camera.location }}</div>
        <div class="camera-time">{{ currentTime }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import EzvizPlayer from '@/components/EzvizPlayer.vue'

export default {
  name: 'CameraGrid',
  components: {
    EzvizPlayer
  },
  props: {
    cameras: Array
  },
  data() {
    return {
      currentTime: '',
      showEzvizStreams: true, // 控制是否显示视频流
      playingStreams: new Set() // 记录正在播放的视频流
    }
  },
  methods: {
    selectCamera(camera) {
      this.$emit('select-camera', camera)
    },
    getStatusClass(camera) {
      if (camera.status === '在线') return 'status-online'
      if (camera.status === '离线') return 'status-offline'
      if (camera.status === '维护中') return 'status-maintenance'
      return ''
    },
    getFloodClass(camera) {
      if (!camera.floodLevel) return ''
      return `flood-${camera.floodLevel} ${camera.floodLevel === 'critical' ? 'animated' : ''}`
    },
    getFloodText(camera) {
      if (!camera.floodLevel) return ''
      const texts = {
        'low': '轻度内涝',
        'medium': '中度内涝',
        'high': '严重内涝',
        'critical': '紧急内涝'
      }
      return texts[camera.floodLevel] || ''
    },
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString()
    },
    handleImageError(event) {
      console.warn(`图片加载失败: ${event.target.src}`)
    },
    
    // 视频流控制方法
    toggleStreamPlay(cameraId) {
      if (this.playingStreams.has(cameraId)) {
        this.playingStreams.delete(cameraId)
        // 这里应该暂停视频流播放，但EzvizPlayer组件需要暴露暂停方法
        // 暂时通过重新加载播放器来实现
      } else {
        // 停止其他正在播放的视频流
        this.playingStreams.clear()
        this.playingStreams.add(cameraId)
      }
    },
    
    isStreamPlaying(cameraId) {
      return this.playingStreams.has(cameraId)
    },
    
    onVideoPlay(cameraId) {
      this.playingStreams.add(cameraId)
    },
    
    onVideoError(cameraId) {
      this.playingStreams.delete(cameraId)
      console.error(`摄像头 ${cameraId} 视频流播放失败`)
    },
    
    // 停止所有视频流
    stopAllStreams() {
      this.playingStreams.clear()
    }
  },
  mounted() {
    this.updateTime()
    setInterval(this.updateTime, 1000)
  },
  
  beforeUnmount() {
    this.stopAllStreams()
  }
}
</script>

<style scoped>
.cameras-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  overflow-y: auto;
  padding: 5px;
  margin-top: 20px;
}

.camera-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
  height: 280px;
}

.camera-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.camera-card-header {
  padding: 12px 15px;
  background: linear-gradient(to right, #1e3c72, #2a5298);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.camera-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.ezviz-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  font-size: 0.6rem;
}

.camera-card-status {
  font-size: 0.8rem;
  opacity: 0.9;
}

.camera-card-content {
  flex: 1;
  position: relative;
  background-color: #000;
}

/* 萤石云视频流容器 */
.ezviz-stream-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.ezviz-mini-player {
  width: 100%;
  height: 100%;
}

.stream-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to bottom,
    transparent 70%,
    rgba(0, 0, 0, 0.3) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.ezviz-stream-container:hover .stream-overlay {
  opacity: 1;
}

.play-btn {
  width: 40px;
  height: 40px;
  background-color: rgba(30, 60, 114, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, transform 0.2s;
}

.play-btn:hover {
  background-color: rgba(42, 82, 152, 0.9);
  transform: scale(1.1);
}

/* 静态图片样式 */
.camera-image-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.camera-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.camera-card:hover .camera-image {
  transform: scale(1.05);
}

.video-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, #1a1a1a, #2d2d2d);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #aaa;
}

.video-placeholder i {
  font-size: 3rem;
  margin-bottom: 15px;
  color: #4fc3f7;
}

.video-watermark {
  position: absolute;
  bottom: 10px;
  right: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.7rem;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 2px 6px;
  border-radius: 3px;
}

.flood-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
}

.live-indicator {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
}

.live-indicator.status-online {
  color: #4caf50;
}

.live-indicator.status-offline {
  color: #f44336;
}

.live-indicator.status-maintenance {
  color: #ff9800;
}

.live-indicator i {
  font-size: 0.6rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.camera-card-footer {
  padding: 12px 15px;
  background-color: #f9f9f9;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.camera-location {
  font-size: 0.85rem;
  color: #666;
}

.camera-time {
  font-size: 0.8rem;
  color: #888;
}

@media (max-width: 1200px) {
  .cameras-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 992px) {
  .cameras-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .cameras-grid {
    grid-template-columns: 1fr;
  }
  
  .stream-overlay {
    opacity: 1; /* 在移动设备上始终显示控制按钮 */
  }
}
</style>