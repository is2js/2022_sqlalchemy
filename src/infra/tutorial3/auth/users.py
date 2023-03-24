import datetime
import enum
import itertools
import uuid
from collections import abc

from dateutil.relativedelta import relativedelta
from flask import url_for, g
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, case, and_, exists, func, DateTime, \
    BigInteger, update, Date, desc, literal_column, column, any_
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, backref, aliased, selectinload, Session, object_session
from werkzeug.security import generate_password_hash, check_password_hash

from src.config import project_config
from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler, db
from src.main.utils.format_date import format_date
from .departments import EmployeeDepartment, Department, DepartmentType
from src.infra.tutorial3.common.base import BaseModel, InviteBaseModel
from src.infra.tutorial3.common.int_enum import IntEnum
from ..common.grouped import grouped
from ..mixins.crudmixin import CRUDMixin


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
    __repr_attrs__ = ['username']
    #### baseModel에 동적으로 cls.ko_NAME이  comment을  __table_args__에 추가된다.
    # -> 사용은 User.__table__.comment로 한다.
    # User.__table__.comment
    # '유저'
    ko_NAME = '일반사용자'

    # 가입시 필수
    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
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
    sex = Column(IntEnum(SexType), default=SexType.미정.value, nullable=True,
                 comment='성별'
                 )
    address = Column(String(60), nullable=True)
    # phone = Column(String(11), nullable=True, unique=True) # nullable데이터는 unique key못주니, form에서 검증하자
    phone = Column(String(11), nullable=True)

    ## 추가2-1 role에 대한 fk 추가
    ## - user입장에선 정보성 role을 fk로 가졌다가, role entity에서 정보를 가져오는 것이지미나
    ## - role입장에선 1:m이다. 1user는 1role,  1role은 여러유저들에게 사용
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    #### employee.user.role 을 @property setter로 두고, session.merge로 변경한다면
    # -> null로 한번 뒀따가, 바뀐 값으로 update하길 2번을 한다.
    # -> 이 때 중간에 fk제약조건이 없어야한다.
    # role_id = Column(Integer, ForeignKey('roles.id'))
    # => 매번 flush 코드 제거하니 None 업데이트 사라짐.

    #### role에 정의했던 관계속성 옮김
    # role = relationship('Role', backref=backref('users', lazy='dynamic'), lazy='subquery')
    # => eager options 적용을 위해 lazy='dynamic' 옵션 제거 => jinja에서 갖다쓰는거 해결하고 처리해야함.
    # role = relationship('Role', backref=backref('users'), lazy='subquery')
    role = relationship('Role',
                        uselist=False,
                        # back_populates='user'
                        )
    # for user_popup User.filter_by(employee___id)
    employee = relationship('Employee', uselist=False, back_populates='user')

    # eagerload와 lazy=subquery를 동시에 주면 sqlite multitrhead 에러난다.

    ## emp에 relationship 추가
    # employees = relationship('Employee', back_populates='user')

    #### .join()에 관계칼럼을 사용하려면, lazy='subquery'를 주면 안된다.
    # role = relationship('Role', backref=backref('users'))

    ## 직원(M)에 대해 1로서 relationship
    #### User(invite.inviter)로부터 직원(1:1)의 1로서 바로 접근가능하게 subquery+uselist=False
    # employee = relationship('Employee', backref=backref('user', lazy='subquery'), uselist=False)# lazy='subquery')
    # employee = relationship('Employee', backref=backref('user', lazy='subquery'), lazy='subquery', uselist=False)
    #### => 관계속성을 Employee로 옮겨 Employee.관계속성을 stmt에 쓸 수있게 한다

    ## invite에 user_id 2개 추가에 대한 2개의 one으로서 relationship
    # -> 같은 테이블 2개에 대한 relaionship은 brackref만 다르게 주지말고,
    # -> foreign_keys를  ManyEntity.필드_id를 각각 다른 필드로서 명시해줘야한다
    # inviters = relationship('EmployeeInvite', backref=backref('inviter', lazy='subquery'), lazy='dynamic',
    #                         foreign_keys='EmployeeInvite.inviter_id'
    #                         )
    # invitees = relationship('EmployeeInvite', backref=backref('invitee', lazy='subquery'), lazy='dynamic',
    #                         foreign_keys='EmployeeInvite.invitee_id'
    #                         )
    # backref 삭제->
    # 1) one to many : lazy='dynamic' + fk 2개이상시, foreign_keys(string:테이블명.fk명)으로 각각 지정
    # 2) many to one : lazy옵션 제거, uselist=False  + fk 2개이상시, foreign_keys( [fk칼럼]) 각각 지정
    # 3) 서로 relationship지정시 : 각각의 relationship을 string으로 back_populates=에 걸어주기
    inviters = relationship('EmployeeInvite', lazy='dynamic', foreign_keys='EmployeeInvite.inviter_id',
                            back_populates='inviter',  # 관계컬럼을 서로 정의할 경우, id copy시 자동으로 채우도록 지정
                            )
    invitees = relationship('EmployeeInvite', lazy='dynamic', foreign_keys='EmployeeInvite.invitee_id',
                            back_populates='invitee',  # 관계컬럼을 서로 정의할 경우, id copy시 자동으로 채우도록 지정
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

    # .create()내부 fill에서 settable검사는 @property는 invalid로 걸린다. @hybrid_property만 통과된다.
    # => BUT password_hash대신 password로 입력하여 setter처리가 되려면, @property여야 자동 반영된다.
    # => fill검사에 property를 추가해야한다.
    #    fill검사를 통과하기 위해 @hybrid_property로 정의함녀 기존 @property를 덮어쓰고
    #    TypeError: 'password' is an invalid keyword argument for User
    # => fill검사 통과용 1) hybrid_property를 먼저 정의하고 2) 실제 setter가 적용되는 @property를 뒤에 선언해서 해결함

    @hybrid_property
    def password(self):
        raise AttributeError('비밀번호는 읽을 수 없습니다.')

    # @password.inplace.setter # 2.0 # https://docs.sqlalchemy.org/en/20/orm/extensions/hybrid.html#defining-setters
    #### User().fill() -> setattr()를 통해서 입력되는, Model.create()에서는 가능하나
    #    User(password= )로 직접적으로 생성하면 @property가 아니라 @hybrid라서 에러뜬다
    @password.setter  # 1.4
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # @property
    # def password(self):
    #     raise AttributeError('비밀번호는 읽을 수 없습니다.')
    #
    # @password.setter
    # def password(self, password):
    #     self.password_hash = generate_password_hash(password)

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
    # def is_(self, role_enum):
    #     # with DBConnectionHandler() as db:
    #     #     role_perm = db.session.execute(select(Role.permissions).where(Role.name == role_name)).scalar()
    #     #### db로 조회하는 대신, roles dict로 최고권한을 조회한다
    #     # role_perm = roles[role_name][-1]
    #     #### dict-> enum으로 바뀌었을때 최고권한
    #     role_perm = role_enum.value[-1]
    #     # print(self.role.permissions, role_perm)
    #     return self.role.permissions >= role_perm

    @hybrid_method
    def is_(self, role_enum):
        # mysql에서는 enum(Permission).value를 안하면 비교가 안되서, enum class에 propoerty 추가
        return self.role.permissions >= role_enum.max_permission

    @is_.expression
    def is_(cls, role_enum, mapper=None):

        mapper = mapper or cls
        Role_ = mapper.role.property.mapper.class_
        # mysql에서는 enum(Permission).value를 안하면 비교가 안되서, enum class에 propoerty 추가
        return cls.role.has(Role_.permissions >= role_enum.max_permission)

    #### permissions 비교는 항상  >=로 하니까
    ####  직원 >= STAFF 를 만들어서 -> 그것의 not으로 User를 골라낸다.
    @hybrid_property
    def is_staff(self):
        return self.is_(Roles.STAFF)

    #### where에 들어갈 sql식으로서 True/False를 만드려면 case문을 써야한다?
    @is_staff.expression
    def is_staff(cls):
        return cls.role.has(Role.permissions >= Roles.STAFF.max_permission)

    @hybrid_property
    def is_chiefstaff(self):
        return self.is_(Roles.CHIEFSTAFF)

    @is_chiefstaff.expression
    def is_chiefstaff(cls):
        return cls.role.has(Role.permissions >= Roles.CHIEFSTAFF.max_permission)

    @hybrid_property
    def is_executive(self):
        return self.is_(Roles.EXECUTIVE)

    @is_executive.expression
    def is_executive(cls):
        return cls.role.has(Role.permissions >= Roles.EXECUTIVE.max_permission)

    @hybrid_property
    def is_administrator(self):
        return self.is_(Roles.ADMINISTRATOR)

    @is_administrator.expression
    def is_administrator(cls):
        return cls.role.has(Role.permissions >= Roles.ADMINISTRATOR.max_permission)

    def ping(self):
        self.last_seen = datetime.datetime.now()
        with DBConnectionHandler() as db:
            db.session.add(self)
            db.session.commit()

    # 최근방문시간 -> model ping메서드 -> auth route에서 before_app_request에 로그인시 메서드호출하면서 수정하도록 변경
    # => user.update로 정리됨.
    # @classmethod
    # def ping_by_id(cls, user_id):
    #     with DBConnectionHandler() as db:
    #         stmt = (
    #             update(cls)
    #             .where(cls.id == user_id)
    #             .values({
    #                 cls.last_seen: datetime.datetime.now()
    #             })
    #         )
    #
    #         db.session.execute(stmt)
    #         db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        with DBConnectionHandler() as db:
            user = db.session.get(cls, id)
            return user

    def update2(self, info_dict=None, **kwargs):
        if info_dict:
            for k, v in info_dict.items():
                setattr(self, k, v)

        for k, v in kwargs.items():
            setattr(self, k, v)

    # 생략시 basemixin에
    # def __repr__(self):
    #     info: str = f"{self.__class__.__name__}"
    #     #             f"[id={self.id!r}]"
    #     return info

    #### with other entity
    def get_my_departments(self, as_leader=False, as_employee=False, as_min_level=False):
        with DBConnectionHandler() as db:
            # 부서정보 -> Employee -> User 관계필터링
            subq_stmt = (
                select(EmployeeDepartment.department_id)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.employee.has(Employee.user == self))
            )
            # 부서 중에 내가 팀장인 부서정보만
            if as_leader:
                subq_stmt = subq_stmt.where(EmployeeDepartment.is_leader == True)

            ## 추가) 부서 중에 내가 팀원으로 있는 정보만
            if as_employee:
                subq_stmt = subq_stmt.where(EmployeeDepartment.is_leader == False)

            dep_ids = (
                subq_stmt
            ).scalar_subquery()

            # 내가 (팀장으로) 소속중인 부서 추출
            # => min_level은 현재까지 집계 Department에 대한 집계를 correlate로 해야하며
            #    그럴 경우, where subquery에 from이 없어서 집계subquery로 못들어가므로
            #    select절에서 집계하여 해당 데이터만 나오도록 해야한다.
            if as_min_level:
                min_level_subq = (
                    select(func.min(Department.level))
                ).correlate(Department).scalar_subquery()

                stmt = (
                    select(Department, min_level_subq)
                    .where(Department.id.in_(dep_ids))
                )
            else:
                stmt = (
                    select(Department)
                    .where(Department.id.in_(dep_ids))
                )

            try:
                return db.session.scalars(
                    stmt
                    .order_by(Department.path)
                ).all()
            except ValueError:
                return []

    @hybrid_property
    def is_employee_active(self):
        with DBConnectionHandler() as db:
            stmt = (
                exists()
                .where(Employee.user_id == self.id)
                .where(Employee.is_active == True)
                .select()
            )
            return db.session.scalar(stmt)

    @hybrid_property
    def has_employee_history(self):
        with DBConnectionHandler() as db:
            stmt = (
                exists()
                .where(Employee.user_id == self.id)
                .select()
            )
            return db.session.scalar(stmt)


class Permission(enum.IntEnum):
    #### outerjoin 조인으로 들어왔을 때, 해당 칼럼에 None이 찍히는데, -> 0을 내부반환하고, 그것을 표시할 DEFAULT NONE 상수를 필수로 써야한다.
    NONE = 0
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

    @property
    def max_permission(self):
        return self.value[-1].value


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
    ko_NAME = '역할'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    name = Column(String(64), unique=True, index=True)
    # User 생성시, default객체가 User인지를 컴퓨터는 알길이 없기에
    # 우리가 정해둔 default role을 검색해서, User생성시 배정할 수 있게 한다
    default = Column(Boolean, default=False, index=True)
    # permission의 합을 가지고 있으며, 다 더해도, 다음 permission에는 도달못한다
    # 특정 permission을 제외시키면, 그 직전 permission까지는 해당할 수 있게도 된다.
    permissions = Column(Integer)

    # 여러 사용자가 같은 Role을 가질 수 있다.
    # users = relationship('User', backref=backref('role', lazy='subquery'), lazy='dynamic')
    #### => User쪽으로 관계속성 옮기기 for stmt 연결

    # employee_invites = relationship('EmployeeInvite', backref=backref('role', lazy='subquery'), lazy='dynamic')
    employee_invites = relationship('EmployeeInvite', back_populates='role')

    # 해결1) User <- Role 관계설정
    # user = relationship('User', back_populates='role', uselist=False)

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
    # @hybrid_method
    # def is_(self, role_enum):
    #     role_perm = role_enum.value[-1]
    #     return self.permissions >= role_perm

    # @is_.expression

    # refactor
    @hybrid_method
    def is_(cls, role_enum, mapper=None):
        mapper = mapper or cls

        return mapper.permissions >= role_enum.max_permission

    # refactor is_와 다르게 role객체를 받아 비교
    @hybrid_method
    def is_under(self, role):
        return self.permissions < role.permissions

    @is_under.expression
    def is_under(cls, role, mapper=None):
        mapper = mapper or cls
        return mapper.permissions < role.permissions

    @classmethod
    def get_by_id(cls, id):
        with DBConnectionHandler() as db:
            role = db.session.get(cls, id)
            return role

    @classmethod
    def get_by_name(cls, name):
        with DBConnectionHandler() as db:
            role = db.session.scalars(
                select(cls)
                .where(cls.name == name)
            ).first()
            return role


