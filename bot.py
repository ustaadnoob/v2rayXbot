import os
import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Tere 2 channels
CHANNELS = [
    {"username": "@bekarChannel", "link": "https://t.me/bekarChannel", "name": "Bekar Channel"},
    {"username": "@raretriccks", "link": "https://t.me/raretriccks", "name": "Rare Tricks"}
]

COUNTRIES = ["Germany", "USA", "Netherlands", "Canada", "France", "UK", "Singapore"]

async def is_joined_all(context, user_id):
    for ch in CHANNELS:
        try:
            m = await context.bot.get_chat_member(ch["username"], user_id)
            if m.status not in ['member','administrator','creator']:
                return False
        except:
            continue
    return True

async def get_not_joined(context, user_id):
    not_joined = []
    for ch in CHANNELS:
        try:
            m = await context.bot.get_chat_member(ch["username"], user_id)
            if m.status not in ['member','administrator','creator']:
                not_joined.append(ch)
        except:
            continue
    return not_joined

def get_configs(country):
    try:
        url = f"https://v2nodes.com/subscriptions/{country.lower()}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        configs = []
        for code in soup.find_all('code'):
            text = code.get_text()
            if text.startswith("vless://") or text.startswith("vmess://"):
                configs.append(text + "#aaloo")
            if len(configs) >= 10:
                break
        return configs
    except:
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined_all(context, update.effective_user.id):
        kb = []
        for ch in CHANNELS:
            kb.append([InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["link"])])
        kb.append([InlineKeyboardButton("✅ Verify (Join Karke Dabao)", callback_data='verify')])

        await update.message.reply_text(
            "⚠️ Bot use karne ke liye 2 channels join karna zaroori hai!\n\n1. Dono Join karo\n2. Join karke Verify dabao",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return
    
    keyboard = []
    for c in COUNTRIES:
        keyboard.append([InlineKeyboardButton(c, callback_data=c)])
    await update.message.reply_text("✅ Verified! Select country:", reply_markup=InlineKeyboardMarkup(keyboard))

async def verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined_all(context, q.from_user.id):
        keyboard = []
        for c in COUNTRIES:
            keyboard.append([InlineKeyboardButton(c, callback_data=c)])
        await q.edit_message_text("✅ Dono join ho gaye! Select country:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        not_joined = await get_not_joined(context, q.from_user.id)
        kb = []
        for ch in CHANNELS:
            kb.append([InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["link"])])
        kb.append([InlineKeyboardButton("✅ Verify Again", callback_data='verify')])
        left = ", ".join([c['name'] for c in not_joined]) if not_joined else "1 channel"
        await q.edit_message_text(f"❌ Abhi bhi {left} join karna rehta hai!", reply_markup=InlineKeyboardMarkup(kb))

async def country_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    # Agar country wala button hai to
    if q.data in COUNTRIES:
        await q.answer()
        if not await is_joined_all(context, q.from_user.id):
            await q.edit_message_text("❌ Pehle dono channels join karo! /start dabao")
            return
        country = q.data
        await q.edit_message_text(f"⏳ Fetching {country} configs...")
        configs = get_configs(country)
        if not configs:
            await q.edit_message_text(f"❌ No configs found for {country}")
            return
        msg = f"✅ {country} - {len(configs)} Configs:\n\n" + "\n\n".join(configs)
        if len(msg) > 4000:
            msg = msg[:4000]
        await q.edit_message_text(msg)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_handler, pattern='verify'))
    app.add_handler(CallbackQueryHandler(country_handler))
    print("Bot Running with 2 Channel Lock...")
    app.run_polling()