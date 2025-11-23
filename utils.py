from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import TEXTS
from database import get_connection # ហៅ function ថ្មី

def escape_md(text):
    if not text: return ""
    return text.replace("_", r"\_").replace("*", r"\*").replace("[", r"\[").replace("`", r"\`")

async def find_and_send_user(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_type: str, exclude_id: int = None):
    user_id = update.effective_user.id
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                # ប្រើ %s ជំនួស ? សម្រាប់ PostgreSQL
                query = "SELECT * FROM users WHERE user_id != %s AND status = 'active' AND is_visible = 1 "
                params = [user_id]

                if exclude_id:
                    query += "AND user_id != %s "
                    params.append(exclude_id)

                if filter_type == 'male': 
                    query += "AND gender IN ('Male', 'Male 👨', 'ប្រុស') "
                elif filter_type == 'female': 
                    query += "AND gender IN ('Female', 'Female 👩', 'ស្រី') "
                elif filter_type == 'nearby':
                    cursor.execute("SELECT province FROM users WHERE user_id = %s", (user_id,))
                    res = cursor.fetchone()
                    my_prov = res[0] if res else ""
                    query += "AND province ILIKE %s " # ILIKE គឺមិនប្រកាន់តួអក្សរតូចធំ
                    params.append(f"%{my_prov}%")

                query += "ORDER BY RANDOM() LIMIT 1"
                cursor.execute(query, tuple(params))
                match = cursor.fetchone()
    except Exception as e:
        print(f"DB Error in utils: {e}")
        match = None
    finally:
        conn.close()
    
    chat_id = update.effective_chat.id
    
    if match:
        target_id = match[0]
        safe_name = escape_md(match[1])
        name_link = f"[{safe_name}](tg://user?id={target_id})"
        username = match[7]
        photo_id = match[6]
        
        contact_info = ""
        if username:
            clean_user = username.replace("https://t.me/", "").replace("@", "").strip()
            display_user = escape_md(clean_user)
            contact_info = f"🔗 Link: https://t.me/{display_user}\n💎 Username: @{display_user}"
        else:
            contact_info = "🔗 Link: (Click Name)"

        caption = (
            f"{TEXTS['found']}\n\n"
            f"👤 {TEXTS['lbl_name']}*{name_link}*\n"
            f"🎂 {match[2]} | ⚧️ {match[3]}\n"
            f"📍 {TEXTS['lbl_prov']} {match[4]}\n"
            f"🔍 {TEXTS['lbl_look']} {match[5]}\n\n"
            f"{contact_info}\n"
            f"{TEXTS['click_to_chat']}"
        )
        
        keyboard = [
            [InlineKeyboardButton(TEXTS['like_btn'], callback_data=f"like_{target_id}"),
             InlineKeyboardButton(TEXTS['report_btn'], callback_data=f"report_{target_id}")],
            [InlineKeyboardButton(TEXTS['btn_next'], callback_data=f"next_{filter_type}_{target_id}")] 
        ]
        
        try:
            if photo_id:
                await context.bot.send_photo(chat_id=chat_id, photo=photo_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await context.bot.send_message(chat_id=chat_id, text="🖼️ [No Photo Available]\n\n" + caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="Error displaying profile.")
    else:
        if filter_type == 'nearby':
            await context.bot.send_message(chat_id=chat_id, text=TEXTS['not_found_nearby'])
        else:
            await context.bot.send_message(chat_id=chat_id, text=TEXTS['not_found'])