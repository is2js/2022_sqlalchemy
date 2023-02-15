import enum

from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from src.infra.tutorial3.common.base import BaseModel
from src.infra.tutorial3.common.int_enum import IntEnum


class BannerType(enum.IntEnum):
    """defining Banner Types: 0 main용, 1 modal용"""
    MAIN = 0
    MODAL = 1

    # type은 form에서 radio필드의 choices를 지정해줄때, enum.IntEnum의 (.value, .name)을 넘겨줄 수 있도록 메서드를 정의한다.
    # -> 폼에 넘겨준 튜플리스트는 jinja에서 (subfield.data, subfield.label)올 쓰인다.
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


class Banner(BaseModel):
    __tablename__ = 'banners'
    ko_NAME = '배너'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    # 1) 아바타와 달리 반드시 있어야한다. avatar = Column(String(200), nullable=True)
    img = Column(String(200))# nullable=False)
    desc = Column(String(200), nullable=True)
    url = Column(String(300), nullable=True)
    # 2) 원본외 추가칼럼
    banner_type = Column(IntEnum(BannerType), default=BannerType.MAIN, nullable=False)
    # 3) main고정 여부 추가칼럼
    is_fixed = Column(Boolean, default=False, nullable=False)

    #### 예비 칼럼들
    # title/subtitle
    # is_sticky = Column(Boolean(), nullable=False)  # 항상 띄워두어야할 필수 공지냐
    # exp_start_date = Column(DateTime, index=True, default=datetime.datetime.now)
    # exp_end_date = Column(DateTime)

    def __repr__(self) -> str:
        info: str = f"{self.__class__.__name__}" \
                    f"[{self.id} => {self.img}]"
        return info
