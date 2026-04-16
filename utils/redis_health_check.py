import redis
import time

r = redis.Redis(host='localhost', port=6379)

while True:
    try:
        if r.ping():
            print("✅ Redis OK")
    except Exception as e:
        print("❌ Redis DOWN:", e)
    time.sleep(5)