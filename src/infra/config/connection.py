from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import db_config


class DBConnectionHandler:
    def __init__(self, echo: bool = False) -> None:
        # self.__connection_string = "mysql+pymysql://root:564123@localhost:3306/cinema"
        self.__connection_string = db_config.DATABASE_URL
        # self.__engine = self.__create_database_engine()
        self.__engine = self.__create_database_engine(echo)
        self.session = None


    def __create_database_engine(self, echo):
        # engine = create_engine(self.__connection_string)
        engine = create_engine(self.__connection_string, echo=echo)

        #### sqlite 인 경우, qeuery 날릴 때마다, 아래 문장을 execute해야, cascade가 정상작동한다
        # 1) many에서 ondelete='cascade' -> # 2) one에서 passive_deletes=True 로만 작동할 수있게 매번 제약조건 날려준다
        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.execute('pragma foreign_keys=ON')

        # if 'sqlite' in self.__connection_string:
        if self.__connection_string.startswith('sqlite'):
            event.listen(engine, 'connect', _fk_pragma_on_connect)

        return engine

    def get_engine(self):
        return self.__engine

    def get_current_session(self):
        Session = sessionmaker(bind=self.__engine)
        return Session

    def __enter__(self):
        Session = sessionmaker(bind=self.__engine)
        self.session = Session()
        # self.session.execute("PRAGMA foreign_keys=ON")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
