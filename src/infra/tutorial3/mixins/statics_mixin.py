from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.infra.tutorial3.mixins.utils.classproperty import class_property
from .crud_mixin import CRUDMixin


# 나중에는 self._query도 객체로 만들어서... : https://stackoverflow.com/questions/629551/how-to-query-as-group-by-in-django
# => query.group_by = ['designation'] 처럼 넣을 수 있게
# => 실행메서드들에서 최종 create_query 한 뒤 -> 실행하게..
# query = Members.objects.all().query
# query.group_by = ['designation']
# results = QuerySet(query=query, model=Members)

class StaticsMixin(CRUDMixin):
    __abstract__ = True

    #### Statics -> base
    # for create_pk_count_column
    @class_property
    def first_pk(cls):
        self_pk_key = next(iter(cls.pks), None)
        if not self_pk_key:
            raise Exception(f'pk칼럼이 없습니다.')

        return self_pk_key

    # for count_until
    @classmethod
    def create_pk_count_column(cls, is_distinct=False):
        # distinct는 _한줄로 추가
        count_column_name = f'{cls.first_pk}__count' + ('_distinct' if is_distinct else '')
        return cls.create_column(cls, count_column_name)

    # for count_until
    @classmethod
    def create_count_column(cls, count_column_name, is_distinct=False):
        if 'count' not in count_column_name:
            count_column_name += '__count'
        if is_distinct and 'distinct' not in count_column_name:
            count_column_name += '_distinct'
        return cls.create_column(cls, count_column_name)

    # 1) query가 필용한 메서드 -> @classmehotd + query + create_query_obj  like filter_by
    ################
    # cls.실행메서드 # => obj + query 생성 후 -> self.실행메서드까지
    ################
    @classmethod
    def count_until(cls, srt_date_column_name, end_date,
                    session: Session = None,
                    filters=None,
                    is_distinct=False,
                    count_column_name=None,
                    ):
        """
        Category.count_until('add_date', today)
        => 3
        Category.count_until('add_date', today, filters=dict(name__ne='1233'))
        => 2

        Category.count_until('add_date', today, count_column_name='name')
        Category.count_until('add_date', today, count_column_name='id')
        Category.count_until('add_date', today, count_column_name='id__count')
        Category.count_until('add_date', today, count_column_name='id__count_distinct')

        """
        # 1) count_column_name이 주어지지 않으면, pk칼럼으로 카운팅할 준비를 한다.
        if not count_column_name:
            count_column = cls.create_pk_count_column(is_distinct=is_distinct)
        else:
            count_column = cls.create_count_column(count_column_name, is_distinct=is_distinct)

        srt_date_column = cls.create_column(cls, srt_date_column_name)

        query = (
            select(count_column)
            .where(func.date(srt_date_column) <= end_date)
            .where(*cls.create_filters(cls, filters=filters))
        )

        query_obj = cls.create_query_obj(session, query)

        return query_obj.scalar()

    # use count_until
    ################
    # cls.실행메서드 # => obj + query 생성 후 -> self.실행메서드까지
    ################
    @classmethod
    def count_and_rate_between(cls, date_column_name, from_date, to_date,
                               session: Session = None,
                               filters=None,
                               is_distinct=False,
                               count_column_name=None,
                               ):
        """
        between으로 한번에 필터링 하지 않는 이유는, rate계산때 문이다.(to - from / from)의 from의 값을 알아야하기 때문
        => from_date는 포함안하고 계싼된다.
        from_date = 오늘 - (오늘을 포함한 보고싶은 지난 x일의) x

        from_date = (오늘 - 오늘로부터 3일전) = 지난 4일 전
        to_date   = 오늘
        => between 계산은  [from_date(4일전) + 1(3일전)] ~  to_date(오늘)을 하므로 => to_date를 포함한 지난 3일을 보게 된다.
        1 2 3 4 5 6 7 8
        ↓ [ 지난7주일  ]
        8 - relativedelta(days=7)

        1. 지난 3일간의 count와 증감률
        Category.count_and_rate_between('add_date',today-relativedelta(days=3), today)
        => (2, 100.0)

        2. 지난 2개월 간의 count와 증감률 filter -> 'name'이 1233인 것 제외하고
        Category.count_and_rate_between('add_date',today-relativedelta(months=2), today, filters=dict(name__ne='1233'))
        => (3, 300)

        """
        to_count = cls.count_until(date_column_name, to_date, session=session,
                                   filters=filters,
                                   is_distinct=is_distinct,
                                   count_column_name=count_column_name
                                   )

        from_count = cls.count_until(date_column_name, from_date, session=session,
                                     filters=filters,
                                     is_distinct=is_distinct,
                                     count_column_name=count_column_name
                                     )

        between_count = to_count - from_count

        if from_count == 0:
            between_rate = round(to_count * 100, 2)
        else:
            between_rate = round(between_count / from_count * 100, 2)

        return between_count, between_rate

    # use count_until
    #####################
    # cls.객체 생성 메서드 # => obj + query 생성 까지만 => 차후 실행메서드 like filter_by
    #####################
    # 객체 or 개별칼럼 -> all() or exceute 선택#
    #####################
    @classmethod
    def group_by(cls, *group_by_column_names, session: Session = None, selects=None, filters=None):
        """
        1. selects 칼럼을 안고른 경우 => model obj가 select 자동 => .all()

        User.group_by('username', session=None).all()
        => [User[id=1,username='admin',], User[id=2,username='asdf15251',], User[id=3,username='asdf15252',], User[id=4,username='asdf15253',]]

        2. selects로 개별칼럼들을 가져오는 경우 => .execute()
        User.group_by('id', selects=['username', 'id__count'], session=None).execute()
        => [('admin', 1), ('asdf15251', 1), ('asdf15252', 1), ('asdf15253', 1)]

        User.group_by('id', 'username', selects=['id', 'id__count', 'username__length'], session=None).order_by('-username__length').execute()
        => [(2, 1, 9), (3, 1, 9), (4, 1, 9), (1, 1, 5)]

        """
        # 1) groupby 칼럼들 만들기
        group_by_columns = cls.create_columns(cls, group_by_column_names)

        # 2) selects(집계칼럼)칼럼 만들기 => 없다면, None이 들어가서 자동으로 cls.create_column에서 모델이 올라간다.
        # if not selects:
        #     select_columns = [cls]
        if selects:
            if not isinstance(selects, (list, tuple, set)):
                selects = [selects]

        query = cls.create_select_statement(cls, filters=filters, selects=selects)

        query = query.group_by(*group_by_columns)

        return cls.create_query_obj(session, query)
