<template>
  <div class="map-wrap">
    <div ref="mapEl" class="tdt-map"></div>

    <!-- 右下侧悬浮按钮 -->
    <img class="layers-change" src="/static/index/layers.svg" @click="togglePanel" />
    <img class="reset-btn"     src="/static/index/reset-position.svg" @click="handleClickReset" />
    <img class="location"      src="/static/index/location.svg" @click="handleLocation" />
  </div>

  <!-- 图层切换面板 -->
  <div v-show="showChangeMap" class="layers">
    <div class="group">
      <div class="group-row">
        <div
          v-for="b in baseList"
          :key="b.key"
          class="layers-item"
          :class="{ active: baseType === b.key }"
          @click="onPickBase(b)"
        >
          <img class="layer-img" :src="b.img" />
          <div class="layer-label">{{ b.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import shantoujson from "@/assets/GeoJson/汕头市.json";

// —— 配置 ——
const TDT_KEY = '44b272f088be993ab7c9f74a107a06c5'
const INIT_CENTER = [ 23.35, 116.68] //广东
const INIT_ZOOM   = 10

// —— refs / state ——
const mapEl = ref(null)
let map = null
let ro = null
const baseType = ref('img')
const showChangeMap = ref(false)
let locMarker = null
let locCircle = null

const baseList = [
  { key: 'vec', name: '矢量', img: '/static/index/tdtsl.svg' },
  { key: 'img', name: '影像', img: '/static/index/tdtyx.svg' },
  { key: 'ter', name: '地形', img: '/static/index/tdtdx.svg' },
]


// —— 工具：创建天地图 WMTS 图层（含注记可选）——
function tdtLayer(type, withAnno = true) {
  const set = 'c' // WGS-84 / EPSG:4326
  const baseLayer = L.tileLayer(
    `https://t{s}.tianditu.gov.cn/${type}_${set}/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${type}&STYLE=default&TILEMATRIXSET=${set}&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
    {
      subdomains: '01234567',
      minZoom: 1,
      maxZoom: 18,
      crossOrigin: '', 
      updateWhenZooming: false,  // 动画缩放时不实时请求新瓦片
      updateWhenIdle: true,      // 停止交互后再刷新瓦片
      keepBuffer: 6,             // 视窗周围保留更多瓦片，减少小范围移动的重复请求
      detectRetina: false ,
      zoomOffset: 1 ,
      attribution:
          "&copy; <a href='https://www.tianditu.gov.cn/'>天地图</a> | 数据来源：国家基础地理信息中心 | 坐标：<span id='ll-dyn-attr'>经：--，纬：--</span>",

    }
  )
  if (!withAnno) return baseLayer

  // 注记图层：影像=cia，地形=cta，矢量=cva
  const annoKey = type === 'img' ? 'cia' : (type === 'ter' ? 'cta' : 'cva')
  const anno = L.tileLayer(
    `https://t{s}.tianditu.gov.cn/${annoKey}_${set}/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${annoKey}&STYLE=default&TILEMATRIXSET=${set}&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
    {
      subdomains: '01234567',
      minZoom: 1,
      maxZoom: 18,
      crossOrigin: ''
    }
  )
  return L.layerGroup([baseLayer, anno])
}


// 预创建三套底图
const layers = {
  vec: tdtLayer('vec', true),
  img: tdtLayer('img', true),
  ter: tdtLayer('ter', true),
}

// 切换底图
function setBase(type) {
  if (!map || !layers[type]) return
  baseType.value = type
  Object.values(layers).forEach(l => map.removeLayer(l))
  layers[type].addTo(map)
  map.invalidateSize()
}

//面板内的选择
function onPickBase(b) {
  setBase(b.key)
  showChangeMap.value = false
}

//定位
function handleLocation() {
  if (!map) return;

  //清理旧标记
  if (locMarker) { map.removeLayer(locMarker); locMarker = null; }
  if (locCircle) { map.removeLayer(locCircle); locCircle = null; }

  map.locate({ setView: true, enableHighAccuracy: true, maxZoom: 14 });
  map.once('locationfound', (e) => {
    const { lat, lng } = e.latlng;      //浏览器定位WGS-84
    const p = L.latLng(lat, lng);     
    locMarker = L.marker(p).addTo(map).bindPopup('您在这里');
    locCircle = L.circle(p, { radius: e.accuracy }).addTo(map);
  });
  map.once('locationerror', (e) => console.warn('定位失败：', e?.message || e));
}
//清除标记
function clearLocationOverlay() {
  if (locMarker) { map.removeLayer(locMarker); locMarker = null }
  if (locCircle) { map.removeLayer(locCircle); locCircle = null }
  map.stopLocate && map.stopLocate()   
  map.closePopup && map.closePopup()   
}
// 重置视图
function handleClickReset() {
  if (!map) return
  map.setView(INIT_CENTER, INIT_ZOOM)
  clearLocationOverlay()
}

// 面板显隐
function togglePanel() {
  showChangeMap.value = !showChangeMap.value
}

// 刷新（外部可调用）
function refresh() {
  map && map.invalidateSize(true)
}



onMounted(async () => {
  await nextTick()
  if (!mapEl.value) return

  map = L.map(mapEl.value, {
    crs: L.CRS.EPSG4326,        
    center: INIT_CENTER,
    zoom: INIT_ZOOM,
    zoomControl: false,
  })

   L.geoJSON(shantoujson, {
        style: function () {
            return {
                stroke: true,
                fill: false,
                color: "#2e7dff",
                weight: 2
            };
        },
        pane: "markerPane"
    }).addTo(map);

  // 默认底图
 layers.img.addTo(map) 

 // —— 动态更新归属栏坐标 —— 
function updateAttrLL(latlng) {
  const el = document.getElementById('ll-dyn-attr')
  if (el && latlng) {
    el.textContent = `经：${latlng.lng.toFixed(6)}，纬：${latlng.lat.toFixed(6)}`
  }
}

// 初始写入一次（用地图中心）
updateAttrLL(map.getCenter())

// 鼠标移动时更新，使用 rAF 做节流避免高频抖动
let rafId = 0
map.on('mousemove', (e) => {
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    updateAttrLL(e.latlng)
    rafId = 0
  })
})



  // 首次刷新尺寸，避免容器初次为 0
  setTimeout(() => map && map.invalidateSize(), 0)

  // 监听容器尺寸变化
  if (window.ResizeObserver && mapEl.value) {
    ro = new ResizeObserver(() => map && map.invalidateSize())
    ro.observe(mapEl.value)
  }
  // 窗口变化
  window.addEventListener('resize', refresh)
})

