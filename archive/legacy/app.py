from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import sqlite3
import html

DB = "training.db"

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def initialize():
    with connect() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS training_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            demo_value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

def page(content):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>249 SHADOW - Database</title>
    <style>
    *{{box-sizing:border-box}}
    body{{font-family:Arial;background:#f0f2f5;margin:0;padding:20px}}
    main{{max-width:650px;margin:25px auto;background:white;padding:22px;border-radius:15px}}
    h2{{color:#17243a}}
    input{{width:100%;padding:13px;margin:7px 0 14px;border:1px solid #ddd;border-radius:8px;font-size:16px}}
    button{{padding:11px 17px;border:0;border-radius:8px;background:#1769e0;color:white;cursor:pointer}}
    .delete{{background:#d93636}}
    .item{{border:1px solid #eee;border-radius:10px;padding:12px;margin:15px 0;overflow-wrap:anywhere}}
    .muted{{color:#777;font-size:13px}}
    a{{color:#1769e0}}
    </style>
    </head>
    <body><main>
    {content}
    </main></body></html>
    """

class App(BaseHTTPRequestHandler):

    def send_page(self, content):
        data = page(content).encode()
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect_home(self):
        self.send_response(303)
        self.send_header("Location","/")
        self.end_headers()

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        search = query.get("q", [""])[0]

        with connect() as db:
            if search:
                rows = db.execute("""
                    SELECT * FROM training_users
                    WHERE username LIKE ? OR demo_value LIKE ?
                    ORDER BY id DESC
                """, (f"%{search}%", f"%{search}%")).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM training_users ORDER BY id DESC"
                ).fetchall()

        content = """
        <h2>249 SHADOW | إدارة SQLite</h2>
        <p class="muted">قاعدة بيانات تعليمية محلية للبيانات الوهمية</p>
        <hr>
        <h3>إضافة سجل جديد</h3>
        <form method="POST" action="/add">
          <label>اسم المستخدم التجريبي</label>
          <input name="username" required>
          <label>قيمة نصية تجريبية (ليست كلمة مرور)</label>
          <input name="demo_value" required>
          <button>إضافة إلى قاعدة البيانات</button>
        </form>
        <hr>
        <h3>البحث في السجلات</h3>
        <form method="GET">
          <input name="q" placeholder="ابحث باسم المستخدم أو القيمة">
          <button>بحث</button>
          <a href="/">عرض الكل</a>
        </form>
        <hr>
        <h3>السجلات المحفوظة</h3>
        """

        if not rows:
            content += "<p>لا توجد سجلات حتى الآن.</p>"

        for r in rows:
            username = html.escape(r["username"])
            value = html.escape(r["demo_value"])
            created = html.escape(r["created_at"])

            content += f"""
            <div class="item">
              <b>رقم السجل:</b> {r['id']}<br><br>
              <b>اسم المستخدم:</b> {username}<br>
              <b>القيمة التجريبية:</b> {value}<br>
              <p class="muted">تاريخ الإنشاء: {created}</p>

              <details>
                <summary>تعديل السجل</summary>
                <form method="POST" action="/update">
                  <input type="hidden" name="id" value="{r['id']}">
                  <input name="username" value="{username}" required>
                  <input name="demo_value" value="{value}" required>
                  <button>حفظ التعديل</button>
                </form>
              </details>

              <form method="POST" action="/delete"
                onsubmit="return confirm('هل تريد حذف هذا السجل؟')">
                <input type="hidden" name="id" value="{r['id']}">
                <button class="delete">حذف السجل</button>
              </form>
            </div>
            """

        self.send_page(content)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 8192:
            self.send_error(413)
            return

        raw = self.rfile.read(length).decode("utf-8")
        data = parse_qs(raw)

        action = urlparse(self.path).path

        with connect() as db:
            if action == "/add":
                username = data.get("username", [""])[0].strip()
                value = data.get("demo_value", [""])[0]

                if username and value:
                    db.execute("""
                        INSERT INTO training_users
                        (username, demo_value)
                        VALUES (?, ?)
                    """, (username, value))

            elif action == "/update":
                record_id = data.get("id", [""])[0]
                username = data.get("username", [""])[0].strip()
                value = data.get("demo_value", [""])[0]

                if record_id.isdigit() and username and value:
                    db.execute("""
                        UPDATE training_users
                        SET username=?, demo_value=?
                        WHERE id=?
                    """, (username, value, int(record_id)))

            elif action == "/delete":
                record_id = data.get("id", [""])[0]

                if record_id.isdigit():
                    db.execute(
                        "DELETE FROM training_users WHERE id=?",
                        (int(record_id),)
                    )

        self.redirect_home()

initialize()

print("249 SHADOW Database")
print("http://127.0.0.1:8767")
HTTPServer(("127.0.0.1",8767),App).serve_forever()
