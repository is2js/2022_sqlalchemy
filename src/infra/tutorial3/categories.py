import datetime
import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, BigInteger, Boolean, func, select, or_
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, backref, Session

from src.infra.tutorial3.common.base import BaseModel  # , IntEnum
from src.infra.tutorial3.common.int_enum import IntEnum
from src.infra.config.base import Base
from src.main.templates.filters import feed_datetime


class Category(BaseModel):
    __tablename__ = 'categories'
    __repr_attrs__ = ['name']

    ko_NAME = '카테고리'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    icon = Column(String(128), nullable=True)

    posts = relationship('Post',  # backref=backref('category', lazy='subquery'),
                         back_populates='category',
                         # cascade="all, delete",  # 방법1)
                         passive_deletes=True,
                         # 해결책2 - 자식FK애 ondelete='CASCADE' 이후 부모relationshio에 이것을 주면, 부모만 삭제하고, 나머지는 DB가 수동적 삭제한다
                         # lazy=True
                         )

    @classmethod
    def insert_categories(cls, session=None, auto_commit=True):
        # 2) role dict묶음을 돌면서, 이미 존재하는지 조회하고, 없을 때 Role객체를 생성하여 role객체를 유지한다
        if not session:
            session = cls.get_scoped_session()

        name_and_icons = [
            ('잡담', 'grey is-light'),
            ('질문', 'success is-light'),
            ('인사', 'info is-light'),
            ('자료', 'warning'),
            ('회의', 'warning is-light'),
            ('공지', 'danger is-light'),
            ('메인일정(캘린더)', 'danger'),
            ('사건/사고', 'dark'),
        ]
        for name, icon in name_and_icons:
            Category.create(
                name=name, icon=icon,
                session=session, auto_commit=False
            )

        if auto_commit:
            session.commit()


posttags = Table('posttags', Base.metadata,
                 Column('tag_id', Integer().with_variant(BigInteger, "postgresql"), ForeignKey('tags.id'),
                        primary_key=True, nullable=False),
                 Column('post_id', Integer().with_variant(BigInteger, "postgresql"), ForeignKey('posts.id'),
                        primary_key=True,
                        nullable=True,  # 임시 삭제용
                        ),
                 mysql_engine='InnoDB',
                 mysql_charset='utf8mb4',
                 comment='Post-Tag 관계테이블'
                 )


# class PostPublishType(enum.Enum):
class PostPublishType(enum.IntEnum):
    #### outerjoin 조인으로 들어왔을 때, 해당 칼럼에 None이 찍히는데, -> 0을 내부반환하고, 그것을 표시할 DEFAULT NONE 상수를 필수로 써야한다.
    NONE = 0
    ## IntEnum을 Post의 필드타입으로 정의한 순간, db는 int지만, 객체에서는 enum의 필드명으로 모든게 표시될 예정이므로 한글로 바꿔봄.
    DRAFT = 1  # DRAFT
    SHOW = 2  # release

    # forms.py에서 radio의 choices로 들어갈 tuple list 를 (.value, .name)으로 반환해주면   html에서는  subfield.data, subfield.label로 사용할 수 있다.
    # https://michaelcho.me/article/using-python-enums-in-sqlalchemy-models
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]

    # forms.py에서 radio의 coerce(형변환)
    # => 이것은 커스텀 IntEnum 필드로서 알아서 post.has_type = 에 form에서 올라온 int value를 집어넣으면,
    #    알아서 process_result_value메서드에 의해 -> int면 self._enumtype(value)을 통한 enum객체로 변환된다.
    #    (원래 db속 int value -> enum객체로 변환하는 메서드인데, form에서 올라오서 필드에 대입해도 알아서 처리해주는 듯 하다)
    # https://stackoverflow.com/questions/44078845/using-wtforms-with-enum
    # @classmethod
    # def coerce(cls, item):
    #     # form에서 올라올 값 -> int가 "1" string data로 올라옴
    #     # ( .value, .name)이 => value="" {{subfield.data}}, label="" {{subfield. label}} 로 채우고 -> route로는 .datadp   .value의 string이 올라온다. 1 -> "1"
    #     # -> coerce는 int면 바로  "1" -> 1이 되겠지만, 객체 생성에 있어서는, enum.필드를 넣어줘야한다?
    #
    #     item = int(item)
    #     field_list = [field for field in cls if field.value == item]
    #     print(field_list)
    #     if len(field_list) > 0:
    #         return field_list[0]
    #     else:
    #         raise ValueError(file'{cls.__name__}을 선택해주세요.')


