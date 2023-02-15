import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, func, BigInteger, Date, Text, distinct, \
    case, and_, or_, delete
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref, with_parent

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3.common.base import BaseModel
from src.infra.tutorial3.common.int_enum import IntEnum
from src.main.templates.filters import format_date


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
    ko_NAME = '부서'

    __tablename__ = 'departments'
    # __table_args__ = {'extend_existing': True}

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)
    # name = Column(String(50), nullable=False, comment="부서 이름")
    # 9. + index, unique까지
    name = Column(String(50), nullable=False, index=True, unique=True, comment="부서 이름")

    # parent_id = Column(Integer, comment="상위 부서 id", nullable=True)  # 1 # 2 # 8 + nullable=True
    parent_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), comment="상위 부서 id",
                       nullable=True)  # 5 # parent_id에 fk입히기
    # 5 # one인 parent의 backref에게는 subquery를 줘서, .parent는 바로 얻을 수 있게 하기?!
    children = relationship('Department', backref=backref(
        'parent', remote_side=[id], lazy='subquery',
        # cascade='all',  # 7
        passive_deletes=True,
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
    path = Column(Text().with_variant(String(100), 'mysql'), index=True,
                  nullable=True)  # 동적으로 채울거라 nullabe=True로 일단 주고, add후 다른데이터를 보고 채운다다 => 자식검색시 path.like(자신apth)로 하니 index 필수
    #### mysql 에러: BLOB/TEXT column 'path' used in key specification without a key length
    # - https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy
    # => type을 Text말고, String(1000)으로 변경

    #### EmployeeDepartment에 position을 남기기 위한, Type
    type = Column(IntEnum(DepartmentType), default=DepartmentType.팀, nullable=False, index=True)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"(id={self.id!r}," \
                    f" name={self.name!r}," \
                    f" parent_id={self.parent_id!r}," \
                    f" sort={self.sort!r}," \
                    f" path={self.path!r})" \
            # f" level={self.level!r}]" # path를 채우기 전에 출력했더니 level써서 에러가 남.
        return info

    def exists(self):
        with DBConnectionHandler() as db:
            department = db.session.scalars(
                select(Department)
                .where(Department.name == self.name)
            ).first()
            return department  # 객체 or None

    def save_backup(self):

        # 검증1: 이미 존재하는 부서
        department_or_none = self.exists()
        if department_or_none:
            print(f"{self.name}는 이미 존재하는 부서입니다.")

            return department_or_none

        with DBConnectionHandler() as db:
            db.session.add(self)
            #### 더이상 path구성에 id를 사용하지 않으므로, flush()나 commit()을 미리 할 필요없이 => add만 해도, 자신이 포함된다.
            # db.session.flush()
            #### => session.add()만 한다고 parent_id 입력시 => parent객체가 연동안된다.
            #### => parent_id로 입력된다면 미리 찾아서 넣어줘야한다?

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

    def save(self):

        # 검증1: 이미 존재하는 부서
        if self.exists():
            # print(f"{self.name}는 이미 존재하는 부서입니다.")
            return False, f"{self.name}는 이미 존재하는 부서입니다."

        with DBConnectionHandler() as db:
            db.session.add(self)
            #### 더이상 path구성에 id를 사용하지 않으므로, flush()나 commit()을 미리 할 필요없이 => add만 해도, 자신이 포함된다.
            # print(f'self.parent_id >> ', self.parent_id)
            # print(f'self.parent >> ', self.parent)
            # self.parent_id >>  5
            # self.parent >> None

            db.session.flush()  # flush하면, id연동 + parent_id로 parent연동이 되므로 => 실패시 rollback하도록 수정하자.
            #### => session.add()만 한다고 parent_id 입력시 => parent객체가 연동안된다.
            #### => parent_id로 입력된다면 미리 찾아서 넣어줘야한다?
            # print(f'self.parent_id >> ', self.parent_id)
            # print(f'self.parent >> ', self.parent)
            # self.parent_id >>  5
            # self.parent >>  Department(id=5, title='한방진료실', parent_id=2, sort=2, path='002003002')
            #### => 확인해보니, flush()해서 id획득 + parent연동이 되었어도 맨 뒤에 rollback하면 돌아온다.

            # 부모가 있으면 부모의 부모의 path에 + 생성아이디로 path를 만들어, 변경전 최초 순서?
            # my) 현재 동급레벨의 갯수로 -> sort를 동적으로 채우고, id로 path를 채우는 대신, sort번호로 path를 채우면 될 것 같다?
            # my) # 6 부모가 있으면 where에 with_parent에 올려, 갯수를 센다

            if self.parent:
                # [검증2-1] 이미 해당 부모의 자식이 10명이 채워진 경우, 11번부터 생성못하게 막기
                # =>  flush() 이후의 실패는 rollback() 달아서, 연동했던 것 취소하기
                if len(self.parent.children) > 10:
                    db.session.rollback()
                    return False, "한 부모아래 자식부서는 10개를 초과할 수 없습니다."

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

                # [검증2-2] 부모 없는 경우 root부서의 갯수가 10명이 채워진 경우, 11번부터 생성못하게 막기
                # =>  flush() 이후의 실패는 rollback() 달아서, 연동했던 것 취소하기
                if sort_count > 10:
                    db.session.rollback()
                    return False, "최상위 부서는 10개를 초과할 수 없습니다."

                # print(f'부모가 없어 level==0인 부서는 flush한 나를 포함하여 {sort_count}개로서 sort가 정해집니다', sep=' / ')
            self.sort = sort_count

            prefix = self.parent.path if self.parent else ''
            self.path = prefix + f"{self.sort:0{self._N}d}"

            #### level은 self.path 완성후 사용할 수 있다.
            # [검증4] parent에 의해 결정되는 level이 7(depth8단계) 초과부터는 안받는다.
            if self.level > 5:
                db.session.rollback()
                return False, "최대 깊이는 6단계 까지입니다."

            db.session.commit()  # 검증(flush 이후 rollback) 통과시에만 commit

            return self.to_dict(delete_columns=['pub_date', 'path', ]), "부서 생성에 성공하였습니다."

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
                .where(cls.status)
                .where(cls.name == name)
            ).first()
            return dep

    @classmethod
    def get_by_id(cls, id: int):
        with DBConnectionHandler() as db:
            dep = db.session.scalars(
                select(cls)
                .where(cls.status)
                .where(cls.id == id)
            ).first()
            return dep

    @classmethod
    def get_all(cls):
        with DBConnectionHandler() as db:
            depts = db.session.scalars(
                select(cls)
                .where(cls.status)
                .order_by(cls.path)
            ).all()
            return depts

    @classmethod
    def get_all_tuple_list(cls):
        with DBConnectionHandler() as db:
            depts = db.session.scalars(
                select(cls)
                .where(cls.status)
                .order_by(cls.path)
            ).all()
            return [(x.id, x.name) for x in depts]

    @classmethod
    def get_all_infos(cls):
        with DBConnectionHandler() as db:
            depts = db.session.scalars(
                select(cls)
                .where(cls.status)
                .order_by(cls.path)
            ).all()
            return [{'id': x.id, 'name': x.name} for x in depts]

    # root부서들부터 자식들 탐색할 수 있게 먼저 호출
    @classmethod
    def get_roots(cls, with_inactive=False):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.parent_id.is_(None))
                .order_by(cls.path)  # view에선 sort순이 중요함.
            )
            if not with_inactive:
                stmt = stmt.where(cls.status)

            return db.session.scalars(stmt).all()

    # dept_to_dict = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns
    #                           if c.name not in ['pub_date', 'path', 'type', ]  # 필터링 할 칼럼 모아놓기
    #                           }

    @classmethod
    def get_all_tree(cls, with_inactive=False):
        root_departments = cls.get_roots(with_inactive=with_inactive)

        tree_list = []
        for root in root_departments:
            tree_list.append(root.get_self_and_children_dict())

        return dict(data=tree_list)

    @classmethod
    def exchange_sort_by_id(cls, id_a, id_b):
        with DBConnectionHandler() as db:
            dep_a = db.session.get(cls, id_a)  # get으로 찾앗으면 이미 add된 상태라서 commit만 하면 바뀐다? => execute때문에 자동 커밋 되는 듯.
            dep_b = db.session.get(cls, id_b)

            #### 같은 레벨 내의 sort 교환이어햐만 한다 => 아닐시 에러 추가
            if dep_a.level != dep_b.level:
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
                .where(Department.status)
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
    # def to_dict(self):
    #     d = super().to_dict()
    #     # del d['children']  # 관계필드는 굳이 필요없다. 내가 직접 조회해서 넣어줄 것임.
    #     return d

    # print(self.__table__.columns)
    # ImmutableColumnCollection(departments.add_date, departments.pub_date, departments.id, departments.name, departments.parent_id, departments.status, departments.sort, departments.path, departments.type)
    #### => 다행이도 객체.__table__.columns는 관계필드('children') 만 조회되지 않는다.
    # row_to_dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}
    # row_to_dict = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns
    #                          if c.name not in []  # 필터링 할 칼럼 모아놓기
    #                          }

    def to_dict(self, delete_columns: list = []):
        # to_dict를 r.__table__.columns로 하면 관계필드는 알아서 빠져있다.
        data = super().to_dict()

        for col in delete_columns:
            if col in data:
                del data[col]
        # 커스텀 영역 ##########
        #### Organization ####

        # 부서장 존재 확인용 -> 부서장이 있따면, 부서 전체 직원 - 1을 해서 [순수 부서원 수]만 내려보낸다.
        direct_leader_id = self.get_leader_id()
        if direct_leader_id:
            data['has_direct_leader'] = True
        else:
            data['has_direct_leader'] = False

        # [순수 부서원 수] count_xxxx 메서드는 scalar()에서 알아서 없으면 0 처리된다.
        data['employee_count'] = self.count_employee() - (1 if direct_leader_id else 0)
        # [순수 하위 부서 수]만 카운팅 한다.
        data['only_children_count'] = self.count_only_children()
        # [순수 부서원 + 하위 부서장과 부서원 수]
        # => view에선 부서장 외 N명이 됨.
        data['all_employee_count'] = self.count_self_and_children_employee() - (1 if direct_leader_id else 0)
        # view에서 level별 color / offset 설정을 위한 변수
        data['level'] = self.level

        # [부서장이 있다면, 부서장을 / 없다면 상위부서 부서장의 정보 추출]
        from . import Employee
        leader_id = self.get_leader_id_recursively()

        if leader_id:
            leader: Employee = Employee.get_by_id(leader_id)
            data['leader'] = {
                'id': leader.id, 'name': leader.name, 'avatar': leader.user.avatar,
                'position': leader.get_position_by_dept_id(self.id),
                'job_status': leader.job_status.name,
                'email': leader.user.email,
            }
        else:
            data['leader'] = None

        # [순수 부서원들의 정보만 추출]
        employee_id_list = self.get_employee_id_list(except_leader=True)
        if employee_id_list:
            employees = Employee.get_by_ids(employee_id_list)
            data['employees'] = []
            for emp in employees:
                data['employees'].append({
                    'id': emp.id, 'name': emp.name, 'avatar': emp.user.avatar,
                    'position': emp.get_position_by_dept_id(self.id),
                    'job_status': emp.job_status.name,
                })
        else:
            data['employees'] = None

        # [부모 부서의 sort]  부모색에 대한 명도만 다른 색을 입히기 위해, 색을 결정하는 부모의 sort도 추가
        parent_id = self.parent_id
        if parent_id:
            data['parent_sort'] = Department.get_by_id(parent_id).sort
        else:
            data['parent_sort'] = None

        return data

    def get_self_and_children_dict(self):
        # result = self.row_to_dict
        result = self.to_dict(delete_columns=['pub_date', 'path', ])

        children = self.get_children()

        #### view의 tree컴포넌트는 항상 children을 가지고 있고, children.length로 자식여부를 판단하므로
        #### => 항상 children을 빈list라도 만들어서 반환하도록 수정
        if len(children) > 0:
            result['children'] = list()
            for child in children:
                # 내 자식들을 dict로 변환한 것을 내 dict의 chilren key로 관계필드 대신 넣되, 자식들마다 다 append로 한다.
                result['children'].append(child.get_self_and_children_dict())

        return result

    def count_only_children(self):
        total_count = 0

        children = self.get_children()
        if len(children) > 0:
            total_count += len(children)
            for child in children:
                total_count += child.count_only_children()
        return total_count

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
    def get_employee_id_list(self, except_leader=False):
        with DBConnectionHandler() as db:
            stmt = (
                select(EmployeeDepartment.employee_id)  # id를 select한 뒤, scalars().all()하면 객체 대신 int  id list가 반환된다.
                .where(EmployeeDepartment.dismissal_date.is_(None))

                .where(EmployeeDepartment.department.has(Department.id == self.id))
            )
            if except_leader:
                stmt = stmt.where(EmployeeDepartment.is_leader == False)
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
    def get_leader_id(self):
        # 양방향 순환참조를 해결하기 위해 메서드내에서 import
        # from .users import Employee

        with DBConnectionHandler() as db:
            stmt = (
                # select(Employee)
                # .join(EmployeeDepartment)
                select(EmployeeDepartment.employee_id)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.department_id == self.id)
                .where(EmployeeDepartment.is_leader == True)
            )
            return db.session.scalars(stmt).first()

    #### 부서장 id => 해당부서장 없으면 상사의 id 찾기
    def get_leader_id_recursively(self):
        # 1) 해당 부서의 팀장을 조회한 뒤, 있으면 그 유저를 반환한다
        leader_id = self.get_leader_id()
        if leader_id:
            return leader_id
        # 2) (해당부서에 팀장X) 상위 부서가 있는지 확인한 뒤, 있으면, 재귀로 다시 돌린다.
        if self.parent_id:
            with DBConnectionHandler() as db:
                parent = db.session.scalars(
                    select(Department)
                    .where(Department.id == self.parent_id)
                ).first()
                return parent.get_leader_id_recursively()
        # 3) (팀장도X 상위부서도X) => 팀장정보가 아예 없으니 None반환
        return None

    @classmethod
    def delete_by_id(cls, dept_id):
        with DBConnectionHandler() as db:
            #### 검증1: 존재해야한다. => `여기서 객체를 찾아 session.delete(  only객체만 )`에 활용한다
            target_dept = db.session.get(cls, dept_id)

            if not target_dept:
                return False, "존재하지 않는 부서를 삭제할 순 없습니다."

            #### 검증2. 자식이 있는지 검사
            # stmt = (
            #     select(func.count(cls.id))
            #     .where(cls.parent_id == dept_id)
            # )
            # children_count = db.session.scalar(stmt)
            # if children_count:
            #     return False, "하위부서가 존재하면 삭제할 수 없습니다."
            if len(target_dept.children) > 0:
                return False, "하위부서가 존재하면 삭제할 수 없습니다."

            #### 검증3. 해당부서에 취임된 직원이 있는지 확인
            # => dept.count_employee(self)와 동일하지만, id + cls method로 처리하는 방식이 다른다.
            stmt = (
                select(func.count(
                    distinct(EmployeeDepartment.employee_id)))  # 직원이 혹시나 중복됬을 수 있으니 중복제거하고 카운팅(양적 숫자X)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.department.has(cls.id == dept_id))
            )

            employee_count = db.session.scalar(stmt)
            # print(employee_count)
            if employee_count:
                return False, "재직 중인 직원이 존재하면 삭제할 수 없습니다."

            #### 검증1, 2, 3  통과시 [존재검사시 사용했던 객체]로 삭제
            # db.session.execute(delete(cls).where(cls.id == dept_id))
            db.session.delete(target_dept)
            # db.session.execute(delete(cls).where(cls.id == dept_id))
            db.session.commit()

            return True, "부서를 삭제했습니다."

    @classmethod
    def change_sort(cls, dept_id, after_sort):
        with DBConnectionHandler() as db:
            target_dept = db.session.get(cls, dept_id)

            if not target_dept:
                raise ValueError('해당 부서는 존재하지 않습니다.')


            if  not isinstance(after_sort, int):
                raise ValueError('sort가 정수여야 합니다.')

            before_sort = target_dept.sort
            if before_sort == after_sort:
                return False, "변경되는 전/후 순서가 같을 순 없습니다."

            #### before -> after로 갈 때, 작은데서 큰데로 VS 큰데서 작은데로 갈때 로직이 달라진다.
            # case1: 2->4 번째로 간다면, (3, 4) 번을 순서대로(order_by .path) 위로 1칸(-1) 올려야한다
            # case2: 4->2 번째로 간다면, (2, 3) 번을 밑에서부터 (order_by .path.desc() ) 아래로 1칸(+1) 내려야한다
            if before_sort < after_sort:
                condition = and_(before_sort < Department.sort, Department.sort <= after_sort)
                added_value_for_new_sort = - 1
                order_by = Department.path
            else:
                condition = and_(after_sort <= Department.sort, Department.sort < before_sort)
                added_value_for_new_sort = 1  # 위로 올라올땐, 중간것들이 내려간다.
                order_by = Department.path.desc()  # 위로 올라와, 한칸씩 내려갈땐, 큰 것부터 내려지게 역순으로 진행하게 한다.

            try:
                #### 순차적으로 업뎃할 때, 서로 영향을 끼치는 (다른놈과 같은 sort + path로 덮어쓰기 상황) 경우
                #    -> select를 미리 다 해놓고, update도 순서대로 해야한다.
                # (1) 2->4번으로 가는 [target_dept + 자식]와  3,4한칸씩 올라가는 [related_depts]를 나눠서, 미리 select해둔다
                target_and_children = db.session.scalars(
                    select(Department)
                    .where(Department.path.like(target_dept.path + '%'))
                ).all()

                related_depts = db.session.scalars(
                    select(Department)
                    .where(Department.parent_id == target_dept.parent_id)
                    .where(condition)
                    .order_by(order_by)
                ).all()
                # print("related_depts", related_depts)

                # (2) 대상부서 update전에, 관련부서들은 -> 자식들과 [조회 + 덮어쓰기 업뎃]을 동시에 해야해서, [대상부서를 뺀 순서가 중요]하다
                #     순회하면서 각 dept마다 자식들을 1칸씩 내려주거나 올려줄 때,
                #   -> 위로 올라갈경우, path(sort)정순 / 내려갈 경우, 밑에서부터 path(sort)역순으로 조회 + update해야한다.
                #      (만약, 올라가는데, 아래것부터 올리면, 아래1칸 올린 것 + 바로 윗칸의 조회가 겹치게 된다.
                #   -> 조회 + 업뎃을 순차적으로 할 땐, 덮어쓰기를 대비해서, [마지막에 하는 대상부서에 가까운 순으로] 순차적 [조회+덮어쓰기업뎃]
                for dept in related_depts:
                    # (3) 자신의 sort업뎃
                    new_sort = dept.sort + added_value_for_new_sort
                    dept.sort = new_sort  # sort업뎃은 자신만 => 자식들은 path업뎃만

                    # (4) 자신 + 자식의 path업뎃
                    path_prefix = dept.parent.path if dept.parent else ''
                    new_path = path_prefix + f'{new_sort:0{3}d}'
                    self_and_children = db.session.scalars(
                        select(Department).where(Department.path.like(dept.path + '%'))).all()
                    for child in self_and_children:
                        child.path = new_path + child.path[len(new_path):]

                # (5) 관련부서들이 한칸씩 다 땡겼으면, 미리 select해둔 대상부서를 옮기기
                target_dept.sort = after_sort
                prefix = target_dept.parent.path if target_dept.parent else ''
                new_path = prefix + f'{after_sort:0{3}d}'
                for child in target_and_children:
                    # new_path + 자식들은 그만큼 기존path를 짜르고 나머지 자신 path를 이어붙임
                    child.path = new_path + child.path[len(new_path):]

                db.session.commit()
                return True, "순서 변경에 성공하였습니다."

            except:
                #### 여러가지가 동시에 업뎃되므로 실패시 rollback까지
                db.sesssion.rollback()
                return False, f"순서변경에 실패하였습니다."

    @classmethod
    def change_sort_cross_level(cls, dept_id, after_parent_id, after_sort):
        with DBConnectionHandler() as db:
            try:
                target_dept: Department = db.session.get(cls, dept_id)

                if not target_dept:
                    raise ValueError('해당 부서는 존재하지 않습니다.')

                if target_dept.parent_id == after_parent_id:
                    raise ValueError('같은 부서내 이동은 change_sort를 이용. 로직이 다름(제거/추가가 아닌 삽입/삭제)')

                if target_dept.parent_id in target_dept.get_self_and_children_id_list():
                    raise ValueError('하위 부서로 이동은 불가능 합니다.')

                if (after_parent_id and not isinstance(after_parent_id, int)) or not isinstance(after_sort, int) :
                    raise ValueError('level, sort는 정수여야 합니다.')

                # (1) 대상부서 + 자식들 미리 select
                target_and_children = db.session.scalars(
                    select(Department)
                    .where(Department.path.like(target_dept.path + '%'))
                    .order_by(Department.path)
                ).all()
                # print("target_and_children", target_and_children)

                # (2) `이동 전` 부모들 아래 나보다 sort가 뒤에있는 것들 미리 select
                # -> before level[앞에가 제거]에서 (대상의 부모의 아이들 중)대상부서 sort보다 뒤에 있는 것들 셀렉
                before_related_depts = db.session.scalars(
                    select(Department)
                    .where(Department.parent_id == target_dept.parent_id)
                    .where(Department.sort > target_dept.sort)
                    .order_by(Department.path)
                ).all()
                # print("before_related_depts", before_related_depts)

                # (3) `이동 후` 부모들 아래 나보다 sort가 **같거나** 뒤에있는 것들 미리 **역순** select
                # -> afeter level[앞에서 추가]에서 after_sort부터 시작해서 더 뒤에있는 것 + 역순으로 업뎃예정 셀렉
                after_related_depts = db.session.scalars(
                    select(Department)
                    .where(Department.parent_id == after_parent_id)
                    .where(Department.sort >= after_sort)
                    .order_by(Department.path.desc()) # 필수
                ).all()

                # print("after_related_depts", after_related_depts)

                # (4) before level의 앞으로(위로) 한칸씩 밀기
                for dept in before_related_depts:
                    # print(f'{dept.name, dept.path}  >> ', dept.name, dept.path)

                    new_sort = dept.sort + (-1)
                    dept.sort = new_sort  # sort업뎃은 자신만 => 자식들은 path업뎃만

                    path_prefix = dept.parent.path if dept.parent else ''
                    new_path = path_prefix + f'{new_sort:0{3}d}'
                    self_and_children = db.session.scalars(
                        select(Department).where(Department.path.like(dept.path + '%'))).all()
                    for child in self_and_children:
                        child.path = new_path + child.path[len(new_path):]

                    # print(f'{dept.name, dept.path}  >> ', dept.name, dept.path)

                # (5) after level의 뒤로(아래로) 역순으로 한칸씩 밀기
                for dept_ in after_related_depts:
                    # print(f'{dept_.name, dept_.path}  >> ', dept_.name, dept_.path)

                    new_sort = dept_.sort + (+1)
                    dept_.sort = new_sort  # sort업뎃은 자신만 => 자식들은 path업뎃만

                    path_prefix = dept_.parent.path if dept_.parent else ''
                    new_path = path_prefix + f'{new_sort:0{3}d}'
                    self_and_children = db.session.scalars(
                        select(Department).where(Department.path.like(dept_.path + '%'))).all()
                    for child in self_and_children:
                        child.path = new_path + child.path[len(new_path):]

                    # print(f'{dept_.name, dept_.path}  >> ', dept_.name, dept_.path)

                # (6) 대상부서는 sort만 자신변경 + parent_id도 변경해야한다.
                # (6-1) parent_id도 변경해줘야한다(같은 부모아래와 다른 점)
                target_dept.sort = after_sort
                target_dept.parent_id = after_parent_id

                # (6-2) parent_id로 parent객체를 찾아, 새로운 path_prefix를 찾아낸다.
                parent = db.session.get(Department, after_parent_id) if after_parent_id else None
                prefix = parent.path if parent else ''
                new_path = prefix + f'{after_sort:0{3}d}'
                # print("new_path, target_dept.sort >>>", new_path, target_dept.sort)

                # (6-3) child 업뎃시, 부모의 path가 바뀌기 전 before_path 길이만큼, 미리 앞에를 잘라내야한다.
                before_path = target_dept.path
                target_dept.path = new_path

                # (6-4) 대상부서.get_children()은, status == 1만 가져오는데 여기선 다 가져와야해서, status조건없이 불러낸 것을 가져온다.
                for child in target_and_children[1:]:
                    # case 1)
                    #     before: 002 001    002(s) + 001
                    #      after: 001 001(s)        + 001  after_level이 before보다 작아지면, 그 차이만큼 뒷부분을 더 짤라내고 이어붙어ㅑㅇ햐ㅏㄴ다.
                    #                        [    ] => 자식들은 cls._N * (b - a)만큼 path를 짜르고 new_path와 붙여야한다.
                    # case 2) 만약, 반대상황이라면?
                    #     before: 001 001(s)        + 001
                    #      after: 002 001    002(s) + 001
                    #                        [    ] 만큼 new_path의 길이보다 덜 인덱싱 해서 , 기존 path와 붙여야한다.
                    #    => child 입장에서는, 부모의 new_path에 +  [부모의 before_path길이만큼 짜른 자신만의 path]만 있으면 된다.
                    child.path = new_path + child.path[len(before_path):]

                db.session.commit()
                return True, "부서의 위치가 변경되었습니다."

            except Exception as e:
                # raise e
                #### 여러가지가 동시에 업뎃되므로 실패시 rollback
                db.session.rollback()
                return False, f"부서의 위치가 변경에 실패하였습니다."

    @classmethod
    def change_status(cls, dept_id):
        # 검증1. 재직중인 직원이 있으면 못바꾼다.
        emp_depts = EmployeeDepartment.get_by_dept_id(dept_id)
        if emp_depts:
            return False, "재직 중인 직원이 있으면 변경할 수 없습니다."

        with DBConnectionHandler() as db:
            dept = db.session.get(cls, dept_id)
            if not dept:
                return False, "해당 부서가 존재하지 않습니다."

            dept.status = int(not dept.status)

            db.session.commit()

            return True, "부서 활성 변경에 성공하였습니다."


