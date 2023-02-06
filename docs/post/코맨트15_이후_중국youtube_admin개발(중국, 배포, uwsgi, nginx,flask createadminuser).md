### flask 배포를 위한 이동

http://www.lotdoc.cn/blog/detail/194/?menu=6



#### python-dotenv 설치(.env파일 자동인식시 필수)



##### flask shell 및 flask run 을 위한, .flaskenv 생성 및 사용 -> .env가 있으면 씹히니 .env에 flask실행 환경변수 2개 지정

- **일반적으로 `flask shell`을 실행하면 환경변수가 적용안되어 `production`으로 실행된다**

  ![image-20221207232416640](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207232416640.png)

- cmd는 `set `  powershell은 `$env:`로 설정하던 환경변수를 해당 `.flaskenv`파일에 명령어 빼고 넣는다

  - .flaskenv

    ```
    FLASK_APP=run.py
    FLASK_ENV=development
    ```

  - **.env .flaskenv 둘다 있는 경우 `.env`를 읽는다**



##### .env에 코드로 사용될일이 없는, 환경변수를 내부(src>confg>settings.py) class로 정의안하고 그냥 .env에만 정의해도 된다.

- 실행시 필요한 환경변수는 그냥 .env맨위에다 정의해주자

  ```
  # jwt
  # TOKEN_KEY=
  # EXP_TIME_MIN=
  # REFRESH_TIME_MIN
  
  
  # run
  # flask 실행시만 필요한 변수(class에 정의안함)
  FLASK_APP=run.py
  FLASK_DEBUG=development
  ```

  ![image-20221207234420980](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207234420980.png)





##### .env에 정의 + python-dotenv 만 해주면, flask run시에도 자동 develop으로 실행된다

![image-20221207234502848](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207234502848.png)







#### Click패키지를 이용한 flask xxxx 명령어 생성(flask설치시 자동설치)

- Werkzeug는 애플리케이션과 서버 간의 표준 Python 인터페이스인 WSGI를 구현합니다.
- Jinja는 애플리케이션에서 제공하는 페이지를 렌더링하는 데 사용되는 템플릿 언어입니다.
  MarkupSafe는 Jinja와 함께 제공됩니다. 주입 공격을 피하기 위해 템플릿을 렌더링할 때 신뢰할 수 없는 입력을 피합니다.
- ItsDangerous는 무결성을 보장하기 위해 데이터에 안전하게 서명합니다. 이는 Flask의 세션 쿠키를 보호하는 데 사용됩니다.
- **Click**은 명령줄 애플리케이션을 작성하기 위한 프레임워크입니다. 명령을 제공하고 사용자 지정 관리 명령을 추가할 수 있습니다.



##### src>main>utils > init_script.py 메서드 추가하여 [flask createadminuser] 명령어 생성

![image-20221208001858894](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208001858894.png)



```python
# app객체를 받아 초기화해주는 메서드
def init_script(app: Flask):
    # app -> terminal용 flask adminuser생성command를 method형태로 추가
    #     -> shell에서는 [flask 메서드명]으로 사용하기 때문에 소문자이어서 지정
    # click -> flask 명령어 사용시 옵션으로 받을 값을 지정
    @app.cli.command()
    @click.option("--username", prompt=True, help="사용할 username을 입력!")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="사용할 password를 입력!")
    def createadminuser(username, password):
        click.echo('관리자 계정을 생성합니다.')
        with DBConnectionHandler() as db:
            user = User(username=username, password=generate_password_hash(password), is_super_user=True)
            db.session.add(user)
            db.session.commit()
        click.echo(f'관리자 계정 [{username}]이 성공적으로 생성되었습니다.')
```



##### app.py의 app객체에서 init_script 적용

```python

# flask createadminuser 명령어 추가
from src.main.utils import init_script
init_script(app)

```



##### terminal에서 flask [init_script한 method명령어] 로 실행해보기

![image-20221208002642380](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208002642380.png)



```
flask createadminuser
```

![image-20221208002718300](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208002718300.png)

![image-20221208002744704](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208002744704.png)





#### pip freeze > requirements.txt

```
pip freeze > requirements.txt
```



#### venv빼고 zip으로 묶어서 linux에 올려 DB세팅해서 실행하기

1. venv만들기
2. 활성화
3. requirements.txt 설치
4. **mysqlsqlicent** 패키지 따로 설치
5. python **manage.py**로 실행하기
   1. development
   2. port 8000
6. **직접** manage.py의 app.run()의 `host="0.0.0.0"`, `port=3000` 등으로 바꾸기
7. **직접** setting.py에서 SQLALCHEMY_DATABASE_URI 바꾸기
   1. id:비번@**같은linux면127.0.0.1:3306** / db명
   2. `flask db migrate` -> `flask db upgrade`로 **연결된 db변경 초기화해서 db만들어주기**





### 배포 설정

#### deploy 폴더 생성 및 uwsgi 세팅

1. root `deploy`폴더 만들기

   ![image-20221208094154708](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208094154708.png)

   

