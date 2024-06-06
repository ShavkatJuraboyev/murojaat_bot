from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CallbackContext
import logging
import time
from telegram.error import TimedOut

# Tokenni o'rnatamiz
TOKEN = 'YOUR_TOKEN'

# Loggerni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Conversation states
START, NAME, PHONE, MAIN_MENU, UPLOAD_FILES, DESCRIPTION, ASK_MORE_FILES = range(7)

# Foydalanuvchilar ma'lumotlarini saqlash uchun
user_data = {}

# Admin chat IDlarini ro'yxatini tuzamiz
admin_chat_ids = ['YOUR_ID']  # 2 3 ta admin bolsa

# Helper function to send a message with retry logic
def send_message_with_retry(bot, chat_id, text, retries=3, delay=5, **kwargs):
    for i in range(retries):
        try:
            return bot.send_message(chat_id=chat_id, text=text, **kwargs)
        except TimedOut:
            logging.warning(f"TimedOut error occurred. Retrying {i+1}/{retries}...")
            time.sleep(delay)
    logging.error("Failed to send message after several retries.")

def start(update: Update, context: CallbackContext) -> int:
    send_message_with_retry(context.bot, update.message.chat_id, "Assalomu alaykum!\n Botimizga xush kelibsiz\n Iltimos, ismingiz va familiyangizni kiriting:")
    return NAME

def name(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id] = {'name': update.message.text}
    send_message_with_retry(context.bot, update.message.chat_id, "Telefon raqamingizni kiriting:")
    return PHONE

def phone(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id]['phone'] = update.message.text

    keyboard = [
        [InlineKeyboardButton("Reklama berish", callback_data='advertise')],
        [InlineKeyboardButton("Shikoyat qilish", callback_data='complain')],
        [InlineKeyboardButton("Maqola joylash", callback_data='post_article')],
        [InlineKeyboardButton("Boshqa", callback_data='other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    send_message_with_retry(context.bot, update.message.chat_id, 'Kerakli bo\'limni tanlang:', reply_markup=reply_markup)
    return MAIN_MENU

def main_menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_data[query.message.chat_id]['option'] = query.data

    query.edit_message_text(text="Video, rasm yoki fayl yuklang:")
    return UPLOAD_FILES

def upload_files(update: Update, context: CallbackContext) -> int:
    if 'files' not in user_data[update.message.chat_id]:
        user_data[update.message.chat_id]['files'] = []

    user_data[update.message.chat_id]['files'].append(update.message)

    keyboard = [
        [InlineKeyboardButton("Ha", callback_data='yes')],
        [InlineKeyboardButton("Yo'q", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(user_data[update.message.chat_id]['files']) >= 1:
        send_message_with_retry(context.bot, update.message.chat_id, "Yana video, rasm yoki fayllar yuklashingizni xohlaysizmi?", reply_markup=reply_markup)
        return ASK_MORE_FILES
    else:
        send_message_with_retry(context.bot, update.message.chat_id, "Yana video, rasm yoki fayllar yuklashingiz mumkin:")
        return UPLOAD_FILES

def ask_more_files(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'yes':
        query.edit_message_text(text="Yana video, rasm yoki fayllar yuklashingiz mumkin:")
        return UPLOAD_FILES
    else:
        query.edit_message_text(text="Murojaat mazmunini yozing:")
        return DESCRIPTION

def description(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id]['description'] = update.message.text
    send_message_with_retry(context.bot, update.message.chat_id, "Murojaatingiz qabul qilindi. Admin javobini kuting.")
    
    # Ma'lumotlarni adminlarga yuborish
    user_chat_id = update.message.chat_id
    admin_message = f"Yangi murojaat:\n\n"
    admin_message += f"Ism: {user_data[user_chat_id]['name']}\n"
    admin_message += f"Telefon: {user_data[user_chat_id]['phone']}\n"
    admin_message += f"Murojat turi: {user_data[user_chat_id]['option']}\n"
    admin_message += f"Fayllar: {len(user_data[user_chat_id]['files'])}\n"
    admin_message += f"Mazmuni: {user_data[user_chat_id]['description']}\n"
    admin_message += f"User ID: {user_chat_id}\n"

    for admin_chat_id in admin_chat_ids:
        send_message_with_retry(context.bot, admin_chat_id, admin_message)
        for file in user_data[user_chat_id]['files']:
            if file.video:
                context.bot.send_video(chat_id=admin_chat_id, video=file.video.file_id)
            elif file.photo:
                context.bot.send_photo(chat_id=admin_chat_id, photo=file.photo[-1].file_id)
            elif file.document:
                context.bot.send_document(chat_id=admin_chat_id, document=file.document.file_id)

    return ConversationHandler.END

def admin_response(update: Update, context: CallbackContext) -> None:
    admin_chat_id = update.message.chat_id
    text = update.message.text

    if update.message.reply_to_message:
        original_message = update.message.reply_to_message.text
        user_chat_id = original_message.split('User ID: ')[1].strip()
        send_message_with_retry(context.bot, int(user_chat_id), text)

def cancel(update: Update, context: CallbackContext) -> int:
    send_message_with_retry(context.bot, update.message.chat_id, "Murojaat bekor qilindi.")
    return ConversationHandler.END

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, name)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, phone)],
            MAIN_MENU: [CallbackQueryHandler(main_menu)],
            UPLOAD_FILES: [MessageHandler(Filters.all & ~Filters.command, upload_files)],
            ASK_MORE_FILES: [CallbackQueryHandler(ask_more_files)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, description)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.reply, admin_response))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
