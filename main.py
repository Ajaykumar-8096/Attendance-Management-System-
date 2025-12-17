from flask import Flask, render_template, request, redirect, session
from db_config import get_db_connection
import hashlib
from datetime import date

app = Flask(__name__)
app.secret_key = "attendance_secret"

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (username, password))
        user = cur.fetchone()
        cur.close()
        db.close()

        if user:
            session["user_id"] = user["user_id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/user")

    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s,%s,'user')",
                    (username, password))
        db.commit()

    cur.execute("""
        SELECT users.username, attendance.date, attendance.status
        FROM attendance
        JOIN users ON attendance.user_id = users.user_id
    """)
    records = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin_dashboard.html", records=records)

@app.route("/user", methods=["GET", "POST"])
def user():
    if "role" not in session or session["role"] != "user":
        return redirect("/")

    user_id = session["user_id"]

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute(
            "INSERT INTO attendance (user_id, date, status) VALUES (%s,%s,'Present')",
            (user_id, date.today())
        )
        db.commit()

    cur.execute("SELECT * FROM attendance WHERE user_id=%s", (user_id,))
    records = cur.fetchall()

    cur.close()
    db.close()

    return render_template("user_dashboard.html", records=records)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
