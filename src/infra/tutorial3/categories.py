import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref

from src.infra.config.db_creator import engine
from src.infra.tutorial3.common.base import BaseModel  # , IntEnum
from src.infra.tutorial3.common.int_enum import IntEnum
from src.infra.config.base import Base


class Category(BaseModel):
    __tablename__ = 'categories'
    ko_NAME = '카테고리'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    icon = Column(String(128), nullable=True)

    posts = relationship('Post', backref=backref('category', lazy='subquery'),
                         cascade="all, delete",  # 방법1)
                         passive_deletes=True,  # 해결책2 - 이것을 주면, 부모만 삭제하고, 나머지는 DB가 수동적 삭제한다
                         lazy=True)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[name={self.name!r}]"
        return info


posttags = Table('posttags', Base.metadata,
                 Column('tag_id', Integer().with_variant(BigInteger, "postgresql"), ForeignKey('tags.id'), primary_key=True, nullable=False),
                 Column('post_id', Integer().with_variant(BigInteger, "postgresql"), ForeignKey('posts.id'), primary_key=True, nullable=False),
                 mysql_engine='InnoDB',
                 mysql_charset='utf8mb4',
                 comment='Post-Tag 관계테이블'
                 )


# class PostPublishType(enum.Enum):
class PostPublishType(enum.IntEnum):
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
    ko_NAME = '게시글'


    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    title = Column(String(128), nullable=False)
    desc = Column(String(200), nullable=False)
    content = Column(Text().with_variant(String(100), 'mysql'), nullable=False)
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
                         nullable=False,
                         # name='post_category_id'
                         )

    tags = relationship('Tag', secondary=posttags,
                        # lazy='subquery',
                        lazy='subquery', join_depth=2,  # (front) for post -> post.tags -> tags |join(',')
                        # backref=backref('posts', lazy=True)
                        backref=backref('posts', lazy='subquery'),  # tag -> (front) tag.posts 해결
                        )

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[title={self.title!r}]"
        return info


class Tag(BaseModel):
    __tablename__ = 'tags'
    ko_NAME = '태그'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    name = Column(String(128), nullable=False, unique=True)

    def __repr__(self):
        # info: str = f"{self.__class__.__name__}" \
        info: str = f"{self.name}"
        return info
