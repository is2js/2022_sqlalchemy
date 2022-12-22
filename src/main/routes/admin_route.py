from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import json
import os
from pathlib import Path

from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, g
from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie, Tab
from sqlalchemy import select, delete, func, text, literal_column, column, literal, and_, extract, distinct, cast, \
    Integer, exists
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from src.config import project_config
from src.infra.commons import paginate
from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Category, Post, Tag, User, Banner, posttags, Setting
from src.infra.tutorial3.auth.users import SexType, Roles, Role, Employee, EmployeeInvite
from src.main.forms import CategoryForm
from src.main.forms.admin.forms import PostForm, TagForm, CreateUserForm, BannerForm, SettingForm
from src.main.forms.auth.forms import EmployeeForm, UserInfoForm
from src.main.utils import login_required, admin_required, role_required, redirect_url
from src.main.utils import upload_file_path, delete_uploaded_file, delete_files_in_img_tag

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def to_string_date(last_month):
    return datetime.strftime(last_month, '%Y-%m-%d')


def get_pie_chart(db, entity, category_column_name, condition=None):
    # 1) sql을 groupby에 카테고리를 올리고, 갯수를 센다
    # -> group_by 집계시에는 label을 못단다?
    # [(False, 2), (True, 2)]
    stmt = select(getattr(entity, category_column_name), func.count(entity.id)).group_by(
        getattr(entity, category_column_name))
    if condition:
        stmt = stmt.where(condition)
    datas = db.session.execute(
        stmt
    ).all()

    # print(datas)
    # [(False, 2), (True, 2)]

    # 2)카테고리 종류가 눈에 들어오기 슆게 바꿔야한다.
    #  성별 -> 0 미정, 1 남자 2 여자
    #  enum을 import해서 처리하는게 좋을 듯.

    # datas = list(map(lambda x: ('관리자' if x[0] else '일반유저', x[1]), datas))
    # print(datas)
    # [('일반유저', 2), ('관리자', 2)]

    # datas = list(map(lambda x: SexType(x[0]).name, datas))
    # print(datas)
    # ['미정', '남자', '여자']
    # 첫번째 데이터x[0]카테고리가 0인 것을 제외시키고 변환하면, 미정을 제외시킬 수 있다.
    # => 데이터가 0인 경우, 에러가 발생하므로, 일단 치운다.
    # datas = list(map(lambda x: (SexType(x[0]).name, x[1]), [x for x in datas if x[0] != 0]))
    datas = list(map(lambda x: (SexType(x[0]).name, x[1]), datas))
    # print(datas)

    # 3) pie차트는 [ (category, count) ] tuple list를 입력으로 받는다.
    #### 빈 datas면.. range error가 나서.. if문 걸어줌.
    if datas:
        c = (
            Pie()
            .add("", datas)
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}({d}%)"))
            .set_global_opts(legend_opts=opts.LegendOpts(pos_left=True, orient='vertical'))
        )
        return c
    else:
        return None


def get_diff_for(db, entity, interval='day', period=7, condition=None):
    if period < 2:
        raise ValueError('최소 1단위 전과 비교하려면, period는 2 이상이어야합니다.')
    end_date = date.today()
    if interval == 'day':
        start_date = end_date - relativedelta(days=period - 1)
    elif interval == 'month':
        start_date = end_date - relativedelta(months=period - 1)
    elif interval == 'year':
        start_date = end_date - relativedelta(years=period - 1)
    else:
        raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')

    end_stmt = select(func.count(entity.id)).where(and_(func.date(getattr(entity, 'add_date')) <= end_date))
    if condition:
        end_stmt = end_stmt.where(condition)
    end_count = db.session.scalar(
        end_stmt
    )

    srt_stmt = select(func.count(entity.id)).where(and_(func.date(getattr(entity, 'add_date')) <= start_date))
    if condition:
        srt_stmt = srt_stmt.where(condition)
    start_count = db.session.scalar(
        srt_stmt
    )
    # print(end_count - start_count, type(end_count))
    diff = end_count - start_count
    # start가 zero division
    try:
        rate_of_increase = round((end_count - start_count) / start_count * 100, 2)
    except:
        rate_of_increase = round(end_count * 100, 2)
    # print(rate_of_increase)
    return diff, rate_of_increase


