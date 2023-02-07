#!/bin/bash

# 프로젝트 폴더로 이동
cd ~/projects/sqlalchemy

export FLASK_APP=manage.py
export APP_CONFIG=production

export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000

# 가상환경 위치 + 실행까지
. ~/venvs/sqlalchemy/bin/activate