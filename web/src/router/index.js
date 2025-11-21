import { createRouter, createWebHashHistory } from 'vue-router'


const Layout = () => import('../views/TileIndex.vue')


const MapPage = () => import('../views/MapPage.vue')
const MonitorPage = () => import('../views/MonitorPage.vue')
const VideoPage = () => import('../views/VideoPage.vue')
const HistoryVideo = () => import('../views/HistoryVideo.vue')
const HlsTest = () => import('../views/HlsTest.vue')
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: Layout,
      children: [
        { path: '', redirect: '/map' }, // 默认进 map
        { path: 'map', name: 'map', component: MapPage, meta: { title: '地图', keepAlive: true } },
        { path: 'monitor', name: 'monitor', component: MonitorPage, meta: { title: '监控', keepAlive: true } },
        { path: 'video', name: 'video', component: VideoPage, meta: { title: '视频', keepAlive: true } },
        { path: 'history_video', name: 'history_video', component: HistoryVideo, meta: { title: '历史视频流', keepAlive: true } },
        { path: 'HlsTest', name: 'HlsTest', component: HlsTest, meta: { title: 'HlsTest', keepAlive: true } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})


router.afterEach((to) => { if (to.meta?.title) document.title = to.meta.title })

export default router
