<template>
  <div class="page-video">
    <!-- 左侧：视频源侧栏 -->
    <aside class="sidebar">
      <CameraSidebarVideo
        v-model:videos="videos"
        :selected="selected && selected.data"
        @select-source="onSelectSource"
      />
    </aside>

    <!-- 右侧：播放器 + 顶部控制 -->
    <main class="main">
      <header class="topbar">
        <div class="title">
          <h2>视频源播放/图片</h2>
          <p v-if="selected">
            已选：{{ selected.data.name }}（{{ selected.data.url }}）
          </p>
          <p v-else>请选择左侧视频源</p>
        </div>

        <div class="actions">
          <button class="btn" @click="reloadList">刷新</button>
          <button v-if="!usingImage" class="btn" :disabled="!playerReady" @click="togglePlay">
            {{ playing ? '暂停' : '播放' }}
          </button>
          <button v-if="!usingImage" class="btn" :disabled="!playerReady" @click="mute = !mute">
            {{ mute ? '取消静音' : '静音' }}
          </button>

          <!-- 识别控制 -->
          <div class="split"></div>
          <label class="opt">抽帧N
            <input type="number" min="1" v-model.number="everyNth" />
          </label>
          <label class="opt">阈值
            <input type="number" min="0" max="1" step="0.05" v-model.number="minConf" />
          </label>
          <button class="btn primary" :disabled="((!usingImage && !playerReady) || !selected)" @click="startInfer">开始识别</button>
          <button class="btn" @click="clearResult">清除结果</button>
        </div>
      </header>

      <section class="player-wrap" :class="{ 'image-mode': usingImage }">
        <!-- 播放器：MP4 走原生、HLS(m3u8) 走 hls.js -->
        <video
          ref="videoEl"
          class="player"
          controls
          playsinline
          v-show="!usingImage"
          :muted="mute"
        ></video>

        <img
          ref="imgEl"
          class="player"
          v-show="usingImage"
          @load="onImageLoad"
          alt="image preview"
        />

        <!-- 叠加层：绘制检测框/水位 -->
        <canvas ref="overlay" class="overlay"></canvas>

        <div v-if="!selected" class="placeholder">
          请选择左侧来源进行播放/查看
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
/* eslint-disable */
import { ref, reactive, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import CameraSidebarVideo from '@/components/CameraSidebarVideo.vue'
import { API_BASE } from '@/lib/api'
/** 左侧列表与当前选中 */
const videos   = ref([])
const selected = ref(null)

/** 播放器状态 */
const videoEl     = ref(null)
const imgEl       = ref(null)  
const overlay     = ref(null)
const hls         = ref(null)
const playerReady = ref(false)
const playing     = ref(false)
const mute        = ref(false)
const usingImage  = ref(false) 
/** 识别参数与结果缓存 */
const everyNth = ref(5)
const minConf  = ref(0.25)
const store = reactive({
  meta: { width: 0, height: 0, fps: 25, duration_ms: 0 },
  frames: [],
  index: new Map(), // key: 100ms 桶的时间戳, val: 帧对象
  imageResult: null,
})

let overlayToken = 0 
let es = null        //SSE 连接
let flvPlayer = null //如果还有flv.js
const buffer = []    // 实时帧缓冲
let synced = false, offsetMs = 0

function resetForNewSource() {
  //断开实时通道播放器
  if (es) { es.close(); es = null }
  // if (hls) { hls.destroy(); hls = null }
  if (flvPlayer) { flvPlayer.destroy(); flvPlayer = null }
  if (videoEl.value) {
    try { videoEl.value.pause() } catch {}
    videoEl.value.removeAttribute('src')
    videoEl.value.load()
  }

  //清空缓存与索引
  buffer.length = 0
  synced = false
  offsetMs = 0
  store.frames = []
  store.index.clear()
  store.imageResult = null        // 图片模式下的结果也清掉
  playing.value = false
  //提升overlayToken，废弃所有旧回调
  overlayToken++

  //擦干净画布
  const cv = overlay.value
  if (cv) {
    const ctx = cv.getContext('2d')
    ctx.clearRect(0, 0, cv.width, cv.height)
  }
}

/** 选中左侧视频源 */
function onSelectSource(payload){
  resetForNewSource()
  selected.value = payload
  usingImage.value = (payload?.type === 'image' || payload?.data?.kind === 'image')
  initPlayer()
  if (usingImage.value) {
    //到新图片：清空上一张的掩膜/结果，并擦画布
    store.imageResult = null
    const cv = overlay.value
    if (cv) {
      const ctx = cv.getContext('2d')
      ctx.clearRect(0, 0, cv.width, cv.height)
    }
  }
  if (usingImage.value) overlayToken++
  
}

function baseEl(){ return usingImage.value ? imgEl.value : videoEl.value }
// 适配 overlay 尺寸
function fitOverlayToPlayer(){
  const el = baseEl(), cv = overlay.value
  if (!el || !cv) return
  const rect = el.getBoundingClientRect()
  const dpr  = Math.max(1, window.devicePixelRatio || 1)
  cv.style.width  = rect.width + 'px'
  cv.style.height = rect.height + 'px'
  cv.width  = Math.round(rect.width  * dpr)
  cv.height = Math.round(rect.height * dpr)
}

/** 刷新列表（占位） */
function reloadList(){
  videos.value = [...videos.value]
}

/** 初始化/切换播放源 */
async function initPlayer(){
  playerReady.value = false
  playing.value = false
  const el = videoEl.value
  if (!el) return

  // 清理旧 hls
  if (hls.value) { hls.value.destroy(); hls.value = null }

  // 清空旧源
  el.pause()
  el.removeAttribute('src')
  while (el.firstChild) el.removeChild(el.firstChild)
  el.load()

  // 清空 overlay
  fitOverlayToPlayer()
  drawOverlay()

  const v = videoEl.value
  if (v){ if (hls.value){ hls.value.destroy(); hls.value=null } v.pause(); v.removeAttribute('src'); v.load() }
  fitOverlayToPlayer(); drawOverlay()

  if (!selected.value) return
  const data = selected.value.data || {}

   if (usingImage.value){
    //先清空上一张的结果并擦画布
   store.imageResult = null
   const cv = overlay.value
   if (cv) {
     const ctx = cv.getContext('2d')
     ctx.clearRect(0, 0, cv.width, cv.height)
   }
   // 图片：直接显示
    if (!data.url) return
    imgEl.value.src = data.url
    // onImageLoad 里会 fit + draw
    overlayToken++ 
    return
  }

  const url  = data.url
  if (!url) return

  // HLS 分支
  const isM3U8 = /\.m3u8(\?.*)?$/i.test(url)
  if (isM3U8) {
    try {
      await ensureHlsLoaded()
      const H = window.Hls
      if (H.isSupported()) {
        hls.value = new H()
        hls.value.loadSource(url)
        hls.value.attachMedia(el)
        hls.value.on(H.Events.MANIFEST_PARSED, async () => {
          fitOverlayToVideo()
          try { await el.play() } catch(_) {}
          playerReady.value = true
          playing.value = !el.paused
        })
        hls.value.on(H.Events.ERROR, (ev, data) => {
          console.warn('HLS 错误：', data)
        })
      } else if (el.canPlayType('application/vnd.apple.mpegurl')) {
        el.src = url
        el.addEventListener('loadedmetadata', async () => {
          fitOverlayToVideo()
          try { await el.play() } catch(_) {}
          playerReady.value = true
          playing.value = !el.paused
        }, { once:true })
      } else {
        console.error('此环境不支持 HLS 播放')
      }
    } catch (e) {
      console.error('加载 hls.js 失败', e)
    }
    return
  }

  // 本地文件（blob）
  if (data.local) {
    const mime = data.fileType || 'video/mp4'
    const source = document.createElement('source')
    source.src  = url
    source.type = mime
    el.appendChild(source)

    el.preload = 'metadata'
    el.load()
    try { await waitMeta(el) } catch (e) { console.error(e); return }

    fitOverlayToPlayer()
    playerReady.value = true
    playing.value = false 
    return
  }

  const isMJPEG = /(\/video(\?.*)?$|action=stream)/i.test(url)
if (isMJPEG) {
  // 用 <img> 显示（避免 <video> 的兼容问题）
  mjpegImgEl.src = url
  mjpegImgEl.onload = () => { fitOverlayToElement(mjpegImgEl); playerReady.value = true }
  // 注意：不要把这张跨域图片画进 canvas，否则会“tainted canvas”报错
  return
}

  // 普通直链 URL
  el.src = url
  el.load()
  el.addEventListener('loadedmetadata', async () => {
    fitOverlayToVideo()
    try { await el.play() } catch(_) {}
    playerReady.value = true
    playing.value = !el.paused
  }, { once:true })
}

//图片载入后适配尺寸&绘制
function onImageLoad(){
  fitOverlayToPlayer()
  drawOverlay() // 如果已有人为的识别结果，会立刻显示
}

function waitMeta(el){
  return new Promise((res, rej) => {
    const ok = () => { cleanup(); res() }
    const er = () => { cleanup(); rej(new Error('媒体加载失败')) }
    const cleanup = () => {
      el.removeEventListener('loadedmetadata', ok)
      el.removeEventListener('error', er)
    }
    el.addEventListener('loadedmetadata', ok, { once:true })
    el.addEventListener('error', er, { once:true })
  })
}

/** 上传并获取后端推理 JSON，建立索引 */
async function startInfer(){
  if (!selected.value) return
  const data = selected.value.data || {}
  const fd = new FormData()
  if (data.fileBlob) {
    fd.append('file', data.fileBlob, data.fileName || 'video.mp4')
  } else if (data.url) {
    fd.append('video_url', data.url) // 仅当后端可访问
  } else {
    return
  }
  if (usingImage.value){
    //图片：POST /api/infer/image
    if (!data.imgBlob){ console.warn('缺少图片文件'); return }
    const fd = new FormData()
    fd.append('file', data.imgBlob, data.imgName || 'image.jpg')
    fd.append('min_conf', String(minConf.value))

    const resp = await fetch(`${API_BASE}/infer/image`, { method:'POST', body: fd })
    if (!resp.ok){ console.error('后端错误', resp.status); return }
    const json = await resp.json()

    // 收下结果到一个单独的槽（图片不涉及时间轴）
    store.imageResult = {
      meta: { width: json?.image_meta?.width || imgEl.value?.naturalWidth || 0,
              height:json?.image_meta?.height|| imgEl.value?.naturalHeight|| 0 },
      objects: json?.objects || [],
      mask_png: json?.mask_png || null
    }
    fitOverlayToPlayer()
    drawOverlay()
    return
  }

  fd.append('every_nth', String(Math.max(1, everyNth.value|0)))
  fd.append('min_conf',  String(minConf.value))

  const resp = await fetch(`${API_BASE}/infer/video`, {
    method: 'POST',
    body: fd,                    
  })

  if (!resp.ok) { console.error('后端错误', resp.status); return }
  const json = await resp.json()
  buildResultIndex(json)
  fitOverlayToPlayer()
  drawOverlay()
}

function buildResultIndex(json){
  const el = videoEl.value
  store.meta.width  = json?.video_meta?.width  || el?.videoWidth  || 0
  store.meta.height = json?.video_meta?.height || el?.videoHeight || 0
  store.meta.fps    = json?.video_meta?.fps    || 25
  store.meta.duration_ms = json?.video_meta?.duration_ms || 0

  store.frames = json?.frames || []
  store.index.clear()
  for (const f of store.frames){
    store.index.set(bucketKey(f.t_ms), f) // 100ms 桶
  }
}



function clearResult(){
  store.frames = []
  store.index.clear()
  store.imageResult = null
  overlayToken++
  const cv = overlay.value
  if (cv) {
    const ctx = cv.getContext('2d')
    ctx.clearRect(0, 0, cv.width, cv.height)
  }
 
}

/** 播放/暂停 */
async function togglePlay() {
  if (usingImage.value) return
  if (!playing.value) {
    await videoEl.value.play()
    playing.value = true
  } else {
    videoEl.value.pause()
    playing.value = false
  }
}


/** 按需加载 hls.js（CDN） */
function ensureHlsLoaded(){
  if (window.Hls) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest'
    s.onload = () => resolve()
    s.onerror = (e) => reject(e)
    document.head.appendChild(s)
  })
}

