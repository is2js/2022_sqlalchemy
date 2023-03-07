import calendar
import enum
from collections import defaultdict
from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func, text, column
from sqlalchemy.orm import Session

from src.infra.tutorial3.mixins.crudmixin import CRUDMixin

SQLITE = 'sqlite'
MYSQL = 'mysql'
POSTGRESQL = 'postgresql'

interval_map = {
    'day': lambda x: relativedelta(days=x),
    'month': lambda x: relativedelta(months=x),
    'year': lambda x: relativedelta(years=x),
}


def get_srt_date_by_interval(end_date, interval, unit, include_end_date=True):
    if unit not in interval_map:
        raise KeyError(f'Invalid interval unit: {unit} -> must be "day" or "month" or "year"')

    # 지난 7일 -> end_date를 포함한다면, 6일전을 srt_date로
    if include_end_date:
        interval -= 1

    srt_date = end_date - interval_map[unit](interval)
    return srt_date


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


def get_date_format(unit, db_dialect):
    date_format = date_format_map[db_dialect][unit]
    return date_format


def to_string_date(date):
    return datetime.strftime(date, '%Y-%m-%d')


def date_to_string_column_expr(date_column_expr, date_format, db_dialect):
    if db_dialect == POSTGRESQL:
        return func.to_char(date_column_expr, date_format).label('date')
    elif db_dialect == MYSQL:
        return func.date_format(date_column_expr, date_format).label('date')
    elif db_dialect == SQLITE:
        return func.strftime(date_format, date_column_expr).label('date')
    else:
        raise NotImplementedError(f'Invalid dialect : {db_dialect}')


