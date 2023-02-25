from collections import OrderedDict, abc

from sqlalchemy import MetaData, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, contains_eager

from src.infra.tutorial3.mixins.object_mixin import ObjectMixin


class SmartMixin(ObjectMixin):
    __abstract__ = True

    @classmethod
    def smart_query(cls, session: Session = None, schema: dict = None, filters: dict = None, orders=None):
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
        => filter_and_order_attrs : ['id__gt', 'id__lt', 'tags___property__in'] + ['tags___name']
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
        #### flatten_schema ####
        # flatten_schema = cls._flat_schema(schema)  # if None -> {}
        # if not orders:
        #     orders = []
        # if orders and not isinstance(orders, (list, tuple, set)):
        #     orders = [orders]

        obj = cls.create_obj(session=session, schema=schema, query=None, filters=filters, orders=orders)
        print('obj._flatten_schema  >> ', obj._flatten_schema)

        # ['id__gt', 'id__lt', 'posts___tags___name__isnull']

        # filter_and_order_attrs = list(cls._flat_filter_keys_generator(filters)) + \
        #                          list(map(lambda s: s.lstrip(cls.DESC_PREFIX), orders))
        # #### alias_map ####
        # # {rel path: alias rel model(mapper), rel attr in main model}
        # # => ('posts', (<AliasedClass; Post>, <InstrumentedAttribute object>))
        # # => ('posts___tags', (<AliasedClass; Tag>, <InstrumentedAttribute object>))
        # alias_map = OrderedDict({})
        #
        # cls._parse_path_and_set_alias_map(parent_model=cls, parent_path='', attrs=filter_and_order_attrs,
        #                                   alias_map=alias_map)

        ######## select query ######
        # query = select(cls)

        # obj.process_filter_or_orders(filters=filters, orders=orders)
        print('obj._alias_map  >> ', obj._alias_map)

        ######## outer join + contains_eager query ######  <- joined in filters , orders relationship
        # loaded_rel_paths = []  # ['posts', 'posts.tags']
        # # for path, (aliased_rel_model, rel_attr) in alias_map.items():
        #
        # for path, (aliased_rel_model, rel_attr) in obj._alias_map.items():
        #
        #
        #     rel_path = path.replace(cls.RELATION_SPLITTER, '.')
        #
        #     print('rel_path  >> ', rel_path)
        #
        #
        #     # 3-2. schema를 인자로 받고 없으면 앞에서  flatten_schema에 빈 {} dict로 초기화해놓는다.
        #     # 3-3. schema=> flatten_schema를 통해 eagerload될 예정인 놈들을 제외하고, 여기서 expr를 만들어놓는다.
        #     #   => load()의 schema에서 SUBQUERY로 지정된 것이 아니라면, 전부 여기서 outerjoin(joined)로 연결되게 한다.
        #
        #     # if not (rel_path in flatten_schema and flatten_schema[rel_path] in [SUBQUERY, SELECTIN]):
        #     # 3-4. #### 대박
        #     # outerjoin시 aliased와 함께, 관걔칼럼을 onclause로서 주는구나..
        #     # => contains_eager에는  [.으로 연결된 관계속성명] + 그때의 alias=에 aliased model을 지정해줄 수 있구나.
        #     # query = (
        #     #     query
        #     #     .outerjoin(aliased_rel_model, rel_column)
        #     #     .options(contains_eager(rel_path, alias=aliased_rel_model))
        #     # )
        #
        #     #### custom 다대일에서 fk가 있을 경우, many<-one시 다박히는 경우 inner join으로
        #     # Post.tags.property.direction.name => 'MANYTOONE' 'ONETOMANY' 'MANYTOMANY'
        #     # => 메서드로 정의
        #     # if not (rel_path in flatten_schema and flatten_schema[rel_path] in [cls.SUBQUERY, cls.SELECTIN]):
        #
        #
        #
        #     if not (rel_path in obj._flatten_schema and obj._flatten_schema[rel_path] in [cls.SUBQUERY, cls.SELECTIN]):
        #
        #
        #         # print('rel_column.property.direction.name>>' , rel_column.property.direction.name)
        #         # rel_column.property.direction.name >> MANYTOMANY
        #         query = (
        #             query
        #             .outerjoin(aliased_rel_model, rel_attr)
        #             .options(contains_eager(rel_path, alias=aliased_rel_model))
        #
        #         )
        #         #### 필터를 만들기 위한, join 생성 중에 관계 방향이 ManyToOne일때만 innerjoin해보자.
        #         #### => inner join할 경우, main entity가 사라질 수 있으니, 필터링에 있는 경우를 제외하자.
        #
        #         # relation_direction = rel_column.property.direction.name
        #         # # print('relation_direction  >> ', relation_direction)
        #         #
        #         # if relation_direction == 'MANYTOONE':
        #         #     query = (
        #         #         query
        #         #         .join(aliased_rel_model, rel_column)
        #         #         .options(contains_eager(rel_path, alias=aliased_rel_model))#, innerjoin=True)) # innerjoin옵션없음.
        #         #     )
        #         #     # print('query  >> ', query)
        #         #     # FROM employees
        #         #     # JOIN users AS users_1
        #         #     #     ON users_1.id = employees.user_id
        #         #
        #         # else:
        #         #     query = (
        #         #         query
        #         #         .outerjoin(aliased_rel_model, rel_column)
        #         #         .options(contains_eager(rel_path, alias=aliased_rel_model))
        #         #     )
        #
        #         # 3-5. eager load가 완료된 rel_path들을 따로 모아둔다.
        #         loaded_rel_paths.append(rel_path)

        # print('loaded_rel_paths  >> ', loaded_rel_paths)
        print('obj._loaded_rel_paths  >> ', obj._loaded_rel_paths)

        ######## where query ######
        # query = (
        #     query
        #     # .where(*cls._create_filters_expr_with_alias_map(cls, filters, alias_map))
        #
        #
        #     .where(*cls._create_filters_expr_with_alias_map(cls, filters, obj._alias_map))
        #
        #
        # )

        ######## order_by query ######
        # query = (
        #     query
        #     # .order_by(*cls._create_order_exprs_with_alias_map(cls, orders, alias_map))
        #
        #
        #     .order_by(*cls._create_order_exprs_with_alias_map(cls, orders, obj._alias_map))
        #
        #
        # )

        ######## order_by query ######
        #### not_loaded_flatten_schema ####
        # if flatten_schema:
        # not_loaded_flatten_schema = {rel_path: value for rel_path, value in flatten_schema.items()

        # if obj._flatten_schema:
        #
        #
        #     not_loaded_flatten_schema = {rel_path: value for rel_path, value in obj._flatten_schema.items()
        #                                  if rel_path not in obj._loaded_rel_paths
        #                                  }
        #
        #     query = query \
        #         .options(*cls._create_eager_option_exprs_with_flatten_schema(not_loaded_flatten_schema))
        #
        #
        #     print('not_loaded_flatten_schema  >> ', not_loaded_flatten_schema)

        # obj.set_query(query)

        # print('obj.__dict__  >> ', obj.__dict__)
        print('obj._query  >> ', obj._query)

        return obj
