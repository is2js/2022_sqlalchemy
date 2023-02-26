import enum
from collections import defaultdict, namedtuple, OrderedDict, abc
from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, or_, select, func, distinct, inspect, Table, cast, Integer, literal_column, text, column, \
    Numeric, desc, asc, join, extract
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import InstrumentedAttribute, joinedload, subqueryload, selectinload, aliased, RelationshipProperty, \
    contains_eager
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import ColumnElement, Subquery, Alias, operators
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.util import classproperty

from src.config import db_config
from src.infra.config.connection import DBConnectionHandler

#### import Error유발해서 직접 정의해서 사용
# from src.main.utils.to_string import to_string_date
from src.infra.tutorial3.mixins.utils.classproperty import class_property


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

#### 관계객체들은 aliased == mapper를 가지고 식을 만들기 때문에 getattr(mapper로 만든column, attr)(value)가 안된다.
# operatios에서 지원하지 않은 is, isnot은  isnull이나 eq로 대체한다.
# operator 함수객체는 from sqlalchemy.sql import operators에서 가져올 수 있다.
# op = _operators[op_name]
# expressions.append(op(column, value))
_operators = {
    # lambda c,v로 정의하면 => 외부에서는  dict_value( c, v)로 입력해서 호출한다.
    'isnull': lambda c, v: (c == None) if v else (c != None),
    # 추가 => 실패, alias 관계객체 -> alias관계컬럼으로 식을 만들어야하므로 일반적인 create_column 후 getattr is_를 불러오는게 안됨.
    # => is, isnot_은  eq로 처리하면 된다. is_: eq=None /  isnot: ne=None
    # 'is': lambda c, v:  c is v ,
    # 'is_': operators.is_,
    # 'isnot': lambda c, v:  c is not v ,
    # 'exact': operators.eq,
    'eq': operators.eq,
    'ne': operators.ne,  # not equal or is not (for None)

    'gt': operators.gt,  # greater than , >
    'ge': operators.ge,  # greater than or equal, >=
    'lt': operators.lt,  # lower than, <
    'le': operators.le,  # lower than or equal, <=

    'in': operators.in_op,
    'notin': operators.notin_op,
    'between': lambda c, v: c.between(v[0], v[1]),

    'like': operators.like_op,
    'ilike': operators.ilike_op,
    'startswith': operators.startswith_op,
    'istartswith': lambda c, v: c.ilike(v + '%'),
    'endswith': operators.endswith_op,
    'iendswith': lambda c, v: c.ilike('%' + v),
    'contains': lambda c, v: c.ilike('%{v}%'.format(v=v)),

    'year': lambda c, v: extract('year', c) == v,
    'year_ne': lambda c, v: extract('year', c) != v,
    'year_gt': lambda c, v: extract('year', c) > v,
    'year_ge': lambda c, v: extract('year', c) >= v,
    'year_lt': lambda c, v: extract('year', c) < v,
    'year_le': lambda c, v: extract('year', c) <= v,

    'month': lambda c, v: extract('month', c) == v,
    'month_ne': lambda c, v: extract('month', c) != v,
    'month_gt': lambda c, v: extract('month', c) > v,
    'month_ge': lambda c, v: extract('month', c) >= v,
    'month_lt': lambda c, v: extract('month', c) < v,
    'month_le': lambda c, v: extract('month', c) <= v,

    'day': lambda c, v: extract('day', c) == v,
    'day_ne': lambda c, v: extract('day', c) != v,
    'day_gt': lambda c, v: extract('day', c) > v,
    'day_ge': lambda c, v: extract('day', c) >= v,
    'day_lt': lambda c, v: extract('day', c) < v,
    'day_le': lambda c, v: extract('day', c) <= v,
}

# for create_eager_options
# 상수로 만든 뒤, 사용시 import해서 쓰도록

## eager load map
eager_load_map = {
    'joined': lambda c_name: joinedload(c_name),
    'inner_joined': lambda c_name: joinedload(c_name, innerjoin=True),
    'subquery': lambda c_name: subqueryload(c_name),
    'selectin': lambda c_name: selectinload(c_name)
}






