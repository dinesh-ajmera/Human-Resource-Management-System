import logging
import os
from datetime import date, datetime

import mysql.connector
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from mysql.connector import errorcode

import config
import models

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hrms")

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ---------- health check (for Docker, load balancers, monitoring) ----------
@app.route('/health')
def health():
    try:
        models.run("SELECT 1", fetch="one")
        return jsonify(status="ok", database="up"), 200
    except mysql.connector.Error:
        log.exception("health check: database is down")
        return jsonify(status="degraded", database="down"), 503


@app.route('/')
def welcome():
    try:
        models.run("SELECT 1", fetch="one")
    except mysql.connector.Error:
        log.exception("database is not connected")
        flash("database is not connected ")
        return render_template("error.html")
    return redirect(url_for('login'))


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if session.get('role') == 'employee':
        session.clear()
        return redirect(url_for('signup'))

    if request.method == "POST":
        first_name = request.form.get("fr_name")
        last_name = request.form.get("la_name")
        email = request.form.get("email")
        password = request.form.get("password")
        mob_nu = request.form.get("mob_num")
        role = request.form.get("role")

        if any(not x or str(x).strip() == ""
               for x in [first_name, last_name, email, password, mob_nu, role]):
            flash("submited empty data !!")
            return redirect(url_for('signup'))

        try:
            if role not in ("HR", "employee"):
                role = "employee"
            # Security: anyone could pick "HR" before. Now an HR account can be
            # created only by the first user or by a logged-in HR user.
            if role == "HR" and session.get('role') != "HR":
                hr_count = models.run(
                    "SELECT COUNT(*) FROM users WHERE role = %s",
                    ("HR",), fetch="one")[0]
                if hr_count > 0:
                    flash("Only HR can create HR accounts. "
                          "You were registered as employee.")
                    role = "employee"

            models.run(
                "INSERT INTO users (f_name, l_name, email, password, mob_nu, role)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                (first_name, last_name, email,
                 models.generate_password_hash(password), mob_nu, role),
                commit=True)
            return redirect(url_for("login"))
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY:
                return render_template("signup.html", data="user exists")
            log.exception("signup failed")
            return render_template("signup.html")

    return render_template("signup.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get('password')
        try:
            result = models.authenticate_user(email, password)
        except mysql.connector.Error:
            log.exception("login failed: database error")
            flash("database is not connected ")
            return render_template("error.html")
        if result:
            session['user_id'] = result[1]
            session['role'] = result[2]
            return redirect(url_for('dashboard'))
        flash("user is not exist")
        return render_template("login.html", data="Invalid email or password")
    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    if session.get('user_id'):
        if session.get('role') == "HR":
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))


@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/employees')
def employee_dashboard():
    if session.get('role') == 'employee':
        return render_template("employee_dashboard.html")
    return redirect(url_for('dashboard'))


@app.route('/admin', methods=["POST", 'GET'])
def admin_dashboard():
    if session.get('role') == 'HR':
        return render_template("admin_dashboard.html")
    return redirect(url_for('login'))


# ---------- leave management ----------
@app.route('/leave', methods=['POST'])
def leave():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    employee_comment = request.form.get('employee_comment') or ""

    if not (start_date and end_date):
        return redirect(url_for('dashboard'))
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return "invalid date format"

    if start_date < date.today():
        return "leave start date cannot be in the past"
    if end_date < start_date:
        return "dates are invalid: end date must not be before start date"

    try:
        models.run(
            "INSERT INTO leaves (employee_id, start_date, end_date,"
            " comments_from_empl) VALUES (%s, %s, %s, %s)",
            (session.get("user_id"), start_date, end_date, employee_comment),
            commit=True)
        return redirect(url_for('history'))
    except mysql.connector.Error:
        log.exception("could not save leave request")
        return "something goes wrong"


