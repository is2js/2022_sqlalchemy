@echo off

:: development / testing / production / default
set APP_CONFIG=production
set FLASK_APP=manage.py

set FLASK_ENV=%APP_CONFIG%
set FLASK_RUN_HOST=localhost
set FLASK_RUN_PORT=5000

.\venv\Scripts\activate

