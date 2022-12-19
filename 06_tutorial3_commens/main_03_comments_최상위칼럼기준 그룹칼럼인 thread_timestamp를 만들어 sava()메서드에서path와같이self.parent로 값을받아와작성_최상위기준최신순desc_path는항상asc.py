import time

from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial3 import *

if __name__ == '__main__':
    # init data가 있을 땐: load_fake_data = True
    # add를 commit()의 등장부터는, 싹다 지우고 시작할 땐: truncate = True
    # 테이블구조가 바뀌는 상황엔, 모든 table 지웠다 새로 생성: drop_table = True
    # create_database(truncate=True, drop_table=False)
    session = Session()
    create_database(truncate=True, drop_table=True)

    #### 16. entity로 가서
    #### (1) thread_timestamp 칼럼을 만들고
    #### (2) 각 대댓글들은, 그룹원으로서, parent의 thread_timestamp을 복사해서 가진다. 부모가 없으면 최상위댓글이므로 자신의 timestamp를 복제한다
    #### (3) 정렬시 thread_timestamp을 그룹기준으로 먼저 정렬하고(최신순desc())


    #### 17. 최상위 댓글을 시간차를 주고 commit()해보자

    c1 = Comment(text='hello1', author='alice')
    c1.save()

    time.sleep(1)
    c2 = Comment(text='hello2', author='bob')
    c2.save()

    c11 = Comment(text='reply11', author='bob', parent=c1)
    c12 = Comment(text='reply12', author='susan', parent=c1)
    c111 = Comment(text='reply111', author='susan', parent=c11)
    c21 = Comment(text='reply21', author='alice', parent=c2)

    for c in [c11, c12, c111, c21]:
        c.save()

    #### 17. 이제 최상위댓글별 그룹칼럼(thread_timestamp)가 save()메서드에서 같이 기록되어 완성된 상태이니
    #### (1) 그룹칼럼(thread_timestamp)을 최신순desc -> path는 고정적으로 asc()정렬해보자
    stmt = (
        select(Comment)
        .order_by(Comment.thread_timestamp.desc(), Comment.path.asc())
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it.level() * '    ', it.author, it.path)
    print('*' * 30)


    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id, comments.path, comments.thread_timestamp
    # FROM comments ORDER BY comments.thread_timestamp DESC, comments.path ASC
    #  bob 000002
    #      alice 000002000006
    #  alice 000001
    #      bob 000001000003
    #          susan 000001000003000005
    #      susan 000001000004
    # ******************************

