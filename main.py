"""Telegram bot — message handlers and main loop."""
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ChatAction

from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_IDS
import storage
from bot.ai_core import chat
from bot.tools import generate_qr

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("superagent")


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await storage.upsert_user(update.effective_user)
    await update.message.reply_text(
        "👋 أهلاً بك في *SuperAgent*\n\n"
        "أنا مساعد ذكي يمكنني:\n"
        "🔍 البحث في الويب\n"
        "🌤️ معرفة الطقس\n"
        "💰 أسعار العملات الرقمية\n"
        "🌍 الترجمة\n"
        "📱 توليد QR (/qr نص)\n"
        "📰 قراءة RSS\n"
        "🎬 معلومات الفيديو\n"
        "🐍 تشغيل أكواد Python\n\n"
        "فقط اكتب سؤالك!",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - بدء\n"
        "/help - المساعدة\n"
        "/qr <نص> - توليد QR code\n"
        "/clear - مسح سجل المحادثة\n"
        "/close - إغلاق جلسة التصفح المفتوحة\n"
        "/stats - إحصائيات (للمشرفين)"
    )


async def cmd_qr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args)
    if not text:
        await update.message.reply_text("استخدم: /qr <النص>")
        return
    png = generate_qr(text)
    await storage.log_tool(update.effective_user.id, "generate_qr")
    await update.message.reply_photo(photo=png, caption=f"QR: {text[:100]}")


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import aiosqlite
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM messages WHERE user_id=?",
                         (update.effective_user.id,))
        await db.commit()
    await update.message.reply_text("✅ تم مسح سجل المحادثة")


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_USER_IDS:
        return
    s = await storage.get_stats()
    text = (f"📊 *الإحصائيات*\n\n"
            f"👥 المستخدمون: {s['total_users']}\n"
            f"🚫 محظورون: {s['blocked_users']}\n"
            f"💬 الرسائل: {s['total_messages']}\n"
            f"🟢 نشطون (24س): {s['active_24h']}\n\n"
            f"🛠️ *الأدوات الأكثر استخداماً:*\n")
    for t in s["top_tools"]:
        text += f"• {t['name']}: {t['count']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Close the active browser session for the user."""
    from bot.tools import close_browser_session
    user_id = update.effective_user.id
    res = await close_browser_session(user_id)
    await update.message.reply_text(res)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""

    await storage.upsert_user(user)
    if await storage.is_blocked(user.id):
        await update.message.reply_text("🚫 تم حظرك من استخدام البوت.")
        return

    await storage.log_message(user.id, "user", text)
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    try:
        reply = await chat(user.id, text)
    except Exception as e:
        log.exception("AI error")
        reply = f"⚠️ خطأ: {e}"

    await storage.log_message(user.id, "assistant", reply)
    # Telegram message limit
    for i in range(0, len(reply), 4000):
        await update.message.reply_text(reply[i:i+4000])


async def post_init(app):
    await storage.init_db()
    log.info("Database initialized.")


def build_app():
    app = (Application.builder()
           .token(TELEGRAM_BOT_TOKEN)
           .post_init(post_init)
           .build())
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("close", cmd_close))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN missing in .env")
    app = build_app()
    log.info("🚀 SuperAgent bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
