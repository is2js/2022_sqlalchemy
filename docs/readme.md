### 2022 SQLAlchemy & regex
#### 기본 폴더 구성
- 폴더 구성 방법은 [제 블로그 포스팅](https://blog.chojaeseong.com/python/cleanpython/project/infra/orm/database/entities/models/2022/10/14/cp03_sqlalchemy%EB%A5%BC-%ED%86%B5%ED%95%9C-infra(DB)-%EC%82%AC%EC%9A%A9-%EC%84%B8%ED%8C%85.html)을 확인해주세요.
  - 기본 폴더 구조 
  ![image-20221024183835868](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221024183835868.png)

#### sqlite window function 대응   
 - 제 [블로그 포스팅](https://blog.chojaeseong.com/python/database/sqlalchemy/sqlite/windowfunction/sqlite3.dll/2022/10/15/window_sqlite_version_upgrade.html)을 참고해주세요

#### SQLAlchemy 1.4 -> 2.0 Style 비교
- [출저](https://daco2020.tistory.com/324)

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



#### SQLALCHEMY 학습 출저
1. [유튜브 1: Programador Lhama](https://www.youtube.com/watch?v=to39SFUxOpg&list=PLAgbpJQADBGKbwhOvd9DVWy-xhA1KEGm1)
2. [유튜브 2: MADTeacher](https://www.youtube.com/watch?v=Y8GsO0Afb9c&list=PLG7hNdgnQsveTeMSjEY_1xQpkev9rP1e5)
3. [튜토리얼1: 파이썬 개발자를 위한 SQLAlchemy](https://soogoonsoogoonpythonists.github.io/sqlalchemy-for-pythonist/tutorial/1.%20%ED%8A%9C%ED%86%A0%EB%A6%AC%EC%96%BC%20%EA%B0%9C%EC%9A%94.html)
3. [튜토리얼2: 김용균님 블로그](https://edykim.com/ko/post/getting-started-with-sqlalchemy-part-1/)


### Regex
- 정규식 패턴 검사 문서: https://docs.python.org/3/howto/regex.html
- 정규식 의미 문서: https://docs.python.org/3/library/re.html

#### 학습 출저
1. [유튜브 1: AppliedAiCourse](https://www.youtube.com/watch?v=z0QUnFfaJXo)
2. [유튜브 2: PyMoondra](https://www.youtube.com/watch?v=yqwYTSNJFLg)