# selects를 포함시켜 expression_based로 만들고 execute() or scalar()로 실행까지
# => 첫 호출 session인자에 + 실행까지 포함하여 filter_by 옵션까지 받는다.
# => 결과물이 scalar의 1개면, => 여러개가 안나오므로, order_by와 limit 옵션은 X
# class ExpressionMixin:
class ExpressionMixin(CRUDMixin):  # 작업시만 BaseQuery + ObjectMixin을 달고 있는 것(CRUDMixin)을 상속해서 작업
    __abstract__ = True

    # ###########################
    # # count_and_rate_between  # for 변화율
    # ###########################
    @classmethod
    def count_and_rate_between(cls, date_attr, to_date,
                               from_date=None, interval=None, unit=None, include_to_date=True,
                               count_attr=None, session: Session = None, filter_by=None,

                               ):
        if not (from_date or (interval and unit)):
            raise Exception(f'from_date 혹은 interval + unit 둘 중 한가지를 입력해야 from_date가 정해집니다.')

        if not from_date:
            from_date = get_srt_date_by_interval(to_date, interval, unit, include_end_date=include_to_date)

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

    # for count_and_rate_between
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
        count_column_expr = cls.create_count_column_expr(count_attr)

        srt_date_column = cls.create_column_expr(cls, date_attr, cls.FILTER_BY)

        query = (
            select(count_column_expr)
            .select_from(cls)  # 필수
            .where(func.date(srt_date_column) <= end_date)
        )

        # query=나 select는 expression_based =True를 만들어, execute()로 수행 + outerjoin만 수행 + 전체조회시 .unique()할 필요없음.
        obj = cls.create_obj(session=session, query=query, filter_by=filter_by)

        return obj.scalar()

    # for count_until + for count_per_date_unit_subquery
    # + for chartwrapper -> count_pie에서 count_attr을 받음.
    @classmethod
    def create_count_column_expr(cls, count_attr):
        count_attr = cls.process_count_attr_name(count_attr)
        #    만약, distinct가 필요했다면, 칼럼명__count_distinct까지 입력했을 것.
        count_column_expr = cls.create_column_expr(cls, count_attr, cls.SELECT, label='count')
        return count_column_expr

    @classmethod
    def process_count_attr_name(cls, count_attr):
        # 1) 칼럼지정안하면, pk 첫번째로 카운트
        if not count_attr:
            count_attr = cls.first_primary_key_name + cls.OPERATOR_OR_AGG_SPLITTER + cls.COUNT
        # 2) 칼럼 지정했으면, __count안달렸으면 달아주고 표현식 만들기
        else:
            if cls.COUNT not in count_attr:
                count_attr += cls.OPERATOR_OR_AGG_SPLITTER + cls.COUNT
        return count_attr

    # #######################
    # # count_for_interval  # series에 비해 구멍있는, group_by로 인해 가진 날짜마다의 count 나열 (series에 outerjoin예정
    # #######################
    @classmethod
    def count_for_interval(cls, date_attr,
                           end_date, interval, unit, srt_date=None,  # series + count_per_date_unit
                           include_end_date=True,  # series
                           count_attr=None, filter_by=None,  # count_per_date_unit
                           session: Session = None
                           ):
        """
        각각은 chart 데이터(date list, count list 각각)로 변환될 예정이다.

        1. Category.count_for_interval('add_date', today, 7, 'day')
        => [('2023-02-22', 0), ('2023-02-23', 0), ('2023-02-24', 0), ('2023-02-25', 0), ('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 1)]

        2. filter 추가
        Category.count_for_interval('add_date', today, 7, 'day', filter_by={'name__ne':'123'})
        =>  [('2023-02-22', 0), ('2023-02-23', 0), ('2023-02-24', 0), ('2023-02-25', 0), ('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 0)]


        """
        #### session을 가져야 dialect를 뽑아낼 수 있으므로, create_obj부터
        # obj = cls.create_obj(session=session, query=query)
        obj = cls.create_obj(session=session)

        # 1) 'series' label의 'date' label(string date) 칼럼을 가진 generate_series 생성
        series_subquery = cls.generate_series_subquery(end_date, interval, unit,
                                                       srt_date=srt_date, include_end_date=include_end_date,
                                                       # db_dialect=db_dialect)
                                                       db_dialect=obj.db_dialect)

        # 2) series에 outerjoin할, 'date'칼럼을 가진, 자신의 데이터 날짜 string 별 group_by해서 series별 구멍이 난
        #    'date', 'count'칼럼을 가진 count subquery 생성
        count_per_date_subquery = cls.count_per_date_unit_subquery(date_attr, end_date, interval, unit,
                                                                   srt_date=srt_date, count_attr=count_attr,
                                                                   filter_by=filter_by,
                                                                   # db_dialect=db_dialect,
                                                                   db_dialect=obj.db_dialect,
                                                                   include_end_date=include_end_date)

        # 3) series <- count_per_date  outerjoin : subquery끼리는, aliased없이 table처럼 하면 된다
        query = (
            select(series_subquery.c.date.label('date'),
                   func.coalesce(count_per_date_subquery.c.count, 0).label('count'))
            .outerjoin(count_per_date_subquery, count_per_date_subquery.c.date == series_subquery.c.date)
            .order_by(series_subquery.c.date.asc())
        )

        # 4) select변경을 가한 query는 생성할 때 query도 같이 set
        #   *filter_by는 count_per_date할때만 적용되어야하므로, 미리 query에 넣어서 넣고, create_obj에서는 배제
        # obj = cls.create_obj(session=session, query=query)
        obj.set_query(query)
        result = obj.execute()

        return result

    # for count_for_interval    subquery1
    # generate_series_subquery  # 구멍없는 날짜의 나열
    @classmethod
    def generate_series_subquery(cls, end_date, interval, unit, srt_date=None,
                                 db_dialect=SQLITE,
                                 include_end_date=True
                                 ):
        """
        subquery label은 'series', 칼럼명은 'date'로 작성된다.
        - postgresql 은 generate_series 메서드를
        - mysql, sqlite는 재귀를 이용해서 생성한다.
        - subquery를 .select()한 뒤 실행해놓고선, fetchall()까지 해야 보인다.

        db.get_session().execute(
            Category.generate_series_subquery(today, 7, 'day')
        .select()).fetchall()
        => [('2023-02-22',), ('2023-02-23',), ('2023-02-24',), ('2023-02-25',), ('2023-02-26',), ('2023-02-27',), ('2023-02-28',)]


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
        # 1) (default)srt_date가 주어지지 않는다면, 구간(interval) 단위(unit)만큼 앞으로 가서 만든다.
        # -> end_date를 포함해서 7일이면, 6일전을 시작으로 가야되므로 flag를 준다.
        if not srt_date:
            srt_date = get_srt_date_by_interval(end_date, interval, unit, include_end_date=include_end_date)

        # 2) db dialect에맞게, date_format을 가져와서, statement를 작성한다.
        date_format = get_date_format(unit, db_dialect)

        if db_dialect == POSTGRESQL:
            stmt = f"""
            select to_char(generate_series, '{date_format}') as date 
            from generate_series('{to_string_date(srt_date)}'::DATE, '{to_string_date(end_date)}'::DATE, '1 {unit}s'::INTERVAL)
            """
            return (
                text(stmt)
                .columns(column('date'))
                .subquery('series')
            )

        else:
            if db_dialect == MYSQL:
                select_date = f"SELECT date + interval 1 {unit}"
                to_char = f"DATE_FORMAT(date, '{date_format}')  AS 'date'"
            elif db_dialect == SQLITE:
                select_date = f"SELECT date(date, '+1 {unit}')"
                to_char = f"strftime('{date_format}', date) AS 'date' "
            else:
                raise NotImplementedError(f'Not implemented for {db_dialect}')

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
                .bindparams(start_date=to_string_date(srt_date), end_date=to_string_date(end_date))
                .columns(column('date'))
                .subquery('series')
            )

    # for count_for_interval    subquery2
    # count_per_date_unit_subquery  # series에 비해 구멍있는, group_by로 인해 가진 날짜마다의 count 나열 (series에 outerjoin예정
    @classmethod
    def count_per_date_unit_subquery(cls, date_attr,
                                     end_date, interval, unit, srt_date=None,  # series와 동일
                                     count_attr=None, filter_by=None,  # 추가
                                     db_dialect=SQLITE, include_end_date=True,  # series
                                     ):
        """
        1. generate_series에 outerjoin 조건으로 쓸 string_date로 group_by에 올려서 count하는데,
        -> series에 비해, 날짜칼럼에 데이터가 존재하는 날짜만 (연속아닐 수 == series대비 구멍뚤린체)로 count하게 된다.
        2. filter_by의 조건식을 다는데, 관계처리를 위해 obj에 filter_by로 넣어줘야하므로, select + group_by를 미리 query로 작성한 뒤
           filter_by는 내부에서 with_alias_map으로 작성되게 뒤에 넣어준다
        -> 그래도 group_by보다 뒤에 적힌 where가 먼저 query에 표시된다.
        => 관계 필드를 조건문에 건 순간, 관계필드 = None인 outerjoin(관계가 조성되지 않는 데이터)는 모두 제외된다.
        3. count기준은 count_attr을 입력하지 않으면, 첫번째pk를 기준으로 세며
        -> pk, uk가 아닌 칼럼을 중복제외하고 세고 싶을 땐 'name__count_distinct'로 다 명시한다.
        4. 쿼리
        (1) filter없는 버전
        subquery = Category.count_per_date_unit_subquery('add_date', today, 7, 'day')
        print(subquery)

        SELECT strftime(:strftime_1, categories.add_date) AS date, coalesce(count(categories.id), :coalesce_1) AS count
        FROM categories
        WHERE date(categories.add_date) BETWEEN :date_1 AND :date_2
        GROUP BY strftime(:strftime_1, categories.add_date)

        (2) filter있는 버전(관계필터까지)
        subquery = Category.count_per_date_unit_subquery('add_date', today, 7, 'day', filter_by=dict(name__ne=None, posts___title__length__lt=10))
        print(subquery)
        SELECT strftime(:strftime_1, categories.add_date) AS date, coalesce(count(categories.id), :coalesce_1) AS count
        FROM categories
        LEFT OUTER JOIN posts AS posts_1
            ON categories.id = posts_1.category_id
        WHERE date(categories.add_date) BETWEEN :date_1 AND :date_2
            AND categories.name IS NOT NULL
            AND length(posts_1.title) < :param_1
        GROUP BY strftime(:strftime_1, categories.add_date)

        5. 실행
        db.get_session().execute(Category.count_per_date_unit_subquery('add_date', today, 7, 'day').select()).fetchall()
        => [('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 1), ('2023-03-01', 1)]


        db.get_session().execute(Category.count_per_date_unit_subquery('add_date', today, 7, 'day', filter_by={'name__ne':'123'}).select()).fetchall()
        => [('2023-02-26', 1), ('2023-02-27', 3), ('2023-03-01', 1)]

        관계 필드를 조건문에 건 순간, 관계필드 = None인 outerjoin(관계가 조성되지 않는 데이터)는 모두 제외된다.
         db.get_session().execute(Category.count_per_date_unit_subquery('add_date', today, 7, 'day', filter_by=dict(name__ne=None, posts___title__ne=None)).select()).fetchall()
        => []
        """
        # 1) (default)srt_date가 주어지지 않는다면, 구간(interval) 단위(unit)만큼 앞으로 가서 만든다.
        # -> end_date를 포함해서 7일이면, 6일전을 시작으로 가야되므로 flag를 준다.
        if not srt_date:
            srt_date = get_srt_date_by_interval(end_date, interval, unit, include_end_date=include_end_date)

        # 2) db dialect에맞게, date_format을 + date column -> strig expr로 변환한다.
        date_format = get_date_format(unit, db_dialect)

        date_column_expr = cls.create_column_expr(cls, date_attr, cls.SELECT)
        # 'date'로 label을 강제지정까지 같이 함. for outerjoin
        date_string_column_expr = date_to_string_column_expr(date_column_expr, date_format, db_dialect)

        # 3) count expr를 작성한다
        count_column_expr = cls.create_count_column_expr(count_attr)

        # 4) string date 칼럼별 count를 센다.
        # filter_exprs = cls.create_conditional_exprs(cls, filter_by) if filter_by else []
        # stmt = (
        #     select(date_string_column_expr, count_column_expr)
        #     .where(*filter_exprs)
        #     .where(func.date(date_column_expr).between(srt_date, end_date))
        #     .group_by(date_string_column_expr)
        # )
        #### filter_by에 alias 관계모델을 반영하기 위해선 obj로 가야한다.
        #    group_by를 먼저 작성해놓긴 하지만, where가 뒤에 붙어도 먼저 처리될 것이다?!
        #### query만 만들거라 session없이 생성해도 상관없다
        query = (
            select(date_string_column_expr, count_column_expr)
            .select_from(cls)
            .where(func.date(date_column_expr).between(srt_date, end_date))
            .group_by(date_string_column_expr)
        )
        # 1. selects나 query가 들어가면 expression based로 인식되어, outerjoin만 된다.
        # 2. obj.create_obj나 OR obj.set_attrs에 filter_by(dict)가 들어가야, alias_map기반으로 관계처리가 된다.
        obj = cls.create_obj(query=query, filter_by=filter_by)

        #### => .close()처리는 실행메서드, .subquery() self메서드 내부로 옮김.
        # obj._session.close()
        # cf) expunge( 객체 ) 는 객체를 session에서 제거

        return obj.subquery()
