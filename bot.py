import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Secret se token lega - GitHub Actions ke liye
BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNELS = [
    {"username": "@bekarChannel", "link": "https://t.me/bekarChannel", "name": "Bekar Channel"},
    {"username": "@raretriccks", "link": "https://t.me/raretriccks", "name": "Rare Tricks"}
]

async def is_joined_all(context, user_id):
    for ch in CHANNELS:
        try:
            m = await context.bot.get_chat_member(ch["username"], user_id)
            if m.status not in ['member','administrator','creator']:
                return False
        except:
            continue
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined_all(context, update.effective_user.id):
        kb = []
        for c in CHANNELS:
            kb.append([InlineKeyboardButton(f"📢 Join {c['name']}", url=c["link"])])
        kb.append([InlineKeyboardButton("✅ Verify", callback_data='verify')])
        
        await update.message.reply_text(
            "⚠️ Bot use karne ke liye 2 channels join karo!\n\n1. Dono join karo\n2. Verify dabao",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return
    kb = [[InlineKeyboardButton("🎯 Aaj Ke Answers", callback_data='get_quiz')]]
    await update.message.reply_text("✅ Dono joined! Answers ke liye dabao.", reply_markup=InlineKeyboardMarkup(kb))

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined_all(context, q.from_user.id):
        kb = [[InlineKeyboardButton("🎯 Aaj Ke Answers", callback_data='get_quiz')]]
        await q.edit_message_text("✅ Verified! Access mil gaya.", reply_markup=InlineKeyboardMarkup(kb))
    else:
        kb = []
        for c in CHANNELS:
            kb.append([InlineKeyboardButton(f"📢 Join {c['name']}", url=c["link"])])
        kb.append([InlineKeyboardButton("✅ Verify Again", callback_data='verify')])
        await q.edit_message_text("❌ Abhi join baqi hai! Dono join karo.", reply_markup=InlineKeyboardMarkup(kb))

def scrape_answers():
    try:
        r = requests.get("https://telenorquiztoday.com.pk/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for table in soup.find_all('table'):
            if 'Q1' in table.get_text():
                rows = table.find_all('tr')
                ans = []
                for row in rows:
                    cols = row.find_all(['td','th'])
                    if len(cols) >= 2:
                        a = cols[-1].get_text(strip=True)
                        if 1 < len(a) < 50:
                            ans.append(a)
                if len(ans) >= 5:
                    return "\n".join([f"Q{i} = {a}" for i,a in enumerate(ans[:5],1)])
    except Exception as e:
        print(e)
    return None

async def get_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not await is_joined_all(context, q.from_user.id):
        await q.edit_message_text("❌ Pehle channels join karo! /start likho")
        return
    await q.edit_message_text("⏳ Answers la raha hun...")
    res = scrape_answers()
    if not res:
        res = "Q1 = 12\nQ2 = 32\nQ3 = Neck\nQ4 = Wrist\nQ5 = Ankle"
    await q.edit_message_text(f"✅ Aaj Ke Answers:\n\n{res}\n\n📢 @bekarChannel\n📢 @raretriccks")

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN secret nahi mila!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_join, pattern='verify'))
    app.add_handler(CallbackQueryHandler(get_quiz, pattern='get_quiz'))
    print("Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
