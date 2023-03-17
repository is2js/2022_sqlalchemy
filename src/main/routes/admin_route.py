from datetime import date, datetime
import pyecharts
from flask import Blueprint, render_template, request, flash, redirect, url_for, g, make_response, session

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3.wrapper.chartwrapper import Chart
from src.infra.tutorial3 import Category, Post, Tag, User, Banner, Setting, Department
from src.infra.tutorial3.auth.users import SexType, Roles, Role, EmployeeInvite, JobStatusType, Employee, \
    EmployeeLeaveHistory
from src.main.decorators.decorators import login_required, role_required
from src.main.forms import CategoryForm
from src.main.forms.admin.forms import PostForm, TagForm, CreateUserForm, BannerForm, SettingForm
from src.main.forms.auth.forms import EmployeeForm
from src.main.utils import redirect_url
from src.main.utils import upload_file_path, delete_uploaded_file, delete_files_in_img_tag
from src.main.utils.format_date import format_date

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# def get_pie_chart(db, entity, category_column_name, conditions=None):
#     # 1) sql을 groupby에 카테고리를 올리고, 갯수를 센다
#     # -> group_by 집계시에는 label을 못단다?
#     # [(False, 2), (True, 2)]
#     stmt = (
#         select(getattr(entity, category_column_name), func.count(entity.id))
#         .group_by(getattr(entity, category_column_name))
#     )
#
#     # if conditions:
#     # 내부에서 빈 conditions는 알아서 처리해줌.
#     stmt = add_dynamic_filter(stmt, entity, conditions)
#
#     datas = db.session.execute(
#         stmt
#     ).all()
#
#     # print(f'{entity} datas in get_pie_chart  >> ', datas)
#     # 유저가 없을 경우 => []
#
#     # print(datas)
#     # [(False, 2), (True, 2)]
#
#     # 2)카테고리 종류가 눈에 들어오기 슆게 바꿔야한다.
#     #  성별 -> 0 미정, 1 남자 2 여자
#     #  enum을 import해서 처리하는게 좋을 듯.
#
#     # datas = list(map(lambda x: ('관리자' if x[0] else '일반유저', x[1]), datas))
#     # print(datas)
#     # [('일반유저', 2), ('관리자', 2)]
#
#     # datas = list(map(lambda x: SexType(x[0]).name, datas))
#     # print(datas)
#     # ['미정', '남자', '여자']
#     # 첫번째 데이터x[0]카테고리가 0인 것을 제외시키고 변환하면, 미정을 제외시킬 수 있다.
#     # => 데이터가 0인 경우, 에러가 발생하므로, 일단 치운다.
#     # datas = list(map(lambda x: (SexType(x[0]).name, x[1]), [x for x in datas if x[0] != 0]))
#     datas = list(map(lambda x: (SexType(x[0]).name, x[1]), datas))
#     # print(datas)
#
#     # 3) pie차트는 [ (category1, count1) , (category2, count2)] tuple list를 입력으로 받는다.
#     #### 빈 datas면.. range error가 나서.. if문 걸어줌.
#     if datas:
#         # print(datas)
#         # [('남자', 8), ('여자', 13)]
#         c = (
#             Pie()
#             .add("", datas)
#             .set_series_opts(label_opts=opts.LabelOpts(
#                 formatter="{b}({d}%)"))  # {b}: 튜플[0] 카테고리명 /  {d} => 현재 튜플[1] count / 전체 튜플[1]의 합 => 다 0일 때, 0/0으로 undefined됨.
#             .set_global_opts(legend_opts=opts.LegendOpts(pos_left=True, orient='vertical'))
#         )
#         return c
#     else:
#         # 데이터가 없는 경우에도, 차트는 만들어야 한다. [('미정'or'남자'or'여자'), count)]가 만들어져야한다.
#         c = (
#             Pie()
#             .add("", [(sex_type.name, 0) for sex_type in SexType])  # enum을 순회하면서 count는 다 0으로
#             .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}"))  # format에서 {d}( 현재/전체 비율 -> 전체 0이므로 {d} 표기 제거)
#             .set_global_opts(legend_opts=opts.LegendOpts(pos_left=True, orient='vertical'))
#         )
#         return c


# def get_diff_for(db, entity, interval='day', period=7, conditions=None):
#     if period < 2:
#         raise ValueError('최소 1단위 전과 비교하려면, period는 2 이상이어야합니다.')
#     end_date = date.today()
#     if interval == 'day':
#         start_date = end_date - relativedelta(days=period - 1)
#     elif interval == 'month':
#         start_date = end_date - relativedelta(months=period - 1)
#     elif interval == 'year':
#         start_date = end_date - relativedelta(years=period - 1)
#     else:
#         raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')
#
#     end_stmt = select(func.count(entity.id)).where(and_(func.date(getattr(entity, 'add_date')) <= end_date))
#     # if conditions:
#     end_stmt = add_dynamic_filter(end_stmt, entity, conditions)
#
#     end_count = db.session.scalar(
#         end_stmt
#     )
#
#     print('end_count  >> ', end_count)
#     # print('StaticsQuery.count_until  >> ', StaticsQuery.count_until(entity, 'add_date', end_date))
#
#     srt_stmt = select(func.count(entity.id)).where(and_(func.date(getattr(entity, 'add_date')) <= start_date))
#     # if conditions:
#     srt_stmt = add_dynamic_filter(srt_stmt, entity, conditions)
#
#     start_count = db.session.scalar(
#         srt_stmt
#     )
#     # print(end_count - start_count, type(end_count))
#     diff = end_count - start_count
#     # start가 zero division
#     try:
#
#         rate_of_increase = round((end_count - start_count) / start_count * 100, 2)
#         print(f'{entity} TRY rate_of_increase  >> ', rate_of_increase)
#     except:
#         rate_of_increase = round(end_count * 100, 2)
#         print(f'{entity} EXCEPT rate_of_increase  >> ', rate_of_increase)
#         print('end_count  >> ', end_count)
#
#     # print(rate_of_increase)
#     return diff, rate_of_increase


# def add_dynamic_filter(stmt, entity, conditions):
#     """
#     cf: 1차: https://stackoverflow.com/questions/41305129/sqlalchemy-dynamic-filtering
#     :param conditions:list of tuple  [('column_name', 'op', value) , ... ]
#         - op list
#             'eq' for ==
#             'ne' for !=
#             'lt' for <
#             'ge' for >=
#             'in' for in_
#             'like' for like
#         - value : list or string
#     :param stmt:
#     :param entity:
#     :return: query statement
#     """
#     if not conditions:
#         return stmt
#
#     for raw in conditions:
#         # 1) tuple에 3개의 요소가 다차있는지 확인은 아래와 같이 try/except로 unpacking가능한지를 확인
#         try:
#             column_name, op, value = raw
#         except:
#             raise Exception(f'Invalid filter {raw}')
#
#         # 2) filter에 쓰일 Model.column 을  getattr()로 뽑아낸다. hybrid property도 가능하다.
#         column = getattr(entity, column_name, None)
#
#         if not column:
#             raise Exception(f'Invalid column name {column_name}')
#
#         # 3) 연산자 중에 in만 value에 따라서, column.in_( value )를 치는데, string으로 '1,2,3'입력도 받아처리해준다.
#         if op == 'in':
#             if isinstance(value, list):
#                 my_filter = column.in_(value)
#             else:
#                 my_filter = column.in_(value.split(','))
#         else:
#             # >>> hasattr(User.is_staff, 'eq')
#             # False
#             # >>> hasattr(User.is_staff, 'eq_')
#             # False
#             # >>> hasattr(User.is_staff, '__eq__')
#             # True
#             # 4) in을 제외한 연산자들은 column. __연산명__() 메서드로 거의다 정의되어있다.
#             #    혹시 없으 수 있으니 .연산() .연산_()  .__연산__() 중 true인 것 1개를 뽑아서 처리하고,
#             #    해당 연산자가 hasattr()로 메서드 가졌는지 안나타나  true만 뽑는 filter에 안걸리면 indexError로 에러를 낸다.
#             try:
#                 # [op, f'{op}_', f'__{op}__'] # 3개 연산자 중에 1개라도 column이 들고 있으면, 그놈 중 첫번재 아무거나
#                 # => list( filter(lambda x: , 배열)) 로 true것들만 골라낸 뒤, 첫번째만
#                 op = list(filter(lambda x: hasattr(column, x), [op, f'{op}_', f'__{op}__']))[0]
#             except IndexError:
#                 raise Exception(f'Invalid operator {op}')
#             # 5)  혹시 value에 'null'을 입력하는 경우는, python None을 대신 넣어준다 (json)
#             if value == 'null':
#                 value = None
#             # User.is_staff.__eq__( value )
#             my_filter = getattr(column, op)(value)
#         stmt = stmt.where(my_filter)
#
#     return stmt


