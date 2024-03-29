import _thread
import datetime
import enum
from collections import OrderedDict, defaultdict, abc
from collections.abc import Iterable

from sqlalchemy import MetaData, select, func, text, exists
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import InstrumentedAttribute, aliased, contains_eager, Session, RelationshipProperty, sessionmaker, \
    scoped_session, object_session
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.exc import DetachedInstanceError

from src.infra.config.connection import db
from src.infra.tutorial3.mixins.base_query import BaseQuery
from src.infra.tutorial3.mixins.utils.classorinstancemethod import class_or_instancemethod

# Base = declarative_base()
# naming_convention = {
#     "ix": 'ix_%(column_0_label)s',
#     "uq": "uq_%(table_name)s_%(column_0_name)s",
#     "ck": "ck_%(table_name)s_%(column_0_name)s",
#     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
#     "pk": "pk_%(table_name)s"
# }
# Base.metadata = MetaData(naming_convention=naming_convention)
from src.infra.tutorial3.mixins.utils.classproperty import class_property

JOINED = 1
DESC_PREFIX = '-'
RELATION_SPLITTER = '___'


def _flat_schema(schema: dict):
    """
    schema = {
        'user': JOINED, # joinedload user
        'comments': (SUBQUERY, {  # load comments in separate query
            'user': JOINED  # but, in this separate query, join user
        })
    }
    => {'user': JOINED, 'comments': SUBQUERY, 'comments.users': JOINED}
    ----
    self-relation를 위한 depth만큼 eagerload하는 기능 추가
    d = Department.load({'children':'selectin'}).filter_by(id=1).first()
    d.children[0]
    => Department(id=2, name='하위부서1', parent_id=1, sort=1, path='001001')
    Department(id=2, name='하위부서1', parent_id=1, sort=1, path='001001')
    d.children[0].children[0]
    => sqlalchemy.orm.exc.DetachedInstanceError:

    d = Department.load({'children':('selectin', 3)}).filter_by(id=1).first()
      >>  {'children': 'selectin', 'children.children': 'selectin', 'children.children.children': 'selectin'}
    d.children[0].children[0]
    => Department(id=5, name='ㅋㅋㅋ', parent_id=2, sort=1, path='001001001')
    d.children[0].children[0].children[0]
    Department(id=6, name='ㅇㅇ', parent_id=5, sort=1, path='001001001001')
    """
    if not schema:
        return {}

    def _flat_recursive(schema, parent_column_name, result):
        for rel_column_name_or_prop, value in schema.items():
            # 관계칼럼을 넣은 경우 ex> User.posts -> 'posts'의 관계칼럼명으로 변환
            if isinstance(rel_column_name_or_prop, InstrumentedAttribute):
                rel_column_name_or_prop = rel_column_name_or_prop.key

            # 1) 'posts' : ('joined', {  }) inner_schema로서 한번 더 평탄화 하기
            if isinstance(value, tuple):
                # 1-1) 추가. tuple인데, 1번째 인자가 inner_schema가 아닌 int로 왔을때
                #      'posts': ('joined', 3) -> inner_schema와 관련없이 자체적으로 depth(.)를 주며 eagerload시킨다.
                # => 그만큼 반복해서 eagerload하게 하기(현재를 부모칼럼으로 한 + int -1로  inner_schema만들기)
                if type(value[1]) == int:
                    eager_type = value[0]

                    load_repeat_count = value[1]
                    current_column_name = parent_column_name + '.' + rel_column_name_or_prop if parent_column_name \
                        else rel_column_name_or_prop

                    while load_repeat_count > 0:
                        result[current_column_name] = eager_type

                        load_repeat_count -= 1
                        current_column_name += '.' + rel_column_name_or_prop
                    # print('result  >> ', result)
                    continue

                else:
                    eager_type, inner_schema = value[0], value[1]

            # 2) 'posts' : {'tags'} 로 tuple이 아닌 그냥 관계명을 던지는 경우
            # -> inner_schema로서 'posts' : ('joined', {'tags' : ??? })로 간주하기
            elif isinstance(value, dict):
                eager_type, inner_schema = JOINED, value

            # 3) 'posts만 오는 경우 -> inner_schema가 없음. posts만 저장해놓기
            else:
                eager_type, inner_schema = value, None

            current_column_name = parent_column_name + '.' + rel_column_name_or_prop if parent_column_name \
                else rel_column_name_or_prop
            result[current_column_name] = eager_type

            if inner_schema:
                _flat_recursive(inner_schema, current_column_name, result)

    result = {}
    _flat_recursive(schema, '', result)

    return result


def _flat_dict_attrs_generator(filters):
    for key, value in filters.items():
        if key.lower().startswith(('and_', 'or_')):
            # yield의 depth없는 재귀 호출은 yiedl from 메서드(자식)으로 한다.
            yield from _flat_dict_attrs_generator(value)
        # 나 자신의 처리(방출)
        else:
            yield key


