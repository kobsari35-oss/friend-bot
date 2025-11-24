import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
except:
    ADMIN_ID = 0

DB_NAME = 'friends_bot.db'
REQUIRED_CHANNEL = '@make_friend2025' 

# --- STATES ---
NAME, AGE, GENDER, PROVINCE, LOOKING_FOR, PHOTO, SEARCH_FILTER = range(7)
EDIT_LOOKING_FOR, EDIT_PHOTO, EDIT_PROVINCE, EDIT_NAME, EDIT_AGE = range(7, 12)

# --- TEXTS (UI DESIGNED) ---
TEXTS = {
    # --- Registration ---
    'ask_name': (
        "👋 **Welcome to Friends Bot!** ✨\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Let's create your profile to find matches.\n\n"
        "👉 **What is your Name?**"
    ),
    'ask_age': "🎂 **How old are you?**\n(Send a number, e.g., 22)",
    'ask_gender': "⚧️ **What is your gender?**",
    'ask_prov': "📍 **Which city do you live in?**",
    'ask_looking': "🔍 **What are you looking for?**\n(e.g., Relationship, Friends, Chat)",
    'ask_photo': "📸 **Upload a Profile Photo**\n(This will be your first impression!)",
    
    'reg_success': "🎉 **Registration Complete!**\n\nYou are now ready to find friends.",
    'age_error': "⚠️ **Invalid Age!** Please enter a number between 12 and 100.",
    'wrong_input_photo': "⚠️ **Please send a Photo!** (Not a file)",

    # --- Subscription ---
    'ask_sub': (
        "🛑 **Access Restricted**\n\n"
        "Please join our community channel to use the bot."
    ),
    'btn_join': "📢 Join Channel",
    'btn_check_sub': "✅ I have Joined",
    'not_subbed': "❌ You haven't joined yet!",
    
    # --- Main Menu ---
    'btn_search': '🚀 Start Matching', 
    'btn_profile': '👤 My Profile', 
    'btn_likes': '💘 Admirers',
    'btn_help': '❓ Guide',
    'menu_msg': (
        "✨ **Main Menu** ✨\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Select an option below to start:"
    ),

    # --- Help ---
    'help_msg': (
        "🔰 **User Guide:**\n\n"
        "🚀 **Matching:** Find random people.\n"
        "👤 **Profile:** Edit your info/photo.\n"
        "💘 **Admirers:** See who liked you.\n"
        "👻 **Ghost Mode:** Hide your profile."
    ),

    # --- Search ---
    'search_prompt': "🔍 **Who do you want to find?**",
    'search_m': 'Boys 👨', 
    'search_f': 'Girls 👩', 
    'search_nearby': 'Nearby 📍', 
    'search_all': 'Anyone 🌎', 
    'cancel': '🔙 Menu',
    'cancelled': "🏠 **Welcome Back.**", 
    
    'not_found': "💔 **No new users found.**\nCheck back later!",
    'not_found_nearby': "💔 **No users nearby.**\nTry searching 'Anyone'.",
    
    'btn_next': "⏭️ Skip",
    'btn_stop': "❌ Stop",
    
    # --- Actions ---
    'like_btn': "❤️ LIKE", 
    'report_btn': "⚠️ Report",
    'like_sent': "❤️ **Like Sent!**",
    'already_liked': "⚠️ You already liked them.",
    
    # --- Visibility ---
    'btn_hide': "👻 Ghost Mode (OFF)", 
    'btn_show': "👁️ Visible (ON)",
    
    'likes_title': "💘 **People who liked you:**\n\n",
    'no_likes': "💔 **No likes yet.**\nTry updating your photo!",

    'btn_male': 'Male 👨', 'btn_female': 'Female 👩', 'btn_other': 'Other 🌈',
    
    # --- Edit Features ---
    'btn_edit_look': "📝 Bio", 
    'btn_edit_photo': "📸 Photo", 
    'btn_edit_prov': "📍 City",
    'btn_edit_name': "✏️ Name", 
    'btn_edit_age': "🎂 Age",
    'updated': "✅ **Profile Updated!**",
    
    'enter_new_look': "📝 **Enter new Bio:**",
    'enter_new_prov': "📍 **Enter new City:**",
    'enter_new_photo': "📸 **Send new Photo:**",
    'enter_new_name': "✏️ **Enter new Name:**",
    'enter_new_age': "🎂 **Enter new Age:**",

    # --- New User Alert ---
    'new_user_alert': (
        "🔔 **NEW MEMBER!**\n"
        "👤 {name}, {age}\n"
        "📍 {prov}\n"
        "👇 *Find them in Search!*"
    )
}