/** ===== 叠加绘制：DPR + letterbox 适配 ===== */
function fitOverlayToVideo(){
  const el = videoEl.value, cv = overlay.value
  if (!el || !cv) return
  const rect = el.getBoundingClientRect()
  const dpr  = Math.max(1, window.devicePixelRatio || 1)
  cv.style.width  = rect.width + 'px'
  cv.style.height = rect.height + 'px'
  cv.width  = Math.round(rect.width  * dpr)
  cv.height = Math.round(rect.height * dpr)
}

function computeLetterbox(){
  const el = baseEl(), cv = overlay.value
  const vw = usingImage.value ? (el?.naturalWidth || 0) : (el?.videoWidth || 0)
  const vh = usingImage.value ? (el?.naturalHeight|| 0) : (el?.videoHeight|| 0)
  const cw = cv?.width  || 0, ch = cv?.height || 0
  if (!vw || !vh || !cw || !ch) return { sx:1, sy:1, ox:0, oy:0 }
  const videoAR = vw/vh, canvasAR=cw/ch
  let dispW, dispH, ox=0, oy=0
  if (videoAR > canvasAR){ dispW=cw; dispH=Math.round(cw/videoAR); oy=Math.round((ch-dispH)/2) }
  else { dispH=ch; dispW=Math.round(ch*videoAR); ox=Math.round((cw-dispW)/2) }
  return { sx:dispW/vw, sy:dispH/vh, ox, oy }
}

