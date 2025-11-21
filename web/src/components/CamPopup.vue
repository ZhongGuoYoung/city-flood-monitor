<template>
  <div class="cam-popup" :class="{ wide: chartVisible }">
    <!-- 两列主容器：左=头部+播放器，右=参数面板+图表 -->
    <div class="cp-main" :class="{ 'with-chart': chartVisible }">
      <!-- 左列：cp-header + 播放器 -->
      <div class="left-col">
        <div class="cp-header">
          <div class="cp-left">
            <img :src="camSvgUrl" class="cp-icon" alt="" />
            <div class="cp-titles">
              <span class="cp-title">{{ info.value?.name }}</span>
              <span class="cp-badges">
                <span
                  v-if="sourceType === 'mp4' || sourceType === 'mjpeg' || sourceType === 'hls'"
                  class="badge live"
                >
                  <span class="dot"></span>Live
                </span>
                <span v-else-if="sourceType === 'snapshot'" class="badge">Snapshot</span>
                <span v-else class="badge muted">Offline</span>
              </span>
            </div>
          </div>
          <div class="cp-right">
            <button class="primary-btn" @click="toggleChart">
              {{ chartVisible ? '停止识别' : '开始识别' }}
            </button>
            <span class="cp-time">{{ now.toLocaleString() }}</span>
            <div class="cp-actions">
              <button class="icon-btn" @click="refresh" title="刷新">⟲</button>
              <button
                class="icon-btn"
                @click="toggleMute"
                :disabled="sourceType !== 'mp4'"
                :title="muted ? '取消静音' : '静音'"
              >
                {{ muted ? '🔇' : '🔊' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 播放器（保持原尺寸不变） -->
        <div class="player" ref="playerRef">
          <div v-if="loading" class="skeleton"></div>

          <video
            v-if="sourceType === 'mp4'"
            ref="videoRef"
            :src="effectiveSrc"
            controls
            playsinline
            :muted="muted"
            preload="metadata"
            crossOrigin="anonymous"
            @loadeddata="onLoaded"
            @error="onError"
            @ended="onVideoEnded"
          />
          <img
            v-else-if="sourceType === 'mjpeg'"
            :src="effectiveSrc"
            :alt="info.value?.name"
            @load="onLoaded"
            @error="onError"
          />
          <img
            v-else-if="sourceType === 'snapshot'"
            :src="effectiveSrc"
            :alt="info.value?.name"
            @load="onLoaded"
            @error="onError"
          />
          <div
            v-else-if="sourceType === 'hls'"
            ref="hlsContainerRef"
            id="ezviz-hls-player"
            class="hls-player-container"
          ></div>     

          <div v-else class="cp-tip">暂无视频或图片</div>

          <div v-if="error && !loading" class="cp-error">
            加载失败
            <button class="retry-btn" @click="refresh">重试</button>
          </div>

          <canvas
            v-if="sourceType === 'mp4'|| sourceType === 'hls'"
            ref="overlayRef"
            class="overlay-canvas"
          ></canvas>          
        </div>
      </div>

      <!-- 右列：参数面板 + 图表 -->
      <el-card v-if="chartVisible" class="chart-card" shadow="hover">
        <!-- 顶部标题 -->
        <div class="chart-header-row">
          <span class="chart-title">识别结果趋势</span>
          <div class="chart-tools">
          <span class="axis-notes">Y1: 淹没范围(%) | Y2: 风险等级</span>
          <button class="mini-btn" @click="exportWord">导出数据</button>
          </div>
        </div>

        <!-- 参数调节面板（专业版） -->
        <div class="cp-advanced">
          <div class="cp-params-left">
            <div class="field">
              <label>输出频率 FPS</label>
              <div class="field-row">
                <input
                  type="range"
                  min="1"
                  max="10"
                  v-model.number="wsParams.fps"
                />
                <span class="field-value">{{ wsParams.fps }} / 秒</span>
              </div>
            </div>

            <div class="field">
              <label>掩膜发送频率</label>
              <select v-model.number="wsParams.send_mask_every">
                <option :value="0">关闭</option>
                <option :value="1">每帧发送</option>
                <option :value="2">每 2 帧</option>
                <option :value="5">每 5 帧</option>
                <option :value="10">每 10 帧</option>
              </select>
              <p class="field-hint">频率越低，带掩膜的数据量越少。</p>
            </div>

            <div class="field inline">
              <div>
                <label>水体输入尺寸</label>
                <input
                  type="number"
                  min="64"
                  step="32"
                  v-model.number="wsParams.imgsz_water"
                />
              </div>
              <div>
                <label>风险输入尺寸</label>
                <input
                  type="number"
                  min="64"
                  step="32"
                  v-model.number="wsParams.imgsz_risk"
                />
              </div>
            </div>
          </div>

          <div class="cp-params-right">
            <div class="field small">
              <label>水体 conf</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                v-model.number="wsParams.conf_water"
              />
            </div>
            <div class="field small">
              <label>水体 IoU</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                v-model.number="wsParams.iou_water"
              />
            </div>

            <div class="field small">
              <label>风险 conf</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                v-model.number="wsParams.conf_risk"
              />
            </div>
            <div class="field small">
              <label>风险 IoU</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                v-model.number="wsParams.iou_risk"
              />
            </div>

            <div class="field-footer">
              <button
                class="apply-btn"
                :disabled="!usingBackend"
                @click="applyParamsToBackend"
              >
                应用到后端
              </button>
              <p class="runtime-hint" v-if="usingBackend">
                当前后端生效：
                <span>fps={{ runtimeParams.fps ?? wsParams.fps }}</span>
                <span>水体 conf={{ (runtimeParams.conf_water ?? wsParams.conf_water).toFixed(2) }}</span>
                <span>风险 conf={{ (runtimeParams.conf_risk ?? wsParams.conf_risk).toFixed(2) }}</span>
              </p>
              <p class="runtime-hint warn" v-else>
                未连接后端，正在使用本地模拟数据。
              </p>
            </div>
          </div>
        </div>

        <!-- 折线图 -->
        <div ref="chartRef" class="echart"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onBeforeUnmount, toRefs, nextTick ,watch} from 'vue'
import camSvgUrl from '@/assets/image/摄像头.svg?url'
import * as echarts from 'echarts'
import { ElCard } from 'element-plus'
import axios from 'axios'
import { API_BASE } from '@/lib/api'
import HlsPlayer from '@ezuikit/player-hls'


// HLS 播放相关
const hlsContainerRef = ref(null)  // HlsPlayer 挂载的 DOM 容器
let hlsPlayer = null               // HlsPlayer 实例
const localHlsUrl = ref('')        // 本地缓存的 HLS 地址（通过 deviceSerial 换出来）
const HLS_CONTAINER_ID = 'ezviz-hls-player'

// ========== 后端接口地址 ==========
const WS_URL = 'ws://localhost:9000/ws'
let ws = null

// ========== 工具函数 ==========
function clampPct (v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return 0
  const pct = n <= 1 ? n * 100 : n
  return Math.max(0, Math.min(100, Math.round(pct)))
}

function labelFromTs (ts) {
  // 用后端给的 ts（毫秒）转时间标签；没有就用当前时间
  const d = new Date(Number(ts) || Date.now())
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${h}:${m}:${s}`
}

function toMMSS (sec) {
  const s = Math.max(0, Math.floor(sec || 0))
  const m = String(Math.floor(s / 60)).padStart(2, '0')
  const r = String(s % 60).padStart(2, '0')
  return `${m}:${r}`
}

// ========== Props ==========
const props = defineProps({
  info: { type: Object, required: true },
  notifyResize: { type: Function, required: false }
})

const { info } = toRefs(props)

watch(
  () => info.value,
  (val) => {
    // 切换摄像头：重置 HLS 播放器
    localHlsUrl.value = ''
    destroyHlsPlayer()

    if (val && val.deviceSerial) {
      // 预先去后端把 HLS 地址换出来
      fetchHlsUrlIfNeeded()
    }
  },
  { immediate: true }
)


// ========== 时间状态 ==========
const state = reactive({ now: new Date(), timer: null })
onMounted(() => {
  state.timer = setInterval(() => { state.now = new Date() }, 1000)
})
onBeforeUnmount(() => {
  if (state.timer) clearInterval(state.timer)
})
const { now } = toRefs(state)

// ========== 播放器状态 ==========
const muted = ref(true)
const loading = ref(true)
const error = ref(false)
const videoRef = ref(null)
const playerRef = ref(null)
const overlayRef = ref(null)

// ========== 图表显示与数据 ==========
const chartVisible = ref(false)
const chartRef = ref(null)
let chart = null
let chartTimer = null
let tickCount = 0
const usingBackend = ref(false)

const xLabels = []       // 横轴
const seriesPct = []     // 淹没范围（%）
const seriesLevel = []   // 风险等级 0~5

// 识别结果导出
const exportRows = [] // { ts, level, percent }

// 后端参数（前端侧可调）
const wsParams = reactive({
  fps: 5,
  conf_water: 0.7,
  iou_water: 0.45,
  conf_risk: 0.7,
  iou_risk: 0.45,
  send_mask_every: 1,
  imgsz_water: 512,
  imgsz_risk: 512
})

// 后端实际生效参数（从 tick.params 或 ack 里回显）
const runtimeParams = ref({})

// ========== 计算属性：视频源 ==========
const sourceType = computed(() => {
  const s = (info.value && info.value.streams) || {}
  if (localHlsUrl.value || s.hls) return 'hls'
  if (s.mp4) return 'mp4'
  if (s.mjpeg) return 'mjpeg'
  if (s.snapshot) return 'snapshot'
  return ''
})

const effectiveSrc = computed(() => {
  const s = (info.value && info.value.streams) || {}
  if (sourceType.value === 'hls') {
    return localHlsUrl.value || s.hls || ''
  }
  return s.mp4 || s.mjpeg || s.snapshot || ''
})

watch(
  () => ({ type: sourceType.value, url: effectiveSrc.value }),
  async ({ type, url }) => {
    if (type === 'hls' && url) {
      await nextTick()
      createHlsPlayer()
      loading.value = false     // HLS 准备好了，取消骨架屏
      error.value = false
    } else {
      destroyHlsPlayer()
    }
  },
  { immediate: true }
)

// ========== 播放器相关 ==========
function refresh () {
  loading.value = true
  error.value = false
  const u = effectiveSrc.value
  if (u && sourceType.value !== 'mp4') {
    const n = u.split('?')[0] + '?t=' + Date.now()
    const streams = Object.assign({}, info.value?.streams || {}, { [sourceType.value]: n })
    if (info.value) info.value.streams = streams
  }
}

async function onLoaded () {
  loading.value = false
  error.value = false
  await nextTick()
  resizeOverlay()
}


function onError () {
  loading.value = false
  error.value = true
}

function onVideoEnded () {
  console.log('[VIDEO] ended')
  if (usingBackend.value) {
    stopBackend()   // 里面会发 {type:'stop'} 然后关 ws
  }
}


function toggleMute () {
  muted.value = !muted.value
}

function currentVideoLabel () {
  if (sourceType.value === 'mp4' && videoRef.value) {
    return toMMSS(videoRef.value.currentTime || 0)
  }
  // 非 mp4 源：自己累加时间标签
  tickCount += 1
  return toMMSS(tickCount)
}

// ========== 用 deviceSerial 换 HLS URL ==========
async function fetchHlsUrlIfNeeded () {
  const cam = info.value
  if (!cam) return
  if (!cam.deviceSerial) return   // 没有 deviceSerial 的直接跳过
  if (localHlsUrl.value) return   // 已经拿过了

  try {
    const res = await axios.get(`${API_BASE}/ezviz/hls-url`, {
      params: {
        deviceSerial: cam.deviceSerial,
        channelNo: cam.channelNo || 1
      }
    })
    const url = res.data.url
    if (!url) {
      console.warn('[EZVIZ] 未返回 HLS 地址', res.data)
      return
    }
    localHlsUrl.value = url
    console.log('[EZVIZ] HLS URL =', url)
  } catch (e) {
    console.error('[EZVIZ] 获取 HLS 地址失败', e)
  }
}


function createHlsPlayer () {
  console.log('[HLS] createHlsPlayer, type=', sourceType.value, 'url=', effectiveSrc.value)
  if (sourceType.value !== 'hls') return
  if (!effectiveSrc.value) {
    console.warn('[HLS] no effectiveSrc')
    return
  }

  // 确保 DOM 在
  const el = document.getElementById(HLS_CONTAINER_ID)
  if (!el) {
    console.warn('[EZVIZ] HLS container not found')
    return
  }

  // 先销毁旧实例
  if (hlsPlayer && typeof hlsPlayer.destroy === 'function') {
    try { hlsPlayer.destroy() } catch (e) { console.warn(e) }
    hlsPlayer = null
  }

  hlsPlayer = new HlsPlayer({
    id: HLS_CONTAINER_ID,        //必须是字符串 id
    url: effectiveSrc.value,
    staticPath: '/decoder/',
    autoplay: true,
    isLive: true,
    width: 800,
    height: 500,
    loggerOptions: {
      name: 'HLS',
      level: 'DEBUG',   // 默认 INFO，改成 DEBUG 方便看错误
      showTime: true
    }
  })
  
  loading.value = false
  error.value = false

  // ⭐ 强制启动播放（有些环境自动播放会被策略挡住）
  setTimeout(() => {
    if (hlsPlayer && typeof hlsPlayer.play === 'function') {
      hlsPlayer.play().catch(err => {
        console.error('[HLS] play error:', err)
      })
    }
  }, 300)
}


function destroyHlsPlayer () {
  if (hlsPlayer && typeof hlsPlayer.destroy === 'function') {
    try { hlsPlayer.destroy() } catch (e) { console.warn(e) }
  }
  hlsPlayer = null
}

// ========== ECharts 初始化 ==========
function initChart () {
  if (!chartRef.value) return
  chart = chart || echarts.init(chartRef.value)
  chart.setOption({
    backgroundColor: '#0d1726',
    tooltip: { trigger: 'axis', textStyle: { fontSize: 15 } },
    legend: {
      data: ['淹没范围(%)', '风险等级'],
      top: 52,
      left: 'center',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#cfe2ff', fontSize: 14 }
    },
    grid: { left: 56, right: 56, top: 90, bottom: 40 },
    xAxis: {
      type: 'category',
      data: xLabels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,.3)' } },
      axisLabel: { color: '#cfe2ff', fontSize: 12, margin: 10 }
    },
    yAxis: [
      {
        type: 'value', name: '淹没范围(%)', min: 0, max: 100,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,.3)' } },
        axisLabel: { color: '#cfe2ff' },
        nameTextStyle: { color: '#cfe2ff', fontSize: 14, padding: [0, 0, 6, 0] },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,.08)' } }
      },
      {
        type: 'value', name: '风险等级', min: 0, max: 5, interval: 1,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,.3)' } },
        axisLabel: { color: '#cfe2ff' },
        nameTextStyle: { color: '#cfe2ff', fontSize: 14, padding: [0, 0, 6, 0] },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '淹没范围(%)',
        type: 'line',
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        data: seriesPct,
        lineStyle: { width: 2 }
      },
      {
        name: '风险等级',
        type: 'line',
        yAxisIndex: 1,
        step: 'end',
        showSymbol: false,
        data: seriesLevel,
        lineStyle: { width: 2 }
      }
    ]
  })
  window.addEventListener('resize', resizeChart)
}

function resizeChart () {
  if (chart) chart.resize()
  resizeOverlay()
  props.notifyResize && props.notifyResize()
}


function disposeChart () {
  window.removeEventListener('resize', resizeChart)
  if (chart) { chart.dispose(); chart = null }
}

// 新增一个点
function pushPoint (level, percent, ts) {
  const label = ts ? labelFromTs(ts) : currentVideoLabel()
  xLabels.push(label)
  seriesLevel.push(level)
  seriesPct.push(percent)
  
  exportRows.push({
    ts: ts ?? null,   // 这里存原始毫秒
    level,
    percent
  })

  const maxPoints = 120
  if (xLabels.length > maxPoints) {
    xLabels.shift()
    seriesLevel.shift()
    seriesPct.shift()
  }

  if (chart) {
    chart.setOption({
      xAxis: { data: xLabels },
      series: [{ data: seriesPct }, { data: seriesLevel }]
    })
  }
}

// ========== 参数清洗（夹在合法范围内） ==========
function sanitizeParams (src) {
  const clamp01 = v => Math.max(0, Math.min(1, Number(v) || 0))
  const fps = Math.max(1, Math.min(30, Number(src.fps) || 5))
  const imgsz_water = Math.max(64, Number(src.imgsz_water) || 640)
  const imgsz_risk = Math.max(64, Number(src.imgsz_risk) || 640)
  const send_mask_every = Math.max(0, Math.floor(Number(src.send_mask_every) || 0))

  return {
    fps,
    conf_water: clamp01(src.conf_water),
    iou_water: clamp01(src.iou_water),
    conf_risk: clamp01(src.conf_risk),
    iou_risk: clamp01(src.iou_risk),
    send_mask_every,
    imgsz_water,
    imgsz_risk
  }
}

// ========== WS 逻辑，适配你现在的接口 ==========

// 连接并发送首包：{ url, fps, conf_water, iou_water, conf_risk, iou_risk, send_mask_every, imgsz_water, imgsz_risk }
function startBackend () {
  if (!WS_URL) return false
  try {
    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.log('[WS] connected')
      const cam = info.value || {}
      const payload = {
        url: effectiveSrc.value || '',
        ...sanitizeParams(wsParams),

        // ====用于后端建任务/存库 ====
        mode: 'detect',                 //标明是一次识别任务
        save_to_db: true,               //后端看到true就建detect_session并写detect_tick
        camera_id: cam.camId || cam.id || '',
        camera_name: cam.name || '',
        location: cam.location || '',
        source_type: sourceType.value,   // 'hls' | 'mp4' | 'mjpeg' | 'snapshot'
        record_video: sourceType.value === 'hls' || sourceType.value === 'mjpeg'
      }
      ws.send(JSON.stringify(payload))
      console.log('[WS] sent start payload:', payload)
    }

    ws.onmessage = (ev) => {
      let msg = {}
      try { msg = JSON.parse(ev.data) } catch {''}

      if (msg.params && typeof msg.params === 'object') {
        runtimeParams.value = msg.params
      }

      if (msg.type === 'tick') {
        const pct = clampPct(msg.pct)
        const lvl = Number(msg.level) || 0
        const ts = msg.ts
        pushPoint(lvl, pct, ts)
        updateOverlayFromBackend(msg)

        //      让视频时间跟后端的 ts 对齐（软同步）
        if (sourceType.value === 'mp4' && videoRef.value && typeof ts === 'number') {
          const targetTime = ts / 1000  // 后端 ts 是毫秒
          const cur = videoRef.value.currentTime || 0
          const diff = Math.abs(cur - targetTime)

          // 如果差得有点多（比如超过 0.3 秒），就“纠正”一下
          if (diff > 0.3) {
            videoRef.value.currentTime = targetTime
          }
        }

        return
      }

      

      if (msg.type === 'ack') {
        console.log('[WS] params updated:', msg.updated)
        return
      }

      if (msg.type === 'eof') {
        console.log('[WS] video finished')
        stopRecognition()
        return
      }

      if (msg.type === 'error') {
        console.error('[WS-ERROR]', msg.msg)
        stopRecognition()
        return
      }
    }

    ws.onerror = (e) => {
      console.error('[WS] error:', e)
    }

    ws.onclose = () => {
      console.log('[WS] closed')
      ws = null
    }

    return true
  } catch (e) {
    console.error('WS open error:', e)
    ws = null
    return false
  }
}

function stopBackend () {
  try {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try { ws.send(JSON.stringify({ type: 'stop' })) } catch {''}
      ws.close()
    }
  } catch {''}
  ws = null
}

// 点击“应用到后端”
function applyParamsToBackend () {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn('WS not connected, cannot apply params')
    return
  }
  const payload = sanitizeParams(wsParams)
  ws.send(JSON.stringify({ type: 'set_params', ...payload }))
  console.log('[WS] set_params:', payload)
}

// ========== 识别开始 / 停止 ==========
async function startRecognition () {
  chartVisible.value = true
  await nextTick()

  if (info.value?.deviceSerial) {
    await fetchHlsUrlIfNeeded()
  }

  if (!chart) initChart()
  resizeOverlay() 

  // 清空旧数据
  xLabels.length = 0
  seriesPct.length = 0
  seriesLevel.length = 0
  tickCount = 0
  exportRows.length = 0
  if (chart) {
    chart.setOption({
      xAxis: { data: [] },
      series: [{ data: [] }, { data: [] }]
    })
  }

  // 停掉旧的本地模拟
  if (chartTimer) {
    clearInterval(chartTimer)
    chartTimer = null
  }

  // 优先用后端
  usingBackend.value= startBackend()

  // mp4用 <video> 播放
 if (sourceType.value === 'mp4' && videoRef.value) { 
  try {
    await videoRef.value.play()
  } catch (e) {
    console.warn('[VIDEO] play error:', e)
  }
 }

//  // HLS用 HlsPlayer 播放
//  if (sourceType.value === 'hls') {
//     await nextTick()
//    createHlsPlayer()
//  }

  // 如果后端没配好，退回本地模拟数据
  // if (!usingBackend) {
  //   chartTimer = setInterval(() => {
  //     const lastPct = seriesPct[seriesPct.length - 1] ?? 35
  //     const nextPct = Math.max(0, Math.min(100, Math.round(lastPct + (Math.random() * 16 - 8))))
  //     const nextLevel = Math.max(0, Math.min(5, Math.round(nextPct / 20)))
  //     pushPoint(nextLevel, nextPct)
  //   }, 1000)
  // }

  await nextTick()
  props.notifyResize && props.notifyResize()
}

function stopRecognition () {
  if (chartTimer) {
    clearInterval(chartTimer)
    chartTimer = null
  }
  if (usingBackend.value) stopBackend()
  usingBackend.value = false

  if (sourceType.value === 'mp4' && videoRef.value) {
    try {
      videoRef.value.pause()
      // videoRef.value.currentTime = 0
    } catch {''}
  }

  if (sourceType.value === 'hls') {
    destroyHlsPlayer()
  }
}


function toggleChart () {
  if (chartVisible.value) {
    chartVisible.value = false
    stopRecognition()
    nextTick(() => props.notifyResize && props.notifyResize())
  } else {
    startRecognition()
  }
}

// ========== 叠加层(canvas) 状态与绘制 ==========
const overlayState = reactive({
  waterPolygons: [], // [{ points: [[x,y], ...] }]  归一化坐标
  riskBoxes: []      // [{ x1,y1,x2,y2,level }]      归一化坐标
})

let waterMaskImg = null

// 调整 canvas 尺寸，使其和播放器区域一致
function resizeOverlay () {
  const canvas = overlayRef.value
  const container = playerRef.value
  if (!canvas || !container) return

  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1

  // 物理像素尺寸
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  // CSS 尺寸
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'

  const ctx = canvas.getContext('2d')
  if (ctx) {
    // 让坐标系按“1 个单位 = 1 个 CSS 像素”来画
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  renderOverlay()
}

// 真正画东西的函数（根据 overlayState）
function renderOverlay () {
  const canvas = overlayRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const w = canvas.clientWidth
  const h = canvas.clientHeight
  ctx.clearRect(0, 0, w, h)

  // 0) 画已经「预处理好」的蓝色掩膜（背景是透明的）
  if (waterMaskImg) {
    ctx.drawImage(waterMaskImg, 0, 0, w, h)
  }

  // 1) 风险框（按归一化坐标画）
  if (overlayState.riskBoxes && overlayState.riskBoxes.length) {
    overlayState.riskBoxes.forEach(box => {
      const x1 = box.x1 * w
      const y1 = box.y1 * h
      const x2 = box.x2 * w
      const y2 = box.y2 * h
      const level = box.level ?? 0

      let color = 'rgba(255, 255, 0, 0.9)'
      if (level >= 3) color = 'rgba(255, 69, 0, 0.9)'
      else if (level >= 2) color = 'rgba(255, 140, 0, 0.9)'

      ctx.save()
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

      const label = `L${level}`
      ctx.font = '14px sans-serif'
      const tw = ctx.measureText(label).width + 6
      const th = 18
      ctx.fillStyle = color
      const ly = Math.max(th, y1 + th / 2)
      ctx.fillRect(x1, ly - th, tw, th)
      ctx.fillStyle = '#000'
      ctx.fillText(label, x1 + 3, ly - 4)
      ctx.restore()
    })
  }
}



// 后端 tick 时更新 overlay 数据（后面接真接口就改这里）
function updateOverlayFromBackend (msg) {
  console.log('[overlay-msg]', msg.water, msg.risk)

  // ========== 1) 处理水体掩膜：灰度 -> 透明背景的蓝色图 ==========
  if (msg.water && msg.water.mask_png_b64) {
    const b64 = msg.water.mask_png_b64
    const rawImg = new Image()

    rawImg.onload = () => {
      // 用离屏 canvas 做一次像素级处理
      const off = document.createElement('canvas')
      off.width = rawImg.width
      off.height = rawImg.height
      const octx = off.getContext('2d')
      octx.drawImage(rawImg, 0, 0)

      const imageData = octx.getImageData(0, 0, off.width, off.height)
      const data = imageData.data
      // 阈值：灰度 > threshold 认为是水，其他设为全透明
      const threshold = 10

      for (let i = 0; i < data.length; i += 4) {
        const r = data[i]     // 灰度掩膜，R=G=B
        const g = data[i + 1]
        const b = data[i + 2]

        const gray = (r+g+b)/3// 或 (r+g+b)/3

        if (gray > threshold) {
          // 水域：上蓝色
          data[i] = 0          // R
          data[i + 1] = 180    // G
          data[i + 2] = 255    // B
          // alpha 根据亮度稍微调一下，最多 220
          data[i + 3] = Math.min(220, gray * 1.2)
        } else {
          // 非水域：完全透明，不影响视频
          data[i + 3] = 0
        }
      }

      octx.putImageData(imageData, 0, 0)

      if (!waterMaskImg) {
        waterMaskImg = new Image()
        waterMaskImg.onload = () => {
          renderOverlay()
        }
      }
      // 这张图已经是「透明背景 + 蓝色水域」了
      waterMaskImg.src = off.toDataURL('image/png')
    }

    rawImg.src = 'data:image/png;base64,' + b64
  } else {
    waterMaskImg = null
  }

  // ========== 2) 处理风险框 ==========
  overlayState.riskBoxes = []
  if (msg.risk && msg.risk.det && Array.isArray(msg.risk.det.boxes_norm)) {
    overlayState.riskBoxes = msg.risk.det.boxes_norm.map(b => ({
      x1: b[0],
      y1: b[1],
      x2: b[2],
      y2: b[3],
      level: b[4] ?? msg.level ?? 0
    }))
  }

  // 对于“只更新风险框、掩膜不变”的情况，也要重新画一次
  renderOverlay()
}

async function exportWord () {
  if (!exportRows.length) {
    alert('暂无可导出的识别数据')
    return
  }

  const cam = props.info || {} // 你弹窗的 info 里一般有 id/name/location 等
  const payload = {
    camera: {
      id: cam.camId || cam.id || '',
      name: cam.name || '',
      location: cam.location || ''
    },
    // 根据 sourceType 区分 mp4 vs 监控
    source_type: sourceType.value === 'mp4' ? 'video' : 'live',
    rows: exportRows.map(r => ({
      ts: r.ts,
      level: r.level,
      percent: r.percent
    }))
  }

  try {
    const res = await axios.post(
      `${API_BASE}/exportWord`,       // 后端新建的导出接口
      payload,
      { responseType: 'blob' }
    )

    const blob = new Blob(
      [res.data],
      { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const tsStr = new Date().toISOString().replace(/[:.]/g, '-')
    a.href = url
    a.download = `${cam.name || 'camera'}_识别结果_${tsStr}.docx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
    alert('导出失败，请稍后重试')
  }
}


