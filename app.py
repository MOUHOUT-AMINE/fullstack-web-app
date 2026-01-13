from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "CHANGE-ME-TO-A-RANDOM-SECRET"  # important pour les sessions
DB_NAME = "database.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Table users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    # Table tasks (on garde comme avant pour l’instant)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET"])
def home():
    # Pour l’instant on affiche toujours la page tasks
    conn = get_connection()
    tasks = conn.execute("SELECT id, task FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", tasks=tasks)


# ---------- AUTH ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("register.html", error="Username and password are required.")

        password_hash = generate_password_hash(password)

        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- TASKS (comme avant) ----------

@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task", "").strip()
    if task:
        conn = get_connection()
        conn.execute("INSERT INTO tasks (task) VALUES (?)", (task,))
        conn.commit()
        conn.close()
    return redirect(url_for("home"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    conn = get_connection()

    if request.method == "POST":
        new_task = request.form.get("task", "").strip()
        if new_task:
            conn.execute("UPDATE tasks SET task = ? WHERE id = ?", (new_task, task_id))
            conn.commit()
        conn.close()
        return redirect(url_for("home"))

    task_row = conn.execute("SELECT id, task FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if task_row is None:
        return redirect(url_for("home"))
    return render_template("edit.html", task=task_row)


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
