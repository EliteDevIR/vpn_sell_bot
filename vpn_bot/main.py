import json, logging, requests, uuid, qrcode, io
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# بارگذاری تنظیمات و داده‌ها
with open("config.json") as f: config = json.load(f)
with open("plans.json") as f: plans = json.load(f)
with open("messages.json") as f: msgs = json.load(f)

ADMIN = config["admin_id"]

# ماژول‌های پروتکل
PROTOCOLS = ["vmess", "vless", "trojan"]

# تنظیم logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تابع افزودن کاربر به x-ui
def xui_add_user(protocol, plan):
    s = requests.Session()
    s.post(f"{config['xui']['url']}/login", json={
        "username": config["xui"]["username"], 
        "password": config["xui"]["password"]})
    port = 0
    user = {
        "protocol": protocol, "expiryTime": int((__import__("time").time()+plan["days"]*86400)*1000),
        "settings": {"clients":[{"id":str(uuid.uuid4())}]}
    }
    if plan["volume_gb"]:
        user["total"] = plan["volume_gb"]*1024**3
    res = s.post(f"{config['xui']['url']}/panel/api/inbound/add", json=user)
    return res.ok, user

# دستورات ربات
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[p] for p in PROTOCOLS]
    await update.message.reply_photo(open("assets/logo.png","rb"), caption=msgs["welcome"], reply_markup=ReplyKeyboardMarkup(kb))

async def handle_protocol(update, ctx):
    proto = update.message.text
    if proto not in PROTOCOLS:
        return await update.message.reply_text(msgs["error_invalid"])
    ctx.user_data["proto"] = proto
    kb = [[f'{plan["id"]}. {plan["name"]}'] for plan in plans]
    await update.message.reply_text(msgs["choose_plan"], reply_markup=ReplyKeyboardMarkup(kb))

async def handle_plan(update, ctx):
    text = update.message.text
    try:
        pid = int(text.split(".")[0])
        plan = next(p for p in plans if p["id"]==pid)
    except:
        return await update.message.reply_text(msgs["error_invalid"])
    ctx.user_data["plan"] = plan
    kb = [["کارت‌به‌کارت"], ["زرین‌پال"], ["BTC/USDT"]]
    await update.message.reply_text(msgs["choose_payment"], reply_markup=ReplyKeyboardMarkup(kb))

async def handle_payment(update, ctx):
    pay = update.message.text
    ctx.user_data["pay"] = pay
    if pay=="کارت‌به‌کارت":
        return await update.message.reply_text(msgs["kart_request_receipt"])
    # بقیه کانال‌ها...
    ctx.user_data["receipt"] = None
    return await process_order(update, ctx)

async def handle_receipt(update, ctx):
    ctx.user_data["receipt"] = update.message.photo[-1].file_id
    await update.message.reply_text(msgs["awaiting_payment"])
    await ctx.bot.send_message(ADMIN, msgs["admin_received_receipt"])
    return

async def process_order(update, ctx):
    await update.message.reply_text(msgs["awaiting_payment"])
    ok, user = xui_add_user(ctx.user_data["proto"], ctx.user_data["plan"])
    if ok:
        link = f"{ctx.user_data['proto']}://{user['settings']['clients'][0]['id']}@{config['domain']}:{config['port']}"
        qr = qrcode.make(link)
        bio = io.BytesIO()
        qr.save(bio, format="PNG")
        bio.seek(0)
        await update.message.reply_photo(bio, caption=msgs["success_payment"])
        await ctx.bot.send_message(ADMIN, msgs["admin_new_order"])
    else:
        await update.message.reply_text("❌ خطا در صدور سرویس")
    ctx.user_data.clear()

def main():
    app = ApplicationBuilder().token(config["telegram_token"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_protocol))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan))
    app.add_handler(MessageHandler(filters.Text("کارت‌به‌کارت"), handle_payment))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    app.run_polling()

if __name__ == "__main__":
    main()