2. deploy > `uwsgi.ini`만들기

   - 프로젝트의 루트 디렉터리 즉, flask-blog 디렉터리에 새로운 배포 폴더를 생성하고 그 안에 uwsgi.ini 파일을 생성합니다.구성은 다음과 같습니다.

     ```yml
     [uwsgi]
     master = True
     # Maximum number of threads
     processes = 10
     threads = 2
     # linux project root폴더 경로
     chdir = /www/wwwroot/flask.proae.cn
     # 실행py
     wsgi-file = %(chdir)/manage.py
     # 1) 직접 uwsgi로 실행시: 정적파일 없어서 nginx 필요없을시 
     http = 0.0.0.0:3000
     # 2) 직접 nginx로 실행시: Configure socket when using nginx forwarding
     ;socket = 127.0.0.1:3000
     # Permission configuration The current user can read and write
     chmod-socket = 660
     # Automatically clear the pid file
     vacuum = true
     # 가상환경 경로
     virtualenv = %(chdir)/venv
     # callback name
     callable = app
     # pid file storage path
     pidfile = %(chdir)/deploy/uwsgi.pid
     daemonize = %(chdir)/deploy/uwsgi.log
     logto = %(chdir)/deploy/error.log
     ```

     - 이 구성의 각 항목은 매우 명확하게 작성되었습니다. 댓글을 직접 누를 수 있습니다. **정적 파일을 전달하기 위해 nginx를 사용할 필요가 없다**면 `socket = 127.0.0.1:3000`이 항목을 삭제하거나 댓글을 달고 활성화하세요 `http = 0.0.0.0:3000`. 도메인 이름 뒤의 **포트에 주의하세요. 아니요, 서버의 보안 그룹에서 열어야 합니다!**

     - 둘의 차이점은 http 설정인데, **uwsgi가 시작되면 서버의 도메인 이름과 포트 번호를 바인딩하여 사이트에 직접 접근**할 수 있는데, 이는 nginx 웹사이트와 연동하지 않고 이미 배포되었다는 뜻입니다!

     - 그러나 **nginx는 매우 좋은 정적 파일 서버**입니다.일반적으로 nginx를 사용하여 요청을 전달하기 위해 백엔드를 모니터링합니다.따라서 **`socket = 127.0.0.1:3000`여기서 선택한 구성은 이 포트 번호에 직접 액세스할 수 없도록 변경**됩니다**.오직 nginx의 모니터링 및 전달** 만 얻을 수 있습니다!



3. root경로로 이동

   `cd /www/wwwroot/flask.proae.cn/`

4. 직접 **uwsgi 패키지를 가상환경에서 설치**

   ```python
   pip install uwsgi
   ```

5. uwsgi.ini을 설정파일로 걸어주기

   ```
   uwsgi --ini deploy/uwsgi.ini
   ```

   - uwsgi 명령을 시작합니다.`uwsgi --ini deploy/uwsgi.ini`

   - 위 명령어를 사용하면 uwsgi 서비스가 시작되고 완료되면 uwsgi.log 날짜 파일과 프로세스 번호 uwsgi.pid를 기록한 파일이 프로젝트의 배포 디렉터리에 생성됩니다. 문제가 있는 경우 uwsgi.log의 로그 파일을 확인하여 관련 오류를 해결하고 추가 디버그할 수 있습니다!

6. uwsgi를 통한 http의 **port로  접속**

![image-20221208095131800](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208095131800.png)





#### nginx 세팅

```yml
server {
    listen 80;                              # 개방포트
    server_name flask.proae.cn;            # 도메인이름 = server_name
    location / {
        uwsgi_pass 127.0.0.1:3000;          # uwsgi servie 포트
        include uwsgi_params;               # 고정배열?!
    } 
    location /admin/static {                      # static파일 경로1
        alias /www/wwwroot/flask.proae.cn/app/admin/static/;
    } 
    location /blog/static {                       # static파일 경로2
        alias /www/wwwroot/flask.proae.cn/app/blog/app/blog/static/;
    } 
}
```



##### uwsgi.ini에서 nginx사용을 위해  http주석처리 / socker 주석열기 ->  init reload -> nginx로 접속(nginx는 port없이 바인딩된 80으로만 접속 )

```yml
# 1) 직접 uwsgi로 실행시: 정적파일 없어서 nginx 필요없을시 
;http = 0.0.0.0:3000
# 2) 직접 nginx로 실행시: Configure socket when using nginx forwarding
socket = 127.0.0.1:3000
```



- 가상환경에서

  - `uwsgi --reload deploy/uwsgi.ini`

  - **접속안되면 pid를 stop -> ini 재설정**
    - `uwsgi --stop deploy/uwsgi.pid`
    - `uwsgi --init deploy/uwsgi.ini`

- port번호없이 (80)으로 도메인으로만 접속

  ![image-20221208100319332](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221208100319332.png)





#### admin 계정 생성

- flask createadminuser







#### 나는 추가적으로 업로드 경로도 지정 해줘야할 듯



