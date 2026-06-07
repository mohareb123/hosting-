# SuperAgent 🤖

نظام ذكاء اصطناعي مستقل يجمع بين بوت Telegram قوي ولوحة تحكم ويب عصرية.

## المميزات

- 🧠 **النواة الذكية**: مدعوم بـ Google Gemini AI
- 💬 **بوت Telegram**: تفاعل طبيعي بالعربية والإنجليزية
- 📊 **لوحة تحكم**: إحصائيات مباشرة، إدارة المستخدمين، سجل المحادثات
- 🛠️ **أدوات متكاملة**:
  - 🔍 بحث ويب (DuckDuckGo)
  - 🌤️ الطقس المباشر (Open-Meteo)
  - 💰 أسعار العملات الرقمية (CoinGecko)
  - 🌍 ترجمة متعددة اللغات
  - 📱 توليد QR Codes
  - 📰 قراءة خلاصات RSS
  - 🎬 استخراج بيانات الفيديو (yt-dlp)
  - 🌐 قراءة المواقع وتلخيصها
  - 🐍 تشغيل أكواد Python في بيئة معزولة

## متطلبات النظام

- Python 3.10+
- pip
- (اختياري) Redis للـ caching

## التثبيت

```bash
# 1. استنساخ المشروع
cd superagent

# 2. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. تثبيت المتطلبات
pip install -r requirements.txt

# 4. إعداد ملف البيئة
cp .env.example .env
# عدّل .env وأضف المفاتيح الخاصة بك
```

## الإعداد

افتح ملف `.env` وأضف:

```env
TELEGRAM_BOT_TOKEN=ضع_توكن_البوت_هنا
GEMINI_API_KEY=ضع_مفتاح_Gemini_هنا
ADMIN_USER_IDS=123456789,987654321
DASHBOARD_SECRET=أي_نص_عشوائي_طويل
```

### الحصول على المفاتيح:

1. **توكن Telegram**: تحدث مع [@BotFather](https://t.me/BotFather)
2. **مفتاح Gemini**: [Google AI Studio](https://aistudio.google.com/app/apikey)

## التشغيل

### تشغيل البوت + لوحة التحكم معًا:
```bash
python run.py
```

### أو كل منهما منفصلًا:
```bash
# البوت فقط
python -m bot.main

# لوحة التحكم فقط (port 8000)
python -m dashboard.main
```

افتح لوحة التحكم على: `http://localhost:8000`

## النشر على VPS

### استخدام systemd

أنشئ `/etc/systemd/system/superagent.service`:

```ini
[Unit]
Description=SuperAgent Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/superagent
ExecStart=/opt/superagent/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

ثم:
```bash
systemctl enable superagent
systemctl start superagent
systemctl status superagent
```

### Docker

```bash
docker build -t superagent .
docker run -d --env-file .env -p 8000:8000 --name superagent superagent
```

## الهيكلية

```
superagent/
├── bot/                   # بوت Telegram
│   ├── main.py            # نقطة الدخول
│   ├── ai_core.py         # محرك Gemini
│   ├── handlers/          # معالجات الرسائل
│   └── tools/             # الأدوات المختلفة
├── dashboard/             # لوحة التحكم (FastAPI)
│   ├── main.py
│   ├── templates/
│   └── static/
├── storage.py             # تخزين بيانات (SQLite)
├── config.py              # الإعدادات
├── run.py                 # تشغيل كل شيء معًا
├── requirements.txt
└── .env.example
```

## الترخيص

MIT
