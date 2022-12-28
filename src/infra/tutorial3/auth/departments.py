import datetime
import enum
import uuid

from dateutil.relativedelta import relativedelta
from flask import url_for, g
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, case, and_, exists, func, DateTime, \
    BigInteger, update, Date, ForeignKeyConstraint, Text, or_
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, backref, with_parent, aliased
from werkzeug.security import generate_password_hash, check_password_hash

from src.config import project_config
from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3.auth import Role, Roles
from src.infra.tutorial3.auth import User, Employee
from src.infra.tutorial3.common.base import BaseModel, InviteBaseModel
from src.infra.tutorial3.common.int_enum import IntEnum


class DepartmentType(enum.IntEnum):
    부장 = 0  # 부서명 ex> 병원장, 진료부장, 간호부 => 끝에 장이 없으면 [부서명 + 장]
    실 = 1  # 실원, 실장 ex> 탕제실, 홍보실, 기획관리실, 정보전산실,
    팀 = 2  # 팀원, 팀장 ex> 총무팀
    과 = 3  # 팀원, 과장 ex> 원무과, 행정과

    치료실 = 4  # 치료사, 실장
    원장단 = 5  # 원장, 대표원장
    진료과 = 6  # 원장, 과장
    의료센터 = 7  # 원장, 센터장

    연구소 = 8  # 연구원, 연구원장
    센터 = 9  # 센터원, 센터장

    위원회 = 10  # 위원, 위원장

    # form을 위한 choices에는, 선택권한을 안준다? -> 0을 value로 잡아서 제외시킴
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]

    def find_position(self, is_leader, dep_name):
        # 1) 부/장부서 => ~장, ~부장
        if self == DepartmentType.부장:
            if is_leader:
                return dep_name + ('' if dep_name.endswith('장') else '장')  # 장으로 끝나지 않는 간호부 => 간호부 + 장이 되게 한다
            else:
                raise ValueError('부/장 부서는 팀원 없이, 리더 1명만 입력해야합니다.')
        # 2) 실 => 실장 - 실원
        elif self == DepartmentType.실:
            return '실장' if is_leader else '실원'
        # 3) 팀 => 팀장 - 실원
        elif self == DepartmentType.팀:
            return '팀장' if is_leader else '팀원'
        # 4) 과 => 과장 - 팀원
        elif self == DepartmentType.과:
            return '과장' if is_leader else '팀원'
        # 5) 치료실 => 실장 - 치료사
        elif self == DepartmentType.치료실:
            return '실장' if is_leader else '치료사'
        # 6) 원장단 => 대표원장 - 원장
        elif self == DepartmentType.원장단:
            return '대표원장' if is_leader else '원장'
        # 7) 진료과 => 과장 - 원장
        elif self == DepartmentType.진료과:
            return '과장' if is_leader else '원장'
        # 8) 의료센터 => 센터장 - 원장
        elif self == DepartmentType.의료센터:
            return '센터장' if is_leader else '원장'
        # 9) 연구소 => 연구소장 - 연구원
        elif self == DepartmentType.연구소:
            return '연구소장' if is_leader else '연구원'
        # 10) 센터 => 센터장 - 센터원
        elif self == DepartmentType.센터:
            return '센터장' if is_leader else '센터원'
        # 11) 위원회 => 위원장 - 위원
        elif self == DepartmentType.위원:
            return '위원장' if is_leader else '위원'


