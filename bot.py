#2nd
import requests
import json
import time
import re
import html
import unicodedata
import queue
import threading
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import pycountry
import phonenumbers
from flask import Flask, Response

# ===== CONFIG =====
API_TOKEN = "Api token"
BASE_URL = "http://51.77.216.195/crapi/dgroup"
BOT_TOKEN: ${{ secrets.BOT_TOKEN }}"
CHAT_IDS = [
    "1087968824"
    ]
CHANNEL_LINK = "https://t.me/bekarChannel"
BACKUP = "https://t.me/raretriccks"

seen_messages = set()
message_queue = queue.Queue()

# ========= TELEGRAM SENDER =========
def send_to_telegram(msg, kb=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success = False

    for chat_id in CHAT_IDS:   # ✅ send to all chats
        payload = {
            "chat_id": chat_id,
            "text": msg[:3900],   # Telegram limit safe side
            "parse_mode": "HTML"
        }
        if kb:
            payload["reply_markup"] = kb.to_json()

        for i in range(3):  # retry 3 times
            try:
                r = requests.post(url, data=payload, timeout=10)
                if r.status_code == 200:
                    success = True
                    break
                else:
                    print(f"❌ Telegram Error ({chat_id}):", r.text)
            except Exception as e:
                print(f"❌ Telegram Exception ({chat_id}):", e)
            time.sleep(1)

    return success

# ========= QUEUE WORKER =========
def sender_worker():
    while True:
        msg, kb = message_queue.get()
        send_to_telegram(msg, kb)
        print("📤 Sent from queue")
        time.sleep(0.5)  # 0.5 sec gap
        message_queue.task_done()


# ========= HELPERS =========
def safe_request(url, params):
    try:
        response = requests.get(url, params=params, timeout=15)
        return response.json()
    except Exception:
        return None


def view_stats(dt1, dt2, records=50, start=0):
    params = {"token": API_TOKEN, "dt1": dt1, "dt2": dt2, "records": records, "start": start}
    return safe_request(f"{BASE_URL}/viewstats", params)


def extract_otp(message: str) -> str | None:
    message = unicodedata.normalize("NFKD", message)
    message = re.sub(r"[\u200f\u200e\u202a-\u202e]", "", message)

    keyword_regex = re.search(r"(otp|code|pin|password)[^\d]{0,10}(\d[\d\-]{3,8})", message, re.I)
    if keyword_regex:
        return re.sub(r"\D", "", keyword_regex.group(2))

    reverse_regex = re.search(r"(\d[\d\-]{3,8})[^\w]{0,10}(otp|code|pin|password)", message, re.I)
    if reverse_regex:
        return re.sub(r"\D", "", reverse_regex.group(1))

    generic_regex = re.findall(r"\d{2,4}[-]?\d{2,4}", message)
    if generic_regex:
        otp = generic_regex[0]
        return re.sub(r"\D", "", otp)

    return None

def mask_number(number: str) -> str:
    if len(number) <= 4:
        return number  # chhota number to mask na karo
    
    mid = len(number) // 2
    # beech ke 2 digits mask karo
    start = number[:mid-1]
    end = number[mid+1:]
    return start + "**" + end



def country_from_number(number: str) -> tuple[str, str]:
    try:
        parsed = phonenumbers.parse("+" + number)
        region = phonenumbers.region_code_for_number(parsed)
        if not region:
            return "Unknown", "🌍"
        country_obj = pycountry.countries.get(alpha_2=region)
        if not country_obj:
            return "Unknown", "🌍"
        country = country_obj.name
        flag = "".join([chr(127397 + ord(c)) for c in region])
        return country, flag
    except Exception:
        return "Unknown", "🌍"


def format_message(record):
    current_time = record.get("dt")
    number = record.get("num") or "Unknown"
    sender = record.get("cli") or "Unknown"
    message = record.get("message") or ""
    payout = record.get("payout", "0")

    country, flag = country_from_number(number)
    otp = extract_otp(message)
    otp_line = f"<blockquote>🔑 <b>OTP:</b> <code>{html.escape(otp)}</code></blockquote>\n" if otp else ""

    formatted = (
        f"{flag} <b>New {sender} OTP Received</b>\n\n"
        f"<blockquote>🕰 <b>Time:</b> <b>{html.escape(str(current_time))}</b></blockquote>\n"
        f"<blockquote>🌍 <b>Country:</b> <b>{html.escape(country)} {flag}</b></blockquote>\n"
        f"<blockquote>📱 <b>Service:</b> <b>{html.escape(sender)}</b></blockquote>\n"
        f"<blockquote>📞 <b>Number:</b> <b>{html.escape(mask_number(number))}</b></blockquote>\n"
        f"{otp_line}"
        f"<blockquote>✉️ <b>Full Message:</b></blockquote>\n"
        f"<blockquote><code>{html.escape(message)}</code></blockquote>\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("🚀 Panel", url=f"{CHANNEL_LINK}")],
        [InlineKeyboardButton("📱Main Channel", url=f"{BACKUP}")]
    ]

    return formatted, InlineKeyboardMarkup(keyboard)

from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

# ===== START COMMAND =====
def start(update: Update, context: CallbackContext):
    text = (
        "🤖 <b>Bot is Active</b>"
    )

    keyboard = [
        [InlineKeyboardButton("🤖 Number Bot", url="https://t.me/hxotpbot")],
        [InlineKeyboardButton("📢 Main Channel", url=f"{BACKUP}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


# ===== ADD HANDLER =====
def start_bot_handlers():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    print("🤖 Start command Activated...")
    updater.idle()


# ========= MAIN FETCHER =========
def main_loop():
    print("🚀 OTP Monitor Started...")

    while True:
        stats = view_stats("1970-01-01 00:00:00", "2099-12-31 23:59:59", records=10) or {}

        if stats.get("status") == "success":
            for record in stats["data"]:
                uid = f"{record.get('dt')}_{record.get('num')}_{record.get('message')}"
                if uid not in seen_messages:
                    seen_messages.add(uid)
                    msg, kb = format_message(record)
                    message_queue.put((msg, kb))   # ✅ queue me bhejna
                    print("🌀 Queued:", record.get("message"))

        time.sleep(0.2)  # faster fetch


# ========= FLASK HEALTH CHECK =========
app = Flask(__name__)

@app.route("/health")
def health():
    return Response("OK", status=200)


# ========= START BOTH =========
if __name__ == "__main__":
    # Start sender worker thread
    # Start /start bot handler
    threading.Thread(target=start_bot_handlers, daemon=True).start()
    threading.Thread(target=sender_worker, daemon=True).start()

    # Start OTP fetcher
    threading.Thread(target=main_loop, daemon=True).start()

    # Start Flask
    app.run(host="0.0.0.0", port=8010)

