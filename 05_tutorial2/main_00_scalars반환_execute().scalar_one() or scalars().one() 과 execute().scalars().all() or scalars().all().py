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

    #### 리스트와 Scalars 반환하기
    ## .scalar_one(), one(), first(), scalars().all(), all 등을 붙이기 전,

    #### 1.4의 session.query()객체에 대하여 2.0 sesson.select() 객체는
    # .all() -> 객체List ->               [  execute().scalars().all() or scalars().all() ]
    # .one() -> 객체 단 1개 ->             [  execute().scalar_one() or scalars().one()    ]
    # .first() -> 객체 여러개 중 1개 (limit1) ↗
    # select객체.one() -> Row 타입 ->  (객체, )의 tuple
    # select객체.first() -> Row 타입 ->  (객체, )의 tuple
    # select객체.all() -> Row 타입 List->  (객체, )의 tuple List

    # session에 넣기 전의 select객체체
    print(type(select(User)))
    # <class 'sqlalchemy.sql.selectable.Select'>

    ## session.execute()와 session.scalars()
    # -> session.execute() or session.scalars()는 query관련객체를 Result객체로 생성한다.
    print(session.execute(select(User)))
    print(session.scalars(select(User)))
    # <sqlalchemy.engine.result.ChunkedIteratorResult object at 0x000002546A7DDEB8>
    # <sqlalchemy.engine.result.ScalarResult object at 0x00000185027711D0>
    print('*'*30)


    execute_one = session.execute(select(User).filter(User.id == 1))
    print(type(execute_one.one()))
    execute_one = session.execute(select(User).filter(User.id == 1))
    print(execute_one.one())
    # <class 'sqlalchemy.engine.row.Row'>
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)

    execute_one = session.execute(select(User).filter(User.id == 1))
    print(type(execute_one.scalar_one()))
    execute_one = session.execute(select(User).filter(User.id == 1))
    print(execute_one.scalar_one())
    # <class 'src.infra.tutorial2.users.User'>
    # User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234']
    print('*'*15)

    scalars_one = session.scalars(select(User).filter(User.id == 1))
    print(type(scalars_one.one()))
    scalars_one = session.scalars(select(User).filter(User.id == 1))
    print(scalars_one.one())
    print('*'*15)
    # <class 'src.infra.tutorial2.users.User'>
    # User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234']

    execute_one = session.execute(select(User).filter(User.id == 1))
    print(type(execute_one.first()))
    execute_one = session.execute(select(User).filter(User.id == 1))
    print(execute_one.first())
    # <class 'sqlalchemy.engine.row.Row'>
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],)

    # execute_all = session.execute(select(User))
    # print(execute_all.scalar().one())
    execute_all = session.execute(select(User))
    print(execute_all.all())
    # [(User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'],), (User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'],), (User[id=3, name'daisy', fullname'daisy Kim', password='1234'],), (User[id=4, name'ara', fullname'ara Cho', password='1234'],)]
    # <class 'list'>
    execute_all = session.execute(select(User))
    print(type(execute_all.all()))

    execute_all = session.execute(select(User))
    print(execute_all.scalars().all())
    execute_all = session.execute(select(User))
    print(type(execute_all.scalars().all()))
    # [User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'], User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'], User[id=3, name'daisy', fullname'daisy Kim', password='1234'], User[id=4, name'ara', fullname'ara Cho', password='1234']]
    # <class 'list'>

    scalars_all = session.scalars(select(User))
    print(scalars_all.all())
    scalars_all = session.scalars(select(User))
    print(type(scalars_all.all()))
    # [User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234'], User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'], User[id=3, name'daisy', fullname'daisy Kim', password='1234'], User[id=4, name'ara', fullname'ara Cho', password='1234']]
    # <class 'list'>


