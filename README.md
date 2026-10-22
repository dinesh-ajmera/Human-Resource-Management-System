# HR Management System (Flask + MySQL)

A web app where employees sign up, check in and out, and request leave,
and HR approves or rejects leave and views attendance.

## Features
- Sign up and login (passwords are hashed)
- Two roles: **HR** and **employee**
- Employee: request leave, view leave history, check in / check out, view attendance
- HR: review pending leave requests, approve or reject with a comment,
  view leave history and everyone's attendance
- `/health` endpoint that reports whether the app and database are up

## Tech stack
Python, Flask, MySQL 8, Gunicorn, Docker, Docker Compose

## Run with Docker (recommended)
```bash
cp .env.example .env        # then edit the passwords and secret key
docker compose up -d --build
```
Open http://localhost:5000 and check http://localhost:5000/health

Create the first account with the role **HR**. After one HR account exists,
only a logged-in HR user can create more HR accounts; everyone else who
registers becomes an employee.

Stop everything: `docker compose down` (add `-v` to also delete the data).

## Run without Docker
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=yourpassword SECRET_KEY=something-random
python models.py            # creates the database and tables
python routes.py
```

## Configuration (environment variables)
| Variable | Meaning | Default |
|---|---|---|
| DB_HOST / DB_PORT | MySQL address | 127.0.0.1 / 3306 |
| DB_USER / DB_PASSWORD | MySQL login | root / (empty) |
| DB_NAME | Database name | HR_system |
| SECRET_KEY | Signs the login cookie | dev-only value |

## Project structure
```
routes.py        Flask routes (pages and actions)
models.py        Database connection, tables, login check
config.py        Settings read from environment variables
templates/       HTML pages
Dockerfile, docker-compose.yml, entrypoint.sh
```

## Roadmap
- [x] Containerized with Docker and Compose
- [ ] CI pipeline (GitHub Actions)
- [ ] Infrastructure on AWS with Terraform
- [ ] Jenkins pipeline and monitoring
