from typing import Any

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from src.infra.config.base import Base


class Node(Base):
    __tablename__ = 'nodes'

    id = Column(Integer, primary_key=True)
    ## 1. 자신의 부모에 대한 many로 fk를 가진다.
    parent_id = Column(Integer, ForeignKey('nodes.id'))
    data = Column(String(50))
    ## 2. 자신의 자식들에 대한 one으로 relationship을 가진다.
    ##    자식들에게는 .parent의 가상속성을 주되,
    ##    fk에 대한 pk를 직접 remote_side로 지정해준다?
    children = relationship("Node", backref=backref('parent', remote_side=[id]))

    def __init__(self, data) -> None:
        self.data = data

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}," \
                    f" parent_id={self.parent_id!r}," \
                    f" data={self.data!r}]" \
                    # f" children={self.children!r}]"
        return info

    ## str에 재귀_with_depth -> padding를 이용하여
    ## children compoiste객체를 출력 하기
    ## 1) 메서드자체는 재귀함수로서, level(depth)를 가지고 있어야하며
    ##    최초호출은 default=0을 줘서, print(객체)만으로 외부0을 같이 입력했다고 가정하고 시작한다.
    def __str__(self, level=0):
        ## 2) 자신의 처리는 현재dpeth * padding + repr를 모은다
        ##    끝이 있으면서 알아서 종료되므로 종착역은 없다
        info: str = f"{'    ' * level} {repr(self.data)}\n"
        for child in self.children:
            ## 3) children을 돌면서,depth + 1한  __str__를 재귀 호출하여 자신의처리 + 자식들처리가 완료된 string을 return받는다.
            info += child.__str__(level + 1)
        ## 자신의 처리 + 자식들처리에 대해 끝처리를 해준다.
        return info

