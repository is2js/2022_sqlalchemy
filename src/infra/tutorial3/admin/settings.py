from sqlalchemy import Column, Integer, String, select, BigInteger

from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler, db

# class Setting(BaseModel):
from src.infra.tutorial3.mixins.crudmixin import CRUDMixin


class Setting(Base, CRUDMixin):
    __tablename__ = 'settings'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    setting_key = Column(String(64), index=True, unique=True)
    setting_value = Column(String(800), default='')


    # get관련 entity method는 filter(where)에 id를 조회 & select에 entity명을 적어야하는 cls method로 만든다.
    @classmethod
    def convert_to_dict(cls):
        # setting의 모든 data(key, value)를 -> 1개의 dict에 담아서 반환한다
        ret = {}
        for setting in cls.all():
            ret[setting.setting_key] = setting.setting_value
        return ret

    # get관련으로서, 기존에 값이 존재하는 key는 찾은 뒤 수정할 수 있게 key로 가져온다
    @classmethod
    def get_by_key(cls, key):
        with DBConnectionHandler() as db:
            return db.session.scalars(select(cls).where(cls.setting_key == key)).first()

# BaseModel을 상속안하므로, 똑같이 session 삽입(임시)
# temp
Setting.set_scoped_session(db.get_scoped_session())
# Setting.set_engine(db.get_engine())