import json
import random
import re

from flask import Blueprint, render_template, request, url_for
from sqlalchemy import select, and_, extract, or_

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Post, Category, Tag, Banner, PostPublishType
from src.infra.tutorial3.common.pagination import paginate

main_bp = Blueprint("main", __name__, url_prefix='/main')



@main_bp.route("/")
def index():
    # ip test
    return f'{request.headers}'
    client_ip = request.headers.get('X-Real-IP') or \
                request.headers.get('X-Forwarded-For', '').split(',')[0] or\
                request.remote_addr
    return f'You Ip Address is {client_ip}'


    page = request.args.get('page', 1, type=int)

    pagination = Post.order_by('-add_date').paginate(page, per_page=9)
    post_list = pagination.items

    # 공용 이미지
    img_path_list = [f'img/post/post-{i}.jpg' for i in range(1, 15 + 1)]
    for post, img_path in zip(post_list, random.sample(img_path_list, k=len(post_list))):
        post.img = img_path

    # banner to json
    banner_list = Banner.order_by('-is_fixed', '-add_date') \
        .limit(5) \
        .all()

    # baner객체들을 img, url만 가진 dict_list로 변환
    banner_list = [{
        'img': f'{url_for("download_file", filename=banner.img)}',
        'url': banner.url,
        'desc': banner.desc,
    }
        for banner in banner_list]

    return render_template('main/index.html', post_list=post_list, pagination=pagination,
                           banner_list=banner_list)


# @main_bp.route("/")
# def index():
#     # post_list = [1, 2, 3, 4, 5, 6]
#     page = request.args.get('page', 1, type=int)
#
#     stmt = select(Post).order_by(Post.add_date.desc())
#     pagination = paginate(stmt, page=page, per_page=9)
#
#     post_list = pagination.items
#
#     # 이미 내장된 img의 경로를 db에 존재하지 않는 필드지만 동적으로 삽입
#     # -> error가능성) sample의 k보다 post가 많아지는 경우? 해당이 안될 수 있다.
#     img_path_list = [f'img/post/post-{i}.jpg' for i in range(1, 15 + 1)]
#     for post, img_path in zip(post_list, random.sample(img_path_list, k=len(post_list))):
#         post.img = img_path
#
#     ## banner to json
#     stmt = select(Banner).order_by(Banner.is_fixed.desc(), Banner.add_date.desc()) \
#         .limit(5)
#     with DBConnectionHandler() as db:
#         banner_list = db.session.scalars(stmt).all()
#     # baner객체들을 img, url만 가진 dict_list로 변환
#     banner_list = [{
#         'img': f'{url_for("download_file", filename=banner.img)}',
#         'url': banner.url,
#         'desc': banner.desc,
#
#     }
#         for banner in banner_list]
#     # json.load()로 읽어올 것이 아니라면, ensure_ascii=False를 필수로 해줘야 view에서 한글로 받을 수 있다.
#     # banner_list = json.dumps(banner_list, ensure_ascii=False)
#     #### 새로운 방법: jinja로는 dictlist를 넘긴 뒤, vue의 데이터 초기화 코드에서, "{{ dict_list | tojson }}"의 문자열 + jinja + tojson필터를 이용한다.
#     # -> app._data.banner_list = JSON.parse('{{ banner_list | tojson }}')
#
#     return render_template('main/index.html', post_list=post_list, pagination=pagination,
#                            banner_list=banner_list)


# @main_bp.route("/category/<int:id>")
# def category(id):
#     # 1. category 찾기
#     with DBConnectionHandler() as db:
#         category = db.session.get(Category, id)
#
#     # 2. 딸린 posts 찾고, pagination적용
#     page = request.args.get('page', 1, type=int)
#     stmt = (
#         select(Post)
#         .where(Post.category_id == category.id)
#         .order_by(Post.add_date.desc())
#     )
#     pagination = paginate(stmt, page=page, per_page=10)
#     post_list = pagination.items
#
#     # print(category, post_list)
#
#     # 3. category + 딸린 post_list 한꺼번에 반환
#     # 4. categories(app_menu)와 상시비교되지만 평소에는 None으로 표기안됨. 진입시만 표기되로고
#     #    category.id == category_id로 비교할 현재 category_id 넘겨주기
#     return render_template('main/category.html',
#                            category=category,
#                            post_list=post_list, pagination=pagination,
#                            category_id=category.id
#                            )

