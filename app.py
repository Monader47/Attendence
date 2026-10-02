import sys
import os

# ضبط تشفير المخرجات إلى UTF-8 لتجنب مشاكل الـ Console في ويندوز
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import webbrowser
import threading
import time
from web_app import app, init_data, get_local_ip

def open_browser():
    """فتح متصفح الإنترنت تلقائياً بعد تشغيل السيرفر"""
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")

def main():
    init_data()
    local_ip = get_local_ip()

    print("\n" + "="*65)
    print("  تم تشغيل برنامج تسجيل غياب الطلاب بنجاح!")
    print("="*65)
    print(f"  للعمل من جهاز الحساب الحالي (Desktop):")
    print(f"    http://localhost:5000")
    print(f"\n  للعمل من الهاتف المحمول (Mobile):")
    print(f"    تأكد أن الموبايل متصل بنفس شبكة الواي فاي وافتح الرابط:")
    print(f"    http://{local_ip}:5000")
    print("="*65 + "\n")

    # فتح المتصفح تلقائياً
    threading.Thread(target=open_browser, daemon=True).start()

    # تشغيل خادم الويب
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()