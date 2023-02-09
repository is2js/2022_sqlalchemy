### config 변경

- 현재 src>config

  - 종류별로 class로 나뉜 상태 -> 객체 생성해서 하나씩 씀

  - **Base class가 있고 -> 바뀌는 변수들마다 Dev, Prod class가 상속해서 사용되어야함**

    - 객체가 아니라, **dict를 생성**해서 메모리에 올려 key로 바로 꺼내 쓸 수 있게

    ```python
    class ProductionConfig(Config):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    
    config = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    
        'default': DevelopmentConfig
    }
    ```

    

  - **app객체를 팩토리화 시킨 뒤, 팩토리 메서드에서 config key를 입력받아, `app.config.from_object()`로 `class를 넘겨`주면 `내부에서 객체 생성` 해당 컨피그를 적용**

    ```python
    def create_app(config_name):  
        app = Flask(__name__)  
    
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
    ```

  - **그외 상수사용은 `선택된 config_name(key)의 dict`가 app객체 속으로 들어갔으니  `current_app`객체를 이용해서 사용한다**

    ```python
    from flask.globals import current_app
    
    #...
    per_page=current_app.config['MYBLOG_POSTS_PER_PAGE'],error_out=False
    ```



#### 여러 Config class를 선택하는 것은 보니까,, 환경변수의 os.getenv('MYBLOG_CONFIG') **or** 'default' 로 결정된다. -> 나는 APP_CONFIG를 환경변수에서 받도록 한다



```python
app = create_app(os.getenv('MYBLOG_CONFIG') or 'default')


def create_app(config_name):  
    app = Flask(__name__)  

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

```



- **나의 경우 flask <-> db가 따로 설계되어있다보니까, flask의 app config와 별개로 db config도 config설정에 따라 뽑아야한다**
  - manage.py에서는 create_app( )시 인자로 config를 선택
  - src > config > settings.py에 준비되어있는 뽑기용 db dict를 마련 -> **db_config객체 생성시 환경변수에서 똑같이 뽑아서 선택되도록 해야할 것 같다.**
- **종류별 app config class와 마찬가지로 `db도 종류별 config class마련 -> 그자리에서 환경변수로 뽑아서 -> settings init에 올리기`작전을 써야할 것 같다.**
- 



#### FlaskConfig를 환경변수 string값에 의해 택1

```python
class FlaskConfig:
    # CORS
    SECRET_KEY = os.getenv("SECRET_KEY") or 'hard to guess string'

    #@staticmethod
    # 나는 app객체에 class를 넘기는게 아니라 객체를 넘겨서 import되어 사용될 예정이므로
    # self를 단 인스턴스 메서드를 작성한다?!
    def init_app(app: Flask):
        pass


class FlaskDevConfig(FlaskConfig):
    DEBUG = True # flask run의 운영환경과 별개


class FlaskTestingConfig(FlaskConfig):
    TESTING = True


class FlaskProdConfig(FlaskConfig):
    pass


app_config = {
    'development': FlaskDevConfig,
    'testing': FlaskTestingConfig,
    'production': FlaskProdConfig,
    'default': FlaskDevConfig,
}
app_config = app_config[os.getenv('APP_CONFIG') or 'default']()

```



#### ProjectConfig 환경변수 택1화

```python
# fastapi 세팅 참고
# https://github.com/heumsi/python-rest-api-server-101/blob/main/project/src/config.py
class Project:
    # project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION")
    # file
    BASE_FOLDER = Path(__file__).resolve().parent.parent.parent  # root
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
```



#### DB Config 택1화

```python
class DBProductionConfig(DB):
    if os.getenv("DB_CONNECTION"):
        DB_CONNECTION = os.getenv("DB_CONNECTION").lower()
        DB_USER: str = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT: str = os.getenv("DB_PORT", "3306")
        DB_NAME: str = os.getenv("DB_NAME", "test")

        DATABASE_URL = f"{DB_CONNECTION}://" \
                       f"{DB_USER}:{DB_PASSWORD}@" \
                       f"{DB_HOST}:{DB_PORT}/" \
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
```

- `production`이면서 `DB_CONNECTION이 주석해제`되어 작동되는 순간 -> RDB 설정으로 넘어간다

  ![image-20221208184428733](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208184428733.png)

  ```
  CONFIG>>> production
  DB_URL>>> mysql+pymysql://None:None@localhost:3306/tutorial3
  UPLOAD_FOLDER>>> C:\Users\is2js\pythonProject\2022_sqlalchemy\uploads
  ```

- **여기서 flask 변수 중 `ENV, TESTING = True`의 옵션은 `flask run`의 운영환경과 별개다**

  ![image-20221208222229231](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208222229231.png)

- **flask 실행 옵션은 `직접 환경변수로 설정`해줘야한다**





#### 내부 config를 위한 환경변수 .env