@main_bp.route("/category/<int:id>")
def category(id):
    # 상위entity인 category 자체 설명
    category = Category.get(id)

    page = request.args.get('page', 1, type=int)

    # category에 딸린 posts들
    # - 각각은 부모인 category 정보를(필터링 뿐만 아니라. post.category.name)을 사용함.
    # - 각각은 딸린 tags정보를
    pagination = Post.load({'category': 'selectin', 'tags': 'joined'}) \
        .filter_by(category___id=id) \
        .order_by('-add_date') \
        .paginate(page, per_page=10)

    post_list = pagination.items

    return render_template('main/category.html',
                           category=category,
                           post_list=post_list, pagination=pagination,
                           category_id=id
                           )


# # 1) 상위entity를 타고 들어가야하는 소속된 하위 entity의 url은 /상위entity/상위entity_id/ + /자신_id로 구성한다
# # -> 단독 entity/id는 이미 admin_route에서 가지기 때문
# @main_bp.route("/category/<int:category_id>/<int:id>")
# def post_detail(category_id, id):
#     # 2) 타고 들어가는 하위의 경우, 부모도 먼저 찾고 -> 나 찾기
#     with DBConnectionHandler() as db:
#         category = db.session.get(Category, category_id)
#         #### cateogory.posts에서  넘어온 post의 id로 post객체를 골라낼 수 있다.
#         # post = [cate_post for cate_post in  category.posts if cate_post.id == id][0]
#         # -> 하지만, lazy로 찾은 객체를 view에 넘겨서 post.title 등을 사용하면 session연결이 끊긴 객체라 뜬다.
#         # -> view에 넘겨줄 객체는 한번 더 찾자.
#         post = db.session.get(Post, id)
#
#         # 3) detail에서 이전글, 다음글을 [1]해당category안에서 [2]id작은것들 가장 큰 것(역순1번째) [2] id큰것들 중 정순 1번재를 찾으면 된다.
#         # ==> 이미 찾아놓은 category, post를 stmt로 쿼리날리면, 경고가 뜬다. 이미 .post와 post.category로 연결된 사이라고
#         # -> category.posts를 이용해서 필터링해서 이전글을 찾는다.
#         prev_posts = sorted([cate_post for cate_post in category.posts if cate_post.id < post.id],
#                             key=lambda x: x.id, reverse=True)
#         next_posts = sorted([cate_post for cate_post in category.posts if cate_post.id > post.id],
#                             key=lambda x: x.id)
#         # 필터링안걸리면 빈list로서 [0] 첫번째 객체를 indexing할 수없기 때문에 조건문으로 준다.
#         prev_post = prev_posts[0] if prev_posts else None
#         next_post = next_posts[0] if next_posts else None
#         ## sqlawarning -> 이미 lazy된 객체끼리 또 조회해서 비교한다고
#         # prev_stmt = select(Post)\
#         #     .where(and_(Category.id == post.category_id, Post.id < post.id))\
#         #     .order_by(Post.id.desc())\
#         #     .limit(1)
#         # next_stmt = select(Post)\
#         #     .where(and_(Category.id == post.category_id, Post.id > post.id))\
#         #     .order_by(Post.id.asc())\
#         #     .limit(1)
#         # prev_post = db.session.scalars(prev_stmt).first()
#         # next_post = db.session.scalars(next_stmt).first()
#
#     # print(post, prev_posts, next_posts)
#
#     return render_template('main/post_detail.html',
#                            category=category, post=post,
#                            prev_post=prev_post, next_post=next_post)
#

