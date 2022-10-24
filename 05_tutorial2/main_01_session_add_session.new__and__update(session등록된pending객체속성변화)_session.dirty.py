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

    # engine은 선언만 해서 바로 연결되는게 아니라 첫 실행이 될 때 연결이 됨.

    # Declarative system으로 만들어진 이 EntityModel클래스들은 table metadata를 가지게 되는데
    # -> 이게 사용자정의 EntityModel클래스들 <-> DB 테이블을 연결해주는 구실
    # 각 테이블별 metadata와 mapper 클래스
    print(User.__table__)  # users
    print(User.__mapper__)  # mapped class User->users
    print('*' * 30)

    #### 최소 테이블 묘사 vs. 완전 상세돋는 묘사
    # sqlite나 postgresql은 테이블을 생성할 때 varchar 컬럼을 길이를 설정하지 않아도 별 문제 없이 데이터타입으로 쓸 수 있지만
    # 그 외 데이터베이스(mysql)에서는 허용되지 않는다. 그러므로 컬럼 길이가 필요한 데이터베이스의 경우 length가 필요하다.
    # -> Column(String(50))
    # Integer, Numeric 같은 경우에도 위와 동일하게 쓸 수 있다.
    # 덧붙여 Firebird나 오라클에서는 PK를 생성할 때 sequence가 필요한데 Sequence 생성자를 써야 한다.
    # -> from sqlalchemy import Sequence
    # -> Column(Integer, Sequence('user_id_seq'), primary_key=True)

    user_cho = User('jaeseong', 'jaeseong Cho', '1234')  # transient - no pk / not in  session
    print(user_cho)
    print(user_cho in session)
    # User[id=None, name'Cho', fullname'JaeSeongCho', password='1234']
    # False

    ## pending - no pk / in session(map)
    # 만약 디비에 쿼리를 하면 모든 pending 된 정보는 flush되고 접근 가능한 상태가 된다.
    session.add(user_cho)
    # User[id=None, name'Cho', fullname'JaeSeongCho', password='1234']
    print(user_cho)
    print(user_cho in session)
    # User[id=None, name'Cho', fullname'JaeSeongCho', password='1234']
    # True

    ## persitent - pk / in session / not db save
    # pending객체가 commit() or select쿼리를 db에 접근하는 순간 반영됨
    # db에 select쿼리를 execute로 날리는 순간 pending -> flush -> persistent
    stmt = (
        select(User)
        .where(User.name == 'jaeseong')
    )
    cho = session.execute(stmt).scalar_one()
    print(user_cho)
    print(user_cho in session)
    # User[id=1, name'jaeseong', fullname'jaeseong Cho', password='1234']
    # True

    ## session은 맵구조의 객체라 반환하는 값이 우리가 기존에 집어넣은 인스턴스랑 동일하다.
    #  identity map이라서 session에서 하는 모든 처리들이 실제 데이터셋과 함께 동작한다.
    #  [Session에서 PK]-> .get(Entity, pk)를 가지면 [같은 PK 파이썬 객체를 반환]하여 동일객체로 유지
    print(user_cho is cho)
    # True


    ## session.add_all( list )
    #  transient 생성과 동시에 pending -> session
    session.add_all([
        User('jaekyung', 'jaekyung Cho', '1234'),
        User('daisy', 'daisy Kim', '1234'),
        User('ara', 'ara Cho', '1234'),
    ])

    ## cf) session.execute( stmt )로 사용시
    # (1) .scalar_one()으로 뽑으면, Entity객체
    # (2) .first()로 뽑으면, tuple 중 0번째가 차있는 Row객체다 -> [0]로 뽑아써야하는 번거로움
    # cho1 = session.execute(stmt).scalar_one()
    # cho2 = session.execute(stmt).first()
    # print(type(cho1), type(cho2))
    # print(cho1, cho2)
    # print(type(cho2[0]))
    # <class 'src.infra.tutorial2.users.User'>
    # <class 'sqlalchemy.engine.row.Row'>
    # User[id=1, name'jaeseong', fullname'jaeseong Cho', password='1234']
    # (User[id=1, name'jaeseong', fullname'jaeseong Cho', password='1234'],)
    # <class 'src.infra.tutorial2.users.User'>

    #### insert, update 여부는 session(map)에서 확인할 수 있다.

    ## session 속에 들어간 EntityModel객체에 한해서,
    # -> 객체 속성변화로 업데이트를 할 수 있다.
    #    (1) session에 add된 객체 get(or select)-> 속성변화 (2) update문
    # => Session은 계속 연결되어있는 객체를 계속 주시하고 있다. 위처럼 수정하면 session은 이미 알고있다.
    cho.password = "test1234"

    ##  [속성변화 -> db 변동 예정]확인은 session.dirty 맵에 들가 있는지 확인하면 된다.
    print(cho in session.dirty)
    print(session.dirty)
    # True
    # IdentitySet([User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234']])

    ## 새로 추가된 애들은 session.new 에서 확인하면 된다.
    print(session.new)
    # IdentitySet(
    #     [User[id=None, name'jaekyung', fullname'jaekyung Cho', password='1234'],
    #     User[id=None, name'daisy', fullname'daisy Kim', password='1234'],
    #     User[id=None, name'ara', fullname'ara Cho', password='1234']]
    # )


    #### by commit -> session속 pending( add, update) -> persistent 상태의 객체들을 db에 반영
    # Session에 pending된 애들을 실행시키려면,
    # commit()은 모든 변경, 추가 이력을 반영한다. 이 트랜잭션이 모두 실행되면 세션은 다시
    # connection pool을 반환하고 물려있던 모든 객체들을 업데이트 한다.
    session.commit()



