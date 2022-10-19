from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### SQL 함수 다뤄보기
    ## func.   count/lower/now/row_number() ..../max/concat/avg/sum

    ## 1. .count()
    # func 객체는 새로운 Function 객체를 생성하기 위한 팩토리 역할을 합니다.
    # select()와 같은 구문을 사용 할때는 인자 값으로 func객체로 생성된 SQL함수를 받을 수 있습니다.
    # => my) func.집계함수()를 변수로 받아놓고 select()절/having()절에 입력할 수 있다.

    cnt = func.count() # count에 칼럼을 넣지 않으면, `*`를 의미한다.
    # select절에 Entity가 들어가지 않으면, .select_from()으로 entity를 FROM절을 세팅해줘야한다.
    stmt_pg = (
        select(cnt)
        .select_from(User)
    )
    print(stmt_pg)
    for it in session.execute(stmt_pg):
        print(it)
    print('*' * 30)
    # SELECT count(*) AS count_1
    # FROM user_account
    # (3,)

    ## 2. lower() : 문자열 함수로 문자열을 소문자로 바꿔줍니다.
    stmt_pg = (
        select(func.lower('A String With Much UPPERCASE'))
    )
    print(stmt_pg)
    for it in session.execute(stmt_pg):
        print(it)
    print('*' * 30)
    # SELECT lower(:lower_2) AS lower_1
    # ('a string with much uppercase',)
    # ******************************

    ## 3. .now() : 현재 시간과 날짜를 반환해주는 함수입니다.
    # => 이 함수는 굉장히 흔하게 사용되는 함수이기에 SQLAlchemy는 서로 다른 백엔드에서 손쉽게 렌더링 할 수 있도록 도와줍니다.
    stmt_pg = (
        select(func.now())
    )
    print(stmt_pg)
    for it in session.execute(stmt_pg):
        print(it)
    print('*' * 30)
    # SELECT now() AS now_1
    # (datetime.datetime(2022, 10, 18, 15, 54, 32),)
    # ******************************

    ## 4. select().compile(dialect=xxx.dialect())
    # SQLAlchemy에서는 SQL에서 일반적으로 자주 쓰이는 count, now, max , concat같은 SQL 함수를
    ##  => 백엔드별로 적절한 데이터 타입을 제공합니다.
    stmt_pg = (
        select(func.now())
        .compile(dialect=postgresql.dialect())
    )
    stmt_mysql = (
        select(func.now())
        .compile(dialect=mysql.dialect())
    )
    stmt_oracle = (
        select(func.now())
        .compile(dialect=oracle.dialect())
    )
    print(stmt_pg)
    # SELECT now() AS now_1
    print(stmt_mysql)
    # SELECT now() AS now_1
    print(stmt_oracle)
    # SELECT CURRENT_TIMESTAMP AS now_1 FROM DUAL

