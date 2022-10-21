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

    ## 객체 캐스케이딩
    # 이제 메모리의 양방향 구조와 연결된 두 개의 User, Address 객체는
    # 이러한 객체는 객체와 연결될 때까지 일시적인 Session 상태에 있습니다.
    # -> Session.add() 를 사용하고, User 객체에 메서드를 적용할 때
    #   관련 객체인 Address 객체도 추가된다는 점을 확인해 볼 필요가 있습니다

    # (1) session에 1개의 객체를 올리면 -> 관련객체도 올라간다
    session.add(u1)

    print(u1 in session)
    # True
    print(a1 in session)
    # True
    print(a2 in session)
    # True

    # 세 개의 객체는 이제 보류(pending) 상태에 있으며, 이는 INSERT 작업이 진행되지 않았음을 의미합니다.
    # 세 객체는 모두 기본 키(ㅔㅏ)가 할당되지 않았으며, 또한 a1 및 a2 객체에는 열(user_id)을 참조 속성이 있습니다.
    # 이는 객체가 아직 실제 데이터베이스 연결되지 않았기 때문입니다
    print(u1.id, a1.user_id)
    # None None

    # (2) commit으로 DB에 저장된 persistent상태의 동기화된 객체들은
    #     pk뿐만 아니라, fk들도 배정된다.
    session.commit()
    print(u1.id)
    # 6
    print(a1.id, a1.user_id)
    # 4 6
    print(a2.id, a2.user_id)
    # 5 6








