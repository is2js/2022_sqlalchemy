from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### ORDER BY / GROUP BY  HAVING
    # / 칼럼별칭 .label()   for select집계함수의 order_by 와 having 재사용 금지
    # / TABLE별칭 .aliased() for self join? or join시 편리하게 쓰기위해?

    # ORDER BY절은 SELECT절에서 조회한 행들의 순서를 설정할 수 있습니다.
    # GROUP BY절은 그룹 함수로 조회된 행들을 특정한 컬럼을 기준으로 그룹을 만듭니다.
    # HAVING은 GROUP BY절을 통해 생성된 그룹에 대해 조건을 겁니다

    ## 1. order_by
    stmt = select(User).order_by(User.name)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # ORDER BY user_account.name
    # (User[id=3, name'patrick', fullname='Patrick Star'],)
    # (User[id=2, name'sandy', fullname='Sandy Cheeks'],)
    # (User[id=1, name'spongebob', fullname='Spongebob Squarepants'],)

    ##  2. order_by 내부  칼럼.desc() / asc()
    # stmt = select(User).order_by(User.fullname.asc())
    stmt = select(User).order_by(User.fullname.desc())
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # ORDER BY user_account.fullname ASC
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # ORDER BY user_account.fullname DESC

    ## 3. GROUP BY, Having
    # SQL에서는 집계함수를 이용해 조회 된 여러개의 행들을 하나의 행으로 합칠 수도 있습니다. 집계함수의 예로 COUNT(), SUM(), AVG()등이 있습니다.
    # SQLAlchemy에서는 func라는 네임스페이스를 이용해 SQL함수를 제공하는데, 이 func는 SQL함수의 이름이 주어지면 Function인스턴스를 생성합니다.
    # 아래의 예제에서는 user_account.id컬럼을 SQL COUNT()함수에 렌더링 하기 위해 count()함수를 호출합니다.
    # -> GROUP BY는 조회된 행들을 특정 그룹으로 나눌 때 필요한 함수입니다. 만약에 SELECT 절에서 몇 개의 컬럼을 조회 할 경우
    #    SQL에서는 직,간접적으로 이 컬럼들이 기본키(primary key)를 기준으로 GROUP BY에 종속되도록 합니다.
    # => 카운팅 등을 할 땐, 그룹대상데이터들의 table.pk(id)로 카운팅(집계)하기
    # -> HAVING 는 GROUP BY로 만들어진 그룹들에 대해 조건을 적용 할 경우 필요합니다.(그룹에 대해 조건을 걸기 때문에 WHERE절과 비슷합니다)

    stmt = select(User.name, func.count(Address.id).label('count')) \
        .join(Address) \
        .group_by(User.name) \
        .having(func.count(Address.id) > 0)

    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name, count(address.id) AS count
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id
    # GROUP BY user_account.name
    # HAVING count(address.id) > :count_1
    # ('sandy', 1)
    # ('spongebob', 1)
    # ******************************

    ## 4. 별칭을 통해 그룹화 또는 순서 정렬하기
    # 어떤 데이터 베이스 백엔드에서는 집계함수를 사용해 테이블을 조회 할 때 ORDER BY 절이나 GROUP BY절에 이미 명시된 집계함수를 다시 명시적으로 사용하지 않는 것이 중요합니다.
    # => 즉, having / order by에서 위에처럼 함수를 다시 부르지않고 별칭으로 사용하기
    # => hvaing은 literal_column('label')로 사용해야한다고 검색된다. mysql에만 된다고 한다?!
    # ex>
    # # NOT GOOD
    # SELECT id, COUNT(id) FROM user_account GROUP BY id
    # ORDER BY count(id) <- select의 집계함수를 그대로 썼다
    # # CORRECT
    # SELECT id, COUNT(id) as cnt_id FROM user_account GROUP BY id
    # ORDER BY cnt_id <- selet의 집계함수에 label(별칭)을 붙이고, 그것을 order_by에 썼다다
    # 따라서 별칭을 통해 ORDER BY 나 GROUP BY를 구현하려면 Select.order_by() 또는 Select.group_by()메서드에 인자로 사용 할 별칭을 넣어주면 됩니다.
    # 여기에 사용된 별칭이 먼저 렌더링 되는건 아니고 컬럼절에 사용된 별칭이 먼저 렌더링 됩니다. 그리고 렌더링된 별칭이 나머지 쿼리문에서 매칭되는게 없다면 에러가 발생합니다.
    ## =>  order_by() having()에   desc('label') or asc('label)을 넣어준다.

    # => User칼럼정보가 따로 필요없고 user의 id별 주소 갯수만 필요하다면,
    #    User와 join안하고 fk(user_id)별 Many테이블칼럼의 데이터 갯수를 세면 된다.
    stmt = select(Address.user_id, func.count(Address.id).label('num_addresses')) \
        .group_by(Address.user_id) \
        .order_by(Address.user_id, desc('num_addresses'))
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT address.user_id, count(address.id) AS num_addresses
    # FROM address
    # GROUP BY address.user_id
    # ORDER BY address.user_id, num_addresses DESC
    # (1, 1)
    # (2, 1)
    # ******************************
    #
    # Process finished with exit code 0

    ## 5. TABLE 별칭: aliased( Entity, name = '') 사용하기
    # 여러개의 테이블을 JOIN을 이용해 조회 할 경우 쿼리문에서 테이블 이름을 여러번 적어줘야 하는 경우가 많습니다. SQL에서는 이러한 문제를 테이블 명이나 서브 쿼리에 별칭(aliases)를 지어 반복되는 부분을 줄일 수 있습니다.
    # 한편 SQLAlchemy에서는 이러한 별칭들은 Core의 FromCaluse.alias()함수를 이용해 구현 할 수 있습니다.
    # ORM도 FromClause.alias()메서드와 비슷한 aliased()함수가 존재합니다.
    # 이 ORM aliased()는 ORM의 기능을 유지하면서 원래 매핑된 Table객체에 내부적으로 Alias객체를 생성합니다.
    user_alias_1 = aliased(User)
    user_alias_2 = aliased(User, name='user2')  # -> sql에서 AS user의 alias가 잡힌다.

    ## => self-referencing시에는 fk제약조건이 없는 상태이므로
    ## => join( , 수동조건) or join_from( , , 수동조건)으로 ON절을 명시해줘야한다.
    stmt = select(user_alias_1.name, user_alias_2) \
        .join_from(user_alias_1, user_alias_2, user_alias_1.id > user_alias_2.id)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account_1.name, user2.name AS name_1
    # FROM user_account AS user_account_1
    # JOIN user_account AS user2  ==========> aliased( , name= )에 준대로 나온다. => 이게 데이터 추출하는데 의미가 있을련지는 모르겠다
    # ON user_account_1.id > user2.id
    # ('sandy', 'spongebob')
    # ('patrick', 'spongebob')
    # ('patrick', 'sandy')
    # ******************************

    add_1 = aliased(Address)
    add_2 = aliased(Address)
    stmt = select(User) \
        .join_from(User, add_1) \
        .where(add_1.email_address == 'tingstyle1@gmail.com') \
        .join_from(User, add_2) \
        .where(add_2.email_address == 'daisy0702@gmail.com') \
        # (User[id=1, name'spongebob', fullname='Spongebob Squarepants'],)
        # X
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # JOIN address AS address_1 ON user_account.id = address_1.user_id
    # JOIN address AS address_2 ON user_account.id = address_2.user_id
    # WHERE address_1.email_address = :email_address_1 AND address_2.email_address = :email_address_2
    ## => my) join where join where을 순차적으로 걸어도,
    ##        join들 먼저 다하고 -> where는 and로 연결된다.
    
