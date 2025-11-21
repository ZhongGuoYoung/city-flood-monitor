<template>
  <div class="page-history-video">
    <!-- 左：历史会话侧栏 -->
    <aside class="sidebar">
      <CameraSidebarHistory
        :videos="videos"
        :selected="selected?.data"
        @select-source="onSelectSource"
        @query-history="onQueryHistory"
        @delete-record="handleDelete"
      />
    </aside>

    <!-- 右：顶部工具条 + 中间左右布局 + 底部进度条 -->
    <main class="main">
      <!-- 顶部工具条 -->
      <header class="topbar">
        <div class="title">
          <h2>历史视频流</h2>
          <p v-if="selected">{{ selected.data.name }}</p>
          <p v-else>请选择左侧的视频源和时间段</p>
        </div>
        <div class="actions">
          <button class="btn" :disabled="!playerReady" @click="togglePlay">
            {{ playing ? '暂停' : '播放' }}
          </button>

          <select
            class="btn"
            :disabled="!playerReady"
            v-model.number="playbackRate"
            @change="applyRate"
          >
            <option :value="0.5">0.5×</option>
            <option :value="1">1×</option>
            <option :value="1.5">1.5×</option>
            <option :value="2">2×</option>
            <option :value="4">4×</option>
          </select>

          <button class="btn" :disabled="!playerReady" @click="mute = !mute">
            {{ mute ? '取消静音' : '静音' }}
          </button>

          <button class="btn" :disabled="!playerReady" @click="snapshot">
            截帧
          </button>

          <!-- 导出 detect_tick 的折线图数据 -->
          <button class="btn" :disabled="!ticks.length" @click="exportCSV">
            导出CSV
          </button>
        </div>
      </header>

      <!-- 中间：左播放器 + 右折线图 -->
      <section class="content">
        <!-- 左：播放器 + 掩膜 canvas -->
        <section class="player-wrap">
          <video
            ref="videoEl"
            class="player"
            :src="playerUrl"
            controls
            playsinline
            :muted="mute"
          ></video>

          <!-- 覆盖层：根据 detect_tick 的 mask_* / water_polys / risk_boxes 画掩膜 -->
          <canvas ref="overlay" class="overlay"></canvas>

          <div v-if="!selected" class="placeholder">
            请选择视频源并设置时间段后点击“查询”
          </div>

          <!-- HUD -->
          <div class="hud">
            <div>速率：{{ playbackRate.toFixed(1) }}×</div>
            <div v-if="durationSec > 0">
              进度：{{ fmtHMS(currentSec) }} / {{ fmtHMS(durationSec) }}
            </div>
          </div>
        </section>

        <!-- 右：折线图（淹没范围 & 风险等级） -->
        <section class="panel chart-panel">
          <header class="panel-head">
            <h3>淹没范围 / 风险等级</h3>
            <div class="panel-legend">
              <span class="legend-item water">
                <span class="dot"></span>淹没范围（water_percent）
              </span>
              <span class="legend-item risk">
                <span class="dot"></span>风险等级（risk_level）
              </span>
            </div>
          </header>

          <!-- 改成 ECharts 容器 -->
          <div ref="chart" class="chart"></div>
        </section>
      </section>

      <!-- 底部：进度条（整个会话时间段） -->
      <div class="progress">
        <input
          type="range"
          min="0"
          max="1000"
          step="1"
          v-model.number="slider"
          @input="onSlider"
        />
        <div class="ticks">
          <span>{{ startStr }}</span>
          <span>{{ endStr }}</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
/* eslint-disable */
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import CameraSidebarHistory from '@/components/CameraSidebarHistory.vue'
import axios from 'axios'
import { API_BASE } from '@/lib/api'
import * as echarts from 'echarts'   // ⭐ 使用 ECharts

// 左侧 detect_session 列表
const videos = ref([])
const selected = ref(null) // { type:'video', data }

const startStr = ref('')
const endStr = ref('')

// 播放器相关
const videoEl = ref(null)
const overlay = ref(null)
const hls = ref(null) // 预留 HLS：目前没用
const playerUrl = ref('')

const playerReady = ref(false)
const playing = ref(false)
const playbackRate = ref(1)
const mute = ref(false)

// 进度条
const slider = ref(0) // 0..1000
const durationSec = ref(0)
const currentSec = ref(0)
let progressTimer = null

