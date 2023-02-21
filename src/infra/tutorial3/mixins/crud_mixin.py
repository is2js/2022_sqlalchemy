"""
base_query 기반으로 각 model들의 쿼리들을 실행할 수 있는 mixin 구현
"""

import inspect

from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint, exists, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, RelationshipProperty, DeclarativeMeta

# from src.infra.config.base import Base
from sqlalchemy.util import hybridmethod

from src.infra.config.connection import db
from src.infra.tutorial3.mixins.base_query import BaseQuery

# for def const_column_names()
from src.infra.tutorial3.mixins.session_mixin import SessionMixin
from src.infra.tutorial3.mixins.utils.classorinstancemethod import class_or_instancemethod
from src.infra.tutorial3.mixins.utils.classproperty import class_property

constraints_map = {
    'pk': PrimaryKeyConstraint,
    'fk': ForeignKeyConstraint,
    'unique': UniqueConstraint,
}

# 1. model들이 자신의 정보를 cls.로 사용할 예정(객체 만들어서 chaining)이라면, Base를 상속해서 Mixin을 만들고, model은 Mixin을 상ㅅ속한다.
# => 그외 객체생성없이 메서드만 추가할 Mixin은 부모상속없이 그냥 만들면 된다.
# 1-2. 정의해준 BaseQuery의 class메서드들을 쓸 수 있게 한다?! => 그냥 import한 것으로 사용만할까?
Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


