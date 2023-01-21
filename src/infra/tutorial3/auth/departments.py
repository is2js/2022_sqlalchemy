import enum

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, func, BigInteger, Date, Text, distinct
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref, with_parent

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3.common.base import BaseModel
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

    # #### front에서 고르기 위해, 부서종류별로 내려주는 메서드
    # def get_positions(self, dep_name):
    #     # 1) 부/장부서 => ~장, ~부장
    #     if self == DepartmentType.부장:
    #         return dep_name + ('' if dep_name.endswith('장') else '장')  # 장으로 끝나지 않는 간호부 => 간호부 + 장이 되게 한다
    #     # 2) 실 => 실장 - 실원
    #     elif self == DepartmentType.실:
    #         return '실장', '실원'
    #     # 3) 팀 => 팀장 - 팀원
    #     elif self == DepartmentType.팀:
    #         return '팀장', '팀원'
    #     # 4) 과 => 과장 - 팀원
    #     elif self == DepartmentType.과:
    #         return '과장', '팀원'
    #     # 5) 치료실 => 실장 - 치료사
    #     elif self == DepartmentType.치료실:
    #         return '실장', '치료사'
    #     # 6) 원장단 => 대표원장 - 원장
    #     elif self == DepartmentType.원장단:
    #         return '대표원장', '원장'
    #     # 7) 진료과 => 과장 - 원장
    #     elif self == DepartmentType.진료과:
    #         return '과장', '원장'
    #     # 8) 의료센터 => 센터장 - 원장
    #     elif self == DepartmentType.의료센터:
    #         return '센터장', '원장'
    #     # 9) 연구소 => 연구소장 - 연구원
    #     elif self == DepartmentType.연구소:
    #         return '연구소장', '연구원'
    #     # 10) 센터 => 센터장 - 센터원
    #     elif self == DepartmentType.센터:
    #         return '센터장', '센터원'
    #     # 11) 위원회 => 위원장 - 위원
    #     elif self == DepartmentType.위원:
    #         return '위원장', '위원'


