import itertools
import random
from pprint import pprint

import faker
from dateutil.relativedelta import relativedelta
from faker import Faker
from sqlalchemy import select, func, distinct, and_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.orm import with_parent

from create_database_tutorial3 import *
from src.infra.tutorial3.common.grouped import grouped
from src.main.templates.filters import format_date

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
    # last_seen = Column(DateTime, default=datetime.datetime.now, nullable=True)

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
    # last_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)

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
    # [<Employee 2>, <Employee 4>, <Employee 5>, <Employee 13>, <Employee 16>, <Employee 18>, <Employee 19>]
    chiefstaffs = Employee.get_by_user_role(Roles.CHIEFSTAFF)
    # [<Employee 11>, <Employee 12>, <Employee 15>]
    executives = Employee.get_by_user_role(Roles.EXECUTIVE)
    # [<Employee 8>, <Employee 10>]

    병원장 = Department(name='병원장', type=DepartmentType.부장).save_backup()

    진료부 = Department(name='진료부', type=DepartmentType.부장, parent=병원장).save_backup()
    간호부 = Department(name='간호부', type=DepartmentType.부장, parent=병원장).save_backup()
    행정부 = Department(name='행정부', type=DepartmentType.부장, parent=병원장).save_backup()

    #### 진료부 하위 부서 - 팀장없이
    한방진료실 = Department(name='한방진료실', type=DepartmentType.원장단, parent=진료부).save_backup()
    탕전실 = Department(name='탕전실', type=DepartmentType.실, parent=진료부).save_backup()
    #### 간호부 하위 부서 - 팀장없이
    외래 = Department(name='외래', type=DepartmentType.치료실, parent=간호부).save_backup()
    병동 = Department(name='병동', type=DepartmentType.치료실, parent=간호부).save_backup()
    #### 행정부 하위 부서 - 팀장없이
    원무 = Department(name='원무', type=DepartmentType.팀, parent=행정부).save_backup()
    총무 = Department(name='총무', type=DepartmentType.팀, parent=행정부).save_backup()


    print('*' * 30, '조직도 만들기', '*' * 30)
    직원: Employee = Employee.get_by_id(22)
    print(f"직원의 현 소속부서: emp.get_my_departments()=>  {직원.get_my_departments()}")
    print(f"직원의 현 소속부서 별 부서id/name + 취임position: emp.get_dept_name_and_position_list")
    for id, name, position in 직원.get_dept_id_and_name_and_position_list():
        print(id, name, position)
    print(f"(new)직원의  퇴사/휴직/복직 모든 부서정보 기록: [부서정보 + 취임정보 history] : emp.get_dept_history_row_list() =>")
    print('-'*4*1,f"EmployeeDepartment property : status => 재직==복직:1 / 휴직:2/ 퇴사:3")
    print('-'*4*1,f" EmployeeDepartment property : status-> status_string => 재직 / 휴직(복직하면 재직) / 퇴사")
    print('-'*4*1,f" EmployeeDepartment property : status-> start_date => 시작일 (재직=복직, 퇴사 -> 고용일 / 휴직 -> 휴직시작일 )")
    print('-'*4*1,f" EmployeeDepartment property : status-> end_date   => 끝  일 (재직=복직, 휴직 -> 현재 /  퇴사 -> 퇴사일 )")
    print('-'*4*2,f" history_row를 status역순(퇴사->휴~복직 -> 휴직 -> 재직 순으로, 같으면 start_date와 end_date가 일찍 끝나는 순으로")
    for history_row in 직원.get_dept_history_row_list():
        print(f"{history_row.start_date}~{history_row.end_date} {history_row.name}({history_row.position}) status:{history_row.status} / {history_row.status_string}")


    print('Add=================')
    print('parent_id만 넣고, session.add하면 self.parent가 연동되는지??? => self.parent_id >>  5 / self.parent >>  None 안됨.' )
    faker = Faker('ko_KR')
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()
    # Department(name=faker.name(), type=DepartmentType.팀, parent_id=None).save()

    print('Delete=================')
    faker_name = faker.name()
    name = faker_name
    new_dept, message = Department(name=name, type=DepartmentType.팀, parent_id=2).save()

    print(f'{name} 생성시도 >>> message = {message} ')

    if new_dept:
        result, message = Department.delete_by_id(new_dept['id'])
        print(f'{new_dept["name"]} 삭제 message = {message} >> ', new_dept["name"])
    else:
        print(f'{name} 생성 실패 >> ', name)



    # 사용 직원 목록 :
    # 직원_병원장
    # 직원_부원장
    # 직원_행정부장
    # 직원_원무팀원
    # print('*' * 30, '모든 부서 조회')
    # for it in Department.get_all():
    #     print(it.level * '    ', it)
    # print('*' * 30)
    # print('*' * 30, '조직도를 위한 Dept tree만들기')
    # print('-' * 4 * 1, f'Department.get_roots()[0] => {Department.get_roots()[0]}')
    # print('-' * 4 * 1, f'Department.get_all_tree() => ')
    # print(Department.get_all_tree())
    # pprint(Department.get_all_tree())

    for it in Department.get_all():
        print(it.level * '    ', '[', it.id,'-', it.name, '] ', '부서장:', Employee.get_by_id(it.get_leader_id()),
              '직원 수:', it.count_employee(),
              '하위부서 모든 직원 수:', it.count_self_and_children_employee())
    print('*' * 30)

