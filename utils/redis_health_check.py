import time

from core.redis_client import get_redis

r = get_redis(timeout=5.0)

while True:
    try:
        if r.ping():
            print("✅ Redis OK")
    except Exception as e:
        print("❌ Redis DOWN:", e)
    time.sleep(5)
