<template>
  <div class="hls-page">
    <header class="hls-header">
      <h1>HLS 流测试页面（萤石）</h1>
      <p class="tip">
        说明：只测试 HLS 播放，不做识别。<br />
        确保 <code>/decoder/decoder.wasm</code> 和
        <code>/decoder/decoder.worker.js</code> 能访问到。
      </p>
    </header>

    <section class="hls-controls">
      <label class="field">
        <span class="label">HLS 地址（m3u8）：</span>
        <input
          v-model="hlsUrl"
          type="text"
          class="input"
          placeholder="粘贴萤石返回的 m3u8 地址，例如 https://open.ys7.com/v3/openlive/xxxx.m3u8?..."
        />
      </label>

      <div class="btn-row">
        <button class="btn primary" :disabled="!hlsUrl" @click="play">
          播放
        </button>
        <button class="btn" @click="stop">停止</button>
        <button class="btn" @click="fillLastEzUrl">填入最近一条 [EZVIZ] URL</button>
      </div>
    </section>

    <section class="hls-player-section">
      <div class="player-box">
        <!-- HlsPlayer 会挂载在这个 div 上 -->
        <div id="hls-test-player" class="hls-player-container"></div>
      </div>
    </section>

    <section class="hls-log">
      <h2>日志</h2>
      <div class="log-box">
        <div
          v-for="(line, idx) in logs"
          :key="idx"
          class="log-line"
        >
          {{ line }}
        </div>
        <div v-if="!logs.length" class="log-empty">暂无日志</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import HlsPlayer from '@ezuikit/player-hls'

const HLS_CONTAINER_ID = 'hls-test-player'

const hlsUrl = ref('')
const logs = ref([])

let player = null

function log (...args) {
  const msg = args
    .map(a => (typeof a === 'string' ? a : JSON.stringify(a)))
    .join(' ')
  logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${msg}`)
}

function destroyPlayer () {
  if (player && typeof player.destroy === 'function') {
    try {
      player.destroy()
      log('[HLS] destroy() called')
    } catch (e) {
      log('[HLS] destroy error:', e)
    }
  }
  player = null
}

async function createPlayer () {
  if (!hlsUrl.value) {
    log('[HLS] 未设置 HLS URL')
    return
  }

  await nextTick()

  const el = document.getElementById(HLS_CONTAINER_ID)
  if (!el) {
    log('[HLS] 容器未找到:', HLS_CONTAINER_ID)
    return
  }

  destroyPlayer()

  log('[HLS] 创建播放器, url =', hlsUrl.value)

  player = new HlsPlayer({
    id: HLS_CONTAINER_ID,      // 注意：这里必须是字符串 id
    url: hlsUrl.value,
    staticPath: '/decoder/',    // 对应 public/decoder/decoder.wasm 等
    autoplay: true,
    isLive: true,
    loggerOptions: {
      name: 'HLS',
      level: 'DEBUG',          // 打印更多日志
      showTime: true
    }
  })

  // 显式调用 play，防止自动播放策略拦截
  setTimeout(() => {
    if (player && typeof player.play === 'function') {
      player.play().then(() => {
        log('[HLS] play() 调用成功')
      }).catch(err => {
        log('[HLS] play() 调用失败:', err)
      })
    }
  }, 300)
}

function play () {
  createPlayer()
}

function stop () {
  destroyPlayer()
}

// 方便你从 Console 复制 [EZVIZ] HLS URL 过来测试
function fillLastEzUrl () {
  const text = window.prompt('请粘贴一条 [EZVIZ] HLS URL：')
  if (text) {
    hlsUrl.value = text.trim()
  }
}

onMounted(() => {
  log('HLS 测试页面已挂载')
})

onBeforeUnmount(() => {
  destroyPlayer()
})
</script>

<style scoped>
.hls-page {
  max-width: 1080px;
  margin: 24px auto;
  padding: 16px 24px 32px;
  color: #e6f1ff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
}

.hls-header h1 {
  font-size: 22px;
  margin-bottom: 8px;
}

.tip {
  font-size: 13px;
  color: #9fb3c8;
}

.tip code {
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 4px;
  border-radius: 4px;
}

.hls-controls {
  margin: 16px 0 12px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #111827;
  border: 1px solid #1f2937;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-size: 13px;
  color: #9fb3c8;
}

.input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #374151;
  background: #020617;
  color: #e5e7eb;
  font-size: 13px;
}

.input::placeholder {
  color: #6b7280;
}

.btn-row {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid #374151;
  background: #111827;
  color: #e5e7eb;
  font-size: 13px;
  cursor: pointer;
}

.btn.primary {
  border-color: #22d3ee;
  background: linear-gradient(90deg, #22c1ee, #3b82f6);
  color: #0f172a;
  font-weight: 500;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hls-player-section {
  margin-top: 16px;
}

.player-box {
  width: 100%;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.8);
}

/* 让播放器区域保持 16:9 */
.hls-player-container {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

.hls-log {
  margin-top: 18px;
}

.hls-log h2 {
  font-size: 16px;
  margin-bottom: 8px;
}

.log-box {
  max-height: 220px;
  overflow: auto;
  border-radius: 8px;
  background: #020617;
  border: 1px solid #1f2937;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.5;
}

.log-line {
  white-space: pre-wrap;
  color: #e5e7eb;
}

.log-empty {
  color: #6b7280;
}
</style>
