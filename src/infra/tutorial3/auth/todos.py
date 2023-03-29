import datetime
import enum

from sqlalchemy import Column, Integer, BigInteger, ForeignKey, String, Date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from src.infra.tutorial3.common.base import BaseModel
from src.infra.tutorial3.common.int_enum import IntEnum


class TodoType(enum.IntEnum):
    개인 = 0
    그룹 = 1

    # form을 위한 choices에는, 선택권한을 안준다? -> 0을 value로 잡아서 제외시킴
    # @classmethod
    # def choices(cls):
    #     return [(choice.value, choice.name) for choice in cls if choice.value]

    @classmethod
    def is_personal(cls, type):
        return cls.개인.value == type

    @classmethod
    def is_group(cls, type):
        return cls.그룹.value == type


class Todo(BaseModel):
    __tablename__ = 'todos'
    ko_NAME = '할일'

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)

    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    employee = relationship('Employee',
                          foreign_keys=[employee_id],
                          uselist=False,
                          back_populates='todos'
                          )

    todo = Column(String(1000), nullable=True)

    type = Column(IntEnum(TodoType), nullable=False, index=True)

    target_date = Column(Date, nullable=True)

    complete_date = Column(Date, default=None)

    @hybrid_property
    def remain_days(self):
        # 타겟데이가 없으면, None 반환 -> 기한 '-'으로 표시
        if self.target_date is None:
            return None

        # 타겟데이가 있으면 -> remain_days가 int로 반환
        today = datetime.date.today()

        delta = self.target_date - today
        return delta.days
