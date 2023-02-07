#!/bin/bash

#### uwsgi, gunicorn 사용 전까지, 직접 환경변수 입력용 sh
# 프로젝트 폴더로 이동
cd ~/projects/sqlalchemy

# development / testing / production / default
export APP_CONFIG=production
export FLASK_APP=manage.py

export FLASK_ENV=$APP_CONFIG
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000

# 가상환경 위치 + 실행까지
. ~/venvs/sqlalchemy/bin/activate