onUnmounted(() => {
  window.removeEventListener('resize', refresh)
  if (ro) { ro.disconnect() }
  if (map) { map.remove(); map = null }
})

defineExpose({ getMap: () => map })
</script>

<style scoped>
.map-wrap {
  width: 100%;
  height: 100%;
  min-height: 480px;
   position: relative;
}
.tdt-map {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  
}
/* 给 Leaflet 容器一个深色底，使用 :deep 选中子组件内部元素 */
:deep(.leaflet-container) { background: #0e1a2b; }

.basemap-switch {
  position: absolute; right: 12px; top: 12px; z-index: 10;
  display: flex; gap: 6px;
  background: rgba(0,0,0,.35);
  padding: 6px; border-radius: 8px;
  backdrop-filter: blur(4px);
}
.basemap-switch button {
  border: 0; padding: 6px 10px; border-radius: 6px; cursor: pointer;
  color: #fff; background: rgba(255,255,255,.2);
}
.basemap-switch button.active { background: rgba(36,118,226,.9); }

.layers-change, .reset-btn, .location {
  position: absolute; right: 10px; width: 48px; height: 48px; z-index: 10; cursor: pointer;
}
.reset-btn { bottom: 72px; z-index: 10000; height: 65px; width: 65px;}
.location  { bottom: 130px;z-index: 10000; height: 65px; width: 65px;}
.layers-change { bottom: 14px;z-index: 10000; height: 65px; width: 65px;}

/* 图层面板（可按需美化） */
.layers {
  position: absolute; right: 70px; bottom: 14px; z-index: 11;
  width: 300px; background: rgba(15, 25, 38, .96);
  border-radius: 12px; padding: 12px; color: #e6f2ff;
  box-shadow: 0 8px 20px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.08);
  z-index: 10000;
  height: 120px;
}
.group-title { font-weight: 600; margin-bottom: 8px; }
.group-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.layers-item {
  border-radius: 8px; overflow: hidden; background: rgba(255,255,255,.06);
  outline: 2px solid transparent; transition: .2s; user-select: none;
}
.layers-item.active { outline-color: #2476e2; box-shadow: 0 0 0 2px rgba(36,118,226,.35); }
.layer-img { display: block; width: 100%; height: 64px; object-fit: cover; }
.layer-label { text-align: center; font-size: 12px; padding: 6px 0; }


</style>
