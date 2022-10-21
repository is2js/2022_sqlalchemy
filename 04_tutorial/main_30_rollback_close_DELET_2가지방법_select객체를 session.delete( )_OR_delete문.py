from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### DELETE 2가지 방법
    # 1. session.delete( select객체 )
    # 2. orm delete문 이용

    # Session.delete() 메서드를 사용하여 개별 ORM 객체를 삭제 대상으로 표시할 수 있습니다.
    # -> delete가 수행되면, 해당 Session에 존재하는 객체들은 [expired 상태]가 되게 됩니다.

    #### 1. session.delete( select객체 )
    ## (1) 메모리에 ENtity가 올라가있다면 id로 select를  sesesion.get(Entity, id)로 하면 된다.
    patrick = session.get(User, 3)
    # print(patrick)
    # User[id=3, name'patrick', fullname='Patrick Star']

    ## (2) select문이나 .get()으로 꺼낸 객체로 delete
    #  =>  session.delete( select한 객체 )
    session.delete(patrick)
    # => update든 /delete든 flush가 일어나야 메모리상 DB에 반영된다.

    ## (3) select문으로, auto flush를 실행 ->
    result = session.execute(
        (
            select(User)
            .where(User.name == 'patrick')
        )
    ).first()  # first()는 객체가 아니라 Row객체(튜플로 나옴)
    print(result)
    # None -> sesion.delete()가 select발생하는 순간 메모리db에 반영되어서, 조회가 안된다.

    ## (3) 메모리상 db에서 삭제되면, 해당 EntityModel객체는 session에서 사라진다.
    print(patrick in session)
    # False

    ## => 위의 UPDATE에서 사용된 'Sandy'와 마찬가지로, 해당 작업들은 진행중인 트랜잭션에서만 이루어진 일이며
    #     commit 하지 않는 이상, 언제든 취소할 수 있습니다.

    #### 2. ORM delete문으로 삭제
    # (1) 확인을 위해 미리 select객체 빼놓기
    squidward = session.get(User, 4)
    # print(squidward, type(squidward))
    #   User[id=4, name'squidward', fullname='Squidward Tentacles']
    #   <class 'src.infra.tutorial.user.User'>

    print(squidward in session)
    # True

    # (2) delete문으로 삭제후, select객체가 sesion에선 사라질 것이다.
    session.execute(
        delete(User)
        .where(User.name == 'squidward')
    )

    print(squidward in session)
    #  False


    #### 3. Rolling Back
    # (1) db저장 취소 및 [session에서 만료] == 객체의 expired 상태
    #  Session.rollback()을 호출하면 트랜잭션을 롤백할 뿐만 아니라
    #  => 현재 이 Session과 연결된 [모든 객체를 expired 상태]로 바꿉니다.
    #  => 이러한 상태 변경은 다음에 객체에 접근 할 때 스스로 새로 고침을 하는 효과가 있고
    #     이러한 프로세스를 [지연 로딩] 이라고 합니다.
    session.rollback()

    # (2) EntityModel객체. __dict__ 로 session과 연결된 상태보기
    # expired 상태의 객체인 squidward 를 자세히 보면,
    # 특별한 SQLAlchemy 관련 상태 객체를 제외하고 다른 정보가 남아 있지 않음을 볼 수 있습니다.
    print(squidward.__dict__)
    # {'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object at 0x000002452F8E6438>}

    # (3) 객체 속성에 접근하는 순간부터 => session에 연결되면서 새 트랜잭션이 생김
    print(squidward.name)
    #### >>> squidward.fullname # session이 만료되었으므로,
    # ==> 해당 객체 속성에 접근 시, 트랜잭션이 새로 일어납니다.
    # ==> 이제 데이터베이스 행이 squidward 객체에도 채워진 것을 볼 수 있습니다.
    print(squidward.__dict__)
    # {'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object at 0x00000254ABD75320>,
    #  'fullname': 'Squidward Tentacles', 'id': 4, 'name': 'squidward'}

    # (4) delete가 취소됨으로서 patrick객체도 session으로 다시 들어오게 된다.
    print(patrick in session)
    # True

    # (5) 삭제취소 객체 is db에서 select한객체 동일하다
    print(session.execute(select(User).where(User.name == 'patrick')).scalar_one() is patrick)
    # True


    #### 4. sesion Close -> session 속 EntityModel객체의 [detached상태] -> 사용지양
    # 마찬가지로 컨텍스트 구문을 통해 생성한 Session을 컨텍스트 구문 내에서 닫으면 다음 작업들이 수행됩니다.
    # (1) 진행 중인 모든 트랜잭션을 취소(예: 롤백)하여 연결 풀에 대한 모든 연결 리소스를 해제합니다.
    #     즉, Session을 사용하여 일부 읽기 전용 작업을 수행한 다음, 닫을 때 트랜잭션이 롤백되었는지 확인하기 위해
    #     Session.rollback()을 명시적으로 호출할 필요가 없습니다. 연결 풀이 이를 처리합니다.
    # (2) Session에서 모든 개체를 삭제합니다.
    #     이것은 sandy, patrick 및 squidward와 같이 이 Session에 대해 로드한 모든 [Python 개체가 이제 detached 상태]에 있음을 의미합니다.
    #     예를 들어 expired 상태에 있던 객체는 Session.commit() 호출로 인해 현재 행의 상태를 포함하지 않고 새로 고칠 데이터베이스 트랜잭션과 더 이상 연관되지 않습니다.
    session.close()

    # => 나는.. 계속 연결정보가 있고 에러가 안난다...
    print(patrick.__dict__)
    print(squidward.__dict__)

    # (3) detached된 객체는 Session.add() 메서드를 사용하여 동일한 객체 또는 새 Session과 다시 연결될 수 있습니다.
    #     그러면 특정 데이터베이스 행과의 관계가 다시 설정됩니다.
    session.add(patrick)
    print(patrick.__dict__)
    #
    #     => detached 상태의 개체는 되도록이면 사용을 지양해야 합니다. Session이 닫히면 이전에 연결된 모든 개체에 대한 참조도 정리합니다.
    #     일반적으로 detached된 객체가 필요한 경우는 웹 어플리케이션에서 방금 커밋된 개체를 뷰에서 렌더링되기 전에 Session이 닫힌 경우가 있습니다.
    #     이 경우 Session.expire_on_commit 플래그를 False로 설정합니다.
