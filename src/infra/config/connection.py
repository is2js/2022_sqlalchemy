from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import db


class DBConnectionHandler:
    def __init__(self, echo: bool = False) -> None:
        # self.__connection_string = "mysql+pymysql://root:564123@localhost:3306/cinema"
        self.__connection_string = db.DATABASE_URL
        self.__engine = self.__create_database_engine()
        self.session = None

    def __create_database_engine(self):
        engine = create_engine(self.__connection_string)
        return engine

    def get_engine(self):
        return self.__engine

    def get_current_session(self):
        Session = sessionmaker(bind=self.__engine)
        return Session

    def __enter__(self):
        Session = sessionmaker(bind=self.__engine)
        self.session = Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
