import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

dotenv_path = Path("./.env")
load_dotenv(dotenv_path=dotenv_path)

BASE_FOLDER = Path(__file__).resolve().parent.parent.parent  # root


# fastapi 세팅 참고
# https://github.com/heumsi/python-rest-api-server-101/blob/main/project/src/config.py
class Project:
    # project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION")
    # user생성시 role안넣은 상태에서, email이 정해진 email이면, 관리자 Role을 넣어준다.
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL") or 'tingstyle1@gmail.com'


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
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or \
                   'sqlite:///' + os.path.join(BASE_FOLDER, f'{os.getenv("DB_NAME") or "data"}-dev.db')


class DBTestingConfig(DB):
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL') or \
                   'sqlite:///:memory:'


class DBProductionConfig(DB):
    if os.getenv("DB_CONNECTION"):
        DB_CONNECTION = os.getenv("DB_CONNECTION").lower()
        DB_USER: str = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
        DB_SERVER = os.getenv("DB_SERVER", "localhost")
        DB_PORT: str = os.getenv("DB_PORT", "3306")
        DB_NAME: str = os.getenv("DB_NAME", "test")

        DATABASE_URL = f"{DB_CONNECTION}://" \
                       f"{DB_USER}:{DB_PASSWORD}@" \
                       f"{DB_SERVER}:{DB_PORT}/" \
                       f"{DB_NAME}"
    else:
        DATABASE_URL = 'sqlite:///' + os.path.join(BASE_FOLDER, f'{os.getenv("DB_NAME")}.db' or "data.sqlite")


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
    DEBUG = True  # flask run의 운영환경과 별개


class FlaskTestingConfig(FlaskConfig):
    TESTING = True


class FlaskProdConfig(FlaskConfig):
    ENV = 'production'
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
