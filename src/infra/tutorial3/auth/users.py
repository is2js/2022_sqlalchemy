import datetime
import enum
import uuid

from dateutil.relativedelta import relativedelta
from flask import url_for, g
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, case, and_, exists, func, DateTime, \
    BigInteger, update, Date
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash

from src.config import project_config
from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3.common.base import BaseModel, InviteBaseModel
from src.infra.tutorial3.common.int_enum import IntEnum


class SexType(enum.IntEnum):
    미정 = 0
    남자 = 1
    여자 = 2

    # form을 위한 choices에는, 선택권한을 안준다? -> 없음 0을 제외시킴
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls if choice.value]


class User(BaseModel):
    __tablename__ = 'users'
    # 가입시 필수
    # id = Column(Integer, primary_key=True)
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    # password = Column(String(320), nullable=False)
    password_hash = Column(String(320), nullable=False)
    # 추가정보 -> 필수정보로 변경(nullable 제거
    # email = Column(String(128), nullable=True, unique=True)  # nullable데이터는 unique key못주니, form에서 검증하자
    # email = Column(String(128), nullable=True)
    email = Column(String(128), nullable=False, index=True, unique=True)

    # 최근방문시간 -> model ping메서드 -> auth route에서 before_app_request에 로그인시 메서드호출하면서 수정하도록 변경
    last_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)

    # 가입후에 수정 -> nullable = True
    is_active = Column(Boolean, nullable=True, default=True)
    avatar = Column(String(200), nullable=True)
    # is_super_user = Column(Boolean, nullable=True, default=False)
    # is_staff = Column(Boolean, nullable=True, default=False)

    ## 추가
    # email/phone은 선택정보이지만, 존재한다면 unique검사가 들어가야한다.
    # => form에서 unique를 검증하고  추가정보로서 unique키를 주면 안된다(None대입이 안되서 unique제약조건에 걸림)
    sex = Column(IntEnum(SexType), default=SexType.미정, nullable=True)
    address = Column(String(60), nullable=True)
    # phone = Column(String(11), nullable=True, unique=True) # nullable데이터는 unique key못주니, form에서 검증하자
    phone = Column(String(11), nullable=True)

    ## 추가2-1 role에 대한 fk 추가
    ## - user입장에선 정보성 role을 fk로 가졌다가, role entity에서 정보를 가져오는 것이지미나
    ## - role입장에선 1:m이다. 1user는 1role,  1role은 여러유저들에게 사용
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    ## 직원(M)에 대해 1로서 relationship
    #### User(invite.inviter)로부터 직원(1:1)의 1로서 바로 접근가능하게 subquery+uselist=False
    employee = relationship('Employee', backref=backref('user', lazy='subquery'), lazy='subquery', uselist=False)
    # employee = relationship('Employee', backref=backref('user', lazy='subquery'), uselist=False)# lazy='subquery')

    ## invite에 user_id 2개 추가에 대한 2개의 one으로서 relationship
    # -> 같은 테이블 2개에 대한 relaionship은 brackref만 다르게 주지말고,
    # -> foreign_keys를  ManyEntity.필드_id를 각각 다른 필드로서 명시해줘야한다
    inviters = relationship('EmployeeInvite', backref=backref('inviter', lazy='subquery'), lazy='dynamic',
                            foreign_keys='EmployeeInvite.inviter_id'
                            )
    invitees = relationship('EmployeeInvite', backref=backref('invitee', lazy='subquery'), lazy='dynamic',
                            foreign_keys='EmployeeInvite.invitee_id'
                            )

    ## 추가2-2 user생성시, role=관계객체를 입력하지 않은 경우, default인 User Role객체를 가져와 add해서 생성되도록 한다
    ## -> if 환경변수의 ADMIN_EMAIL에 해당하는 경우, 관리자 Role객체를 가져와 add해서 생성되게 한다
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ## 원본대로 생성했는데, 따로 role객체를  role = Role( )로 부여하지 않았다면,
        ## (2) 그게 아니라면 role중에 default=True객체(default User객체)를 Role객체로 찾아 넣어준다.
        # if not self.role :
        #### form에서 role_id를 받아 줬는데도, role객체로 안들어왔다고 기본값으로 생성됨 주의
        #### => 관계객체가 안들어와서 동적으로 default로 생성할 땐,
        ####    self.role 뿐만 아니라 self.role_id의 fk도 안들어오는지 같이 확인
        if not self.role and not self.role_id:
            ## (1) ADMIN_EMAIL인지 확인하여, admin Role객체를 부여한다
            if self.email == project_config.ADMIN_EMAIL:
                condition = Role.name == 'Administrator'
            else:
                condition = Role.default == True
            with DBConnectionHandler() as db:
                self.role = db.session.scalars(select(Role).where(condition)).first()

    @property
    def password(self):
        raise AttributeError('비밀번호는 읽을 수 없습니다.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # permission_required에서 사용되는 권한확인용
    def can(self, permission):
        if not self.role:
            return False
        return self.role.has_permission(permission)

    # 기능별 permission대신, role로 확인가능하도록
    # => 이퀄비교를 하면, 해당role만 정확하게 찾는다.
    # => 그 이상으로 가능하도록 처리해야한다.
    # => role_name에 해당하는 Role객체 -> permissions를 구하고
    #   현재유저의 permissions가 크거나 같으면 허용해야한다...
    def is_(self, role_enum):
        # with DBConnectionHandler() as db:
        #     role_perm = db.session.execute(select(Role.permissions).where(Role.name == role_name)).scalar()
        #### db로 조회하는 대신, roles dict로 최고권한을 조회한다
        # role_perm = roles[role_name][-1]
        #### dict-> enum으로 바뀌었을때 최고권한
        role_perm = role_enum.value[-1]
        # print(self.role.permissions, role_perm)
        return self.role.permissions >= role_perm

    #### permissions 비교는 항상  >=로 하니까
    ####  직원 >= STAFF 를 만들어서 -> 그것의 not으로 User를 골라낸다.
    @hybrid_property
    def is_staff(self):
        return self.is_(Roles.STAFF)

    #### where에 들어갈 sql식으로서 True/False를 만드려면 case문을 써야한다?
    @is_staff.expression
    def is_staff(cls):
        #### 방법1
        # cls(== User) 를 sub를 사용할 주체entity의 1row씩 들어온다 생각하고
        # => SQL에서 관계 필드의 대소비교-> True/False는
        #    (1) subq key 연결조건 +  추가조건으로 대소비교를 걸고 ->
        #        - cls는 외부 주체entity의 각 row라 생각하자.
        #        - 추가조건에 관계entity.필드의 조건을 걸어서 대소비교를 한다.
        #    (2) select 대신 해당 관계데이터가 exists되느냐/ 없느냐로 T/F판단이전에 먼저 판단한다 ->
        #        - select( Role ) 대신 exists()로 절을 만든다.
        #    (3) where절에 2entity가 들어갔을 때, 주체entity의 subquery용으로서
        #       관계entity만 select절에 잡히도록 명시하려면  .correlate(cls)를 붙인다.
        #       - 일반적으로 join용 데이터는 .subquery()로 만들고 subq.c.칼럼으로 엮서 쓰지만
        #       - 조건확인을 위한 subquery는 exists() + .correlate( 외부 주체entity ==cls )를 명시해준다.)
        # subq = (
        #     exists(1)
        #     .where(Role.id == cls.role_id)
        #     .where(Role.permissions >= Roles.STAFF.value[-1])
        # ).correlate(cls)
        #### join용 .subquery()가 아니라 where에 쓸 조건문용 subq는 .subquery()달지 않고, .correlcate( 주체entity )를 달아줘서 연결하여 사용될 subq임을 명시한다
        #### => 안하면 join아닌 from 카다시안으로join된 데이터가 형성 -> from에 2개table이 잡혀버린다.

        # (4) 존재하면 True/존재안하면 False로 => case로 변환해서 주체entity의 where절에 들어갈 수 있게 한다
        # return select([case([(subq, True)], else_=False)]).label("label")
        # return select([case([(subq, True)], else_=False)])
        # WHERE CASE WHEN (EXISTS (SELECT 1
        # return case([(subq, True)], else_=False)

        # (5) exists문은 case로 T/F없이 바로 필터링 expression으로 작동된다.
        # WHERE EXISTS (SELECT 1
        # return subq

        #### 방법2
        # (1) where에 걸릴 expression으로서,
        #    - 주체entity.확인할관계entity.any()는 ->기본조건(데이터연결)만 where에 들어간 exists()문이 완성되고
        #    - 주체entity.확인할관계entity.any( 관계entity로 추가조건 )는 -> 연걸 + 관계entity필드로 추가조건된 exists()문이 완성된다.
        # (2) any()속에 [추가조건 걸 관계Entity 필드 대소비교]를 넣어주고,
        #    - 주체가 Many(User)이므로 .has()로 걸어준다.

        # return cls.role.any(Role.permissions >= Roles.STAFF.value[-1])
        # sqlalchemy.exc.InvalidRequestError: 'any()' not implemented for scalar attributes. Use has().
        return cls.role.has(Role.permissions >= Roles.STAFF.value[-1])

    @hybrid_property
    def is_chiefstaff(self):
        return self.is_(Roles.CHIEFSTAFF)

    @is_chiefstaff.expression
    def is_chiefstaff(cls):
        return cls.role.has(Role.permissions >= Roles.CHIEFSTAFF.value[-1])

    @hybrid_property
    def is_executive(self):
        return self.is_(Roles.EXECUTIVE)

    @is_executive.expression
    def is_executive(cls):
        return cls.role.has(Role.permissions >= Roles.EXECUTIVE.value[-1])

    @hybrid_property
    def is_administrator(self):
        return self.is_(Roles.ADMINISTRATOR)

    @is_administrator.expression
    def is_administrator(cls):
        return cls.role.has(Role.permissions >= Roles.ADMINISTRATOR.value[-1])

    def ping(self):
        self.last_seen = datetime.datetime.now()
        with DBConnectionHandler() as db:
            db.session.add(self)
            db.session.commit()

    # 최근방문시간 -> model ping메서드 -> auth route에서 before_app_request에 로그인시 메서드호출하면서 수정하도록 변경
    @classmethod
    def ping_by_id(cls, user_id):
        with DBConnectionHandler() as db:
            stmt = (
                update(cls)
                .where(cls.id == user_id)
                .values({
                    cls.last_seen: datetime.datetime.now()
                })
            )

            db.session.execute(stmt)
            db.session.commit()
            # current_user = db.session.get(cls, user_id)
            # current_user.last_seen = datetime.datetime.now()
            # db.session.add(current_user)
            # db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        with DBConnectionHandler() as db:
            user = db.session.get(cls, id)
            return user

    def update(self, kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}]"
        return info


