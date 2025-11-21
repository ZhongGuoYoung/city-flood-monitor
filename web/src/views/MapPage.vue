<template>
  <MapTdt ref="mapRef" />
</template>

<script setup>
import { ref, nextTick, onMounted, createApp } from 'vue'
import L from 'leaflet'
import MapTdt from '@/components/MapTdt.vue'
// import cameras from '@/data/MapData.js'                 //点位数据
import camSvgUrl from '@/assets/image/摄像头.svg?url'   //图标资源
import CamPopup from '@/components/CamPopup.vue'        //监控弹窗
import axios from 'axios'
import { API_BASE } from '@/lib/api'

const cameraList = ref([]) 
/**MapTdt暴露的底图map*/
const mapRef = ref(null)
async function waitForMap () {
  await nextTick()
  return new Promise((resolve, reject) => {
    const t = setInterval(() => {
      const m = mapRef.value?.getMap?.()
      if (m) { clearInterval(t); resolve(m) }
    }, 50)
    setTimeout(() => { clearInterval(t); reject(new Error('Map not ready')) }, 8000)
  })
}

/** 摄像头图标 */
const camIcon = L.icon({
  iconUrl: camSvgUrl,
  iconSize: [35, 35],
  iconAnchor: [14, 28],
  tooltipAnchor: [0, -2]
})

/** 打开弹窗：把 CamPopup.vue 挂到 Leaflet 的弹窗容器 */
function openCamPopup (map, info) {
  const mountEl = document.createElement('div')
  let popup
  const app = createApp(CamPopup, {
    info,
    notifyResize: () => {
      if (!popup) return
      requestAnimationFrame(() => {
        popup.update()
        map.panInside?.([info.lat, info.lng], {
          paddingTopLeft: [24, 24],
          paddingBottomRight: [24, 24]
        })
      })
    }
  })

  const vw = map.getSize().x
  const minW = Math.min(760, vw - 60)
  app.mount(mountEl)

  popup = L.popup({
    maxWidth: 3000,
    minWidth: minW,
    className: 'cam-popup-wrap',
    autoPan: true,
    keepInView: true,
    autoPanPaddingTopLeft: [24, 24],
    autoPanPaddingBottomRight: [24, 24]
  })
    .setLatLng([info.lat, info.lng])
    .setContent(mountEl)

  popup.openOn(map)
  popup.on('remove', () => { app.unmount() })
}

/** 把摄像头点位加到图上，不做缩放/视域调整 */
function addCameras (map, points) {
  const group = L.layerGroup().addTo(map)
  points.forEach(p => {
    L.marker([p.lat, p.lng], { icon: camIcon })
      .bindTooltip(p.name, { permanent: true, direction: 'bottom', className: 'cam-label' })
      .addTo(group)
      .on('click', () => openCamPopup(map, p))
  })
  return group
}

/** 从后端加载摄像头列表，并转成前端需要的结构 */
async function loadCamerasFromApi () {
  // 如果你 vite 配了代理，可以写 '/api/cameras'
  // 没有代理就写完整地址：'http://localhost:9000/api/cameras'
  const resp = await axios.get(`${API_BASE}/cameras`)
  const rows = resp.data || []
  console.log(resp.data)

  return rows.map(row => ({
    id: row.id,
    camId: row.cam_id,
    name: row.name,
    status: row.status,
    lat: Number(row.lat),
    lng: Number(row.lng),
    streams: {
      mp4: row.stream_mp4 || '',
      mjpeg: row.stream_mjpeg || '',
      hls: row.stream_hls || ''
    },
    snapshot: row.snapshot_url || '',
    deviceSerial: row.deviceSerial,
    channelNo: row.channelNo
  }))
}

onMounted(async () => {
  const map = await waitForMap()

  try {
    cameraList.value = await loadCamerasFromApi()
    if (!cameraList.value.length) {
      console.warn('后端没有返回摄像头数据，地图上不会有点位')
      return
    }
    addCameras(map, cameraList.value)  // 用接口数据加点
  } catch (err) {
    console.error('加载摄像头出错', err)
  }
})
</script>

<style scoped>
/* 标签样式 */
.cam-label{
  background: rgba(0,0,0,.6);
  color:#fff;
  border:none;
  padding:2px 6px;
  border-radius:4px;
}
.cam-popup-wrap .leaflet-popup-content-wrapper{
  border-radius: 12px;  
  background: #fff;
}
.cam-popup-wrap .leaflet-popup-content{ margin: 0; }
</style>
