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
        """
        1. 중간에 join은 execute()를 예상하고, 모든 칼럼들을 나타낸다.
          -> 원래 join은 ModelClass만 받지만, 내부처리로 관계속성 + 관계속성명을 변환처리한다.
          -> 그외 isouter 옵션등을 사용할 수 있다.

        User.filter_by(id=1).join(Role).execute()

        User.filter_by(id=1).join(User.role).execute()

        User.filter_by(id=1).join('role').execute()

        SELECT *
        FROM (SELECT users.add_date AS add_date, users.pub_date AS pub_date, users.id AS id, users.username AS username, users.password_hash AS password_hash, users.email AS email, users.last_seen AS last_seen, users.is_active AS is_active, users.avatar
            AS avatar, users.sex AS sex, users.address AS address, users.phone AS phone, users.role_id AS role_id
            FROM users
            WHERE users.id = :id_1) AS anon_1
            JOIN roles
                ON roles.id = anon_1.role_id

        [('2023-02-15 01:53:10.263698', '2023-02-21 15:23:07.229291', 1, 'admin', 'pbkdf2:sha256:260000$B8emxNA8yt49c1aB$4db1b71a6b0dadea35ad2586af3f5bf7b01fbbfa2c7fbbf404f57e542b864c50', 'tingstyle1@gmail.com', '2023-02-21 15:23:07.226288', 1, None, 0,
        None, None, 6, '2023-02-15 01:52:57.103137', '2023-02-15 01:52:57.103137', 6, 'ADMINISTRATOR', 0, 255)]

        """
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
            .select_from(
                join(self._query, target,
                     onclause=onclause, isouter=isouter, full=full)
            )
        )

        # print(self._query)

        return self