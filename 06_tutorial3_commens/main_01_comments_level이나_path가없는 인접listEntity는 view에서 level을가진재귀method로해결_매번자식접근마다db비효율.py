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
    create_database(truncate=True, drop_table=False)
    session = Session()

    #  데이터 삽입들 삽입
    ## 2. 인접리스트 Entity 데이터 삽입
    # -> 동기화되므로 root에서 append하여, add하면 다 등록됨을 저번에 알아봄

    ## 이번에는 개별로 등록하도록 하도록 한다.
    ## => api로서는 1개의 question만 등록(Add)요청이 올 것이기 때문??
    c1 = Comment(text='hello1', author='alice')
    session.add(c1)
    c2 = Comment(text='hello2', author='bob')

    #### 3. 대댓글 등록부터는, parent_id(원래댓글id_pk) or parent(관계칼럼)의 객체가 주어져야한다.
    ## => 칼럼이 아닌 relationship에서 주는 backref를
    ##    many(자식)입장으로서 keyword로 입력할 수 있다.!!
    ## -> 부모의   chilren.append로 동기화하는것과 비슷하다

    ## => 어차피 하위entity로서, 상위entity를 존재유무를 find(fk)로 해서 찾을 것이니
    ##    찾은 상위객체(부모객체)를 fk대신 활용할 수 있을 것이다.

    # c11 = Comment(text='reply11', author='bob', parent_id=)
    c11 = Comment(text='reply11', author='bob', parent=c1)
    session.add(c11)
    c12 = Comment(text='reply12', author='susan', parent=c1)
    session.add(c12)
    c111 = Comment(text='reply111', author='susan', parent=c11)
    session.add(c111)
    c21 = Comment(text='reply21', author='alice', parent=c2)
    session.add(c21)

    session.commit()


    #### 4. 자기자신을 품고 있는 인접list Entity가 depth(level)정보가 없다면
    ## => view에서 직접 root node 지정+ 재귀로 level을 메서드로 구현해서
    ##    padding * level로 보여줘야한다.
    def display_comment(comment, level=0):
        ## 부모로서 현재부터 방문
        print(f"{'    ' * level} {comment.author} {comment.text}")
        ## 자식들 list를 순회해서 방문
        for reply in comment.replies:
            ## 자식들은, 자신이 부모로서 다시 호출
            display_comment(reply, level + 1)


    display_comment(c1)
    #  alice hello1
    #      bob reply11
    #          susan reply111
    #      susan reply12

    #### 5. parent가 없이 생성된, level=0 comment들을 시간순으로 출력
    stmt = (
        select(Comment)
        # parent_id(fk) is null대신, backref 관계칼럼 객체 == None으로 판단할 수 있다.
        # .where(Comment.parent_id)
        .where(Comment.parent == None)
        .order_by(Comment.timestamp.asc())
    )
    print(stmt)
    for comment in session.scalars(stmt):
        display_comment(comment)
    print('*' * 30)
    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id
    # FROM comments
    # WHERE comments.parent_id IS NULL
    # ORDER BY comments.timestamp ASC
    #  alice hello1
    #      bob reply11
    #          susan reply111
    #      susan reply12
    #  bob hell21
    #      alice reply21
    # ******************************



    #### but, 재귀를 통한 호출은 자식 접근시마다 매번 db에 호출을 보내여
    #### 매우 비효율적이게 된다.

    # The for-loop at the bottom retrieves all the top-level comments (those that have no parent), and then for each of them it recursively retrieves their replies in the display_comment() function.
    #
    # This solution is extremely inefficient. If you have a comment thread with a hundred comments, you will need to issue a hundred additional database queries after the one that gets the top-level comments to reconstruct the entire tree. And if you wanted to paginate your comments, the only thing you can do is paginate the top-level-comments, you can't really paginate the comment thread as a whole.
    # 이 솔루션은 매우 비효율적입니다. 100개의 주석이 있는 주석 스레드가 있는 경우 전체 트리를 재구성하기 위해 최상위 주석을 얻은 쿼리 다음에
    # 100개의 추가 데이터베이스 쿼리를 실행해야 합니다.
    # 댓글에 페이지를 매기고 싶다면 최상위 댓글에 페이지를 매기는 것뿐입니다.
    # 댓글 스레드 전체에 페이지를 매길 수는 없습니다.