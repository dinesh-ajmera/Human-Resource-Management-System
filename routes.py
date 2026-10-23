import hmac
import logging
import os
import re
import secrets
from datetime import date, datetime
from functools import wraps

import mysql.connector
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from mysql.connector import errorcode

import config
import models

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hrms")

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ======================================================================
# Helpers: CSRF protection, access control, template filters, errors
# ======================================================================
def csrf_token():
    """One random token per session. Every POST form must send it back."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        expected = session.get("_csrf")
        sent = request.form.get("_csrf", "")
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400)


def login_required(roles=None):
    """Allow only logged-in users, optionally only some roles."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            if roles and session.get("role") not in roles:
                flash("You do not have access to that page.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapper
    return decorator


@app.template_filter("date_fmt")
def date_fmt(value):
    return value.strftime("%d %b %Y") if value else "—"


@app.template_filter("long_date")
def long_date(value):
    return value.strftime("%A, %d %B %Y") if value else ""


@app.template_filter("time_fmt")
def time_fmt(value):
    return value.strftime("%I:%M %p").lstrip("0") if value else "—"


@app.template_filter("datetime_fmt")
def datetime_fmt(value):
    return value.strftime("%d %b %Y, %I:%M %p") if value else "—"


@app.template_filter("days_between")
def days_between(start, end):
    return (end - start).days + 1


@app.template_filter("duration")
def duration(start, end):
    if not (start and end):
        return "—"
    minutes = int((end - start).total_seconds() // 60)
    return f"{minutes // 60}h {minutes % 60}m"


def error_page(message, code):
    return render_template("error.html", message=message, code=code), code


@app.errorhandler(mysql.connector.Error)
def database_error(err):
    log.error("database error: %s", err)
    return error_page("We could not reach the database. "
                      "Please try again in a moment.", 503)


@app.errorhandler(400)
def bad_request(_err):
    return error_page("Your session expired or the form was not valid. "
                      "Please go back, refresh the page and try again.", 400)


@app.errorhandler(404)
def not_found(_err):
    return error_page("That page does not exist.", 404)


@app.errorhandler(405)
def not_allowed(_err):
    return error_page("That action is not allowed here.", 405)


@app.errorhandler(500)
def server_error(_err):
    return error_page("Something went wrong on our side.", 500)


def greeting():
    hour = datetime.now().hour
    return "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"


def today_attendance(user_id):
    return models.run(
        "SELECT check_in, check_out, live_status, status FROM attendance"
        " WHERE employee_id = %s AND attendance = CURDATE()",
        (user_id,), fetch="one", as_dict=True)


# ======================================================================
# Health check and landing
# ======================================================================
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
    models.run("SELECT 1", fetch="one")   # shows the error page if DB is down
    return redirect(url_for('login'))


# ======================================================================
# Accounts
# ======================================================================
def hr_signup_allowed():
    """HR accounts: only the very first user, or a logged-in HR user."""
    if session.get('role') == 'HR':
        return True
    count = models.run("SELECT COUNT(*) FROM users WHERE role = %s",
                       ("HR",), fetch="one")[0]
    return count == 0


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if session.get('role') == 'employee':
        session.clear()
        return redirect(url_for('signup'))

    allow_hr = hr_signup_allowed()
    if request.method == "GET":
        return render_template("signup.html", allow_hr=allow_hr)

    first_name = (request.form.get("fr_name") or "").strip()
    last_name = (request.form.get("la_name") or "").strip()
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    mob_nu = (request.form.get("mob_num") or "").strip()
    role = request.form.get("role") or "employee"

    def fail(message):
        return render_template("signup.html", allow_hr=allow_hr,
                               data=message), 400

    if not all([first_name, last_name, email, password, mob_nu]):
        return fail("Please fill in every field.")
    if len(password) < 6:
        return fail("Password must be at least 6 characters.")
    if not re.fullmatch(r"\d{10,12}", mob_nu):
        return fail("Mobile number must be 10 to 12 digits.")

    if role not in ("HR", "employee"):
        role = "employee"
    if role == "HR" and not allow_hr:
        flash("Only HR can create HR accounts, so you were registered "
              "as an employee.", "info")
        role = "employee"

    try:
        models.run(
            "INSERT INTO users (f_name, l_name, email, password, mob_nu, role)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (first_name, last_name, email,
             models.generate_password_hash(password), mob_nu, role),
            commit=True)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return fail("An account with this email already exists.")
        raise

    if session.get('role') == 'HR':
        flash(f"Account created for {first_name} {last_name} ({role}).",
              "success")
        return redirect(url_for('admin_dashboard'))
    flash("Account created. You can log in now.", "success")
    return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = (request.form.get("email") or "").strip()
        password = request.form.get('password') or ""
        result = models.authenticate_user(email, password)
        if result:
            session.clear()
            session['user_id'] = result[1]
            session['role'] = result[2]
            session['name'] = result[3]
            return redirect(url_for('dashboard'))
        return render_template("login.html",
                               data="Invalid email or password."), 401
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return render_template("login.html")


@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required()
def dashboard():
    if session.get('role') == "HR":
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('employee_dashboard'))


