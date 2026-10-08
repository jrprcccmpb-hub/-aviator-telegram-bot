import os
import sqlite3
from statistics import mean, median
from datetime import datetime
from threading import Thread

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

DB = "aviator.db"
web = Flask(__name__)

@web.get("/")
def home():
    return "Aviator Stats Bot is running."

def database():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS rounds(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        multiplier REAL,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS bankroll(
        user_id INTEGER PRIMARY KEY,
        amount REAL
    )""")
    c.commit()
    return c

def rounds(user_id, limit=100):
    c = database()
    r = c.execute(
        "SELECT multiplier FROM rounds WHERE user_id=? "
        "ORDER BY id DESC LIMIT ?", (user_id, limit)
    ).fetchall()
    c.close()
    return [x[0] for x in r]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ Aviator Stats Bot\n\n"
        "/round 1.45 - record a round\n"
        "/last - recent rounds\n"
        "/stats - statistics\n"
        "/bankroll 500 - set bankroll\n"
        "/report - session report\n\n"
        "⚠️ This bot analyzes past rounds; it cannot reliably predict the next crash."
    )

async def round_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /round 1.45")
        return
    try:
        value = float(context.args[0].replace("x", ""))
        if value < 1:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Enter a valid multiplier, e.g. /round 2.35")
        return

    c = database()
    c.execute(
        "INSERT INTO rounds(user_id,multiplier,created_at) VALUES(?,?,?)",
        (update.effective_user.id, value, datetime.utcnow().isoformat())
    )
    c.commit()
    c.close()
    await update.message.reply_text(f"✅ Recorded {value:.2f}x")

async def last_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = rounds(update.effective_user.id, 15)
    if not r:
        await update.message.reply_text("No rounds recorded yet.")
        return
    await update.message.reply_text(
        "📊 Recent rounds:\n" + "  ".join(f"{x:.2f}x" for x in r)
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = rounds(update.effective_user.id)
    if not r:
        await update.message.reply_text("No rounds recorded yet.")
        return

    await update.message.reply_text(
        "📈 Statistics\n\n"
        f"Rounds: {len(r)}\n"
        f"Average: {mean(r):.2f}x\n"
        f"Median: {median(r):.2f}x\n"
        f"Lowest: {min(r):.2f}x\n"
        f"Highest: {max(r):.2f}x\n"
        f"Below 2x: {sum(x < 2 for x in r)}\n"
        f"2x–4.99x: {sum(2 <= x < 5 for x in r)}\n"
        f"5x+: {sum(x >= 5 for x in r)}\n\n"
        "⚠️ Past results do not predict the next round."
    )

async def bankroll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /bankroll 500")
        return
    try:
        amount = float(context.args[0])
        if amount < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Enter a valid amount.")
        return

    c = database()
    c.execute(
        "INSERT INTO bankroll(user_id,amount) VALUES(?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount",
        (update.effective_user.id, amount)
    )
    c.commit()
    c.close()
    await update.message.reply_text(f"💰 Bankroll set to {amount:.2f}")

async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = rounds(update.effective_user.id, 50)
    if not r:
        await update.message.reply_text("No rounds recorded yet.")
        return
    await update.message.reply_text(
        "📝 Session report\n\n"
        f"Rounds: {len(r)}\n"
        f"Average: {mean(r):.2f}x\n"
        f"Highest: {max(r):.2f}x\n"
        f"Below 2x: {sum(x < 2 for x in r)}\n\n"
        "Past results do not determine the next crash."
    )

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    Thread(target=run_web, daemon=True).start()

    bot = Application.builder().token(token).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", start))
    bot.add_handler(CommandHandler("round", round_cmd))
    bot.add_handler(CommandHandler("last", last_cmd))
    bot.add_handler(CommandHandler("stats", stats_cmd))
    bot.add_handler(CommandHandler("bankroll", bankroll_cmd))
    bot.add_handler(CommandHandler("report", report_cmd))

    bot.run_polling()

if __name__ == "__main__":
    main()