@admin_bp.route('/')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def index():
    post_count = Post.count()
    post_count_diff, post_count_diff_rate = Post.count_and_rate_between('add_date', date.today(), interval=7,
                                                                        unit='day', filter_by=None)
    category_count = Category.count()
    category_count_diff, category_count_diff_rate = Post.count_and_rate_between('add_date', date.today(),
                                                                                interval=7,
                                                                                unit='day',
                                                                                filter_by=None)
    banner_count = Banner.count()
    banner_count_diff, banner_count_diff_rate = Banner.count_and_rate_between('add_date', date.today(), interval=7,
                                                                              unit='day',
                                                                              filter_by=None)

    user_count = User.filter_by(is_staff=False).count()
    user_count_diff, user_count_diff_rate = User.count_and_rate_between('add_date', date.today(), interval=7,
                                                                        unit='day',
                                                                        filter_by=dict(is_staff=False))

    # employee_count = Employee.filter_by(
    #     and_=dict(
    #         or_=dict(is_active=True, is_leaved=True),
    #         user___role___name__ne='ADMINISTRATOR',
    #     )
    # ).count()
    #

    # employee_count = Employee.filter_by(
    #     and_=dict(
    #         or_=dict(is_active=True, is_leaved=True),
    #         has_role=Role.filter_by(name='ADMINISTRATOR').first(),
    #     )
    # ).count()

    employee_count = Employee.filter_by(
        and_=dict(
            or_=dict(is_active=True, is_leaved=True),
            # user___role___name__ne=Roles.ADMINISTRATOR.name,
            # has_role_name__ne=Roles.ADMINISTRATOR.name,
            except_admin=True
        )).count()

    employee_count_diff, employee_count_diff_rate = Employee.count_and_rate_between(
        'add_date', date.today(),
        interval=7,
        unit='day',
        filter_by=dict(
            and_=dict(
                or_=dict(
                    is_active=True,
                    is_leaved=True),
                # user___role___name__ne=Roles.ADMINISTRATOR.name
                except_admin=True
            )),
    )

    # before
    # post_count = db.session.scalar(select(func.count(Post.id)))
    # post_count_diff, post_count_diff_rate = get_diff_for(db, Post, interval='day', period=7)
    # category_count = db.session.scalar(select(func.count(Category.id)))
    # category_count_diff, category_count_diff_rate = get_diff_for(db, Category, interval='day', period=7)
    # banner_count = db.session.scalar(select(func.count(Banner.id)))
    # banner_count_diff, banner_count_diff_rate = get_diff_for(db, Banner, interval='day', period=7)

    # user_count = db.session.scalar(select(func.count(User.id)).where(~User.is_staff))
    # user_count_diff, user_count_diff_rate = get_diff_for(db, User, interval='day', period=7,
    #                                                      conditions=[('is_staff', 'eq', False)]
    #                                                      )

    # # 직원 중에 재직+휴직(퇴사만 아니면) 카운터에 포함시킨다. + 관리자는 제외한다.
    # employee_count = db.session.scalar(
    #     select(func.count(Employee.id))
    #     .where(or_(Employee.is_active, Employee.is_leaved))
    #     .where(not Employee.is_administrator)  # hybrid expression을 조건문에 걸땐, ~ 이 아닌 not으로 걸자.
    # )
    # # => 관리자 제외시킬 건데, is_admin==관리자이상 => and_()로 연결해서 필수제외조건으로 추가한다
    # employee_count_diff, employee_count_diff_rate = get_diff_for(db, Employee, interval='day', period=7,
    #                                                              conditions=[('is_administrator', 'eq', False)],
    #                                                              )

    # 연결되어있는 것도  sql문으로하려면, 직접 where에 연결해줘야한다(꽁join 아니면)
    ## none을 0개로 셀땐 func.coalesce(values.c.cnt, 0)
    # stmt = select(Category.name, func.count(Post.id).label('count')) \
    #     .where(Post.category_id == Category.id) \
    #     .group_by(Post.category_id)

    ## post 갯수0짜리도 찍히게 하려면,[사실상 one별 many의 집계] => many에서 fk별 집계한 뒤, one에 fk==id로 붙인다.
    ##  (1) Post에서 subquery로 미리 카테고리id별 count를 subquery로 계산
    ##  (2) Category에 category별 count를 left outer join
    ## => main_06_subquery_cte_기본.py 참고
    #### < 1-1 category별 post 갯수>
    # subq = select(Post.category_id, func.coalesce(func.count(Post.id), 0).label('count')) \
    #     .group_by(Post.category_id) \
    #     .subquery()
    # stmt = select(Category.name, subq.c.count) \
    #     .join_from(Category, subq, isouter=True) \
    #     .order_by(subq.c.count.desc())
    # post_count_by_category = db.session.execute(stmt)

    # [('분류1', 5), ('22', 2)]
    post_count_by_category = Category.group_by('id', selects=['name', 'posts___id__count']).execute()

    post_by_category_x_datas = []
    post_by_category_y_datas = []
    for category, post_cnt_by_category in post_count_by_category:
        post_by_category_x_datas.append(category)
        post_by_category_y_datas.append(post_cnt_by_category)

    #### < 1-2 post가 가장 많이 걸린 tag> -> Tag별 post갯수세기 -> 중간테이블이라서 바로 집계되지만, name을 얻으려면 left join
    #### => left.right관계명으로 assoc table무시하고, outerjoin을 건다(내부에서 assoc 와 right(Post)를 일반join한 뒤 outerjoin한다)
    # stmt = select(Tag.name, func.coalesce(Post.id, 0).label('count'), func.coalesce(cast(Post.has_type, Integer), 0).label('sum')) \
    # stmt = select(Tag.name, func.coalesce(func.count(Post.id), 0).label('count'),
    #               func.sum(cast(Post.has_type, Integer)).label('sum')) \
    #     .join(Tag.posts, isouter=True) \
    #     .group_by(Tag.id) \
    #     .order_by(literal_column('count').desc()) \
    #     .limit(3)

    #### 기존 => 아직해소 되지 않은 [ rows ] => jinja에서만 사용가능해짐 row.name / row.count 등
    # tag_with_post_count  >>  [('태그1', 1, 2)]
    # => but jinja에서 내부가 실행되나. tag_with_post_count -> for tag -> tag.name  tag.count tag.sum
    # => db컨넥션을 풀기 위해 enum치환하여 dict로 풀어서 -> jinja에선 tag['name'], tag['count']. tag['sum']으로 변경하기
    # tag_with_post_count = db.session.execute(stmt).all()

    #### 업뎃 => enum처리한 dict list로 반환하며, jinja에서 dict list -> dict['name'] 를 사용하도록 변경
    # tag_with_post_count = StaticsQuery.agg_with_relationship(Tag, 'name', 'posts',
    #                                                          rel_agg_dict={'id': 'count', 'has_type': 'sum'},
    #                                                          )
    # print('tag_with_post_count [before]  >> ', tag_with_post_count)
    # [{'name': '태그1', 'count': 1, 'sum': 2}, {'name': 'asdf', 'count': 0, 'sum': 0}]

    # 칼럼명_집계로 자동label을 잡으니, 템플릿에서 맞게 수정해준다.
    tag_with_post_count = Tag.group_by('id', selects=['name', 'posts___id__count', 'posts___view_count__sum']) \
        .limit(3).to_dict2()
    # print('tag_with_post_count [after]  >> ', tag_with_post_count)
    # [{'name': '태그1', 'id_count': 1, 'id_sum': 2}, {'name': 'asdf', 'id_count': 0, 'id_sum': 0}]

    #### < 2-1 일주일 user 수>
    #### before
    # user_chart = get_user_chart(db, conditions=[('is_administrator', 'eq', False)])
    #### before 2
    # prev_chart = PrevChart()
    # user_chart = prev_chart.create_count_bar(User, 'add_date', date.today(),
    #                                     interval_unit='day', interval_value=7,
    #                                     # filters={'and': [('is_administrator', '==', False)]}
    #                                     filters={'is_administrator': False}
    #                                     )
    # print('user_chart._xaxis_data  >> ', user_chart._xaxis_data)
    #  ['24일', '25일', '26일', '27일', '28일', '1일', '2일']

    chart = Chart(pyecharts)
    # user_chart = chart.count_bar_for_interval(
    #     User, 'add_date', 7, 'day', filter_by=dict(is_administrator=False),
    #                                           )
    user_chart = chart.count_bars_for_interval(
        [User, Employee], 'add_date', 7, 'day', filter_by_per_model=dict(
            User=dict(is_staff=False),
            Employee=dict(
                and_=dict(
                    or_=dict(
                        is_active=True,
                        is_leaved=True
                    ),
                    # has_role_name__ne=Roles.ADMINISTRATOR.name,
                    except_admin=True,
                )
            ))
    )


    # print('user_chart._xaxis_data  >> ', user_chart._xaxis_data)
    #  ['24일', '25일', '26일', '27일', '28일', '1일', '2일']

    # print("user_chart", user_chart)
    # <2-2-2 user 성별 piechart > 아직 성별칼럼이 없으니 직원수 vs 일반 유저로 비교해보자.
    # user_sex_pie_chart = get_pie_chart(db, User, 'sex', conditions=[('sex', 'ne', SexType.미정.value)])
    #### before
    # user_sex_pie_chart = get_pie_chart(db, User, 'sex', conditions=[('is_administrator', 'eq', False)])
    #### before 2
    # user_sex_pie_chart = prev_chart.create_pie(User, 'sex', agg='count',
    #                                            # filters={'and': [('is_administrator', '==', False)]}
    #                                            filters={'is_administrator': False}
    #                                            )
    #### after
    user_sex_pie_chart = chart.count_pie_per_category(User, 'sex', filter_by=dict(is_administrator=False))

    ### 만약, df로 만들거라면 row별로 dict()를 치면 row1당 column:value의 dict list가 된다.
    # print([dict(r) for r in db.session.execute(stmt)])

    #### < 월별 연간 통계 by pyerchart>
    # year_x_datas, year_post_y_datas = get_datas_count_by_date(db, Post, 'add_date', interval='month', period=12)
    # _, year_user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='month', period=12,
    #                                                # conditions=[('is_administrator', 'eq', False)],
    #                                                filters={'is_administrator': False}
    #                                                )
    # _, year_category_y_datas = get_datas_count_by_date(db, Category, 'add_date', interval='month', period=12)
    # _, year_banner_y_datas = get_datas_count_by_date(db, Banner, 'add_date', interval='month', period=12)
    # _, year_tag_y_datas = get_datas_count_by_date(db, Tag, 'add_date', interval='month', period=12)
    # year_chart = (
    #     Bar()
    #     .add_xaxis(year_x_datas)
    #     .add_yaxis('유저 수', year_user_y_datas)  # y축은 name먼저
    #     .add_yaxis('포스트 수', year_post_y_datas)
    #     .add_yaxis('카테고리 수', year_category_y_datas)
    #     .add_yaxis('배너 수', year_banner_y_datas)
    #     .add_yaxis('태그 수', year_tag_y_datas)
    # )
    #
    # year_chart = prev_chart.create_count_bars([User, Employee, Post, Category, Banner, Tag], 'add_date',
    #                                           date.today(),
    #                                           interval_unit='month', interval_value=12,
    #                                           filters_with_model={
    #                                               User: {'is_administrator': False},
    #                                               Employee: {'name__ne': '관리자'},
    #                                           })

    year_chart = chart.count_bars_for_interval([User, Employee, Post, Category, Banner, Tag], 'add_date', 12,
                                               'month',
                                               filter_by_per_model={
                                                   User: dict(is_administrator=False),
                                                   Employee: dict(
                                                       and_=dict(
                                                           or_=dict(
                                                               is_active__eq=True,
                                                               is_leaved__eq=True),
                                                           # user___is_administrator=False,
                                                           except_admin=True,
                                                       ))
                                               })

    return render_template('admin/index.html',
                           post_count=(post_count, post_count_diff_rate),
                           category_count=(category_count, category_count_diff_rate),
                           banner_count=(banner_count, banner_count_diff_rate),
                           user_count=(user_count, user_count_diff_rate),
                           employee_count=(employee_count, employee_count_diff_rate),

                           post_by_category=(post_by_category_x_datas, post_by_category_y_datas),
                           tag_with_post_count=tag_with_post_count,

                           user_count_bar_options=user_chart.dump_options(),
                           user_sex_pie_options=user_sex_pie_chart.dump_options(),
                           year_options=year_chart.dump_options(),

                           chart=[user_chart, user_sex_pie_chart]
                           )


# def get_user_chart(db, conditions=None):
#     user_x_datas, user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='day', period=7,
#                                                          conditions=conditions)
#
#     user_chart = (
#         Bar()
#         .add_xaxis(user_x_datas)
#         .add_yaxis('유저 수', user_y_datas)
#     )
#
#     return user_chart
#
#
# def get_datas_count_by_date(db, entity, date_column_name, interval='day', period=7, conditions=None, filters=None):
#     if period < 2:
#         raise ValueError('최소 1단위 전과 비교하려면, period는 2 이상이어야합니다.')
#
#     end_date = date.today()  # end_date는 datetime칼럼이라도, date기준으로
#     if interval == 'day':
#         start_date = end_date - relativedelta(days=period - 1)
#     elif interval == 'month':
#         start_date = end_date - relativedelta(months=period - 1)
#     elif interval == 'year':
#         start_date = end_date - relativedelta(years=period - 1)
#     else:
#         raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')
#
#     series = generate_series_subquery(db, start_date, end_date, interval=interval)
#     #### 교체 성공
#     # series = StaticsQuery.create_date_series_subquery(end_date, interval_unit=interval, interval_value=period)
#
#     ### subquery를 확인시에는 .select()로 만들어서 .all()후 출력
#     # print(db.session.execute(series.select()).all())
#     # print(ts, type(ts))
#     ## 3) User의 생싱일date별 count 집계하기
#     # [('2022-11-19', 1), ('2022-11-25', 2)]
#     ## ==> datetime필드를, date기준으로 filtering하고 싶다면
#     ##     칼럼.between()에 못넣는다.
#     ## ==> datetime -> date로 칼럼을 변경하고 filter해야지, 오늘13시도, today()에 걸린다
#     ## 만약, today() 2022-11-29를   2022-11-29 13:00:00 datetime필드로 필터링하면
#     ##  오늘에 해당 데이터가 안걸린다. 데이터를 일단 변환하고 필터링에 넣어야한다.
#     # select(func.date(User.add_date).label('date'), func.count(User.id).label('count')) \
#     #### 이전
#     values = count_by_date_subquery(db, interval, entity, date_column_name, end_date, start_date,
#                                     conditions=conditions)
#     #### 업뎃
#     # values = StaticsQuery.create_date_to_count_subquery(entity, date_column_name, end_date, interval, period,
#     #                                                     filters=filters)
#
#     # print(db.session.execute(values.select()).all())
#
#     # .group_by(func.strftime("%Y", User.add_date).label('date'))\
#     # => [('2022', 4)]
#     # .group_by(func.date(User.add_date).label('date'))\
#     # .group_by(func.date(User.add_date))
#     # print(db.session.execute(values.select()).all())
#     # [('2022-11-19', 1), ('2022-11-25', 2), ... ('2022-11-29', 1)]
#     ## 3) series에 values르 outerjoin with 없는 데이터는 0으로
#     stmt = (
#         select(series.c.date, func.coalesce(values.c.count, 0).label('count'))
#         .outerjoin(values, values.c.date == series.c.date)
#         .order_by(series.c.date.asc())
#     )
#     ## scalars()하면 date만 나온다.
#     # print(db.session.scalars(stmt).all())
#     # [('2022-10-29', 0), ('2022-10-30', 0), ... ('2022-11-25', 2), ('2022-11-26', 0), ('2022-11-27', 0), ('2022-11-28', 0), ('2022-11-29', 1)]
#     # print(db.session.execute(stmt).all())
#     x_datas = []
#     y_datas = []
#     for day, user_count in db.session.execute(stmt):
#         x_datas.append(day)
#         y_datas.append(user_count)
#     # print('x_datas, y_datas  >> ', x_datas, y_datas)
#
#     # 집계대상 필터링은 Y-m-d(date) -> group_by strftime으로 (day) or Y-m-d/(month)Y-m/(year)Y 상태
#     # 이미 문자열로 Y-m-d  or Y-m  or Y 중 1개로 정해진 상태다. -> -로 split한 뒤 마지막거만 가져오면 interval 단위
#     # => 출력을 위해 day단위면, d만 / month단위면 m만 나가도록 해준다 (year는 이미 Y)
#     if interval == 'day':
#         x_datas = list(map(lambda x: x.split('-')[-1] + '일', x_datas))
#     elif interval == 'month':
#         x_datas = list(map(lambda x: x.split('-')[-1] + '월', x_datas))  # 이미 Y-m그룹화 상태
#     elif interval == 'year':
#         x_datas = list(map(lambda x: x + '년', x_datas))
#     return x_datas, y_datas


