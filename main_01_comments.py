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


    #### 6. 자식들을 db에 한번의 쿼리로 가져올 수 잇는 방법
    #### => 재귀를 피해야한다.
    ## (1) CTE로 한번에 호출했지만, depth/level 정보가 없으니, depth를 만들 수없다.
    #### => SQL 쿼리 1번으로 해결하는 방법  재귀 CTE(이미 다룸) -> depth정보없이 불러오기만 한다.
    parent = (
        select(Comment)
        .where(Comment.parent_id == 1) # 특정 부모 1개 지정
    ).cte(recursive=True)

    child = aliased(Comment)
    parent = (
        parent
        .union_all(
            select(child)
            .where(child.parent_id == parent.c.id)
        )
    )
    stmt = (
        select(parent)
    )
    print(type(stmt))
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    print(session.scalars(stmt).all())
    # [3, 4, 6]
    print(session.execute(stmt).all())
    # [(3, 'reply11', 'bob', datetime.datetime(2022, 10, 26, 19, 23, 8, 585834), 1), (4, 'reply12', 'susan', datetime.datetime(2022, 10, 26, 19, 23, 8, 585834), 1), (6, 'reply111', 'susan', datetime.datetime(2022, 10, 26, 19, 23, 8, 585834), 3)]


    #### 7. 일단, depth정보를 entity에 기록 or 바깥에서 재귀 + depth변수로 돌려서 획득한다.
    #### json으로 만들 때도..어차피 재귀를 타야한다?
    # Getting recursive structures out of a relational database is not trivial.
    # It usually need joins that get more complex per number of levels.
    # You should consider creating the recursive structure in Python code.
    # 관계형 데이터베이스에서 재귀 구조를 가져오는 것은 쉬운 일이 아닙니다.
    # 일반적으로 레벨 수에 따라 더 복잡해지는 조인이 필요합니다.
    # Python 코드에서 재귀 구조를 만드는 것을 고려해야 합니다.

    # Does this answer your question? How to get dict of lists from relationship in sqlalchemy? –
    # 자식객체들을 관계칼럼에서 list -> [ 객채별dict ] : https://gist.github.com/onecrayon/646da61accf54674d4f5098376a2c5df

    ## python 재귀로 json만들기
    # (1) 2011: https://stackoverflow.com/questions/4896104/creating-a-tree-from-self-referential-tables-in-sqlalchemy
    # Creating a tree from self referential tables in SQLalchemy
    # (2) 2017: (1)을 참조하고 마쉬멜로로 해결 : https://stackoverflow.com/questions/34299680/nested-json-from-adjacency-list
    # # create SQLAlchemy object
    # record = db.session.query(Medications). \
    #     options(joinedload_all("children", "children",
    #                            "children", "children",
    #                            "children", "children")).first()
    # (3) 마쉬멜로 -sqlalchemy 예제: https://stackoverflow.com/questions/55534149/how-do-i-produce-nested-json-from-database-query-with-joins-using-python-sqla
    # self.session.query(Parent).options(
    #             joinedload(Parent.children)
    #         ).all()

    # (4) 라인웍스 마쉬멜로 (pagination도 따로 적용) : https://github.com/linewalks/Flask-Skeleton/blob/master/main/schema/board.py

    ## 참고 serialize 방법들: https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json

    ####
