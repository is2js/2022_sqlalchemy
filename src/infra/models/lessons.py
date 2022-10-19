from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

# from .database import Base
from src.infra.config.base import Base


association_table = Table('association', Base.metadata,
                          Column('lesson_id', Integer, ForeignKey('lessons.id')),
                          Column('group_id', Integer, ForeignKey('groups.id')),
                          )

class Lessons(Base):
    __tablename__ = 'lessons'

    id = Column(Integer, primary_key=True)
    lesson_title = Column(String)
    groups = relationship('Groups', secondary=association_table, backref='group_lessons')

    def __repr__(self):
        return f"Lesson [ID: {self.id}, LessonTitle: {self.lesson_title}]"