class Post(BaseModel):
    __tablename__ = 'posts'
    __repr_attrs__ = ['title']
    ko_NAME = '게시글'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    title = Column(String(128), nullable=False)
    desc = Column(String(200), nullable=False)
    content = Column(Text().with_variant(String(3000), 'mysql'), nullable=False)
    # has_type = Column(Enum(PostPublishType), server_default='show', nullable=False)
    # IntEnum을 TypeDecorator로 정의해놓고 그 타입으로 써야한다.
    # has_type = Column(Enum(PostPublishType), server_default=PostPublishType.show.value, nullable=False)
    ## => 여기서 server_default= 로 enum을 주면 에러가 발생함.

    ### 1) Integer Type + 변수만 enum + form에서 enum으로 같이 뿌려주기 성공하고나서
    # has_type = Column(Integer, default=PostPublishType.SHOW, nullable=False)
    ### 2) IntEnum( Enumclass ) + view에서 post.has_type.name + .value로 사용가능해진다.
    # -> server_default는 int로 반영되어야한다. default=로만 줘야한다.
    has_type = Column(IntEnum(PostPublishType), default=PostPublishType.SHOW.value, nullable=False)

    # 해결책1) many에 ondelete를 줘야 db제약조건과 동일해지지만, 부모삭제시 set null을 기본 수행한다
    category_id = Column(Integer().with_variant(BigInteger, "postgresql"),
                         ForeignKey('categories.id',
                                    ondelete="CASCADE"),
                         # nullable=False,
                         # name='post_category_id'
                         )

    category = relationship('Category', foreign_keys=[category_id], back_populates='posts')

    tags = relationship('Tag', secondary=posttags,
                        # lazy='subquery',
                        # lazy='subquery', join_depth=2,  # (front) for post -> post.tags -> tags |join(',')
                        # backref=backref('posts', lazy=True)
                        # backref=backref('posts', lazy='subquery'),  # tag -> (front) tag.posts 해결
                        )

    # 등록안된 ip일 때만 증가하는 조회수 칼럼 추가
    view_count = Column(Integer().with_variant(BigInteger, "postgresql"), default=0)

    # cascade delete 1: Fk에 DB레벨 제약조건을 on~ 으로 준다.
    # cascade delete 2: one의 relationship에 passive_delets=True를 줘서, DB에게 cascade를 맞긴다.
    post_counts = relationship('PostCount', passive_deletes=True)  # , back_populates='post')

    # 글 작성자(직원) fk 칼럼 추가
    author_id = Column(Integer().with_variant(BigInteger, "postgresql"),
                       ForeignKey('employees.id', ondelete="CASCADE"),
                       nullable=True,  # 임시 삭제용
                       )
    # Many create시  one객체로 fill하려면, Many -> One의 relation 추가
    author = relationship('Employee', foreign_keys=[author_id], back_populates='posts', uselist=False)

    # 댓글(many)에 대한 relationship for passive_deletes
    comments = relationship('Comment', passive_deletes=True, back_populates='post')

    @hybrid_method
    def type(cls, type_enum, mapper=None):
        mapper = mapper or cls
        return mapper.has_type == type_enum.value

    @hybrid_property
    def comment_count(self):
        return len(self.comments)

    # # refactor
    # @hybrid_method
    # def is_author_below_to(cls, department, mapper=None):
    #     """
    #     1번 부서 -> 1번부서의 자식부서들에 속한 작성자들의 -> Post
    #
    #     Post.filter_by(
    #         is_author_below_to=Department.get(1)
    #     ).all()
    #     ----
    #     [<Post#1 'test'>, <Post#2 '오늘 업데이트 공지...'>, <Post#3 '오늘 재판 내용관련...'>, <Post#6 '질문입니다'>,
    #     """
    #     mapper = mapper or cls
    #     Author_ = mapper.author.mapper.class_
    #
    #     return mapper.author.has(
    #         Author_.is_below_to(department)
    #     )

    # refactor 2
    @hybrid_method
    def is_author_upper_department(cls, upper_department, mapper=None):
        """
        부서가 레벨0이면, 자식들의 id를 scalar 서브쿼리로 만들어서, In으로 필터링되게 한다
        부서가 레벨1이면, list에 담아서 in으로 필터링한다
        ----
        레벨0
        Post.filter_by(is_author_upper_department=Department.get(1)).all()
        [<Post#1 'zzzzzzzz'>, <Post#2 '2222'>, <Post#3 '333333333'>, <Post#4 '44444'>]

        레벨1
        Post.filter_by(is_author_upper_department=Department.get(2)).all()
        => [<Post#1 'zzzzzzzz'>, <Post#3 '333333333'>, <Post#2 '2222'>]
        """
        mapper = mapper or cls
        Author_ = mapper.author.mapper.class_

        # IN은 1개라도 list를 요구함.
        # level_1_ids = [upper_department.id]
        #
        # # level 0부서가 들어올 경우, scalar_subquery를 통해, 자식들의 id를 한큐에 구한 뒤, IN에 넣어준다
        # if upper_department.level == 0:
        #     Department_ = Author_.upper_department.mapper.class_
        #
        #     level_1_ids = select(Department_.id) \
        #         .where(
        #         or_(
        #             Department_.id == upper_department.id,
        #             Department_.parent_id == upper_department.id
        #         )
        #     ) \
        #         .scalar_subquery()
        #
        # return mapper.author.has(
        #     Author_.upper_department_id.in_(level_1_ids)
        # )
        return mapper.author.has(
            Author_.upper_department_id == upper_department.id
        )

    # refactor
    @hybrid_method
    def is_tagged_by(cls, tag, mapper=None):
        mapper = mapper or cls
        Tag_ = mapper.tags.mapper.class_
        return mapper.tags.any(Tag_.id == tag.id)


