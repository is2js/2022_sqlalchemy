from .base import Base
from .connection import DBConnectionHandler

conn = DBConnectionHandler()
engine = conn.get_engine()

Session = conn.get_current_session()


def create_db():
    Base.metadata.create_all(engine)