class Permission(enum.IntEnum):
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4  # User
    CLEAN = 8
    RESERVATION = 16  # Staff, Doctor
    ATTENDANCE = 32  # ChiefStaff
    EMPLOYEE = 64  # Executive
    ADMIN = 128  # Admin


class Roles(enum.Enum):
    # 각 요소들이 결국엔 int이므로, deepcopy는 생각안해도 된다?
    #### 미리 int들을 안더하는 이유는, 순회하면서, permission이 같은 것은 누적 또 하면 안되기 때문

    USER: list = [
        Permission.FOLLOW,
        Permission.COMMENT,
        Permission.WRITE
    ]

    STAFF: list = list(USER) + [
        Permission.CLEAN,
        Permission.RESERVATION
    ]

    DOCTOR: list = list(STAFF)

    CHIEFSTAFF: list = list(DOCTOR) + [
        Permission.ATTENDANCE
    ]

    EXECUTIVE: list = list(CHIEFSTAFF) + [
        Permission.ATTENDANCE,
        Permission.EMPLOYEE
    ]

    ADMINISTRATOR: list = list(EXECUTIVE) + [
        Permission.ADMIN
    ]


roles = {
    'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],

    'Staff': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
              Permission.CLEAN, Permission.RESERVATION],
    'Doctor': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
               Permission.CLEAN, Permission.RESERVATION],

    'ChiefStaff': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                   Permission.CLEAN, Permission.RESERVATION,
                   Permission.ATTENDANCE
                   ],

    'Executive': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                  Permission.CLEAN, Permission.RESERVATION,
                  Permission.ATTENDANCE,
                  Permission.EMPLOYEE
                  ],

    'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                      Permission.CLEAN, Permission.RESERVATION,
                      Permission.ATTENDANCE,
                      Permission.EMPLOYEE,
                      Permission.ADMIN,
                      ],
}


