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

    #### 관계객체 로딩
    # (1) 1개  EntityModel객체만 로딩하면, 관계객체관련된 SQL은 작성안된다.
    stmt = (select(User).where(User.id == 6))
    print(stmt)
    u1 = session.execute(stmt).scalar_one()
    print(u1)
    # SELECT user_account.id, user_account.name, user_account.fullname
    # FROM user_account
    # WHERE user_account.id = :id_1
    # User[id=6, name'pkrabs', fullname='Pearl Krabs']

    # (2) 관계속성에 접근하면, 관계객체가 그제서야 관계객체가 나온다.
    print(u1.addresses)
    # [Address[id=4, email_address'pear1.krabs@gmail.com', user_id=6],
    #  Address[id=5, email_address'pearl@aol.com', user_id=6]]

    #### u1.addresses 에 연결된 객체들에도 id가 들어와있는 것을 볼 수 있습니다.
    #### => 해당 객체를 검색하기 위해 우리는 lazy load 방식으로 볼 수 있습니다.
    #### lazy loading : 누군가 해당 정보에 [접근하고자 할때 그때 SELECT문을 날려서 정보를 충당]하는 방식.
    #    => 즉, 그때그때 필요한 정보만 가져오는 것입니다.
    # SELECT address.id AS address_id, address.email_address AS address_email_address,
    # address.user_id AS address_user_id
    # FROM address
    # WHERE ? = address.user_id
    # [...] (6,)

    #### SQLAlchemy ORM의 기본 컬렉션 및 관련 특성은 lazy loading 입니다.
    # 즉, 한번 relationship 된 컬렉션은 데이터가 메모리에 존재하는 한 계속 접근을 사용할 수 있습니다.
    #### lazy loading은 최적화를 위한 명시적인 단계를 수행하지 않으면 비용이 많이 들 수 있지만,
    #    적어도 lazy loading은 중복 작업을 수행하지 않도록 최적화되어 있습니다.









