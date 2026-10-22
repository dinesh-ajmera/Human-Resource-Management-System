import logging
import re
import time

import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: F401

import config

log = logging.getLogger("hrms")

if not re.fullmatch(r"[A-Za-z0-9_]+", config.DB_NAME):
    raise ValueError("DB_NAME may only contain letters, numbers and underscore")

TABLES = {}

TABLES["users"] = (
    "CREATE TABLE IF NOT EXISTS users ("
    " user_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,"
    " f_name VARCHAR(30) NOT NULL,"
    " l_name VARCHAR(50) NOT NULL,"
    " email VARCHAR(100) UNIQUE NOT NULL,"
    " password VARCHAR(255) NOT NULL,"
    " created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
    " mob_nu CHAR(12) NOT NULL,"
    " role ENUM('HR', 'employee') NOT NULL DEFAULT 'employee'"
    ") ENGINE=InnoDB"
)

TABLES["leaves"] = (
    "CREATE TABLE IF NOT EXISTS leaves ("
    " leave_id INT PRIMARY KEY AUTO_INCREMENT,"
    " employee_id INT NOT NULL,"
    " approved_by INT DEFAULT NULL,"
    " start_date DATE NOT NULL,"
    " end_date DATE NOT NULL,"
    " comments_from_empl VARCHAR(200) NOT NULL,"
    " comments_from_HR VARCHAR(200) DEFAULT NULL,"
    " created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
    " last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    "   ON UPDATE CURRENT_TIMESTAMP,"
    " status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',"
    " FOREIGN KEY (approved_by) REFERENCES users(user_id),"
    " FOREIGN KEY (employee_id) REFERENCES users(user_id)"
    ") ENGINE=InnoDB"
)

TABLES["attendance"] = (
    "CREATE TABLE IF NOT EXISTS attendance ("
    " attendance_id INT PRIMARY KEY AUTO_INCREMENT,"
    " employee_id INT NOT NULL,"
    " check_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
    " check_out TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,"
    " attendance DATE DEFAULT (CURRENT_DATE),"
    " live_status ENUM('live', 'checked_out') DEFAULT 'live',"
    " status ENUM('absent', 'present', 'half_day', 'leave') DEFAULT 'absent',"
    " UNIQUE KEY one_record_per_day (employee_id, attendance),"
    " FOREIGN KEY (employee_id) REFERENCES users(user_id)"
    ") ENGINE=InnoDB"
)


def connect(with_database=True):
    """Open a new MySQL connection using settings from config.py."""
    params = dict(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        connection_timeout=5,
    )
    if with_database:
        params["database"] = config.DB_NAME
    return mysql.connector.connect(**params)


def run(sql, params=(), fetch=None, commit=False):
    """Run one SQL query on its own connection.

    fetch: "one" -> one row, "all" -> list of rows, None -> nothing.
    Rows are plain tuples, in the same column order as the SELECT.
    """
    cnx = connect()
    cursor = cnx.cursor()
    try:
        cursor.execute(sql, params)
        result = None
        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "all":
            result = cursor.fetchall()
        if commit:
            cnx.commit()
        return result
    finally:
        cursor.close()
        cnx.close()


def init_db(retries=10, delay=3):
    """Create the database and tables if they do not exist.

    Retries for a while, because MySQL can take a few seconds to start.
    """
    cnx = None
    for attempt in range(1, retries + 1):
        try:
            cnx = connect(with_database=False)
            break
        except mysql.connector.Error as err:
            log.warning("MySQL not ready (%s/%s): %s", attempt, retries, err)
            time.sleep(delay)
    if cnx is None:
        raise RuntimeError("Could not connect to MySQL")

    cursor = cnx.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}`")
    cursor.execute(f"USE `{config.DB_NAME}`")
    for name, ddl in TABLES.items():
        cursor.execute(ddl)
        log.info("table %s ready", name)
    cnx.commit()
    cursor.close()
    cnx.close()


def authenticate_user(email, password):
    """Return (password_hash, user_id, role) if login is valid, else None."""
    row = run(
        "SELECT password, user_id, role FROM users WHERE email = %s",
        (email,),
        fetch="one",
    )
    if row and check_password_hash(row[0], password):
        return row
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("Database and tables are ready")
