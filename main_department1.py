import itertools

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func, distinct, and_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.orm import with_parent

from create_database import *
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
    # Employee.get_by_user_id('')
    # current_employee_id = 진료부장_취임.employee_id
    current_employee_id = EmployeeDepartment.get_by_dept_id(Department.get_by_name('진료부').id)[0].employee_id
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
    print(f'진료부.get_selectable_departments_for_edit() => {진료부.get_selectable_departments_for_edit()}')

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
    print(f"한방진료실.count_employee() => {한방진료실.employee_count()}")
    print(f"병원장.count_employee() => {병원장.employee_count()}")

    print('*' * 30, '현 부서의 직원 수 대신 -> 자식들과 중복 검정을 위해 현 부서 소속의 직원_id 모으기 ', '*' * 30)
    print('*' * 30, '=> 바로 메서드화', '*' * 30)
    print(f"한방진료실.get_employee_id_list() => {한방진료실.get_employee_id_list()}")

    print('*' * 30, '현 부서 + 자식 부서 직원id list에 누적 for 중복제거시켜서 카운팅하려고 ', '*' * 30)
    print('*' * 30, '=> 바로 메서드화', '*' * 30)
    print(f"한방진료실.count_self_and_children_employee() => {한방진료실.get_self_and_children_emp_id_list()}")
    print(f"간호부.count_self_and_children_employee() => {간호부.get_self_and_children_emp_id_list()}")
    print(f"병원장.count_self_and_children_employee() => {병원장.get_self_and_children_emp_id_list()}")

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
    print(f"병원장.get_leader() => {병원장.get_leader_id()}")

    print('----바로 메서드화 => [재귀로 가장 가까운 팀장찾기] 해당부서 팀장을, 없으면 상위부서에서 팀장을, 상위부서가 없으면 None : 부서.get_leader_recursively(),  ',
          '*' * 30)

    print(f"행정부.get_leader_id_recursively() => {행정부.get_leader_id_recursively()}")
    print(f"진료부.get_leader_id_recursively() => {진료부.get_leader_id_recursively()}")
    print(f"병원장.get_leader_id_recursively() => {병원장.get_leader_id_recursively()}")

    print(
        '----바로 메서드화 => 현 직원 => 현부서를 바탕으로 상사 찾기(내가 팀장인데 부모X -> None/내가 팀장인데 부모O -> 부모의 가까운팀장찾기 / 내가팀장X -> 가까운 팀장 찾기) , ',
        '*' * 30)
    print('---------현 직원이 부서가 있을 때만.. 작동해야한다. - if employee.get_my_departments()')  #
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
        .where(Department.status)
    )
    print(session.execute(stmt).all())
    # [('병원장', '병원장'), ('진료부', '진료부장'), ('한방진료실', '대표원장')]
    print('*' * 30, '메서드화', '*' * 30)
    print(f"직원_병원장.get_dept_id_and_name_and_position_list() => {직원_병원장.get_dept_id_and_name_and_position_list()}")
    print(f"직원_부원장.get_dept_id_and_name_and_position_list() => {직원_부원장.get_dept_id_and_name_and_position_list()}")
    print(f"직원_행정부장.get_dept_id_and_name_and_position_list() => {직원_행정부장.get_dept_id_and_name_and_position_list()}")
    print(f"직원_원무팀원.get_dept_id_and_name_and_position_list() => {직원_원무팀원.get_dept_id_and_name_and_position_list()}")

    print('*' * 30, '직원의 재직상태에 따른 마지막근무일(재직-today, 휴직-최종휴직일, 퇴사-퇴직일) 가져오기', '*' * 30)
    print('----', '=> 바로 메서드property 화 ', )
    직원_부원장: Employee = Employee.get_by_id(4)
    직원_병원장: Employee = Employee.get_by_id(8)
    퇴사자: Employee = Employee.get_by_id(2)
    print(f"재직상태:{직원_부원장.job_status} / 직원_부원장.last_working_date=>{직원_부원장.last_working_date}")
    print(f"재직상태:{직원_병원장.job_status} / 직원_병원장.last_working_date=>{직원_병원장.last_working_date}")
    print(f"재직상태:{퇴사자.job_status} / 직원_병원장.last_working_date=>{퇴사자.last_working_date}")

    print('*' * 30, '직원의 휴직(휴직~복직)정보가 있으면 가져오기', '*' * 30)
    # print(직원_부원장.id) # 12월16일 emp.id 4
    stmt = (
        select(EmployeeLeaveHistory)
        .where(EmployeeLeaveHistory.employee_id == 직원_부원장.id)  # 있따는 말은 이미 휴직/복직 set완성
        .order_by(EmployeeLeaveHistory.add_date)  # 시간순으로 가져오기
    )

    print(session.scalars(stmt).all())
    print('----', '메서드화 => emp.get_leave_history(self):', '-' * 30)
    print(f"직원_부원장.get_leave_history() => {직원_부원장.get_leave_histories()}")
    print(f"직원_병원장.get_leave_history() => {직원_병원장.get_leave_histories()}")
    일년중_맞춰서1달휴직: Employee = Employee.get_by_id(13)
    print(f"일년중_맞춰서1달휴직.get_leave_history() => {일년중_맞춰서1달휴직.get_leave_histories()}")

    print('*' * 30, '[계산] 직원의 입사일-last_working_date를 두고, 중간에 휴직history있으면 가져와서 구간만들기', '*' * 30)
    start_date = 직원_부원장.join_date
    end_date = 직원_부원장.last_working_date

    leave_histories = 직원_부원장.get_leave_histories()

    if not leave_histories:
        print(직원_부원장.calc_complete_month_and_days(start_date, end_date))
    else:
        # 13 입사,        15일 퇴사
        #   13일 휴직, 14일 복직
        # => 모아놓고 정렬하면 [13, 13, 14, 15] => 중복제거를 막하면 [13, 14, 15] 안됨
        # => 모아놓고 정렬하면 [13, 13, 14, 15 => 2개씩 잘라서 계산하고 누적해야한다
        #    [13, 13] = 0 , [14, 15] = 1 => 총 근무 1일
        ## 1) 일단 입사일, 마지막 근무일을 list에 모아놓고, 나머지 휴/복직일을 append해서 모아서 정렬한다
        # => 아니면 우선순위 큐? => (X) 1개씩 뽑는게 아니라 2개씩 pair로 뽑을 것이기 때문에
        # => 마지막에 1번 정렬하면 순서가 보장되기 때문에, 딱히 필요 없다.
        dates = [start_date, end_date]
        # => (휴직일, 복직일)의 tuple list를 평탄화 list로 만드는 방법은 2가지 : https://www.geeksforgeeks.org/python-convert-list-of-tuples-into-list/
        #    (1) list comp로 만든 tuple list => 다시 한번 list comp 돌기
        #      t_list =  [(x.leave_date, x.reinstatement_date ) for x in leave_histories ]
        #      _dates = [item for t in t_list for item in t]
        #    (2)  list comp로 만든 tuple list =>  chain(* tuple_list)로 넣고 list()화 하기
        dates += list(itertools.chain(*[(x.leave_date, x.reinstatement_date) for x in leave_histories]))
        dates = sorted(dates)


        ## 2) 입사-마지막근무일  +  휴직1-복직1 + 휴직2-복직2  형태로서 => 2개씩 짝 짓기
        ## 그룹짓기 방법: https://stackoverflow.com/questions/5389507/iterating-over-every-two-elements-in-a-list
        # 1) live_template에서, 길이//구간당갯수로 구간index를 만들어 처리
        # 2) 스택오버플로우에서 (1) iter()로 만든 뒤, zip( iter, iter )로 처리하면, 1개씩 준 것과 연결되어서 나온다
        #    => 만약 나누어 떨어지지 않는 경우, 일반zip을 쓰면 끊긴다
        #    => 이 때는, itertools.zip_longest()를 쓰면 된다.
        # print(dates)
        # iter_dates = iter(dates * 2)
        # for x in zip(iter_dates, iter_dates, iter_dates):
        #     print(x)
        #     # (datetime.date(2022, 12, 23), datetime.date(2023, 1, 13), datetime.date(2023, 1, 14))
        #     # (datetime.date(2023, 1, 14), datetime.date(2022, 12, 23), datetime.date(2023, 1, 13))
        #
        # iter_dates = iter(dates * 2)
        # for x in itertools.zip_longest(iter_dates, iter_dates, iter_dates):
        #     print(x)
        #     # (datetime.date(2022, 12, 23), datetime.date(2023, 1, 13), datetime.date(2023, 1, 14))
        #     # (datetime.date(2023, 1, 14), datetime.date(2022, 12, 23), datetime.date(2023, 1, 13))
        #     # (datetime.date(2023, 1, 14), datetime.date(2023, 1, 14), None)

        # print([x for x in grouped(dates, 2)])
        # [
        #     (datetime.date(2022, 12, 23), datetime.date(2023, 1, 13)),
        #     (datetime.date(2023, 1, 14), datetime.date(2023, 1, 14))
        # ]
        # print(grouped(dates, 3, strict=True)) # 나누어 떨어지지 않는 경우, ValueError
        # print([x for x in grouped(dates, 3)])
        # [
        #     (datetime.date(2022, 12, 23), datetime.date(2023, 1, 13), datetime.date(2023, 1, 14)),
        #     (datetime.date(2023, 1, 14), None, None)
        # ]

        #### 2개씩 짝지어진 근무기간을 계산하여 month만 누적하기 (days는 누적하면 안됨)
        def calc_complete_months(start_date, end_date):
            months = 0
            while end_date >= start_date + relativedelta(months=1):
                end_date -= relativedelta(months=1)
                months += 1
            return months


        total_complete_months = 0
        for srt, end in grouped(dates, 2):
            complete_months = calc_complete_months(srt, end)
            print(f"{srt}~{end}: 만근개월 수: {complete_months}")
            total_complete_months += complete_months
        print(total_complete_months)

    print('----', '메서드(property)화 => emp.complete_working_months_and_last_month_days(self):', '-' * 30)
    print(f"직원_부원장.complete_working_months_and_last_month_days => {직원_부원장.complete_working_months_and_last_month_days}")
    print(f"직원_병원장.complete_working_months_and_last_month_days => {직원_병원장.complete_working_months_and_last_month_days}")
    print(
        f"일년중_맞춰서1달휴직.complete_working_months_and_last_month_days => {일년중_맞춰서1달휴직.complete_working_months_and_last_month_days}")

    print('----', '메서드(property)화 => emp.vacations_with_description(self):', '-' * 30)
    print(f"직원_부원장.vacations_with_description => {직원_부원장.vacations_with_description}")
    print(f"직원_병원장.vacations_with_description => {직원_병원장.vacations_with_description}")
    print(f"일년중_맞춰서1달휴직.vacations_with_description => {일년중_맞춰서1달휴직.vacations_with_description}")

    print('*' * 30, '[직원추가] 팀장이라면, 자기부서 + 하위부서들의 id,name 정보 받아오기')
    # 1) form에 내가 팀장이 부서들의 id, name 나열하기
    my_departments_as_leader = 직원_부원장.get_my_departments(as_leader=True, as_min_level=True)
    if not my_departments_as_leader:
        print("팀장인 부서를 가진 직원만, 해당부서에 직원을 추가할 수 있습니다.")
    # my_departments_as_leader =직원_병원장.get_my_departments(as_leader=True)
    # dept_id_and_name_list = [(x.id, x.name) for x in my_departments_as_leader]
    # print(dept_id_and_name_list)
    # [(1, '병원장'), (2, '진료부'), (5, '한방진료실')]

    # => min_level로 찾고, 하위부서는 팀장이 아니여도 직원추가가 가능하도록
    my_min_level_departments_as_leader = 직원_병원장.get_my_departments(as_leader=True, as_min_level=True)
    if not my_min_level_departments_as_leader:
        print("팀장인 부서를 가진 직원만, 해당부서에 직원을 추가할 수 있습니다.")
    # print(my_min_level_departments_as_leader)
    # [Department(id=1, title='병원장', parent_id=None, sort=1, path='002')]
    # min_level_dept: Department = my_min_level_departments_as_leader[0]
    # min_level_dept.get_children()
    # print(min_level_dept)
    # print(min_level_dept.get_self_and_children_id_list())
    # [8, 10, 5, 16, 18, 19, 8, 8, 4, 16]
    #### min_level도 여러개 있을 수 있으니, 반복문을 돌려서 누적한다.
    #### + id만 모을게 아니라, name도 모아야하니 메서드를 또 하나 판다. => get_self_and_children_dept_info_tuple_list (id, name, level)
    #### => id, name를 모으는데, level별로 정렬되도록 level까지 보내준다.
    dept_id_and_name_list = []
    for min_dept in my_min_level_departments_as_leader:
        dept_id_and_name_list += min_dept.get_self_and_children_dept_info_tuple_list()

    # print(dept_id_and_name_list)
    # [(1, '병원장', 0), (3, '간호부', 1), (7, '외래', 2), (8, '병동', 2), (4, '행정부', 1), (9, '원무', 2), (10, '총무', 2), (2, '진료부', 1), (6, '탕전실', 2), (5, '한방진료실', 2)]
    #### level별로 정렬하고, level은 삭제한다.
    print([(x[0], x[1]) for x in sorted(dept_id_and_name_list, key=lambda x: x[2])])
    # [(1, '병원장'), (3, '간호부'), (4, '행정부'), (2, '진료부'), (7, '외래'), (8, '병동'), (9, '원무'), (10, '총무'), (6, '탕전실'), (5, '한방진료실')]

    # 2) route에서는, 선택된 부서_id, 선택된_직원_id + 부서장여부 + 취임일을 통해 [부서 취임]정보를 생성한다.
    십구번_취임 = EmployeeDepartment(
        department_id=dept_id_and_name_list[0][0],
        employee_id=19,
        employment_date=datetime.date.today(),
        # is_leader=True
    ).save()

    print('----', '메서드화 => 내가 팀장인 min_level부서들의 하위부서들을, 직원추가에 들어갈 부서list로 추출:', '-' * 30)
    print('----', 'get_dept_infos_for_add_staff()', '-' * 30)
    print(f"직원_부원장.get_dept_infos_for_add_staff => {직원_부원장.get_dept_infos_for_add_staff()}")
    print(f"직원_병원장.get_dept_infos_for_add_staff => {직원_병원장.get_dept_infos_for_add_staff()}")
    행정부장 = Employee.get_by_id(10)
    print(f"행정부장.get_dept_infos_for_add_staff => {행정부장.get_dept_infos_for_add_staff()}")
    관리자 = Employee.get_by_user_role(Roles.ADMINISTRATOR)[0]
    print(f"괸리자.get_dept_infos_for_add_staff => {관리자.get_dept_infos_for_add_staff()}")

    print('----', '직원추가될 직원들을, STAFF이상이면서,  나보다 하위 직책에서 받아오기(관리자/EXE/실장만 해당?)')
    stmt = (
        select(Employee, Role)
        # 관계필드가 아니라, .role은 프로퍼티라서 join조건에 못넣는다.
        #### Employee.role(프로퍼티).id == Role.id 로 할 시,  => 1로 고정되어버리는 현상. => 관계필드가 아니면 expression에 쓰지말자.
        .join(User, Employee.user)
        .join(Role,
              and_(User.role, Role.is_(Roles.STAFF), Role.is_under(행정부장.role)))  # 필터링용join entity의 조건은 join시 같이 걸자
        .where(Employee.job_status == 1)  # 재직중인 사람 들 중
        # .where(Role.is_under(행정부장.role)) # 자신의 role permission이 특정직원의 role permission보다 낮은 사람들만 => 필터링용join entity의 조건은 join시 같이 걸어도 된다.
        # 이미 다른 부서에 가입되어있어도 괜찮으니, 무소속을 걸러내진 않는다.
        # .where(~Employee.employee_departments.any())
    )
    # print(stmt)
    # print(session.scalars(stmt).all())
    # print(직원_부원장.role.name)
    # for emp in session.scalars(stmt).all():
    #     print(emp.name, emp.role.name)
    print(session.execute(stmt).all())
    # [(<Employee 4>, <Role 'STAFF'>), (<Employee 16>, <Role 'STAFF'>), (<Employee 19>, <Role 'STAFF'>), (<Employee 21>, <Role 'STAFF'>), (<Employee 22>, <Role 'STAFF'>)]

    print('----', '메서드화 => emp.get_under_role_employees( no_dept=False) or ( no_dept=True) ')
    print(f"({행정부장.role.name}) 행정부장.get_under_role_employees => {행정부장.get_under_role_employees()}")
    print(f"({직원_부원장.role.name}) 직원_부원장.get_under_role_employees => {직원_부원장.get_under_role_employees()}")
    print(f"({직원_병원장.role.name}) 직원_병원장.get_under_role_employees => {직원_병원장.get_under_role_employees()}")
    print(f"({관리자.role.name}) 관리자.get_under_role_employees => {관리자.get_under_role_employees()}")
    print(
        f"({관리자.role.name}) 관리자.get_under_role_employees(no_dept=True) => {관리자.get_under_role_employees(no_dept=True)}")

    # (CHIEFSTAFF) 행정부장.get_under_role_employees => [<Employee 4>, <Employee 16>, <Employee 19>, <Employee 21>, <Employee 22>]
    # (STAFF) 직원_부원장.get_under_role_employees => []
    # (CHIEFSTAFF) 직원_병원장.get_under_role_employees => [<Employee 4>, <Employee 16>, <Employee 19>, <Employee 21>, <Employee 22>]
    # (ADMINISTRATOR) 관리자.get_under_role_employees => [<Employee 4>, <Employee 8>, <Employee 10>, <Employee 11>, <Employee 12>, <Employee 16>, <Employee 19>, <Employee 21>, <Employee 22>]
    # (ADMINISTRATOR) 관리자.get_under_role_employees(no_dept=True) => [<Employee 11>, <Employee 12>, <Employee 22>]

    print('*' * 30, '[부서변경] 기존부서에 새부서취임일을 -> 해임일을 넣고나서 => 새 부서취임정보를 만들기', '*' * 30)
    #### 창에서 new_dept_id를 받고,  기존 dept_id로 처리를 먼저 해야한다.
    print('21번 직원을 부서정보가 없으면 []에 취임. [있으면 제일 마지막 부서]를 가져온다.')
    이십일번_직원: Employee = Employee.get_by_id(21)
    #### BUG FIX => get_my_departments하면, 해고일 들어간 취임정보도 나오고 있는 상황
    depts = 이십일번_직원.get_my_departments()
    #### BUG FIX => get_my_departments하면, 해고일 들어간 취임정보도 나오고 있는 상황

    print(f"21번 직원의 현재 부서 => {depts}")
    if not depts:
        print('21번 직원은 소속부서가 없어서 원무과에 배정합니다.')
        before_dept: Department = Department.get_by_name('원무')
        십구번_원무과_직원_취임 = EmployeeDepartment(employee=이십일번_직원, department=before_dept,
                                           employment_date=datetime.date(2023, 1, 15))
        십구번_원무과_직원_취임.save()
    else:
        print('21번 직원은 소속부서가 있고, 마지막 부서를 기존 부서에 배정합니다.')
        before_dept: Department = depts[-1]

    # 1) 현재 소속부서들이 여러개 있을 수 있다. 이 중에 1개를 before_dept로 form에서 선택
    # =>  after_dept는 기존에 만들어둔 현재 소속부서 제외 목록을 가져온다.
    print(f'기존 부서: {before_dept}')
    # 현재부서: Department(id=9, title='원무', parent_id=4, sort=1, path='002002001')
    print(f' [기존 + 기존의하위부서를 제외한] 변경가능 부서목록(get_selectable_departments_for_edit)')
    after_depts = before_dept.get_selectable_departments_for_edit()
    print(after_depts)
    # [(1, '병원장'), (3, '간호부'), (7, '외래'), (8, '병동'), (4, '행정부'), (10, '총무'), (2, '진료부'), (6, '탕전실'), (5, '한방진료실')]

    # 2) after_depts 중에 1개의 부서를 선택 + [취임일] 까지 선택해서 route로 넘어온다면,
    target_date = datetime.date(2023, 1, 18)
    #   2-1) before_dept + 선택된 emp_id의  부서취임정보에 [취임일]을 해임일로 입력
    # EmployeeDepartment.get_by_emp_id() => emp_id로만 검색하면 여러부서 취임정보가 나오므로 dept_id까지 포함해서 찾은 메서드를 추가해준다.

    before_emp_dept: EmployeeDepartment = EmployeeDepartment.get_by_emp_and_dept_id(이십일번_직원.id, before_dept.id)
    before_emp_dept.dismissal_date = target_date

    session.add(before_emp_dept)

    #   2-2) after_dept(id로 올 예정) + 선택된 emp_id로는 새 부서취임정보를 생성한다.
    print(f"after_dept는 가능한 부서목록중 가장 마지막으로 잡는다 => {after_depts[-1]}")
    after_dept_id = after_depts[-1][0]
    이십일번_직원_부서변경: EmployeeDepartment = EmployeeDepartment(employee=이십일번_직원, department_id=after_dept_id,
                                                          employment_date=target_date)

    # 3) after쪽으로 변경이 완료되어야, before의 해임일 지정도 commit()되도록 한다.
    # if 이십일번_직원_부서변경.save():
    #     print(f"부서변경 성공 => {before_dept.id} -> {after_dept_id}")
    #     session.commit()
    # return True, "부서 변경 성공 => {before_dept.id} -> {after_dept_id}"
    # else:
    #     print("부서변경 실패")
    #     session.rollback()
    # return False, "부서변경 실패
    result, message = 이십일번_직원_부서변경.save()
    if result:
        session.commit()
    else:
        session.rollback()

    print(message)

    print('----',
          '메서드화 => emp.change_department_with_promote_or_demote(십팔번_after_dept[0], target_date, before_dept_id=십팔번_before_dept_id, is_leader = is_leader)')
    ####  before는 self.에 1개 만 있는게 아니라 여러개 중 선택이므로, 인자로 받는다.
    십팔번_emp: Employee = Employee.get_by_id(18)
    #### before가 없을 수도 있으니 keyword로 변경한다.
    if 십팔번_emp.get_my_departments():
        십팔번_before_dept: Department = 십팔번_emp.get_my_departments()[-1]
        십팔번_before_dept_id = 십팔번_before_dept.id
        십팔번_after_dept: tuple = 십팔번_before_dept.get_selectable_departments_for_edit()[-1]
    else:
        십팔번_before_dept_id = None
        십팔번_after_dept: tuple = Department.get_all_tuple_list()[-1]
    target_date = datetime.date.today()
    #### 부서변경시, is_leader도 받아야하며, 그것에 의해 position이 결정된다.
    as_leader = True

    # print(
        # f"십팔번_emp.change_department_with_promote_or_demote(십팔번_after_dept[0], target_date, before_dept_id=십팔번_before_dept_id, as_leader=True) => "
        # f"{십팔번_emp.change_department_with_promote_or_demote(십팔번_after_dept[0], target_date, before_dept_id=십팔번_before_dept_id, as_leader=as_leader)}")
    #
    # 십팔번_emp: Employee = Employee.get_by_id(18)
    # #### before가 없을 수도 있으니 keyword로 변경한다.
    # if 십팔번_emp.get_my_departments():
    #     십팔번_before_dept: Department = 십팔번_emp.get_my_departments()[-1]
    #     십팔번_before_dept_id = 십팔번_before_dept.id
    #     십팔번_after_dept: tuple = 십팔번_before_dept.get_selectable_departments_for_edit()[-1]
    # else:
    #     십팔번_before_dept_id = None
    #     십팔번_after_dept: tuple = Department.get_all_tuple_list()[-1]
    # target_date = datetime.date.today()
    # #### 부서변경시, is_leader도 받아야하며, 그것에 의해 position이 결정된다.
    # as_leader = False
    # print(
    #     f"십팔번_emp.change_department_with_promote_or_demote(십팔번_after_dept[0], target_date, before_dept_id=십팔번_before_dept_id, is_leader = False) => "
    #     f"{십팔번_emp.change_department_with_promote_or_demote(십팔번_after_dept[0], target_date, before_dept_id=십팔번_before_dept_id, as_leader=as_leader)}")
    #
    # # print('----' , '메서드화 => 부서변경시 after_dept에 대한  position을 내려주는 메서드(dept객체.type(DepartmentType-enum))에서 호출 = get_positions(self, dep_name):')
    # # after_dept = Department.get_by_id(십팔번_after_dept[0])
    # # print(f"after_dept.type.get_positions(after_dept.name)=> {after_dept.type.get_positions(after_dept.name):}")
    # # after_dept.type.get_positions(after_dept.name)=> ('대표원장', '원장')
    #
    # print('----',
    #       '변수 추가 => get_my_departments(except_dept_id=) 변수 추가로 승진여부 확인시 관계필드role에 똑같은 Role이 안들어가도록 is_promote/is_demote확인용')
    # #### 부서처리 전에, 승진/강등 여부에 따라, role변경해주기
    # # -> 관계객체 .role 에 접근시 이미 해당데이터가 있기 때문에, STAFF 에  = STAFF를 찾아 할당하면 에러가 난다
    # # -> 외부에서 is_demote가 되려면 같은role의 STAFF가 아닐 때부터 처리해야한다.
    # #### 현재 CHIEFSTAFF이상인데 && [팀장인 부서가 없는 상태(온리 지금만 팀장이상)]일 때
    #
    # print(f"직원_병원장.get_my_departments(as_leader=True) => {직원_병원장.get_my_departments(as_leader=True)}")
    # print(
    #     f"직원_병원장.get_my_departments(as_leader=True, except_dept_id=1) => {직원_병원장.get_my_departments(as_leader=True, except_dept_id=1)}")
    #
    # print('----', '메서드화 => 부서변경 내부에서 emp.is_promote(), is_demote()로 승진(STAFF->CHIEF)/강등(CHIEF->STAFF) 상황인지 판단하는 메서드구현')
    # 십팔번_emp: Employee = Employee.get_by_id(18)
    # if 십팔번_emp.get_my_departments():
    #     십팔번_before_dept: Department = 십팔번_emp.get_my_departments()[-1]
    #     십팔번_before_dept_id = 십팔번_before_dept.id
    # #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & is_leader =True(최초 팀장으로 가면) => 승진
    # #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
    # print(십팔번_emp.get_my_departments())
    # print(f"십팔번_emp.is_promote(as_leader=False) => {십팔번_emp.is_promote(as_leader=False)}")
    # print(f"십팔번_emp.is_promote(as_leader=True) => {십팔번_emp.is_promote(as_leader=True)}")
    # #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & is_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
    # #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
    # print(
    #     f"십팔번_emp.is_demote(as_leader=True, current_dept_id=십팔번_before_dept_id) => {십팔번_emp.is_demote(as_leader=True, current_dept_id=십팔번_before_dept_id)}")
    # print(
    #     f"십팔번_emp.is_demote(as_leader=False, current_dept_id=십팔번_before_dept_id) => {십팔번_emp.is_demote(as_leader=False, current_dept_id=십팔번_before_dept_id)}")
    #
    # print('----', '부서가 없는 경우에도 승진이 적용되는지 테스트')
    # #### 부서없는 경우, 현재 팀장으로 소속된 부서가 없는 상황 & as_leader이므로 승진에 해당하게 된다.
    # 이십이_부서없는_emp: Employee = Employee.get_by_id(22)
    # print(f"이십이_부서없는_emp.is_promote(as_leader=False) => {이십이_부서없는_emp.is_promote(as_leader=False)}")
    # print(f"이십이_부서없는_emp.is_promote(as_leader=True) => {이십이_부서없는_emp.is_promote(as_leader=True)}")
    #
    # #### 애초에 소속모든부서(before) => 선택가능한 부서를 통합시켜서 받아오자.
    # #### 병원장 , 진료부장 => 병원장이면 모든 부서가 하위부서니 안된다. 진료부장이라면 상위부서+동기부서들은 가능하다
    # #### 제일 하위부서의 선택가능 목록에서, 자신의 부서들을 빼면 되려나? => 직원 - 부서변경 => 걍 개별부서별로 변경하도록 하자.
    # # https://stackoverflow.com/questions/45089840/how-to-create-dynamic-two-relational-dropdown-in-vuejs

    print('----', '부서변경은 완료함. emp.change_department(모든 정보) => 내부에서 is_promote, is_demote + role변경까지 다 진행하도록 변경')





    print('*' * 30, '[개별부서 정보] ', '*' * 30)
    dept_id = 5 # 간호부

    dept: Department = Department.get_by_id(dept_id)
    print(f"부서명:dept.name=>  {dept.name}")
    print(f"부서 레벨:dept.level=>  {dept.level}")
    print(f"부서 상태:dept.status=>  {dept.status}")
    print(f"부서 생성일:dept.add_date=>  {format_date(dept.add_date)}")

    print(f"부서장 id: dept.get_leader_id()=>  {dept.get_leader_id()}")
    print("-" * 4 * 1, f'부서장 id로 부서장 객체 찾기: Employee.get_by_id(dept.get_leader_id()) => {Employee.get_by_id(dept.get_leader_id())}')

    print(f"부서장 id(없을 경우, 상위부서장 id): 부서장이 없으면 부모 부서까지 탐색(재귀)끝까지 찾아보기: dept.get_leader_id_recursively()=>  {dept.get_leader_id_recursively()}")
    print("-" * 4 * 1,".get_leader_id()")
    print("-" * 4 * 1,
          f'부서장 없으면 상위 부서장 id 객체: Employee.get_by_id(dept.get_leader_id_recursively()) => {Employee.get_by_id(dept.get_leader_id_recursively())}')



    print(f"하위 모든 부서원 수: dept.count_self_and_children_employee()=>  {dept.count_self_and_children_employee()}")
    print("-"*4*1, "[재귀] .get_self_and_children_emp_id_list()")
    print("-"*4*2, ".get_employee_id_list() + .get_children()")

    print(f"부서원 수:dept.count_employee()=>  {dept.employee_count()}")
    print(f"부서장 제외 부서원 id 목록: dept.get_employee_id_list(except_leader=True)=>  {dept.get_employee_id_list(except_leader=True)}")
    print("-" * 4 * 1, f'부서원 id_list로 부서원들 객체 찾기: Employee.get_by_ids(dept.get_employee_ids(except_leader=True)) => {Employee.get_by_ids(dept.get_employee_id_list(except_leader=True))}')


    print(f"(new) 특정 직원의 특정 dept_id에 대한 position =>  emp.get_position_by_dept_id(dept.id)")
    print('-' * 4*1, "print( emp.name, emp.get_position_by_dept_id(dept.id) )")
    for emp in Employee.get_by_ids(dept.get_employee_id_list(except_leader=True)):
        print(emp.name, emp.get_position_by_dept_id(dept.id))

    # 부서 개별정보(부서+) <-> 부서관리(전체 부서) <-> 내 부서 정보(내가 속한 부서 정보)
    print('*' * 30, '직원의 [내 부서정보] (<-> 직원개인정보)] ', '*' * 30)
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
        print(it.level * '    ', '[', it.id,'-', it.name, '] ', '부서장:', Employee.get_by_id(it.get_leader_id()),
              '직원 수:', it.employee_count(),
              '하위부서 모든 직원 수:', it.count_self_and_children_employee())
    print('*' * 30)

