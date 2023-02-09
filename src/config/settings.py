import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from logging.config import dictConfig

dotenv_path = Path("./.env")
load_dotenv(dotenv_path=dotenv_path)

BASE_FOLDER = Path(__file__).resolve().parent.parent.parent  # root( config -> src -> root)


# fastapi 세팅 참고
# https://github.com/heumsi/python-rest-api-server-101/blob/main/project/src/config.py
class Project:
    # project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME") or 'sqlalchemy'  # 직접 deafult값  줌
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION")
    # user생성시 role안넣은 상태에서, email이 정해진 email이면, 관리자 Role을 넣어준다.
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL") or 'tingstyle1@gmail.com'  # 직접 default 값 줌


# path로 join만 하면 [마지막을 파일명으로 취급]하여 '/'가 없다.
# -> 뒤에 개별폴더명이 붙을 joinpath라면 + '마지막 폴더명/'을 붙여서 연결하여, 다음엔 '/'없이 파일명 or 개별폴더명/파일명만 올 수 있도록 만든다.
# UPLOAD_FOLDER = BASE_FOLDER.joinpath('uploads/')
class ProjectDevConfig(Project):
    UPLOAD_FOLDER = BASE_FOLDER.joinpath('uploads/')


class ProjectTestingConfig(Project):
    UPLOAD_FOLDER = BASE_FOLDER.joinpath('uploads/')


class ProjectProdConfig(Project):
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER') \
                    or BASE_FOLDER.joinpath('uploads/')


project_config = {
    'development': ProjectDevConfig,
    'testing': ProjectTestingConfig,
    'production': ProjectProdConfig,

    'default': ProjectDevConfig
}
project_config = project_config[os.getenv('APP_CONFIG') or 'default']()


class DB:
    POST_PER_PAGE = int(os.getenv("POST_PER_PAGE", "10"))
    COMMENTS_PER_PAGE = int(os.getenv("COMMENTS_PER_PAGE", "20"))


class DBDevConfig(DB):
    DATABASE_URL = 'sqlite:///' + os.path.join(BASE_FOLDER, f'{os.getenv("DB_NAME") or "data"}-dev.db')


class DBTestingConfig(DB):
    DATABASE_URL = 'sqlite:///:memory:'


class DBProductionConfig(DB):
    # .env 파일에 DB_CONNECTION 여부가 sqlite vs RDB를 결정한다.
    if os.getenv("DB_CONNECTION"):
        DB_CONNECTION = os.getenv("DB_CONNECTION").lower()
        DB_USER: str = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT: str = os.getenv("DB_PORT", "3306")
        DB_NAME: str = os.getenv("DB_NAME", "test")

        DATABASE_URL = f"{DB_CONNECTION}://" \
                       f"{DB_USER}:{DB_PASSWORD}@" \
                       f"{DB_HOST}:{DB_PORT}/" \
                       f"{DB_NAME}"
    else:
        DATABASE_URL = 'sqlite:///' + os.path.join(BASE_FOLDER, f'{os.getenv("DB_NAME") or "data"}-prod.db')


db_config = {
    'development': DBDevConfig,
    'testing': DBTestingConfig,
    'production': DBProductionConfig,

    'default': DBDevConfig
}
db_config = db_config[os.getenv('APP_CONFIG') or 'default']()


class Auth:
    # jwt. Watch out -> int( None )
    TOKEN_KEY = os.getenv("TOKEN_KEY")
    EXP_TIME_MIN = int(os.getenv("EXP_TIME_MIN", "30"))
    REFRESH_TIME_MIN = int(os.getenv("REFRESH_TIME_MIN", "15"))


auth_config = Auth()


class FlaskConfig:
    # CORS
    SECRET_KEY = os.getenv("SECRET_KEY") or 'hard to guess string'

    # @staticmethod
    # def init_app(app: Flask):
    #     pass

    # 나는 app객체에 class를 넘기는게 아니라 객체를 넘겨서 import되어 사용될 예정이므로
    # self를 단 인스턴스 메서드를 작성한다?!
    def init_app(self, app: Flask):
        pass


class FlaskDevConfig(FlaskConfig):
    DEBUG = True


class FlaskTestingConfig(FlaskConfig):
    TESTING = True


class FlaskProdConfig(FlaskConfig):
    DEBUG = False


app_config = {
    'development': FlaskDevConfig,
    'testing': FlaskTestingConfig,
    'production': FlaskProdConfig,
    'default': FlaskDevConfig,
}

app_config = app_config[os.getenv('APP_CONFIG') or 'default']()

# print("CONFIG>>>", os.getenv('APP_CONFIG'))
# print("DB_URL>>>", db_config.DATABASE_URL)
# print("UPLOAD_FOLDER>>>", project_config.UPLOAD_FOLDER)


if os.getenv('APP_CONFIG') == 'production':
    # Prod 환경일때만, 로깅 폴더 만들고 적용하기
    # 1) Prod에서 로그폴더 자동 생성
    LOG_FOLDER = os.path.join(BASE_FOLDER, 'logs/')
    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)

    # 1) logging 설정
    dictConfig({
        'version': 1, # 1 고정값 사용. 버전무관하게 만들어주는 안전장치
        'formatters': {
            # 출력형식 : 현재시간 / 로그레벨 / 로그호출 모듈명 / 출력내용
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }
        },
        'handlers': {
            # 출력 방법 -> file로
            'file': {
                # 출력 로그 레벨 설정: 그 이상 레벨을 다 출력한다. (DEBUG < INFO < WARNING < ERROR < CRITICAL)
                # => logging.debug, logging.info, logging.warning, logging.error, logging.critical 함수 중 logging.debug는 출력안될 것이다.
                # - 1단계 DEBUG: 디버깅 목적으로 사용
                # - 2단계 INFO: 일반 정보를 출력할 목적으로 사용
                # - 3단계 WARNING: 경고 정보를 출력할 목적으로(작은 문제) 사용
                # - 4단계 ERROR: 오류 정보를 출력할 목적으로(큰 문제) 사용
                # - 5단계 CRITICAL: 아주 심각한 문제를 출력할 목적으로 사용
                'level': 'INFO',
                # 로그핸들러 class지정.
                # - RotatingFileHandler는 파일크기가 설정한 값보다 커지면 파일 뒤에 인덱스를 붙여 백업. RotatingFileHandler의 장점은 로그가 무한히 생겨도 파일 개수를 일정하게 유지(rolling)하므로 "로그 파일이 너무 커져서 디스크가 꽉 차는 위험"을 방지
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_FOLDER, f'{project_config.PROJECT_NAME}.log'),
                'maxBytes': 1024 * 1024 * 5,  # 5 MB
                # maxBytes을 넘어설 때 최대 만들 로그파일 갯수.
                'backupCount': 5,
                'formatter': 'default',
            },
        },
        # 최상위 로거 설정
        'root': {
            'level': 'INFO',
            'handlers': ['file']
        }
    })
