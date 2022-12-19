from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload

from create_database_tutorial2 import *


def get_subs(main):
    sub_list = [main]
    for sub in main.children:
        # sub가 부모로서 자식들 모으기
        # 1) 계층나눠서 모으기 -> 할 필요없음.
        # sub_list.append(get_subs(sub))
        # 2) 자식들이 자식의자식들을 모은 list를 extends로 합쳐서, flat한 list로 모으기
        sub_list += get_subs(sub)
    return sub_list


if __name__ == '__main__':
    create_database()
    session = Session()
    ## 0. str으로 출력시, 재귀로 자식들을 모두 표현하도록 정의
    # def __str__(self, level=0):
    #     info: str = f"{'    ' * level} {repr(self.data)}\n"
    #     for child in self.children:
    #         info += child.__str__(level + 1)
    #     return info

    ##### 1. commit하진 않지만, add -> flush -> persitent로서 id, fk배정 받을
    #  데이터 삽입들 삽입
    root = Node('root')
    a = Node('A')
    b = Node('B')
    c = Node('C')
    d = Node('D')
    e = Node('E')
    f = Node('F')
    g = Node('G')
    # ROOT-+->A-+->B-+->C
    #      |         |
    #      |         +->D-+->F
    #      +->E-+->G
    root.children += [a, e]

    a.children.append(b)
    e.children.append(g)

    b.children += [c, d]

    d.children.append(f)

    print(root)
    #  'root'
    #      'A'
    #          'B'
    #              'C'
    #              'D'
    #                  'F'
    #      'E'
    #          'G'
    print('*' * 30)

    ## 관계객체 1개만 add하면, 모두가 session.new에 등록되고
    session.add(root)
    ## flush하면 모두가 persistent객체로서, id, fk가 배정된다.
    session.flush()

    ## (1) A의 바로 아래 하위부서 모두 추출 by .chilren 관계필드
    # -> 바로 아래 부서는 .chilren 부를 수 있따.
    print(a.children)
    # [Node[id=None, parent_id=None, data='B']]
    print('*' * 30)

    ## (2) aliased를 이용한 self join하면, 해당부모 바로  아래 && 조건에 맞는 자식객체들만 불러올 수 있다.
    # -> aliased parent + join( parent관계컬럼 ) 이용한 self_join은, parent에 대한 child드들 1계단 밖에 못가져왔었다.
    parent = aliased(Node)
    stmt = (
        select(Node)
        .join(Node.parent.of_type(parent))
        .where(parent.data == 'A')  # 부모 택1
        .where(Node.data == 'B')  # 자식들 중 조건걸기 <-> .chilren 모둔 자식들
    )
    print(stmt)
    for it in session.scalars(stmt):
        print(it.__repr__())
    print('*' * 30)
    # SELECT nodes.id, nodes.parent_id, nodes.data
    # FROM nodes
    # JOIN nodes AS nodes_1
    #     ON nodes_1.id = nodes.parent_id
    # WHERE nodes_1.data = :data_1

    # Node[id=4, parent_id=2, data='B']

    #### 2. str__처럼, 재귀메서드(depth마다 달라지는 stack변수)로 모으면 안되나?
    ## - 자신의처리 -> 자식들포함 집계할 빈 list에 자신을 모음
    ## - for 자식들처리 -> 돌면서, 자식들을 모음
    ## - 끝처리 -> 다모은 list를 반환.
    # 1) 자신의처리 -> 자식들과 자신을 모아서 부모로 반환해줄 빈 list에 자신을 넣기
    # sub_list = [a]
    # 2) 끝이 정해진 자식들을 돌면서, 자식이 부모가 되어, 자식의 자식들 모으도록 재귀호출
    #    -> 메서드화해서, 자신parent, 자식 children
    # for sub in a.children:
    #     #sub가 부모로서 자식들 모으기
    # 3) 메서드 안에서 자식+자식들 모았으면 끝처리로 return [객체 집계한 list]
    print(get_subs(a))
    # [
    #   Node[id=2, parent_id=1, data='A'],
    #     [
    #       Node[id=4, parent_id=2, data='B'],
    #         [
    #             Node[id=6, parent_id=4, data='C']
    #         ],
    #         [
    #             Node[id=7, parent_id=4, data='D'],
    #                [
    #                    Node[id=8, parent_id=7, data='F']
    #                ]
    #          ]
    #      ]
    # ]
    ## => 자식들 list를 append하지말고 extends
    # [Node[id=2, parent_id=1, data='A'], Node[id=4, parent_id=2, data='B'], Node[id=6, parent_id=4, data='C'], Node[id=7, parent_id=4, data='D'], Node[id=8, parent_id=7, data='F']]



