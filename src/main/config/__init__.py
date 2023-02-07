# from .app import app

import datetime
from pathlib import Path

from flask import Flask, render_template
from flask_cors import CORS
from sqlalchemy import select

from src.config import app_config

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Category, Setting, Permission, Roles

## Path.cwd()는 실행파일(root의 run.py)의 위치가 찍힌다 -> root부터 경로잡기
# -> path는 joinpath시 끝이 디렉토리라면 / 까지 넣어줘야한다.

template_dir = str(Path.cwd().joinpath('src/main/templates/'))
static_dir = str(Path.cwd().joinpath('src/main/static/'))
print(f"template_dir: {template_dir}\n"
      f"static_dir: {static_dir}")


## 추가 extenstion객체 생성
# migrate = Migrate()
# moment = Moment()
# pagedown = PageDown()


def create_app(config_name='default'):
    print("config_name>>>", config_name)

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir,
                instance_relative_config=True
                )

    ## db환경변수를 개별로 넣지않고 config object로 넣는다.
    # app.config["SECRET_KEY"] = app_config.SECRET_KEY
    # app_config.init_app(app)
    app.config.from_object(app_config)
    print(app.config)

    ## extension객체들로 app객체 초기화
    CORS(app)

    ## 필터 추가
    from src.main.templates.filters import feed_datetime, join_phone, join_birth, format_date, format_datetime, \
        format_timedelta
    app.jinja_env.filters["feed_datetime"] = feed_datetime
    app.jinja_env.filters["join_phone"] = join_phone
    app.jinja_env.filters["join_birth"] = join_birth
    app.jinja_env.filters["format_date"] = format_date
    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["format_timedelta"] = format_timedelta

    ## bp아닌 것들은 add_url_rule용
    from src.main.routes import (
        main_bp, index,
        api_routes_bp, auth_bp,
        admin_bp,
        util_bp,
        dept_bp,
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(api_routes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(util_bp)
    app.register_blueprint(dept_bp)

    # 기본 / url 지정 in route.py의 function
    app.add_url_rule('/', endpoint='index', view_func=index)
    from ..utils.upload_utils import download_file
    app.add_url_rule('/uploads/<path:filename>', endpoint='download_file', view_func=download_file)

    ## app context단위로 항상 떠있는 entity 객체value의 dict 반환 method 주입
    app.context_processor(inject_category_and_settings)
    app.context_processor(inject_today_date)
    # app.context_processor(inject_permission_and_roles)
    app.context_processor(inject_permission)

    ## [flask xxxx] 명령어 추가
    from src.main.utils import init_script
    init_script(app)

    ## 오류페이지 등록
    app.register_error_handler(404, render_error)
    app.register_error_handler(500, render_error)

    return app


def inject_category_and_settings():
    with DBConnectionHandler() as db:
        categories = db.session.scalars(
            select(Category)
            .order_by(Category.id.asc())
        ).all()

        settings = Setting.to_dict()

    return dict(
        categories=categories,
        settings=settings,
    )


def inject_today_date():
    return {'today_date': datetime.date.today}


# def inject_permission_and_roles():
## role Roles이넘을 이용해 user객체의 hybrid_property로 다 정해줌
def inject_permission():
    return dict(
        Permission=Permission,
        # Roles=Roles,
    )


## 에러 핸들링
# def page_not_found(e):
def render_error(e):
    # print(dir(e))
    # 'args', 'code', 'description', 'get_body', 'get_description', 'get_headers', 'get_response', 'name', 'response', 'with_traceback', 'wrap']
    # print(e.code) # 404
    # print(e.description) # The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

    return render_template(
        'errors/404.html',
        status_code=e.code,
        description=e.description), e.code
