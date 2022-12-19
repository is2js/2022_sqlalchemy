from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial2 import *

if __name__ == '__main__':
    create_database()
    session = Session()

    # commit()은 모든 추가(add), 변경(update) 이력을 반영한다.
    # commit() or select()로 트랜잭션이 모두 실행되면 세션은 다시 connection pool을 반환하고 물려있던 모든 객체들을 업데이트 한다.
    # commit()을 실행한 이후 새 트랜잭션이 실행되어 [모든 행이 다시 로드된 상태] => pk 및 fk 자동 배정
    # sqlalchemy에서는 기본적으로 이전 트랜잭션에서 [새 트랜잭션으로 처음 실행될 때 모든 데이터를 새로 가져]온다.
    # 그래서 가장 최근의 상태를 바로 사용할 수 있다. 다시 불러오는 레벨을 설정하고 싶으면 세션 사용하기 문서를 확인하자.

    ## 세션 객체의 상태들
    # User 객체가 Session 외부에서 PK 없이 Session 안에 들어가고 실제로 데이터베이스에 추가될 때 까지
    # 각 “객체 상태” 를 가지고 있다. transient, pending, persistent 세가지. 이 상태들을 알고 있으면 도움이 되므로 객체 상태에 대한 설명을 잽싸게 읽어보자.

    ## 롤백하기
    # Session이 트랜잭션으로 동작하고 나서 우린 롤백 하는 것도 가능하다. 롤백해보기 위해 값을 변경해보자.
    cho = session.get(User, 1)
    cho.name = 'js'

    # 가짜 유저 생성 -> add하여 pending상태
    fake_user = User('fake', 'fake Invalid', '1234')
    session.add(fake_user)

    # select query를 날려 persistent상태로 만들어 pk배정
    # => 객체 list로 받고 싶다면,
    # (1) session.execute(  stmt ).scalars().all()   or
    # (2) session.scalars(  stmt ) .all()
    # all = session.execute(select(User).where(User.name.in_(['js', 'fake'])))\
    #     .scalars().all()
    all = session.scalars(
        select(User)
        .where(User.name.in_(['js', 'fake']))
    ).all()
    print(all, type(all))
    # [User[id=1, name'js', fullname'jaeseong Cho', password='test1234'], User[id=5, name'fake', fullname'fake Invalid', password='1234']]
    # <class 'list'>
    print('*'*30)


    #### persistent 상태(session, pk배정)의 객체를 rollback
    ## => rollback()하면, 변경전 상태로 돌아가며, add한 객체도 session에서 사라진다.
    session.rollback()

    print(cho.name == 'js')
    print(fake_user in session)
    # False
    # False

