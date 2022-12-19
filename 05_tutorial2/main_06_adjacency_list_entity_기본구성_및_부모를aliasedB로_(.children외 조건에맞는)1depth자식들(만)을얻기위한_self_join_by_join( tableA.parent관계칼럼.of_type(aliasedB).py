from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial2 import *

if __name__ == '__main__':
    create_database()
    session = Session()

    #### self join by aliased
    ## 1. entity는 자식으로서의 부모id를 Fk를 가지면서 동시에 자식들에 대한 부모로서 relationship을 가진다.
    # class Node(Base):
    #     __tablename__ = 'nodes'
    #
    #     id = Column(Integer, primary_key=True)
    #     ## 1. 자신의 부모에 대한 many로 fk를 가진다.
    #     parent_id = Column(Integer, ForeignKey('nodes.id'))
    #     data = Column(String(50))
    #     ## 2. 자신의 자식들에 대한 one으로 relationship을 가진다.
    #     ##    자식들에게는 .parent의 가상속성을 주되,
    #     ##    fk에 대한 pk를 직접 remote_side로 지정해준다?
    #     children = relationship("Node", backref=backref('parent', remote_side=[id]))

    node1 = Node(1)
    node2 = Node(2)
    node3 = Node(3)
    node1.children += [node2, node3]
    print(node1.children)
    # [Node[id=None, parent_id=None, data=2, children=[]], Node[id=None, parent_id=None, data=3, children=[]]]

    ## 관계객체끼리 add하면, 동기화
    print(node2.parent)
    # Node[id=None, parent_id=None, data=1, children=[Node[id=None, parent_id=None, data=2, children=[]], Node[id=None, parent_id=None, data=3, children=[]]]]

    session.add(node1)

    ## flush 전, session.new로 새로 등록될 객체 확인
    ## => add한 node1객체뿐만 아니라, 연결된 node2, node3도 등록됨.
    print(session.new)
    # IdentitySet([
    # Node[id=None, parent_id=None, data=1, children=[Node[id=None, parent_id=None, data=2, children=[]], Node[id=None, parent_id=None, data=3, children=[]]]],
    # Node[id=None, parent_id=None, data=2, children=[]],
    # Node[id=None, parent_id=None, data=3, children=[]]])

    ## flush하면 session.new에선 사라짐. db에 저장되는 persistent상태( db 실제 저장은 안됨)
    ## => flush된 persistent상태 -> pk, fk 배정이 끝나면 session.new에서는 사라진다. 실제 디비저장은 안된다.
    session.flush()
    print(session.new)
    # IdentitySet([])

    ## 관계로 동기화된 객체는 모두 add를 따로 안해도
    ## 1개객체 add하면 flush후 관계객체들 모두 id 배정됨
    print(node1)
    # Node[id=1, parent_id=None, data=1, children=[Node[id=2, parent_id=1, data=2, children=[]], Node[id=3, parent_id=1, data=3, children=[]]]]
    print(node2)
    # Node[id=2, parent_id=1, data=2, children=[]]

    ## 커밋하면.. db저장은? => 동기화된 객체들 모두 db에 저장된다.
    # session.commit()
    # => add한 node1뿐만 아니라, node2, 3도 다 db에 저장됨.
    # 1,null,1
    # 2,1,2
    # 3,1,3
    print('*' * 30)

    #### 기존 관계칼명으로 JOIN() 복습
    #### => join()시 tableB대신 tableA.B관계칼럼으로 대신햇었다.
    # select절에 tableA가 없다면(from유추X), selef_from(tableA).join(tableA.B관계칼럼) OR
    #                                     join_from(tableA, tableA.관계칼럼)
    #     stmt = (
    #         select(Address.email_address) # -> select절에선 tableB.칼럼 자유롭게 사용하다가
    #         .select_from(User)
    #         .join(User.addresses) # -> join(tableB) 대신 tableA.B관계칼럼으로
    #     )

    # select절에 tableA가 있다면(from유추), join(tableA.B관계칼럼)으로 조인햇었다.
    # stmt = (
    #     select(User.name, Addresses.email_address)
    #     .join(User.addresses)
    # )
    #
    # SELECT users.name, addresses.email_address
    # FROM users
    # JOIN addresses ON users.id = addresses.user_id

    # stmt = (
    #     select(Node)
    #     .join(na.parent)
    # )

    #### 2. query시에는 aliased로 테이블을 복제해놓고 조회한다
    na = aliased(Node)

    ## (1) select에는 원본A join()에는 alias B만 올리면, 과도한 ON유추
    ## ON절을 유추하다보니, 2개를 id == fk and  fk == id 다 유추해버린다.
    ## => id == parent_id and parent_id == id 2개를 조건으로 다 걸어버려
    ## => id == parent_id만 필요한데,   자식이면서 && 부모인 것을 붙일려고 하니 아무것도 안나온다.
    # -> alias를 다른 테이블로 인식해서 from에는 원본만 1개 걸리지만, on유추를 시키면 2개의 ON절이 생긴다.
    stmt = (
        select(Node)
        .join(na)
    )
    print(stmt)

    for it in session.scalars(stmt).all():
        print(it)
    print('*' * 30)

    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # JOIN nodes AS nodes_1
    #     ON nodes.id = nodes_1.parent_id AND nodes_1.id = nodes.parent_id

    ## (2) select절에 A,  join()에는 alias B대신 tableA.B관계칼럼을 주고 싶은데
    ##     alias가 등장하지 않는 체, 같은 테이블이라서.. tableA.B관계칼럼으로 join시 에러가 난다
    # sqlalchemy.exc.InvalidRequestError: Can't construct a join from mapped class Node->nodes to mapped class Node->nodes, they are the same entity
    #### => 이럴 때 줄 수 있는 것이 join ( tableA.B관계칼럼.of_type(aliased B) )이다.
    stmt = (
        select(Node)
        # .join(Node.children)
        .join(Node.children.of_type(na))
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it)
    print('*' * 30)

    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # JOIN nodes AS nodes_1
    #     ON nodes.id = nodes_1.parent_id
    # Node[id=1, parent_id=None, data=1, children=[Node[id=2, parent_id=1, data=2, children=[]], Node[id=3, parent_id=1, data=3, children=[]]]]
    # Node[id=1, parent_id=None, data=1, children=[Node[id=2, parent_id=1, data=2, children=[]], Node[id=3, parent_id=1, data=3, children=[]]]]

    #### => 결과가.. 부모객체 1개에 대해, 조건을 만족하는 자식들의 갯수만큼 join되어 복제되어서 나온다.
    ####    부모조건갯수 X 그마다 자식들의 갯수 만큼 누적합

    ## (3) self join시, 부모의 1개에 , 자식도 1개만 걸리게 주면 데이터는 1x1 1개다.
    ## => tableA에는 parent를 1개를 명시, aliased B에는 자식들에 대한 조건을 추가해서 조회하자.
    ## => 부모 객체1개, 자식객체 1개가 나온다.
    stmt = (
        select(Node, na)
        .join(Node.children.of_type(na))
        .where(Node.data == 1) # 부모 조건
        .where(na.data > 1) # 부모에 join된 자식들마다 필터링 조건
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it)
    print('*' * 30)
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes JOIN nodes AS nodes_1 ON nodes.id = nodes_1.parent_id
    # WHERE nodes.data = :data_1 AND nodes_1.data > :data_2
    #   Node[id=1, parent_id=None, data=1]
    #   Node[id=1, parent_id=None, data=1]
    # ******************************





    ## (5) select에는 부모만 있으면 알아서 자식들이 children에 들어가잇을텐데..
    ## => 부모1개에 대해 따라붙은 자식들의 조건을 주면서, 같이 가져오고 싶을 때만..
    ## => join( )  whereA부모조건, where aliasB  자식들에 대한 조건..
    ## => 그래봤자, 부모.children에는 모든 자식들이 들어가있으니 조심.
    ## => 부모1 X 조건만족자식들  카다시안곱이므로.. 만족하는 자식들의 갯수나.. 구할 수 있으려나..

    #### => select에 원본A와 alias B를 각각 올려 조회해도 1개 밖에 결과가 없다.
    #### => 부모와 자식객체들을 동시에 받아보진 못한다.

    #### 어차피 tableA정보밖에 출력이 안되니
    ####  tableA를 여러개가 나올 수 있는 자식들로, aliased B를 parent로 취급한ㄷ ㅟ
    ####  해당 부모에 대한 자식들A를 받아볼 수 있을 것이다.

    #### 그리고, B관계명을 relationship에서 받은 parent로 줘서.. alias를 부모취급하고
    #### 받아볼 수 있는 tableA를, 자식드로 취급해서
    #### 부모조건 -> 해당하는 자식들을 다 받아볼 수 있게 하자.
    parent = aliased(Node)

    #### 부모가 data < 3인, 자식들
    stmt = (
        # select(Node.data) # [1]
        # select(Node.id, na.id, Node.data) # [1]
        select(Node) # [Node[id=1, parent_id=None, data=1]]
        # .where(Node.id == 2)
        # .join(Node.children.of_type(na))
        .join(Node.parent.of_type(parent))
        .where(parent.data <3)
    )

    print(stmt)
    print(session.execute(stmt).all())
    print('*' * 30)
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes JOIN nodes AS nodes_1 ON nodes_1.id = nodes.parent_id
    # WHERE nodes_1.data < :data_1
    # [Node[id=2, parent_id=1, data=2], Node[id=3, parent_id=1, data=3]]