class Department(BaseModel):
    _N = 3

    __tablename__ = 'departments'

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    # name = Column(String(50), nullable=False, comment="부서 이름")
    # 9. + index, unique까지
    name = Column(String(50), nullable=False, index=True, unique=True, comment="부서 이름")

    # parent_id = Column(Integer, comment="상위 부서 id", nullable=True)  # 1 # 2 # 8 + nullable=True
    parent_id = Column(Integer, ForeignKey('departments.id'), comment="상위 부서 id", nullable=True)  # 5 # parent_id에 fk입히기
    # 5 # one인 parent의 backref에게는 subquery를 줘서, .parent는 바로 얻을 수 있게 하기?!
    children = relationship('Department', backref=backref(
        'parent', remote_side=[id], lazy='subquery',
        cascade='all',  # 7
    ))
    # 8 # children + joined backref parent 대신, parent를 정의해줄 수 도 있다.
    # parent = db.relationship('Department', remote_side=[id],  backref="subdepartment")

    # 7 # cascade='all' 을 줘서, 삭제시 자식들도 다 같이 삭제되게 한다?!
    #  parent_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    #  children = db.relationship(
    #         'Department',
    #         cascade='all',
    #         backref=db.backref('parent', remote_side='Department.id'))

    # 1.
    # leader = Column(String(50), comment="부서 부장")
    # 8. leader를 user에서 가져와서, 특정user에 의해 부서가 신설된다?
    #### User-Department는 직원들 부서정보고.. 여긴 따로 팀생성시 팀장정보라서.. 따로 관리되는지 확인하기
    # => my) 신설은 admin이 할 수 있지만, 팀장을 지정해놓기

    #### user를 employee로 바꾸기
    # leader_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    # => 대박) 팀장입장에서 Many인 Department관계의 fk를, Many속에 정의한 One의 fk로 []안에 직접 지정할 수 있다.
    #    one에 대한 관계속성을 joined로 하여 부서.leader(User객체)를 바로 뽑아볼 수 있게 한다
    # #### nullable한 관계필드를 joined를 주면, 없는데도 가져와서 None.필드를 호출하여 에러가 난다
    # leader = relationship("Employee", backref="managed_department", foreign_keys=[leader_id])  # lazy='joined')
    #### => leader정보를 따로 Department에 배정하지말고, EmployeeDepartment에 is_leader를 개설해서 그쪽에서 처리하게 한다.

    status = Column(Boolean, comment='부서 사용 상태(0 미사용, 1사용)', default=1)
    #### sort는 save시 path처럼 동적으로 채우기
    # path -> level 처럼, save시 동적으로 현재레벨 조회해서 자동으로 맨 마지막 +1로 채워야할 듯?
    sort = Column(Integer, comment="부서 순서", nullable=True)  # 1 #  .order_by(Department.sort).all()

    # 2. 부서 생성시 조건에 따라 -> 사람이 지정한다 (원랜 계산으로도 나온다?)
    #### level, code, root를  => 동적생성 path로 바꾸기
    # level = Column(Integer, nullable=False)  # 2 # 3

    # 4. root여부 -> code(path)를 구성
    # if parent_id 없으면 -> root = True
    # if root: 현재까지 root부서의 갯수 + '' 문자열 -> code생성
    # else: parent_id로 부모부서객체 -> 부모부서의 자식들현재갯수  + '부모code' -> code 생성
    # code생성: 부모코드('' or 생성된코드) + 같은level의 현재까지 존재갯수( 부모의 자식들 or root라면 root갯수)를 01부터 2자리로 유지
    # -> code는 정렬시 전체 기준에 들어간다 => sort가 있으면 무쓸모?? sort가 바뀌면 sort기준으로 가야하므로..
    # code = Column(String(24))
    # root = Column(Boolean, default=False)  # parent_id가 None이면 root에 True넣어주고, 그외는 False로 기본 생성
    # menu
    path = Column(Text, index=True, nullable=True)  # 동적으로 채울거라 nullabe=True로 일단 주고, add후 다른데이터를 보고 채운다다

    #### EmployeeDepartment에 position을 남기기 위한, Type
    type = Column(IntEnum(DepartmentType), default=DepartmentType.팀, nullable=False, index=True)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}," \
                    f" title={self.name!r}," \
                    f" parent_id={self.parent_id!r}]" \
            # f" level={self.level!r}]" # path를 채우기 전에 출력했더니 level써서 에러가 남.
        return info

    def exists(self):
        with DBConnectionHandler() as db:
            department = db.session.scalars(select(Department).where(Department.name == self.name)).first()
            return department  # 객체 or None

    def save(self):
        department_or_none = self.exists()
        if department_or_none:
            print(f"{self.name}는 이미 존재하는 부서입니다.")
            return department_or_none

        with DBConnectionHandler() as db:
            db.session.add(self)
            #### 더이상 path구성에 id를 사용하지 않으므로, flush()나 commit()을 미리 할 필요없이 => add만 해도, 자신이 포함된다.
            # db.session.flush()

            # 부모가 있으면 부모의 부모의 path에 + 생성아이디로 path를 만들어, 변경전 최초 순서?
            # my) 현재 동급레벨의 갯수로 -> sort를 동적으로 채우고, id로 path를 채우는 대신, sort번호로 path를 채우면 될 것 같다?
            # my) # 6 부모가 있으면 where에 with_parent에 올려, 갯수를 센다
            if self.parent:
                sort_count = db.session.scalar(
                    (
                        select(func.count(Department.id))
                        .select_from(Department)
                        .where(with_parent(self.parent, Department.children))
                        # .where(with_parent(self.parent)) # TypeError: with_parent() missing 1 required positional argument: 'prop'
                    )
                )
                # print(stmt)
                # SELECT count(departments.id) AS count_1
                # FROM departments
                # WHERE :param_1 = departments.parent_id
                # print(f'부모를 가졌으며, 해당부모의 자식수는 flush한 나를 포함하여 {sort_count}개로 sort가 정해집니다', sep=' / ')

            else:
                #### path를 채우기도 전에 먼저 level을 쓸 순 없다.
                #### => 최상위를 가려내기 위해, sort -> path -> level을 채우기 전에, 먼저 level로 필터링 해야한다
                # sort_count = db.session.scalar(select(func.count(Department.id)).where(Department.level == 0))
                #### => 사실상 최상위 필터링은 parent_id, parent = None으로 찾아야한다.
                sort_count = db.session.scalar(select(func.count(Department.id)).where(Department.parent_id.is_(None)))
                # print(f'부모가 없어 level==0인 부서는 flush한 나를 포함하여 {sort_count}개로서 sort가 정해집니다', sep=' / ')
            self.sort = sort_count

            prefix = self.parent.path if self.parent else ''
            self.path = prefix + f"{self.sort:0{self._N}d}"

            db.session.commit()

            return self

    @hybrid_property
    def level(self):
        return len(self.path) // self._N - 1

    @level.expression
    def level(cls):
        # 0 division 가능성이 있으면 = (cls.path / case([(cls._N == 0, null())], else_=cls.colC), /는 지원되나 //는 지원안됨. func.round()써던지 해야할 듯.?
        return func.length(cls.path) / cls._N - 1


