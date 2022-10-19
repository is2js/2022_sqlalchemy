from sqlalchemy import text, Table, Column, Integer, String, ForeignKey

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory

from create_database_tutorial import *

if __name__ == '__main__':
    session = Session()

    user_table = Table('user_account', Base.metadata,
                       Column('id', Integer, primary_key=True),
                       Column('name', String(30)),
                       Column('fullname', String),
                       )

    # ForeignKey('테이블 이름.외래 키') 형태로 외래 키 컬럼을 선언할 수 있습니다.
    # -> 이 때 Column 객체의 데이터타입을 생략할 수 있습니다. 데이터타입은 외래 키에 해당하는 컬럼을 찾아서 자동으로 추론
    address = Table('address', Base.metadata,
                    Column('id', Integer, primary_key=True),
                    Column('user_id', ForeignKey('user_account.id'), nullable=False),
                    Column('email_address', String, nullable=False),
                    )

    create_database(load_fake_data=False)

    print('*' * 30)
    print(user_table.c.keys())
    # ['id', 'name', 'fullname']
    print(user_table.c.name)
    # user_account.name
    print(user_table.primary_key)
    # PrimaryKeyConstraint(Column('id', Integer(), table=<user_account>, primary_key=True, nullable=False))

    session.execute(text("select * from user_account"))


    ## 기존DB에 있따면, 객체로 받을 수 있다.
    ## => table = Table( , ,autoload_with=engine)
