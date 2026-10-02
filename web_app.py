import os
import json
import socket
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from excel_parser import load_students
from pdf_generator import generate_pdf_report

app = Flask(__name__, template_folder="templates")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "today_attendance.json")
students_db = []
classes_db = []

def get_local_ip():
    """الحصول على عنوان IP المحلى لجهاز الكمبيوتر لإتاحة الاتصال من الهاتف"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def init_data():
    global students_db, classes_db
    raw_students, classes_db = load_students()

    # تحميل الحضور المسجل مسبقاً لهذا اليوم إن وجد
    saved_state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                # لو البيانات المحفوظة للتاريخ الحالي نستخدمها
                if saved_data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                    saved_state = saved_data.get("records", {})
        except Exception:
            pass

    students_db = []
    for s in raw_students:
        s_id = str(s["id"])
        saved = saved_state.get(s_id, {})
        students_db.append({
            "id": s["id"],
            "name": s["name"],
            "class": s["class"],
            "status": saved.get("status", "غائب"),
            "notes": saved.get("notes", "")
        })

def save_state():
    records = {str(s["id"]): {"status": s["status"], "notes": s["notes"]} for s in students_db}
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "records": records
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def get_data():
    local_ip = get_local_ip()
    mobile_url = f"http://{local_ip}:5000"
    return jsonify({
        "students": students_db,
        "classes": classes_db,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "mobile_url": mobile_url
    })

@app.route("/api/update_status", methods=["POST"])
def update_status():
    data = request.json or {}
    s_id = data.get("id")
    new_status = data.get("status", "حاضر")

    for s in students_db:
        if s["id"] == s_id:
            s["status"] = new_status
            break

    save_state()
    return jsonify({"success": True, "students": students_db})

@app.route("/api/update_notes", methods=["POST"])
def update_notes():
    data = request.json or {}
    s_id = data.get("id")
    notes = data.get("notes", "")

    for s in students_db:
        if s["id"] == s_id:
            s["notes"] = notes
            break

    save_state()
    return jsonify({"success": True})

@app.route("/api/mark_class_present", methods=["POST"])
def mark_class_present():
    data = request.json or {}
    class_name = data.get("class_name")

    if class_name:
        for s in students_db:
            if s["class"] == class_name:
                s["status"] = "حاضر"

    save_state()
    return jsonify({"success": True, "students": students_db})

@app.route("/api/reset_attendance", methods=["POST"])
def reset_attendance():
    for s in students_db:
        s["status"] = "غائب"
        s["notes"] = ""

    save_state()
    return jsonify({"success": True, "students": students_db})

@app.route("/api/download_pdf")
def download_pdf():
    import io
    pdf_buffer = io.BytesIO()
    generate_pdf_report(students_db, pdf_buffer)
    pdf_buffer.seek(0)
    filename = f"Daily_Attendance_{datetime.now().strftime('%Y_%m_%d')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    init_data()
    local_ip = get_local_ip()
    print("=" * 60)
    print(f"  نظام تسجيل الحضور والغياب يعمل الآن بنجاح!")
    print(f"  - للفتح من الكمبيوتر: http://localhost:5000")
    print(f"  - للفتح من جهاز الموبايل: http://{local_ip}:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
