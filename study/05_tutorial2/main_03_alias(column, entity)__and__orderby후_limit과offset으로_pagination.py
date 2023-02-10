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

    #### column alias는 select절에서 .label('')로  / Entity alias는 aliased(, name='')로 만든다.
    stmt = (
        select(User.name.label('name_label'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it.name_label)
    print('*' * 30)
    # SELECT users.name AS name_label
    # FROM users
    # jaeseong
    # jaekyung
    # daisy
    # ara

    user_alias = aliased(User, name='user_alias')
    stmt = (
        select(user_alias)
    )
    print(stmt)
    for it in session.execute(stmt).scalars().all():
        print(it)
    print('*' * 30)
    # SELECT user_alias.id, user_alias.name, user_alias.fullname, user_alias.password 
    # FROM users AS user_alias
    # User[id=1, name'jaeseong', fullname'jaeseong Cho', password='test1234']
    # User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234']
    # User[id=3, name'daisy', fullname'daisy Kim', password='1234']
    # User[id=4, name'ara', fullname'ara Cho', password='1234']

    #### limit/offset은 stmt에서 .limit()을 / offset은 python에서 slicing 하면된다.?
    ## => limit은 기본적으로 order by와 함께 쓰인다.
    stmt = (
        select(User)
        .order_by(User.id)
        .limit(3)  # offset 적용 후 총 3개를 가져온다
        .offset(1)  # offset이 limit보다 먼저 적용된다.
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)


    # SELECT users.id, users.name, users.fullname, users.password
    # FROM users
    # ORDER BY users.id
    #  LIMIT :param_1
    #  OFFSET :param_2
    # (User[id=2, name'jaekyung', fullname'jaekyung Cho', password='1234'],)
    # (User[id=3, name'daisy', fullname'daisy Kim', password='1234'],)
    # (User[id=4, name'ara', fullname'ara Cho', password='1234'],)

    #### stmt를 가변변수로 생각하여, pagination 적용 함수 만들기
    def pagination_with_filters(session, entity, filters=None, page=0, page_size=None):
        stmt = select(entity)

        # apply filter
        if filters:
            if isinstance(filters, dict):
                stmt = stmt.filter_by(**filters)
            else:
                stmt = stmt.filter(filters)

        # apply page_size to limit (offset이후 나올 총 갯수)
        if page_size:
            # stmt = stmt.limit(page_size)
            # limit은 기본적으로order_by와 함께 쓰인다.
            stmt = stmt.order_by(entity.id).limit(page_size)

        # apply page to offset ( page * page_size = 넘겨야할 총 갯수)
        ## ex> page =2를 보고싶다 -> index는 2를 주지만, pass해야할 것은 len가0, 1 2개다.
        ##    => 보고싶은 page index == offset에서는 갯수로 작용된다.
        if page:
            stmt = stmt.offset(page * page_size)

        return session.execute(stmt).scalars().all()


    ## 1번째 페이지를 보고싶다. 페이지별 갯수는 2개이다.
    print(pagination_with_filters(session, User, None, page=1, page_size=2))
    # [User[id=3, name'daisy', fullname'daisy Kim', password='1234'],
    #  User[id=4, name'ara', fullname'ara Cho', password='1234']]

    ## 이름이 ara인 데이터를 보고 싶다 (no pagination)
    print(pagination_with_filters(session, User, {'name':'ara'}))
    # [User[id=4, name'ara', fullname'ara Cho', password='1234']]




    #### limit + offset을 select후 order_by()만 해놓고
    # => pyton slicing으로 적용해도 된다.
    stmt = (
        select(User)
        .order_by(User.id)
    )

    print(stmt)
    for it in session.scalars(stmt).all()[1:3]:
        print(it)
    print('*' * 30)