@admin_bp.route('/')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def index():
    with DBConnectionHandler() as db:
        post_count = db.session.scalar(select(func.count(Post.id)))
        post_count_diff, post_count_diff_rate = get_diff_for(db, Post, interval='day', period=7)
        category_count = db.session.scalar(select(func.count(Category.id)))
        category_count_diff, category_count_diff_rate = get_diff_for(db, Category, interval='day', period=7)
        banner_count = db.session.scalar(select(func.count(Banner.id)))
        banner_count_diff, banner_count_diff_rate = get_diff_for(db, Banner, interval='day', period=7)
        # 같은 User entity라서 condition= 옵션을 추가함.
        user_count = db.session.scalar(select(func.count(User.id)).where(~User.is_staff))
        user_count_diff, user_count_diff_rate = get_diff_for(db, User, interval='day', period=7,
                                                             condition=not User.is_staff,
                                                             )
        employee_count = db.session.scalar(select(func.count(User.id)).where(User.is_staff))
        employee_count_diff, employee_count_diff_rate = get_diff_for(db, User, interval='day', period=7,
                                                                     condition=User.is_staff,
                                                                     )

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
        subq = select(Post.category_id, func.coalesce(func.count(Post.id), 0).label('count')) \
            .group_by(Post.category_id) \
            .subquery()
        stmt = select(Category.name, subq.c.count) \
            .join_from(Category, subq, isouter=True) \
            .order_by(subq.c.count.desc())
        # [('분류1', 5), ('22', 2)]
        post_count_by_category = db.session.execute(stmt)
        post_by_category_x_datas = []
        post_by_category_y_datas = []
        for category, post_cnt_by_category in post_count_by_category:
            post_by_category_x_datas.append(category)
            post_by_category_y_datas.append(post_cnt_by_category)
        #### < 1-2 post가 가장 많이 걸린 tag> -> Tag별 post갯수세기 -> 중간테이블이라서 바로 집계되지만, name을 얻으려면 left join
        #### => left.right관계명으로 assoc table무시하고, outerjoin을 건다(내부에서 assoc 와 right(Post)를 일반join한 뒤 outerjoin한다)
        # stmt = select(Tag.name, func.coalesce(Post.id, 0).label('count'), func.coalesce(cast(Post.has_type, Integer), 0).label('sum')) \
        stmt = select(Tag.name, func.coalesce(func.count(Post.id), 0).label('count'),
                      func.sum(cast(Post.has_type, Integer)).label('sum')) \
            .join(Tag.posts, isouter=True) \
            .group_by(Tag.id) \
            .order_by(literal_column('count').desc()) \
            .limit(3)
        tag_with_post_count = db.session.execute(stmt).all()

        #### < 2-1 일주일 user 수>
        user_chart = get_user_chart(db)
        # <2-2-2 user 성별 piechart > 아직 성별칼럼이 없으니 직원수 vs 일반 유저로 비교해보자.
        user_sex_pie_chart = get_pie_chart(db, User, 'sex', condition=User.sex != SexType.미정)

        ### 만약, df로 만들거라면 row별로 dict()를 치면 row1당 column:value의 dict list가 된다.
        # print([dict(r) for r in db.session.execute(stmt)])

        #### < 월별 연간 통계 by pyerchart>
        year_x_datas, year_post_y_datas = get_datas_count_by_date(db, Post, 'add_date', interval='month', period=12)
        _, year_user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='month', period=12)
        _, year_category_y_datas = get_datas_count_by_date(db, Category, 'add_date', interval='month', period=12)
        _, year_banner_y_datas = get_datas_count_by_date(db, Banner, 'add_date', interval='month', period=12)
        _, year_tag_y_datas = get_datas_count_by_date(db, Tag, 'add_date', interval='month', period=12)
        year_chart = (
            Bar()
            .add_xaxis(year_x_datas)
            .add_yaxis('유저 수', year_user_y_datas)  # y축은 name먼저
            .add_yaxis('포스트 수', year_post_y_datas)
            .add_yaxis('카테고리 수', year_category_y_datas)
            .add_yaxis('배너 수', year_banner_y_datas)
            .add_yaxis('태그 수', year_tag_y_datas)
        )

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


def get_user_chart(db):
    user_x_datas, user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='day', period=7)
    #
    user_chart = (
        Bar()
        .add_xaxis(user_x_datas)
        .add_yaxis('유저 수', user_y_datas)
    )
    return user_chart