```yml
#### 비워둘거면 아예 주석처리해야 빈문자열이 안가서 python내부 default값이 적용된다.
#### config####  development or testing or production 
# (주석처리시 default key값인 development)
APP_CONFIG=development

#### project####  
# = upload_path를 비워두면, base + 'uploads/'를 업로드 폴더로 간주한다.
# PROJECT_NAME=
# PROJECT_VERSION=
# UPLOAD_PATH=



#### DB #### 
# = dev) DEV_DATABASE_URL을 따로 지정하지 않으면, base + DB_NAME or (DB_NAME주석처리시)data-dev.sqlite
# = testing) TEST_DATABASE_URL 따로 지정하지 않으면, sqlite:///:memory:로 작동한다 
# = prod) DB_CONNECTION를 주석처리시, base + DB_NAME or (DB_NAME주석처리시)data.sqlite
# POST_PER_PAGE = 10
# COMMENTS_PER_PAGE = 10

# DEV_DATABASE_URL= # 생략시 base+ [DB_NAME.db or data-dev.sqlite]
DB_NAME=tutorial3 # 생략시 base + data-dev.sqlite or data.sqlite 

#### production + RDB적용시 #### 
# DB_CONNECTION=mysql+pymysql # 생략시 sqlite로 돌아가며, base+ [DB_NAME.db or data-dev.sqlite]
# DB_USER=root
# DB_PASSWORD=564123
# DB_HOST=0.0.0.0
# DB_PORT=3306

#### FLASK #### 
SECRET_KEY = 'secret-key'


#### jwt #### 
# TOKEN_KEY=
# EXP_TIME_MIN=
# REFRESH_TIME_MIN
```





### app객체 팩토리화-> 팩토리 생성시 config상태를 받아 그에 맞는 flask 상태를 만들도록 + 순환참조 안되도록

- create_app 함수가 app 객체를 생성해 반환하도록 코드를 수정했다. 이때 app 객체가 함수 안에서 사용되므로 hello_pybo 함수를 create_app 함수 안에 포함했다. 바로 여기서 사용된 create_app 함수가 바로 **애플리케이션 팩토리**다.

  > 함수명으로 create_app 대신 다른 이름을 사용하면 정상으로 동작하지 않는다. create_app은 플라스크 내부에서 정의된 함수명이다.



- **[중요]!!** flask run 명령은 반드시 프로젝트 홈 디렉터리(`C:/projects/myproject`)에서 실행해야한다. 다른 곳에서 실행하면 실행은 되지만 정상으로 동작하지 않는다. 앞으로도 `flask run`으로 플라스크 서버를 실행할 때는 위치를 꼭 확인하자.

  - 파일명을 바꾸어도 플라스크 서버가 잘 실행된다. 우리는 플라스크 기본 앱을 `FLASK_APP=pybo`로 설정했다. 따라서 이전에 pybo는 프로젝트 루트에 있는 pybo.py 파일을 가리켰지만, 이번에는 pybo 모듈 즉 `pybo/__init__.py` 파일을 가리킨다.

    > `pybo.py` 와 `pybo/__init__.py`는 동일한 pybo 모듈이다.

    따라서 pybo.py 파일을 `pybo/__init__.py` 파일로 바꾸어도 오류없이 잘 동작한다.





- **my) create_app을 -> run.py manage.py에서 실제 객체를 만들어서 실행시키며, `실행이후에는 해당app객체의 순환참조를 받기 위해 from flask import current_app`으로 사용하는 것 같다**
  - 딱히 app객체가 사용될 일은 많이 없으나 **app.config에 심어둔 flaskconfig를 활용할 때 쓰일 수 있다.**



#### 기존방식과 변화

- 기존:
  - main > config > `app.py` 객체 생성 및 초기화 -> `init.py`에서는 import해서 메모리 올림 -> `run.py`에서 app객체 가져와서 사요
- **변경방식**
  - main > config > `init.py`에   팩토리메서드인 `create_app`정의 (app객체 생성 초기화 return app)
  - root > `manage.py`에서 create_app메서드 가져와서 app객체 생성하여 run



##### main > config > init.py

```python
# from .app import app

import datetime
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from sqlalchemy import select

from src.config import app_config

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Category, Setting

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

def create_app(config_name):
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    ## db환경변수를 개별로 넣지않고 config object로 넣는다.
    # app.config["SECRET_KEY"] = app_config.SECRET_KEY
    app.config.from_object(app_config)
    app_config.init_app(app)
    print("config_name>>>", config_name)
    print(app.config)

    ## extension객체들로 app객체 초기화
    CORS(app)

    ## 필터 추가
    from src.main.templates.filters import feed_datetime, join_phone
    app.jinja_env.filters["feed_datetime"] = feed_datetime
    app.jinja_env.filters["join_phone"] = join_phone

    ## bp아닌 것들은 add_url_rule용
    from src.main.routes import (
        main_bp, index,
        api_routes_bp, auth_bp,
        admin_bp,
        util_bp,
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(api_routes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(util_bp)

    # 기본 / url 지정 in route.py의 function
    app.add_url_rule('/', endpoint='index', view_func=index)
    from ..utils.upload_utils import download_file
    app.add_url_rule('/uploads/<path:filename>', endpoint='download_file', view_func=download_file)

    ## app context단위로 항상 떠있는 entity 객체value의 dict 반환 method 주입
    app.context_processor(inject_category_and_settings)
    app.context_processor(inject_today_date)

    ## [flask createadminuser] 명령어 추가
    from src.main.utils import init_script
    init_script(app)

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

```





##### root > manage.py

```python
import os
from src.main.config import create_app


app = create_app(os.getenv('APP_CONFIG') or 'default')

```



##### flask run용 환경변수는 FLASK_APP='manage.py'를 사용



#### flask run 실행 환경변수 run.cmd, run.ps1만들기

- SERVER_NAME= `host:port`
- PORT: FLASK_RUN_FORT

```powershell
$env:FLASK_APP='manage.py'
$env:FLASK_ENV='development'
$env:FLASK_DEBUG='true'
$env:FLASK_RUN_HOST='localhost'
$env:FLASK_RUN_PORT='5000'
```



```cmd
@echo off
set FLASK_APP='manage.py'
set FLASK_ENV='development'
set FLASK_DEBUG='true'
set FLASK_RUN_HOST='localhost'
set FLASK_RUN_PORT='5000'
```



`./run.ps`

`flask run`

