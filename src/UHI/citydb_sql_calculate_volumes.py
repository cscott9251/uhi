from UHI.config import *
import subprocess
import psycopg2

def connect_to_3dcitydb():


    conn = psycopg2.connect(
        dbname=f"{PGCITYDB}",
        user=f"{PGADMIN}",
        password=f"{PGADMIN_PASSWORD}",
        host=f"{PGHOST}",  # or another host
        port="5432"         # default PostgreSQL port
    )

    return conn

conn = connect_to_3dcitydb()

cur = conn.cursor()

with open(f"{SQL_DIR}\\calculate_volume_query.sql", "r", encoding="utf-8") as f:
    sql = f.read()

cur.execute(sql)

conn.commit()

cur.close()