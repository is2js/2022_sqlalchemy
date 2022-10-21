from src.infra.config.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship




class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(ForeignKey('user_account.id'))

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}," \
                    f" email_address{self.email_address!r}," \
                    f" user_id={self.user_id!r}]"
        return info
