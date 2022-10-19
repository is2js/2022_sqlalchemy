### SQLAlchemy 연습
1. `.env`를 아래와 같이 생성하고 시작해주세요
   ```
   # database-sqlite===
   DB_CONNECTION=sqlite
   # DB_NAME=xxxx(db생략)
   # DB_NAME=memory
   DB_NAME=tutorial

   # database===
   # DB_CONNECTION=mysql+pymysql
   # DB_NAME=cinema
   # DB_USER=root
   # DB_PASSWORD=564123
   # DB_SERVER= 
   # DB_PORT=

   # jwt
   # TOKEN_KEY=
   # EXP_TIME_MIN=
   # REFRESH_TIME_MIN
   ```

2. 기본 폴더 구성은 해당repo를 확인한다.
   ![20221019222721](https://raw.githubusercontent.com/is3js/screenshots/main/20221019222721.png)

2. sqlite3는 하위버전(3.25.0미만)에서 window function을 제공하지 않으므로 직접 업데이트 해야합니다.
   1. (venv) sqlite 현재 버전 확인(3.25.0부터 지원한다)
      ```python
      >>> import sqlite3
      >>> sqlite3.version # python librrary 버전에 불과함.
      '2.6.0'
      >>> sqlite3.sqlite_version # sqlite3.dll 버전임 -> 이것을 업데이트 해야한다.
      '3.21.0'
      ```
   2. venv를 만들어주는 환경의 sqlite3.dll부터 변경
      1. 현재 venv를 만드는 local python의 버전을 확인한다.
         - 환경설정 > Project: > Python Interpreter > 점점점 Add (+) > Base Interpreter 경로 확인
            ![20221019222134](https://raw.githubusercontent.com/is3js/screenshots/main/20221019222134.png)
         - 실행 > `%appdata%` > base 경로 > `Dlls`폴더까지 들어가서 sqlite3.dll 확인하기
            ![20221019222609](https://raw.githubusercontent.com/is3js/screenshots/main/20221019222609.png)
