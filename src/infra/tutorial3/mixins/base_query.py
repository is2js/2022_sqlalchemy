import enum
from collections import defaultdict, namedtuple
from datetime import datetime

from dateutil.relativedelta import relativedelta
from pyecharts.charts import Bar
from sqlalchemy import and_, or_, select, func, distinct, inspect, Table, cast, Integer, literal_column, text, column, \
    Numeric, desc, asc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import InstrumentedAttribute, joinedload, subqueryload, selectinload
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.util import classproperty

from src.config import db_config
from src.infra.config.connection import DBConnectionHandler


#### import Error유발해서 직접 정의해서 사용
# from src.main.utils.to_string import to_string_date

def to_string_date(last_month):
    return datetime.strftime(last_month, '%Y-%m-%d')


"""
BaseQuery 참고1(flask): https://vscode.dev/github/adpmhel24/BakeryProject/blob/master/bakery_project/bakery_app/_helpers.py
BaseQuery 참고2(fastapi): https://vscode.dev/github/adpmhel24/BakeryProject/blob/master/bakery_project/bakery_app/_helpers.py

BaseMixin 참고: https://github.com/riseryan89/notification-api/blob/master/app/database/schema.py

Mixin 완성본 참고:  https://github.com/absent1706/sqlalchemy-mixins/tree/ce4badbc51f8049783fa3909615ccfc7c1198d98/sqlalchemy_mixins
- smartquery: https://github.com/absent1706/sqlalchemy-mixins/blob/ce4badbc51f8049783fa3909615ccfc7c1198d98/sqlalchemy_mixins/smartquery.py
- inpsect mixins: https://github.com/absent1706/sqlalchemy-mixins/blob/ce4badbc51f8049783fa3909615ccfc7c1198d98/sqlalchemy_mixins/inspection.py
"""

DESC_PREFIX = '-'
OPERATOR_OR_FUNC_SPLITTER = '__'

# https://github.com/absent1706/sqlalchemy-mixins/blob/ce4badbc51f8049783fa3909615ccfc7c1198d98/sqlalchemy_mixins/smartquery.py#L396
op_dict = {
    "==": "eq",
    "eq": "eq",
    "!=": "ne",
    "ne": "ne",
    ">": "gt",
    "gt": "gt",
    "<": "lt",
    "lt": "lt",
    ">=": "ge",
    "ge": "ge",
    "<=": "le",
    "le": "le",
    "like": "like",
    "ilike": "ilike",
    "in": "in",
    "notilike": "notilike",
    "is": "is_",
    "isnot": "isnot",
    "between": "between"
}

# for create_eager_options
# 상수로 만든 뒤, 사용시 import해서 쓰도록
## eager types
JOINED = 'joined'
INNER_JOINED = 'inner_joined'
SUBQUERY = 'subquery'
SELECTIN = 'selectin'

## eager load map
eager_load_map = {
    'joined': lambda c_name: joinedload(c_name, innerjoin=True),
    'inner_joined': lambda c_name: joinedload(c_name),
    'subquery': lambda c_name: subqueryload(c_name),
    'selectin': lambda c_name: selectinload(c_name)
}

# for create_eager_options
def _flat_schema(schema: dict):
    """
    schema = {
        'user': JOINED, # joinedload user
        'comments': (SUBQUERY, {  # load comments in separate query
            'user': JOINED  # but, in this separate query, join user
        })
    }
    => {'user': JOINED, 'comments': SUBQUERY, 'comments.users': JOINED}


    # the same schema using class properties:
    schema = {
        Post.user: JOINED,
        Post.comments: (SUBQUERY, {
            Comment.user: JOINED
        })
    }

    """

    # 3) 꼬리재귀를 위해, 인자에 level마다 바뀌는 schema->innser_schmea  + 자식이 자신이될(parent_xx) 칼럼명 이은 것, 누적변수 result를 추가한 뒤
    #  => 내부메서드로 만든 다음, 기초값을 자신과 누적변수에 초기값을 넣어서 호출한다.
    def _flat_recursive(schema, parent_column_name, result):
        for rel_column_name_or_prop, value in schema.items():
            # 1) Post.user 등 관계속성을 사용하는 경우 => 관계 칼럼명을 가져온다.
            if isinstance(rel_column_name_or_prop, InstrumentedAttribute):
                rel_column_name_or_prop = rel_column_name_or_prop.key

            # 2-1) value가 tuple로 입력된 경우는, { Post.user : ( SUBQUERY, { 'user': JOINED } ) } 의 재귀형태다.
            # => 내부 eager type + 내부 schema로 분리한다.
            if isinstance(value, tuple):
                eager_type, inner_schema = value[0], value[1]

            # 2-2) value가 tuple[0]의 eager type이 생략된  dict로 입력된 경우는, { User.posts: {  Post.comments : { Comment.user: JOINED }}}
            # => eager type이 JOINED로 고정이며 + value가 내부shcema를 의미한다.
            elif isinstance(value, dict):
                eager_type, inner_schema = JOINED, value

            # 2-3) 그외의 경우는 내부schema는 없는 것이며, value가 eager_type인 경우다.
            else:
                eager_type, inner_schema = value, None

            # 5) 시작부터 부모의 것이 있다고 생각하고 부모의 정보를 받아 사용하여 나를 처리한다.
            # => 부모의 관계속성명.나의관계속성명 을 연결한다. 부모가 있으면 부모를 앞에 두고 연결한다.
            current_column_name = parent_column_name + '.' + rel_column_name_or_prop if parent_column_name \
                else rel_column_name_or_prop
            # 6) result라는 dict 누적변수에 earger type을 [현재 이은 경로]를 key로 value로 넣어준다.
            result[current_column_name] = eager_type

            # 7) 만약 연결될 내부 schema( value에 dict or tuple[1]의 dict가 존재할 경우 다시 재귀를 호출한다.
            # => 꼬리재귀 + 누적변수를 가지고 다녀서, 호출만 해주면 알아서 누적된다.
            if inner_schema:
                _flat_recursive(inner_schema, current_column_name, result)


    # 4) 초기값 투입
    result = {}
    _flat_recursive(schema, '', result)

    return result


# for create_eager_options
# depth가 .으로 연결된 칼럼명 조합으로 들어온다.
def _to_eager_options(flatten_schema):
    """
    input: {'user': JOINED, 'comments': SUBQUERY, 'comments.users': JOINED'}
    => 이미 lazy='dynamic'으로 준 칼럼은 subqueryload를 할 수 없다.
    => 할때마다 가져오는 lazy='dynamic' => sqlalchemy.orm.dynamic.AppenderQuery
    => 옵션없다가 한번에 eagerload명시 가져오는 =>  sqlalchemy.orm.strategy_options.Load

    => [<sqlalchemy.orm.strategy_options._UnboundLoad object at 0x0000025E9DBF7D68>,   # Load(strategy=None)
    <sqlalchemy.orm.strategy_options._UnboundLoad object at 0x0000025E9DBF7E10>,   # Load(strategy=None)
    <sqlalchemy.orm.strategy_options._UnboundLoad object at 0x0000025E9DBF7EF0>]   # Load(strategy=None)

    """
    # 1) 입력한 flattend_schema(dict)를 순회(순서 상관없음. depth는 .이 해결)하면서 종류에 따라 load모듈을 list에 append한다.
    result = []
    for column_name, eager_type in flatten_schema.items():
        if eager_type not in eager_load_map.keys():
            raise NotImplementedError(f'Invalid eager load type: {eager_type} by column name: {column_name}')

        result.append(eager_load_map[eager_type](column_name))

    return result


