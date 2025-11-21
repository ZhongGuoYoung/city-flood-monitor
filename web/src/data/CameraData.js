// 摄像头数据
export const cameraData = [
  {
    id: 1,
    name: '中山路与解放路交叉口',
    status: '在线',
    location: '中山路128号',
    floodLevel: 'high',
    // Image:"/public/images/1.png",// 新增图片URL
    // imageUrl: require('@/assets/images/1.png'), // 使用 assets 路径
    //萤石

    deviceSerial: "D37384593",

    analysis: {
      waterDepth: '25',
      waterDepthChange: '+5 cm',
      floodRisk: '严重内涝',
      riskDescription: '存在严重内涝风险，建议立即采取措施',
      trafficStatus: '中断',
      trafficDescription: '道路已封闭，车辆无法通行',
      rainfall: '35'
    }
  },
  {
    id: 2,
    name: '人民广场地下通道',
    status: '在线',
    location: '人民广场南侧',
    floodLevel: 'critical',
    // imageUrl: require('@/assets/images/2.png'), // 使用 assets 路径
    deviceSerial: "D37384597",
    analysis: {
      waterDepth: '45',
      waterDepthChange: '+12 cm',
      floodRisk: '紧急内涝',
      riskDescription: '紧急内涝情况，需要立即疏散',
      trafficStatus: '完全中断',
      trafficDescription: '地下通道已完全淹没',
      rainfall: '42'
    }
  },
  {
    id: 3,
    name: '滨江大道低洼路段',
    status: '在线',
    location: '滨江大道45号',
    floodLevel: 'medium',
    // imageUrl: require('@/assets/images/3.png'), // 使用 assets 路径
    analysis: {
      waterDepth: '18',
      waterDepthChange: '+3 cm',
      floodRisk: '中度内涝',
      riskDescription: '存在内涝风险，建议加强监控',
      trafficStatus: '缓慢',
      trafficDescription: '部分车道受影响',
      rainfall: '28'
    }
  },
  {
    id: 4,
    name: '城北立交桥下',
    status: '维护中',
    location: '城北立交桥',
    floodLevel: null,

    analysis: {
      waterDepth: '0',
      waterDepthChange: '0 cm',
      floodRisk: '无风险',
      riskDescription: '设备维护中，暂无数据',
      trafficStatus: '正常',
      trafficDescription: '交通畅通',
      rainfall: '0'
    }
  },
  {
    id: 5,
    name: '火车站南广场',
    status: '在线',
    location: '火车站南出口',
    floodLevel: 'low',
    // imageUrl: require('@/assets/images/5.png'), // 使用 assets 路径
    analysis: {
      waterDepth: '8',
      waterDepthChange: '+1 cm',
      floodRisk: '轻度内涝',
      riskDescription: '轻微积水，不影响交通',
      trafficStatus: '正常',
      trafficDescription: '交通基本正常',
      rainfall: '15'
    }
  },
  {
    id: 6,
    name: '市政府前路段',
    status: '在线',
    location: '市政府大门前',
    floodLevel: null,
    // imageUrl: require('@/assets/images/6.png'), // 使用 assets 路径
    analysis: {
      waterDepth: '3',
      waterDepthChange: '0 cm',
      floodRisk: '无风险',
      riskDescription: '无内涝风险',
      trafficStatus: '畅通',
      trafficDescription: '交通畅通无阻',
      rainfall: '12'
    }
  },
  {
    id: 7,
    name: '东湖隧道入口',
    status: '离线',
    location: '东湖隧道东入口',
    floodLevel: 'high',
    analysis: {
      waterDepth: '30',
      waterDepthChange: '+8 cm',
      floodRisk: '严重内涝',
      riskDescription: '存在严重内涝风险，设备离线',
      trafficStatus: '未知',
      trafficDescription: '设备离线，无法获取交通信息',
      rainfall: '38'
    }
  },
  {
    id: 8,
    name: '城西工业区主干道',
    status: '在线',
    location: '工业区大道88号',
    floodLevel: null,
    // imageUrl: require('@/assets/images/8.png'), // 使用 assets 路径
    analysis: {
      waterDepth: '5',
      waterDepthChange: '0 cm',
      floodRisk: '无风险',
      riskDescription: '无内涝风险',
      trafficStatus: '畅通',
      trafficDescription: '交通畅通',
      rainfall: '10'
    }
  },
  {
    id: 9,
    camId: 'cam_phone',
    name: '信息工程大学（手机）',
    status: '在线',
    location: '南京',
    floodLevel: 'medium',

    // 现在先用 DroidCam 的 MJPEG 地址即可直接显示
    mjpegUrl: 'http://10.51.215.219:4747/video',

    // 预留：以后转好 HLS 再填上，组件会自动优先用 HLS
    hlsUrl: '', // 例如 http://<server>/hls/cam_phone.m3u8

    // 预留：后端 WebSocket（叠框）接好后再填
    wsUrl: '',  // 例如 ws://<backend>:5000/ws?cam_id=cam_phone

    // 缩略图可先用 DroidCam 的单帧接口
    thumb: 'http://10.51.215.219:4747/shot.jpg',

    analysis: {
      waterDepth: '45',
      waterDepthChange: '+12 cm',
      floodRisk: '紧急内涝',
      riskDescription: '紧急内涝情况，需要立即疏散',
      trafficStatus: '完全中断',
      trafficDescription: '地下通道已完全淹没',
      rainfall: '42'
    }
  }
]

// 内涝等级映射
export const floodLevelMap = {
  'low': 1,
  'medium': 2,
  'high': 3,
  'critical': 4
}

// 洪涝等级文本映射
export const floodTextMap = {
  'low': '轻度内涝',
  'medium': '中度内涝',
  'high': '严重内涝',
  'critical': '紧急内涝'
}