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

    #### EXISTS로 만드는 where()용 상호연관 서브쿼리들
    # (1) where exists () 는 where절에 있음에도 상호연관서브쿼리로 메인쿼리의 메인Entity칼럼을 사용해서 구성하며
    # -> () subquery내용은 where로 조건에 맞는 selet 1 or select func.count()를 건다
    # (2) 조건을 건 subquery를 구성하고, .exists()로 Exists객체를 만든 뒤 -> 메인쿼리이의 where에 걸면 된다.

    ## 1. user(fk from main쿼리)별 address(subquery) 갯수가 2개이상인 user.name
    ## (1) main쿼리에 select에 User가 있다고 가정하고, subquery를 exists를 건다
    ##    -> where에 main쿼리의 MainEntity.id == 로 유사 join을 건다
    subq = (
        select(func.count(Address.id).label('count'))
        .where(User.id == Address.user_id)  # User.id -> Main쿼리의 MainEntity의 id를 써서 wehre로 join을 건다
        .group_by(Address.user_id)
        .having(literal_column('count') > 1)
    ).exists()
    # print(subq)
    # EXISTS (SELECT count(address.id) AS count
    #         FROM address, user_account
    #         WHERE user_account.id = address.user_id GROUP BY address.user_id
    #         HAVING count > :count_1)

    ## (2) subquery로 작성한 exists를 where에 넣으면 된다.
    stmt = select(User.name).where(subq)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name
    # FROM user_account
    # WHERE EXISTS (SELECT count(address.id) AS count
    #               FROM address
    #               WHERE user_account.id = address.user_id GROUP BY address.user_id
    #               HAVING count > :count_1)
    # ('sandy',)
    # ******************************

    ## 2. exists_subquery는 ~의 존재하지 않는 부정의 경우가 더 많이 사용된다.
    ## - 이메일 주소가 없는 유저네임을 선택하는 쿼리문입니다.
    ## => where로만 select해서 데이터가 존재하는 것만 만든다.
    ## => 존재X에 대해, 존재O는 count를 할 필요없다 select만 날리면 끝이다.
    ## (1) 상호연관 where main칼럼을 이용해, exists()로 서브쿼리를 만든다.
    subq = (
        select(Address.id)
        .where(User.id == Address.user_id)
    ).exists()

    stmt = (
        select(User.name)
        .where(~ subq)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name
    # FROM user_account
    # WHERE NOT (EXISTS (SELECT address.id
    #                    FROM address
    #                    WHERE user_account.id = address.user_id))
    # ('patrick',)
    # ******************************