class JobStatusType(enum.IntEnum):
    대기 = 0
    재직 = 1
    휴직 = 2
    퇴사 = 3

    # form을 위한 choices에는, 선택권한을 안준다? -> 0을 value로 잡아서 제외시킴
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls if choice.value]

    @classmethod
    def is_active(cls, jos_status):
        # enum은 비교할때 enum객체 op value로 비교하면 된다. 따로 .value로 비교안해도 됨.
        return cls.재직.value == jos_status

    @classmethod
    def is_leave(cls, jos_status):
        return cls.휴직.value == jos_status

    @classmethod
    def is_resign(cls, jos_status):
        return cls.퇴사.value == jos_status


class Employee(BaseModel):
    __tablename__ = 'employees'
    ko_NAME = '직원'

    # id = Column(Integer, primary_key=True)
    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    # 연결고리이자, user로부터 -> employee의 정보를 찾을 때, 검색조건이 될 수 있다.
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    #### Many쪽에 backref가 아닌 관계속성을 직접 정의해야, => Many.one.any()를 stmt에 쓸 수 있다.
    # User에서 정의했던 관계속성 옮김 =>  employee = relationship('Employee', backref=backref('user', lazy='subquery'), lazy='subquery', uselist=False)
    user = relationship('User',
                        uselist=False,
                        # back_populates='employee'
                        )

    # 부서

    name = Column(String(40), nullable=False)
    sub_name = Column(String(40), nullable=False)
    birth = Column(String(13), nullable=False)

    # join_date = Column(Date, nullable=False)
    join_date = Column(Date, nullable=True)

    # job_status가 User에서 신청한 대기 Employee(role이 아직 User)를 검색해서 대기중인 Employee데이터를 골라낼 수도 있다.
    # - 예약시에는 reserve_status가 대기 중인 것을 골라낼 것이다.
    job_status = Column(IntEnum(JobStatusType), default=JobStatusType.재직.value, nullable=False, index=True)
    resign_date = Column(Date, nullable=True)
    # new : 휴직 상태의 최종휴직일을 알도록 칼럼을 추가한다
    leave_date = Column(Date, nullable=True)

    reference = Column(String(500), nullable=True)

    #### MANY 취임정보(들)에 대한 relationship 생성
    employee_departments = relationship('EmployeeDepartment',
                                        foreign_keys='EmployeeDepartment.employee_id',
                                        back_populates='employee',
                                        )
    employee_leave_histories = relationship('EmployeeLeaveHistory',
                                            foreign_keys='EmployeeLeaveHistory.employee_id',
                                            back_populates='employee',
                                            )

    #### 다대다(취임정보)를 건너서 바로 Employee -> (EmpDept) -> Dept에 relationship 생성
    # -> 오로지 조회용 Department class를 import없이 불러오기 위함.
    # -> 대체 Employee.employee_departments.property.mapper.class_.department.mapper.class_
    departments = relationship('Department',
                               # secondary=EmployeeDepartment, # Table객체 아니라 바로 못올림.
                               # secondary='employee_departments', # string도 더 위에서 정의한 Table객체 아니면 안됨.
                               secondary=EmployeeDepartment.__table__,
                               # back_populates='employees', # 이미 one-Many, one-Many로 relationship만들어서 안됨.
                               # lazy=True, # session에 있을때 즉시 소환하는 lazy='selectin'임.
                               viewonly=True,  # one-Many + Many-one으로 id복사하고 있다고 뜨니, 그냥 조회용으로만
                               )

    posts = relationship('Post', passive_deletes=True, back_populates='author')

    # new -> 상위부서
    # => 취임정보 생성시, level 1 dept를 path로 구해서, 그것을 one으로 추가한다.
    upper_department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'),
                                 index=True,
                                 nullable=True
                                 )
    upper_department = relationship("Department", foreign_keys=[upper_department_id],)

    # qrcode, qrcode_img: https://github.com/prameshstha/QueueMsAPI/blob/85dedcce356475ef2b4b149e7e6164d4042ffffb/bookings/models.py#L92

    #### 특정 role의 사람들을 다 가져오기 위한 메서드
    # -> 부서에 사람배치하는 test or 모든 팀장 가져오기?
    @classmethod
    def get_by_user_role(cls, roles: Roles):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.is_active)
            )

            if roles == Roles.USER:
                stmt = stmt.where(cls.user.has(~User.is_staff))
            elif roles == Roles.STAFF:
                stmt = stmt.where(cls.user.has(User.is_staff)).where(cls.user.has(~User.is_chiefstaff))
            elif roles == Roles.CHIEFSTAFF:
                stmt = stmt.where(cls.user.has(User.is_chiefstaff)).where(cls.user.has(~User.is_executive))
            elif roles == Roles.EXECUTIVE:
                stmt = stmt.where(cls.user.has(User.is_executive)).where(cls.user.has(~User.is_administrator))
            elif roles == Roles.ADMINISTRATOR:
                stmt = stmt.where(cls.user.has(User.is_administrator))
            else:
                raise ValueError('잘못된 Roles를 입력했습니다.')

            # print(stmt)
            # SELECT employees.add_date, employees.pub_date, employees.id, employees.user_id, employees.name, employees.sub_name, employees.birth, employees.join_date, employees.job_status, employees.resign_date, employees.reference
            # FROM employees
            # WHERE (employees.job_status NOT IN (__[POSTCOMPILE_job_status_1])) AND (EXISTS (SELECT 1
            # FROM users
            # WHERE users.id = employees.user_id AND (EXISTS (SELECT 1
            # FROM roles
            # WHERE roles.id = users.role_id AND roles.permissions >= :permissions_1))))
            # User[id=16]

            return db.session.scalars(stmt).all()

    ## employee도 대기/퇴사상태가 잇어서 구분하기 위함
    @hybrid_property
    def is_active(self):
        # return JobStatusType.대기 != self.job_status and self.job_status != JobStatusType.퇴사
        return self.job_status not in [JobStatusType.대기, JobStatusType.휴직, JobStatusType.퇴사]

    @is_active.expression
    def is_active(cls):
        # 객체와 달리, expression은 and_로 2개 조건식을 나눠 써야한다.
        # return and_(JobStatusType.대기 != cls.job_status, cls.job_status != JobStatusType.퇴사)
        # return not cls.job_status.in_([JobStatusType.대기, JobStatusType.퇴사])
        return cls.job_status.notin_([JobStatusType.대기, JobStatusType.휴직, JobStatusType.퇴사])

    @hybrid_property
    def is_pending(self):
        return self.job_status == JobStatusType.대기.value

    @is_pending.expression
    def is_pending(cls):
        return cls.job_status == JobStatusType.대기.value

    @hybrid_property
    def is_active(self):
        return self.job_status == JobStatusType.재직.value

    @is_active.expression
    def is_active(cls):
        return cls.job_status == JobStatusType.재직.value

    @hybrid_property
    def is_leaved(self):
        return self.job_status == JobStatusType.휴직.value

    @is_leaved.expression
    def is_leaved(cls):
        return cls.job_status == JobStatusType.휴직.value

    @hybrid_property
    def is_resigned(self):
        return self.job_status == JobStatusType.퇴사.value

    @is_resigned.expression
    def is_resigned(cls):
        return cls.job_status == JobStatusType.퇴사.value

    @property
    def birthday(self):
        month, day = self.birth[2:4], self.birth[4:6]
        return f"{int(month):2d}월{int(day):2d}일"

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
            birth_year_int = int(("20" if self.birth[6] in ['3', '4'] else '19') + self.birth[:2])
            birth_month_int, birth_day_int = int(self.birth[2:4]), int(self.birth[4:6])
            birth_date = datetime.date(birth_year_int, birth_month_int, birth_day_int)
            return birth_date
        except:
            return None

    ## self.join_date + relativedelta(months=1) 는 정확히 다음달 같은 일을 나타낸다
    # - 2월1일(join) 입사했으면, 3월1일(today)에 연차가 생기도록, (딱 1달이 되는날)
    # - 차이가 1달이라는 말은, 시작일제외하고 [시작일로부터 차이가 한달]이 지났다는 말이다.
    #    3-1 = 시작일 빼고 2일,   차이6 => 시작일포함 7일, 시작일 제외 시작일부터 6일지남
    # - 계산기준일에 relativedelta를 끼워서 계산하도록 한다.
    # - 월차휴가 계산과 동일하며, 월차는 연도제한 + 연차도 계산해야한다.
    def calc_complete_month_and_days(self, start_date, end_date):
        #### 시작일이 2년차 시작일을 넘어가면 월차계산을 할 필요가 없다.
        #### 또는 srt는 1년만인데, end가 1년을 넘어가면 또 계산안한다.
        # 참고(연차휴가 퇴직정산): https://www.nodong.kr/AnnuaVacationComparison
        # 참고(만 1년(365일) 근무 후 퇴직시 연차휴가 발생 여부): https://www.nodong.kr/holyday/2265906

        next_year_start_date = self.join_date + relativedelta(years=1)
        if start_date >= next_year_start_date:
            # print(f'시작일{start_date}가 입사1년(2년차시작, 12개째 발생지점){next_year_start_date}을 넘어서는 순간 월차계산은 0으로 return된다')
            return 0, 0

        #### (start가 월차발생지점보다 작은데)
        #### 마지막 근무일이 2년차 시작일(deadline_date)보다 큰 경우,
        #### 월차 11개의 미자믹은, 1.1입사 -> 2.1부터 12.1까지만 판단하므로
        #### => 다음해 1.1은 계산시 사용되면 안된다.
        ####    월차발생기준일은 2.1등 +1달한 것의 기준인데, 12개발생하는 기준점인 다음해 1.1을 제외시켜 자제적으로 계산 안되게 한다

        # if end_date >= next_year_start_date:
        #     12개 발생 기준점을 없애버리자.=> 계산식을 안고쳐도 된다?!
        # print(f'마지막 근무일{end_date}가 입사후1년 == 12번째 월차발생지점{next_year_start_date}을 넘어서는 순간 마지막 근무일 대신 deadline_date - 1로 end_date를 바꿔서 일을 빼서, 발생못하게 막는다(최대 1년마지막날)')
        # end_date = next_year_start_date - relativedelta(days=1)

        # end_date = min(end_date, next_year_start_date - relativedelta(days=1))

        #### end_date를 12개 발생지점(2년차 시작일)이 안되도록 -1로 계산되게 하여 11개로 제한했지만,
        #### => 중간에 맞춰서  1달 쉰사람은, 11개 발생지점이 되기도 한다.
        #### => end_date를 12개 발생지점(2년차 시작일, 다음해 입사일)까지 허용하되
        ####   반복문에서 1달씩 누적시, 11개를 넘지 못하도록 한다.
        end_date = min(end_date, next_year_start_date)

        months = 0
        while end_date >= start_date + relativedelta(months=1):
            end_date -= relativedelta(months=1)
            # months += 1
            #### 원래는 각 구간별 11개 이하가 아니라, 바깥에서 누적되는 것이 11개 이하가 되도록 유지해야하지만
            #### 1) 휴직없이 풀로 일한다 => 누적없이 이 메서드 1번만 타서 전체가 11개이하가 된다.
            #### 2) 중간에 휴직을 짧게 했다 => 직전 누적월차를 고려해서 11개 이하가 되도록 유지해야하지만
            ####    => 휴직을 1번이라도 한 이상, 이미 1개를 놓치기 때문에, 12개발생지점까지 카운팅한다손 치더라도,
            ####       최대 12개 발생가능 중에 1개는 무조건 깍여서 최대 11개가 된다.
            if months < 11:
                months += 1

        # 사실상 1개월만근이후 남은 days은 [월차]계산시 필요없다.
        days = (end_date - start_date).days  # timedelta.days   not int()

        return months, days

    # 재직상태에 따라 근무의 마지막일 찾기
    @property
    def last_working_date(self):
        # => 그림1: https://raw.githubusercontent.com/is3js/screenshots/main/image-20230114212700480.png
        #### 이 사람이 퇴사한 상태라면, 퇴사일을 마지막으로 기준으로 근무 개월수를 세어야한다
        if self.is_resigned:
            # if self.is_resigned and self.resign_date:

            # end_date = self.resign_date
            #### 퇴직일이 해당일이라면, 하루 전이 마지막 근무일이다.
            end_date = self.resign_date - relativedelta(days=1)
        #### 이 사람이 휴직 상태라면, 부서취임정보에서 휴직일을 들고와야한다?
        #### => 어차피 나중에 부서취임을 필수로 해서, 중간휴직-중간복직이 나올 것이기 때문에
        ####    최종휴직일(nullable)칼럼을 만들고, 휴직상태시 최종 휴직날짜를 알게 한다
        elif self.is_leaved:
            #### 휴직일이 해당일이라면, 그 전날까지가 근무일이다.
            end_date = self.leave_date - relativedelta(days=1)
        # 재직이나 대기상태 => 해당일도 근무일이다.
        else:
            end_date = datetime.date.today()
        return end_date

    # 근무개월 수 (다음달 해당일시 차이가 1달로 +1)
    # 연차휴가 참고식: https://www.acmicpc.net/problem/23628
    # https://www.saramin.co.kr/zf_user/tools/holi-calculator
    @property
    def complete_working_months_and_last_month_days(self):
        # end_date = self.last_working_date

        ## self.join_date + relativedelta(months=1) 는 정확히 다음달 같은 일을 나타낸다
        # - 2월1일(join) 입사했으면, 3월1일(today)에 연차가 생기도록, (딱 1달이 되는날)
        # - 차이가 1달이라는 말은, 시작일제외하고 [시작일로부터 차이가 한달]이 지났다는 말이다.
        #    3-1 = 시작일 빼고 2일,   차이6 => 시작일포함 7일, 시작일 제외 시작일부터 6일지남
        # - 계산기준일에 relativedelta를 끼워서 계산하도록 한다.
        # - 월차휴가 계산과 동일하며, 월차는 연도제한 + 연차도 계산해야한다.
        # months, days = self.calc_complete_month_and_days(self.join_date, end_date)

        leave_histories = self.get_leave_histories()
        # 1) 중간에 휴-복직 기록이 없는 경우, 입사-마지막근무일로 만근개월수를 계산한다
        if not leave_histories:
            complete_months, last_month_days = self.calc_complete_month_and_days(self.join_date, self.last_working_date)
            # print(f"휴-복직 없는 놈({self.join_date}~{self.last_working_date}) => 한번에 계산 {complete_months, last_month_days}")
            return complete_months, last_month_days
        # 2) 중간 휴-복직 기록이 있을 경우, 입사일-마지막근무일과 모두 합해서, 정렬한 뒤,
        #   => 2개씩 짝지어 섹션마다 만근개월수를 계산한다.
        else:
            dates = [self.join_date, self.last_working_date]
            # 휴-복직 기록의 날짜만 골라서,  1차원 list로 평탄화하여 extends
            dates += list(itertools.chain(*[(x.leave_date, x.reinstatement_date) for x in leave_histories]))

            total_complete_months = 0
            last_month_days = None
            for srt, end in grouped(sorted(dates), 2):
                complete_months, remain_days = self.calc_complete_month_and_days(srt, end)
                total_complete_months += complete_months
                last_month_days = remain_days
                # print(f"휴-복직 있는놈({srt}~{end})=> 매번 계산 {complete_months, remain_days}")
            # print(f"휴-복직 있는놈=> 최종 계산 {total_complete_months, last_month_days}")
            return total_complete_months, last_month_days

    # 만근 개월수 => 만근 년수 만들기(원래는 해당연도별로 필터링해서, 해당연도 만근했는지 확인해야할 듯)
    @property
    def complete_working_years(self):
        months, _ = self.complete_working_months_and_last_month_days
        years, _ = divmod(months, 12)
        return years

    @property
    def complete_working_date(self):
        months, days = self.complete_working_months_and_last_month_days
        years, months = divmod(months, 12)

        result = f'{days}일'
        if months:
            result = f"{months}개월" + result
        if years:
            result = f"{years}년" + result

        return result

    #### 여기는 1개월만근과 관계없이 입사 N년차(1부터 시작)
    @property
    def years_from_join(self):
        end_date = self.last_working_date

        years = 1
        while end_date >= self.join_date + relativedelta(years=1):
            end_date -= relativedelta(years=1)
            years += 1

        return years

    @property
    def employee_number(self):
        return f"{self.join_date.year}{self.id:04d}"

    def __repr__(self):
        return '<Employee %r>' % self.id

    def to_dict(self, without_id=False):
        d = super().to_dict()
        del d['add_date']  # base공통칼럼을 제외해야 keyword가 안겹친다
        del d['pub_date']
        # del d['user']  # 관계필드는 굳이 필요없다. -> inspect안써서 더이상 관계필드 조홰 안한다.
        # form에서는 id를 넣어주면 중복되서 삭제햇었는데, view에서는 필요로 한다.
        if without_id:
            del d['id']
        return d

    def update2(self, info_dict, **kwargs):
        if info_dict:
            for k, v in info_dict.items():
                setattr(self, k, v)

        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_by_user_id(cls, user_id: int):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.user_id == user_id)
            )

            return db.session.scalars(stmt).first()

    #### with other entity
    def get_my_departments(self, as_leader=False, as_employee=False, as_min_level=False, except_dept_id=None):
        with DBConnectionHandler() as db:

            # 부서정보 -> Employee
            subq_stmt = (
                select(EmployeeDepartment.department_id)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.employee.has(Employee.id == self.id))
            )

            #### 부서 변경시, 현재부서를 제외한 부서들을 조회하기 위한 keyword 및 stmt 추가
            if except_dept_id:
                subq_stmt = subq_stmt.where(EmployeeDepartment.department_id != except_dept_id)

            # 부서 중에 내가 팀장인 부서정보만
            if as_leader:
                subq_stmt = subq_stmt.where(EmployeeDepartment.is_leader == True)

            ## 추가) 부서 중에 내가 팀원으로 있는 정보만
            if as_employee:
                subq_stmt = subq_stmt.where(EmployeeDepartment.is_leader == False)

            dep_ids = (
                subq_stmt
            ).scalar_subquery()

            # 내가  소속중인 부서 추출
            #### as_min_level을 적용하면 select문이 달라진다.
            ## => 다른 테이블이 아닌 [같은 테이블 필터링 후]의 집계결과를 where scalar_subquery로 쓸 순 없다
            ##    주entity의 필터링(where)된 결과 그대로 이어서 집계적용하려면 subquery에 correlate( 주entity)를 줘야하며
            ##    correlate를 준 뒤로는, scalar_subquery에 from이 생략되어 where절에서 집계가 불가능하다.
            ## => correlate 주entity stmt유지 집계 => select절의 집계로 사용되어야한다.
            if as_min_level:
                # correlate + select 는 entity원본으로 지정해야, 원본entity필터링된 상황에서 적용된다.
                min_level_subq = (
                    select(func.min(Department.level))
                ).correlate(Department) \
                    .scalar_subquery()

                # 필터링 끝난 뒤에 같은entity 집계는 select절에서 바로 띄우면, 해당 집계 데이터만 나온다
                # -> select절에 객체, 집게subquery지만, .all()로 하면 객체만 / .execute()하면 튜플형태로 나온다.
                stmt = (
                    select(Department, min_level_subq)
                    .where(Department.id.in_(dep_ids))
                )


            else:
                stmt = (
                    select(Department)
                    .where(Department.id.in_(dep_ids))
                )

            # 내가 소속중인 부서 중에 가장 상위 부서 (level 낮은 부서) 필터링 -> 여러개 or [] 일 수 있음.
            # 1) min_level이 필터링 된 주체entity에 대한 것에서 집계하려면
            # => corrleate필수다. 주entity 전체에 대한 집계를 해서  min_level = 0으로 잡힌다.
            # 2) 주stmt에 where scalar_subquery에 거는 순간, correlate때문에 where절에 from절이 없다고 에러가 뜬다
            # 3) aliased를 적용해줬더니.. level이 다시 0으로 잡혀서 주체entity를 인식 못한다.
            # => aliased를 주entity필터링 결과 그대로 집계시 + correlate에는 적용 못한다.

            #### ValueError: None is not a valid DepartmentType
            #### 아예 부서정보가 조회안됬는데 as_min_level=True로 집계한다면 오류가 난다.
            # 일단 try except로 잡아보자.
            try:
                return db.session.scalars(
                    stmt
                    .order_by(Department.path)
                ).all()
            except ValueError:
                return []

    # refactor
    def get_departments(self, as_leader=False, as_employee=False,
                        min_level=False, exclude=None, session=None):
        """
        emp = Employee.get(2)
        emp.get_departments()
        => [Department(id=1, name='상위부서', parent_id=None, sort=1, path='001'), Department(id=2, name='하위부서1', parent_id=1, sort=1, path='001001'), Department(id=3, name='하위부서2', parent_id=1, sort=2, path='001002')]
        emp.get_departments(as_leader=True)
        => [Department(id=1, name='상위부서', parent_id=None, sort=1, path='001'), Department(id=3, name='하위부서2', parent_id=1, sort=2, path='001002')]
        emp.get_departments(as_employee=True)
        => [Department(id=2, name='하위부서1', parent_id=1, sort=1, path='001001')]
        emp.get_departments(min_level=True)
        => [Department(id=1, name='상위부서', parent_id=None, sort=1, path='001')]
        emp.get_departments(exclude=1)
        => [Department(id=2, name='하위부서1', parent_id=1, sort=1, path='001001'), Department(id=3, name='하위부서2', parent_id=1, sort=2, path='001002')]
        emp.get_departments(exclude=[1,2])
        => [Department(id=3, name='하위부서2', parent_id=1, sort=2, path='001002')]
        """
        # Department_ = self.__class__.departments.property.mapper.class_
        # -> 이것도 되지만 aliased일때 처리가 추가된 듯? -> 아님.. 걍 됨.
        Department_ = self.__class__.departments.mapper.class_

        initial_filter_name = 'is_belonged_to'
        if as_leader and as_employee:
            raise Exception(f'only 1 select as_leader or as_employee')
        elif as_leader:
            initial_filter_name += '_as_leader'
        elif as_employee:
            initial_filter_name += '_as_employee'

        filter_map = {
            'and_': {
                f'{initial_filter_name}': self
            }
        }

        # 배제할 dept_id가 있다면, 추가 (view에서 선택된 dept를 제외할 때)
        if exclude:
            if isinstance(exclude, abc.Iterable):
                filter_map.get('and_').update({'id__notin': exclude})
            else:
                filter_map.get('and_').update({'id__ne': exclude})

        # 지금까지의 query에 집계값을 filter에 반영하기
        if min_level:
            # 1. 지금까지 사용된 query를 얻기 위해 실행직전까지를 obj로 만든다.
            # obj = Department_.filter_by(**filter_map).order_by('path')
            # # 2. .alias()를 통해 Subquery를 만들어고 변수로 뽑아 from이 될 준비를 한다.
            # # -> 이 순간, @hybrid_property는 못쓰게 되며, subquery.a.칼럼으로 뽑아서 select한다
            # a = obj._query.alias() # .alias()는 subquery를 만든다.
            a = Department_.filter_by(**filter_map).subquery()
            # 3. 집계 expression을 a.c.칼럼으로 expression을 작성하고, select_from( a )를 추가하여 새로운 query를 만듦.
            level_expr = func.length(a.c.path) / Department_._N - 1
            min_query = select(func.min(level_expr)).select_from(a)
            # 4. 집계가 제대로 뽑히는지 test
            # min_level_scalar = obj._session.scalar(
            #     min_query
            # )
            # 5. main query와 함께 실행 + where절에 value로 사용할 수 있도록 scalar_subquery()를 붙인다.
            # - 이 때, main query와 무관한 집계여야만, main query의 where절(filter_by의 value)에 사용할 수 있다.
            min_level_subq = min_query.scalar_subquery()

            # 6. 집계값을 filter_by에 동적으로 추가한다.
            filter_map.get('and_').update({'level': min_level_subq})

        return Department_.filter_by(**filter_map, session=session).order_by('path').all()

    def get_level_1_department_id(self):
        """
        e = Employee.get(1)
        e.get_level_1_department_id()
        ----
        6 or None
        """
        Department_ = self.__class__.departments.mapper.class_

        depts = self.get_departments()

        level_1_depts = set()
        for dept in depts:
            level_1_depts.add(Department_.get_level_1_department_id(dept))

        if len(level_1_depts) > 1:
            raise Exception(f'{self}는 현재 2개이상의 그룹에 소속 중입니다. 1개의 그룹에만 일하도록 해주세요.')

        return next(iter(level_1_depts), None)

    #### with other entity
    # def is_leader_in(self, department: Department):
    #     with DBConnectionHandler() as db:
    #         stmt = (
    #             select(EmployeeDepartment)
    #             .where(EmployeeDepartment.dismissal_date.is_(None))
    #             .where(EmployeeDepartment.department.has(Department.id == department.id))
    #             .where(EmployeeDepartment.employee.has(Employee.id == self.id))
    #         )
    #
    #         emp_dep: EmployeeDepartment = db.session.scalars(stmt).first()
    #
    #         if not emp_dep:
    #             return False
    #
    #         return emp_dep.is_leader

    # refactor
    def is_leader_in(self, department, session=None):
        """
        dept = Department.get(1)
        emp = Employee.get(2)
        emp.is_leader_in(dept)
        True
        dept2 = Department.get(2)
        emp.is_leader_in(dept2)
        False
        """
        EmployeeDepartment_ = self.__class__.employee_departments.mapper.class_
        is_leader = EmployeeDepartment_.filter_by(
            dismissal_date=None,
            is_leader=True,
            is_recorded_about=self,
            is_recorded_in=department,
            session=session
        ).exists()

        return is_leader

    #### with other entity
    def get_leader_or_senior_leader(self):
        # 1) 내 상사를 찾기 위해, 내가 가진 부서중 가장 상위 부서를 찾는다.
        min_level_dept: Department = self.get_my_departments(as_min_level=True)
        # print(f"min_level_dept = >{min_level_dept}")
        # -> list로 나오기 때문에 [0] 해주기 애초에 부서가 없으면, None return

        # 2) 부서가 없으면, 상사도 없으니 None을 반환한다
        if not min_level_dept:
            return None
        # (부서가 있을 때, min_level의 부서(들) list에서 path순 정렬됬으니 1개만 가져온다)
        min_level_dept = min_level_dept[0]

        # 3) (부서가 있을 때) 내가 팀장일 땐, 부모부서가 있는지 확인 후,
        if self.is_leader_in(min_level_dept):
            #  3-1) 부모부서 없으면 상사None,
            if not min_level_dept.parent_id:
                return None
            #  3-2) 부모부서 있으면 부모부서를 시작으로 가장 가까운 팀장을 찾는다.
            with DBConnectionHandler() as db:
                parent_dept = db.session.scalars(
                    select(Department)
                    .where(Department.id == min_level_dept.parent_id)
                ).first()

                parent_leader_id = parent_dept.get_leader_id_recursively()
                if parent_leader_id:
                    return Employee.get_by_id(parent_leader_id)
                return None
        # 4) (내가 팀장이 아닐 땐) 현 부서의 가까운 팀장을 찾아서 반환한다.
        leader_id = min_level_dept.get_leader_id_recursively()
        if leader_id:
            return Employee.get_by_id(leader_id)
        return None

    #### with other entity
    def get_dept_id_and_name_and_position_list(self):
        with DBConnectionHandler() as db:
            stmt = (
                select(Department.id, Department.name, EmployeeDepartment.position)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.employee_id == self.id)
                # dept name정보 + 부서 active필터링를 위해 join
                .join(EmployeeDepartment.department)
                # .where(Department.status == 1) # postgre는 Boolean필드에 대해서 boolean으로만 비교한다.
                .where(Department.status)
                # level순으로 정렬하기 위해, path로 정렬
                .order_by(Department.path, EmployeeDepartment.is_leader.desc())
            )
            return db.session.execute(stmt).all()

    #### EmployeeDepartment의 (고용일은 당연있고) 휴직일x퇴사일x/휴직했고 복귀X/퇴사일찍힘.jobstatus로 정렬하기 위해
    #### EmployeeDepartment에 . statushybrid_propert -> expression 완성하여 => order_by
    ####                     .status_string을 .status로 만들어서 -> select

    #### with other entity
    def get_dept_history_row_list(self):
        with DBConnectionHandler() as db:
            stmt = (
                select(Department.id, Department.name,
                       # EmployeeDepartment.status,# 정렬에 사용하고, 따로 한글로 매핑함.
                       EmployeeDepartment.status,
                       EmployeeDepartment.status_string,
                       EmployeeDepartment.position,
                       EmployeeDepartment.is_leader,
                       EmployeeDepartment.start_date,
                       EmployeeDepartment.end_date,
                       )
                # .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.employee_id == self.id)
                # dept name정보 + 부서 active필터링를 위해 join
                .join(EmployeeDepartment.department)
                # .where(Department.status == 1)
                # 퇴사정보를 맨 처음, 그다음 복직정보, 그다음 휴직/재직 정보 순으로
                #  + 같은 상태면, 종료일이 빠른 빠른 순으로 먼저
                .order_by(desc(EmployeeDepartment.status), EmployeeDepartment.start_date,
                          EmployeeDepartment.end_date)
            )
            return db.session.execute(stmt).all()

    #### with other entity
    def get_position_by_dept_id(self, dept_id):
        with DBConnectionHandler() as db:
            if self not in db.session:
                db.session.add(self)

            stmt = (
                select(EmployeeDepartment.position)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.employee_id == self.id)
                .where(EmployeeDepartment.department_id == dept_id)
                # dept name정보 + 부서 active필터링를 위해 join
                .join(EmployeeDepartment.department)
                .where(Department.status)
            )
            position = db.session.scalar(stmt)
            return position if position else '(공석)'

    #### with other entity
    # @hybrid_property
    # def role(self):
    #     with DBConnectionHandler() as db:
    #         stmt = (
    #             select(Role)
    #             .where(Role.user.has(User.id == self.user_id))
    #         )
    #         role = db.session.scalars(stmt).first()
    #         return role

    # refactor
    @hybrid_property
    def role(self):
        return self.user.role

    @role.setter
    def role(self, role):
        self.user.role = role

    # refactor => @hybrid_property와 동일한 이름의 method/expression을 생성하면 filter_by에 걸리기도 전에 덮어쓴다.
    @hybrid_method
    def has_role(cls, role, mapper=None):
        """
        *@hybrid_property보다 위에 정의한 경우 -> filter_by로 표현식을 getattr()로 만들 때,
           @hybrid_property를 가져가서, getattr(cls, attr, None)시 표현식이 안만들어진다.
           더 아래쪽의 @hybrid_property를 가져가면 getattr()에서 None으로 반환됨.
        => Employee.filter_by(role=Role.get(2)).all()
        []

        *@hybrid_proerty보다 아래에 정의하여 -> filter_by 표현식에서 @hybrid_method가 잡혀가게 해야한다.

        => Employee.filter_by(role=Role.get(2)).all()
        [<Employee 5>]
        """
        mapper = mapper or cls
        User_ = mapper.user.mapper.class_
        return mapper.user.has((User_.role_id == role.id))

    # refactor => @hybrid_method는 method(value, mapper)를 타기 때문에 __ne이 적용안된다.
    # @hybrid_method
    # def has_role_name(cls, role_name, mapper=None):
    #     """
    #     # Rel-Rel의 id or obj가 아닌, Role의 특정 필드(name)를 인자로 필터링 한다면,
    #     # Re + Rel모두 class_를 뽑아낸 뒤, has ( has())로 2번 걸어줘야한다.
    #     # has1개만 두면, EXIST 절이 casadian product from Rel1, Rel1로 잡히게 된다.
    #
    #     Employee.filter_by(has_role_name__ne='ADMINISTRATOR').all()
    #     => [<Employee 2>, <Employee 3>, <Employee 4>, <Employee 5>]
    #     """
    #     mapper = mapper or cls
    #     User_ = mapper.user.mapper.class_
    #     Role_ = User_.role.mapper.class_
    #
    #     return mapper.user.has(User_.role.has(Role_.name == role_name))

    # refactor
    @hybrid_method
    def except_admin(cls, value, mapper=None):
        """
        Employee.filter_by(except_admin=True).all()
        => [<Employee 2>, <Employee 3>, <Employee 4>, <Employee 5>]
        """
        mapper = mapper or cls
        User_ = mapper.user.mapper.class_
        Role_ = User_.role.mapper.class_

        return mapper.user.has(User_.role.has(Role_.name == Roles.ADMINISTRATOR.name)) != value

    @hybrid_property
    def is_staff(self):
        # return self.role.is_(Roles.STAFF)
        return self.user.role.is_(Roles.STAFF)

    @hybrid_property
    def is_chiefstaff(self):
        """
        required: Employee.load({'user': ('selectin', {'role':'selectin'})})
        """
        return self.user.role.is_(Roles.CHIEFSTAFF)

    #### with other entity
    @hybrid_property
    def is_executive(self):
        # return self.role.is_(Roles.EXECUTIVE)
        return self.user.role.is_(Roles.EXECUTIVE)

    #### with other entity
    @hybrid_property
    def is_administrator(self):
        # return self.role.is_(Roles.ADMINISTRATOR)
        return self.user.role.is_(Roles.ADMINISTRATOR)

    @classmethod
    def get_by_name(cls, name):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.name == name)
            )

            return db.session.scalars(stmt).first()

    # @classmethod
    # def get_by_id(cls, id):
    #     with DBConnectionHandler() as db:
    #         stmt = (
    #             select(cls)
    #             .where(cls.id == id)
    #         )
    #
    #         return db.session.scalars(stmt).first()

    @classmethod
    def get_by_ids(cls, emp_ids: list):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.id.in_(emp_ids))
                # view에서 직원들만 나타낼 떄 입사순으로
                .order_by(cls.join_date)
            )

            return db.session.scalars(stmt).all()

    # delete
    # @classmethod
    # def get_not_resigned_by_id(cls, id):
    #     with DBConnectionHandler() as db:
    #         stmt = (
    #             select(cls)
    #             .options(selectinload('user').selectinload('role'))
    #             .where(cls.id == id)
    #             .where(cls.job_status != JobStatusType.퇴사)
    #         )
    #
    #         return db.session.scalars(stmt).first()

    # refactor
    # def update_job_status(self, job_status, target_date):
    #     """
    #     EagerLoad required: User.Role + EmployeeDepartment
    #     ----
    #     employee = Employee.load({'user': ('selectin', {'role': 'selectin'}),
    #                           'employee_departments': 'joined',
    #                           }) \
    #         .filter_by(id=employee_id).first()
    #     """
    #     #### 재직->퇴사로 변경하는 경우
    #     # 1) job_status assign
    #     # 2) resign_date assign
    #     # 3) log(reference) append
    #     # 4) #R.user.role -> default 'USER' assign if not default
    #     # 5) #R Many EmployeeDepartment list -> dismissal_date assign
    #     if JobStatusType.is_resign(job_status):
    #         for emp_dept in self.employee_departments:
    #             emp_dept.dismissal_date = target_date
    #
    #         if not self.user.role.default:
    #             self.user.role = Role.filter_by(name='USER').first()
    #
    #         reference = f'퇴사({format_date(target_date)})'
    #         if self.reference:
    #             reference += '</br>' + self.reference
    #
    #         data = dict(job_status=job_status, resign_date=target_date, reference=reference)
    #         return self.update(**data)
    #
    #     #### 재직->휴직으로 변경하는 경우
    #     # 1) job_status assign
    #     # 2) leave_date assign
    #     # 3) log(reference) append
    #     # 4) #R Many EmployeeDepartment list -> leave_date assign + (기존 최종복직일 비우기)reinstatement_date None assign
    #     elif JobStatusType.is_leave(job_status):
    #         for emp_dept in self.employee_departments:
    #             emp_dept.leave_date = target_date
    #             emp_dept.reinstatement_date = None
    #
    #         reference = f'휴직({format_date(target_date)})'
    #         if self.reference:
    #             reference += '</br>' + self.reference
    #
    #         data = dict(job_status=job_status, leave_date=target_date, reference=reference)
    #         return self.update(**data)
    #
    #     #### 휴직->복직(재직)으로 변경하는 경우
    #     # 1) job_status assign
    #     # 2) (복직일 기록은 없고, EmployeeLeaveHistory가 target_date로 생성된다)
    #     # 3) log(reference) append
    #     # 4) #R Many EmployeeDepartment list -> reinstatement_date assign
    #     # 5) EmployeeLeaveHistory create by emp, emp.leave_date + target_date(reinstatement_date)
    #     elif JobStatusType.is_active(job_status):
    #         for emp_dept in self.employee_departments:
    #             emp_dept.reinstatement_date = target_date
    #
    #         reference = f'복직({format_date(target_date)})'
    #         if self.reference:
    #             reference += '</br>' + self.reference
    #
    #         # EmployeeLeaveHistory.create(employee=self, leave_date=self.leave_date,
    #         #                             reinstatement_date=target_date)
    #         #### class를 가져와서 연결하려면, self.관계가 아니라, self.__class__.관계로 접근해야RelationshipProperty가 나온다
    #         # => self.로 접근하면, list가 나온다.
    #         EmployeeLeaveHistory_ = self.__class__.employee_leave_histories.property.mapper.class_
    #         EmployeeLeaveHistory_.create(employee=self, leave_date=self.leave_date,
    #                                      reinstatement_date=target_date)
    #
    #         data = dict(job_status=job_status, reference=reference)
    #         return self.update(**data)
    #     else:
    #         raise KeyError(f'Invalid job status : {job_status}')

    # refactor 2 -  load없이도 호출되도록 변경
    def update_job_status(self, job_status, target_date, session: Session = None, auto_commit=True):
        """
        EagerLoad required: User.Role + EmployeeDepartment -> X
        ----
        employee = Employee.load({'user': ('selectin', {'role': 'selectin'}),
                              'employee_departments': 'joined',
                              }) \
            .filter_by(id=employee_id).first()
        """
        if not session:
            session = self.get_scoped_session()
        session.add(self)

        #### 재직->퇴사로 변경하는 경우
        # 1) job_status assign
        # 2) resign_date assign
        # 3) log(reference) append
        # 4) #R.user.role -> default 'USER' assign if not default
        # 5) #R Many EmployeeDepartment list -> dismissal_date assign
        if JobStatusType.is_resign(job_status):
            for emp_dept in self.employee_departments:
                emp_dept.dismissal_date = target_date

            if not self.role.default:
                self.role = Role.filter_by(name='USER', session=session).first()

            reference = f'퇴사({format_date(target_date)})'
            if self.reference:
                reference += '</br>' + self.reference

            data = dict(job_status=job_status, resign_date=target_date, reference=reference)
            return self.update(**data, session=session, auto_commit=auto_commit)

        #### 재직->휴직으로 변경하는 경우
        # 1) job_status assign
        # 2) leave_date assign
        # 3) log(reference) append
        # 4) #R Many EmployeeDepartment list -> leave_date assign + (기존 최종복직일 비우기)reinstatement_date None assign
        elif JobStatusType.is_leave(job_status):
            for emp_dept in self.employee_departments:
                emp_dept.leave_date = target_date
                emp_dept.reinstatement_date = None

            reference = f'휴직({format_date(target_date)})'
            if self.reference:
                reference += '</br>' + self.reference

            data = dict(job_status=job_status, leave_date=target_date, reference=reference)
            return self.update(**data, session=session, auto_commit=auto_commit)

        #### 휴직->복직(재직)으로 변경하는 경우
        # 1) job_status assign
        # 2) (복직일 기록은 없고, EmployeeLeaveHistory가 target_date로 생성된다)
        # 3) log(reference) append
        # 4) #R Many EmployeeDepartment list -> reinstatement_date assign
        # 5) EmployeeLeaveHistory create by emp, emp.leave_date + target_date(reinstatement_date)
        elif JobStatusType.is_active(job_status):
            for emp_dept in self.employee_departments:
                emp_dept.reinstatement_date = target_date

            reference = f'복직({format_date(target_date)})'
            if self.reference:
                reference += '</br>' + self.reference

            # EmployeeLeaveHistory.create(employee=self, leave_date=self.leave_date,
            #                             reinstatement_date=target_date)
            #### class를 가져와서 연결하려면, self.관계가 아니라, self.__class__.관계로 접근해야RelationshipProperty가 나온다
            # => self.로 접근하면, list가 나온다.
            EmployeeLeaveHistory_ = self.__class__.employee_leave_histories.property.mapper.class_
            EmployeeLeaveHistory_.create(employee=self, leave_date=self.leave_date,
                                         reinstatement_date=target_date,
                                         session=session,
                                         auto_commit=False,
                                         )

            data = dict(job_status=job_status, reference=reference)
            return self.update(**data, session=session, auto_commit=auto_commit)
        else:
            raise KeyError(f'Invalid job status : {job_status}')

    # ### with other entity
    # @classmethod
    # def change_job_status(cls, emp_id: int, job_status: int, target_date):
    #     #### 퇴사상태로 변경하는 경우 -> job_stauts 외 resign_date 할당 + (other entity)role을 default인 USER로 변경
    #     #     - 관계entity의 속성을 변경해야하므로, sql으로 하지 않고, 객체를 찾아서 변경하도록 변경한다.
    #     #### 그외 EmployeDepartment에서 자신의 취임정보에 dismissal_date를 할당하여 비활성화 한다.
    #     if job_status == JobStatusType.퇴사:
    #         with DBConnectionHandler() as db:
    #             emp: Employee = cls.get_by_id(emp_id)
    #
    #             emp.job_status = job_status
    #             # emp.resign_date = datetime.date.today()
    #             emp.resign_date = target_date
    #
    #             emp.fill_reference(f'퇴사({format_date(target_date)})')
    #
    #             #### 관계필드를 조회하는 순간 같은세션에서 같은 key의 객체를 가져오게 되므로
    #             #### USER role이 아닌 경우에만, USER role을 찾아서 대입해준다.
    #             if emp.user.role.default != True:
    #                 emp.user.role = Role.get_by_name('USER')  # emp.role은 User의 role을 가져오는 식이므로 변경에 못쓴다.
    #
    #             db.session.add(emp)
    #
    #             #### 해당부서에 해임까지 시키기 => 내가 속한 모든 부서취임 정보list를 가져와서
    #             # -> 모드 해임일을 입력하여 비활성화 시킨다.
    #             emp_dept_list: list = EmployeeDepartment.get_by_emp_id(emp.id)
    #             for emp_dept in emp_dept_list:
    #                 emp_dept.dismissal_date = target_date
    #
    #             db.session.add_all(emp_dept_list)
    #             db.session.commit()
    #
    #             return emp
    #
    #     #### 휴직은 job_status만 변경(퇴직일X, ROLE변화X)
    #     #### emp_dept에 휴직일 기입
    #     elif job_status == JobStatusType.휴직:
    #         with DBConnectionHandler() as db:
    #             emp: Employee = cls.get_by_id(emp_id)
    #
    #             emp.job_status = job_status
    #             #### 휴직시, 최종 휴직일칼럼도 채운다 like 퇴직
    #             emp.leave_date = target_date
    #
    #             emp.fill_reference(f'휴직({format_date(target_date)})')
    #
    #             db.session.add(emp)
    #
    #             ####  휴직시 기존 취임정보(들)에 휴직일을 찍었음.
    #             emp_dept_list: list = EmployeeDepartment.get_by_emp_id(emp.id)
    #             for emp_dept in emp_dept_list:
    #                 emp_dept.leave_date = target_date
    #                 ####  new) for leave history => 휴직시, 최종복직일을 비우는 로직 추가
    #                 emp_dept.reinstatement_date = None
    #
    #             db.session.add_all(emp_dept_list)
    #             db.session.commit()
    #
    #             return emp
    #
    #     #### 복직처리 => 기존 부서 그대로 복직한다. 필요하면 해임하고, 부서변경해야한다.
    #     elif job_status == JobStatusType.재직:
    #         with DBConnectionHandler() as db:
    #             emp: Employee = cls.get_by_id(emp_id)
    #
    #             emp.job_status = job_status
    #
    #             emp.fill_reference(f'복직({format_date(target_date)})')
    #
    #             db.session.add(emp)
    #
    #             emp_dept_list: list = EmployeeDepartment.get_by_emp_id(emp.id)
    #             for emp_dept in emp_dept_list:
    #                 emp_dept.reinstatement_date = target_date
    #
    #             db.session.add_all(emp_dept_list)
    #
    #             #### new) 복직시, 휴-복직일이 완성되어, leave_history를 남긴다
    #             leave_history = EmployeeLeaveHistory(employee=emp,
    #                                                  # 휴직일을, 내가속한부서들에서 가져오지말고, emp에 만들어준 최종휴직일을 써보자.
    #                                                  leave_date=emp.leave_date,
    #                                                  # 복직일은, 당일이므로 toady를 취임정보에 넣듯이 today로 처리해보자.
    #                                                  reinstatement_date=target_date,
    #                                                  )
    #             db.session.add(leave_history)
    #
    #             db.session.commit()
    #
    #             return emp

    def fill_reference(self, text):
        if not self.reference:
            self.reference = text
        else:
            self.reference = text + '</br>' + self.reference

    #### with other entity
    def get_leave_histories(self):
        with DBConnectionHandler() as db:
            stmt = (
                select(EmployeeLeaveHistory)
                .where(EmployeeLeaveHistory.employee_id == self.id)  # 있다는 말은 이미 휴직/복직 set완성
                .order_by(EmployeeLeaveHistory.add_date)  # 시간순으로 가져오기
            )

            result = db.session.scalars(stmt).all()
            return result

    #### with other entity
    @property
    def vacations_with_description(self):
        # 1) 입사1년차(1년미만 근무)인 경우, 만근 개월 수 => [1년미만만 알아서 계산하는 월차]를 그대로 반환한다
        complete_months, _ = self.complete_working_months_and_last_month_days
        if self.years_from_join < 2:
            # print('1년차 미만이시네요. 월차만 계산합니다.')
            return complete_months, f"{complete_months}(1년미만)"
        # 2) 입사2년차부터는 입사1년차동안 출근율 80%이상 출근시, 2년차 1일차에 [연차]가 15개가 공짜로 생긴다
        #    기존 1년차 최대 11개에서 + 2~3년차는 매년 +15개씩, 3~4년차는 16개씩 증가한다
        #   => 그렇다면, [월차]계산은 1년차까지만 하고 나머지는 숫자로 누적해얗나다.
        #   => 월차계산시, end_date를 최대 1년으로 계산해야한다.
        #   => srt, end 계산하기 전에, dates목록에서 1년차를 넘어간 것들은 빼야한다?!

        # (2년차 이상) => 2년차 시작일로부터 1년씩 더해가면서, 발생시점을 넘기면 +15,+15, +16, +16
        if self.years_from_join < 4:
            # print('2~3년차시네요. 1년간 월차 + 매년 15개씩 만 계산합니다.')
            # 2, 3년차에는 각각 1*15 , 2* 15를 더한다.
            return complete_months + (
                    self.years_from_join - 1) * 15, f"{complete_months}(1년미만)+15*{(self.years_from_join - 1)}(2~3년차)"
        # (4년차 이상부터) 2개(2,3년차)를 15, 나머지는 16을 더한다.
        else:
            # print('4년차이상이시네요. 1년간 월차 + 2년간(2,3년차) 15개씩 + 4년차부터 16개씩')
            return complete_months + 2 * 15 + (
                    self.years_from_join - 3) * 16, f"{complete_months}(1년미만)+15*{(self.years_from_join - 1)}(2~3년차) + 16*{(self.years_from_join - 3)}(4년차이후)"

    #### with other entity
    #### 직원추가시 팀장 부서가 있다면, 그 부서와 그 하위부서들의 (id, name) list를 반환
    def get_dept_infos_for_add_staff(self):
        #### 관리자일 경우, 모든 부서들 나올 수 있도록
        if self.is_administrator:
            return [(x.id, x.name) for x in Department.get_all()]

        my_min_level_departments_as_leader = self.get_my_departments(as_leader=True, as_min_level=True)
        if not my_min_level_departments_as_leader:
            print("팀장인 부서를 가진 직원만, 해당부서에 직원을 추가할 수 있습니다.")
            return []

        dept_id_and_name_list = []
        for min_dept in my_min_level_departments_as_leader:
            dept_id_and_name_list += min_dept.get_self_and_children_dept_info_tuple_list()

        return [(x[0], x[1]) for x in sorted(dept_id_and_name_list, key=lambda x: x[2])]

    #### with other entity
    #### 나보다 하위 직원들(무소속포함) 받아오기
    def get_under_role_employees(self, no_dept=False):
        with DBConnectionHandler() as db:
            stmt = (
                select(Employee)
                # 관계필드가 아니라, .role은 프로퍼티라서 join조건에 못넣는다.
                #### Employee.role(프로퍼티).id == Role.id 로 할 시,  => 1로 고정되어버리는 현상. => 관계필드가 아니면 expression에 쓰지말자.
                .join(User, Employee.user)
                .join(Role, and_(User.role, Role.is_(Roles.STAFF),
                                 Role.is_under(self.role)))  # 필터링용join entity의 조건은 join시 같이 걸자
                .where(Employee.job_status == 1)  # 재직중인 사람 들 중
                # .where(Role.is_under(행정부장.role)) # 자신의 role permission이 특정직원의 role permission보다 낮은 사람들만 => 필터링용join entity의 조건은 join시 같이 걸어도 된다.
                # 이미 다른 부서에 가입되어있어도 괜찮으니, 무소속을 걸러내진 않는다.
                # .where(~Employee.employee_departments.any())
            )

            if no_dept:
                stmt = stmt.where(~Employee.employee_departments.any())

            return db.session.scalars(stmt).all()

    #### with other entity
    def change_department_with_promote_or_demote(self, after_dept_id, target_date,
                                                 before_dept_id=False,
                                                 as_leader=False,
                                                 ):
        #### after_dept_id는 해당부서가 반드시 존재해야하므로, 존재 검사를 한다
        if not Department.get_by_id(after_dept_id):
            return False, "해당 부서는 사용할 수 없는 부서입니다."

        with DBConnectionHandler() as db:
            #### 부서처리 전에, 승진/강등 여부에 따라, role변경해주기
            # -> 관계객체에 접근시 이미 해당데이터가 있기 때문에, 할당시에는 같은 객체를 불러오면 안된다.
            # -> 외부에서 is_demote가 되려면 STAFF가 아닐 때부터 처리해야한다.
            if self.is_demote(as_leader=as_leader, current_dept_id=before_dept_id):
                self.user.role = Role.get_by_name('STAFF')
                db.session.add(self)
                print("강등입니다.")
            if self.is_promote(as_leader=as_leader):
                self.user.role = Role.get_by_name('CHIEFSTAFF')
                db.session.add(self)
                print("승진입니다.")

            #### 이전 부서가 있는 경우, 이전부서에 해임처리
            # => 위에서 self를 add라느라 썼다면, 쓰지말고 id(value)만 넘겨서 처리되도록 하자.
            if before_dept_id:
                before_emp_dept: EmployeeDepartment = EmployeeDepartment.get_by_emp_and_dept_id(self.id,
                                                                                                before_dept_id)
                before_emp_dept.dismissal_date = target_date

                db.session.add(before_emp_dept)

            after_emp_dept: EmployeeDepartment = EmployeeDepartment(employee_id=self.id,
                                                                    department_id=after_dept_id,
                                                                    is_leader=as_leader,
                                                                    employment_date=target_date)
            result, message_after_save = after_emp_dept.save()

            if result:
                # 만약 after성공했다면, 취임정보.save()의 메세지 대신, 부서변경 메세지로 반환
                db.session.commit()
                return True, f"부서 변경을 성공하였습니다."
            else:
                # 만약 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환
                db.session.rollback()
                return False, message_after_save

    # def change_department(self, current_dept_id, after_dept_id, as_leader, target_date):
    #     with DBConnectionHandler() as db:
    #         ## 부서의 [제거 or 변경/추가] 와 무관하게 승진/강등여부 판단 => role필드 변화해놓기
    #         # => cf) 관계객체(user)의 .role필드에는 해당 데이터가 불러와 있으니, 같은 객체를 get조회해서 대입할시 에러 나니 조심.
    #         if self.is_demote(current_dept_id, after_dept_id, as_leader):
    #             self.user.role = Role.get_by_name('STAFF')
    #             # db.session.add(self) # 뒤에 self.reference변경때문에 add를 좀 더 뒤에서
    #
    #         if self.is_promote(after_dept_id, as_leader):
    #             self.user.role = Role.get_by_name('CHIEFSTAFF')
    #             # db.session.add(self)
    #
    #         ## 현재 취임정보를 제거할 상황(부서변경or부서제거)을 찾아 먼저 제거하기
    #         # (1) 현재부서가 선택되었다면, [부서추가]가 아닌 [부서변경] OR  [부서제거]상황이다.
    #         #    => 둘다 현재부서 취임정보를 해임시켜야한다.
    #         if current_dept_id:
    #             current_emp_dept: EmployeeDepartment = EmployeeDepartment.get_by_emp_and_dept_id(self.id,
    #                                                                                              current_dept_id)
    #             current_emp_dept.dismissal_date = target_date
    #
    #             db.session.add(current_emp_dept)
    #
    #         ## 다음 취임정보를 생성하지 않는 상황(부서 제거) 먼저 처리하기
    #         # (2) after 부서가 선택안되었다면 (current는 무조건 선택된) => [부서제거]의 상황으로 취임정보 생성 없이
    #         #     현재 취임정보 삭제된 상태를 commit하고 끝낸다.
    #         #    1) after부서가 없다면 -> [부서제거]로서 취임정보 생성 없이 바로 return해야한다.
    #         #    =>  after부서가 없는 [부서제거] 상태 ( current는 무조건 있음 )를 처리한다.
    #         #    2) after부서가 있다면 -> [부서변경] or [부서추가]의 상황으로 취임정보 새로 생성되어야한ㄷ다
    #         # (2-1)
    #         if not after_dept_id and current_dept_id:
    #             # 부서제거시, 부서제거 refence입력하고 add
    #             current_dept: Department = Department.get_by_id(current_dept_id)
    #             self.fill_reference(f"[{current_dept.name}]부서 해임({format_date(target_date)})")
    #             db.session.add(self)
    #
    #             db.session.commit()
    #             return True, f"[{current_dept.name}]부서 제거를 성공하였습니다."
    #
    #         ## 다음 취임정보를 생성하는 상황(부서 변경 or 부서 추가)
    #         # (2-2) (after부서가 있는 상태): current O[부서변경] or current X [부서추가] -> after 부서 취임정보 생성
    #         after_emp_dept: EmployeeDepartment = EmployeeDepartment(employee_id=self.id,
    #                                                                 department_id=after_dept_id,
    #                                                                 is_leader=as_leader,
    #                                                                 employment_date=target_date)
    #         result, message_after_save = after_emp_dept.save()
    #
    #         if result:
    #             ## result가 True라는 말은, after부서가 있어서 => 새로운 부서 취임정보 생성 완료
    #             after_dept: Department = Department.get_by_id(after_dept_id)
    #             # (3) current부서 O : 부서 변경 / current부서 X : 부서 추가
    #             # (4) 취임정보.save()에서 나온 성공1/실패N 메세지 중 [취임정보 생성 성공1]에 대해
    #             # => current O/X에 따라 부서변경/ 부서추가의 메세지 따로 반환
    #             if current_dept_id:
    #                 current_dept: Department = Department.get_by_id(current_dept_id)
    #                 self.fill_reference(f"[{current_dept.name}→{after_dept.name}]부서 변경({format_date(target_date)})")
    #
    #                 message = f"부서 변경[{current_dept.name}→{after_dept.name}]을 성공하였습니다."
    #
    #             else:
    #                 self.fill_reference(f"[{after_dept.name}]부서 취임({format_date(target_date)})")
    #                 message = f"부서 추가[{after_dept.name}]를 성공하였습니다."
    #
    #             db.session.add(self)
    #             db.session.commit()
    #
    #             return True, message
    #
    #         ## save에 실패하면 message_after_save의 이유로 실패했다고 rollback하고  반환한다.
    #         # (5) 최종 저장여부를 결정하는 것은 부서변경여부다. .save()가 실패하여 result가 False로 올경우 rollback한다.
    #         else:
    #             # (2-2) 만약  after부서에 취임 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환 => route에서 그대로 취임실패 메세지를 flash
    #             db.session.rollback()
    #             return False, message_after_save

    # refactor
    def change_department2(self, current_dept_id, after_dept_id, as_leader, target_date):
        """
        required : Employee.load({
                    'user': ('selectin', {'role':'selectin'}),
                    'employee_departments':'joined' # for update employee_departments fill
                })\
        """
        data = dict()  # 한번에 fill = update의 인자로 주기 위해 모으기 용

        # 여기는 role은 property다.
        # Employee -> user -> Role로 이으려면, 연달아서 가아야한다.
        # Role_ = self.__class__.role.property.mapper.class_
        Role_ = self.__class__.user.mapper.class_.role.mapper.class_

        # 1. 승진여부 -> #Role 변화 : 부서변화(취임정보)의  [제거 or 변경/추가]와 무관하게 먼저 판단하기
        if self.is_demote(current_dept_id, after_dept_id, as_leader):
            # self.user.role = Role.filter_by(name='STAFF').first()
            # self.fill(role =Role.filter_by(name='STAFF').first())
            data['role'] = Role_.filter_by(name='STAFF').first()

        elif self.is_promote(after_dept_id, as_leader):
            # self.fill(role=Role.filter_by(name='CHIEFSTAFF').first())
            data['role'] = Role_.filter_by(name='CHIEFSTAFF').first()

        EmployeeDepartment_ = self.__class__.employee_departments.mapper.class_
        # 2. 선택된 [현재부서]의 [취임정보#EmployeeDepartment 해임 표시] 할 상황 -> [부서변경]or[부서제거]을 찾아 처리
        # (1) 현재부서가 선택되었다면, [부서추가]가 아닌 => [부서변경] OR [부서제거]상황  => 둘다 현재부서 [취임정보를 해임]시켜야한다.
        if current_dept_id:
            current_emp_dept = EmployeeDepartment_.filter_by(
                dismissal_date=None,
                employee_id=self.id,
                department_id=current_dept_id,
            ).first()
            # many relationship 객체인데, 1개를 수정해야하는 상황이면, fill/update에 list가 아닌 1개의 수정된 obj를 넣어주면
            # -> fill내부에서 append로 반영되고, 기존에 존재하던 것도 merge에 의해 자동 수정 반영된다.
            current_emp_dept.dismissal_date = target_date
            # self.fill(employee_departments=current_emp_dept)
            data['employee_departments'] = current_emp_dept

        # (2) 다음 취임정보#EmployeeDepartment를 생성하지 않는 상황 -> [부서 제거] 먼저 처리하기
        #    -> after 부서가 선택안되었다면 (current는 무조건 선택된) => [부서제거]의 상황으로 취임정보 생성 없이
        #       현재 취임정보 해임된 상태를 commit하고 끝낸다.
        #    (2-1) after부서가 없다면 -> [부서제거]로서 취임정보 생성 없이 바로 return해야한다.
        #       =>  after부서가 없는 [부서제거] 상태 ( current는 무조건 있음 )를 처리한다.
        #    (2-2) after부서가 있다면 -> [부서변경] or [부서추가]의 상황으로 취임정보 새로 생성되어야한ㄷ다
        Department_ = self.__class__.departments.mapper.class_
        # (2-1)
        if not after_dept_id:
            # 부서제거시, 부서제거 reference입력하고 add
            current_dept = Department_.get(current_dept_id)
            self.fill_reference(f"[{current_dept.name}]부서 해임({format_date(target_date)})")
            # result, msg = self.update()
            result, msg = self.update(**data)
            if result:
                return True, f"[{current_dept.name}]부서 제거를 성공하였습니다."
            else:
                return False, msg

        # (2-2) 다음 취임정보#EmployeeDepartment를 생성하는 상황(부서 변경 or 부서 추가)
        # (2-2-1) (after부서가 있는 상태): current O[부서변경] or current X [부서추가] -> after 부서 취임정보 생성
        #### 추가. .save()에 검증을 통합하지말고, .create()위에 일단 정의하기

        # 추가1. exists()는 create에 fill될 keyword를 가지고 미리 filter_by를 만든 뒤 호출한다.
        # 이 때, fill될 데이터는 filter_by + create 둘다에서 쓸 것이니 -> 미리 변수로 만들어놓는다.
        # result, message_after_save = after_emp_dept.save()
        after_emp_dept_data = dict(
            dismissal_date=None,  # default 칼럼이지만, filter_by에 활용하기 위해, 직접 default값을 명시
            employee_id=self.id,
            department_id=after_dept_id,
            employment_date=target_date,
            is_leader=as_leader,
        )

        # # 검증1. 변경할 부서가 이미 소속된 부서인 경우, 탈락
        # exists_after_emp_dept = EmployeeDepartment_.filter_by(
        #     **{k: v for k, v in after_emp_dept_data.items() if k not in ['is_leader', 'employee_date']}
        # ).exists()
        # if exists_after_emp_dept:
        #     return False, '이미 소속 중인 부서입니다.'
        #
        # # 검증2. as_leader로 부서변경을 원했는데, 이미 해당 after부서에 leader로 취업한 사람이 있는 경우, 탈락
        # if as_leader and EmployeeDepartment_.filter_by(
        #         **{k: v for k, v in after_emp_dept_data.items() if k not in ['employee_id', 'employee_date']}
        # ).exists():
        #     return False, '해당 부서에는 이미 팀장이 존재합니다.'
        #
        # # 검증3. 해당 after dept가 1인부서(부/장급부서)인데, 이미 1명의 active한 취임정보가 존재하는 경우
        # after_dept = Department_.get(after_dept_id)
        # if after_dept.type == DepartmentType.부장 and EmployeeDepartment_.filter_by(
        #         **{k: v for k, v in after_emp_dept_data.items() if k in ['dismissal_date', 'department_id']}
        # ).exists():
        #     return False, '해당 부서는 1인 부서로서, 이미 팀장이 존재합니다.'

        # auto_commit=True로 줄 경우, 무조건 session.merge의 결과를 활용해야한다. False일 경우, session에 떠있어서, main obj 수정시 자동 반영 된다?
        after_emp_dept, msg = EmployeeDepartment_.create(
            **after_emp_dept_data,
            auto_commit=False,  # 중간 rel obj 생성이라 commit은 뒤에서
        )

        if after_emp_dept:
            # result가 True라는 말은, after부서가 있어서 => 새로운 부서 취임정보 생성 완료
            # after_dept = Department_.filter_by(status=True, id=after_dept_id).first()
            # (3) current부서 O : 부서 변경 / current부서 X : 부서 추가
            # (4) 취임정보.create()에서 나온 성공1/실패N 메세지 중 [취임정보 생성 성공1]에 대해
            # => current O/X에 따라 부서변경/ 부서추가의 메세지 따로 반환
            # if current_dept_id:
            # current_dept = Department.get(current_dept_id)
            after_dept = Department_.get(after_dept_id)
            if current_dept_id:
                current_dept = Department_.get(current_dept_id)
                self.fill_reference(f"[{current_dept.name}→{after_dept.name}]부서 변경({format_date(target_date)})")
                message = f"부서 변경[{current_dept.name}→{after_dept.name}]을 성공하였습니다."

            else:
                self.fill_reference(f"[{after_dept.name}]부서 취임({format_date(target_date)})")
                message = f"부서 추가[{after_dept.name}]를 성공하였습니다."

            # updated_data.update(dict(employee_departments=[current_emp_dept, after_emp_dept]))
            # self.fill(employee_departments=after_emp_dept)
            #### 이미 기존에 append할 employee_departments가 있는 상황인데,
            #    list로 전달하면, 덮어쓰기 되어버리므로
            #    추가적으로 append할 때는 1개는 fill로 처리하자.
            self.fill(employee_departments=after_emp_dept)  # data['employee_departments']가 이미 있으므로 미리 fill -> append
            self.update(**data)

            return True, message

        ## save에 실패하면 message_after_save의 이유로 실패했다고 rollback하고  반환한다.
        # (5) 최종 저장여부를 결정하는 것은 부서변경여부다. .save()가 실패하여 result가 False로 올경우 rollback한다.
        else:
            # (2-2) 만약  after부서에 취임 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환 => route에서 그대로 취임실패 메세지를 flash
            # db.session.rollback()
            return False, msg

    # refactor 2 - cls.가 아닌 model obj에서 relation을 접근해서 처리할 땐,
    #              미리 load하지말고, session을 걸어놓고 처리하도도록
    #              1) 외부session받고, 2) 없으면 공용세션가져와서 사용하고 3) 조회할거면 외부주입으로 미리 add안해도 되고
    #              4) 추가 조회안하고, relation들 접근할거면 미리 add( self ) 하고
    #              5) 중간 CUD는 모두 auto_commit=False로 주고, 중간 R도 외부세션으로서 close안되게 하고
    #              6) 처리후 auto_commit여부에 따라 마지막은 auto_commit=auto_commit
    #                 True면 close/commit or False면 flush만?
    #
    def change_department(self, current_dept_id, after_dept_id, as_leader, target_date,
                          session: Session = None, auto_commit=True):
        """
        required(X) -> 공용세션 가져와 등록해놓고 relation 접근 or  공용세션으로 외부주입조회로 한번에 명시add + CUD
        """
        if not session:
            session = self.get_scoped_session()
            # self가 포함된 [외부주입 추가조회(not close, 변화반영상태)]없다면, self add하고 relation에 접근하게 한다
        session.add(self)

        data = dict()  # 한번에 fill = update의 인자로 주기 위해 모으기 용

        Role_ = self.__class__.user.mapper.class_.role.mapper.class_
        # print('session.identity_map.values()  >> ', session.identity_map.values())

        # 1. 승진여부 -> #Role 변화 : 부서변화(취임정보)의  [제거 or 변경/추가]와 무관하게 먼저 판단하기
        if self.is_demote(current_dept_id, after_dept_id, as_leader, session=session):
            # self.user.role = Role.filter_by(name='STAFF').first()
            # self.fill(role =Role.filter_by(name='STAFF').first())
            # print('session.identity_map.values() is_demote >> ', session.identity_map.values())
            data['role'] = Role_.filter_by(name='STAFF', session=session).first()

        elif self.is_promote(after_dept_id, as_leader, session=session):
            # print('session.identity_map.values() is_promote >> ', session.identity_map.values())
            # self.fill(role=Role.filter_by(name='CHIEFSTAFF').first())
            data['role'] = Role_.filter_by(name='CHIEFSTAFF', session=session).first()

        # print('session.identity_map.values() after promote >> ', session.identity_map.values())

        EmployeeDepartment_ = self.__class__.employee_departments.mapper.class_
        # 2. 선택된 [현재부서]의 [취임정보#EmployeeDepartment 해임 표시] 할 상황 -> [부서변경]or[부서제거]을 찾아 처리
        # (1) 현재부서가 선택되었다면, [부서추가]가 아닌 => [부서변경] OR [부서제거]상황  => 둘다 현재부서 [취임정보를 해임]시켜야한다.
        if current_dept_id:
            current_emp_dept = EmployeeDepartment_.filter_by(
                dismissal_date=None,
                employee_id=self.id,
                department_id=current_dept_id,
                session=session,
            ).first()
            # many relationship 객체인데, 1개를 수정해야하는 상황이면, fill/update에 list가 아닌 1개의 수정된 obj를 넣어주면
            # -> fill내부에서 append로 반영되고, 기존에 존재하던 것도 merge에 의해 자동 수정 반영된다.
            current_emp_dept.dismissal_date = target_date
            # self.fill(employee_departments=current_emp_dept)
            data['employee_departments'] = current_emp_dept

        # (2) 다음 취임정보#EmployeeDepartment를 생성하지 않는 상황 -> [부서 제거] 먼저 처리하기
        #    -> after 부서가 선택안되었다면 (current는 무조건 선택된) => [부서제거]의 상황으로 취임정보 생성 없이
        #       현재 취임정보 해임된 상태를 commit하고 끝낸다.
        #    (2-1) after부서가 없다면 -> [부서제거]로서 취임정보 생성 없이 바로 return해야한다.
        #       =>  after부서가 없는 [부서제거] 상태 ( current는 무조건 있음 )를 처리한다.
        #    (2-2) after부서가 있다면 -> [부서변경] or [부서추가]의 상황으로 취임정보 새로 생성되어야한ㄷ다
        Department_ = self.__class__.departments.mapper.class_
        # (2-1)
        if not after_dept_id:
            #### 부서제거
            # 부서제거시, 부서제거 reference입력하고 add
            # print('session.identity_map.values()  >> ', session.identity_map.values())

            current_dept = Department_.get(current_dept_id, session=session)

            #### new3) 1개의 level1 상위부서들 중 여러 부서에 취임가능한 상태이므로,
            #          마지막 1개 남은 부서의 해임일 때, 상위부서도 제거한다.
            # => 이미 위에서 current_dept가 있을 시, session에서 [일단 dismissal_date가 채워진 상황]이므로
            # => * active한 부서취임정보 검색시 1남을 때가 아닌 0개 남을때로 확인한다.
            current_all_depts = self.get_departments(session=session)
            # if len(current_all_depts) == 1:
            if len(current_all_depts) == 0:
                self.fill(upper_department=None)

            self.fill_reference(f"[{current_dept.name}]부서 해임({format_date(target_date)})")
            # result, msg = self.update()

            result, msg = self.update(**data, session=session, auto_commit=auto_commit)
            # print('session.identity_map.values()  >> ', session.identity_map.values())
            if result:
                return True, f"[{current_dept.name}]부서 제거를 성공하였습니다."
            else:
                return False, msg

        # (2-2) 다음 취임정보#EmployeeDepartment를 생성하는 상황(부서 변경 or 부서 추가)
        # (2-2-1) (after부서가 있는 상태): current O[부서변경] or current X [부서추가] -> after 부서 취임정보 생성
        #### 추가. .save()에 검증을 통합하지말고, .create()위에 일단 정의하기
        # 추가1. exists()는 create에 fill될 keyword를 가지고 미리 filter_by를 만든 뒤 호출한다.
        # 이 때, fill될 데이터는 filter_by + create 둘다에서 쓸 것이니 -> 미리 변수로 만들어놓는다.
        # result, message_after_save = after_emp_dept.save()
        after_emp_dept_data = dict(
            dismissal_date=None,  # default 칼럼이지만, filter_by에 활용하기 위해, 직접 default값을 명시
            employee_id=self.id,
            department_id=after_dept_id,
            employment_date=target_date,
            is_leader=as_leader,
        )

        # # 검증1. 변경할 부서가 이미 소속된 부서인 경우, 탈락
        # exists_after_emp_dept = EmployeeDepartment_.filter_by(
        #     **{k: v for k, v in after_emp_dept_data.items() if k not in ['is_leader', 'employee_date']}
        # ).exists()
        # if exists_after_emp_dept:
        #     return False, '이미 소속 중인 부서입니다.'
        #
        # # 검증2. as_leader로 부서변경을 원했는데, 이미 해당 after부서에 leader로 취업한 사람이 있는 경우, 탈락
        # if as_leader and EmployeeDepartment_.filter_by(
        #         **{k: v for k, v in after_emp_dept_data.items() if k not in ['employee_id', 'employee_date']}
        # ).exists():
        #     return False, '해당 부서에는 이미 팀장이 존재합니다.'
        #
        # # 검증3. 해당 after dept가 1인부서(부/장급부서)인데, 이미 1명의 active한 취임정보가 존재하는 경우
        # after_dept = Department_.get(after_dept_id)
        # if after_dept.type == DepartmentType.부장 and EmployeeDepartment_.filter_by(
        #         **{k: v for k, v in after_emp_dept_data.items() if k in ['dismissal_date', 'department_id']}
        # ).exists():
        #     return False, '해당 부서는 1인 부서로서, 이미 팀장이 존재합니다.'

        # auto_commit=True로 줄 경우, 무조건 session.merge의 결과를 활용해야한다. False일 경우, session에 떠있어서, main obj 수정시 자동 반영 된다?

        after_emp_dept, msg = EmployeeDepartment_.create(
            **after_emp_dept_data,
            session=session,
            auto_commit=False,  # 중간 rel obj 생성이라 commit은 뒤에서
        )

        if after_emp_dept:
            # result가 True라는 말은, after부서가 있어서 => 새로운 부서 취임정보 생성 완료
            # after_dept = Department_.filter_by(status=True, id=after_dept_id).first()
            # (3) current부서 O : 부서 변경 / current부서 X : 부서 추가
            # (4) 취임정보.create()에서 나온 성공1/실패N 메세지 중 [취임정보 생성 성공1]에 대해
            # => current O/X에 따라 부서변경/ 부서추가의 메세지 따로 반환
            # if current_dept_id:
            # current_dept = Department.get(current_dept_id)
            after_dept = Department_.get(after_dept_id, session=session)
            if current_dept_id:
                # 부서 변경
                current_dept = Department_.get(current_dept_id, session=session)

                #### new4) 부서변경은 이미 employee에 upper_department_id를 가진 상태이므로
                #          after의 상위부서와 비교한다.
                target_upper_dept = Department_.filter_by(path=after_dept.path[:6], session=session).first()
                current_all_departments = self.get_departments(session=session) # 현재부서는 빠진 상태
                # 현재 상위부서에 대한 부서가, 현재부서를 제외하고 남아있으면, 비교하여 검증한다
                if len(current_all_departments) > 1:
                    if self.upper_department_id != target_upper_dept.id:
                        session.close()
                        return False, '이미 다른 그룹에 소속된 직원입니다. Level 1의 부서들 중 1곳에서만 소속 가능합니다.'

                self.fill(upper_department=target_upper_dept)

                self.fill_reference(f"[{current_dept.name}→{after_dept.name}]부서 변경({format_date(target_date)})")
                message = f"부서 변경[{current_dept.name}→{after_dept.name}]을 성공하였습니다."

            else:
                # 부서 추가
                self.fill_reference(f"[{after_dept.name}]부서 취임({format_date(target_date)})")
                message = f"부서 추가[{after_dept.name}]를 성공하였습니다."

                #### new) after 부서의 상위부서(level=1)를 찾아 필드로 추가
                target_upper_dept = Department_.filter_by(path=after_dept.path[:6], session=session).first()

                #### new2) 상위부서 추가하기 전에, [현재 상위부서 존재]시 현재 상위부서와 타겟 상위부서를 비교해서, 다르면 여기서 탈락
                if self.upper_department_id and self.upper_department_id != target_upper_dept.id:
                    session.close()
                    return False, '이미 다른 그룹에 소속된 직원입니다. Level 1의 부서들 중 1곳에서만 소속 가능합니다.'

                self.fill(upper_department=target_upper_dept)

            # updated_data.update(dict(employee_departments=[current_emp_dept, after_emp_dept]))
            # self.fill(employee_departments=after_emp_dept)
            #### 이미 기존에 append할 employee_departments가 있는 상황인데,
            #    list로 전달하면, 덮어쓰기 되어버리므로
            #    추가적으로 append할 때는 1개는 fill로 처리하자.

            self.fill(employee_departments=after_emp_dept)  # data['employee_departments']가 이미 있으므로 미리 fill -> append
            self.update(**data, session=session, auto_commit=auto_commit)

            # session.commit()

            return True, message

        ## save에 실패하면 message_after_save의 이유로 실패했다고 rollback하고  반환한다.
        # (5) 최종 저장여부를 결정하는 것은 부서변경여부다. .save()가 실패하여 result가 False로 올경우 rollback한다.
        else:
            # (2-2) 만약  after부서에 취임 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환 => route에서 그대로 취임실패 메세지를 flash
            # db.session.rollback()
            return False, msg

    # #### with other entity
    # def is_promote(self, as_leader):
    #     #### (0) 팀장으로 가는 경우가 아니면 탈락이다.
    #     if not as_leader:
    #         return False
    #     #### (1) 팀장으로 가는데, 이미 팀장인 부서가 있다면 탈락이다.
    #
    #     #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & as_leader =True(최초 팀장으로 가면) => 승진
    #     #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
    #     depts_as_leader = self.get_my_departments(as_leader=True)
    #     return len(depts_as_leader) == 0

    #### refactor
    def is_promote(self, after_dept_id, as_leader, session=None):
        # 추가 -> (1) 이미 직위가 CHIEFSTAFF이상이면 탈락이다.
        if self.is_chiefstaff:
            return False

        # 추가 -> (2) 변경할 부서가 없으면 [부서제거]이므로 승진은 탈락이다.
        if not after_dept_id:
            return False
        # 추가 -> (3) after부서가 부/장급일 땐, as_leader가 부서원으로 왔어도 True로 미리 바꿔놔야한다.
        # after_dept: Department = Department.get_by_id(after_dept_id)
        after_dept: Department = Department.filter_by(status=True, id=after_dept_id, session=session)
        #            그 전에, active부서가 아니면 탈락이다.
        if not after_dept:
            return False

        if after_dept.type == DepartmentType.일인부서:
            as_leader = True

        # (4) (부서가있더라도) 팀장으로 가는 경우가 아니면 탈락이다.
        if not as_leader:
            return False

        # (5) 팀+장으로 가는데, 이미 팀장인 부서가 있다면 탈락이다. => 없어야 통과다
        #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & as_leader =True(최초 팀장으로 가면) => 승진
        #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
        # depts_as_leader = self.get_my_departments(as_leader=True)
        depts_as_leader = self.get_departments(as_leader=True, session=session)
        if depts_as_leader:
            return False

        return True

    #### refactor
    def is_demote(self, current_dept_id, after_dept_id, as_leader, session=None):
        # (0) EXECUTIVE 이상인 사람은, 강등에 해당하지 않는다.(이사급, 관리자가 STAFF되어버리는 참사 방지)
        # => 애초에 강등은, CHIESTAFF <-> STAFF 사이에서만 일어난다.
        if self.is_executive:
            return False

        # (1) 이미 CHIEFSTAFF 미만 직위의 직원(STAFF)면 강등 탈락이다.
        if not self.is_chiefstaff:
            return False

        # (2) 현재부서가 없다면 [부서 추가]의 상황으로 강등 탈락.
        if not current_dept_id:
            return False

        # (3) 현재부서가 있더라도, 조회시 active한 부서가 아니라면 강등 탈락이다.
        Department_ = self.__class__.departments.mapper.class_
        current_dept = Department_.filter_by(status=True, id=current_dept_id, session=session).first()
        if not current_dept:
            return False

        # (4) current외 다른 부서의 팀장으로 소속되어 있다면 강등 탈락이다.
        #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & as_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
        #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
        # other_depts_as_leader = self.get_my_departments(as_leader=True, except_dept_id=current_dept_id)
        other_depts_as_leader = self.get_departments(as_leader=True, exclude=current_dept_id, session=session)

        if other_depts_as_leader:
            return False

        # (5) (팀장인 또다른 부서X)현부서만 가지고 있더라도, 팀장이 아니라면 강등 탈락이다.
        is_current_dept_leader = self.is_leader_in(current_dept, session=session)
        if not is_current_dept_leader:
            return False

        # (6) after부서가 None이어도 되는데, 만약 있는데 부/장급 부서라면 as_leader True를 할당해야하며
        # -> as_leader 판단시 True면 [부서원or부서제거]의 상황이 아니므로 탈락이다.
        if after_dept_id:
            after_dept: Department = Department.get(after_dept_id, session=session)
            if after_dept.type == DepartmentType.일인부서:
                as_leader = True

        # (7) as_leader가 True면 CHIEFSTAFF이상으로 가는 거라 탈락이다.
        if as_leader:
            return False

        return True

    @classmethod
    def get_by_name_as_dict(cls, name):

        with DBConnectionHandler() as db:
            employees = db.session.scalars(
                select(Employee)
                .where(Employee.job_status != JobStatusType.퇴사)
                .where(Employee.name.like('%' + name + '%'))
                .order_by(Employee.join_date)
            ).all()

            # view에 보내기 전에 처리해주기
            results = []
            for emp in employees:
                emp_dict = emp.to_dict()
                ## 민감정보 삭제
                del emp_dict['birth']
                ## value -> enum(valuee)-> .name으로 변환
                # emp_dict['job_status'] = JobStatusType[emp_dict['job_status']].name
                #### job_status에는 이미 enum이 들어가 있다.
                emp_dict['job_status'] = emp_dict['job_status'].name

                results.append(emp_dict)

            return results

    # # refactor for to_dict - @hybrid_property leader in Department
    # def get_position(self, department):
    #     """
    #     부서를 주면, 취임정보를 필터링하여 직원의 position을 확인
    #     - 없으면 '공석'을 반환
    #
    #     s = db.get_session()
    #     d2 = Department.get(2, session=s)
    #
    #     e = d2.leader_employee
    #     e.get_position(d2)
    #     => '부서장'
    #
    #     ee = Employee.get(3, session=s)
    #     ee.get_position(d2)
    #     => '공석'
    #     """
    #     positions_in_department = map(lambda x: x.position,
    #                                   filter(lambda
    #                                              x: not x.dismissal_date and x.employee_id == self.id and x.department_id == department.id,
    #                                          self.employee_departments))
    #
    #     return next(positions_in_department, '공석')

    # refactor 2 for to_dict - @hybrid_property leader in Department
    #            + add_employee route에서 load 없이 position 획득
    def get_position(self, department, session: Session = None, close=True):
        """
        부서를 주면, 취임정보를 필터링하여 직원의 position을 확인
        - 없으면 '공석'을 반환
        d = Department.get(2)
        e = Employee.get(2)
        e.get_position(d)
        => '부서장'


        s = db.get_session()
        d2 = Department.get(2, session=s)

        e = d2.leader_employee
        e.get_position(d2)
        => '부서장'

        ee = Employee.get(3, session=s)
        ee.get_position(d2)
        => '공석'
        """
        if not session:
            session = self.get_scoped_session()
        session.add(self)

        positions_in_department = map(lambda x: x.position,
                                      filter(lambda
                                                 x: not x.dismissal_date and x.employee_id == self.id and x.department_id == department.id,
                                             self.employee_departments))

        if close:
            session.close()

        return next(positions_in_department, '공석')

    # refactor for to_dict
    @hybrid_property
    def avatar(self):
        return self.user.avatar

    @hybrid_property
    def email(self):
        return self.user.email

    # # refactor
    # @hybrid_method
    # def is_root_department(cls, root_dept, mapper=None):
    #     mapper = mapper or cls
    #     ED_ = mapper.employee_departments.mapper.class_
    #     Department_ = ED_.department.mapper.class_
    #
    #     # a = Department_.get_top_department_query.scalar_subquery()
    #     # level_expr = func.length(a.c.path) / Department_._N - 1
    #     # parent_query = select(a.c.id).select_from(a)
    #     # parent_ids = parent_query.scalar_subquery()
    #
    #     # filter_map.get('and_').update({'level': min_level_subq})
    #
    #     # ED_.department_id 가 2개인 순간 subquery 여러개 발생 -> 한 사람이 2개 부서일 경우, recusrvie_parent가 2개가 생겨서 에러 ->
    #     # return mapper.employee_departments.any(ED_.dismissal_date.is_(None) & ED_.department.has(Department_.recursive_parent(ED_.department_id)) == root_dept.id)
    #
    #     # return mapper.employee_departments.any(ED_.dismissal_date.is_(None) & \
    #     #     ED_.department.has(
    #     #             Department_.recursive_parent(ED_.department_id).as_scalar() == root_dept.id
    #     #     )
    #     # )
    #     return mapper.employee_departments.any(ED_.dismissal_date.is_(None) & \
    #         ED_.department.has(
    #                 Department_.recursive_parent(ED_.department_id).scalar_subquery() == root_dept.id
    #         )
    #     )
    #
    #     # query = select([ED_.id]). \
    #     #     where(ED_.dismissal_date.is_(None)). \
    #     #     join(Department_, and_(
    #     #     Department_.id == ED_.department_id,
    #     #     Department_.recursive_parent(Department_.id).correlate(Department_).scalar_subquery() == root_dept.id
    #     # ))
    #     #
    #     # return mapper.employee_departments.any(ED_.id == query.as_scalar())
    #
    #     # root_dept_ids_subq = Department_.recursive_parent(ED_.department_id).subquery()
    #     # return mapper.employee_departments.any(ED_.dismissal_date.is_(None) & # 나의 취임 기록 중
    #     # ED_.department.has(
    #     #     # 취임부서의 root Dept들 중에 [root_dept]가 포함되어있어야한다.
    #     #         root_dept.id == Department_.recursive_parent(Department_.id).scalar_subquery()
    #     # ) # 내 취임부서들 중, root부서들
    #     #     exists().where(
    #     #         and_(
    #     #             (ED_.department_id == Department_.id),
    #     #             root_dept.id == Department_.recursive_parent(
    #     #                 Department_.id).scalar_subquery()
    #     #         )
    #     #     )
    #     # ) # 내 취임부서들 중, root부서들
    #
    #     # return mapper.employee_departments.any(and_(
    #     #     ED_.dismissal_date.is_(None),
    #     #     # any_(
    #     #             and_(
    #     #                 (ED_.department_id == Department_.id),
    #     #                 any_(
    #     #                     Department_.id.in_(Department_.recursive_parent(Department_.id))
    #     #                 )
    #     #         )
    #     #     # )
    #     # ))

    @hybrid_method
    def is_below_to(cls, dept, mapper=None):
        """
        1번 부서에 속한 직원들 ( 1번 부서+자식부서들의 취임정보를 가지고 있는)

        Employee.filter_by(is_below_to=Department.get(1)).all()
        ----
        [<Employee 1>, <Employee 2>, <Employee 3>]

        """
        mapper = mapper or cls
        ED_ = mapper.employee_departments.mapper.class_

        return mapper.employee_departments.any(
            ED_.dismissal_date.is_(None) & ED_.is_below_to(dept)
        )