function bucketKey(t_ms){
  return Math.round((t_ms || 0) / 100) * 100 // 100ms 桶
}

function nearestFrame(t_ms){
  const step = 100
  for (let d=0; d<=500; d+=step){
    const k1 = bucketKey(t_ms + d)
    if (store.index.has(k1)) return store.index.get(k1)
    if (d>0){
      const k2 = bucketKey(t_ms - d)
      if (store.index.has(k2)) return store.index.get(k2)
    }
  }
  return null
}

function drawOverlay(){
  const el = videoEl.value, cv = overlay.value
  if (!cv) return
  const ctx = cv.getContext('2d')
  ctx.clearRect(0,0,cv.width,cv.height)

  const { sx, sy, ox, oy } = computeLetterbox()

  // 图片模式：优先绘制并返回
  if (usingImage.value){
    const r = store.imageResult
    if (!r) return
    if (r.mask_png){
      const myToken = overlayToken   //取当前版本号
      const img = new Image()
      img.onload = () => {
        if (myToken !== overlayToken) return
        const dispW = Math.round(r.meta.width  * sx)
        const dispH = Math.round(r.meta.height * sy)
        ctx.drawImage(img, 0,0, r.meta.width, r.meta.height, ox, oy, dispW, dispH)
        drawObjects(ctx, r.objects, sx, sy, ox, oy)
      }
      img.src = 'data:image/png;base64,' + r.mask_png
      return
    }
    drawObjects(ctx, r.objects, sx, sy, ox, oy)
    return
  }

  // 视频模式：根据时间轴匹配帧
  if (!el) return
  const t_ms = Math.round(el.currentTime * 1000)
  const f = store.index.get(bucketKey(t_ms)) || nearestFrame(t_ms)
  if (!f) return

  // ① 栅格掩膜（整帧 PNG）
  if (f.mask_png){
    const img = new Image()
    img.onload = () => {
      const dispW = Math.round((store.meta.width ) * sx)
      const dispH = Math.round((store.meta.height) * sy)
      ctx.drawImage(img, 0, 0, store.meta.width, store.meta.height, ox, oy, dispW, dispH)
      drawObjects(ctx, f.objects, sx, sy, ox, oy)
    }
    img.src = 'data:image/png;base64,' + f.mask_png
    return
  }

  // ② 退回：多边形/框
  drawObjects(ctx, f.objects, sx, sy, ox, oy)
}

