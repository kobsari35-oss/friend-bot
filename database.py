import os
import psycopg2
from psycopg2 import pool

db_pool = None

def init_pool():
    global db_pool
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL missing.")
        return
    try:
        # sslmode='require' is needed for cloud DBs like Neon/Render
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, db_url, sslmode='require')
        if db_pool: print("✅ DB Pool Created.")
    except Exception as e:
        print(f"❌ DB Pool Error: {e}")

def get_db_connection():
    global db_pool
    if not db_pool: init_pool()
    try:
        if db_pool:
            return db_pool.getconn()
        else:
            return None
    except Exception as e:
        print(f"❌ Get Conn Error: {e}")
        # Try to reconnect once
        try:
            init_pool()
            if db_pool: return db_pool.getconn()
        except: pass
        return None

def release_db_connection(conn):
    global db_pool
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except Exception as e:
            print(f"Release Error: {e}")

def init_db():
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to DB for Init.")
        return
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        name TEXT, age INTEGER, gender TEXT, province TEXT, looking_for TEXT,
                        photo_id TEXT, username TEXT, first_name TEXT,
                        status TEXT DEFAULT 'active', is_visible INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS likes (
                        id SERIAL PRIMARY KEY,
                        sender_id BIGINT, receiver_id BIGINT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(sender_id, receiver_id)
                    )
                ''')
        print("✅ Tables Initialized.")
    except Exception as e:
        print(f"❌ Init DB Error: {e}")
    finally:
        release_db_connection(conn)