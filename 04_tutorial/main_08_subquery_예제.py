from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### 스칼라 서브 쿼리, 상호연관 쿼리
    # (1) main 쿼리에서, join없이 타entity를 조회하고 싶을 때, select서브쿼리== 스칼라서브쿼리를 쓰면 된다.
    #     main 쿼리에서 완성될, tableA의 칼럼을 where에서 자기칼럼처럼 쓰되, join on이 없다
    #     .scalar_subquery()로 만든다.
    # -> 여기서는, User.id를 쓰되, from에 2테이블 자동쎄팅 안된다. (추후 main의 select절에 있을 User.id를 갖다쓰는 상호연관서브쿼리)
    scalar_subq = select(func.count(Address.id)) \
        .where(User.id == Address.user_id) \
        .scalar_subquery()
    # print(scalar_subq)
    # (SELECT count(address.id) AS count_1
    # FROM address, user_account
    # WHERE user_account.id = address.user_id)
    # => 엥? from에 자동세팅한다? 스칼라는 main칼럼을 이용해서 join없이 from2테이블없을텐데??
    # => 스칼라 서브 쿼리가 user_account와 address를 FROM절에서 렌더링하지만
    #    메인쿼리에 있는 user_account테이블이 있어서 스칼라 서브 쿼리에서는
    #    user_account 테이블을 렌더링하지 않습니다.
    # => my) 사용할 땐 렌더링 안된다!!!!!! 밑에서 확인해보자.

    # => 만약, scalar_subquery()가 아니라면?? 2entity를 select or where에 [join도 없이 사용]됬으니,
    #    from에 2테이블이 세팅될 것이다.(렌더링도 될 것임)
    subq = select(func.count(Address.id)) \
        .where(User.id == Address.user_id) \
        .subquery()
    # print(subq)
    # SELECT count(address.id) AS count_1
    # FROM address, user_account
    # WHERE user_account.id = address.user_id


    ## 2. 스칼라서브쿼리를 main쿼리와 사용
    # -> from에 2테이블 세팅안한다. -> main의 select절의 칼럼을 그대로 가져와 사용하기 때문에, join/2테이블from세팅없이 정보를 합친다
    stmt = select(User.name, scalar_subq)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name, (SELECT count(address.id) AS count_1
    #                            FROM address ===> 스칼라서브쿼리는 실제 사용하면, from절에 2entity세팅을 안한다.
    #                            WHERE user_account.id = address.user_id) AS anon_1
    # FROM user_account

    # ('spongebob', 1)
    # ('sandy', 2)
    # ('patrick', 0)
    # ******************************

    ## => 스칼라서브쿼리는 SQL에서는 테이블마다 별칭이 필수이며,
    ##    칼럼으로 라벨링도 해주자.
    stmt = select(User.name, scalar_subq.label('address_count'))
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name, (SELECT count(address.id) AS count_1
    #                            FROM address
#                                WHERE user_account.id = address.user_id) AS address_count
    # FROM user_account
    
    # ('spongebob', 1)
    # ('sandy', 2)
    # ('patrick', 0)
    # ******************************
    #
    # Process finished with exit code 0



