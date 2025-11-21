<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <i class="fas fa-video"></i>
      <h1>城市内涝监控系统</h1>
    </div>
    
    <!-- 监测源选项卡 -->
    <div class="monitor-source-tabs">
      <div 
        class="tab-item"
        :class="{ active: activeTab === 'monitor' }"
        @click="handleTabChange('monitor')"
      >
        <i class="fas fa-camera"></i>
        <span>监控</span>
      </div>
      <div 
        class="tab-item"
        :class="{ active: activeTab === 'video' }"
        @click="handleTabChange('video')"
      >
        <i class="fas fa-video"></i>
        <span>视频</span>
      </div>
      <div 
        class="tab-item"
        :class="{ active: activeTab === 'image' }"
        @click="handleTabChange('image')"
      >
        <i class="fas fa-image"></i>
        <span>图片</span>
      </div>
    </div>
    
    <!-- 搜索和筛选控制 -->
    <div class="sidebar-controls" v-if="activeTab === 'monitor'">
      <div class="search-box">
        <i class="fas fa-search"></i>
        <input 
          type="text" 
          placeholder="搜索摄像头..." 
          :value="searchQuery"
          @input="handleSearchInput"
        >
      </div>
      <div class="filter-controls">
        <button 
          class="filter-btn" 
          :class="{ active: filter === 'all' }"
          @click="handleFilterChange('all')"
        >
          全部
        </button>
        <button 
          class="filter-btn" 
          :class="{ active: filter === 'online' }"
          @click="handleFilterChange('online')"
        >
          在线
        </button>
        <button 
          class="filter-btn" 
          :class="{ active: filter === 'flood' }"
          @click="handleFilterChange('flood')"
        >
          内涝
        </button>
      </div>
      
      <!-- 排序控制 -->
      <div class="sort-controls" v-if="filter === 'flood'">
        <button 
          class="sort-btn" 
          :class="{ active: sortOrder === 'asc' }"
          @click="handleSortChange('asc')"
        >
          <i class="fas fa-sort-amount-down-alt"></i>
          升序
        </button>
        <button 
          class="sort-btn" 
          :class="{ active: sortOrder === 'desc' }"
          @click="handleSortChange('desc')"
        >
          <i class="fas fa-sort-amount-up"></i>
          降序
        </button>
      </div>
    </div>
    
    <!-- 摄像头列表 -->
    <div class="camera-list" v-if="activeTab === 'monitor'">
      <div 
        v-for="camera in cameras" 
        :key="camera.id"
        class="camera-item"
        :class="{ active: selectedCamera && selectedCamera.id === camera.id }"
        @click="handleCameraSelect(camera)"
      >
        <i class="fas fa-camera"></i>
        <div class="camera-info">
          <div class="camera-name">{{ camera.name }}</div>
          <div class="camera-status">
            <span class="status-indicator" :class="getStatusClass(camera.status)"></span>
            {{ camera.status }}
            <span v-if="camera.floodLevel" class="flood-indicator-small" :class="getFloodClass(camera.floodLevel)">
              {{ getFloodText(camera.floodLevel) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 视频列表 -->
    <div class="source-list" v-if="activeTab === 'video'">
      <div class="add-source-btn" @click="showAddDialog('video')">
        <i class="fas fa-plus"></i>
        <span>添加视频源</span>
      </div>
      <div 
        v-for="video in videos" 
        :key="video.id"
        class="source-item"
        :class="{ active: selectedSource && selectedSource.id === video.id && selectedSource.type === 'video' }"
        @click="handleSourceSelect(video, 'video')"
      >
        <i class="fas fa-video"></i>
        <div class="source-info">
          <div class="source-name">{{ video.name }}</div>
          <div class="source-desc">{{ video.description }}</div>
        </div>
      </div>
    </div>
    
    <!-- 图片列表 -->
    <div class="source-list" v-if="activeTab === 'image'">
      <div class="add-source-btn" @click="showAddDialog('image')">
        <i class="fas fa-plus"></i>
        <span>添加图片源</span>
      </div>
      <div 
        v-for="image in images" 
        :key="image.id"
        class="source-item"
        :class="{ active: selectedSource && selectedSource.id === image.id && selectedSource.type === 'image' }"
        @click="handleSourceSelect(image, 'image')"
      >
        <i class="fas fa-image"></i>
        <div class="source-info">
          <div class="source-name">{{ image.name }}</div>
          <div class="source-desc">{{ image.description }}</div>
        </div>
      </div>
    </div>
    
    <!-- 添加视频/图片对话框 -->
    <div class="modal-overlay" v-if="showDialog">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>{{ dialogTitle }}</h3>
          <button class="close-btn" @click="closeDialog">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleAddSource">
            <div class="form-group">
              <label for="source-name">名称</label>
              <input 
                type="text" 
                id="source-name" 
                v-model="newSource.name" 
                placeholder="请输入名称"
                required
              >
            </div>
            <div class="form-group">
              <label for="source-url">{{ dialogType === 'video' ? '视频URL' : '图片URL' }}</label>
              <input 
                type="url" 
                id="source-url" 
                v-model="newSource.url" 
                :placeholder="dialogType === 'video' ? '请输入视频URL' : '请输入图片URL'"
                required
              >
            </div>
            <div class="form-group">
              <label for="source-desc">描述</label>
              <textarea 
                id="source-desc" 
                v-model="newSource.description" 
                placeholder="请输入描述"
                rows="3"
              ></textarea>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-cancel" @click="closeDialog">取消</button>
          <button class="btn btn-confirm" @click="handleAddSource">确认添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CameraSidebar',
  props: {
    cameras: Array,
    selectedCamera: Object,
    filter: String,
    sortOrder: String,
    searchQuery: String,
    activeTab: {
      type: String,
      default: 'monitor'
    }
  },
  emits: ['select-camera', 'update-filter', 'update-sort', 'update-search', 'select-source', 'tab-change'],
  data() {
    return {
      showDialog: false,
      dialogType: 'video', // 'video' 或 'image'
      videos: [],
      images: [],
      selectedSource: null,
      newSource: {
        name: '',
        url: '',
        description: ''
      }
    }
  },
  computed: {
    dialogTitle() {
      return this.dialogType === 'video' ? '添加视频源' : '添加图片源'
    }
  },
  methods: {
    handleTabChange(tab) {
      // 直接通知父组件选项卡变化
      this.$emit('tab-change', tab)
    },
    
    showAddDialog(type) {
      this.dialogType = type
      this.showDialog = true
      // 重置表单
      this.newSource = {
        name: '',
        url: '',
        description: ''
      }
    },
    
    closeDialog() {
      this.showDialog = false
    },
    
    handleAddSource() {
      if (!this.newSource.name || !this.newSource.url) {
        alert('请填写名称和URL')
        return
      }
      
      const newItem = {
        id: Date.now(), // 使用时间戳作为ID
        name: this.newSource.name,
        url: this.newSource.url,
        description: this.newSource.description
      }
      
      if (this.dialogType === 'video') {
        this.videos.push(newItem)
      } else {
        this.images.push(newItem)
      }
      
      this.closeDialog()
      alert('添加成功！')
    },
    
    handleSourceSelect(source, type) {
      this.selectedSource = { ...source, type }
      this.$emit('select-source', { type, data: source })
    },
    
    handleCameraSelect(camera) {
      this.$emit('select-camera', camera)
    },
    
    handleFilterChange(filter) {
      this.$emit('update-filter', filter)
    },
    
    handleSortChange(sortOrder) {
      this.$emit('update-sort', sortOrder)
    },
    
    handleSearchInput(event) {
      this.$emit('update-search', event.target.value)
    },
    
    getStatusClass(status) {
      if (status === '在线') return 'status-online'
      if (status === '离线') return 'status-offline'
      if (status === '维护中') return 'status-maintenance'
      return ''
    },
    
    getFloodClass(floodLevel) {
      if (!floodLevel) return ''
      return `flood-${floodLevel}`
    },
    
    getFloodText(floodLevel) {
      if (!floodLevel) return ''
      const texts = {
        'low': '轻度内涝',
        'medium': '中度内涝',
        'high': '严重内涝',
        'critical': '紧急内涝'
      }
      return texts[floodLevel] || ''
    }
  }
}
</script>

<style scoped>
/* 样式保持不变 */
.sidebar {
  width: 300px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  overflow-y: auto;
  transition: all 0.3s ease;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.sidebar-header h1 {
  font-size: 1.4rem;
  font-weight: 600;
}

.sidebar-header i {
  font-size: 1.6rem;
  color: #4fc3f7;
}

/* 监测源选项卡样式 */
.monitor-source-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background-color: rgba(255, 255, 255, 0.05);
}

.tab-item {
  flex: 1;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.85rem;
}

.tab-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.tab-item.active {
  background-color: rgba(79, 195, 247, 0.2);
  color: #4fc3f7;
}

.tab-item i {
  font-size: 1.2rem;
}

.sidebar-controls {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.search-box {
  position: relative;
  margin-bottom: 15px;
}

.search-box input {
  width: 100%;
  padding: 10px 15px 10px 40px;
  border-radius: 4px;
  border: none;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.9rem;
}

.search-box input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.search-box i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.6);
}

