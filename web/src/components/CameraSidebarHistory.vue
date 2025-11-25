<template>
  <div class="source-list">
    <!-- 时间段 -->
    <div class="time-box">
      <div class="time-row">
        <label>开始</label>
        <el-date-picker
          v-model="startStr"
          type="date"
          placeholder="选择开始日期"
          value-format="YYYY-MM-DD"
          :editable="false"          
          class="time-picker"
        />
      </div>
      <div class="time-row">
        <label>结束</label>
        <el-date-picker
          v-model="endStr"
          type="date"
          placeholder="选择结束日期"
          value-format="YYYY-MM-DD"
          :editable="false"
          class="time-picker"
        />
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
.source-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 12px 18px;
  background: linear-gradient(180deg, rgba(13, 24, 48, 0.65), rgba(10, 16, 32, 0.9));
  color: #e5e7eb;
  font-family: 'Poppins', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.time-box {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: linear-gradient(145deg, rgba(34, 211, 238, 0.06), rgba(15, 23, 42, 0.76));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 12px 32px -26px rgba(34, 211, 238, 0.65);
}

.time-row {
  display: grid;
  grid-template-columns: 46px 1fr;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.time-row label {
  font-size: 12px;
  color: rgba(226, 232, 240, 0.85);
}

.time-row input {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.7);
  color: #e2e8f0;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.time-row input:focus {
  border-color: rgba(34, 211, 238, 0.85);
  box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.25);
}

.btn {
  width: 100%;
  margin-top: 8px;
  border-radius: 10px;
  cursor: pointer;
  padding: 10px 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
  transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.15s ease, border-color 0.2s ease;
}

.query-btn {
  border: 1px solid rgba(34, 211, 238, 0.65);
  background: linear-gradient(135deg, #2563eb, #22d3ee);
  color: #e0f2fe;
  box-shadow: 0 12px 30px -20px rgba(34, 211, 238, 0.9), inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.query-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 34px -22px rgba(34, 211, 238, 0.96);
}

.query-btn:active {
  transform: translateY(0);
  filter: brightness(0.97);
}

/* 删除按钮（红调） */
.danger-btn {
  border: 1px solid rgba(248, 113, 113, 0.7);
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.28), rgba(248, 113, 113, 0.16));
  color: #fecdd3;
  box-shadow: 0 10px 28px -22px rgba(248, 113, 113, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.danger-btn:not(:disabled):hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
}

.danger-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
  border-color: rgba(148, 163, 184, 0.28);
  background: rgba(148, 163, 184, 0.14);
  color: rgba(226, 232, 240, 0.6);
}

.source-item {
  padding: 14px 14px;
  cursor: pointer;
  transition: all 0.18s ease;
  border-left: 4px solid transparent;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #e5e7eb;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 0 10px 30px -26px rgba(34, 211, 238, 0.65);
}

.source-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(34, 211, 238, 0.25);
  transform: translateY(-1px);
}

.source-item.active {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.18), rgba(37, 99, 235, 0.15));
  border-color: #22d3ee;
  box-shadow: 0 14px 36px -26px rgba(34, 211, 238, 0.75);
}

.source-item i {
  font-size: 1.15rem;
  color: #38bdf8;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.55);
}

.source-info {
  flex: 1;
}

.source-name {
  font-weight: 600;
  margin-bottom: 4px;
  letter-spacing: 0.01em;
}

.source-desc {
  font-size: 0.82rem;
  color: rgba(226, 232, 240, 0.72);
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 空状态 */
.source-list > div:last-child[style] {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  margin: 0 2px;
}
.time-picker {
  width: 100%;
}

/* 如果想让它和深色面板更贴一点，可以再细调整： */
:deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.7);
  border-radius: 10px;
}

</style>