# Post Count 모델 작성
class PostCount(BaseModel):
    __tablename__ = 'postcounts'
    __repr_attrs__ = ['post_id']
    ko_NAME = '조회수'

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    ip = Column(String(30), nullable=False)

    # cascade delete 1: Fk에 DB레벨 제약조건을 on~ 으로 준다.
    # cascade delete 2: one의 relationship에 passive_delets=True를 줘서, DB에게 cascade를 맞긴다.
    post_id = Column(Integer().with_variant(BigInteger, "postgresql"),
                     ForeignKey('posts.id', ondelete="CASCADE"),
                     nullable=True,  # 임시 삭제용
                     )


class Comment(BaseModel):
    __tablename__ = 'comments'
    _N = 3  # path를 만들 때, 자를 단위
    _MAX_LEVEL = 2  # 첫자식을 1로 보는 join_depth 개념
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)

    # 부모 글
    post_id = Column(Integer().with_variant(BigInteger, "postgresql"), ForeignKey('posts.id', ondelete="CASCADE"),
                     nullable=True,  # 임시 삭제용
                     )
    post = relationship('Post', foreign_keys=[post_id], uselist=False, back_populates='comments')

    # 글 작성자(직원) fk 칼럼 추가
    author_id = Column(Integer().with_variant(BigInteger, "postgresql"),
                       ForeignKey('employees.id', ondelete="SET NULL"),
                       nullable=True
                       )
    # Many create시  one객체로 fill하려면, Many -> One의 relation 추가
    author = relationship('Employee', foreign_keys=[author_id], uselist=False,
                          # back_populates='comments',
                          )

    content = Column(Text().with_variant(String(3000), 'mysql'), nullable=False)

    parent_id = Column(Integer, ForeignKey('comments.id', ondelete='cascade'),
                       comment="상위 댓글 id",
                       nullable=True)
    parent = relationship('Comment', remote_side=[id], passive_deletes=True,
                          back_populates='replies',
                          )
    replies = relationship('Comment', order_by='Comment.path', back_populates='parent')

    status = Column(Boolean, comment='댓글 사용 상태(0 미사용, 1사용)', default=1)

    # dynamic field
    sort = Column(Integer, comment="댓글 순서", nullable=True)
    path = Column(Text().with_variant(String(100), 'mysql'), index=True, nullable=True)

    @hybrid_property
    def level(self):
        return len(self.path) // self._N - 1

    @level.expression
    def level(cls):
        return func.length(cls.path) / cls._N - 1

    @hybrid_property
    def avatar(self):
        return self.author.user.avatar

    @hybrid_property
    def author_name(self):
        return self.author.name

    @classmethod
    def create(cls, session: Session = None, auto_commit=True, **kwargs):
        parent_id = kwargs.get('parent_id', None)

        # 현재 댓글의 순서
        count_in_same_level = cls.filter_by(parent_id=parent_id).count()
        # if count_in_same_level >= cls._MAX_COUNT_IN_SAME_LEVEL:
        #     return False, '자식부서는 10개를 초과할 수 없습니다.'
        kwargs['sort'] = sort = count_in_same_level + 1

        # 부모기반 path만들기
        parent = cls.filter_by(id=parent_id).first()
        path_prefix = parent.path if parent else ''
        kwargs['path'] = path = path_prefix + f'{sort:0{cls._N}d}'

        # 레벨 제한
        level = len(path) // cls._N - 1
        if level > cls._MAX_LEVEL:
            return False, f'댓글의 깊이는 {cls._MAX_LEVEL}단계까지만 허용합니다.'

        return super().create(**kwargs)

    @classmethod
    def get_roots(cls, active=False, session: Session = None):
        """
        Comment.get_roots()

        [<Comment#1>, <Comment#2>, <Comment#3>]
        """
        obj = cls.filter_by(session=session, parent_id=None, post_id=None)
        if active:
            obj = obj.filter_by(status=True)

        return obj.order_by('path').all()

    @classmethod
    def get_tree_of_roots(cls, active=False, session: Session = None):

        roots = cls.get_roots(active=active, session=session)

        tree_list = []
        for root in roots:
            tree_list.append(
                root.to_dict2(
                    nested=cls._MAX_LEVEL, relations='replies', hybrid_attrs=True,
                    exclude=['path', 'pub_date'],
                    session=session
                )
            )

        return dict(data=tree_list)

    @classmethod
    def get_tree_from(cls, post_id, active=False, session: Session = None):
        # 최상위 comment - 특정 post_id에 소속된
        obj = cls.filter_by(session=session, parent_id=None, post_id=post_id)
        if active:
            obj = obj.filter_by(status=True)

        comments = obj.order_by('path').all()

        # comment들을 to_dict를 돌려 replies 포함시키기
        tree_list = []
        for comment in comments:
            tree_list.append(
                comment.to_dict2(
                    nested=cls._MAX_LEVEL, relations='replies', hybrid_attrs=True,
                    exclude=['path'],
                    session=session
                )
            )

        return dict(data=tree_list)

    # column내용과 일치하는 propery를 만들면 recursion에러난다.
    @hybrid_property
    def feed_add_date(self):
        return feed_datetime(self.add_date, is_feed=True, k=365)

    @hybrid_property
    def feed_pub_date(self):
        return feed_datetime(self.pub_date, is_feed=True, k=365)

    @hybrid_property
    def author_name(self):
        return self.author.name

    @hybrid_property
    def avatar(self):
        return self.author.user.avatar


# 작성자  유저 -> 해당그룹의 직원일 때만 -> 읽은사람에 추가
# class PostReader(BaseModel):
#     __tablename__ = 'postreaders'
#
#     id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
#     post_id = Column(Integer().with_variant(BigInteger, "postgresql"),
#                      ForeignKey('posts.id', ondelete="CASCADE"), )
#     employee_id


class Tag(BaseModel):
    __tablename__ = 'tags'
    ko_NAME = '태그'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    name = Column(String(128), nullable=False, unique=True)

    posts = relationship('Post', secondary=posttags, viewonly=True)

    def __repr__(self):
        # info: str = f"{self.__class__.__name__}" \
        info: str = f"{self.name}"
        return info