function drawObjects(ctx, objects, sx, sy, ox, oy){
  const dpr = Math.max(1, window.devicePixelRatio || 1)
  for (const o of objects || []) {
    if (o.poly && o.poly.length >= 3) {
      ctx.save(); ctx.beginPath()
      for (let i = 0; i < o.poly.length; i++) {
        const px = Math.round(ox + o.poly[i][0] * sx)
        const py = Math.round(oy + o.poly[i][1] * sy)
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py)
      }
      ctx.closePath()
      ctx.globalAlpha = 0.35; ctx.fillStyle = colorForClass(o.cls); ctx.fill()
      ctx.globalAlpha = 1.0;  ctx.lineWidth = 2*dpr; ctx.strokeStyle = colorForClass(o.cls); ctx.stroke()
      ctx.restore()
      continue
    }
    if (o.bbox){
      const [x1,y1,x2,y2] = o.bbox
      const rx = x => Math.round(ox + x * sx)
      const ry = y => Math.round(oy + y * sy)
      ctx.lineWidth = 2*dpr; ctx.strokeStyle = 'lime'
      ctx.strokeRect(rx(x1), ry(y1), Math.round((x2-x1)*sx), Math.round((y2-y1)*sy))
    }
  }
}

function colorForClass(cls){
  // 简单的类别到颜色映射（可换更漂亮的色板）
  const palette = {
    waterline: 'rgba(0, 170, 255, 1)',
    floodwater: 'rgba(0, 255, 170, 1)',
  }
  if (palette[cls]) return palette[cls]
  // 哈希任何字符串为稳定颜色
  let h = 0; for (let i=0;i<cls.length;i++) h = (h*31 + cls.charCodeAt(i))|0
  const r = 100 + (h & 0x7F), g = 100 + ((h>>7) & 0x7F), b = 100 + ((h>>14) & 0x7F)
  return `rgba(${r},${g},${b},1)`
}

