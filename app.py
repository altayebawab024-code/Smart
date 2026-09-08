from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart_exam_scheduler_secret_key_2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "exam_scheduler.db")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            department TEXT,
            students_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            capacity INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invigilators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            hall_id INTEGER,
            invigilator_id INTEGER,
            exam_date TEXT,
            exam_time TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (hall_id) REFERENCES halls (id),
            FOREIGN KEY (invigilator_id) REFERENCES invigilators (id)
        )
    """)
    conn.commit()
    conn.close()

# إنشاء الجداول عند بدء التشغيل
init_db()

BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Exam Scheduler AI</title>
<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, Tahoma, sans-serif; background: #f3f6fa; color: #222; }
header { background: #17365d; color: white; padding: 18px; text-align: center; }
header h1 { margin: 0 0 5px; font-size: 20px; }
header p { margin: 0; font-size: 13px; opacity: 0.9; }
nav { background: white; padding: 10px; display: flex; justify-content: center; flex-wrap: wrap; gap: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
nav a { text-decoration: none; background: #17365d; color: white; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; }
nav a:hover { opacity: 0.85; }
.container { width: 94%; max-width: 1000px; margin: 15px auto; }
.card { background: white; padding: 18px; margin-bottom: 18px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; }
.stat { background: white; padding: 15px; text-align: center; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.stat h2 { color: #17365d; font-size: 26px; margin: 5px; }
.stat h3 { margin: 0; font-size: 15px; color: #555; }
input, select, textarea { width: 100%; padding: 10px; margin: 6px 0 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
textarea { height: 80px; resize: none; }
button { background: #17365d; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-size: 15px; width: 100%; font-weight: bold; }
.generate-button { background: #198754; margin-top: 10px; }
table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 8px 5px; text-align: center; }
th { background: #17365d; color: white; }
.message { background: #e8f5e9; padding: 10px; border-radius: 6px; margin-bottom: 12px; color: #2e7d32; }
.warning { background: #fff3cd; padding: 10px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; }
.error { background: #f8d7da; padding: 10px; border-radius: 6px; margin-bottom: 12px; color: #c62828; }
#answer { margin-top: 12px; padding: 12px; background: #f1f5f9; border-radius: 8px; white-space: pre-line; min-height: 50px; font-size: 14px; }
.login-box { max-width: 400px; margin: 30px auto; }
.login-title { text-align: center; color: #17365d; }
.logout { background: #dc3545; }
.table-responsive { overflow-x: auto; }
</style>
</head>
<body>
<header>
<h1>Exam Scheduler AI</h1>
<p>نظام ذكي لإدارة وجدولة الامتحانات</p>
</header>
<nav>
<a href="/">الرئيسية</a>
<a href="/subjects">المواد</a>
<a href="/halls">القاعات</a>
<a href="/invigilators">المراقبون</a>
<a href="/exams">الامتحانات</a>
<a href="/generate_schedule">الجدولة</a>
<a href="/assistant">المساعد</a>
<a href="/logout" class="logout">خروج</a>
</nav>
<div class="container">
{{ content|safe }}
</div>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة."

    content = f"""
    <div class="card login-box">
        <h2 class="login-title">🔐 تسجيل دخول المشرف</h2>
        <p style="text-align:center; font-size:13px; color:#666;">المشرف الافتراضي: admin | كلمة المرور: admin123</p>
        {f'<div class="error">{error}</div>' if error else ''}
        <form method="POST">
            <label>اسم المستخدم</label>
            <input type="text" name="username" placeholder="أدخل اسم المستخدم" required autofocus>
            <label>كلمة المرور</label>
            <input type="password" name="password" placeholder="أدخل كلمة المرور" required>
            <button type="submit">🔐 تسجيل الدخول</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.before_request
def require_login():
    if request.endpoint in ["login", "static"]:
        return None
    if not session.get("logged_in"):
        return redirect(url_for("login"))