class BaseQuery:
    DIALECT_NAME = db_config.get_dialect_name()

    DESC_PREFIX = '-'
    OPERATOR_OR_AGG_SPLITTER = '__'
    RELATION_SPLITTER = '___'

    ## eager types
    JOINED = 'joined'
    INNER_JOINED = 'inner_joined'
    SUBQUERY = 'subquery'
    SELECTIN = 'selectin'

    @classmethod
    def get_column(cls, model, column_name):
        # ORM model이 아니라 Table() 객체일 경우 -> .c에서 getattr
        print('type(model)  >> ', type(model))
        # # '*' 처리 2
        # if column_name == '*':
        #     if isinstance(model, (Table, Subquery, Alias)):
        #         return model.c
        #     else:
        #         return model
        #### expr join시 model자체가 string(alias)가 들어오면 text로 작성하여 돌려보낸다.
        if isinstance(model, str):
            return text(model + '.' + column_name)

        #### query_obj .join()시 현재까지의stmt -> Subquery or Alias로 만드는데, 거기서 칼럼 얻어내기
        # if isinstance(model, (Table)):
        if isinstance(model, (Table, Subquery, Alias)):
            column = getattr(model.c, column_name, None)
        else:
            column = getattr(model, column_name, None)
        # Table()객체는 boolean 자리에 입력시 에러
        # if not column:
        if column is None:
            raise Exception(f'Invalid column_name: {column_name} in {model}')

        return column

    @classmethod
    def check_and_split_attr_names(cls, column_name):
        column_name = column_name.split(f'{cls.OPERATOR_OR_AGG_SPLITTER}')
        if len(column_name) > 3:
            raise Exception(f'Invalid func column name: {column_name}')

        return column_name

    @classmethod
    def create_column(cls, model, column_name, in_select=False):
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
            column_name, func_name = cls.check_and_split_attr_names(column_name)  # split결과 3개이상나오면 에러 1개, 2개는 넘어감

            column = cls.get_column(model, column_name)

            #### func 적용 apply_func = 인자 추가
            if func_name.startswith('count'):
                if in_select:
                    column = func.coalesce(func.count(column), 0).label(func_name)
                else:
                    column = func.count(column).label(func_name)
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
        if not isinstance(model, str) and not column_names:
            return [model]

        # expr for join으로 l_select만 None이라고 해서 text('*')를 건네면 안되므로 빈 값을 건네주자.
        elif isinstance(model, str) and not column_names:
            return []

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

    # for agg_with_rel
    # for join relation_mixin
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

    # for create_filters0
    @classmethod
    def _flat_filter_keys_generator(cls, filters):
        for key, value in filters.items():
            if key.lower().startswith(('and_', 'or_')):
                # yield의 depth없는 재귀 호출은 yiedl from 메서드(자식)으로 한다.
                yield from cls._flat_filter_keys_generator(value)
            # 나 자신의 처리(방출)
            else:
                yield key

    # for _parse_path_and_set_alias_map
    @classmethod
    def get_relation_column_names(cls, model):
        """list(User.__mapper__.iterate_properties)
        => [<RelationshipProperty at 0x165ab5d9048; role>, <...]
        """
        return [c.key for c in model.__mapper__.iterate_properties
                if isinstance(c, RelationshipProperty)]

    # for _parse_path_and_set_alias_map
    @classmethod
    def check_rel_column_name(cls, parent_model, rel_column_name):
        # 부모model의 .relation칼럼 목록에 rel_column_name이 없으면 잘못된 것이다.
        if rel_column_name not in cls.get_relation_column_names(parent_model):
            raise KeyError(f'Invalid relationship name: {rel_column_name}')

    # for create_filters0
    @classmethod
    def _parse_path_and_set_alias_map(cls, parent_model, parent_path, attrs, alias_map):
        """
        input attrs: ['id__gt', 'id__lt', 'tags___property__in']
        output: => OrderedDict([('tags', (<AliasedClass at 0x1de19e32908; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001DE19999150>))])
        """
        # 1. relations에는 일단 ___으로 split하여 rel_column_name(key)에 해당 attr들을 list로 모은다.
        relations = defaultdict(list)

        for attr in attrs:
            # 1) 제일 먼저 관계속성이 찍혀잇는지 확인한다
            if cls.RELATION_SPLITTER in attr:
                # 2) 여러개일 수 있는 '___'에서 첫번째 껏으로만 자르고, 뒤에는 안자른다는 split(, 1)
                # 'related___property__in'.split('___', 1) => ['related', 'property__in']
                rel_column_name, rel_attr = attr.split(cls.RELATION_SPLITTER, 1)
                # 3) rel_column_name을 key로 rel_attr들을  list에 모은다.
                relations[rel_column_name].append(rel_attr)

        # 2. 모아진 dict를 순회하면서 현재 진입 model + 부모의 model_path를 이용하여, 자신의 path를 만든다.
        # => path는 ___으로 이어서 부모rel_column_name___현재rel_column_name 형식으로 이어서 만든다.
        # => 이것은 추후 flat한 schema와의 확인을 위해서다.
        for rel_column_name, rel_attr in relations.items():
            # 2-1) rel_colum_name이 유효한지 실제 model에서 검사한다.
            cls.check_rel_column_name(parent_model, rel_column_name)
            # 2-2) split한 ___를 부모model과 붙여서, attr가 빠진 순수 relation칼럼을 ___로 이은 path를 만든다.
            path = (parent_path + cls.RELATION_SPLITTER + rel_column_name) if parent_path \
                else rel_column_name

            # 2-2) rel_columns_name => 관계칼럼을 가져온다( create_column을 쓰면 __를 연산자 or 집계함수 처리해버리니 하면 안됨)
            rel_column = cls.get_column(parent_model, rel_column_name)
            # 2-3) 관계칼럼 -> 관계모델 -> alias까지 씌운다
            aliased_rel_model = aliased(rel_column.property.mapper.class_)
            # 2-4) 저장소 aliases 에  (aliased 관계모델,과 관계칼럼))을 tuple로 현재path에 저장한다.
            alias_map[path] = aliased_rel_model, rel_column

            # 3. 이제 rel_model/path가 부모가 되어 재귀호출한다. 종착역은 없다. 잇을때까지한다. 저장소에 setter만 하기 때문에
            cls._parse_path_and_set_alias_map(aliased_rel_model, path, rel_attr, alias_map)

    # for  create_filter_exprs
    @classmethod
    def get_filterable_attr_names(cls, model):
        return cls.get_column_names(model) + cls.get_relation_column_names(model) + \
               cls.get_hybrid_property_names(model) + cls.get_hybrid_method_names(model)

    # for _create_filters_expr_with_alias_map
    @classmethod
    def create_filter_exprs(cls, model, **filters):
        """
        forms expressions like [Product.age_from = 5,
                                Product.subject_ids.in_([1,2])]
        from filters like {'age_from': 5, 'subject_ids__in': [1,2]}
        Example 1:
            db.query(Product).filter(
                *Product.create_filter_exprs(age_from = 5, subject_ids__in=[1, 2]))
        Example 2:
            filters = {'age_from': 5, 'subject_ids__in': [1,2]}
            db.query(Product).filter(*Product.create_filter_exprs(**filters))
        ### About alias ###:
        If we will use alias:
            alias = aliased(Product) # table name will be product_1
        we can't just write query like
            db.query(alias).filter(*Product.create_filter_exprs(age_from=5))
        because it will be compiled to
            SELECT * FROM product_1 WHERE product.age_from=5
        which is wrong: we select from 'product_1' but filter on 'product'
        such filter will not work
        We need to obtain
            SELECT * FROM product_1 WHERE product_1.age_from=5
        For such case, we can call create_filter_exprs ON ALIAS:
            alias = aliased(Product)
            db.query(alias).filter(*alias.create_filter_exprs(age_from=5))
        Alias realization details:
          * we allow to call this method
            either ON ALIAS (say, alias.create_filter_exprs())
            or on class (Product.create_filter_exprs())
          * when method is called on alias, we need to generate SQL using
            aliased table (say, product_1), but we also need to have a real
            class to call methods on (say, Product.get_relation_column_names)
          * so, we have 'mapper' that holds table name
            and 'cls' that holds real class
            when we call this method ON ALIAS, we will have:
                mapper = <product_1 table>
                cls = <Product>
            when we call this method ON CLASS, we will simply have:
                mapper = <Product> (or we could write <Product>.__mapper__.
                                    It doesn't matter because when we call
                                    <Product>.getattr, SA will magically
                                    call <Product>.__mapper__.getattr())
                cls = <Product>
        """
        # 1. main model외 relation의 alias가 들어온다면, inspect().mapper.class_로 관계model을 가져온다.
        #    => main model 및 관계 alias  =>  mapper로 표현  +  model은 쌩 class만 취급.
        # mapper for create_column / model for attrs검사
        mapper, model = cls.split_mapper_and_model_for_alias(model)

        # 2. filter를 돌면서, 표현식을 만든다.
        expressions = []

        # 연산자 split후 남은 필터옵션(name__eq -> name)이 해당model의 필터링에 쓸 수 있는지 확인한다.
        valid_attrs = cls.get_filterable_attr_names(model)

        for attr, value in filters.items():
            # 2-1) 입력한 필터 옵션이 hybrid method로서 호출될 경우
            #      hybrid메서드는  연산자 연산이 아니라, method(value)를 expr로서 넣어준다.
            #   => 이대, hybrid메서드 호출 주체를 alias로 주기 위해 mapper=옵션을 준다.
            if attr in cls.get_hybrid_method_names(model):
                method = getattr(cls, attr)
                expressions.append(method(value, mapper=mapper))
            # 2-2) 입력한 필터 옵션이 연산자처리인 경우
            else:
                # # 2-2-1) 연산자 포함된 경우, id__gt=1
                # if cls.OPERATOR_OR_FUNC_SPLITTER in attr:
                #     attr_name, op_name = attr.rsplit(cls.OPERATOR_OR_FUNC_SPLITTER, 1)
                #     if op_name not in _operators:
                #         raise KeyError(f'Invalid Operator name `{op_name}` in `{attr}`')
                #     op = _operators[op_name]
                # # 2-2-1) 연산자가 생략되어 eq인 경우, name=1
                # else:
                #     attr_name, op = attr, operators.eq
                #
                # # 3. 연산자 split후 남아있는 attr 이름이 해당model의 필터링 컬럼으로 유효한지 확인.
                # if attr_name not in valid_attrs:
                #     raise KeyError(f'Invalid filtering attr name `{attr_name}` in `{attr}`')
                # column = getattr(mapper, attr_name)

                # 이미 관계는 처리한 상태에서, model + attr로, 표현식만 만들면 된다.
                # 'id'  'id__eq'   'id__count' 'id__count__eq' -> select/order와 다르게,
                # 2-2-1) filter expr는 if __가 있다면, [1]op 'id__eq' [2] op(eq)이 생략된 집계 'id__count' OR  [3] op명시 집계 'id__count__eq'
                #                    __   없다면,  무조건 eq의 생략 & 집계 X이다. 'id'
                print('1. attr  >> ', attr)

                if cls.OPERATOR_OR_AGG_SPLITTER in attr:
                    # attr_name, op_name = attr.rsplit(cls.OPERATOR_OR_AGG_SPLITTER, 1)
                    # 2-2-1-1) __가 있다면, 3 중 1   'id__eq' or 'id__count' or 'id__count__eq'
                    # => 우측 자르기 'id' + op VS  'id' + agg or 'id__count' + op
                    # => 좌측 자르기 'id' + 'eq' VS 'id' + 'count  or  'id' + 'count__op'
                    # => 집계 VS 비집계를 나누려면, 좌측자르기 한 뒤, 확인해야한다?!
                    attr_name, op_or_agg_name = attr.split(cls.OPERATOR_OR_AGG_SPLITTER, 1)
                    print('2. attr_name, op_or_agg_name  >> ', attr_name, op_or_agg_name)

                    # 2-2-1-1-1) 집계인 경우(count or count__eq) => attr_name + agg_name을 create_column으로 보내서 만든다.?!
                    # 'id' + 'count' or 'count__eq'
                    #  => 다시 한번 __여부를 확인하여 없으면 eq생략, 있으면 해당연산자다
                    if op_or_agg_name.startswith(('count', 'sum', 'length')):
                        # 'count__eq'
                        if cls.OPERATOR_OR_AGG_SPLITTER in op_or_agg_name:
                            agg_name, op_name = op_or_agg_name.split(cls.OPERATOR_OR_AGG_SPLITTER, 1)
                            print('3. agg_name, op_name  >> ', agg_name, op_name)

                            op = _operators[op_name]
                            attr_name = attr_name + '__' + agg_name
                            print('4. attr_name  >> ', attr_name)

                            column = cls.create_column(mapper, attr_name)

                        # 'count'
                        else:
                            agg_name = op_or_agg_name
                            print('3. agg_name(no op_name)  >> ', agg_name)
                            attr_name = attr_name + '__' + agg_name
                            print('4. attr_name  >> ', attr_name)
                            column = cls.create_column(mapper, attr_name)
                            op = operators.eq

                    # 2-2-1-1-2) 집계아닌 경우 'id' + 'eq'
                    else:
                        attr_name, op_name = attr.rsplit(cls.OPERATOR_OR_AGG_SPLITTER, 1)
                        if op_name not in _operators:
                            raise KeyError(f'Invalid Operator name `{op_name}` in `{attr}`')
                        op = _operators[op_name]
                        column = getattr(mapper, attr_name)

                    # expressions.append(op(column, value))
                # 2-2-2) __가 없다면, 무조건 eq가 생략된 집계없는 attr
                else:
                    attr_name, op = attr, operators.eq
                    if attr_name not in valid_attrs:
                        raise KeyError(f'Invalid filtering attr name `{attr_name}` in `{attr}`')
                    column = getattr(mapper, attr_name)


                expressions.append(op(column, value))

        return expressions

    # for filter_expr and order_expr
    @classmethod
    def split_mapper_and_model_for_alias(cls, model):
        if isinstance(model, AliasedClass):
            mapper, model = model, inspect(model).mapper.class_
        else:
            mapper = model
        return mapper, model

    # for create_filters0
    @classmethod
    def _create_filters_expr_with_alias_map(cls, model, filters, alias_map):
        """

        """
        for key, value in filters.items():
            # 재귀
            if key.lower().startswith(('and_', 'or_')):
                # 자신의 처리 결과물은 yield from [generator]라서, 재귀호출시 (*재귀)로 처리할 수 있따.
                if key.lower().startswith(('and_')):
                    yield and_(*cls._create_filters_expr_with_alias_map(model, value, alias_map))
                else:
                    yield or_(*cls._create_filters_expr_with_alias_map(model, value, alias_map))
                continue
            # 자신의 처리 filter expr 생성 by cls.create_filters()
            # -> 관계꺼면, 관계model을 map에서 꺼내서 호출하고,
            # -> 아니라면 자신이 처리한다.
            #### 대박
            # 1) filter입력key에 ___가 끼여있으면, 관계model이 주인공 / 아니라면 현재model이 주인공
            #   가장오른족에서 1번째를 split한 뒤  => a___b -> alias_map에서 꺼내 사용한다
            #    'related___user___property__in'.rsplit('___', 1) =>  ['related___user', 'property__in']
            if cls.RELATION_SPLITTER in key:
                # 2)
                rel_column_and_attr_name = key.rsplit(cls.RELATION_SPLITTER, 1)
                model, attr_name = alias_map[rel_column_and_attr_name[0]][0], rel_column_and_attr_name[1]
            else:
                attr_name = key

            # 2) filter입력key에 ___가 입력된 model이 entity / 없으면 attr이다
            yield from cls.create_filter_exprs(model, **{attr_name: value})

    # for _create_order_exprs_with_alias_map
    @classmethod
    def create_order_expr(cls, model, attr):
        # 1) main model 외 aliased rel model이 올 경우, mapper(Alias), model(원본 rel model class)를 구분한다.
        # -> model로는 sortable한 칼럼인지 검사한다.
        # -> mapper로는 getattr( , attr_name)으로 칼럼을 가져온다.
        mapper, model = cls.split_mapper_and_model_for_alias(model)
        # 2) - 달리면 desc를 아니면 asc func을 따로 빼준다.
        order_func, attr = (desc, attr[1:]) if attr.startswith(cls.DESC_PREFIX) \
            else (asc, attr)
        # 3) sortable한 칼럼인지 확인한다.
        cls.check_sortable_column_name(model, attr)
        # 4) 실제 칼럼을 가져올 땐, mapper에서 가져온다(검사만model)
        return order_func(getattr(mapper, attr))

    @classmethod
    def _create_order_exprs_with_alias_map(cls, model, orders, alias_map):
        if not orders:
            return []
        if orders and not isinstance(orders, (list, tuple, set)):
            orders = [orders]
        print('*orders  >> ', *orders)

        expressions = []

        # 변수 추가
        for attr in orders:
            # 1) attr에서는 일단 relation부터 확인한 뒤, alias에서 빼와서 각각의 expr를 만든다.
            if cls.RELATION_SPLITTER in attr:
                # 2) 빼내기 전에 desc 여부를 있으면 떼어내야한다.
                desc_prefix = ''
                if attr.startswith(cls.DESC_PREFIX):
                    desc_prefix = cls.DESC_PREFIX
                    attr = attr.lstrip(cls.DESC_PREFIX)
                # 3) 관계명을 떼온 뒤, alias에서 aliased_rel_model , rel_column을 가져온다.
                # print('attr  >> ', attr)

                rel_column_and_attr_name = attr.rsplit(cls.RELATION_SPLITTER, 1)
                # print('rel_column_and_attr_name  >> ', rel_column_and_attr_name)

                current_model, attr = alias_map[rel_column_and_attr_name[0]][0], desc_prefix + rel_column_and_attr_name[
                    1]
            else:
                # 4)관계명이 없는 경후, 현재 호출 model을 model로, +-을 통째로 attr을 넣어 메서드 내부에서 만들게 한다.
                current_model = model

            # 5) 해당 모델 + attr_name을 가지고 표현식을 만든다.
            # -> main model 전용이라 그냥 들어간다면,
            # print('model, attr  >> ', current_model, attr)

            print('current_model, attr  >> ', current_model, attr)

            expressions.append(cls.create_order_expr(current_model, attr))

        return expressions

    @classmethod
    def create_filters0(cls, model, filters, schema=None, orders=None):
        """
        { or_: {
            'id__gt': 1000,
            and_ : {
                'id__lt': 500,
                'tags___property__in': (1,2,3)
                }
            }
        }
        list(BaseQuery.create_filters0(Post, { 'or_': { 'id__gt': 1000, 'and_' : { 'id__lt': 500, 'tags___property__in': (1,2,3)}}}))
        => attrs : ['id__gt', 'id__lt', 'tags___property__in']
        => alias_map : OrderedDict(([('tags', (<AliasedClass at 0x1de19e32908; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001DE19999150>))])

        => query :
            SELECT tags_1.* posts.*
            FROM posts
            LEFT OUTER JOIN (posttags AS posttags_1 JOIN tags AS tags_1 ON tags_1.id = posttags_1.tag_id)
              ON posts.id = posttags_1.post_id
        => loaded_rel_paths :  ['tags']
        => cls._create_filters_expr_with_alias_map(model, filters, alias_map):
           posts.id > :id_1 OR (posts.id < :id_2 AND tags_1.name IN (__[POSTCOMPILE_name_1]))

        => query :
        SELECT tags_1.add_date, tags_1.pub_date, tags_1.id, tags_1.name, posts.add_date AS add_date_1, posts.pub_date AS pub_date_1, posts.id AS id_1, posts.title, posts."desc", posts.content, posts.has_type, posts.category_id
        FROM posts
        LEFT OUTER JOIN (posttags AS posttags_1 JOIN tags AS tags_1 ON tags_1.id = posttags_1.tag_id)
            ON posts.id = posttags_1.post_id
        WHERE posts.id > :id_2 OR
                posts.id < :id_3 AND tags_1.name IN (__[POSTCOMPILE_name_1])

        =>  query : ORDER BY users_1.id DESC, employees.name ASC
        => *cls._create_order_exprs_with_alias_map(model, orders, alias_map)) :
            users_1.id DESC employees.name ASC

        => not_loaded_flatten_schema  >>  {'posts': 'subquery'}


        """
        flatten_schema = cls._flat_schema(schema)
        if not orders:
            orders = []
        if orders and not isinstance(orders, (list, tuple, set)):
            orders = [orders]


        # 1. filter의 key들만 순서대로 평탄화한다. => _flat_schema처럼 dict {}에 depth로 저장할 게 아니라면
        #   yield를 통해 순차적으로 재귀 방출할 수 있게 한다.
        filter_and_order_attrs = list(cls._flat_filter_keys_generator(filters))  # ['id__gt', 'id__lt', 'tags___property__in']
        # orders에만 포함된 칼럼도 -> alias_map에 포함되어서 -> outerjoin되어야한다.
        # -> 여기는 연산자가 없이 -name, tags___name 형태로, 존재하니 앞에 -만 떼서 넣어주면 된다.
        filter_and_order_attrs += list(map(lambda s: s.lstrip(cls.DESC_PREFIX), orders))
        print('attrs(flat filter keys)  >> ', filter_and_order_attrs)

        # 2. 이제 각 filter name들에서 ___이 없으면 root cls인 model을 ''path 기준으로, 'rel_column_name. 다음' path에다가
        #    관계칼럼___이 붙어있으면 관계칼럼명 -> aliased 관계모델, 관계칼럼를 찾아서  관계모델부터 .으로 연결된 path을 key로 저장한다.
        #   순서대로 OrderedDict에 모은다. => 관계모델별.path에다가  기록할 저장소로서 재귀메서드를 만들어 호출한다.
        alias_map = OrderedDict({})
        # 시작을 들어온 model(cls)로 하고, depth마다 달라지는 model/path + 주어진 재료attrs/저장소alias를 인자로 준다.
        cls._parse_path_and_set_alias_map(model, '', filter_and_order_attrs, alias_map)

        print('alias_map  >> ', alias_map)

        # => OrderedDict([('tags', (<AliasedClass at 0x1de19e32908; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001DE19999150>))])
        # => 명시한 rel_column_name :  aliased관계모델, 해당 관계칼럼만  저장된다. ( 현재model의 칼럼은x)

        # print(alias_map) # posts___tags___id__in
        # OrderedDict([
        #   ('posts', (<AliasedClass at 0x1f209df5240; Post>, <sqlalchemy.orm.attributes.InstrumentedAttribute object at 0x000001F209958B48>)),
        #   ('posts___tags', (<AliasedClass at 0x1f209e71550; Tag>, <sqlalchemy.orm.attributes.InstrumentedAttrib
        # ute object at 0x000001F209E35AF0>))])

        #### selcet query 미리 만들어놓기 ####
        query = select(model)

        # 3. ___연결 path, rel model, rel column을 순회하면서
        # #### eager load query #### 달아주기  +  loaded_path 모아놓기
        #   => path는 flattend_schema와 동일한 형태인, {'user': JOINED, 'comments': SUBQUERY, 'comments.users': JOINED'}
        #      .으로 연결한 형태로 변형시킨다. schema의 key들은 관계속성명으로 연결됬었으니, 여기랑 같다?
        loaded_rel_paths = []
        for path, (aliased_rel_model, rel_column) in alias_map.items():
            rel_path = path.replace(cls.RELATION_SPLITTER, '.')
            # 3-2. schema를 인자로 받고 없으면 앞에서  flatten_schema에 빈 {} dict로 초기화해놓는다.
            # 3-3. schema=> flatten_schema를 통해 eagerload될 예정인 놈들을 제외하고, 여기서 expr를 만들어놓는다.
            #   => load()의 schema에서 SUBQUERY로 지정된 것이 아니라면, 전부 여기서 outerjoin(joined)로 연결되게 한다.

            # if not (rel_path in flatten_schema and flatten_schema[rel_path] in [SUBQUERY, SELECTIN]):
            # 3-4. #### 대박
            # outerjoin시 aliased와 함께, 관걔칼럼을 onclause로서 주는구나..
            # => contains_eager에는  [.으로 연결된 관계속성명] + 그때의 alias=에 aliased model을 지정해줄 수 있구나.
            # query = (
            #     query
            #     .outerjoin(aliased_rel_model, rel_column)
            #     .options(contains_eager(rel_path, alias=aliased_rel_model))
            # )

            #### custom 다대일에서 fk가 있을 경우, many<-one시 다박히는 경우 inner join으로
            # Post.tags.property.direction.name => 'MANYTOONE' 'ONETOMANY' 'MANYTOMANY'
            # => 메서드로 정의
            if not (rel_path in flatten_schema and flatten_schema[rel_path] in [cls.SUBQUERY, cls.SELECTIN]):
                # print('rel_column.property.direction.name>>' , rel_column.property.direction.name)
                # rel_column.property.direction.name >> MANYTOMANY
                query = (
                    query
                    .outerjoin(aliased_rel_model, rel_column)
                    .options(contains_eager(rel_path, alias=aliased_rel_model))
                )
                #### 필터를 만들기 위한, join 생성 중에 관계 방향이 ManyToOne일때만 innerjoin해보자.
                #### => inner join할 경우, main entity가 사라질 수 있으니, 필터링에 있는 경우를 제외하자.

                # relation_direction = rel_column.property.direction.name
                # # print('relation_direction  >> ', relation_direction)
                #
                # if relation_direction == 'MANYTOONE':
                #     query = (
                #         query
                #         .join(aliased_rel_model, rel_column)
                #         .options(contains_eager(rel_path, alias=aliased_rel_model))#, innerjoin=True)) # innerjoin옵션없음.
                #     )
                #     # print('query  >> ', query)
                #     # FROM employees
                #     # JOIN users AS users_1
                #     #     ON users_1.id = employees.user_id
                #
                # else:
                #     query = (
                #         query
                #         .outerjoin(aliased_rel_model, rel_column)
                #         .options(contains_eager(rel_path, alias=aliased_rel_model))
                #     )

                # 3-5. eager load가 완료된 rel_path들을 따로 모아둔다.
                loaded_rel_paths.append(rel_path)

        print(query, loaded_rel_paths)
        # query =>
        # SELECT posts.* tags_1.*
        # FROM posts
        # LEFT OUTER JOIN (posttags AS posttags_1 JOIN tags AS tags_1 ON tags_1.id = posttags_1.tag_id)
        #   ON posts.id = posttags_1.post_id
        # loaded_rel_paths => ['tags']

        # query 2 =>  2중 연결 Category posts___tags___id__in
        # SELECT categories.* posts_1.* tags_1.*
        # FROM categories
        # LEFT OUTER JOIN posts AS posts_1
        #   ON categories.id = posts_1.category_id
        # LEFT OUTER JOIN (posttags AS posttags_1
        #   JOIN tags AS tags_1 ON tags_1.id = posttags_1.tag_id)
        #       ON posts_1.id = posttags_1.post_id

        #### 4. alias_map(OrderedDict) 기반으로 재귀 filter query 만들기
        # -> 메서드를 재귀 yield로 제네레이터를 만들어도 *로 반출 가능하다.
        query = (
            query
            .where(*cls._create_filters_expr_with_alias_map(model, filters, alias_map))
        )
        # => query :
        # WHERE posts.id > :id_2 OR
        #           posts.id < :id_3 AND tags_1.name IN (__[POSTCOMPILE_name_1])
        # => *cls._create_filters_expr_with_alias_map(model, filters, alias_map):
        # posts.id > :id_1 OR (posts.id < :id_2 AND tags_1.name IN (__[POSTCOMPILE_name_1]))

        # => query2 : 'posts___tags___id__in': (1,2,3)
        # WHERE categories.id > :id_3 OR
        #   categories.id < :id_4 AND tags_1.id IN (__[POSTCOMPILE_id_5])

        #### 5. order by query 생략 ####
        query = (
            query
            .order_by(*cls._create_order_exprs_with_alias_map(model, orders, alias_map))
        )

        print('query  >> ', query)
        print('*cls._create_order_exprs_with_alias_map(model, orders, alias_map  >> ',
              *cls._create_order_exprs_with_alias_map(model, orders, alias_map))
        # => ORDER BY users_1.id DESC, employees.name ASC
        # => users_1.id DESC employees.name ASC

        #### 6. schema=None(___) -> flatten_schema={}(. : alias관계모델, 관계칼럼) + loaded_rel_paths(.)로
        #       filter에 등장한 관계 => outerjoin(joined)를 제외한
        #       필터에없는 joined + 나머지 subquery옵션들 체워주기
        #### => 필터를 만들면서 쓸거는 outerjoin으로, alias도 만어서 filter들도 만든다.
        #### => 하지만, subqueryload, selectinload는 객체를 추출한 뒤 .으로 사용할 예정이므로
        ####    제일 나중에 처리해줘도 상관없다.
        if flatten_schema:
            not_loaded_flatten_schema = {rel_path: value for rel_path, value in flatten_schema.items()
                                         if rel_path not in loaded_rel_paths
                                         }

            # print('not_loaded_flatten_schema  >> ', not_loaded_flatten_schema)
            # not_loaded_flatten_schema  >>  {'tags': 'subquery'}
            # For a one-to-many or many-to-many relationship, it's (usually) better to use subqueryload
            # instead, for performance reasons:
            # session.query(Product).join(User.addresses)\
            #     .options(subqueryload(Product.orders),\
            #              subqueryload(Product.tags)).all()
            # =>
            query = query \
                .options(*cls._create_eager_option_exprs_with_flatten_schema(not_loaded_flatten_schema))

        return query

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
            if key.lower().startswith(('and_', 'or_')):
                child_filters = and_(*cls.create_filters(model, value)) if key.lower().startswith('and_') \
                    else or_(*cls.create_filters(model, value))
                total_filters.append(child_filters)
                continue

            # CASE 2: dict순회시 'and_'나'or_'가 아니라서 => key='column__연산' / value = 값
            # => column__연산을 split하고, where 내을 list에 append한다.
            # => 어차피 재귀로 타고온 2번째라서, 부모에게 list를 건네, 부모에서 and_()나 or_()로 묶일 예정이다.
            #      이 때, 비교연산자를 안적는 경우, __eq로 간주하게 한다.
            split_attrs = cls.check_and_split_attr_names(key)  # # split결과 3개이상나오면 에러 1개, 2개는 넘어감

            if len(split_attrs) == 1:
                # split했기 때문에, [ 'username'] 으로 들어가있음. -> key[0]
                column = cls.create_column(model, split_attrs[0])
                # # 어차피 and or or로 시작하며, 아닌 턴에서는 list로만 append하면 부모가 and_()나 or_()로 싼다
                total_filters.append(column == value)

            elif len(split_attrs) == 2:
                column_name, op_name = split_attrs
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
    # for create_filter0
    # @classproperty
    @classmethod
    def get_hybrid_property_names(cls, model):
        items = inspect(model).all_orm_descriptors
        return [item.__name__ for item in items if isinstance(item, hybrid_property)]

    # for create_filter0
    @classmethod
    def get_hybrid_method_dict(cls, model):
        items = inspect(model).all_orm_descriptors
        return {item.func.__name__: item
                for item in items if type(item) == hybrid_method}

    # for create_filter0 - create_filter_exprs
    @classmethod
    def get_hybrid_method_names(cls, model):
        return list(cls.get_hybrid_method_dict(model).keys())

    # for create_order_bys
    # @classproperty
    @classmethod
    def get_sortable_columns(cls, model):
        return cls.get_column_names(model) + cls.get_hybrid_property_names(model)

    # for create_order_bys
    @classmethod
    def check_sortable_column_name(cls, model, attr):
        if attr not in cls.get_sortable_columns(model):
            raise KeyError(f'Invalid order by column: {attr}')

    @classmethod
    def create_order_bys(cls, attrs, model=None):
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

        if not attrs:
            return []

        if not isinstance(attrs, (list, tuple, set)):
            attrs = [attrs]

        order_by_columns = []

        for attr in attrs:
            #### column_name이 아니라, 칼럼(InstrumentedAttribute) or 증감칼럼(UnaryExpression)으로 들어올 경우
            # => 바로 append시킨다.
            # >>> type(User.id)
            # <class 'sqlalchemy.orm.attributes.InstrumentedAttribute'> <- 일반칼럼을 입력한 경우
            # >>> type(User.id.desc())
            # <class 'sqlalchemy.sql.elements.UnaryExpression'> <- ColumnElement
            # => 변경해줘야한다.
            if not isinstance(attr, str):
                if isinstance(attr, InstrumentedAttribute):
                    attr = attr.asc()
                    order_by_columns.append(attr)
                elif isinstance(attr, UnaryExpression):
                    order_by_columns.append(attr)
                else:
                    raise ValueError(f'잘못된 입력입니다 : {attrs}')
                continue

            # 지연으로 맥일 함수를 ()호출없이 가지고만 있는다.
            # -를 달고 있으면, 역순으로 맥인다.
            # order_func = desc if column_name.startswith(DESC_PREFIX) else asc

            #### 칼럼으로 순서 적용가능한지는 model.sortable_attributes안에 있는지로 확인한다.
            # -> -달고 있으면 때고 검사해야한다.
            # if column_name not in model.sortable_attributes:
            #     raise KeyError(f'Invalid order column: {column_name}')
            #### 2개를 한번에 처리(order_func + '-'달고 있으면 떼기)
            order_func, attr = (desc, attr[1:]) if attr.startswith(cls.DESC_PREFIX) \
                else (asc, attr)

            #### 추가 column_name에 id__count 등 집계함수가 있을 수 있다. => 검사는 순수 칼럼네임만 받아야한다.
            if cls.OPERATOR_OR_AGG_SPLITTER in attr:
                column_name_for_check, func_name = attr.split(cls.OPERATOR_OR_AGG_SPLITTER)
                cls.check_sortable_column_name(model, column_name_for_check)
            else:
                cls.check_sortable_column_name(model, attr)

            # column을 만들고, desc()나 asc()를 지연으로 맥인다.
            order_by_column = order_func(cls.create_column(model, attr))

            order_by_columns.append(order_by_column)

        return order_by_columns

    # for create_eager_options
    #### 추가) join과 유사한 eagerload를  위한 statement
    @classmethod
    def create_eager_exprs(cls, schema=None):
        """
        BaseQuery.create_eager_options({'user' : 'joined', 'comments': ('subquery', {'users': 'joined'})})
        => flatten_schema:  => {'user': JOINED, 'comments': SUBQUERY, 'comments.users': JOINED'}
        => to_eager_options => [<sqlalchemy.orm.strategy_options._UnboundLoad object at 0x000002820F626D30>, <sqlalchemy.orm.strategy_options._UnboundLoad object at 0x000002820F626DD8>, <sqlalchemy.orm.strategy_options._UnboundLoad object at 0x000002820F626EB8>]

        """
        if not schema:
            return []

        flatten_schema = cls._flat_schema(schema)
        return cls._create_eager_option_exprs_with_flatten_schema(flatten_schema)

    #  for raw_join in relation
    @classmethod
    def set_join_stmt(cls, stmt, target, **kwargs):
        # raw_join이라면 이미 칼럼은 text('alias.칼럼명')로 이미 작성된 상태이다.
        #

        return stmt.select_from(join(aliased(cls, name='left_table'), aliased(target, name='right_table'), **kwargs))

    @classmethod
    def create_select_statement(cls, model,
                                eager_options=None,
                                selects=None,
                                filters=None,
                                order_bys=None,
                                is_expr=None,
                                join_target=None,
                                join_options=None,
                                join_left_alias_name='left_table',
                                l_selects=None,
                                join_right_alias_name='right_table',
                                r_selects=None
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
        #### raw_join 발동시 빈칼럼을 '*'로 만들고, query를 only exrpression으로 바뀌게 한다.
        # => 이게 들어가는 순간..Query has only expression-based entities, which do not apply to relationship property "EmployeeDepartment.department"
        # => 미리 칼럼이 string  + create_column으로  만들어져서 온다.
        if is_expr:
            if not (
                    l_selects or r_selects):  # or (selects and isinstance(join_target, (AliasedClass, Alias, Subquery))):
                # join에서 칼럼 선택상황이라면 일단 select_columns를 '*'로 채워두고 뒤에서 고를 것이다.
                select_columns = [text('*')]
            else:
                select_columns = cls.create_columns(join_left_alias_name, column_names=l_selects) + \
                                 cls.create_columns(join_right_alias_name, column_names=r_selects)
        else:
            if not selects:
                select_columns = [model]
            else:
                select_columns = cls.create_columns(model, column_names=selects)

        stmt = (
            select(*select_columns)
            .options(*cls.create_eager_exprs(schema=eager_options))
        )

        # 첫 객체 생성이 raw_join이었을 경우, 중간에 삽입한다.
        # => 근데, 칼럼이 선택 안된 경우(=right target table이 alias안붙은 상태)만.. 중간에 삽입한다.
        #### 만약 칼럼들이 선택되서, target이 aliased로 들어온다면 => 같은명의 칼럼 모호함 없이기 위해 select_from으로 문장을 만들어줘야한다.
        if join_target is not None:  # and not isinstance(join_target, (AliasedClass, Alias, Subquery)):
            # => d
            stmt = cls.set_join_stmt(stmt, join_target, **join_options)

        stmt = (
            stmt
            .where(*cls.create_filters(model, filters=filters))
            #### order_by는 Mixin에서 self메서드로 사용되므로, cls용 model은 키워드로 바꿈 => 사용시 인자 위치도 바뀜.
            .order_by(*cls.create_order_bys(order_bys, model=model))
        )

        # if join_target is not None and isinstance(join_target, (AliasedClass, Alias, Subquery)):
        #     print('asasdfasdlaisd')
        #     stmt = (
        #         select(select_columns)
        #         .select_from(
        #             join(stmt.alias(name='left_table'), join_target, **join_options)
        #         )
        #     )

        print('create_select_stmt  >> \n', stmt)

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

    # for create_eager_options
    # for SmartMixin
    @classmethod
    def _flat_schema(cls, schema: dict):
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
        if not schema:
            return {}

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
                    eager_type, inner_schema = cls.JOINED, value

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
    @classmethod
    def _create_eager_option_exprs_with_flatten_schema(cls, flatten_schema):
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
