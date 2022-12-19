import time

from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload, lazyload

from create_database_tutorial3 import *

if __name__ == '__main__':
    # init data가 있을 땐: load_fake_data = True
    # add를 commit()의 등장부터는, 싹다 지우고 시작할 땐: truncate = True
    # 테이블구조가 바뀌는 상황엔, 모든 table 지웠다 새로 생성: drop_table = True
    # create_database(truncate=True, drop_table=False)
    session = Session()
    create_database(truncate=False, drop_table=False)



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
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it.level * '    ', it.author, it.path)
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


    ## 18. 최상위 댓글의 그룹값(thread_timestamp or thread_vote)이 변한다면
    ##     해당 최상위의 하위 검색을 path.like(self.path + '%')로 검색한 뒤
    ##  하위부서들  그룹값(thread_xxx)를 모두 변화시켜줘야한다.
    ## => .save()와 같이 지식이 생겨버린다. .update_group_column()

    stmt = (
        select(Comment)
        .where(Comment.id == 1)
    )
    top = session.scalars(stmt).one()
    print(top)
    stmt = (
        select(Comment)
        .where(Comment.path.like(top.path + '%'))
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it)
    print('*' * 30)
    # Comment[id=1, text='hello1', author='alice', path='000001']
    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id, comments.path, comments.thread_timestamp
    # FROM comments
    # WHERE comments.path LIKE :path_1
    # Comment[id=1, text='hello1', author='alice', path='000001']
    # Comment[id=3, text='reply11', author='bob', path='000001000003']
    # Comment[id=4, text='reply111', author='susan', path='000001000003000004']
    # Comment[id=5, text='reply12', author='susan', path='000001000005']
    # ******************************

    #### top레벨의 그룹값의 원본 변경시 -> 하위도 like path + '%'로 검색해서 모두
    # ex> vote변경 -> top부터 하위모든 것들의 thread_vote 변경
    # class Comment(db.Model):
    #     def change_vote(vote):
    #         for comment in Comment.query.filter(Comment.path.like(self.path + '%')):
    #             self.thread_vote = vote
    #             db.session.add(self)
    #         db.session.commit()

    # If you prefer something a little bit more efficient, you can do it with a update() call bypassing the ORM.
    ## => 객체속성변화말고 update문으로 더 효율적으로 할 수 있다.
    #    stmt = (
    #         update(User)
    #         .where(User.name == 'sandy')
    #         .values(fullname="Squirrel Extraordinaire")
    #     )
    # stmt = (
    #     update(Comment)
    #     .where(Comment.path.like(top.path + '%'))
    #     .values(thread_vote = 업데이트된 vote값)
    # )
    # print(stmt)
    # for it in session.execute(stmt):
    #     print(it)
    # print('*' * 30)

    ## 19.  fk를 문자열 대신, Entity.id 나 자신이므로 id만 주기 + ondelete= 옵션주기
    #(1) Fk지정시, ondelte 옵션을 준다. : parent_id = Column(Integer, ForeignKey(id, ondelete='CASCADE'))
    #(2) relationship에서는 backref가 아닌 자신에게 cascade="all" 옵션을 준다.  : , cascade="all"
    # session.expunge_all() # session를 다 날린다?!
    # c1 = session.get(Comment, 1)
    # session.delete(c1)
    # stmt = (
    #     select(Comment)
    #     # .options(lazyload('*'))
    # )
    # print(stmt)
    # for it in session.execute(stmt):
    #     print(it)
    # print('*' * 30)
    # SELECT comments.id, comments.text, comments.author, comments.timestamp, comments.parent_id, comments.path, comments.thread_timestamp
    # FROM comments
    # (Comment[id=2, text='hello2', author='bob', level=0],)
    # (Comment[id=6, text='reply21', author='alice', level=1],)
    # ******************************

    ### 20.

