import time

import requests

from core.redis_client import get_redis

# TELEGRAM CONFIG
BOT_TOKEN = "8750549333:AAFWfopkDy6Fi5x01ZxoM9Gg0JmkZMk619g"
CHAT_ID = "6656920393"

def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=data)
        print("Telegram response:", response.text)
    except Exception as e:
        print("Telegram ERROR:", e)

r = get_redis(timeout=5.0)

was_down = False

while True:
    try:
        if r.ping():
            print("✅ Redis OK")
            if was_down:
                send_alert("✅ Redis RECOVERED")
                was_down = False
    except:
        print("❌ Redis DOWN")
        if not was_down:
            send_alert("🚨 ALERT: Redis is DOWN!")
            was_down = True
    time.sleep(5)