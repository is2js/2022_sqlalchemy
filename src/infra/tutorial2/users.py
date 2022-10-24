from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.infra.config.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    fullname = Column(String(50))
    password = Column(String(12))

    # addresses = relationship('Address', order_by ="Address.id", backref='user')

    def __init__(self, name, fullname, password):
        self.name = name
        self.fullname = fullname
        self.password = password

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}," \
                    f" name{self.name!r}," \
                    f" fullname{self.fullname!r}," \
                    f" password={self.password!r}]"
        return info