@app.route("/")
def home():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subjects")
    subjects = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM halls")
    halls = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM invigilators")
    invigilators = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM exams")
    exams = cursor.fetchone()[0]
    conn.close()

    content = f"""
    <div class="card">
        <h2>مرحبًا بك في النظام 👋</h2>
        <p>نظام لإدارة المواد والقاعات والمراقبين والامتحانات مع مساعد ذكي وجدولة تلقائية.</p>
    </div>
    <div class="cards">
        <div class="stat"><h3>المواد</h3><h2>{subjects}</h2></div>
        <div class="stat"><h3>القاعات</h3><h2>{halls}</h2></div>
        <div class="stat"><h3>المراقبون</h3><h2>{invigilators}</h2></div>
        <div class="stat"><h3>الامتحانات</h3><h2>{exams}</h2></div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/subjects", methods=["GET", "POST"])
def subjects():
    conn = connect_db()
    cursor = conn.cursor()
    message = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        department = request.form.get("department", "").strip()
        students_count = request.form.get("students_count", "0").strip()
        try:
            students_count = int(students_count)
            if students_count < 0: raise ValueError
            if not name:
                message = "اسم المادة مطلوب."
            else:
                cursor.execute("INSERT INTO subjects (name, code, department, students_count) VALUES (?, ?, ?, ?)",
                               (name, code, department, students_count))
                conn.commit()
                message = "تمت إضافة المادة بنجاح."
        except ValueError:
            message = "عدد الطلاب يجب أن يكون رقمًا صحيحًا."

    cursor.execute("SELECT id, name, code, department, students_count FROM subjects ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()

    rows = "".join([f"<tr><td>{s['id']}</td><td>{s['name']}</td><td>{s['code'] or '-'}</td><td>{s['department'] or '-'}</td><td>{s['students_count']}</td></tr>" for s in data])
    content = f"""
    <div class="card">
        <h2>إضافة مادة</h2>
        {f'<div class="message">{message}</div>' if message else ''}
        <form method="POST">
            <label>اسم المادة</label>
            <input type="text" name="name" required>
            <label>كود المادة</label>
            <input type="text" name="code">
            <label>القسم</label>
            <input type="text" name="department">
            <label>عدد الطلاب</label>
            <input type="number" name="students_count" min="0" value="0" required>
            <button type="submit">حفظ المادة</button>
        </form>
    </div>
    <div class="card">
        <h2>المواد المسجلة</h2>
        <div class="table-responsive">
            <table>
                <tr><th>#</th><th>المادة</th><th>الكود</th><th>القسم</th><th>الطلاب</th></tr>
                {rows}
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/halls", methods=["GET", "POST"])
def halls():
    conn = connect_db()
    cursor = conn.cursor()
    message = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        capacity = request.form.get("capacity", "").strip()
        try:
            capacity = int(capacity)
            if capacity <= 0: raise ValueError
            if not name:
                message = "اسم القاعة مطلوب."
            else:
                cursor.execute("INSERT INTO halls (name, capacity) VALUES (?, ?)", (name, capacity))
                conn.commit()
                message = "تمت إضافة القاعة بنجاح."
        except ValueError:
            message = "السعة يجب أن تكون رقمًا أكبر من صفر."
        except sqlite3.IntegrityError:
            message = "اسم القاعة موجود بالفعل."

    cursor.execute("SELECT id, name, capacity FROM halls ORDER BY capacity")
    data = cursor.fetchall()
    conn.close()

    rows = "".join([f"<tr><td>{h['id']}</td><td>{h['name']}</td><td>{h['capacity']}</td></tr>" for h in data])
    content = f"""
    <div class="card">
        <h2>إضافة قاعة</h2>
        {f'<div class="message">{message}</div>' if message else ''}
        <form method="POST">
            <label>اسم القاعة</label>
            <input type="text" name="name" required>
            <label>سعة القاعة</label>
            <input type="number" name="capacity" min="1" required>
            <button type="submit">حفظ القاعة</button>
        </form>
    </div>
    <div class="card">
        <h2>القاعات المسجلة</h2>
        <div class="table-responsive">
            <table>
                <tr><th>#</th><th>القاعة</th><th>السعة</th></tr>
                {rows}
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/invigilators", methods=["GET", "POST"])
def invigilators():
    conn = connect_db()
    cursor = conn.cursor()
    message = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            cursor.execute("INSERT INTO invigilators (name) VALUES (?)", (name,))
            conn.commit()
            message = "تمت إضافة المراقب بنجاح."
        else:
            message = "اسم المراقب مطلوب."

    cursor.execute("SELECT id, name FROM invigilators ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()

    rows = "".join([f"<tr><td>{i['id']}</td><td>{i['name']}</td></tr>" for i in data])
    content = f"""
    <div class="card">
        <h2>إضافة مراقب</h2>
        {f'<div class="message">{message}</div>' if message else ''}
        <form method="POST">
            <label>اسم المراقب</label>
            <input type="text" name="name" required>
            <button type="submit">حفظ المراقب</button>
        </form>
    </div>
    <div class="card">
        <h2>المراقبون المسجلون</h2>
        <div class="table-responsive">
            <table>
                <tr><th>#</th><th>اسم المراقب</th></tr>
                {rows}
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/exams", methods=["GET", "POST"])
def exams():
    conn = connect_db()
    cursor = conn.cursor()
    message = ""
    error = False

    if request.method == "POST":
        subject_id = request.form.get("subject_id")
        hall_id = request.form.get("hall_id")
        invigilator_id = request.form.get("invigilator_id")
        exam_date = request.form.get("exam_date")
        exam_time = request.form.get("exam_time")

        cursor.execute("SELECT students_count FROM subjects WHERE id = ?", (subject_id,))
        subject = cursor.fetchone()
        cursor.execute("SELECT capacity FROM halls WHERE id = ?", (hall_id,))
        hall = cursor.fetchone()

        if not subject or not hall:
            message = "المادة أو القاعة غير صالحة."
            error = True
        elif subject["students_count"] > hall["capacity"]:
            message = f"عدد الطلاب ({subject['students_count']}) أكبر من سعة القاعة ({hall['capacity']})."
            error = True
        else:
            cursor.execute("SELECT id FROM exams WHERE hall_id = ? AND exam_date = ? AND exam_time = ?", (hall_id, exam_date, exam_time))
            if cursor.fetchone():
                message = "القاعة مستخدمة بالفعل في هذا التاريخ والوقت."
                error = True
            else:
                cursor.execute("SELECT id FROM exams WHERE invigilator_id = ? AND exam_date = ? AND exam_time = ?", (invigilator_id, exam_date, exam_time))
                if cursor.fetchone():
                    message = "المراقب لديه امتحان آخر في هذا التاريخ والوقت."
                    error = True
                else:
                    cursor.execute("INSERT INTO exams (subject_id, hall_id, invigilator_id, exam_date, exam_time) VALUES (?, ?, ?, ?, ?)",
                                   (subject_id, hall_id, invigilator_id, exam_date, exam_time))
                    conn.commit()
                    message = "تمت إضافة الامتحان بنجاح."

    cursor.execute("SELECT id, name, students_count FROM subjects ORDER BY name")
    subjects_data = cursor.fetchall()
    cursor.execute("SELECT id, name, capacity FROM halls ORDER BY capacity")
    halls_data = cursor.fetchall()
    cursor.execute("SELECT id, name FROM invigilators ORDER BY name")
    invigilators_data = cursor.fetchall()

    cursor.execute("""
        SELECT exams.id, subjects.name AS subject_name, subjects.students_count,
               halls.name AS hall_name, halls.capacity, invigilators.name AS invigilator_name,
               exams.exam_date, exams.exam_time
        FROM exams
        LEFT JOIN subjects ON exams.subject_id = subjects.id
        LEFT JOIN halls ON exams.hall_id = halls.id
        LEFT JOIN invigilators ON exams.invigilator_id = invigilators.id
        ORDER BY exams.exam_date, exams.exam_time
    """)
    exam_data = cursor.fetchall()
    conn.close()

    subject_opts = "".join([f"<option value='{s['id']}'>{s['name']} ({s['students_count']} طالب)</option>" for s in subjects_data])
    hall_opts = "".join([f"<option value='{h['id']}'>{h['name']} (سعة: {h['capacity']})</option>" for h in halls_data])
    invigilator_opts = "".join([f"<option value='{i['id']}'>{i['name']}</option>" for i in invigilators_data])

    rows = "".join([f"<tr><td>{e['subject_name']}</td><td>{e['students_count']}</td><td>{e['hall_name']}</td><td>{e['capacity']}</td><td>{e['invigilator_name']}</td><td>{e['exam_date']}</td><td>{e['exam_time']}</td></tr>" for e in exam_data])

    content = f"""
    <div class="card">
        <h2>إضافة امتحان يدويًا</h2>
        {f'<div class="{"error" if error else "message"}">{message}</div>' if message else ''}
        <form method="POST">
            <label>المادة</label>
            <select name="subject_id" required><option value="">اختر المادة</option>{subject_opts}</select>
            <label>القاعة</label>
            <select name="hall_id" required><option value="">اختر القاعة</option>{hall_opts}</select>
            <label>المراقب</label>
            <select name="invigilator_id" required><option value="">اختر المراقب</option>{invigilator_opts}</select>
            <label>تاريخ الامتحان</label>
            <input type="date" name="exam_date" required>
            <label>وقت الامتحان</label>
            <input type="time" name="exam_time" required>
            <button type="submit">حفظ الامتحان</button>
        </form>
    </div>
    <div class="card">
        <h2>الامتحانات المسجلة</h2>
        <div class="table-responsive">
            <table>
                <tr><th>المادة</th><th>الطلاب</th><th>القاعة</th><th>السعة</th><th>المراقب</th><th>التاريخ</th><th>الوقت</th></tr>
                {rows}
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/generate_schedule", methods=["GET", "POST"])
def generate_schedule():
    message = ""
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        if not start_date:
            message = "اختر تاريخ بداية الامتحانات."
        else:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, students_count FROM subjects
                    WHERE id NOT IN (SELECT subject_id FROM exams WHERE subject_id IS NOT NULL)
                    ORDER BY students_count DESC
                """)
                subjects_data = cursor.fetchall()
                cursor.execute("SELECT id, name, capacity FROM halls ORDER BY capacity")
                halls_data = cursor.fetchall()
                cursor.execute("SELECT id, name FROM invigilators ORDER BY id")
                invigilators_data = cursor.fetchall()

                if not subjects_data:
                    message = "لا توجد مواد جديدة بحاجة لجدولة."
                elif not halls_data:
                    message = "لا توجد قاعات مسجلة."
                elif not invigilators_data:
                    message = "لا يوجد مراقبون مسجلون."
                else:
                    times = ["09:00", "11:30", "02:00"]
                    cursor.execute("SELECT hall_id, invigilator_id, exam_date, exam_time FROM exams")
                    existing = cursor.fetchall()
                    used_halls = {(e["hall_id"], (e["exam_date"], e["exam_time"])) for e in existing}
                    used_invs = {(e["invigilator_id"], (e["exam_date"], e["exam_time"])) for e in existing}

                    scheduled_count = 0
                    inv_idx = 0

                    for subj in subjects_data:
                        count = subj["students_count"] or 0
                        suitable_hall = next((h for h in halls_data if h["capacity"] >= count), None)
                        if not suitable_hall: continue

                        scheduled = False
                        for day in range(30):
                            c_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day)).strftime("%Y-%m-%d")
                            for t in times:
                                slot = (c_date, t)
                                h_key = (suitable_hall["id"], slot)
                                sel_inv = None

                                for att in range(len(invigilators_data)):
                                    idx = (inv_idx + att) % len(invigilators_data)
                                    cand = invigilators_data[idx]
                                    if (cand["id"], slot) not in used_invs:
                                        sel_inv = cand
                                        inv_idx = (idx + 1) % len(invigilators_data)
                                        break

                                if h_key not in used_halls and sel_inv:
                                    cursor.execute("INSERT INTO exams (subject_id, hall_id, invigilator_id, exam_date, exam_time) VALUES (?, ?, ?, ?, ?)",
                                                   (subj["id"], suitable_hall["id"], sel_inv["id"], c_date, t))
                                    used_halls.add(h_key)
                                    used_invs.add((sel_inv["id"], slot))
                                    scheduled_count += 1
                                    scheduled = True
                                    break
                            if scheduled: break

                    conn.commit()
                    message = f"تمت الجدولة الذكية بنجاح لعدد ({scheduled_count}) مواد."
                conn.close()
            except ValueError:
                message = "التاريخ غير صحيح."

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subjects.name AS subject_name, subjects.students_count, halls.name AS hall_name,
               halls.capacity, invigilators.name AS invigilator_name, exams.exam_date, exams.exam_time
        FROM exams
        LEFT JOIN subjects ON exams.subject_id = subjects.id
        LEFT JOIN halls ON exams.hall_id = halls.id
        LEFT JOIN invigilators ON exams.invigilator_id = invigilators.id
        ORDER BY exams.exam_date, exams.exam_time
    """)
    schedule = cursor.fetchall()
    conn.close()

    rows = "".join([f"<tr><td>{e['subject_name']}</td><td>{e['students_count']}</td><td>{e['hall_name']}</td><td>{e['capacity']}</td><td>{e['invigilator_name']}</td><td>{e['exam_date']}</td><td>{e['exam_time']}</td></tr>" for e in schedule])

    content = f"""
    <div class="card">
        <h2>🤖 الجدولة الذكية التلقائية</h2>
        <p>تقوم الخوارزمية بمنع أي تعارض في القاعات أو المراقبين وتوزيع الطلاب حسب السعة.</p>
        {f'<div class="message">{message}</div>' if message else ''}
        <form method="POST">
            <label>تاريخ بداية الامتحانات</label>
            <input type="date" name="start_date" required>
            <button type="submit" class="generate-button">🤖 إنشاء الجدول تلقائيًا</button>
        </form>
    </div>
    <div class="card">
        <h2>📅 الجدول الامتحاني النهائي</h2>
        <div class="table-responsive">
            <table>
                <tr><th>المادة</th><th>الطلاب</th><th>القاعة</th><th>السعة</th><th>المراقب</th><th>التاريخ</th><th>الوقت</th></tr>
                {rows}
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