// 组件卸载时清理
onBeforeUnmount(() => {
  stopRecognition()
  disposeChart()
  destroyHlsPlayer()
})
</script>

<style scoped>
.cam-popup {
  --left-w: 860px;   /* 左侧播放器区域宽 */
  --chart-w: 780px;  /* 右侧折线图+面板宽 */
  --chart-h: 520px;  /* 右侧高度 */
  width: var(--left-w);
  background: radial-gradient(circle at top, #16233a 0, #050b14 52%, #02050a 100%);
  color: #cfe2ff;
  border: 1px solid rgba(111, 195, 255, 0.3);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.55);
}

.cam-popup.wide {
  width: calc(var(--left-w) + 12px + var(--chart-w));
}

/* 主容器两列：左=头部+播放器，右=图表 */
.cp-main {
  display: grid;
  grid-template-columns: 1fr;
}
.cp-main.with-chart {
  grid-template-columns: var(--left-w) var(--chart-w);
  gap: 12px;
}

/* 左列内部：头部 + 播放器 */
.left-col {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
}

/* 头部 */
.cp-header {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(90deg, #08111f, #111d33);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.cp-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.cp-icon {
  width: 22px;
  height: 22px;
  display: block;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.6));
}
.cp-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.cp-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.cp-badges {
  display: flex;
  gap: 6px;
}
.badge {
  font-size: 12px;
  line-height: 1;
  padding: 3px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}