/** 事件绑定 */
function onTimeUpdate(){ drawOverlay() }
function onResize(){ fitOverlayToPlayer(); drawOverlay() }

/** 监听选择变化切源 */
watch(selected, async () => { await nextTick(); initPlayer() })

onMounted(() => {
  videoEl.value?.addEventListener('timeupdate', onTimeUpdate)
  window.addEventListener('resize', onResize)
  // 可选：初次自动加载第一项
  if (videos.value.length > 0) {
    selected.value = { type: 'video', data: videos.value[0] }
  }
})

onBeforeUnmount(() => {
  videoEl.value?.removeEventListener('timeupdate', onTimeUpdate)
  window.removeEventListener('resize', onResize)
  if (hls.value) { hls.value.destroy(); hls.value = null }
})
</script>

<style scoped>
.page-video{
  display: grid;
  grid-template-columns: 320px 1fr;
  height: 100%;
  overflow: hidden;
  background: #f5f7fb;
}
.sidebar{
  background: linear-gradient(180deg, #1e3c72, #2a5298);
  color: #fff;
  overflow: auto;
}
.main{
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}
.topbar{
  background:#fff; border-radius:10px; padding:12px 16px;
  display:flex; justify-content:space-between; align-items:center;
  box-shadow:0 2px 10px rgba(0,0,0,.05);
  flex-wrap: wrap;
}
.title h2{ margin:0; font-size:18px; color:#111827 }
.title p{ margin:4px 0 0; font-size:12px; color:#6b7280; }
.actions{ display:flex; gap:8px; align-items:center; flex-wrap: wrap; }
.split{ width:1px; height:20px; background:#e5e7eb; margin:0 6px; }
.opt{ display:flex; align-items:center; gap:6px; font-size:12px; color:#374151; }
.opt input{ width:64px; padding:4px 6px; border:1px solid #e5e7eb; border-radius:6px; }
.btn{
  padding:6px 12px; border:1px solid #e5e7eb; border-radius:8px;
  background:#fff; cursor:pointer;
}
.btn:hover{ background:#f3f4f6; }
.btn.primary{ background:#1e3c72; color:#fff; border-color:#1e3c72; }
.btn.primary:hover{ background:#2a5298; }

.player-wrap{
  background:#000; border-radius:10px; overflow:hidden; position:relative;
  height: 100%;
   display:flex; align-items:center; justify-content:center;
}
.player-wrap.image-mode{
  width: 100%;
  height: 100%;
  justify-content: flex-start; 
  align-items: center;
}
.player{
  width:100%; height:100%;
  background:#000;
  object-fit: contain; 
}
.player-wrap.image-mode .player{
  width:auto; height:auto;
  max-width:100%; max-height:100%;
  object-fit: contain;             /* 双保险 */
}
.overlay{
  position:absolute; left:0; top:0; width:100%; height:100%;
  pointer-events: none;
}
.placeholder{
  position:absolute; inset:0; display:grid; place-items:center; color:#9ca3af; font-size:14px;
}
@media (max-width: 768px){
  .player-wrap{ height: 260px; }
  .player-wrap.image-mode{ height: 260px; width: 100%; }
}
</style>
