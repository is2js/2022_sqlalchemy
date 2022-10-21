from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### INSERT

    ## 1. 행을 나타나는 객체인스턴스를 만들기 [transient]
    ## => ORM 매핑에 의해 자동으로 생성된 __init__() 생성자 덕에 생성자의
    #     열 이름을 키(keywrod)로 사용하여 각 객체를 생성할 수 있습니다
    ekrabs = User(name="ehkrabs", fullname="Eugene H. Krabs")

    # User('squidward',)
    ## => id를 제외한 생성자를 만들어줘야, keyword가 아닌 방식으로 Model객체를 생성할 수 있다.
    squidward = User('squidward', "Squidward Tentacles")
    print(squidward)
    # User[id=None, name'squidward', fullname='Squidward Tentacles']

    ## => id의 None 값은 속성에 아직 값이 없음을 나타내기 위해 SQLAlchemy에서 제공합니다.

    ## => 위의 두 객체(squiward와 krabs)는 transient 상태라고 불리게 됩니다.
    #     transient 상태란, 어떤 데이터베이스와 연결되지 않고, INSERT문을 생성할 수 있는 Session객체와도 아직 연결되지 않은 상태를 의미합니다.
    ## my) id가 배정되지 않은(not insert), sesion에 add도 안한 객체는 [transient 상태의 EntityModel객체]라고 한다



    ## 2. Session에 객체 추가하기[Pending] from transient
    session.add(squidward)
    session.add(ekrabs)
    print(session.new)
    # IdentitySet([User[id=None, name'squidward', fullname='Squidward Tentacles'], User[id=None, name'ehkrabs', fullname='Eugene H. Krabs']])

    ## => session에 add된 객체상태를 transient => [pending 상태의 EntityModel객체]라고 한다
    # => 확인은 session.new를 출력하여 pending상태의 객체를 확인할 수 있다.
    # IdentitySet은 모든 경우에 객체 ID를 hash하는 Python set입니다.
    # 즉, Python 내장 함수 중 hash()가 아닌, id() 메소드를 사용하고 있습니다.


    ## 3. Flushing[persistent, 트랜잭션 열림.]   from pending
    # Session 객체는 unit of work 패턴 (opens new window)을 사용합니다. 참고:https://zetlos.tistory.com/1179902868
    # 이는 변경 사항을 누적(pending)하지만, 필요할 때까지는 실제로 데이터베이스와 통신을 하지 않음을 의미합니다.
    # 이런 동작 방식을 통해서 위에서 언급한 pending 상태의 객체들이 더 효율적인 SQL DML로 사용됩니다.
    # 현재의 변경된 사항들을 실제로 Database에 SQL을 통해 내보내는 작업을 flush 이라고 합니다.

    print(session.flush()) # None
    # INSERT INTO user_account (name, fullname) VALUES (?, ?)
    # [...] ('squidward', 'Squidward Tentacles')
    # INSERT INTO user_account (name, fullname) VALUES (?, ?)
    # [...] ('ehkrabs', 'Eugene H. Krabs')

    ## my) flush()를 해서 DB에 SQL을 보냈어도 commit전까지는 DB에 기록안된다!!

    ## flush()를 했어도, commit()은 아직 안됬다
    ## => 이제 트랜잭션은 Session.commit(), Session.rollback(), Session.close() 중 하나가 호출될 때 까지
    #    열린 상태로 유지됩니다.

    # Session.flush()를 직접 사용하여, 현재 pending 상태에 있는 내용을 직접 밀어넣을 수 있지만,
    # Session은 [autoflush라는] 동작을 특징으로 하므로 일반적으로는 필요하지 않습니다.
    # Session.commit()이 호출 될 때 마다 변경 사항을 flush 합니다
    # => my)   commit()을 통해 add 된 pending 객체들이 auto flush()된다.
    # 이제 트랜잭션은 Session.commit(), Session.rollback(), Session.close() 중 하나가 호출될 때 까지 열린 상태로 유지됩니다


    ## 4. 자동생성된 id, pk칼럼(기본키 속성) [persistent by flush()]
    ## => flush가 되면 DB에 저장되진 않지만, id는 배정된다.
    ## => 저장되진 않았지만, DB에 insert는 된 상태를 [persistent 상태의 EntityModel객체]라고 한다
    print(squidward.id)
    print(ekrabs.id)
    # 4
    # 5

    # 행이 삽입되게 되면, 우리가 생성한 Python 객체는 persistent 라는 상태가 됩니다.
    # persistent 상태는 로드된 Session 객체와 연결됩니다.
    # INSERT 실행 시, ORM이 각각의 새 객체에 대한 기본 키 식별자를 검색하는 효과를 가져옵니다.
    # 이전에 소개한 것과 동일한 CursorResult.inserted_primary_key 접근자를 사용합니다.

    # ORM이 flush 될 때, executemany 대신, 두 개의 다른 INSERT 문을 사용하는 이유가 바로 이 CursorResult.inserted_primary_key 때문입니다.
    # SQLite의 경우 한 번에 한 열을 INSERT 해야 자동 증가 기능을 사용할 수 있습니다.(PostgreSQL의 IDENTITY나 SERIAL 기능등 다른 다양한 데이터베이스들의 경우들도 이처럼 동작합니다.)
    # psycopg2와 같이 한번에 많은 데이터에 대한 기본 키 정보를 제공 받을 수 있는 데이터베이스가 연결되어 있다면, ORM은 이를 최적화하여 많은 열을 한번에 INSERT 하도록 합니다.


    ## 5. Identity Map
    ## => Identity Map(ID Map)은 현재 메모리에 로드된 모든 EntityMdoel객체를
    #     기본 키 ID에 연결하는 메모리 내 저장소입니다.
    #     Session.get()을 통해서 객체 중 하나를 검색할 수 있습니다.
    #     (1) 이 메소드는 객체가 메모리에 있으면, ID Map에서,
    #     (2) 그렇지 않으면 SELECT문을 통해서 객체를 검색합니다.
    ## my) commit을 통해 DB에 반영은 안됬찌만, flush로 인해 id가 배정된 상태면
    ##     id맵으로 검색할 수 있다.
    some_squidward = session.get(User, 4)
    print(some_squidward)
    # User[id=4, name'squidward', fullname='Squidward Tentacles']

    ## => 중요한 점은, ID Map은 Python 객체 중에서도 고유한 객체를 유지하고 있다는 점입니다.
    print(some_squidward is squidward)
    # True
    ## => ID map은 동기화되지 않은 상태에서, 트랜잭션 내에서 복잡한 개체 집합을 조작할 수 있도록 하는 중요한 기능입니다.

    ## 6. Committing => flush로 열렸던 트랜잭션이 닫히면서, DB에 반영되는 순간
    # 현재까지의 변경사항을 트랜잭션에 commit 합니다.
    session.commit()

    ## => DB에 4, 5번 데이터가 등록됨.