# 2.
class EmployeeDepartment(BaseModel):
    ko_NAME = '취임정보'
    __tablename__ = 'employee_departments'
    # __table_args__ = {'extend_existing': True}

    # __table_args__ = (ForeignKeyConstraint(['user_id'], ['users.id'], name='users_tag_maps_department_id_fk'),)

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True)

    # user_id = Column(Integer, nullable=False)
    # department_id = Column(Integer, nullable=True) # 부서는 nullable일 수 있다.?! 유저마다 유저부서 정보가 생기는데, 부서는 없을 수 있음? => 유저-부서정보라서 꼭 있어야한다. 여기선 join할 일이 없어서 안쓰는 듯.
    # 5.에서는 user-contract관계에서 contract.id의 FK를 index=True
    # employee_id = Column(Integer, nullable=False, index=True)
    # department_id = Column(Integer, nullable=False, index=True)
    # pickupapi # 다대다+정보도 관계테이블처럼 fk로 주기
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)

    # department_id = Column(Integer, ForeignKey('departments.id'), nullable=False, index=True)
    #### session.delete( dept )시, fk테이블인 여기에서 where = dept.id update set NULL이 자동으로 이루어진다.
    #### => (1) one이 삭제될 수도 있다면(실제 검증에서 삭제안하게 할 건데), 부가적으로 발생하는 update에 대비해서 nullable=False를 지워준다.
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), index=True,
                           nullable=True)

    # new
    employee = relationship("Employee", backref="employee_departments", foreign_keys=[employee_id],
                            # lazy='joined', # fk가 nullable하지 않으므로, joined를 줘도 된다.
                            )

    department = relationship("Department", backref=backref("employee_departments", passive_deletes=True),
                              foreign_keys=[department_id],
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
            return db.session.scalars(stmt).all()

    #     재직 = 1 => 역순 정리시 history 제일 뒤쪽에 나타날 예정
    #     복직 = 1 => 휴직~복직 => 복직된 순간 재직 정보다?!
    #     휴직 = 2
    #     퇴사 = 3
    @hybrid_property
    def status(self):

        # 휴직일, 퇴직일이 모두 안채워져있으면 -> 재직 1
        if not self.leave_date and not self.dismissal_date:
            # return '재직'
            return 1
        # (휴직일 or 퇴직일이 찬 상태)
        # 퇴직일 차있으면 휴직/복직일 상관없이 먼저 퇴직으로 골라 내야한다.
        if self.dismissal_date:
            # return '퇴직'
            return 3

        # (퇴직일X ->휴직일이 차있는 상태)
        # 휴직일은 잇는데 복직일이 없으면 휴직 상태 => 2
        if self.leave_date and not self.reinstatement_date:
            # return '휴직'
            return 2

        # 휴직일과 복직일 모두 있으면=> 복직 = 재직과 동일한 1
        if self.leave_date and self.reinstatement_date:
            # return '복직' -> '재직'과 동일
            return 1

        return 0

    @status.expression
    def status(self):
        # 칼럼.is_(None) or isnot(None)  isnot은 _가 없다.
        # python and 대신 조건문을 and_(, ,)로 연결한다.

        return case([
            (and_(self.dismissal_date.is_(None), self.leave_date.is_(None)), 1),  # 재직
            (self.dismissal_date.isnot(None), 3),  # 퇴사
            (and_(self.leave_date.isnot(None), self.reinstatement_date.is_(None)), 2),  # 휴직
            (and_(self.leave_date.isnot(None), self.reinstatement_date.isnot(None)), 1),  # 복직
        ],
            else_=0
        )

    @hybrid_property
    def status_string(self):
        # status_string_list = ['재직', '복직', '휴직', '퇴사']
        # return status_string_list[status]
        # TypeError: list indices must be integers or slices, not hybrid_propertyProxy
        if self.status == 1:
            return '재직'
        if self.status == 2:
            return '휴직'
        if self.status == 3:
            return '퇴사'
        return '에러'

    @status_string.expression
    def status_string(self):
        return case([
            (self.status == 1, '재직'),
            (self.status == 2, '휴직'),
            (self.status == 3, '퇴사'),
        ],
            else_='에러'
        )

    #### 취임정보의 status에서 따라서, start_date ~ end_date가 다르다.
    # 시작일 (재직, 복직, 퇴사 -> 고용일 / 휴직 -> 휴직시작일 )
    # 끝  일 (재직, 휴직, : 현재 / 복직 ->복직일 / 퇴사 -> 퇴사일 )
    # 고용일 고정이지만 ~ 해임일(재직, 휴직: 오늘 / 복직: 복직일 / 퇴사: 퇴사일)로
    @hybrid_property
    def start_date(self):
        # 휴직 -> 휴직일이 시작
        if self.status == 2:
            return self.leave_date
        # 그외 재직(복직), 퇴사 -> 고용일이 시작
        return self.employment_date

    @start_date.expression
    def start_date(self):
        return case([
            (self.status == 2, self.leave_date),
        ],
            else_=self.employment_date
        )

    @hybrid_property
    def end_date(self):
        # 재직(복직) or 휴직시 [현재]가 end_date
        if self.status == 1 or self.status == 2:
            return datetime.date.today()
        # 퇴직시 퇴직일이 end_date
        return self.dismissal_date

    @end_date.expression
    def end_date(self):
        # db종류와 상관없이 func.now()는 timestamp를 제공한다..?!
        # => date로 바꾸기 위해, fun.date()로 한번 더 싼다.
        return case([
            (or_(self.status == 1, self.status == 2), func.date(func.now())),
        ],
            else_=self.dismissal_date
        )

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
