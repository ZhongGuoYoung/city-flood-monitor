<template>
  <div class="sidebar">
    <!-- 搜索 & 筛选 & 排序 -->
    <div class="sidebar-controls">
      <div class="search-box">
        <i class="fas fa-search"></i>
        <input
          type="text"
          placeholder="搜索摄像头..."
          :value="searchQuery"
          @input="e => $emit('update-search', e.target.value)"
        />
      </div>

      <div class="filter-controls">
        <button
          class="filter-btn"
          :class="{ active: filter === 'all' }"
          @click="$emit('update-filter','all')"
        >全部</button>
        <button
          class="filter-btn"
          :class="{ active: filter === 'online' }"
          @click="$emit('update-filter','online')"
        >在线</button>
        <button
          class="filter-btn"
          :class="{ active: filter === 'flood' }"
          @click="$emit('update-filter','flood')"
        >内涝</button>
      </div>

      <div class="sort-controls" v-if="filter === 'flood'">
        <button
          class="sort-btn"
          :class="{ active: sortOrder === 'asc' }"
          @click="$emit('update-sort','asc')"
        >
          <i class="fas fa-sort-amount-down-alt"></i>升序
        </button>
        <button
          class="sort-btn"
          :class="{ active: sortOrder === 'desc' }"
          @click="$emit('update-sort','desc')"
        >
          <i class="fas fa-sort-amount-up"></i>降序
        </button>
      </div>
    </div>

    <!-- 摄像头列表 -->
    <div class="camera-list">
      <div
        v-for="camera in visibleCameras"
        :key="camera.id"
        class="camera-item"
        :class="{ active: selectedCamera && selectedCamera.id === camera.id }"
        @click="$emit('select-camera', camera)"
      >
        <i class="fas fa-camera"></i>
        <div class="camera-info">
          <div class="camera-name">{{ camera.name }}</div>
          <div class="camera-status">
            <span class="status-indicator" :class="getStatusClass(camera.status)"></span>
            {{ camera.status }}
            <span
              v-if="camera.floodLevel"
              class="flood-indicator-small"
              :class="getFloodClass(camera.floodLevel)"
            >{{ getFloodText(camera.floodLevel) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  
</template>

<script>
export default{
  name: 'CameraSidebarMonitor',
  props:{
    cameras: Array,
    selectedCamera: Object,
    filter: String,
    sortOrder: String,
    searchQuery: String
  },
  emits:['select-camera','update-filter','update-sort','update-search'],
  computed: {
    visibleCameras(){
      const q = (this.searchQuery || '').trim().toLowerCase()
      const floodOrder = { low:1, medium:2, high:3, critical:4 }

      let list = Array.isArray(this.cameras) ? this.cameras : []
      //搜索
      list = list.filter(c => (c.name || '').toLowerCase().includes(q))

      //筛选
      if (this.filter === 'online') list = list.filter(c => c.status === '在线')
      if (this.filter === 'flood')  list = list.filter(c => !!c.floodLevel)

      //排序
      const dir = this.sortOrder === 'asc' ? 1 : -1
      return [...list].sort((a,b) => {
        if (this.filter === 'flood'){
          const A = floodOrder[a.floodLevel] ?? -1
          const B = floodOrder[b.floodLevel] ?? -1
          return dir * (A - B)
        }
        return (a.name || '').localeCompare(b.name || '')
      })
    }
  },
  methods:{
    getStatusClass(s){
      if (s === '在线') return 'status-online'
      if (s === '离线') return 'status-offline'
      if (s === '维护中') return 'status-maintenance'
      return ''
    },
    getFloodClass(level){
      return level ? `flood-${level}` : ''
    },
    getFloodText(level){
      const map = { low:'轻度内涝', medium:'中度内涝', high:'严重内涝', critical:'紧急内涝' }
      return map[level] || ''
    }
  }
}
</script>

<style scoped>
/* 侧栏容器 */
.sidebar {
  width: 300px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: 2px 0 10px rgba(0,0,0,.1);
}

/* 控件区 */
.sidebar-controls {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(255,255,255,.1);
  flex-shrink: 0;
}
.search-box { position: relative; margin-bottom: 15px; }
.search-box input{
  width: 100%;
  padding: 10px 15px 10px 40px;
  border-radius: 4px; border: none;
  background: rgba(255,255,255,.1); color: #fff;
}
.search-box input::placeholder{ color: rgba(255,255,255,.6); }
.search-box i{
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  color: rgba(255,255,255,.6);
}
.filter-controls{ display:flex; gap:10px; margin-bottom: 15px; }
.filter-btn{
  flex:1; padding:8px 0; border:none; border-radius:4px; cursor:pointer;
  background: rgba(255,255,255,.1); color:#fff; transition:.2s;
}
.filter-btn:hover, .filter-btn.active{ background: rgba(79,195,247,.3); }
.sort-controls{ display:flex; gap:10px; }
.sort-btn{
  flex:1; padding:8px 0; border:none; border-radius:4px; cursor:pointer;
  background: rgba(255,255,255,.1); color:#fff; display:flex; align-items:center; justify-content:center; gap:6px;
}
.sort-btn:hover, .sort-btn.active{ background: rgba(79,195,247,.3); }

/* 列表 */
.camera-list{ flex:1; padding:10px 0; overflow-y:auto; }
.camera-item{
  padding: 15px 20px; display:flex; align-items:center; gap:12px;
  cursor:pointer; transition:.2s; border-left:4px solid transparent;
}
.camera-item:hover{ background: rgba(255,255,255,.1); }
.camera-item.active{
  background: rgba(79,195,247,.2);
  border-left-color: #4fc3f7;
}
.camera-item i{ font-size:1.2rem; color:#4fc3f7; }
.camera-info{ flex:1; }
.camera-name{ font-weight:500; margin-bottom:4px; }
.camera-status{ font-size:.8rem; opacity:.9; display:flex; align-items:center; gap:6px; }

/* 状态点 */
.status-indicator{
  display:inline-block; width:8px; height:8px; border-radius:50%;
  background:#aaa;
}
.status-online{ background:#22c55e !important; }
.status-offline{ background:#ef4444 !important; }
.status-maintenance{ background:#f59e0b !important; }

/* 内涝小标记 */
.flood-indicator-small{
  padding:2px 6px; border-radius:10px; font-size:.7rem; line-height:1;
  background: rgba(255,255,255,.15);
}
.flood-low{ background:#22c55e; }
.flood-medium{ background:#eab308; }
.flood-high{ background:#f97316; }
.flood-critical{ background:#ef4444; }

@media (max-width: 768px){
  .sidebar{ width:100%; height:auto; max-height:40vh; }
}
</style>
