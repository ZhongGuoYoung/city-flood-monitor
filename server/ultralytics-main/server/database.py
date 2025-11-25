import pymysql


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
