import datetime
import enum
import uuid

from dateutil.relativedelta import relativedelta
from flask import url_for, g
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, case, and_, exists, func, DateTime, \
    BigInteger, update, Date, ForeignKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash

from src.config import project_config
from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3.common.base import BaseModel, InviteBaseModel
from src.infra.tutorial3.common.int_enum import IntEnum


class Department(BaseModel):
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
    leader_id = Column(Integer, ForeignKey('employees.id'))
    # => 대박) 팀장입장에서 Many인 Department관계의 fk를, Many속에 정의한 One의 fk로 []안에 직접 지정할 수 있다.
    #    one에 대한 관계속성을 joined로 하여 부서.leader(User객체)를 바로 뽑아볼 수 있게 한다
    leader = relationship("Employee", backref="managed_department", foreign_keys=[leader_id], lazy='joined')

    status = Column(Boolean, comment='부서 사용 상태(0 미사용, 1사용)', default = 1)
    #### sort는 save시 path처럼 동적으로 채우기
    # path -> level 처럼, save시 동적으로 현재레벨 조회해서 자동으로 맨 마지막 +1로 채워야할 듯?
    sort = Column(Integer, comment="부서 순서")  # 1 #  .order_by(Department.sort).all()

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



# 2.
class EmployeeDepartment(BaseModel):
    __tablename__ = 'user_departments'
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

    # 2. 고용일과 퇴직일은 없을 수 있다?! (퇴직일만 nullable=True인듯)
    employment_date = Column(Date, nullable=True)
    dismissal_date = Column(Date, nullable=True)

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
