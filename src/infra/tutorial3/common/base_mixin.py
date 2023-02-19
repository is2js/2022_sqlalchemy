"""
base_query 기반으로 각 model들의 쿼리들을 실행할 수 있는 mixin 구현
"""
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint, exists
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, RelationshipProperty

from src.infra.config.base import Base
from src.infra.config.connection import db
from src.infra.tutorial3.common.base_query import BaseQuery
from src.infra.utils import class_property

# for def const_column_names()
constraints_map = {
    'pk': PrimaryKeyConstraint,
    'fk': ForeignKeyConstraint,
    'unique': UniqueConstraint,
}


# 1. model들이 자신의 정보를 cls.로 사용할 예정(객체 만들어서 chaining)이라면, Base를 상속해서 Mixin을 만들고, model은 Mixin을 상ㅅ속한다.
# => 그외 객체생성없이 메서드만 추가할 Mixin은 부모상속없이 그냥 만들면 된다.
# 1-2. 정의해준 BaseQuery의 class메서드들을 쓸 수 있게 한다?! => 그냥 import한 것으로 사용만할까?
class BaseMixin(Base, BaseQuery):
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
    def __init__(self, session=None, query=None, **kwargs):
        # 3. super() 인자 생략하면, super(나, self)로서 => [나의 상위(super)]에서부터 찾아쓰게
        # 인자 super(나 or 부모class중 택1, self)를 줘서 구체적인 부모를 지정할 수 있다.
        # => 나를 첫번째 인자로 주면, 나(BaseMixin)의 부모(super) -> Base부터 찾는다는 뜻이다.
        super(BaseMixin, self).__init__(**kwargs)
        self._query = query
        # 4. 객체를 생성하는 순간 chaining이 시작될 땐, 외부에서 사용중이던 session이 안들어오면 새 session을 배급한다.
        # => 배급한 session은 실행메서드들이 close를 꼭 해줄 것이다.
        self.served = None  # => 뒤에서 self._get_session에서 초기화해준다.
        self._session = self._get_session(session)
        # print('create obj session >   >> ', self._session)

    # 감춰진 query를 setter만 가능하도록
    # => 생성자에서도 self._query에 query=로 주고 있음.
    @property
    def query(self):
        raise AttributeError("query can't not read.")

    @query.setter
    def query(self, query):
        self._query = query

    # 1. obj의 session처리
    def _get_session(self, session):
        # 새로 만든 session일 경우 되돌려주기(close처리) 상태(self.served=)를  아직 False상태로 만들어놓는다.

        if not session:
            session, self.served = db.get_session(), False
            return session

        # 외부에서 받은 session을 받았으면 served로 확인한다.
        self.served = True
        return session

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
    def first(self):
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
    def save_self(self, session: Session = None, auto_commit: bool = True):
        self.set_session(session)

        #### try/catch는 외부세션을 넣어주는데서 할 것이다?
        self._session.add(self)
        # 1. add후 id, 등 반영하기 위해 [자체생성/외부받은 session 상관없이] flush를 때려준다.
        self._session.flush()
        # 2. 외부session인 경우, 외부의 마지막 옵션으로 더이상 사용안한다면 밖에서 auto_commit=True로 -> commit()을 때려 close시킨다.
        # => self.close()는 외부session을 flush()만 시키는데, 외부session이 CUD하는 경우, 자체적으로 commit()해야한다.
        # => 외부에서 더 쓴다면, 외부에서 sessino=sesion만 넣고 auto_commit 안하면 된다.
        if auto_commit:
            self._session.commit()

        return self

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

    # 추가) order_by는 filter_by없이 class메소드로도 쓰일 것 같음
    # => 이럴 경우, order_by에서 cls() obj를 만들어줘야한다.

    #### 5. Filter-> Get / Create부터는 내부에서 객체생성 with session => 실행까지 될 예정이므로
    ####   @classmethod로 작성한다.
    @classmethod
    def filter_by(cls, session: Session = None, selects=None, **kwargs):
        """
        User.filter_by(id=1)
        -> User[id=None]

        User.filter_by(selects=['username'], id=1).all()
        -> ['admin']

        """
        query = cls.create_select_statement(cls, filters=kwargs, selects=selects)
        obj = cls(session=session, query=query)  # served는 session여부에 따라서 알아서 내부 초기화 됨.

        return obj

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

    def get_unique_key(self):
        self_unique_key = next((column_name for column_name in self.column_names if column_name in self.uks), None)
        # print('unique_key  >> ', self_unique_key)
        if not self_unique_key:
            # 3) 유니크 키가 없는 경우, 필터링해서 존재하는지 확인할 순 없다.
            raise Exception(f'생성 전, 이미 존재 하는지 유무 확인을 위한 unique key가 존재하지 않습니다.')

        return self_unique_key

    #### create/update/delete는 session을 받아올 경우 auto_commt여부도 받아야한다.
    #### 아직 add되지 않은 객체용.
    def exists_self(self, session: Session = None):
        """
        그냥 존재검사(.exists())가 아니라, 생성시 kwargs를 바탕으로 유니크key를 골라내서 검사함

        User(username='관리자', sex=0, email='tingstyle1@gmail.com').exists()
        self.uks  >>  ['username']
        self.column_names  >>  ['add_date', 'pub_date', 'id', 'username', 'password_hash', 'email', 'last_seen', 'is_active', 'avatar', 'sex', 'address', 'phone', 'role_id']
        self_unique_key  >>  username
        """
        self.set_session(session)

        # 1) 생성하려고 준 정보중에 unique 칼럼을 찾고, 그것으로 조회한다.
        # print('self.uks  >> ', self.uks)
        # 2) 이미 obj = cls()가 생성되면, 각 칼럼columns에 값이 입력된 상태다. super().__init__(**kwags)에 의해
        # print('self.column_names  >> ', self.column_names)
        # 2) 여러개 중에 1개만 뽑은 뒤
        self_unique_key = self.get_unique_key()

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
        obj_query = self.create_select_statement(model=self.__class__,
                                                 filters={self_unique_key: getattr(self, self_unique_key)},
                                                 )
        self.query = obj_query

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
        obj = cls(session=session, **kwargs)

        # db들어가기 전 객체의 unique key로 존재 검사
        if obj.exists_self(auto_commit=False):
            return False

        return obj.save_self(auto_commit=auto_commit)

    #### update는 filter_by로 객체를 찾아놓은 과정에서, 생성된  obj에 _query에 update만 하도록 되어있어
    # => 내부 self._session을 가지고 있는 obj상태로서, 실행메서드(self 인스턴스 메서드)에 가깝다
    # => auto_commit여부를 받는다.
    # => setattr()로 받은 인자를 넣어주는데, 여러 검증이 필요하기 때문에 fill이라는 메서드로 빼준다.
    @class_property
    def settable_column_names(cls):
        return cls.column_names + cls.settable_relation_names + cls.hybrid_property_names

    def fill(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.settable_column_names:
                raise KeyError(f"Invalid column name: {key}")
            setattr(self, key, value)

        return self

    # 실행메서드 결과로 나온 순수 model obj 객체들(filter_by안한)의 session 보급
    def set_session(self, session):
        if not hasattr(self, '_session') or not self._session:
            self._session = self._get_session(session)
            self.query = None  #

    # self._query가 차있다면, filter_by에 의해 나온 session_obj
    # 없다면 model_obj
    @property
    def has_session(self):
        return hasattr(self, '_session') and self._session

    def update(self, session: Session = None, auto_commit: bool = True, **kwargs):
        #### 문제는 User.get()으로 찾을 시, cls() obj가 내포되지 않아 self내부 _session이 없다.
        # => filter_by()로 찾은 객체는, 아직 실행하지 않았으면 cls() obj로서 내부 _session을 가지고 있다.
        # => 실행해버리면.. 없다.
        # => 자체적으로 현재 self에 보급해주는 로직을 만들어야한다.
        # => self.set_session(session)
        """
        1. filter_by없이 결과메서드 이후 결과객체에서 _session없는 상태
        # 1) self.has_sessoin이 없으면 => self.set_session으로 순수model obj도 내/외부 session을 가질 수 있게 함.
        # 2) 순수model obj가 받거나 생성한 session으로 fill(**kwargs)이후 .save_self()함

        Category.get_all()
        [Category[name='ㅓㅓ'], Category[name='456'], Category[name='555']]
        c1.update(auto_commit=True, name='ㅏㅏ')
        Category.get_all()
        [Category[name='ㅏㅏ'], Category[name='456'], Category[name='555']]

        2. filter_by로 객체 생성하면서, session보급받은 상태
        # => 가진 세션으로 일단 update전 순수model 1개를 select한다.
        # => 셀렉된  순수model obj는 session이 없는 상태이므로 fill은 가능 save는 불가능이다.
        # => 실행메서드 .save_self(session=)에 바깥 filter_by obj의 session을 받아서, 자신의 session을 채우고, .save_self()를 수행한다

        Category.filter_by(id=1).update(auto_commit=True, name='aa')
        Category.get_all()
        [Category[name='aa'], Category[name='456'], Category[name='555']]

        3. filter_by로 걸었는데, 1개가 아닌 여러개가 발견되거 안발견되는 경우

        Category.filter_by(id__gt=3).update(auto_commit=True, name='카테1')
        => No row was found when one was required
        => False
        Category.filter_by(id__lt=3).update(auto_commit=True, name='카테1')
        => Multiple rows were found when exactly one was required
        => False


        """
        #### 실행 후 순수model객체(filter_by안거친)의 실행메서드로서 실행 전 session보급
        # filter_by로 실행안한 상태의 객체를 검사 => 미리 세션보급 필요함.
        # self.set_session(session)

        # => 만약 filter_by가 아니라 cls() X => self._session 없는 상태면, self._query도 None상태이므로 이것으로 감별한다.
        #    session은 두 경우 모두 차있다.
        # => self._query를 가졌는지 거기에 차있는지 확인하는 메서드 is_session_obj구현이후로는
        #    그것의 else에 두도록 위치 변경

        # 1) filter_by로 생성된 경우(self._query가 차있는 경우) => statment은 불린처리 안됨.
        #    => 여러개 필터링 될 수도 있다..
        # if self._query is not None:
        if self.has_session:
            try:
                model_obj = self.one()
            except Exception as e:
                print(e)
                return False
            # 찾은 model 객체를 바꾼 뒤, 현재 obj(filter_by)의 세션으로 add
            # => mode_.obj에는 session이 안들어있어서, .save()를 호출 못한다?!
            # => .save()도 session을 받을 수 있도록 변경하자?!
            # => 자체 세션이 없는 model_obj만 .save()에 외부session을 주입해서 save하자.

            # 당근 순수model obj는 가진 세션이 없어서 외부session을 넣어준다.
            # => 안넣어주면 자체적으로 set_session시 생성할 수 있지만, 1개를 재활용한다.
            return model_obj.fill(**kwargs).save_self(session=self._session, auto_commit=auto_commit)

        # 2) filter_by로 생성된 상황이 아닌, 순수모델객체에서 호출되는 경우
        # => 이미 init_session을 해놨기 때문에 model obj라도 session이 보급된 상태다.
        # => .save_self()는 객체 실행메서드로서 내부에서 session을 체크하고 확인한다.
        else:
            self.set_session(session)
            return self.fill(**kwargs).save_self(auto_commit=auto_commit)

    def delete_self(self, session: Session = None, auto_commit: bool = True):
        self.set_session(session)

        self._session.delete(self)
        self._session.flush()

        if auto_commit:
            self._session.commit()

        return self

    # delete
    def delete(self, session: Session = None, auto_commit: bool = True):
        """

        :param session:
        :param auto_commit:
        :return:
        """
        # 삭제시 FK 제약조건이 뜰 수 있다.
        if self.has_session:
            try:
                model_obj = self.one()
            except Exception as e:
                print(e)
                return False

            return model_obj.delete_self(session=self._session, auto_commit=auto_commit)

        else:
            self.set_session(session)

            self.delete_self(auto_commit=auto_commit)
            self._session.flush()

            if auto_commit:
                self._session.commit()

            return self

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
            values = [values] # tuple()로 씌우면, 1개짜리 string은 iterable로 생각해서 '12' -> '1', '2'가 되어버림.

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
        obj = cls.filter_by(session=session)

        if order_bys:
            if not isinstance(order_bys, (list, tuple, set)):
                order_bys = [order_bys]

            obj = obj.order_by(*order_bys)

        result = obj.all()

        return result

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
        if session is None:
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

        # 조회값(values list)이 1개였던 경우에는 list를 풀어서 반환(조회되면 [0], 조회값없으면 None)
        if len(values) <= 1:
            if results:
                return results[0]
            return None

        return results
