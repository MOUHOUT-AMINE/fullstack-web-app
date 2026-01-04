from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_NAME = "database.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
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
    conn.row_factory = sqlite3.Row  # pour accéder comme un dictionnaire: row["task"]
    return conn


@app.route("/", methods=["GET"])
def home():
    conn = get_connection()
    tasks = conn.execute("SELECT id, task FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", tasks=tasks)


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
