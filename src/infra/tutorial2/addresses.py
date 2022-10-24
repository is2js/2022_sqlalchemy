from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from src.infra.config.base import Base


class Addresses(Base):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    email_address = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", backref=backref('addresses', order_by=id))

    ## user에게 준다면
    # class User(Base):
    #     addresses = relationship('Address', order_by="Address.id", backref='user')

    def __init__(self, name, fullname, password):
        self.name = name
        self.fullname = fullname
        self.password = password

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}," \
                    f" email_address{self.email_address!r}," \
                    f" user_id={self.user_id!r}]"
        return info