class Role(BaseModel):
    __tablename__ = 'roles'

    # id = Column(Integer, primary_key=True)
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    name = Column(String(64), unique=True)
    # User 생성시, default객체가 User인지를 컴퓨터는 알길이 없기에
    # 우리가 정해둔 default role을 검색해서, User생성시 배정할 수 있게 한다
    default = Column(Boolean, default=False, index=True)
    # permission의 합을 가지고 있으며, 다 더해도, 다음 permission에는 도달못한다
    # 특정 permission을 제외시키면, 그 직전 permission까지는 해당할 수 있게도 된다.
    permissions = Column(Integer)

    # 여러 사용자가 같은 Role을 가질 수 있다.
    users = relationship('User', backref=backref('role', lazy='subquery'), lazy='dynamic')

    employee_invites = relationship('EmployeeInvite', backref=backref('role', lazy='subquery'), lazy='dynamic')

    ## Role을 생성(수정시도 생성)할 때, Role객체 생성시 따로 permissions= int값(enum)을 입력하지 않는다면,
    ## - permission을 int 0으로 채워둔다.
    ## - 사실 Role객체를 미리 생성할 일은 없고, 나중에 일괄생성하는데, 그때 0부터 채우도록 하는 것
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.permissions:
            self.permissions = 0

    ## role마다 주어지는 permission 묶음을 마련해놓고, int값으로 계산하여 role 전체를 1번에 생성
    ## -> 조회가 들어가서 insert임에도 불구하고, cls메서드로 정의한다.
    @classmethod
    def insert_roles(cls):
        # 1) 각 role(name)별  permission 묵음 dict를 미리 마련한다
        # roles = {
        #     'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
        #

        # 2) role dict묶음을 돌면서, 이미 존재하는지 조회하고, 없을 때 Role객체를 생성하여 role객체를 유지한다
        with DBConnectionHandler() as db:
            # 8) role마다 default role인 User인지 아닌지를 확인하기 위해 선언
            # default_role = 'User'
            default_role = Roles.USER.name

            # for role_name in roles:
            for role_name, role_enum in Roles.__members__.items():
                # role = db.session.scalars(select(cls).filter_by(name=role_enum.name)).first()
                role = db.session.scalars(select(cls).filter_by(name=role_name)).first()
                if not role:
                    # role = cls(name=role_enum.name)
                    role = cls(name=role_name)
                # 3) 이미 존재하든, 새로 생성했든 해당role객체의 permissions필드를 0으로 초기화한다
                role.reset_permissions()
                # 4) 해당role_name에 해당하는 int permission들을 순회하면서 필드에 int값을 누적시킨다
                # for perm in roles[role_name]:
                # for perm in role_enum.value:
                # print(role_name, role_enum, type(role_enum))
                # USER,  Roles.USER <enum 'Roles'>
                # print(role_enum.value)
                # [<Permission.FOLLOW: 1>, <Permission.COMMENT: 2>, <Permission.WRITE: 4>]
                for perm in role_enum.value:
                    role.add_permission(perm)
                # 7) 해당role에 default role인 User가 맞는지 확인하여 필드에 넣어준다.
                role.default = (role.name == default_role)

                db.session.add(role)
            db.session.commit()

    def reset_permissions(self):
        self.permissions = 0

    # 5) add할 때, 이미 가지고 있는지 확인한다
    # -> perm == perm의 확인은, (중복int를 가지는 Perm도 생성가능하다고 생각할 수 있다)
    def has_permission(self, perm):
        return self.permissions & self.permissions >= perm

    def add_permission(self, perm):
        # 6) 해당 perm(같은int)을 안가지고 잇을때만 추가한다다
        if not self.has_permission(perm):
            self.permissions += perm

    #### 객체대소비교1. 모든 대소비교기준을 self < other인 __lt__를 먼저 정의한다
    # - list내부 객체의 객체list .sort()만 할거면 이것만 정의해줘도 된다.
    # (1) 어떤 필드를 이용할지  self.xxx   other.xxx  를 정한다
    # (2) 어떤 순서로 할지  오름차순이면 왼쪽.xxx < 오른쪽.xxx가 True가 되도록 return한다
    #     내림차순이면 반대로 return self.xxx > other.xxx로 주면 된다.
    # def __lt__(self, other):
    #     return self.permissions < other.permissions
    # https://stackoverflow.com/questions/1061283/lt-instead-of-cmp

    # https://stackoverflow.com/questions/71912085/hybrid-expressions-in-sqlalchemy-with-arguments
    @hybrid_method
    def is_less_than(self, role):
        return self.permissions < role.permissions

    @is_less_than.expression
    def is_under(cls, role):
        return cls.permissions < role.permissions

    @classmethod
    def get_by_id(cls, id):
        with DBConnectionHandler() as db:
            user = db.session.get(cls, id)
            return user

    @hybrid_method
    def is_(self, role_enum):
        role_perm = role_enum.value[-1]
        return self.permissions >= role_perm

    @is_.expression
    def is_(cls, role_enum):
        role_perm = role_enum.value[-1]
        return cls.permissions >= role_perm

    def __repr__(self):
        return '<Role %r>' % self.name


