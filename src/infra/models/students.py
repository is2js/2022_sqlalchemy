from typing import List

from sqlalchemy import Column, String, Integer, ForeignKey

# from .database import Base
from src.infra.config.base import Base

class Students(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    surname = Column(String)
    name = Column(String)
    patronymic = Column(String)
    age = Column(Integer)
    address = Column(String)
    group = Column(Integer, ForeignKey('groups.id'))

    # model의 init은 필드 정의하고 받아도 된다.
    # 입력은 fullname으로 받고, 짤라서 필드에 배정한다. 사용자편의?!
    def __init__(self, full_name: List[str], age: int, address: str, id_group: int):
        self.surname = full_name[0]
        self.name = full_name[1] if len(full_name) > 1 else None
        self.patronymic = full_name[2] if len(full_name) > 2 else None
        self.age = age
        self.address = address
        self.group = id_group

    def __repr__(self):
        info: str = f"Student [name: {self.surname} {self.name} {self.patronymic}, " \
            f"age: {self.age}, adress: {self.address}, ID group: {self.group} ]"
        return info


