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

    ## where절은 [select not join(단일entity select)에 한해 filter, filter_by]를 쓸 수 있다.
    # (1) filter_by+ keyword방식으로 equal만 비교
    ####    => keyword방식의 인자는, 외부에서 equals조건들을 dict로 받은 뒤, **dict로 한번에 넣어줄 수 있다.
    # (2) filter -> ENtity.칼럼 + 조건식에 모든 연산자들 사용
    #### => equals, not equals, like, in, not in, null, is not null, and /체이닝 , or, match

    #### 단일Entity의 where == filter_by
    stmt = (
        select(User)
        .filter_by(name='ara')
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name = :name_1
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)
    # ******************************

    ## filter_by의 keyword인자에  (**외부dict) 인자 넣어보기
    filters = {'name': 'jaeseong', 'password': 'test1234'}
    stmt = (
        select(User)
        .filter_by(**filters)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name = :name_1 AND users.password = :password_1
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)
    # ******************************

    #### 단일Entity의 where2 == filter
    # 클래스 단위의 [속성]과 [파이썬 표준 연산자]를 쓸 수 있다.
    stmt = (
        select(User)
        .filter(User.fullname == 'jaeseong Cho')
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # select객체는 체이닝후 새 select객체를 반환하여 -> chaining이 가능하다.
    stmt = (
        select(User)
        .filter(User.name == 'jaesoeng')
    )
    print(type(stmt))
    # <class 'sqlalchemy.sql.selectable.Select'>

    stmt = (
        select(User)
        .filter(User.name == 'jaeseong')
        .filter(User.fullname == 'jaeseong Cho')
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # <class 'sqlalchemy.sql.selectable.Select'>
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name = :name_1
    #     AND users.fullname = :fullname_1
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)

    # not equals
    stmt = (
        select(User)
        .filter(User.name != 'jaeseong')
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name != :name_1
    # (User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'],)
    # (User[id=3, name'daisy', fullname'daisy Kim', password='1234'],)
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)
    # ******************************

    ## .like() 칼럼에서 바로 나오는 메서드다
    stmt = (
        select(User)
        .filter(User.fullname.like('%ch%'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.fullname LIKE :fullname_1
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)
    # (User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'],)
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)
    # ******************************

    ## in_([])도 import없이 칼럼에서 바로 나온다.
    stmt = (
        select(User)
        .filter(User.name.in_(['jaeseong', 'ara']))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name IN (__[POSTCOMPILE_name_1])
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)
    # ******************************

    ## in_() 은 list외에 [해당 칼럼을 select한  subqeury식의 stmt]를 만들어서 넣어줘야된다.
    ## (1) ch를 name에 포함하는 것들의 name칼럼 select stmt문 -> (2) filter로 select
    ## 실제 subquery가 아니라, select객체를 넣어줘야한다.
    stmt = (
        select(User)
        .filter(User.name.in_(
            select(User.name)
            .filter(User.name.like('%ch%'))
            # .subquery() # -> erro
        ))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name IN (SELECT users.name
    #                       FROM users
    #                       WHERE users.name LIKE :name_1)
    # ******************************
    #
    # Process finished with exit code 0

    ## not in_
    # => not like 등 method 연산자의 not은 앞에 ~ 를 붙인다.
    stmt = (
        select(User)
        .filter(~User.name.in_(['jaeseong', 'ara']))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE (users.name NOT IN (__[POSTCOMPILE_name_1]))
    # (User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'],)
    # (User[id=3, name'daisy', fullname'daisy Kim', password='1234'],)
    # ******************************

    ## IS NULL, IS NOT NULL은  python None과 비교하면 된다.
    stmt = (
        select(User)
        .filter(User.name != None)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name IS NOT NULL
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)
    # (User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'],)
    # (User[id=3, name'daisy', fullname'daisy Kim', password='1234'],)
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)
    # ******************************

    ## in_, like, 외에 .conatins()/.startswidth/.endswitdh  메서드도 칼럼에서 나온다.
    ## => startswith: SQL에서는 like 'string' || '%'로 검색해준다.
    # WHERE (users.name :name_1 || LIKE '%')
    ## => endswith: SQL에서는  WHERE (users.name LIKE '%' || :name_1)
    ## => contains: SQL에서는 WHERE (users.name LIKE '%' || :name_1 || '%')
    stmt = (
        select(User)
        # .filter(User.name.startswith('j'))
        # .filter(User.name.endswith('g'))
        .filter(User.name.contains('j'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    ## and_와 or_는 따로 메서드를 import해야한다.
    ## => and_는 체이닝으로 대체할 수 있지만, or_를 생각해서 and_()를 사용해보자.
    # filter(and_( ,  ))
    stmt = (
        select(User)
        .filter(and_(User.name == 'jaeseong', User.fullname == 'jaeseong Cho'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name = :name_1
    #     AND users.fullname = :fullname_1
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)
    # ******************************

    # filter(or_( , ))
    stmt = (
        select(User)
        .filter(or_(User.name=='jaeseong', User.name =='ara'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # WHERE users.name = :name_1
    #     OR users.name = :name_2
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)
    # ******************************
