<template>
  <div 
    class="iframe-player-container" 
    :class="{ 
      'compact-mode': compactMode,
      'show-controls': showControls 
    }"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
    @mousemove="onMouseMove"
  >
    <!-- 控制栏 - 悬停时显示 -->
    <div class="player-controls" v-if="!compactMode">
      <div class="control-left">
        <span class="camera-name">{{ cameraData.name }}</span>
        <span class="status-indicator" :class="playerStatus"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="control-right">
        <button class="control-btn" @click="refreshPlayer" :disabled="loading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
        <button class="control-btn" @click="toggleFullscreen">
          <i class="fas fa-expand"></i>
          全屏
        </button>
        <button class="control-btn" @click="toggleAudio">
          <i class="fas" :class="audioEnabled ? 'fa-volume-up' : 'fa-volume-mute'"></i>
          {{ audioEnabled ? '静音' : '开启声音' }}
        </button>
      </div>
    </div>

    <!-- 播放器主体 -->
    <div class="player-main-area" :class="{ 'compact-main': compactMode }">
      <div class="video-container-16-9" :class="{ 'compact-video': compactMode }">
        <div class="iframe-wrapper">
          <iframe
            :key="iframeKey"
            :src="iframeUrl"
            class="video-iframe"
            frameborder="0"
            allowfullscreen
            @load="onIframeLoad"
            @error="onIframeError"
            ref="videoIframe"
            :style="iframeStyle"
          ></iframe>
        </div>
        
        <!-- 加载状态覆盖层 -->
        <div v-if="loading" class="loading-overlay">
          <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
          </div>
          <p>重新加载视频流...</p>
        </div>
        
        <!-- 错误状态覆盖层 -->
        <div v-if="error && !loading" class="error-overlay">
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <h3>视频加载失败</h3>
          <p>{{ errorMessage }}</p>
          <button class="retry-btn" @click="refreshPlayer">
            <i class="fas fa-redo"></i>
            重新尝试
          </button>
        </div>

        <!-- 悬停提示 -->
        <div v-if="!compactMode && !showControls && iframeLoaded" class="hover-hint">
          <i class="fas fa-hand-pointer"></i>
          <span>悬停显示控制栏</span>
        </div>
      </div>
    </div>

    <!-- 信息栏 - 悬停时显示 -->
    <div class="player-info" v-if="!compactMode && showControls">
      <div class="info-item">
        <i class="fas fa-video"></i>
        <span>设备序列号: {{ cameraData.deviceSerial || '未配置' }}</span>
      </div>
      <div class="info-item">
        <i class="fas fa-clock"></i>
        <span>最后更新: {{ lastUpdateTime }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { getAccessToken } from '../services/api';

export default {
  name: 'IframePlayer',
  props: {
    cameraData: {
      type: Object,
      required: true
    },
    lastUpdateTime: {
      type: String,
      default: ''
    },
    compactMode: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      error: false,
      errorMessage: '',
      accessToken: null,
      audioEnabled: false,
      iframeLoaded: false,
      iframeKey: 0,
      refreshCount: 0,
      showControls: false,
      mouseMoveTimer: null,
      controlsTimeout: null
    }
  },
  computed: {
    playerStatus() {
      if (this.loading) return 'loading'
      if (this.error) return 'error'
      if (this.iframeLoaded) return 'playing'
      return 'idle'
    },
    statusText() {
      switch (this.playerStatus) {
        case 'loading': return '连接中...'
        case 'error': return '连接失败'
        case 'playing': return '直播中'
        default: return '待播放'
      }
    },
    iframeUrl() {
      if (!this.cameraData.deviceSerial || !this.accessToken) {
        return ''
      }
      
      const baseUrl = 'https://open.ys7.com/ezopen/h5/iframe'
      const params = {
        url: `ezopen://open.ys7.com/${this.cameraData.deviceSerial}/1.live`,
        accessToken: this.accessToken,
        autoplay: 1,
        audio: this.audioEnabled ? 1 : 0,
        template: 'simple',
        t: Date.now()
      }
      
      if (this.compactMode) {
        params.audio = 0;
      }
      
      const queryString = Object.keys(params)
        .map(key => `${key}=${encodeURIComponent(params[key])}`)
        .join('&')
      
      return `${baseUrl}?${queryString}`
    },
    iframeStyle() {
      return {
        opacity: this.iframeLoaded && !this.loading ? 1 : 0,
        transition: 'opacity 0.3s ease-in-out'
      }
    }
  },
  methods: {
    // 鼠标进入事件
    onMouseEnter() {
      if (this.compactMode) return;
      this.showControlsImmediately();
    },

    // 鼠标离开事件
    onMouseLeave() {
      if (this.compactMode) return;
      this.hideControlsWithDelay();
    },

    // 鼠标移动事件
    onMouseMove() {
      if (this.compactMode) return;
      
      // 防抖处理，避免频繁触发
      if (this.mouseMoveTimer) {
        clearTimeout(this.mouseMoveTimer);
      }
      
      this.mouseMoveTimer = setTimeout(() => {
        this.showControlsImmediately();
        this.hideControlsWithDelay();
      }, 100);
    },

    // 立即显示控制栏
    showControlsImmediately() {
      if (this.controlsTimeout) {
        clearTimeout(this.controlsTimeout);
      }
      this.showControls = true;
    },

    // 延迟隐藏控制栏
    hideControlsWithDelay() {
      if (this.controlsTimeout) {
        clearTimeout(this.controlsTimeout);
      }
      this.controlsTimeout = setTimeout(() => {
        this.showControls = false;
      }, 2000); // 2秒后隐藏
    },

    // 获取AccessToken
    async fetchAccessToken() {
      try {
        this.loading = true
        this.error = false
        const response = await getAccessToken();
        
        if (response.success) {
          this.accessToken = response.accessToken;
          console.log('成功获取AccessToken');
          return true;
        } else {
          throw new Error(response.error || '获取AccessToken失败');
        }
      } catch (error) {
        console.error('获取AccessToken失败:', error);
        this.showError(`获取访问令牌失败: ${error.message}`);
        return false;
      }
    },

    // 初始化播放器
    async initPlayer() {
      if (!this.cameraData.deviceSerial) {
        this.showError('该摄像头未配置设备序列号');
        return;
      }

      this.error = false;
      this.errorMessage = '';

      try {
        const tokenSuccess = await this.fetchAccessToken();
        if (!tokenSuccess) {
          return;
        }
        
        this.iframeKey++;
        this.iframeLoaded = false;
        
      } catch (err) {
        console.error('播放器初始化失败:', err);
        this.showError(`播放器初始化失败: ${err.message}`);
      }
    },

    // 处理iframe加载完成
    onIframeLoad() {
      console.log('iframe加载成功');
      this.iframeLoaded = true;
      this.error = false;
      this.loading = false;
      this.$emit('loaded');
    },

    // 处理iframe加载错误
    onIframeError(error) {
      console.error('iframe加载失败', error);
      this.showError('视频加载失败，请检查网络连接或设备状态');
      this.$emit('error', error);
    },

    // 显示错误
    showError(message) {
      this.error = true;
      this.errorMessage = message;
      this.loading = false;
      this.iframeLoaded = false;
    },

    // 刷新播放器
    async refreshPlayer() {
      if (this.loading) return;
      
      console.log('开始刷新播放器...');
      this.refreshCount++;
      
      this.iframeLoaded = false;
      this.error = false;
      
      try {
        await this.fetchAccessToken();
        this.iframeKey++;
        
        setTimeout(() => {
          if (!this.iframeLoaded && !this.error) {
            this.showError('视频流加载超时，请检查网络连接');
          }
        }, 10000);
        
      } catch (error) {
        console.error('刷新播放器失败:', error);
        this.showError(`刷新失败: ${error.message}`);
      }
    },

    // 切换全屏
    toggleFullscreen() {
      const playerContainer = this.$el.querySelector('.player-main-area');
      if (!document.fullscreenElement) {
        playerContainer.requestFullscreen?.().catch(err => {
          console.log('全屏请求失败:', err);
        });
      } else {
        document.exitFullscreen?.();
      }
    },

    // 切换音频
    toggleAudio() {
      this.audioEnabled = !this.audioEnabled;
      if (this.iframeLoaded) {
        this.refreshPlayer();
      }
    }
  },
  mounted() {
    this.initPlayer();
  },
  beforeUnmount() {
    // 清理定时器
    if (this.mouseMoveTimer) {
      clearTimeout(this.mouseMoveTimer);
    }
    if (this.controlsTimeout) {
      clearTimeout(this.controlsTimeout);
    }
  },
  watch: {
    'cameraData.deviceSerial': {
      handler() {
        this.initPlayer();
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.iframe-player-container {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  transition: all 0.3s ease;
}

/* 紧凑模式样式 */
.iframe-player-container.compact-mode {
  box-shadow: none;
  border-radius: 0;
  background: transparent;
}

/* 控制栏样式 - 默认隐藏，悬停时显示 */
.player-controls {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  flex-shrink: 0;
  z-index: 20;
  transform: translateY(-100%);
  opacity: 0;
  transition: all 0.3s ease;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

/* 显示控制栏时的样式 */
.iframe-player-container.show-controls .player-controls {
  transform: translateY(0);
  opacity: 1;
}

.control-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.camera-name {
  font-weight: 600;
  font-size: 1.1rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-indicator.loading {
  background-color: #ff9800;
  animation: pulse 1.5s infinite;
}

.status-indicator.error {
  background-color: #f44336;
  animation: pulse 1s infinite;
}

.status-indicator.playing {
  background-color: #4caf50;
}

.status-indicator.idle {
  background-color: #9e9e9e;
}

.control-right {
  display: flex;
  gap: 8px;
}

.control-btn {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 5px;
}

.control-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 播放器主体区域 */
.player-main-area {
  flex: 1;
  position: relative;
  background: #000;
  min-height: 400px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.player-main-area.compact-main {
  min-height: 200px;
  background: transparent;
}

/* 16:9 固定比例容器 */
.video-container-16-9 {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 比例 */
  background: #000;
}

.video-container-16-9.compact-video {
  background: transparent;
}

.iframe-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
}

.video-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: #000;
  z-index: 1;
}

/* 悬停提示 */
.hover-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  z-index: 5;
  transition: opacity 0.3s ease;
}

.iframe-player-container.show-controls .hover-hint {
  opacity: 0;
}

/* 加载和错误覆盖层 */
.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  z-index: 2;
}

.loading-spinner {
  margin-bottom: 15px;
}

.loading-spinner i {
  font-size: 2rem;
  color: #4fc3f7;
}

.error-icon {
  margin-bottom: 15px;
}

.error-icon i {
  font-size: 2rem;
  color: #f44336;
}

.error-overlay h3 {
  margin-bottom: 10px;
  color: #f44336;
}

.error-overlay p {
  margin-bottom: 20px;
  text-align: center;
  max-width: 80%;
}

.retry-btn {
  padding: 10px 20px;
  background: #1e3c72;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.3s;
}

.retry-btn:hover {
  background: #2a5298;
}

/* 信息栏样式 - 默认隐藏，悬停时显示 */
.player-info {
  background: #1a1a1a;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #ccc;
  font-size: 0.85rem;
  flex-shrink: 0;
  z-index: 20;
  transform: translateY(100%);
  opacity: 0;
  transition: all 0.3s ease;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}

/* 显示信息栏时的样式 */
.iframe-player-container.show-controls .player-info {
  transform: translateY(0);
  opacity: 1;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .player-controls {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .control-left,
  .control-right {
    justify-content: center;
  }
  
  .player-info {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  /* 在移动设备上始终显示控制栏和信息栏 */
  .player-controls,
  .player-info {
    transform: translateY(0);
    opacity: 1;
    position: relative;
  }
  
  .hover-hint {
    display: none;
  }
}

/* 全屏模式优化 */
:fullscreen .iframe-player-container {
  border-radius: 0;
}

:fullscreen .player-main-area {
  min-height: 100vh;
}

:fullscreen .video-container-16-9 {
  height: 100vh;
  padding-bottom: 0;
}

/* 全屏时控制栏和信息栏优化 */
:fullscreen .player-controls {
  position: fixed;
  top: 0;
}

:fullscreen .player-info {
  position: fixed;
  bottom: 0;
}
</style>