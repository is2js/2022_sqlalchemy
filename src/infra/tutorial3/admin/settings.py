from sqlalchemy import Column, Integer, String, select, BigInteger

from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler


# class Setting(BaseModel):
class Setting(Base):
    __tablename__ = 'settings'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    setting_key = Column(String(64), index=True, unique=True)
    setting_value = Column(String(800), default='')

    def __repr__(self) -> str:
        return f'{self.id}=>{self.setting_key}'

    # get관련 entity method는 filter(where)에 id를 조회 & select에 entity명을 적어야하는 cls method로 만든다.
    @classmethod
    def to_dict(cls):
        # setting의 모든 data(key, value)를 -> 1개의 dict에 담아서 반환한다
        ret = {}
        with DBConnectionHandler() as db:
            for setting in db.session.scalars(select(cls)):
                ret[setting.setting_key] = setting.setting_value
            return ret

    # get관련으로서, 기존에 값이 존재하는 key는 찾은 뒤 수정할 수 있게 key로 가져온다
    @classmethod
    def get_by_key(cls, key):
        with DBConnectionHandler() as db:
            return db.session.scalars(select(cls).where(cls.setting_key == key)).first()

