from sqlalchemy import MetaData, select, Table, join
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, InstrumentedAttribute, DeclarativeMeta

from src.infra.tutorial3.mixins.base_query import BaseQuery
from src.infra.tutorial3.mixins.utils.classorinstancemethod import class_or_instancemethod

Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class RelationMixin(Base, BaseQuery):
    __abstract__ = True

    """
    User.with_({
        'posts': {
            'comments': {
                'user': JOINED
            }
        }
    }).all()
    
    User.with_({
        User.posts: {
            Post.comments: {
                Comment.user: JOINED
            }
        }
    }).all()
    
    
    from sqlalchemy_mixins import JOINED, SUBQUERY
    Post.with_({
        'user': JOINED, # joinedload user
        'comments': (SUBQUERY, {  # load comments in separate query
            'user': JOINED  # but, in this separate query, join user
        })
    }).all()
    
    
    Comment.with_joined('user', 'post', 'post.comments').first()
    User.with_subquery('posts', 'posts.comments').all()
    
    Comment.with_joined('user','post')
    Comment.with_({'user': JOINED})
    
    comments = Comment.where(post___public=True, post___user___name__like='Bi%').all()
    """
    @class_or_instancemethod
    def join(cls, schema:dict, session: Session = None):
        """
        관계칼럼 정의시 lazy=옵션을 안준 상태로 정의해야한다.
        1. 관계속성을 eager 로 subquery로 가져온 경우 => 접근 가능
        u = User.join({'role':'subquery'}).filter_by(id=1).first()
        => u.role
        <Role 'ADMINISTRATOR'>

        2. 그냥 관계객체를 load하면 => 접근 불가능.
        u = User.filter_by(id=1).first()
        => u.role
        Parent instance <User at 0x2c788c1fa58> is not bound to a Session;

        """
        query = cls.create_select_statement(cls, eager_options=schema)

        return cls.create_query_obj(session, query)

    @join.instancemethod
    def join(self, target, onclause=None, isouter=False, full=False):
        # target에 관게속성이 오는 경우 -> model class로 변경
        # => join(기존select, join대상)에서는 관계속성은 안받고 table만 받는다.
        if isinstance(target, InstrumentedAttribute):
            target = self.get_relation_model(self.__class__, target.key)
        # 관계속성명으로 오는 경우 -> model class로 변경
        elif isinstance(target, str):
            target = self.get_relation_model(self.__class__, target)

        # target에 model class로 오는 경우 -> 통과
        elif isinstance(target, (DeclarativeMeta, Table)):
            pass

        # self._query = (
        #     self._query
        #     .join(target, onclause=onclause, isouter=True, full=full)
        # )

        #### 객체상태에서 join할 경우, model obj의 관계속성에 load되는 것이 아니다.
        # => select절에서 뽑아먹을 수 있게 해야한다.
        self._query = (
            select('*')
            .select_from(join(self._query, target, onclause=None, isouter=False, full=False))
        )

        print(self._query)


        return self