def format_datetime(value, fmt='%Y-%m-%d %H:%M'):
    formatted = value.strftime(fmt.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    return formatted


def format_date(value, fmt='%Y-%m-%d'):
    formatted = value.strftime(fmt.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    return formatted


def transform_int_enum_in_row(row, column_names, to_name=False):
    """
    row 변환한 것을 list append없이 한번에 모으기 위해, return 모은 것(X)
    =>  yield 모아야할 값들 1개씩 방출(추가처리가능) => 메서드 바깥에선 tuple(generator)로 한번에 모으기 가능
    """
    for column_name in column_names:
        _value = getattr(row, column_name)
        if isinstance(_value, enum.IntEnum):
            if to_name:
                yield _value.name
            else:
                yield _value.value
        else:
            yield _value


def create_session_generator(session_cls):
    db_session = None
    try:
        db_session = session_cls()
        yield db_session
    except:
        db_session.rollback()
        raise
    finally:
        # print('자동 close >> ')
        # db_session.close()
        print('자동 remove >> ')
        db_session.close()


Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class ObjectMixin(Base, BaseQuery):
    __abstract__ = True

    # 호출되진 않지만 명시만 -> 실제 초기화는 .init_obj에서
    def __init__(self):
        # thread별 scoped session 생성할 때마다 저장
        self._sessions = {}

        self.served = None
        self._session = None
        self._query = None
        self._flatten_schema = None
        self._loaded_rel_paths = None
        self._alias_map = None
        self._expression_base = None

    # 1. 비sqlite or only API 사용을 위한 경우, 공유할 session 1개만 받는다.
    scoped_session = None

    @classmethod
    def set_scoped_session(cls, scoped_session):
        cls.scoped_session = scoped_session

    # 2. sqtlie + flask-jinja를 사용하여
    # 1) app.context_processor(inject_category_and_settings)처럼
    #    route login외 서로 다른 thread에서 session이 호출될 우려가 있는 경우
    _engine = None

    @classmethod
    def set_engine(cls, engine):
        cls._engine = engine

    @classmethod
    def get_scoped_session(self):
        # for template engine + sqlite (1thread only 1session)
        if self._engine:
            thread_id = _thread.get_ident()  # get thread id
            if thread_id in self._sessions:
                return self._sessions[thread_id]

            Session = scoped_session(sessionmaker(bind=self._engine))
            self._sessions[thread_id] = Session()
            return self._sessions[thread_id]

        elif self.scoped_session:
            return self.scoped_session

        else:
            raise Exception(f'engine or scoped session을 삽입해주세요.')

    #### FastAPI - DependsOn( model.get_session ) => generator 생성 메서드를 호출하지 않고 입력
    # 1) @property or @class_property로 정의해서 DependsOn내부 contextmanger에서 호출
    # 2) 알아서 () 호출후, next()까지 호출하는 듯.
    # 3) 일반 호출은 finally도 동시에 호출되지만, DependsOn 내부에서는 yield끝나고 호출됨.
    #    일반 사용하고 싶다면, next(model.get_session())로 생성하고 꺼내쓰기?
    # => fastapi 예시: https://kkminseok.github.io/posts/fastapiAlchemy03/
    @class_property
    def get_session(cls):
        return cls.create_session_generator

    # contextmanager에서만 yield끝난 뒤 filnally가 시작되어 -> fastAPI의 Depends( model.get_session () ) 용
    @classmethod
    def create_session_generator(cls):
        db_session = None
        try:
            db_session = cls.scoped_session()
            yield db_session
        except:
            db_session.rollback()
        finally:
            print('자동 close')
            db_session.close()

    ####  FastAPI ###############

    #
    # ADDITIONAL_ATTRS = ['_session', 'served', '_flatten_schema', '_query', '_loaded_rel_paths', '_alias_map',
    #                     '_expression_based']

    #### session을 들고 있는 객체 상태에서 그 dialect뽑아내기
    @property
    def db_dialect(self):
        """
         Category.filter_by().db_dialect  / self.db_dialect
         => 'sqlite'
        """
        if not self._session:
            raise Exception(f'Current no session')

        # >>> s.bind.dialect
        # <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x000002B099E804A8>
        # >>> s.bind.dialect.name
        # 'sqlite'
        return self._session.bind.dialect.name

    @classmethod
    def _get_session_and_mark_served(cls, session):
        # 새로 만든 session일 경우 되돌려주기(close처리) 상태(cls.served=)를  아직 False상태로 만들어놓는다.

        if not session:
            # session, cls.served = db.get_session(), False
            session, cls.served = cls.session_generator(), False
            return session

        # 외부에서 받은 session을 받았으면 served로 확인한다.
        cls.served = True
        return session

    @classmethod
    def create_session(cls):
        return cls.session_generator()

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

    @classmethod
    def create_obj(cls, session: Session = None, query=None, schema=None,
                   filter_by=None, order_by=None, selects=None, having=None, **kwargs):

        obj = cls().init_obj(session=session, query=query, schema=schema)
        if kwargs:
            obj.fill(**kwargs)

        obj.set_attrs(filter_by=filter_by, order_by=order_by, selects=selects, having=having)

        return obj

    ###################
    # Fill for create_obj/Update/Create # -> .save()하기 전에, 채울 때 settable_column_name인지 확인용 / 같은 값은 아닌지 확인용으로 사용할 수 있다.
    ###################
    # for Update + for Create + for create_obj
    def fill(self, **kwargs):
        # is_updated = False

        for column_name, new_value in kwargs.items():
            # flask form.data(dict)로 항상 들어오는 'csrf_toekn'와  form으로 들어오는 hidden태그는 무시
            #    + hidden 태그도 혹시 들어오면 에러내지말고 pass
            if column_name in ['csrf_token', 'submit'] or column_name.startswith('hidden_'):
                continue

            # settable_column_names외에 @property or @hybrid_prorperty(cls.attr로 인식)도 .setter or .expression 있으면 허용한다.
            if column_name not in self.settable_column_names and not self.is_setter_or_expression(column_name):
                raise KeyError(f"Invalid column name: {column_name}")

            # 같은 값은 업데이트 안하고 넘김
            # => hybrid_property는 읽는 것을 생략하자. property는 get을 거부할 수 있다.
            # if getattr(self, column_name) == new_value:
            # if getattr(self, column_name) == new_value:
            # if column_name not in self.hybrid_property_names and getattr(self, column_name) == new_value:
            # => settable(하이브리드proeperty + method) 은 통과했지만, 값비교시 꺼내는 것은 순수 column만 꺼내서 비교하기
            if column_name in self.column_names and getattr(self, column_name) == new_value:
                continue

            ## keyword에 relation propperty가 uselist=False면, 해당class type의 객체가 뜨지만
            # => many relationship이 keyword로 오면,
            # -> employee_departments: type: sqlalchemy.orm.collections.InstrumentedList
            # -> 그렇다면 입력 many객체가 1개면, many에 append / list가 오면 덮어쓰는 것(일반 setter와 같음)로 정한다.
            # -> many에 append를 하면 기존에 있던 것이라면, session.merge()에 의해 자동 수정반영된다.
            ## property가 password라서 읽으면 에러나는 것인데, many relationship 검사를 할 수도 있다.
            # -> 이 때 확인하는 과정에서 에러가 나 버린다.
            # -> 해당이 column_name이 relation_property일때만 검사하도록 수정한다.
            # if isinstance(getattr(self, column_name), InstrumentedList) \
            if column_name in self.relation_names and isinstance(getattr(self, column_name), InstrumentedList) \
                    and not isinstance(new_value, list):
                getattr(self, column_name).append(new_value)
            else:
                setattr(self, column_name, new_value)

        return self  # 한번 이라도 업뎃되면 True/ 아니면 False 반환

    # for fill
    # settable_column_names외에 @property라도 setter가 있으면 허용한다.
    # -> settable_column_names에 포함하지 않은 이유는, @property 목록에서 순회하며 검사해야하는 것을 피하기 위해
    # -> settable_column_names가 아니면서 && [@property.setter도 아니면] 탈락 => 탈락조건에 and로 추가하여
    # => 통과는 A or B로 되게 한다.
    # Employee.role.setter: <built-in method setter of property object at 0x000001B92EA08B88>
    def is_setter_or_expression(self, column_name):
        return hasattr(getattr(self.__class__, column_name), 'setter') or \
               hasattr(getattr(self.__class__, column_name), 'expression')

        # for exists_self + for update - fill - settable column snames

    @class_property
    def column_names(cls):
        return cls.__table__.columns.keys()

    # for update - fill
    @class_property
    def settable_column_names(cls):
        return cls.column_names + cls.settable_relation_names + cls.hybrid_property_names

    @class_property
    def settable_relation_names(cls):
        """
        User.settable_relation_names
        ['role', 'inviters', 'invitees', 'employee']
        """
        return [prop for prop in cls.relation_names if getattr(cls, prop).property.viewonly is False]

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

    # for update - fill
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

    def init_obj(self, session: Session = None, query=None, schema=None):
        self._sessions = {}

        self.served = None  # set_session_and_check_served에서 T/F 초기화
        self._session = self.set_session_and_check_served(session)  # 내부에서 어떻게든 None 아닌 것으로 초기화
        self._query = self.set_query(query) if self.set_query(query) is not None else select(self.__class__)
        self._flatten_schema = self.set_schema(schema) or {}
        self._loaded_rel_paths = []
        self._alias_map = OrderedDict({})
        # 사실상 query가 미리 주어지는 것도 select(cls)가 아닌 미리 selects를 주는 것과 같아서
        # -> selects => set_attrs가 아니고 미리 selects문장을 만든 query도 주어진다면, expression based로 봐야한다.
        self._expression_based = False if query is None else True

        return self

    # 외부인자 없어도 내부 생성해서 반환한다.
    def set_session_and_check_served(self, session):

        # 1) 외부session주어지면, 기존session가진 것 여부 상관없이 그것으로 교체 or 초기화
        if session:
            self._session = session
            self.served = True
            return self._session
        # 2) 외부session이 없는 경우 -> 기존 session 확인후 존재하지 않을 때만 ~~session 새로 생성~~ => scoped_session 배정으로 변경
        #    외부X 내부O시 그것을 그대로 활용
        else:
            # 3) 기존 session확인하기 전에, 있는지 초기화여부부터 확인해야한다.?!
            if not hasattr(self, '_session'):
                self._session = None

            # 4) 초기화가 보장되었다면, 기존 것을 확인한 뒤 없으면 내부생성 초기화.(not return False 초기화)
            # => 내부 생성대신 scoped_session 박힌 것을 재활용
            if self._session is None:
                # self._session = self.scoped_session # sqlite에서는 1개의 scpoed_session을 사용시 스레드 다른 곳에서 사용하는 에러
                self._session = self.get_scoped_session()
                self.served = False

                return self._session
            # 3) 외부x, 내부o라면, scoped_session 사용 중 => 새로운 session set실패했다고 return False하면 안됨.
            #    중간에 생성시 False 초기화 되어버림
            #    => 그것을 그대로 반환하여, 초기화의 일환으로 취급
            else:
                # return False
                # print('self._session  >> ', self._session)
                return self._session

    def set_query(self, query=None, eagerload=None, where=None, order_by=None, options=None, outerjoin=None,
                  group_by=None, having=None, limit=None, offset=None):
        def _is_chaining():
            return not (
                    eagerload is None and where is None and order_by is None and options is None
                    and outerjoin is None and group_by is None and having is None and limit is None
                    and offset is None
            )

        # 1. 외부X -> return False로 초기화 (set실패) -> 초기화시 select(self.__class__)로 초기화
        if not _is_chaining() and query is None:
            return None  # 이것만 return False말고 reutrn None -> 초기화 select(self.__class__)

        # 2. 외부O -> 내부확인후 존재하면 update  VS  초기화빈값이면 assign
        # => 내부는 항상 select(main)으로 존재하게 만들어놨음.
        # if self._query is not None:
        # => 체이닝 여부를 확인하고 아니라면 해당 쿼리를 그냥 삽입하자. for execute용 select(칼럼들).select_from(cls)
        if _is_chaining():
            if not hasattr(self, '_query'):
                self._query = select(self.__class__)

            # 이미 select( main )으로 작성된 상황이라면 체이닝을 해야하는데,
            # -> 하려면 인자로 expression만 받아서, 틀에 끼워넣어줘야한다.
            if eagerload:
                # filter_by, order_by는 cls model객체에 담기위해
                # => 1) outerjoin해서 필터링 가능하게 하고
                # => 2) conatinas_eager를 select(cls)자동으로서, cls 관계필드에 접근하기 위해 container_eager까지
                aliased_rel_model, rel_attr, rel_path = eagerload

                self._query = (
                    self._query
                    .outerjoin(aliased_rel_model, rel_attr)
                    .options(contains_eager(rel_path, alias=aliased_rel_model))
                )

            if outerjoin:
                # eagerload와 다르게, execute용인 group_by / having시에는
                # 1) outerjoin해서 필터링 가능하게 하지만
                # 2) select(cls)가 아닌 select( 필드, 집계필드).select_from(cls) 상황에서는
                # => contains_eager까지 하면, select()에 cls가 포함안된 경우,
                #   can't find property named "employee".로 관계칼럼을 찾지못해 outerjoin이 안된다.
                aliased_rel_model, rel_attr = outerjoin

                self._query = (
                    self._query
                    .outerjoin(aliased_rel_model, rel_attr)
                    # .options(contains_eager(rel_path, alias=aliased_rel_model))
                )

            if where:
                if not isinstance(where, abc.Iterable):
                    raise KeyError(
                        f'입력할 조건 Clause는 list나 tuple에 싸서 입력해주세요. 조건절을 포장 없이 입력하면 True/False로 전달되어 제대로 작동하지 않습니다.'
                    )
                self._query = (
                    self._query
                    .where(*where)
                )

            if order_by:
                if not isinstance(order_by, abc.Iterable):
                    order_by = [order_by]
                self._query = (
                    self._query
                    .order_by(*order_by)
                )

            if options:
                if not isinstance(options, abc.Iterable):
                    options = [options]
                self._query = (
                    self._query
                    .options(*options)
                )

            if group_by:
                if not isinstance(group_by, abc.Iterable):
                    group_by = [group_by]
                self._query = (
                    self._query
                    .group_by(*group_by)
                )

            if having:
                raise KeyError(
                    f'입력할 조건 Clause는 list나 tuple에 싸서 입력해주세요. 조건절을 포장 없이 입력하면 True/False로 전달되어 제대로 작동하지 않습니다.'
                )
                self._query = (
                    self._query
                    .having(*having)
                )

            if limit:
                self._query = (
                    self._query
                    .limit(limit)
                )

            if offset:
                self._query = (
                    self._query
                    .offset(offset)
                )

        # 체이닝이 아닌 query가 들어올 경우, 최초 init시 들어온 query=로서 할당 초기화
        else:
            self._query = query
            #### 쌩쿼리가 입력되면, only expression임을 명시하자
            self._expression_based = True

        return self._query

    def set_schema(self, schema=None):
        if not schema:
            return False  # -> 초기화

        else:
            if not hasattr(self, '_flatten_schema'):
                self._flatten_schema = {}

            if self._flatten_schema:
                self._flatten_schema.update(_flat_schema(schema))
            else:
                self._flatten_schema = _flat_schema(schema)

        return self._flatten_schema

    def set_attrs(self, filter_by: dict = None, having: dict = None, selects=None, order_by=None):

        """
        Column attrs : selects/order_by/group_by

        Conditional attrs mean filters or having
        - filters -> for select(cls) -> all / first etc
        - having -> for select(칼럼들).select_from ->  only execute

        """
        # 한번이라도 selects가 들어오면, expression_based로서 => eager load할 때, outerjoin만 (contains_eager X)
        if selects:
            self._expression_based = True
        # 의존성 필드 포함시 내부에서 같이 초기화 -> 내부/외부여부에 따라 외부x시-> 내부 존재여부 확인후 초기화 -> 외부o시 할당 초기화
        # 1. 외부x시 내부 확인후 없으면 return False 초기화
        # if not (filters or having):
        #     return False  # -> alias_map 초기화

        # 2. 외부o시 내부 존재확인 후 (내부 초기화도 안된 상태일 수 있어서 없으면 초기화까지 추가)
        # if not hasattr(self, '_alias_map'):
        #     self._alias_map = OrderedDict({})
        #    -> 인자들 변환 후
        #    udpate VS 빈값에 할당 => set_alias_map 내부에서
        self.parse_attrs_and_set_alias_map(filter_by=filter_by, having=having, order_by=order_by, selects=selects)

        # 2-2. set된 alias_map -> eager expression 체이닝 후 loaded_rel_paths 채워 업데이트
        # 2-3. ._set_filter_or_order_exprs(filters=filters, orders=orders)
        #### select(group_by)만 query부터 set하고, expr (outer 등)을 삽입
        self.set_queries_and_load_rel_paths(filter_by=filter_by, having=having, order_by=order_by, selects=selects)

        return True

    def parse_attrs_and_set_alias_map(self, filter_by=None, having=None, order_by=None, selects=None):
        attrs = []
        if filter_by:
            attrs += list(_flat_dict_attrs_generator(filter_by))

        if having:
            attrs += list(_flat_dict_attrs_generator(having))

        if selects:
            if selects and not isinstance(selects, abc.Iterable):
                selects = [selects]
            attrs += selects
        if order_by:
            if order_by and not isinstance(order_by, abc.Iterable):
                order_by = [order_by]
            attrs += list(map(lambda s: s.lstrip(DESC_PREFIX), order_by))

        # 2-1. alias_map 채우기 => 내부에서  update VS 빈값에 할당? (자료구조의 경우 update위주로)
        self._set_alias_map(parent_model=self.__class__, parent_path='', attrs=attrs)

    # select()메서드와 겹쳐서 여기만 selects로 인자를 줌
    def set_queries_and_load_rel_paths(self, filter_by=None, having=None, order_by=None, selects=None):
        # select만 먼저 query를 만들어 defatul select(cls)를 덮어쓰도록 set_query를 먼저한다.
        if selects:
            select_column_exprs = self.create_column_exprs_with_alias_map(self.__class__, selects, self._alias_map,
                                                                          self.SELECT)  # select 속 집계함수의 경우, coalese를 붙인다.
            query = (
                select(*select_column_exprs)
                .select_from(self.__class__)  # execute시 cls를 제외하고 싶다면, 구세주.
            )
            self.set_query(query)

            # for_execute는 (칼럼선택상황)으로서 contains_eager를 안한다.select()에 cls없이 칼럼선택하면 에러남. select_from(cls)도 안통하고 에러
            self._set_eager_query_and_load_rel_paths()
        # select가 아니라면, 먼저 outerjoin(+contains_eager)을 하고 나서 해당 query를 set한다.
        else:

            self._set_eager_query_and_load_rel_paths()

            if order_by:
                self.set_query(
                    order_by=self.create_column_exprs_with_alias_map(self.__class__, order_by, self._alias_map,
                                                                     self.ORDER_BY))
            if filter_by:
                # self._set_query_and_load_rel_paths(for_execute=False)
                self.set_query(
                    where=self._create_conditional_exprs_with_alias_map(self.__class__, filter_by, self._alias_map))
            if having:
                # self._set_query_and_load_rel_paths(for_execute=True)
                self.set_query(
                    having=self._create_conditional_exprs_with_alias_map(self.__class__, having, self._alias_map))

    # # filters, orders -> filter_or_order_attrs 통해  alias_map이 채워진다.
    # def process_conditional_attrs(self, filters: dict = None, having: dict = None):
    #     """
    #     Conditional attrs mean filters or having
    #     - filters -> for select(cls) -> all / first etc
    #     - having -> for select(칼럼들).select_from ->  only execute
    #     """
    #     # 의존성 필드 포함시 내부에서 같이 초기화 -> 내부/외부여부에 따라 외부x시-> 내부 존재여부 확인후 초기화 -> 외부o시 할당 초기화
    #     # 1. 외부x시 내부 확인후 없으면 return False 초기화
    #     # if not (filters or having):
    #     #     return False  # -> alias_map 초기화
    #
    #     # 2. 외부o시 내부 존재확인 후 (내부 초기화도 안된 상태일 수 있어서 없으면 초기화까지 추가)
    #     # if not hasattr(self, '_alias_map'):
    #     #     self._alias_map = OrderedDict({})
    #     #    -> 인자들 변환 후
    #     #    udpate VS 빈값에 할당 => set_alias_map 내부에서
    #     filter_or_having_attrs = []
    #     if filters:
    #         filter_or_having_attrs += list(_flat_dict_attrs_generator(filters))
    #     if having:
    #         filter_or_having_attrs += list(_flat_dict_attrs_generator(having))
    #
    #     # 2-1. alias_map 채우기 => 내부에서  update VS 빈값에 할당? (자료구조의 경우 update위주로)
    #     self._set_alias_map(parent_model=self.__class__, parent_path='',
    #                         attrs=filter_or_having_attrs)
    #     # 2-2. set된 alias_map -> eager expression 체이닝 후 loaded_rel_paths 채워 업데이트
    #     # => set_alias_map 시 자동으로 처리되어야하므로 내부의 마지막으로 이동
    #     # => 다시 가져옴. filter/orders 처리와 having(only execute, no select(cls))의 처리가 다름.
    #     if filters:
    #         self._set_query_for_eager_or_execute_and_load_rel_paths(for_execute=False)
    #         self.set_query(
    #             filter_by=self._create_filters_or_having_expr_with_alias_map(self.__class__, filters, self._alias_map))
    #     if having:
    #         self._set_query_for_eager_or_execute_and_load_rel_paths(for_execute=True)
    #         self.set_query(
    #             having=self._create_filters_or_having_expr_with_alias_map(self.__class__, having, self._alias_map))
    #
    #     # 2-3.
    #     # self._set_filter_or_order_exprs(filters=filters, orders=orders)
    #
    #     return True
    #     # 2-4. flatten_schema + loaded_rel_paths -> unloaded schema처리하기
    #     # self._set_unloaded_eager_exprs()
    #     # => unloaded는 .first() 등의 실행메서드로 옮겨감. filter, order 다 처리하고나서 로드
    #
    # def process_non_conditional_attrs(self, selects=None, orders=None):
    #     """
    #      Non conditional attrs mean select or orders
    #     - orders -> for select(cls) -> all / first etc => outerjoin + eagerload
    #     - select -> for select(칼럼들).select_from ->  only execute => only outerjoin
    #     """
    #     selects_or_order_attrs = []
    #     if selects:
    #         if select and not isinstance(select, (list, tuple, set)):
    #             select = [select]
    #         selects_or_order_attrs += select
    #     if orders:
    #         if orders and not isinstance(orders, (list, tuple, set)):
    #             orders = [orders]
    #         selects_or_order_attrs += list(map(lambda s: s.lstrip(DESC_PREFIX), orders))
    #
    #     self._set_alias_map(parent_model=self.__class__, parent_path='',
    #                         attrs=selects_or_order_attrs)
    #
    #     #### select(group_by)만 query부터 set하고, expr (outer 등)을 삽입
    #     if selects:
    #         select_columns = self.create_columns_with_alias_map(self.__class__, select, self._alias_map,
    #                                                             in_selects=True)  # 집계함수의 경우, coalese를 붙인다.
    #         query = (
    #             select(*select_columns)
    #             .select_from(self.__class__)  # execute시 cls를 제외하고 싶다면, 구세주.
    #         )
    #         self.set_query(query)
    #
    #         self._set_query_for_eager_or_execute_and_load_rel_paths(for_execute=True)
    #
    #     if orders:
    #         self._set_query_for_eager_or_execute_and_load_rel_paths(for_execute=False)
    #         self.set_query(order_by=self._create_order_exprs_with_alias_map(self.__class__, orders, self._alias_map))
    #
    #     return True

    # def process_having_eager_exprs(self, having: dict):
    #     if not having:
    #         return False
    #     # filter/orders 재귀로 attrs추출 재활용
    #     having_attrs = list(_flat_dict_keys_generator(having))
    #
    #     self._set_alias_map_and_loaded_rel_paths(parent_model=self.__class__, parent_path='',
    #                                              attrs=having_attrs)
    #     # filter/orders의 select(cls)용 eager exprs (outerjoin + contains_eager)이 다르다.
    #     # <-> groupby(select(칼럼선택).select_from(cls) -> having용 eager exprs(only outerjoin)
    #     # => select(칼럼선택).select_from(cls)는 contains_eager시 rel_path를 못읽는다.
    #     # => only_execute=True옵션을 줘서, 내부에서 contains_eager안하도록 한다.
    #     self._set_eager_exprs_and_load_rel_paths(only_execute=True)
    #
    #     # filter expr 생성을 재활용
    #     self.set_query(
    #         having=self._create_filters_or_having_expr_with_alias_map(self.__class__, having, self._alias_map))
    #
    # def process_selects_eager_exprs(self, select):
    #     if select and not isinstance(select, (list, tuple, set)):
    #         select = [select]
    #
    #     # 맵은 일단 먼저 만들고 -> 맵으로 칼럼 + query를 만든 뒤 -> eager(outerjoin)
    #     self._set_alias_map_and_loaded_rel_paths(parent_model=self.__class__, parent_path='', attrs=select)
    #
    #     # selects만  set eager expr(outerjoin) 보다 select().select_from(cls)를 먼저  set_query를 한다?
    #     # select_columns = self.create_columns(self.__class__, column_names=select, in_selects=True)
    #     select_columns = self.create_columns_with_alias_map(self.__class__, select, self._alias_map, in_selects=True)
    #
    #     query = (
    #         select(*select_columns)
    #         .select_from(self.__class__)  # execute시 cls를 제외하고 싶다면, 구세주.
    #     )
    #     self.set_query(query)
    #
    #     # attrs = list(map(lambda s: s.lstrip(DESC_PREFIX), select))
    #
    #     self._set_eager_exprs_and_load_rel_paths(only_execute=True)

    def _set_alias_map(self, parent_model, parent_path, attrs):
        """
        input attrs: ['id__gt', 'id__lt', 'tags___property__in']
        output: => OrderedDict([('tags', (<AliasedClass at 0x1de19e32908; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001DE19999150>))])
        """

        relations = defaultdict(list)

        for attr in attrs:
            if RELATION_SPLITTER in attr:
                # print('attr  >> ', attr)
                rel_column_name, rel_attr = attr.split(RELATION_SPLITTER, 1)
                # print('rel_attr  >> ', rel_attr)

                relations[rel_column_name].append(rel_attr)

        for rel_column_name, rel_attr in relations.items():
            self.check_rel_column_name(parent_model, rel_column_name)  # BaseQuery
            path = (parent_path + RELATION_SPLITTER + rel_column_name) if parent_path \
                else rel_column_name

            rel_column = self.get_column(parent_model, rel_column_name)  # BaseQuery
            aliased_rel_model = aliased(rel_column.property.mapper.class_)

            # 2. 외부o시 존재확인후 update VS 빈값에 할당
            # => path가 자료구조에 없으면 넣어주는 것으로 update
            # => 자료구조는 빈값에 할당이 아니라, 빈값에 update만 해주면 된다.
            #### _alias_map에 없는 경우만 path 추가 =>  + loaded_rel_paths에 업는 경우에만 outerjoin해야한다.
            ####   + schema가 있을 경우, loaded도 저장해놓고, 모든 filter, order연쇄가 끝날때 eagerload하게 한다?!
            ####     schema가 없으면, subquery나 selectin할 일이 없다.
            if path not in self._alias_map.keys():
                self._alias_map[path] = aliased_rel_model, rel_column

            self._set_alias_map(aliased_rel_model, path, rel_attr)

    #### 이미 초기화된 상태에서 filter, order 처리하기
    # -> 초반부분 1. set_alias_map + 2. outerjoin+eagerload는 동일하나 -> 3 query부분만 다르다.
    def _set_eager_query_and_load_rel_paths(self):
        # 1. attrs -> alias_map -> rel_path파싱 -> [기존 확인후 없으면] loaded_rel_paths 채우기 + query expression 채우기
        for path, (aliased_rel_model, rel_attr) in self._alias_map.items():
            rel_path = path.replace(self.RELATION_SPLITTER, '.')

            #### 추가, 기존에 loaded_rel_paths에 있는지 확인하여 없는 경우에만 load해준다.
            # -> filter, order를 체이닝해서 할 경우를 대비한 것.
            if rel_path in self._loaded_rel_paths:
                continue

            # 2. flatten schema가 있고 그 속에 subquery, selection으로 기록된 rel path들은 대상이 아니다.
            #### 주석처리 ####
            # if rel_path in self._flatten_schema and self._flatten_schema[rel_path] in [self.SUBQUERY, self.SELECTIN]:
            #     continue
            #### 주석처리 ####
            #### 추가 수정. eager_exprs(outerjoin)을 flatten_schema보다 더 우선적으로 하게 해서
            #    loaded_rel_paths에 올리고, -> 실행메서드에서 나머지 subquery/selectin을 outerjoin(filter/orders)제외하고 한번에 처리에정이다.
            #  -> 그러므로, [schema 우선검사]하고 올리지 말고, filter,/order부터 다 올리고 -> 나중에 처리

            # ===> 관계칼럼이 중복되더라도, flatten_schema보다 filter/order에 나온 것이 우선으로 처리됨.
            # filters = { 'id__lt': 500, 'employee___name__ne': None, 'department___id__ne': None}
            # schema =  schema={'department': 'selectin'}
            # 주석처리 전: self._loaded_rel_paths  >>  ['employee']
            #            unloaded_flatten_schema  >>  {'department': 'selectin'}
            # 주석처리 후: self._loaded_rel_paths  >>  ['employee', 'department']
            #           unloaded_flatten_schema  >>  {}
            # ====> 필터링은 되나, .all() / exeucte(selects=)시 중복문제가 생긴다   중복/casadian product

            # 체이닝을 직접하지 않기 위해, eager outerjoin에 필요한 3가지 인자를 튜플로 건네준다.
            # [0]: outerjoin(첫번재rel_model) 이자 contains_eager의 alias=인자,  ex> AliasedClass Post
            # [1]: outerjoin의 2번재 인자 (main class의 관계칼럼) ex> User.posts
            # [2]: conatains_eager의 1번째 인자 rel_path ex> posts
            #### selects가 한번이라도 들어왔다면, only expression으로서 eageroad없이 outerjoin만
            if self._expression_based:
                # execute만 할거면 select(cls)가 아닌 다른 칼럼들 select상황
                # + select_from(cls)에서 contains_eager(  ,rel_path)의 rel_path 못읽게 된다.
                self.set_query(outerjoin=(aliased_rel_model, rel_attr))
            #### selects가 한번도 안들어왔으면 select(cls)상황으로서 contains_eager까지 포함한 outerjoin
            else:
                self.set_query(eagerload=(aliased_rel_model, rel_attr, rel_path))

            self._loaded_rel_paths.append(rel_path)

    def _set_filter_or_order_exprs(self, filters=None, orders=None):
        # _create_filter_exprs_with_alias_map()
        #### BaseQuery -> smartmixin(Class단위 전체 호출)에서 쓸 수 있도록, 남겨두고, 재활용하자.
        #    BaseQuery가 -> smartmixin, objectmixin에서 양방향으로 쓰이므로, smartmixin은 objectmixin을 슬 수 없다?
        #               -> smartmixin은 BaseQuery를 일단 못쓰게 막고, objectmixin을 가지고 테스트 한다.
        # if filters:
        #     self.set_query(filter_by=self._create_filters_or_having_expr_with_alias_map(self.__class__, filters, self._alias_map))
        # if orders:
        #     self.set_query(order_by=self._create_order_exprs_with_alias_map(self.__class__, orders, self._alias_map))
        ...

    def _set_unloaded_eager_exprs(self):
        # 1. unloaded = flatten_schema가 있을 때만  => flatten - loaded의 나머지 'subquery', 'selectin'을 eagerload한다.
        if not self._flatten_schema:
            return

        # 2. flatten_schema + loaded_rel_paths -> unloaded된 eager목록 schema 을 구한다.
        unloaded_flatten_schema = {
            rel_path: value for rel_path, value in self._flatten_schema.items()
            if rel_path not in self._loaded_rel_paths
        }

        # 이것도 없으면 끝낸다.
        if not unloaded_flatten_schema:
            return

        # 3. obj없이 class로 사용하기 위해 BaseQuery의 classmehtod를 self로 호출해서 expression을 만든 뒤
        #    query에 set한다. -> outerjoin(eager=)과 달리, join없는 eagerload는 options로 들어간다.
        self.set_query(options=self._create_eager_option_exprs_with_flatten_schema(unloaded_flatten_schema))

        # 4. #### 추가, eagerload한 것도 loaded_rel_path에 추가해서, 다음번 unloaded에 안걸리게 한다.
        # -> schema에 subquery/selectin으로 적은 것들이, 뒤에 또 join안되게 조심해야할 듯.
        # -> 1개의filters, orders가 끝나면 -> unloaded를 eagerload해놓고 loaded로 보내기 때문
        # -> filter -> subquery자동 loaded -> filter추가시 subquery했던 것이라면? 일단 outerjoin을 겹처서 해버릴 듯.
        #    loaded는 subquery/selectin을 위한 것이므로.. filter추가는 안보고 일단 outerjoin부터 시킨다.
        # => outerjoin할때도 loaded확인해야할 듯. => 이미 _set_eager_exprs_and_load_rel_paths에서 추가함
        # => filter, order할 거 다하고, 실행직전에 이것을 호출하면 가장 좋을텐데.
        # => BaseQuery의 실행메서드들을 오버라이딩하면 될 듯. (X) crud_mixin에 있으니 복사해서 사용하면 될 듯.

        #### 실행직전에 한다면, 아래로직이 필요없다. 걸거 다 걸고나서, 실행직전에 해준다.
        # print('self._loaded_rel_paths  >> ', self._loaded_rel_paths) # ['employee']
        # self._loaded_rel_paths += list(unloaded_flatten_schema.keys())
        # print('self._loaded_rel_paths  >> ', self._loaded_rel_paths) # ['employee', 'department']

    ####  .first() / .all() 을 여기서 정의, unloaded된 schema상의 'subquery', 'selectin' eagerload해주기
    def close(self):
        # 순수모델에서 호출할 경우 예외처리
        if not hasattr(self, '_session'):
            return

        # 내부session을 -> 조회라도 항상 close()
        # => 내부공용세션이라도, 매번 여러객체를 조회하기 때문에, 매번 close해준다.
        #    변경사항이 필요한 경우, close되더라도, 어차피 merge로 인해 session올라가서 처리된다.
        # * 내부 공용세션이라고 close안해주면 => sqlalchemy.exc.TimeoutError:
        #   QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00

        #  내부session이면, 조회한 객체들은 공용session의 identity_map에서 없애, 조회 후 obj 변화는 반영안된다.
        if not self.served:
            self._session.close()

        # 외부session이면 close할 필요없이 반영만  [외부 쓰던 session은 close 대신] -> [flush()로 db 반영시켜주기]
        # -> 외부session이면, 금방 사라지거나, 맨마지막 놈이 commit되어 자동close()되므로 flush()만 해준다.
        # 외부session이면, 금방 사라지거나, 맨마지막 놈이 commit되어 자동close()되므로 flush()만 해준다.
        #     # -> 이 때 조회된 객체들은 close()가 안되어, 외부session의 identity_map에 남아있다
        else:
            self._session.flush()
        #### => 공용세션 사용으로 바뀌면서, 조회시마다 close()할 필요없다?
        #####   외부세션일때만, self.close()가 호출 되도록 해야할 듯.

    @class_or_instancemethod
    def first(cls, session: Session = None):
        """
        Category.first()
        """
        obj = cls.create_obj(session=session)

        return obj.first()

    @first.instancemethod
    def first(self):
        # 실행메서드 직전에schema상의 subquery, selectin eagerload 처리
        self._set_unloaded_eager_exprs()

        result = self._session.scalars(self._query).first()
        self.close()
        return result

    def one(self):
        self._set_unloaded_eager_exprs()

        result = self._session.scalars(self._query).one()
        self.close()
        return result

    @class_or_instancemethod
    def all(cls, session: Session = None):
        """
        Category.all()
        """
        obj = cls.create_obj(session=session)

        return obj.all()

    @all.instancemethod
    def all(self):
        self._set_unloaded_eager_exprs()
        #### outerjoin + joinedload으로 1객체당 여러데이터가 붙었다면,
        #    select(cls)의 상황에서는 1개의 main entity만 나오고, 관계칼럼(many) 접근시 그에 대해 딸린 것들이 나와야한다.
        #    하지만, outerjoin의 특성상 many가 join되면, one도 그만큼 row가 늘어나는데, 그것을 방지하기 위해
        #    one <- many에서 붙은 many의 row만큼 one-many1 one-many2 one-many3을 방지하기 위해,
        #    => unique()를 select(cls)의 pk별 1개씩만 유지시켜서, 일반 객체 조회가 되게 한다.
        #### scalars가 아닌 상황(execute)에서는 select(cls)를 위해 맨 마지막 .distinct()를 붙이자.
        if not self._expression_based:
            result = self._session.scalars(self._query).unique().all()
        else:
            result = self._session.scalars(self._query).all()

        self.close()
        return result

    def scalar(self):
        self._set_unloaded_eager_exprs()

        if not self._expression_based:
            result = self._session.scalar(self._query.distinct())
        else:
            result = self._session.scalar(self._query)

        self.close()
        return result

    def execute(self, int_enum_transform=False, to_name=False):
        """
        실행시 enum_transform True일 경우, enum의 value를 / to_name=True까지 줄 경우 enum의 name을 뽑게 한다
        => 내부에선 yield -> tuple(generator) -> list( generator )로 정의함.
        ----
        User.group_by('sex', selects=['sex', 'id__count']).execute()
        => [(<SexType.미정: 0>, 3), (<SexType.여자: 2>, 5)]

        User.group_by('sex', selects=['sex', 'id__count']).execute(enum_transform=True)
        =>[(0, 3), (2, 5)]

        User.group_by('sex', selects=['sex', 'id__count']).execute(enum_transform=True, to_name=True)
        => [('미정', 3), ('여자', 5)]
        """
        self._set_unloaded_eager_exprs()

        if not self._expression_based:
            result = self._session.execute(self._query.distinct())
        else:
            result = self._session.execute(self._query)

        #### 입력된 enum_name이나 enum_value으로 변경하게 하기
        # => fetch전 ChunkedIteratorResult 상태여야 전체 칼럼명 확인 가능함.
        # => 어차피 순회하며 새로만든 row를 list에 담아 return하므로
        if int_enum_transform:
            result = list(self.transform_int_enum_in_rows(result, to_name))
            self.close()
            return result

        # 내부 session일 경우, 닫혀서 외부에서 내부row객체 조회가 안된다.
        # execute한 것은 list()로 풀어해쳐줘야 밖에서 쓸 수 있다.? -> fetchall()로 쓸 수 있게 한다.
        if not self.served:
            result = result.fetchall()

        self.close()

        return result

    def transform_int_enum_in_rows(self, rows, to_name):
        column_names = rows.keys()
        # new_result = []
        for row in rows:
            yield tuple(transform_int_enum_in_row(row, column_names, to_name=to_name))
            # new_result.append(new_row)
        # return new_result

    @class_or_instancemethod
    def count(cls, session: Session = None):
        """
        Category.count()
        """
        obj = cls.create_obj(session=session)

        return obj.count()

    # def count(self):
    @count.instancemethod
    def count(self):
        self._set_unloaded_eager_exprs()

        result = self._session.scalar(self.create_count_query())
        self.close()

        return result

    # for count + for paginate 의 중간 count문장만.(실행메서드를 갖다쓰면 session close)
    def create_count_query(self):
        count_stmt = select([func.count()]).select_from(self._query)
        return count_stmt

    def exists(self):
        self._set_unloaded_eager_exprs()

        result = self._session.scalar(exists(self._query).select())
        self.close()
        return result

    # for 객체 update, 등. ->
    #
    #
    # Three years late to the party. Was looking for answer to this but could not find one online so I figured it through trial and error.
    #
    # My answer is based on sqlalchemy 1.3x.
    #
    # The insert -> from_select -> 'select *' combo is done as below:
    #
    # sel = select([table1.c.a, table1.c.b]).where(table1.c.c > 5)
    # ins = table2.insert().from_select(sel.c, sel)
    # The statement sel.c somehow return the array of col

    # for expressionmixin의 count_per_date_unit_subquery
    def subquery(self):
        """
        메서드 내부에서 self_.query.subquery()를 반환함. 이 때, 내부생성 session이라면 삭제해주자.
        """
        #### 추가. subquery로 만들더라도, filter에 적힌 selectin/subquery에 대한 eagerload옵션은 들어가야할 것 같다.
        self._set_unloaded_eager_exprs()

        # print('self._query.subquery()  >> ', self._query.subquery())
        #### 실행메서드같지만, session안받아 session 내부생성되어있으므로, close처리
        self._session.close()

        return self._query.subquery()

    # for route에서 row별 table 데이터(json) 전달
    def to_dict2(self, nested=False, relations=None, hybrid_attrs=False, exclude=None, include=None,
                 session: Session = None, depth=0, enum_name=False, close=True,
                 ):
        """
        *self메서드지만, session=을 인자로 가지는 이유:
        => 같은session으로 *재귀를 돌려, eagerload없이도 children/relation에 접근 -> dict를 생성하고 반환

        1) 이미 mode_obj로 조회되어 session없는 순수model객체 상태(not session obj) -> has not _session
            ex> u = User.get(1) -> (O) no session 객체 1개
            => init_obj하여 session 보급후, add하여 relation접근가능한 상태로 만들어 처리
            => if not hasattr(self, '_session')으로 확인
            => session종료와 함께, 순수model obj_init으로 생긴 [_session, served, _flatten_schema, _query, _loaded_rel_paths, _expression_based] attrs들 삭제해줘야, model obj 다시 메서드 호출시 동일 동작
               by self.close_model_obj() - 실행함수 session을 처리하는 self.close()를 포함하여 attr들 삭제
            ----
            1-1) include할 것만 or 전체에서 exclude할 것만 선택하기
                 그외  hybrid_atts= 도 선택해서 추가 가능하다.
            c = Category.get(2)
            c.to_dict2(exclude=['add_date', 'pub_date'])
            => {'id': 2, 'name': '337', 'icon': '12'}

            1-2) relation을 nested하기
            #    포함시킬 relation을 relations=에 명시하고, nested=True(1)
            #    * self-relational인 경우, nested=6 과 같이 join_depth를 명시한다.

            *nested=True(depth=1)로 관계객체도 불러오기
            c.to_dict2(nested=True, exclude=['add_date', 'pub_date'])
            => {'id': 2, 'name': '337', 'icon': '12',
                'posts': [{'id': 2, 'title': '444444444', 'desc': '444444444444444444444444', 'content': '<p>4444444</p>', 'has_type': 2, 'category_id': 2}]
                }

            *self-relation의 nested라면, 정해진 max_depth를 nested에 주면,
             -> nested에 준 값보다 data의 depth가 얕으면 알아서 children:[]로 반환하며 재귀를 멈춘다.
            d = Department.get(3)
            d.to_dict(nested=Department._DEPTH_LIMIT, relations='children', include=['id', 'name'])
            {
                'id':3,
                'name':'44',
                'children':[
                    {
                        'id':14,
                        'name':'11111',
                        'children':[]
                    },
                    {
                        'id':15,
                        'name':'1111112',
                        'children':[]
                    }
                ]
            }

        2) filter_by 등으로 session obj상태이나, 아직 조회안된 상황 -> _session + not _expression_based
            ex> User.filter_by() -> (X) 몇개 나오는지 모름
            => 가진 session으로 all()하여 model_obj 복수로 가진 뒤, closed된 session을 재활용하여 외부session공급하여 개별model obj를 1)을 반복수행 dict list 반환
            => else(hasattr(self, '_session')) + if self._expression_based == False로 확인
            ----
            *filter_by()로 to_dict2()시 list로 반환됨.
            *relation필드도 exclude에 넣어서 필요한 관계객체만 만들기
            User.filter_by(id__lt=3).to_dict2(nested=True, relations='employee', exclude=['password_hash', 'add_date', 'pub_date', 'inviters', 'invitees', 'role'])
            => [
                {'id': 1, 'username': 'admin', 'email': 'tingstyle1@gmail.com', 'last_seen': '2023-03-02 05:10', 'is_active': True, 'avatar': None, 'sex': 0, 'address': None, 'phone': None, 'role_id': 6,
                    'employee': [{'id': 1, 'user_id': 1, 'name': '관리자', 'sub_name': 'Administrator', 'birth': '9910101918111', 'join_date': '2023-02-15', 'job_status': 1, 'resign_date': None, 'leave_date': None, 'reference': '관리자 계정'}]
                },
                {'id': 2, 'username': 'asdf15251', 'email': 'as5df1231@asdf.com', 'last_seen': '2023-02-19 06:56', 'is_active': True, 'avatar': 'avatar/74858fcc7bfe48c38faf8d304a24345b', 'sex': 2, 'address': '전남 나주시', 'phone': '01046003333', 'role_id': 4,
                    'employee': [{'id': 4, 'user_id': 2, 'name': 'Cho Ara', 'sub_name': 'ara', 'birth': '8712821918511', 'join_date': '2023-02-21', 'job_status': 1, 'resign_date': None, 'leave_date': None, 'reference': '[하위부서2]부서 취임(2023-02-21)'}]
                }
               ]

        3) session obj상태이나 execute예정으로 relation는 없이, selcets칼럼들만 rows가 나오는 상태 -> _session + _expression_based
            ex> Usef.group_by('id') -> selects칼럼 or query삽입으로  rows로 정해짐.
            => relation접근이 없으므로 session필요없어 .execute()-자동sessio처리- > row들을 dict처리
            => else(hasattr(self, '_session')) + if self._expression_based == True로 확인
            ----
            Tag.group_by('id', selects=['name', 'posts___id__count', 'posts___id__sum']).to_dict2()
            => [{'name': '태그1', 'id_count': 1, 'id_sum': 2}, {'name': 'asdf', 'id_count': 0, 'id_sum': 0}]

             Tag.group_by('id', selects=['name', 'posts___id__count', 'posts___id__sum']).to_dict2(exclude='id_sum')
            => [{'name': '태그1', 'id_count': 1}, {'name': 'asdf', 'id_count': 0}]

        4) include 키워드 포함
          d = Department.first()
          d.to_dict2(include=['id', 'name'])
          =>  {'id': 1, 'name': '상위부서'}
        """
        # 배제할 것이 list가 아니더라도 list로 처리
        # -> abc.Iterable로 주면, string 1개를 iterable로 인식함.
        if exclude and not isinstance(exclude, (list, tuple, set)):
            exclude = [exclude]
        # 포함할 것만 주어질 수도 있다.
        if include and not isinstance(include, (list, tuple, set)):
            include = [include]

        #### 1. model obj 1개
        # -> init_obj 후, session에 add하여, relation 조회가능한 상태 -> close_model_obj
        if not hasattr(self, '_session'):
        #     self.init_obj(session=session)
        #     self._session.add(self)
            if not session:
                session = self.get_scoped_session()
            session.add(self)

            result = dict()

            # 1) 배제가 없으면 .__table__.columns에서 일반 칼럼들을 다 꺼낸다. (관계x hybridx)
            # + include도 같이 처리한다.
            view_column_names = self.filter_include_and_exclude(self.column_names, include, exclude)

            # iterrator filter객체로 나온상태라 list로 써버리면 데이터 없음.
            # print('list(view_column_names)  >> ', list(view_column_names))


            # 2) 일반칼럼데이터들을 집어넣는다. - 시간형식은 예외처리한다.
            for column_name in view_column_names:

                _value = getattr(self, column_name)

                if isinstance(_value, datetime.datetime):
                    _value = format_datetime(_value)
                elif isinstance(_value, datetime.date):
                    _value = format_date(_value)
                ## enum처리
                # row(select(칼럼들).from_select(cls) + .execute())에서 enum값은 name을
                # -> 통계처리 등 할때, name으로 분류되어야함.
                # 객체(select(cls) + .first())에서 enum의 value를 뽑고 싶어한다.
                # -> json으로 value가 넘어가야함.
                elif isinstance(_value, enum.Enum):
                    # enum의 name을 추출하고 싶다면 enum_name=True로 주기
                    if enum_name:
                        _value = _value.name
                    else:
                        _value = _value.value

                result[column_name] = _value

            # 3) 하이브리드칼럼을 넣기를 선택한다면, 순회하면서 넣는다.
            if hybrid_attrs:
                # 여기도 배제 확인
                view_hybrid_prop_names = self.filter_include_and_exclude(self.hybrid_property_names, include, exclude)

                for hybrid_prop_name in view_hybrid_prop_names:
                    result[hybrid_prop_name] = getattr(self, hybrid_prop_name)

            # 4) 관계객체의 데이터를 dict형태로 포함하여 넣고 싶다면, 재귀로 얻어낸 dict를 최종dict에 포함시킨다.
            #    *여기서는 include/exclude상관없이 무조건 포함
            if nested:
                if not relations:
                    raise KeyError('nested obj를 원한다면, relations=에 relationship property를 명시해주세요')
                if not isinstance(relations, (list, tuple, set)):
                    relations = [relations]

                if not all(relation in self.relation_names for relation in relations):
                    raise KeyError(f'Invalid relationship : {relations} in depth {nested}')

                # relation의 배제확인은 nested를 타야하므로 아예 검사 제외시킨다?!
                # -> 어차피 relation이 칼럼명으로 나오긴하나, 명시되면 포함시켜야하는데,
                # view_relation_names = self.filter_include_and_exclude(relations, include, exclude)
                # for relation_name in view_relation_names:
                for relation_name in relations:

                    obj = getattr(self, relation_name)
                    # 추가1) relation(or 자식)이 비어있다면, 빈 list를 만들어 반환한다 -> view에서 돌아가게 함.
                    if not obj:
                        result[relation_name] = []
                        continue

                    # 이 때, ObjectMixin을 상속한 model이 아니라, Iterable한 여러모델일 수 있다면,
                    # -> 해당하는 것만 모아서 변환 후 list로 넣어준다. hybrid_atts=False,
                    # 재귀에서도 배제를 처리하기 때문에, main - relation의 배제할 칼럼명이 안겹쳐지게 조심한다.
                    #### relation은 1단계만 처리하기 위해, 관계객체 to_dict에선 nested옵션 + 을 안준다.
                    if isinstance(obj, ObjectMixin):
                        # 재귀를 돌릴 때, 같은 session을 활용하기 위해 self._session을 넣어준다.
                        # => 만약 안넣어준다면, relation obj가 다른 session(부모처럼 자체 내부새셩 생성)에 존재한다고 뜬다.
                        result[relation_name] = obj.to_dict2(nested=nested - 1, relations=relations,
                                                             hybrid_attrs=hybrid_attrs, include=include, exclude=exclude,
                                                             session=session, depth=depth + 1,enum_name=enum_name,
                                                             close=close
                                                             )
                    # 여기는 relation obj에 접근 Many라서  경우다. 순회하면서, 각각 돌려줘야한다.
                    elif isinstance(obj, Iterable):
                        result[relation_name] = [
                            o.to_dict2(nested=nested - 1, relations=relations, hybrid_attrs=hybrid_attrs, include=include,
                                       exclude=exclude, session=session, depth=depth + 1, enum_name=enum_name, close=close) for o in obj
                            if isinstance(o, ObjectMixin)
                        ]

            # session없는 model_obj라도 예외처리.됨
            # nested 하려면, relations이 load되어있어야한다.
            # self.close_model_obj() # session 등을 지우면, 재귀로 외부session이 날아가버리는 부작용으로 취소
            #### session close만 -> 최상층에서만..? 어차피 dict에 채우고 종료해도 상관없다?

            if not depth and close:
                self.close()
            return result


        else:
            #### 2.filter_by 등으로 session obj상태이나, 아직 조회안된 상황 -> _session + not _expression_based
            #    => 가진 session으로 all()하여 model_obj 복수로 가진 뒤, closed된 session을 재활용하여 외부session공급하여
            #    -> 순회하며 개별model obj를 1)을 반복수행 dict list 반환
            if not self._expression_based:
                #### 추가) execute용 _expression_based가 아니라면, filter_by후에 eagerload까지?!
                # self._set_unloaded_eager_exprs()
                # => relation을 입력시, 1depth에 한해서 to_dict2()를 처리하므로 eagerload와는 관련없다?
                # => session안에서 relation에 접근해서 괜찮다.

                # 1) 실행메서드.all()을 하면 sesion이 닫히고, 객체들이 빠져나간 close()가 호출되는데, 각 객체들은 순수model obj(1번상황)
                # => 모두 add한 다음, to_dict를 개별객체마다 진행한다.?!
                results = self.all()
                self._session.add_all(results)

                dict_list = []
                for model_obj in results:
                    model_dict = model_obj.to_dict2(nested=nested, relations=relations, hybrid_attrs=hybrid_attrs,
                                                    include=include,
                                                    exclude=exclude,
                                                    session=self._session, depth=depth, enum_name=enum_name, close=False)
                    dict_list.append(model_dict)

                self.close()

                return dict_list

            #### 3. session obj상태이나 execute예정으로 relation는 없이, selcets칼럼들만 rows가 나오는 상태
            #   => relation접근이 없으므로 session필요없어 .execute()-자동sessio처리- > row들을 dict처리
            # if not self._expression_based:
            else:
                rows = self.execute()
                self.close()

                # 1개 row의 개별 값들은 인덱싱으로 접근 가능하여, row index + 칼럼명을 동시에 받아 처리?!
                result = []
                for row in rows:
                    row_dict = dict()
                    for column_name in row.keys():
                        # 꺼내기 전에 배제부터 확인
                        if exclude and column_name in exclude:
                            continue
                        _value = getattr(row, column_name)
                        ## enum처리
                        # row(select(칼럼들).from_select(cls) + .execute())에서 enum값은 name을
                        # -> 통계처리 등 할때, name으로 분류되어야함.
                        # 객체(select(cls) + .first())에서 enum의 value를 뽑고 싶어한다.
                        # -> json으로 value가 넘어가야함.
                        if isinstance(_value, enum.Enum):
                            _value = _value.name
                        row_dict[column_name] = _value

                    result.append(row_dict)
                return result

    # for to_dict
    def filter_include_and_exclude(self, attr_names, include, exclude):
        if include:
            attr_names = filter(lambda e: e in include, attr_names)

        if exclude is None:
            return attr_names

        view_attrs = filter(lambda e: e not in exclude, attr_names)
        return view_attrs

    # for to_dict + for update/delete 모든 Model_obj에서 init하여 실행되는 함수들
    # => 재호출해도 다 다시 초기화되며,  session 등을 지우면, 외부session이 날아가버리는 부작용으로 취
    # def close_model_obj(self):
    #     self.close()
    #
    #     for attr in self.ADDITIONAL_ATTRS:
    #         if hasattr(self, attr):
    #             delattr(self, attr)

    #### select(cls) == not expression_based 실행메서드를 추가한다면
    # => session안에서 relation에 접근할 경우(to_dict)가 아니라면,
    #    self._set_unloaded_eager_exprs()를 추가한 뒤 실행시키자.

    #####
    # load된 self-relational obj용
    #####
    # refactor
    # def flatten_children(self, attr_name='children'):
    #     """
    #     dept = Department.load({'children':('joined', 2)}).filter_by(id=1).first()
    #     [Department(id=1, name='상위부서', parent_id=None, sort=1, path='001'), Department(id=2, name='하위부서1', parent_id=1, sort=1, path='001001'), Department(id=5, name='ㅋㅋㅋ', parent_id=2, sort=1, path='001001001'), Department(id=3, name='하위부
    #     서2', parent_id=1, sort=2, path='001002')]
    #     """
    #     # 자신의 처리이자, 최종 data
    #     result = [self]
    #     try:
    #         for child in getattr(self, attr_name):
    #             result += child.flatten_children()
    #     except DetachedInstanceError:
    #         return result
    #
    #     return result

    # refactor 2
    def flatten_children(self, attr_name='children', session:Session=None, close=True, depth=0):
        """
        """
        if not session:
            session = self.get_scoped_session()
        session.add(self)

        # 자신의 처리이자, 최종 data
        result = [self]

        for child in getattr(self, attr_name):
            result += child.flatten_children(session=session, close=False, depth=depth+1)

        if close and not depth:
            session.close()

        return result
