import pymysql

try:
    print("Connecting...")
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='dbBarbershop',
        connect_timeout=5
    )
    print("Connection successful!")
    connection.close()
except Exception as e:
    print(f"Connection failed: {e}")
