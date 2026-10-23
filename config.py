import os

# All settings come from environment variables, so no passwords live in code.
# Locally, copy .env.example to .env (Docker Compose reads it automatically).

DB_PORT = int(os.environ.get("DB_PORT"))
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

# Used to sign the login session cookie. Must be long and random in production.
SECRET_KEY = os.environ.get("SECRET_KEY")
