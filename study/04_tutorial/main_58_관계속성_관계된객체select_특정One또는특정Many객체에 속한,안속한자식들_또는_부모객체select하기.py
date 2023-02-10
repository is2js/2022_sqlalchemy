from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### 관계속성 관계연산자
    # 1. 특정 One갹체에 속하는/안속한 Many객체들 select하기
    # -> 2가지ㅏ 방법
    # 2. 특정 Many객체의 부모 One객체 select하기



    #### 1. 특정 One에 속하는 Many객체들 select하기
    # -> Many의 One 관계속성 vs One객체로 fk == pk 일치여부 확인
    # => One에 속하는 Many객체들을 select할 때, Many.One관계속성 == One객체 로 확인한다.

    # (1) One객체를 select한뒤, One에 속하는 Many객체들을 where(Many.One관계속성 == )비교로 select한다
    u2 = session.get(User, 2)
    stmt = (
        select(Address)
        .where(Address.user == u2)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT address.id, address.email_address, address.user_id
    # FROM address
    # WHERE :param_1 = address.user_id
    # (Address[id=2, email_address'sandy@sqlalchemy.org', user_id=2],)
    # (Address[id=3, email_address'sandy@squirrelpower.org', user_id=2],)
    # ******************************

    # (2) One에 속하지 않는 Many객체들 select by One관계속성 != One객체
    stmt = (
        select(Address)
        .where(Address.user != u2)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT address.id, address.email_address, address.user_id
    # FROM address
    # WHERE address.user_id != :user_id_1
    #     OR address.user_id IS NULL
    # => 특이하게 one의 fk를 가지지 않는 것 + fk가 IS NULL인 것들도 같이 가져온다.

    # (Address[id=1, email_address'spongebob@sqlalchemy.org', user_id=1],)
    # (Address[id=4, email_address'pear1.krabs@gmail.com', user_id=6],)
    # (Address[id=5, email_address'pearl@aol.com', user_id=6],)
    # (Address[id=8, email_address'patrick@aol.com', user_id=3],)
    # (Address[id=9, email_address'patrick@gmail.com', user_id=3],)
    # ******************************

    # (3) with_parent  => fk를 들고 있는 Many vs relationship을 가진 One의 경우,
    #                     Many에게는 relationship 속성이 없을 땐, Address.user가 불가능할 수 있다.
    #                     특정One객체는 있어서,  with_parent( u2, User.one만가진relationship속성)으로 처리할 수 있다.
    # 참고:https://stackoverflow.com/questions/67478942/sqlalchemy-relationship-selection-criteria
    #     stmt = (
    #         select(Address)
    #         .where(Address.user == u2)
    #     )
    stmt = (
        select(Address)
        .where(with_parent(u2, User.addresses))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # SELECT address.id, address.email_address, address.user_id
    # FROM address
    # WHERE :param_1 = address.user_id
    # (Address[id=2, email_address'sandy@sqlalchemy.org', user_id=2],)
    # (Address[id=3, email_address'sandy@squirrelpower.org', user_id=2],)


    #### 2. 특정 Many객체의 부모 One객체 select하기
    a1 = session.get(Address, 1)
    # -> where( one.Many관계속성.contains( many객체 ))
    stmt = (
        select(User)
        .where(User.addresses.contains(a1))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # WHERE user_account.id = :param_1
    # (User[id=1, name'spongebob', fullname='Spongebob Squarepants'],)
    # ******************************