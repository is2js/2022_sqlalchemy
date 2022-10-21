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

    #### 쿼리에서 relationship 사용하기

    ## 2. 별칭(aliased)을 사용하여 조인하기
    # relationship()을 사용하여 SQL JOIN을 구성하는 경우 [PropComparator.of_type()] 사용하여
    # 조인 대상이 aliased()이 되는 사용 사례가 적합합니다.
    # 그러나 relationship()를 사용하여 [ORM Entity Aliases]에 설명된 것과 동일한 조인을 구성합니다.
    # my) aliased() -> 자기참조 or subquery Table객체.c.를  EnttityModel처럼 바꿔서 다루기 등

    ## (1) aliased로 tableB를 2번 join할 수 있다.
    ## => 똑같은 데이터(pk==fk 카다시안곱)가 2배수가 될 뿐이다.
    ## join을 2번하면, join결과(pk,fk카다시안곱)똑같은 데이터가 2배수가 된다.
    ## where를 joined tableB의 서로다른 칼럼으로 걸었다면, 1차에 2배수, 2차에 0개가 나오게 된다.
    address_alias_1 = aliased(Address)
    address_alias_2 = aliased(Address)
    stmt = (
        select(User)
        .join_from(User, address_alias_1)
        .where(address_alias_1.email_address == 'patrick@aol.com')
        .join_from(User, address_alias_2)
        .where(address_alias_1.email_address == 'patrick@gmail.com')
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # JOIN address AS address_1
    #     ON user_account.id = address_1.user_id
    # JOIN address AS address_2
    #     ON user_account.id = address_2.user_id
    # WHERE address_1.email_address = :email_address_1
    #     AND address_1.email_address = :email_address_2

    ## (2) alised를 tableA로 사용하고, 그 관계칼럼으로 join을 만들 수 있다.
    ## => select절에, tableA가 사용된다면, from절에 tableA가 자동 세팅되어 -> from tableA를 명시 안해도, join( tableA.B관계칼럼)으로 joon가능하다
    user_alias_1 = aliased(User)
    stmt = (
        select(user_alias_1.name, Address.email_address)
        .join(user_alias_1.addresses)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account_1.name
    # FROM user_account AS user_account_1
    # JOIN address
    # ON user_account_1.id = address.user_id
    # ('spongebob',) => tableB에 연결되는 데이터가 1뿐
    # ('sandy',)
    # ('sandy',)
    # ('pkrabs',) => tableB에 연결되는 데이터가 4개??
    # ('pkrabs',)
    # ('pkrabs',)
    # ('pkrabs',)
    # ('patrick',)
    # ('patrick',)