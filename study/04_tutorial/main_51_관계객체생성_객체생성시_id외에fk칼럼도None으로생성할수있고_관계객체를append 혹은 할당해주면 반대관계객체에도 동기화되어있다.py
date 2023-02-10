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

    #### 관련 개체 작업하기
    # relationship()은 매핑된 두 객체 간의 관계를 정의하며, <자기 참조> 관계라고도 합니다.

    # class User(Base):
    #     __tablename__ = 'user_account'

    # ... Column mappings

    # addresses = relationship("Address", back_populates="user")

    # class Address(Base):
    #     __tablename__ = 'address'

    # ... Column mappings

    # user = relationship("User", back_populates="addresses")

    # 위 구조를 보면 User 객체에는 addresses(복수) 변수, Address 객체에는 user(단수)라는 변수가 있습니다.
    # relationship 객체로 생성되어져 있는 것을 볼 수 있습니다. 이는 실제 데이터베이스에 컬럼으로 존재하는 변수는 아니지만
    # 코드 상에서 쉽게 접근할 수 있도록 하기 위해 설정 되었습니다.
    # 또한 relationship 선언시 파라미터로 back_populates 항목은 반대의 상황 즉, Address 객체에서 User 객체를 찾아 갈 수 있게 해줍니다.

    ## 1. 관계된 객체 사용
    # (1) 새 EntityModel 객체를 생성하면 relationsihp에 적힌 back이 속성으로 나타난다.
    # => session과 연결안된 객체이므로 비어있을 것이다.
    # => list 로 구성된다.
    u1 = User("pkrabs", "Pearl Krabs")
    # print(u1.addresses)
    # []

    # (2) 새 객체의 ManyEntity backref는 list이므로 append로 관계 Entity객체를 만들어 넣어줄 수 있다.
    # (3) 관계 객체를 새로 만들 땐, id뿐만 아니라 fk도 채우지말고 생성한다.
    #### 관계객체는 OneEntity의 id인 fk를 제외하고 생성하자.
    #### => 생성자에서는 넣어줘야했으니, keyword방식으로 생성한다
    #### my) fk를 포함한 생성자는, fk를 맨뒤로 몰아 선택형 keyword로 받도록 하자.
    # a1 = Address("pear1.krabs@gmail.com")
    a1 = Address(email_address="pear1.krabs@gmail.com")
    u1.addresses.append(a1)

    print(u1.addresses)
    # [Address[id=None, email_address'pear1.krabs@gmail.com', user_id=None]]
    #### => OneEntity의 관계속성에 집어넣었지만, fk가 채워지진 않는다.

    #### (4) relation Entity끼리는, [관계객체 append or add]시 객체간 동기화가 일어나서
    ####     한쪽에 넣어줬으면, 다른쪽도 생긴다.
    #### => my) id, fk없는 상태이지만, 객체간 속성동기화가 된다.
    # Address 객체를 인스턴스 User.addresses 컬렉션과 연관시켰다면. 변수 u1 에는 또 다른 동작이 발생하는데,
    # User.addresses 와 Address.user 관계가 동기화 되어
    # User 객체에서 Address 이동할 수 있을 뿐만 아니라
    # Address 객체에서 다시 User 객체로 이동할 수도 있습니다
    # => a1의 관계속성에도 user가 들어가잇게 된다.. 신기!
    print(a1.user)
    # User[id=None, name'pkrabs', fullname='Pearl Krabs']
    # => 두개의 relationshiop() 객체 간의 relationship.back_populates 을 사용한 동기화 결과입니다.


    ## (5) 반대방향으로도 해보자.
    ##     address에서는 생성시, 이미 생성된 user객체르 넣어주면, user에도 동기화된다.

    # a2 = Address(email_address="pearl@aol.com", user=u1)

    ## => oneentity관계속성은 list가 아니라 1개의 값이므로, 객체 생성시 할당으로 넣어줄 수 있다.
    a2 = Address(email_address="pearl@aol.com")
    a2.user = u1

    ## -> a2생성시 u1를 추가해줬으면, u1의 관계속성(address)에 동기화되어있다.
    print(u1.addresses)
    # [Address[id=None, email_address'pear1.krabs@gmail.com', user_id=None],
    # Address[id=None, email_address'pearl@aol.com', user_id=None]]