// detect_tick：后端时序数据
// 表结构：session_id, ts_ms, video_sec, water_percent, risk_level,
//         mask_h, mask_w, water_polys, risk_boxes
const ticks = ref([])       // 每项：{ video_sec, water_percent, risk_level, mask_w, mask_h, water_polys, risk_boxes }
const currentTick = ref(null)

// 折线图（ECharts）
const chart = ref(null)
let chartInstance = null

const MASK_OFFSET_X_FRAC = 0   // 横向平移（按宽度的比例），>0 向右，<0 向左
const MASK_OFFSET_Y_FRAC = 0.15   // 纵向平移（按高度的比例），>0 向下，<0 向上
const MASK_SCALE_X = 1.0         // 横向缩放，>1 变宽，<1 变窄
const MASK_SCALE_Y = 0.7         // 纵向缩放，>1 变高，<1 变矮


function pad (n) {
  return n < 10 ? '0' + n : '' + n
}

function defaultRange () {
  const d = new Date()
  const Y = d.getFullYear()
  const M = pad(d.getMonth() + 1)
  const D = pad(d.getDate())
  const date = `${Y}-${M}-${D}`
  return { start: date, end: date }
}

// 拉取 detect_session 列表
async function loadSessions ({ start, end, all } = {}) {
  const params = {}
  if (all) {
    params.all = true
  } else {
    if (start) params.start = start
    if (end) params.end = end
  }
  const { data } = await axios.get(`${API_BASE}/detect/sessions`, { params })
  videos.value = data.items || []
}

// 选中一条 session：播放 + 拉取 detect_tick
async function onSelectSource ({ data, start, end }) {
  selected.value = { type: 'video', data }
  startStr.value = start
  endStr.value = end

  const url = data.playUrl || data.recordPath || ''
  if (!url) {
    console.warn('[History] session has no playUrl / recordPath')
    return
  }

  ticks.value = []
  currentTick.value = null

  await initPlayerWithUrl(url)
  // 假定 detect_tick 的查询方式是 ?session_id=xxx，你按自己后端改
  await loadTicks(data.id)
}

// 左侧“查询历史”按钮
async function onQueryHistory ({ start, end, all }) {
  startStr.value = start || ''
  endStr.value = end || ''
  if (all) {
    await loadSessions({ all: true })
    return
  }
  await loadSessions({ start, end })
}

// 删除会话
async function handleDelete (video) {
  if (!video || !video.id) return
  await axios.delete(`${API_BASE}/detect/sessions/${video.id}`)
  videos.value = videos.value.filter(v => v.id !== video.id)
}

// 初始化播放器
async function initPlayerWithUrl (url) {
  playerReady.value = false
  playing.value = false
  playerUrl.value = url

  await nextTick()
  const el = videoEl.value
  if (!el) return

  try {
    el.pause()
    el.currentTime = 0
  } catch (e) {
    console.warn('[History] reset video failed:', e)
  }

  const onReady = () => {
    el.removeEventListener('loadedmetadata', onReady)
    el.removeEventListener('loadeddata', onReady)
    afterPlayReady()
  }

  if (el.readyState >= 1) {
    onReady()
  } else {
    el.addEventListener('loadedmetadata', onReady)
    el.addEventListener('loadeddata', onReady)
  }
}

function afterPlayReady () {
  const el = videoEl.value
  if (!el) return
  playerReady.value = true
  playing.value = false
  applyRate()

  durationSec.value = Math.floor(el.duration || 0)

  resizeOverlay()
  updateChart()   
  startProgressTimer()
}

function togglePlay () {
  const el = videoEl.value
  if (!el) return
  if (el.paused) {
    el.play()
    playing.value = true
  } else {
    el.pause()
    playing.value = false
  }
}

function applyRate () {
  const el = videoEl.value
  if (!el) return
  el.playbackRate = playbackRate.value
}

// 进度刷新
function startProgressTimer () {
  stopProgressTimer()
  progressTimer = setInterval(updateProgress, 300)
}

