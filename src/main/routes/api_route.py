from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, flash, url_for, redirect
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload, subqueryload, immediateload, aliased, lazyload
from sqlalchemy.orm.strategy_options import contains_eager

from src.config import db_config
from src.infra.commons import paginate
from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Comment, Menu
from src.main.forms import CommentForm, ReplyForm

api_routes_bp = Blueprint("api_routes", __name__)


@api_routes_bp.route("/api", methods=["GET"])
def something():
    return jsonify({"abcd": "abcd"})


@api_routes_bp.route("/explore", methods=["GET", "POST"])
def explore():
    comment_form = CommentForm()
    reply_form = ReplyForm()

    with DBConnectionHandler() as db:
        stmt = (
            select(Comment)
            .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
            .order_by(Comment.thread_timestamp.desc(), Comment.path.asc(), Comment.id.asc())
        )

        # select()객체, execute(), scalars()모두 paginate()메서드가 없음
        ## => 내가 정의해야한다.
        ## => 함수로 정의해야 route에서 page를 stringquery변수로 받아올때 처리가 편하다
        ## => page는 1번부터 시작하게 한다.
        ## => 데이터가 없을 때는, 404에러를 내어야하는데, 지금은 []빈 데이터가 넘어가는 경우 아예 표시되지 않는다.
        ##   (for순회의 힘)
        # the page number, starting from 1
        # the number of items per page
        # an error flag. If True, when an out of range page is requested a 404 error will be automatically returned to the client. If False, an empty list will be returned for out of range pages.
        page = request.args.get('page', 1, type=int)
        # stmt = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)
        # comments = db.session.scalars(stmt).all()
        # 1) comments객체 대신 pagination객체를 받아와서 -> comments key에 pagination.items를 넘겨준다
        comment_pagination = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)

    # 2) prev_url, next_url 객체를 url_for()를 이용해 미리 만들어서 같이 넘겨준다.
    #   (만약 미리 만들지 않으면, view(html)에서 pagination객체를 받아 .속성을 이용해 url_for()를 만들어야 해서 복잡?)
    # => 여기서는 view에는 pagination객체 말고, entity객체와 url_for객체를 미리 만들어서 넘겨주자
    # 2-1) if .has_next 면 .next_num을 page=keyword에 넣어서 url_for객체를,
    #     아니면 None을 넣어서 next_url객체를 만든다.
    next_url = url_for('api_routes.explore', page=comment_pagination.next_num) \
        if comment_pagination.has_next else None
    prev_url = url_for('api_routes.explore', page=comment_pagination.prev_num) \
        if comment_pagination.has_prev else None

    with DBConnectionHandler() as db:
        stmt = (
            select(Comment)
            .where(Comment.id == 1)
        )
        comments2 = db.session.scalars(
            stmt
        ).all()

    # 3) 만들어준 pages + 현재page번호를 필드도 같이 넘겨준다.
    return render_template("menu/comment.html"
                           , comment_form=comment_form
                           , reply_form=reply_form
                           , comments=comment_pagination.items
                           , next_url=next_url
                           , prev_url=prev_url
                           , current_page=comment_pagination.page
                           , pages=comment_pagination.pages
                           , comments2=comments2
                           )


