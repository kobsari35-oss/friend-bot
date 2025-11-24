import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden
from config import TEXTS
from database import get_db_connection, release_db_connection

def escape_md(text):
    if not text: return "Unknown"
    return text.replace("_", r"\_").replace("*", r"\*").replace("[", r"\[").replace("`", r"\`")

def get_time_ago(dt):
    if not dt: return "Offline"
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60: return "🟢 Online"
    if seconds < 3600: return f"🟢 {int(seconds // 60)}m ago"
    if seconds < 86400: return f"🟡 {int(seconds // 3600)}h ago"
    return f"🔴 {int(seconds // 86400)}d ago"

async def find_and_send_user(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_type: str, exclude_id: int = None):
    user_id = update.effective_user.id
    conn = get_db_connection()
    
    if not conn:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ System busy. Try again.")
        return

    match = None
    try:
        with conn:
            with conn.cursor() as cursor:
                # Update Last Active
                cursor.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
                
                query = """
                    SELECT * FROM users 
                    WHERE user_id != %s AND status = 'active' AND is_visible = 1
                    AND name IS NOT NULL AND photo_id IS NOT NULL
                """
                params = [user_id]
                if exclude_id:
                    query += " AND user_id != %s"
                    params.append(exclude_id)

                if filter_type == 'male': query += " AND gender IN ('Male', 'Male 👨', 'ប្រុស')"
                elif filter_type == 'female': query += " AND gender IN ('Female', 'Female 👩', 'ស្រី')"
                elif filter_type == 'nearby':
                    cursor.execute("SELECT province FROM users WHERE user_id = %s", (user_id,))
                    res = cursor.fetchone()
                    if res and res[0]:
                        query += " AND province ILIKE %s"
                        params.append(f"%{res[0]}%")

                query += " ORDER BY RANDOM() LIMIT 1"
                cursor.execute(query, tuple(params))
                match = cursor.fetchone()
    except Exception as e:
        print(f"Search Error: {e}")
    finally:
        release_db_connection(conn)
    
    chat_id = update.effective_chat.id
    if match:
        target_id = match[0]
        safe_name = escape_md(match[1])
        
        # --- UI DESIGN: PROFILE CARD ---
        caption = (
            f"🌟 **{safe_name}, {match[2]}**\n"
            f"📍 {escape_md(match[4])}\n" 
            f"──────────────────\n"
            f"❝ *{escape_md(match[5])}* ❞\n"
            f"──────────────────\n"
            f"⚧️ {match[3]}  •  🕒 {get_time_ago(match[12])}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(TEXTS['like_btn'], callback_data=f"like_{target_id}"),
                InlineKeyboardButton(TEXTS['btn_next'], callback_data=f"next_{filter_type}_{target_id}")
            ],
            [
                InlineKeyboardButton("💌 Direct Chat", url=f"tg://user?id={target_id}") 
            ],
            [
                InlineKeyboardButton(TEXTS['report_btn'], callback_data=f"report_{target_id}"),
                InlineKeyboardButton(TEXTS['btn_stop'], callback_data="stop_0")
            ]
        ]
        
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=match[6], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except BadRequest:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ **Photo Error**\n\n" + caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        msg = TEXTS['not_found_nearby'] if filter_type == 'nearby' else TEXTS['not_found']
        await context.bot.send_message(chat_id=chat_id, text=msg)

async def broadcast_new_user(context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    sender_id = user_data['id']
    caption = TEXTS['new_user_alert'].format(
        name=escape_md(user_data['name']),
        age=user_data['age'],
        prov=escape_md(user_data['province'])
    )
    
    users = []
    conn = get_db_connection()
    if not conn: return 
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE status = 'active' AND user_id != %s LIMIT 100", (sender_id,))
                users = cursor.fetchall()
    except: return
    finally: release_db_connection(conn)

    kb = [[InlineKeyboardButton("🔎 Search Now", switch_inline_query_current_chat="")]]
    
    for u in users:
        try:
            await context.bot.send_photo(chat_id=u[0], photo=user_data['photo'], caption=caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            await asyncio.sleep(0.05) 
        except: continue