function stopProgressTimer () {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

function updateProgress () {
  const el = videoEl.value
  if (!el) return
  currentSec.value = el.currentTime || 0
  if (durationSec.value > 0) {
    slider.value = Math.floor((currentSec.value / durationSec.value) * 1000)
  }
  syncTickWithVideo()
}

function onSlider () {
  const el = videoEl.value
  if (!el || durationSec.value <= 0) return
  const target = (slider.value / 1000) * durationSec.value
  el.currentTime = target
  currentSec.value = target
  syncTickWithVideo()
}

// ---------- detect_tick：加载 + 与视频时间同步 ----------

//解析返回的字符串
function parseJsonSafe (v) {
  if (!v) return []
  let val = v

  // 已经是数组，直接用
  if (Array.isArray(val)) return val

  // 最多尝试解析 2 次，处理字符串嵌套的情况
  for (let i = 0; i < 2; i++) {
    if (Array.isArray(val) || typeof val === 'object') {
      return val
    }
    if (typeof val === 'string') {
      try {
        val = JSON.parse(val)
      } catch (e) {
        console.warn('parseJsonSafe error', e, v)
        return []
      }
    } else {
      break
    }
  }

  return Array.isArray(val) || typeof val === 'object' ? val : []
}



// 这里假定后端有：GET /detect/ticks?session_id=xxx
async function loadTicks (sessionId) {
  if (!sessionId) return
  try {
    const { data } = await axios.get(`${API_BASE}/detect/ticks`, {
      params: { session_id: sessionId }
    })
    const items = data.items || data || []
    ticks.value = items
      .map(t => ({
        video_sec: t.video_sec ?? t.video_time ?? 0,
        water_percent: t.water_percent ?? 0,
        risk_level: t.risk_level ?? 0,
        mask_w: t.mask_w,
        mask_h: t.mask_h,
        water_polys: parseJsonSafe(t.water_polys),
        risk_boxes: parseJsonSafe(t.risk_boxes)
      }))
      .sort((a, b) => a.video_sec - b.video_sec)

    updateChart()      
    syncTickWithVideo()
  } catch (err) {
    console.error('loadTicks failed', err)
    ticks.value = []
    updateChart()
  }
}

// 根据当前视频时间找到最近一条 tick
function syncTickWithVideo () {
  if (!ticks.value.length) {
    currentTick.value = null
    drawOverlay()
    return
  }
  const t = currentSec.value
  let best = ticks.value[0]
  let bestDiff = Math.abs(best.video_sec - t)

  for (let i = 1; i < ticks.value.length; i++) {
    const tk = ticks.value[i]
    const diff = Math.abs(tk.video_sec - t)
    if (diff < bestDiff) {
      best = tk
      bestDiff = diff
    } else if (tk.video_sec > t && diff > bestDiff) {
      break
    }
  }
  currentTick.value = best
  drawOverlay()
}

// 截帧
function snapshot () {
  const el = videoEl.value
  if (!el) return
  const cvs = document.createElement('canvas')
  cvs.width = el.videoWidth
  cvs.height = el.videoHeight
  const ctx = cvs.getContext('2d')
  ctx.drawImage(el, 0, 0, cvs.width, cvs.height)
  const url = cvs.toDataURL('image/png')
  const a = document.createElement('a')
  a.href = url
  a.download = `snapshot_${Date.now()}.png`
  a.click()
}

// ---------- 覆盖层：根据 mask_* / polys / boxes 画掩膜 ----------

function resizeOverlay () {
  const el = videoEl.value
  const ov = overlay.value
  if (!el || !ov) return

  // 视频在屏幕上的位置和大小
  const rectVideo = el.getBoundingClientRect()
  // 容器（player-wrap）的屏幕位置
  const rectWrap = ov.parentElement.getBoundingClientRect()

  const dpr = window.devicePixelRatio || 1
  const width = rectVideo.width
  const height = rectVideo.height

  // 设置 canvas 真实像素大小
  ov.width = width * dpr
  ov.height = height * dpr
  // 设置 CSS 尺寸
  ov.style.width = width + 'px'
  ov.style.height = height + 'px'

  // 让 canvas 左上角对齐到视频画面左上角
  const offsetX = rectVideo.left - rectWrap.left
  const offsetY = rectVideo.top - rectWrap.top
  ov.style.left = offsetX + 'px'
  ov.style.top = offsetY + 'px'

  drawOverlay()
}



function drawOverlay () {
  const ov = overlay.value
  const el = videoEl.value
  if (!ov || !el) return

  const ctx = ov.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const w = ov.clientWidth
  const h = ov.clientHeight

  ctx.clearRect(0, 0, ov.width, ov.height)
  ctx.save()
  ctx.scale(dpr, dpr)

  const tk = currentTick.value
  if (!tk) {
    ctx.restore()
    return
  }

  // 方便统一使用：整体校准
  const offX = MASK_OFFSET_X_FRAC
  const offY = MASK_OFFSET_Y_FRAC
  const sX = MASK_SCALE_X
  const sY = MASK_SCALE_Y

  // ---------- 掩膜区域：water_polys ----------
  if (tk.water_polys && tk.water_polys.length) {
    const raw = tk.water_polys
    // 兼容 [ {outer: [...]}, {outer: [...] } ] 和 [ [x,y], ... ]
    const polys = []

    const arr = Array.isArray(raw) ? raw : [raw]
    arr.forEach(item => {
      if (!item) return
      if (Array.isArray(item.outer)) {
        polys.push(item.outer)
      } else if (Array.isArray(item)) {
        polys.push(item)
      }
    })

    ctx.fillStyle = 'rgba(59,130,246,0.32)'
    ctx.strokeStyle = 'rgba(59,130,246,0.8)'
    ctx.lineWidth = 1.5

    polys.forEach(poly => {
      if (!poly || !poly.length) return
      ctx.beginPath()
      poly.forEach((pt, idx) => {
        if (!pt || pt.length < 2) return
        // 这里按 0~1 归一化处理：0 左/上，1 右/下
        const nx = Math.min(Math.max(pt[0], 0), 1)
        const ny = Math.min(Math.max(pt[1], 0), 1)

        const x = (nx * sX + offX) * w
        const y = (ny * sY + offY) * h

        if (idx === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.closePath()
      ctx.fill()
      ctx.stroke()
    })
  }

  // ---------- 风险框：risk_boxes = [[x1,y1,x2,y2,level], ...] ----------
  if (tk.risk_boxes && tk.risk_boxes.length) {
    let boxes = tk.risk_boxes
    if (!Array.isArray(boxes)) {
      boxes = [boxes]
    }
    // 有些情况会是 [ [ [...], [...]] ]，这里拍平一层
    if (boxes.length === 1 && Array.isArray(boxes[0][0])) {
      boxes = boxes[0]
    }

    ctx.strokeStyle = 'rgba(239,68,68,0.9)'
    ctx.lineWidth = 2

    boxes.forEach(box => {
      if (!box || box.length < 4) return
      const nx1 = Math.min(Math.max(box[0], 0), 1)
      const ny1 = Math.min(Math.max(box[1], 0), 1)
      const nx2 = Math.min(Math.max(box[2], 0), 1)
      const ny2 = Math.min(Math.max(box[3], 0), 1)

      const x1 = (nx1 * sX + offX) * w
      const y1 = (ny1 * sY + offY) * h
      const x2 = (nx2 * sX + offX) * w
      const y2 = (ny2 * sY + offY) * h

      const bw = x2 - x1
      const bh = y2 - y1
      ctx.strokeRect(x1, y1, bw, bh)
    })
  }

  ctx.restore()
}


// ---------- 折线图：用 ECharts 画 X=video_sec，Y=water_percent & risk_level ----------

// 初始化 ECharts 实例
function initChart () {
  const dom = chart.value
  if (!dom) return
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(dom)
  updateChart()
}

// 更新图表数据
function updateChart () {
  const dom = chart.value
  if (!dom) return

  if (!chartInstance) {
    initChart()
    return
  }

  if (!ticks.value.length) {
    chartInstance.setOption({
      xAxis: { type: 'category', data: [] },
      yAxis: [{ type: 'value' }, { type: 'value' }],
      series: []
    })
    return
  }

  const xs = ticks.value.map(t => t.video_sec || 0)
  const waterRaw = ticks.value.map(t => t.water_percent || 0)
  const riskData = ticks.value.map(t => t.risk_level || 0)

  // 判断 water_percent 是 0~1 还是 0~100
  const maxWater = Math.max(...waterRaw)
  const waterIsRatio = maxWater <= 1.5
  const waterData = waterIsRatio ? waterRaw.map(v => v * 100) : waterRaw

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter (params) {
        // params 是一个数组（两个 series）
        const p = params
        const lines = []
        if (p.length) {
          lines.push(`时间：${p[0].axisValue}s`)
        }
        p.forEach(it => {
          if (it.seriesName === '淹没范围') {
            lines.push(`${it.marker}${it.seriesName}：${it.data.toFixed(1)}%`)
          } else if (it.seriesName === '风险等级') {
            lines.push(`${it.marker}${it.seriesName}：${it.data}`)
          }
        })
        return lines.join('<br/>')
      }
    },
    // legend: {
    //   data: ['淹没范围', '风险等级']
    // },
    grid: {
      left: 48,
      right: 40,
      top: 32,
      bottom: 32
    },
    xAxis: {
      type: 'category',
      name: '时间(s)',
      boundaryGap: false,
      data: xs
    },
    yAxis: [
      {
        type: 'value',
        name: '淹没范围(%)',
        position: 'left',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      {
        type: 'value',
        name: '风险等级',
        position: 'right',
        min: 0,
        max: 5,
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '淹没范围',
        type: 'line',
        yAxisIndex: 0,
        smooth: true,
        symbol: 'none',
        data: waterData
      },
      {
        name: '风险等级',
        type: 'line',
        yAxisIndex: 1,
        step: 'middle',
        symbol: 'circle',
        data: riskData
      }
    ]
  }

  chartInstance.setOption(option, true)
}

// 导出：video_sec, water_percent, risk_level
function exportCSV () {
  if (!ticks.value.length) return
  const rows = [['video_sec', 'water_percent', 'risk_level']]
  ticks.value.forEach(t => {
    rows.push([t.video_sec, t.water_percent, t.risk_level])
  })
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'detect_tick_series.csv'
  a.click()
  URL.revokeObjectURL(url)
}

function fmtHMS (sec) {
  const s = Math.max(0, Math.floor(sec || 0))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const ss = s % 60
  return `${pad(h)}:${pad(m)}:${pad(ss)}`
}

function onResize () {
  resizeOverlay()
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 生命周期
onMounted(async () => {
  const { start, end } = defaultRange()
  startStr.value = start
  endStr.value = end
  await loadSessions({ all: true })

  nextTick(() => {
    resizeOverlay()
    initChart()   // ⭐ 初始化图表
    window.addEventListener('resize', onResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  stopProgressTimer()
  if (hls.value) {
    hls.value.destroy()
    hls.value = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.page-history-video {
  display: grid;
  grid-template-columns: 320px 1fr;
  height: 100%;
  overflow: hidden;
  background: #f5f7fb;
}

.sidebar {
  background: linear-gradient(180deg, #1e3c72, #2a5298);
  color: #fff;
  overflow: auto;
}

.main {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}

/* 顶部工具条 */
.topbar {
  background: #fff;
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.title h2 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.title p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.btn {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}

.btn:hover {
  background: #f3f4f6;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* 中间内容：左视频右图 */
.content {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1.4fr);
  gap: 12px;
  align-items: stretch;
  overflow: hidden;
}

/* 播放器 */
.player-wrap {
  position: relative;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  min-height: 420px;
  display: grid;
  place-items: center;
}

.player {
  width: 100%;
  height: 100%;
  max-height: calc(100vh - 260px);
  background: #000;
  outline: none;
}

/* 只由 JS 控制大小和位置 */
.overlay {
  position: absolute;
  pointer-events: none; /* 仅展示掩膜，不可点击 */
}


.placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #9ca3af;
  font-size: 14px;
}

.hud {
  position: absolute;
  right: 10px;
  top: 10px;
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 12px;
  display: grid;
  gap: 4px;
}

/* 底部进度条 */
.progress {
  background: #fff;
  border-radius: 10px;
  padding: 8px 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.progress input[type='range'] {
  width: 100%;
}

.ticks {
  display: flex;
  justify-content: space-between;
  color: #6b7280;
  font-size: 12px;
  margin-top: 4px;
}

/* 右边折线图面板 */
.panel {
  background: #fff;
  border-radius: 10px;
  padding: 12px 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.chart-panel {
  min-height: 420px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  color: #111827;
}

.panel-legend {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #4b5563;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

.legend-item.water .dot {
  background: #1d4ed8;
}

.legend-item.risk .dot {
  background: #dff044;
}

/* ECharts 容器 */
.chart {
  width: 100%;
  flex: 1;
  background: #fbfdff;
  border: 1px solid #eef2ff;
  border-radius: 8px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .content {
    grid-template-columns: 1fr;
  }
  .chart-panel {
    min-height: 260px;
  }
}
</style>
