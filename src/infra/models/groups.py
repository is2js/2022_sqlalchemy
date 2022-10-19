from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

# from .database import Base
from src.infra.config.base import Base


class Groups(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    group_name = Column(String)
    student = relationship('Students')

    def __repr__(self):
        return f"Group [ID: {self.id}, GroupName: {self.group_name}]"