def get_datas_count_by_date(db, entity, date_column_name, interval='day', period=7):
    if period < 2:
        raise ValueError('최소 1단위 전과 비교하려면, period는 2 이상이어야합니다.')

    end_date = date.today()  # end_date는 datetime칼럼이라도, date기준으로
    if interval == 'day':
        start_date = end_date - relativedelta(days=period - 1)
    elif interval == 'month':
        start_date = end_date - relativedelta(months=period - 1)
    elif interval == 'year':
        start_date = end_date - relativedelta(years=period - 1)
    else:
        raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')

    series = generate_series_subquery(start_date, end_date, interval=interval)
    ### subquery를 확인시에는 .select()로 만들어서 .all()후 출력
    # print(db.session.execute(series.select()).all())
    # print(ts, type(ts))
    ## 3) User의 생싱일date별 count 집계하기
    # [('2022-11-19', 1), ('2022-11-25', 2)]
    ## ==> datetime필드를, date기준으로 filtering하고 싶다면
    ##     칼럼.between()에 못넣는다.
    ## ==> datetime -> date로 칼럼을 변경하고 filter해야지, 오늘13시도, today()에 걸린다
    ## 만약, today() 2022-11-29를   2022-11-29 13:00:00 datetime필드로 필터링하면
    ##  오늘에 해당 데이터가 안걸린다. 데이터를 일단 변환하고 필터링에 넣어야한다.
    # select(func.date(User.add_date).label('date'), func.count(User.id).label('count')) \
    values = count_by_date_subquery(interval, entity, date_column_name, end_date, start_date)
    # print(db.session.execute(values.select()).all())

    # .group_by(func.strftime("%Y", User.add_date).label('date'))\
    # => [('2022', 4)]
    # .group_by(func.date(User.add_date).label('date'))\
    # .group_by(func.date(User.add_date))
    # print(db.session.execute(values.select()).all())
    # [('2022-11-19', 1), ('2022-11-25', 2), ... ('2022-11-29', 1)]
    ## 3) series에 values르 outerjoin with 없는 데이터는 0으로
    stmt = (
        select(series.c.date, func.coalesce(values.c.count, 0).label('count'))
        .outerjoin(values, values.c.date == series.c.date)
        .order_by(series.c.date.asc())
    )
    ## scalars()하면 date만 나온다.
    # print(db.session.scalars(stmt).all())
    # [('2022-10-29', 0), ('2022-10-30', 0), ... ('2022-11-25', 2), ('2022-11-26', 0), ('2022-11-27', 0), ('2022-11-28', 0), ('2022-11-29', 1)]
    # print(db.session.execute(stmt).all())
    x_datas = []
    y_datas = []
    for day, user_count in db.session.execute(stmt):
        x_datas.append(day)
        y_datas.append(user_count)
    # 집계대상 필터링은 Y-m-d(date) -> group_by strftime으로 (day) or Y-m-d/(month)Y-m/(year)Y 상태
    # 이미 문자열로 Y-m-d  or Y-m  or Y 중 1개로 정해진 상태다. -> -로 split한 뒤 마지막거만 가져오면 interval 단위
    # => 출력을 위해 day단위면, d만 / month단위면 m만 나가도록 해준다 (year는 이미 Y)
    if interval == 'day':
        x_datas = list(map(lambda x: x.split('-')[-1] + '일', x_datas))
    elif interval == 'month':
        x_datas = list(map(lambda x: x.split('-')[-1] + '월', x_datas))  # 이미 Y-m그룹화 상태
    elif interval == 'year':
        x_datas = list(map(lambda x: x + '년', x_datas))
    return x_datas, y_datas


