from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial2 import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #  데이터 삽입들 삽입
    root = Node('root')
    a = Node('A')
    b = Node('B')
    c = Node('C')
    d = Node('D')
    e = Node('E')
    f = Node('F')
    g = Node('G')
    # ROOT-+->A-+->B-+->C
    #      |         |
    #      |         +->D-+->F
    #      +->E-+->G
    root.children += [a, e]

    a.children.append(b)
    e.children.append(g)

    b.children += [c, d]

    d.children.append(f)

    print(root)
    #  'root'
    #      'A'
    #          'B'
    #              'C'
    #              'D'
    #                  'F'
    #      'E'
    #          'G'
    print('*' * 30)

    session.add(root)
    session.flush()  # pk, fk 배정

    #### 재귀 cte를 통한, A의 하위부서 얻기
    #### 방법1: https://sanjayasubedi.com.np/python/sqlalchemy/recursive-query-in-postgresql-with-sqlalchemy/
    # 1. 비재귀용어용 하위부서를 모을 부모1개를 select하는 것을 만든다.
    # => my) 비재귀용어에서, 부모로 사용할 node를 1개를 원본table에서 where로 선택한다.
    #        해당테이블의 칼럼들 다 사용한다.
    parent = (
        select(Node)
        .where(Node.data == 'A')
    )
    print(parent)
    print('*' * 30)
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # WHERE nodes.data = :data_1
    # ******************************

    # 2. 비재귀용어 부모1개 select절을 +  재귀 cte로 만들어 parent table화 시킨다.
    parent = parent.cte('cte', recursive=True)
    print(parent)
    print('*' * 30)
    print(type(parent))  # <class 'sqlalchemy.sql.selectable.CTE'>
    # => SQL은 그대로
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # WHERE nodes.data = :data_1
    # ******************************

    # 3. 비재귀+재귀cte의 union아래부분에, 사용할, 재귀용어용 자식alias를 만든다
    child = aliased(Node)
    print(child)
    print('*' * 30)
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # WHERE nodes.data = :data_1
    # ******************************

    # 4. 비재귀+재귀cte(CTE객체-Table객체)와 재귀용alias Table를 자식으로보고 select(자식alias Entity). join(cte 부모Table, 자식.parent_id==부모.c.id)한다.
    # -> cte객체는 table객체처럼 .c.로 쓴다. / on절을 유추하지 않게 직접 조건을 준다(유추하면 id==parent_id, parent_id==id 둘다 걸어버림)
    # -> 이 때, 계층형 하위정보를 얻을 땐, 재귀select절이 자식table / join절이 부모table(cte객체)
    # -> 자식에다가 부모를 <- join건다
    child = (
        select(child)
        .join(parent, child.parent_id == parent.c.id)
    )
    print(child)
    print('*' * 30)
    # WITH RECURSIVE cte(id, parent_id, data) AS
    # (SELECT nodes.id AS id, nodes.parent_id AS parent_id, nodes.data AS data
    #  FROM nodes
    #  WHERE nodes.data = :data_1)
    #  SELECT nodes_1.id, nodes_1.parent_id, nodes_1.data
    #  FROM nodes AS nodes_1 JOIN cte ON nodes_1.parent_id = cte.id
    # ******************************

    # 5. parent와 child를 union all한다.
    #  -> distinct 해야할 상황이 아니라면 union all로만 사용
    # => cte에 union_all하면, 그대로 cte객체다.
    table = parent.union_all(child)
    print(table)
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # WHERE nodes.data = :data_1
    # UNION ALL
    # SELECT nodes_1.id, nodes_1.parent_id, nodes_1.data
    # FROM nodes AS nodes_1 JOIN cte ON nodes_1.parent_id = cte.id
    print(type(table))  # <class 'sqlalchemy.sql.selectable.CTE'>

    for it in session.execute(select(table)):
        print(it)
    print('*' * 30)
    # (2, 1, 'A')
    # (4, 2, 'B')
    # (6, 4, 'C')
    # (7, 4, 'D')
    # (8, 7, 'F')
    # ******************************

    print(session.scalars(select(table)).all())
    # [2, 4, 6, 7, 8]

    #### 방법2: https://spoqa.github.io/2013/08/21/cte.html
    # 1. 비재귀(parent by 원본)으로 부모1개를 select 후  -> cte객체 테이블을 만든다.
    parent = (
        select(Node)
        .where(Node.data == 'A')
    ).cte(recursive=True)

    # 2. 원본을 aliased하여 재귀용 child table을 만든다.
    child = aliased(Node)

    # 3.
    # 1) [child + parent를 where로 join]한 뒤 ( where로 조인은 from에 2개의 table이 들어간다 )
    # 2) parent . union_all ( child ) 하여 parent table에 통합한다.

    # 1) select(child).where(child.parent_id == parent.c.id)

    parent = (
        parent
        .union_all(
            select(child)
            .where(child.parent_id == parent.c.id)
        )
    )

    # 4. 통합table을 select + 필요시 order_by한다.
    stmt = (
        select(parent)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # WITH RECURSIVE anon_1(id, parent_id, data) AS
    # (SELECT nodes.id AS id, nodes.parent_id AS parent_id, nodes.data AS data
    #  FROM nodes
    #  WHERE nodes.data = :data_1

    #  UNION ALL

    #  SELECT nodes_1.id AS id, nodes_1.parent_id AS parent_id, nodes_1.data AS data
    #  FROM nodes AS nodes_1, anon_1
    #  WHERE nodes_1.parent_id = anon_1.id)

    #  SELECT anon_1.id, anon_1.parent_id, anon_1.data
    # FROM anon_1

    # (2, 1, 'A')
    # (4, 2, 'B')
    # (6, 4, 'C')
    # (7, 4, 'D')
    # (8, 7, 'F')

    print(session.scalars(stmt).all())
    # [2, 4, 6, 7, 8]
    print(session.execute(stmt).all())
    # [(2, 1, 'A'), (4, 2, 'B'), (6, 4, 'C'), (7, 4, 'D'), (8, 7, 'F')]
    print(session.execute(stmt).scalars().all())
    # [2, 4, 6, 7, 8]

    #### cte를 통한 재귀쿼리는... 객체들을 모으질 못하니.. 재귀메서드로 구현이 더 좋을 수도?
    #### => 재귀메서드로 가면, 횟수만큼 db에 쿼리해서 비효율적이다.

    #### CTE에 level해결책 -> tutorial3로 구성하고 cte날리기기
    # https://www.peterspython.com/en/blog/threaded-comments-using-common-table-expressions-cte-for-a-mysql-flask-blog-or-cms#comments

    # WITH RECURSIVE tree_path (id, thread_created_on, parent_id, text, level, path) AS
    # (
    #   SELECT id, thread_created_on, parent_id, text as text, 0 as level, zpstring_id as path
    #     FROM comment
    #     WHERE
    #           content_item_id = 34
    #       AND parent_id IS NULL
    #   UNION ALL
    #   SELECT t.id, t.thread_created_on, t.parent_id, t.text, tp.level + 1 AS level, CONCAT(tp.path, '/', t.zpstring_id)
    #     FROM tree_path AS tp JOIN comment AS t
    #       ON tp.id = t.parent_id
    # )
    # SELECT * FROM tree_path
    # ORDER BY path;


    # +------+---------------------+-----------+-------------------------------------------+-------+----------------------------+
    # | id   | thread_created_on   | parent_id | text                                      | level | path                       |
    # +------+---------------------+-----------+-------------------------------------------+-------+----------------------------+
    # |  110 | 2020-02-08 20:49:19 |      NULL | first level 0 text                        |     0 | 00000110                   |
    # |  111 | 2020-02-08 20:49:19 |       110 | reply to: first level 0 text              |     1 | 00000110/00000111          |
    # |  112 | 2020-02-08 20:49:19 |       111 | reply to: reply to: first level 0 text    |     2 | 00000110/00000111/00000112 |
    # |  113 | 2020-02-08 20:49:19 |       111 | 2e reply to: reply to: first level 0 text |     2 | 00000110/00000111/00000113 |
    # |  114 | 2020-02-08 20:49:38 |      NULL | second level 0 text                       |     0 | 00000114                   |
    # |  115 | 2020-02-08 20:49:38 |       114 | reply to: second level 0 text             |     1 | 00000114/00000115          |
    # +------+---------------------+-----------+-------------------------------------------+-------+----------------------------+