class Department(BaseModel):
    _N = 3

    __tablename__ = 'departments'
    # __table_args__ = {'extend_existing': True}

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
    ), order_by='Department.path')
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
    path = Column(Text, index=True,
                  nullable=True)  # 동적으로 채울거라 nullabe=True로 일단 주고, add후 다른데이터를 보고 채운다다 => 자식검색시 path.like(자신apth)로 하니 index 필수

    #### EmployeeDepartment에 position을 남기기 위한, Type
    type = Column(IntEnum(DepartmentType), default=DepartmentType.팀, nullable=False, index=True)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"(id={self.id!r}," \
                    f" title={self.name!r}," \
                    f" parent_id={self.parent_id!r}," \
                    f" sort={self.sort!r}," \
                    f" path={self.path!r})" \
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
                sort_count = db.session.scalar(
                    select(func.count(Department.id)).where(Department.parent_id.is_(None))
                )
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

    @classmethod
    def get_by_name(cls, name: str):
        with DBConnectionHandler() as db:
            dep = db.session.scalars(
                select(cls)
                .where(cls.status == 1)
                .where(cls.name == name)
            ).first()
            return dep

    @classmethod
    def get_by_id(cls, id: int):
        with DBConnectionHandler() as db:
            dep = db.session.scalars(
                select(cls)
                .where(cls.status == 1)
                .where(cls.id == id)
            ).first()
            return dep

    @classmethod
    def get_all(cls):
        with DBConnectionHandler() as db:
            depts = db.session.scalars(
                select(cls)
                .where(cls.status == 1)
                .order_by(cls.path)
            ).all()
            return depts

    @classmethod
    def get_all_tuple_list(cls):
        with DBConnectionHandler() as db:
            depts = db.session.scalars(
                select(cls)
                .where(cls.status == 1)
                .order_by(cls.path)
            ).all()
            return [(x.id, x.name) for x in depts]

    @classmethod
    def get_all_infos(cls):
        with DBConnectionHandler() as db:
            depts = db.session.scalars(
                select(cls)
                .where(cls.status == 1)
                .order_by(cls.path)
            ).all()
            return [{'id': x.id, 'name': x.name} for x in depts]

    @classmethod
    def change_sort_by_id(cls, id_a, id_b):
        with DBConnectionHandler() as db:
            dep_a = db.session.get(cls, id_a)  # get으로 찾앗으면 이미 add된 상태라서 commit만 하면 바뀐다? => execute때문에 자동 커밋 되는 듯.
            dep_b = db.session.get(cls, id_b)

            #### 같은 레벨 내의 sort 교환이어햐만 한다 => 아닐시 에러 추가
            if dep_a.leve != dep_b.level:
                raise ValueError('같은 level의 부서만 순서변경이 가능합니다.')

            dep_a.sort, dep_b.sort = dep_b.sort, dep_a.sort

            # path는 기존path로 필터링해야하니 변수로 만들어놓는다.
            a_prefix = dep_a.parent.path if dep_a.parent else ''  # 부모는 안바뀌고
            new_a_path = a_prefix + f"{dep_a.sort:0{cls._N}d}"  # 자신은 바뀐sort로 바뀐apth를 만든다

            b_prefix = dep_b.parent.path if dep_b.parent else ''
            new_b_path = b_prefix + f"{dep_b.sort:0{cls._N}d}"

            #### 각각 update를 떼리면, 뒤에것의 바뀐path로 검색시  바뀐a들이 걸려버린다.
            #### => 업뎃하기 전에 둘다 미리 select해놓고, 이후 update한다.
            a_and_subs = db.session.scalars(select(cls).where(cls.path.like(dep_a.path + '%'))).all()
            b_and_subs = db.session.scalars(select(cls).where(cls.path.like(dep_b.path + '%'))).all()

            for a_or_sub in a_and_subs:
                a_or_sub.path = new_a_path + a_or_sub.path[len(new_a_path):]

            for b_or_sub in b_and_subs:
                b_or_sub.path = new_b_path + b_or_sub.path[len(new_b_path):]

            db.session.commit()

    def get_children(self):
        with DBConnectionHandler() as db:
            stmt = (
                select(Department)
                .where(with_parent(self, Department.children))
                # 활성화된 메뉴만
                .where(Department.status == 1)
                # 나의 자식들이 나오는데, 같은 level의 부서들이 나오므로 -> 정렬은 path순으로 하자.
                .order_by(Department.path)
            )
            return db.session.scalars(stmt).all()

    def get_self_and_children_id_list(self):
        # (3-1) 재귀를 돌며 누적시킬 것을 현재부터 뽑아낸다? => 첫 입력인자에 계속 누적시킬 거면, return없이 list에 그대로 append만 해주면 된다.
        result = [self.id]
        # (3-1) 현재(부모)부서에서 자식들을 뽑아 순회시키며, id만 뽑아놓고, 이제 자신이 부모가 된다.
        # => 자신처리+중간누적을 반환하는 메서드라면, 재귀호출후 반환값을 부모의 누적자료구조에 추가누적해준다.
        # for child in parent.children:
        for child in self.get_children():
            result += child.get_self_and_children_id_list()
        return result

    def get_self_and_children_dept_info_tuple_list(self):
        # (3-1) 재귀를 돌며 누적시킬 것을 현재부터 뽑아낸다? => 첫 입력인자에 계속 누적시킬 거면, return없이 list에 그대로 append만 해주면 된다.
        result = [(self.id, self.name, self.level)]
        # (3-1) 현재(부모)부서에서 자식들을 뽑아 순회시키며, id만 뽑아놓고, 이제 자신이 부모가 된다.
        # => 자신처리+중간누적을 반환하는 메서드라면, 재귀호출후 반환값을 부모의 누적자료구조에 추가누적해준다.
        # for child in parent.children:
        for child in self.get_children():
            result += child.get_self_and_children_dept_info_tuple_list()
        return result

    def get_selectable_departments_for_edit(self):
        departments = Department.get_all()
        selectable_parent_departments = [(x.id, x.name) for x in departments if
                                         x.id not in self.get_self_and_children_id_list()]
        return selectable_parent_departments

    def get_selectable_departments(self):
        departments = Department.get_all()
        selectable_parent_departments = [{'id': x.id, 'name': x.name} for x in departments if
                                         x.id not in self.get_self_and_children_id_list()]
        return selectable_parent_departments

    #### BaseModel의 to_dict는 inspect(self) 를 칠 때, 관계필드까지 다 조사하면서, DetachedInstanceError가 뜨니, 재귀에선 활용못한다.
    #### => 람다함수를 이용하여 객체.__table__.columns로 칼럼을 돌면서 만들어준다.
    def to_dict(self):
        d = super().to_dict()
        # del d['children']  # 관계필드는 굳이 필요없다. 내가 직접 조회해서 넣어줄 것임.
        return d

    # print(self.__table__.columns)
    # ImmutableColumnCollection(departments.add_date, departments.pub_date, departments.id, departments.name, departments.parent_id, departments.status, departments.sort, departments.path, departments.type)
    #### => 다행이도 객체.__table__.columns는 관계필드('children') 만 조회되지 않는다.
    # row_to_dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}
    row_to_dict = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns
                             if c.name not in []  # 필터링 할 칼럼 모아놓기
                             }

    def get_self_and_children_dict(self):
        result = self.row_to_dict()

        result['children'] = list()
        for child in self.get_children():
            # 내 자식들을 dict로 변환한 것을 내 dict의 chilren key로 관계필드 대신 넣되, 자식들마다 다 append로 한다.
            result['children'].append(child.get_self_and_children_dict())
        return result

    #### with other entity
    def count_employee(self):
        with DBConnectionHandler() as db:
            stmt = (
                select(func.count(distinct(EmployeeDepartment.employee_id)))  # 직원이 혹시나 중복됬을 수 있으니 중복제거하고 카운팅(양적 숫자X)
                .where(EmployeeDepartment.dismissal_date.is_(None))

                .where(EmployeeDepartment.department.has(Department.id == self.id))
            )
            return db.session.scalar(stmt)

    #### with other entity
    #### 자식부서에 같은 사람이 취임할 수 있기 때문에, 개별count -> 단순 누적으로 하면 안된다.
    #### => EmployeeDepartment상의 employee_id를 누적한 뒤, 중복제거해서 반환하는 것으로  처리해야한다.
    def get_employee_id_list(self):
        with DBConnectionHandler() as db:
            stmt = (
                select(EmployeeDepartment.employee_id)  # id를 select한 뒤, scalars().all()하면 객체 대신 int  id list가 반환된다.
                .where(EmployeeDepartment.dismissal_date.is_(None))

                .where(EmployeeDepartment.department.has(Department.id == self.id))
            )
            return db.session.scalars(stmt).all()

    #### with other entity
    def get_self_and_children_emp_id_list(self):
        result = self.get_employee_id_list()

        for child in self.get_children():
            result += child.get_self_and_children_emp_id_list()

        # 카운터를 세기 위해 len(set())으로 반환하고 싶지만, 자식들도 list로 건네줘야하기 때문에, 누적list를 반환해줘야한다.
        return result

    #### with other entity
    def count_self_and_children_employee(self):
        return len(set(self.get_self_and_children_emp_id_list()))

    #### with other entity
    def get_leader(self):
        # 양방향 순환참조를 해결하기 위해 메서드내에서 import
        from .users import Employee

        with DBConnectionHandler() as db:
            stmt = (
                select(Employee)
                .join(EmployeeDepartment)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.department_id == self.id)
                .where(EmployeeDepartment.is_leader == True)
            )
            return db.session.scalars(stmt).first()

    #### 상사 찾기
    def get_leader_recursively(self):
        # 1) 해당 부서의 팀장을 조회한 뒤, 있으면 그 유저를 반환한다
        leader = self.get_leader()
        if leader:
            return leader
        # 2) (해당부서 팀장X) 상위 부서가 있는지 확인한 뒤, 있으면, 재귀로 다시 돌린다.
        if self.parent_id:
            with DBConnectionHandler() as db:
                parent = db.session.scalars(select(Department).where(Department.id == self.parent_id)).first()
                return parent.get_leader_recursively()
        # 3) (팀장도X 상위부서도X) => 팀장정보가 아예 없으니 None반환
        return None


