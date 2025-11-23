import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import (
    TOKEN, NAME, AGE, GENDER, PROVINCE, LOOKING_FOR, PHOTO, SEARCH_FILTER, 
    EDIT_LOOKING_FOR, EDIT_PHOTO, EDIT_PROVINCE, EDIT_NAME, EDIT_AGE, 
    TEXTS
)
from database import init_db
from keep_alive import keep_alive
import handlers as h

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    keep_alive()
    init_db()

    if not TOKEN:
        print("❌ Error: TOKEN missing.")
        return

    application = Application.builder().token(TOKEN).build()

    btn_search = f"^{TEXTS['btn_search']}$"
    btn_profile = f"^{TEXTS['btn_profile']}$"
    btn_likes = f"^{TEXTS['btn_likes']}$"
    btn_help = f"^{TEXTS['btn_help']}$"

    common = [
        CommandHandler("cancel", h.cancel),
        CommandHandler("start", h.start),
        CommandHandler("help", h.help_cmd),
        MessageHandler(filters.Regex(btn_profile), h.my_profile),
        MessageHandler(filters.Regex(btn_search), h.start_search),
        MessageHandler(filters.Regex(btn_help), h.help_cmd),
        MessageHandler(filters.Regex(btn_likes), h.show_likes)
    ]

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

    search_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(btn_search), h.start_search)],
        states={SEARCH_FILTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.perform_search)]},
        fallbacks=common,
    )

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

    application.add_handler(conv_handler)
    application.add_handler(search_handler)
    application.add_handler(edit_handler)
    
    application.add_handler(MessageHandler(filters.Regex(btn_profile), h.my_profile))
    application.add_handler(MessageHandler(filters.Regex(btn_help), h.help_cmd))
    application.add_handler(MessageHandler(filters.Regex(btn_likes), h.show_likes))
    
    application.add_handler(CallbackQueryHandler(h.action_callback, pattern="^(like|report|next|vis)_"))
    
    application.add_handler(CommandHandler("ban", h.ban_user))
    application.add_handler(CommandHandler("stats", h.stats))
    application.add_handler(CommandHandler("broadcast", h.broadcast))
    
    print("🚀 Bot is Running (No Delete Feature)...")
    application.run_polling()

if __name__ == '__main__':
    main()