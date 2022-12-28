import datetime
import json
import re
import time

from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload, lazyload

from create_database_tutorial3 import *
from src.infra.tutorial3.auth.departments import DepartmentType
from src.infra.tutorial3.notices import BannerType

if __name__ == '__main__':
    # 1. init data가 있을 땐: load_fake_data = True
    # 2. add() -> commit() method save 등장부터는, 싹다 지우고 시작할 땐: truncate = True
    # 3. 테이블구조가 바뀌는 상황엔, 모든 table 지웠다 새로 생성: drop_table = True
    # create_database(truncate=True, drop_table=False)
    session = Session()
    # create_database(truncate=False, drop_table=False, load_fake_data=False)
    # bulk_insert_from_json('./backup_2022-12-02_211719.json', 'users')
    # 4. 현재 데이터들을 table별로 json으로 백업하기
    # https://stackoverflow.com/questions/47307873/read-entire-database-with-sqlalchemy-and-dump-as-json
    # dump_sqlalchemy('users',is_id_change=True)
    # dump_sqlalchemy('users')
    # 5. 백업json을 table별로 key로하는 dict로 불러오기
    # load_dump("./backup_2022-12-02_211719.json") # print(type(tables)) # <class 'dict'>
    # 6. 백업json -> dict로 load한 뒤, Entity별 bulk_insert_mappings(Entity, dict list)
    # bulk_insert_from_json('./backup_2022-12-03_172847.json', 'users')

    # Role.insert_roles()


    #### 필드추가 전 1) 필드 추가전 먼저 dump   ( 테이블은 미리 추가하면 안된다!!!!!! )
    # dump_sqlalchemy() # User last_seen, ping_by_id() # Employee entity 추가전
    # dump_sqlalchemy('employees')
    # 저장>>> ./backup_2022-12-14_193544.json

    #### 필드추가 전 2) nullable 필드 code 추가 (테이블추가 아님!!!!!!!!!)
    #### => entity에 nullable로 필드 코드 추가
    #last_seen = Column(DateTime, default=datetime.datetime.now, nullable=True)

    #### 필드추가 전 3) 필드를 nullable로 생성된를 drop_table=True로 테이블 생성 -> bulk insert
    # create_database(truncate=False, drop_table=True, load_fake_data=False)
    # bulk_insert_from_json('./backup_2022-12-23_132512.json')
    ####  OR  테이블 1개만 수동 삭제 =>  drop_table=False로 생성 + 특정테이블 insert
    # create_database(truncate=False, drop_table=False, load_fake_data=False)
    # bulk_insert_from_json('./backup_2022-12-23_134339.json', table_name='employees')


    #### 필드추가 전 4) nullable 필드 수동 채우기 or flask shell에서 코드로 채우기
    # @app.shell_context_processor
    # def make_shell_context():
    #     return dict(db=DBConnectionHandler(), User=User, Role=Role)

    # Role.insert_roles()
    #
    # (venv) flask shell
    # admin_role = Role.query.filter_by(name='Administrator').first()
    # default_role = Role.query.filter_by(default=True).first()
    # for u in User.query.all():
    #     if u.role is None:
    #             if u.email == app.config['MYBLOG_ADMIN']:
    #                     u.role = admin_role
    #             else:
    #                     u.role = default_role
    #
    # db.session.commit()

    #### 필드추가 전 6) nullable =False로 변경하고 나중에 migrate
    #last_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)


    #### 필드추가 전 7) 테이블 code 추가

    #### 필드추가 전 8) 테이블 추가는 drop_table = False상태로 생성
    # create_database(truncate=False, drop_table=False, load_fake_data=False)



    ######## department, employeedepartment 설정
    create_database(truncate=False, drop_table=False, load_fake_data=False)
    # 조직도 참고: http://m.soldamclinic.com/page/page114
    # 병원장 / 진료부 + 간호부 + 행정부 /
    #         진료부 - 한방진료실 / 양방진료실 / 물리치료실 / 탕전실
    #         간호부 - 외래 / 병동 / 고객지원 / 서비스센터
    #         행정부 - 원무팀 / 총무팀
    #### (1) 부서 생성
    staffs = Employee.get_by_user_role(Roles.STAFF)
    chiefstaffs = Employee.get_by_user_role(Roles.CHIEFSTAFF)
    executives = Employee.get_by_user_role(Roles.EXECUTIVE)
    # [<Employee 2>, <Employee 4>, <Employee 5>, <Employee 13>, <Employee 16>, <Employee 18>, <Employee 19>]
    # [<Employee 11>, <Employee 12>, <Employee 15>]
    # [<Employee 8>, <Employee 10>]

    병원장 = Department(name='병원장', type=DepartmentType.부장).save()

    진료부 = Department(name='진료부', type=DepartmentType.부장, parent=병원장).save()
    간호부 = Department(name='간호부', type=DepartmentType.부장, parent=병원장).save()
    행정부 = Department(name='행정부', type=DepartmentType.부장, parent=병원장).save()

    #### 진료부 하위 부서 - 팀장없이
    한방진료실 = Department(name='한방진료실', type=DepartmentType.원장단, parent=진료부).save()
    탕전실 = Department(name='탕전실', type=DepartmentType.실, parent=진료부).save()
    #### 간호부 하위 부서 - 팀장없이
    외래 = Department(name='외래', type=DepartmentType.치료실, parent=간호부).save()
    병동 = Department(name='병동', type=DepartmentType.치료실, parent=간호부).save()
    #### 행정부 하위 부서 - 팀장없이
    원무 = Department(name='원무', type=DepartmentType.팀, parent=행정부).save()
    총무 = Department(name='총무', type=DepartmentType.팀, parent=행정부).save()


    #### (2) 부서에 부임
    #### => 한 사람은 (다른)여러부서에 [user의 role과 상관없이 오로지 팀원으로만] 입사한다 & 팀장은 부서정보에서 수정해서 넣어줄 것이다.
    ####   + 부서 추가 가입시, 다른 부서에만 가입가능하므로, add시에는 [같은부서인지에 대한 exists]는 필요하다.
    병원장_취임 = EmployeeDepartment(
        department=병원장,
        employee=executives[0],
        employment_date=datetime.date.today(),
        is_leader=True
    ).save()

    #### 동적으로 객체를 이용하는데, joined도 안해준 상태에서 관계객체 대신, fk_id를 직접 넣어준다면 작동할까?
    대표원장_취임 = EmployeeDepartment(
        department_id=한방진료실.id, # 내부에서 flush해서, self.department.type을 쓰므로, id를 입력해줘도 된다.
        employee=chiefstaffs[0],
        employment_date=datetime.date.today(),
        is_leader=True
    ).save()

    부원장_취임 = EmployeeDepartment(
        department_id=한방진료실.id,
        employee=staffs[0],
        employment_date=datetime.date.today(),
        # is_leader=True
    ).save()


    대표원장_추가로_취임시_안됨 = EmployeeDepartment(
        department=한방진료실,
        employee=chiefstaffs[1], # 추가로 다른사람을 부임시키면 -> 부서장 이미 있다고 든다.
        employment_date=datetime.date.today(),
        is_leader=True # 이미 is_leader가 있는 부서인데
    ).save()

    부장급_부서에_1명_초과가입시_안됨 = EmployeeDepartment(
        department=병원장,
        employee=chiefstaffs[0],
        employment_date=datetime.date.today(),
        # is_leader=True # 부서장이든 말든 부장급부서는 1명이 이미 존재하면 -> 1명만 부임가능 부서라고 뜬다.
    ).save()








