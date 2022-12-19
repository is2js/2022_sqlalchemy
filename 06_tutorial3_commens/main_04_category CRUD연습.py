import datetime
import time

from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload, lazyload

from create_database_tutorial3 import *
from src.infra.tutorial3.notices import BannerType

if __name__ == '__main__':
    # 1. init data가 있을 땐: load_fake_data = True
    # 2. add() -> commit() method save 등장부터는, 싹다 지우고 시작할 땐: truncate = True
    # 3. 테이블구조가 바뀌는 상황엔, 모든 table 지웠다 새로 생성: drop_table = True
    # create_database(truncate=True, drop_table=False)
    session = Session()
    create_database(truncate=True, drop_table=False, load_fake_data=True)

    # all
    stmt = (
        select(Category)
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it)
    print('*' * 30)

    # first -> scalars().first()
    # -> scalars( 복수 ).one()은 없다 -> .one()은 이미 1개의 결과가 만족된 상태여야한다.
    # 1) scalars( limit(1)).one() or
    # 2) execute((). scalar_one()  or
    # 3) scalars( ).first()

    stmt = (
        select(Category)
    )
    print(stmt)
    print(session.scalars(stmt).first())
    print('*' * 30)

    # get -> session.get(Entity, id)
    print(session.get(Category, 1))
    print(session.get(Category, 2))
    print('*' * 30)

    #filter
    stmt = (
        select(Category)
        .filter(Category.name.startswith('분류'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    
    # orderby
    stmt = (
        select(Category)
        .order_by(Category.add_date)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # orderby 역순은 칼럼.desc() or desc('라벨명') 대신 앞에 -빼기를 넣어줘도 된다?!
    # => 안된다.
    # =>  flask-sqlalchemy만 가능함.
    stmt = (
        select(Category)
        # .order_by(-Category.add_date)
        .order_by(Category.add_date.desc())
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # limit은 갯수를 넘겨도 오류는 안난다.
    stmt = (
        select(Category)
        # .limit(3)
        .limit(7)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)

    # 수정은 기존에는 session.query().update({})로 특정필드에 대해 바로 가능했지만
    # 2.0스타일에서는 update문을 강제 or 객체필드변화후 commit()
    # 1) update-> session.get( Entity, id) -> 객체필드변화 -> commit or update().where().values(필드=)문
    # => updaate확인은 in session.dirty
    # 2) delete-> session.delete(Entity, id) commit or delete문
    # => delete확인은 in session
    cate1 = session.get(Category, 1)
    cate1.name = '신분류1'
    print( cate1 in session.dirty ) # True
    session.commit()
    print( cate1.name ) # 신분류1 -> onupdate 설정으로 인해 pub_date바뀜

    session.delete(cate1)
    session.commit()
    print(session.get(Category, 1)) # None

    #### 삭제한 객체는 연동되어 None이 된다. 그 객체를 활용할 순 없다.
    print(cate1)
    # session.add(cate1) # AttributeError: 'NoneType' object has no attribute 'name'
    # session.commit() # sqlalchemy.exc.InvalidRequestError: Instance '<Category at 0x26920cb9780>' has been deleted.  Use the make_transient() function to send this object back to the transient state.