# 1) 상위entity를 타고 들어가야하는 소속된 하위 entity의 url은 /상위entity/상위entity_id/ + /자신_id로 구성한다
# -> 단독 entity/id는 이미 admin_route에서 가지기 때문
@main_bp.route("/category/<int:category_id>/<int:id>")
def post_detail(category_id, id):
    # 2) 타고 들어가는 하위의 경우, 부모도 먼저 찾고 -> 나 찾기

    post = Post.load({'category': 'selectin', 'tags': 'joined'}) \
        .filter_by(id=id).first()

    # limit 이전 글의 갯수
    prev_post = Post.filter_by(
        category___id=category_id,
        id__lt=id,
    ).order_by('-id') \
        .limit(1) \
        .first()

    # limit 다음 글의 갯수
    next_post = Post.filter_by(
        category___id=category_id,
        id__gt=id,
    ).order_by('id') \
        .limit(1) \
        .first()

    return render_template('main/post_detail.html',
                           post=post,
                           prev_post=prev_post, next_post=next_post)


# @main_bp.context_processor
# def inject_archive():
#     with DBConnectionHandler() as db:
#         ## archive
#         # 1) post를 시간 역순 for 최신글 정렬해놓고 -> 생성일add_date에서 %Y년 %월의 string으로 변경한 다음
#         # -> 년 월일 추출이므로 역순으로 정렬해도 상관없다. -> 아니? archive목록에 시간역순으로 구성되어야하므로 역순으로 뽑는게 맞다.
#         # 2) set으로 중복을 제거한 dates를 준비한다.
#         posts = db.session.scalars(select(Post).order_by(Post.add_date.desc())).all()
#         # https://onlytojay.medium.com/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%82%A0%EC%A7%9C-%ED%91%9C%ED%98%84-%ED%95%9C%EA%B8%80-%EC%97%90%EB%9F%AC-44aea1ae66d8
#         date_format = '%Y년 %m월'.encode('unicode-escape').decode()
#         dates = set(post.add_date.strftime(date_format).encode().decode('unicode-escape') for post in posts)
#
#         ## tags
#         tags = db.session.scalars(select(Tag)).all()
#         # 3) entity 모델객체에, html에서 필요한 요소들을 동적으로 필드를 만들어서 보내줄 수 있다.
#         # -> html쓸 꾸며주는 class를 객체.style = [] 리스트로 넣어서 보내고, html에서는 | random()으로 1개르 뽑아서 쓴다.
#         for tag in tags:
#             tag.style = ['is-success', 'is-danger', 'is-black', 'is-light', 'is-primary', 'is-link', 'is-info',
#                          'is-warning']
#
#     ## new_posts
#     # -> 역순으로 정렬된 상태이므로 limit(flask) or 인덱싱으로 추출만 하면 된다.
#     new_posts = posts[:5]
#     # print(new_posts)
#
#     return dict(dates=dates, tags=tags, new_posts=new_posts)

date_format = '%Y년 %m월'.encode('unicode-escape').decode()

@main_bp.context_processor
def inject_archive():
    # Archive route용 모든 Post들의 출판일(pub_date)에서 -> [0000년 00월] 추출
    # -> archive route는 [0000년 00월]에서 숫자를 추출해서 extact('날짜단위', )로 필터링해서 조회할 수 있게 된다.
    posts = Post.filter_by(type=PostPublishType.SHOW).order_by('-pub_date').all()
    # https://onlytojay.medium.com/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%82%A0%EC%A7%9C-%ED%91%9C%ED%98%84-%ED%95%9C%EA%B8%80-%EC%97%90%EB%9F%AC-44aea1ae66d8

    dates = set(post.pub_date.strftime(date_format).encode().decode('unicode-escape')
                for post in posts)

    # archieve와 별개로 역순 정렬된 posts에서 최근5개 포스트 추출
    new_posts = posts[:5]

    # tag들을 뽑되, 동적으로 .style 필드를 줘서, view에서 이용한다.
    tags = Tag.all()
    for tag in tags:
        tag.style = ['is-success', 'is-danger', 'is-black', 'is-light', 'is-primary', 'is-link', 'is-info',
                     'is-warning']

    return dict(dates=dates, tags=tags, new_posts=new_posts)


