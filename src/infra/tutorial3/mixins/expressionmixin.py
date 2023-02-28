from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.infra.tutorial3.mixins.crudmixin import CRUDMixin


# selects를 포함시켜 expression_based로 만들고 execute() or scalar로 수행하자.
# => 첫 호출 session인자에 + 실행까지 포함하여 filter_by 옵션까지 받는다.
# => 결과물이 scalar의 1개면, => 여러개가 안나오므로, order_by와 limit 옵션은 X
class ExpressionMixin(CRUDMixin):
    __abstract__ = True

    ################
    # count_until  #  for count_and_rate_between
    ################
    @classmethod
    def count_until(cls, date_attr, end_date, count_attr=None,
                    session: Session = None, filter_by=None
                    ):
        """
        1. 칼럼을 지정하지 않는 경우, 첫번째 자동검색 pk 칼럼을 count (not distinct)
        Category.count_until('add_date', today).scalar()
        # 6
        Category.count_until('add_date', today, filter_by=dict(id__lt=3))
        # 2 (#1,  #2)

        2. 칼럼을 지정해서 카운팅( attr명에 집계함수 count를 작성하지 않으면, count를 집게)
           => distinct가 아니라면, id든, uk든, 일반칼럼이든 [똑같이 중복허용해서 센다는 소리]
        Category.count_until('add_date', today, count_attr='icon').scalar()
         # 5 (112, 112, 3, 3, 3)

        3. distinct를 붙이고 싶다면, 직접 count_attr='not pk or uk칼럼__count_distinct'
           => [distinct + not id/uk칼럼]이라면, [중복을 제외하고 센다]는 소리 (id/uk는 distinct해도 중복안나옴)
        Category.count_until('add_date', today, count_attr='icon__count_distinct').scalar()
        # 2 (112, 3)

        """
        # 1) count_attr이  주어지지 않으면, pk칼럼 + __count 로 column expr를 만든다.
        if not count_attr:
            count_column_expr = cls.create_column_expr(cls, cls.first_primary_key_name + '__' + 'count', cls.SELECT)
        else:
            if cls.COUNT not in count_attr:
                count_attr += cls.OPERATOR_OR_AGG_SPLITTER + cls.COUNT
            count_column_expr = cls.create_column_expr(cls, count_attr, cls.SELECT)

        srt_date_column = cls.create_column_expr(cls, date_attr, cls.FILTER_BY)

        query = (
            select(count_column_expr)
            .select_from(cls)  # 필수
            .where(func.date(srt_date_column) <= end_date)
        )

        # query=나 select는 expression_based =True를 만들어, execute()로 수행 + outerjoin만 수행 + 전체조회시 .unique()할 필요없음.
        obj = cls.create_obj(session=session, query=query, filter_by=filter_by)

        return obj.scalar()

    # ################
    # # count_until  #
    # ################
    @classmethod
    def count_and_rate_between(cls, date_attr, from_date, to_date, count_attr=None,
                               session: Session = None, filter_by=None
                               ):
        """
        Count_until 처음                ~            ToDate
        Count_until 처음 ~ FromDate [       between       ] => fromdate를 제외하여 count/rate를 계산한다.
        from_date + 1 ~ to_date 이므로, 지난 7일을 보려면, from_date를  -7day로 줘서, from_date+1 ~ to_date를 7일로 계산되게 한다


        1. 지난 3일간의 count와 rate
        Category.count_and_rate_between('add_date', today-relativedelta(days=3), today)
        => (5, 500.0)

           지난 3일간, id가 10보다 작은 것들의 count와 rate
        Category.count_and_rate_between('add_date', today-relativedelta(days=3), today, filter_by=dict(id__lt=10))
        => (3, 300.0)

        2. 지난 2개월 간의 count와 증감률 filter -> 'name'이 1233인 것 제외하고
        Category.count_and_rate_between('add_date',today-relativedelta(months=2), today, filters=dict(name__ne='1233'))
        => (6, 600)
        """
        to_count = cls.count_until(date_attr, to_date, count_attr=count_attr,
                                   session=session,
                                   filter_by=filter_by
                                   )

        from_count = cls.count_until(date_attr, from_date, count_attr=count_attr,
                                     session=session,
                                     filter_by=filter_by
                                     )

        between_count = to_count - from_count

        if from_count == 0:
            between_rate = round(to_count * 100, 2)
        else:
            between_rate = round(between_count / from_count * 100, 2)

        return between_count, between_rate
