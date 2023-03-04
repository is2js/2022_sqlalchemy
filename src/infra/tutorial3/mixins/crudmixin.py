# ObjectMixin(BaseQuery) 이후로는 세팅된 Base를 사용하여, BaseModel이 Base대신 이것을 상속한다.
from __future__ import annotations

import math
import typing

from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint, exists, MetaData, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, RelationshipProperty

from src.infra.tutorial3.mixins.objectmixin import ObjectMixin
from src.infra.tutorial3.mixins.utils.classorinstancemethod import class_or_instancemethod
from src.infra.tutorial3.mixins.utils.classproperty import class_property

constraints_map = {
    'pk': PrimaryKeyConstraint,
    'fk': ForeignKeyConstraint,
    'unique': UniqueConstraint,
}

Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class CRUDMixin(Base, ObjectMixin):
    __abstract__ = True

    ############
    # Create   #
    ############
    @classmethod
    def create(cls, session: Session = None, auto_commit: bool = True, **kwargs):
        """
        Category.create(name='123')
        """
        # obj = cls.create_obj(session=session, **kwargs)
        obj = cls.create_obj(session=session)
        obj.fill(**kwargs)  # 검증을 위해 fill을 사용한다.

        # 1. 만들어진 [미등록 obj]내 unique=True인 칼럼의 값을 가져와, 존재하는지 검사한다.
        # if obj.exists_self():
        #     return False, 'create fail'

        return obj.save(auto_commit=auto_commit), 'create success'

    # for create + ## 실행메서드 ##
    def exists_self(self):
        """
        등록 obj 존재검사(X), 등록 전, create()전 [미등록 obj의 unique 칼럼]을 바탕으로 db 존재 검사.
        =>  SELECT EXISTS (SELECT *
            FROM users
            WHERE users.username IS NULL) AS anon_1
        """
        # 미등록 obj에서 unique를 확인 후, 해당 값으로, 기등록 데이터가 있는지 확인함.
        unique_column_value = getattr(self, self.first_unique_key_name)
        if not unique_column_value:
            raise Exception(f'unique column 값을 입력하지 않았습니다.')

        filter_exprs = self.create_conditional_exprs(self.__class__,
                                                     {self.first_unique_key_name: unique_column_value})
        # 자신의 내부 쿼리는 바꾸지 않고, 일시적으로 쿼리 -> 실행까지
        stmt = self._query \
            .where(*filter_exprs)

        return self._session.scalar(exists(stmt).select())

    # for exists_self
    @classmethod
    def get_constraint_attr_names(cls, target='pk'):
        """
        User.get_constraint_attr_names(target='unique')
        ['username']
        User.get_constraint_attr_names(target='pk')
        ['id']
        User.get_constraint_attr_names(target='fk')
        ['role_id']
        """
        # 제약조건 관련은 .__table__.constrains에서만 꺼낼 수 있어서 inpsect (X)
        if isinstance(target, str) and target.lower() not in constraints_map.keys():
            raise NotImplementedError(f'해당 {target} 제약조건의 칼럼명 목록 조회는 구현되지 않았습니다.')

        #### 가짜 Base 상속해야 inspect / cls.__table__ 모두가능  +  inspect는 constrainst 정보 없음. BUT inpsect(self)도 가능.
        constraints = cls.__table__.constraints
        target_constraint_class = constraints_map.get(target)
        target_constraint = next((c for c in constraints if isinstance(c, target_constraint_class)), None)

        # 해당 제약조건의 칼럼이 없으면, 그냥 빈 리스트 반환
        if not target_constraint:
            return []

        return target_constraint.columns.keys()

    # for exists_self
    @class_property
    def unique_key_names(cls):
        return cls.get_constraint_attr_names(target='unique')

    # for exists_self
    @property
    def first_unique_key_name(self):
        """
        User.first_unique_key_name
        """
        self_unique_key = next(
            (column_name for column_name in self.column_names if column_name in self.unique_key_names), None)
        if not self_unique_key:
            raise Exception(f'Create 전, 존재 유무 확인을 위한 unique key를 입력하지 않았습니다.')

        return self_unique_key

    @class_property
    def foreign_key_names(cls):
        return cls.get_constraint_attr_names(target='fk')

    # for create + for update  ## 실행메서드 ##
    def save(self, auto_commit: bool = True):
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

    #################
    # Read -load    #
    #################
    @class_or_instancemethod
    def load(cls, schema: dict, session: Session = None):
        """
        filter_by /order_by/ havaing의 attrs로 입력하지 않고 바로 eagerload를 수행하도록 schema를 입력함.
        - dict형식으로 입력하되, 하위entity는 ('상위entity-load type', { '하위entity': '하위entity load type'} )로 value에 tuple을 활용
        - tuple 생략시 joined로 load됨.
        - 내부에서 ._flatten_schema로 등록되어, 실행메서드 호출시, 확인 후 모두 eagerload함.

        EmployeeDepartment.load({'employee':'selectin'})
        => obj._flatten_schema  >>  {'employee': 'selectin'}
        EmployeeDepartment.load({'employee':('selectin', {'department': 'joined'})})
        => obj._flatten_schema  >>  {'employee': 'selectin', 'employee.department': 'joined'}
        """
        obj = cls.create_obj(session=session, schema=schema)

        return obj

    @load.instancemethod
    def load(self, schema):
        """
        EmployeeDepartment.filter_by().load({'employee':'selectin'})
        => self._flatten_schema  >>  {'employee': 'selectin'}
        """
        # eagerload는 filter/order이후 실행메서드에서 처리되므로, schema만 올려주면 된다.
        self.set_schema(schema)

        return self

    ###################
    # Read - filter_by#
    ###################
    @class_or_instancemethod
    def filter_by(cls, session: Session = None, **kwargs):
        """
        1. and/or는 and_, or_를 key로하는 dict로 연결해서 사용한다.
        2. '럼__연산자=값에서 연산자를 생략하면, eq로 취급한다.
        3. '관계칼럼명___칼럼__연산=값' 형식으로 입력시, 내부에서 outerjoin + contains_eager이 수행되어,
           select(cls)된 main entity에 접근할 수 있다. (단, group_by등 selects=칼럼을 지정하는 경우, execute용으로 전환되어, outerjoin만 수행)

        EmployeeDepartment.filter_by(or_=dict(id=1, employee___id__ne=None)).all()
        """
        obj = cls.create_obj(session=session, filter_by=kwargs)

        return obj

    @filter_by.instancemethod
    def filter_by(self, **kwargs):
        """
        1. 딱히 사용될 일이 없을 것 같으나, load(schema=) 이후 연계할 수 있다.
        2. group_by이후의 관계칼럼의 filter_by는  contains_eager없이 outerjoin만 된다.

        ed = EmployeeDepartment.load({'department':'selectin'}).filter_by(position='상위부서장').first()
        ed.department
        => Department(id=1, name='상위부서', parent_id=None, sort=1, path='001')
        """
        self.set_attrs(filter_by=kwargs)

        return self

    @class_or_instancemethod
    def order_by(cls, *args, session: Session = None):
        """
        Category.order_by("-id").all()
        EmployeeDepartment.order_by("-department___id").all()
        """
        obj = cls.create_obj(session=session, order_by=args)

        return obj

    @order_by.instancemethod
    def order_by(self, *args):
        """
        Category.filter_by(id__lt=5).order_by("-id").all()
        """
        self.set_attrs(order_by=args)

        return self

    @class_or_instancemethod
    def limit(cls, limit, session: Session = None):
        """
        Category.limit(2).all()
        """
        obj = cls.create_obj(session=session)
        obj.set_query(limit=limit)

        return obj

    @limit.instancemethod
    def limit(self, limit):
        """
        Category.filter_by(id__ne=None).limit(2).all()
        """
        self.set_query(limit=limit)

        return self

    # offset은 limit없이 전체 데이터를 스캔하므로 성능 문제가 발생할 수 있다.
    @class_or_instancemethod
    def offset(cls, offset, session: Session = None):
        """
        Category.offset(2).all()
        """
        obj = cls.create_obj(session=session)
        obj.set_query(offset=offset)

        return obj

    @offset.instancemethod
    def offset(self, offset):
        """
        Category.filter_by(id__ne=None).offset(2).all()
        Category.limit(10).offset(2).all()
        # offset은 limit과 함께 사용한다. 그렇지 않으면 전체데이터 베이스 스캔 성능 저하 우려.
        """
        self.set_query(offset=offset)

        return self

    ###################
    # Read - get      #
    ###################
    @classmethod
    def get(cls, *args, session: Session = None, **kwargs):
        """
        1. id(pk)로  1개만 검색하는 경우 => sessioin.get(cls, id)로 찾음.
            User.get(1)

        2. id(pk)   2개이상입력시 filter_by(where) +  in      .all() 으로 찾음.
            User.get(1, 2) => WHERE users.id IN (__[POSTCOMPILE_id_1]) => [<User>, <.User object at 0x000002BE16C02FD0>]

        3. kwargs(unique key or pk) key1개, values list 가능 우 -> filter_by(where)로 1개 .first() / 여러개 .all()
            User.get(username='admin')
            Category.get(name=['123', '12345'])
        """
        # 둘중에 1개는 반드시 들어와야한다
        if not (args or kwargs) or (args and kwargs):
            raise KeyError(f'id를 입력하거나 키워드 형식으로 unique칼럼을 지정하되 방법은 1가지만 선택해주세요.')

        if not all(attr in cls.primary_key_names + cls.unique_key_names for attr in kwargs.keys()):
            raise KeyError(f'키워드로 검색시, id(pk) 혹은 unique Column으로 검색해주세요.')

        # 1) args(pk)로 검색하는 경우
        if args and not kwargs:
            if not any(type(id_) == int for id_ in args):
                raise KeyError(f'id(pk)를 정수로 입력해주세요.')

            pk_for_search = cls.first_primary_key_name

            if len(args) == 1:
                # obj = cls.create_obj(session=session, filter_by={pk_for_search: args[0]})
                #### id 1개만 입력할 경우, session.get()으로 찾도록 변경
                obj = cls.create_obj(session=session)
                result = obj._session.get(cls, args)
                obj.close()
                # print('obj._query in one >> ', obj._query)
                return result

            else:
                obj = cls.create_obj(session=session, filter_by={f'{pk_for_search}__in': args})
                results = obj.all()
                # 조회된 갯수가 다르면 못찾은 것을 찾아 에러를 방출한다.
                if len(results) != len(args):
                    not_searched_pks = sorted(set(args) - set([getattr(obj, pk_for_search) for obj in results]))
                    raise KeyError(f'Invalid Primary Key(s): {not_searched_pks}')

                # print('obj._query in many >> ', obj._query)
                return results

        # 2) kwargs(unique 칼럼)으로 검색하는 경우
        # if kwargs and not args:
        else:
            # kwargs검색은 오직 keyword9(uk) 1개만 허용
            if len(kwargs.keys()) != 1:
                raise KeyError(f'Only one keyword(pk or unique key) value allowed. {[*kwargs.keys()]}')

            col_name, values = [*kwargs.items()][0]  # (key, '123') or (key, ['123', '456'])
            if not isinstance(values, (list, tuple, set)):
                values = [values]

            if len(values) == 1:
                obj = cls.create_obj(session=session, filter_by={col_name: values[0]})
                return obj.first()

            else:
                obj = cls.create_obj(session=session, filter_by={f'{col_name}__in': values})
                results = obj.all()
                # 조회된 갯수가 다르면 못찾은 것을 찾아 에러를 방출한다.
                if len(results) != len(values):
                    not_searched_values = sorted(set(values) - set([getattr(obj, col_name) for obj in results]))
                    raise KeyError(f'Can\'t search pk or unique key({col_name}) value: {not_searched_values}')
                # print('obj._query in many >> ', obj._query)
                return results

    # for get
    @class_property
    def primary_key_names(cls):
        return cls.get_constraint_attr_names(target='pk')

    @class_property
    def first_primary_key_name(cls):
        """
        User.first_primary_key_name
        """
        self_primary_key = next(
            (column_name for column_name in cls.column_names if column_name in cls.primary_key_names), None)
        if not self_primary_key:
            raise Exception(f'primary key가 존재하지 않습니다.')

        return self_primary_key

    #####################
    # Group By + Having #
    #####################
    @classmethod
    def group_by(cls, *group_by_column_names, session: Session = None, selects=None):
        """
        1. 자체 집계
        Category.group_by('icon', selects=['name', 'id__count']).execute()
        => [('ccc', 4), ('337', 2)]

        2. a별 b의 집계 -> a의 id로 group_by하고, b를 집계
        Tag.group_by('id', selects=['name', 'posts___id__count', 'posts___has_type__sum'])
           .order_by('-posts___id__count').execute()
        => [('태그1', 1, <PostPublishType.SHOW: 2>), ('asdf', 0, <PostPublishType.NONE: 0>)]
        => 결과 Row객체는 .keys()로 접근 필드를 확인할 수 있다.
        result.keys() => RMKeyView(['name', 'id_count', 'has_type_sum'])

        """
        obj = cls.create_obj(session=session, selects=selects)

        # if select:
        #     # obj.process_selects_eager_exprs(select)
        #     obj.process_non_conditional_attrs(selects=select)
        #### relationship -> contains_eager로 사용하려면, 무조건 main model(cls) select에 들어가야
        # => Query has only expression-based entities - can't find property named "employee".가 안뜬다.
        # select_columns = cls.create_columns(cls, column_names=select, in_selects=True) # 집계가 in_select시 coalesce
        # select_columns = [cls] + select_columns
        #### => select에 cls외 다른 것을 올리고 싶다면, execute용으로 전환되며, select_from(cls)를 주고
        ####    outerjoin을 자동으로 하되, contains_eager이 빠져야한다.

        group_by_column_exprs = cls.create_column_exprs_with_alias_map(cls, group_by_column_names, obj._alias_map,
                                                                       cls.GROUP_BY)
        obj.set_query(group_by=group_by_column_exprs)

        return obj

    def having(self, **kwargs):
        """
        Category.group_by('icon', selects=['id', 'icon__sum']).having(icon__sum__lt=24).execute()
        =>
        SELECT categories.id, coalesce(sum(categories.icon), ?) AS icon_sum
        FROM categories GROUP BY categories.icon
        HAVING sum(categories.icon) < ?
        """
        self.set_attrs(having=kwargs)

        return self

    ###################
    # Paginate        #
    ###################
    @class_or_instancemethod
    def paginate(cls, page, per_page=10, session: Session = None):
        """
        p = Category.paginate(page=1, per_page=3)
        p.total, p.page, list(p.iter_pages()), p.page, p.has_next, p.next_num, p.has_prev, p.prev_num, p.items
        => (7, 1, [1, 2, 3], 1, True, 2, False, None, [<Category#2 '337'>, <Category#6 'aaa'>, <Category#8 'ccc'>])

        """
        if page <= 0:
            raise AttributeError('page needs to be >= 1')
        if per_page <= 0:
            raise AttributeError('per_page needs to be >= 1')
        obj = cls.create_obj(session=session)

        total = obj._session.scalar(
            obj.create_count_query()
        )

        obj.set_query(limit=per_page)
        obj.set_query(offset=(page - 1) * per_page)
        items = obj.all()

        return Pagination(items, total, page, per_page)

    @paginate.instancemethod
    def paginate(self, page, per_page=10):
        """
        p = Category.filter_by().paginate(page=1, per_page=10)
        p.total: 7 => 페이지네이션 무관, 전체 아이템 갯수
        p.pages: 3 => 페이지네이션 전체 페이지 수

        p.iter_pages() + list() :[1, 2, 3] => 템플릿 for 순회하며 찍을 Iterrator
        p.page: 1 => 선택한 페이지
            -> for page in iter_pages()의 각각의 page들와
            -> 선택한 페이지 p.page를 != 로 비교하여, 현제페이지 VS 주위페이지를 비교한다

        p.has_next -> p.next_num : 다음페이지를 가지면, 다음 페이지 번호로 링크를 건다.
        p.has_prev -> p.prev_num : 이전 페이지 번호를 가지면, 이전 페이지번호로 링크를 건다.

        p.items -> 현재페이지의 객체 list

        :param page: 선택한 페이지
        :param per_page: 페이지당 갯수
        :return: Paginate객체
        """
        if page <= 0:
            raise AttributeError('page needs to be >= 1')
        if per_page <= 0:
            raise AttributeError('per_page needs to be >= 1')

        total = self._session.scalar(
            self.create_count_query()
        )

        self.set_query(limit=per_page)
        self.set_query(offset=(page - 1) * per_page)
        items = self.all()

        return Pagination(items, total, page, per_page)

    ###################
    # Update -        # -> only self method => create_obj없이 model_obj에서 [최초호출].init_obj()로 초기화
    ###################
    def update(self, session: Session = None, auto_commit: bool = True, **kwargs):
        """
        c = Category.get(1) # c.name '카테고리1'
        c.update(name='카테고리1') # (False, '값의 변화가 없어서 업데이트 실패)
        c.update(name='카테고리111') # (<Category>, '업데이트 성공')

        ***업데이트후 조회 등을 하려면 반드시 auto_commit=False
        c2 = Category.get(2, session=s)
        c2.update(name='122333b', session=s, auto_commit=False) => auto_commit=True로 커밋되면 뒤에서 확인못한다.
        c2.to_dict(session=s)
        s.commit()
        ----
        return self, '업데이트 성공'
        False, '업데이트 실패'
        """
        # create: cls(**kwargs).init_obj()
        try:
            is_updated = self.fill(**kwargs)

            if is_updated:
                updated_obj = self.init_obj(session=session).save(auto_commit=auto_commit)

                # model_obj를 직접 변환시, 재호출을 위해 초기화 취소 -> 재호출해도 다 다시 초기화되며,  session 등을 지우면, 외부session이 날아가버리는 부작용으로 취소
                # self.close_model_obj()
                # print('updated_obj.name  >> ', updated_obj.name)

                return updated_obj, '업데이트 성공'
            else:
                # self.close_model_obj()
                return False, '값의 변화가 없어서 업데이트 실패'

        except Exception as e:
            print(e)
            # self.close_model_obj()
            return False, '알수 없는 이유로 업데이트 실패'

    ###################
    # Delete          # -> only self method => create_obj없이 model_obj에서 [최초호출].init_obj()로 초기화
    ###################
    def delete(self, session: Session = None, auto_commit: bool = True):
        """
        c1 = Category.first()
        c1.delete()
        """
        self.init_obj(session=session)

        try:
            self._session.delete(self)
            self._session.flush()

            if auto_commit:
                self._session.commit()

            # self.close_model_obj()
            return self, '삭제 성공'

        except:
            # self.close_model_obj()
            return False, '삭제 실패'

    ###################
    # Delete By        # -> cls method => .get()으로 1개 or 여러개 검색 => 1개든 여러개든 순회하며 삭제
    ###################                   .get() 검색시 실패하면 에러검증 + 순회 delete시 1개라도 실패하면 에러 발생
    @classmethod
    def delete_by(cls, *args, session: Session = None, auto_commit=True, **kwargs):
        """
        1. Category.delete_by(1, 2, 3)
            Category.delete_by(1, 1000) => KeyError: 'Invalid Primary Key(s): [1000]'
            Category.delete_by(3, 4) => fk걸린 것이면 에러날 수도 있다.

        2. Category.delete_by(name=['aaa','bbb'])

        """
        if not (args or kwargs) or (args and kwargs):
            raise KeyError(f'id를 입력하거나 키워드 형식으로 unique칼럼을 지정하되 방법은 1가지만 선택해주세요.')

        if not all(attr in cls.primary_key_names + cls.unique_key_names for attr in kwargs.keys()):
            raise KeyError(f'삭제 시 검색시, id(pk) 혹은 키워드로 unique Column을 입력해주세요.')

        # 한개든 여러개든 순회하며 1개의 session으로 처리한다. -> 외부session으로 취급하고 auto_commit=False로 delete
        # => 1개의 세션을 유지하려면, obj를 만들어야아한다. 바로 get으로 부르면 결과물만 나옴
        obj_for_delete = cls.create_obj(session=session)

        # 1) args(pk)로 삭제하는 경우 -> get()으로 검색시 args로 검색해서 가져온다.
        if args and not kwargs:
            objs = cls.get(*args, session=obj_for_delete._session)  # args(pk)검색시 발견안되면 내부에서 에러난다.
        # 2) kwargs(pk or unique key)로 삭제하는 경우 -> get()으로 검색시 kwrags로 검색해서 가져온다.
        else:
            objs = cls.get(session=obj_for_delete._session, **kwargs)  # kwarg는 1개만 검색하며, 발견안되면 내부 에러

        # get으로 1개 또는 list 가 나올 수 있어서 list로 변환
        if not isinstance(objs, (list, tuple, set)):
            objs = [objs]

        delete_fails = []
        # args(id, pk)로 검색시와   kwargs(pk or unique key)로 검색시 column_name이 각각 다르다.
        col_name = cls.first_primary_key_name if args else [*kwargs.keys()][0]

        for obj in objs:
            result, _msg = obj.delete(session=obj_for_delete._session, auto_commit=False)
            if not result:
                delete_fails.append(getattr(obj, col_name))

        if delete_fails:
            # 1개라도 삭제 실패시, 내부session이면 rollback하자. 외부session이면 False return으로 알아서 처리할 듯.
            if not obj_for_delete.served:
                obj_for_delete._session.rollback()
            return False, f'Delete Fails : {sorted(delete_fails)}'

        # 모두 삭제 성공시, 내부든 외부든 auto_commit True라면, 해당 session을 커밋하면 된다.
        # => 외부라도 obj_for_delete 에 session으로 들어가있다.
        if auto_commit:
            obj_for_delete._session.commit()

        return True, 'All deleted.'


