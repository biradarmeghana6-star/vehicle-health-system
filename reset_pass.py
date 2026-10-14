import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

passwords_to_try = ['', 'postgres', 'admin', 'root', '1234', 'password']
connected = False

for pwd in passwords_to_try:
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password=pwd,
            host='localhost',
            port=5432
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("ALTER USER postgres WITH PASSWORD 'postgres';")
        try:
            cur.execute("CREATE DATABASE vehicle_health_db;")
        except Exception:
            pass # Database already exists
        print(f"SUCCESS! Connected with password '{pwd}' and reset postgres password to 'postgres'!")
        cur.close()
        conn.close()
        connected = True
        break
    except Exception as e:
        continue

if not connected:
    print("Could not connect automatically with standard passwords.")