# 2.
class EmployeeDepartment(BaseModel):
    __tablename__ = 'employee_departments'
    # __table_args__ = (ForeignKeyConstraint(['user_id'], ['users.id'], name='users_tag_maps_department_id_fk'),)

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)

    # user_id = Column(Integer, nullable=False)
    # department_id = Column(Integer, nullable=True) # 부서는 nullable일 수 있다.?! 유저마다 유저부서 정보가 생기는데, 부서는 없을 수 있음? => 유저-부서정보라서 꼭 있어야한다. 여기선 join할 일이 없어서 안쓰는 듯.
    # 5.에서는 user-contract관계에서 contract.id의 FK를 index=True
    # employee_id = Column(Integer, nullable=False, index=True)
    # department_id = Column(Integer, nullable=False, index=True)
    # pickupapi # 다대다+정보도 관계테이블처럼 fk로 주기
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False, index=True)

    # new
    employee = relationship("Employee", backref="employee_department", foreign_keys=[employee_id],
                            # lazy='joined', # fk가 nullable하지 않으므로, joined를 줘도 된다.
                            )

    department = relationship("Department", backref="employee_department", foreign_keys=[department_id],
                              # lazy='joined', # fk가 nullable하지 않으므로, joined를 줘도 된다.
                              )

    # 2. 고용일과 퇴직일은 없을 수 있다?! (퇴직일만 nullable=True인듯)
    employment_date = Column(Date, nullable=False, comment='입사일과 다른, 부임일')
    dismissal_date = Column(Date, nullable=True)

    # new 입사당시에 position을 Department.type에 따라 동적입력 -> 칼럼 nullable=True 필수 + .save()로 저장
    position = Column(String(50), nullable=True, comment="부서Type에 따른 직무")
    # new 입사당시에 is_leader인지를 받아서, 그것에 따른 position이 입력되게 해준다. => Department의 leader는 삭제하자.
    #### => 팀장, 팀원 모두가 부임정보에 나와있게 된다.
    is_leader = Column(Boolean, nullable=False, default=False)

    #### (1) 같은부서에 대해서만 존재 여부 확인 -> 다른 부서에는 또 부임할 수 있다.
    def exists_same_department(self):
        with DBConnectionHandler() as db:
            # Employee는 자신의 필수정보(name)으로만 중복검사햇으나
            # 여기서는 fk_id or fk관계객체를 이용해서 검사해야한다? => 둘중에 뭐가 들어올지 모르면서, add/flush하진 않을 것 같은데..
            #### 여기선 flush로 db에 갖다올 일이 없으니, 해당객체의 입력상황을 if 관계객체 else fk_id 로 나눠서 id를 뽑아서 검사하자
            dep_id = self.department.id if self.department else self.department_id
            emp_id = self.employee.id if self.employee else self.employee_id

            emp_dep = db.session.scalars(
                select(EmployeeDepartment) \
                    .where(EmployeeDepartment.dismissal_date.is_(None))  # 아직 끝나지 않은 부임정보에 대해
                    .where(EmployeeDepartment.employee_id == emp_id)  # 해당직원의 정보가
                    .where(EmployeeDepartment.department_id == dep_id)  # 해당부서에 부임정보가 이미 존재하는지
            ).first()

            return emp_dep  # 객체 or None

    #### (2) is_leader로 지원했는데, 팀장이 이미 차 있는지 여부
    def exists_already_leader(self):
        with DBConnectionHandler() as db:
            dep_id = self.department.id if self.department else self.department_id
            already_leader = db.session.scalars(
                select(EmployeeDepartment) \
                    .where(EmployeeDepartment.dismissal_date.is_(None))  # 퇴직정보가 아닌 것 중
                    .where(EmployeeDepartment.department_id == dep_id)  # 해당부서 정보 중
                    .where(EmployeeDepartment.is_leader == True)  # 팀장이 이미 있는지
            ).first()

            return already_leader

    #### (3) 부/장급 부서는 only 1명만 등록가능하고, is_leader가 체크안되어있더라도, 체크해줘야한다
    def is_full_in_one_person_department(self):
        with DBConnectionHandler() as db:
            if self.department:
                dep_type = self.department.type
            else:
                # department_id로 입력된 경우
                dep_type = db.session.scalars(
                    select(Department)
                    .where(Department.id == self.department_id)
                ).first().type

            if dep_type != DepartmentType.부장:
                return False
            # (부/장급 부서인 경우) => 미리 데이터가 나오면 탈락
            is_full = db.session.scalars(
                select(EmployeeDepartment)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(
                    EmployeeDepartment.department_id == (self.department.id if self.department else self.department_id))
            ).first()
            return is_full

    def save(self):
        #### (1) 퇴직정보제외하고 & 해당 지원부서에 대해서 & 해당직원이 이미 존재하는지 여부 확인 -> 다른 부서에는 또 부임할 수 있다.
        emp_dep_or_none = self.exists_same_department()
        if emp_dep_or_none:
            print('이미 부임된 부서입니다. >>> ')
            return None

        #### (2) is_leader로 지원했는데, 팀장이 이미 차 있는지 여부 (exits호출 조건으로서 if is_leadear가 True여야한다.)
        if self.is_leader and self.exists_already_leader():
            print('해당부서에 이미 부서장이 존재합니다.')
            return None

        #### (3) 부/장급 부서는 only 1명만 등록가능하고, is_leader가 체크안되어있더라도, 체크해줘야한다
        if self.is_full_in_one_person_department():
            print('1명만 부임가능한 부서로서 이미 할당된 부/장급 부서입니다.')
            return None

        with DBConnectionHandler() as db:
            #### flush나 commit을 하지 않으면 => fk_id 입력 vs fk관계객체입력이 따로 논다.
            #### => 한번 갔다오면, 관계객체 입력 <-> fk_id 입력이 동일시되며, fk_id입력으로도 내부에서 관계객체를 쓸 수 있게 된다.
            #### => 즉 외부에서 department_id=로 입력해도, 내부에서 self.department객체를 쓸 수 있게 된다.
            db.session.add(self)
            db.session.flush()  # fk_id 입력과 fk관계객체입력 둘중에 뭘 해도 관계객체를 사용할 수 있게 DB한번 갔다오기

            self.position = self.department.type.find_position(is_leader=self.is_leader,
                                                               dep_name=self.department.name)  # joined를 삭제하면 fk만 넣어줘도 이게 돌아갈까?

            #### 한번만 session에 add해놓으면, 또 add할 필요는 없다.
            # db.session.add(self)
            db.session.commit()

        return self