.badge.live {
  background: rgba(44, 189, 108, 0.9);
}
.badge.muted {
  background: rgba(255, 255, 255, 0.12);
  color: #ddd;
}
.badge .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  margin-right: 4px;
  vertical-align: middle;
}

.cp-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cp-time {
  opacity: 0.9;
  font-size: 14px;
}
.cp-actions {
  display: flex;
  gap: 8px;
}

/* 按钮 */
.primary-btn {
  height: 30px;
  padding: 0 14px;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  color: #fff;
  font-size: 14px;
  background: linear-gradient(120deg, #56a0ff, #25d0ff);
  box-shadow: 0 0 12px rgba(86, 160, 255, 0.7);
}
.primary-btn:hover {
  filter: brightness(1.05);
}
.icon-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
}
.icon-btn[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}
.icon-btn:hover {
  background: rgba(255, 255, 255, 0.24);
}

/* 播放器 */
.player {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  margin: 0 12px 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.85);
}

.player video,
.player img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  position: relative;
  z-index: 1;
}
.hls-player-container {
  width: 100%;
  height: 100%;
}
/* 叠加层 canvas：盖在视频上，鼠标事件透传 */
.overlay-canvas {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
}

.overlay-canvas {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
/* 骨架屏 & 错误 */
.skeleton {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #101d30, #13223a, #101d30);
  animation: sk 1.2s infinite;
}
@keyframes sk {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}
.cp-tip {
  color: #ddd;
  text-align: center;
  padding: 40px 0;
}
.cp-error {
  position: absolute;
  inset: auto 0 0 0;
  background: rgba(0, 0, 0, 0.55);
  padding: 8px;
  text-align: center;
}
.retry-btn {
  margin-left: 8px;
}

/* 右侧卡片：参数 + 图表 */
.chart-card {
  background: #0d1726;
  color: #cfe2ff;
  border: 1px solid rgba(111, 195, 255, 0.28);
  height: var(--chart-h);
  display: flex;
  flex-direction: column;
  padding-bottom: 8px;
}
.chart-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px 4px;
  font-size: 13px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.chart-title {
  font-weight: 600;
}
.axis-notes {
  font-size: 12px;
  opacity: 0.9;
}

/* 高级参数面板 */
.cp-advanced {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 8px;
  padding: 6px 10px 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.cp-params-left,
.cp-params-right {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field.inline {
  flex-direction: row;
  gap: 10px;
}
.field.inline > div {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field label {
  font-size: 12px;
  color: #cfe2ff;
  opacity: 0.9;
}
.field-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.field input[type="range"] {
  flex: 1;
}
.field input[type="number"],
.field select {
  height: 26px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(3, 10, 22, 0.9);
  color: #e5f0ff;
  padding: 0 6px;
  font-size: 12px;
}
.field input[type="number"]:focus,
.field select:focus {
  outline: none;
  border-color: rgba(86, 160, 255, 0.9);
}
.field.small {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.field.small label {
  flex: 1;
}
.field.small input {
  width: 70px;
}
.field-value {
  font-size: 12px;
  opacity: 0.9;
}
.field-hint {
  font-size: 11px;
  opacity: 0.75;
}

/* 应用按钮 & 参数回显 */
.field-footer {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.apply-btn {
  align-self: flex-start;
  height: 26px;
  padding: 0 12px;
  border: none;
  border-radius: 13px;
  cursor: pointer;
  color: #fff;
  font-size: 12px;
  background: linear-gradient(120deg, #2bce8f, #25d0ff);
  box-shadow: 0 0 8px rgba(37, 208, 255, 0.7);
}
.apply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
.runtime-hint {
  font-size: 11px;
  opacity: 0.85;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.runtime-hint.warn {
  color: #ffb347;
}

/* ECharts 容器 */
.echart {
  width: 100%;
  flex: 1;
  min-height: 260px;
}

.chart-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-btn {
  border: none;
  border-radius: 12px;
  padding: 2px 10px;
  font-size: 12px;
  cursor: pointer;
  color: #fff;
  background: rgba(86, 160, 255, 0.8);
}
.mini-btn:hover {
  filter: brightness(1.05);
}

</style>
