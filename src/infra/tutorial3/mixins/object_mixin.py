from collections import OrderedDict, defaultdict, abc

from sqlalchemy import MetaData, select, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import InstrumentedAttribute, aliased, contains_eager, Session

from src.infra.config.connection import db
from src.infra.tutorial3.mixins.base_query import BaseQuery

Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)

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
    """
    if not schema:
        return {}

    def _flat_recursive(schema, parent_column_name, result):
        for rel_column_name_or_prop, value in schema.items():
            if isinstance(rel_column_name_or_prop, InstrumentedAttribute):
                rel_column_name_or_prop = rel_column_name_or_prop.key

            if isinstance(value, tuple):
                eager_type, inner_schema = value[0], value[1]

            elif isinstance(value, dict):
                eager_type, inner_schema = JOINED, value

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


def _flat_filter_keys_generator(filters):
    for key, value in filters.items():
        if key.lower().startswith(('and_', 'or_')):
            # yield의 depth없는 재귀 호출은 yiedl from 메서드(자식)으로 한다.
            yield from _flat_filter_keys_generator(value)
        # 나 자신의 처리(방출)
        else:
            yield key


class ObjectMixin(BaseQuery):
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

    @classmethod
    def create_obj(cls, session: Session = None, query=None, schema=None,
                   filters=None, orders=None,
                   **kwargs):

        obj = cls(**kwargs).init_obj(session=session, query=query, schema=schema, filters=filters, orders=orders)
        return obj

    def init_obj(self, session: Session = None, query=None, schema=None, filters=None, orders=None):

        self.served = None  # set_session_and_check_served에서 T/F 초기화
        self._session = self.set_session_and_check_served(session)  # 내부에서 어떻게든 초기화
        self._query = self.set_query(query) or select(self.__class__) # None으로 초기화하지말고, select(main mdoel)로 초기화
        self._flatten_schema = self._set_schema(schema) or {}

        self._loaded_rel_paths = []  # filter or orders가 존재시, process_filter_or_orders에서 채워짐.
        self._alias_map = OrderedDict({}) if not (filters or orders) \
            else self.process_filter_or_orders(filters=filters, orders=orders)

        return self

    # 외부인자 없어도 내부 생성해서 반환한다.
    def set_session_and_check_served(self, session):

        # 1) 외부session주어지면, 기존session가진 것 여부 상관없이 그것으로 교체 or 초기화
        if session:
            self._session = session
            self.served = True
            return self._session
        # 2) 외부session이 없는 경우 -> 기존 session 확인후 존재하지 않을 때만 session 새로 생성
        else:
            # 3) 기존 session확인하기 전에, 있는지 초기화여부부터 확인해야한다.?!
            if not hasattr(self, '_session'):
                self._session = None

            # 4) 초기화가 보장되었다면, 기존 것을 확인한 뒤 없으면 내부생성 초기화.(not return False 초기화)
            if self._session is None:
                self._session = db.get_session()
                self.served = False

                return self._session
            # 3) 외부x, 내부o라면 새로운 session을 set 실패
            else:
                return False

    def set_query(self, query=None, join=None, filter_by=None, order_by=None, options=None):
        def _is_chaining():
            return not (join is None and filter_by is None and order_by is None and options is None)

        # 1. 외부X -> return False로 초기화 (set실패) -> 초기화시 select(self.__class__)로 초기화
        if not _is_chaining() and query is None:
            return False  # -> 초기화 select(self.__class__)

        # 2. 외부O -> 내부확인후 존재하면 update  VS  초기화빈값이면 assign
        # => 내부는 항상 select(main)으로 존재하게 만들어놨음.
        # if self._query is not None:
        # => 체이닝 여부를 확인하고 아니라면 해당 쿼리를 그냥 삽입하자.
        if _is_chaining():
            if not hasattr(self, '_query'):
                self._query = select(self.__class__)

            # 이미 select( main )으로 작성된 상황이라면 체이닝을 해야하는데,
            # -> 하려면 인자로 expression만 받아서, 틀에 끼워넣어줘야한다.
            if join:
                self._query = (
                    self._query
                    .outerjoin(join[0], join[1])
                    .options(contains_eager(join[2], alias=join[0]))
                )

            if filter_by:
                self._query = (
                    self._query
                    .where(*filter_by)
                )

            if order_by:
                self._query = (
                    self._query
                    .order_by(*order_by)
                )

            if options:
                self._query = (
                    self._query
                    .options(*options)
                )

        # 체이닝이 아닌 query가 들어올 경우, 최초 init시 들어온 query=로서 할당 초기화
        else:
            self._query = query

        return self._query

    def _set_schema(self, schema=None):
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

    # filters, orders -> filter_or_order_attrs 통해  alias_map이 채워진다.
    def process_filter_or_orders(self, filters: dict = None, orders=None):
        # 의존성 필드 포함시 내부에서 같이 초기화 -> 내부/외부여부에 따라 외부x시-> 내부 존재여부 확인후 초기화 -> 외부o시 할당 초기화
        # 1. 외부x시 내부 확인후 없으면 return False 초기화
        if not (filters or orders):
            return False  # -> alias_map 초기화

        # 2. 외부o시 존재확인후
        #    -> 인자들 변환 후
        #    udpate VS 빈값에 할당 => set_alias_map 내부에서
        filter_or_order_attrs = []
        if filters:
            filter_or_order_attrs += list(_flat_filter_keys_generator(filters))
        if orders:
            if orders and not isinstance(orders, (list, tuple, set)):
                orders = [orders]
            filter_or_order_attrs += list(map(lambda s: s.lstrip(DESC_PREFIX), orders))

        # 2-1. alias_map 채우기 => 내부에서  update VS 빈값에 할당? (자료구조의 경우 update위주로)
        self._set_alias_map_and_loaded_rel_paths_and_eager_exprs(parent_model=self.__class__, parent_path='',
                                                                 attrs=filter_or_order_attrs)
        # 2-2. set된 alias_map -> eager expression 체이닝 후 loaded_rel_paths 채워 업데이트
        # self._set_eager_exprs_and_load_rel_paths_from_alias_map()
        # => set_alias_map 시 자동으로 처리되어야하므로 내부의 마지막으로 이동
        # 2-3.
        self._set_filter_or_order_exprs(filters=filters, orders=orders)

        # 2-4. flatten_schema + loaded_rel_paths -> unloaded schema처리하기
        # self._set_unloaded_eager_exprs()
        # => unloaded는 .first() 등의 실행메서드로 옮겨감. filter, order 다 처리하고나서 로드

    def _set_alias_map_and_loaded_rel_paths_and_eager_exprs(self, parent_model, parent_path, attrs):
        """
        input attrs: ['id__gt', 'id__lt', 'tags___property__in']
        output: => OrderedDict([('tags', (<AliasedClass at 0x1de19e32908; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001DE19999150>))])
        """

        relations = defaultdict(list)

        for attr in attrs:
            if RELATION_SPLITTER in attr:
                rel_column_name, rel_attr = attr.split(RELATION_SPLITTER, 1)
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

            self._set_alias_map_and_loaded_rel_paths_and_eager_exprs(aliased_rel_model, path, rel_attr)

        # 2-2. set된 alias_map -> eager expression 체이닝 후 loaded_rel_paths 채워 업데이트
        self._set_eager_exprs_and_load_rel_paths()

    #### 이미 초기화된 상태에서 filter, order 처리하기
    # -> 초반부분 1. set_alias_map + 2. outerjoin+eagerload는 동일하나 -> 3 query부분만 다르다.
    def _set_eager_exprs_and_load_rel_paths(self):
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

            self.set_query(join=(aliased_rel_model, rel_attr, rel_path))

            self._loaded_rel_paths.append(rel_path)

    def _set_filter_or_order_exprs(self, filters=None, orders=None):
        # _create_filter_exprs_with_alias_map()
        #### BaseQuery -> smartmixin(Class단위 전체 호출)에서 쓸 수 있도록, 남겨두고, 재활용하자.
        #    BaseQuery가 -> smartmixin, objectmixin에서 양방향으로 쓰이므로, smartmixin은 objectmixin을 슬 수 없다?
        #               -> smartmixin은 BaseQuery를 일단 못쓰게 막고, objectmixin을 가지고 테스트 한다.
        if filters:
            self.set_query(filter_by=self._create_filters_expr_with_alias_map(self.__class__, filters, self._alias_map))
        if orders:
            self.set_query(order_by=self._create_order_exprs_with_alias_map(self.__class__, orders, self._alias_map))

    def _set_unloaded_eager_exprs(self):
        # 1. unloaded = flatten_schema가 있을 때만  => flatten - loaded의 나머지 'subquery', 'selectin'을 eagerload한다.
        if not self._flatten_schema:
            return

        # 2. flatten_schema + loaded_rel_paths -> unloaded된 eager목록 schema 을 구한다.
        unloaded_flatten_schema = {
            rel_path: value for rel_path, value in self._flatten_schema.items()
            if rel_path not in self._loaded_rel_paths
        }
        print('self._loaded_rel_paths  >> ', self._loaded_rel_paths)

        print('unloaded_flatten_schema  >> ', unloaded_flatten_schema)

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
        # 내부session을 -> close()
        if not self.served:
            self._session.close()
        # 외부session이면 close할 필요없이 반영만  [외부 쓰던 session은 close 대신] -> [flush()로 db 반영시켜주기]
        else:
            self._session.flush()

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

    def all(self):
        self._set_unloaded_eager_exprs()

        result = self._session.scalars(self._query).all()

        self.close()
        return result

    def scalar(self):
        self._set_unloaded_eager_exprs()

        result = self._session.scalar(self._query)

        self.close()
        return result

    def execute(self, selects=None):
        self._set_unloaded_eager_exprs()

        if selects:
            # self._query = self._query # outerjoin한 것 골라내지나, select_from()을 한 순간  최초select(self.__class__)만 select에 들어간다.
            # alias도  없이 칼럼명 그대로 AS 원래칼럼명으로 잡히게 된다.
            ##### => main model에서만 골라낼 수 있도록 하자.
            if not isinstance(selects, (list, tuple, set)):
                selects = [selects]

            self._query = (
                select([text(col_name) for col_name in selects])
                .select_from(self._query)
            )

        result = self._session.execute(self._query)
        # 내부 session일 경우, 닫혀서 외부에서 내부row객체 조회가 안된다.
        # execute한 것은 list()로 풀어해쳐줘야 밖에서 쓸 수 있다.? -> fetchall()로 쓸 수 있게 한다.
        if not self.served:
            result = result.fetchall()

        self.close()

        return result

    def count(self):
        self._set_unloaded_eager_exprs()

        count_stmt = select([func.count()]).select_from(self._query)
        result = self._session.scalar(count_stmt)
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