# 2.
class EmployeeDepartment(BaseModel):
    __tablename__ = 'employee_departments'
    # __table_args__ = {'extend_existing': True}

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
    employee = relationship("Employee", backref="employee_departments", foreign_keys=[employee_id],
                            # lazy='joined', # fk가 nullable하지 않으므로, joined를 줘도 된다.
                            )

    department = relationship("Department", backref="employee_departments", foreign_keys=[department_id],
                              # lazy='joined', # fk가 nullable하지 않으므로, joined를 줘도 된다.
                              )

    # 2. 고용일과 퇴직일은 없을 수 있다?! (퇴직일만 nullable=True인듯)
    employment_date = Column(Date, nullable=False, comment='입사일과 다른, 부임일')
    dismissal_date = Column(Date, nullable=True)
    # 휴직처리를 위한 휴직일과 복직일 칼럼 추가
    leave_date = Column(Date, nullable=True)
    reinstatement_date = Column(Date, nullable=True)

    # new 입사당시에 position을 Department.type에 따라 동적입력 -> 칼럼 nullable=True 필수 + .save()로 저장
    position = Column(String(50), nullable=True, comment="부서Type에 따른 직무")
    # new 입사당시에 is_leader인지를 받아서, 그것에 따른 position이 입력되게 해준다. => Department의 leader는 삭제하자.
    #### => 팀장, 팀원 모두가 부임정보에 나와있게 된다.
    is_leader = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}]" \
            # f" title={self.employee.name!r}," \
        # f" parent_id={self.department.name!r}]" \ # 관계필드는 적지말자.

        # f" level={self.level!r}]" # path를 채우기 전에 출력했더니 level써서 에러가 남.
        return info

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
            return None, "이미 부임된 부서입니다."

        #### (2) is_leader로 지원했는데, 팀장이 이미 차 있는지 여부 (exits호출 조건으로서 if is_leadear가 True여야한다.)
        if self.is_leader and self.exists_already_leader():
            print('해당부서에 이미 부서장이 존재합니다.')
            return None, "해당부서에 이미 부서장이 존재합니다."

        #### (3) 부/장급 부서는 only 1명만 등록가능하고, is_leader가 체크안되어있더라도, 체크해줘야한다
        if self.is_full_in_one_person_department():
            print('1명만 부임가능한 부서로서 이미 할당된 부/장급 부서입니다.')
            return None, "1명만 부임가능한 부서로서 이미 할당된 부/장급 부서입니다."

        with DBConnectionHandler() as db:
            #### flush나 commit을 하지 않으면 => fk_id 입력 vs fk관계객체입력이 따로 논다.
            #### => 한번 갔다오면, 관계객체 입력 <-> fk_id 입력이 동일시되며, fk_id입력으로도 내부에서 관계객체를 쓸 수 있게 된다.
            #### => 즉 외부에서 department_id=로 입력해도, 내부에서 self.department객체를 쓸 수 있게 된다.
            db.session.add(self)
            db.session.flush()  # fk_id 입력과 fk관계객체입력 둘중에 뭘 해도 관계객체를 사용할 수 있게 DB한번 갔다오기

            #### 부장급 부서의 취임이라면, is_leader를 무조건 True로 넣어줘서 => position 결정 전에 넣어주고, 자동으로 팀장 포지션이 되게 한다
            if self.department.type == DepartmentType.부장:
                self.is_leader = True

            self.position = self.department.type.find_position(is_leader=self.is_leader,
                                                               dep_name=self.department.name)  # joined를 삭제하면 fk만 넣어줘도 이게 돌아갈까?

            #### 한번만 session에 add해놓으면, 또 add할 필요는 없다.
            # db.session.add(self)
            db.session.commit()

        return True, "새로운 부서취임 정보가 발생하였습니다."

    @classmethod
    def get_by_emp_id(cls, emp_id):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.dismissal_date == None)
                .where(cls.employee_id == emp_id)
            )
            return db.session.scalars(stmt).all()

    @classmethod
    def get_by_emp_and_dept_id(cls, emp_id, dept_id):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.dismissal_date.is_(None))
                .where(cls.employee_id == emp_id)
                .where(cls.department_id == dept_id)
            )
            return db.session.scalars(stmt).first()

    # 부/장급 부서취임정보는 dept_id 검색만 하면, 부/장 1명 정보만 나올 것이다
    @classmethod
    def get_by_dept_id(cls, dept_id):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.dismissal_date.is_(None))
                .where(cls.department_id == dept_id)
            )
            return db.session.scalars(stmt).first()

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
