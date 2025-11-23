import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import (
    TOKEN, NAME, AGE, GENDER, PROVINCE, LOOKING_FOR, PHOTO, SEARCH_FILTER, 
    EDIT_LOOKING_FOR, EDIT_PHOTO, EDIT_PROVINCE, EDIT_NAME, EDIT_AGE, 
    TEXTS
)
from database import init_db
from keep_alive import keep_alive
import handlers as h

# បើក Logging ដើម្បីមើល Error
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    # 1. បើក Web Server (សម្រាប់ UptimeRobot)
    keep_alive()
    
    # 2. ភ្ជាប់ Database (PostgreSQL)
    init_db()

    if not TOKEN:
        print("❌ Error: TOKEN missing.")
        return

    # 3. បង្កើត Application
    application = Application.builder().token(TOKEN).build()

    # --- កំណត់ពាក្យសម្រាប់ចាប់យកការចុចប៊ូតុង ---
    btn_search = f"^{TEXTS['btn_search']}$"
    btn_profile = f"^{TEXTS['btn_profile']}$"
    btn_likes = f"^{TEXTS['btn_likes']}$"
    btn_help = f"^{TEXTS['btn_help']}$"

    # --- Handlers ធម្មតា ---
    common = [
        CommandHandler("cancel", h.cancel),
        CommandHandler("start", h.start),
        CommandHandler("help", h.help_cmd),
        MessageHandler(filters.Regex(btn_profile), h.my_profile),
        MessageHandler(filters.Regex(btn_search), h.start_search),
        MessageHandler(filters.Regex(btn_help), h.help_cmd),
        MessageHandler(filters.Regex(btn_likes), h.show_likes)
    ]

    # --- Conversation: ចុះឈ្មោះ (Registration) ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", h.start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_gender)],
            PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_province)],
            LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_looking_for)],
            PHOTO: [MessageHandler(filters.PHOTO, h.get_photo)],
        },
        fallbacks=common,
    )

    # --- Conversation: ស្វែងរក (Search) ---
    search_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(btn_search), h.start_search)],
        states={SEARCH_FILTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.perform_search)]},
        fallbacks=common,
    )

    # --- Conversation: កែប្រែប្រវត្តិរូប (Edit Profile) ---
    edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.edit_start, pattern="^edit_")],
        states={
            EDIT_LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_look)],
            EDIT_PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_prov)], 
            EDIT_PHOTO: [
                MessageHandler(filters.PHOTO, h.save_edit_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, h.bad_photo)
            ],
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_name)],
            EDIT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_age)],
        },
        fallbacks=common,
    )

    # Add Handlers
    application.add_handler(conv_handler)
    application.add_handler(search_handler)
    application.add_handler(edit_handler)
    
    # Add Menu Handlers
    application.add_handler(MessageHandler(filters.Regex(btn_profile), h.my_profile))
    application.add_handler(MessageHandler(filters.Regex(btn_help), h.help_cmd))
    application.add_handler(MessageHandler(filters.Regex(btn_likes), h.show_likes))
    
    # Add Callback Handlers (Like, Next, Report, Visibility)
    application.add_handler(CallbackQueryHandler(h.action_callback, pattern="^(like|report|next|vis)_"))
    
    # Add Admin Commands
    application.add_handler(CommandHandler("ban", h.ban_user))
    application.add_handler(CommandHandler("stats", h.stats))
    application.add_handler(CommandHandler("broadcast", h.broadcast))
    
    print("🚀 Bot is Starting on Render...")

    # --- FIX CONFLICT ERROR (ដំណោះស្រាយបញ្ហា Conflict) ---
    # drop_pending_updates=True: លុបសារដែលកកស្ទះចោល ដើម្បីឱ្យ Bot ថ្មីដំណើរការបានលឿន
    # allowed_updates=Update.ALL_TYPES: អនុញ្ញាតឱ្យទទួលគ្រប់ប្រភេទសារ
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()