class BaseQuery:
    DIALECT_NAME = db_config.get_dialect_name()

    @classmethod
    def get_column(cls, model, column_name):
        # ORM model이 아니라 Table() 객체일 경우 -> .c에서 getattr
        if isinstance(model, Table):
            column = getattr(model.c, column_name, None)
        else:
            column = getattr(model, column_name, None)
        # Table()객체는 boolean 자리에 입력시 에러
        # if not column:
        if column is None:
            raise Exception(f'Invalid column_name: {column_name} in {model}')

        return column

    @classmethod
    def split_and_check_name(cls, column_name):
        column_name = column_name.split(f'{OPERATOR_OR_FUNC_SPLITTER}')
        if len(column_name) > 2:
            raise Exception(f'Invalid func column name: {column_name}')

        return column_name

    @classmethod
    def create_column(cls, model, column_name):
        """
        BaseQuery.create_column(User, 'id')
        <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x0000024B4967A5C8>

        BaseQuery.create_column(User, 'id__count')
        <sqlalchemy.sql.elements.Label object at 0x0000024B4989E748>

        BaseQuery.create_column(User, 'id__count_distinct')
        DISTINCT coalesce(count(users.id), :coalesce_1)


        """

        # 칼럼이 집계함수와 같이 들어온다면 집계함수를 적용할 수 있게 한다.
        if '__' in column_name:
            column_name, func_name = cls.split_and_check_name(column_name)  # split결과 3개이상나오면 에러 1개, 2개는 넘어감

            column = cls.get_column(model, column_name)

            #### func 적용 apply_func = 인자 추가
            if func_name.startswith('count'):
                column = func.coalesce(func.count(column), 0).label(func_name)
            elif func_name.startswith('sum'):
                column = func.coalesce(func.sum(cast(column, Integer)), 0).label(func_name)
            elif func_name.startswith('length'):
                column = func.coalesce(func.length(column), 0).label(func_name)
            else:
                raise NotImplementedError(f'Invalid column func_name: {func_name}')

            # 집계함수에 distinct()씌우는 기능 추가
            # id__count_distinct
            if '_' in func_name:
                additional_func_name = func_name.split('_')[-1]
                if additional_func_name == 'distinct':
                    column = distinct(column)
                else:
                    raise NotImplementedError(f'Invalid additional func_name: {additional_func_name}')

            return column

        else:
            return cls.get_column(model, column_name)

    @classmethod
    def create_columns(cls, model, column_names=None):
        """
        return a list of columns from the model
        - https://vscode.dev/github/adpmhel24/jpsc_ordering_system

        BaseQuery.create_columns(User, ['id', 'id__sum'])
        [<sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x0000024B4967A5C8>, <sqlalchemy.sql.elements.Label object at 0x0000024B4989EA20>]
        BaseQuery.create_columns(User, ['id', 'username__count'])
        [<sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x0000024B4967A5C8>, <sqlalchemy.sql.elements.Label object at 0x0000024B4989EB38>]
        BaseQuery.create_columns(User, ['id', 'username__length'])
        [<sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x0000024B4967A5C8>, <sqlalchemy.sql.elements.Label object at 0x0000024B4989E710>]

        """
        if not column_names:
            return [model]

        if not isinstance(column_names, (list, tuple, set)):
            column_names = [column_names]

        columns = []
        for column_name in column_names:
            # 칼럼들이 들어올 때, str 'id'가 아니라, [('id', 'count')] 집계를 요구할 수 있다.
            # if not isinstance(column_name, str):
            #     if not isinstance(column_name, (list, tuple, set)):
            #         raise Exception(f'Invalid column name: {column_name}')
            #     column_name, apply_func = column_name
            # => 집계를 ['id__count', 'name']형식으로 바꾸자.

            columns.append(cls.create_column(model, column_name))

        return columns

    @classmethod
    def get_relation_model(cls, model, relation_name):
        """
        # Tag.__mapper__.relationships.items()[0]
        # ('posts', <RelationshipProperty at 0x28546b9e3c8; posts>)
        # relationship.target
        # Table('posts', MetaData()...
        """
        rel_column = next((r[1] for r in model.__mapper__.relationships.items() if r[0] == relation_name),
                          None)
        if rel_column is None:
            raise Exception(f'Invalid relation_name: {relation_name} in {model}')

        return rel_column.target

    @classmethod
    def create_filters2(cls, model, filters):
        """
        재귀를 이용하여, and_or_or(key)의 내부들을 연결한다.
        return sqlalchemy's filter
        :param model:
        :param filters: filter dict -> 기본적으로 {'and': [(col_name, op, value)]} , {'or': { 'and': 조건1, 'and': 조건2} } 형식으로 사용한다.
            filters = {
                'or_1':{
                    'and': [('id', '>', 5), ('id', '!=', 3)],
                    'and': [('name', '==', 'cho')]
                },
                'and': [ ('age', '>', 20)]
            }
        :return: sqlalchemy's filter
        """
        # 1. where(* cls.method) 형태로 unpack될 것이므로, 아무것도 없다면, 빈 list가 풀어지게 하자.
        # -> 또한 재귀의 종착역?!
        if not filters:
            return []

        # 2.
        filt = []
        for filter_op in filters:
            # 1) dict의 value가 dict면, key가 'and' -> value dict 요소들을 [ value를 자신인자(filters)로 재귀메서드호출->list반환->*unpacking]한 뒤, and_()로 연결 / key가 'or' -> or_()로 연결이다.
            ## 재귀(바로 결과물 filt list가 반환된다)
            if type(filters[filter_op]) == dict:
                if 'and' in filter_op:
                    filt.append(
                        and_(*cls.create_filters2(model, filters[filter_op]))
                    )
                elif 'or' in filter_op:
                    filt.append(
                        or_(*cls.create_filters2(model, filters[filter_op]))
                    )
                else:
                    raise Exception(f'invalid filter operator: {filter_op}')

                continue
            ## continue로 인한 비재귀(value가 tuple list)인 경우 -> key(and or)에 따라 filter묶음을 만들어서 순서대로 append해주면 된다.
            # -> 한번에 조건들을 filt_aux에 순서대로 append해놓고, key에 따라 전체를 and_() 하거나 or_()로 묶을 것이다.
            filt_aux = []
            for raw in filters[filter_op]:
                # 1) try로 unpack가능한 (,,)인지 확인
                try:
                    col_name, op_name, value = raw
                except:
                    raise Exception(f'Invalid filter: {raw}')

                # 2) model.column 꺼내기
                # column = getattr(model, col_name)
                # if not column:
                column = cls.create_column(model, col_name)
                if column is None:
                    raise Exception(f'Invalid column: {col_name}')

                # 3) op string -> op attribute로 변환
                if op_name not in op_dict:
                    raise Exception(f'Invalid filter operator: {op_name}')

                # 3-1) in연산자만 attr확인없이 1개의 sqlachemy연산이 되므로 바로 filt_aux에 추가하면 된다.
                if op_dict[op_name] == 'in':
                    filt_aux.append(column.in_(value))
                    continue
                # 추가 between도 바로 처리
                elif op_dict[op_name] == 'between':
                    filt_aux.append(column.between(value[0], value[1]))
                    continue

                # 3-2) in이 아닌 다른 연산자들은 연산메서드(attribute)로 바꿔서 적용한 filter를 append
                #      -> hasattr()로 확인한 결과 연산메서드가 하나도 안나오면 에러를 낸다.
                # try:
                #     op = op_dict[op_name]
                #     attr = list(filter(lambda x: hasattr(column, x), [op, f'{op}_', f'__{op}__']))[0]
                #     print(attr)
                # except IndexError:
                #     raise Exception(f'Invalid operator name {op_name}')
                # 3.6+ 버전 -> next( (generator by comp) , None) -> 없으면 None이 나옴. 있다면 true인 것 첫번째가 나올 것이다.
                #             next( (generator by comp)) -> 없으면 StopIteration으로 except를 catch해도 된다.
                operator = op_dict[op_name]
                attr = next((op for op in (operator, f'{operator}_', f'__{operator}__') if hasattr(column, op)), None)
                if not attr:
                    raise Exception(f'Invalid filter operator name: {op_name}')

                # 4) value가 json의 null이 올 수도
                if value == 'null':
                    value = None

                # filt_aux에 해당column의  해당연산메서드attr를 꺼내서, value를 호출한 filter를 append
                filt_aux.append(getattr(column, attr)(value))

            # 5. filt_aux에 모아진 column.operatr(value) 필터내용들을, 비재귀 tuple list의 key(filter_op)로 통합
            if 'and' in filter_op:
                filt.append(and_(*filt_aux))
            elif 'or' in filter_op:
                filt.append(or_(*filt_aux))
            else:
                raise Exception(f'Invalid filter operator: {filter_op}')

        return filt

    @classmethod
    def create_filters(cls, model, filters):
        """
        나중에 Mixin으로 들어가면 filters(dict) => 인자 **kwargs로 변경 후, 외부에서는 keyword로만 입력하기. and_={}일때 dict펼치기
                           , filters.items() =>  kwargs.items()로 변경

        print( StaticsQuery.create_filters(User, filters={'id': 1}) [0])
        -> users.id = :id_1
        print( StaticsQuery.create_filters(User, filters={'id__eq': 1}) [0])
        -> users.id = :id_1
        ####  조건을 2개이상 걸 경우, 'and_'나 'or_'를 부모 key로서 걸어줘야한다. 'and'도 되지만, keyword방식에선 못씀. and_=로 걸어야한다
        print( StaticsQuery.create_filters(User, filters={'id': 1, 'username': 'admin'}) [0])
        -> users.id = :id_1
        print( StaticsQuery.create_filters(User, filters={'and_':{'id': 1, 'username': 'admin'}}) [0])
        -> users.id = :id_1 AND users.username = :username_1

        #### depth로 조건을 걸면, and나 or가 안나올때까지 재귀를 태워서, 부모가 list를 받아 연산자를 걸어 최종반환한다
        print( StaticsQuery.create_filters(User, filters={'and_': {'id__lt': 10, 'or_': {'username': 'admin', 'id__ne':1 }}}) [0])
        -> users.id < :id_1 AND (users.username = :username_1 OR users.id != :id_2)
        """
        # 1. dict가 안들어와 -> filters 결과물인 list가 반환이 안되는 상황
        if not filters:
            return []
        # 2. dict를 받아서 filters list를 만든다.
        # CASE 1: dict순회시 => key='and_' or 'or_' / value = 자식dict
        # CASE 2: dict순회시 'and_'나'or_'가 아니라서 => key='column__연산' / value = 값
        # {
        #  'or_1':{ <---- CASE 1
        #       'and_1': { 'id__gt':5, 'id__ne':3 }, <---- CASE 2
        #       'and_2': dict(name__eq='cho') <---- 2-2
        #  },

        total_filters = []

        for key, value in filters.items():
            # CASE 1: dict순회시 => key='and_' or 'or_' / value = 자식dict
            # => 자식dict를 다시 create_filers의 인자로서 재귀로 넣고 filter list를 받은 뒤
            #    연산자에 따라서 묵어준다.
            if 'and' in key or 'or' in key:
                child_filters = and_(*cls.create_filters(model, value)) if 'and' in key \
                    else or_(*cls.create_filters(model, value))
                total_filters.append(child_filters)
                continue

            # CASE 2: dict순회시 'and_'나'or_'가 아니라서 => key='column__연산' / value = 값
            # => column__연산을 split하고, where 내을 list에 append한다.
            # => 어차피 재귀로 타고온 2번째라서, 부모에게 list를 건네, 부모에서 and_()나 or_()로 묶일 예정이다.
            #      이 때, 비교연산자를 안적는 경우, __eq로 간주하게 한다.
            key = cls.split_and_check_name(key)  # # split결과 3개이상나오면 에러 1개, 2개는 넘어감
            if len(key) == 1:
                # split했기 때문에, [ 'username'] 으로 들어가있음. -> key[0]
                column = cls.create_column(model, key[0])
                # # 어차피 and or or로 시작하며, 아닌 턴에서는 list로만 append하면 부모가 and_()나 or_()로 싼다
                total_filters.append(column == value)
            else:  # len(key) == 2:
                column_name, op_name = key
                column = cls.create_column(model, column_name)

                # 3) op string -> op attribute로 변환
                if op_name not in op_dict:
                    raise Exception(f'Invalid filter operator: {op_name}')
                # 3-1) in연산자만 attr확인없이 1개의 sqlachemy연산이 되므로 바로 filt_aux에 추가하면 된다.
                if op_dict[op_name] == 'in':
                    total_filters.append(column.in_(value))
                else:
                    # 3-2) 나머지 연산자들 처리
                    operator = op_dict[op_name]
                    attr = next((op for op in (operator, f'{operator}_', f'__{operator}__') if hasattr(column, op)),
                                None)
                    if not attr:
                        raise Exception(f'Invalid filter operator name: {op_name}')

                    # 4) value가 json의 null이 올 수도
                    if value == 'null':
                        value = None

                    total_filters.append(getattr(column, attr)(value))

        return total_filters

    #####
    # classproperty    #
    #####
    # sqlalchemy가 주는 것 => model이 상속하는 경우 mode빼고, @classproperty로
    # @classproperty
    @classmethod
    def get_column_names(cls, model):
        # 1. inspect를 쓰는 방법 : https://github.com/absent1706/sqlalchemy-mixins/blob/master/sqlalchemy_mixins/smartquery.py
        # => list(inspect(User).columns.keys())
        # 2. ORM(Column객체)과 다른 table의 ColumnProperty를 순회 inspect(User).mapper.column_attrs -> 칼럼순회  -> 이름 column_attr.key
        # 3. model.__table__을 활용하는 법
        # =>list(User.__table__.columns.keys())
        # => __table__을 활용하면 hybrid property 등을 차후 확인할 수 없게 된다.
        #   ex> 'Table' object has no attribute 'all_orm_descriptors'
        #       list(inspect(User).all_orm_descriptors)
        return inspect(model).columns.keys()

    # for create_order_bys
    # @classproperty
    @classmethod
    def get_hybrid_property_names(cls, model):
        items = inspect(model).all_orm_descriptors
        return [item.__name__ for item in items if isinstance(item, hybrid_property)]

    # for create_order_bys
    # @classproperty
    @classmethod
    def get_sortable_columns(cls, model):
        return cls.get_column_names(model) + cls.get_hybrid_property_names(model)

    # for create_order_bys
    @classmethod
    def check_sortable_column(cls, column_name_for_check, model):
        if column_name_for_check not in cls.get_sortable_columns(model):
            raise KeyError(f'Invalid order by column: {column_name_for_check}')

    @classmethod
    def create_order_bys(cls, column_names, model=None):
        """
        StaticsQuery.create_order_bys(User, '-id')
        ->[<sqlalchemy.sql.elements.UnaryExpression object at 0x0000011E9E339B70>]

        Mixin으로 바껴서 model없이 column_names만 받는다면, *column_names로 콤마들을 받아서
        column_names를 인자 1개만 들어와도 list(tuple)로 다루면 된다.

        """
        #### Mixin에서 obj(self)가 쓸 수 있도록 mode을 키워드로 바꿈
        # => none일 경우 자기자신으로
        if not model:
            model = cls

        if not column_names:
            return []

        if not isinstance(column_names, (list, tuple, set)):
            column_names = [column_names]

        order_by_columns = []

        for column_name in column_names:
            #### column_name이 아니라, 칼럼(InstrumentedAttribute) or 증감칼럼(UnaryExpression)으로 들어올 경우
            # => 바로 append시킨다.
            # >>> type(User.id)
            # <class 'sqlalchemy.orm.attributes.InstrumentedAttribute'> <- 일반칼럼을 입력한 경우
            # >>> type(User.id.desc())
            # <class 'sqlalchemy.sql.elements.UnaryExpression'> <- ColumnElement
            # => 변경해줘야한다.
            if not isinstance(column_name, str):
                if isinstance(column_name, InstrumentedAttribute):
                    column_name = column_name.asc()
                    order_by_columns.append(column_name)
                elif isinstance(column_name, UnaryExpression):
                    order_by_columns.append(column_name)
                else:
                    raise ValueError(f'잘못된 입력입니다 : {column_names}')
                continue

            # 지연으로 맥일 함수를 ()호출없이 가지고만 있는다.
            # -를 달고 있으면, 역순으로 맥인다.
            # order_func = desc if column_name.startswith(DESC_PREFIX) else asc

            #### 칼럼으로 순서 적용가능한지는 model.sortable_attributes안에 있는지로 확인한다.
            # -> -달고 있으면 때고 검사해야한다.
            # if column_name not in model.sortable_attributes:
            #     raise KeyError(f'Invalid order column: {column_name}')
            #### 2개를 한번에 처리(order_func + '-'달고 있으면 떼기)
            order_func, column_name = (desc, column_name[1:]) if column_name.startswith(DESC_PREFIX) \
                else (asc, column_name)

            #### 추가 column_name에 id__count 등 집계함수가 있을 수 있다. => 검사는 순수 칼럼네임만 받아야한다.
            if OPERATOR_OR_FUNC_SPLITTER in column_name:
                column_name_for_check, func_name = column_name.split(OPERATOR_OR_FUNC_SPLITTER)
                cls.check_sortable_column(column_name_for_check, model)
            else:
                cls.check_sortable_column(column_name, model)

            # column을 만들고, desc()나 asc()를 지연으로 맥인다.
            order_by_column = order_func(cls.create_column(model, column_name))

            order_by_columns.append(order_by_column)

        return order_by_columns

    # for create_eager_options
    #### 추가) join과 유사한 eagerload를  위한 statement
    @classmethod
    def create_eager_options(cls, schema=None):
        """
        BaseQuery.create_eager_options({'user' : 'joined', 'comments': ('subquery', {'users': 'joined'})})
        => flatten_schema:  => {'user': JOINED, 'comments': SUBQUERY, 'comments.users': JOINED'}
        => to_eager_options => [<sqlalchemy.orm.strategy_options._UnboundLoad object at 0x000002820F626D30>, <sqlalchemy.orm.strategy_options._UnboundLoad object at 0x000002820F626DD8>, <sqlalchemy.orm.strategy_options._UnboundLoad object at 0x000002820F626EB8>]

        """
        if not schema:
            return []

        flatten_schema = _flat_schema(schema)
        return _to_eager_options(flatten_schema)

    @classmethod
    def create_select_statement(cls, model,
                                eager_options=None,
                                selects=None,
                                filters=None,
                                order_bys=None,
                                ):
        """
        1. 필터만 걸 때 -> 모든 칼럼
        print(BaseQuery.create_select_statement(User, filters={'id__in': [1,2,3,4]}))
        ---
        SELECT users.add_date, users.pub_date, users.id, users.username, users.password_hash, users.email, users.last_seen, users.is_active, users.avatar, users.sex, users.address, users.phone, users.role_id
        FROM users
        WHERE users.id IN (__[POSTCOMPILE_id_1])

        2. selects에 뽑고 싶은 칼럼 기입
        print(BaseQuery.create_select_statement(User, selects=['username'], filters={'id__in': [1,2,3,4]}))
        ---
        SELECT users.username
        FROM users
        WHERE users.id IN (__[POSTCOMPILE_id_1])

        3.print(BaseQuery.create_select_statement(User, selects=['username'], filters={'id__in': [1,2,3,4]}, order_bys=['-id', 'username']))
        ---
        SELECT users.username
        FROM users
        WHERE users.id IN (__[POSTCOMPILE_id_1]) ORDER BY users.id DESC, users.username ASC

        4. 'joined' eager load + 관계칼럼명(관계속성) => nested outerjoin
           => 가장 깊은 곳만 'joined'를 명시해주고, 중간방법 tuple을 생략하면 joined로 인식하여 직접 outer join한다.

        4-1) 1번만 outerjoin
        print(BaseQuery.create_select_statement(Category, eager_options={'posts' : 'joined'}))
        SELECT categories.*, posts_1.*
        FROM categories
        LEFT OUTER JOIN posts AS posts_1 ON categories.id = posts_1.category_id

        4-2) 2번 nested outer join
        print(BaseQuery.create_select_statement(Category, eager_options={'posts' : { 'tags':'joined'}}))
        {'posts': 'joined', 'posts.tags': 'joined'}
        SELECT categories.*, tags_1.*_1 AS , posts_1.*
        FROM categories
        LEFT OUTER JOIN posts AS posts_1 ON categories.id = posts_1.category_id
        LEFT OUTER JOIN (posttags AS posttags_1 JOIN tags AS tags_1 ON tags_1.id = posttags_1.tag_id) ON posts_1.id = posttags_1.post_id

        5. 'subquery' or 'selectin' -> inner join이지만, sql(db-level)에선 안찍히고, main entity의 관계속성에 로드된다.
        # => lazy='dynamic'과 반대되는 개념으로 lazy='subquery', lazy='selectin'이 적용되서 load되는 것 과 같다.
        # =>  to get relationships, NO additional query is needed

        print(BaseQuery.create_select_statement(Category, eager_options={'posts' : 'subquery'}))
        SELECT categories.*
        FROM categories

        print(BaseQuery.create_select_statement(Category, eager_options={'posts' : 'selectin'}))
        SELECT categories.*
        FROM categories
        """

        stmt = (
            select(*cls.create_columns(model, column_names=selects))
            .options(*cls.create_eager_options(schema=eager_options))
            .where(*cls.create_filters(model, filters=filters))
            #### order_by는 Mixin에서 self메서드로 사용되므로, cls용 model은 키워드로 바꿈 => 사용시 인자 위치도 바뀜.
            .order_by(*cls.create_order_bys(order_bys, model=model))
        )

        return stmt

    # columns, filters를 둘다 받아 내부에서 사용 + 실행은 안한 쿼리 -> 외부에서 .first()일지 .all()일지도 밖에서 결정한다.
    @classmethod
    def execute_scalars(cls, model, column_names=None, filters=None):
        """
        외부에서 .all()  or .first()를 선택해서 사용한다.
        """
        with DBConnectionHandler() as db:
            return db.session.scalars(
                select(*cls.create_columns(model, column_names))
                .where(*cls.create_filters(model, filters))
            )

    @classmethod
    def execute_scalar(cls, model, column_names=None, filters=None):
        """
         StaticsQuery.execute_scalar_select(User, [('id', 'count')])
        -> 1
        """
        with DBConnectionHandler() as db:
            return db.session.scalar(
                select(*cls.create_columns(model, column_names))
                .where(*cls.create_filters(model, filters))
            )

    @classmethod
    def execute_to_dict_list(cls, stmt):
        """
            [{'sex': '미정', 'count': 1}, {'sex': '남자', 'count': 5}]

        """
        with DBConnectionHandler() as db:
            # return db.session.execute(stmt).mappings().all()
            # enum변환을 못해서 새로 작성
            result = list()
            for row in db.session.execute(stmt):
                temp_dict = row._asdict()
                for col_name in stmt.columns.keys():
                    # Enum칼럼인 경우, {'sex': [<SexType.미정: 0>], 'count': [1]})
                    col_value = getattr(row, col_name)
                    if isinstance(col_value, enum.Enum):
                        col_value = col_value.name
                    temp_dict.update({col_name: col_value})  # inplace
                # print(temp_dict)
                result.append(temp_dict)

            return result

    @classmethod
    def execute_to_list_in_dict(cls, stmt):
        # print('stmt.columns  >> ', stmt.columns)
        # print('stmt.columns.keys()  >> ', stmt.columns.keys())
        # stmt.columns  >>  ImmutableColumnCollection(anon_1.id, anon_1.name, anon_1.count)
        # stmt.columns.keys()  >>  ['id', 'name', 'count']
        """
        defaultdict(<class 'list'>, {'id': [1, 2, 3], 'name': ['123', '캬캬', '게시판3'], 'count': [1, 1, 1]})

        """
        result = defaultdict(list)

        with DBConnectionHandler() as db:
            for row in db.session.execute(stmt):
                for col_name in stmt.columns.keys():
                    # Enum칼럼인 경우, {'sex': [<SexType.미정: 0>], 'count': [1]})
                    # ->속성은 똑같이 : sqlalchemy.orm.attributes.InstrumentedAttribute 이지만
                    # -> 출력이 execute된 결과에서 꺼내면
                    # type(getattr(row, name))  >>  <enum 'SexType'> 의 enum이 나온다
                    col_value = getattr(row, col_name)
                    if isinstance(col_value, enum.Enum):
                        col_value = col_value.name
                        #  {'sex': ['미정'], 'count': [1]})
                    result[col_name].append(col_value)

        return result

    @classmethod
    def execute_to_tuple_list(cls, stmt):
        # print('stmt.columns  >> ', stmt.columns)
        # print('stmt.columns.keys()  >> ', stmt.columns.keys())
        # stmt.columns  >>  ImmutableColumnCollection(anon_1.id, anon_1.name, anon_1.count)
        # stmt.columns.keys()  >>  ['id', 'name', 'count']
        """
        defaultdict(<class 'list'>, {'id': [1, 2, 3], 'name': ['123', '캬캬', '게시판3'], 'count': [1, 1, 1]})

        """
        result = list()

        with DBConnectionHandler() as db:
            for row in db.session.execute(stmt):
                new_row = tuple()
                for col_name in stmt.columns.keys():
                    # Enum칼럼인 경우,[ {(<SexType.미정: 0>, 1)]
                    # ->속성은 똑같이 : sqlalchemy.orm.attributes.InstrumentedAttribute 이지만
                    # -> 출력이 execute된 결과에서 꺼내면
                    # type(getattr(row, name))  >>  <enum 'SexType'> 의 enum이 나온다
                    print(row, col_name)
                    col_value = getattr(row, col_name)
                    if isinstance(col_value, enum.Enum):
                        col_value = col_value.name
                    new_row += (col_value,)
                result.append(new_row)

        return result

    @classmethod
    def execute_to_named_tuple_list(cls, stmt):

        result = list()
        col_names = stmt.columns.keys()
        NamedRow = namedtuple('NamedRow', ' '.join(col_names), rename=True)

        with DBConnectionHandler() as db:
            for row in db.session.execute(stmt):
                new_row = NamedRow(*row)
                # for col_name in col_names:
                # Enum칼럼인 경우,[ {(<SexType.미정: 0>, 1)]
                # ->속성은 똑같이 : sqlalchemy.orm.attributes.InstrumentedAttribute 이지만
                # -> 출력이 execute된 결과에서 꺼내면
                # type(getattr(row, name))  >>  <enum 'SexType'> 의 enum이 나온다
                # col_value = getattr(new_row, col_name)
                # if isinstance(col_value, enum.Enum):
                #     col_value = col_value.name
                # new_row
                result.append(new_row)

        return result

    # 내부용 - 공통
    @staticmethod
    def get_start_date_from(end_date, interval_unit, interval_value, is_during=True):
        """
        end_date로부터, 단위와 기간을 받아, 해당하는 start_date를 얻는다.
        ex>  7월13일(end_date) - 1일 단위로 3전 -> 7월 10일(start_date)
        !! 만약, 3일동안의 data를 구한다고 하면, interval_value는 2가 되어야한다
        !!      3일 전을 start_date로 => 12(1일전), 11(2일전), 10(3일전) => 10일~ 13일을 계산할 경우, 총 4일을 계산한다
                하지만, 주로 지난 7주일<<<동안>>> 을 계산을 많이 한다.
          => is_during=True 옵션을 받아, 7-1일 전 => 6일 전 => 오늘 포함 7일 동안으로 계산하자.
         -> end_date을 포함하여 start ~ end_date 동안을 계산함.
         ex> datetime.date(2023, 2, 11)
            StaticsQuery.get_start_date_from(datetime.date.today(), 'day', 7)
            datetime.date(2023, 2, 5)
            StaticsQuery.get_start_date_from(datetime.date.today(), 'day', 1)
            datetime.date(2023, 2, 11)
            StaticsQuery.get_start_date_from(datetime.date.today(), 'day', 1, is_during=False)
            datetime.date(2023, 2, 10)

        :param interval_unit: 'day', 'month', 'year' string
        :param interval_value: int
        :param is_during: boolean
        :return:
        """

        if is_during:  # 지난 value(7일) unit(일) 동안 = end_date에서 6일 전을 start_date로
            interval_value = interval_value - 1

        interval_map = {
            'day': lambda x: relativedelta(days=x),
            'month': lambda x: relativedelta(months=x),
            'year': lambda x: relativedelta(years=x),
        }

        if interval_unit not in interval_map:
            raise Exception(f'Invalid interval_unit: {interval_unit} -> must in "day" or "month" or "year"')

        start_date = end_date - interval_map[interval_unit](interval_value)

        return start_date

    # mysql : https://devjhs.tistory.com/89
    # 년: %Y (4자리 년도), %y (2자리 년도)
    # 월: %m(2자리 숫자), %c (1자리), %M(영문길), %b(영문짧)
    # 일: %d(2자리 숫자), %e (1자리)
    # 요일: %W(긴요일) %a(짧은 요일)
    # 시: %H(24시간) %I(12시간)
    # 분: %i(분)
    # 초: %S
    # 시분초: %T(hh:mm:SS), %r(hh:mm:ss AP|PM)

    # postgresql의 to_char는 올 대문자가 필요하다.
    # : https://www.postgresqltutorial.com/postgresql-string-functions/postgresql-to_char/
    date_format_map = {
        'sqlite': {
            'day': '%Y-%m-%d',
            'month': '%Y-%m',
            'year': '%Y',
        },
        'mysql': {
            'day': '%Y-%m-%d',
            'month': '%Y-%m',
            'year': '%Y',
        },
        'postgresql': {
            'day': 'YYYY-MM-DD',
            'month': 'YYYY-MM',
            'year': 'YYYY',
        }
    }

    @classmethod
    def get_date_format(cls, interval_unit):

        date_format = cls.date_format_map[cls.DIALECT_NAME][interval_unit]

        return date_format

    @classmethod
    def to_string_column(cls, date_column, date_format):

        if cls.DIALECT_NAME == 'postgresql':
            return func.to_char(date_column, date_format).label('date')
        elif cls.DIALECT_NAME == 'mysql':
            return func.date_format(date_column, date_format).label('date')
        elif cls.DIALECT_NAME == 'sqlite':
            return func.strftime(date_format, date_column).label('date')
        else:
            raise NotImplementedError(f'Invalid dialect : {cls.DIALECT_NAME}')


