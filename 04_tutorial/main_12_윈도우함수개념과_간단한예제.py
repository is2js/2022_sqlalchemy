from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### 윈도우 함수
    # GROUP BY와 비슷한 함수이고 행간의 관계를 쉽게 정의 하기 위해 만든 함수
    # 참고블로그: https://mizykk.tistory.com/121
    # -> Group By는 집계된 결과만 보여주는 반면, 윈도우함수는 기존 데이터에 집계된 값을 추가하여 나타낸다.

    ## SQL
    # 함수(함수_적용_열) OVER (PARTITION BY 그룹열 ORDER BY 순서열)
    # PARTITION BY : Group By와 같은 기능
    # ORDER BY : Order By와 같은 기능(DESC : 내림차순)
    # ex) 국가별 profit의 합
    # - 윈도우함수 : SELECT SUM(profit) OVER (PARTITION BY country) FROM table
    # - Group By : SELECT SUM(profit) FROM table GROUP BY country

    # 1. 집계 -> max/min/count가 아닌 sum은, partition by를 안써주면, 모든 행에 대해 누적합 한다
    #    SUM() : 합 / MIN() : 최소값 / MAX() : 최대값 / AVG() : 평균 / COUNT() : 갯수
    # 2. 순위 ->
    # 1) ROW_NUMBER() : 중복 없는 순위. 행 번호
    # 2) RANK() : 중복 가능. 공동순위만큼 건너뛴다.
    # 3) DENSE_RANK()
    #    - 중복가능
    #    - 공동순위가 있더라도 1, 2, 3 순차적으로 순위가 매겨진다.
    #    - 동일한 순위는 하나의 순위로 취급
    # 4) ORDER BY로 순위 칼럼을 지정한다.
    # SELECT val
    #     -- 행 번호
    #     , ROW_NUMBER() OVER (ORDER BY val) AS 'row_number'
    #     -- 순위
    #     , RANK() OVER (ORDER BY val) AS 'rank'
    #     -- 순위 : 순차적
    #     , DENSE_RANK() OVER (ORDER BY val) AS 'dense_rank'
    # FROM table
    # 3. 데이터 위치 바꾸기
    # 1) LAG(열, n, 결측값 채울 값) : n칸 미루기
    # - LAG(열, n) OVER (PARTITION BY 그룹열 ORDER BY 순서열)
    # 2) LEAD(열, n, 결측값 채울 값) : n칸 당기기
    # - LEAD(열, n) OVER (PARTITION BY 그룹열 ORDER BY 순서열)
    # SELECT Id
    #     , RecordDate  -- ORDER 열
    #     , Temperature  -- 대상 열
    #     -- 미루기
    #     , LAG(Temperature) OVER (ORDER BY RecordDate) AS 'lag'
    #     -- 당기기
    #     , LEAD(Temperature) OVER (ORDER BY RecordDate) AS 'lead'
    # FROM table

    ## SQLALCHEMY
    # SQLAlchemy에서는, func 네임스페이스에 의해 생성된 모든 SQL 함수 중 하나로 OVER 구문을 구현하는 FunctionElement.over() 메서드가 있습니다.
    # 윈도우 함수 중 하나로 행의 개수를 세는 row_number() 함수가 있습니다.
    # 각 행을 사용자 이름대로 그룹을 나누고 그 안에서 이메일 주소에 번호를 매길 수 있습니다

    ## 0. sqlite3.dll  -> sqlite 3.25부터 제공한다?!
    # 1. https://sqlite.org/download.html
    # 2. x64 검색 -> sqlite-dll-win64-x64-3390400.zip 다운로드
    # 3. python 설치 경로 확인
    #    python -m site --user-site
    # 3. 실행에서 %appdata%   local/programs/python/버전/Dlls에 있는 sqlite3.dll를 변경해해주세요

    ## 1. func.row_number() -> 단독으로는 못쓰고 row_number().over()가 기본문법이다.
    # stmt = (
    #     select(func.row_number())
    #     .select_from(User)
    # )
    # sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) misuse of window function row_number()

    stmt = (
        select(func.row_number().over())
        .select_from(User)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # ***************DATABASE_URL: sqlite:///tutorial.db***************
    # SELECT row_number() OVER () AS anon_1
    # FROM user_account
    # (1,)
    # (2,)
    # (3,)
    # ******************************

    ## - user네임별 행번호 매기기면서, email 뽑기
    stmt = (
        select(
            func.row_number().over(partition_by=User.name),
            User.name,
            Address.email_address
        )
        .select_from(User)
        .join(Address)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT row_number() OVER (PARTITION BY user_account.name) AS anon_1, user_account.name, address.email_address
    # FROM user_account JOIN address ON user_account.id = address.user_id
    # (1, 'sandy', 'sandy@sqlalchemy.org')
    # (2, 'sandy', 'sandy@squirrelpower.org')
    # (1, 'spongebob', 'spongebob@sqlalchemy.org')
    # ******************************
    
    
    ## 2. count().over(order_by=)로 name별 갯수를 데이터마다 표기하되, 점점 누적된다.
    stmt = (
        select(
            func.count().over(order_by=User.name),
            User.name,
            Address.email_address
        )
        .select_from(User)
        .join(Address)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT count(*) OVER (ORDER BY user_account.name) AS anon_1, user_account.name, address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id
    # (2, 'sandy', 'sandy@sqlalchemy.org')
    # (2, 'sandy', 'sandy@squirrelpower.org')
    # (3, 'spongebob', 'spongebob@sqlalchemy.org')
    # ******************************

    ## count().filter()는 집계를 안하고도, 특정칼럼의 값별로 갯수를 세어준다
    stmt = (
        select(
            func.count(Address.email_address).filter(User.name == 'sandy'),
            func.count(Address.email_address).filter(User.name == 'spongebob'),
        )
        .select_from(User)
        .join(Address)
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT count(address.email_address) FILTER (WHERE user_account.name = :name_1) AS anon_1, count(address.email_address) FILTER (WHERE user_account.name = :name_2) AS anon_2
    # FROM user_account JOIN address ON user_account.id = address.user_id
    # (2, 1)
    # ******************************