# #### with other entity
# def is_demote(self, as_leader, current_dept_id):
#
#     #### (0) 팀원으로 가는 경우가 아니면 애초에 탈락이다.
#     if as_leader:
#         return False
#     #### 강등에는 현재부서에 대해 팀장이라는 조건이 필요하다.
#     #### (1) 현재부서가 없다면 강등에서 먼저 탈락이다.
#     current_dept = Department.get_by_id(current_dept_id)
#     if not current_dept:
#         return False
#
#     #### (2) 현재부서 있더라도, 팀장이 아니면 탈락이다.
#     is_current_dept_leader = self.is_leader_in(Department.get_by_id(current_dept_id))
#     if not is_current_dept_leader:
#         return False
#
#     #### (3) 현재부서의 팀장인 상태에서, 제외하고 다른팀 팀장이면 강등에서 탈락이다.
#
#     #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & as_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
#     #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
#     other_depts_as_leader = self.get_my_departments(as_leader=True, except_dept_id=current_dept_id)
#
#     return len(other_depts_as_leader) == 0

#### 초대는 분야마다 초대하는 content(직원초대 -> Role 중 1개)가 다르기 때문에
#### => Type을 놓지않고, 필드를 다르게해서 새로 만들어야한다.
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

class EmployeeInvite(InviteBaseModel, CRUDMixin):
    ko_NAME = '직원초대'

    __tablename__ = 'employee_invites'

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    # user -> inviter / invitee
    inviter_id = Column(Integer, ForeignKey('users.id'))
    invitee_id = Column(Integer, ForeignKey('users.id'))
    # Many to Many에서 dynamic(필터까지 적용하여 실제query실행직전에 collection load)을 적용한
    # relationship을 *정의된 fk칼럼를 직접 지정하여 relationship 생성
    # 1) one to many : lazy='dynamic' + fk 2개이상시, foreign_keys(string:테이블명.fk명)으로 각각 지정
    # 2) many to one : lazy옵션 제거, uselist=False  + fk 2개이상시, foreign_keys( [fk칼럼]) 각각 지정
    # 3) 서로 relationship지정시 : 각각의 relationship을 string으로 back_populates=에 걸어주기
    inviter = relationship('User', foreign_keys=[inviter_id], uselist=False,
                           back_populates='inviters',  # 관계컬럼을 서로 정의할 경우, id copy시 자동으로 채우도록 지정
                           )
    invitee = relationship('User', foreign_keys=[invitee_id], uselist=False,
                           back_populates='invitees',  # 관계컬럼을 서로 정의할 경우, id copy시 자동으로 채우도록 지정
                           )

    # 직원초대에서는, 초대마다 바뀔 수 있는 role정보를 가져 따로 엔터티를 만들었다.
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    role = relationship('Role', foreign_keys=[role_id], uselist=False, back_populates='employee_invites')

    def __repr__(self):
        return '<EmployeeInvite %r=>%r >' % (self.inviter_id, self.invitee_id)

    @hybrid_method
    def is_sented_by(cls, user, mapper=None):
        """
        print(EmployeeInvite.is_sented_by( User.get(1)))
        ----
        EXISTS (SELECT 1
        FROM users, employee_invites
        WHERE users.id = employee_invites.inviter_id AND users.id = :id_1)
        """
        # 표현식은 aliased인 경우, filter_by에서 expression 작성시
        # method(value, mapper=mapper)로 작성된다.
        mapper = mapper or cls
        # has/any에 들어갈 User model class 는 import하지말고,
        # mapper.관계칼럼을 이용해서 꺼낸다.
        Inviter = mapper.inviter.property.mapper.class_  # User
        return mapper.inviter.has(Inviter.id == user.id)

    @hybrid_method
    def is_received_by(cls, user, mapper=None):
        """
        print(EmployeeInvite.is_sented_by( User.get(1)))
        ----
        EXISTS (SELECT 1
        FROM users, employee_invites
        WHERE users.id = employee_invites.invitee_id AND users.id = :id_1)
        """
        mapper = mapper or cls
        Invitee = mapper.invitee.property.mapper.class_  # User
        return mapper.invitee.has(Invitee.id == user.id)

    @classmethod
    def get_by_invitee(cls, user):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.invitee == user)
                # .where(cls.is_not_expired)
                .where(cls.is_valid)
            )
            # print(stmt)
            # SELECT employee_invites.is_answered, employee_invites.is_accepted, employee_invites.create_on, employee_invites.key, employee_invites.id, employee_invites.inviter_id, employee_invites.invitee_id, employee_invites.role_id
            # FROM employee_invites
            # WHERE :param_1 = employee_invites.invitee_id
            # AND employee_invites.create_on >= :create_on_1
            # AND employee_invites.is_answered = false

            invite_list = db.session.scalars(stmt).all()
        return invite_list


