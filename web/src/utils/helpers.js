// 添加到 src/utils/helpers.js 的顶部
import { floodLevelMap, floodTextMap } from '../data/CameraData.js'
// 获取状态类名
export const getStatusClass = (status) => {
  if (status === '在线') return 'status-online'
  if (status === '离线') return 'status-offline'
  if (status === '维护中') return 'status-maintenance'
  return ''
}

// 获取洪涝类名
export const getFloodClass = (floodLevel, isAnimated = false) => {
  if (!floodLevel) return ''
  return `flood-${floodLevel}${isAnimated && floodLevel === 'critical' ? ' animated' : ''}`
}

// 获取洪涝文本
export const getFloodText = (floodLevel) => {
  if (!floodLevel) return ''
  return floodTextMap[floodLevel] || ''
}

// 过滤和排序摄像头
export const filterAndSortCameras = (cameras, searchQuery, filter, sortOrder) => {
  let result = [...cameras]
  
  // 搜索过滤
  if (searchQuery) {
    const query = searchQuery.toLowerCase()
    result = result.filter(camera => 
      camera.name.toLowerCase().includes(query) || 
      camera.location.toLowerCase().includes(query)
    )
  }
  
  // 状态过滤
  if (filter === 'online') {
    result = result.filter(camera => camera.status === '在线')
  } else if (filter === 'flood') {
    result = result.filter(camera => camera.floodLevel)
  }
  
  // 内涝排序
  if (filter === 'flood' && sortOrder) {
    result = result.sort((a, b) => {
      const levelA = a.floodLevel ? floodLevelMap[a.floodLevel] : 0
      const levelB = b.floodLevel ? floodLevelMap[b.floodLevel] : 0
      if (sortOrder === 'asc') {
        return levelA - levelB
      } else {
        return levelB - levelA
      }
    })
  }
  
  return result
}