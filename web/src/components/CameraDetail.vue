<template>
  <div class="camera-detail">
    <!-- 统一表头 -->
    <div class="detail-header">
      <div class="header-left">
        <i class="fas fa-camera"></i>
        <div class="header-title">
          <h2>{{ camera.name }}</h2>
          <p>{{ camera.location }}</p>
        </div>
      </div>
      <div class="header-right">
        <div class="header-status">
          <span class="status-badge" :class="getStatusClass(camera)">
            {{ camera.status }}
          </span>
          <span v-if="camera.floodLevel" class="flood-badge" :class="getFloodClass(camera)">
            {{ getFloodText(camera) }}
          </span>
        </div>
        <div class="header-time">{{ currentTime }}</div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="detail-content">
      <!-- 视频区域 -->
      <div class="video-section">
        <!-- 使用新的 IframePlayer 组件 -->
        <IframePlayer 
          :cameraData="camera"
          :lastUpdateTime="lastUpdateTime"
          class="video-player"
          @loaded="onPlayerLoaded"
          @error="onPlayerError"
        />
      </div>

      <!-- 信息面板 -->
      <div class="info-section">
        <!-- 分析结果 -->
        <div class="analysis-panel">
          <h3><i class="fas fa-chart-bar"></i> 实时分析数据</h3>
          <div class="analysis-grid">
            <div class="analysis-item water-depth" :class="getFloodClass(camera)">
              <div class="analysis-icon">
                <i class="fas fa-tint"></i>
              </div>
              <div class="analysis-content">
                <div class="analysis-value">{{ camera.analysis.waterDepth }} cm</div>
                <div class="analysis-label">积水深度</div>
                <div class="analysis-trend">{{ camera.analysis.waterDepthChange }}</div>
              </div>
            </div>
            
            <div class="analysis-item flood-risk" :class="getFloodClass(camera)">
              <div class="analysis-icon">
                <i class="fas fa-exclamation-triangle"></i>
              </div>
              <div class="analysis-content">
                <div class="analysis-value">{{ camera.analysis.floodRisk }}</div>
                <div class="analysis-label">内涝风险</div>
                <div class="analysis-trend">{{ camera.analysis.riskDescription }}</div>
              </div>
            </div>
            
            <div class="analysis-item traffic" :class="getFloodClass(camera)">
              <div class="analysis-icon">
                <i class="fas fa-road"></i>
              </div>
              <div class="analysis-content">
                <div class="analysis-value">{{ camera.analysis.trafficStatus }}</div>
                <div class="analysis-label">交通状况</div>
                <div class="analysis-trend">{{ camera.analysis.trafficDescription }}</div>
              </div>
            </div>
            
            <div class="analysis-item rainfall">
              <div class="analysis-icon">
                <i class="fas fa-cloud-rain"></i>
              </div>
              <div class="analysis-content">
                <div class="analysis-value">{{ camera.analysis.rainfall }} mm/h</div>
                <div class="analysis-label">降雨量</div>
                <div class="analysis-trend">过去1小时累计</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 摄像头信息 -->
        <div class="camera-info-panel">
          <h3><i class="fas fa-info-circle"></i> 设备信息</h3>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">摄像头ID:</span>
              <span class="info-value">{{ camera.id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">设备序列号:</span>
              <span class="info-value">{{ camera.deviceSerial || '未配置' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最后更新:</span>
              <span class="info-value">{{ lastUpdateTime }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">监控状态:</span>
              <span class="info-value status-display">
                <span class="status-dot" :class="getStatusClass(camera)"></span>
                {{ camera.status }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 引入新的 IframePlayer 组件
import IframePlayer from './IframePlayer.vue'

export default {
  name: 'CameraDetail',
  components: {
    IframePlayer
  },
  props: {
    camera: Object,
    currentTime: String,
    lastUpdateTime: String
  },
  methods: {
    getStatusClass(camera) {
      if (camera.status === '在线') return 'status-online'
      if (camera.status === '离线') return 'status-offline'
      if (camera.status === '维护中') return 'status-maintenance'
      return ''
    },
    getFloodClass(camera) {
      if (!camera.floodLevel) return ''
      return `flood-${camera.floodLevel}`
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
    onPlayerLoaded() {
      console.log('播放器加载成功')
    },
    onPlayerError(error) {
      console.error('播放器加载失败:', error)
    }
  }
}
</script>

<style scoped>
.camera-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

/* 统一表头 */
.detail-header {
  background: white;
  padding: 10px 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left i {
  font-size: 2rem;
  color: #1e3c72;
}

.header-title h2 {
  font-size: 1.5rem;
  color: #1e3c72;
  margin: 0;
}

.header-title p {
  color: #666;
  margin: 4px 0 0 0;
  font-size: 0.95rem;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.header-status {
  display: flex;
  gap: 10px;
}

.status-badge,
.flood-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.status-online {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-badge.status-offline {
  background: #ffebee;
  color: #c62828;
}

.status-badge.status-maintenance {
  background: #fff3e0;
  color: #ef6c00;
}

.flood-badge {
  color: white;
}

.flood-badge.flood-low {
  background: #4caf50;
}

.flood-badge.flood-medium {
  background: #ff9800;
}

.flood-badge.flood-high {
  background: #f44336;
}

.flood-badge.flood-critical {
  background: #9c27b0;
  animation: pulse 2s infinite;
}

.header-time {
  color: #666;
  font-size: 0.9rem;
}

/* 主要内容区域 */
.detail-content {
  flex: 1;
  display: flex;
  gap: 10px;
  padding: 10px;
  overflow: hidden;
}

/* 视频区域 */
.video-section {
  flex: 2;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 95%;
  
}

.video-player {
  flex: 1;
  min-height: 500px;
}

/* 信息区域 */
.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 300px;
  max-width: 400px;
}

.analysis-panel,
.camera-info-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 10px;
}

.analysis-panel h3,
.camera-info-panel h3 {
  margin: 0 0 15px 0;
  color: #1e3c72;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.1rem;
}

/* 分析网格 */
.analysis-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #1e3c72;
}

.analysis-item.water-depth {
  border-left-color: #2196f3;
}

.analysis-item.flood-risk {
  border-left-color: #ff9800;
}

.analysis-item.traffic {
  border-left-color: #4caf50;
}

.analysis-item.rainfall {
  border-left-color: #00bcd4;
}

.analysis-item.flood-low {
  border-left-color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
}

.analysis-item.flood-medium {
  border-left-color: #ff9800;
  background: rgba(255, 152, 0, 0.1);
}

.analysis-item.flood-high {
  border-left-color: #f44336;
  background: rgba(244, 67, 54, 0.1);
}

.analysis-item.flood-critical {
  border-left-color: #9c27b0;
  background: rgba(156, 39, 176, 0.1);
  animation: pulse 2s infinite;
}

.analysis-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: white;
}

.analysis-item.water-depth .analysis-icon {
  background: #2196f3;
}

.analysis-item.flood-risk .analysis-icon {
  background: #ff9800;
}

.analysis-item.traffic .analysis-icon {
  background: #4caf50;
}

.analysis-item.rainfall .analysis-icon {
  background: #00bcd4;
}

.analysis-content {
  flex: 1;
}

.analysis-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 2px;
}

.analysis-label {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 2px;
}

.analysis-trend {
  font-size: 0.8rem;
  color: #888;
}

/* 摄像头信息 */
.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-label {
  font-weight: 500;
  color: #666;
  font-size: 0.9rem;
}

.info-value {
  color: #333;
  font-size: 0.9rem;
}

.status-display {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.status-online {
  background: #4caf50;
}

.status-dot.status-offline {
  background: #f44336;
}

.status-dot.status-maintenance {
  background: #ff9800;
}

/* 动画 */
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .detail-content {
    flex-direction: column;
  }
  
  .info-section {
    max-width: none;
    flex-direction: row;
  }
  
  .analysis-panel,
  .camera-info-panel {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-right {
    align-items: flex-start;
  }
  
  .detail-content {
    padding: 15px;
  }
  
  .info-section {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .detail-header {
    padding: 15px;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .header-title h2 {
    font-size: 1.3rem;
  }
  
  .analysis-item {
    flex-direction: column;
    text-align: center;
    gap: 10px;
  }
  
  .analysis-content {
    text-align: center;
  }
}
</style>