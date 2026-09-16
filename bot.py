import os
import re
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

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

def get_configs(country):
    try:
        urls = [
            f"https://v2nodes.com/subscriptions/{country.lower()}/",
            f"https://www.v2nodes.com/subscriptions/{country.lower()}/",
            f"https://v2nodes.com/{country.lower()}/"
        ]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        for url in urls:
            print(f"Trying {url}")
            r = requests.get(url, headers=headers, timeout=20)
            text = r.text
            found = re.findall(r'(vless://[^\s<"\']+|vmess://[^\s<"\']+|trojan://[^\s<"\']+|ss://[^\s<"\']+)', text)
            if found:
                clean = []
                for c in found[:10]:
                    if "#aaloo" not in c:
                        c = c + f"#{country}-aaloo"
                    clean.append(c)
                return clean
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_joined_all(context, user_id):
        buttons = [[InlineKeyboardButton(ch["name"], url=ch["link"])] for ch in CHANNELS]
        buttons.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
        await update.message.reply_text("Bot use karne ke liye pehle channels join karo:", reply_markup=InlineKeyboardMarkup(buttons))
        return
    await show_countries(update)

async def show_countries(update):
    buttons = [[InlineKeyboardButton(c, callback_data=f"country_{c}")] for c in COUNTRIES]
    markup = InlineKeyboardMarkup(buttons)
    text = "Country select karo:"
    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    else:
        await update.callback_query.message.edit_text(text, reply_markup=markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "verify":
        if await is_joined_all(context, query.from_user.id):
            await show_countries(update)
        else:
            await query.answer("Abhi tak join nahi kiya!", show_alert=True)
        return

    if data.startswith("country_"):
        country = data.split("_")[1]
        await query.message.edit_text(f"{country} ke configs nikal raha hu...")
        configs = get_configs(country)
        if not configs:
            await query.message.edit_text(f"No configs found for {country}. Dusra country try karo.")
            await show_countries(update)
            return
        msg = f"**{country} Configs ({len(configs)}):**\n\n" + "\n\n".join([f"`{c}`" for c in configs])
        await query.message.edit_text(msg, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