class JobStatusType(enum.IntEnum):
    대기 = 0
    재직 = 1
    휴직 = 2
    퇴사 = 3

    # form을 위한 choices에는, 선택권한을 안준다? -> 0을 value로 잡아서 제외시킴
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls if choice.value]


class Employee(BaseModel):
    __tablename__ = 'employees'

    # id = Column(Integer, primary_key=True)
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    # 연결고리이자, user로부터 -> employee의 정보를 찾을 때, 검색조건이 될 수 있다.
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    # 부서

    name = Column(String(40), nullable=False)
    sub_name = Column(String(40), nullable=False)
    birth = Column(String(12), nullable=False)

    join_date = Column(Date, nullable=False)

    # job_status가 User에서 신청한 대기 Employee(role이 아직 User)를 검색해서 대기중인 Employee데이터를 골라낼 수도 있다.
    # - 예약시에는 reserve_status가 대기 중인 것을 골라낼 것이다.
    job_status = Column(IntEnum(JobStatusType), default=JobStatusType.재직, nullable=False, index=True)
    resign_date = Column(Date, nullable=True)

    # qrcode, qrcode_img: https://github.com/prameshstha/QueueMsAPI/blob/85dedcce356475ef2b4b149e7e6164d4042ffffb/bookings/models.py#L92

    ## employee도 대기/퇴사상태가 잇어서 구분하기 위함
    @hybrid_property
    def is_active(self):
        # return JobStatusType.대기 != self.job_status and self.job_status != JobStatusType.퇴사
        return self.job_status not in [JobStatusType.대기, JobStatusType.퇴사]

    @is_active.expression
    def is_active(cls):
        # 객체와 달리, expression은 and_로 2개 조건식을 나눠 써야한다.
        # return and_(JobStatusType.대기 != cls.job_status, cls.job_status != JobStatusType.퇴사)
        # return not cls.job_status.in_([JobStatusType.대기, JobStatusType.퇴사])
        return cls.job_status.notin_([JobStatusType.대기, JobStatusType.퇴사])

    @hybrid_property
    def is_pending(self):
        return self.job_status == JobStatusType.대기

    @is_pending.expression
    def is_pending(cls):
        return cls.job_status == JobStatusType.대기

    @hybrid_property
    def is_resign(self):
        return self.job_status == JobStatusType.퇴사

    @is_resign.expression
    def is_resign(cls):
        return cls.job_status == JobStatusType.퇴사

    @property
    def birthday(self):
        month, day = self.birth[2:4], self.birht[4:6]
        return f"{int(month):2d}월{int(day):2d}"

    @property
    def age(self):

        today_date = datetime.date.today()
        # 주민번호가 뒷자리 시작 [6]이 3or4면, 20년대생 / 아니면 19년대생이다.
        # 주민번호 뒷자리 시작 [6]이 짝수면 여자다 (90년대 -> 1 남  20년대 -> 3 남)
        birth_date = self.birth_to_date()
        if birth_date:
            # 나이는 다음해의 생일을 지나야 +1일인데,
            # (1) 일단 연도를 먼저 뺀다. 일단 해가 달라지면 1살로 봤다가
            # (2)  거기서 생일의 월일이 오늘보다 크다면, 아직 다음해 월일을 안지났으면 -1을 해준다. => 등호로 안지났을대를 - ( True)로 빼준다.
            #      today가 >= 크거나 같은 경우, 1살 먹은 것으로 치고 빼기 0이 된다.
            age = (
                    today_date.year - birth_date.year
                    - ((today_date.month, today_date.day) < (birth_date.month, birth_date.day))
            )
            return str(age) + '세'
        return '-'

    def birth_to_date(self):
        try:
            birth_year_int = int("20" if self.birth[6] in ['3', '4'] else '19' + self.birth[:2])
            birth_month_int, birth_day_int = int(self.birth[2:4]), int(self.birth[4:6])
            birth_date = datetime.date(birth_year_int, birth_month_int, birth_day_int)
            return birth_date
        except:
            return None

    # 근무개월 수 (다음달 해당일시 차이가 1달로 +1)
    @property
    def months_and_days_from_join_date(self):
        today_date = datetime.date.today()
        ## self.join_date + relativedelta(months=1) 는 정확히 다음달 같은 일을 나타낸다
        # - 2월1일(join) 입사했으면, 3월1일(today)에 연차가 생기도록, (딱 1달이 되는날)
        # - 차이가 1달이라는 말은, 시작일제외하고 [시작일로부터 차이가 한달]이 지났다는 말이다.
        #    3-1 = 시작일 빼고 2일,   차이6 => 시작일포함 7일, 시작일 제외 시작일부터 6일지남
        # - 계산기준일에 relativedelta를 끼워서 계산하도록 한다.
        # - 월차휴가 계산과 동일하며, 월차는 연도제한 + 연차도 계산해야한다.
        months = 0
        while today_date >= self.join_date + relativedelta(months=1):
            today_date -= relativedelta(months=1)
            months += 1
        days = (today_date - self.join_date).days  # timedelta.days   not int()
        return months, days

    # 재직자 N년차(햇수) 1년차(0)부터 시작하며, 일한 개월수가 12가 넘어가야 2년차다
    @property
    def years_from_join_date(self):
        months, _ = self.months_and_days_from_join_date
        years = (months // 12) + 1
        return years

    # 연차휴가 참고식: https://www.acmicpc.net/problem/23628
    # https://www.saramin.co.kr/zf_user/tools/holi-calculator
    @property
    def working_days(self):
        months, days = self.months_and_days_from_join_date
        years, months = divmod(months, 12)  # 여기서 years는 N년차가 아니라, 0부터 시작하는 근무연수

        result = f"{days}일"
        if months:
            result = f"{months}개월" + result
        if years:
            result = f"{years}년" + result
        return result

    @property
    def employee_number(self):
        return f"{self.join_date.year}{self.id:04d}"

    def __repr__(self):
        return '<Employee %r>' % self.id


# class InviteType(enum.IntEnum):
#     직원_초대 = 0
#     모임_초대 = 1
#
#     예약_초대 = 5
#     리뷰_초대 = 6
#     결제_초대 = 7
#     환불_초대 = 8
#
#     # form을 위한 choices에는, 선택권한을 안준다? -> 없음 0을 제외시킴
#     @classmethod
#     def choices(cls):
#         return [(choice.value, choice.name) for choice in cls if choice.value]


class EmployeeInvite(InviteBaseModel):
    __tablename__ = 'employee_invites'

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    # user -> inviter / invitee
    inviter_id = Column(Integer, ForeignKey('users.id'))
    invitee_id = Column(Integer, ForeignKey('users.id'))

    # 직원초대에서는, 초대마다 바뀔 수 있는 role정보를 가져 따로 엔터티를 만들었다.
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    def __repr__(self):
        return '<EmployeeInvite %r=>%r >' % (self.inviter_id, self.invitee_id)

    @classmethod
    def get_by_invitee(cls, user):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.invitee == user)
                .where(cls.is_not_expired)
            )

            invite_list = db.session.scalars(stmt).all()
        return invite_list
