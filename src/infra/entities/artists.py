from src.infra.config.base import Base
from sqlalchemy import Column, String, Integer, ForeignKey


class Artists(Base):
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    title_filmes = Column(String(50), ForeignKey("filmes.title")) # FK의 tablename.pkColumn

    def __repr__(self):
        return f"Artists (name={self.name}, filme={self.title_filmes})"
