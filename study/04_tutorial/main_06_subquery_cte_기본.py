from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### 서브쿼리와 CTE
    # CTE(Common Table Expression)는 동일 쿼리 내에서 여러번 참조할 수 있게 하는 쿼리 내 임시 결과 집합입니다.
    #   이 글 (https://blog.sengwoolee.dev/m/84)에 CTE에 대해 잘 설명되어 있으니, 잘 모르시겠는 분들은 참고하시면 좋습니다.
    # -> CTE 는 개체로 저장되지 않고, 쿼리 지속 시간 동안만 존재한다는 점에서 파생 테이블과 비슷하나,
    #    CTE는 파생 테이블과 달리 자체 참조가 가능하며 동일 쿼리에서 여러 번 참조할 수 있다.
    # - 가독성 : CTE는 가독성을 높이며 쿼리 논리를 모두 하나의 큰 쿼리로 묶는 대신에 문 뒷부분에서 결합되는 여러 CTE를 만듭니다.
    #          이를 통해 필요한 데이터 청크를 가져와 최종 SELECT에서 결합할 수 있습니다.
    # - 뷰 대체 : 뷰를 CTE로 대체할 수 있습니다. 뷰를 만들 수 있는 권한이 없거나 해당 쿼리에서만 사용되어 만들지 않으려는 경우 유용합니다.
    # - 재귀 : CTE를 사용하여 자신을 호출할 수 있는 재귀 쿼리를 만듭니다. 이는 조직도와 같은 계층적 데이터에 대해 작업해야 할 때 편리합니다.
    # - 제한 사항 : 자체 참조(재귀) 또는 비 결정적 함수를 사용하여 GROUP BY 수행과 같은 SELECT 문 제한을 극복합니다.
    # - 순위 : ROW_NUMBER, RANK, NTITLE 등과 같은 순위 함수를 사용하고자 할 때 사용할 수 있습니다.

    ## 1. subquery -> ManyEntity에서, fk별 포함한 집계를 하고, 그 결과를 OneENtity에 한줄로 붙여줄 수 있다.
    ## => 보통은 select로 나오지않는 집계결과를 subquery로만든다
    ##    여기서는 user_id별, address의 갯수를 subquery로 만들어보자.
    subq = select(Address.user_id, func.count(Address.id).label('count')) \
        .group_by(Address.user_id) \
        .subquery()
    # print(subq)
    # SELECT address.user_id, count(address.id) AS count
    # FROM address
    # GROUP BY address.user_id
    ## => label을 썼으면, 다음사용 접근시는 subq.c.count의 라벨명으로 칼럼에 접근해야한다.

    #### subqeury객체는 entity가 아니라 Table객체기 때문에, .c.를 붙여서 칼럼에 접근한다!!!!!!!!!!

    ## => user_id별 | count 를, User table에 fk로서 join시켜 count정보를 붙인다.
    #### 주로 subquery는   원본테이블의 fk | 집계결과를 만들어서, 원본테이블에 left join으로 subquery상 집계결과를 붙인다.
    ##    fk라서 join시 on명시는 안해도 된다.
    stmt = select(User.name, User.fullname, subq.c.count) \
        .join_from(User, subq)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name, user_account.fullname, anon_1.count
    # FROM user_account
    # JOIN (SELECT address.user_id AS user_id, count(address.id) AS count
    #       FROM address
    #       GROUP BY address.user_id) AS anon_1 -> subquery의 집계결과를 left join으로 붙인다.
    # ON user_account.id = anon_1.user_id
    # ('spongebob', 'Spongebob Squarepants', 1)
    # ('sandy', 'Sandy Cheeks', 2)

    ## CTE : 쿼리실행session동안만 존재. SQL로 쓰면 재재귀호출이 가능짐(->ORM에선 .cte( recursive=True))
    user_id_addr_count_cte = select(Address.user_id, func.count(Address.id).label('count')) \
        .group_by(Address.user_id) \
        .cte()
    stmt = select(User.name, User.fullname, user_id_addr_count_cte.c.count) \
        .join_from(User, user_id_addr_count_cte)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # WITH anon_1 AS
    # (SELECT address.user_id AS user_id, count(address.id) AS count
    # FROM address GROUP BY address.user_id)
    ## => subquery와 달리, CTE는 with as 로 cte를 만들고나서, 테이블로 활용한다.
    #  SELECT user_account.name, user_account.fullname, anon_1.count
    # FROM user_account JOIN anon_1 ON user_account.id = anon_1.user_id
    # ('spongebob', 'Spongebob Squarepants', 1)
    # ('sandy', 'Sandy Cheeks', 2)
    # ******************************

    ## aliased(원본Entity, subq) -> subquery(Table객체로서 .c.로 컬럼접근) => 필터링된 Entity로 .c.없이 사용가능해진다.
    ## (1) sqlalclhemy.org로 끝나는 % 것을 제외 ~한 Address의 subquery
    subq = select(Address) \
        .where(~Address.email_address.like('%@sqlalchemy.org')) \
        .subquery()
    address_subq = aliased(Address, subq)
    # print(subq)
    # SELECT address.id, address.email_address, address.user_id
    # FROM address
    # WHERE address.email_address NOT LIKE :email_address_1
    # print(address_subq)
    # aliased(Address)

    stmt = select(User, address_subq) \
        .join_from(User, address_subq) \
        .order_by(User.id, address_subq.id)  # subquery의 aliased(워본Entity)는 .c.를 쓰지 않고 Entity처럼 바로 .칼럼으로 접근한다.
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname, anon_1.id AS id_1, anon_1.email_address, anon_1.user_id
    # FROM user_account
    # JOIN (SELECT address.id AS id, address.email_address AS email_address, address.user_id AS user_id
    #       FROM address
    #        WHERE address.email_address NOT LIKE :email_address_1) AS anon_1
    # ON user_account.id = anon_1.user_id ORDER BY user_account.id, anon_1.id

    # (User[id=2, name'sandy', fullname='Sandy Cheeks'], Address[id=3, email_address'sandy@squirrelpower.org', user_id=2])

    ## aliased를 원본 Address가 아닌 User로 만드는 범행을 저지르면
    ## => (1) 내부서브쿼리는 원본내용으로 작동하되
    ## => (2) select절에 올린 subquery가.. User Entity를  기준으로  내용을 뽑아온다다.

    # address_subq = aliased(User, subq)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # JOIN (SELECT address.id AS id, address.email_address AS email_address, address.user_id AS user_id
    #       FROM address
    #       WHERE address.email_address NOT LIKE :email_address_1) AS anon_1
    # ON user_account.id = anon_1.user_id ORDER BY user_account.id, user_account.id
    # (User[id=2, name'sandy', fullname='Sandy Cheeks'], User[id=2, name'sandy', fullname='Sandy Cheeks'])

    ## cte도 aliased(원본Entity, cte)로, 원본Entity처럼 작동하게 하자.
    ## => my) 특정entity에 대한 cte, subq는 aliased로 만들어 Table객체가 아닌, 원본Entity로 사용하자.
    cte = select(Address).where(~Address.email_address.like('%@squirrelpower.org')).cte()
    address_cte = aliased(Address, cte)
    stmt = select(User, address_cte) \
        .join_from(User, address_cte) \
        .order_by(User.id, address_cte.id)

    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # WITH anon_1 AS
    # (SELECT address.id AS id, address.email_address AS email_address, address.user_id AS user_id
    # FROM address
    # WHERE address.email_address NOT LIKE :email_address_1)

    #  SELECT user_account.id, user_account.name, user_account.fullname, anon_1.id AS id_1, anon_1.email_address, anon_1.user_id
    # FROM user_account
    # JOIN anon_1 ON user_account.id = anon_1.user_id ORDER BY user_account.id, anon_1.id
    # (User[id=1, name'spongebob', fullname='Spongebob Squarepants'], Address[id=1, email_address'spongebob@sqlalchemy.org', user_id=1])
    # (User[id=2, name'sandy', fullname='Sandy Cheeks'], Address[id=2, email_address'sandy@sqlalchemy.org', user_id=2])
    # ******************************

    ## select절에 칼럼이 아닌, Entity 통째로 올라간 순간, Entity객체를 반환하므로, 반복문이나 실행문에서
    ## 객체를 따로 받아도 된다.
    for user, address in session.execute(stmt):
        print(repr(user), '의 주소객체: ', end='')
        print(address)
    print('*' * 30)
    # User[id=1, name'spongebob', fullname='Spongebob Squarepants'] 의 주소객체: Address[id=1, email_address'spongebob@sqlalchemy.org', user_id=1]
    # User[id=2, name'sandy', fullname='Sandy Cheeks'] 의 주소객체: Address[id=2, email_address'sandy@sqlalchemy.org', user_id=2]