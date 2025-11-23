from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import Forbidden, BadRequest
from config import *
from utils import escape_md, find_and_send_user
from database import get_connection # Import Connection

def get_main_menu():
    keyboard = [
        [TEXTS['btn_search'], TEXTS['btn_profile']],
        [TEXTS['btn_likes'], TEXTS['btn_help']]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Helper Function: Check Registration
def is_registered(user_id):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                return cursor.fetchone() is not None
    except:
        return False
    finally:
        conn.close()

async def require_registration(update: Update):
    msg = "⚠️ **Account Required!**\n\nYou need to register first before using this feature.\n👉 Click /start to register."
    try:
        await update.message.reply_text(msg, parse_mode='Markdown')
    except:
        await update.callback_query.message.reply_text(msg, parse_mode='Markdown')

# --- REGISTRATION ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if is_registered(user_id):
        await update.message.reply_text(TEXTS['menu_msg'], reply_markup=get_main_menu())
        return ConversationHandler.END
    else:
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    # ON CONFLICT DO NOTHING is Postgres equivalent of INSERT OR IGNORE
                    cursor.execute("INSERT INTO users (user_id, is_visible) VALUES (%s, 1) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        finally:
            conn.close()
                
        await update.message.reply_text(TEXTS['ask_name'], parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
        return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET name = %s WHERE user_id = %s", (update.message.text, user_id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['ask_age'])
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    age_text = update.message.text
    if not age_text.isdigit() or int(age_text) < 12 or int(age_text) > 100:
        await update.message.reply_text(TEXTS['age_error'])
        return AGE
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET age = %s WHERE user_id = %s", (int(age_text), user_id))
    finally:
        conn.close()
        
    keyboard = [[TEXTS['btn_male'], TEXTS['btn_female'], TEXTS['btn_other']]]
    await update.message.reply_text(TEXTS['ask_gender'], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    gender = update.message.text.split(' ')[0]
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET gender = %s WHERE user_id = %s", (gender, user_id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['ask_prov'], reply_markup=ReplyKeyboardRemove())
    return PROVINCE

async def get_province(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET province = %s WHERE user_id = %s", (update.message.text, user_id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['ask_looking'])
    return LOOKING_FOR

async def get_looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET looking_for = %s WHERE user_id = %s", (update.message.text, user_id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['ask_photo'])
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = update.effective_user
    user_id = tg_user.id
    photo_file = update.message.photo[-1].file_id
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET photo_id = %s, username = %s, first_name = %s WHERE user_id = %s", 
                               (photo_file, tg_user.username, tg_user.first_name, user_id))
    finally:
        conn.close()
        
    await update.message.reply_text(TEXTS['reg_success'], parse_mode='Markdown', reply_markup=get_main_menu())
    return ConversationHandler.END

# --- SEARCH ---
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await require_registration(update)
        return ConversationHandler.END

    status = 'active'
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT status FROM users WHERE user_id = %s", (user_id,))
                res = cursor.fetchone()
                if res: status = res[0]
    finally:
        conn.close()

    if status == 'banned':
        await update.message.reply_text(TEXTS['banned'])
        return ConversationHandler.END

    keyboard = [[TEXTS['search_m'], TEXTS['search_f']], [TEXTS['search_nearby'], TEXTS['search_all']], [TEXTS['cancel']]]
    await update.message.reply_text(TEXTS['search_prompt'], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_FILTER

async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_registered(update.effective_user.id):
        await require_registration(update)
        return ConversationHandler.END

    choice = update.message.text
    if '❌' in choice:
        await update.message.reply_text(TEXTS['cancelled'], reply_markup=get_main_menu())
        return ConversationHandler.END
    
    filter_code = 'all'
    if 'Male' in choice or '👨' in choice: filter_code = 'male'
    elif 'Female' in choice or '👩' in choice: filter_code = 'female'
    elif 'Nearby' in choice or '📍' in choice: filter_code = 'nearby'
    
    await find_and_send_user(update, context, filter_code)
    return SEARCH_FILTER 

# --- ACTIONS ---
async def action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try: await query.answer()
    except: pass
    
    if not is_registered(update.effective_user.id):
        await require_registration(update)
        return

    data = query.data.split('_')
    action = data[0]
    sender_id = update.effective_user.id
    
    conn = get_connection()
    
    if action == 'vis':
        new_status = int(data[1])
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET is_visible = %s WHERE user_id = %s", (new_status, sender_id))
        finally:
            conn.close()
            
        msg = TEXTS['vis_shown'] if new_status == 1 else TEXTS['vis_hidden']
        await query.message.reply_text(msg)
        await my_profile(update, context) 
        return
    
    if action == "next":
        filter_type = data[1] 
        try: current = int(data[2])
        except: current = None
        await find_and_send_user(update, context, filter_type, exclude_id=current)
        return

    try: target_id = int(data[1])
    except: return
    
    if sender_id == target_id: return

    if action == "like":
        sender = None
        is_match = False
        already_liked = False
        
        try:
            with conn:
                with conn.cursor() as cursor:
                    # Check existing like
                    cursor.execute("SELECT id FROM likes WHERE sender_id = %s AND receiver_id = %s", (sender_id, target_id))
                    if cursor.fetchone():
                        already_liked = True
                    else:
                        # Insert Like
                        cursor.execute("INSERT INTO likes (sender_id, receiver_id) VALUES (%s, %s)", (sender_id, target_id))
                        
                        # Get Sender Info
                        cursor.execute("SELECT * FROM users WHERE user_id = %s", (sender_id,))
                        sender = cursor.fetchone()
                        
                        # Check Match
                        cursor.execute("SELECT id FROM likes WHERE sender_id = %s AND receiver_id = %s", (target_id, sender_id))
                        is_match = cursor.fetchone() is not None
        except Exception as e:
            print(f"Like Error: {e}")
        finally:
            conn.close()

        if already_liked:
            await query.message.reply_text(TEXTS['already_liked'])
            return

        if is_match:
            # Need to fetch Target Name
            target_name = "User"
            conn = get_connection()
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT name FROM users WHERE user_id = %s", (target_id,))
                        res = cursor.fetchone()
                        if res: target_name = res[0]
            finally:
                conn.close()

            await query.message.reply_text(TEXTS['match_msg'].format(name=escape_md(target_name), id=target_id), parse_mode='Markdown')
            try:
                # Use sender info (sender[1] is name)
                sender_name = sender[1] if sender else "Someone"
                await context.bot.send_message(chat_id=target_id, text=TEXTS['match_msg'].format(name=escape_md(sender_name), id=sender_id), parse_mode='Markdown')
            except: pass
        else:
            if sender:
                safe_name = escape_md(sender[1])
                sender_photo = sender[6]
                msg = f"{TEXTS['got_like']}\n\n👤 [{safe_name}](tg://user?id={sender_id})\n📝 {sender[5]}"
                try:
                    if sender_photo:
                        await context.bot.send_photo(chat_id=target_id, photo=sender_photo, caption=msg, parse_mode='Markdown')
                    else:
                        await context.bot.send_message(chat_id=target_id, text="❤️ **You got a Like!**\n(User has no photo)\n\n" + msg, parse_mode='Markdown')
                    
                    await query.message.reply_text(TEXTS['like_sent'])
                except Forbidden:
                    await query.message.reply_text("✅ Heart saved (User blocked bot).")
                except:
                    await query.message.reply_text("✅ Heart saved.")

    elif action == "report" and ADMIN_ID != 0:
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ REPORT: User ID {target_id}")
            await query.message.reply_text("✅ Reported.")
        except: pass

# --- PROFILE & EDIT ---
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await require_registration(update)
        return

    user = None
    likes_count = 0
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*) FROM likes WHERE receiver_id = %s", (user_id,))
                likes_count = cursor.fetchone()[0]
    finally:
        conn.close()

    if not user:
        await require_registration(update)
        return
    
    safe_name = escape_md(user[1])
    is_vis = user[10] if len(user) > 10 else 1 
    status_text = "🟢 Public" if is_vis == 1 else "🔴 Ghost"
    caption = f"{TEXTS['btn_profile']}\n\n👤 {TEXTS['lbl_name']}*{safe_name}*\n🎂 Age: {user[2]}\n❤️ Likes: `{likes_count}`\n👁️ {status_text}\n📍 {TEXTS['lbl_prov']} {user[4]}\n🔍 {TEXTS['lbl_look']} {user[5]}\n"
    
    vis_btn = TEXTS['btn_hide'] if is_vis == 1 else TEXTS['btn_show']
    vis_cb = "vis_0" if is_vis == 1 else "vis_1"
    
    keyboard = [
        [InlineKeyboardButton(TEXTS['btn_edit_name'], callback_data='edit_name'), InlineKeyboardButton(TEXTS['btn_edit_age'], callback_data='edit_age')],
        [InlineKeyboardButton(TEXTS['btn_edit_look'], callback_data='edit_look'), InlineKeyboardButton(TEXTS['btn_edit_photo'], callback_data='edit_photo')],
        [InlineKeyboardButton(TEXTS['btn_edit_prov'], callback_data='edit_prov')],
        [InlineKeyboardButton(vis_btn, callback_data=vis_cb)]
    ]
    
    photo_id = user[6]
    
    if update.callback_query:
        try:
            if photo_id:
                await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.callback_query.message.delete()
                await context.bot.send_message(chat_id=user_id, text="⚠️ **No Photo Set**\n\n" + caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except BadRequest: pass
        except: pass
    else:
        if photo_id:
            await update.message.reply_photo(photo=photo_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.message.reply_text(text="⚠️ **No Photo Set**\n\n" + caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_likes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await require_registration(update)
        return

    likers = []
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                query = 'SELECT u.user_id, u.name, u.username FROM likes l JOIN users u ON l.sender_id = u.user_id WHERE l.receiver_id = %s ORDER BY l.timestamp DESC LIMIT 20'
                cursor.execute(query, (user_id,))
                likers = cursor.fetchall()
    finally:
        conn.close()

    if not likers:
        await update.message.reply_text(TEXTS['no_likes'])
        return
    msg = TEXTS['likes_title']
    for l in likers:
        link = f"tg://user?id={l[0]}"
        msg += f"❤️ [{escape_md(l[1])}]({link})\n"
    await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

# --- EDIT HANDLERS ---
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if not is_registered(update.effective_user.id):
        await require_registration(update)
        return ConversationHandler.END
    
    if query.data == 'edit_look':
        await query.message.reply_text(TEXTS['enter_new_look'])
        return EDIT_LOOKING_FOR
    elif query.data == 'edit_photo':
        await query.message.reply_text(TEXTS['enter_new_photo'])
        return EDIT_PHOTO
    elif query.data == 'edit_prov':
        await query.message.reply_text(TEXTS['enter_new_prov'])
        return EDIT_PROVINCE
    elif query.data == 'edit_name':
        await query.message.reply_text(TEXTS['enter_new_name'])
        return EDIT_NAME
    elif query.data == 'edit_age':
        await query.message.reply_text(TEXTS['enter_new_age'])
        return EDIT_AGE
        
    return ConversationHandler.END

async def save_edit_look(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET looking_for = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['updated'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def save_edit_prov(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET province = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['updated'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def save_edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET photo_id = %s WHERE user_id = %s", (update.message.photo[-1].file_id, update.effective_user.id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['updated'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def save_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET name = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['updated'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def save_edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text
    if not age.isdigit() or int(age) < 12 or int(age) > 100:
        await update.message.reply_text(TEXTS['age_error'])
        return EDIT_AGE
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET age = %s WHERE user_id = %s", (int(age), update.effective_user.id))
    finally:
        conn.close()
    await update.message.reply_text(TEXTS['updated'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def bad_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(TEXTS['wrong_input_photo'])
    return EDIT_PHOTO

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(TEXTS['cancelled'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_registered(update.effective_user.id):
        await require_registration(update)
        return ConversationHandler.END
    
    await update.message.reply_text(TEXTS['help_msg'], parse_mode='Markdown', reply_markup=get_main_menu())
    return ConversationHandler.END

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id = int(context.args[0])
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET status = 'banned' WHERE user_id = %s", (t_id,))
        finally:
            conn.close()
        await update.message.reply_text(f"🚫 Banned {t_id}")
    except: pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID: return
    count = 0
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
    finally:
        conn.close()
    await update.message.reply_text(f"Users: {count}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID: return
    
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text(TEXTS['broadcast_err'])
        return

    users = []
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users")
                users = cursor.fetchall()
    finally:
        conn.close()
    
    count = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=f"📢 **ANNOUNCEMENT:**\n\n{msg}", parse_mode='Markdown')
            count += 1
        except: pass 
    
    await update.message.reply_text(TEXTS['broadcast_sent'].format(count=count))