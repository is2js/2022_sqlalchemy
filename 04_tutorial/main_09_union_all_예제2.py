from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### UNION, UNION ALL 연산자들
    # 함수들의 반환 값은 CompoundSelect인데 Select와 비슷하게 쓰일 수 있는 객체이지만 더 적은 메서드를 갖고 있습니다.
    # union_all()의 반환값 CompoundSelect객체는 Connection.execute()로 실행될 수 있습니다

    ## 1. 각각의 stmt를 만들어놓고, union_all(stmt1, stmt2) 형식으로 구현한다

    stmt1 = select(User).where(User.name == 'sandy')
    stmt2 = select(User).where(User.name == 'patrick')
    u = union_all(stmt1, stmt2)  # u는 CompoundSelect 객체입니다.
    print(u)
    for it in session.execute(u):
        print(it)
    print('*' * 30)

    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # WHERE user_account.name = :name_1
    # UNION ALL
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # WHERE user_account.name = :name_2

    # (2, 'sandy', 'Sandy Cheeks')
    # (3, 'patrick', 'Patrick Star')

    ## 2. UNION_ALL 한 queryset를 subquery로 만들어야만, Table객체가 되어, 다른table과 함께 사용할 수 있따
    u_subq = u.subquery()
    # Address <- UNION_ALL 한것을 join하여,  원하는 Address정보 + 원하는 User들정보만 뽑기
    stmt = (
        select(u_subq.c.name, Address)
        .join_from(Address, u_subq)
        .order_by(u_subq.c.name, Address.email_address)
    )

    # SELECT anon_1.name, address.id, address.email_address, address.user_id
    # FROM address
    # JOIN (SELECT user_account.id AS id, user_account.name AS name, user_account.fullname AS fullname
    #       FROM user_account
    #       WHERE user_account.name = :name_1 UNION ALL SELECT user_account.id AS id, user_account.name AS name, user_account.fullname AS fullname
    #       FROM user_account
    #       WHERE user_account.name = :name_2) AS anon_1
    # ON anon_1.id = address.user_id
    # ORDER BY anon_1.name, address.email_address

    # ('sandy', Address[id=2, email_address'sandy@sqlalchemy.org', user_id=2])
    # ('sandy', Address[id=3, email_address'sandy@squirrelpower.org', user_id=2])

    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
