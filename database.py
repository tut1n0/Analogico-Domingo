import pymysql
from pymysql.cursors import DictCursor


def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="analogico_domingo",
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False
    )