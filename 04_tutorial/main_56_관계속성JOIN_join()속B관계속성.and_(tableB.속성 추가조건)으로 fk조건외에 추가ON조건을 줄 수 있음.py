from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### relation()으로 ON 조건 확대
    # 관계된 경로에 대한 특정 조인의 범위를 신속하게 제한하는 방법뿐만 아니라 마지막 섹션에서 소개하는 로더 전략 구성과 같은 사용 사례에도 유용
    # PropComparator.and_() 메서드는 AND를 통해 JOIN의 ON 절에 결합되는 일련의 SQL 식을 위치적으로 허용합니다. 예를 들어,
    # User 및 Address을 활용하여 ON 기준을 특정 이메일 주소로만 제한하려는 경우 이와 같습니다.

    ## 1. relation()으로 ON 조건 확대
    ## (1) join에 .B관계속성으로 On을 유추하고난 뒤, 관계속성(PropComparator).and_로 fk외에 추가ON조건을 tableB로 조건을 걸 수 있다.
    stmt = (
        select(User.fullname)
        .join(User.addresses.and_(Address.email_address == 'pear1.krabs@gmail.com'))
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # JOIN address
    #     ON user_account.id = address.user_id  => 관계속성으로 ON 유추
    #     AND address.email_address = :email_address_1 => 관계속성.and_()로 ON 조건 추가가
    # ('Pearl Krabs',)
    # ******************************