# 3.
# users_and_departments = db.Table(
#     'users_and_departments',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
#     db.Column('dep_id', db.Integer, db.ForeignKey('department_hierarchies.id'))
# )

# 3. class User
# departments = db.relationship('DepartmentHierarchy', secondary=users_and_departments,
#                                   backref=db.backref('users', lazy='dynamic'), lazy='dynamic')


# 5.
# contract_user_association_table = Table(
#     'contract_user_association', Model.metadata,
#     Column('user_id', db.Integer, db.ForeignKey('users.id'), index=True),
#     Column('contract_id', db.Integer, db.ForeignKey('contract.id'), index=True),

# 5. class User
# class User(UserMixin, SurrogatePK, Model):
# 	#...
#     department_id = ReferenceCol('department', ondelete='SET NULL', nullable=True)
#     department = db.relationship(
#         'Department', backref=backref('users', lazy='dynamic'),
#         foreign_keys=department_id, primaryjoin='User.department_id==Department.id'
#     )
#
#     @classmethod
#     def department_user_factory(cls, department_id):
#         return cls.query.filter(
#             cls.department_id == department_id,
#             db.func.lower(Department.name) != 'equal opportunity review commission'
#         )

# 6.
# '''
# 部门层级关系
# '''
# class RelDepartment(BaseModel, db.Model):
#     parent_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
#     parent_department = db.relationship('BizDepartment', foreign_keys=[parent_department_id],
#                                       back_populates='parent_department', lazy='joined')    # 父部门
#     child_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
#     child_department = db.relationship('BizDepartment', foreign_keys=[child_department_id],
#                                       back_populates='child_department', lazy='joined')       # 子部门