# ======================================================================
# Dashboards
# ======================================================================
@app.route('/employees')
@login_required(roles=("employee",))
def employee_dashboard():
    user_id = session['user_id']
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for row in models.run(
            "SELECT status, COUNT(*) AS n FROM leaves"
            " WHERE employee_id = %s GROUP BY status",
            (user_id,), fetch="all", as_dict=True):
        if row["status"] in counts:
            counts[row["status"]] = row["n"]
    recent = models.run(
        "SELECT leave_id, start_date, end_date, status FROM leaves"
        " WHERE employee_id = %s ORDER BY created_at DESC LIMIT 5",
        (user_id,), fetch="all", as_dict=True)
    return render_template("employee_dashboard.html",
                           greeting=greeting(), today_date=date.today(),
                           today=today_attendance(user_id),
                           counts=counts, recent=recent)


@app.route('/admin', methods=["POST", 'GET'])
@login_required(roles=("HR",))
def admin_dashboard():
    stats = models.run(
        "SELECT"
        " (SELECT COUNT(*) FROM users WHERE role = 'employee') AS employees,"
        " (SELECT COUNT(*) FROM leaves WHERE status = 'pending') AS pending,"
        " (SELECT COUNT(*) FROM attendance"
        "   WHERE attendance = CURDATE()) AS present_today,"
        " (SELECT COUNT(*) FROM attendance WHERE attendance = CURDATE()"
        "   AND live_status = 'live') AS working_now",
        fetch="one", as_dict=True)
    return render_template("admin_dashboard.html",
                           greeting=greeting(), today_date=date.today(),
                           today=today_attendance(session['user_id']),
                           stats=stats)


