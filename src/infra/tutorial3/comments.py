# import datetime
#
# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, select, cast, null
# from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy.orm import relationship, backref
#
# from src.infra.config.base import Base
#
# # https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy
# from src.infra.config.connection import DBConnectionHandler
#
#
# #### 부모인 경우(자식을 가지는 경우) 삭제 금지 case
# # https://stackoverflow.com/questions/55968951/sqlalchemy-fk-ondelete-does-not-restrict
#
#
# class Comment(Base):
#     __tablename__ = 'comments'
#     _N = 6
#
#     id = Column(Integer, primary_key=True)
#     text = Column(String(140))
#     # 원래는 fk로 줘야할 듯.
#     author = Column(String(32))
#     # 시간관련은 외부입력없이 자동입력되기 위해 default= datetime.datetime.now와 , index=True를 통해 검색을 빠르게 만들어준다.
#     # => 서버시간 기준으로 하기 위함은 server_default=func.now()로 주면 된다.
#     timestamp = Column(DateTime(), default=datetime.datetime.now, index=True)
#     ## 1. 자기자신과 같은 종류를 품고 있는 [인접 리스트]로 대댓글 구현
#     ## => 자식입장에서 구현
#     # 1) 자식들로서 fk(parent_id)를 나 자신의 id로 가지고 있다.
#     # parent_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'))
#     parent_id = Column(Integer, ForeignKey(id, ondelete='CASCADE'))
#     # , unique=True)
#     # 2) 부모로서 자식들을 relationship으로 가질 수 있다.
#     #    => 이 때, bacref에 remote_side = []에 내 id(pk)칼럼을 배정하기 위해
#     #       backref='parent' 문자열 관계명 대신 backref=backref()객체에 옵션을 같이 준다.
#     #       부모로서는, 자식들을 데이터를 eager-loading 하지 않는다?!
#     replies = relationship('Comment'
#                            # , backref=backref('parent', remote_side=[id]) #, lazy='dynamic') -> to one 관계에선 지원안한다고 나옴. uselist 여부를 무러봄
#                            , backref=backref('parent', remote_side=[id], passive_deletes=True)
#                            # orphan은 many -> to relationship에서는 주면 안된다? one에서 줘서, one만 삭제 가능하게 한다?
#                            # ->delete-orphan cascade is normally configured only on the "one" side of a one-to-many relationship, and not on the "many" side of a many-to-one or many-to-many relationship.  To force this relationship to allow a particular "Comment" object to be referred towards by only a single "Comment" object at a time via the Comment.parent relationship, which would allow delete-orphan cascade to take place in this direction, set the single_parent=True flag. (Background on this error at: https://sqlalche.me/e/14/bbf0)
#                            # (1) delete는 부모가 삭제될 때 자식이 삭제되도록 하고,
#                            # (2) delete-orphan은 부모가 삭제되지 않은 경우에도 부모로부터 "제거된" 모든 자식을 삭제합니다)
#                            ## https://stackoverflow.com/questions/5033547/sqlalchemy-cascade-delete
#                            # , backref=backref('parent', remote_side=[id]) #,
#                            # ,[1] passive_deletes='all' #  True, All 안됨 [2] backref()안에 줘도 안됨.
#                            , cascade="all"  # [3] backref가 아닌, replies 자신에게 준다
#                            # , passive_deletes=True # [3] backref가 아닌, replies 자신에게 준다
#
#                            ## 평상시는 lazy->dynamic 걸어놓고, path -> level()로 jinja2에서 객체.level()별로 indent만 넣어주면 됨.
#                            ## 계층적 구조로 다 eager-loading for api하는 경우에만..
#                            , join_depth=6  # 필수1
#                            , lazy='subquery'  # 필수2
#                            # , lazy='dynamic' # 안됨. -> 'Comment.replies' does not support object population - eager loading cannot be applied.
#                            # , lazy = 'joined' # 안됨 -> The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections
#                            )
#     # ,lazy='dynamic') # => 명시하면, subqueryload조차 안됨. 아예안됨.
#     ## 7. 한번에 쿼리하기 위해 path칼럼을 추가한다.(Text 01.01., index)
#     path = Column(Text().with_variant(String(100), 'mysql'), index=True)
#
#     #### 14. 최상위댓글별 그룹을 timestamp로 지정하기 위해
#     ####     자신 + 대댓글들은 부모의 timestamp를 복제한 thread_timestamp를 가진다.
#     ####  group timestamp 칼럼 == thread_timestamp
#     thread_timestamp = Column(DateTime())
#
#     ## 8. 현재 인스턴스의 level을 self.path를 통해 구해주는 level 메서드를 만든다.
#     ## => 이 때, (0 padding의 갯수) 로 나눈 몫에 - 1(0부터 시작)한 것이 level(depth)다
#     ## ex> 01 02 => len 4 // 2   -  1 ==  depth 1
#     ##     012 001 => len 6 // 3   - 1 == depth 1
#     ##     0001 0002 0003   => len 12 // 4   - 1 == dpeth 2
#     ##     1) 전체갯수 // 각 구간별 열의 갯수 -> 몇번째 구간인지 1부터.
#     ##     2) 1부터 몇번째 구간인지  -  1    -> 0번째부터 몇번째 구간인지 == 0부터 몇번째 depth인지
#     # def level(self):
#     #     return len(self.path) // self._N - 1
#     ## 21.
#     @hybrid_property
#     def level(self):
#         return len(self.path) // self._N - 1
#
#     ## 22. 이것까지 줘야 계측칼럼도 정렬할 수 잇음. by classmethod로서 entity를 cls로 이용
#     ## if return return일 경우 case문으로 처리
#     ## len(self.필드) => func.length(cls.필드) , 나누기 -> func.div -> sqlite에선 지원안함.
#     @level.expression
#     def level(cls):
#         # 0 division 가능성이 있으면 = (cls.path / case([(cls._N == 0, null())], else_=cls.colC)
#         # /는 지원되나 //는 지원안됨. func.round()써던지 해야할 듯.?
#         return func.length(cls.path) / cls._N - 1
#
#     ## 9. 나중에 repository나, 다른 session을 사용하는 곳으로 옮겨야겠찌만,
#     ##  save () 메서드를 이용해서,
#     ## 1) Comment 기본 데이터 저장 (paht는 비워둠) -> fk(부모_id) 배정 받음.
#     ## 2) self.parent.path로, 부모까지 완성된 path를 물려받아 += 0 padding과 함께 자신의id로 입력
#     ##    부모가 없으면, ''로 누적한 뒤, 자신의 path입력
#
#     ## => 지식이 생겨버린다 + Entity에 session을 당겨와야하는 상황
#     ## => 나중에 repository로 옮기던지 하자.
#     def save(self):
#         with DBConnectionHandler() as db:
#             db.session.add(self)
#             db.session.flush()
#
#             prefix = self.parent.path if self.parent else ''
#             self.path = prefix + f"{self.id:0{self._N}d}"
#
#             #### 15.
#             # 부모가 있으면, 부모의 그룹timestamp인 thread_timestamp 복제
#             # 부모가 없으면, 최상위이므로, 자신의 timestamp복제
#             self.thread_timestamp = self.parent.thread_timestamp if self.parent else self.timestamp
#
#             db.session.commit()
#
#     ## => 이제부터 각 객체들은 add commit이 아니라 save()로 저장해야한다.
#
#     ## 22.
#
#     def __repr__(self):
#         info: str = f"{self.__class__.__name__}" \
#                     f"[id={self.id!r}," \
#                     f" text={self.text!r}," \
#                     f" author={self.author!r}," \
#                     f" level={self.level!r}]"
#         # f" level={self.level()!r}]"
#         return info
