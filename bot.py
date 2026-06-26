import os, json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing BOT_TOKEN")

with open("config.json", encoding="utf-8") as f:
    CONFIG = json.load(f)
with open("routes.json", encoding="utf-8") as f:
    ROUTES = json.load(f)

LANGUAGES = {"vi":"🇻🇳 Tiếng Việt","en":"🇬🇧 English","ru":"🇷🇺 Русский"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(v, callback_data=f"lang:{k}")] for k,v in LANGUAGES.items()]
    await update.message.reply_text("✈️ CAM RANH AIRPORT TRANSFER\n\nChoose language:", reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("lang:"):
        kb = [[InlineKeyboardButton(r, callback_data=f"route:{r}")] for r in ROUTES]
        kb.append([InlineKeyboardButton("Other destination", callback_data="route:other")])
        await q.edit_message_text("📍 Select destination:", reply_markup=InlineKeyboardMarkup(kb))
        return
    if data.startswith("route:"):
        route = data.split(":",1)[1]
        if route == 'other':
            await q.edit_message_text(f"Telegram: {CONFIG['telegram_contact']}\nWhatsApp: {CONFIG['whatsapp']}")
            return
        context.user_data['route'] = route
        kb = [[InlineKeyboardButton(v, callback_data=f"vehicle:{v}")] for v in ROUTES[route]]
        await q.edit_message_text(f"🚖 {route}\n\nChoose vehicle:", reply_markup=InlineKeyboardMarkup(kb))
        return
    if data.startswith("vehicle:"):
        vehicle = data.split(":",1)[1]
        route = context.user_data['route']
        price = ROUTES[route][vehicle]
        msg = f"Route: {route}\nVehicle: {vehicle}\nPrice: {price:,} VND\n\n"
        if price >= CONFIG['deposit_threshold']:
            msg += f"Deposit required: {CONFIG['deposit_amount']:,} VND"
        else:
            msg += 'Pay directly to driver.'
        await q.edit_message_text(msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
