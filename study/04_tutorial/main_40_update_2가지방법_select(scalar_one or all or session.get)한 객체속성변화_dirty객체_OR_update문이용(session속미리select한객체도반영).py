from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### UPDATE 2가지 방법
    # 1. Session에서 사용하는 unit of work 패턴 방식이 있습니다.
    #    변경사항이 있는 기본 키 별로 UPDATE 작업이 순서대로 내보내지게 됩니다.
    #    => my) select한 객체의 속성변화로 자동 업데이트

    # 2. "ORM 사용 업데이트"라고 하며 명시적으로 Session과 함께 Update 구성을 사용할 수도 있습니다.
    # cf) 2.0부터는 .one() 대신 .scalar_one()으로 사용한다?
    #    => my) update무능ㄹ 사용

    ## 1. [객체 속성변화] -> 변경사항을 자동으로 업데이트하기
    # (1) stmt execute결과를 print만 하지말고, 객체를 변수에 받는다.
    stmt = (
        select(User)
        .filter_by(name='sandy')
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # WHERE user_account.name = :name_1
    # (User[id=2, name'sandy', fullname='Sandy Cheeks'],)

    # (2) session.execute()만 하면 -> ChunkedIteratorResult(Result객체)
    #     => <class 'sqlalchemy.engine.result.ChunkedIteratorResult'>
    sandy_one = session.execute(stmt).one()
    sandy_scalar_one = session.execute(stmt).scalar_one()
    sandy_all = session.execute(stmt).all()
    sandy_first = session.execute(stmt).first()
    print(type(sandy_one), type(sandy_scalar_one), type(sandy_all), type(sandy_first))
    print(sandy_one, sandy_scalar_one, sandy_all, sandy_first)
    print('*' * 30)

    # (3) .one()으로 추출시 -> Row객체 => 객체 바로 속성조절 못함.
    #     =>   <class 'sqlalchemy.engine.row.Row'>
    #          (User[id=2, name'sandy', fullname='Sandy Cheeks'],)

    #     .scalar_one()으로 추출시 -> User객체 => 업데이트를 위한 객체 속성조절 가능하다.
    #      =>   <class 'src.infra.tutorial.user.User'>
    #           User[id=2, name'sandy', fullname='Sandy Cheeks']

    #      .all() -> User객체 list
    #      =>   <class 'list'>
    #           [(User[id=2, name'sandy', fullname='Sandy Cheeks'],)]

    #      .first() -> one()과 동일한 Row객체
    #      =>   <class 'sqlalchemy.engine.row.Row'>
    #           (User[id=2, name'sandy', fullname='Sandy Cheeks'],)

    #### my) session.execute로 객체를 바로뽑으려면 scalar_one()이나 all()을 쓰자.
    # -> one()이나 first()를 쓰면 tuple형태의 Row객체로 반환되어 객체조정하려면 [0]인덱싱해야한다?!

    #### 이 'Sandy' 유저 객체는 데이터베이스에서 행, 더 구체적으로는 트랙잭션 측면에서
    # 기본 키가 2인 행에 대한 proxy 역할을 합니다.

    ## (4) select한 객체의 속성변화 -> session이 변화를 자동 기록한다
    ## => session [객체변화 인식] 확인은 session.dirty에서 sandy객체가 포함되어있는지 확인한다.
    print('select객체 속성변화 전 session.dirty포함여부:', sandy_scalar_one in session.dirty)

    sandy_scalar_one.fullname = "Sandy Squirrel"

    print('select객체 속성변화 후 session.dirty포함여부:', sandy_scalar_one in session.dirty)
    # select객체 속성변화 전 session.dirty포함여부: False
    # select객체 속성변화 후 session.dirty포함여부: True

    ## my) 객체 속성변화는 session에만 기록된 pending상태로서 db 저장 안된상태?
    ## => 이 'Sandy' 유저 객체는 데이터베이스에서 행, 더 구체적으로는 트랙잭션 측면에서 기본 키가 2인 행에 대한 proxy 역할을 합니다.

    ## Session이 flush를 실행하게 되면, 데이터베이스에서 UPDATE가 실행되어 데이터베이스에 실제로 값을 갱신합니다.
    # 문을 추가로 실행하게 되면, 자동으로 flush가 실행되어 sandy의 바뀐 이름 값을 SELECT를 통해서 바로 얻을 수 있습니다.

    ## (5) select를 다시 해서 dirty(속성변한 EntityModel객체)상태가 불러와지는지 보자.
    #### select를 하는 순간, commit을 안했음에도 [자동 flush]가 구동되어
    #### => db에는 [저장은 안됬찌만], [db메모리상으로는 바뀐 상태]이다.
    stmt = (
        select(User)
        .filter_by(name='sandy')
    )
    sandy = session.execute(stmt).scalar_one()
    print(sandy.fullname == 'Sandy Squirrel')
    # True
    #### => 객체속성변화 -> commit을 안해도 다른 쿼리(select)등으로 인해 자동flush가 발생되어
    ####    메모리상 db에 반영된 상태다.(persisent)

    ## (6) 그렇다면, db에 반영되었으므로 sesion.dirty에서는 사라졌을 것이다.
    print(sandy_scalar_one in session.dirty)
    # False

    #### => 객체속성변화는 [flush될대 DB상 업데이트까지 반영]시킨다.(저장은 안됨)

    ## 2. select한 객체속성변화로 자동업데이트가 아닌
    ## => update문으로 ORM사용 직접 업데이트
    ## (1)
    stmt = (
        update(User)
        .where(User.name == 'sandy')
        .values(fullname="Squirrel Extraordinaire")
    )

    session.execute(stmt)

    #### (2) update문으로 업데이트된 내용이, 기존에 select했던 객체에도 반영이 ㄴ된다.
    ## => 현재 Session에서 주어진 조건과 일치하는 객체가 있다면,
    #     이 객체에도 해당하는 update가 반영되게 됩니다.
    print(sandy_scalar_one.fullname)
    # Squirrel Extraordinaire
