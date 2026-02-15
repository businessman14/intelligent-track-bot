import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import csv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# ضع التوكن هنا
# =========================
BOT_TOKEN = "8435186661:AAHdGtoSgD18ki3w8u_dA4ddcxeW4eU32lg"

# =========================
# رابط القناة العامة
# =========================
CHANNEL_LINK = "https://t.me/IntelligentTradeSystems"

# =========================
# إعداد قاعدة البيانات
# =========================
DB_PATH = Path("data.db")

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        first_source TEXT,
        first_seen_utc TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        source TEXT,
        seen_utc TEXT
    )
    """)

    con.commit()
    con.close()

def save_visit(user_id, source):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO visits (user_id, source, seen_utc) VALUES (?, ?, ?)",
        (user_id, source, now_utc_iso())
    )
    con.commit()
    con.close()

def ensure_user_first_source(user_id, first_name, username, source):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row is None:
        cur.execute("""
            INSERT INTO users
            (user_id, first_name, username, first_source, first_seen_utc)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, first_name, username, source, now_utc_iso()))

    con.commit()
    con.close()

def get_stats():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("""
        SELECT first_source, COUNT(*)
        FROM users
        GROUP BY first_source
        ORDER BY COUNT(*) DESC
    """)

    rows = cur.fetchall()
    con.close()
    return total_users, rows

# =========================
# أوامر البوت
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source = "unknown"
    if context.args:
        source = context.args[0].strip().lower()

    user = update.effective_user

    save_visit(user.id, source)

    ensure_user_first_source(
        user.id,
        user.first_name or "",
        user.username or "",
        source
    )

    keyboard = [
        [InlineKeyboardButton("🚀 اضغط هنا للانضمام للقناة", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بك في Intelligent Trade Systems\n\n"
        "🎯 أنظمة تداول قائمة على تحليل منضبط وإدارة مخاطر احترافية.\n"
        "📊 محتوى تعليمي وتحليلي يهدف لتطوير مهاراتك في قراءة السوق.\n\n"
        "💬 يمكنك طرح الأسهم للتحليل أو اقتراح أسهم للمتابعة كمحتوى تعليمي.\n\n"
        "⬇️ اضغط الزر بالأسفل للانضمام للقناة الرسمية",
        reply_markup=reply_markup
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, rows = get_stats()

    lines = [
        "📊 تقرير المصادر",
        f"👥 إجمالي المستخدمين: {total}",
        ""
    ]

    if not rows:
        lines.append("لا يوجد بيانات.")
    else:
        for src, count in rows:
            lines.append(f"• {src}: {count}")

    await update.message.reply_text("\n".join(lines))

def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))

    print("Bot is running... لإيقافه اضغط Ctrl+C")
    app.run_polling()

if __name__ == "__main__":
    main()