@app.route("/leaves", methods=["POST", "GET"])
def leaves():
    if session.get('role') != 'HR':
        return redirect(url_for('login'))
    result = models.run(
        "SELECT leave_id, employee_id, start_date, end_date,"
        " comments_from_empl, created_at FROM leaves WHERE status = %s",
        ('pending',), fetch="all")
    if result:
        return render_template('leaves.html', result=result)
    flash(" there is no leaves requests available . just chill bro !!!")
    return redirect(url_for('dashboard'))


@app.route('/admin_responce', methods=['POST', 'GET'])
def admin_responce():
    if request.method != 'POST' or session.get('role') != 'HR':
        return redirect(url_for('login'))

    responce = request.form.get('responce')
    comment = request.form.get('comment')
    leave_id = request.form.get('leave_id')
    if responce not in ('approved', 'rejected'):
        flash("invalid response")
        return redirect(url_for('leaves'))
    try:
        models.run(
            "UPDATE leaves SET status = %s, comments_from_HR = %s,"
            " approved_by = %s WHERE leave_id = %s",
            (responce, comment, session.get("user_id"), leave_id),
            commit=True)
        flash(f"leave is {responce} successfully")
        return redirect(url_for('leaves'))
    except mysql.connector.Error:
        log.exception("could not update leave")
        return " leave is not submit due to some technical essue"


@app.route('/history', methods=['POST', 'GET'])
def history():
    if session.get("role") == 'HR':
        result = models.run(
            "SELECT employee_id, approved_by, comments_from_empl,"
            " comments_from_HR, last_updated_at, start_date, end_date, status"
            " FROM leaves WHERE status != %s",
            ('pending',), fetch="all")
        return render_template('history_for_admin.html', result=result)
    if session.get("role") == 'employee':
        result = models.run(
            "SELECT approved_by, comments_from_empl, comments_from_HR,"
            " last_updated_at, start_date, end_date, status"
            " FROM leaves WHERE employee_id = %s",
            (session.get('user_id'),), fetch="all")
        return render_template('history_for_employee.html', result=result)
    return redirect(url_for('dashboard'))


# ---------- attendance ----------
@app.route('/check_in', methods=['POST', "GET"])
def check_in():
    if request.method != 'POST' or not session.get("user_id"):
        return redirect(url_for('login'))
    try:
        already = models.run(
            "SELECT status FROM attendance"
            " WHERE employee_id = %s AND attendance = CURDATE()",
            (session.get("user_id"),), fetch="one")
        if not already:
            models.run(
                "INSERT INTO attendance (employee_id, status) VALUES (%s, %s)",
                (session.get("user_id"), 'present'), commit=True)
            session['live_status'] = "live"
    except mysql.connector.Error:
        log.exception("check-in failed")
    return redirect(url_for('dashboard'))


@app.route('/check_out', methods=['POST', "GET"])
def check_out():
    if request.method != 'POST' or not session.get("user_id"):
        return redirect(url_for('login'))
    try:
        row = models.run(
            "SELECT live_status FROM attendance"
            " WHERE employee_id = %s AND attendance = CURDATE()",
            (session.get("user_id"),), fetch="one")
        if row and row[0] != 'checked_out':
            models.run(
                "UPDATE attendance SET live_status = %s"
                " WHERE employee_id = %s AND attendance = CURDATE()",
                ('checked_out', session.get("user_id")), commit=True)
    except mysql.connector.Error:
        log.exception("check-out failed")
    return redirect(url_for('dashboard'))


@app.route('/attendances', methods=['POST', 'GET'])
def attendaces():
    if session.get('role') == 'HR':
        result = models.run(
            "SELECT employee_id, attendance, status FROM attendance"
            " ORDER BY attendance DESC", fetch="all")
        return render_template("attendance.html", result=result)
    if session.get('role') == 'employee':
        result = models.run(
            "SELECT attendance, status FROM attendance WHERE employee_id = %s"
            " ORDER BY attendance DESC",
            (session.get('user_id'),), fetch="all")
        return render_template("attendance.html", result=result)
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,
            debug=os.environ.get("FLASK_DEBUG") == "1")