# def count_by_date_subquery(db, interval, entity, date_column_name, end_date, start_date, conditions=None):
#     if interval == 'day':
#         strftime_format = '%Y-%m-%d'
#     elif interval == 'month':
#         strftime_format = '%Y-%m'
#     elif interval == 'year':
#         strftime_format = '%Y'
#     else:
#         raise ValueError('invalid aggregation interval(string, day or month or year)  &  period=int')
#
#     if isinstance(db.session.bind.dialect, postgresql.dialect):
#         select_stmt = func.to_char(getattr(entity, date_column_name), strftime_format).label('date')
#     elif isinstance(db.session.bind.dialect, mysql.dialect):
#         select_stmt = func.date_format(getattr(entity, date_column_name), strftime_format).label('date')
#     else:
#         select_stmt = func.strftime(strftime_format, getattr(entity, date_column_name)).label('date')
#     stmt = (
#         select(select_stmt, func.count(entity.id).label('count'))
#         .where(and_(
#             start_date <= func.date(getattr(entity, date_column_name)),
#             func.date(getattr(entity, date_column_name)) <= end_date)
#         ))
#
#     # if conditions:
#     stmt = add_dynamic_filter(stmt, entity, conditions)
#
#     return (
#         # 여기에도 카운팅할 때, 다이나믹 filter 적용되어야함
#         stmt
#         .group_by(select_stmt)
#         .subquery()
#     )
#
#
# def generate_series_subquery(db, start_date, end_date, interval='day'):
#     if interval == 'day':
#         strftime_format = '%Y-%m-%d'
#     if interval == 'month':
#         strftime_format = '%Y-%m'
#     elif interval == 'year':
#         strftime_format = '%Y'
#
#     # select date form dates담에 ;를 넘으면 outer join시 에러
#     # stmt = f"""
#     #         WITH RECURSIVE dates(date) AS (
#     #               VALUES (:start_date)
#     #           UNION ALL
#     #               SELECT date(date, '+1 {interval}')
#     #               FROM dates
#     #               WHERE date < :end_date
#     #         )
#     #         SELECT strftime('{strftime_format}', date) AS 'date' FROM dates
#     #         """
#     # sqlite_select_date = f"SELECT date(date, '+1 {interval}')"
#     # postgresql_select_date = f"SELECT date + interval '1 {interval}s"
#     # mysql_select_date = f"SELECT date + interval 1 {interval}"
#     #
#     # # sqlite_to_char = f"strftime('{strftime_format}', date)"
#
#     date_format_map = {
#         'sqlite': {
#             'day': '%Y-%m-%d',
#             'month': '%Y-%m',
#             'year': '%Y',
#         },
#         'mysql': {
#             'day': '%Y-%m-%d',
#             'month': '%Y-%m',
#             'year': '%Y',
#         },
#         'postgresql': {
#             'day': 'YYYY-MM-DD',
#             'month': 'YYYY-MM',
#             'year': 'YYYY',
#         }
#     }
#     if isinstance(db.session.bind.dialect, postgresql.dialect):
#         # select_date = f"SELECT to_date(date, 'yyyy-MM-dd') + interval '1 {interval}s' AS date" # postgre는 '단일따옴표 안붙인다.
#         # to_char = f"TO_CHAR(date, '{strftime_format}')"
#         stmt = f"""
#                 select to_char(generate_series, '{date_format_map['postgresql'][interval]}') as date
#                 from generate_series('{to_string_date(start_date)}'::DATE, '{to_string_date(end_date)}'::DATE, '1 {interval}s'::INTERVAL)
#                 """
#         _text = text(
#             stmt
#         )
#
#         return _text.columns(column('date')).subquery('series')
#
#     elif isinstance(db.session.bind.dialect, sqlite.dialect):
#         # select_date = select(func.dateadd(func.now(),  text('interval 1 day')).label('date')).compile(dialect=sqlite.dialect())
#         select_date = f"SELECT date(date, '+1 {interval}')"
#         to_char = f"strftime('{strftime_format}', date) AS 'date' "
#         # sqlite는 values (시작date)
#         # mysql은 select(시작date)
#         stmt = f"""
#             WITH RECURSIVE dates(date) AS (
#                   VALUES (:start_date)
#                     UNION ALL
#                   {select_date}
#                   FROM dates
#                   WHERE date < :end_date
#             )
#
#             SELECT {to_char} FROM dates
#             """
#
#     elif isinstance(db.session.bind.dialect, mysql.dialect):
#         select_date = f"SELECT date + interval 1 {interval}"
#         to_char = f"DATE_FORMAT(date, '{strftime_format}')  AS 'date'"
#
#         stmt = f"""
#                     WITH RECURSIVE dates(date) AS (
#                           SELECT (:start_date)
#                             UNION ALL
#                           {select_date}
#                           FROM dates
#                           WHERE date < :end_date
#                     )
#
#                     SELECT {to_char} FROM dates
#                     """
#     else:
#         raise NotImplementedError(
#             'Not implemented for this dialect'
#         )
#
#     _text = text(
#         stmt
#     ).bindparams(start_date=to_string_date(start_date), end_date=to_string_date(end_date))
#
#     # func.to_char(orig_datetime, 'YYYY-MM-DD HH24:MI:SS) - psql
#     # SELECT strftime('%Y', date) FROM dates - sqlite
#
#     # with DBConnectionHandler() as db:
#     #     print(db.session.execute(stmt.columns(column('date')).label('date')).subquery('series').select()).all())
#     ## output 1 - date는 date타입이지만, 출력은 문자열로 된다.
#     # unit=day
#     # [('2022-10-29',), ('2022-10-30',),... ('2022-11-28',), ('2022-11-29',)]
#
#     # unit=month
#     # [('2022-10-29',), ('2022-11-29',)]
#     # unit=year
#     # [('2021-11-30',), ('2022-11-30',)]
#     ## output 2 - sqlite SELECT strftime('%Y', CURRENT_TIMESTAMP)으로
#     ##            그외는  SELECT EXTRACT(YEAR FROM CURRENT_DATE) 를 쓴다.
#     # => month일땐, Y-m으로  / year일땐, Y로만 나와야, 거기에 맞춘 values를 outer_join 시킬수 있을 것이다.
#     # => text.columns(column()) 지정시 func.extract로 변경하자.
#     # [('2021-11-30',), ('2022-11-30',)]
#     # if interval == 'year':
#     #     return stmt.columns(extract('year',column('date'))).subquery('series')
#
#     return _text.columns(column('date')).subquery('series')
#

@admin_bp.route('/category')
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category():
    # s = next(Category.get_session2())
    # print('s  >> ', s)
    # c2 = Category.get(2, session=s)
    # print('c2  >> ', c2)
    # s2 = next(Category.get_session2())
    # print('s2.scalars(select(Category)).first()  >> ', s2.scalars(select(Category)).first())

    # with DBConnectionHandler() as db:
    # admin- table에는 id역순으로 제공해줘야 최신순으로 보인다.
    # category_list = db.session.scalars((
    #     select(Category)
    #     .order_by(Category.id.desc())
    # )).all()

    # querystring의 page에서 page값 받고, int변환하되, 기본값 1
    page = request.args.get('page', 1, type=int)

    # # 직접 추출대신 pagination으로 처리하기 (id역순으로 전체조회)
    # stmt = select(Category).order_by(Category.id.desc())
    # # pagination = paginate(stmt, 1, per_page=1)
    # pagination = paginate(stmt, page=page, per_page=10)

    # after
    pagination = Category.order_by('-id').paginate(page, per_page=10)

    category_list = pagination.items

    return render_template('admin/category.html',
                           category_list=category_list, pagination=pagination)


