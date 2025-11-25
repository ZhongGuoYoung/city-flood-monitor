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

          <button
             class="btn"
              :disabled="!selected || !ticks.length"
              @click="downloadVideoWithMask"
            >
             下载视频
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
                <span class="dot"></span>淹没范围
              </span>
              <span class="legend-item risk">
                <span class="dot"></span>风险等级
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
      data: xs,
      axisLine: { lineStyle: { color: '#fff' } },
        axisLabel: {
          formatter: '{value}',
          color: '#fff'
        },
      splitLine: { show: false }
    },
    yAxis: [
      {
        type: 'value',
        name: '淹没范围(%)',
        position: 'left',
        min: 0,
        max: 100,
        nameTextStyle: { color: '#c7d2fe', fontWeight: 600 },
        axisLine: { lineStyle: { color: '#38bdf8' } },
        axisLabel: {
          formatter: '{value}%',
          color: '#e2e8f0'
        },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.28)' } }
      },
      {
        type: 'value',
        name: '风险等级',
        position: 'right',
        min: 0,
        max: 5,
        nameTextStyle: { color: '#fed7aa', fontWeight: 600 },
        axisLine: { lineStyle: { color: '#fbbf24' } },
        axisLabel: {
          formatter: '{value}',
          color: '#fbbf24'
        },
        splitLine: { show: false }
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

//导出视频
async function downloadVideoWithMask () {
  if (!selected.value) return

  const sessionId = selected.value.data.id
  const name = selected.value.data.name || 'history'

  try {
    // 这里的路径要和后端保持一致
    // 后端是：@router.get("/api/history/{session_id}/exportVideo")
    const url = `${API_BASE}/history/${sessionId}/exportVideo`
    // 如果你后端写的是 export_video，改成：
    // const url = `${API_BASE}/history/${sessionId}/export_video`

    const res = await axios.get(url, {
      responseType: 'blob'
    })

    const blob = res.data
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = `${name}_mask.mp4`
    a.click()
    URL.revokeObjectURL(blobUrl)
  } catch (err) {
    console.error('downloadVideoWithMask failed', err)
    window.alert('导出失败，请检查后端日志')
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
  --bg: #0b1224;
  --panel: rgba(15, 23, 42, 0.78);
  --panel-strong: rgba(24, 33, 54, 0.92);
  --border: rgba(148, 163, 184, 0.18);
  --primary: #22d3ee;
  --primary-strong: #2563eb;
  --text: #e5e7eb;
  --muted: #94a3b8;
  background:
    radial-gradient(120% 140% at 15% 20%, rgba(56, 189, 248, 0.12), transparent 40%),
    radial-gradient(100% 120% at 85% 0%, rgba(14, 165, 233, 0.12), transparent 38%),
    linear-gradient(135deg, #0f172a 0%, #0b1224 48%, #0f172a 100%);
  color: var(--text);
  font-family: 'Poppins', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.sidebar {
  background: linear-gradient(180deg, rgba(30, 60, 114, 0.88), rgba(42, 82, 152, 0.92));
  color: #f8fafc;
  overflow: auto;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.04), 0 18px 38px -24px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
}

.main {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 顶部工具条 */
.topbar {
  background: var(--panel);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--border);
  box-shadow: 0 18px 40px -26px rgba(34, 211, 238, 0.6), 0 10px 24px -20px rgba(15, 23, 42, 0.8);
}

.title h2 {
  margin: 0;
  font-size: 18px;
  color: #f8fafc;
  letter-spacing: 0.01em;
}

.title p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 14px;
  border: 1px solid rgba(34, 211, 238, 0.5);
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary-strong), var(--primary));
  color: #e8f4ff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
  transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease, background 0.2s ease;
  box-shadow: 0 12px 30px -20px rgba(14, 165, 233, 0.9), inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 35px -22px rgba(34, 211, 238, 0.95), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  filter: brightness(1.04);
}

.btn:active {
  transform: translateY(0);
  filter: brightness(0.96);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
  box-shadow: none;
  background: linear-gradient(135deg, #1f2937, #111827);
  border-color: rgba(148, 163, 184, 0.32);
  color: #94a3b8;
}

.actions select.btn {
  appearance: none;
  padding-right: 36px;
  background:
    linear-gradient(135deg, var(--primary-strong), var(--primary)),
    linear-gradient(45deg, transparent 50%, rgba(232, 244, 255, 0.9) 50%),
    linear-gradient(135deg, rgba(232, 244, 255, 0.9) 50%, transparent 50%);
  background-position: center center, calc(100% - 18px) 50%, calc(100% - 12px) 50%;
  background-repeat: no-repeat;
  background-size: cover, 8px 8px, 8px 8px;
}

.actions select.btn option {
  color: #0f172a;
}

/* 中间内容：左视频右图 */
.content {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1.4fr);
  gap: 16px;
  align-items: stretch;
  overflow: hidden;
}

/* 播放器 */
.player-wrap {
  position: relative;
  background: radial-gradient(120% 160% at 30% 30%, rgba(34, 211, 238, 0.08), transparent 58%), #020617;
  border-radius: 12px;
  overflow: hidden;
  min-height: 440px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border);
  box-shadow: 0 16px 46px -32px rgba(34, 211, 238, 0.75), 0 12px 42px -34px rgba(0, 0, 0, 0.9);
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
  color: rgba(226, 232, 240, 0.8);
  font-size: 14px;
  letter-spacing: 0.01em;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.78), rgba(2, 6, 23, 0.82));
}

.hud {
  position: absolute;
  right: 10px;
  top: 10px;
  background: rgba(15, 23, 42, 0.62);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 12px;
  display: grid;
  gap: 4px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  backdrop-filter: blur(6px);
  box-shadow: 0 10px 28px -20px rgba(34, 211, 238, 0.7);
}

/* 底部进度条 */
.progress {
  background: var(--panel-strong);
  border-radius: 12px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  box-shadow: 0 16px 36px -28px rgba(34, 211, 238, 0.58);
}

.progress input[type='range'] {
  width: 100%;
  appearance: none;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.22), rgba(37, 99, 235, 0.2));
  border: 1px solid var(--border);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.35);
}

.progress input[type='range']::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), #38bdf8);
  border: 1px solid #fff;
  box-shadow: 0 6px 16px -8px rgba(56, 189, 248, 0.9);
}

.progress input[type='range']::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), #38bdf8);
  border: 1px solid #fff;
  box-shadow: 0 6px 16px -8px rgba(56, 189, 248, 0.9);
}

.ticks {
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 12px;
  margin-top: 6px;
  letter-spacing: 0.01em;
}

/* 右边折线图面板 */
.panel {
  background: var(--panel);
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  box-shadow: 0 18px 48px -32px rgba(34, 211, 238, 0.55), 0 8px 28px -28px rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  color: var(--text);
}

.chart-panel {
  min-height: 440px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  color: #e2e8f0;
  letter-spacing: 0.01em;
}

.panel-legend {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #dbeafe;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

.legend-item.water .dot {
  background: #38bdf8;
  box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.2);
}

.legend-item.risk .dot {
  background: #fbbf24;
  box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.2);
}

/* ECharts 容器 */
.chart {
  width: 100%;
  flex: 1;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.82), rgba(10, 12, 29, 0.92));
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
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
