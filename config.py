"""Configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

ADMIN_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_USER_IDS", "").split(",")
    if uid.strip().isdigit()
]

DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET", "change-me")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "superagent.db")

SYSTEM_PROMPT = """أنت SuperAgent، مساعد ذكاء اصطناعي متطور ومستقل.
- تجيب بالعربية إذا سُئلت بالعربية، وبالإنجليزية إذا سُئلت بالإنجليزية.
- تستخدم الأدوات المتاحة بذكاء عند الحاجة (بحث، طقس، عملات، ترجمة، QR، RSS، فيديو، قراءة مواقع، تشغيل كود).
- أجوبتك واضحة، منظمة، ومفيدة.
- لا تذكر تفاصيل تقنية داخلية إلا إذا طُلب منك ذلك."""
