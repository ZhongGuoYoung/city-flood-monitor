import cameraCoverImg from '@/assets/image/11.png';

export default [
    {
        id: 101,
        camId: 'cam_net_demo',
        name: '网络视频测试1',
        lat: 23.47,
        lng: 116.69,
        status: 'online',
        streams: {
            mp4: '/videos/video_1.mp4',
            mjpeg: '',
            hls: ''
        },
        // 2. 修正：去掉引号，直接引用导入的变量
        snapshot: cameraCoverImg
    },
    {
        id: 102,
        camId: 'local_cam_2',
        name: '本地视频2(模拟摄像头)',
        lat: 23.36,
        lng: 116.69,
        status: 'online',
        streams: {
            mp4: 'videos/video_2.mp4',
            mjpeg: '',
            hls: ''
        },
        snapshot: cameraCoverImg
    },
    {
        id: 103,
        camId: 'cam_mjpeg_demo',
        name: '网络视频测试3',
        lat: 23.26,
        lng: 116.44,
        status: 'online',
        streams: {
            mp4: '/videos/video_3.mp4',
            mjpeg: '',
            hls: ''
        },
        snapshot: cameraCoverImg
    },
    {
        id: 104,
        camId: 'cam_mjpeg_demo',
        name: '网络视频测试4',
        lat: 23.28,
        lng: 116.67,
        status: 'online',
        streams: {
            mp4: '',
            mjpeg: '',
            hls: ''
        },
        snapshot: cameraCoverImg
    },
    {
        id: 105,
        camId: 'cam_mjpeg_demo',
        name: '网络视频测试5',
        lat: 23.63,
        lng: 116.84,
        status: 'online',
        streams: {
            mp4: '',
            mjpeg: '',
            hls: ''
        },
        snapshot: cameraCoverImg
    },
    {
        id: 106,
        camId: 'cam_mjpeg_demo',
        name: '网络视频测试6',
        lat: 23.08,
        lng: 116.39,
        status: 'online',
        streams: {
            mp4: '',
            mjpeg: '',
            hls: ''
        },
        snapshot: cameraCoverImg
    }
]