# @main_bp.route('/category/<string:date>')
# def archive(date):
#     # 1) 정규표현식으로 년 4글자(%Y)와 월2글자(%m)을 추출한다
#     # http://localhost:5000/main/category/2020년10월
#     # -> ['2020', '10']
#     # 1월은 안나오고 01월을 해야 추출된다.
#     # 혹시 몰라서 뒤에것은 d{1,2}로 수정
#     # -> 이 때, 추출단위마다 |를 씌워야, list에서 개별변수로 인식하며, 해당하는 것들을 순서대로 다찾는다
#     # -> 단, 추가발견되면 추가로 나온다  ex>  2020년1월1010일 -> ['2020', '1', '1010']
#     # regex = re.compile(r'\d{4}|\d{2}')
#     regex = re.compile(r'\d{4}|\d{1,2}')
#     dates = regex.findall(date)
#
#     # 3) 이제 dates['2022', '01']을 이용하여 posts를 골라낸다
#     # -> add_date 타입에 대해 extract('year', ) 'month'를 활용해서 where조건을 만든다.
#     page = request.args.get('page', 1, type=int)
#     stmt = (
#         select(Post)
#         .where(and_(
#             extract('year', Post.add_date) == int(dates[0]),
#             extract('month', Post.add_date) == int(dates[1]),
#         ))
#         .order_by(Post.add_date.desc())
#     )
#     pagination = paginate(stmt, page=page, per_page=10)
#     post_list = pagination.items
#
#     # 2) breadcrumb를 위해 path로 온 하위의 의미인 date도 같이 넘겨준다
#     # -> 또한, page내이션으로 같은 route를 방문해야하기 때문에, date를 그대로 가져간다
#     return render_template('main/archive.html', date=date,
#                            post_list=post_list, pagination=pagination
#                            )



# '2021년 03월' 에서 숫자4개짜리 + 숫자1~2개짜리를 각각 추출하는 yyyy_mm_compiler
# -> yyyy_mm_compiler.findall( 대상 ) -> ['2021', '03']
yyyy_mm_compiler = re.compile(r'\d{4}|\d{1,2}')

@main_bp.route('/category/<string:date>')
def archive(date):
    page = request.args.get('page', 1, type=int)

    # 1) 정규표현식으로 년 4글자(%Y)와 월2글자(%m)을 추출한다 -> ['2021', '03']
    #    각각을 int로 바꾼 뒤, tuple -> unpacking한다.
    year, month = tuple(map(lambda x: int(x), yyyy_mm_compiler.findall(date)))

    # posts의 필터에 yyyy 필터 + mm필터를 각각 걸어서 해당하는 posts들만 추출한다.
    pagination = Post.load({'category':'selectin', 'tags': 'joined'}).filter_by(
        type=PostPublishType.SHOW,
        pub_date__year=year,
        pub_date__month=month
    ).order_by('-pub_date') \
        .paginate(page, per_page=10)

    post_list = pagination.items

    # 2) breadcrumb를 위해 path로 온 하위의 의미인 date도 같이 넘겨준다
    # -> 또한, page내이션으로 같은 route를 방문해야하기 때문에, date를 그대로 가져간다
    return render_template('main/archive.html', date=date,
                           post_list=post_list,
                           pagination=pagination
                           )

@main_bp.route('/tag/<int:id>')
def tag(id):
    page = request.args.get('page', 1, type=int)

    tag = Tag.get(id)
    pagination = Post.load({'category':'selectin'}).filter_by(tags___id=id).paginate(page, per_page=10)
    post_list = pagination.items

    return render_template('main/tag.html', post_list=post_list, tag=tag,
                           pagination=pagination)


@main_bp.route('/search')
def search():
    page = request.args.get('page', 1, type=int)
    word = request.args.get('word', '', type=str).strip()
    pagination = Post.load({'category':'selectin', 'tags':'joined'})\
        .filter_by(or_=dict(title__contains=word, content__contains=word))\
        .paginate(page, per_page=10)

    post_list = pagination.items

    return render_template('main/search.html', post_list=post_list, pagination=pagination, word=word)

# @main_bp.route('/search')
# def search():
#     page = request.args.get('page', 1, type=int)
#     word = request.args.get('word', '', type=str)
#
#     # breadcrumb를 위해 들어온 순수 word와 별개의 변수로 정의
#     search_word = f'%{word}%'
#     stmt = (
#         select(Post)
#         .where(or_(
#             Post.title.like(search_word),
#             Post.content.like(search_word),
#         ))
#     )
#     pagination = paginate(stmt, page=page, per_page=10)
#     post_list = pagination.items
#
#     return render_template('main/search.html', post_list=post_list, pagination=pagination, word=word)
