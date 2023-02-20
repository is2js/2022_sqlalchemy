from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .crud_mixin import CRUDMixin
from ...utils import class_property


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
    # cls.실행메서드 #
    ################
    @classmethod
    def count_until(cls, srt_date_column_name, end_date, session: Session = None, filters=None, count_column_name=None,
                    is_distinct=False):
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
            .where(func.date(srt_date_column <= end_date))
            .where(*cls.create_filters(cls, filters=filters))
        )

        query_obj = cls.create_query_obj(session, query)

        return query_obj.scalar()

