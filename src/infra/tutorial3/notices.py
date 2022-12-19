import datetime
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, select, and_

from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler


class BannerType(enum.Enum):
    """defining Banner Types"""

    MAIN = "main"
    MODAL = "modal"


class Notice(Base):
    __tablename__ = 'notices'

    id = Column(Integer, primary_key=True)
    is_sticky = Column(Boolean(), nullable=False)  # 항상 띄워두어야할 필수 공지냐
    is_banner = Column(Boolean())  # 배너용이냐? == 이미지도 있느냐
    title = Column(String(200), nullable=False)
    body = Column(Text)
    # body_html = Column(Text) # Bleach용

    hit = Column(Integer, nullable=False, default=0)
    # timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
    # 수정되는 날짜도 확인해야함. 수정자도 있어야 함.
    created_time = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_time = Column(DateTime, nullable=False, default=datetime.datetime.now)
    deleted_time = Column(DateTime, index=True)  # 삭제 되지 않은 프로젝트 검색시 쿼리 성능 향상을 위한 index

    banner_title = Column(String(30))
    # img_url -> 배너용 title 존재하면   banner/ + banner_title . png로 save()에서 자동으로 채워준다.
    img_url = Column(Text)
    banner_type = Column(Enum(BannerType))  # main용이냐, modal용이냐
    exp_start_date = Column(DateTime, index=True, default=datetime.datetime.now)
    exp_end_date = Column(DateTime)

    # 작성자 와 좋아요 -> 인증 전까지 생략
    # register_author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # change_author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # like = db.relationship('User', secondary=post_recommend, backref='like_posts')

    # (1) menu -> .save(self) 시 인스턴스메서드로서 add() flush() 후  self.객체필드 써서 추가필드 자동으로 작성되게 했었음.
    def save(self):
        with DBConnectionHandler() as db:
            try:
                db.session.add(self)
                if self.is_banner:
                    self.img_url = 'banner/' + self.banner_title + '.png'
                db.session.commit() 
                
                return self
            except Exception as e:
                db.session.rollback()
                raise e

    # (2) .get(cls, id, is_delete) -> soft delete적용시 안지워진 것만 가져오게 하기 위해, 별로의 get메서드가 들어간다.
    #    -> cls로 Entity.is_delete필드를 where조건에 넣어서   객체들을 가져온다. <-> self는 현재 객체상태에서...
    @classmethod
    def get(cls, notice_id, is_delete=False):
        # IS NULL, IS NOT NULL은  python None과 비교하면 된다.
        # .filter(User.name != None)
        # -> Entity.칼럼.is_()  와 .isnot( ) 도 존재한다.
        delete_condition = cls.deleted_time.is_(None) if not is_delete else cls.deleted_time.isnot(None)

        stmt = (
            select(cls)
            .where(and_(
                cls.id == notice_id,
                delete_condition
            ))
        )

        with DBConnectionHandler() as db:
            return db.session.scalars(stmt).all()

    # (3) .update는 update_time 을 고려하여 정의하며,  인스턴스메서드로서, entity객체가 select된 상황에서, 객체.update()를 쳐준다.
    def update(self, **kwargs):
        """Update instance attributes from dictionary.
        Key and value validation should be performed beforehand!
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.updated_time = datetime.datetime.now()

        with DBConnectionHandler() as db:
            # 객체 내부에서 read를 제외한 것은 모두 commit()하는 경우,
            # try except 씌워야한다. -> 성공하면 해당 객체를 반환해보자.?
            try:
                db.session.commit()
                # 객체에 연동되므로 굳이 반환안해도 될듯..?
                return self
            except Exception as e:
                db.session.rollback()
                raise e

    # (4) soft delete는 비어있는 delete_time을 채워주면 된다.
    def soft_delete(self):
        self.deleted_time = datetime.datetime.now()
        with DBConnectionHandler() as db:
            try:
                db.session.commit()
                return self
            except Exception as e:
                db.session.rollback()
                raise e


