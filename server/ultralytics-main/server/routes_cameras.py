# server/routes_cameras.py----地图上的监控摄像头
from fastapi import APIRouter
import pymysql

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


def get_conn():
    return pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="123456",
        database="city_flood_monitor",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )


@router.get("/")
def list_cameras():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cam_id, name, status, lat, lng,
                       stream_mp4, stream_mjpeg, stream_hls, snapshot_url, deviceSerial, channelNo
                FROM flood_camera
                ORDER BY id
            """)
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()
