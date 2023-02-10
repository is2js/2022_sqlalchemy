from sqlalchemy import select


#### stmt를 가변변수로 생각하여  orderby +limit  / offset를 인자에 따라 적용하여 재할당
#### pagination 적용 함수 만들기
from src.config import db_config


def pagination_with_filter(session, entity, filters=None, page=0, page_size=None):
    stmt = select(entity)

    # apply filter
    if filters:
        # pagination_with_filter( User, {'name': 'ara'}, )
        if isinstance(filters, dict):
            stmt = stmt.filter_by(**filters)
        # pagination_with_filter( User, User.name == 'ara, )
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


def paginate(stmt, page=1, per_page=db_config.COMMENTS_PER_PAGE):
    # apply per_page to limit (offset이후 나올 총 갯수)
    if per_page:
        # stmt = stmt.limit(per_page)
        # limit은 기본적으로order_by와 함께 쓰인다.
        stmt = stmt.limit(per_page)

    # apply page to offset ( (page-1) * page_size = 넘겨야할 총 갯수)
    ## ex> page =2 를 보고싶다 -> 앞에 1 page ( per_page갯수만큼 )  pass해야한다.
    ##    => 보고싶은 page  == (page-1 * page당갯수)만큼 건너띈다.
    if page:
        stmt = stmt.offset((page - 1) * per_page)

    return stmt