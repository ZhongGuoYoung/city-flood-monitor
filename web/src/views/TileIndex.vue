<template>
  <el-container class="container">
    <!-- 顶部导航条 -->
    <el-header class="header">
      <div class="title-box">
        <h1 class="title">
          <span class="title-main">城市内涝监控系统</span>
        </h1>
      </div>

      <nav class="nav nav-right">
        <router-link
          v-for="item in models"
          :key="item.key"
          :class="{ active: modelPicked === item.key }"
          :to="'/' + item.key"
          @click="modelPicked = item.key"
        >
          <span class="nav-label">{{ item.name }}</span>
        </router-link>
      </nav>
    </el-header>

    <div class="content">
      <router-view />
    </div>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const models = ref([
  { name: '态势总览',   key: 'map' },
  { name: '实时监测',   key: 'monitor' },
  { name: '视频联动',   key: 'video' },
  { name: '事件回溯',   key: 'history_video' },
  { name: 'HlsTest',   key: 'HlsTest' },
])

const router = useRouter()
const modelPicked = ref('map')
const m = router.currentRoute.value.path.split('/')[1]
if (m) modelPicked.value = m
</script>

<style lang="scss">

html, body, #app, .container { height: 100%; margin: 0; }
body{ -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

/* 顶部栏 */
.header{
  position: sticky;
  top: 0;
  z-index: 10;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 16px;
  background: rgba(255,255,255,0.8);
  backdrop-filter: saturate(160%) blur(8px);
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}

.title-box{ flex: 1 1 auto; }
.title-box .title{
  margin: 0;
  font-size: 35px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.5px;
}
.title-box .title .title-main{
  background: linear-gradient(90deg,#0ea5e9 0%, #2563eb 50%, #7c3aed 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* 右侧导航 */
.nav{ display: flex; align-items: center; gap: 10px; }
.nav-right{ flex: 0 0 auto; }
.nav a{
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  font-size: 20px;
  height: 48px;           
  border-radius: 8px;
  color: #334155;
  text-decoration: none;
  position: relative;
  transition: background .18s ease, color .18s ease, box-shadow .18s ease, transform .18s ease;
}
.nav a:hover{ background: #f3f4f6; color: #0f172a; }
.nav a.active{
  background: #2563eb;
  color: #fff;
  box-shadow: 0 6px 14px rgba(37,99,235,.25);
  transform: translateY(-1px);
}
.nav a::after{
  content: '';
  position: absolute;
  left: 12px; right: 12px; bottom: 6px;
  height: 2px;
  background: linear-gradient(90deg,#93c5fd 0%, #2563eb 60%, #7c3aed 100%);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform .18s ease;
}
.nav a:hover::after, .nav a.active::after{ transform: scaleX(1); }
.nav .nav-label{ line-height: 1; }

.content{
  flex: 1 1 auto;
  min-height: calc(100% - 80px);
  margin: 0; padding: 0; border: 0; border-radius: 0; box-shadow: none;
  position: relative;
  overflow: hidden;
}
.header::after{
  content: '';
  position: absolute;
  left: 0; right: 0; bottom: -1px;
  height: 3px;
  background: linear-gradient(90deg, #0ea5e9 0%, #2563eb 50%, #7c3aed 100%);
  opacity: .85;
}

.content > *{ width:100%; height:100%; }
</style>
