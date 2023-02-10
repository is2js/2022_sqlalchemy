from sqlalchemy import text

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial

from create_database_tutorial import *

if __name__ == '__main__':
    create_database(load_fake_data=False)

    session = Session()
    # 1. session으로 execute가 가능하다.
    # 2. text()안에 sql문을 작성한다.
    # 3. column에 타입을 적어주면 된다.
    session.execute(text(
        """
        CREATE TABLE some_table (x int, y int);
        """))

    ## INSERT
    # -> 4. insert에는 VALUES의 인자에 :콜론을 달아놓고, execute 2번째 인자로
    # -> [] 안에 dict로 1줄씩 넣어주면 된다.
    session.execute(text(
        """
        INSERT INTO some_table (x, y) VALUES (:x, :y)
        """
    ), [
        {'x': 11, 'y': 12},
        {'x': 13, 'y': 14},
    ])
    session.commit()

    ## SELECT with param
    # -> stmt는 text( :).bindparams(keywords)로 만들면 된다.
    stmt = text("SELECT x, y FROM some_table WHERE y > :y ORDER BY x, y").bindparams(y=13)
    result = session.execute(stmt)
    print('*' * 30)
    for row in result:
        print(row)

    ## UPDATE -> INSERT처럼, execute의 2번재 인자로 준다.

    session.execute(
        text("UPDATE some_table SET y=:y WHERE x=:x")
        , [
            {'x': 11, 'y': 11},
            {'x': 13, 'y': 11},
        ])

    stmt = text("SELECT * FROM some_table")
    result = session.execute(stmt)
    print('*' * 30)
    for row in result:
        print(row)
