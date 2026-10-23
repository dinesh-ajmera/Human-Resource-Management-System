#!/bin/sh
set -e

# 1) create the database tables if they do not exist
python models.py

# 2) start the web server
python routes.py
