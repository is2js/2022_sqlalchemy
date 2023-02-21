from src.infra.config.connection import db


class SessionMixin:
    __abstract__ = True

    # 1. obj의 session처리
    # mixin 7. 이것도 cls메서드로 바꾼다.
    @classmethod
    def _get_session_and_mark_served(cls, session):
        # 새로 만든 session일 경우 되돌려주기(close처리) 상태(cls.served=)를  아직 False상태로 만들어놓는다.

        if not session:
            session, cls.served = db.get_session(), False
            return session

        # 외부에서 받은 session을 받았으면 served로 확인한다.
        cls.served = True
        return session

    # for create_query_obj ->filter_by/create   OR  for  model_obj(update/delete) to session_obj
    # 실행메서드 결과로 나온 순수 model obj 객체들(filter_by안한)의 session 보급
    # mixin 4. 생성자재정의를 없애고 mixin이 setter를 가지고 생성된 객체에 동적 필드를 주입하도록 바꾼다.
    # => 추가로 query까지 생성자에 받던 것을 Optional로 받게 한다.
    # => 추가로 setter가 반영된 객체를 반영하게 하여 obj = cls().setter()형식으로 바로 받을 수 있게 한다.
    # def set_session_and_query(self, session):
    #     if not hasattr(self, '_session') or not self._session:
    #         self._session = self._get_session_and_mark_served(session)
    #         self.query = None  #
    # @classmethod
    # => cls()만들고주입하므로 다시 self 메서드로 변경
    def set_session_and_query(self, session, query=None):
        # mixin 15. filter_by()이후, 세션을 재주입 받는 상황이라면, 우선적으로 주입되어야한다.
        # 1) filter_by이후 session_obj가 되었지만, [외부 세션을 새로 주입] 받는 경우
        # => query는 건들지말고, session만 바꿔야한다.
        # if session :
        #     self._session = session
        #     self.served = True
        #     # filter_by 이후 query를 가진 상태면 query는 보존하고 session만 바꾼다.
        #     self._query = None
        #     return self
        #
        # # 2) session_obj로 처음 변하나는 순간 -> query도 주입받는다?
        # # if not hasattr(self, '_session') :
        # else:
        # self.served = None  # _get_session시 자동 served가 체킹 되지만, 명시적으로 나타내기
        self._session = self._get_session_and_mark_served(session)
        if query is not None:
            self._query = query  #
        return self

    # mixin 11. create에서 사용시 **kwargs를 다 받으므로, 인자에 추가. query
    # def create_query_obj(cls, session, query=None):
    @classmethod
    def create_query_obj(cls, session, query=None, **kwargs):
        obj = cls(**kwargs).set_session_and_query(session, query=query)

        return obj

    @property
    def is_query_obj(self):
        return hasattr(self, '_query') and self._query is not None


    # for filter_by. + model_obj. 둘다 호출될 수있는 메서드 ex> .update / .delete에서 필수
    # => cf) model_obj를 cls()로 만들 땐, .set_session_and_query를 .create_query_obj에서 호출하게 됨.
    #### filter_by/create에서 발생된 query_obj냐 VS model_obj냐에 따라서 알아서 session을 주입한다.
    def set_session(self, session):
        # 1) query_obj가 아니면, 순수model_obj로서, 무조건 session을 주입한다.
        if not self.is_query_obj:
            self.set_session_and_query(session)
        # 2) query_obj인 경우, 새 session이 들어온 경우만 그 session으로 업뎃한다.
        else:
            if session:
                self.set_session_and_query(session)