# 6. class Department
# class BizDepartment(BaseModel, db.Model):
#     code = db.Column(db.String(32))                                         # 部门代码
#     name = db.Column(db.Text)                                               # 部门名称
#     company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))  # 所属法人ID
#     company = db.relationship('BizCompany', back_populates='departments')   # 所属法人
#     employees = db.relationship('BizEmployee', back_populates='department')
#
#     parent_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.parent_department_id], back_populates='parent_department', lazy='dynamic', cascade='all')  # 父部门
#     child_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.child_department_id], back_populates='child_department', lazy='dynamic', cascade='all')     # 子部门

# 6. class User
# class BizEmployee(BaseModel, db.Model):
#     code = db.Column(db.String(32))     # 职号
#     name = db.Column(db.String(128))    # 姓名
#     email = db.Column(db.String(128))   # 邮箱
#     phone = db.Column(db.String(20))    # 电话
#     company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))          # 所属法人ID
#     company = db.relationship('BizCompany', back_populates='employees')             # 所属法人
#     department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))    # 所属部门ID
#     department = db.relationship('BizDepartment', back_populates='employees')       # 所属部门


# 8. class User
# class User(db.Model, AuthUser, Mixin):
#     '''
#     при добавлении полей не забыть их добавить в
#     application/models/serializers/users.py для корректной валидации данных
#     '''
#
#     __tablename__ = 'users'
#
#     (
#         STATUS_ACTIVE,
#         STATUS_DELETED,
#     ) = range(2)
#
#     STATUSES = [(STATUS_ACTIVE, 'Active'), (STATUS_DELETED, 'Deleted')]
#
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String)  # TODO Add constraint on length; can't be nullable in future
#     full_name = db.Column(db.String(64))
#     login = db.Column(db.String(64), unique=True)
#     status = db.Column(db.Integer, default=STATUS_ACTIVE)
#     mobile_phone = db.Column(db.String, nullable=True)  # TODO Add constraint on length and format
#     inner_phone = db.Column(db.String, nullable=True)   # TODO Add constraint on length and format
#     birth_date = db.Column(db.DateTime, nullable=True)  # TODO Add default value
#     skype = db.Column(db.String(64), nullable=True)
#
#     department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
#     # department.users == works (만든 팀장장user를 제외
#     department = db.relationship("Department", backref="users", foreign_keys=[department_id])

#     position = db.Column(db.String(255))
#     photo_id = db.Column(db.Integer, db.ForeignKey('file.id'))
#     is_admin = db.Column(db.Boolean, default=False)
#     news_notification = db.Column(db.Boolean, default=False)
#     reg_date = db.Column(db.DateTime, default=datetime.now)
#     permissions = db.relationship("Permission", secondary=user_permission_associate, backref="users", lazy='dynamic')
#     roles = db.relationship("Role", secondary=user_role_associate, backref="users", lazy='dynamic')
#     photo = db.relationship("File", lazy="joined")
