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



    #### 6. 미구엘 블로그를 참고하여, depth/level 대신  path필드(string, index)를 가지며
    #### pk(id)처럼, 자동으로 증가하는 값을 path에 setter로
    #### 부모id.자식id.자식id... 순으로 넣는다.
    #### 마치묘는 실제로 넣진 않는다.
    # alice: hello1        path: '1'
    # bob: reply11         path: '1.2'
    # bob: hello2          path: '3'
    # susan: reply12       path: '1.4'
    # susan: reply111      path: '1.2.5'
    # alice: reply21       path: '3.6'
    ## => 이렇게 넣을 경우, path로 정렬하게 되면, 아래와 같이 하위객체들이 모이게 된다.
    # alice: hello1        path: '1'    <-- top-level
    # bob: reply11         path: '1.2'    <-- second-level
    # susan: reply111      path: '1.2.5'    <-- third-level
    # susan: reply12       path: '1.4'    <-- second-level
    # bob: hello2          path: '3'    <-- top-level
    # alice: reply21       path: '3.6'    <-- second-level
    ## => 단점은. 1.xx 후 10.xxx가 2.xxx보다 먼저 정려되어버리는 문제점이 생긴다
    ##    문자열숫자의 단점으로서 => 0 padding을 넣어줘야한다.
    ##    0 padding의 갯수만큼 댓글을 가질 수 있기에, 01로 시작하면 99가 한계다
    ##    0 pading을 적당하게 가져야한다.
    # alice: hello1        path: '01'
    # bob: reply11         path: '01.02'
    # susan: reply111      path: '01.02.05'
    # susan: reply12       path: '01.04'
    # bob: hello2          path: '03'
    # alice: reply21       path: '03.06'
    ## => 6자리 100만개를 기본 솔루션으로 가져가자
    #### 그런 다음, level() (인스턴스 메서드)를 추가해서, 객체필드(self.path)를 사용한 level도 구할 수 있다.
    #### => 단점으로는 register시, path를 제외한 필드로 add commit()후, level를 따로 구해서 한번더 commit() 해줘야한다.


    #### 10. path까지 기입하기 위한,
    ####     데이터 삽입 by .save()

    ## 이번에는 개별로 등록하도록 하도록 한다.
    ## => api로서는 1개의 question만 등록(Add)요청이 올 것이기 때문??
    c1 = Comment(text='hello1', author='alice')
    time.sleep(1)
    c2 = Comment(text='hello2', author='bob')

    c11 = Comment(text='reply11', author='bob', parent=c1)
    c12 = Comment(text='reply12', author='susan', parent=c1)
    c111 = Comment(text='reply111', author='susan', parent=c11)
    c21 = Comment(text='reply21', author='alice', parent=c2)

    for c in [c1, c2, c11, c12, c111, c21]:
        c.save()

    # 1,hello1,alice,2022-10-26 14:29:18,,000001
    # 2,reply11,bob,2022-10-26 14:29:18,1,000001000002
    # 3,reply12,susan,2022-10-26 14:29:18,1,000001000003
    # 4,reply111,susan,2022-10-26 14:29:18,2,000001000002000004
    # 5,hello2,bob,2022-10-26 14:29:18,,000005
    # 6,reply21,alice,2022-10-26 14:29:18,5,000005000006


    #### 11. path는 order_by에서 정렬할 때 쓴다.
    ## => 빠른순으로 level0 댓글 - 거기에 달린 댓글 한 set씩 같이 나온다.
    stmt = (
        select(Comment)
        .order_by(Comment.path)
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it.author, it.text, it.path)
    print('*' * 30)
    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id, comments.path
    # FROM comments ORDER BY comments.path
    # alice hello1 000001
    # bob reply11 000001000002
    # susan reply111 000001000002000004
    # susan reply12 000001000003
    # bob hello2 000005
    # alice reply21 000005000006
    # ******************************


    #### 12. 특정 post/board에 달린 댓글들 -> path오름차순 정렬후, .level()을 이용해서  padding을 준다.
    # -> 원래는 board_id에 대해  거기 딸린 것을 가져와야하는데
    #     # ondelete="CASCADE"를 지정하여 Board가 삭제시 자동적으로 해당된 댓글 또한 삭제
    #   board_id = db.Column(db.Integer, db.ForeignKey(Board.id, ondelete="CASCADE"), nullable=True)
    stmt = (
        select(Comment)
        # .where(post_id=post.id)
        .order_by(Comment.path.desc())
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it.level() * '    ', it.author, it.path)
    print('*' * 30)
    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id, comments.path
    # FROM comments ORDER BY comments.path ASC
    #  alice 000001
    #      bob 000001000002
    #          susan 000001000002000004
    #      susan 000001000003
    #  bob 000005
    #      alice 000005000006
    # ******************************

    #### path정렬의 제한 -> 최상위 댓글부터 path순(최상위에 달린순서)대로만 가져올 수 있다.

    #### => path.desc()로 정렬하면, depth깊을 순으로 가져와서 이상ㅎ게 출력된다.
    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id, comments.path
    # FROM comments ORDER BY comments.path DESC
    #      alice 000005000006
    #  bob 000005
    #      susan 000001000003
    #          susan 000001000002000004
    #      bob 000001000002
    #  alice 000001
    # ******************************

    #### 13. 최신순(timestamp-desc)이면서 depth순(path-asc)으로 가져오려면?
    #### => 현재 댓글들은 path acs순이 유지되어야, depth가 정상유지된다.
    #### => 그렇다면, (1) 최상위놈들-딸리 하위놈들을 timestamp그룹으로 묵고 -> 그룹timestamp는 desc()으로
    #                (2) -> 그룹내에서 path.asc()순으로 정렬하면 된다.
    # 최상위 댓글에 한해서, 최신에서 가장 오랜 순으로 가져오려면?

    # 다른 경우에는 사용자가 최상위 댓글을 위 또는 아래로 투표할 수 있으며 가장 많이 투표된 댓글을 먼저 표시하려고 합니다.

    # 이러한 대체 정렬 전략을 구현하려면 추가 열을 사용해야 합니다. 최상위 주석의 타임스탬프를 기준으로 정렬하려면
    # 각 회신에 중복된 최상위 주석의 타임스탬프가 있는 thread_timestamp 열을 추가하기만 하면 됩니다.
    # save() 메서드는 이 타임스탬프를 부모에서 자식으로 전달할 수 있으므로 이 추가 열을 관리하는 데 부담이 되지 않습니다.
    # 그런 다음 응답 순서를 유지하기 위해 경로별 보조 정렬을 사용하여 타임스탬프별로 정렬할 수 있습니다.

    #### (1) thread_timestamp 칼럼을 만들고
    #### (2) 각 대댓글들은, 그룹원으로서, parent의 thread_timestamp을 복사해서 가진다. 부모가 없으면 최상위댓글이므로 자신의 timestamp를 복제한다
    #### (3) 정렬시 thread_timestamp을 그룹기준으로 먼저 정렬하고(최신순desc())