class StaticsQuery(BaseQuery):

    # 내부용
    @classmethod
    def count_until(cls, model, srt_date_column_name, end_date, filters=None, is_distinct=False):
        """
        해당column의 값을 start_date값으로부터  특정date까지 몇개의 데이터가 있는지 파악한다
         - 주로, (동일한 srt_date_column==시작date   ~   end_date)1번 - (동일한 srt_date_column==시작date   ~   end_date)1번을 계산해서 그 차이를 계산할 때 쓰인다.
         - ex> StaticsQuery.count_until(entity, 'add_date', end_date)
        :param model: sqlalchemy Entity
        :param srt_date_column_name: string
        :param end_date:  date or datetime
        :param filters:
        :param is_distinct: boolean
        :return:
        """
        with DBConnectionHandler() as db:
            # id_column = getattr(model, 'id', None)
            id_column = cls.create_column(model, 'id')

            if is_distinct:
                id_column = distinct(id_column)

            # srt_date_column = getattr(model, srt_date_column_name, None)
            srt_date_column = cls.create_column(model, srt_date_column_name)

            stmt = (
                select(func.count(id_column))
                .where(func.date(srt_date_column <= end_date))
                .where(*cls.create_filters(model, filters=filters))
            )

            return db.session.scalar(stmt)

    # 외부용
    @classmethod
    def calc_diff_count_and_rate_from_to(cls, model, srt_date_column, from_date, to_date, filters=None,
                                         is_distinct=False):
        """
        srt_date_column값으로부터 ~~~~~~~~~~ to_date
        srt_date_column값으로부터 ~~~~ from_date
                                     <-----------> 차이의 count 및 rate를 계산한다.
        :param model:
        :param srt_date_column:
        :param from_date:
        :param to_date:
        :param filters:
        :param is_distinct:
        :return:
        """
        to_count = cls.count_until(model, srt_date_column, to_date, filters=filters, is_distinct=is_distinct)
        from_count = cls.count_until(model, srt_date_column, from_date, filters=filters, is_distinct=is_distinct)
        diff_count = from_count - to_count

        # 시작값이 0이면, rate계산시 zerodivision error
        # -> (끝값 x 100)% 로 계산한 뒤, 반올림한다. ex> 0.9 -> 90.0%
        if from_count == 0:
            diff_rate = round(to_count * 100, 2)
        else:
            diff_rate = round((to_count - from_count) / from_count * 100, 2)

        return diff_count, diff_rate

    # 내부용
    @classmethod
    def create_count_by_column_subquery(cls, model, group_by_column_name,
                                        count_column_name='id',
                                        filters=None,
                                        is_distinct=False,
                                        for_outer=True
                                        ):
        """
        group_by_column별 count_column의 갯수를 카운팅한 뒤, 'count'라는 칼럼을 만들고, subquery로 반환한다.
        -> 주로 Many에 대해 fk(one.id)별 many의 갯수를 subquery로 만들 때 사용한다.

        ex>  subq = StaticsQuery.create_count_by_column_subquery(Post, 'category_id')
                    cls.create_count_by_column_subquery(ManyEntity, group_by_column='fk(one_id)')

        ->  subq = select(Post.category_id, func.coalesce(func.count(Post.id), 0).label('count')) \
                    .group_by(Post.category_id) \
                    .subquery()
            stmt = select(Category.name, subq.c.count) \
                    .join_from(Category, subq, isouter=True) \
                    .order_by(subq.c.count.desc())
        """
        count_column = cls.create_column(model, count_column_name)

        # if isinstance(model, Table):
        #     group_by_column = getattr(model.c, group_by_column, None)
        # else:
        #     group_by_column = getattr(model, group_by_column, None)

        group_by_column = cls.create_column(model, group_by_column_name)
        # if not group_by_column:
        # if group_by_column is None:
        #     raise Exception(f'Invalid group_by_column : {group_by_column}')

        if is_distinct:
            count_column = distinct(count_column)

        # subquery & outerjoin을 위해, None일 땐, 0으로 만들어주기 (default True)
        count_column = func.count(count_column)

        if for_outer:
            count_column = func.coalesce(count_column, 0)

        return (
            # subqeury로서 label 붙여주기
            select(group_by_column, count_column.label('count'))
            .where(*cls.create_filters(model, filters))
            .group_by(group_by_column)
        ).subquery()

    # 외부용
    @classmethod
    def calculate_many_count_by_one_column(cls, one_model, one_column, many_model,
                                           many_fk_column=None,
                                           many_count_column='id',
                                           one_filters=None,
                                           many_filters=None,
                                           many_is_distinct=False,
                                           many_for_outer=True,
                                           descending=True,
                                           ):
        """
        1) many에서 먼저, many 속 one의 pk인 'many_fk_column'로 groupby하며 many의 id로 count를 세서 subquery를 만들고
        2) one에 subquery를 left outer join한 뒤
        3) one의  'one_column'별로, join된 count를 표기한다. -> desceding = False일 경우 count를 오름차순으로

        group_by_column별 count_column의 갯수를 카운팅한 뒤, 'count'라는 칼럼을 만들고, subquery로 반환한다.
        -> 주로 Many에 대해 fk(one.id)별 many의 갯수를 subquery로 만들 때 사용한다.

        ex>  subq = StaticsQuery.create_count_by_column_subquery(Post, 'category_id')
                    cls.create_count_by_column_subquery(ManyEntity, group_by_column='fk(one_id)')

              subq = select(Post.category_id, func.coalesce(func.count(Post.id), 0).label('count')) \
                    .group_by(Post.category_id) \
                    .subquery()
            ->stmt = select(Category.name, subq.c.count) \
                    .join_from(Category, subq, isouter=True) \
                    .order_by(subq.c.count.desc())
        """
        one_column = getattr(one_model, one_column, None)
        if not one_column:
            raise Exception(f'Invalid column: {one_column}')

        if not many_fk_column:
            # many에서는 fk(oneEntity_id)를 groupby로 넣어 one.id를 주기위해 센다 ex> Post.category_id
            # id_ = one_model.__tablename__ + '_id'
            # many_fk_column = getattr(many_model, id_, None)
            #### inspect(One) .relationships -> 관계entity class(r.mapper.class_)들 중 many_model로 필터링
            #### -> Many Entity의 columns들 중 , .foreign_keys ( set{}결과)가 차있는 fk칼럼들 필터링
            # [Column('category_id', Integer(), ForeignKey('categories.id'), table=<posts>, nullable=False)]
            # [col for col in Post.__table__.columns if col.foreign_keys and col.table.name == Post.__tablename__][0].key
            print(one_model.__tablename__)
            #### cf) 관계테이블일 경우, 바로 __table__과 동급 Table객체이므로 따로 처리해줘야한다?!
            if isinstance(many_model, Table):
                many_model.__table__ = many_model

            print([many_col.table.name for many_col in many_model.__table__.columns if
                   many_col.foreign_keys])
            many_fk_columns = [many_col for many_col in many_model.__table__.columns if many_col.foreign_keys]
            #  # posts.category_id
            print(many_fk_columns)
            # list([col for col in Post.__table__.columns if col.foreign_keys]   [0].foreign_keys)[0].target_fullname
            # 'categories.id'
            many_fk_column = next((col for col in many_fk_columns for fk_data in col.foreign_keys if
                                   fk_data.target_fullname == one_model.__tablename__ + '.id'), None)
            if not many_fk_columns:
                raise Exception(f'두 entity간 fk column이 Many Entity {many_model.__tablename__}에 존재하지 않습니다.')
            print(many_fk_column)
            # column객체의 name은 .key로 꺼낸다.
            many_fk_column = many_fk_column.key
            print(many_fk_column)

        print("1차 완료")

        #### cf2) 관계테이블일 경우, count_column='id'에 many가 자신의 갯수를 셀 때, many(posttags)에 자신의 id가 없을 수 있고
        ####     => many로 들어오는 fk칼럼을 찾아줘야한다. id를 카운팅하게 해줘야한다.
        # ex> StaticsQuery.calculate_many_count_by_one_column(Tag, 'name', posttags)
        # => 위에서는 FK데이터 속에 one_model의 테이블명.id 로 fk를 골라냇지만, 여기선, one_model이 아닌 나머지 모델로 골라내야한다.
        #  =>
        # one_model의 fk data의 target_fullname 대신 자신의 name(name=안주면X) 자신의column의 name이 ->  many의 네임과 같아야한다?!
        # many_model.__tablename__ 대신 .name을 사용한다.
        if isinstance(many_model, Table):
            many_fk_columns = [many_col for many_col in many_model.__table__.columns if many_col.foreign_keys]
            # print(many_fk_columns)
            # [Column('tag_id', Integer(), ForeignKey('tags.id'), table=<posttags>, primary_key=True, nullable=False),
            # Column('post_id', Integer(), ForeignKey('posts.id'), table=<posttags>, primary_key=True, nullable=False)]
            for col in many_fk_columns:
                for fk_data in col.foreign_keys:
                    print(fk_data.name)
                    print(fk_data.column.name)
                    print(fk_data.target_fullname)
                    print(one_model.__tablename__ + '.id')
                    # None
                    # id
                    # posts.id
            many_count_column = next((col for col in many_fk_columns for fk_data in col.foreign_keys if
                                      fk_data.target_fullname != one_model.__tablename__ + '.id'), None)
            many_count_column = many_count_column.key

            print(many_count_column)

        subquery = cls.create_count_by_column_subquery(many_model, many_fk_column,
                                                       count_column=many_count_column,
                                                       filters=many_filters,
                                                       is_distinct=many_is_distinct,
                                                       for_outer=many_for_outer
                                                       )
        print('subquery  생성완료>> ')

        with DBConnectionHandler() as db:
            print('DBConnectionHandler() as db 진입완료 ')

            print('subquery  >> ', subquery)

            #### 여기서도 갯수가 없으면 func.coalesce
            # many에서 fk별 count도 0 초기값
            # one에서 outer join시킬 때도, 0초기값? => 안해주면 None으로 뜨더라..
            # => 애초에 Many에서 count할 데이터가 없어서 outerjoin될 row자체가 없는 경우를 대비한다.
            stmt = (
                select(one_column, func.coalesce(subquery.c.count, 0))
                .join_from(one_model, subquery, isouter=True)
                .where(*cls.create_filters(one_model, one_filters))
            )

            if descending:
                stmt = stmt.order_by(subquery.c.count.desc())
            else:
                stmt = stmt.order_by(subquery.c.count.asc())

            # [('분류1', 5), ('22', 2)]
            result = db.session.execute(stmt)
            print('result  >> ', result)
            # return result
            #### <sqlalchemy.engine.result.ChunkedIteratorResult object at 0x000001D37F3A24A8>
            #### ChunkedIteratorResult 자체를 return해서 외부에서 사용할 순 없다.
            #### => 연결된 객체라.. with꺼지고 나서 연결데이터를 밖에서 사용(순회)하면 에러 난다.
            #### => list() 및 사용해놓고 반환해야한다.
            return list(result)

    #### 외부용 -> 차트용
    @classmethod
    def agg(cls, model, group_by_column, agg_dict,
            select_column_names=None,
            filters=None,
            is_distinct=False,
            descending=True,
            limit=5
            ):
        """
        1. select_column_names을 지정해주지 않으면 groupby 칼럼 + 집계칼럼들이 select된다.
        StaticsQuery.agg(Category, 'id', agg_dict=dict(id='count', name='length'))
        => [(1, 1, 3), (2, 1, 3)]
        2. select_column_names을 지정해주면, select칼럼들 + 집계칼럼들이 select된다.
        StaticsQuery.agg(Category, 'id', agg_dict=dict(id='count', name='length'), select_column_names='name')
        => [('123', 1, 3), ('456', 1, 3)]


         === dict ===
        1. 카테고리의 name별 'count'
        StaticsQuery.agg(Category, 'name', agg_dict=dict(id='count'))
        defaultdict(<class 'list'>, {
            'name': ['123', '456'],
            'count': [1, 1]
        })

        2. 카테고리의 name별 ['count', 'sum']
        StaticsQuery.agg(Category, 'name', agg_dict=dict(id=['count','sum']))
        defaultdict(<class 'list'>, {
            'name': ['456', '123'],
            'count': [1, 1],
            'sum': [2, 1]
        })
        """

        # 입력된 칼럼은 groupby 기준이자, select 1번째 기본
        group_by_column = cls.create_column(model, group_by_column)

        # 따로 select하고 싶은 칼럼이 없다면, -> groupby 칼럼 + 집계칼럼들을 select할 예쩡이다.
        if not select_column_names:
            select_columns = [group_by_column]
        else:
            # 칼럼 1개만 적을 경우 대비
            if not isinstance(select_column_names, list):
                select_column_names = [select_column_names]
            select_columns = cls.create_columns(model, select_column_names)

        # 먼저 적힌 집계 먼저 발견되는 순으로 order_by에 입력
        order_by_columns = []

        # 3.7이후로는 defaultdict도 순서가 유지된다.
        for col_name, aggs in agg_dict.items():
            # str으로 집계가 1개 올 수 있지만, list로 여러개 집계를 요구할 수 있다.
            # => 1개인 것을 []안에 넣어서, 반복문으로 통일로직을 만든다.
            if not isinstance(aggs, (list, tuple, set)):
                aggs = [aggs]

            # list로 통일후 검증1) 실수로 중복으로 agg_dict={id=['count', 'count']} 방지
            if len(aggs) != len(set(aggs)):
                raise AttributeError(f'Duplicated agg string: {aggs}!')

            # list로 통일후 검증2) 모든요소가 str검사시 true여야한다.
            if not all(isinstance(agg, str) for agg in aggs):
                raise AttributeError(f'Invalid agg string: {aggs}! elements must to be str.')

            for agg in aggs:
                agg_column = cls.create_column(model, col_name)

                if agg == 'count':
                    if is_distinct:
                        agg_column = distinct(agg_column)
                    select_columns = select_columns + [func.coalesce(func.count(agg_column), 0).label(agg)]
                if agg == 'sum':
                    select_columns = select_columns + [func.coalesce(func.sum(cast(agg_column, Integer)), 0).label(agg)]
                if agg == 'length':
                    select_columns = select_columns + [func.coalesce(func.length(agg_column), 0).label(agg)]

                order_by_columns.append(
                    literal_column(agg).desc() if descending else literal_column(agg)
                )

        # with DBConnectionHandler() as db:
        stmt = (
            select(*select_columns)
            .group_by(group_by_column)
            .order_by(*order_by_columns)
            .where(*cls.create_filters(model, filters))
            .limit(limit))

        # return list(db.session.execute(stmt).all())
        # return cls.execute_to_list_in_dict(stmt)
        return cls.execute_to_tuple_list(stmt)

    #### 외부용 -> 차트용
    @classmethod
    def agg_with_relationship(cls, model, col_name, rel_col_name,
                              rel_agg_dict=dict(id='count'),
                              filters=None,
                              rel_filters=None,
                              is_distinct=False,
                              descending=True,
                              limit=5,
                              ):
        """
        카테고리의 네임별 / Post의 id로 센 Count
        StaticsQuery.agg_with_relationship(Category, 'name', 'posts', rel_agg_dict=dict(id=['count']))
        defaultdict(<class 'list'>, {
            'name': ['123', '456'],
            'count': [1, 0]
            })
        카테고리의 네임별 / Post의 id로 센 Count, id의 Sum
        StaticsQuery.agg_with_relationship(Category, 'name', 'posts', rel_agg_dict={'id':['count', 'sum']})
        defaultdict(<class 'list'>, {
            'name': ['123', '456'],
            'count': [1, 0], 'sum': [1, 0]
            })
        """

        group_by_column = cls.create_column(model, col_name)
        select_columns = [group_by_column]

        # Tag.__mapper__.relationships.items()[0]
        # ('posts', <RelationshipProperty at 0x28546b9e3c8; posts>)
        # relationship.target
        # Table('posts', MetaData()...
        rel_model = cls.get_relation_model(model, rel_col_name)

        #### __mapper__에서는 RelationshipProperty을 꺼낼 수 있고 -> .target으로 table객체를 꺼낼 수 있지만
        # join에 활용되는 orm.attributes.InstrumentedAttribute이랑은 다르다.
        # https://stackoverflow.com/questions/19641908/flask-sqlalchemy-manual-orm-relationshipproperty-object-has-no-attribute-par
        # sqlalchemy.exc.ArgumentError: Join target, typically a FROM expression, or ORM relationship attribute expected, got <RelationshipProperty at 0x1c8a2ee5e48; posts>.
        rel_column = cls.create_column(model, rel_col_name)

        # 먼저 적힌 집계 먼저 발견되는 순으로 order_by에 입력
        order_by_columns = []

        # 3.7이후로는 defaultdict도 순서가 유지된다.
        for col_name, aggs in rel_agg_dict.items():
            # str으로 집계가 1개 올 수 있지만, list로 여러개 집계를 요구할 수 있다.
            # => 1개인 것을 []안에 넣어서, 반복문으로 통일로직을 만든다.
            if not isinstance(aggs, (list, tuple, set)):
                aggs = [aggs]

            # list로 통일후 검증1) 실수로 중복으로 agg_dict={id=['count', 'count']} 방지
            if len(aggs) != len(set(aggs)):
                raise AttributeError(f'Duplicated agg string: {aggs}!')

            # list로 통일후 검증2) 모든요소가 str검사시 true여야한다.
            if not all(isinstance(agg, str) for agg in aggs):
                raise AttributeError(f'Invalid agg string: {aggs}! elements must to be str.')

            for agg in aggs:
                agg_column = cls.create_column(rel_model, col_name)
                if agg == 'count':
                    if is_distinct:
                        agg_column = distinct(agg_column)
                    select_columns = select_columns + [func.coalesce(func.count(agg_column), 0).label(agg)]
                if agg == 'sum':
                    select_columns = select_columns + [func.coalesce(func.sum(cast(agg_column, Integer)), 0).label(agg)]
                if agg == 'length':
                    select_columns = select_columns + [func.coalesce(func.length(agg_column), 0).label(agg)]

                order_by_columns.append(
                    literal_column(agg).desc() if descending else literal_column(agg)
                )

        # with DBConnectionHandler() as db:
        #### join되는 관계모델의 filters는 join에 걸어 join 조건으로 추가해서 join되기 전에 where로 필터링되게 한다.
        # https://stackoverflow.com/questions/48120944/can-you-add-conditions-to-the-on-clause-of-a-relationship-join-in-sqlalchemy
        #### one model의 조건은 where에 걸어 join후에 시행된다.
        #### => join(테이블, 추가조건)은 가능한데, join(관계필드, 추가조건)은 안된다.
        ####    => join(테이블, 추가조건)만 주면, .id == .fk연결을 안하고 추가조건만 연결한다.
        ####    => join(테이블, and_( .id == .fk , 추가조건))으로 가야한다.
        ####           .fk를 직접 사용하지말고, and_( 관계필드 , 추가조건)로 관계필드만 주면 .id == .fk가 자동연결된다.
        stmt = (
            select(*select_columns)
            # 1차 => rel_filters를 그냥 넣으면  안걸림.
            # .join(rel_column, *cls.create_filters(rel_model, rel_filters), isouter=True) #  error
            # 2차 => 관계칼럼말고, 관계모델로join을 걸면, 찾은 관계모델이 alias로 취급된다.
            # => posttags_1.tag_id [관계 테이블명이 alias가 잡혀버림]
            # => 참고) https://github.com/absent1706/sqlalchemy-mixins/blob/master/sqlalchemy_mixins/smartquery.py
            # FROM tags LEFT OUTER JOIN posts ON tags.id = posttags_1.tag_id AND posts.id = posttags_1.post_id
            # => 관계테이블이 alias로서 posttags_1을 붙여버려 문제가 생긴다.
            # .outerjoin(rel_model, and_(rel_column, *cls.create_filters(rel_model, rel_filters)))
            # .outerjoin(rel_model,  and_(*cls.create_filters(rel_model, rel_filters)))
            # => 추가 조건을 join과 동시에 거려면, 관계칼럼으로 안되며, model로 join하고 id연결조건을 직접 달아줘야한다.
            #     하지만 여기서는, 관계테이블에 의해 공짜로 연결되기 위해서는 관계칼럼으로 join해야한다.
            # :https://stackoverflow.com/questions/34290956/sqlalchemy-condition-on-join-fails-with-attributeerror-neither-binaryexpress
            .outerjoin(rel_column)  # 해결1) 성능은 떨어질지라도, outerjoin부터 시키고
            .where(*cls.create_filters(rel_model, rel_filters))  # 해결2) 거기서 관계모델을 필터링시킨다.
            .where(*cls.create_filters(model, filters))
            .group_by(group_by_column)
            .order_by(*order_by_columns)
            .limit(limit)
        )
        # print(stmt)
        # print('stmt  >> ', stmt)
        # 1) join(테이블, 추가조건만) 줄 경우 -> .id == .fk 연결안됨
        # SELECT categories.id, categories.name, coalesce(count(posts.id), :coalesce_1) AS count
        # FROM categories LEFT OUTER JOIN posts ON posts.title != :title_1 GROUP BY categories.id ORDER BY count DESC
        #  LIMIT :param_1
        # 2) join(테이블, and( 관계필드, 추가조건) 줄 경우 -> .id == .fk 연결시켜준다.
        #  SELECT categories.id, categories.name, coalesce(count(posts.id), :coalesce_1) AS count
        # FROM categories LEFT OUTER JOIN posts ON categories.id = posts.category_id AND posts.id != :id_1 GROUP BY categories.id ORDER BY count DESC
        #  LIMIT :param_1

        #### execute는 반복자에 들어가서야 수행된다.(__iter__) 반복시켜놓고 반환해야 에러가 안걸린다.
        # return list(db.session.execute(stmt))
        # StaticsQuery.agg_relationship(Category, ['id', 'name'], 'posts', rel_agg_list=[('id', 'count')])
        #         [(1, '123', 2)]

        # print(type(db.session.execute(stmt)))
        # print(type(db.session.execute(stmt).all()))
        # <class 'sqlalchemy.engine.result.ChunkedIteratorResult'>
        # <class 'list'> => list라도 내부는 아직 ChunkedIteratorResult라서 return하고 사용하면 에러 난다
        # return db.session.execute(stmt).mappings().all()
        # [{'id': 1, 'name': '123', 'count': 1}, {'id': 2, 'name': '캬캬', 'count': 1}, {'id': 3, 'name': '게시판3', 'count': 1}]
        #### 내가 하고 싶은 것은.. dict list가 아니라, dict list value다
        # column_names = [column.key for column in columns]
        # print('column_names  >> ', column_names)

        # result = dict()
        #             # for name in column_names:
        #             #     result[name] = list()
        #             # for row in db.session.execute(stmt):
        #             #     # print(dir(row))
        #             #     # _values_impl', 'count', 'index', 'keys']
        #             #     # print(row.name, row.count)
        #             #     for name in  column_names:
        #             #         result[name].append(getattr(row, name))
        #             # return result

        #### 이미 작성된 stmt에서 select절의 칼럼정보 및 칼럼이름들을 쉽게 가져올 수있다.
        # print('stmt.columns  >> ', stmt.columns)
        # print('stmt.columns.keys()  >> ', stmt.columns.keys())
        # stmt.columns  >>  ImmutableColumnCollection(anon_1.id, anon_1.name, anon_1.count)
        # stmt.columns.keys()  >>  ['id', 'name', 'count']

        # return cls.execute_to_list_in_dict(stmt)
        # return cls.execute_to_tuple_list(stmt)
        # return cls.execute_to_named_tuple_list(stmt)
        return cls.execute_to_dict_list(stmt)
        # return [{column: value for column, value in row.items()} for row in db.session.execute(stmt).all()]

    ##########
    # series #
    ##########

    #### 내부용 - 시리즈 1
    @classmethod
    def create_date_series_subquery(cls, end_date, interval_unit=None, interval_value=None, start_date=None,
                                    is_during=True):
        """
        series_subq = StaticsQuery.create_series_subquery(end_date, interval_unit='day', interval_value=7)

        WITH RECURSIVE dates(date) AS (
        mysql/sqlite)   SELECT (:start_date) / VALUES (:start_date)
                        UNION ALL
        mysql/sqlite)   SELECT date + interval 1 day / select date(date, '+1 day')
                        FROM dates
                        WHERE date < :end_date

        mysql/sqlite)
                SELECT DATE_FORMAT(date, '%Y-%m-%d')  AS 'date' /
                SELECT strftime('%Y-%m-%d', date) AS 'date'
                )

        postgresql)
                select to_char(generate_series, 'YYYY-MM-DD') as date
                from generate_series('2000-00-00'::DATE, '2000-00-11'::DATE, '1 dayss'::INTERVAL)
        """
        if not start_date:
            start_date = cls.get_start_date_from(end_date, interval_unit, interval_value, is_during=is_during)

        # print(start_date)
        # DIALECT_NAME = cls.get_dialect_name()

        date_format = cls.get_date_format(interval_unit)

        # 1) postgresql만 재귀없이 generate_series로 format에 맞는 date들을 subquery로 만들 수 있다.
        # -> from start, end_date string을 넣고 -> interval로 만들어진 date -> select에서 to_char
        # -> text()에 넣어 'series'라는 이름의 subquery로 변환
        # if DIALECT_NAME == 'postgresql':
        if cls.DIALECT_NAME == 'postgresql':
            stmt = f"""
                    select to_char(generate_series, '{date_format}') as date 
                    from generate_series('{to_string_date(start_date)}'::DATE, '{to_string_date(end_date)}'::DATE, '1 {interval_unit}s'::INTERVAL)
                    """

            return text(stmt).columns(column('date')).subquery('series')

        else:
            # 2) mysql과 sqlite는 재귀를 돌리는데, select/to_char stmt가 서로 다르다.
            #
            # if DIALECT_NAME == 'mysql':
            if cls.DIALECT_NAME == 'mysql':
                select_date = f"SELECT date + interval 1 {interval_unit}"
                to_char = f"DATE_FORMAT(date, '{date_format}')  AS 'date'"
            elif cls.DIALECT_NAME == 'sqlite':
                select_date = f"SELECT date(date, '+1 {interval_unit}')"
                to_char = f"strftime('{date_format}', date) AS 'date' "
            else:
                raise NotImplementedError(f'Not implemented for {cls.DIALECT_NAME}')

            # start_date, end_date를 date형식으로 넣어야하는데, f"{}"로는 string밖에 못나타내니
            # -> text().bindparams()에 string을 넣으면, 자동으로 date로 들어간다?!
            # 3) mysql과 sqlite는 cte사용시 select (시작값) vs values(시작값)이 다르다.

            stmt = f"""
            WITH RECURSIVE dates(date) AS (
                  {'SELECT' if cls.DIALECT_NAME == 'mysql' else 'VALUES'} (:start_date)
                  UNION ALL
                  {select_date}
                  FROM dates
                  WHERE date < :end_date
            )

            SELECT {to_char} FROM dates
            """

        return (
            text(stmt)
            .bindparams(start_date=to_string_date(start_date), end_date=to_string_date(end_date))
            .columns(column('date'))
            .subquery('series')
        )

    #### 내부용 - 시리즈 2
    #### series에 대해 군데군대 date별 count
    @classmethod
    def create_date_to_count_subquery(cls, model, date_column_name, end_date, interval_unit=None, interval_value=None,
                                      filters=None, start_date=None, is_during=True):
        """

        date series에 outerjoin될 <- date별 count
        StaticsQuery.create_date_to_count_subquery(entity, date_column_name, end_date, interval_unit, interval_value,
                                                       filters=filters)
        """
        if not start_date:
            start_date = cls.get_start_date_from(end_date, interval_unit, interval_value, is_during=is_during)

        date_format = cls.get_date_format(interval_unit)
        date_column = cls.create_column(model, date_column_name)
        date_string_column = cls.to_string_column(date_column, date_format)

        stmt = (
            select(date_string_column, func.count(cls.create_column(model, 'id')).label('count'))
            # .where(and_(
            #     start_date <= func.date(date_string_column),
            #     func.date(date_string_column) <= end_date
            # )
            .where(*cls.create_filters(model, filters))
            .where(func.date(date_column).between(start_date, end_date))
            .group_by(date_string_column)
        )

        return stmt.subquery()

    #### 외부용 -> 차트용
    @classmethod
    def count_for_interval(cls, model, date_column_name, end_date,
                           interval_unit=None, interval_value=None,
                           start_date=None, filters=None, add_korean=True):
        """
        StaticsQuery.count_for_interval(Post, 'add_date', date.today(), interval_unit='month',
                                                        interval_value=12)
        return
        defaultdict(<class 'list'>,
        {
            'date': ['3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월', '1월', '2월'],
            'count': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
        )
        """

        series_subquery = cls.create_date_series_subquery(end_date, interval_unit=interval_unit,
                                                          interval_value=interval_value, start_date=start_date)
        values_subquery = cls.create_date_to_count_subquery(model, date_column_name, end_date,
                                                            interval_unit=interval_unit, interval_value=interval_value,
                                                            start_date=start_date, filters=filters)

        stmt = (
            select(series_subquery.c.date.label('date'), func.coalesce(values_subquery.c.count, 0).label('count'))
            .outerjoin(values_subquery, values_subquery.c.date == series_subquery.c.date)
            .order_by(series_subquery.c.date.asc())
        )

        result = cls.execute_to_list_in_dict(stmt)
        if result['date']:
            if interval_unit == 'day':
                result['date'] = list(
                    map(lambda x: f'{int(x.split("-")[-1])}{"일" if add_korean else ""}', result['date']))
            elif interval_unit == 'month':
                result['date'] = list(map(lambda x: f'{int(x.split("-")[-1])}{"월" if add_korean else ""}',
                                          result['date']))  # 이미 Y-m그룹화 상태
            else:
                result['date'] = list(map(lambda x: f'{x}{"년" if add_korean else ""}', result['date']))

        return result
