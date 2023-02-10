from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### EXISTS has() , and()
    # - EXISTS 서브쿼리들 섹션에서는 SQL EXISTS 키워드를 스칼라 서브 쿼리, 상호연관 쿼리 섹션과 함께 소개했습니다.
    # - relationship()은 관계 측면에서 공통적으로 서브쿼리를 생성하는데 사용할 수 있는 일부 도움을 제공합니다.

    # (1) exists()로 만드는 서브쿼리 복습
    # my) exists subquery는 where절에 옴에도, 상호연관쿼리로서,
    #     join없이 where에서 메인의 칼럼(MainEntity)을 사용했었고
    #     SQL문에서도 join이 안타난다.
    #     where에 main쿼리 table.pf == tableB.fk로 연결해서join처럼 만든 뒤
    #     => .exist()를 붙혀서, subquery로 만들어서, 메인쿼리의 where절에 줬다.
    #        주로 subq를 만들고,  메인where정레는 .where( ~ subq) 로 부정조건으로 사용햇었다.
    #     subq = (
    #         select(Address.id)
    #         .where(User.id == Address.user_id)
    #     ).exists()
    #
    #     stmt = (
    #         select(User.name)
    #         .where(~ subq)
    #     )


    #### one(User) to many(Address)에서 one where절의 many에 대한 exists subquery 빠르게 구현하기

    ## 1. (JOIN용 join() 안이 아닌) Main쿼리의 Where()안에 .B관계속성.any( ) or (tableB.일반속성 조건문 )으로 만드는
    ##    Exist용 subquery자동완성
    # User.addresses와 같은 1:N (one-to-many) 관계의 경우 PropComparator.any()를 사용하여
    # user_account테이블과 다시 연결되는 주소 테이블에 서브쿼리를 생성할 수 있습니다.
    # 이 메서드는 하위 쿼리와 일치하는 행을 제한하는 선택적 WHERE 기준을 허용합니다

    #### where절에 .B관계속성

    # (1) 원래 join이 아닌, where절에 B관계속성만 갖다대면, JOIN + ON 유추 대신,
    #    => from에 2테이블 + where에 PK==FK를 유추해준다.
    #    => 여러 테이블(카다시안 곱)을 통한 join이 완성됨.
    stmt = (
        select(User.fullname)
        .where(User.addresses)
    )
    print(stmt)
    print('*'*30)
    # SELECT user_account.fullname
    # FROM user_account, address
    # WHERE user_account.id = address.user_id

    # (2) where절에 B관계속성.any()를 주면, from 2테이블 + where에 pk==fk 유추는 없어지고
    #     => from tableA 세팅 + where EXIST ( ) 가 세팅된다.
    #### my) where절에 .B관계속성.any()는 tableB의 exists() subquery를 자동으로 만들어준다.
    stmt = (
        select(User.fullname)
        .where(User.addresses.any())
    )
    print(stmt)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # WHERE EXISTS (SELECT 1
    #               FROM address
    #               WHERE user_account.id = address.user_id)

    # (3) where절 .B관계속성.any()를 통한 tableB exists() subquery에 any()내부에는 tableB로 추가조건을 걸 수 있다.
    #    -> exists subquery는 상호연관쿼리라 메인에 있던 tableA의 pk속성 써서  join대신 연결해주니
    #       tableB.속성으로는, 자유롭게 조건을 추가할 수 있다.
    stmt = (
        select(User.fullname)
        # .where(User.addresses.any()) # => B관계속성.any()로 mainA.pk칼럼을 where에 사용한 B의 exists subquery()가 만들어진다.
        .where(User.addresses.any(Address.email_address == 'pear1.krabs@gmail.com')) # => B에 대한 exists subquery에 B속성으로 조건을 추가한다.
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # WHERE EXISTS (SELECT 1
    #               FROM address
    #               WHERE user_account.id = address.user_id
    #                   AND address.email_address = :email_address_1)
    # ('Pearl Krabs',)
    # ******************************


    #### (4) main(tablaA)에대해, 관련된 tableB 정보가 없는 tableA 데이터를 구할땐 any() + 부정어(~)로 빠르게 구한다
    stmt = (
        select(User.fullname)
        .where(~User.addresses.any()) # => pf==fk 연결된 Address 테이블 Exist가 없는 것
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # WHERE NOT (EXISTS (SELECT 1
    #                    FROM address
    #                    WHERE user_account.id = address.user_id))
    # ('Squidward Tentacles',)
    # ('Eugene H. Krabs',)
    # ('Pearl Krabs',)
    # ******************************


    #### Many(Address) to One(User) Many where절의 one에 대한 exists subquery 빠르게 구현하기
    #### => 이 때는, .B(One)관계속성.has()로 구현하면 된다.

    # PropComparator.has() 메서드는 PropComparator.any()와 비슷한 방식으로 작동하지만, N:1 (Many-to-one) 관계에 사용됩니다.
    # - 예시로 "pkrabs"에 속하는 모든 Address 객체를 찾으려는 경우 이와 같습니다.
    #         => 연결테이블의 속성이 "pkrabs"인 모든 Address객체
    #         => select Address하는데,   [연결정보]가 .name이 pkrabs [인]  모든 데이터=> [EXISTS subquery]
    #            "연결정보가 ~인, 존재하는, 존재하지 않는" => EXISTS Subquery 생각 => .B관계속성.any() 나. .B관계속성.has()생각
    #            2테이블이므로, join대신 subquery로 해결한다
    #            ~에 속하는,  ~인 데이터 == where exists select 1 관계테이블조건
    #            연결정보가 있는, 거기서 데이터가 ~인 [연결정보를 가지고 있는] 모든 객체 -> join or subquery로 연결된 모든 데이터 SELECT 1을 EXISTS로..
    #
    #   my)  ~ 에 속하는, ~인, ~로 존재하는, ~가 아닌 => subquery내 해당데이터 select 1 후 -> EXISTS()로 씌워서 그런 상태인 데이터 다 가져오기
    stmt = (
        select(Address)
        # .where() # => 여기서 관계테이블에 대한 exists 조건(연결정보가 ~인, 연결정보가 ~로 존재하는, 연결정보가 ~ 에 속하는)이 필요하다? => 관계속성으로 만들어본다.
        # .where(User.addresses.has()) # => Many to One이면, any() 대신 has()로 exists subquery를 만든다.
        .where(Address.user.has(User.name == 'pkrabs')) # "연결정보가 ~로 존재하는" + "name이 xxx로" => has()이후 추가조건을 내부에 건다
    )
    #### has()에 any()를 쓴다면
    # -> sqlalchemy.exc.InvalidRequestError: 'has()' not implemented for collections.  Use any().
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT address.id, address.email_address, address.user_id
    # FROM address
    # WHERE EXISTS (SELECT 1
    #               FROM user_account
    #               WHERE user_account.id = address.user_id
    #                   AND user_account.name = :name_1)

    # (Address[id=4, email_address'pear1.krabs@gmail.com', user_id=6],)
    # (Address[id=5, email_address'pearl@aol.com', user_id=6],)
    # ******************************