@admin_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category_add():
    form = CategoryForm()
    if form.validate_on_submit():
        # category = Category(name=form.name.data, icon=form.icon.data)
        # with DBConnectionHandler() as db:
        #     db.session.add(category)
        #     db.session.commit()
        result, msg = Category.create(name=form.name.data, icon=form.icon.data)

        flash(f'{result.name} Category 생성 성공!')
        return redirect(url_for('admin.category'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/category_form.html', form=form, errors=errors)


# @admin_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.EXECUTIVE])
# def category_edit(id):
#     # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
#     with DBConnectionHandler() as db:
#         category = db.session.get(Category, id)
#
#     # 2) 찾은 객체의 데이터를 바탕으로 form을 만들어서 GET 화면에 뿌려준다.
#     # => 이 때, form에 id= 키워드를 주면, edit용 form으로 인식해서 validate를 나를 제외하고 하도록 한다
#     # form = CategoryForm(name=category.name, icon=category.icon, id=category.id)
#     form = CategoryForm(category)
#     # return render_template('admin/category_form.html', form=form, errors=errors)
#
#     # 3) form에서 달라진 데이터로 POST가 들어오면, 수정하고 커밋한다.
#     if form.validate_on_submit():
#         with DBConnectionHandler() as db:
#             category = db.session.get(Category, id)
#             # print("category>>>", category.__dict__)
#
#             category.name = form.name.data
#             category.icon = form.icon.data if len(form.icon.data) > 0 else None  # 수정form화면에서 암것도 없으면 ''이 올 것이기 때무네
#
#             db.session.add(category)
#             # print("category>>>", category.__dict__)
#             db.session.commit()
#         flash(f'{form.name.data} Category 수정 완료.')
#         return redirect(url_for('admin.category'))
#
#     # 4) 검증이 들어간 form에 대한 erros는 if form.validate_on_submit()보다 아래에 둔다.
#     errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
#
#     return render_template('admin/category_form.html', form=form, errors=errors)


@admin_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category_edit(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    # with DBConnectionHandler() as db:
    #     session = db.session
    # category = db.session.get(Category, id)
    category: Category = Category.get(id)
    form = CategoryForm(category)

    if form.validate_on_submit():
        # print('form.data  >> ', form.data)
        # {'name': 'fgasdd', 'icon': '', 'csrf_token': 'IjY2ZDkwMzcyMDg2NDcxY2M5YjEyNmQ4OThhZDhiZTg2ZjU4MmUzODQi.ZANJ-Q.iGlbT3hIDHydBI9MfvUxwysyrcY'}

        data = form.data
        if not len(data['icon']):
            data['icon'] = None

        # get/update시 각각 개별 session으로
        category: Category = Category.get(id)
        result, msg = category.update(**data)
        # with DBConnectionHandler() as db:
        #     session = db.session
        #
        #     category: Category = Category.get(id, session=session)
        #     result, msg = category.update(name=target_name, icon=target_icon,
        #                                   session=session) # commit하면,

        if result:
            success_msg = f'{category.name} {msg}'
            flash(success_msg)
            return redirect(url_for('admin.category'))

        fail_msg = f'{category.name} {msg}'
        flash(fail_msg)

    # 4) 검증이 들어간 form에 대한 erros는 if form.validate_on_submit()보다 아래에 둔다.
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/category_form.html', form=form, errors=errors)


# @admin_bp.route('/category/delete/<int:id>')
# @login_required
# @role_required(allowed_roles=[Roles.EXECUTIVE])
# def category_delete(id):
#     # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
#     with DBConnectionHandler() as db:
#         category = db.session.get(Category, id)
#         if category:
#
#             # post cascading 되기 전에, content에서 이미지 소스 가져와 삭제하기
#             if category.posts:
#                 for post in category.posts:
#                     delete_files_in_img_tag(post.content)
#
#             db.session.delete(category)
#             db.session.commit()
#             flash(f'{category.name} Category 삭제 완료.')
#             return redirect(url_for('admin.category'))


@admin_bp.route('/category/delete/<int:id>')
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category_delete(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    category = Category.load({'posts': 'subquery'}).filter_by(id=id).first()
    # post cascading 되기 전에, content에서 이미지 소스 가져와 삭제하기
    if category.posts:
        for post in category.posts:
            delete_files_in_img_tag(post.content)

    result, msg = category.delete()
    if result:
        flash(f'{result.name} Category 삭제 완료.')
    else:
        flash(f'{msg}')
    return redirect(url_for('admin.category'))


# @admin_bp.route('/category/delete2/<int:id>')
# @login_required
# def category_delete2(id):
#     # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
#     with DBConnectionHandler(echo=True) as db:
#         # category = db.session.get(Category, id)
#         #
#         # if category:
#         #     db.session.delete(category)
#         stmt = delete(Category).where(Category.id == id)
#         print(stmt)
#         db.session.execute(stmt)
#         db.session.commit()
#         # flash(f'{category.name} Category 삭제 완료.')
#         return redirect(url_for('admin.category'))

@admin_bp.route('/article')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article():
    page = request.args.get('page', 1, type=int)

    pagination = Post.load({'category':'selectin', 'tags': 'joined'}).order_by('-add_date').paginate(page, per_page=10)
    # stmt = select(Post).order_by(Post.add_date.desc())
    # pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    return render_template('admin/article.html',
                           post_list=post_list, pagination=pagination)


# @admin_bp.route('/article/add', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.STAFF])
# def article_add():
#     form = PostForm()
#
#     if form.validate_on_submit():
#         post = Post(
#             title=form.title.data,
#             desc=form.desc.data,
#             content=form.content.data,
#             # form에서 올라온 value는 coerce=int에 의해 int value가 올라오고 -> 그대로 집어넣으면, 알아서 enum필드객체로 변환된다.
#             has_type=form.has_type.data,
#             category_id=form.category_id.data,
#         )
#
#         with DBConnectionHandler() as db:
#             # 2) 다대다에 해당하는 tags를 한꺼번에 추가해줘야한다. 개별객체, append보다는 객체 list를 만들어서, 넣어주자.
#             # -> form에서 오는 data는, 숫자list가 될 것이다?
#             post.tags = [db.session.get(Tag, tag_id) for tag_id in form.tags.data]
#             db.session.add(post)
#             db.session.commit()
#         flash(f'{form.title.data} Post 생성 성공!')
#         return redirect(url_for('admin.article'))
#
#     errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
#
#     return render_template('admin/article_form.html',
#                            form=form, errors=errors)
@admin_bp.route('/article/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article_add():
    form = PostForm()
    # print('form.data  >> ', form.data)
    # form.data  >>  {'title': None, 'desc': None, 'content': None, 'has_type': 2, 'category_id': None, 'tags': None, 'csrf_token': None}
    #### => form객체로 넘어오는 데이터는, .data가 dict로 뽑아내진다
    #####   cf) form객체 없는 post의 경우, 1) HTML FORM request.form 2) AXIOS 등 request.get_json()

    if form.validate_on_submit():
        # 1. form에서 올라온 value는 coerce=int에 의해 int value가 올라오고 -> 그대로 집어넣으면, 알아서 enum필드객체로 변환된다.
        # 2. 다대다 중간테이블 -> fk 필드를 안가지고 있는데, tags에 id(int)값들이 올라왔다면 creat->field에서 말고 따로 처리를 해줘야한다.
        #   먼저 Many쪽 객체들을 다 찾은 다음, 객체.관계 ( list)에 할당해줘야한다.
        data = form.data  # 따로 안빼놓으면 수정 안됨.
        data['tags'] = [Tag.get(tag_id) for tag_id in data.get('tags', [])]
        result, msg = Post.create(**data)
        if result:
            flash(f'{result.title} Post 생성 성공!')
            return redirect(url_for('admin.article'))

        flash(f'{msg}')

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html',
                           form=form, errors=errors)


@admin_bp.route('/article/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article_edit(id):
    post = Post.filter_by(id=id).load({'category':'selectin','tags': 'joined'}).first()
    form = PostForm(post)

    if form.validate_on_submit():
        data = form.data
        data['tags'] = [Tag.get(tag_id) for tag_id in data.get('tags', [])]
        result, msg = post.update(**data)

        if result:
            flash(f'{result.title} Post 수정 완료.')
            return redirect(url_for('admin.article'))

        flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html', form=form, errors=errors)


@admin_bp.route('/article/delete/<int:id>')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article_delete(id):
    post = Post.get(id)

    # img태그 속 src를 찾아, 해당 파일 경로를 추적하여 삭제
    delete_files_in_img_tag(post.content)

    result, msg = post.delete()
    if result:
        flash(f'{post.title} Post 삭제 완료.')
    else:
        flash(msg)

    return redirect(url_for('admin.article'))


@admin_bp.route('/tag')
@login_required
def tag():
    page = request.args.get('page', 1, type=int)

    # stmt = select(Tag).order_by(Tag.add_date.desc())
    # pagination = paginate(stmt, page=page, per_page=10)
    pagination = Tag.order_by('-add_date').paginate(page, per_page=10)

    tag_list = pagination.items

    return render_template('admin/tag.html',
                           tag_list=tag_list, pagination=pagination)


@admin_bp.route('/tag/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def tag_add():
    form = TagForm()

    if form.validate_on_submit():
        result, msg = Tag.create(**form.data)
        if result:
            flash(f'{form.name.data} Tag 생성 성공!')
            return redirect(url_for('admin.tag'))

        flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/tag_form.html', form=form, errors=errors)


@admin_bp.route('/tag/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def tag_edit(id):
    tag = Tag.get(id)

    form = TagForm(tag)
    if form.validate_on_submit():
        result, msg = tag.update(**form.data)

        if result:
            flash(f'{tag} {msg}')
            return redirect(url_for('admin.tag'))
        flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/tag_form.html', form=form, errors=errors)


@admin_bp.route('/tag/delete/<int:id>')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def tag_delete(id):
    tag = Tag.get(id)
    result, msg = tag.delete()
    if result:
        flash(f'{tag} {msg}')
    else:
        flash(msg)
    return redirect(url_for('admin.tag'))


@admin_bp.route('/user')
@login_required
def user():
    page = request.args.get('page', 1, type=int)

    # stmt = select(User).order_by(User.add_date.desc())
    # ~User.is_staff => only user
    # stmt = select(User) \
    #     .where(~User.is_staff) \
    #     .order_by(User.add_date.desc())

    pagination = User.load({'role': 'selectin'}).filter_by(is_staff=False).order_by('-add_date').paginate(page,
                                                                                                          per_page=10)

    # pagination = paginate(stmt, page=page, per_page=10)
    user_list = pagination.items

    #### 직원초대시 modal에 띄울 role_list를 건네주기
    # with DBConnectionHandler() as db:
    #     role_list = db.session.scalars(
    #         select(Role)
    #         .where(Role.is_(Roles.STAFF))  # 상수 STAFF이상이면서
    #         .where(Role.is_under(g.user.role))  # Role객체의 permissions가 현재 직원의 Roles보다는 적게
    #     ).all()
    # print(role_list) # [<Role 'STAFF'>, <Role 'DOCTOR'>, <Role 'CHIEFSTAFF'>, <Role 'EXECUTIVE'>]
    role_list = Role.filter_by(is_=Roles.STAFF, is_under=g.user.role).all()
    # print('role_list  >> ', role_list)
    # role_list  >>  [<Role 'STAFF'>, <Role 'DOCTOR'>, <Role 'CHIEFSTAFF'>, <Role 'EXECUTIVE'>]

    return render_template('admin/user.html',
                           user_list=user_list, pagination=pagination,
                           role_list=role_list
                           )


# @admin_bp.route('/user/add', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def user_add():
#     # form = CreateUserForm(g.user)
#     form = CreateUserForm()
#
#     # with DBConnectionHandler() as db:
#     #     roles = db.session.scalars(select(Role).where(Role.permissions < g.user.role.permissions)).all()
#     # self.role_id.choices = [(role.id, role.name) for role in roles]
#     # form.role_id.choices = [(role.id, role.name) for role in roles if role.name != Roles.ADMINISTRATOR.name]
#
#     if form.validate_on_submit():
#         # print('form.data  >> ', form.data)
#         # form.data  >>  {'username': 'user추가', 'password': '1234', 'email': '123123@123123.com', 'is_super_user': False, 'is_active': True, 'is_staff': False, 'avatar': None,
#         # 'csrf_token': 'IjY2ZDkwMzcyMDg2NDcxY2M5YjEyNmQ4OThhZDhiZTg2ZjU4MmUzODQi.ZAN_2w.m7BcXt-rUEHVHKXd-5DqubEof40'}
#
#         # print("boolean은 체크되면 뭐로 넘어오나", form.is_super_user.data)
#         # -> BooleanField는 value는 'y'로 차있지만, check되면 True로 넘어온다
#         user = User(
#             username=form.username.data,
#             # 3) password는 hash로 만들어서 넣어야한다.
#             # password=generate_password_hash(form.password.data),
#             password=form.password.data,
#             email=form.email.data,
#             # 4) db에 저장한 update된 '개별폴더/filename'으로 한다.
#             #  -> file이 없는 경우를 대비해서 setter형식으로 넣어주자.
#             # avatar=f'avatar/{filename}',
#             is_active=form.is_active.data,
#             # is_super_user=form.is_super_user.data,
#             # is_staff=form.is_staff.data,
#             ### is_staff필드가가 hybrid_property랑 동일해서 결국 지우든지 바꿔야함.
#         )
#
#         # 1) file 업로드 관련 유틸을 import한뒤,
#         #   form에서 받은 file객체f 를 통해 -> 저장full경로 + filename만 반환받는다.
#         f = form.avatar.data
#         if f:
#             avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
#             # print(f"avatar_path, filename >>> {avatar_path, filename}")
#             # 2) f(file객체)를 .save( 저장경로 )로 저장한다.
#             f.save(avatar_path)
#             user.avatar = f'avatar/{filename}'
#
#         with DBConnectionHandler() as db:
#             db.session.add(user)
#             db.session.commit()
#
#         flash(f'{form.username.data} User 생성 성공!')
#         return redirect(url_for('admin.user'))
#
#     errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
#
#     return render_template('admin/user_form.html', form=form, errors=errors)


@admin_bp.route('/user/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def user_add():
    form = CreateUserForm()

    if form.validate_on_submit():
        # print('form.data  >> ', form.data)
        # form.data  >>  {'username': 'user추가', 'password': '1234', 'email': '123123@123123.com', 'is_super_user': False, 'is_active': True, 'is_staff': False, 'avatar': None,
        # 'csrf_token': 'IjY2ZDkwMzcyMDg2NDcxY2M5YjEyNmQ4OThhZDhiZTg2ZjU4MmUzODQi.ZAN_2w.m7BcXt-rUEHVHKXd-5DqubEof40'}
        data = form.data
        data = {key: value for key, value in data.items() if
                key in ['username', 'password', 'email', 'is_active', 'avatar']}
        if data.get('avatar'):
            avatar_file = data.get('avatar')
            avatar_path, filename = upload_file_path(directory_name='avatar', file=avatar_file)
            avatar_file.save(avatar_path)
            data['avatar'] = f'avatar/{filename}'

        result, msg = User.create(**data)
        if result:
            flash(f'{result.username} User 생성 성공!')
            return redirect(url_for('admin.user'))

        flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)


# @admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def user_edit(id):
#     with DBConnectionHandler() as db:
#         user = db.session.get(User, id)
#
#     # form = CreateUserForm(g.user, user=user)
#     # 더이상 User관리에서 직접 역할 주기위한 직원g.user를 집어넣지 않는다.
#     form = CreateUserForm(user=user)
#
#     if form.validate_on_submit():
#         # username은 수정못하게 걸어놧으니 pasword부터 처리한다.
#         # password는 데이터가 들어온 경우만 -> hash걸어서 저장한다.
#         # print(f"form.password.data>>>{form.password.data}")
#         if form.password.data:
#             # user.password = generate_password_hash(form.password.data)
#             user.password = form.password.data
#         # avatar의 경우, 현재 db필드인 'avatar/파일명'이 data로 들어가있지만,
#         # -> 파일명(기존 user.avatar값과 동일)이 아닌 file객체가data로 온 경우만, 새롭게 upload하는 처리를 해준다.
#         f = form.avatar.data
#         # print(f"f>>>{f}")
#         if f != user.avatar:
#             avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
#             f.save(avatar_path)
#
#             # user.avatar 덮어쓰기 전에, db에 저장된 경로를 바탕으로 -> upload폴더에서 기존 file삭제
#             # -> 기존 user.avatar에 암것도 없어도 안에서 바로 종료되도록 예외처리
#             delete_uploaded_file(directory_and_filename=user.avatar)
#
#             user.avatar = f'avatar/{filename}'
#
#         # 나머지 필드도 변경
#         user.email = form.email.data
#         user.role_id = form.role_id.data
#         user.is_active = form.is_active.data
#         # user.is_super_user = form.is_super_user.data
#         # user.is_staff = form.is_staff.data
#
#         with DBConnectionHandler() as db:
#             db.session.add(user)
#             db.session.commit()
#
#         flash(f'{form.username.data} User 수정 완료.')
#         return redirect(url_for('admin.user'))
#
#     errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
#
#     return render_template('admin/user_form.html', form=form, errors=errors)

@admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def user_edit(id):
    user = User.get(id)
    form = CreateUserForm(user=user)

    if form.validate_on_submit():
        data = form.data
        data = {key: value for key, value in data.items() if
                key in ['password', 'email', 'is_active', 'avatar', 'role_id']}
        if not data.get('password', None):
            del data['password']
        if data.get('avatar') and user.avatar != data.get('avatar'):
            avatar_file = data.get('avatar')
            avatar_path, filename = upload_file_path(directory_name='avatar', file=avatar_file)
            avatar_file.save(avatar_path)

            delete_uploaded_file(directory_and_filename=user.avatar)

            data['avatar'] = f'avatar/{filename}'

        result, msg = user.update(**data)

        if result:
            flash(f'{result} User 수정 완료.')
            return redirect(url_for('admin.user'))
        flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)


@admin_bp.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def user_delete(id):
    user = User.get(id)
    delete_uploaded_file(directory_and_filename=user.avatar)
    result, msg = user.delete()
    if result:
        flash(f'{result} {msg}')
    else:
        flash(msg)
    return redirect(url_for('admin.user'))


@admin_bp.route('/banner')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner():
    page = request.args.get('page', 1, type=int)

    pagination = Banner.order_by('-is_fixed', '-add_date').paginate(page=page, per_page=10)
    banner_list = pagination.items

    return render_template('admin/banner.html',
                           banner_list=banner_list, pagination=pagination)


@admin_bp.route('/banner/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner_add():
    form = BannerForm()

    if form.validate_on_submit():
        data = form.data
        data = {key: value for key, value in data.items() if
                key in ['img', 'banner_type', 'is_fixed', 'desc', 'url']}
        img_file = data.get('img')
        if img_file:
            banner_path, filename = upload_file_path(directory_name='banner', file=img_file)
            img_file.save(banner_path)
            data['img'] = f'banner/{filename}'

        result, msg = Banner.create(**data)
        if result:
            flash(f'{result} {msg}')
            return redirect(url_for('admin.banner'))

        flash(msg)

    return render_template('admin/banner_form.html', form=form)


@admin_bp.route('/banner/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner_edit(id):
    banner = Banner.get(id)
    form = BannerForm(banner)

    if form.validate_on_submit():
        data = form.data
        data = {key: value for key, value in data.items() if
                key in ['img', 'banner_type', 'is_fixed', 'desc', 'url']}

        # 수정안되서 경로 그대로 오는지 vs 새 파일객체가 오는지 구분
        img_file = data.get('img')
        if img_file and img_file != banner.img:
            banner_path, filename = upload_file_path(directory_name='banner', file=img_file)
            img_file.save(banner_path)
            delete_uploaded_file(directory_and_filename=banner.img)
            data['img'] = f'banner/{filename}'

        # 나머지 필드도 변경
        result, msg = banner.update(**data)
        if result:
            flash(f'{result} Banner 수정 완료.')
            return redirect(url_for('admin.banner'))

        flash(msg)

    return render_template('admin/banner_form.html', form=form)


@admin_bp.route('/banner/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner_delete(id):
    banner = Banner.get(id)
    # 필드에 file을 가지고 있는 entity는 file도 같이 삭제한다.
    delete_uploaded_file(directory_and_filename=banner.img)
    result, msg = banner.delete()
    if result:
        flash(f'{result} {msg}')
    else:
        flash(msg)
        return redirect(url_for('admin.banner'))


@admin_bp.route('/setting', methods=['GET'])
@login_required
@role_required(allowed_roles=[Roles.ADMINISTRATOR])
def setting():
    s_dict = Setting.convert_to_dict()

    # db객체 list대신 dict를 건네준다.
    # return render_template('admin/setting.html', s_dict=s_dict, active_tab=1)
    return render_template('admin/setting.html', s_dict=s_dict)


@admin_bp.route('/setting/edit', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.ADMINISTRATOR])
def setting_edit():
    s_dict = Setting.convert_to_dict()
    form = SettingForm(s_dict)
    # print(s_dict)

    if form.validate_on_submit():
        # with DBConnectionHandler() as db:
        # 1) form의 to_dict메서드를 활용하여, form 모든 정보를 key, value로서 순회할 수 있게 한다
        return_s_dict = form.to_dict()

        # print(return_s_dict)
        # print(return_s_dict['start_date'], type(return_s_dict['start_date']))
        # Thu Nov 03 2022 00:00:00 GMT+0900 (한국 표준시) <class 'str'>

        #### 파일업로드 처리 -> dict를 하나씩 보기 전에 처리, dict의 key에 할당
        f = return_s_dict["logo"]
        # 수정안되서 경로 그대로 오는지 vs 새 파일객체가 오는지 구분
        # 최초 수정시에는  db에 logo key가 아예 없을 수 있기 때문에 s_dict는 get으로 얻어오기
        if f != s_dict.get("logo", None):
            logo_path, filename = upload_file_path(directory_name='logo', file=f)
            f.save(logo_path)

            delete_uploaded_file(directory_and_filename=s_dict.get("logo", None))

            return_s_dict["logo"] = f'logo/{filename}'

        for key, value in return_s_dict.items():

            # 1) 각 key,value는 1row로서 Setting의 1개의 객체에 해당하므로
            #    setting객체를 만들어 입력할텐데,
            #    1-1) [이미 꺼냈떤 s_dict에서 이미 존재하는 key]이면 => 조회후 객체필드 변경(update)
            #    1-2) 없던 key는 새객체만들어서 add를 나눠서 해준다.
            if key in s_dict:
                # print(key, "는 이미 존재인데")
                # setting = Setting.get_by_key(key)
                setting = Setting.filter_by(setting_key=key).first()
                # 1-1-2) 이미 존재해서 꺼냈을 때 값을 비교해서 다르면 업데이트
                if setting.setting_value == value:
                    # print(key, "같은 값이라서 continue")
                    continue
                else:
                    # print(key, "값이 달라져서 update")
                    setting.setting_value = value
                    #### 객체 필드변경후 commit만 하면 자동반영X -> session이 달라서
                    #### => 수정이든, 새로생성이든 아래에서 공통적으로 session.add()해야함.

            else:
                # print(key, "없어서  새로 생성 -> value가 None이도 None으로 넣을 것임.")
                # setting = Setting(
                #     setting_key=key,
                #     setting_value=value
                # )
                result, _ = Setting.create(setting_key=key, setting_value=value)

        flash(f'세팅 수정 완료.')

        return redirect(url_for('admin.setting'))

    return render_template('admin/setting_form.html', form=form)


@admin_bp.route('/employee')
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee():
    page = request.args.get('page', 1, type=int)

    # stmt = select(User) \
    #     .where(User.is_staff) \
    #     .order_by(User.add_date.desc())
    #### employee정보를 기준으로 직원관리를 표시하려면 User에서 골라내는게 아니라, Employee중에서 골라야한다.
    #### - Employee도 대기상태 or 퇴사상태 데이터가 있기 때문에, 필터링을 한번 해야한다
    # stmt = select(Employee) \
    #     .order_by(Employee.join_date.desc())
    # .where(Employee.is_active) \

    pagination = Employee.load({'user': ('selectin', {'role': 'selectin'})}).order_by('-join_date').paginate(page,
                                                                                                             per_page=10)
    employee_list = pagination.items

    #### 재직상태변경 modal 속 select option 추가로 내려보내기
    job_status_list = JobStatusType.choices()
    # print(job_status_list)
    # [(1, '재직'), (2, '휴직'), (3, '퇴사')]
    #### => 여기서만 재직 = 1을 복직으로 변경해서 내려주자. (form에서는 재직으로?)
    job_status_list = job_status_list[1:] + [(1, '복직')]
    # [(2, '휴직'), (3, '퇴사') (1, '복직')]

    return render_template('admin/employee.html',
                           employee_list=employee_list,
                           pagination=pagination,
                           job_status_list=job_status_list
                           )


# @admin_bp.route('/employee/add/<int:user_id>', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def employee_add(user_id):
#     user = User.get_by_id(user_id)
#     # form = EmployeeForm(user, employer=g.user) # 고용주인 현재유저를 form내부에서 g.user로 쓰고 인자에서 삭제
#     form = EmployeeForm(user)
#
#     if form.validate_on_submit():
#         # User정보와 Employee정보를 따로 분리해서 각각 처리한다.
#
#         #### user ####
#         # - 직원으로 변환되면, user의 role부터 미리 선택된 것으로 바뀌어야한다.
#         user_info = {
#             'email': form.email.data,
#             'sex': form.sex.data,
#             'phone': form.phone.data,
#             'address': form.address.data,
#
#             'role_id': form.role_id.data,
#         }
#         user.update2(user_info)
#
#         f = form.avatar.data
#         if f != user.avatar:
#             avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
#             f.save(avatar_path)
#             delete_uploaded_file(directory_and_filename=user.avatar)
#             user.avatar = f'avatar/{filename}'
#
#         #### employee ####
#         # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
#         employee = Employee(
#             user=user,
#             name=form.name.data,
#             sub_name=form.sub_name.data,
#             birth=form.birth.data,
#             join_date=form.join_date.data,
#             # job_status는 form에는 존재하지만, 생성시에는 view에 안뿌린다. 대신 default값이 들어가있으니, 그것으로 재직되게 한다?
#             job_status=form.job_status.data,
#             # resign_date는 deafult값없이 form필드에도 명시안한다
#         )
#
#         flash("직원 전환 성공")
#         with DBConnectionHandler() as db:
#             db.session.add(user)
#             db.session.add(employee)
#             db.session.commit()
#
#         return redirect(url_for('admin.employee'))
#
#     return render_template('admin/employee_form.html',
#                            form=form
#                            )
@admin_bp.route('/employee/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_add(user_id):
    # user = User.get(user_id)
    # 재입사인지 확인을 위해, employee까지 load해서 None이면 신규입사, 아니면 재입사다
    user = User.load({'employee':'selectin'}).filter_by(id=user_id).first()

    # 재입사인 경우, 수정form으로 인식되도록 employee=넣어주기
    # -> uselist relation이 데이터가 없으면 조회시 None으로 들어감. -> 내부에서 없는 것으로 취급
    user_employee = user.employee
    form = EmployeeForm(user, employee=user_employee)

    if form.validate_on_submit():
        # User정보와 Employee정보를 따로 분리해서 각각 처리한다.
        data = form.data

        #### user ####
        # - 여러개의 role이 아니라 1개의 role만 올라오므로 role relation을 불러올 필요는 없다
        user_data = {key: value for key, value in data.items() if
                     key in ['email', 'sex', 'phone', 'address', 'role_id', 'avatar']}

        if user_data.get('avatar') and user.avatar != user_data.get('avatar'):
            avatar_file = user_data.get('avatar')
            avatar_path, filename = upload_file_path(directory_name='avatar', file=avatar_file)
            avatar_file.save(avatar_path)
            delete_uploaded_file(directory_and_filename=user.avatar)
            user_data['avatar'] = f'avatar/{filename}'

        # - 직원으로 변환되면, user의 role부터 미리 선택된 것으로 바뀌어야한다.
        user.fill(**user_data)

        #### employee (재입사vs신규입사)####
        # 1) employee relation이 존재함 -> 재입사 -> employee Update
        #    달라질 수 있는 기본정보 VS 입사와 동일한 고정정보
        if user_employee:
            user_employee.fill(
                # 재입사시 바뀔 수도 있는 정보(이미 form이 수정형으로서 채워져 있음)
                name=form.name.data,
                sub_name=form.sub_name.data,
                birth=form.birth.data,
                join_date=form.join_date.data,
                # 재입사시 고정적인 부분 => 재직1 상태변경/퇴직일/휴직일 비우기
                job_status=JobStatusType.재직.value,  # 재입사시 고정
                resign_date=None,
                leave_date=None,
            )
            # 특별한 fill
            user_employee.fill_reference(f'재입사({format_date(form.join_date.data)})')
            # employee정보를 main obj인 user에 fill

        # 2) employee relation조회시 None -> 신규입사 -> employee Create
        else:
            # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
            # job_status는 form에는 존재하지만, 생성시에는 view에 안뿌린다. 대신 default값이 들어가있으니, 그것으로 재직되게 한다?
            # resign_date는 default값 없이 form필드에도 명시안한다
            employee_data = {key: value for key, value in data.items() if
                             key in ['name', 'sub_name', 'birth', 'join_date', 'job_status']}
            employee_data['user'] = user  # 수정된 relation user정보를 fill해서 main obj에서 한번에 수정 반영

            user_employee, msg = Employee.create(
                **employee_data,
                reference=f'신규입사({format_date(form.join_date.data)})'
            )
            if not user_employee:
                flash(msg)
                return redirect(url_for('admin.employee'))

        # 완성된 employee정보를 main이 user의 relation에 전달
        user.fill(employee=user_employee)
        result, msg = user.update()
        if result:
            flash("직원 전환 성공", category='is-info')
        else:
            flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
    return render_template('admin/employee_form.html', form=form, errors=errors)


# @admin_bp.route('/invite/employee/<int:user_id>', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def employee_invite(user_id):
#     print(request.form)
#     if request.method == "POST":
#         print("post>>>", request.form.get('role_id'), request.form.get('user_id'))
#     #### 초대 존재 여부는
#     # 1) 현재 초대Type(상위 주제entity)에 대해서만 검색해야한다,(초대 Type이 다르면 또 보낼 수 있음)
#     # 2) *응답(수락/거절)되서 삭제된 것외에 만료된 것을 제외하고 검색해야한다.(만료되면 또 보낼 수 있음)
#     # 3) 검색시에는, 보내는사람과 받는사람을 필터링하면 된다. 관계테이블이므로, 관계객체.has()/any() - 데이터존재검사 + 추가조건을 건다
#     with DBConnectionHandler() as db:
#         inviter = g.user
#         invitee = db.session.get(User, user_id)
#         # 존재여부 확인 -> 연결된 타테이블 확인은  select 주체,  where 주체.관계객체.any[존재조건]( 관계객체.필드 == [추가조건])
#         # - 주체가 Many(Invite)면, has()로 exitst절을 만든다.
#         # - 데이터 존재유무는 select절에 주체entity를 fun.count()에 씌워서 db.session.scalar()로 count를 가져올 수 있찌만, 우리는 T/F만 잇으면 되므로
#         # or
#         # - select exists()문은 subquery로서만 활용되며,
#         #   - extist().where() 후 .select()를 붙여서 -> scalars( ).one() -> .scalar()로 가져오면 T/F가 반환된다.
#         stmt = (
#             ### 관계칼럼으로 검사하기 전에, EmployeeInvite를 주entity로 만들어줄 걸어줄 조건 or 없다면 select_from()으로 잡아주기
#             # exists()
#             # .where(Invite.type == InviteType.직원_초대)
#             exists()
#             .select_from(EmployeeInvite)  # exists()조건들을 WHERE에 담을 주 entity(left)
#             .where(EmployeeInvite.inviter.has(User.id == inviter.id))
#             .where(EmployeeInvite.invitee.has(User.id == invitee.id))
#             # e
#             .where(EmployeeInvite.is_not_expired)
#
#             .select()
#         )
#         # print(stmt)
#         # SELECT EXISTS (SELECT *
#         # FROM invites
#         # WHERE invites.type = :type_1 AND (EXISTS (SELECT 1
#         # FROM users
#         # WHERE users.id = invites.inviter_id AND users.id = :id_1)) AND (EXISTS (SELECT 1
#         # FROM users
#         # WHERE users.id = invites.invitee_id AND users.id = :id_2))) AS anon_1
#         is_invite_exists = db.session.scalar(stmt)
#         # print(is_invite_exists)
#         # True
#
#         if is_invite_exists:
#             flash(f"{invitee.username}에게 이미 직원초대를 보냈습니다.", category="is-danger")
#         else:
#             role_staff = db.session.scalars(select(Role).where(Role.name == 'STAFF')).first()
#
#             invite = EmployeeInvite(
#                 inviter=inviter,
#                 invitee=invitee,
#                 role=role_staff,
#             )
#
#             db.session.add(invite)
#             db.session.commit()
#
#             flash(f"{invitee.username}에게 직원초대({role_staff.name})를 보냈습니다.", category='is-success')
#
#     return redirect(url_for('admin.user'))

@admin_bp.route('/invite/employee/', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_invite():
    role_id = request.form.get('role_id', type=int)
    user_id = request.form.get('user_id', default=None, type=int)

    #### 초대 존재 여부는
    # 1) 현재 초대Type(상위 주제entity)에 대해서만 검색해야한다,(초대 Type이 다르면 또 보낼 수 있음)
    # 2) *응답(수락/거절)되서 삭제된 것외에 만료된 것을 제외하고 검색해야한다.(만료되면 또 보낼 수 있음)
    # 3) 검색시에는, 보내는사람과 받는사람을 필터링하면 된다. 관계테이블이므로, 관계객체.has()/any() - 데이터존재검사 + 추가조건을 건다
    # 4) 만료되지 않는 것에 대해서만 존재검사를 한다.
    # 5) *추후 answer안된 것들만 검사한다
    # inviter = g.user
    # invitee = User.get(user_id)
    data = dict(
        inviter=g.user,
        invitee=User.get(user_id)
    )

    # eagerload할 필요가 없기 때문에, hybrid_method로 exsists를 만들어 relation 필터링한다.
    # is_invite_exists = EmployeeInvite \
    #     .filter_by(and_=dict(is_valid=True, inviter___id=inviter.id, invitee___id=invitee.id)) \
    #     .exists()
    is_invite_exists = EmployeeInvite \
        .filter_by(**data, is_valid=True) \
        .exists()

    if is_invite_exists:
        flash(f"{data['invitee'].username}에게 이미 직원초대를 보냈습니다.", category="is-danger")
    else:
        role = Role.filter_by(id=role_id).first()

        result, msg = EmployeeInvite.create(**data, role=role)
        if result:
            flash(f"{data['invitee'].username}에게 직원초대({role.name})를 보냈습니다.", category='is-success')
        else:
            flash(msg)

    # return redirect(url_for('admin.user'))
    return redirect(redirect_url())


# @admin_bp.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def employee_edit(id):
#     # 1) user기본정보는, employee 1:1 subquery로서 바로 찾을 수 있기 때문에 조회는 생략한다.
#     # employee화면에서는, employee id를 보내주기 때문에 user_id와 별개로 id로 찾는다.
#     with DBConnectionHandler() as db:
#         employee = db.session.get(Employee, id)
#     # 2) employeeForm이 수정form일땐, role선택여부를 위해 g.user가 고용주로 들어가며
#     #   기본정보인 user정보를 채우기 위해, user도 들어간다.
#
#     #### 직원관련 수정 등은, role구성이 자신이하로만 구성되므로, 조건을 확인하여, 아니면 돌려보내보자
#     if not employee.user.role.is_under(g.user.role):
#         flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
#         return redirect(redirect_url())
#
#     # 항상 수정form을 만드는 user / employform의 수정form인 employee= / role이 1개가 아니라, g.user이하의 role을 만드는 employer=
#     form = EmployeeForm(employee.user, employee=employee)
#
#     # print("form.join_date.data >>>", form.join_date.data)
#
#     if form.validate_on_submit():
#         #### user ####
#         user_info = {
#             'email': form.email.data,
#             'sex': form.sex.data,
#             'phone': form.phone.data,
#             'address': form.address.data,
#
#             'role_id': form.role_id.data,
#         }
#         user = employee.user
#         user.update2(user_info)
#
#         f = form.avatar.data
#         if f != user.avatar:
#             avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
#             f.save(avatar_path)
#             delete_uploaded_file(directory_and_filename=user.avatar)
#             user.avatar = f'avatar/{filename}'
#
#         #### employee ####
#         employee_info = {
#             'name': form.name.data,
#             'sub_name': form.sub_name.data,
#             'birth': form.birth.data,
#             'join_date': form.join_date.data,
#             'job_status': form.job_status.data,
#             #### 수정된 user객체를 넣어준다
#             'user': user,
#             #### 생성시에 없었던, job_status와, resign_date를 넣어준다
#             # 'job_status': form.job_status.data,
#             # 'resign_date': form.resign_date.data,
#         }
#
#         employee.update2(employee_info)
#
#         with DBConnectionHandler() as db:
#             db.session.add(employee)
#             db.session.commit()
#             # print(employee.user.role_id)
#             flash("직원 수정 성공", category='is-success')
#             print('employee  >> ', employee.name)
#
#         return redirect(url_for('admin.employee'))
#
#     return render_template('admin/employee_form.html',
#                            form=form
#                            )

# @admin_bp.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def employee_edit(id):
#     # 1) user기본정보는, employee 1:1 subquery로서 바로 찾을 수 있기 때문에 조회는 생략한다.
#     # employee화면에서는, employee id를 보내주기 때문에 user_id와 별개로 id로 찾는다.
#     with DBConnectionHandler() as db:
#         employee = db.session.get(Employee, id)
#     # 2) employeeForm이 수정form일땐, role선택여부를 위해 g.user가 고용주로 들어가며
#     #   기본정보인 user정보를 채우기 위해, user도 들어간다.
#
#     #### 직원관련 수정 등은, role구성이 자신이하로만 구성되므로, 조건을 확인하여, 아니면 돌려보내보자
#     if not employee.user.role.is_under(g.user.role):
#         flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
#         return redirect(redirect_url())
#
#     # 항상 수정form을 만드는 user / employform의 수정form인 employee= / role이 1개가 아니라, g.user이하의 role을 만드는 employer=
#     form = EmployeeForm(employee.user, employee=employee)
#
#     # print("form.join_date.data >>>", form.join_date.data)
#
#     if form.validate_on_submit():
#         #### user ####
#         user_info = {
#             'email': form.email.data,
#             'sex': form.sex.data,
#             'phone': form.phone.data,
#             'address': form.address.data,
#
#             'role_id': form.role_id.data,
#         }
#         user = employee.user
#         user.update2(user_info)
#
#         f = form.avatar.data
#         if f != user.avatar:
#             avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
#             f.save(avatar_path)
#             delete_uploaded_file(directory_and_filename=user.avatar)
#             user.avatar = f'avatar/{filename}'
#
#         #### employee ####
#         employee_info = {
#             'name': form.name.data,
#             'sub_name': form.sub_name.data,
#             'birth': form.birth.data,
#             'join_date': form.join_date.data,
#             'job_status': form.job_status.data,
#             #### 수정된 user객체를 넣어준다
#             'user': user,
#             #### 생성시에 없었던, job_status와, resign_date를 넣어준다
#             # 'job_status': form.job_status.data,
#             # 'resign_date': form.resign_date.data,
#         }
#
#         employee.update2(employee_info)
#
#         with DBConnectionHandler() as db:
#             db.session.add(employee)
#             db.session.commit()
#             # print(employee.user.role_id)
#             flash("직원 수정 성공", category='is-success')
#             print('employee  >> ', employee.name)
#
#         return redirect(url_for('admin.employee'))
#
#     return render_template('admin/employee_form.html',
#                            form=form
#                            )

@admin_bp.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_edit(id):
    # 1) user기본정보는, employee 1:1 subquery로서 바로 찾을 수 있기 때문에 조회는 생략한다.
    # employee화면에서는, employee id를 보내주기 때문에 user_id와 별개로 id로 찾는다.
    # with DBConnectionHandler() as db:
    #     employee = db.session.get(Employee, id)
    # 아래에 보니, 기본적으로 employee는 user.role까지 터치한다.
    # employee = Employee.get(id)
    employee = Employee.load({'user': ('selectin', {'role': 'selectin'})}) \
        .filter_by(id=id).first()

    # 2) employeeForm이 수정form일땐, role선택여부를 위해 g.user가 고용주로 들어가며
    #   기본정보인 user정보를 채우기 위해, user도 들어간다.

    #### 직원관련 수정 등은, role구성이 자신이하로만 구성되므로, 조건을 확인하여, 아니면 돌려보내보자
    if not employee.user.role.is_under(g.user.role):
        flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
        return redirect(redirect_url())

    # 항상 수정form을 만드는 user / employform의 수정form인 employee= / role이 1개가 아니라, g.user이하의 role을 만드는 employer=
    form = EmployeeForm(employee.user, employee=employee)

    if form.validate_on_submit():
        data = form.data
        #### user ####
        user_data = {key: value for key, value in data.items() if
                     key in ['email', 'sex', 'phone', 'address', 'role_id', 'avatar']}
        user = employee.user
        if user_data.get('avatar') and user.avatar != user_data.get('avatar'):
            avatar_file = user_data.get('avatar')
            avatar_path, filename = upload_file_path(directory_name='avatar', file=avatar_file)
            avatar_file.save(avatar_path)
            delete_uploaded_file(directory_and_filename=user.avatar)
            user_data['avatar'] = f'avatar/{filename}'

        # - 직원으로 변환되면, user의 role부터 미리 선택된 것으로 바뀌어야한다.
        user.fill(**user_data)

        #### employee ####
        # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
        # job_status는 form에는 존재하지만, 생성시에는 view에 안뿌린다. 대신 default값이 들어가있으니, 그것으로 재직되게 한다?
        # resign_date는 default값 없이 form필드에도 명시안한다
        employee_data = {key: value for key, value in data.items() if
                         key in ['name', 'sub_name', 'birth', 'join_date', 'job_status']}
        employee_data['user'] = user  # 수정된 user정보를 넣어서 수정해준다.

        result, msg = employee.update(**employee_data)

        if result:
            flash(f'{result} {msg}')
            return redirect(url_for('admin.employee'))

        flash(msg)

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
    return render_template('admin/employee_form.html', form=form, errors=errors)


# @admin_bp.route('/employee/job_status', methods=['POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def employee_job_status_change():
#     # print('request.form.to_dict()  >> ', request.form.to_dict())
#     # request.form.to_dict()  >>  {'employee_id': '9', 'job_status': '1', 'date': '2023-03-06'}
#
#     employee_id = request.form.get('employee_id', type=int)
#     job_status = request.form.get('job_status', type=int)
#     target_date = request.form.get('date',
#                                    type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
#                                    )
#
#     with DBConnectionHandler() as db:
#         employee = db.session.get(Employee, employee_id)
#
#         if not employee.role.is_under(g.user.role):
#             flash('자신보다 하위 직위의 직원만 수정할 수 있습니다.', category='is-danger')
#             return redirect(redirect_url())
#
#         #### 퇴사자는 재직상태 변경 못하고, 직원초대로만 가능하도록 early return
#         if employee.job_status == JobStatusType.퇴사:
#             flash(f'퇴사자는 재직상태변경이 불가하며 User관리에서 직원초대로 새로 입사해야합니다. ', category='is-danger')
#             return redirect(redirect_url())
#
#         #### new => 퇴직은 입사일보다 더 이전에는 할 수 없도록 검사하기
#         if job_status == JobStatusType.퇴사 and target_date < employee.join_date:
#             flash(f'입사일보다 더 이전으로 퇴사할 수 없습니다. ', category='is-danger')
#             return redirect(redirect_url())
#
#         #### 복직은 휴직자만 가능하도록 걸기
#         if job_status == JobStatusType.재직 and employee.job_status != JobStatusType.휴직:
#             flash(f'복직은 휴직자만 선택할 수 있습니다. ', category='is-danger')
#             return redirect(redirect_url())
#
#         #### new => 복직은 최종 휴직일(in emp)보다 더 이전에는 할 수 없도록 검사하기
#         if job_status == JobStatusType.재직 and target_date < employee.leave_date:
#             flash(f'휴직일보다 더 이전으로 복직할 수 없습니다. ', category='is-danger')
#             return redirect(redirect_url())
#
#         #### 이미 해당 재직상태인데 같은 것으로 변경하는 것을 막기 위한 처리문
#         # => 이것을 처리해줘야 emp.user.role  <-> Role.get_by_name('USER')시 session내 같은 객체 조회를 막을 수 있다
#         if employee.job_status == job_status:
#             flash(f'같은 상태로 변경할 수 없습니다. ', category='is-danger')
#             return redirect(redirect_url())
#
#     # Employee.change_job_status(employee_id, job_status)
#     Employee.change_job_status(employee_id, job_status, target_date)
#     flash(f'재직상태변경이 완료되었습니다.', category='is-success')
#
#     # flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
#
#     # #### 퇴사처리1) 직원의 재직상태를 퇴사로 변경
#     # employee.job_status = job_status
#     # if job_status == JobStatusType.퇴사:
#     #     #### 퇴사처리 메서드로 구현(job_status-외부 + resign_date-내부 + role(default인 USER)-내부 변경
#     #     #### => 재직상태는 외부에서 주는 것이라 인자로 받아서 처리?!
#     #     employee.change_status(job_status)
#     #
#     #     #### 퇴사처리2) 직원의 퇴직일(resign_date)가 찍히게 된다.
#     #     employee.resign_date = date.today()
#     #
#     #     #### 퇴사처리3) 직원의 Role을 STAFF이상 => User(deafult=True)로 변경한다.
#     #     # 퇴사처리시 role을 user로 다시 바꿔, 직원정보는 남아있되, role이 user라서 접근은 못하게 한다
#     #     role = db.session.scalars(
#     #         select(Role)
#     #         .where(Role.default == True)
#     #     ).first()
#     #     employee.user.role = role
#     #
#     #
#     # db.session.add(employee)
#     # db.session.commit()
#
#     return redirect(redirect_url())

@admin_bp.route('/employee/job_status', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_job_status_change():
    # print('request.form.to_dict()  >> ', request.form.to_dict())
    # request.form.to_dict()  >>  {'employee_id': '9', 'job_status': '1', 'date': '2023-03-06'}

    employee_id = request.form.get('employee_id', type=int)
    job_status = request.form.get('job_status', type=int)
    target_date = request.form.get('date',
                                   type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
                                   )

    # employee = Employee.load({'user': ('selectin', {'role': 'selectin'})}).filter_by(id=employee_id).first()
    employee = Employee.load({'user': ('selectin', {'role': 'selectin'}),
                              'employee_departments': 'joined',
                              }) \
        .filter_by(id=employee_id).first()

    employee_role = employee.user.role

    #### 기본 검증
    # 1) 날짜의 유효성 검증 (퇴사 > 입사일)
    if JobStatusType.is_resign(job_status) and target_date < employee.join_date:
        flash(f'입사일보다 더 이전으로 퇴사할 수 없습니다. ', category='is-danger')
        return redirect(redirect_url())

    # 2) 같은 상태로의 변환
    if employee.job_status == job_status:
        flash(f'같은 상태로 변경할 수 없습니다. ', category='is-danger')
        return redirect(redirect_url())

    #### 특수 검증
    # 4) 대상직원이 현재유저보다 더 낮은 직위여야한다.
    if not employee_role.is_under(g.user.role):
        flash('자신보다 하위 직위의 직원만 수정할 수 있습니다.', category='is-danger')
        return redirect(redirect_url())

    # 5) 이미 퇴사한 상태라면, 직원초대/직원전환으로만 재직상태를 변경하게 한다.
    if JobStatusType.is_resign(employee.job_status):
        flash(f'퇴사자는 재직상태변경이 불가하며 User관리에서 직원초대로 새로 입사해야합니다. ', category='is-danger')
        return redirect(redirect_url())

    # 6) 복직(재직선택)은 휴직자만 선택가능하도록
    if JobStatusType.is_active(job_status) and employee.job_status != JobStatusType.휴직:
        flash(f'복직은 휴직자만 선택할 수 있습니다. ', category='is-danger')
        return redirect(redirect_url())

    # 7) 날짜의 유효성 검증 (복직일 > 최종 휴직일)
    if JobStatusType.is_active(job_status) and target_date < employee.leave_date:
        flash(f'휴직일보다 더 이전으로 복직할 수 없습니다. ', category='is-danger')
        return redirect(redirect_url())

    # Employee.change_job_status(employee_id, job_status, target_date)

    # required: user.role(selectin) + employee_departments(joined)
    result, msg = employee.update_job_status(job_status, target_date)
    if result:
        flash(f'재직상태변경이 완료되었습니다.', category='is-success')
    else:
        flash(msg)

    return redirect(redirect_url())


@admin_bp.route('employee/<int:employee_id>/user_popup')
@login_required
def user_popup(employee_id):
    # employee = Employee.load({'user': ('selectin', {'role': 'selectin'})}).filter_by(id=employee_id).first()
    # user = employee.user
    user = User.load({'role': 'selectin'}) \
        .filter_by(employee___id=employee_id).first()

    return render_template('admin/employee_user_popup.html', user=user)


# #### front 미구현
# @admin_bp.route('/departments/<int:employee_id>', methods=['GET'])
# @login_required
# def get_current_departments(employee_id):
#     emp: Employee = Employee.get_by_id(employee_id)
#     current_depts = emp.get_my_departments()
#     current_dept_infos = [{'id': x.id, 'name': x.name} for x in current_depts]
#
#     return make_response(
#         dict(deptInfos=current_dept_infos),
#         200
#     )

#### front 미구현 for [부서] 변경 모달?!
@admin_bp.route('/departments/<employee_id>', methods=['GET'])
@login_required
def get_current_departments(employee_id):
    employee = Employee.get(int(employee_id))
    # current_depts = employee.get_my_departments()
    # print('current_depts  >> ', current_depts)
    # # 특정 Employee의 - 현재 취임한 EmployeeDepartment정보가 있는 & 해고된 것은 아닌 - Department들
    # filter_by_map = dict(
    #     and_=dict(
    #         employee_departments___dismissal_date=None,
    #         employee_departments___employee___id=employee_id
    #     )
    # )
    # active_depts = Department.filter_by(**filter_by_map).all()
    # print('active_depts  >> ', active_depts)
    #
    # # 현재 선택된 (특정)부서(id)를 제외하기
    # filter_by_map.get('and_').update(dict(id__ne=4))
    # active_depts = Department.filter_by(**filter_by_map).all()
    # print('active_except_depts  >> ', active_depts)
    #
    # # 내가 팀장인 부서만
    # filter_by_map.get('and_').update(dict(employee_departments___is_leader=True))
    # active_depts = Department.filter_by(**filter_by_map).all()
    # print('active_except_is_leader_depts  >> ', active_depts)
    #
    #
    # # 필터링된 모든 부서들 중  최상위level 부서들만
    # min_level_of_dept = float('inf')
    # min_level_depts = []
    # for dept in active_depts:
    #     if dept.level == min_level_of_dept:
    #         min_level_depts.append(dept)
    #     elif dept.level < min_level_of_dept:
    #         min_level_of_dept = dept.level
    #         min_level_depts = [dept]
    # print('min_level_dep'
    #       ' ts  >> ', min_level_depts)
    #
    # #### No Load with has/any + @hybrid_method
    # # relation path 묶어서 ___ keyword를 대체한다
    #
    # current_dept_infos = [{'id': x.id, 'name': x.name} for x in current_depts]
    # print('current_dept_infos  >> ', current_dept_infos)

    departments = employee.get_departments()
    current_dept_infos = [x.to_dict2(include=['id', 'name']) for x in departments]

    return make_response(
        dict(deptInfos=current_dept_infos),
        200
    )


# @admin_bp.route('/departments/selectable/', methods=['POST'])
# @login_required
# def get_selectable_departments():
#     # print(request.form) # ImmutableMultiDict([('current_dept_id', '5'), ('employee_id', '16')])
#     # print(request.args) # ImmutableMultiDict([])
#     employee_id = request.form.get('employee_id', type=int)
#     current_dept_id = request.form.get('current_dept_id', type=int)
#     # print(employee_id, current_dept_id)  # None, None
#     #### 현재부서에서 [부서 추가]시 current_dept_id가 None으로 들어올 수 있다.
#     # if not employee_id or not current_dept_id:
#     if not employee_id:
#         return make_response(dict(message='직원id가 잘못되었습니다.'), 403)
#
#     #### 현재부서가 None => [부서 추가]로 판단하여, 변경부서를 모든 부서를 건네준다.
#     if current_dept_id:
#         current_dept: Department = Department.get_by_id(current_dept_id)
#         selectable_depts_infos = current_dept.get_selectable_departments()
#     else:
#         selectable_depts_infos = Department.get_all_infos()
#
#     #### 선택된 현재부서 => 가능한 부서들을 뽑아왔는데,
#     #### => emp_id까지 추가로 받아서, 가능한 부서들  - ( 직원의 선택안된 현재 부서들id 제외시켜주기 )
#     #### => [부서 추가]의 상황에서도  현재 소속부서들은 그대로 빼준다.
#     current_employee: Employee = Employee.get_by_id(employee_id)
#     current_dept_ids = [dept.id for dept in current_employee.get_my_departments()]
#
#     # 필터링
#     selectable_depts_infos = [dept for dept in selectable_depts_infos if dept.get('id') not in current_dept_ids]
#
#     return make_response(
#         dict(deptInfos=selectable_depts_infos),
#         200
#     )

@admin_bp.route('/departments/selectable/', methods=['POST'])
@login_required
def get_selectable_departments():
    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    # print(employee_id, current_dept_id)  # None, None

    # 직원정보가 없으면 잘못된 요청이다.
    if not employee_id:
        return make_response(dict(message='직원id가 잘못되었습니다.'), 403)

    employee = Employee.get(employee_id)
    # 1. [현재 부서]가 None => <부서 추가>로 판단하여,
    # => [변경할 부서]에는 <모든 부서 - (내가 소속중인 부서)>를 반환해줘야한다.
    if not current_dept_id:
        current_dept_ids = [dept.id for dept in employee.get_my_departments()]
        selectable_depts_infos = Department.filter_by(status=True, id__notin=current_dept_ids) \
            .order_by('path').to_dict2(include=['id', 'name'])

    # 2. [현재부서]가 존재할 경우 => <모든 부서 - (현재부서 + 현재부서의 자식부서들)>을 반환해줘야한다.
    # if current_dept_id:
    else:
        # current_dept = Department.load({'children': ('joined', 6)}).filter_by(id=current_dept_id).first()
        current_dept = Department.filter_by(id=current_dept_id).first()
        not_allowed_dept_ids = [x.id for x in current_dept.flatten_children()]
        selectable_depts_infos = Department.filter_by(status=True, id__notin=not_allowed_dept_ids).order_by(
            'path').to_dict2(include=['id', 'name'])

    return make_response(
        dict(deptInfos=selectable_depts_infos),
        200
    )


# @admin_bp.route('/departments/all', methods=['GET'])
# @login_required
# def get_all_departments():
#     dept_infos = Department.get_all_infos()
#     if not dept_infos:
#         return make_response(dict(message='선택가능한 부서가 없습니다.'), 500)
#
#     return make_response(dict(deptInfos=dept_infos), 200)
@admin_bp.route('/departments/all', methods=['GET'])
@login_required
def get_all_departments():
    # dept_infos = Department.get_all_infos()
    dept_infos = Department.filter_by(status=True).order_by('path').to_dict2(include=['id', 'name'])
    if not dept_infos:
        return make_response(dict(message='선택가능한 부서가 없습니다.'), 500)

    return make_response(dict(deptInfos=dept_infos), 200)


# @admin_bp.route('/departments/promote/', methods=['POST'])
# @login_required
# def determine_promote():
#     current_dept_id = request.form.get('current_dept_id', type=int)
#     employee_id = request.form.get('employee_id', type=int)
#     as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
#     # 부/장급부서는 자동으로 as_leader = True를 박기 위해 추가로 받음.
#     after_dept_id = request.form.get('after_dept_id', type=int)
#
#     # 필수 인자들이 안들어오면 에러다.
#     if not employee_id:
#         return make_response(dict(message='잘못된 요청입니다.'), 403)
#
#     # => 현재부서/변경부서는 둘중에 1개는 없을 수 있다. => 둘다 없으면 판단 못한다. => 부서장여부 스위치만 건들인 경우?
#     # if not current_dept_id and not after_dept_id:
#     if not (current_dept_id or after_dept_id):
#         return make_response(dict(message='부서를 선택한 뒤, 부서장여부를 결정해주세요.'), 403)
#
#     # 부/장급부서를 변경부서로 선택했다면, 넘어오는 as_leader를 무조건 True로 반영하기
#     # => 현재부서 -> 변경부서 [부서제거] 선택도입시 nuabllable한 after_dept_id로서, if 존재할때만 쿼리 날리기
#     # if after_dept_id:
#     #     after_dept: Department = Department.get_by_id(after_dept_id)
#     #     if after_dept.type == DepartmentType.부장:
#     #         as_leader = True
#
#     current_employee: Employee = Employee.get_by_id(employee_id)
#
#     # 승진여부판단에선 (전제 변경부서가 선택)이므로 => 변경부서가 [부서제거]-None가 아닌 [실제 값]으로 존재할때만 판단하도록 변경
#     # if as_leader:
#     # if after_dept_id and as_leader:
#     is_promote = current_employee.is_promote(after_dept_id, as_leader)
#     # else:
#     #     # 부서장여부는, 부/장급이면 자동으로 True로 채워졌는데, 그래도 False라면, 승진은 절대 아니므로 배제하고 쿼리날릴 필요도 없이 무조건 False로
#     #     is_promote = False
#
#     # 강등여부판단은 전제가 [변경부서선택 with 부서원] OR  변경부서선택을 => [부서제거]로 None이어도 상관없다.
#     # => 내부에서 1개 팀장인데 && 부서원으로 뿐만 아니라 1개 팀장인데 && after_dept_id가 None도 추가해야할 듯하다.
#     # if current_dept_id:
#     # 1) 현재부서  +  선택부서가 부서원으로 판단
#     is_demote = current_employee.is_demote(current_dept_id, after_dept_id, as_leader)
#     # 2) 현재부서 + 선택부서가 None으로 해지를 추가할 예정
#     # else:
#     #     현재부서는 nullable이고, 현재부서가 없다면, 쿼리날리기도 전에 강등은 있을 수 없어서 무조건 False
#     # is_demote = False
#
#     return make_response(dict(isPromote=is_promote, isDemote=is_demote), 200)

@admin_bp.route('/departments/promote/', methods=['POST'])
@login_required
def determine_promote():
    current_dept_id = request.form.get('current_dept_id', type=int)
    employee_id = request.form.get('employee_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    # 부/장급부서는 자동으로 as_leader = True를 박기 위해 추가로 받음.
    after_dept_id = request.form.get('after_dept_id', type=int)

    # 필수 인자들이 안들어오면 에러다.
    if not employee_id:
        return make_response(dict(message='잘못된 요청입니다.'), 403)

    # => 현재부서/변경부서는 둘중에 1개는 없을 수 있다. => 둘다 없으면 판단 못한다. => 부서장여부 스위치만 건들인 경우?
    # if not current_dept_id and not after_dept_id:
    if not (current_dept_id or after_dept_id):
        return make_response(dict(message='부서를 선택한 뒤, 부서장여부를 결정해주세요.'), 403)

    # 부/장급부서를 변경부서로 선택했다면, 넘어오는 as_leader를 무조건 True로 반영하기
    # => 현재부서 -> 변경부서 [부서제거] 선택도입시 nuabllable한 after_dept_id로서, if 존재할때만 쿼리 날리기
    # if after_dept_id:
    #     after_dept: Department = Department.get_by_id(after_dept_id)
    #     if after_dept.type == DepartmentType.부장:
    #         as_leader = True

    # current_employee: Employee = Employee.get_by_id(employee_id)
    current_employee: Employee = Employee.load({'user': ('selectin', {'role': 'selectin'})}) \
        .filter_by(id=employee_id) \
        .first()

    # 승진여부판단에선 (전제 변경부서가 선택)이므로 => 변경부서가 [부서제거]-None가 아닌 [실제 값]으로 존재할때만 판단하도록 변경
    # if as_leader:
    # if after_dept_id and as_leader:
    is_promote = current_employee.is_promote(after_dept_id, as_leader)
    # else:
    #     # 부서장여부는, 부/장급이면 자동으로 True로 채워졌는데, 그래도 False라면, 승진은 절대 아니므로 배제하고 쿼리날릴 필요도 없이 무조건 False로
    #     is_promote = False

    # 강등여부판단은 전제가 [변경부서선택 with 부서원] OR  변경부서선택을 => [부서제거]로 None이어도 상관없다.
    # => 내부에서 1개 팀장인데 && 부서원으로 뿐만 아니라 1개 팀장인데 && after_dept_id가 None도 추가해야할 듯하다.
    # if current_dept_id:
    # 1) 현재부서  +  선택부서가 부서원으로 판단
    is_demote = current_employee.is_demote(current_dept_id, after_dept_id, as_leader)

    # 2) 현재부서 + 선택부서가 None으로 해지를 추가할 예정
    # else:
    #     현재부서는 nullable이고, 현재부서가 없다면, 쿼리날리기도 전에 강등은 있을 수 없어서 무조건 False
    # is_demote = False

    return make_response(dict(isPromote=is_promote, isDemote=is_demote), 200)


# @admin_bp.route('/departments/change', methods=['POST'])
# @login_required
# @role_required(allowed_roles=[Roles.CHIEFSTAFF])
# def department_change():
#     # print(request.form)
#     # ImmutableMultiDict([('employee_id', '4'), ('current_dept_id', '5'), ('after_dept_id', '4'), ('as_leader', '부서장'), ('date', '2023-01-20')])
#     employee_id = request.form.get('employee_id', type=int)
#     current_dept_id = request.form.get('current_dept_id', type=int)
#     after_dept_id = request.form.get('after_dept_id', type=int)
#     # b-switch 아래 hidden input은 isSwitchedCustom에 의해 부서장 or 부서원이 들어옴
#     as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
#     target_date = request.form.get('date',
#                                    type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
#                                    )
#
#     # with DBConnectionHandler() as db:
#     #     employee: Employee = db.session.get(Employee, employee_id)
#     employee: Employee = Employee.get_not_resigned_by_id(employee_id)
#     #### 해당 직원이 is_active필터링이 안걸리면 퇴사상태의 직원으로 간주하고, 변경불가하다고 돌려보내기
#     if not employee:
#         flash('퇴사한 직원은 부서 변경이 불가능 합니다.', category='is-danger')
#         return redirect(redirect_url())
#
#     # (bool, msg) 반환
#     result, message = employee.change_department(current_dept_id, after_dept_id, as_leader, target_date)
#
#     if result:
#         flash(message, category='is-success')
#     else:
#         flash(message, category='is-danger')
#
#     return redirect(redirect_url())


@admin_bp.route('/departments/change', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def department_change():
    # print(request.form)
    # ImmutableMultiDict([('employee_id', '4'), ('current_dept_id', '5'), ('after_dept_id', '4'), ('as_leader', '부서장'), ('date', '2023-01-20')])
    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    after_dept_id = request.form.get('after_dept_id', type=int)
    # b-switch 아래 hidden input은 isSwitchedCustom에 의해 부서장 or 부서원이 들어옴
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    target_date = request.form.get('date',
                                   type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
                                   )

    employee: Employee = Employee.load({
        'user': ('selectin', {'role': 'selectin'}),
        'employee_departments': 'joined'  # for update employee_departments fill
    }) \
        .filter_by(id=employee_id) \
        .first()

    #### 해당 직원이 is_active필터링이 안걸리면 퇴사상태의 직원으로 간주하고, 변경불가하다고 돌려보내기
    if JobStatusType.is_resign(employee.job_status):
        flash('퇴사한 직원은 부서 변경이 불가능 합니다.', category='is-danger')
        return redirect(redirect_url())

    # (bool, msg) 반환
    result, message = employee.change_department(current_dept_id, after_dept_id, as_leader, target_date)

    if result:
        flash(message, category='is-success')
    else:
        flash(message, category='is-danger')

    return redirect(redirect_url())
