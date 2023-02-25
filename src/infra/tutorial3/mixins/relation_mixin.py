from sqlalchemy import MetaData, select, Table, join, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, InstrumentedAttribute, DeclarativeMeta, aliased, contains_eager, joinedload

from src.infra.tutorial3.mixins.base_query import BaseQuery
from src.infra.tutorial3.mixins.objectmixin import ObjectMixin
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


class RelationMixin(Base, ObjectMixin):
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
    def load(cls, schema: dict, session: Session = None):
        """
        관계칼럼 정의시 lazy=옵션을 안준 상태로 정의해야한다.
        1. 관계속성을 eager 로 subquery로 가져온 경우 => 접근 가능
        u = User.load({'role':'subquery'}).filter_by(id=1).first()
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
    @load.instancemethod
    def load(self, schema):
        """
        # 관계속성 or 관계속성명을 입력

        Department.load(schema={Department.employee_departments:'joined'}).first()
        Department.filter_by(id=1).load(schema={Department.employee_departments:'joined'}).first()

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

        self._query = (
            self._query
            .options(*self.create_eager_options(schema=schema))
        )

        print(self._query)
        return self

    #### '*' 및 alias때문에 only expression query가 된다.
    # -> create_query_obj 생성시점에서 flag를 받아
    # -> 기본 칼럼을  [model] 대신 ['*']로 가져가고 execute를 해야한다.
    @classmethod
    def raw_join(cls, target, session: Session = None,
                 l_selects=None, r_selects=None,
                 left_alias_name='left_table', right_alias_name='right_table',
                 **kwargs):

        """
        EmployeeDepartment.raw_join('employee', isouter=True).execute()
        => SELECT *
           FROM employee_departments AS left_table
           LEFT OUTER JOIN employees AS right_table
            ON right_table.id = left_table.employee_id

        EmployeeDepartment.raw_join('employee', isouter=True, l_selects=['id', 'position'], r_selects=['id', 'name']).execute()
        =>  SELECT left_table.id, left_table.position, right_table.id, right_table.name
            FROM employee_departments AS left_table
            LEFT OUTER JOIN employees AS right_table
                ON left_table.employee_id = right_table.id
        """

        join_options = dict(onclause=None, isouter=False, full=False)
        join_options.update(kwargs)
        # raw_join하는 경우
        # => 칼럼선택이 있든 없든 is_raw플래그를 띄워 selects가 없을 경우  [model] 대신 [text('*')]가 select된다.

        left_rel_column, rel_model = cls.get_rel_prop_and_model(target)
        #### cls(left_table)은 join일 경우만 alias를 달수 있도록 => create_select_statement에서 alias로 만든다.
        # => 칼럼 선택X시 칼럼명 '*' / 선택시 여기서 text('left_table.칼럼명')까지 완성하고 보낸다.

        # 1) 칼럼 선택이 없으면, query를 '*'로 구성할 수 있도록 is_raw를 True로 stmt를 만든다.
        if not (l_selects or r_selects):
            query = cls.create_select_statement(cls,
                                                is_expr=True,
                                                join_target=rel_model,
                                                join_options=join_options,
                                                l_selects=None,
                                                r_selects=None,
                                                join_left_alias_name=left_alias_name,
                                                join_right_alias_name=right_alias_name
                                                )

            return cls.create_query_obj(session, query)


        # 2) 칼럼이 left or right 선택하는 경우
        # => target(right)테이블에만 alias를 맥여서 join + r_select칼럼들을 만들어야한다.
        #    + right 칼럼명은 alias + . + 칼럼 으로 가져간다.
        #    (left는 alias먹일 경우 자동join안된다)
        else:

            # 관계속성으로 left_fk 와 right_pk의 칼럼명을 구하고, expr으로 작성한다.
            left_fk_name, right_pk_name = cls.get_fk_and_rel_pk_name(left_rel_column)
            # on절은 left_table과 right_table로 alias를 미리 정해두고,
            # => 관계속성으롭터 left_fk 칼럼과 right_pk칼럼을 만들어서 대입해준다.
            join_options.update(dict(onclause=text(f'{left_alias_name}.{left_fk_name} = {right_alias_name}.{right_pk_name}')))
            # print(self.__dict__)

            # self.set_session(session)
            # else:
            #

            print('target, left_rel_column, right_model  >> ', target, left_rel_column, rel_model)

            # select_columns = []
            ## aliased( stmt .subquery ) 와 stmt.alias() 둘다 되는 것 같다:
            ## https://github.com/sqlalchemy/sqlalchemy/issues/6274
            # 1) self._query => Alias
            # current_table = aliased(self._query.subquery(self.__class__.__name__))
            # current_table = aliased(self._query.subquery())
            # 2) self._query => Subquery
            # => AttributeError: 'Subquery' object has no attribute 'label'
            # current_table = self._query.alias(self.__class__.__name__)
            # current_table = self._query.alias()

            if l_selects:
                if not isinstance(l_selects, (list, tuple, set)):
                    l_selects = [l_selects]
                # columns = cls.create_columns(left_alias_name, l_selects)
                # select_columns += cls.to_expr_columns(l_selects, left_alias_name)

            if r_selects:
                # select_columns += cls.to_expr_columns(r_selects, right_alias_name)
                if not isinstance(r_selects, (list, tuple, set)):
                    r_selects = [r_selects]

            print('l_selects  >> ', l_selects)
            print('r_selects  >> ', r_selects)

            # self._query = (
            #     select(select_columns)
            #     .select_from(
            #         join(current_table, target,
            #              onclause=onclause, isouter=isouter, full=full)
            #     )
            # )

            #### 이 때, target에 .alias(name= )을 만들어서 건네줘야한다.
            query = cls.create_select_statement(cls,
                                                is_expr=True,
                                                join_target=rel_model,
                                                join_options=join_options,
                                                l_selects=l_selects,
                                                r_selects=r_selects,
                                                join_left_alias_name=left_alias_name,
                                                join_right_alias_name=right_alias_name
                                                )

            return cls.create_query_obj(session, query)

    # for raw_join
    @classmethod
    def get_fk_and_rel_pk_name(cls, left_rel_column):
        left_fk = left_rel_column.property.local_remote_pairs[0][0].name
        right_pk = left_rel_column.property.local_remote_pairs[0][1].name
        return left_fk, right_pk


    # for raw_join
    @classmethod
    def get_rel_prop_and_model(cls, target):
        # target에 관게속성이 오는 경우 -> model class로 변경
        # => join(기존select, join대상)에서는 관계속성은 안받고 table만 받는다.
        if isinstance(target, InstrumentedAttribute):
            left_rel_column = target
            right_model = cls.get_relation_model(cls, target.key)

        # 관계속성명으로 오는 경우 -> model class로 변경
        elif isinstance(target, str):
            left_rel_column = cls.get_column(cls, target)
            right_model = cls.get_relation_model(cls, target)

        # target에 model class로 오는 경우 -> 통과
        else:  # isinstance(target, (DeclarativeMeta, Table)):
            raise Exception(f'Invalid RelationProperty or name : {target}')
        return left_rel_column, right_model

