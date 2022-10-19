from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from src.infra.config.base import Base

class Filmes(Base):
    __tablename__ = 'filmes'

    title = Column(String(50), primary_key=True)
    genre = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    artists = relationship("Artists", backref="artists", lazy="subquery")

    def __repr__(self):
        return f"Filme (title={self.title}, age={self.age}, artists={self.artists})"
