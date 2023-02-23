from collections import OrderedDict, defaultdict

from sqlalchemy.orm import InstrumentedAttribute, aliased

from src.infra.config.connection import db

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


class SessionMixin:
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

    @classmethod
    def create_obj(cls, session, query=None, schema=None, flatten_schema=None,
                   filters=None, orders=None, **kwargs):
        obj = cls(**kwargs).init_obj(session, query=query, schema=schema, flatten_schema=flatten_schema,
                                     filters=filters, orders=orders)
        return obj

    def init_obj(self, session, query=None, schema=None, flatten_schema=None,
                 filters=None, orders=None):
        self.set_sess(session).set_query(query).set_schema(schema, flatten_schema) \
            .set_alias_map_attrs(filters, orders)

        return self

    def set_sess(self, session):
        #### session & served
        if not hasattr(self, '_session'):
            self._session = None

        # 1) 외부session주어지면, 기존session가진 것 여부 상관없이 그것으로 교체
        if session:
            self._session = session
            self.served = True
        # 2) 외부session이 없는 경우 -> 기존 session 확인후 존재하지 않을 때만 session 새로 생성
        else:
            if self._session is None:
                self._session = db.get_session()
                self.served = False

        return self

    def set_query(self, query):
        if not hasattr(self, '_query'):
            self._query = None

        # 외부 query는 우선공급이 아니라, 기존 query가 있을 경우 query를 이어줘야한다.
        # 외부 쿼리가 있는 경우에만 연결하거나 할당해준다.
        if query is not None:
            if self._query is not None:
                self._query = self._query.query
            else:
                self._query = query

        return self

    def set_schema(self, schema=None, flatten_schema=None):
        if not hasattr(self, '_flatten_schema'):
            self._flatten_schema = {}

        # 이미 obj생성되었어도 schema마 정보가 {}로 초기화되어 비어있을때만, 외부껏을 할당해준다.
        if not self._flatten_schema:
            if flatten_schema:
                self._flatten_schema = flatten_schema
            else:
                if schema:
                    self._flatten_schema = _flat_schema(schema)

        return self

    # filters, orders -> filter_and_order_attrs를 통해  alias_map이 채워진다.
    def set_alias_map_attrs(self, filters=None, orders=None):
        if not hasattr(self, '_alias_map'):
            self._alias_map = OrderedDict({})

        # 초기상태인 경우 -> 상관없이 내부에서 keys()로 확인후 없는 것만 추가.
        # if not self._alias_map:
        attrs = []
        if filters:
            attrs += list(_flat_filter_keys_generator(filters))
        if orders:
            attrs += list(map(lambda s: s.lstrip(DESC_PREFIX), orders))

        self._parse_path_and_set_alias_map(parent_model=self.__class__, parent_path='', attrs=attrs)

    def _parse_path_and_set_alias_map(self, parent_model, parent_path, attrs):
        """
        input attrs: ['id__gt', 'id__lt', 'tags___property__in']
        output: => OrderedDict([('tags', (<AliasedClass at 0x1de19e32908; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001DE19999150>))])
        """
        # 1. relations에는 일단 ___으로 split하여 rel_column_name(key)에 해당 attr들을 list로 모은다.
        relations = defaultdict(list)

        for attr in attrs:
            if RELATION_SPLITTER in attr:
                rel_column_name, rel_attr = attr.split(RELATION_SPLITTER, 1)
                relations[rel_column_name].append(rel_attr)

        for rel_column_name, rel_attr in relations.items():
            self.check_rel_column_name(parent_model, rel_column_name)
            path = (parent_path + RELATION_SPLITTER + rel_column_name) if parent_path \
                else rel_column_name

            rel_column = self.get_column(parent_model, rel_column_name)  # 해당 클래스에선 BaseQuery상속해서 가능
            aliased_rel_model = aliased(rel_column.property.mapper.class_)

            #### 없는 경우만 추가
            if path not in self._alias_map.keys():
                self._alias_map[path] = aliased_rel_model, rel_column

            self._parse_path_and_set_alias_map(aliased_rel_model, path, rel_attr)

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
