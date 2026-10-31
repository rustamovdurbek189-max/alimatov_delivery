import os
import math
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8910663587:AAFGJKbqjjPrZIJ2n8qxCFn-RVOqsW0h5o4"

# Conversation handler holatlari
MANZIL_KIRITISH, POST_LOKATSIYA, TARQATISH = range(3)

# Ma'lumotlarni xotirada saqlash uchun
user_data_store = {}

def get_distance(lat1, lon1, lat2, lon2):
    """Ikki nuqta orasidagi masofani hisoblash (Haversine formulasi)"""
    R = 6371  # Yer radiusi (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data_store[user_id] = {'locations': []}
    
    keyboard = [["➕ Manzil kiritish"], ["🚚 Yuklarni tarqatishni boshlash"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Xush kelibsiz! Yetkazib berish botiga xush kelibsiz.\n\n"
        "Yangi yuklarni kiritish uchun '➕ Manzil kiritish' tugmasini bosing.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def start_kiritish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Manzilni kiriting.\n\n"
        "📌 **Muhim:** Aniqroq marshrut tuzish uchun ushbu nuqtaning **Telegram Geolokatsiyasini (Location)** yuboring.\n\n"
        "Barcha manzillarni yuborib bo'lgach '✅ Kiritishni tugatish' tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup([["✅ Kiritishni tugatish"]], resize_keyboard=True)
    )
    return MANZIL_KIRITISH

async def add_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {'locations': []}
        
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        user_data_store[user_id]['locations'].append({'lat': lat, 'lon': lon})
        count = len(user_data_store[user_id]['locations'])
        await update.message.reply_text(f"📍 Location qabul qilindi! Jami kiritilgan manzillar: {count} ta.")
    else:
        text = update.message.text
        if text == "✅ Kiritishni tugatish":
            keyboard = [["🚚 Yuklarni tarqatishni boshlash"]]
            await update.message.reply_text(
                "Barcha manzillar saqlandi!\n\n"
                "Toshkent shahri kirish postiga yetib kelganingizda '🚚 Yuklarni tarqatishni boshlash' tugmasini bosing.",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return ConversationHandler.END
        
        await update.message.reply_text("Iltimos, manzil aniq bo'lishi uchun Telegram orqali **Location (Geolokatsiya)** yuboring.")
    return MANZIL_KIRITISH

async def start_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data_store or not user_data_store[user_id]['locations']:
        await update.message.reply_text("Hali hech qanday manzil kiritilmagan! Avval '➕ Manzil kiritish' tugmasi orqali manzillarni kiriting.")
        return ConversationHandler.END

    loc_button = KeyboardButton("📍 Hozirgi joylashuvimni yuborish (Post)", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[loc_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "Toshkent shahri kirish postiga yetib kelgan bo'lsangiz, pastdagi tugmani bosib hozirgi joylashuvingizni (Location) yuboring:",
        reply_markup=reply_markup
    )
    return POST_LOKATSIYA

async def process_next_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if update.message.location:
        curr_lat = update.message.location.latitude
        curr_lon = update.message.location.longitude
        user_data_store[user_id]['last_pos'] = (curr_lat, curr_lon)
    elif 'last_pos' in user_data_store[user_id]:
        curr_lat, curr_lon = user_data_store[user_id]['last_pos']
    else:
        await update.message.reply_text("Joylashuv aniqlanmadi. Qaytadan harakat qilib ko'ring.")
        return ConversationHandler.END

    locations = user_data_store[user_id]['locations']
    
    if not locations:
        reply_markup = ReplyKeyboardMarkup([["➕ Manzil kiritish"]], resize_keyboard=True)
        await update.message.reply_text("🎉 **Bugungi missiya yakunlandi!** Barcha yuklar o'z egalariga yetkazildi.", reply_markup=reply_markup)
        return ConversationHandler.END

    # Eng yaqin manzilni hisoblash
    nearest_idx = 0
    min_dist = float('inf')
    
    for idx, loc in enumerate(locations):
        dist = get_distance(curr_lat, curr_lon, loc['lat'], loc['lon'])
        if dist < min_dist:
            min_dist = dist
            nearest_idx = idx

    nearest = locations.pop(nearest_idx)
    user_data_store[user_id]['last_pos'] = (nearest['lat'], nearest['lon'])

    yandex_link = f"https://yandex.ru/navi/?whatshere[point]={nearest['lon']},{nearest['lat']}&whatshere[zoom]=18"
    
    msg = (
        f"📦 **Navbatdagi eng yaqin manzil:**\n"
        f"📏 Masofa: taxminan {min_dist:.2f} km\n\n"
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
            MANZIL_KIRITISH: [MessageHandler(filters.LOCATION | filters.TEXT, add_location)],
            POST_LOKATSIYA: [MessageHandler(filters.LOCATION, process_next_delivery)],
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