@api_routes_bp.route("/comments", methods=["GET", "POST"])
def index():
    comment_form = CommentForm()
    reply_form = ReplyForm()

    if request.method == 'POST' and comment_form.validate_on_submit():
        author = comment_form.author.data
        text = comment_form.text.data

        comment = Comment(text=text, author=author)
        comment.save()

        flash("comment posted", "success")

    with DBConnectionHandler() as db:
        stmt = (
            select(Comment)
            .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
            .order_by(Comment.thread_timestamp.desc(), Comment.level, Comment.timestamp.desc())
        # (특정최상위 선택안할시 그룹칼럼별), level별, 원하는 순서
        )
        page = request.args.get('page', 1, type=int)
        # stmt = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)

        comment_pagination = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)

        # comments2 = db.session.scalars(select(Comment).options(joinedload(Comment.replies)).where(Comment.id == 1)).all()
        # https://stackoverflow.com/questions/47243397/sqlalchemy-joinedload-filter-column

        # lazy='joined')
        stmt = (
            select(Comment)
            # .options(
            ## backref parent +  remoste_side가 없으면,
            # lazy=subquery + join_depth=6에
            # + select만으로 options없이 다됨.

            ## 한꺼번에 보내기 위해.relatinoship lazy dynamic -> 생략
            ## joinedload를 하면 on절 2개를 유추하나본다 ->  unique() method에러가 난다고 한다.
            ## subqueryload밖에 없는데 1번만하면, depth1만 지정하게 된다.
            ## selectin도 여러번 하면 가능 depth1만 지정하게 된다.
            # selectinload("replies")
            # FK에 uniquekey를 주고, joinedload는 unique() method에러는 안나나 ->( backref (parent-one)로 도전) => 여러개 걸어도 detach걸림
            # joinedload(Comment.replies, aliase=True)

            ## 찾았따.. (1) lazy로 subquery로 걸어놓고
            ##         (2) join_depth = 6 으로 주면, subquery든 selectinload든 1번만 걸어주면 자체참조 알아서 깊이만큼해준다.

            # selectinload("replies")
            # subqueryload("replies")
            ## 공식문서 마지막: https://docs.sqlalchemy.org/en/20/orm/self_referential.html#composite-adjacency-lists

            # .selectinload("replies")
            # .selectinload("replies")
            # .selectinload("replies")
            # .selectinload("replies")
            # .selectinload("replies")
            # .joinedload("parent")
            # .joinedload("parent")
            # .joinedload("parent")
            # .joinedload("parent")
            # .joinedload("parent")
            ## depth만큼 안해주면
            # .DetachedInstanceError: Parent instance
            # .selectinload("replies")
            # .selectinload("replies")
            # .selectinload("replies")
            # .selectinload("replies")
            # .subqueryload(Comment.replies)
            # .subqueryload(Comment.replies)
            # .subqueryload(Comment.replies)
            # .subqueryload(Comment.replies)
            # .subqueryload(Comment.replies)
            # )\
            .where(Comment.id == 1)
        )
        # print(stmt)

        comments2 = db.session.scalars(
            stmt
        ).all()
        # comments2 = db.session.scalars(select(Comment).options(joinedload(Comment.replies)).where(Comment.id == 1)).all()
        # comments2 = db.session.scalars(select(Comment).options(selectinload(Comment.replies)).where(Comment.id == 1)).all()
        # comments2 = db.session.scalars(select(Comment).options(subqueryload(Comment.replies)).where(Comment.id == 1)).all()
        # -> The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections
        # -> The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections
        # -> The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections
        # -> The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections

        ## lazy='dynamic')
        # -> Neither 'InstrumentedAttribute' object nor 'Comparator' object associated with Comment.replies has an attribute '__name__'
        # -> 'Comment.replies' does not support object population - eager loading cannot be applied.
        # -> 'Comment.replies' does not support object population - eager loading cannot be applied.
        # -> 'Comment.replies' does not support object population - eager loading cannot be applied.

        ##
        # def is_parent(self):
        #     return self.parent_id == self.id
        # To obtain the siblings of an issue you can write a custom query that gets all the issues that have the same parent_id except the one the query is issued on:
        #
        # def get_siblings(self):
        #     return Issue.query.filter(Issue.parent_id == self.parent_id, Issue.id != self.id).all()

    # 2) prev_url, next_url 객체를 url_for()를 이용해 미리 만들어서 같이 넘겨준다.
    #   (만약 미리 만들지 않으면, view(html)에서 pagination객체를 받아 .속성을 이용해 url_for()를 만들어야 해서 복잡?)
    # => 여기서는 view에는 pagination객체 말고, entity객체와 url_for객체를 미리 만들어서 넘겨주자
    # 2-1) if .has_next 면 .next_num을 page=keyword에 넣어서 url_for객체를,
    #     아니면 None을 넣어서 next_url객체를 만든다.
    next_url = url_for('api_routes.index', page=comment_pagination.next_num) \
        if comment_pagination.has_next else None
    prev_url = url_for('api_routes.index', page=comment_pagination.prev_num) \
        if comment_pagination.has_prev else None

    # 3) 만들어준 pages + 현재page번호를 필드도 같이 넘겨준다.
    return render_template("menu/comment.html", comments=comment_pagination.items, comments2=comments2
                           , comment_form=comment_form
                           , reply_form=reply_form
                           , next_url=next_url
                           , prev_url=prev_url
                           , current_page=comment_pagination.page
                           , pages=comment_pagination.pages
                           )


@api_routes_bp.route("/comments/<int:comment_id>", methods=["POST"])  # ,strict_slashes=False)
def register_reply(comment_id):
    reply_form = ReplyForm()

    if request.method == 'POST' and reply_form.validate_on_submit():
        author = reply_form.author.data
        text = reply_form.text.data

        # comment = Comment(text=text, author=author)
        with DBConnectionHandler() as db:
            stmt = (
                select(Comment)
                .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
                .where(Comment.id == comment_id)
            )
            parent = db.session.scalars(stmt).one()

        reply = Comment(parent=parent, text=text, author=author)
        reply.save()

        flash("reply posted", "success")
        return redirect(url_for('api_routes.index'))


@api_routes_bp.route("/comments/<int:comment_id>")  # ,strict_slashes=False)
def delete_comment(comment_id):
    print(f"delete comment {comment_id}")

    with DBConnectionHandler() as db:
        stmt = (
            select(Comment)
            .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
            .where(Comment.id == comment_id)
        )
        target = db.session.scalars(stmt).one()
        # print(target)
        db.session.delete(target)
        db.session.commit()

        flash("comment delete with children", "success")
    return redirect(url_for('api_routes.index'))


@api_routes_bp.route("/menu", methods=["GET", "POST"])
def menu():
    with DBConnectionHandler() as db:
        stmt = (
            select(Menu)
            .where(Menu.level == 0)  # subquery로 다가져올테니, 최상위만 일단 불러온다.
            .order_by(Menu.thread_timestamp.asc(), Menu.level, Menu.path.asc())
        # 자기참조테이블의 전체조회는 (1) (생성순)그룹칼럼으로 모으고 (2)level(hybrid)별 (3) 원하는 칼럼순- > level_seq를 추가할 듯
        )
        menus = db.session.scalars(stmt).all()

        # flash(f"endpoint loading", "success")
    # m111 ~4

    return render_template('menu/navbar_jinja.html', menus=menus)