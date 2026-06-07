"""Run both the Telegram bot and the FastAPI dashboard together."""
import asyncio
import logging
import threading
import uvicorn

from config import DASHBOARD_PORT
import storage
from bot.main import build_app
from telegram import Update

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("superagent.run")


def run_dashboard():
    cfg = uvicorn.Config("dashboard.main:app", host="0.0.0.0",
                         port=DASHBOARD_PORT, log_level="info")
    server = uvicorn.Server(cfg)
    asyncio.run(server.serve())


def main():
    # Initialize DB synchronously first
    asyncio.run(storage.init_db())

    # Dashboard in a separate thread (has its own event loop)
    t = threading.Thread(target=run_dashboard, daemon=True)
    t.start()
    log.info(f"📊 Dashboard: http://0.0.0.0:{DASHBOARD_PORT}")

    # Bot in main thread
    app = build_app()
    log.info("🤖 Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