# BaseModel을 상속안하므로, 똑같이 session 삽입(임시)
# temp
EmployeeInvite.set_scoped_session(db.get_scoped_session())


# EmployeeInvite.set_engine(db.get_engine())

class EmployeeLeaveHistory(BaseModel, CRUDMixin):
    ko_NAME = '휴/복직기록'
    __tablename__ = 'employee_leave_histories'

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)

    employee_id = Column(Integer, ForeignKey('employees.id'),
                         nullable=True, # 임시 삭제용
                         index=True)

    #### 원래는 직원별, 부서별, 휴~복직 정보를 모으려고 했는데
    #### => 어차피 내가 속한 부서들 다 가져와서 한번에 처리하므로
    #### => 아예 부서정보를 빼고 1번만 생성되도록 한다면, 나중에 중복제거를 안해도 된다.
    #### => 그렇다면, 취임정보(employee_departments)테이블과 무관하게 생성해도 된다.
    #### => 직원이 휴직하면 소속부서 전체가 휴직정보를 남기지만,
    ####    복직시 history는 직원단위로 1개만 남기게 한다?!
    # department_id = Column(Integer, ForeignKey('employee_departments.department_id'),
    #                        nullable=False, index=True)
    #### 부서정보가 빠지면, EmpDept가 아닌 Emp와 1:M의 관계로서, 반대로 관계객체도 만들 수 있다?!
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="employee_leave_histories")

    leave_date = Column(Date, nullable=False)
    reinstatement_date = Column(Date, nullable=False)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[직원id={self.employee_id!r}," \
                    f" 휴직={self.leave_date!r} ~ 복직={self.reinstatement_date!r}]"
        return info

    # BaseModel을 상속안하므로, 똑같이 session 삽입(임시)
    # temp
    # EmployeeLeaveHistory.set_scoped_session(db.get_scoped_session())
    # EmployeeLeaveHistory.set_engine(db.get_engine())
