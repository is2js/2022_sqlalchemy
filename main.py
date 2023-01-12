from flask import jsonify
from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_, distinct

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload, lazyload

from create_database_tutorial3 import *
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
        department=Department.get_by_name('병원장'),
        employee=Employee.get_by_user_role(Roles.CHIEFSTAFF)[0],
        employment_date=datetime.date.today(),
        is_leader=True
    ).save()

    부장급_부서에_1명_초과가입시_안됨 = EmployeeDepartment(
        department=Department.get_by_name('병원장'),
        employee=Employee.get_by_user_role(Roles.EXECUTIVE)[0],
        employment_date=datetime.date.today(),
        # is_leader=True # 부서장이든 말든 부장급부서는 1명이 이미 존재하면 -> 1명만 부임가능 부서라고 뜬다.
    ).save()

    진료부장_취임 = EmployeeDepartment(
        department=Department.get_by_name('진료부'),
        employee=Employee.get_by_user_role(Roles.CHIEFSTAFF)[0],
        # 한번 썼던 사람은 다시 찾는게 아니라면 못쓴다. 내부에서 .name 등의 필드에 접근했기 때문?
        employment_date=datetime.date.today(),
        is_leader=True
    ).save()

    #### 동적으로 객체를 이용하는데, joined도 안해준 상태에서 관계객체 대신, fk_id를 직접 넣어준다면 작동할까?
    대표원장_취임 = EmployeeDepartment(
        department_id=Department.get_by_name('한방진료실').id,  # 내부에서 flush해서, self.department.type을 쓰므로, id를 입력해줘도 된다.
        employee=Employee.get_by_user_role(Roles.CHIEFSTAFF)[1],
        employment_date=datetime.date.today(),
        is_leader=True
    ).save()

    대표원장_추가로_취임시_안됨 = EmployeeDepartment(
        department=Department.get_by_name('한방진료실'),
        employee=Employee.get_by_user_role(Roles.CHIEFSTAFF)[0],  # 추가로 다른사람을 부임시키면 -> 부서장 이미 있다고 든다.
        employment_date=datetime.date.today(),
        is_leader=True  # 이미 is_leader가 있는 부서인데
    ).save()

    부원장_취임 = EmployeeDepartment(
        department_id=Department.get_by_name('한방진료실').id,
        employee=Employee.get_by_user_role(Roles.STAFF)[0],
        employment_date=datetime.date.today(),
        # is_leader=True
    ).save()

    부원장_취임_2 = EmployeeDepartment(
        department_id=Department.get_by_name('한방진료실').id,
        employee=Employee.get_by_user_role(Roles.STAFF)[1],
        employment_date=datetime.date.today(),
        # is_leader=True
    ).save()

    행정부_팀장_취임 = EmployeeDepartment(
        department_id=Department.get_by_name('행정부').id,
        employee=Employee.get_by_user_role(Roles.CHIEFSTAFF)[1],
        employment_date=datetime.date.today(),
        is_leader=True
    ).save()

    원무팀_팀원_취임 = EmployeeDepartment(
        department_id=Department.get_by_name('원무').id,
        employee=Employee.get_by_user_role(Roles.STAFF)[2],
        employment_date=datetime.date.today(),
    ).save()

    #### 진료부장을 current_user로 생각해서, 부서+자식부서들 선택 / 나보다 하위직원 뽑기
    current_employee_id = 진료부장_취임.employee_id
    stmt = (
        select(User)
        .where(User.employee.any(Employee.id == current_employee_id))
    )
    current_user = session.scalars(stmt).first()
    # print(current_user)
    # SELECT users.add_date, users.pub_date, users.id, users.username, users.password_hash, users.email, users.last_seen, users.is_active, users.avatar, users.sex, users.address, users.phone, users.role_id
    # FROM users
    # WHERE EXISTS (SELECT 1
    # FROM employees
    # WHERE users.id = employees.user_id AND employees.id = :id_1)
    # User[id=20]

    ## (1) 내가 팀장으로 속한 부서정보들 구하기
    print('*' * 30, '내가 팀장으로 속한 부서정보(들) 구하기 by has + is_leader', '*' * 50)
    # 1-1.  부서정보를 뽑되, 필터링 entity를 Employee -> .user_id or user로 User까지 사용하면 된다.
    # 1) 최종적으로 구할 객체의 entity -> select에
    # 2) Ed -> .any()/.has()로 Employee로 먼저 1차 필터링 entity 연결 (기본조건)
    # 3) Employee.관계피륻(fk_id)로 2차 필터링 entity 연결
    # 4) 그정보들 중에 내가 팀장으로 있는 부서정보
    stmt = (
        select(EmployeeDepartment)
        .where(EmployeeDepartment.dismissal_date.is_(None))
        .where(EmployeeDepartment.employee.has(Employee.user == current_user))

        .where(EmployeeDepartment.is_leader == True)
    )

    emp_dep_leader_all = session.scalars(
        stmt
    ).all()

    # print(stmt)

    # SELECT employee_departments *
    # FROM employee_departments
    # WHERE employee_departments.dismissal_date IS NULL
    #   AND (EXISTS (SELECT 1
    #       FROM employees
    #       WHERE employees.id = employee_departments.employee_id
    #           AND :param_1 = employees.user_id))
    #  AND employee_departments.is_leader = true

    print(emp_dep_leader_all)
    # [EmployeeDepartment[id=1, title='123', parent_id='병원장'], EmployeeDepartment[id=2, title='123', parent_id='진료부'], EmployeeDepartment[id=3, title='123', parent_id='한방진료실']]

    ## (2) 이 중에, 내가 팀장인 부서정보중에, 가장 level이 가장 낮은  상위 부서 찾기
    # -> 같은 세션안에서 처리하므로, 관계필드를 타고 들어가서 비교해도 된다.
    # min_level_emp_dep_list = min(emp_dep_leader_all, key=lambda x:x.department.level)
    # print(min_level_emp_dep) # EmployeeDepartment[id=1, title='123', parent_id='병원장']
    ## (3) 없을 수도 있고, 같은level이 2개가 걸릴 수 도 있다. => 반복문으로 처리하자.

    print('*' * 30, '내가 팀장인 부서정보중에, 가장 level이 가장 낮은  상위 부서 찾기 min_lv_subq + has ', '*' * 50)
    subq_scalar_min_level = (
        select(func.min(Department.level))
    ).correlate(EmployeeDepartment) \
        .scalar_subquery()

    stmt = (
        select(EmployeeDepartment)
        .where(EmployeeDepartment.dismissal_date.is_(None))
        .where(EmployeeDepartment.employee.has(Employee.user == current_user))
        .where(EmployeeDepartment.is_leader == True)
        # 내가 팀장 인 부서정보들 중, level이 가장 낮은 것으로 필터링 => 여러개일 수 있다.
        .where(EmployeeDepartment.department.has(Department.level == subq_scalar_min_level))
    )

    user_leader_min_level_deps = session.scalars(
        stmt
    ).all()

    # print(stmt)
    # SELECT employee_departments.add_date, employee_departments.pub_date, employee_departments.id, employee_departments.employee_id, employee_departments.department_id, employee_departments.employment_date, employee_departments.dismissal_date, employee_departments.position, employee_departments.is_leader
    # FROM employee_departments
    # WHERE employee_departments.dismissal_date IS NULL AND (EXISTS (SELECT 1
    # FROM employees
    # WHERE employees.id = employee_departments.employee_id AND :param_1 = employees.user_id)) AND employee_departments.is_leader = true AND (EXISTS (SELECT 1
    # FROM departments
    # WHERE departments.id = employee_departments.department_id AND length(departments.path) / :length_1 - :param_2 = (SELECT max(length(departments.path) / :length_2 - :param_3) AS max_1
    # FROM departments)))

    # print(user_leader_min_level_deps)
    # [EmployeeDepartment[id=1, title='123', parent_id='병원장']]

    ## (3) 팀장인  min level 부서정보들 => 부서객체로 변환하기?
    subq = (
        select(EmployeeDepartment.department_id)
        .where(EmployeeDepartment.dismissal_date.is_(None))
        .where(EmployeeDepartment.employee.has(Employee.user == current_user))
        .where(EmployeeDepartment.is_leader == True)
        # 내가 팀장 인 부서정보들 중, level이 가장 낮은 것으로 필터링 => 여러개일 수 있다.
        .where(EmployeeDepartment.department.has(Department.level == subq_scalar_min_level))
    ).scalar_subquery()

    stmt = (
        select(Department)
        .where(Department.id.in_(subq))
    )

    # print(stmt)
    # print(session.scalars(stmt).all())
    # SELECT departments.add_date, departments.pub_date, departments.id, departments.name, departments.parent_id, departments.status, departments.sort, departments.path, departments.type
    # FROM departments
    # WHERE departments.id IN (SELECT employee_departments.department_id
    # FROM employee_departments
    # WHERE employee_departments.dismissal_date IS NULL AND (EXISTS (SELECT 1
    # FROM employees
    # WHERE employees.id = employee_departments.employee_id AND :param_1 = employees.user_id)) AND employee_departments.is_leader = true AND (EXISTS (SELECT 1
    # FROM departments
    # WHERE departments.id = employee_departments.department_id AND length(departments.path) / :length_1 - :param_2 = (SELECT min(length(departments.path) / :length_2 - :param_3) AS min_1
    # FROM departments))))
    # [Department[id=1, title='병원장', parent_id=None]]

    ## (3) 부서로 먼저 변환후, min_level 필터링
    stmt = (
        select(Department)
        .where(Department.id.in_([x.department_id for x in user_leader_min_level_deps]))
    )

    # print(stmt)
    # print(session.scalars(stmt).all())

    ## (4) 개선 -> 부서로 먼저 변환후 min level필터링
    print('*' * 30, '개선) has(user) + min_lv_select_scalar_subq -> 2개로 select ', '*' * 50)
    user_leader_dep_ids = (
        select(EmployeeDepartment.department_id)
        .where(EmployeeDepartment.dismissal_date.is_(None))
        .where(EmployeeDepartment.employee.has(Employee.user == current_user))
        .where(EmployeeDepartment.is_leader == True)
    ).scalar_subquery()

    min_level = (
        select(func.min(Department.level))
    ).scalar_subquery()

    stmt = (
        select(Department)
        .where(Department.id.in_(user_leader_dep_ids))
        .where(Department.level == min_level)
    )

    # print(stmt)
    print(session.scalars(stmt).all())
    # SELECT departments
    # FROM departments
    # WHERE departments.id IN (SELECT employee_departments.department_id
    #       FROM employee_departments
    #       WHERE employee_departments.dismissal_date IS NULL AND (EXISTS (SELECT 1
    #           FROM employees
    #           WHERE employees.id = employee_departments.employee_id AND :param_1 = employees.user_id))
    #       AND employee_departments.is_leader = true)
    # AND length(departments.path) / :length_1 - :param_2 = (SELECT min(length(departments.path) / :length_2 - :param_3) AS min_1
    #       FROM departments)
    # [Department[id=1, title='병원장', parent_id=None]]

    #### 메서드화
    print('*' * 30, '메서드화', '*' * 30)
    # print(f"current_user.get_departments() >> {current_user.get_departments()}")
    # print(f"current_user.get_departments(as_leader=True) >> {current_user.get_departments(as_leader=True)}")
    print(
        f"current_user.get_my_departments(as_leader=True, as_employee=False, as_min_level=True) => "
        f"{current_user.get_my_departments(as_leader=True, as_employee=False, as_min_level=True)}"
    )
    print(
        f"User.get_by_id(11).get_my_departments(as_min_level=True) => "
        f"{User.get_by_id(11).get_my_departments(as_min_level=True)}"
    )

    # print('부서조회', '*' * 30)
    ## (5) 모든 부서 재귀 조회 - 전체 조회는 path 정렬 + level 패딩을 줘서, 1개씩 출력한다
    # - path로 인해, 자신의 자식부터 다 연결하고, 다음 것으로 넘어간다
    # stmt = (
    #     select(Department)
    #     .order_by(Department.path)
    # )
    # for it in session.scalars(stmt):
    #     print(it.level * '    ', it)
    # print('*' * 30)
    # 부서조회 ******************************
    #  Department(id=1, title='병원장', parent_id=None) path='001',
    #      Department(id=2, title='진료부', parent_id=1) path='001001',
    #          Department(id=5, title='한방진료실', parent_id=2) path='001001001',
    #          Department(id=6, title='탕전실', parent_id=2) path='001001002',
    #      Department(id=3, title='간호부', parent_id=1) path='001002',
    #          Department(id=7, title='외래', parent_id=3) path='001002001',
    #          Department(id=8, title='병동', parent_id=3) path='001002002',
    #      Department(id=4, title='행정부', parent_id=1) path='001003',
    #          Department(id=9, title='원무', parent_id=4) path='001003001',
    #          Department(id=10, title='총무', parent_id=4) path='001003002',
    # ******************************

    ## sort -> path -> level이 나오는데   level별로 같은 레벨이면 sort순으로 정렬해보자.
    ## -  sort 변경시 path도 같이 변경되어야할 것 같고, 그 path별로 정렬해야할 것 같다. 특정level별 조회할 일은 없을 듯. level은 padding사용만 할 듯.
    ## - path자체가 자식있으면 자식들 + sort순이다.
    ## - 나의 자식들만 처리하려면, 따로 thread칼럼을 만들어야한다.

    ##  특정 level만 모은다면, 그 땐 path가 아니라 sort순으로? 그래도 path순으로 하면 된다?
    # -> sort는 같은부모아래에서의 순서라서, 같은 부모도 아닌데 sort로 정렬하면 다른부모의 자식1번들만 먼저 나와서 섞이게 된다.
    # stmt = (
    #     select(Department)
    #     .order_by(Department.path)
    # )

    # for it in session.scalars(stmt):
    #     print(it.level * '    ', it)
    # print('*' * 30)

    # sort
    #          Department(id=5, title='한방진료실', parent_id=2) path='001001001',
    #          Department(id=7, title='외래', parent_id=3) path='001002001',
    #          Department(id=9, title='원무', parent_id=4) path='001003001',
    #          Department(id=6, title='탕전실', parent_id=2) path='001001002',
    #          Department(id=8, title='병동', parent_id=3) path='001002002',
    #          Department(id=10, title='총무', parent_id=4) path='001003002',

    # path
    #          Department(id=5, title='한방진료실', parent_id=2) path='001001001',
    #          Department(id=6, title='탕전실', parent_id=2) path='001001002',
    #          Department(id=7, title='외래', parent_id=3) path='001002001',
    #          Department(id=8, title='병동', parent_id=3) path='001002002',
    #          Department(id=9, title='원무', parent_id=4) path='001003001',
    #          Department(id=10, title='총무', parent_id=4) path='001003002',

    # print('sort변경시 path도 같이 변경되게 하기', '*' * 30)
    ## (6) 모든 부서 재귀 조회 - 전체 조회는 path 정렬 + level 패딩을 줘서, 1개씩 출력한다
    #   Department(id=1, title='병원장', parent_id=None) sort=1) path='001',
    #      Department(id=2, title='진료부', parent_id=1) sort=1) path='001001',
    #          Department(id=5, title='한방진료실', parent_id=2) sort=1) path='001001001',
    #          Department(id=6, title='탕전실', parent_id=2) sort=2) path='001001002',
    #      Department(id=3, title='간호부', parent_id=1) sort=2) path='001002',
    #          Department(id=7, title='외래', parent_id=3) sort=1) path='001002001',
    #          Department(id=8, title='병동', parent_id=3) sort=2) path='001002002',
    #      Department(id=4, title='행정부', parent_id=1) sort=3) path='001003',
    #          Department(id=9, title='원무', parent_id=4) sort=1) path='001003001',
    #          Department(id=10, title='총무', parent_id=4) sort=2) path='001003002',

    # session.commit()  # 같은 데이터를 다시 불러와서 쓰기 위해. 세션 정리하기
    #
    # #### 일단 자신의 path부터 바꾸기 => parent의 path에서 덧칠
    # 진료부 = Department.get_by_name('진료부')
    # 간호부 = Department.get_by_name('간호부')
    #
    # ## 다른 세션에서 가져온 객체의 관계객체를 쓰려면 현재session에서 add해놓고 써야한다.
    # session.add_all(
    #     [진료부, 간호부]
    # )
    #
    # # .save()없이 일괄적으로 path를 자식포함 바꾸더라도, 내 sort는 먼저 바꿔놔야한다.
    # 진료부.sort = 1  # 1 -> 2
    # 간호부.sort = 2  # 2 -> 1
    # session.commit()
    # #      Department(id=2, title='진료부', parent_id=1) sort=2) path='001001',
    # #      Department(id=3, title='간호부', parent_id=1) sort=1) path='001002',
    #
    # # print(진료부.parent.path) # 001
    # # print(간호부.parent.path)  # 001
    # prefix = 진료부.parent.path if 진료부.parent else ''
    # after_진료부_path = prefix + f"{진료부.sort:0{진료부._N}d}"
    # prefix = 간호부.parent.path if 간호부.parent else ''
    # after_간호부_path = prefix + f"{간호부.sort:0{간호부._N}d}"
    # #      Department(id=3, title='간호부', parent_id=1) sort=1) path='001001',
    # #          Department(id=5, title='한방진료실', parent_id=2) sort=1) path='001001001',
    # #          Department(id=6, title='탕전실', parent_id=2) sort=2) path='001001002',
    # #      Department(id=2, title='진료부', parent_id=1) sort=2) path='001002',
    # #          Department(id=7, title='외래', parent_id=3) sort=1) path='001002001',
    # #          Department(id=8, title='병동', parent_id=3) sort=2) path='001002002',
    #
    # # #### => 자신은 부모path + 새sort => 새path를 만들었지만,  자식들은 path가 그대로라서,  <부모가 바뀌어버림>
    # # #### => 자식들을 tree로 조회한 뒤, 모든 자식들의 prefix(부모path)만 바꿔줘야한다.
    # # #### => 아니면 바뀌기 전의  내path + like를 써서, 모든 자식들을 골라낼 수도 있다. -> 내path만 검색도 하니, 나까지 포함된다.
    # # ####    모든 자식들을 순서, level상관없이 모두 부모path인 내path를 변경해야하는데, level에 따라 뒷자리path가 달라지니, 앞자리로 처리해야한다.
    # # ####  (1) 내path로 나포함 + 자식들을 다 데려온 뒤
    # # ####  (2) 내path ==  새로운sort로 수정한 뒤 +  부모path와 연결한다.
    # # ####  (3) offset1로 나를 뺀, 자식들은 부모path만 바뀌어야한다. 내path자체가 부모path의 길이이므로, 부모path 이후로의 자신의 path를 유지한 체, 부모path만 바뀐 내 path로 바꿔야한다.
    # stmt = (
    #     update(Department)
    #     .where(Department.path.like(진료부.path + '%'))
    #     .values({Department.path: after_진료부_path + func.substr(Department.path, len(after_진료부_path) + 1)})
    #         .execution_options(synchronize_session='fetch') # execute만 하는 update expression에 python메서드를 사용해서 업데이트하려면 필수옵션이다(안그럼 sql식에 이진수가 들어간 꼴)
    # )
    # session.execute(stmt)
    # session.commit()
    #
    # stmt2 = (
    #     update(Department)
    #     .where(Department.path.like(간호부.path + '%'))
    #     .values({Department.path: after_간호부_path + func.substr(Department.path, len(after_간호부_path) + 1)})
    #     .execution_options(synchronize_session='fetch')
    # )
    # session.execute(stmt2)
    # session.commit()
    # # print(stmt)
    # # for it in session.scalars(stmt):
    # #     print(it)
    # # print('*' * 30)
    #
    # #### root(병원장) 바꿔서 3level 다 바뀌는지 확인하기
    # stmt3 = (
    #     update(Department)
    #     .where(Department.path.like(병원장.path + '%'))
    #     .values({Department.path: '002' + func.substr(Department.path, len('002') + 1)})
    #     .execution_options(synchronize_session='fetch')
    # )
    # session.execute(stmt3)
    # session.commit()
    # # ******************************
    # #  Department(id=1, title='병원장', parent_id=None) sort=1) path='002',
    # #      Department(id=4, title='행정부', parent_id=1) sort=3) path='002003',
    # #          Department(id=9, title='원무', parent_id=4) sort=1) path='002003001',
    # #          Department(id=10, title='총무', parent_id=4) sort=2) path='002003002',
    # #      Department(id=2, title='진료부', parent_id=1) sort=7) path='002007',
    # #          Department(id=5, title='한방진료실', parent_id=2) sort=1) path='002007001',
    # #          Department(id=6, title='탕전실', parent_id=2) sort=2) path='002007002',
    # #      Department(id=3, title='간호부', parent_id=1) sort=8) path='002008',
    # #          Department(id=7, title='외래', parent_id=3) sort=1) path='002008001',
    # #          Department(id=8, title='병동', parent_id=3) sort=2) path='002008002',

    #### path로만 정렬하면, 각 부서마다 자식들을 sort순으로 다 출력하고 다음 것으로 넘어간다
    #### 특정 level의 부서들만 뽑아서 정렬할 땐 .sort로 정렬하자.

    #### sort변경은 1:1로 2개씩 한다.(직접 1개씩 주입하면 겹치게 되어 망함)
    #### 외부에서는 dep_id 2개가 주어지게 할 것이다.?
    #### 메서드화

    #
    # print('Department.change_sort_by_id(진료부.id, 간호부.id)')
    # print('*' * 30)
    # Department.change_sort_by_id(진료부.id, 간호부.id)
    # for it in Department.get_all():
    #     print(it.level * '    ', it)
    #
    # print('Department.change_sort_by_id(간호부.id, 행정부.id)')
    # print('*' * 30)
    # Department.change_sort_by_id(간호부.id, 행정부.id)
    # for it in Department.get_all():
    #     print(it.level * '    ', it)
    #
    # print('Department.change_sort_by_id(한방진료실.id, 탕전실.id)')
    # print('*' * 30)
    # Department.change_sort_by_id(한방진료실.id, 탕전실.id)
    # for it in Department.get_all():
    #     print(it.level * '    ', it)

    #### 나 + 자식들id를 누적하는 재귀
    print('*' * 30, '특정 부서의 (나 제외) 직후 1차 자식들만 조회 with parent(부모객체)', '*' * 30, )
    # (1) with_parent( 부모객체, 부모Entity.자식관계속성)  or   parent_id == 내id로  바로직후 자식들을 뽑아낸다.
    # => my) with_parent는 타entity를 부모(One)으로 할 때, 하위 entity들을 뽑아낼 때 좋을 것 같다.
    session.commit()
    진료부 = Department.get_by_name('진료부')
    session.add(진료부)
    stmt = (
        select(Department)
        .where(with_parent(진료부, Department.children))
        # 나의 자식들이 나오는데, 같은 level의 부서들이 나오므로 -> 정렬은 path순으로 하자.
        .order_by(Department.path)
    )
    # print(stmt)
    # SELECT departments.add_date, departments.pub_date, departments.id, departments.name, departments.parent_id, departments.status, departments.sort, departments.path, departments.type
    # FROM departments
    # WHERE :param_1 = departments.parent_id

    children_department = session.scalars(stmt).all()
    # [Department(id=2, title='진료부', parent_id=1) sort=3) path='002003',, Department(id=3, title='간호부', parent_id=1) sort=1) path='002001',, Department(id=4, title='행정부', parent_id=1) sort=2) path='002002',]

    # (2) 자기참조이며 같은세션이므로 .children 관계속성으로 뽑아낼 수 있다 대신, 조회순서를 관계속성에 order_by='entity.필드' 로 지정해준다.
    print(children_department)

    print('*' * 30, '메서드화', '*' * 30)
    print(f'진료부.get_children() => {진료부.get_children()}')


    # [Department(id=2, title='진료부', parent_id=1) sort=3) path='002003',, Department(id=3, title='간호부', parent_id=1) sort=1) path='002001',, Department(id=4, title='행정부', parent_id=1) sort=2) path='002002',]

    #  children = relationship('Department', backref=backref(
    #         'parent', remote_side=[id], lazy='subquery',
    #         cascade='all',  # 7
    #     ), order_by='Department.path') #  order_by="desc(CourseInstance.semester_sort_ix)",
    # print(진료부.children)
    # [Department(id=3, title='간호부', parent_id=1) sort=1) path='002001',, Department(id=4, title='행정부', parent_id=1) sort=2) path='002002',, Department(id=2, title='진료부', parent_id=1) sort=3) path='002003',]

    # (2) 재귀메서드안에서 자식들을 편하게 뽑아서 순회시킬 수 있도록 property로 정의한다 => 외부에서 하는게 아니라, 현재특정부서객체에서 호출해야하므로 cls method가 아닌 property로

    # (3) 자식부서들을 순회하며 자식부서가 부모역할을 하도록 메서드인자에 해당객체를 + 정보를 보관할 결과물을 인자 or 내부에 list를 만들어 모은다.
    # def get_child_departments(parent: Department, id_list: list):
    def get_self_and_children_id_list(parent: Department):
        # (3-1) 재귀를 돌며 누적시킬 것을 현재부터 뽑아낸다? => 첫 입력인자에 계속 누적시킬 거면, return없이 list에 그대로 append만 해주면 된다.
        result = [parent.id]
        # (3-1) 현재(부모)부서에서 자식들을 뽑아 순회시키며, id만 뽑아놓고, 이제 자신이 부모가 된다.
        # => 자신처리+중간누적을 반환하는 메서드라면, 재귀호출후 반환값을 부모의 누적자료구조에 추가누적해준다.
        # for child in parent.children:
        for child in parent.get_children():
            result += get_self_and_children_id_list(child)
        return result


    # print(get_self_and_children_id_list(진료부))
    # [2, 6, 5]

    # (4) 전체부서 - (나와 내자식들id를)로 제외시켜서, 수정form에 선택할 수 있는 부모부서로 나타내기
    # => 수정form에서 부모부서를 고를 때, 나와 내자식들을 제외한 부서들을 부모로 선택할 수 있다.
    departments = Department.get_all()
    selectable_parent_departments = [(x.id, x.name) for x in departments if
                                     x.id not in get_self_and_children_id_list(진료부)]
    print('*' * 30, '나와 내자식들 id 조회 (나 포함 재귀) -> 그것들을 제외한 부서들의 id, name선택 for 부서 수정시 선택 ', '*' * 30, )
    print(selectable_parent_departments)
    # [(1, '병원장'), (3, '간호부'), (7, '외래'), (8, '병동'), (4, '행정부'), (9, '원무'), (10, '총무')]

    print('*' * 30, '메서드화1: 나+나의자식들id list with 재귀', '*' * 30)
    print(f'진료부.get_self_and_children() => {진료부.get_self_and_children_id_list()}')
    print('*' * 30, '메서드화2: 나+나의자식들을 제외한 부서id, name list', '*' * 30)
    print(f'진료부.get_selectable_departments() => {진료부.get_selectable_departments()}')

    print('*' * 30, '나와 내 자식들 dict (자식은 "children" key) with lambda ', '*' * 30)
    print('*' * 30, ' => 바로 메서드화까지 ', '*' * 30)
    print(f'진료부.get_self_and_children_dict() => {진료부.get_self_and_children_dict()}')

    print('*' * 30, '현 부서의 직원 수 카운트', '*' * 30)
    # 부서정보에서, has/any로 타엔터티 기준을 현 부서로 걸어서, 그에 만족하는 수를 구한다.
    # => 통합정보에서는, many, 관계테이블에서 select하며 조건을 one테이블을 건다?!
    # stmt = (
    #     select(EmployeeDepartment)
    #     .where(EmployeeDepartment.dismissal_date.is_(None))
    #
    #     .where(EmployeeDepartment.department.has(Department.id == 한방진료실.id))
    # )

    # print(stmt)
    # SELECT employee_departments.add_date, employee_departments.pub_date, employee_departments.id, employee_departments.employee_id, employee_departments.department_id, employee_departments.employment_date, employee_departments.dismissal_date, employee_departments.position, employee_departments.is_leader
    # FROM employee_departments
    # WHERE employee_departments.dismissal_date IS NULL AND (EXISTS (SELECT 1
    # FROM departments
    # WHERE departments.id = employee_departments.department_id AND departments.id = :id_1))
    # current_dep_employees = session.scalars(stmt).all()
    # print([x.employee_id for x in current_dep_employees])
    # [EmployeeDepartment[id=2, title='123', parent_id='진료부']]
    stmt = (
        select(func.count(distinct(EmployeeDepartment.id)))  # 사람을 셀 때는 양적으로 세는지, 중복제외 세는지 distinct를 고려한다.
        .where(EmployeeDepartment.dismissal_date.is_(None))

        .where(EmployeeDepartment.department.has(Department.id == 한방진료실.id))
    )
    employee_count_in_dep = session.scalar(stmt)
    print(employee_count_in_dep)

    print('*' * 30, '메서드화', '*' * 30)
    print(f"한방진료실.count_employee() => {한방진료실.count_employee()}")
    print(f"병원장.count_employee() => {병원장.count_employee()}")

    print('*' * 30, '현 부서의 직원 수 대신 -> 자식들과 중복 검정을 위해 현 부서 소속의 직원_id 모으기 ', '*' * 30)
    print('*' * 30, '=> 바로 메서드화', '*' * 30)
    print(f"한방진료실.get_employee_id_list() => {한방진료실.get_employee_id_list()}")

    print('*' * 30, '현 부서 + 자식 부서 직원id list에 누적 for 중복제거시켜서 카운팅하려고 ', '*' * 30)
    print('*' * 30, '=> 바로 메서드화', '*' * 30)
    print(f"한방진료실.count_self_and_children_employee() => {한방진료실.get_self_and_children_id_list()}")
    print(f"간호부.count_self_and_children_employee() => {간호부.get_self_and_children_id_list()}")
    print(f"병원장.count_self_and_children_employee() => {병원장.get_self_and_children_id_list()}")

    print('*' * 30, '(직원 프로필용)현 부서 + 자식 부서 직원id list에서 중복제거하여 => 직원 수 count ', '*' * 30)
    print('*' * 30, '=> 바로 메서드화', '*' * 30)
    print(f"한방진료실.count_self_and_children_employee() => {한방진료실.count_self_and_children_employee()}")
    print(f"간호부.count_self_and_children_employee() => {간호부.count_self_and_children_employee()}")
    print(f"병원장.count_self_and_children_employee() => {병원장.count_self_and_children_employee()}")

    print('*' * 30, '(직원 프로필용2) => 상사 찾기 with 상위 재귀', '*' * 30)

    print('----바로 메서드화 current_user(g.user.id) => 직원 정보 가져오기 Employee.get_by_user_id', '*' * 30)
    print(f"Employee.get_by_user_id(current_user.id) => {Employee.get_by_user_id(current_user.id)}")

    직원_병원장: Employee = Employee.get_by_user_id(current_user.id)

    print('----바로 메서드화 직원의 소속부서들 가져오기=> User도 있는 Employee.get_my_departments', '*' * 30)
    print(f"직원_병원장.get_my_departments() => {직원_병원장.get_my_departments()}")

    print('----바로 메서드화 => 직원이 [주어진 부서(들) 중 1개 부서]에 대해 팀장인지 확인 => 직원.is_leader_in(부서)', '*' * 30)
    for dep in 직원_병원장.get_my_departments():
        print(f"{직원_병원장.name}.is_leader_in({dep.name}) => {직원_병원장.is_leader_in(dep)}")


    print('----바로 메서드화 => 해당부서 팀장 정보 조회  부서.get_leader()', '*' * 30)
    print(f"병원장.get_leader() => {병원장.get_leader()}")

    print('----바로 메서드화 => [재귀로 가장 가까운 팀장찾기] 해당부서 팀장을, 없으면 상위부서에서 팀장을, 상위부서가 없으면 None : 부서.get_leader_recursively(),  ', '*' * 30)

    print(f"행정부.get_leader_recursively() => {행정부.get_leader_recursively()}")
    print(f"진료부.get_leader_recursively() => {진료부.get_leader_recursively()}")
    print(f"병원장.get_leader_recursively() => {병원장.get_leader_recursively()}")

    print('----바로 메서드화 => 현 직원 => 현부서를 바탕으로 상사 찾기(내가 팀장인데 부모X -> None/내가 팀장인데 부모O -> 부모의 가까운팀장찾기 / 내가팀장X -> 가까운 팀장 찾기) , ', '*' * 30)
    print('---------현 직원이 부서가 있을 때만.. 작동해야한다. - if employee.get_my_departments()')#
    직원_부원장: Employee = Employee.get_by_user_role(Roles.STAFF)[0]
    # print(직원_부원장)
    print(f"직원_부원장.get_leader_or_senior_leader() => {직원_부원장.get_leader_or_senior_leader()}")
    직원_행정부장: Employee = Employee.get_by_user_id(2)
    print(f"직원_행정부장.get_leader_or_senior_leader() => {직원_행정부장.get_leader_or_senior_leader()}")
    print(f"직원_병원장.get_leader_or_senior_leader() => {직원_병원장.get_leader_or_senior_leader()}")
    직원_원무팀원: Employee = Employee.get_by_user_id(11)
    print(f"직원_원무팀원.get_leader_or_senior_leader() => {직원_원무팀원.get_leader_or_senior_leader()}")

    print('*' * 30, '직원의 (부서명, position) list 조회', '*' * 30)
    # 취임정보entity서 position을 가져오면 된다.
    # => 한 사람이 여러 부서를 가질 수 있으니, 부서별 / 취임정보position을 같이 가져온다
    # => 부서명을 가져오려면, join시켜야한다.
    stmt = (
        select(Department.name, EmployeeDepartment.position)
        .where(EmployeeDepartment.dismissal_date.is_(None))
        .where(EmployeeDepartment.employee_id == 직원_병원장.id)
        .join(EmployeeDepartment.department)
        .where(Department.status == 1)
    )
    print(session.execute(stmt).all())
    # [('병원장', '병원장'), ('진료부', '진료부장'), ('한방진료실', '대표원장')]
    print('*' * 30, '메서드화', '*' * 30)
    print(f"직원_병원장.get_dept_and_position_list() => {직원_병원장.get_dept_and_position_list()}")
    print(f"직원_부원장.get_dept_and_position_list() => {직원_부원장.get_dept_and_position_list()}")
    print(f"직원_행정부장.get_dept_and_position_list() => {직원_행정부장.get_dept_and_position_list()}")
    print(f"직원_원무팀원.get_dept_and_position_list() => {직원_원무팀원.get_dept_and_position_list()}")




    # 사용 직원 목록 :
    # 직원_병원장
    # 직원_부원장
    # 직원_행정부장
    # 직원_원무팀원
    # print('*' * 30, '모든 부서 조회')
    # for it in Department.get_all():
    #     print(it.level * '    ', it)
    # print('*' * 30)
    print('*' * 30, '모든 부서 조회 with 직원 수 + 부서장')
    for it in Department.get_all():
        print(it.level * '    ', '[', it.name, '] ', '부서장:', it.get_leader(), '직원 수:', it.count_employee(), '하위부서 모든 직원 수:',
              it.count_self_and_children_employee())
    print('*' * 30)






