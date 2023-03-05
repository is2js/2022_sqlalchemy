import _thread
import os

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
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
        # echo = True if os.getenv('APP_CONFIG') != 'production' else False
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

    def __get_db_session(self):
        # 1회성이지만 generator로 만들어야, return후 대기했다가 추가동작을 할 수 있다.
        Session = sessionmaker(bind=self.__engine)
        #### 생성된 세션은 yield로 보내고, 다음 next()호출 전까지는, 대기하며, try/finally를 이용하여
        #### 일단 생성후, 사용되었다면, close()까지 자동으로 되도록 한다.
        # => 즉, yield를 통해 제한없는 무한생성을 해주나, 해줄때마다 close()되게 한다.
        # => 외부에서 닫히면??
        db_session = None
        try:
            db_session = Session()
            yield db_session
        except:
            db_session.rollback()
            raise
        finally:
            # yield 아래쪽은, 다음 next()로 1번씩 호출할 때, 다시 작동된 뒤, 새로 시작하는데
            # => close()를 하고 새 session이 나오게 한다.
            print('자동 close  >> ')

            db_session.close()

    #### property로 만들어야, 함수생성 -> 추가로직을 동시에 바깥에서 ()한번으로 할 수 있다.
    @property
    def get_session(self):
        # return self.__get_db_session().__next__
        return self.get_scoped_session()


    def get_scoped_session(self):
        return scoped_session(sessionmaker(bind=self.__engine, autocommit=False, autoflush=False))

    def __enter__(self):
        Session = sessionmaker(bind=self.__engine)
        self.session = Session()
        # self.session.execute("PRAGMA foreign_keys=ON")
        #
        # # dialect 필드 추가
        # self.DIALECT_NAME = self.session.bind.dialect.name

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def __repr__(self):
        return f"{self.__connection_string}에 연결합니다."


# 아무대서나 get_session()할 수 있도록 객체 선언해놓기
# => 원래는 with DBConnectionHandler() as db:로 사용하려고 했으나
#   try yield -> 대기 -> close가 자동으로 되기 때문에 전역으로서 하나 만들어놓기
# 1) mixin에서 import해서 session생성
# 2) manage에서 import해서 session생성
db = DBConnectionHandler()