# for  paginate
class Pagination:
    # https://parksrazor.tistory.com/457
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.page = page
        self.total = total

        # 이전 페이지를 가지고 있으려면, 현재page - 1 = 직전페이지 계산결과가, 실존 해야하는데, 그게 1보다 크거나 같으면 된다.
        #  0 [ 1 2 page ]
        self.has_prev = page - 1 >= 1
        # 이전 페이지 존재유무에 따라서 이전페이지 넘버를 현재page -1 or None 로 만든다.
        self.prev_num = (self.has_prev and page - 1) or None

        # 다음 페이지를 가지고 있으려면, 갯수로 접근해야한다.
        # (1) offset할 직전페이지까지의 갯수: (현재page - 1)*(per_page)
        # (2) 현재페이지의 갯수: len(items) => per_page를 못채워서 더 적을 수도 있다.
        # (3) total갯수보다 현재페이지까지의 갯수가 1개라도 더 적어야, 다음페이지로 넘어간다
        self.has_next = ((page - 1) * per_page + len(items)) < total
        # 다음페이지를 갖고 있다면 + 1만 해주면된다.
        self.next_num = page + 1 if self.has_next else None

        # total pages 수는, per_page를 나눠서 math.ceil로 올리면 된다.
        # self.pages = math.ceil(total / per_page) + 1
        self.pages = math.ceil(total / per_page) if total else 0

        # https://github.com/pallets-eco/flask-sqlalchemy/blob/main/src/flask_sqlalchemy/pagination.py

    def iter_pages(self, *,
                   left_edge: int = 2,  # 1페 포함 보여질 갯수,
                   left_current: int = 2,  # 현재로부터 왼쪽에 보여질 갯수,
                   right_current: int = 4,  # 현재로부터 오른쪽에 보여질 갯수,
                   right_edge: int = 2,  # 마지막페이지 포함 보여질 갯수
                   ) -> typing.Iterator[int | None]:

        # 1) 전체 페이지갯수를 바탕으로 end특이점을 구해놓는다.
        pages_end = self.pages + 1
        # 2) end특이점 vs1페부터보여질 갯수+1을 비교해, 1페부터 끝까지의 특이점을 구해놓는다.
        left_end = min(left_edge + 1, pages_end)
        # 3) 1페부터 특이점까지를 1개씩 yield로 방출한다.
        yield from range(1, left_end)
        # 4) 만약 페이지끝 특이점과 1페끝 특이점이 같으면 방출을 마친다.
        if left_end == pages_end:
            return
        # 5) 선택한 page(7) - 왼쪽에 표시할 갯수(2) (보정x 현재로부터 윈도우만큼 떨어진 밖.== 현재 제외 윈도우 시작점) -> 5 [6 7]
        #    과 left끝특이점 중 max()를 mid시작으로 본다.
        #   + 선택한page(7) + 오른쪽표시갯수(4) == 11 == 현재포함윈도우밖 == 현재제외 윈도우의 끝점 vs 전체페이지끝특이점중 min을 mid_end로 보낟
        mid_start = max(left_end, self.page - left_current)
        mid_end = min(pages_end, self.page + right_current)
        # 6) mid 시작과 left끝특이점 비교하여 mid가 더 크면, 중간에 None을 개설한다
        if mid_start - left_end > 0:
            yield None
        # 7) mid의 시작~끝까지를 방출한다.
        yield from range(mid_start, mid_end)
        # 8) mid_end와  (페이지끝특이점 - 우측에서 보여질 갯수)를 비교하여 더 큰 것을 right 시작점으로 본다.
        right_start = max(mid_end, pages_end - right_edge)
        # 9) mid_end(특이점)과 right시작점이 차이가 나면 중간에  None을 개설한다.
        if right_start - mid_end > 0:
            yield None
        # 10) right_start부터, page_end까지 방출한다.
        yield from range(right_start, pages_end)
