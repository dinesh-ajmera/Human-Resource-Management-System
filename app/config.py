import os

# All settings come from environment variables, so no passwords live in code.
# Locally, copy .env.example to .env (Docker Compose reads it automatically).

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "HR_system")

# Used to sign the login session cookie. Must be long and random in production.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