def assistant_answer(question):
    q = question.strip().lower()
    conn = connect_db()
    cursor = conn.cursor()
    try:
        if "كم مادة" in q or "عدد المواد" in q:
            cursor.execute("SELECT COUNT(*) FROM subjects")
            return f"عدد المواد المسجلة هو: {cursor.fetchone()[0]}"
        if "ما هي المواد" in q or "المواد" in q:
            cursor.execute("SELECT name, students_count FROM subjects")
            data = cursor.fetchall()
            return "المواد:\n" + "\n".join([f"• {s['name']} ({s['students_count']} طالب)" for s in data]) if data else "لا توجد مواد."
        if "كم قاعة" in q or "عدد القاعات" in q:
            cursor.execute("SELECT COUNT(*) FROM halls")
            return f"عدد القاعات المسجلة: {cursor.fetchone()[0]}"
        if "كم مراقب" in q or "عدد المراقبين" in q:
            cursor.execute("SELECT COUNT(*) FROM invigilators")
            return f"عدد المراقبين المسجلين: {cursor.fetchone()[0]}"
        if "امتحان" in q:
            cursor.execute("SELECT COUNT(*) FROM exams")
            return f"عدد الامتحانات المسجلة في الجدول: {cursor.fetchone()[0]}"
        return "لم أفهم السؤال، يمكنك سؤالي: كم عدد المواد؟ ما هي المواد؟ كم قاعة؟ كم مراقب؟ كم امتحان؟"
    except Exception as e:
        return f"حدث خطأ: {e}"
    finally:
        conn.close()

@app.route("/assistant")
def assistant_page():
    content = """
    <div class="card">
        <h2>🤖 المساعد الذكي</h2>
        <p>اسأل المساعد عن بيانات الامتحانات والمواد والقاعات والمراقبين.</p>
        <textarea id="question" placeholder="مثال: كم عدد المواد؟"></textarea>
        <button onclick="askAssistant()">إرسال السؤال</button>
        <div id="answer">الإجابة ستظهر هنا...</div>
    </div>
    <script>
    async function askAssistant() {
        const q = document.getElementById("question").value;
        const ans = document.getElementById("answer");
        if (!q.trim()) { ans.innerText = "اكتب السؤال أولاً."; return; }
        ans.innerText = "جاري البحث...";
        try {
            const res = await fetch("/ask", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({question: q})
            });
            const data = await res.json();
            ans.innerText = data.answer;
        } catch (err) {
            ans.innerText = "حدث خطأ أثناء الاتصال.";
        }
    }
    </script>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    q = data.get("question", "")
    return jsonify({"answer": assistant_answer(q)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
