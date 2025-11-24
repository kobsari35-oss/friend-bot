import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN, NAME, AGE, GENDER, PROVINCE, LOOKING_FOR, PHOTO, SEARCH_FILTER, EDIT_NAME, EDIT_AGE, EDIT_PROVINCE, EDIT_PHOTO, EDIT_LOOKING_FOR
import handlers as h
from database import init_db
from keep_alive import keep_alive

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    keep_alive()
    init_db()

    if not TOKEN:
        print("❌ Error: BOT_TOKEN is missing")
        return

    app = Application.builder().token(TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[
            CommandHandler('start', h.start),
            CallbackQueryHandler(h.check_subscription_callback, pattern='^check_subscription$')
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_gender)],
            PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_province)],
            LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.get_looking_for)],
            PHOTO: [MessageHandler(filters.PHOTO, h.get_photo)]
        },
        fallbacks=[CommandHandler('cancel', h.cancel)]
    )

    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(🚀 Start Matching|Start Matching)$"), h.start_search)],
        states={
            SEARCH_FILTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.perform_search)]
        },
        fallbacks=[
            CommandHandler('cancel', h.cancel),
            MessageHandler(filters.Regex("^(Menu|🔙 Menu)$"), h.cancel)
        ]
    )

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.edit_start, pattern='^edit_')],
        states={
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_name)],
            EDIT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_age)],
            EDIT_PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_prov)],
            EDIT_LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, h.save_edit_look)],
            EDIT_PHOTO: [
                MessageHandler(filters.PHOTO, h.save_edit_photo),
                MessageHandler(filters.ALL, h.bad_photo)
            ]
        },
        fallbacks=[CommandHandler('cancel', h.cancel)]
    )

    app.add_handler(reg_conv)
    app.add_handler(search_conv)
    app.add_handler(edit_conv)
    
    app.add_handler(MessageHandler(filters.Regex("Profile"), h.my_profile))
    app.add_handler(MessageHandler(filters.Regex("Admirers"), h.show_likes))
    app.add_handler(MessageHandler(filters.Regex("Guide"), h.help_cmd))
    app.add_handler(CommandHandler("help", h.help_cmd))

    app.add_handler(CommandHandler("ban", h.ban_user))
    app.add_handler(CommandHandler("stats", h.stats))
    app.add_handler(CommandHandler("broadcast", h.broadcast))

    app.add_handler(CallbackQueryHandler(h.action_callback))

    print("🚀 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()