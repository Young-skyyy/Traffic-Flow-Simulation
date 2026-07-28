# -*- coding: utf-8 -*-
"""MySQL 数据库连接测试脚本"""

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "921129YYmnqnb",
}


def test_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print("数据库连接成功！")
        print(f"MySQL 版本: {version}")
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"连接失败，错误信息：{e}")


if __name__ == "__main__":
    test_connection()