def count_by_date_subquery(interval, entity, date_column_name, end_date, start_date):
    if interval == 'day':
        strftime_format = '%Y-%m-%d'
    elif interval == 'month':
        strftime_format = '%Y-%m'
    elif interval == 'year':
        strftime_format = '%Y'
    else:
        raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')

    return (
        select(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'),
               func.count(entity.id).label('count'))
        .where(and_(
            start_date <= func.date(getattr(entity, date_column_name)),
            func.date(getattr(entity, date_column_name)) <= end_date)
        )
        .group_by(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'))
        .subquery()
    )


def generate_series_subquery(start_date, end_date, interval='day'):
    if interval == 'day':
        strftime_format = '%Y-%m-%d'
    if interval == 'month':
        strftime_format = '%Y-%m'
    elif interval == 'year':
        strftime_format = '%Y'

    # select date form dates담에 ;를 넘으면 outer join시 에러
    _text = text(f"""
        WITH RECURSIVE dates(date) AS (
              VALUES (:start_date)
          UNION ALL
              SELECT date(date, '+1 {interval}')
              FROM dates
              WHERE date < :end_date
        )
        SELECT strftime('{strftime_format}', date) AS 'date' FROM dates
        """).bindparams(start_date=to_string_date(start_date), end_date=to_string_date(end_date))
    # func.to_char(orig_datetime, 'YYYY-MM-DD HH24:MI:SS
    # SELECT strftime('%Y', date) FROM dates

    # with DBConnectionHandler() as db:
    #     print(db.session.execute(stmt.columns(column('date')).label('date')).subquery('series').select()).all())
    ## output 1 - date는 date타입이지만, 출력은 문자열로 된다.
    # unit=day
    # [('2022-10-29',), ('2022-10-30',),... ('2022-11-28',), ('2022-11-29',)]

    # unit=month
    # [('2022-10-29',), ('2022-11-29',)]
    # unit=year
    # [('2021-11-30',), ('2022-11-30',)]
    ## output 2 - sqlite SELECT strftime('%Y', CURRENT_TIMESTAMP)으로
    ##            그외는  SELECT EXTRACT(YEAR FROM CURRENT_DATE) 를 쓴다.
    # => month일땐, Y-m으로  / year일땐, Y로만 나와야, 거기에 맞춘 values를 outer_join 시킬수 있을 것이다.
    # => text.columns(column()) 지정시 func.extract로 변경하자.
    # [('2021-11-30',), ('2022-11-30',)]
    # if interval == 'year':
    #     return stmt.columns(extract('year',column('date'))).subquery('series')

    return _text.columns(column('date')).subquery('series')


@admin_bp.route('/category')
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category():
    # with DBConnectionHandler() as db:
    # admin- table에는 id역순으로 제공해줘야 최신순으로 보인다.
    # category_list = db.session.scalars((
    #     select(Category)
    #     .order_by(Category.id.desc())
    # )).all()

    # querystring의 page에서 page값 받고, int변환하되, 기본값 1
    page = request.args.get('page', 1, type=int)

    # 직접 추출대신 pagination으로 처리하기 (id역순으로 전체조회)
    stmt = select(Category).order_by(Category.id.desc())
    # pagination = paginate(stmt, 1, per_page=1)
    pagination = paginate(stmt, page=page, per_page=10)

    category_list = pagination.items

    return render_template('admin/category.html',
                           category_list=category_list, pagination=pagination)


@admin_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category_add():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, icon=form.icon.data)
        with DBConnectionHandler() as db:
            db.session.add(category)
            db.session.commit()
        flash(f'{form.name.data} Category 생성 성공!')
        return redirect(url_for('admin.category'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/category_form.html', form=form, errors=errors)


@admin_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category_edit(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    with DBConnectionHandler() as db:
        category = db.session.get(Category, id)

    # 2) 찾은 객체의 데이터를 바탕으로 form을 만들어서 GET 화면에 뿌려준다.
    # => 이 때, form에 id= 키워드를 주면, edit용 form으로 인식해서 validate를 나를 제외하고 하도록 한다
    # form = CategoryForm(name=category.name, icon=category.icon, id=category.id)
    form = CategoryForm(category)
    # return render_template('admin/category_form.html', form=form, errors=errors)

    # 3) form에서 달라진 데이터로 POST가 들어오면, 수정하고 커밋한다.
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            category = db.session.get(Category, id)
            # print("category>>>", category.__dict__)

            category.name = form.name.data
            category.icon = form.icon.data if len(form.icon.data) > 0 else None  # 수정form화면에서 암것도 없으면 ''이 올 것이기 때무네

            db.session.add(category)
            # print("category>>>", category.__dict__)
            db.session.commit()
        flash(f'{form.name.data} Category 수정 완료.')
        return redirect(url_for('admin.category'))

    # 4) 검증이 들어간 form에 대한 erros는 if form.validate_on_submit()보다 아래에 둔다.
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/category_form.html', form=form, errors=errors)


@admin_bp.route('/category/delete/<int:id>')
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def category_delete(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    with DBConnectionHandler() as db:
        category = db.session.get(Category, id)
        if category:

            # post cascading 되기 전에, content에서 이미지 소스 가져와 삭제하기
            if category.posts:
                for post in category.posts:
                    delete_files_in_img_tag(post.content)

            db.session.delete(category)
            db.session.commit()
            flash(f'{category.name} Category 삭제 완료.')
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

    stmt = select(Post).order_by(Post.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    return render_template('admin/article.html',
                           post_list=post_list, pagination=pagination)


@admin_bp.route('/article/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article_add():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            desc=form.desc.data,
            content=form.content.data,
            # form에서 올라온 value는 coerce=int에 의해 int value가 올라오고 -> 그대로 집어넣으면, 알아서 enum필드객체로 변환된다.
            has_type=form.has_type.data,
            category_id=form.category_id.data,
        )

        with DBConnectionHandler() as db:
            # 2) 다대다에 해당하는 tags를 한꺼번에 추가해줘야한다. 개별객체, append보다는 객체 list를 만들어서, 넣어주자.
            # -> form에서 오는 data는, 숫자list가 될 것이다?
            post.tags = [db.session.get(Tag, tag_id) for tag_id in form.tags.data]
            db.session.add(post)
            db.session.commit()
        flash(f'{form.title.data} Post 생성 성공!')
        return redirect(url_for('admin.article'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html',
                           form=form, errors=errors)


@admin_bp.route('/article/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article_edit(id):
    with DBConnectionHandler() as db:
        post = db.session.get(Post, id)

    form = PostForm(post)

    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            post = db.session.get(Post, id)

            post.title = form.title.data
            post.desc = form.desc.data
            post.content = form.content.data
            # 2) form에서 올라온 value는 coerce=int에 의해 int value가 올라오고
            #   -> 그대로 집어넣으면, 알아서 enum필드객체로 변환된다.
            post.has_type = form.has_type.data
            post.category_id = form.category_id.data

            post.tags = [db.session.get(Tag, tag_id) for tag_id in form.tags.data]

            db.session.add(post)
            db.session.commit()

            flash(f'{form.title.data} Post 수정 완료.')
            return redirect(url_for('admin.article'))
    #
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html', form=form, errors=errors)


@admin_bp.route('/article/delete/<int:id>')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def article_delete(id):
    with DBConnectionHandler() as db:
        post = db.session.get(Post, id)

        # img태그 속 src를 찾아, 해당 파일 경로를 추적하여 삭제
        delete_files_in_img_tag(post.content)

        if post:
            db.session.delete(post)
            db.session.commit()
            flash(f'{post.title} Post 삭제 완료.')
            return redirect(url_for('admin.article'))


@admin_bp.route('/tag')
@login_required
def tag():
    page = request.args.get('page', 1, type=int)

    stmt = select(Tag).order_by(Tag.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    tag_list = pagination.items

    return render_template('admin/tag.html',
                           tag_list=tag_list, pagination=pagination)


@admin_bp.route('/tag/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def tag_add():
    form = TagForm()

    if form.validate_on_submit():
        tag = Tag(name=form.name.data)
        with DBConnectionHandler() as db:
            db.session.add(tag)
            db.session.commit()
        flash(f'{form.name.data} Tag 생성 성공!')
        return redirect(url_for('admin.tag'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/tag_form.html', form=form, errors=errors)


@admin_bp.route('/tag/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def tag_edit(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)

    form = TagForm(tag)

    if form.validate_on_submit():
        prev_name = tag.name  # 변경 전 이름을 가져다 놓기 cf) 로그인 기록처럼 log table을 만들어도 될듯?
        tag.name = form.name.data
        db.session.add(tag)
        db.session.commit()

        flash(f'{prev_name}->{form.name.data} Tag 수정 완료.')
        return redirect(url_for('admin.tag'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/tag_form.html', form=form, errors=errors)


@admin_bp.route('/tag/delete/<int:id>')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def tag_delete(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)

        if tag:
            db.session.delete(tag)
            db.session.commit()
            flash(f'{tag.name} Tag 삭제 완료.')
            return redirect(url_for('admin.tag'))


@admin_bp.route('/user')
@login_required
def user():
    page = request.args.get('page', 1, type=int)

    # stmt = select(User).order_by(User.add_date.desc())
    # ~User.is_staff => only user
    stmt = select(User) \
        .where(~User.is_staff) \
        .order_by(User.add_date.desc())

    # print(stmt)

    pagination = paginate(stmt, page=page, per_page=10)
    user_list = pagination.items

    #### 직원초대시 modal에 띄울 role_list를 건네주기
    with DBConnectionHandler() as db:
        role_list = db.session.scalars(
            select(Role)
            .where(Role.is_(Roles.STAFF))  # 상수 STAFF이상이면서
            .where(Role.is_under(g.user.role))  # Role객체의 permissions가 현재 직원의 Roles보다는 적게
        ).all()

    # print(role_list) # [<Role 'STAFF'>, <Role 'DOCTOR'>, <Role 'CHIEFSTAFF'>, <Role 'EXECUTIVE'>]

    return render_template('admin/user.html',
                           user_list=user_list, pagination=pagination,
                           role_list=role_list
                           )


@admin_bp.route('/user/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def user_add():
    # form = CreateUserForm(g.user)
    form = CreateUserForm()

    # with DBConnectionHandler() as db:
    #     roles = db.session.scalars(select(Role).where(Role.permissions < g.user.role.permissions)).all()
    # self.role_id.choices = [(role.id, role.name) for role in roles]
    # form.role_id.choices = [(role.id, role.name) for role in roles if role.name != Roles.ADMINISTRATOR.name]

    if form.validate_on_submit():
        # print("boolean은 체크되면 뭐로 넘어오나", form.is_super_user.data)
        # -> BooleanField는 value는 'y'로 차있지만, check되면 True로 넘어온다
        user = User(
            username=form.username.data,
            # 3) password는 hash로 만들어서 넣어야한다.
            # password=generate_password_hash(form.password.data),
            password=form.password.data,
            email=form.email.data,
            # 4) db에 저장한 update된 '개별폴더/filename'으로 한다.
            #  -> file이 없는 경우를 대비해서 setter형식으로 넣어주자.
            # avatar=f'avatar/{filename}',
            is_active=form.is_active.data,
            # is_super_user=form.is_super_user.data,
            # is_staff=form.is_staff.data,
            ### is_staff필드가가 hybrid_property랑 동일해서 결국 지우든지 바꿔야함.
        )

        # 1) file 업로드 관련 유틸을 import한뒤,
        #   form에서 받은 file객체f 를 통해 -> 저장full경로 + filename만 반환받는다.
        f = form.avatar.data
        if f:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            # print(f"avatar_path, filename >>> {avatar_path, filename}")
            # 2) f(file객체)를 .save( 저장경로 )로 저장한다.
            f.save(avatar_path)
            user.avatar = f'avatar/{filename}'

        with DBConnectionHandler() as db:
            db.session.add(user)
            db.session.commit()

        flash(f'{form.username.data} User 생성 성공!')
        return redirect(url_for('admin.user'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)


@admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def user_edit(id):
    with DBConnectionHandler() as db:
        user = db.session.get(User, id)

    # form = CreateUserForm(g.user, user=user)
    # 더이상 User관리에서 직접 역할 주기위한 직원g.user를 집어넣지 않는다.
    form = CreateUserForm(user=user)

    if form.validate_on_submit():
        # username은 수정못하게 걸어놧으니 pasword부터 처리한다.
        # password는 데이터가 들어온 경우만 -> hash걸어서 저장한다.
        # print(f"form.password.data>>>{form.password.data}")
        if form.password.data:
            # user.password = generate_password_hash(form.password.data)
            user.password = form.password.data
        # avatar의 경우, 현재 db필드인 'avatar/파일명'이 data로 들어가있지만,
        # -> 파일명(기존 user.avatar값과 동일)이 아닌 file객체가data로 온 경우만, 새롭게 upload하는 처리를 해준다.
        f = form.avatar.data
        # print(f"f>>>{f}")
        if f != user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)

            # user.avatar 덮어쓰기 전에, db에 저장된 경로를 바탕으로 -> upload폴더에서 기존 file삭제
            # -> 기존 user.avatar에 암것도 없어도 안에서 바로 종료되도록 예외처리
            delete_uploaded_file(directory_and_filename=user.avatar)

            user.avatar = f'avatar/{filename}'

        # 나머지 필드도 변경
        user.email = form.email.data
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        # user.is_super_user = form.is_super_user.data
        # user.is_staff = form.is_staff.data

        with DBConnectionHandler() as db:
            db.session.add(user)
            db.session.commit()

        flash(f'{form.username.data} User 수정 완료.')
        return redirect(url_for('admin.user'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)


@admin_bp.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def user_delete(id):
    with DBConnectionHandler() as db:
        user = db.session.get(User, id)

        if user:
            # 필드에 file을 가지고 있는 entity는 file도 같이 삭제한다.
            delete_uploaded_file(directory_and_filename=user.avatar)
            db.session.delete(user)
            db.session.commit()
            flash(f'{user.username} User 삭제 완료.')
            return redirect(url_for('admin.user'))


@admin_bp.route('/banner')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner():
    page = request.args.get('page', 1, type=int)

    stmt = select(Banner).order_by(Banner.is_fixed.desc(), Banner.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    banner_list = pagination.items

    return render_template('admin/banner.html',
                           banner_list=banner_list, pagination=pagination)


@admin_bp.route('/banner/add', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner_add():
    form = BannerForm()

    if form.validate_on_submit():
        # 파일이 없을 수는 없지만, user처럼 이미지 없는 경우도 있을 수 있으므로 해당필드는 나중에 f가 있으면 채운다.
        banner = Banner(
            desc=form.desc.data,
            url=form.url.data,
            banner_type=form.banner_type.data,
            is_fixed=form.is_fixed.data
        )

        f = form.img.data
        if f:
            banner_path, filename = upload_file_path(directory_name='banner', file=f)
            f.save(banner_path)

            delete_uploaded_file(directory_and_filename=banner.img)

            banner.img = f'banner/{filename}'

        with DBConnectionHandler() as db:
            db.session.add(banner)
            db.session.commit()

        flash(f'{form.desc.data} Banner 생성 성공!')
        return redirect(url_for('admin.banner'))

    return render_template('admin/banner_form.html', form=form)


@admin_bp.route('/banner/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner_edit(id):
    with DBConnectionHandler() as db:
        banner = db.session.get(Banner, id)

    form = BannerForm(banner)

    if form.validate_on_submit():
        f = form.img.data
        # 수정안되서 경로 그대로 오는지 vs 새 파일객체가 오는지 구분
        if f != banner.img:
            banner_path, filename = upload_file_path(directory_name='banner', file=f)
            f.save(banner_path)

            delete_uploaded_file(directory_and_filename=banner.img)

            banner.img = f'banner/{filename}'

        # 나머지 필드도 변경
        banner.banner_type = form.banner_type.data
        banner.is_fixed = form.is_fixed.data
        banner.desc = form.desc.data
        banner.url = form.url.data

        with DBConnectionHandler() as db:
            db.session.add(banner)
            db.session.commit()

        flash(f'{form.desc.data} Banner 수정 완료.')
        return redirect(url_for('admin.banner'))

    return render_template('admin/banner_form.html', form=form)


@admin_bp.route('/banner/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def banner_delete(id):
    with DBConnectionHandler() as db:
        banner = db.session.get(Banner, id)

        if banner:
            # 필드에 file을 가지고 있는 entity는 file도 같이 삭제한다.
            delete_uploaded_file(directory_and_filename=banner.img)
            db.session.delete(banner)
            db.session.commit()
            flash(f'{banner.desc} Banner 삭제 완료.')
            return redirect(url_for('admin.banner'))


@admin_bp.route('/setting', methods=['GET'])
@login_required
@role_required(allowed_roles=[Roles.ADMINISTRATOR])
def setting():
    s_dict = Setting.to_dict()

    # db객체 list대신 dict를 건네준다.
    # return render_template('admin/setting.html', s_dict=s_dict, active_tab=1)
    return render_template('admin/setting.html', s_dict=s_dict)


@admin_bp.route('/setting/edit', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.ADMINISTRATOR])
def setting_edit():
    s_dict = Setting.to_dict()
    form = SettingForm(s_dict)
    # print(s_dict)

    if form.validate_on_submit():
        with DBConnectionHandler() as db:
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
                    print(key, "는 이미 존재인데")
                    setting = Setting.get_by_key(key)
                    # 1-1-2) 이미 존재해서 꺼냈을 때 값을 비교해서 다르면 업데이트
                    if setting.setting_value == value:
                        print(key, "같은 값이라서 continue")
                        continue
                    else:
                        print(key, "값이 달라져서 update")
                        setting.setting_value = value
                        #### 객체 필드변경후 commit만 하면 자동반영X -> session이 달라서
                        #### => 수정이든, 새로생성이든 아래에서 공통적으로 session.add()해야함.

                else:
                    print(key, "없어서  새로 생성 -> value가 None이도 None으로 넣을 것임.")
                    setting = Setting(
                        setting_key=key,
                        setting_value=value
                    )

                db.session.add(setting)

            db.session.commit()
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
    stmt = select(Employee) \
        .where(Employee.is_active) \
        .order_by(Employee.join_date.desc())

    pagination = paginate(stmt, page=page, per_page=10)
    employee_list = pagination.items

    return render_template('admin/employee.html',
                           employee_list=employee_list,
                           pagination=pagination)


@admin_bp.route('/employee/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_add(user_id):
    user = User.get_by_id(user_id)
    form = EmployeeForm(user, employer=g.user)

    if form.validate_on_submit():
        # User정보와 Employee정보를 따로 분리해서 각각 처리한다.

        #### user ####
        # - 직원으로 변환되면, user의 role부터 미리 선택된 것으로 바뀌어야한다.
        user_info = {
            'email': form.email.data,
            'sex': form.sex.data,
            'phone': form.phone.data,
            'address': form.address.data,

            'role_id': form.role_id.data,
        }
        user.update(user_info)

        f = form.avatar.data
        if f != user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)
            delete_uploaded_file(directory_and_filename=user.avatar)
            user.avatar = f'avatar/{filename}'

        #### employee ####
        # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
        employee = Employee(
            user=user,
            name=form.name.data,
            sub_name=form.sub_name.data,
            birth=form.birth.data,
            join_date=form.join_date.data,
            # job_status는 form에는 존재하지만, 생성시에는 view에 안뿌린다. 대신 default값이 들어가있으니, 그것으로 재직되게 한다?
            job_status=form.job_status.data,
            # resign_date는 deafult값없이 form필드에도 명시안한다
        )

        flash("직원 전환 성공")
        with DBConnectionHandler() as db:
            db.session.add(user)
            db.session.add(employee)
            db.session.commit()

        return redirect(url_for('admin.employee'))

    return render_template('admin/employee_form.html',
                           form=form
                           )


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
    # request.path /admin/invite/employee/
    # request.referrer http://localhost:5000/admin/user
    # => 요청을 보낸 곳의 url을 처리하고 난 뒤 -> redirect 해주기 위한 메서드 개발

    # print(request.form)
    # print(request.form.args.to_dict()) # post에선 못씀.
    role_id = request.form.get('role_id', type=int)
    user_id = request.form.get('user_id', default=None, type=int)
    # print("post>>>", role_id, user_id)

    #### 초대 존재 여부는
    # 1) 현재 초대Type(상위 주제entity)에 대해서만 검색해야한다,(초대 Type이 다르면 또 보낼 수 있음)
    # 2) *응답(수락/거절)되서 삭제된 것외에 만료된 것을 제외하고 검색해야한다.(만료되면 또 보낼 수 있음)
    # 3) 검색시에는, 보내는사람과 받는사람을 필터링하면 된다. 관계테이블이므로, 관계객체.has()/any() - 데이터존재검사 + 추가조건을 건다
    # 4) 만료되지 않는 것에 대해서만 존재검사를 한다.
    # 5) *추후 answer안된 것들만 검사한다
    with DBConnectionHandler() as db:
        inviter = g.user
        invitee = db.session.get(User, user_id)

        stmt = (

            exists()
            .select_from(EmployeeInvite)  # exists()조건들을 WHERE에 담을 주 entity(left)
            .where(EmployeeInvite.inviter.has(User.id == inviter.id))
            .where(EmployeeInvite.invitee.has(User.id == invitee.id))
            # .where(EmployeeInvite.is_not_expired)
            .where(EmployeeInvite.is_valid)
            .select()
        )

        is_invite_exists = db.session.scalar(stmt)

        if is_invite_exists:
            flash(f"{invitee.username}에게 이미 직원초대를 보냈습니다.", category="is-danger")
        else:
            role = db.session.scalars(select(Role).where(Role.id == role_id)).first()

            invite = EmployeeInvite(
                inviter=inviter,
                invitee=invitee,
                role=role,
            )

            db.session.add(invite)
            db.session.commit()

            flash(f"{invitee.username}에게 직원초대({role.name})를 보냈습니다.", category='is-success')

    # return redirect(url_for('admin.user'))
    return redirect(redirect_url())


@admin_bp.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_edit(id):
    # 1) user기본정보는, employee 1:1 subquery로서 바로 찾을 수 있기 때문에 조회는 생략한다.
    # employee화면에서는, employee id를 보내주기 때문에 user_id와 별개로 id로 찾는다.
    with DBConnectionHandler() as db:
        employee = db.session.get(Employee, id)
    # 2) employeeForm이 수정form일땐, role선택여부를 위해 g.user가 고용주로 들어가며
    #   기본정보인 user정보를 채우기 위해, user도 들어간다.

    #### 직원관련 수정 등은, role구성이 자신이하로만 구성되므로, 조건을 확인하여, 아니면 돌려보내보자
    if not employee.user.role.is_under(g.user.role):
        flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
        return redirect(redirect_url())

    # 항상 수정form을 만드는 user / employform의 수정form인 employee= / role이 1개가 아니라, g.user이하의 role을 만드는 employer=
    form = EmployeeForm(employee.user, employee=employee, employer=g.user)

    if form.validate_on_submit():
        #### user ####
        user_info = {
            'email': form.email.data,
            'sex': form.sex.data,
            'phone': form.phone.data,
            'address': form.address.data,

            'role_id': form.role_id.data,
        }
        user = employee.user
        user.update(user_info)

        f = form.avatar.data
        if f != user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)
            delete_uploaded_file(directory_and_filename=user.avatar)
            user.avatar = f'avatar/{filename}'

        #### employee ####
        employee_info = {
            'name': form.name.data,
            'sub_name': form.sub_name.data,
            'birth': form.birth.data,
            'join_date': form.join_date.data,
            'job_status': form.job_status.data,
            #### 수정된 user객체를 넣어준다
            'user': user,
            #### 생성시에 없었던, job_status와, resign_date를 넣어준다
            # 'job_status': form.job_status.data,
            # 'resign_date': form.resign_date.data,
        }
        employee.update(employee_info)

        with DBConnectionHandler() as db:
            db.session.add(employee)
            db.session.commit()
            print(employee.user.role_id)
            flash("직원 수정 성공", category='is-success')

        return redirect(url_for('admin.employee'))

    return render_template('admin/employee_form.html',
                           form=form
                           )
