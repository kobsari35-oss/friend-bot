import os
import psycopg2

def get_connection():
    """បង្កើត Connection ទៅកាន់ PostgreSQL"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise Exception("❌ រកមិនឃើញ DATABASE_URL ទេ។ សូមដាក់វានៅក្នុង Environment Variables!")
    
    conn = psycopg2.connect(db_url)
    return conn

def init_db():
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                # Create Users Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        name TEXT,
                        age INTEGER,
                        gender TEXT,
                        province TEXT,
                        looking_for TEXT,
                        photo_id TEXT,
                        username TEXT,
                        first_name TEXT,
                        status TEXT DEFAULT 'active',
                        is_visible INTEGER DEFAULT 1
                    )
                ''')
                
                # Create Likes Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS likes (
                        id SERIAL PRIMARY KEY,
                        sender_id BIGINT,
                        receiver_id BIGINT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(sender_id, receiver_id)
                    )
                ''')
        conn.close()
        print("✅ Database initialized successfully (PostgreSQL).")
    except Exception as e:
        print(f"❌ Database Error: {e}")