.filter-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-btn {
  flex: 1;
  padding: 8px 0;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.85rem;
}

.filter-btn:hover, .filter-btn.active {
  background-color: rgba(79, 195, 247, 0.3);
}

.sort-controls {
  display: flex;
  gap: 10px;
}

.sort-btn {
  flex: 1;
  padding: 8px 0;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.sort-btn:hover, .sort-btn.active {
  background-color: rgba(79, 195, 247, 0.3);
}

.camera-list, .source-list {
  flex: 1;
  padding: 10px 0;
  overflow-y: auto;
}

.camera-item, .source-item {
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
  display: flex;
  align-items: center;
  gap: 12px;
}

.camera-item:hover, .source-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.camera-item.active, .source-item.active {
  background-color: rgba(79, 195, 247, 0.2);
  border-left-color: #4fc3f7;
}

.camera-item i, .source-item i {
  font-size: 1.2rem;
  color: #4fc3f7;
}

.camera-info, .source-info {
  flex: 1;
}

.camera-name, .source-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.camera-status, .source-desc {
  font-size: 0.8rem;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 添加源按钮 */
.add-source-btn {
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px dashed rgba(255, 255, 255, 0.3);
  margin: 10px;
  border-radius: 4px;
  justify-content: center;
}

.add-source-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: #4fc3f7;
}

.add-source-btn i {
  font-size: 1rem;
  color: #4fc3f7;
}

/* 对话框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  color: #333;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #1e3c72;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #4fc3f7;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s;
}

.btn-cancel {
  background-color: #f5f5f5;
  color: #333;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-confirm {
  background-color: #1e3c72;
  color: white;
}

.btn-confirm:hover {
  background-color: #2a5298;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
    max-height: 40vh;
  }
}
</style>