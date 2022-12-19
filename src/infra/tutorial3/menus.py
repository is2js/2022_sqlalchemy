import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref

from src.infra.config.base import Base

# https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy
from src.infra.config.connection import DBConnectionHandler


class Menu(Base):
    __tablename__ = 'menus'
    _N = 3

    id = Column(Integer, primary_key=True)
    # category = Column(String(140))
    title = Column(String(140))
    icon = Column(String(32))
    # endpoint = Column(String(32))
    has_img = Column(Boolean())
    # img_url = Column(String(50))
    timestamp = Column(DateTime(), default=datetime.datetime.now, index=True)
    ####  group gatecogry 칼럼 == thread_gatecogry
    ### => 최상위레벨 기준으로 정렬되는 칼럼으로 해야한다.. category로 했다간.. 카테고리정렬이되어.. 생성 순서대로 안나온다.
    thread_timestamp = Column(DateTime())

    # 23. 그룹별 / level별 / 따로 [변경가능한 level별메뉴순서]를 칼럼으로 새로 만든다.
    # => 외부에서 전체조회시 order_by( 그룹칼럼, level칼럼, level_seq칼럼)순으로 모은다
    # - unique를 준다면, 변경시 에러날 것 같아서 안줌.
    level_seq = Column(Integer)

    # 24. 자신만의 마지막 tempalte_name과, setter로 부모껏과 함꼐 만들어질 name
    template_name = Column(String(40))
    # 25. thread_timestamp처럼 save에서 만들어진다.
    full_template_name = Column(String(100))
    # 27. level_seq를 나타내줄 칼럼



    parent_id = Column(Integer, ForeignKey(id, ondelete='CASCADE'))
    submenus = relationship('Menu'
                           , backref=backref('parent', remote_side=[id], passive_deletes=True)
                           , cascade="all"  # [3] backref가 아닌, replies 자신에게 준다
                           , join_depth=3  # 필수1
                           , lazy='subquery'  # 필수2
                           )
    path = Column(Text, index=True)

    ## 21.
    @hybrid_property
    def level(self):
        return len(self.path) // self._N - 1

    ## 22. 이것까지 줘야 계측칼럼도 정렬할 수 잇음. by classmethod로서 entity를 cls로 이용
    ## if return return일 경우 case문으로 처리
    ## len(self.필드) => func.length(cls.필드) , 나누기 -> func.div -> sqlite에선 지원안함.
    @level.expression
    def level(cls):
        # 0 division 가능성이 있으면 = (cls.path / case([(cls._N == 0, null())], else_=cls.colC)
        # /는 지원되나 //는 지원안됨. func.round()써던지 해야할 듯.?
        return func.length(cls.path) / cls._N - 1


    def save(self):
        with DBConnectionHandler() as db:
            db.session.add(self)
            db.session.flush()

            prefix = self.parent.path if self.parent else ''
            self.path = prefix + f"{self.id:0{self._N}d}"

            self.thread_timestamp = self.parent.thread_timestamp if self.parent else self.timestamp

            # 26. category는 path로 대체할 수 있으니 삭제한다?
            #    endpoint도 같이 삭제하고 template_name으로 대체한다.
            self.full_template_name = (self.parent.full_template_name + '_' + self.template_name) if self.parent else self.template_name

            db.session.commit()

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}," \
                    f" category={self.category!r}," \
                    f" title={self.title!r}," \
                    f" endpoint={self.endpoint!r}," \
                    f" level_seq={self.level_seq!r}," \
                    f" level={self.level!r}]"
        return info
