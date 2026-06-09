import os
import sqlite3
import secrets
from flask import Flask, render_template, request, \
    redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, \
    check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ✅ Strong random secret key
app.secret_key = secrets.token_hex(32)

# ✅ Security configurations
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

# ✅ Fix: Define constants for template names
LOGIN_TEMPLATE = "login.html"
UPLOAD_TEMPLATE = "upload.html"


def allowed_file(filename):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        admin_pass = os.environ.get(
            "ADMIN_PASSWORD", "admin123"
        )
        conn.execute("""
            INSERT OR IGNORE INTO users (username, password)
            VALUES (?, ?)
        """, ("admin", generate_password_hash(admin_pass)))


init_db()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password required")
            return render_template(LOGIN_TEMPLATE)

        if len(username) > 50 or len(password) > 50:
            flash("Invalid input length")
            return render_template(LOGIN_TEMPLATE)

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if user and check_password_hash(
                user["password"], password
            ):
                session.clear()
                session["user"] = username
                session.permanent = False
                return redirect(url_for("upload"))
            else:
                flash("Invalid credentials")

    return render_template(LOGIN_TEMPLATE)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("file")

        if not file or not file.filename:
            flash("No file selected")
            return render_template(
                UPLOAD_TEMPLATE, user=session["user"]
            )

        if not allowed_file(file.filename):
            flash("File type not allowed!")
            return render_template(
                UPLOAD_TEMPLATE, user=session["user"]
            )

        filename = secure_filename(file.filename)
        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"], filename
        )
        file.save(save_path)
        flash("File uploaded successfully!")

    return render_template(
        UPLOAD_TEMPLATE, user=session["user"]
    )


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    app.run(host=host, port=5000, debug=False)