# ======================================================================
# Leave management
# ======================================================================
@app.route('/leave', methods=['POST'])
@login_required()
def leave():
    start_raw = request.form.get('start_date')
    end_raw = request.form.get('end_date')
    comment = (request.form.get('employee_comment') or "").strip()[:200]

    try:
        start_date = datetime.strptime(start_raw, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_raw, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        flash("Please choose valid start and end dates.", "error")
        return redirect(url_for('dashboard'))

    if start_date < date.today():
        flash("Leave cannot start in the past.", "error")
        return redirect(url_for('dashboard'))
    if end_date < start_date:
        flash("The end date cannot be before the start date.", "error")
        return redirect(url_for('dashboard'))
    if not comment:
        flash("Please give a short reason for your leave.", "error")
        return redirect(url_for('dashboard'))

    models.run(
        "INSERT INTO leaves (employee_id, start_date, end_date,"
        " comments_from_empl) VALUES (%s, %s, %s, %s)",
        (session['user_id'], start_date, end_date, comment), commit=True)
    flash("Leave request submitted. HR will review it soon.", "success")
    return redirect(url_for('history'))


@app.route('/leave/cancel', methods=['POST'])
@login_required()
def cancel_leave():
    models.run(
        "DELETE FROM leaves WHERE leave_id = %s AND employee_id = %s"
        " AND status = 'pending'",
        (request.form.get('leave_id'), session['user_id']), commit=True)
    flash("Leave request cancelled.", "info")
    return redirect(request.referrer or url_for('history'))


@app.route("/leaves", methods=["POST", "GET"])
@login_required(roles=("HR",))
def leaves():
    result = models.run(
        "SELECT l.leave_id, l.employee_id,"
        " CONCAT(u.f_name, ' ', u.l_name) AS employee_name,"
        " l.start_date, l.end_date, l.comments_from_empl AS employee_comment,"
        " l.created_at"
        " FROM leaves l JOIN users u ON u.user_id = l.employee_id"
        " WHERE l.status = %s ORDER BY l.created_at",
        ('pending',), fetch="all", as_dict=True)
    return render_template('leaves.html', result=result)


@app.route('/admin_responce', methods=['POST', 'GET'])
@login_required(roles=("HR",))
def admin_responce():
    if request.method != 'POST':
        return redirect(url_for('leaves'))

    responce = request.form.get('responce')
    if responce not in ('approved', 'rejected'):
        flash("Invalid response.", "error")
        return redirect(url_for('leaves'))

    models.run(
        "UPDATE leaves SET status = %s, comments_from_HR = %s,"
        " approved_by = %s WHERE leave_id = %s AND status = 'pending'",
        (responce, (request.form.get('comment') or "").strip()[:200],
         session['user_id'], request.form.get('leave_id')), commit=True)
    flash(f"Leave request {responce}.",
          "success" if responce == "approved" else "info")
    return redirect(url_for('leaves'))


@app.route('/history', methods=['POST', 'GET'])
@login_required()
def history():
    if session.get("role") == 'HR':
        result = models.run(
            "SELECT l.leave_id, CONCAT(e.f_name, ' ', e.l_name) AS employee_name,"
            " CONCAT(a.f_name, ' ', a.l_name) AS responder,"
            " l.comments_from_empl AS employee_comment,"
            " l.comments_from_HR AS hr_comment, l.last_updated_at,"
            " l.start_date, l.end_date, l.status"
            " FROM leaves l JOIN users e ON e.user_id = l.employee_id"
            " LEFT JOIN users a ON a.user_id = l.approved_by"
            " WHERE l.status != %s ORDER BY l.last_updated_at DESC",
            ('pending',), fetch="all", as_dict=True)
        return render_template('history_for_admin.html', result=result)

    result = models.run(
        "SELECT l.leave_id, CONCAT(a.f_name, ' ', a.l_name) AS responder,"
        " l.comments_from_empl AS employee_comment,"
        " l.comments_from_HR AS hr_comment, l.last_updated_at,"
        " l.start_date, l.end_date, l.status"
        " FROM leaves l LEFT JOIN users a ON a.user_id = l.approved_by"
        " WHERE l.employee_id = %s ORDER BY l.created_at DESC",
        (session.get('user_id'),), fetch="all", as_dict=True)
    return render_template('history_for_employee.html', result=result)


# ======================================================================
# Attendance
# ======================================================================
@app.route('/check_in', methods=['POST', "GET"])
@login_required()
def check_in():
    if request.method != 'POST':
        return redirect(url_for('dashboard'))
    if today_attendance(session['user_id']):
        flash("You have already checked in today.", "info")
    else:
        models.run(
            "INSERT INTO attendance (employee_id, status) VALUES (%s, %s)",
            (session['user_id'], 'present'), commit=True)
        flash("Checked in. Have a great day!", "success")
    return redirect(url_for('dashboard'))


@app.route('/check_out', methods=['POST', "GET"])
@login_required()
def check_out():
    if request.method != 'POST':
        return redirect(url_for('dashboard'))
    row = today_attendance(session['user_id'])
    if not row:
        flash("You have not checked in today.", "error")
    elif row["live_status"] == 'checked_out':
        flash("You have already checked out today.", "info")
    else:
        models.run(
            "UPDATE attendance SET live_status = %s"
            " WHERE employee_id = %s AND attendance = CURDATE()",
            ('checked_out', session['user_id']), commit=True)
        flash("Checked out. See you tomorrow!", "success")
    return redirect(url_for('dashboard'))


@app.route('/attendances', methods=['POST', 'GET'])
@login_required()
def attendaces():
    if session.get('role') == 'HR':
        result = models.run(
            "SELECT a.attendance AS day,"
            " CONCAT(u.f_name, ' ', u.l_name) AS employee_name,"
            " a.check_in, a.check_out, a.status, a.live_status"
            " FROM attendance a JOIN users u ON u.user_id = a.employee_id"
            " ORDER BY a.attendance DESC, a.check_in DESC LIMIT 500",
            fetch="all", as_dict=True)
    else:
        result = models.run(
            "SELECT attendance AS day, check_in, check_out, status,"
            " live_status FROM attendance WHERE employee_id = %s"
            " ORDER BY attendance DESC LIMIT 200",
            (session.get('user_id'),), fetch="all", as_dict=True)
    return render_template("attendance.html", result=result)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,
            debug=os.environ.get("FLASK_DEBUG") == "1")
