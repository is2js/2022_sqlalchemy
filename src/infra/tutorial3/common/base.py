import datetime
import uuid

from flask import url_for
from sqlalchemy import Column, DateTime, BigInteger, Integer, ForeignKey, Boolean, String, func, and_, inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr

from src.infra.config.base import Base
from src.infra.tutorial3.common.int_enum import IntEnum
from src.main.templates.filters import format_date, format_datetime


class BaseModel(Base):
    __abstract__ = True

    add_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pub_date = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def to_dict(self):
        # (1) inspect(self)시 관계필드까지 조회하는데, form이나 front에서 DetachedError난다.
        # <-> 반면 self.__table__.columns는 관계필드를 조회안한다.
        # return {c: getattr(self, c) for c in inspect(self).attrs.keys()}
        # (2) dict comp쓰지말고, for문으로 돌면서, date/datetime 변환하기
        # return {c.name: getattr(self, c.name) for c in self.__table__.columns
        #         if c.name not in []  # 필터링 할 칼럼 모아놓기
        #         }
        data = dict()

        for col in self.__table__.columns:
            _key = col.name
            print(_key)
            _value = getattr(self, _key)

            if isinstance(_value, datetime.datetime):
                _value = format_datetime(_value)
            elif isinstance(_value, datetime.date):
                _value = format_date(_value)

            data[_key] = _value

        return data

    @staticmethod
    def to_dict_list(l):
        return [m.to_dict() for m in l]


class InviteBaseModel(Base):
    __abstract__ = True

    # 초대 만료기한
    _INVITE_EXPIRE_DAYS = 3

    # fk들도 다 상속시키고 싶다면, @declared_attr + method
    # https://stackoverflow.com/questions/9183012/sqlalchemy-mixin-foreignkey-and-relation

    is_answered = Column(Boolean, default=False)
    is_accepted = Column(Boolean, default=False)

    # expired계산을 위한 생성날짜
    create_on = Column(DateTime, default=datetime.datetime.now, nullable=False)

    # url을 만들기 위한 key생성(외부용?)
    key = Column(String(80), unique=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ## 일단 주어진 keyword는 다 집어넣고도, -> 이후 self.key를  내가 직접 key=로 넣어주지 않을때만 랜덤 생성한다.
        if not self.key:
            self.key = self.generate_key()

    @staticmethod
    def generate_key():
        return str(uuid.uuid4()).replace('-', '')

    # def my_random_string(string_length=10):
    #     """Returns a random string of length string_length."""
    #     random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    #     random = random.upper() # Make all characters uppercase.
    #     random = random.replace("-","") # Remove the UUID '-'.
    #     return random[0:string_length] # Return the random string.
    #
    # print(my_random_string(6)) # For example, D9E50C

    def send(self, request=None):
        url = self.get_absolute_url()
        if request:
            url = request.build_absolute_uri(url)

        # template = find_template("invite")
        # context = {
        #     "inviter_name": self.inviter.get_full_name(),
        #     "email": self.invitee_email,
        #     "invite_link": url,
        # }

        # return template.send_email([self.invitee_email], context)
        return url

    def get_absolute_url(self) -> str:
        # return reverse("accounts:invite_accept", kwargs={"key": self.key})
        return url_for("auth.invite", kwargs={"key": self.key})

    @property
    def expire_datetime(self):
        return self.create_on + datetime.timedelta(days=self._INVITE_EXPIRE_DAYS)

    @property
    def remain_timedelta(self):
        return self.expire_datetime - datetime.datetime.now()

    @hybrid_property
    def is_not_expired(self) -> bool:
        return datetime.datetime.now() <= self.expire_datetime

    # todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    #
    # payments = Payment.query.filter(Payment.due_date >= todays_datetime).all()
    @is_not_expired.expression
    def is_not_expired(cls):
        #### DateTime필드 vs dateTime obj비교는 되는데,
        #### DateTime필드에 timedelta를 섞을 순 없다. => datetime 관련을 한쪽에 몰아서 비교한다.
        #### 각각을 비교하고 싶다면. 속성.month  extract('month)를 hybrid로 만들어서 할 수도 있다.
        # https://stackoverflow.com/questions/51451768/sqlalchemy-querying-with-datetime-columns-to-filter-by-month-day-year
        #### 나느 date로만 비교시 func.date( DateTime필드 )  vs  int (date.month)로 비교했었다.
        return cls.create_on >= datetime.datetime.now() - datetime.timedelta(days=cls._INVITE_EXPIRE_DAYS)

    @hybrid_property
    def is_not_answered(self) -> bool:
        return not self.is_answered

    @is_not_answered.expression
    def is_not_answered(cls):
        # return not cls.is_answered
        return cls.is_answered == False

    @hybrid_property
    def is_valid(self) -> bool:
        return self.is_not_expired and self.is_not_answered

    @is_valid.expression
    def is_valid(cls):
        return and_(cls.is_not_expired, cls.is_not_answered)
