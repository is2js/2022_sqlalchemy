from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### Loading relationshiop의 종류
    # 관계 로드 섹션에서는 매핑된 객체 인스턴스로 작업할 때 relationship()을 사용하여
    #   [매핑된 특성에 엑세스]할때야 비로소 이 컬렉션에 있어야 하는 객체를 로드하며,
    #   컬렉션이 채워지지 않은 경우 lazy load가 발생한다는 개념을 도입했습니다.

    # Lazy loading 방식은 가장 유명한 ORM 패턴 중 하나이며, 가장 논란이 많은 ORM 패턴이기도 합니다.
    # 메모리에 있는 수십개의 ORM 객체가 각각 소수의 언로드 속성을 참조하는 경우,
    #   객체의 일상적인 조작은 누적이 될 수 있는 많은 문제(N+1 Problem)를 암묵적으로 방출될 수 있습니다
    #   이러한 암시적 쿼리는 더 이상 사용할 수 없는 데이터베이스 변환을 시도할 때 또는 비동기화 같은 대체 동시성 패턴을 사용할 때
    #   실제로 전혀 작동하지 않을 수 있습니다.
    # N + 1 Problem이란?
    #   쿼리 1번으로 N건의 데이터를 가져왔는데 원하는 데이터를 얻기 위해 이 N건의 데이터를 데이터 수 만큼 반복해서
    #   2차적으로 쿼리를 수행하는 문제입니다.

    # lazy loading 방식은 사용 중인 동시성 접근법과 호환되고 다른 방법으로 문제를 일으키지 않을 때 매우 인기있고 유용한 패턴입니다.
    # 이러한 이유로 SQLAlchemy의 ORM은 이러한 로드 동작을 제어하고 최적화할 수 있는 기능에 중점을 둡니다.

    # 무엇보다 ORM의 lazy loading 방식을 효과적으로 사용하는 첫 번째 단계는 Application을 테스트하고 SQL을 확인하는 것입니다.
    # Session에서 분리된 객체에 대해 로드가 부적절하게 발생하는 경우, Loading relationship의 종류 사용을 검토해야 합니다.

    # Select.options() 메서드를 사용하여 SELECT 문과 연결할 수 있는 객체로 표시됩니다.


   ## 1. select할 때, .options( selectinload ( .b관계속성))을 주면,
    ##    관계속성접근하기도 전에, 이미 관계객체들이 loading되어있다고 한다.
    stmt = (
        select(User)
        .options(selectinload(User.addresses))
    )
    print(stmt)
    for it in session.execute(stmt).scalars():
        print(it.addresses)
    print('*' * 30)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # [Address[id=1, email_address'spongebob@sqlalchemy.org', user_id=1]]
    # [Address[id=2, email_address'sandy@sqlalchemy.org', user_id=2], Address[id=3, email_address'sandy@squirrelpower.org', user_id=2]]
    # [Address[id=8, email_address'patrick@aol.com', user_id=3], Address[id=9, email_address'patrick@gmail.com', user_id=3]]
    # []
    # []
    # [Address[id=4, email_address'pear1.krabs@gmail.com', user_id=6], Address[id=5, email_address'pearl@aol.com', user_id=6]]
    # []
    # ******************************

    ## 2. selectin은 relationship 정의시에 미리 옵션lazy=""으로 줄 수 있다.
    #     addresses = relationship("Address", back_populates="user", lazy="selectin")

    #### 가장 많이 사용되는 loading 방식
    # 옛날기준 설명굿: https://edykim.com/ko/post/getting-started-with-sqlalchemy-part-2/
    #     선행로딩 3가지 방법(옛날 것)
    #      1. 서브쿼리 load / 2. joined load / 3. 명시적 join + 선행로딩: contains_eager
    #      => 여기 튜토리얼에서는 subquery load 대신, selectinload를 소개하고 있다.
    #       joinedload()는 오랜동안 써왔지만 subqueryload() 메소드가 더 새로운 형태의 선행로딩 형태다.
    #       둘 다 한 행을 기준으로 관계된 객체를 가져오는 것은 동일하지만
    #       (1) subqueryload()는 적합한 관계 컬렉션을 가져오기에 적합하고 반면
    #       (2) joinedload()가 다대일 관계에 적합하다.
    #          -> join할 때 사용할 수 있는 방법으로 관계된 객체나 컬렉션을 불러올 때 한번에 불러올 수 있다
    #          -> my) join가능할때.. subquery는 main.칼럼을 where에서 연결하므로 join안해도되니.. pk, fk연결안되어잇을때가능?
    #       (3) contains_eager
    #          -> 다대일 객체를 미리 불러와 동일 객체에 필터링 할 경우에 유용하게 사용된다.
    #          -> my) 동일객체 필터링이 추가되는 경우, joinedload는 join을 한번더 하지만, 이것은 1번만 join한다
    #       (4) raise loading
    #          -> 느리지만, N+1 문제를 완전히 해결
    # 예시코드 블로그: https://leontrolski.github.io/sqlalchemy-relationships.html
    # 장고옵션과 같이보여준다.

    # 1. selectinload
    # - 최신 SQLAlchemy에서 가장 유용한 로딩방식 옵션은 selectinload()입니다.
    #   이 옵션은 관련 컬렉션을 참조하는 객체 집합의 문제인 가장 일반적인 형태의 "N + 1 Problem"문제를 해결합니다
    #   대부분의 경우 JOIN 또는 서브 쿼리를 도입하지 않고 관련 테이블에 대해서만 내보낼 수 있는 SELET 양식을 사용하여 이 작업을 수행합니다.
    #   또한 컬렉션이 로드되지 않은 상위 객체에 대한 쿼리만 수행합니다.

    # 아래 예시는 User 객체와 관련된 Address 객체를 selectinload()하여 보여줍니다.
    # Session.execute() 호출하는 동안 데이터베이스에서는 [두 개의 SELECT 문이 생성]되고
    # 두 번째는 관련 Address 객체를 가져오는 것입니다.
    # from sqlalchemy.orm import selectinload
    # stmt = (
    #    select(User)
    #    .options(selectinload(User.addresses))
    #    .order_by(User.id)
    #  )

    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account ORDER BY user_account.id
    # [...] ()

    # SELECT address.user_id AS address_user_id, address.id AS address_id,
    # address.email_address AS address_email_address
    # FROM address
    # WHERE address.user_id IN (?, ?, ?, ?, ?, ?)
    # [...] (1, 2, 3, 4, 5, 6)


    # 2. Joined Loading 방식 -> 다대일
    # Joined Loading은 SQLAlchemy에서 가장 오래됬으며, 이 방식은 eager loading의 일종으로 joined eager loading이라고도 합니다.
    # N : 1 관계의 객체를 로드하는 데 가장 적합하며, relationship()에 명시된 테이블을
    # SELECT JOIN하여 모든 테이블의 데이터들을 한꺼번에 가져오는 방식으로
    # Address 객체에 연결된 사용자가 있는 다음과 같은 경우에 OUTER JOIN이 아닌 INNER JOIN을 사용할 수 있습니다.
    # >>> from sqlalchemy.orm import joinedload
    # >>> stmt = (
    # ...   select(Address).options(joinedload(Address.user, innerjoin=True)).order_by(Address.id)
    # ... )
    # >>> for row in session.execute(stmt):
    # ...     print(f"{row.Address.email_address} {row.Address.user.name}")
    # SELECT address.id, address.email_address, address.user_id, user_account_1.id AS id_1,
    # user_account_1.name, user_account_1.fullname
    # FROM address
    # JOIN user_account AS user_account_1 ON user_account_1.id = address.user_id
    # ORDER BY address.id
    # [...] ()

    ## joinedload()는 1 : N 관계를 의미하는 컬렉션에도 사용되지만
    # 중접 컬렉션 및 더 큰 컬렉션이므로 selectinload() 처럼
    # 사례별로 평가해야 하는 것과 같은 다른 옵션과 비교 합니다.
    # SELECT 쿼리문의 WHERE 및 ORDER BY 기준은 joinload()에 의해 렌더링된 테이블을 대상으로 하지 않는다는 점에
    # 유의하는 것이 중요합니다. 위 SQL 쿼리에서 직접 주소를 지정할 수 없는 *익명 별칭**이 user_account테이블에 적용된 것을 볼 수 있습니다.
    # 이 개념은 Zen of joined Eager Loading 섹션에서 더 자세히 설명합니다.
    #
    # joinedload()에 의해 ON 절은 이전 ON 조건 확대에서 설명한 방법 joinedload()을 사용하여
    # 직접 영향을 받을 수 있습니다.
    # 참고
    # 일반적인 경우에는 "N + 1 problem"가 훨씬 덜 만연하기 때문에 다대일 열망 로드가 종종 필요하지 않다는 점에 유의하는 것이 중요합니다.
    # 많은 객체가 모두 동일한 관련 객체를 참조하는 경우(예: Address 각각 동일한 참조하는 많은 객체) 일반 지연 로드를 사용하여
    # User객체에 대해 SQL이 한 번만 내보내 집니다. 지연 로드 루틴은 Session가능한 경우 SQL을 내보내지 않고 현재 기본 키로 관련 객체를 조회 합니다.

    ## 3. Explicit Join + Eager load 방식
    # 일반적인 사용 사례는 contains_eager()옵션을 사용하며, 이 옵션은 [JOIN을 직접 설정했다고 가]정하고
    # 대신 COLUMNS 절의 추가 열이 반환된 각 객체의 관련 속성에 로드해야 한다는 점을 제외하고는 joinedload() 와 매우 유사합니다.
    # >>> from sqlalchemy.orm import contains_eager
    #
    # >>> stmt = (
    # ...   select(Address).
    # ...   join(Address.user).
    # ...   where(User.name == 'pkrabs').
    # ...   options(contains_eager(Address.user)).order_by(Address.id)
    # ... )

    # SELECT user_account.id, user_account.name, user_account.fullname,
    # address.id AS id_1, address.email_address, address.user_id
    # FROM address
    # JOIN user_account ON user_account.id = address.user_id
    # WHERE user_account.name = ?
    # ORDER BY address.id
    # [...] ('pkrabs',)

    # 위에서 user_account.name을 필터링하고
    # user_account의 반환된 Address.user속성으로 로드했습니다.
    # joinedload()를 별도로 적용했다면 불필요하게 두 번 조인된 SQL 쿼리가 생성되었을 것입니다.

    # >>> stmt = (
    # ...   select(Address).
    # ...   join(Address.user).
    # ...   where(User.name == 'pkrabs').
    # ...   options(joinedload(Address.user)).order_by(Address.id)
    # ... )
    # >>> print(stmt)  # SE

    # SELECT address.id, address.email_address, address.user_id,
    # user_account_1.id AS id_1, user_account_1.name, user_account_1.fullname
    # FROM address JOIN user_account ON user_account.id = address.user_id
    # LEFT OUTER JOIN user_account AS user_account_1 ON user_account_1.id = address.user_id
    # WHERE user_account.name = :name_1 ORDER BY address.id

    # 참고
    # 관계 로딩 기법의 2가지 기법
    # Zen of joined Eager Loading - 해당 로딩 방식에 대한 세부정보
    # Routing Explicit Joins/Statements into Eagerly Loaded Collections - using contains_eager()


    #### 로더 경로 설정
    # PropComparator.and_() 방법은 실제로 대부분의 로더 옵션에서 일반적으로 사용할 수 있습니다.
    # 예를 들어 sqlalchemy.org도메인에서 사용자 이름과 이메일 주소를 다시 로드하려는 경우
    # selectinload() 전달된 인수에 PropComparator.and_()를 적용하여 다음 조건을 제한할 수 있습니다.

    # >>> from sqlalchemy.orm import selectinload
    # >>> stmt = (
    # ...   select(User).
    # ...   options(
    # ...       selectinload(
    # ...           User.addresses.and_(
    # ...             ~Address.email_address.endswith("sqlalchemy.org")
    # ...           )
    # ...       )
    # ...   ).
    # ...   order_by(User.id).
    # ...   execution_options(populate_existing=True)
    # ... )

    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # ORDER BY user_account.id
    # [...] ()
    # SELECT address.user_id AS address_user_id, address.id AS address_id,
    # address.email_address AS address_email_address
    # FROM address
    # WHERE address.user_id IN (?, ?, ?, ?, ?, ?)
    # AND (address.email_address NOT LIKE '%' || ?)
    # [...] (1, 2, 3, 4, 5, 6, 'sqlalchemy.org')

    # 위에서 매우 중요한 점은 .execution_options(populate_existing=True) 옵션이 추가되었다는 점 입니다.
    # 행을 가져올 때 적용되는 이 옵션은 로더 옵션이 이미 로드된 객체의 기존 컬렉션 내용을 대체해야 함을 나타냅니다.
    # Session객체로 반복 작업하므로 위에서 로드되는 객체는 본 튜토리얼의 ORM 섹션 시작 시 처음 유지되었던 것과 동일한 Python 인스턴스입니다.



    ## 4. raise loading 방식
    # raiseload()옵션은 일반적으로 느린 대신 오류를 발생시켜 N + 1 문제가 발생하는 것을 완전히 차단하는데 사용됩니다.
    # 예로 두 가지 변형 모델이 있습니다. SQL이 필요한 lazy load 와 현재 Session만 참조하면 되는 작업을 포함한
    # 모든 "load" 작업을 차단하는 raiseload.sql_only 옵션입니다.

    #     addresses = relationship("Address", back_populates="user", lazy="raise_on_sql")
    #     user = relationship("User", back_populates="addresses", lazy="raise_on_sql")

    # 이러한 매핑을 사용하면 응용 프로그램이 'lazy loading'에 차단되어 특정 쿼리에 로더 전략을 지정해야 합니다.

    # u1 = s.execute(select(User)).scalars().first()
    # u1.addresses
    # sqlalchemy.exc.InvalidRequestError: 'User.addresses' is not available due to lazy='raise_on_sql'

    # 예외는 이 컬렉션을 대신 먼저 로드해야 함을 나타냅니다.

    # lazy="raise_on_sql" 옵션은 N : 1 관계에도 현명하게 시도합니다.
    # 위에서 Address.user속성이 Address에 로드되지 않았지만 해당 User 객체가 동일한 Session에 있는 경우 "raiseload"은 오류를 발생시키지 않습니다.