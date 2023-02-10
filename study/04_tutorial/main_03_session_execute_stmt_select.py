from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial

# user_account
# 1,spongebob,Spongebob Squarepants
# 2,sandy,Sandy Cheeks
# 3,patrick,Patrick Star

# address
# 1,tingstyle1@gmail.com,1
# 2,daisy0702@gmail.com,2

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    ## 1. ORM으로 생성했다면, 모델.__table__로 테이블 정보를 확인할 수 있따.
    print('*' * 30)
    print(User.__table__)
    # user_account

    #### SELECT
    ## 2. session.execute( )에 text("SQL") 대신 select() 를 구성할 수 있다.
    ## => select는 1개라도 entity 가 들어가면, FROM에 자동 세팅되고, select()안에 필드로 SELECT절을 구성한다.

    # print(select(User))
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account

    stmt = select(User).where(User.name == 'spongebob')
    print('*' * 30)
    for it in session.execute(stmt):
        print(it)

    ## select절에 2개 entity를 놓고, where에 조건을 주면, join과 같은 효과를 둔다.
    ## => 여러테이블을 하나의 테이블처럼 사용하는 조인방법이라고 한다.
    ## => 케사디안 곱으로 모든 경우의수가 나열되며, where로 fk 조건을 준다.
    ## => 다대다에서도 비슷했다.
    # ## 6) 다대다 관계의 테이블을 2개를 특정 칼럼만 찍히게 올리되
    # ## => filter로 관계테이블.c를 통해 일치시킨다?
    # ## => m x n 조합 중에, 관계테이블에서 서로 일치하는 것만 나올 것이다.
    # for it, gr in session.query(Lessons.lesson_title, Groups.group_name).filter(and_(
    #         association_table.c.lesson_id == Lessons.id,
    #         association_table.c.group_id == Groups.id,
    # )):
    #    print(it, gr)
    # print('*' * 30)
    stmt = select(User.name, Address)\
        .where(User.id == Address.user_id)\
        .order_by(Address.id)
    # SELECT user_account.name, address.id, address.email_address, address.user_id
    # FROM user_account, address
    # WHERE user_account.id = address.user_id ORDER BY address.id
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)

    print('*' * 30)
    print(session.execute(stmt).all())
    ## => select절에 entity를 칼럼활용안하면, 객체자체가 뽑아져 나온다.
    # [('spongebob', Address[id=1, email_address'tingstyle1@gmail.com', user_id=1])]


    #### SELECT절에 라벨링  ||연산 이용하기 (라벨링된 SQL 표현식 조회하기)
    ## => 칼럼마다 .label("")을 붙여주면 칼럼별이 된다.
    ## => 칼럼마다 () 괄호안에서 문자열을 더해주면, || 연산으로 값에 같이 찍혀서 나온다.
    print('*' * 30)
    stmt = select((User.name).label('username')).order_by(User.name)
    print(stmt)
    # SELECT user_account.name AS username
    # FROM user_account ORDER BY user_account.name
    print('*' * 30)
    stmt = select(("Username: " + User.name).label('username')).order_by(User.name)
    print(stmt)
    # SELECT :name_1 || user_account.name AS username
    # FROM user_account ORDER BY user_account.name
    for it in session.execute(stmt):
        print(it)
    # ('Username: spongebob',)

    #### 실제 라벨링한 값으로 접근하려면 칼럼명을 라벨링값으로 줘야한다.
    for it in session.execute(stmt):
        print(it.username)
    # Username: spongebob



    #### 문자열 컬럼 만들어 조회하기 -> literal_column
    # SELECT 'some_phrase', name FROM user_account
    # (1) text()를 이용해서 sql구문으로서 ''작은따옴표안에 넣어주기
    # => 그 결과, 출력물에도 어쩔 수 없이 작은 따옴표가 전부 붙어서 나옵니다.
    stmt = select(text("'some phrase'"), User.name).order_by(User.name)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    # SELECT 'some pharse', user_account.name
    # FROM user_account ORDER BY user_account.name
    # ('some pharse', 'spongebob')

    # (2)text()보다 literal_column()을 사용해 작은 따옴표가 결과물에 붙어져서 나오는 문제를 해결할 수 있습니다.
    # => literal_column()은 명시적으로 컬럼을 의미하고, 서브쿼리나 다른 SQL 표현식에서 쓰일 수 있게 라벨링도 할 수 있습니다.
    # => 컬럼이라 .label()도 가능하므로 -> .p로 라벨링칼럼으로 접근해서 작은따옴표를 없앤다
    stmt = select(literal_column("'some phrase'").label('p'), User.name).order_by(User.name)
    print('*' * 30)
    print(stmt)
    for it in session.execute(stmt):
        print(it)

    for it in session.execute(stmt):
        print(it.p, it.name)

    # SELECT 'some phrase' AS p, user_account.name
    # FROM user_account ORDER BY user_account.name
    # ('some phrase', 'spongebob')
    # some phrase spongebob


    #### WHERE
    ## where절을 통한 join구현 + where조건하나 더 주기
    ## => where절 2개는 체이닝 + , 파라마티터 추가 + and_ 로도 가능하다







