from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial2 import *


def get_subs(main):
    sub_list = [main]
    for sub in main.children:
        # sub가 부모로서 자식들 모으기
        # 1) 계층나눠서 모으기 -> 할 필요없음.
        # sub_list.append(get_subs(sub))
        # 2) 자식들이 자식의자식들을 모은 list를 extends로 합쳐서, flat한 list로 모으기
        sub_list += get_subs(sub)
    return sub_list


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
    session.flush()

    #### SQL로 보는 CTE
    # CTE는 개체로 저장되지 않고 쿼리 지속 시간 동안만 존재한다는 점에서 파생 테이블과 비슷하나,
    # => CTE는 파생 테이블과 달리 자체 참조가 가능하며 동일 쿼리에서 여러 번 참조할 수 있다.

    # (1) 정의: https://deep-dive-dev.tistory.com/47
    # -- WITH expression_name의 CTE를 생성한다.
    # WITH expression_name [ ( column_name [,...n] ) ]
    # AS
    # (
    #     CTE_query_definition
    # )
    #
    # -- 이후 expression_name을 마치 테이블명처럼 사용할 수 있다.
    # SELECT <column_list> FROM expression_name

    # (2) 재귀와 CTE
    # SQL문은 일반적으로 recursive 구조를 사용하기 적합하지 않다.
    # 하지만 CTE는 Query 자체를 참조하도록 허용한다.
    # Recursive CTE는 전체 결과 집합을 얻을 때까지 데이터의 하위 집합을 반복적으로 실행하여
    # 계층 구조 데이터나 트리 구조 데이터를 처리할 수 있게 한다.
    # 또한 max_recursive_iterations 옵션을 제공하여 무한루프를 피할 수 있다.
    # 따라서 Recursive CTE을 사용하는 경우는 대부분 [계층적 데이터를 표현]해야 할 때이다.

    # => 우리 프로젝트에서는 화면의 메뉴들을 계층적으로 표현하여 권한에 따라 특정 계층 이하의 메뉴만 노출하기 위해 사용하였었다.

    # 재귀 쿼리는 재귀 CTE를 참조하는 쿼리입니다.
    # 재귀 쿼리는 조직 구조, BOM 등과 같은 계층적 데이터 쿼리와 같은 많은 상황에서 유용합니다
    # WITH RECURSIVE cte_name AS(
    #     CTE_query_definition -- non-recursive term
    #     UNION [ALL]
    #     CTE_query definion  -- recursive term
    # ) SELECT * FROM cte_name;


    # (3) syntax: + https://hyeonukdev.tistory.com/m/164
    # CTE 식은 Anchor part와 Recursive part로 나누어진다.

    # Anchor part가 먼저 호출되어 첫 번째 결과 집합 T0를 만든다.
    # => 비재귀적 용어는 CTE 구조의 기본 결과 집합을 형성하는 CTE 쿼리 정의입니다.
    # ==> 비재귀 항을 실행하여 기본 결과 집합(R0)을 만듭니다.

    # Ti는 입력으로 사용하고, Ti+1은 출력으로 사용하여 Recursive part를 호출한다.
    # => 재귀 용어는 UNION 또는 UNION ALL연산자를 사용하여 비재귀 용어와 결합된 하나 이상의 CTE 쿼리 정의 입니다.
    #    재귀 용어는 CTE 이름 자체를 참조합니다.
    # ==> Ri를 입력으로 사용하여 재귀 항을 실행하여 결과 집합 Ri+1을 출력으로 반환합니다.

    # 더 이상 반환할 결과가 없을 때까지 이를 반복하고 모든 결과를 UNION ALL 한 결과 집합을 반환한다
    # => 종료 확인: 이전 반복에서 반환된 행이 없으면 재귀가 중지됩니다.
    # ==> 빈 집합이 반환될 때까지 2단계를 반복합니다. (종료 확인)
    # ===> UNION 또는 UNION ALL결과 집합 R0, R1, … Rn 의 최종 결과 집합을 반환합니다

    ## => sqlalchemy에선, 출력되는 칼럼명이 필요없으므로 생략한다.
    # WITH RECURSIVE subdepartment AS
    # (
    #     -- non-recursive term: [Anchor part]
    #     SELECT * FROM department WHERE name = 'A'
    #
    #     UNION ALL
    #
    #     -- recursive term: [Recursive part]
    #     SELECT d.* FROM department AS d
    #     JOIN subdepartment
    #     AS sd ON (d.parent_department = sd.id)
    # )
    # SELECT * FROM subdepartment ORDER BY name;

    # (4) 사용이유:https://blog.sengwoolee.dev/m/84
    # - 가독성 : CTE는 가독성을 높이며 쿼리 논리를 모두 하나의 큰 쿼리로 묶는 대신에 문 뒷부분에서 결합되는 여러 CTE를 만듭니다.
    # 이를 통해 필요한 데이터 청크를 가져와 => [최종 SELECT에서 결합]할 수 있습니다.
    #
    # - 뷰 대체 : 뷰를 CTE로 대체할 수 있습니다. 뷰를 만들 수 있는 권한이 없거나 해당 쿼리에서만 사용되어 만들지 않으려는 경우 유용합니다.
    # - 재귀 : CTE를 사용하여 자신을 호출할 수 있는 재귀 쿼리를 만듭니다. 이는 조직도와 같은 계층적 데이터에 대해 작업해야 할 때 편리합니다.
    # - 제한 사항 : 자체 참조(재귀) 또는 비 결정적 함수를 사용하여 GROUP BY 수행과 같은 SELECT 문 제한을 극복합니다.
    # - 순위 : ROW_NUMBER, RANK, NTITLE 등과 같은 순위 함수를 사용하고자 할 때 사용할 수 있습니다.
    #
    # CTE의 유형은 재귀 CTE와 비 재귀 CTE의 두가지 범주로 나눌 수 있습니다.
    # 재귀 CTE는 자신을 참조하는 일반적인 테이블 표현식입니다. 비재귀적 CTE는 자신을 참조하지 않으며 이해하기 쉽습니다.


    # (5) 예시 SQL와 그 과정 설명
    #  [1] https://hyeonukdev.tistory.com/m/164
    # WITH RECURSIVE subordinates AS (
    # 	SELECT
    # 		employee_id,
    # 		manager_id,
    # 		full_name
    # 	FROM
    # 		employees
    # 	WHERE
    # 		employee_id = 2
    # 	UNION
    # 		SELECT
    # 			e.employee_id,
    # 			e.manager_id,
    # 			e.full_name
    # 		FROM
    # 			employees e
    # 		INNER JOIN subordinates s ON s.employee_id = e.manager_id
    # ) SELECT
    # 	*
    # FROM
    # 	subordinates;

    ## 해설:
    # 1. 데이터: ![image-20221026021618734](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221026021618734.png)
    # 2. 비재귀적 용어는 ID가 2인 직원인 기본 결과 집합 R 0을 반환합니다 .
    # => my) 비재귀용어에서, 부모로 사용할 node를 1개를 원본table에서 where로 선택한다
    #        해당테이블의 칼럼들 다 사용한다.
    #  employee_id | manager_id |  full_name
    # -------------+------------+-------------
    #            2 |          1 | Megan Berry
    # 3. 재귀적 용어는 직원 ID 2의 직속 부하를 반환합니다. 이것은 직원  테이블과  부하 직원  CTE 를 조인한 결과입니다 .
    # 재귀 항의 첫 번째 반복은 다음 결과 집합을 반환합니다.
    # => my) 재귀용에선, cte를 자식 alias로서, tableA로 생각하고, 비재귀용어의 table을 부모 tableB로 생각하여
    #        자식.parent_id == 부모.id로 [join]을 통해 자식들 데이터를 가져온 뒤, 매번 union한다.
    # employee_id | manager_id |    full_name
    # -------------+------------+-----------------
    #            6 |          2 | Bella Tucker
    #            7 |          2 | Ryan Metcalfe
    #            8 |          2 | Max Mills
    #            9 |          2 | Benjamin Glover

    # 4. PostgreSQL은 재귀 용어를 반복적으로 실행합니다.
    #    재귀 멤버의 두 번째 반복은 단계 위의 결과 집합을 입력 값으로 사용하고 다음 결과 집합을 반환합니다.
    # => my) 재귀용어가 반복되며, join된 데이터들을 비재귀용어의 부모데이터로 생각하고 다시 cte로 join한다.
    #  employee_id | manager_id |    full_name
    # -------------+------------+-----------------
    #           16 |          7 | Piers Paige
    #           17 |          7 | Ryan Henderson
    #           18 |          8 | Frank Tucker
    #           19 |          8 | Nathan Ferguson
    #           20 |          8 | Kevin Rampling

    # 5. 세 번째 반복은 ID가 16, 17, 18, 19 및 20인 직원에게 보고하는 직원이 없기 때문에 빈 결과 집합을 반환합니다.
    # PostgreSQL은 비재귀 및 재귀 용어에 의해 생성된 첫 번째 및 두 번째 반복의 모든 결과 집합의 합집합인 최종 결과 집합을 반환합니다.
    #  employee_id | manager_id |    full_name
    # -------------+------------+-----------------
    #            2 |          1 | Megan Berry
    #            6 |          2 | Bella Tucker
    #            7 |          2 | Ryan Metcalfe
    #            8 |          2 | Max Mills
    #            9 |          2 | Benjamin Glover
    #           16 |          7 | Piers Paige
    #           17 |          7 | Ryan Henderson
    #           18 |          8 | Frank Tucker
    #           19 |          8 | Nathan Ferguson
    #           20 |          8 | Kevin Rampling
    # (10 rows)

    #### (6) 예시 SQL + SQLALCHEMY 2개
    # [2] https://sanjayasubedi.com.np/python/sqlalchemy/recursive-query-in-postgresql-with-sqlalchemy/
    # with recursive cte as (
    # select
    # 	id, name, level, parent_id
    # from
    # 	categories c
    # where
    # 	c.id = 128
    # 	-- initial selector
    # union
    # select
    # 	c2.id, c2.name, c2.level, c2.parent_id
    # from
    # 	categories c2
    # join cte on
    # 	c2.parent_id = cte.id
    # 	-- recursive part
    # )
    # select
    # 	*
    # from
    # 	cte;

    # topq = sess.query(Category)
    # topq = topq.filter(Category.id == 128)
    # topq = topq.cte('cte', recursive=True)
    #
    # bottomq = sess.query(Category)
    # bottomq = bottomq.join(topq, Category.parent_id == topq.c.id)
    #
    # recursive_q = topq.union(bottomq)
    # q = sess.query(recursive_q)

    # [3] https://spoqa.github.io/2013/08/21/cte.html
    # WITH RECURSIVE subdepartment AS
    # (
    #     -- non-recursive term
    #     SELECT * FROM department WHERE name = 'A'
    #
    #     UNION ALL
    #
    #     -- recursive term
    #     SELECT d.* FROM department AS d
    #     JOIN subdepartment
    #     AS sd ON (d.parent_department = sd.id)
    # )
    # SELECT * FROM subdepartment ORDER BY name;

    # subdepartment = select([
    # 	department.c.id,
    # 	department.c.parent_department,
    # 	department.c.name]).where(department.c.name == 'A') \
    # 	.cte(recursive=True)

    # subd_alias = subdepartment.alias()
    # department_alias = department.alias()
    #
    # subdepartment = subdepartment.union_all(
    # 	select([
    # 		department_alias.c.id,
    # 		department_alias.c.parent_department,
    # 		department_alias.c.name]) \
    # 	.where(department_alias.c.parent_department == subd_alias.c.id))

    # statement = select([
    # 	subdepartment.c.id,
    # 	subdepartment.c.parent_department,
    # 	subdepartment.c.name]).order_by(subdepartment.c.name)



    ## UNION vs UNION ALL
    # 중복 여부의 판단은 SELECT된 튜플들에 속해있는 [모든 컬럼의 값들 자체가 중복 체크의 기준]이 되는 것이다.
    #
    # 자~, 그러면 이제 MySQL이 내부적으로 UNION ALL과 UNION을 처리하는 과정을 알아보자.
    # 1. 최종 UNION [ALL | DISTINCT] 결과에 적합한 임시 테이블(Temporary table)을 메모리 테이블로 생성
    # 2. [UNION 또는 UNION DISTINCT 의 경우, Temporary 테이블의 모든 컬럼으로 Unique Hash 인덱스 생성]
    # 3. 서브쿼리1 실행 후 결과를 Temporary 테이블에 복사
    # 4. 서브쿼리2 실행 후 결과를 Temporary 테이블에 복사
    # 5. 만약 3,4번 과정에서 Temporary 테이블이 특정 사이즈 이상으로 커지면
    #     Temporary 테이블을 Disk Temporary 테이블로 변경
    #     (이때 Unique Hash 인덱스는 Unique B-Tree 인덱스로 변경됨)
    # 6. Temporary 테이블을 읽어서 Client에 결과 전송
    # 7. Temporary 테이블 삭제

    # 결론은,
    # 0. UNION 이든지 UNION ALL이든지 사실 그리 좋은 SQL 작성은 아니다.
    #     UNION이 필요하다는 것은 사실 두 엔터티(테이블)가 하나의 엔터티(테이블)로 통합이 되었어야
    #     할 엔터티들이었는데, 알 수 없는 이유로 분리 운영되는 경우가 상당히 많다.
    #     즉 모델링 차원에서 엔터티를 적절히 통합하여 UNION의 요건을 모두 제거하자.
    # 1. 두 집합에 절대 중복된 튜플(레코드)가 발생할 수 없다는 보장이 있다면 UNION ALL을 꼭 사용하자.
    #     두 집합에서 모두 각각의 PK를 조회하는데, 그 두 집합의 PK가 절대 중복되지 않는 형태
    # 2. 중복이 있다 하더라도 그리 문제되지 않는다면 UNION 보다는 UNION ALL을 사용하자.
    # 3. 만약 UNION이나 UNION ALL을 사용해야 한다면, 최소 필요 컬럼만 SELECT 하자.
