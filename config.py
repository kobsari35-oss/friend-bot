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

# --- STATES ---
NAME, AGE, GENDER, PROVINCE, LOOKING_FOR, PHOTO, SEARCH_FILTER = range(7)
EDIT_LOOKING_FOR, EDIT_PHOTO, EDIT_PROVINCE, EDIT_NAME, EDIT_AGE = range(7, 12) # ដក DELETE ចេញ

# --- TEXTS ---
TEXTS = {
    # --- Registration ---
    'ask_name': (
        "👋 **Welcome to Make Friend Community!** 🌟\n\n"
        "Here you can connect with new friends or find a partner nearby.\n"
        "Let's set up your profile to get started.\n\n"
        "👉 **First, what is your name?**"
    ),
    'ask_age': "🎂 **Nice to meet you!**\nHow old are you? (Please enter a number)",
    'ask_gender': "⚧️ **What is your gender?**",
    'ask_prov': "📍 **Where are you currently living?**\n(City or Province)",
    'ask_looking': "🔍 **What are you looking for?**\n(e.g., New Friends, Dating, Chatting...)",
    'ask_photo': "📸 **One last step!**\nPlease send a photo of yourself so others can see you.",
    
    'reg_success': "✅ **Registration Successful!**\nWelcome aboard! You can now start searching.",
    'age_error': "⚠️ **Invalid Age!**\nPlease enter a number between 12 and 100.",
    'wrong_input_photo': "⚠️ **Please send a Photo!**\n(Files or Text are not accepted)",

    # --- Main Menu ---
    'btn_search': '🔍 Find Partner', 
    'btn_profile': '📂 My Profile', 
    'btn_likes': '❤️ Who Liked Me',
    'btn_help': 'ℹ️ Help / Guide',
    'menu_msg': "👇 **Main Menu:**\nChoose an option below:",

    # --- Help ---
    'help_msg': (
        "📖 **User Guide:**\n\n"
        "1️⃣ **Find Partner:** Browse users randomly or nearby.\n"
        "2️⃣ **My Profile:** View or edit your info & visibility.\n"
        "3️⃣ **Who Liked Me:** See people who sent you a heart.\n\n"
        "🛡️ *Tip: Be polite and safe when chatting!*"
    ),

    # --- Search ---
    'search_prompt': "🔍 **Who do you want to find today?**",
    'search_m': 'Find Male 👨', 
    'search_f': 'Find Female 👩', 
    'search_nearby': 'Find Nearby 📍', 
    'search_all': 'Find All 🌎', 
    'cancel': 'Cancel ❌',
    'cancelled': "✅ Operation Cancelled.", 
    
    'not_found': "😢 **No new users found.**\nPlease try again later!",
    'not_found_nearby': "😢 **No users found nearby.**\nTry searching 'Find All' instead.",
    'found': "✨ **New Friend Found!** ✨",
    'btn_next': "Next Person ➡️",
    'click_to_chat': "👉 **Click Name to Chat!**",

    # --- Actions ---
    'like_btn': "❤️ Like", 
    'report_btn': "⚠️ Report",
    'like_sent': "✅ **Heart sent!** We hope they like you back.",
    'already_liked': "⚠️ **You already liked this person!**",
    'got_like': "❤️ **Someone likes you!**",
    'match_msg': "💘 **IT'S A MATCH!** 💘\n\nYou and [{name}](tg://user?id={id}) liked each other!\n**Start chatting now!**",
    
    # --- Visibility ---
    'btn_hide': "🛡️ Go Ghost (Hide)", 
    'btn_show': "👀 Go Public (Show)",
    'vis_hidden': "✅ **You are now Hidden.**\nPeople won't find you in search.",
    'vis_shown': "✅ **You are now Visible.**\nPeople can find you again!",
    
    'likes_title': "❤️ **People who liked you:**\n\n",
    'no_likes': "😢 No likes yet.\nTry updating your photo to get more attention!",

    'banned': "🚫 **You are Banned** from using this bot.",
    'btn_male': 'Male 👨', 'btn_female': 'Female 👩', 'btn_other': 'Other 🌈',
    
    # --- Edit Features ---
    'btn_edit_look': "✏️ Purpose", 
    'btn_edit_photo': "📸 Photo", 
    'btn_edit_prov': "📍 Location",
    'btn_edit_name': "✏️ Name",
    'btn_edit_age': "🎂 Age",
    'updated': "✅ **Profile Updated Successfully!**",
    
    'enter_new_look': "✍️ **Enter new text for 'Looking For':**",
    'enter_new_prov': "📍 **Enter your new City/Province:**",
    'enter_new_photo': "📸 **Send your new Photo:**",
    'enter_new_name': "✍️ **Enter your new Name:**",
    'enter_new_age': "🎂 **Enter your new Age:**",
    
    # --- Broadcast ---
    'broadcast_sent': "📢 **Broadcast sent to {count} users!**",
    'broadcast_err': "⚠️ Usage: /broadcast [Your Message]",
    
    'lbl_name': "Name: ", 'lbl_prov': "City: ", 'lbl_look': "Seeking: "
}