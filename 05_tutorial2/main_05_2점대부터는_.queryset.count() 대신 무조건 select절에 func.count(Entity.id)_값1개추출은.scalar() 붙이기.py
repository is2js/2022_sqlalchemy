from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial2 import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### 1.4 query .count() -> select객체에서는 무조건 select절에서 count

    ## (1) 집계 entity를 기준으로 .id칼럼을 카운팅한다.
    stmt = (
        select(func.count(User.id))
        .filter(User.name.like('j%'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # SELECT count(users.id) AS count_1
    # FROM users
    # WHERE users.name LIKE :name_1
    # (2,)
    # ******************************


    ## (2) select절에 func.count()만 하면 count(*)와 동일하다.
    # -> 이 때는 select_from으로 from을 명시해준다.
    stmt = (
        select(func.count())
        .select_from(User)
        .filter(User.name.like('j%'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT count(*) AS count_1
    # FROM users
    # WHERE users.name LIKE :name_1
    # (2,)
    # ******************************

    ## from에 명시 안해주려면, select절에 entity가 들어가야한다.
    ## => (1) 처럼 fun.count(User.id)의 id를 기입해서 count하면 된다.


    ## (4) 숫자만 추출하고 싶다면, .scalar()로 값을 가져오면 된다.
    stmt = (
        select(func.count())
        .select_from(User)
        .filter(User.name.like('j%'))
    )
    print(stmt)
    print(session.execute(stmt).scalar())
    print('*' * 30)
    # SELECT count(*) AS count_1
    # FROM users
    # WHERE users.name LIKE :name_1
    # 2
    # ******************************




