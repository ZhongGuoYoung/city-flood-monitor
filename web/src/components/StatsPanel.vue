<template>
  <div class="stats-container">
    <div class="stats-header">
      <div class="stats-title">
        <i class="fas fa-chart-bar"></i>
        <span>系统概览</span>
      </div>
      <div class="video-time">更新于: {{ displayTime }}</div>
    </div>
    <div class="stats-grid">
      <div class="stat-card total">
        <div class="stat-value">{{ totalCameras }}</div>
        <div class="stat-label">总摄像头数</div>
      </div>
      <div class="stat-card online">
        <div class="stat-value">{{ onlineCameras }}</div>
        <div class="stat-label">在线摄像头</div>
      </div>
      <div class="stat-card flood">
        <div class="stat-value">{{ floodCameras }}</div>
        <div class="stat-label">内涝预警点</div>
      </div>
      <div class="stat-card critical">
        <div class="stat-value">{{ criticalCameras }}</div>
        <div class="stat-label">严重内涝点</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatsPanel',
  props: {
    cameras: Array,
    lastUpdateTime: [Number, String, Date]
  },
  computed: {
    displayTime() {
      if (this.lastUpdateTime == null || this.lastUpdateTime === '') return '-'
      let d
      if (typeof this.lastUpdateTime === 'number') d = new Date(this.lastUpdateTime)
      else if (this.lastUpdateTime instanceof Date) d = this.lastUpdateTime
      else if (/^\d+$/.test(this.lastUpdateTime)) d = new Date(Number(this.lastUpdateTime))
      else d = new Date(this.lastUpdateTime)

      if (isNaN(d.getTime())) return '-'

      const hh = String(d.getHours()).padStart(2, '0')
      const mm = String(d.getMinutes()).padStart(2, '0')
      const ss = String(d.getSeconds()).padStart(2, '0')
      return `${hh}:${mm}:${ss}`
    },
    totalCameras() {
      return this.cameras.length
    },
    onlineCameras() {
      return this.cameras.filter(camera => camera.status === '在线').length
    },
    floodCameras() {
      return this.cameras.filter(camera => camera.floodLevel).length
    },
    criticalCameras() {
      return this.cameras.filter(camera => camera.floodLevel === 'critical').length
    }
  }
}
</script>

<style scoped>
.stats-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 15px; /* 减小内边距 */
  flex-shrink: 0;
  height: 120px; /* 固定高度，比原来更小 */
}

.stats-header {
  margin-bottom: 10px; /* 减小底部边距 */
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-title {
  font-size: 1rem; /* 减小字体大小 */
  font-weight: 600;
  color: #1e3c72;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px; /* 减小网格间距 */
}

.stat-card {
  padding: 10px; /* 减小内边距 */
  border-radius: 6px;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  height: 60px; /* 固定卡片高度 */
  justify-content: center; /* 垂直居中内容 */
}

.stat-value {
  font-size: 1.4rem; /* 减小数值字体大小 */
  font-weight: 700;
  margin-bottom: 2px; /* 减小底部边距 */
}

.stat-label {
  font-size: 0.8rem; /* 减小标签字体大小 */
  color: #666;
}

.stat-card.total {
  border-left: 4px solid #1e3c72;
}

.stat-card.online {
  border-left: 4px solid #4caf50;
}

.stat-card.flood {
  border-left: 4px solid #f44336;
}

.stat-card.critical {
  border-left: 4px solid #9c27b0;
}

@media (max-width: 992px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats-container {
    height: auto; /* 在小屏幕上自动高度 */
    min-height: 120px;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-container {
    padding: 10px;
  }
  
  .stat-card {
    height: 50px;
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
    padding: 8px 15px;
  }
  
  .stat-value {
    font-size: 1.2rem;
    margin-bottom: 0;
  }
}
</style>
