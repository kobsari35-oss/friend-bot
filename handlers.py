import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import *
from utils import escape_md, find_and_send_user, broadcast_new_user, get_time_ago
from database import get_db_connection, release_db_connection

# --- HELPERS ---
def get_main_menu():
    return ReplyKeyboardMarkup([
        [TEXTS['btn_search'], TEXTS['btn_profile']],
        [TEXTS['btn_likes'], TEXTS['btn_help']]
    ], resize_keyboard=True)

def is_registered(user_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                return cursor.fetchone() is not None
    except: return False
    finally: release_db_connection(conn)

async def check_subscription_status(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except: return True 

# --- REGISTRATION ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if not get_db_connection():
        await update.message.reply_text("⚠️ System starting up. Please /start again.")
        return ConversationHandler.END

    if is_registered(user_id):
        await update.message.reply_text(TEXTS['menu_msg'], reply_markup=get_main_menu())
        return ConversationHandler.END

    conn = get_db_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO users (user_id, is_visible) VALUES (%s, 1) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        finally: release_db_connection(conn)

    if not await check_subscription_status(user_id, context):
        kb = [[InlineKeyboardButton(TEXTS['btn_join'], url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
              [InlineKeyboardButton(TEXTS['btn_check_sub'], callback_data="check_subscription")]]
        await update.message.reply_text(TEXTS['ask_sub'], reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        return ConversationHandler.END

    await update.message.reply_text(TEXTS['ask_name'], parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    return NAME

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if await check_subscription_status(update.effective_user.id, context):
        await query.message.delete()
        await context.bot.send_message(chat_id=update.effective_user.id, text=TEXTS['ask_name'], parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
        return NAME
    else:
        await query.answer(TEXTS['not_subbed'], show_alert=True)
        return ConversationHandler.END

# --- REGISTRATION STEPS ---
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db_connection()
    if not conn: return NAME
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET name = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally: release_db_connection(conn)
    await update.message.reply_text(TEXTS['ask_age'])
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text.isdigit() or not (12 <= int(update.message.text) <= 99):
        await update.message.reply_text(TEXTS['age_error'])
        return AGE
    conn = get_db_connection()
    if not conn: return AGE
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET age = %s WHERE user_id = %s", (int(update.message.text), update.effective_user.id))
    finally: release_db_connection(conn)
    kb = [[TEXTS['btn_male'], TEXTS['btn_female'], TEXTS['btn_other']]]
    await update.message.reply_text(TEXTS['ask_gender'], reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db_connection()
    if not conn: return GENDER
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET gender = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally: release_db_connection(conn)
    await update.message.reply_text(TEXTS['ask_prov'], reply_markup=ReplyKeyboardRemove())
    return PROVINCE

async def get_province(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db_connection()
    if not conn: return PROVINCE
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET province = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally: release_db_connection(conn)
    await update.message.reply_text(TEXTS['ask_looking'])
    return LOOKING_FOR

async def get_looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db_connection()
    if not conn: return LOOKING_FOR
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET looking_for = %s WHERE user_id = %s", (update.message.text, update.effective_user.id))
    finally: release_db_connection(conn)
    await update.message.reply_text(TEXTS['ask_photo'])
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text(TEXTS['wrong_input_photo'])
        return PHOTO
    
    photo_file = update.message.photo[-1].file_id
    user = update.effective_user
    conn = get_db_connection()
    if not conn: return PHOTO
    user_data = None

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET photo_id = %s, username = %s, first_name = %s WHERE user_id = %s", 
                               (photo_file, user.username, user.first_name, user.id))
                cursor.execute("SELECT name, age, gender, province FROM users WHERE user_id = %s", (user.id,))
                res = cursor.fetchone()
                if res:
                    user_data = {'id': user.id, 'photo': photo_file, 'name': res[0], 'age': res[1], 'gender': res[2], 'province': res[3]}
    finally: release_db_connection(conn)

    if user_data:
        asyncio.create_task(broadcast_new_user(context, user_data))

    await update.message.reply_text(TEXTS['reg_success'], parse_mode='Markdown', reply_markup=get_main_menu())
    return ConversationHandler.END

# --- SEARCH ---
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_registered(update.effective_user.id):
        await update.message.reply_text("⚠️ Please /start first.")
        return ConversationHandler.END
    
    kb = [[TEXTS['search_m'], TEXTS['search_f']], [TEXTS['search_nearby'], TEXTS['search_all']], [TEXTS['cancel']]]
    await update.message.reply_text(TEXTS['search_prompt'], reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return SEARCH_FILTER

async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == TEXTS['cancel'] or 'Back' in choice:
        await update.message.reply_text(TEXTS['cancelled'], reply_markup=get_main_menu())
        return ConversationHandler.END
    
    filter_code = None
    if 'Boys' in choice: filter_code = 'male'
    elif 'Girls' in choice: filter_code = 'female'
    elif 'Nearby' in choice: filter_code = 'nearby'
    elif 'Anyone' in choice: filter_code = 'all'

    if filter_code:
        await update.message.reply_text(f"🔍 Searching...", reply_markup=ReplyKeyboardRemove())
        await find_and_send_user(update, context, filter_code)
        return SEARCH_FILTER
    
    if choice in [TEXTS['btn_profile'], TEXTS['btn_likes'], TEXTS['btn_help']]:
        await update.message.reply_text("🏠 Menu", reply_markup=get_main_menu())
        return ConversationHandler.END
    
    await update.message.reply_text("⚠️ Invalid Option.")
    return SEARCH_FILTER

# --- ACTIONS & MATCHING SYSTEM ---
async def action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try: await query.answer()
    except: pass
    
    data = query.data.split('_')
    action = data[0]
    sender_id = update.effective_user.id
    
    if action == "stop":
        await query.message.delete()
        await context.bot.send_message(chat_id=sender_id, text=TEXTS['menu_msg'], reply_markup=get_main_menu())
        return
    if action == "next":
        try: await query.message.delete()
        except: pass
        if len(data) > 1:
            exclude = int(data[2]) if len(data) > 2 else None
            await find_and_send_user(update, context, data[1], exclude_id=exclude)
        return

    conn = get_db_connection()
    if not conn: return
    try:
        if action == 'vis':
            new_status = int(data[1])
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET is_visible = %s WHERE user_id = %s", (new_status, sender_id))
            await my_profile(update, context)
            return
        
        if len(data) < 2: return
        target_id = int(data[1])
        
        if action == "report":
            await query.message.reply_text("✅ Reported.")
            if ADMIN_ID != 0:
                report_text = f"🚨 **REPORT**\nUser `{sender_id}` reported `{target_id}` ([Link](tg://user?id={target_id}))"
                kb_admin = [[InlineKeyboardButton("🚫 BAN USER NOW", callback_data=f"ban_{target_id}")]]
                await context.bot.send_message(chat_id=ADMIN_ID, text=report_text, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode='Markdown')
        
        elif action == "ban":
            if sender_id != ADMIN_ID: return
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET status = 'banned' WHERE user_id = %s", (target_id,))
            await query.message.edit_text(f"🚫 **BANNED ID:** `{target_id}` ✅")

        elif action == "like":
            if sender_id == target_id: return
            match_found = False
            sender_data = None
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM likes WHERE sender_id=%s AND receiver_id=%s", (sender_id, target_id))
                    if cursor.fetchone():
                        await query.message.reply_text(TEXTS['already_liked'])
                        return
                    cursor.execute("INSERT INTO likes (sender_id, receiver_id) VALUES (%s, %s)", (sender_id, target_id))
                    
                    # CHECK MATCH
                    cursor.execute("SELECT 1 FROM likes WHERE sender_id=%s AND receiver_id=%s", (target_id, sender_id))
                    match_found = (cursor.fetchone() is not None)
                    
                    cursor.execute("SELECT name, photo_id FROM users WHERE user_id=%s", (sender_id,))
                    sender_data = cursor.fetchone()
            
            # --- UI: MATCH ALERT ---
            if match_found:
                kb_sender = [[InlineKeyboardButton(f"💬 Chat with User", url=f"tg://user?id={target_id}")]]
                await query.message.reply_text("🔥 **IT'S A MATCH!** 🔥\nStart chatting now!", reply_markup=InlineKeyboardMarkup(kb_sender))
                
                try: 
                    kb_receiver = [[InlineKeyboardButton(f"💬 Chat with {sender_data[0]}", url=f"tg://user?id={sender_id}")]]
                    await context.bot.send_message(
                        chat_id=target_id, 
                        text=f"🔥 **IT'S A MATCH!** 🔥\nYou matched with {escape_md(sender_data[0])}!", 
                        reply_markup=InlineKeyboardMarkup(kb_receiver),
                        parse_mode='Markdown'
                    )
                except: pass
            else:
                await query.message.reply_text("❤️ Like Sent!")
                if sender_data:
                    caption = f"😍 **Someone Liked You!**\n👤 **{escape_md(sender_data[0])}**"
                    try: await context.bot.send_photo(chat_id=target_id, photo=sender_data[1], caption=caption, parse_mode='Markdown')
                    except: pass
    except Exception as e:
        print(f"Action Error: {e}")
    finally: release_db_connection(conn)

# --- PROFILE UI (WITH LIKE COUNT) ---
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = get_db_connection()
    if not conn: return
    user = None
    like_count = 0 

    try:
        with conn:
            with conn.cursor() as cursor:
                # Get User
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                
                # Get Like Count
                cursor.execute("SELECT COUNT(*) FROM likes WHERE receiver_id = %s", (user_id,))
                res_likes = cursor.fetchone()
                if res_likes: like_count = res_likes[0]
                
    finally: release_db_connection(conn)

    if not user:
        await update.message.reply_text("⚠️ Register first.")
        return

    is_vis = user[10]
    vis_btn = TEXTS['btn_hide'] if is_vis else TEXTS['btn_show']
    vis_data = "vis_0" if is_vis else "vis_1"
    
    caption = (
        f"👤 **YOUR PROFILE CARD**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📛 **Name:** `{escape_md(user[1])}`\n"
        f"🎂 **Age:** `{user[2]}`  |  ⚧️ `{user[3]}`\n"
        f"📍 **Location:** `{escape_md(user[4])}`\n"
        f"❤️ **Likes:** `{like_count}`   🔥\n" 
        f"👁️ **Status:** {('✅ Visible' if is_vis else '👻 Hidden')}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 **Bio:**\n_{escape_md(user[5])}_"
    )
    
    kb = [
        [InlineKeyboardButton("📸 Change Photo", callback_data='edit_photo')],
        [InlineKeyboardButton("✏️ Name", callback_data='edit_name'), InlineKeyboardButton("✏️ Bio", callback_data='edit_look')],
        [InlineKeyboardButton("📍 City", callback_data='edit_prov'), InlineKeyboardButton("🎂 Age", callback_data='edit_age')],
        [InlineKeyboardButton(vis_btn, callback_data=vis_data)]
    ]
    
    if update.callback_query:
        try:
            if user[6]:
                await update.callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            else:
                await update.callback_query.message.edit_text(text="[No Photo]\n" + caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except: pass
    else:
        if user[6]:
            await update.message.reply_photo(photo=user[6], caption=caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        else:
            await update.message.reply_text(text="[No Photo]\n" + caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def show_likes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = get_db_connection()
    if not conn: return
    likers = []
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT u.name, u.user_id FROM likes l JOIN users u ON l.sender_id = u.user_id WHERE l.receiver_id = %s ORDER BY l.timestamp DESC LIMIT 10", (user_id,))
                likers = cursor.fetchall()
    finally: release_db_connection(conn)
    
    if not likers:
        await update.message.reply_text(TEXTS['no_likes'])
    else:
        msg = "💘 **People who liked you:**\n\n"
        for name, uid in likers:
            msg += f"👤 [{escape_md(name)}](tg://user?id={uid})\n"
        await update.message.reply_text(msg, parse_mode='Markdown')

# --- EDIT HANDLERS ---
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == 'edit_name':
        await query.message.reply_text(TEXTS['enter_new_name'])
        return EDIT_NAME
    elif data == 'edit_age':
        await query.message.reply_text(TEXTS['enter_new_age'])
        return EDIT_AGE
    elif data == 'edit_prov':
        await query.message.reply_text(TEXTS['enter_new_prov'])
        return EDIT_PROVINCE
    elif data == 'edit_look':
        await query.message.reply_text(TEXTS['enter_new_look'])
        return EDIT_LOOKING_FOR
    elif data == 'edit_photo':
        await query.message.reply_text(TEXTS['enter_new_photo'])
        return EDIT_PHOTO
    return ConversationHandler.END

async def save_edit_generic(update: Update, context: ContextTypes.DEFAULT_TYPE, col: str) -> int:
    conn = get_db_connection()
    if not conn: return ConversationHandler.END
    val = update.message.text
    if col == 'photo_id': 
        if not update.message.photo:
            await update.message.reply_text(TEXTS['wrong_input_photo'])
            return EDIT_PHOTO
        val = update.message.photo[-1].file_id
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE users SET {col} = %s WHERE user_id = %s", (val, update.effective_user.id))
    finally: release_db_connection(conn)
    
    await update.message.reply_text(TEXTS['updated'], reply_markup=get_main_menu())
    return ConversationHandler.END

async def save_edit_name(u, c): return await save_edit_generic(u, c, 'name')
async def save_edit_look(u, c): return await save_edit_generic(u, c, 'looking_for')
async def save_edit_prov(u, c): return await save_edit_generic(u, c, 'province')
async def save_edit_photo(u, c): return await save_edit_generic(u, c, 'photo_id')
async def save_edit_age(u, c): 
    if not u.message.text.isdigit():
        await u.message.reply_text(TEXTS['age_error'])
        return EDIT_AGE
    return await save_edit_generic(u, c, 'age')
async def bad_photo(u, c): await u.message.reply_text(TEXTS['wrong_input_photo']); return EDIT_PHOTO

# --- ADMIN & MISC ---
async def cancel(update, context): await update.message.reply_text("🏠 Home", reply_markup=get_main_menu()); return ConversationHandler.END
async def help_cmd(update, context): await update.message.reply_text(TEXTS['help_msg'], parse_mode='Markdown', reply_markup=get_main_menu())

async def ban_user(update, context):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id = int(context.args[0])
        conn = get_db_connection()
        if not conn: return
        with conn:
            with conn.cursor() as cur: cur.execute("UPDATE users SET status='banned' WHERE user_id=%s", (t_id,))
        release_db_connection(conn)
        await update.message.reply_text(f"🚫 Banned {t_id}")
    except: await update.message.reply_text("Usage: /ban ID")

async def stats(update, context):
    if update.effective_user.id != ADMIN_ID: return
    conn = get_db_connection()
    if not conn: return
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            tot = cur.fetchone()[0]
    release_db_connection(conn)
    await update.message.reply_text(f"📊 Users: {tot}")

async def broadcast(update, context):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: return
    conn = get_db_connection()
    if not conn: return
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()
    release_db_connection(conn)
    await update.message.reply_text("Broadcasting...")
    for u in users:
        try: await context.bot.send_message(u[0], f"📢 {msg}")
        except: pass