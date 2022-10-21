### SQLAlchemy 공부
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

2. 기본 폴더 구성은 [해당repo](https://github.com/is2js/2022_sqlalchemy)에서 아래 목록들을 확인한다.
   ![20221019222721](https://raw.githubusercontent.com/is3js/screenshots/main/20221019222721.png)

3. sqlite3는 하위버전(3.25.0미만)에서 window function을 제공하지 않으므로 직접 업데이트 해야합니다.
   1. (venv) sqlite 현재 버전 확인(3.25.0 이상 버전부터 window function 지원한다)
      ```python
      >>> import sqlite3
      >>> sqlite3.version # python librrary 버전에 불과함.
      '2.6.0'
      >>> sqlite3.sqlite_version # sqlite3.dll 버전임 -> 이것을 업데이트 해야한다.
      '3.21.0'
      ```
   2. venv를 만들어주는 `base interpreter`의 sqlite3.dll부터 변경
      1. 현재 venv를 만드는 local python의 버전을 확인한다.
         - 환경설정 > Project: > Python Interpreter > 점점점 Add (+) > Base Interpreter 경로 확인
            ![20221019222134](https://raw.githubusercontent.com/is3js/screenshots/main/20221019222134.png)
         - 실행 > `%appdata%` > base 경로 > `Dlls`폴더까지 들어가서 sqlite3.dll 파일 확인하기
            ![20221019222609](https://raw.githubusercontent.com/is3js/screenshots/main/20221019222609.png)
      2. [sqlite3 홈페이지](https://sqlite.org/download.html)를 방문하여 `x64`검색으로 3.25.0 이상버전을 다운받는다.
         - ctrl+f로 `x64` 검색 -> sqlite-dll-win64-x64-3390400.zip 다운로드
      3. 기존 sqlite3.dll 에 `.old`를 붙여 백업하고, `zip 속의 sqlite3.dll로 교체`한다.

   3. venv의 sqlite3.dll 변경
      - venv > Scrips 폴더에 > sqlite3.dll에 위치
         ![20221019224637](https://raw.githubusercontent.com/is3js/screenshots/main/20221019224637.png)
      - 다운 받은 것으로 교체해준다
   4. (venv) sqlite 현재 버전 바뀐 것 다시 확인
      ```python
      >>> import sqlite3
      >>> sqlite3.sqlite_version 
      '3.39.0'
      ```

#### SQLAlchemy 1.4 -> 2.0 Style 비교
- [참고](https://daco2020.tistory.com/324)
| 1.x 스타일                                                   | 2.0 스타일                                                   | 레퍼런스                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| session.query(User).get(42)                                  | session.get(User, 42)                                        | [ORM Query - get() method moves to Session](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#migration-20-get-to-session) |
| session.query(User).all()                                    | session.execute(   select(User) ).scalars().all() # or session.scalars(select(User)).all() | [ORM Query Unified with Core Select](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#migration-20-unify-select) [Session.scalars()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.Session.scalars) [Result.scalars()](https://docs.sqlalchemy.org/en/14/core/connections.html#sqlalchemy.engine.Result.scalars) |
| session.query(User).\ filter_by(name='some user').one()      | session.execute(   select(User).   filter_by(name="some user") ).scalar_one() | [ORM Query Unified with Core Select](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#migration-20-unify-select) [Result.scalar_one()](https://docs.sqlalchemy.org/en/14/core/connections.html#sqlalchemy.engine.Result.scalar_one) |
| session.query(User).\ filter_by(name='some user').first()    | session.scalars(  select(User).  filter_by(name="some user").  limit(1) ).first() | [ORM Query Unified with Core Select](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#migration-20-unify-select) [Result.first()](https://docs.sqlalchemy.org/en/14/core/connections.html#sqlalchemy.engine.Result.first) |
| session.query(User).options(   joinedload(User.addresses) ).all() | session.scalars(   select(User).   options(    joinedload(User.addresses)   ) ).unique().all() | [ORM Rows not uniquified by default](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#joinedload-not-uniqued) |
| session.query(User).\   join(Address).\   filter(Address.email == 'e@sa.us').\   all() | session.execute(   select(User).   join(Address).   where(Address.email == 'e@sa.us') ).scalars().all() | [ORM Query Unified with Core Select](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#migration-20-unify-select) [Joins](https://docs.sqlalchemy.org/en/14/orm/queryguide.html#orm-queryguide-joins) |
| session.query(User).from_statement(   text("select * from users") ).all() | session.scalars(   select(User).   from_statement(     text("select * from users")   ) ).all() | [Getting ORM Results from Textual and Core Statements](https://docs.sqlalchemy.org/en/14/orm/queryguide.html#orm-queryguide-selecting-text) |
| session.query(User).\   join(User.addresses).\   options(    contains_eager(User.addresses)   ).\   populate_existing().all() | session.execute(   select(User).   join(User.addresses).   options(contains_eager(User.addresses)).   execution_options(populate_existing=True) ).scalars().all() | [ORM Execution Options](https://docs.sqlalchemy.org/en/14/orm/queryguide.html#orm-queryguide-execution-options) [Populate Existing](https://docs.sqlalchemy.org/en/14/orm/queryguide.html#orm-queryguide-populate-existing) |
| session.query(User).\   filter(User.name == 'foo').\   update(     {"fullname": "Foo Bar"},     synchronize_session="evaluate"   ) | session.execute(   update(User).   where(User.name == 'foo').   values(fullname="Foo Bar").   execution_options(synchronize_session="evaluate") ) | [UPDATE and DELETE with arbitrary WHERE clause](https://docs.sqlalchemy.org/en/14/orm/session_basics.html#orm-expression-update-delete) |
| session.query(User).count()                                  | session.scalar(select(func.count()).select_from(User)) session.scalar(select(func.count(User.id))) | [Session.scalar()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.Session.scalar) |



#### 학습자료
1. [유튜브 1](https://www.youtube.com/watch?v=to39SFUxOpg&list=PLAgbpJQADBGKbwhOvd9DVWy-xhA1KEGm1)
2. [유튜브 2](https://www.youtube.com/watch?v=Y8GsO0Afb9c&list=PLG7hNdgnQsveTeMSjEY_1xQpkev9rP1e5)
3. [튜토리얼](https://soogoonsoogoonpythonists.github.io/sqlalchemy-for-pythonist/tutorial/1.%20%ED%8A%9C%ED%86%A0%EB%A6%AC%EC%96%BC%20%EA%B0%9C%EC%9A%94.html)