<template>
  <div class="page-monitor">
    <!-- 左侧 -->
    <CameraSidebarMonitor
      :cameras="cameras"
      :selectedCamera="selectedCamera"
      :filter="filter"
      :sortOrder="sortOrder"
      :searchQuery="searchQuery"
      @select-camera="selectCamera"
      @update-filter="(v)=>filter=v"
      @update-sort="(v)=>sortOrder=v"
      @update-search="(v)=>searchQuery=v"
    />

    <!-- 右侧 -->
    <div class="main-content">
      <div class="content-header">
        <div class="header-title">
          <h2>{{ getHeaderTitle() }}</h2>
          <p>{{ getHeaderSubtitle() }}</p>
        </div>
        <div class="header-controls">
          <button class="control-btn" @click="refreshData">
            <i class="fas fa-sync-alt"></i>
            刷新数据
          </button>
          <button class="control-btn" @click="showSettings">
            <i class="fas fa-cog"></i>
            系统设置
          </button>
          <button class="control-btn" @click="toggleView">
            <i class="fas" :class="getToggleButtonIcon"></i>
            {{ getToggleButtonText }}
          </button>
        </div>
      </div>
      
      <div class="content-body">
        <!-- 多摄像头视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view-container">
          <StatsPanel 
            :cameras="cameras"
            :lastUpdateTime="lastUpdateTime"
          />
          <CameraGrid 
            :cameras="filteredCameras"
            @select-camera="selectCamera"
          />
        </div>
        
        <!-- 单摄像头视图 -->
        <div v-else-if="viewMode === 'detail' && selectedCamera" class="camera-detail-view">
          <CameraDetail 
            :camera="selectedCamera"
            :currentTime="currentTime"
            :lastUpdateTime="lastUpdateTime"
          />
        </div>
        
        <!-- 无选中内容时的提示 -->
        <div v-else class="no-content-selected">
          <div class="placeholder" style="height: 100%; border-radius: 8px;">
            <i class="fas fa-video" style="font-size: 5rem;"></i>
            <h3>请选择内容</h3>
            <p>从左侧列表中选择监控摄像头、视频源或图片源</p>
          </div>
        </div>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import CameraSidebarMonitor from '@/components/CameraSidebarMonitor.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import CameraGrid from '@/components/CameraGrid.vue'
import CameraDetail from '@/components/CameraDetail.vue'
import { cameraData, floodLevelMap } from '@/data/CameraData'

const cameras = ref(cameraData.map(x => ({ ...x, updatedAt: x.updatedAt || Date.now() })))
const selectedCamera = ref(null)

const filter = ref('all')     // 'all' | 'online' | 'flood'
const searchQuery = ref('')
const sortKey = ref('floodLevel') // 'name' | 'status' | 'floodLevel' | 'updatedAt'
const sortOrder = ref('desc')     // 'asc' | 'desc'
const viewMode = ref('grid')
const currentTime = ref(Date.now())
const lastUpdateTime = ref(Date.now())
let timer = null
const statusOrder = { '在线': 0, '离线': 1, '故障': 2 }


const filtered = computed(() => {
  const q = (searchQuery.value || '').trim().toLowerCase()
  let list = cameras.value.filter(c => (c.name || '').toLowerCase().includes(q))
  if (filter.value === 'online') list = list.filter(c => c.status === '在线')
  if (filter.value === 'flood')  list = list.filter(c => !!c.floodLevel)
  return list
})


const sortedCameras = computed(() => {
  const dir = sortOrder.value === 'asc' ? 1 : -1
  const score = (c) => {
    switch (sortKey.value) {
      case 'name':       return c.name || ''
      case 'status':     return statusOrder[c.status] ?? 99
      case 'floodLevel': return floodLevelMap[c.floodLevel] ?? -1
      case 'updatedAt':  return new Date(c.updatedAt || 0).getTime()
      default:           return 0
    }
  }
  return [...filtered.value].sort((a, b) => {
    const A = score(a), B = score(b)
    if (typeof A === 'string' || typeof B === 'string') {
      return dir * String(A).localeCompare(String(B))
    }
    return dir * (A - B)
  })
})


const filteredCameras = computed(() => sortedCameras.value)


function refreshData(){
  const now = Date.now()
  cameras.value = cameras.value.map(c => ({ ...c, updatedAt: now }))
  lastUpdateTime.value = now
}



function stopAuto(){ if (timer) { clearInterval(timer); timer = null } }


function toggleView(){
  viewMode.value = viewMode.value === 'grid' ? 'detail' : 'grid'
}

function selectCamera(c){
  selectedCamera.value = c
  viewMode.value = 'detail'
}

function showSettings(){
  console.debug('open settings')
}

function getHeaderTitle(){
  return viewMode.value === 'detail' && selectedCamera.value
    ? selectedCamera.value.name
    : '多摄像头监控视图'
}

function getHeaderSubtitle(){
  return `城市内涝监测与预警系统`
}

const getToggleButtonText = computed(() => viewMode.value === 'grid' ? '单摄像头视图' : '多摄像头视图')
const getToggleButtonIcon = computed(() => viewMode.value === 'grid' ? 'fa-expand' : 'fa-th')

onMounted(() => {
  timer = setInterval(() => { currentTime.value = Date.now() }, 1000)
})


onBeforeUnmount(() => stopAuto())
</script>

<style scoped>
.page-monitor{ display:flex; height:100%; overflow:hidden; }
.monitor-main{ flex:1; display:flex; flex-direction:column; gap:12px; padding:12px; overflow:hidden; }
.toolbar{ display:flex; gap:8px; margin-bottom:4px; }
.btn{ padding:6px 12px; border:1px solid #ddd; border-radius:6px; background:#fff; cursor:pointer; }
.grid-wrap{ flex:1; overflow:auto; }
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  padding: 15px 25px;
  background-color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-title h2 {
  font-size: 1.5rem;
  color: #1e3c72;
}

.header-title p {
  color: #666;
  font-size: 0.9rem;
}

.header-controls {
  display: flex;
  gap: 15px;
}

.control-btn {
  padding: 8px 15px;
  background-color: #1e3c72;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-btn:hover {
  background-color: #2a5298;
}

.content-body {
  flex: 1;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}
</style>
