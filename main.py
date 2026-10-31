import os
import urllib.parse
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8893604989:AAGCdbkeZbaVWWkdEmfvRW-b9z9xLhJXGrk"

# Conversation handler holatlari
MANZIL_KIRITISH, TARQATISH = range(2)

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data_store[user_id] = {'addresses': []}
    
    keyboard = [["➕ Manzil kiritish"], ["🚚 Yuklarni tarqatishni boshlash"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Xush kelibsiz! Yetkazib berish botiga xush kelibsiz.\n\n"
        "Yangi yuk manzillarini kiritish uchun '➕ Manzil kiritish' tugmasini bosing.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def start_kiritish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Manzillarni matn ko'rinishida kiriting (Masalan: Shahriobod 320).\n\n"
        "Barcha manzillarni birma-bir yuborib bo'lgach '✅ Kiritishni tugatish' tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup([["✅ Kiritishni tugatish"]], resize_keyboard=True)
    )
    return MANZIL_KIRITISH

async def add_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {'addresses': []}
        
    text = update.message.text.strip()
    
    if text == "✅ Kiritishni tugatish":
        keyboard = [["🚚 Yuklarni tarqatishni boshlash"]]
        await update.message.reply_text(
            f"Barcha manzillar saqlandi! Jami: {len(user_data_store[user_id]['addresses'])} ta manzil.\n\n"
            "Toshkent shahri kirish postiga yetib kelganingizda '🚚 Yuklarni tarqatishni boshlash' tugmasini bosing.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return ConversationHandler.END
    
    user_data_store[user_id]['addresses'].append(text)
    count = len(user_data_store[user_id]['addresses'])
    await update.message.reply_text(f"📍 Manzil saqlandi: '{text}'. Jami kiritilgan manzillar: {count} ta.")
    return MANZIL_KIRITISH

async def start_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data_store or not user_data_store[user_id]['addresses']:
        await update.message.reply_text("Hali hech qanday manzil kiritilmagan! Avval '➕ Manzil kiritish' tugmasi orqali manzillarni kiriting.")
        return ConversationHandler.END

    await update.message.reply_text("Toshkentga xush kelibsiz! Tarqatishni boshlaymiz.")
    return await process_next_delivery(update, context)

async def process_next_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    addresses = user_data_store[user_id]['addresses']
    
    if not addresses:
        reply_markup = ReplyKeyboardMarkup([["➕ Manzil kiritish"]], resize_keyboard=True)
        await update.message.reply_text("🎉 **Bugungi missiya yakunlandi!** Barcha yuklar o'z egalariga yetkazildi.", reply_markup=reply_markup)
        return ConversationHandler.END

    # Navbatdagi manzilni olish
    next_address = addresses.pop(0)

    # Yandex Navigator / Maps uchun qidiruv linkini tayyorlash
    query = f"Tashkent {next_address}"
    encoded_query = urllib.parse.quote(query)
    yandex_link = f"https://yandex.ru/maps/?text={encoded_query}"
    
    msg = (
        f"📦 **Navbatdagi manzil:**\n"
        f"🏠 **{next_address}**\n\n"
        f"🗺 [Yandex Navigatorda ochish]({yandex_link})\n\n"
        f"Yukni topshirganingizdan so'ng **'✅ Yetkazildi'** tugmasini bosing."
    )
    
    keyboard = [["✅ Yetkazildi"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    return TARQATISH

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Manzil kiritish$"), start_kiritish),
            MessageHandler(filters.Regex("^🚚 Yuklarni tarqatishni boshlash$"), start_delivery),
            MessageHandler(filters.Regex("^✅ Yetkazildi$"), process_next_delivery)
        ],
        states={
            MANZIL_KIRITISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_address)],
            TARQATISH: [MessageHandler(filters.Regex("^✅ Yetkazildi$"), process_next_delivery)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
