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

    #### 쿼리에서 relationship 사용하기
    # -> relationship() 이 SQL 쿼리 구성을 자동화하는데 도움이 되는 여러 가지 방법을 소개합니다.

    ## 1. relationship()을 사용하여 조인하기
    # - Select.join() 및 Select.join_from() 메서드를 사용하여 SQL JOIN을 구성할 때는,
    #   이러한 메서드는 두 테이블을 연결하는 ForeignKeyConstraint 객체가 있는지 여부에 따라
    #   ON 절을 유추하거나 특정 ON 절을 나타내는 SQL Expression 구문을 제공 할 수 있었다
    # => relationship() 객체를 사용하여 join의 ON 절을 설정할 수 있습니다.
    #    relationship() 에 해당하는 객체는 Select.join()의 단일 인수로 전달될 수 있으며,
    #    right join과 ON 절을 동시에 나타내는 역할을 합니다
    ####  => 즉, select절에는 tableB.칼럼을 이용하되, from TableA  join( TableA.관계B칼럼)

    ## (1) select_from(tableA)있는 상태에서
    # join(tableB) 대신  join(tableA.Brelationship속성)

    stmt = (
        select(Address.email_address)
        .select_from(User)
        .join(User.addresses)
    )
    print(stmt)
    # SELECT address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id
    ## => join에 관계속성의 Entity가 오며, On도 유추해서 간다.
    ## => relationship() 객체를 사용하여 join의 테이블명시 + ON 절을 설정

    #### relationship 속성이 있지만, join()이나 join_from()이 없는 경우는
    #### JOIN될 TableB와 ON을 알아서 유추하지 않는다.
    stmt = (
        select(Address.email_address)
        .select_from(User)
    )
    print(stmt)
    print('*' * 30)
    # SELECT address.email_address
    # FROM address, user_account


    #### select_from(tableA)있는 상태에서 join(tableA.Brelationship속성) 대신
    #### (2)  join_from( tableA, tableA.B관계속성)도 가능하다
    #### => 어떻게든 from tableA가 있고,join에는 tableB대신 B관계속성을 사용하면 된다.
    stmt = (
        select(Address.email_address)
        .join_from(User, User.addresses)
    )
    print(stmt)
    print('*' * 30)
    # SELECT address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id

    #### my) tableB 대신, B관계속성을 join을 걸면되는데
    ####     select_from(tableA)나  join_from( tableA,  )로 from이 지정되어있어야한다.

    ## (3) 만약, B관계칼럼을 지정하지 않으면, FK제약관계에 의한 ON이 자동유추 될 뿐이다.
    ## => B관계칼럼없이도, 알아서 ON을 유추하여 join한다.
    stmt = (
        select(Address.email_address)
        .join_from(User, Address)
    )
    print(stmt)
    print('*' * 30)
    # SELECT address.email_address
    # FROM user_account
    # JOIN address
    # ON user_account.id = address.user_id

