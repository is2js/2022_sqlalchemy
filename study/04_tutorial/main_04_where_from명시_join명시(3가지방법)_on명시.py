from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### WHERE
    stmt = select(User).where(User.name == 'sandy')
    print('*' * 30)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    ## 1. select절에 여러테이블이 아닌, where절에 다른 테이블을 넣어도 from에 세팅되어 카다디안 곱에서, join된다.
    ## (1) where을 체이닝
    stmt = select(Address.email_address) \
        .where(Address.user_id == User.id) \
        .where(User.name == 'spongebob')

    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT address.email_address
    # FROM address, user_account
    # WHERE address.user_id = user_account.id AND user_account.name = :name_1
    # ('tingstyle1@gmail.com',)

    ## (2) where() 1개에 콤마로 여러조건을 and로 추가
    stmt = select(Address.email_address) \
        .where(Address.user_id == User.id, User.name == 'spongebob')

    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT address.email_address
    # FROM address, user_account
    # WHERE address.user_id = user_account.id AND user_account.name = :name_1
    # ('tingstyle1@gmail.com',)
    # ******************************

    ## (3) where안에 콤마가 아닌 and_ + or_ 로 명시
    stmt = select(Address.email_address) \
        .where(and_(Address.user_id == User.id, User.name == 'spongebob'))

    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT address.email_address
    # FROM address, user_account
    # WHERE address.user_id = user_account.id AND user_account.name = :name_1
    # ('tingstyle1@gmail.com',)
    # ******************************

    ## 2. 1개 테이블의 WHERE -> where 대신 keywords방식의 filter_by를 쓸 수 있음.
    stmt = select(User) \
        .filter_by(name='sandy', fullname='Sandy Cheeks')

    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # WHERE user_account.name = :name_1 AND user_account.fullname = :fullname_1
    # (User[id=2, name'sandy', fullname='Sandy Cheeks'],)
    # ******************************
    #
    # Process finished with exit code 0

    ####  FROM과 JOIN 동시 명시
    # cf)  join_from( tableA, tableB) / join( tableB ) / select_from( tableA ) .join( tableB )에서
    # - 지금 껏: FROM절은 따로 명시하지 않아도
    #   [1] select()메서드의 인자에 넣은 2개이상 테이블의 컬럼들 or
    #   [2] where()절에 추가한 테이블의 컬럼에 의해
    #   FROM에 자동세팅 -> [[[[카다시안 곱]]]] -> where 조건에 의한 join이 됬었다.
    # - 만약 select()의 위치 인자로 서로 다른 두 개의 테이블을 참조하는 컬럼을,(컴마)로 구분지어 넣을 수도 있습니다
    stmt = select(User.name, Address.email_address)
    # => where안준 자동FROM세팅은 카다시안 곱으로서 a x b의 경우의 수를 나타낼 뿐이다.
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.name, address.email_address
    # FROM user_account, address
    # ('spongebob', 'tingstyle1@gmail.com')
    # ('spongebob', 'daisy0702@gmail.com')
    # ('sandy', 'tingstyle1@gmail.com')
    # ('sandy', 'daisy0702@gmail.com')
    # ('patrick', 'tingstyle1@gmail.com')
    # ('patrick', 'daisy0702@gmail.com')
    # ******************************

    # (1) join_from( tableA, tableB)
    # => 카다시안곱 상황에서 where조건으로 join시키는 것 대신, [암시적으로 알아서 pk,fk를 찾아 join]시켜준다.
    # => 왼쪽테이블을 FROM에, 오른쪽테이블을 JOIN에 걸어준다.
    stmt = select(User.name, Address.email_address).join_from(User, Address)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.name, address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id

    # ('spongebob', 'tingstyle1@gmail.com')
    # ('sandy', 'daisy0702@gmail.com')
    # ******************************

    # (2) join( tableB ):
    # -> 암시적으로 select절에 쓰인 테이블 중 1개는 from에,
    # -> join( )에 명시한 table은 join절에 들어가게 하며
    # -> pk, fk는 알아서 걸어준다.
    # =>[ join명시테이블을, join절에 -> 나머지테이블을 from절에 ]
    stmt = select(User.name, Address.email_address).join(Address)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.name, address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id
    # ('spongebob', 'tingstyle1@gmail.com')
    # ('sandy', 'daisy0702@gmail.com')
    # ******************************

    # select절에 명시된 것 중 다른 테이블을 join에 걸면, 그것이 join절에 나머지는 from절에 들어간다
    stmt = select(User.name, Address.email_address).join(User)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.name, address.email_address
    # FROM address
    # JOIN user_account
    # ON user_account.id = address.user_id
    # ('spongebob', 'tingstyle1@gmail.com')
    # ('sandy', 'daisy0702@gmail.com')
    # ******************************

    ## (3) select() select_from( from 절테이블 ) .join( join절 테이블)
    ## => from도 명시적으로 걸어줄 수 있다.
    ## => 3가지 경우 모두 pk, fk는 알아서 암시적으로 연결된다.
    stmt = select(User.name, Address.email_address) \
        .select_from(User) \
        .join(Address)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.name, address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id
    # ('spongebob', 'tingstyle1@gmail.com')
    # ('sandy', 'daisy0702@gmail.com')
    # ******************************

    ## 2. select_from()을 할 수 없이 써야하는 경우
    # => select절에 테이블Entity가 안올라가 FROM절이 자동세팅 안되는 경우 ex> func.count('*')
    stmt = select(func.count('*')).select_from(User)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT count(:count_2) AS count_1
    # FROM user_account
    # (3,)

    #### 3. On절 세팅하기 -> join()의 2번째 인자에 조건식으로 명시
    # -> 지금가지는 from자동세팅, on자동세팅 되는 경우가 많았다.
    # => ForeignKeyConstraint, 즉 외부키 제약을 갖고 있어서 자동으로 세팅이 된 것입니다.
    # => 만약에 Join의 대상인 두 개의 테이블에서 이러한 제약 key가 없을 경우 ON절을 직접 지정해야 합니다.

    #    이러한 기능은 Select.join()나 Select.join_from()메서드에 파라미터 전달을 통해 명시적으로 ON절을 세팅할 수 있습니다.
    ## => join_from( tableA, tableB) / join( tableB ) / select_from( tableA ) .join( tableB )에서
    ##    join()메서드의 2번재 인자로 tableA.pk == tableB.fk 의 조건식을 넘겨주면 자동으로 ON으로 세팅된다.

    stmt = select(User.name, Address.email_address) \
        .select_from(User) \
        .join(Address, User.id == Address.user_id)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.name, address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id
    # ('spongebob', 'tingstyle1@gmail.com')
    # ('sandy', 'daisy0702@gmail.com')
    # ******************************



    #### 4. outer, full join -> isouter / full = True 키워드를 주면 된다.
    stmt = select(User, Address).join(Address, isouter=True)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ******************************
    # SELECT user_account.id, user_account.name, user_account.fullname, address.id AS id_1, address.email_address, address.user_id
    # FROM user_account
    # LEFT OUTER JOIN address
    # ON user_account.id = address.user_id
    # (User[id=1, name'spongebob', fullname='Spongebob Squarepants'], Address[id=1, email_address'tingstyle1@gmail.com', user_id=1])
    # (User[id=2, name'sandy', fullname='Sandy Cheeks'], Address[id=2, email_address'daisy0702@gmail.com', user_id=2])
    # (User[id=3, name'patrick', fullname='Patrick Star'], None)
    # ******************************

    # stmt = select(User, Address).join(Address, full=True)
    # # sqlite3.OperationalError: RIGHT and FULL OUTER JOINs are not currently supported
    # print('*' * 30)
    # print(stmt)
    # for it in session.execute(stmt):
    #     print(it)
    # print('*' * 30)