# class CRUDMixin(Base, BaseQuery):
# mixin 2. Mixin의 Base는 BaseModel Base가 아닌 새로운 Base를 기능이용을 위해 땡겨쓰는 것이다.
class CRUDMixin(Base, BaseQuery, SessionMixin):
    __abstract__ = True  # Base상속 model인데, tablename안정해줄거면 있어야한다.

    # : https://stackoverflow.com/questions/20460339/flask-sqlalchemy-constructor
    # 2. 각 sqlalchemy model들은 사실상 cls()로 객체를 생성해도 init이나 new를 실행하지 않는다.
    # => 그 이유는 keyword만 칼럼정보로 받아 처리하기 때문이다.
    # => 하지만, 상태패턴처럼 .filter_by() 이후, 정보를 .order_by(), .first()에 넘기려면
    #   부모의 인자그대로 오버라이딩 후 => self._query의 필드를 가지고 있어야 chaning할 수 있다.
    """
    User(session=db.session, username='조재성').session 
    => <sqlalchemy.orm.session.Session object at 0x000002286C7A64E0>
    User(session=db.session, username='조재성').username
    => '조재성'
    """

    # 4. 자식으로서 chaning시 객체가 생성될 텐데, 그 때 넘겨주고 싶으면 인자를 **kwargs 앞에 너어주면 된다.
    # mixin 3. 믹스인은 생성자를 재정의해선 안된다. 하더라도 BaseModel에서 해야하는데,
    # => Mixin은 동적 필드를 setter로 채워주는 식으로 변경한다.
    # def __init__(self, session=None, query=None, **kwargs):
    #     # 3. super() 인자 생략하면, super(나, self)로서 => [나의 상위(super)]에서부터 찾아쓰게
    #     # 인자 super(나 or 부모class중 택1, self)를 줘서 구체적인 부모를 지정할 수 있다.
    #     # => 나를 첫번째 인자로 주면, 나(BaseMixin)의 부모(super) -> Base부터 찾는다는 뜻이다.
    #     super(CRUDMixin, self).__init__(**kwargs)
    #     self._query = query
    #     # 4. 객체를 생성하는 순간 chaining이 시작될 땐, 외부에서 사용중이던 session이 안들어오면 새 session을 배급한다.
    #     # => 배급한 session은 실행메서드들이 close를 꼭 해줄 것이다.
    #     self.served = None  # => 뒤에서 self._get_session에서 초기화해준다.
    #     self._session = self._get_session_and_mark_served(session)
    #     # print('create obj session >   >> ', self._session)

    # 감춰진 query를 setter만 가능하도록
    # => 생성자에서도 self._query에 query=로 주고 있음.
    @property
    def query(self):
        raise AttributeError("query can't not read.")

    @query.setter
    def query(self, query):
        self._query = query

    # 2. obj의 served상태에 따라 close(내부생성) or flush(외부받아온 것) 되도록
    def close(self):
        # 외부에서 받은 상태가 아니면 자체session을 -> close()
        if not self.served:
            self._session.close()
        # 외부세션이면 close할 필요없이 반영만  [외부 쓰던 session은 close 대신] -> [flush()로 db 반영시켜주기]
        else:
            self._session.flush()

    # 3. obj의 내부 _query쿼리를 2.0스타일로 실행
    #   first()/all()/count() 등의 실행메서드는 생성된 객체.method()로 작동하므로 일반 self메서드로 작성한다.
    def first(self, auto_close: bool = True):
        result = self._session.scalars(self._query).first()
        self.close()
        return result

    def one(self):
        result = self._session.scalars(self._query).one()
        self.close()
        return result

    def all(self):
        result = self._session.scalars(self._query).all()
        self.close()
        return result

    def scalar(self):
        result = self._session.scalar(self._query)
        self.close()
        return result

    def execute(self):
        result = self._session.execute(self._query)
        # execute한 것은 list()로 풀어해쳐줘야 밖에서 쓸 수 있다.?
        # 내부 session일 경우, 외부에서 자유롭게 쓰기 위해 순회해서 session걸린 것을 없애자
        if not self.served:
            result = list(result)
        self.close()
        return result

    def count(self):
        # => 그냥 all()로 가져와서 데이터를 세자.
        # => 아니라면, count를 select한 뒤, scalar로 받아야한다.
        result = len(self.all())
        self.close()
        return result

    # 객체에서 self.check_exists()로 생성 kwargs로 자체적으로 검사하고 있으면 반환하도록 설계된 상태임.
    def exists(self):
        # 자식들은 따로 overide하겠지만,
        # self._query => exists(self._query)로 싼 뒤(실행불가 sql 상태)
        #             => .select() (실행가능 sql=select)
        #             => scalar => T/F로 반환한다.
        result = self._session.scalar(exists(self._query).select())
        self.close()
        return result

    # 추가) for db에 반영하는 commit이 포함된 경우, close()는 생략된다. -> 외부 sessoin을 flush()만하고 더 쓰던지, commit()으로 끝낸다.
    # => Committing will also just expire the state of all instances in the session so that they receive fresh state on next access.
    #    Closing expunges (removes) all instances from the session.
    def save_self(self, target=None, auto_commit: bool = True):
        # => self메서드들은 이미 session_obj상태에서 호출하도록 변경
        # self.set_session_and_query(session)

        if not target:
            target = self

        #### try/catch는 외부세션을 넣어주는데서 할 것이다?
        self._session.add(target)
        # 1. add후 id, 등 반영하기 위해 [자체생성/외부받은 session 상관없이] flush를 때려준다.
        self._session.flush()
        # 2. 외부session인 경우, 외부의 마지막 옵션으로 더이상 사용안한다면 밖에서 auto_commit=True로 -> commit()을 때려 close시킨다.
        # => self.close()는 외부session을 flush()만 시키는데, 외부session이 CUD하는 경우, 자체적으로 commit()해야한다.
        # => 외부에서 더 쓴다면, 외부에서 sessino=sesion만 넣고 auto_commit 안하면 된다.
        if auto_commit:
            self._session.commit()

        return target

    # 추가) order_by도 filter_by이후 실행메서드 처럼 객체에서 하는 것이다.
    # => 이 때, 인자가 튜플로 들어온다.
    # => 문제은 BaseQuery에 cls메서드로 작성해놨다 => self.classmethod로도 쓸 수 있지만, model인자가 문제다.
    #    일단 classmehotd의 model을 model=None으로 주고, 없을 경우, model = cls로 줬다.
    # => print(model)하면 cls가 그대로 들어가있다. <class 'src.infra.tutorial3.auth.users.User'>
    def order_by(self, *args):
        """
        User.filter_by().order_by("-id").all()
        User.filter_by().order_by(User.id).all()
        User.filter_by().order_by(User.id.desc()).all()
        """
        self._query = self._query \
            .order_by(*self.create_order_bys(args))

        return self

    def limit(self, count: int):
        """
        User.filter_by().order_by().limit(3).all()
        => [User[id=1,username='admin',], User[id=2,username='asdf15251',], User[id=3,username='asdf15252',]]

        User.filter_by().order_by().limit(2).all()
        => [User[id=1,username='admin',], User[id=2,username='asdf15251',]]

        User.filter_by().order_by().limit(1).all()
        => [User[id=1,username='admin',]]

        """
        if not isinstance(count, int):
            raise Exception(f'Invalid count(not int type): {count}')

        self._query = self._query \
            .limit(count)

        return self

    # 추가) order_by는 filter_by없이 class메소드로도 쓰일 것 같음
    # => 이럴 경우, order_by에서 cls() obj를 만들어줘야한다.
    ###############################################################
    #### Model에서 바로 호출되어 객체 생성시 session_obj로 만드는 함수 ####
    #### create + filter_by => cls.create_query_obj() 사용    ####
    #### filter_by => session 외 query까지 들어감.                ####
    ###############################################################

    # for exists_self
    @property
    def first_unique_key(self):
        self_unique_key = next((column_name for column_name in self.column_names if column_name in self.uks), None)
        # print('unique_key  >> ', self_unique_key)
        if not self_unique_key:
            # 3) 유니크 키가 없는 경우, 필터링해서 존재하는지 확인할 순 없다.
            raise Exception(f'생성 전, 이미 존재 하는지 유무 확인을 위한 unique key가 존재하지 않습니다.')

        return self_unique_key

    # for create                #
    #############################
    # _self류(session이미확보)인데, query가 필요한 exists_self   #
    # create_select_statement   #
    # query 만들고 .exists()     #
    #############################
    # mixin 12. create -> session_obj를 만들어서 호출되므로, session은 보장된 상태다?
    # => _self메서드들은 session_obj를 만들고 난 뒤, 호출될 예정이므로, 상관없다.?!
    def exists_self(self):
        """
        그냥 존재검사(.exists())가 아니라, 생성시 kwargs를 바탕으로 유니크key를 골라내서 검사함

        User(username='관리자', sex=0, email='tingstyle1@gmail.com').exists()
        self.uks  >>  ['username']
        self.column_names  >>  ['add_date', 'pub_date', 'id', 'username', 'password_hash', 'email', 'last_seen', 'is_active', 'avatar', 'sex', 'address', 'phone', 'role_id']
        self_unique_key  >>  username
        """
        # mixin 13. session 보장받음.
        # self.set_session_and_query(session)

        # 1) 생성하려고 준 정보중에 unique 칼럼을 찾고, 그것으로 조회한다.
        # print('self.uks  >> ', self.uks)
        # 2) 이미 obj = cls()가 생성되면, 각 칼럼columns에 값이 입력된 상태다. super().__init__(**kwags)에 의해
        # print('self.column_names  >> ', self.column_names)
        # 2) 여러개 중에 1개만 뽑은 뒤
        self_unique_key = self.first_unique_key
        # print('self.__dict__  >> ', self.__dict__)

        # print('{self_unique_key: getattr(self, self_unique_key)}  >> ',
        #       {self_unique_key: getattr(self, self_unique_key)})
        # {self_unique_key: getattr(self, self_unique_key)}  >>  {'username': None}
        # existing_obj  >>  None

        # existing_obj = self.filter_by(
        #     session=self._session,
        #     **{self_unique_key: getattr(self, self_unique_key)}) \
        #     .first()

        #### create로 obj생성후 filter_by로 또 obj 생성하는 것 방지하기 위해, filter_by내부로직을 차용
        query = self.create_select_statement(model=self.__class__,
                                             filters={self_unique_key: getattr(self, self_unique_key)},
                                             )
        self._query = query

        return self.exists()

    @classmethod
    def create(cls, session: Session = None, auto_commit: bool = True, **kwargs):
        """
        1. session안받고 내부에서 생성 -> auto_commit 필수
        2. session받아서 외부세션으로 생성 -> 1) 더 사용할거면 auto_commit안해도됨(flush) 2) 마지막사용이면 auto_commit 넣기
        User.create(
            session=session,
            auto_commit=True, => 외부세션 사용중이라면, 맨 CUD에만(중간사용이면 flush만) <-> 내부는 항상 auto_commit True
            username='asdf15253', password='aasdf2sadf5sdf132',email='as5df1235@asdf.com', is_active=True
            )
        """
        # mixin 10. filter_by처럼 create도 cls메서드로 session_obj를 만든다.
        # => 이 떄, query는 없고, **kwargs를 다 받는가 차이점.
        # obj = cls(session=session, **kwargs)
        # obj = cls(session=session, **kwargs)
        query_obj = cls.create_query_obj(session=session, **kwargs)

        # db들어가기 전 객체의 unique key로 존재 검사
        if query_obj.exists_self():
            return False

        return query_obj.save_self(auto_commit=auto_commit)

    # create_select_statement + create_query_obj + query
    @class_property
    def has_query_obj(cls):
        return hasattr(cls, '_query')

    @class_or_instancemethod
    def filter_by(cls, session: Session = None, selects=None, **kwargs):
        """
        User.filter_by(id=1)
        -> User[id=None]

        User.filter_by(selects=['username'], id=1).all()
        -> ['admin']

        """

        query = cls.create_select_statement(cls, filters=kwargs, selects=selects)
        # mixin 6. 더이상 Model들의 생성자에서 session과 query를 받는게 아니라
        # => setter로 생성후 setter로 주입한다.
        # obj = cls(session=session, query=query)  # served는 session여부에 따라서 알아서 내부 초기화 됨.

        # mixin 9. 반복되는 session주입 model객체 -> session_obj를 만드는 과정을 메서드로 추출
        # obj = cls().set_session_and_query(session, query=query)
        return cls.create_query_obj(session, query)

    @filter_by.instancemethod
    def filter_by(self, **kwargs):
        self._query = (
            self._query
            .where(*self.create_filters(self.__class__, kwargs))
        )
        return self

    # mapper(cls.__mapper__) == inpsect(cls) 와 cls.__table__은 둘다 .columns for Column객체(Table객체용 객체칼럼 db.Column) 를 가지고 있지만,
    # => mapper.attrs for Properties(ORM hybridproperty 포함 )을 가지고 있다. ColumnProperty / RelationshipProperty
    # => mapper.all_orm_descriptors => hybrid_property  +  InstrumentedAttribute (ColumnProperty + RelationshipProperty)
    #    => keys()로 이름만 가능.
    #    for hybrid_property
    # => mapper.attrs => RelationshipProperty + ColumnProperty => .keys() 이름만
    #    순회) mapper.iterate_properties
    #    for RelationshipProperty

    # => mapper.column_attrs => ColumnProperty => .keys() 이름만
    #    for 순수칼럼(관계X) property

    # => mapper.columns OR  cls.__table__.columns => .keys() 이름만
    #    for 순수칼럼(관계X) column
    #    => Note that __table__.columns will give you the SQL field names,
    #       not the attribute names that you've used in your ORM definitions (if the two differ).

    # => mapper.primary_key => (Column('id', Variant(), table=<users>, primary_key=True, nullable=False),)
    #    => pk칼럼명을 가져올 순 있으나, fk에 관련된 정보는 없다.

    # => cls.__table___ => pk외 fk, index, 제약조건을 통한 unique도 가능?
    #   .primary_key => PrimaryKeyConstraint(Column('id', Variant(), table=<users>, primary_key=True, nullable=False))
    #   .foreign_keys =>  {ForeignKey('roles.id')}
    #    .indexes =>  {Index('ix_users_email', Column('email', String(length=128), table=<users>, nullable=False), unique=True)}
    #    .User.__table__.constraints =>
    #           UniqueConstraint(Column('username', String(length=128), table=<users>, nullable=False)),
    #           PrimaryKeyConstraint(Column('id', Variant(), table=<users>, primary_key=True, nullable=False))}
    #           ForeignKeyConstraint(<sqlalchemy.sql.base.DedupeColumnCollection object at 0x00000230E47A53B8>, None, name='fk_users_role_id_roles', table=Table('users', MetaData(), Column('add_date', DateTime(), table=<users>, nullable=False, default=ColumnDef
    # for c in User.__table__.constraints:
    # ...     print(c.name, c.columns._all_columns)
    # ...
    # fk_users_role_id_roles [Column('role_id', Integer(), ForeignKey('roles.id'), table=<users>, nullable=False)]
    # uq_users_username [Column('username', String(length=128), table=<users>, nullable=False)]
    # pk_users [Column('id', Variant(), table=<users>, primary_key=True, nullable=False)]

    #  table=<users>, primary_key=True, nullable=False))}
    # => RelationshipProperty 포함 칼럼종류 => .attrs / mapper.attrs.keys()
    #                               ['role', 'inviters', 'invitees', 'add_date', 'pub_date', 'id', 'username', 'password_hash', 'email', 'last_seen', 'is_active', 'avatar', 'sex', 'address', 'phone', 'role_id', 'employee']
    # => hybrid property제외 함 칼럼종류 => .attrs / mapper.column_attrs.keys()
    #                               ['add_date', 'pub_date', 'id', 'username', 'password_hash', 'email', 'last_seen', 'is_active', 'avatar', 'sex', 'address', 'phone', 'role_id']
    # self.__table__.columns will "only" give you the columns defined in that particular class,
    # i.e. without inherited ones.
    # if you need all, use self.__mapper__.columns. in your example i'd probably use something like this:

    # Base기반의 선언적 mapping을 사용한다면, __mapper__나 inpsect()를 쓰는게 좋다?
    # type(inspect(User))
    # <class 'sqlalchemy.orm.mapper.Mapper'>
    # mapper = User.__mapper__
    # <class 'sqlalchemy.orm.mapper.Mapper'>
    # mapper.attrs
    # <sqlalchemy.util._collections.ImmutableProperties object at 0x00000230E4C4C908>
    # attr = [c for c in mapper.attrs if c.key=='username'][0]
    # type(attr)
    # <class 'sqlalchemy.orm.properties.ColumnProperty'>
    # type(attr.expression)
    # <class 'sqlalchemy.sql.schema.Column'>
    # attr.expression.unique
    # True

    #### 제약조건 칼럼확인은 low level인 cls.__table__에서 .consraints로 확인한다.
    @class_property
    def column_names(cls):
        # return inspect(cls).columns.keys()
        return cls.__table__.columns.keys()

    @class_property
    def pks(cls):
        return cls.const_column_names(target='pk')

    @class_property
    def fks(cls):
        return cls.const_column_names(target='fk')

    @class_property
    def uks(cls):
        return cls.const_column_names(target='unique')

    @classmethod
    def const_column_names(cls, target='pk'):
        """
        User.const_column_names(target='unique')
        ['username']

        User.pks
        ['username']
        User.fks
        ['role_id']
        User.uks
        ['username']
        """
        # 제약조건 관련은 .__table__.constrains에서 꺼내 쓴다.
        if isinstance(target, str) and target.lower() not in constraints_map.keys():
            raise NotImplementedError(f'해당 {target} 제약조건의 칼럼명 목록 조회는 구현되지 않았습니다.')

        constraints = cls.__table__.constraints
        # User.__table__.constraints =>
        # {ForeignKeyConstraint( ..  , UniqueConstraint(Column('username', String(length=128), table=<users>, nullable=False)), PrimaryKeyConstraint(Column('id', Variant(),
        #  table=<users>, primary_key=True, nullable=False))}
        target_constraint = next((c for c in constraints if isinstance(c, constraints_map.get(target))), None)

        # 해당 제약조건의 칼럼이 없으면, 그냥 빈 리스트 반환
        if not target_constraint:
            return []

        return target_constraint.columns.keys()

    # for __eq__
    @class_property
    def columns_except_pk_and_default(cls):
        # columns_names   for pk, fk, uk 찾기와 달리,
        # pk(id)와 default값이 있는 칼럼들은 비교에서 제외시키기 위해, 해당 칼럼들을 제외해서 가져온다.
        return [c for c in cls.__table__.columns if c.primary_key is False or c.default is None]

    # columns_except_pk_and_default를 활용하여 eq, repr 정의하기
    # => pk와 deafult칼럼을 제외하고 비교한다.
    def __eq__(self, other):
        # commit안된 객체 출력을 대비, id 빼고 칼럼들을 비교함.
        return all(getattr(self, c.key) == getattr(other, c.key) for c in self.columns_except_pk_and_default)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}["
        # for c in self.columns_except_pk_and_default:
        for name in self.pks + self.uks:
            info += f"{name}={getattr(self, name)!r},"
        info += "]"
        return info

    ###################
    # filter_by 하위   #
    ###################
    @classmethod
    def get(cls, session: Session = None, **kwargs):
        """
        filter_by와 동일과정 시행후  실행메서드를 all()로 -> next( , None)로 있으면 첫번째 것 없으면 None 반환

        User.get(id=1))
        => User[id=1]

        User.get(id=111111111)
        => None

        User.get(email='asdf')
        => KeyError: 'Only pk or unique로만 검색가능합니다.'
        """
        if not all(key in cls.pks + cls.uks for key in kwargs.keys()):
            raise KeyError(f'Only pk or unique key search allowed.')

        # 실행메서드지만, filter_by에 의해 세션보급됨.
        obj = cls.filter_by(session=session, **kwargs)  # 메서드엔 filters=가 아니라 keyword방식으로 그대로 들어가야한다.

        # => obj.one()으로 처리하면, None일때도 에러난다. => .all()로 받아서, 갯수카운팅
        result = obj.first()

        #### 있으면 첫번재 것 없으면 None은 next( iterator, None )로 구현한다.
        return result

    # for update
    #### relations 칼럼은 .__table__이 아니라 high-level ORM의 mapper를 이용해야한다.
    @class_property
    def relation_names(cls):
        """
        User.relation_names
        ['role', 'inviters', 'invitees', 'employee']
        """
        mapper = cls.__mapper__
        # mapper.relationships.items()
        # ('role', <RelationshipProperty at 0x2c0c8947ec8; role>), ('inviters', <RelationshipProperty at 0x2c0c8947f48; inviters>),

        return [prop.key for prop in mapper.iterate_properties
                if isinstance(prop, RelationshipProperty)]

    @class_property
    def settable_relation_names(cls):
        """
        User.settable_relation_names
        ['role', 'inviters', 'invitees', 'employee']
        """
        return [key for key in cls.relation_names
                if getattr(cls, key).property.viewonly is False]

    # hybrid_property도 mapper에서 꺼낸다.
    @class_property
    def hybrid_property_names(cls):
        """
        User.hybrid_property_names
        ['is_staff', 'is_chiefstaff', 'is_executive', 'is_administrator', 'is_employee_active', 'has_employee_history']
        """
        mapper = cls.__mapper__
        props = mapper.all_orm_descriptors
        # [ hybrid_property  +  InstrumentedAttribute (ColumnProperty + RelationshipProperty) ]
        return [prop.__name__ for prop in props
                if isinstance(prop, hybrid_property)]

    # for fill
    #### update는 filter_by로 객체를 찾아놓은 과정에서, 생성된  obj에 _query에 update만 하도록 되어있어
    # => 내부 self._session을 가지고 있는 obj상태로서, 실행메서드(self 인스턴스 메서드)에 가깝다
    # => auto_commit여부를 받는다.
    # => setattr()로 받은 인자를 넣어주는데, 여러 검증이 필요하기 때문에 fill이라는 메서드로 빼준다.
    @class_property
    def settable_column_names(cls):
        return cls.column_names + cls.settable_relation_names + cls.hybrid_property_names

    # for update
    def fill(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.settable_column_names:
                raise KeyError(f"Invalid column name: {key}")
            setattr(self, key, value)

        return self

    # for update / delete => filter_by VS model_obj 구분 by query
    # self._query가 차있다면, filter_by에 의해 나온 session_obj
    # 없다면 model_obj
    # @property
    # mixin 5.
    # @class_property# => self메서드 내부  self.is_session_obj시 인식 안됨.
    # def is_query_obj(cls):
    #     print('hasattr(cls, _session)  >> ', hasattr(cls, '_session')) # => False
    #     print('cls._session  >> ', cls._session) # type object 'User' has no attribute '_session'
    #     return hasattr(cls, '_session') and cls._session


    def update(self, session: Session = None, auto_commit: bool = True, **kwargs):
        #### 문제는 User.get()으로 찾을 시, cls() obj가 내포되지 않아 self내부 _session이 없다.
        # => filter_by()로 찾은 객체는, 아직 실행하지 않았으면 cls() obj로서 내부 _session을 가지고 있다.
        # => 실행해버리면.. 없다.
        # => 자체적으로 현재 self에 보급해주는 로직을 만들어야한다.
        # => self.set_session_and_query(session)
        """
        1. 기본 model_obj에서 사용
        c2 = Category.filter_by(name='2').first()
        c2.update(name='22')
        Category[id=4,name='22',]

        2. filter_by로 사용
        1) filter_by에서 생성된 session_obj에서 model_obj를 업뎃 후 commit => updated_model_obj를 반환하면 session에러
        Category.filter_by(name='334').update(session=s1, name='335')
        => True

        2) 외부세션에서 auto_commit=False상태라면, updated_model_obj가 session에 남아 사용가능
        s1 = db.get_session()
        Category.filter_by(name='335').update(session=s1, auto_commit=False, name='336')
        => Category[id=2,name='336',]
        s1.commit()
        """
        # update/delete는 filter_by의 session_obj(query_obj)든  model_obj든 session을 미리 확보한다
        # 1) filter_by에 의해 session과 query가 이미 있는 경우는 외부session이 들어올때만 업뎃한다.
        # => 이미 filter_by내부 cls.create_session_obj에 의해 session이 차있는데 또 다시 생성한다.
        # 2) model_obj에서 호출된다면, 외부session여부와 상관없이 무조건 호출되어야한다.
        self.set_session(session)

        # 1) filter_by로 생성된 경우(self._query가 차있는 경우) => statment은 불린처리 안됨.
        #    => 여러개 필터링 될 수도 있다..
        # if self._query is not None:
        if self.is_query_obj:
            try:
                model_obj = self.one()
            except Exception as e:
                print(e)
                return False

            # return model_obj.fill(**kwargs).save_self(session=self._session, auto_commit=auto_commit)
            # model_obj를 save_self하려면 setter로 만들어야한다
            # => save_self는 더이상 self류에게 session을 주지 안흔ㄴ다.

            # => 새로 생긴 결과물 model_obj를 update 데이터를 fill하되,
            # => model에게 save하라고 하지말고 target을 넘겨서 self로 한다?!
            #    like self.delete_self(target=model_obj, auto_commit=auto_commit)
            # return self.save_self(target=model_obj.fill(**kwargs), auto_commit=auto_commit)

            #### self가 아닌 차 model_obj가 update가 끝나 commit까지 했다면, 밖으로 return시 Detached된 상태가 된다.
            # => 이 경우, repr가 찍힐 때 session에러 난다.
            # => 외부session + auto_commit False가 아닌 경우에는 [commit끝난 updated model_obj를 외부에서 쓸 순 없다]
            updated_model_obj = self.save_self(target=model_obj.fill(**kwargs), auto_commit=auto_commit)
            # => 외부세션이라서 auto_commit=False 일 때만 updated_model_obj가 sessoin에 남아 외부에 return할 수 있다.
            # => self._sesion에서 타 mode_obj를 업뎃 후 commit했다면 session에서 사라진 상태라 repr 등 .name에 접근할 수 없다.
            if auto_commit is False:
                return updated_model_obj
            return True

        # 2) filter_by로 생성된 상황이 아닌, 순수모델객체에서 호출되는 경우
        # => 이미 init_session을 해놨기 때문에 model obj라도 session이 보급된 상태다.
        # => .save_self()는 객체 실행메서드로서 내부에서 session을 체크하고 확인한다.
        else:
            # self.set_session_and_query(session) # => 앞으로 뺀다.
            return self.fill(**kwargs).save_self(auto_commit=auto_commit)

    # for delete
    def delete_self(self, target=None, auto_commit: bool = True):
        # mixin 15.  앞으로 session_obj든 model_obj든 session_obj은 setter로 set_session으로  보장받는다.
        # => query가 차이만 난다.
        # self.set_session_and_query(session)
        if not target:
            target = self

        self._session.delete(target)
        self._session.flush()

        if auto_commit:
            self._session.commit()

        return target

    # delete
    # => session인자: filter_by시에는 필요없지만, model_obj호출시 외부session을 받는 경우 + filter_by에 내부생성했어도 외부껄로 바꿀 때
    #   원래는 filter_by시 외부세션을 넣어주는게 더 좋다.
    def delete(self, session: Session = None, auto_commit: bool = True):
        """
        1. filter_by()조건에 1개의 obj만 검색될 경우, 바로 delete
            1) 내부 .one()에서 하나도 안나온 경우
            Category.filter_by(name='2').delete()
            => No row was found when one was required
            => False

            2) 1개만 나온 경우
            Category.filter_by(name='333').delete()
            => Category[name='333']


        2. model_obj에서 .delete()호출
            c3 = Category.filter_by(name='3').first()
            c3.delete()
            => Category[name='3']

        """
        # 삭제시 FK 제약조건이 뜰 수 있다.

        # mixin 18.
        #  filter_by를 통해 오는 경우, 이미 session을 가지고 있지만, 그것으로 .one()검색하는데, 그전에 바꾸려면 미리 바꿔야한다.
        # => 메서드에서 session이 새로 들어올 경우만 바꾸도록 작성한다.
        # 1) filter_by를 거쳐오는 경우 session가진 상태 => session만 여기서 바꾸고 내부에서 query는 건들지 않는다.
        # 2) mode_obj인 경우, session을 안가진 상태 => session 내부생성 or 외부 주입
        # => 2경우 모두 공통이므로 앞으로 뺀다.
        # => 그렇다면 model_obj(객체.delete) vs session_obj(filter_by.delete) 구분 => query로 한다
        self.set_session(session)

        # 1) filter_by에 의해 query + session이 들어왔을 때 => 찾아서 session으로 delete
        # => User.filter_by().delete90
        if self.is_query_obj:
            try:
                model_obj = self.one()
            except Exception as e:
                print(e)
                return False

            return self.delete_self(target=model_obj, auto_commit=auto_commit)

        else:
            # 2) model_obj.delete(session)으로 들어왓을 때 => query가 is None 상태다.
            # => u1.delete()
            return self.delete_self(auto_commit=auto_commit)

    #### 공통으로 쓸 session을 필수로 받아서, 한번에 commit
    @classmethod
    def delete_by(cls, session: Session = None, auto_commit: bool = True, **kwargs):
        """
        pk나 unique key 1개를 keyword로 받고, value에는 1개 혹은 list를 받아서
        => 여러 데이터를 지울 수 있다.
        Category.delete_by(id=3)
        Category.delete_by(name=['335', '12'])
        """
        # filter_by(객체+query생성) 없이  => cls용 실행메서드이며, cls메서드 단위로 session보급하기.
        # => cls 내부에서 1번만 보급 or 생성 => obj의 delete()마다 여러번 돌려쓴 뒤, 맨 마지막에 commit
        if session is None:
            session = db.get_session()

        pk_or_uks = tuple(kwargs.keys())
        if len(pk_or_uks) != 1:
            raise Exception(f'keyword는 pk 혹은 uniqkue key 1개만 입력해주세요.: {pk_or_uks}')

        pk_or_uk = pk_or_uks[0]
        if pk_or_uk not in (cls.pks + cls.uks):
            raise Exception(f'keyword는 pk 혹은 uniqkue key여야 합니다.: {pk_or_uk}')

        values = kwargs.get(pk_or_uk, [])

        if not isinstance(values, (list, tuple, set)):
            values = [values]  # tuple()로 씌우면, 1개짜리 string은 iterable로 생각해서 '12' -> '1', '2'가 되어버림.

        fails = []
        for value in values:
            obj = cls.get(session=session, **{pk_or_uk: value})

            # 실패1) 해당 pk or uk로 검색시 객체가 없는 경우
            if not obj:
                fails.append(value)
                continue

            # 실패2) delete에 실패한 경우

            # auto_commit 주지말고 외부session 재활용으로 이어나가도록 함.
            result = obj.delete(session=session, auto_commit=False)
            if not result:
                fails.append(value)

        if fails:
            print(f'삭제에 실패한 목록: {fails}')

        if auto_commit:
            session.commit()

    @classmethod
    def get_all(cls, session: Session = False, order_bys=None):
        """
        User.get_all(order_bys="id")
        [User[id=1,username='admin',], User[id=2,username='asdf15253',]]

        User.get_all(order_bys="-id")
        [User[id=2,username='asdf15253',], User[id=1,username='admin',]]
        """
        # filter_by를 사용하는 cls메서드는 따로 BaseQuery를 사용하지 않고, obj를 반환받는다.
        # mixin 8. cls.filter_by()의 객체 생성은,
        obj = cls.filter_by(session=session)

        if order_bys:
            if not isinstance(order_bys, (list, tuple, set)):
                order_bys = [order_bys]

            obj = obj.order_by(*order_bys)

        results = obj.all()

        return results

    @classmethod
    def get_by(cls, session: Session = None, **kwargs):
        """
        인자는 pk 혹은 unique key만 허용한다.

        1. 조회할려던 keyword 값이 1개이면,list든 값1개든, 1개의 값으로 반환 -> 객체 or None

        Category.get_by(name='카테고리11')
        => Category[name='카테고리11']

        Category.get_by(name=['카테고리11'])
        => Category[name='카테고리11']


        2. 여러개를 조회 -> 객체list or 빈list [ ] 로 반환

        Category.get_by(name=['카테고리11', '335'])
        => [Category[name='카테고리11'], Category[name='335']]

        Category.get_by(name=['ㅇㅁㄴㅇ','ㅁㄴㅇㄹ'])
        => 조회에 실패한 목록: ['ㅇㅁㄴㅇ', 'ㅁㄴㅇㄹ']
        => []
        """
        # filter_by(객체+query생성) 없이  => cls용 실행메서드이며, cls메서드 단위로 session보급하기.
        # => cls 내부에서 1번만 보급 or 생성 => obj의 delete()마다 여러번 돌려쓴 뒤, 맨 마지막에 commit
        is_served = True
        if session is None:
            is_served = False
            session = db.get_session()

        pk_or_uks = tuple(kwargs.keys())
        if len(pk_or_uks) != 1:
            raise Exception(f'keyword는 pk 혹은 uniqkue key 1개만 입력해주세요.: {pk_or_uks}')

        pk_or_uk = pk_or_uks[0]
        if pk_or_uk not in (cls.pks + cls.uks):
            raise Exception(f'keyword는 pk 혹은 uniqkue key여야 합니다.: {pk_or_uk}')

        values = kwargs.get(pk_or_uk, [])

        # 값이 1개라면, 한번만 get해서 보내주기
        if not isinstance(values, (list, tuple, set)):
            values = [values]

        results = []
        fails = []
        for value in values:
            obj = cls.get(session=session, **{pk_or_uk: value})

            # 실패1) 해당 pk or uk로 검색시 객체가 없는 경우
            if not obj:
                fails.append(value)
                continue

            results.append(obj)

        if fails:
            print(f'조회에 실패한 목록: {fails}')

        session.flush()

        # 외부보급session이 아니라, 자체 생성한 session이면, 직접 close까지
        if not is_served:
            session.close()

        # 조회값(values list)이 1개였던 경우에는 list를 풀어서 반환(조회되면 [0], 조회값없으면 None)
        if len(values) <= 1:
            if results:
                return results[0]
            return None

        return results
