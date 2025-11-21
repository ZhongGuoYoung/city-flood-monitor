<template>
  <div class="source-list">
    <!-- 时间段 -->
    <div class="time-box">
      <div class="time-row">
        <label>开始</label>
        <input type="date" v-model="startStr" />
      </div>
      <div class="time-row">
        <label>结束</label>
        <input type="date" v-model="endStr" />
      </div>

      <!-- 操作按钮区 -->
      <button class="btn query-btn" @click="emitQuery">
        查询历史
      </button>

      <!-- 新增：全部按钮（永远显示），清除时间筛选，显示全部 -->
      <button class="btn query-btn" @click="showAll">
        全部
      </button>

      <!-- 新增：删除当前选中数据 -->
      <button
        class="btn danger-btn"
        :disabled="!current"
        @click="onDelete"
      >
        删除选中
      </button>
    </div>

    <!-- 历史记录列表（全部来自 props.videos） -->
    <div
      v-for="video in filteredVideos"
      :key="video.id"
      class="source-item"
      :class="{ active: (selected && selected.id === video.id) || (current && current.id === video.id) }"
      @click="select(video)"
    >
      <i class="fas fa-video"></i>
      <div class="source-info">
        <div class="source-name">{{ video.name || ('记录 #' + video.id) }}</div>
        <div class="source-desc">
          {{ formatTime(video.recordTime || video.startedAt) }}
        </div>
      </div>
    </div>

    <!-- 没有数据时的提示 -->
    <div v-if="!filteredVideos.length" style="padding:12px 16px; color:#ccc; font-size:12px;">
      当前时间段暂无记录
    </div>
  </div>
</template>

<script setup>
/* eslint-env vue/setup-compiler-macros */
import { ref, watch, computed } from 'vue'

const props = defineProps({
  //  videos 由父组件传入：即 detect_session 列表
  videos:   { type: Array,  default: () => [] },
  selected: { type: Object, default: null }
})

/**
 * 事件：
 * - select-source   → { type:'video', data, start, end }
 * - query-history   → { start, end }
 * - delete-record   → video 对象（当前选中项），由父组件去调接口删除
 */
const emit = defineEmits(['select-source', 'query-history', 'delete-record'])

// 本地列表 =  props.videos
const localVideos = ref(Array.isArray(props.videos) ? [...props.videos] : [])
watch(
  () => props.videos,
  v => { localVideos.value = Array.isArray(v) ? [...v] : [] },
  { deep: true }
)

// 当前选中
const current = ref(props.selected || null)
watch(
  () => props.selected,
  v => { current.value = v }
)

// ==== 历史时间段 ====
// 初始为空，不自动给日期，只有用户选择才有
const startStr = ref('')
const endStr   = ref('')

// 是否开启按时间段过滤，默认 false = 显示全部
const filterEnabled = ref(false)

// 点击“查询历史” → 抛给父组件由父组件去请求 detect_session
function emitQuery () {
  if (!startStr.value || !endStr.value) {
    // if (typeof window !== 'undefined') {
    //   window.alert('请先选择开始和结束日期')
    // }
    return
  }
  emit('query-history', {
    start: startStr.value,
    end:   endStr.value
  })
  filterEnabled.value = true
}

// 点击“全部” → 清除筛选，前端显示全部
// 如果你希望顺便让父组件重新查全部，也可以在这里 emit 一个特殊参数
function showAll () {
  startStr.value = ''
  endStr.value = ''
  filterEnabled.value = false
  // 同时通知父组件重新拉取全部数据
  emit('query-history', { start: null, end: null, all: true })
}

// 列表点击选中某条记录
function select (video) {
  current.value = video
  emit('select-source', {
    type: 'video',
    data: video,
    start: startStr.value,
    end:   endStr.value
  })
}

// 时间筛选
const filteredVideos = computed(() => {
  if (!filterEnabled.value) return localVideos.value

  const sDate = new Date(startStr.value)
  const eDate = new Date(endStr.value)
  if (isNaN(sDate) || isNaN(eDate) || eDate < sDate) {
    return localVideos.value
  }

  // 起始：当天 00:00:00
  const s = new Date(
    sDate.getFullYear(), sDate.getMonth(), sDate.getDate(), 0, 0, 0, 0
  ).getTime()
  // 结束：当天 23:59:59.999
  const e = new Date(
    eDate.getFullYear(), eDate.getMonth(), eDate.getDate(), 23, 59, 59, 999
  ).getTime()

  return localVideos.value.filter(v => {
    const ts = v.recordTime || v.startedAt
    if (!ts) return true
    const t = new Date(ts).getTime()
    return t >= s && t <= e
  })
})

function formatTime (ts) {
  if (!ts) return '—'
  return String(ts).replace('T', ' ')
}

// 新增：删除当前选中的记录（只抛事件，真正删数据库由父组件做）
function onDelete () {
  if (!current.value) return

  // 简单确认一下，防止误删
  const name = current.value.name || ('记录 #' + current.value.id)
  if (typeof window !== 'undefined') {
    const ok = window.confirm(`确定删除该记录：${name} 吗？`)
    if (!ok) return
  }

  // 通知父组件删除
  emit('delete-record', current.value)

  // 前端本地列表也先删掉一份，界面立刻更新
  localVideos.value = localVideos.value.filter(v => v.id !== current.value.id)
  current.value = null
}

// 筛选结果变化时，自动选中第一条
watch(filteredVideos, (list) => {
  if (!list.length) return
  if (!current.value || !list.some(v => v.id === current.value.id)) {
    current.value = list[0]
    emit('select-source', {
      type: 'video',
      data: current.value,
      start: startStr.value,
      end:   endStr.value
    })
  }
})
</script>

<style scoped>
.time-box{
  margin:10px; padding:10px; border-radius:8px;
  border:1px dashed rgba(255,255,255,.25); color:#fff;
}
.time-row{
  display:grid; grid-template-columns: 42px 1fr;
  align-items:center; gap:8px; margin-bottom:8px;
}
.time-row label{ font-size:12px; opacity:.9; }
.time-row input{
  padding:6px 8px; border-radius:6px; border:1px solid rgba(255,255,255,.25);
  background: rgba(255,255,255,.05); color:#fff;
}
.query-btn{
  width:100%; margin-top:6px;
  border:1px solid rgba(255,255,255,.35); border-radius:8px;
  background:rgba(255,255,255,.08); color:#fff;
  cursor:pointer; padding:6px 10px;
}
.query-btn:hover{ background:rgba(255,255,255,.14); }

/* 新增：删除按钮样式（红色一点） */
.danger-btn{
  width:100%; margin-top:6px;
  border:1px solid rgba(255,99,132,.7); border-radius:8px;
  background:rgba(255,99,132,.12); color:#ff8c9a;
  cursor:pointer; padding:6px 10px;
}
.danger-btn:disabled{
  opacity:.4; cursor:not-allowed;
}
.danger-btn:not(:disabled):hover{
  background:rgba(255,99,132,.18);
}

.source-item{
  padding:15px 20px; cursor:pointer; transition:all .2s ease;
  border-left:4px solid transparent; display:flex;
  align-items:center; gap:12px; color:#fff;
}
.source-item:hover{ background-color:rgba(255,255,255,.1); }
.source-item.active{
  background-color:rgba(79,195,247,.2);
  border-left-color:#4fc3f7;
}
.source-item i{ font-size:1.2rem; color:#4fc3f7; }
.source-info{ flex:1; }
.source-name{ font-weight:500; margin-bottom:4px; }
.source-desc{
  font-size:.8rem; opacity:.8;
  display:flex; align-items:center; gap:5px;
}
</style>
