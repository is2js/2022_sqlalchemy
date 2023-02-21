from sqlalchemy import MetaData, select, Table, join
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, InstrumentedAttribute, DeclarativeMeta, aliased, contains_eager, joinedload

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
    def join(cls, schema: dict, session: Session = None):
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

    #### select 만들기
    @join.instancemethod
    def join(self, target, onclause=None, isouter=False, full=False,
             selects=None, target_selects=None,
             ):
        """
        1. selects + target selects를 안거는 경우 -> eagerload로 main entity에 정보 담기
        # 1-1) join을 통해 eager load안한 경우 -> 관계속성 접근시 detached Error
        ed = EmployeeDepartment.filter_by(id=1).first()
        ed.employee =>  sqlalchemy.orm.exc.DetachedInstanceError:
        # 1-2) join(관계속성명 / 관계속성 / 관계테이믈명 -> 관계테이믈 추출) => 관계속성 접근가능해진다.
        ed = EmployeeDepartment.filter_by(id=1).join('employee').first()
        ed = EmployeeDepartment.filter_by(id=1).join(EmployeeDepartment.employee).first()
        ed.employee =>  <Employee 2>




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

        # self._query = (
        #     self._query
        #     .join(target, onclause=onclause, isouter=True, full=full)
        # )

        #### 객체상태에서 join할 경우, model obj의 관계속성에 load되는 것이 아니다.
        # => select절에서 뽑아먹을 수 있게 해야한다.
        if not (selects or target_selects):
            # select_columns = '*'
            # current_table = self._query

            self._query = (
                self._query
                ##### eager만한다면 관계속성+관계속성명 가능하나,
                ##### eager 이후 chainning join에서 join타겟을 못잡는다.
                .options(joinedload(target))
                #### 여기서는 관계속성/만  ->  (join + earger까지) -> 뒤에 체이닝 된다.
                #### 하지만 체이닝시 select의 문제가
                # .join(target, onclause=onclause, isouter=isouter, full=full)
                # .options(contains_eager(target))
            )

        else:

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


            select_columns = []
            ## aliased( stmt .subquery ) 와 stmt.alias() 둘다 되는 것 같다:
            ## https://github.com/sqlalchemy/sqlalchemy/issues/6274
            # 1) self._query => Alias
            # current_table = aliased(self._query.subquery(self.__class__.__name__))
            # current_table = aliased(self._query.subquery())
            # 2) self._query => Subquery
            # => AttributeError: 'Subquery' object has no attribute 'label'
            # current_table = self._query.alias(self.__class__.__name__)
            # current_table = self._query.alias()

            joined_table_label= 'adc'


            if select:
                if not isinstance(selects, (list, tuple, set)):
                    selects = [selects]
                select_columns += self.create_columns(joined_table_label, selects)
            if target_selects:
                if not isinstance(target_selects, (list, tuple, set)):
                    target_selects = [target_selects]
                select_columns += self.create_columns(target, target_selects)

            print('select_columns  >> ', select_columns)

            # self._query = (
            #     select(select_columns)
            #     .select_from(
            #         join(current_table, target,
            #              onclause=onclause, isouter=isouter, full=full)
            #     )
            # )
            self._query = (
                select(select_columns)
                .select_from(
                    self._query.join(target,
                         onclause=onclause, isouter=isouter, full=full).subquery(joined_table_label)
                )
            )

        print(self._query)

        return self
