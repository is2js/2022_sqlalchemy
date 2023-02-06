모델과 사용

#### 1 pear-admin => tree사용하는 듯

- sort가 있다.
  - https://github.com/binicey/IMFactory-BIT/blob/c34693aa635d565a0c55180c86cd7f87a1a71a91/models/users.py

```python
class DepartmentModel(db.Model):
    __tablename__ = 'cp_dept'
    id = db.Column(db.Integer, primary_key=True, comment="部门ID")
    parent_id = db.Column(db.Integer, comment="父级编号")
    dept_name = db.Column(db.String(50), comment="部门名称")
    leader = db.Column(db.String(50), comment="负责人")
    phone = db.Column(db.String(20), comment="联系方式")
    email = db.Column(db.String(50), comment="邮箱")
    status = db.Column(db.Boolean, comment='状态(1开启,0关闭)')
    comment = db.Column(db.Text, comment="备注")
    address = db.Column(db.String(255), comment="详细地址")
    sort = db.Column(db.Integer, comment="排序")

    create_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

```

```python
class DepartmentsResource(Resource):

    def get(self):
        dept_data = DepartmentModel.query.order_by(DepartmentModel.sort).all()
        # TODO dtree 需要返回状态信息
        res = {
            "status": {"code": 200, "message": "默认"},
            "data": [
```



#### 2 **[Devachki](https://github.com/SidorovaVika/Devachki)**Public

- https://github.com/SidorovaVika/Devachki/blob/427c4b5dd7a7a39709862de7d088b7ecc655c807/project/models/departments.py#L3

- level칼럼

  ```python
  class Department(db.Model):
      __tablename__ = 'department'
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.VARCHAR(200), nullable=False)
      parent_id = db.Column(db.Integer, nullable=True)
      level = db.Column(db.Integer, nullable=False)
  ```

- **User와 M:N으로 구성하면서, **

  - **고용일/해고일이 명시되며**
  - `__table_args__`에 user_id를 제약조건으로 걸었다.

  ```python
  class User(db.Model):
      __tablename__ = 'user'
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.VARCHAR(200), nullable=False)
      surname = db.Column(db.VARCHAR(200), nullable=False)
      email = db.Column(db.VARCHAR(200), nullable=False, unique=True)
      phone = db.Column(db.VARCHAR(200), nullable=False)
      password = db.Column(db.VARCHAR(200), nullable=False)
  
      user_departments = db.relationship('UserDepartment')
  
      def get_role(self):
          return UserDepartment.query.filter(UserDepartment.user_id == self.id).filter(
              UserDepartment.dismissal_date == None).first().post
  ```

  ```python
  class UserDepartment(db.Model):
      __tablename__ = 'user_department'
      id = db.Column(db.Integer, primary_key=True)
      user_id = db.Column(db.Integer, nullable=False)
      department_id = db.Column(db.Integer, nullable=True)
      post=db.Column(db.VARCHAR(200), nullable=False)
      employment_date=db.Column(db.Date, nullable=True)
      dismissal_date=db.Column(db.Date, nullable=True)
      __table_args__ = (db.ForeignKeyConstraint(['user_id'], ['user.id'], name='users_tag_maps_department_id_fk'),)
  ```

  

- 메뉴를 csv로 만든다

  - cli.py

    ```python
    from project.app import create_app
    import click
    import csv
    from project.models.departments import Department
    from project.models import db
    from project.models.user import User
    from project.models.advisory_board import Advisor
    from project.models.user_department import UserDepartment
    from werkzeug.security import generate_password_hash
    import datetime
    import random
    
    app = create_app()
    
    
    @app.cli.command('create-departments')
    @click.argument('csvfile', nargs=1)
    def create(csvfile):
        db.session.add(Department(name="Федеральное отделение", parent_id=None, level=1))
        with open(csvfile, newline='') as csvfile:
            r = csv.reader(csvfile, delimiter=';')
            for row in r:
                if row[0] != "Региональное отделение":
                    if not (Department.query.filter(Department.name == row[0]).first()):
                        db.session.add(Department(name=row[0], parent_id=1, level=2))
                    db.session.add(
                        Department(name=row[2], parent_id=Department.query.filter(Department.name == row[0]).first().id,
                                   level=3))
        db.session.commit()
    
    
    @app.cli.command('clear-bd')
    def clear_bd():
        db.session.remove()
        db.drop_all()
        db.session.commit()
        db.create_all()
    
    
    @app.cli.command('create-users')
    @click.argument('csvfile', nargs=1)
    @click.argument('dep_id', nargs=1)
    def create_users(csvfile, dep_id):
        if not (User.query.filter(User.email == "important@mail.ru").first()):
            user = User(name="Главный", surname="Самый", email="important@mail.ru", phone="+79215729636",
                        password=generate_password_hash("1234"))
            db.session.add(user)
            db.session.commit()
            user_dep_id = UserDepartment(user_id=user.id, department_id=Department.query.filter(
                Department.name == "Московское").first().id, post="Руководитель Федерального Отделения",
                                         employment_date=datetime.date.today(), dismissal_date=None)
            db.session.add(user_dep_id)
            db.session.commit()
        with open(csvfile, newline='') as csvfile:
            r = csv.reader(csvfile, delimiter=';')
            for row in r:
                db.session.add(
                    User(name=row[1], surname=row[0], email=row[2], phone=row[3], password=generate_password_hash("1234")))
                db.session.commit()
                if row[4] == "":
                    row[4] = None
                if row[5] == "":
                    row[5] = None
                if len(row) > 6:
                    if row[6] == "":
                        row[6] = None
                    if row[7] == "":
                        row[7] = None
                db.session.add(
                    UserDepartment(user_id=User.query.filter(User.email == row[2]).first().id, department_id=int(dep_id),
                                   post="Пользователь", employment_date=row[4], dismissal_date=row[5]))
                db.session.commit()
    
    
    @app.cli.command('create-random-users')
    def create_random_users():
        if not (User.query.filter(User.email == "important@mail.ru").first()):
            user = User(name="Главный", surname="Самый", email="important@mail.ru", phone="+79215729636",
                        password=generate_password_hash("1234"))
            db.session.add(user)
            db.session.commit()
            user_dep_id = UserDepartment(user_id=user.id, department_id=Department.query.filter(
                Department.name == "Московское").first().id, post="Руководитель Федерального Отделения",
                                         employment_date=datetime.date.today(), dismissal_date=None)
            db.session.add(user_dep_id)
            db.session.commit()
        for i in range(20):
            print(i)
            with open('users/users_{}.csv'.format(i), newline='') as csvfile:
                r = csv.reader(csvfile, delimiter=';')
                for row in r:
                    if not (User.query.filter(User.email == row[2]).first()):
                        db.session.add(User(name=row[1], surname=row[0], email=row[2], phone=row[3],
                                            password=generate_password_hash("1234")))
                        db.session.commit()
                        loc_deps_id = [i.id for i in Department.query.filter(Department.level == 3).all()]
                        dep_id = random.choice(loc_deps_id)
                        if row[4] == "":
                            row[4] = None
                        if row[5] == "":
                            row[5] = None
                        if len(row) > 6:
                            if row[6] == "":
                                row[6] = None
                            if row[7] == "":
                                row[7] = None
                            db.session.add(Advisor(user_id=User.query.filter(User.email == row[2]).first().id,
                                                   department_id=dep_id,
                                                   employment_date=row[6], dismissal_rate=row[7]))
                            db.session.commit()
                            db.session.add(UserDepartment(user_id=User.query.filter(User.email == row[2]).first().id,
                                                          department_id=dep_id, post="Сотрудник",
                                                          employment_date=row[4], dismissal_date=row[5]))
                            db.session.commit()
                        else:
                            db.session.add(UserDepartment(user_id=User.query.filter(User.email == row[2]).first().id,
                                                          department_id=random.choice(loc_deps_id), post="Пользователь",
                                                          employment_date=row[4], dismissal_date=row[5]))
                            db.session.commit()
                        print('Успех')
    
    
    if __name__ == '__main__':
        app.cli()
    
    ```

    

  - department.csv

    ```python
    "Региональное отделение";"Сокращение";"Местное отделение"
    "Московское отделение";"МРО";"Юго-Западное"
    "Московское отделение";"МРО";"Северо-Восточное"
    "Московское отделение";"МРО";"Центральное"
    "Московское отделение";"МРО";"Северное"
    "Московское отделение";"МРО";"Южное"
    "Московское отделение";"МРО";"Восточное"
    "Московское отделение";"МРО";"Западное"
    "Московское отделение";"МРО";"Юго-Восточное"
    "Московское отделение";"МРО";"Северо-Западное"
    "Отделение Санкт-Петербург";"СПбРО";"Красногвардейское"
    "Отделение Санкт-Петербург";"СПбРО";"Московское"
    "Отделение Санкт-Петербург";"СПбРО";"Василеостровское"
    "Отделение Санкт-Петербург";"СПбРО";"Невское"
    "Отделение Санкт-Петербург";"СПбРО";"Адмиралтейское"
    "Отделение Санкт-Петербург";"СПбРО";"Приморское"
    "Отделение Санкт-Петербург";"СПбРО";"Кировское"
    "Отделение Санкт-Петербург";"СПбРО";"Калиниское"
    "Отделение Санкт-Петербург";"СПбРО";"Курортное"
    "Отделение Санкт-Петербург";"СПбРО";"Фрунзенское"
    "Отделение Санкт-Петербург";"СПбРО";"Пушкинское"
    "Отделение Санкт-Петербург";"СПбРО";"Петроградское"
    "Отделение Санкт-Петербург";"СПбРО";"Выборгское"
    "Московское областное отделение";"МОРО";"Волоколамское"
    "Московское областное отделение";"МОРО";"Егорьевское"
    "Московское областное отделение";"МОРО";"Клинское"
    "Московское областное отделение";"МОРО";"Раменское"
    "Тверское отделение";"ТРО";"Тверское"
    "Самарское отделение";"СамРО";"Правобережное"
    "Самарское отделение";"СамРО";"Левобережное"
    "Екатеринбургское";"ЕкРО";"Северное"
    "Екатеринбургское";"ЕкРО";"Южное"
    "Новосибирское";"НРО";"Дзержинское"
    "Новосибирское";"НРО";"Заельцовское"
    "Новосибирское";"НРО";"Центральное"
    "Новосибирское";"НРО";"Первомайское"
    
    ```

    



##### 사용 분석하기

###### 부서만들기 => 최상위부서(parent_id=None) + level = 1으로 직접 1개를 만들고, 그 이후로는 입력데이터를 조건문으 확인한 뒤, `parent_id 및 level`을 직접 지정해준다

- **최상위부서는 직접 `parent_id=None` + `level=1`으로 1개를 만든다**
- 그 이후로는 csv파일을 읽어서 **name이 존재하지 않을 경우, parent_id = , level=2부터 지정해서 만들어 add까지 해준다.**
- level3의 경우, **row[0]정보를 이름으로 검색 -> department객체.id를 부모id로 지정**한 뒤, 자신을 level3로 만든다

```python
@app.cli.command('create-departments')
@click.argument('csvfile', nargs=1)
def create(csvfile):
    db.session.add(Department(name="연방부서", parent_id=None, level=1))
    with open(csvfile, newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=';')
        for row in r:
            if row[0] != "지역부서":
                if not (Department.query.filter(Department.name == row[0]).first()):
                    db.session.add(Department(name=row[0], parent_id=1, level=2))
                db.session.add(
                    Department(name=row[2], parent_id=Department.query.filter(Department.name == row[0]).first().id,
                               level=3))
    db.session.commit()
```





###### Deparment는 아예 타엔터티와 관계가 없고 User <-> UserDepartment  ->관계만 가진다

```python
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(200), nullable=False)
    surname = db.Column(db.VARCHAR(200), nullable=False)
    email = db.Column(db.VARCHAR(200), nullable=False, unique=True)
    phone = db.Column(db.VARCHAR(200), nullable=False)
    password = db.Column(db.VARCHAR(200), nullable=False)

    user_departments = db.relationship('UserDepartment')

    def get_role(self):
        return UserDepartment.query.filter(UserDepartment.user_id == self.id).filter(
            UserDepartment.dismissal_date == None).first().post

```



```python
from project.models import db


class UserDepartment(db.Model):
    __tablename__ = 'user_department'
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, nullable=False)
    department_id = db.Column(db.Integer, nullable=True)

    post=db.Column(db.VARCHAR(200), nullable=False)
    employment_date=db.Column(db.Date, nullable=True)
    dismissal_date=db.Column(db.Date, nullable=True)

    __table_args__ = (db.ForeignKeyConstraint(['user_id'], ['user.id'], name='users_tag_maps_department_id_fk'),)

```



- User는 자신의 role(Post)를 UserDepartment에서 찾는다.

```python
    def get_role(self):
        return UserDepartment.query.filter(UserDepartment.user_id == self.id).filter(
            UserDepartment.dismissal_date == None).first().post
```



###### [직원추가] 현재User가 직원을 추가(User join UD로 users후보들 내려볼) 땐, User가 UD상의 역할에 따라 uses.join(ud)후 필터링시  찾는 부서 및 users수도 달라진다.  => 부모부서일 땐, .in_(자식부서id들)을 활용하면 될 듯.

- 현재유저id-> UD필터링으로  부서id -> 현부서의 parent부서 -> 그것의 자식부서 
  - **원래는 with_parent로 One(부모)에 속한 것들 다 뽑아낼 수 있지 않나?**

```python
class AddStaffView(View):
    def dispatch_request(self):
        user_id = current_user.get_id()
        loc_dep = UserDepartment.query.filter(UserDepartment.user_id == user_id).first().department_id
        reg_dep = Department.query.filter(Department.id == loc_dep).first().parent_id
        chil = Department.query.filter(Department.parent_id == reg_dep).all()
        chil_id = [i.id for i in chil]
```



- **현재유저의 부서상Role에 따라**

  - **`User엔터티에 UserDepartment를 join(Many를 붙여서, 부서있는 유저만 남음)`한 뒤  UD상의 role(퇴직일None필터링)**을 찾은 뒤 
  - 내가 부서에서 role을 가지고 있다면
  - role이 고급이면 -> `== 현재부서`를 UD에서 필터링해서 모든유저를
  - 더 고급이면 -> 현부서의 `parent부서의 모든 자식부서들`을 `.in_`으로 필터링해서 모든 유저들을
  - 더더 고급이면 -> 모든 부서의 User정보를 가져와 **직원 추가시 나타날 유저들을 반환해준다**

  

```python
        post = UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
            UserDepartment.dismissal_date == None).first().post
        if post == 'Руководитель Местного Отделения' or post == 'Заместитель Руководителя Местного Отделения':
            users = User.query.join(User.user_departments).filter(UserDepartment.post == "Пользователь").filter(
                UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.department_id == loc_dep).all()
        if post == 'Руководитель Регионального Отделения' or post == 'Заместитель Руководителя Регионального Отделения':
            users = User.query.join(User.user_departments).filter(UserDepartment.post == "Пользователь").filter(
                UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.department_id.in_(chil_id)).all()
        if post == 'Руководитель Федерального Отделения' or post == 'Заместитель Руководителя Федерального Отделения':
            users = User.query.join(User.user_departments).filter(UserDepartment.post == "Пользователь").filter(
                UserDepartment.dismissal_date.is_(None)).all()
        random.shuffle(users)
        return render_template('add_staff.html', users=users, user_id=user_id)

```





###### [부서변경] User가 관계상의 Department를 바꿀 때 - 관계정보가 있는 UserDepartment정보를 삭제하지말고, 관계종료시의 정보(퇴직일)를 넣어 update한 뒤, 새 관계정보를 넣어줘야 한다

- User가 관계있는 Department를 바꾼다면, 기존 User-Dempartment의 정보를 삭제하지말고 관계종료정보를 채워주고, User의 department를 바꿔준다?!

  - **나의 연결entity정보를 바꾸기 전에, `관계테이블 entity에서 나의 정보를 찾고 퇴직정보인 dismissal_date를 입력`해준다**
  - commit후에 **내 연결entity정보를 `새 department로 새로 UserDepartment 관계를 작성`**한다

  ```python
  if var == 'add_staff':
      
      UserDepartment.query.filter(
          UserDepartment.user_id == user_id).first().dismissal_date = datetime.date.today()
      db.session.commit()
      
      user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
          UserDepartment.user_id == user_id).first().department_id, post="Сотрудник",
                                   employment_date=datetime.date.today(), dismissal_date=None)
      db.session.add(user_dep_id)
      db.session.commit()
      
      #users = User.query.join(User.user_departments).filter(UserDepartment.post == "Пользователь").filter(
          UserDepartment.dismissal_date.is_(None)).all()
      #user_id = current_user.get_id()
      flash("Успешно")
      return redirect(url_for('add_staff'))
  ```

  

###### [직원제거] 기존 회사정보를 퇴직정보로 바꾸고, 퇴직정보의 퇴직부서로  무직자 role로 정보를 등록한다?

- **해당user의 직원정보는 UserDepartment에서 user_id로 조회**해야한다. **department는 단순히 정보성 one entity로 생각**하자

  - **유효한 직원정보는 `dismissal_date.is_(None)`을 필터를 걸면 된다.**
    - 직원정보가 폐기되면, 저것을 채우니까
  - 유효한 직원정보가 없으면, 직원제거가 안되므로 돌아간다

- 내 **기존 유효한 & 직원정보를 퇴직시키고 commit**한다

- 퇴직정보를 조회해서, 거기서, **퇴직한 department_id**를 바탕으로 **새 UserDepartment를 `무직자?`로 만들어준다?**

  

```python
        if var == 'dis_staff':
            if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                    UserDepartment.dismissal_date == None).first().post == "Пользователь":
                flash("Данный пользователь не является сотрудником")
            else:
                UserDepartment.query.filter(
                    UserDepartment.user_id == user_id).filter(
                    UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                db.session.commit()
                
                user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                    UserDepartment.user_id == user_id).first().department_id, post="Пользователь",
                                             employment_date=datetime.date.today(), dismissal_date=None)
                db.session.add(user_dep_id)
                db.session.commit()
                advis = Advisor.query.filter(
                    Advisor.user_id == user_id,
                    Advisor.dismissal_date == None).all()
                if advis:
                    for ad in advis:
                        ad.dismissal_date = datetime.date.today()
                db.session.commit()
                flash("Успешно")
```





###### [승진인가?] 현재 부서정보를 퇴직시키고, 퇴직부서정보의 부서id로 + role을 고용인으로 새로 정보를 만든다.

```python
        if var == 'staff':
            if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                    UserDepartment.dismissal_date == None).first().post == "Сотрудник":
                flash("Данный сотрудник уже на этой должности")
            else:
                UserDepartment.query.filter(
                    UserDepartment.user_id == user_id).filter(
                    UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                db.session.commit()
                user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                    UserDepartment.user_id == user_id).first().department_id, post="Сотрудник",
                                             employment_date=datetime.date.today(), dismissal_date=None)
                db.session.add(user_dep_id)
                db.session.commit()
                flash("Успешно")

        return redirect(url_for('user', user_id=user_id))
```







- 잘모르겠지만 일단 가져오기

  - changeView.py

    ```python
    from flask.views import View
    from flask import render_template, request, redirect, url_for, flash
    from project.models.user import User
    from flask_login import current_user
    from project.models.advisory_board import Advisor
    from project.models.user_department import UserDepartment
    from project.models.departments import Department
    import datetime
    from project.models import db
    
    
    class ChangeView(View):
    
        def dispatch_request(self, user_id, var):
            user = User.query.filter(User.id == current_user.get_id()).first()
            role=UserDepartment.query.filter(UserDepartment.user_id==user.id,UserDepartment.dismissal_date == None).first().post
            user_loc_dep = UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                UserDepartment.dismissal_date == None).first().department_id
            user_reg_dep = Department.query.filter(Department.id == user_loc_dep).first().parent_id
            chil = Department.query.filter(Department.parent_id == user_reg_dep).all()
            chil_id = [i.id for i in chil]
            if role == "Руководитель Федерального Отделения":
                main_dep_id = 1
            if role == "Руководитель Регионального Отделения":
                main_dep_id = Department.query.filter(Department.id == UserDepartment.query.filter(
                    UserDepartment.user_id == user.id).first().department_id).first().parent_id
            if role == "Руководитель Местного Отделения":
                main_dep_id = UserDepartment.query.filter(UserDepartment.user_id == user.id).first().department_id
    
            if var == 'add_staff':
                UserDepartment.query.filter(
                    UserDepartment.user_id == user_id).first().dismissal_date = datetime.date.today()
                db.session.commit()
                user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                    UserDepartment.user_id == user_id).first().department_id, post="Сотрудник",
                                             employment_date=datetime.date.today(), dismissal_date=None)
                db.session.add(user_dep_id)
                db.session.commit()
                users = User.query.join(User.user_departments).filter(UserDepartment.post == "Пользователь").filter(
                    UserDepartment.dismissal_date.is_(None)).all()
                user_id = current_user.get_id()
                flash("Успешно")
                return redirect(url_for('add_staff'))
    
            if var == 'advisor':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id,
                                               UserDepartment.dismissal_date == None).first().post == "Пользователь":
                    flash("Данный пользователь не является сотрудником")
                else:
                    advis = Advisor(user_id=user_id, department_id=main_dep_id,
                                    employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(advis)
                    db.session.commit()
                    flash("Успешно")
    
            if var == 'dis_advisor':
                Advisor.query.filter(
                    Advisor.user_id == user_id).filter(
                    Advisor.dismissal_date == None).filter(
                    Advisor.department_id == main_dep_id).first().dismissal_date = datetime.date.today()
                db.session.commit()
                flash("Успешно")
    
            if var == 'add_federal_zam':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Заместитель Руководителя Федерального Отделения":
                    flash("Данный сотрудник уже на этой должности")
                elif len(UserDepartment.query.filter(
                        UserDepartment.post == "Заместитель Руководителя Федерального Отделения").filter(
                    UserDepartment.dismissal_date == None).all()) < 3:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id,
                                                 post="Заместитель Руководителя Федерального Отделения",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    flash("Успешно")
                else:
                    flash("Данная вакансия недоступна")
    
            if var == 'add_regional_director':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Руководитель Регионального Отделения":
                    flash("Данный сотрудник уже на этой должности")
                elif UserDepartment.query.filter(
                        UserDepartment.post == "Руководитель Регионального Отделения").filter(
                    UserDepartment.department_id.in_(chil_id)).filter(
                    UserDepartment.dismissal_date == None).first():
                    flash("Данная вакансия недоступна")
                else:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id,
                                                 post="Руководитель Регионального Отделения",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    flash("Успешно")
    
            if var == 'add_regional_zam':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Заместитель Руководителя Регионального Отделения":
                    flash("Данный сотрудник уже на этой должности")
                elif len(UserDepartment.query.filter(
                        UserDepartment.post == "Заместитель Руководителя Регионального Отделения").filter(
                    UserDepartment.department_id.in_(chil_id)).filter(UserDepartment.dismissal_date == None).all()) < 3:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id,
                                                 post="Заместитель Руководителя Регионального Отделения",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    flash("Успешно")
                else:
                    flash("Данная вакансия недоступна")
    
            if var == 'add_local_director':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Руководитель Местного Отделения":
                    flash("Данный сотрудник уже на этой должности")
                elif UserDepartment.query.filter(
                        UserDepartment.post == "Руководитель Местного Отделения").filter(
                    UserDepartment.department_id == user_loc_dep).filter(
                    UserDepartment.dismissal_date == None).first():
                    flash("Данная вакансия недоступна")
                else:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id, post="Руководитель Местного Отделения",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    flash("Успешно")
    
            if var == 'add_local_zam':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Заместитель Руководителя Местного Отделения":
                    flash("Данный сотрудник уже на этой должности")
                elif len(UserDepartment.query.filter(
                        UserDepartment.post == "Заместитель Руководителя Местного Отделения").filter(
                    UserDepartment.department_id == user_loc_dep).filter(
                    UserDepartment.dismissal_date == None).all()) < 3:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id,
                                                 post="Заместитель Руководителя Местного Отделения",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    flash("Успешно")
                else:
                    flash("Данная вакансия недоступна")
    
            if var == 'dis_staff':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Пользователь":
                    flash("Данный пользователь не является сотрудником")
                else:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id, post="Пользователь",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    advis = Advisor.query.filter(
                        Advisor.user_id == user_id,
                        Advisor.dismissal_date == None).all()
                    if advis:
                        for ad in advis:
                            ad.dismissal_date = datetime.date.today()
                    db.session.commit()
                    flash("Успешно")
    
            if var == 'staff':
                if UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().post == "Сотрудник":
                    flash("Данный сотрудник уже на этой должности")
                else:
                    UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).filter(
                        UserDepartment.dismissal_date == None).first().dismissal_date = datetime.date.today()
                    db.session.commit()
                    user_dep_id = UserDepartment(user_id=user_id, department_id=UserDepartment.query.filter(
                        UserDepartment.user_id == user_id).first().department_id, post="Сотрудник",
                                                 employment_date=datetime.date.today(), dismissal_date=None)
                    db.session.add(user_dep_id)
                    db.session.commit()
                    flash("Успешно")
    
            return redirect(url_for('user', user_id=user_id))
    
    ```

  - FederalView

    ```python
    from flask.views import View
    from flask import render_template
    from project.models.departments import Department
    from flask_login import current_user
    from project.models.user_department import UserDepartment
    from project.models.user import User
    from project.models.advisory_board import Advisor
    
    
    class FederalView(View):
        def dispatch_request(self, dep_id):
            dep = Department.query.filter(Department.id == dep_id).first()
            chil = Department.query.filter(Department.parent_id == dep_id).all()
            chil_id = []
            chil_chil = []
            for i in chil:
                children = Department.query.filter(Department.parent_id == i.id).all()
                chil_id.append([j.id for j in children])
            for i in range(len(chil_id)):
                chil_chil.append([])
                for j in chil_id[i]:
                    chil_chil[i].append(
                        len(User.query.join(User.user_departments).filter(UserDepartment.department_id == j).filter(
                            UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post != "Пользователь").all()))
            for i in range(len(chil_chil)):
                chil_chil[i] = sum(chil_chil[i])
            director = User.query.join(User.user_departments).filter(
                UserDepartment.post == "Руководитель Федерального Отделения").filter(
                UserDepartment.dismissal_date.is_(None)).first()
            fed_zam = User.query.join(User.user_departments).filter(
                UserDepartment.dismissal_date.is_(None)).filter(
                UserDepartment.post == "Заместитель Руководителя Федерального Отделения").all()
            advis_id = [i.user_id for i in
                        Advisor.query.filter(Advisor.department_id == dep_id).filter(Advisor.dismissal_date == None).all()]
            advisors = User.query.filter(User.id.in_(advis_id)).all()
            return render_template('federal.html', chil=chil, user_id=current_user.get_id(), dep=dep, chil_chil=chil_chil,
                                   director=director, fed_zam=fed_zam, advisors=advisors)
    
    ```

- localview

  ```python
  from flask.views import View
  from flask import render_template, request
  from project.models.user import User
  from flask_login import current_user
  from project.models.user_department import UserDepartment
  from project.models.departments import Department
  from project.models.advisory_board import Advisor
  
  
  class LocalView(View):
      def dispatch_request(self, dep_id):
          dep=Department.query.filter(Department.id==dep_id).first()
          staff = User.query.join(User.user_departments).filter(UserDepartment.department_id==dep_id).filter(UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post!="Пользователь").filter(UserDepartment.post!="Руководитель Местного Отделения").filter(UserDepartment.post!="Заместитель Руководителя Местного Отделения").all()
          parent=Department.query.filter(Department.id==dep.parent_id).first()
          user_id=current_user.get_id()
          loc_dir=User.query.join(User.user_departments).filter(UserDepartment.department_id==dep_id).filter(UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post=="Руководитель Местного Отделения").first()
          loc_zam=User.query.join(User.user_departments).filter(UserDepartment.department_id==dep_id).filter(UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post=="Заместитель Руководителя Местного Отделения").all()
          advis_id=[i.user_id for i in Advisor.query.filter(Advisor.department_id==dep_id).filter(Advisor.dismissal_date==None).all()]
          advisors=User.query.filter(User.id.in_(advis_id)).all()
          return render_template('local.html',user_id=user_id,staff=staff,parent=parent,dep=dep,loc_dir=loc_dir,loc_zam=loc_zam,advisors=advisors)
  ```

- regional view

  ```python
  from flask.views import View
  from flask import render_template
  from project.models.departments import Department
  from flask_login import current_user
  from project.models.user import User
  from project.models.user_department import UserDepartment
  from sqlalchemy import func
  from project.models import db
  from project.models.advisory_board import Advisor
  
  
  class RegionalView(View):
      def dispatch_request(self, dep_id):
          dep = Department.query.filter(Department.id == dep_id).first()
          chil = Department.query.filter(Department.parent_id == dep_id).all()
          count_users = db.session.query(
              UserDepartment.department_id,
              func.count('*').label('c_count')
          ).filter(
              UserDepartment.department_id.in_([i.id for i in chil])
          ).filter(
              UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post != "Пользователь").group_by(
              UserDepartment.department_id).all()
          count_users = dict(count_users)
          parent = Department.query.filter(Department.id == dep.parent_id).first()
          reg_dir = User.query.join(User.user_departments).filter(
              UserDepartment.department_id.in_([i.id for i in chil])).filter(
              UserDepartment.dismissal_date.is_(None)).filter(
              UserDepartment.post == "Руководитель Регионального Отделения").first()
          reg_zam = User.query.join(User.user_departments).filter(
              UserDepartment.department_id.in_([i.id for i in chil])).filter(
              UserDepartment.dismissal_date.is_(None)).filter(
              UserDepartment.post == "Заместитель Руководителя Регионального Отделения").all()
          advis_id = [i.user_id for i in
                      Advisor.query.filter(Advisor.department_id == dep_id).filter(Advisor.dismissal_date == None).all()]
          advisors = User.query.filter(User.id.in_(advis_id)).all()
          return render_template('regional.html', chil=chil, parent=parent, user_id=current_user.get_id(), dep=dep,
                                 count_users=count_users, reg_dir=reg_dir, reg_zam=reg_zam, advisors=advisors)
  
  ```

  

- user_view.py

  ```python
  from flask.views import View
  from flask import render_template
  from flask_login import current_user
  from project.models.user import User
  from project.models.advisory_board import Advisor
  from project.models.departments import Department
  from project.models.user_department import UserDepartment
  
  
  class UserView(View):
      def dispatch_request(self, user_id):
          main_dep_id=None
          actions = {
              'add_federal_zam': (
                  'Назначить заместителем руководителя федерального отделения', ['Руководитель Федерального Отделения']),
              'add_regional_director': (
                  'Назначить руководителем регионального отделения',
                  ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения']),
              'add_regional_zam': (
                  'Назначить заместителем руководителя регионального отделения',
                  ['Руководитель Регионального Отделения']),
              'add_local_director': (
                  'Назначить руководителем местного отделения',
                  ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения',
                   'Руководитель Регионального Отделения', 'Заместитель Руководителя Регионального Отделения']),
              'add_local_zam': (
                  'Назначить заместителем руководителя местного отделения', ['Руководитель Местного Отделения']),
              'staff': (
                  'Назначить сотрудником местного отделения',
                  ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения',
                   'Руководитель Регионального Отделения', 'Заместитель Руководителя Регионального Отделения',
                   'Руководитель Местного Отделения', 'Заместитель Руководителя Местного Отделения']),
              'dis_staff': (
                  'Уволить',
                  ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения',
                   'Руководитель Регионального Отделения', 'Заместитель Руководителя Регионального Отделения',
                   'Руководитель Местного Отделения', 'Заместитель Руководителя Местного Отделения'])
          }
          user = User.query.filter(User.id == user_id).first()
          if not (current_user.is_authenticated):
              return render_template('user.html', user=user)
  
          user_posts = UserDepartment.query.filter(UserDepartment.user_id == user_id).all()
          dep_id = UserDepartment.query.filter(UserDepartment.user_id == user.id).first().department_id
          dep = Department.query.filter(Department.id == dep_id).first()
          user_regional_dep_id = dep.parent_id
          cur_user_id = int(current_user.get_id())
          our_dep_id = UserDepartment.query.filter(UserDepartment.user_id == cur_user_id).first().department_id
          our_dep = Department.query.filter(Department.id == our_dep_id).first()
          our_regional_dep_id = our_dep.parent_id
          post = UserDepartment.query.filter(UserDepartment.user_id == cur_user_id).filter(
              UserDepartment.dismissal_date == None).first().post
          opportunities = []
          for i in actions:
              if post in actions[i][1]:
                  opportunities.append(i)
          regional_indic = user_regional_dep_id == our_regional_dep_id
          local_indic = dep_id == our_dep_id
          dis_indic = False
          user_post = UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
              UserDepartment.dismissal_date == None).first().post
  
          if post == 'Руководитель Федерального Отделения':
              if user_post == 'Заместитель Руководителя Федерального Отделения' or user_post == 'Руководитель Регионального Отделения' or user_post == 'Заместитель Руководителя Регионального Отделения' or user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                  dis_indic = True
  
          if post == 'Заместитель Руководителя Федерального Отделения':
              if user_post == 'Руководитель Регионального Отделения' or user_post == 'Заместитель Руководителя Регионального Отделения' or user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                  dis_indic = True
  
          if post == 'Руководитель Регионального Отделения':
              if regional_indic:
                  if user_post == 'Заместитель Руководителя Регионального Отделения' or user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                      dis_indic = True
  
          if post == 'Заместитель Руководителя Регионального Отделения':
              if regional_indic:
                  if user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                      dis_indic = True
  
          if post == 'Руководитель Местного Отделения':
              if local_indic:
                  if user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                      dis_indic = True
  
          if post == 'Заместитель Руководителя Местного Отделения':
              if local_indic:
                  if user_post == 'Сотрудник' or user_post == 'Пользователь':
                      dis_indic = True
  
          if post == "Руководитель Федерального Отделения":
              main_dep_id = 1
          if post == "Руководитель Регионального Отделения":
              main_dep_id = Department.query.filter(Department.id == UserDepartment.query.filter(
                  UserDepartment.user_id == user.id).first().department_id).first().parent_id
          if post == "Руководитель Местного Отделения":
              main_dep_id = UserDepartment.query.filter(UserDepartment.user_id == user.id).first().department_id
  
          advisor_indic = Advisor.query.filter(Advisor.user_id == user_id).filter(Advisor.dismissal_date == None).filter(
              Advisor.department_id == main_dep_id).first()
  
          return render_template('user.html', user=user, dep=dep, cur_user_id=cur_user_id, local_indic=local_indic,
                                 opportunities=opportunities, actions=actions, regional_indic=regional_indic, post=post,
                                 dis_indic=dis_indic, user_posts=user_posts, advisor_indic=advisor_indic)
  ```

  





###### [FederalView = 현재부서 하위정보 다같이 보기] 특정부서 정보보기? 재귀없이 자식부서 + 자식부서의 직원수까지만 하위부서 모으기

1. 현재부서를 찾는다

2. 현재부서의 자식부서들을 찾는다

3. 자식부서들의 id만 모은다

4. 자식부서id들을 순회하면서, 

   1. User에다가 UserDepartment부서정보를 join후 **현재i번재 자식부서의 User들을 조회하여 len()으로 그 숫자만 append한다**

5. **자식부서들의 직원수를 만 sum한다?**

6. view로는 현재부서 + **자식부서들 + 자식의 하위총직원수**를 각각 던져준다

   ```python
   class FederalView(View):
       def dispatch_request(self, dep_id):
           dep = Department.query.filter(Department.id == dep_id).first()
           chil = Department.query.filter(Department.parent_id == dep_id).all()
           chil_id = []
           chil_chil = []
           for i in chil:
               children = Department.query.filter(Department.parent_id == i.id).all()
               chil_id.append([j.id for j in children])
           for i in range(len(chil_id)):
               chil_chil.append([])
               for j in chil_id[i]:
                   chil_chil[i].append(
                       len(User.query.join(User.user_departments).filter(UserDepartment.department_id == j).filter(
                           UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post != "Пользователь").all()))
           for i in range(len(chil_chil)):
               chil_chil[i] = sum(chil_chil[i])
           director = User.query.join(User.user_departments).filter(
               UserDepartment.post == "Руководитель Федерального Отделения").filter(
               UserDepartment.dismissal_date.is_(None)).first()
           fed_zam = User.query.join(User.user_departments).filter(
               UserDepartment.dismissal_date.is_(None)).filter(
               UserDepartment.post == "Заместитель Руководителя Федерального Отделения").all()
           advis_id = [i.user_id for i in
                       Advisor.query.filter(Advisor.department_id == dep_id).filter(Advisor.dismissal_date == None).all()]
           advisors = User.query.filter(User.id.in_(advis_id)).all()
           return render_template('federal.html', chil=chil, user_id=current_user.get_id(), dep=dep, chil_chil=chil_chil,
                                  director=director, fed_zam=fed_zam, advisors=advisors)
   
   ```

   

- view에서는 자식부서들을 순회하며 반복문으로 뿌려준다
  - federal.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Федеральное отделение</title>
</head>
<body>
<h1>{{dep.name}}</h1>
<big>
{% if current_user.is_authenticated %}
    {% if director %}
    <p>Руководитель: <a href="{{url_for('user',user_id=director.id)}}">{{director.name}} {{director.surname}}</a></p>
    <p>Телефон: {{ director.phone }}</p>
    <p>E-mail: {{ director.email }}</p>
    {% endif %}
    {% if fed_zam %}
        <p>Заместители руководителя:</p>
        {% for zam in fed_zam %}
        <a href="{{url_for('user',user_id=zam.id)}}">{{zam.name}} {{zam.surname}}</a><br><br>
        {% endfor %}
    {% endif %}
    {% if advisors %}
        <p>Консультационный совет:</p>
        {% for advis in advisors %}
            <a href="{{url_for('user',user_id=advis.id)}}">{{advis.name}} {{advis.surname}}</a><br><br>
        {% endfor %}
    {% endif %}
    <p>Список отделений (количество сотрудников):</p>
    {% for i in range(chi	l|length) %}

            <p><a href="{{url_for('regional',dep_id=chil[i].id)}}">{{chil[i].name}}</a>
                {% if chil_chil[i] %}
                {{chil_chil[i]}}
                {% else %}
                    Нет сотрудников
                {% endif %}
            </p>
    {% endfor %}
    <form action="{{url_for('user',user_id=user_id)}}">
        <button type="submit">Моя страница</button>
    </form>
    <br>
    <form action="/logout">
        <button type="submit">Выйти</button>
    </form>
{% else %}
    <p>Просмотр страницы доступен только сотрудникам</p>
    <form action="/login">
        <button>Войти</button>
    </form>
    <form action="/signup">
        <button>Зарегистрироваться</button>
    </form>
{% endif %}
</big>
</body>
</html>
```



###### [개별 부서 정보 + html][LocalView = 로그인메뉴에 띄우는 부서1개 정보] 재귀없이 선택된부서의 직원들 + 팀장 + 부모부서 찾기

1. dep_id로 해당 **부서객체**를 찾는다
2. dep_id로 User + UserDerpatment join + dep_id로 필터링 + role을 직원 + **role을 팀장아님**으로 해서 해서 **해당부서 staff직원들**을 찾는다
3. dep_id로 User + UserDerpatment join + dep_id로 필터링 + **role을 팀장으로 해서 해당부서 팀장**을 찾는다
4. dep_id -> **부서객체를 찾아놓은 것으로 .parent_id로 부모부서**를 찾는다.
   - **front에서 dep_id를 받으면, 해당부서객체로 -> 해당부서의 부모부서를 찾을 수 있다.**
5. 현재 로그인한 사람의 user_id를 챙겨놓는다

```python
class LocalView(View):
    def dispatch_request(self, dep_id):
        dep=Department.query.filter(Department.id==dep_id).first()
        staff = User.query.join(User.user_departments).filter(UserDepartment.department_id==dep_id).filter(UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post!="Пользователь").filter(UserDepartment.post!="Руководитель Местного Отделения").filter(UserDepartment.post!="Заместитель Руководителя Местного Отделения").all()
        parent=Department.query.filter(Department.id==dep.parent_id).first()
        user_id=current_user.get_id()
        loc_dir=User.query.join(User.user_departments).filter(UserDepartment.department_id==dep_id).filter(UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post=="Руководитель Местного Отделения").first()
        loc_zam=User.query.join(User.user_departments).filter(UserDepartment.department_id==dep_id).filter(UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post=="Заместитель Руководителя Местного Отделения").all()
        advis_id=[i.user_id for i in Advisor.query.filter(Advisor.department_id==dep_id).filter(Advisor.dismissal_date==None).all()]
        advisors=User.query.filter(User.id.in_(advis_id)).all()
        return render_template('local.html',user_id=user_id,staff=staff,parent=parent,dep=dep,loc_dir=loc_dir,loc_zam=loc_zam,advisors=advisors)
```



```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Местное отделение</title>
</head>
<body>
<h1>{{dep.name}}</h1>
<big>
{% if current_user.is_authenticated %}
    {% if loc_dir %}
    <p>Руководитель: <a href="{{url_for('user',user_id=loc_dir.id)}}">{{loc_dir.name}} {{loc_dir.surname}}</a></p>
    <p>Телефон: {{ loc_dir.phone }}</p>
    <p>E-mail: {{ loc_dir.email }}</p>
    {% endif %}
    {% if loc_zam %}
        <p>Заместители руководителя:</p>
        {% for zam in loc_zam %}
        <a href="{{url_for('user',user_id=zam.id)}}">{{zam.name}} {{zam.surname}}</a><br><br>
        {% endfor %}
    {% endif %}
    {% if advisors %}
        <p>Консультационный совет:</p>
        {% for advis in advisors %}
            <a href="{{url_for('user',user_id=advis.id)}}">{{advis.name}} {{advis.surname}}</a><br><br>
        {% endfor %}
    {% endif %}
    {% if staff %}
        <p>Список сотрудников:</p><br>
        {% for user in staff%}
        <a href="{{url_for('user',user_id=user.id)}}">{{user.name}} {{user.surname}}</a><br><br>
        {% endfor %}
    {% else %}
        <p>В данном отделении нет сотрудников</p>
    {% endif %}
    <a href="{{url_for('regional',dep_id=parent.id)}}">{{ parent.name }}</a>

    <form action="{{url_for('user',user_id=user_id)}}">
        <button type="submit">Моя страница</button>
    </form>
    <br>
    <form action="/logout">
        <button type="submit">Выйти</button>
    </form>
{% else %}
    <p>Просмотр страницы доступен только сотрудникам</p>
    <form action="/login">
        <button>Войти</button>
    </form>
    <form action="/signup">
        <button>Зарегистрироваться</button>
    </form>
{% endif %}
</big>
</body>
</html>
```



###### [RegionalView] 자식부서id: 직원수 dict 만들기 +  자식부서 팀장User + 자식부서 부팀장 찾기

1. 현재 **부서객체**를 찾는다
2. 현재부서의 **자식부서객체들**을 .all()로 다찾는다
3. 자식부서객체들의 listcomp로 **자식부서id_list**를 만든다.
   1. UserDepartment의 department_id를 `.in_()`에 `자식id_list`를 필터링해서 **부서정보 중에, 나의 자식부서들의 유저정보들을 모은다**
   2. 그 중에 퇴직정보는 제외 + 무직자 제외 시킨 뒤
   3. **department_id별, count를 해서, `부서별 user정보 수`를 groupby 후 카운팅한다**
   4. **`.all()로 만든 (부서id별, 유저수) list`를 튜플리스트를 key:value `dict()`로 만든다.**
4. **부모부서객체**를 찾는다.
5. User에 **UserDepartment(부서정보)를 join**시켜, 부서정보가 있는 User정보를 만든 뒤 
   1. 부서정보들 중에, 자식부서id_list들로 `.in_()` 필터링해서 **부서정보 있는 User들 중에, `자식부서정보만 가지는 User들 필터링`한다 **
   2. 무직자 필터링
   3. 팀장만 필터링.first()를 통해, **`하위부서들 중에 팀장 부서정보를 가진 User == 하위부서 팀장User`를 찾는다??**
6. **5번과 마찬가지로 하위부서 부팀장**을 찾는다

```python

class RegionalView(View):
    def dispatch_request(self, dep_id):
        dep = Department.query.filter(Department.id == dep_id).first()
        chil = Department.query.filter(Department.parent_id == dep_id).all()
        count_users = db.session.query(
            UserDepartment.department_id,
            func.count('*').label('c_count')
        ).filter(
            UserDepartment.department_id.in_([i.id for i in chil])
        ).filter(
            UserDepartment.dismissal_date.is_(None)).filter(UserDepartment.post != "Пользователь").group_by(
            UserDepartment.department_id).all()
        count_users = dict(count_users)
        parent = Department.query.filter(Department.id == dep.parent_id).first()
        reg_dir = User.query.join(User.user_departments).filter(
            UserDepartment.department_id.in_([i.id for i in chil])).filter(
            UserDepartment.dismissal_date.is_(None)).filter(
            UserDepartment.post == "Руководитель Регионального Отделения").first()
        reg_zam = User.query.join(User.user_departments).filter(
            UserDepartment.department_id.in_([i.id for i in chil])).filter(
            UserDepartment.dismissal_date.is_(None)).filter(
            UserDepartment.post == "Заместитель Руководителя Регионального Отделения").all()
        advis_id = [i.user_id for i in
                    Advisor.query.filter(Advisor.department_id == dep_id).filter(Advisor.dismissal_date == None).all()]
        advisors = User.query.filter(User.id.in_(advis_id)).all()
        return render_template('regional.html', chil=chil, parent=parent, user_id=current_user.get_id(), dep=dep,
                               count_users=count_users, reg_dir=reg_dir, reg_zam=reg_zam, advisors=advisors)

```



- view에서는 **자식부서를 순회하면서 `자식부서id: 직원수` dict에서 해당 차례 자식부서들마다 카운터를 이용한다**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Региональное отделение</title>
</head>
<body>
<h1>{{dep.name}}</h1>
<big>
{% if current_user.is_authenticated %}
    {% if reg_dir %}
    <p>Руководитель: <a href="{{url_for('user',user_id=reg_dir.id)}}">{{reg_dir.name}} {{reg_dir.surname}}</a></p>
    <p>Телефон: {{ reg_dir.phone }}</p>
    <p>E-mail: {{ reg_dir.email }}</p>
    {% endif %}
    {% if reg_zam %}
        <p>Заместители руководителя:</p>
        {% for zam in reg_zam %}
        <a href="{{url_for('user',user_id=zam.id)}}">{{zam.name}} {{zam.surname}}</a><br><br>
        {% endfor %}
    {% endif %}
    {% if advisors %}
        <p>Консультационный совет:</p>
        {% for advis in advisors %}
            <a href="{{url_for('user',user_id=advis.id)}}">{{advis.name}} {{advis.surname}}</a><br><br>
        {% endfor %}
    {% endif %}
    <p>Список отделений (количество сотрудников):</p><br>
    {% for chi in chil %}
    <p><a href="{{url_for('local',dep_id=chi.id)}}">{{chi.name}}</a>
        {% if count_users[chi.id] %}
        {{count_users[chi.id]}}
    {% else %}
    Нет сотрудников
    {% endif %}</p>
    {% endfor %}
    <a href="{{url_for('federal',dep_id=parent.id)}}">{{parent.name}}</a>
    <form action="{{url_for('user',user_id=user_id)}}">
        <button type="submit">Моя страница</button>
    </form>
    <br>
    <form action="/logout">
        <button type="submit">Выйти</button>
    </form>
{% else %}
    <p>Просмотр страницы доступен только сотрудникам</p>
    <form action="/login">
        <button>Войти</button>
    </form>
    <form action="/signup">
        <button>Зарегистрироваться</button>
    </form>
{% endif %}
</big>
</body>
</html>
```



###### [UserView] 유저정보에서는 퇴직정보포함 부서정보 + 

1. `특정user`의 **부서정보들**을 .all()로 찾고  (퇴직정보들, 중복부서 다 포함)
2. 특정user의 부서정보를 first()로 찾고, 부서id를 뽑는다.
   - 부서id로 **부서객체**를 찾는다.
3. 부서객체에서 .parent_id로 **부모 부서id를 찾는다**
4. `현재 유저`의 부서id -> **부서객체**를 찾는다
5. 현재유저의 **부모 부서id**를 찾는다.
6. 현재유저의 퇴직정보제외한 **부서의 role**을 찾는다.



- actions dict에서 종류별로 role을 돌면서, **현재유저의 부서role이 포함되어있는 것만 list에 모은다**



- 특정유저의 부모부서id == 현재유저의 부모부서id
  - **2명이 부모부서가 같은지를 T/F로 보관한다**
- **2명의 현재부서가 같은지를 T/F로 보관한다**



- **특정유저의 부서role을 찾는다**



- **현재유저의 부서role에 따라**
  - **특정유저의 부서Role**가 맞으면
    - **dis_를 True로 flag**를 만들어준다
- **현재유저의 부서role**이
  - 최상위라면 main_dep_id 에 = 1을 직접
  - level 2 대장이라면, 특정유저의 부모부서를 main_dep_id으로
  - 최하위라면 현재부서를 main_dep_id로 배정한다

```python
class UserView(View):
    def dispatch_request(self, user_id):
        main_dep_id=None
        actions = {
            'add_federal_zam': (
                'Назначить заместителем руководителя федерального отделения', ['Руководитель Федерального Отделения']),
            'add_regional_director': (
                'Назначить руководителем регионального отделения',
                ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения']),
            'add_regional_zam': (
                'Назначить заместителем руководителя регионального отделения',
                ['Руководитель Регионального Отделения']),
            'add_local_director': (
                'Назначить руководителем местного отделения',
                ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения',
                 'Руководитель Регионального Отделения', 'Заместитель Руководителя Регионального Отделения']),
            'add_local_zam': (
                'Назначить заместителем руководителя местного отделения', ['Руководитель Местного Отделения']),
            'staff': (
                'Назначить сотрудником местного отделения',
                ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения',
                 'Руководитель Регионального Отделения', 'Заместитель Руководителя Регионального Отделения',
                 'Руководитель Местного Отделения', 'Заместитель Руководителя Местного Отделения']),
            'dis_staff': (
                'Уволить',
                ['Руководитель Федерального Отделения', 'Заместитель Руководителя Федерального Отделения',
                 'Руководитель Регионального Отделения', 'Заместитель Руководителя Регионального Отделения',
                 'Руководитель Местного Отделения', 'Заместитель Руководителя Местного Отделения'])
        }
        user = User.query.filter(User.id == user_id).first()
        if not (current_user.is_authenticated):
            return render_template('user.html', user=user)

        user_posts = UserDepartment.query.filter(UserDepartment.user_id == user_id).all()
        dep_id = UserDepartment.query.filter(UserDepartment.user_id == user.id).first().department_id
        dep = Department.query.filter(Department.id == dep_id).first()
        user_regional_dep_id = dep.parent_id
        cur_user_id = int(current_user.get_id())
        our_dep_id = UserDepartment.query.filter(UserDepartment.user_id == cur_user_id).first().department_id
        our_dep = Department.query.filter(Department.id == our_dep_id).first()
        our_regional_dep_id = our_dep.parent_id
        post = UserDepartment.query.filter(UserDepartment.user_id == cur_user_id).filter(
            UserDepartment.dismissal_date == None).first().post
        opportunities = []
        for i in actions:
            if post in actions[i][1]:
                opportunities.append(i)
        regional_indic = user_regional_dep_id == our_regional_dep_id
        local_indic = dep_id == our_dep_id
        dis_indic = False
        user_post = UserDepartment.query.filter(UserDepartment.user_id == user_id).filter(
            UserDepartment.dismissal_date == None).first().post

        if post == 'Руководитель Федерального Отделения':
            if user_post == 'Заместитель Руководителя Федерального Отделения' or user_post == 'Руководитель Регионального Отделения' or user_post == 'Заместитель Руководителя Регионального Отделения' or user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                dis_indic = True

        if post == 'Заместитель Руководителя Федерального Отделения':
            if user_post == 'Руководитель Регионального Отделения' or user_post == 'Заместитель Руководителя Регионального Отделения' or user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                dis_indic = True

        if post == 'Руководитель Регионального Отделения':
            if regional_indic:
                if user_post == 'Заместитель Руководителя Регионального Отделения' or user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                    dis_indic = True

        if post == 'Заместитель Руководителя Регионального Отделения':
            if regional_indic:
                if user_post == 'Руководитель Местного Отделения' or user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                    dis_indic = True

        if post == 'Руководитель Местного Отделения':
            if local_indic:
                if user_post == 'Заместитель Руководителя Местного Отделения' or user_post == 'Сотрудник' or user_post == 'Пользователь':
                    dis_indic = True

        if post == 'Заместитель Руководителя Местного Отделения':
            if local_indic:
                if user_post == 'Сотрудник' or user_post == 'Пользователь':
                    dis_indic = True

        if post == "Руководитель Федерального Отделения":
            main_dep_id = 1
        if post == "Руководитель Регионального Отделения":
            main_dep_id = Department.query.filter(Department.id == UserDepartment.query.filter(
                UserDepartment.user_id == user.id).first().department_id).first().parent_id
        if post == "Руководитель Местного Отделения":
            main_dep_id = UserDepartment.query.filter(UserDepartment.user_id == user.id).first().department_id

        advisor_indic = Advisor.query.filter(Advisor.user_id == user_id).filter(Advisor.dismissal_date == None).filter(
            Advisor.department_id == main_dep_id).first()

        return render_template('user.html', user=user, dep=dep, cur_user_id=cur_user_id, local_indic=local_indic,
                               opportunities=opportunities, actions=actions, regional_indic=regional_indic, post=post,
                               dis_indic=dis_indic, user_posts=user_posts, advisor_indic=advisor_indic)
```





- **view에서는**
  - **유저의 퇴직정보포함 모든 부서정보들을 순회하며 보여준다**
  - **유저정보가 현재유저 + 팀장급이면, `/add_staff`를 form에 필드없이 submit할 수 있게 한다**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Страница пользователя</title>
</head>
<body>
<h1>Страница пользователя</h1>
<big>
<p>Имя: {{user.name}}</p>
<p>Фамилия: {{user.surname}}</p>
{% if current_user.is_authenticated %}
    {% if dis_indic or local_indic and post!='Пользователь'%}
        <p>E-mail: {{user.email}}</p>
        <p>Телефон: {{user.phone}}</p><br>
        <p>Должности сотрудника: </p>
        {% for post in user_posts %}
        <p>{{ post.post }} c {{ post.employment_date }}{% if post.dismissal_date %} по {{ post.dismissal_date }}{% endif %}</p>
        {% endfor %}
    {% endif %}
    <a href="{{url_for('local',dep_id=dep.id)}}">{{ dep.name }}</a>
    <br>

    {% if user.id==cur_user_id %}
        {% if post!='Сотрудник' and post!='Пользователь' %}
            <form action="/add_staff">
                <button type="submit">Принять сотрудников</button>
            </form>
        {% endif %}
    {% else %}
        <ul>
                {% if dis_indic %}
                    {% if advisor_indic %}
                        <form action="{{url_for('change',user_id=user.id,var='dis_advisor')}}">
                            <p><li><button type="submit"><big>Удалить из консультационного совета</big></button></li></p>
                        </form>
                    {% else %}
                        <form action="{{url_for('change',user_id=user.id,var='advisor')}}">
                            <p><li><button type="submit"><big>Добавить в консультационный совет</big></button></li></p>
                        </form>
                    {% endif %}
                {% endif %}
            {% for act in actions %}
                {% if act in opportunities%}
                    {% if dis_indic %}
                        <form action="{{url_for('change',user_id=user.id,var=act)}}">
                            <li><button type="submit"><big>{{actions[act][0]}}</big></button></li><br>
                        </form>
                    {% endif %}
                {% endif %}
            {% endfor %}
        </ul>
    {% if get_flashed_messages() %}
        <p>{{ get_flashed_messages()[0] }}</p>
    {% endif %}
        <form action="{{url_for('user',user_id=cur_user_id)}}">
            <button type="submit">Моя страница</button>
        </form>
    {% endif %}
    <br>
    <form action="/logout">
        <button type="submit">Выйти</button>
    </form>
{% else %}
    <p>Просмотр страницы доступен только сотрудникам</p>
    <form action="/login">
        <button>Войти</button>
    </form>
    <form action="/signup">
        <button>Зарегистрироваться</button>
    </form>
{% endif %}
</big>
</body>
</html>
```







#### 3 **[seesun_crm_services](https://github.com/ubqai/seesun_crm_services)**Public

- https://vscode.dev/github/ubqai/seesun_crm_services/blob/e08cc69f133860b2aa3aa6a50f23d79c14a24bd2/application/models.py#L816





- level칼럼

  ```python
  class DepartmentHierarchy(db.Model):
      __tablename__ = 'department_hierarchies'
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String(300), nullable=False)
      parent_id = db.Column(db.Integer)
      level_grade = db.Column(db.Integer)
  
      def __repr__(self):
          return '<DepartmentHierarchy %r -- %r>' % (self.id, self.name)
  ```



- sales도 동일한 parent_id와 level을 가지고 있다

  ```python
  class SalesAreaHierarchy(db.Model):
      __tablename__ = 'sales_area_hierarchies'
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String(300), nullable=False)
      parent_id = db.Column(db.Integer)
      level_grade = db.Column(db.Integer)
  
      def __repr__(self):
          # return 'SalesAreaHierarchy %r' % self.name
          return '<SalesAreaHierarchy %r -- %r>' % (self.id, self.name)
  
      @classmethod
      def get_team_info_by_regional(cls, regional_id):
          regional_province = {}
          for regional_info in SalesAreaHierarchy.query.filter_by(parent_id=regional_id).all():
              # 每个省份只有一个销售员
              team = ()
              team_info = UserAndSaleArea.query.filter(UserAndSaleArea.parent_id != None,
                                                       UserAndSaleArea.sales_area_id == regional_info.id).first()
              if team_info is None:
                  team = (-1, "无")
              else:
                  u = User.query.filter(User.id == team_info.user_id).first()
                  team = (u.id, u.nickname)
              regional_province[regional_info.id] = {"regional_province_name": regional_info.name, "team_info": team}
  
          if regional_province == {}:
              regional_province[-1] = {"regional_province_name": "无", "team_info": (-1, "无")}
  
          return regional_province
  ```

  

- user

  ```python
  users_and_departments = db.Table(
      'users_and_departments',
      db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
      db.Column('dep_id', db.Integer, db.ForeignKey('department_hierarchies.id'))
  )
  ```

  ```python
  class User(db.Model, Rails):
      __tablename__ = 'users'
      id = db.Column(db.Integer, primary_key=True)
      password_hash = db.Column(db.String(100), nullable=False)
      email = db.Column(db.String(60), nullable=False, unique=True)
      nickname = db.Column(db.String(200))
      user_or_origin = db.Column(db.Integer)
      created_at = db.Column(db.DateTime, default=datetime.datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
      user_infos = db.relationship('UserInfo', backref='user')
      orders = db.relationship('Order', backref='user', lazy='dynamic')
      contracts = db.relationship('Contract', backref='user', lazy='dynamic')
      material_applications = db.relationship('MaterialApplication', backref='user', lazy='dynamic')
      design_applications = db.relationship('DesignApplication', backref='applicant', lazy='dynamic')
      resources = db.relationship('Resource', secondary=users_and_resources,
                                  backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
      sales_areas = db.relationship('SalesAreaHierarchy', secondary=users_and_sales_areas,
                                    backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
      departments = db.relationship('DepartmentHierarchy', secondary=users_and_departments,
                                    backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
      # 特殊属性 - 每一位使用0,1作为区分
      # 经销商用户 - 首位表示是否加盟 0:未加盟 , 1:加盟
      # 是否被禁止登入 - 第2位表示是否被禁止登入 0:未禁止， 1:禁止
      # 员工 - 暂未使用此字段
      extra_attributes = db.Column(db.String(10), default='')
  
      def __repr__(self):
          return '<User %r -- %r>' % (self.id, self.nickname)
  
      # 用户的对象是否可认证 , 因为某些原因不允许被认证
      def is_authenticated(self):
          return True
  
      # 用户的对象是否有效 , 账号被禁止
      def is_active(self):
          return True
  
      # 为那些不被获准登录的用户返回True
      def is_anonymous(self):
          if self.extra_attributes is not None and self.extra_attributes[1:2] == '1':
              return True
          return False
  
      # 设置用户是否禁用
      def set_is_anonymous(self, is_anonymous_data):
          if is_anonymous_data is None or is_anonymous_data == 'None':
              is_anonymous_data = '0'
  
          if self.extra_attributes is None or self.extra_attributes == "":
              # 第一位默认为1
              self.extra_attributes = '1' + is_anonymous_data
          else:
              list_extra_attributes = list(self.extra_attributes)
              list_extra_attributes[1] = is_anonymous_data
              self.extra_attributes = ''.join(list_extra_attributes)
  
      # 设置用户是否加盟 -- 供应商专属属性
      def set_join_dealer(self, join_dealer_data):
          if join_dealer_data is None or join_dealer_data == 'None':
              join_dealer_data = '1'
  
          if self.user_or_origin == 2:
              if self.extra_attributes is None or self.extra_attributes == "":
                  # 第二位默认为0
                  self.extra_attributes = join_dealer_data + "0"
              else:
                  list_extra_attributes = list(self.extra_attributes)
                  list_extra_attributes[0] = join_dealer_data
                  self.extra_attributes = ''.join(list_extra_attributes)
  
      # 为用户返回唯一的unicode标识符
      def get_id(self):
          return str(self.id).encode("utf-8")
  
      def check_can_login(self):
          if self.user_or_origin == 3 and self.departments.count() == 0:
              return "用户[%s]部门异常,请联系管理员" % self.nickname
          if self.is_anonymous():
              if self.user_or_origin == 2:
                  return "[%s经销商]暂时无法登陆，请联系管理员" % self.nickname
              else:
                  return "用户[%s]已被禁用,请联系管理员" % self.nickname
          return ""
  
      def get_user_type_name(self):
          return {2: "经销商", 3: "员工"}[self.user_or_origin]
  
      # 前台查询,新增,修改用户权限控制
      def authority_control_to_user(self, other_user):
          # 可操作任意经销商
          if other_user is None or other_user.user_or_origin == 2:
              return None
          # 等级权限高 - 董事长
          if self.get_max_level_grade() < other_user.get_max_level_grade():
              return None
          # 所属部门是否有交集
          self_d_array = [d.id for d in self.departments.all()]
          other_d_array = [d.id for d in other_user.departments.all()]
          if list(set(self_d_array).intersection(set(other_d_array))) != []:
              return None
  
          return "当前用户[%s] 无权限操作用户[%s]" % (self.nickname, other_user.nickname)
  
      @property
      def password(self):
          return self.password_hash
  
      @password.setter
      def password(self, value):
          self.password_hash = bcrypt.generate_password_hash(value).decode('utf-8')
  
      # 获取用户的最大部门等级
      def get_max_level_grade(self):
          max_level_grade = 99
          for d in self.departments:
              if max_level_grade > d.level_grade:
                  max_level_grade = d.level_grade
  
          return max_level_grade
  
      # 授权加载2小时
      @cache.memoize(7200)
      # 是否有授权
      def is_authorized(self, endpoint, method="GET"):
          print("User[%s] endpoint[%s] is authorized cache" % (self.nickname, endpoint))
          return AuthorityOperation.is_authorized(self, endpoint, method)
  
      # 获取用户所属role -- 暂使用所属部门代替
      def get_roles(self):
          return [(d.id, d.name) for d in self.departments.order_by(DepartmentHierarchy.id.asc()).all()]
  
      def get_province_sale_areas(self):
          if not self.user_or_origin == 3:
              return []
          if self.departments.filter_by(name="销售部").first() is not None:  # 销售部员工
              areas = []
              for area in self.sales_areas:
                  if area.level_grade == 2:  # 销售总监，管理一个大区
                      areas += SalesAreaHierarchy.query.filter_by(level_grade=3, parent_id=area.id).all()
                  elif area.level_grade == 3:  # 普通销售人员，管理一个省
                      areas += [area]
                  else:
                      areas += []
              return areas
          else:
              return []
  
      def get_subordinate_dealers(self):
          return db.session.query(User).join(User.sales_areas).filter(User.user_or_origin == 2).filter(
              SalesAreaHierarchy.level_grade == 4).filter(
              SalesAreaHierarchy.id.in_([area.id for area in SalesAreaHierarchy.query.filter(
                  SalesAreaHierarchy.parent_id.in_([province.id for province in self.get_province_sale_areas()]))])).all()
  
      @property
      def is_sales_department(self):
          sales_department = DepartmentHierarchy.query.filter_by(name='销售部').first()
          if sales_department in self.departments:
              return True
          else:
              return False
  
      @cache.memoize(7200)
      def get_orders_num(self):
          if self.is_sales_department:
              num = Order.query.filter_by(order_status='新订单').filter(
                  Order.user_id.in_(set([user.id for user in self.get_subordinate_dealers()]))).count()
              return num
          else:
              return 0
  
      def get_other_app_num(self):
          return self.get_material_application_num() + self.get_project_report_num() + self.get_share_inventory_num()
  
      @cache.memoize(7200)
      def get_material_application_num(self):
          if self.is_sales_department:
              num = MaterialApplication.query.filter_by(status='新申请').filter(
                  MaterialApplication.user_id.in_(set([user.id for user in self.get_subordinate_dealers()]))).count()
              return num
          else:
              return 0
  
      @cache.memoize(7200)
      def get_material_application_approved_num(self):
          return MaterialApplication.query.filter(MaterialApplication.status == '同意申请').count()
  
      @cache.memoize(7200)
      def get_project_report_num(self):
          if self.is_sales_department:
              num = ProjectReport.query.filter_by(status='新创建待审核').filter(
                  ProjectReport.app_id.in_(set([user.id for user in self.get_subordinate_dealers()]))).count()
              return num
          else:
              return 0
  
      @cache.memoize(7200)
      def get_share_inventory_num(self):
          if self.is_sales_department:
              num = ShareInventory.query.filter_by(status='新申请待审核').filter(
                  ShareInventory.applicant_id.in_(set([user.id for user in self.get_subordinate_dealers()]))).count()
              return num
          else:
              return 0
  
      # @cache.memoize(7200)
      def get_finance_contract_num(self):
          return Contract.query.filter(Contract.payment_status == '未付款').count()
  
      def get_contract_for_tracking_num(self):
          return Contract.query.filter((Contract.payment_status == '已付款') &
                                       (Contract.shipment_status == '未出库')).count()
  
      # 获取'新申请'产品设计的数量, DesignApplication
      @cache.memoize(7200)
      def get_new_design_application_num(self):
          return DesignApplication.query.filter(DesignApplication.status == '新申请').count()
  
      # 是否为销售总监
      # Y - 是 ； N - 否 ; U - 未知
      def is_sale_manage(self):
          # 存在已有的销售记录
          if self.get_sale_manage_provinces():
              return "Y"
          # 什么记录都没
          if self.user_or_origin == 3 and self.departments.filter_by(
                  name="销售部").first() is not None and self.sales_areas.first() is None:
              return "U"
  
          return "N"
  
      # 获取销售总监所管理的大区
      def get_sale_manage_provinces(self):
          if not self.user_or_origin == 3:
              return []
          if self.departments.filter_by(name="销售部").first() is None:
              return []
  
          return [uasa.sales_area_id for uasa in UserAndSaleArea.query.filter(UserAndSaleArea.user_id == self.id,
                                                                              UserAndSaleArea.parent_id == None).all()]
  
      # 是否管理某一大区
      def is_manage_province(self, sale_area_id):
          return sale_area_id in self.get_sale_manage_provinces()
  
      # 是否经销商
      def is_dealer(self):
          return self.user_or_origin == 2
  
      # 是否员工
      def is_staff(self):
          return self.user_or_origin == 3
  
      # 是否加盟经销商
      def is_join_dealer(self):
          return self.user_or_origin == 2 and \
                 self.extra_attributes is not None and \
                 self.extra_attributes[0:1] == "1"
  
      # 根据email+密码获取用户实例
      @classmethod
      def login_verification(cls, email, password, user_or_origin):
          user = User.query.filter(User.email == email)
          if user_or_origin:
              user = user.filter(User.user_or_origin == user_or_origin)
          user = user.first()
          if user is not None:
              if not bcrypt.check_password_hash(user.password, password):
                  user = None
  
          return user
  
      # 验证并修改用户密码
      @classmethod
      def update_password(cls, email, password_now, password_new, password_new_confirm, user_or_origin):
          user = User.login_verification(email, password_now, user_or_origin)
  
          if user is None:
              raise ValueError("密码错误")
  
          if password_now == password_new:
              raise ValueError("新旧密码不可相同")
  
          if password_new != password_new_confirm:
              raise ValueError("新密码两次输入不匹配")
          if len(password_new) < 8 or len(password_new) > 20:
              raise ValueError("密码长度必须大等于8小等于20")
  
          user.password = password_new
          user.save
  
      # 获取所有role -- 暂使用所属部门代替
      @classmethod
      def get_all_roles(cls):
          return [(d.id, d.name) for d in DepartmentHierarchy.query.order_by(DepartmentHierarchy.id.asc()).all()]
  
  
  class UserInfo(db.Model):
      __tablename__ = 'user_infos'
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String(400))
      telephone = db.Column(db.String(20))
      address = db.Column(db.String(500))
      title = db.Column(db.String(200))
      user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  
      def __repr__(self):
          return '<UserInfo %r -- %r>' % (self.id, self.name)
  ```

  



##### Rails라는 class는 self.를 add commit <-> 실패시rollback / delete commit()을 하는 Mixin

```python
class Rails(object):
    @property
    def save(self):
        # 增加rollback防止一个异常导致后续SQL不可使用
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        return self

    @property
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
```







##### department예시

###### seed.py => fill_db역할

- 부서목록 string을 만들고, 

  - **특정name을 level1으로 직접 생성**, 
  - 나머지는 레벨2를 배정해서 저장한다.

  ```python
  dh_array = '董事长 销售部 仓储物流部 电商部 设计部 市场部 售后部 财务部'.split()
  for dh_name in dh_array:
      if not DepartmentHierarchy.query.filter_by(name=dh_name).first():
          dh = DepartmentHierarchy(name=dh_name)
          if dh_name == "董事长":
              dh.level_grade = 1
          else:
              dh.level_grade = 2
              dh.parent_id = DepartmentHierarchy().query.filter_by(name='董事长').first().id
          db.session.add(dh)
          db.session.commit()
  
  ```

- admin email로 생성된 User가 없으면, level=1의 첫번째 부서로 Admin유저를 만든다.

  ```python
  if not User.query.filter_by(email="admin@hotmail.com").first():
      u = User(email="admin@hotmail.com", nickname="admin", user_or_origin=3, password='1qaz@WSX')
      dh = DepartmentHierarchy().query.filter_by(level_grade=1).first()
      u.departments.append(dh)
      u.save
  ```

  

###### model.py

- 공유인벤토리

  - **sale_director_id**
    - 지원자 -> sale지역 -> 첫번째의 -> parent_id -> **province_id** in `SalesAreaHierarchy`
    - province_id로 SalesArea를 찾고, 그것의 parent_id -> **region_id** in `SalesAreaHierarchy`
    - user 중에 
      - user.departments(M:N)를 join한 뒤, where( DepartmentHierarchy.name == 특정부서)
      - user.sales_areas(M:N)를 join한 뒤, where( SalesAreaHierarchy.id == region_id )
      - .first() -> us
        - if us  return us.id else return 0

  ```python
  class ShareInventory(db.Model, Rails):
      id = db.Column(db.Integer, primary_key=True)
      applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'))
      audit_id = db.Column(db.Integer)
      created_at = db.Column(db.DateTime, default=datetime.datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
      status = db.Column(db.String(50))
      batch_no = db.Column(db.String(50))
      product_name = db.Column(db.String(200))
      sku_option = db.Column(db.String(200))
      sku_code = db.Column(db.String(30))
      sku_id = db.Column(db.Integer)
      production_date = db.Column(db.String(30))
      stocks = db.Column(db.Float)
      price = db.Column(db.Float)
      audit_price = db.Column(db.Float)
      pic_files = db.Column(db.JSON)
  
      @property
      def app_user(self):
          return User.query.get_or_404(self.applicant_id)
  
      @property
      def sale_director_id(self):
          province_id = User.query.get_or_404(self.applicant_id).sales_areas.first().parent_id
          region_id = SalesAreaHierarchy.query.get_or_404(province_id).parent_id
          us = db.session.query(User).join(User.departments).join(User.sales_areas).filter(
              User.user_or_origin == 3).filter(
              DepartmentHierarchy.name == "销售部(판매부)").filter(
              SalesAreaHierarchy.id == region_id).first()
          if us is not None:
              return us.id
          else:
              return 0
  ```

  



- Order

  - **sale_director, sale_director_id**

  ```python
  class Order(db.Model, Rails):
      __tablename__ = 'orders'
      id = db.Column(db.Integer, primary_key=True)
      order_no = db.Column(db.String(30), unique=True)
      created_at = db.Column(db.DateTime, default=datetime.datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
      user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
      order_status = db.Column(db.String(50))
      order_memo = db.Column(db.Text)
      buyer_info = db.Column(db.JSON)
      sale_contract = db.Column(db.String(200))
      sale_contract_id = db.Column(db.Integer)
      contracts = db.relationship('Contract', backref='order', lazy='dynamic')
      order_contents = db.relationship('OrderContent', backref='order')
  
      def __repr__(self):
          return 'Order(id: %s, order_no: %s, user_id: %s, order_status: %s, order_memo: %s)' % (
              self.id, self.order_no, self.user_id, self.order_status, self.order_memo)
  
      @property
      def sale_director(self):
          province_id = User.query.get_or_404(self.user_id).sales_areas.first().parent_id
          region_id = SalesAreaHierarchy.query.get_or_404(province_id).parent_id
          us = db.session.query(User).join(User.departments).join(User.sales_areas).filter(
              User.user_or_origin == 3).filter(
              DepartmentHierarchy.name == "销售部").filter(
              SalesAreaHierarchy.id == region_id).first()
          if us is not None:
              return us.nickname
          else:
              return ''
  
      @property
      def sale_director_id(self):
          province_id = User.query.get_or_404(self.user_id).sales_areas.first().parent_id
          region_id = SalesAreaHierarchy.query.get_or_404(province_id).parent_id
          us = db.session.query(User).join(User.departments).join(User.sales_areas).filter(
              User.user_or_origin == 3).filter(
              DepartmentHierarchy.name == "销售部").filter(
              SalesAreaHierarchy.id == region_id).first()
          if us is not None:
              return us.id
          else:
              return 0
  
      @property
      def sale_contract_phone(self):
          return '' if self.sale_contract_id is None else User.query.get(self.sale_contract_id).user_infos[0].telephone
  ```





- user

  - user입장에서 MN이지만, Many인데, user.departments를 id오름차순으로 가져온 뒤, id, name 튜플반환

  ```python
  # 获取用户所属role -- 暂使用所属部门代替
  def get_roles(self):
      return [(d.id, d.name) for d in self.departments.order_by(DepartmentHierarchy.id.asc()).all()]
  ```

  - **user가 여러 department를 가지고 있는데, 그 안에 특정 department에 속하는지, 판매부서에 속하는지 확인**
    - 특정부서를 먼저 찾고, 그게 내가 가진 부서에 속하는지 확인

  ```python
  @property
  def is_sales_department(self):
      sales_department = DepartmentHierarchy.query.filter_by(name='销售部').first()
      if sales_department in self.departments:
          return True
      else:
          return False
  ```



- AuthorityOperation

  - 다대다 테이블에서는, 자신이 가진 각 one의 pk + table로 조회하면 된다

    ```python
    class AuthorityOperation(db.Model, Rails):
        __tablename__ = 'authority_operations'
        id = db.Column(db.Integer, primary_key=True)
        webpage_id = db.Column(db.Integer, db.ForeignKey('webpage_describes.id'))
        role_id = db.Column(db.Integer, nullable=False)  # 暂时对应DepartmentHierarchy.id
        flag = db.Column(db.String(10))  # 权限配置是否有效等
        remark = db.Column(db.String(200))  # 权限备注
        time = db.Column(db.DateTime, default=datetime.datetime.now)  # 权限设置时间
    
        def __repr__(self):
            return '<AuthorityOperation %r -- %r,%r>' % (self.id, self.webpage_id, self.role_id)
    
        # role_id获取对应中文
        def get_role_name(self):
            return DepartmentHierarchy.query.filter_by(id=self.role_id).first().name
    ```

    

######  views.py

- team_profit

  - **level 2의 SaleArea들을 돌면서**에 대해

    - **지역**마다, 특정부서의 user들을 확인한 뒤 있으면
      - **team으로서 nickname**저장
      - 그 닉네임마다 동시에 
        - team으로서 level2 -> **level4의 모든 user_id를 뽑음**
          - **해당level2지역을 부모로 가진 지역**들을 **지역들id list**를 뽑은 뒤
            - 지역2 자식들 지역3id list를 **parent_id.in_( [ ])에 넣어서 그것들의 자식들 지역4id list를 뽑음** 
              - **level2지역 자식들 -> 또 자식들을 뽑았는데, level3, 4 일 수도 있지만, 그 이하일 수도 있어서 `level==4 필터링 추가`**
        - **지역level4에 속하는user_ids**를 뽑았으면, 계약들 중 **user_ids가 포함된 계약들**만 뽑음
          - **계약들 중, db.JSON칼럼의 계약내용에에서 .get('amount', '0') + float변환으로 문자열로 적힌 숫자들을 뽑아서 reduce로 누적함**

    ```python
    
    class Contract(db.Model):
        __tablename__ = 'contracts'
        id = db.Column(db.Integer, primary_key=True)
        contract_no = db.Column(db.String(30), unique=True)
        contract_date = db.Column(db.DateTime, default=datetime.datetime.now)
        created_at = db.Column(db.DateTime, default=datetime.datetime.now)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
        contract_status = db.Column(db.String(50))
        product_status = db.Column(db.String(50))
        shipment_status = db.Column(db.String(50))
        payment_status = db.Column(db.String(50), default='未付款')
        contract_content = db.Column(db.JSON)
    
        def __repr__(self):
            return 'Contract(id: %s, contract_no: %s, contract_date: %s, order_id: %s, contract_status: %s, product_status: %s, shipment_status: %s, ...)' % (
                self.id, self.contract_no, self.contract_date, self.order_id, self.contract_status, self.product_status,
                self.shipment_status)
    
        @property
        def production_status(self):
            tracking_info = TrackingInfo.query.filter_by(contract_no=self.contract_no).first()
            if tracking_info:
                return tracking_info.production_status
            return '未生产'
    
        @property
        def delivery_status(self):
            tracking_info = TrackingInfo.query.filter_by(contract_no=self.contract_no).first()
            if tracking_info:
                return tracking_info.delivery_status
            return '未发货'
    
    ```

    

    ```python
    
    @order_manage.route('/team_profit')
    def team_profit():
        teams = []
        total_amount = []
        for region in SalesAreaHierarchy.query.filter_by(level_grade=2):
            us = db.session.query(User).join(User.departments).join(User.sales_areas).filter(
                User.user_or_origin == 3).filter(
                DepartmentHierarchy.name == "销售部").filter(
                SalesAreaHierarchy.id == region.id).first()
            if us is not None:
                teams.append(us.nickname)
                user_ids = [user.id for user in db.session.query(User).join(User.sales_areas).filter(
                    User.user_or_origin == 2).filter(SalesAreaHierarchy.level_grade == 4).filter(
                    SalesAreaHierarchy.id.in_([area.id for area in SalesAreaHierarchy.query.filter(
                        SalesAreaHierarchy.parent_id.in_([area.id for area in SalesAreaHierarchy.query.filter(
                            SalesAreaHierarchy.parent_id == region.id)]))]))]
                contracts = Contract.query.filter_by(payment_status='已付款').filter(Contract.user_id.in_(user_ids)).all()
                amount = reduce(lambda x, y: x + y, [float(contract.contract_content.get('amount', '0'))
                                                     for contract in contracts], 0)
    
                total_amount.append(amount)
        return render_template('order_manage/team_profit.html', teams=teams, total_amount=total_amount)
    ```

    

###### forms.py => Dynamic query Select Field 구성( 현재부서 + min greedy로 나의 최대 부서level과 비교해서 => union으로 현재부터 하위부서들을 합쳐서 구성) + form field reset 메서드에서 current_user마다 배정

- `current_user` 를 import해서 사용하여 `dynamic query select field` 만들기

  - def get_dynamic_dept_ranges_query

    - 기본 select query를 만들고

      1. 탈락조건 login된 유저X or 인증된 유저X or **user.ManyDepartmnets. count == 0(복수존재는 count로)**로서 부서가 없는 유저라면, **모든 부서를 반환한다**

      2. **로그인/권한/부서를 가진 User라면**

         1. `current_user`의 **해당user의 departments 중 가장 max_level을 greedy를 찾는다. `가장 낮은 level을 찾는 식`인 것 같다** 

            ```python
            # 获取用户的最大部门等级
            def get_max_level_grade(self):
                max_level_grade = 99
                for d in self.departments:
                    if max_level_grade > d.level_grade:
                        max_level_grade = d.level_grade
            
                return max_level_grade
            ```

         2. User가 가진 max_depart_level보다 큰 **보다 하위 Department를** 필터조건으로 추가하고

            - **User가 가진 departments(관계칼럼)를 `.union()`으로 `현재 유저의 부서들`에 union한다**

      ```python
      def get_dynamic_dept_ranges_query():
          dhs = DepartmentHierarchy.query
      
          # 前端已进行控制,防止异常增加逻辑
          if current_user is None or not current_user.is_authenticated or current_user.departments.count() == 0:
              return dhs.order_by(DepartmentHierarchy.id).all()
      
          max_depart_level = current_user.get_max_level_grade()
          dhs = dhs.filter(DepartmentHierarchy.level_grade > max_depart_level)
          dhs = dhs.union(current_user.departments)
      
          return dhs.order_by(DepartmentHierarchy.id).all()
      ```



- dynamic query를 BaseForm의 def reset_select_field로 정의해준다

  ```python
  class BaseForm(Form):
      def reset_select_field(self):
          self.dept_ranges.query = get_dynamic_dept_ranges_query()
          self.sale_range_province.query = get_dynamic_sale_range_query(3)
          self.sale_range.query = get_dynamic_sale_range_query(4)
  
      @classmethod
      def get_sale_range_by_parent(cls, level_grade, parent_id):
          return get_dynamic_sale_range_query(level_grade, parent_id)
  
  ```

- BaseForm을 상속한 UserForm을 정의한다

  - 초기화한 dept_ranges 폼 필드를 변수명으로 해서 QuerySelectField를 정의하면, 알아서 초기화된다?

  ```python
  # BASE USER
  class UserForm(BaseForm, BaseCsrfForm):
      email = StringField('邮箱', [validators.Email(message="请填写正确格式的email")])
      name = StringField('姓名', [validators.Length(min=2, max=30, message="字段长度必须大等于2小等于30")])
      nickname = StringField('昵称', [validators.Length(min=2, max=30, message="字段长度必须大等于2小等于30")])
      password = PasswordField('密码', validators=[
          validators.DataRequired(message="字段不可为空"),
          validators.Length(min=8, max=20, message="字段长度必须大等于8小等于20"),
          validators.EqualTo('password_confirm', message="两次输入密码不匹配")
      ])
      password_confirm = PasswordField('密码')
      address = TextAreaField('地址', [validators.Length(min=5, max=300, message="字段长度必须大等于5小等于300")])
      # 电话匹配规则 11位手机 or 3-4区号(可选)+7-8位固话+1-6分机号(可选)
      phone = StringField('电话',
                          [validators.Regexp(r'(^\d{11})$|(^(\d{3,4}-)?\d{7,8}(-\d{1,5})?$)', message="请输入正确格式的电话")])
      title = StringField('头衔')
      user_type = SelectField('用户类型', choices=[('3', '员工'), ('2', '经销商')],
                              validators=[validators.DataRequired(message="字段不可为空")])
      # dept_ranges = SelectMultipleField('dept_ranges',choices=[ ('-1','选择所属部门')] + [(str(dh.id),dh.name) for dh in DepartmentHierarchy.query.all() ])
      # sale_range = SelectField('sale_range',choices=[ ('-1','选择销售范围')] + [(str(sah.id),sah.name) for sah in SalesAreaHierarchy.query.filter_by(level_grade=4).all() ])
      dept_ranges = QuerySelectMultipleField(u'所属部门', get_label="name", validators=[valid_dept_ranges])
      sale_range_province = QuerySelectField(u'销售范围(省)', get_label="name", allow_blank=True)
      sale_range = QuerySelectField(u'销售范围', get_label="name", allow_blank=True, validators=[valid_sale_range])
      join_dealer = SelectField(u'是否加盟', coerce=int, choices=[(1, '是'), (0, '否')])
      is_anonymous = SelectField('是否禁用', coerce=int, choices=[(1, '是'), (0, '否')])
  ```

- **`route에서 form객체를 셀렉트필드 초기화` 함수를 호출한다.**

  ```python
  @organization.route('/user/new', methods=['GET', 'POST'])
  def user_new():
      if request.method == 'POST':
          try:
              form = UserForm(request.form, meta={'csrf_context': session})
              form.reset_select_field()
              app.logger.info("form: [%s]" %  form.join_dealer.data)
  
  ```

  





- sale range는 **외부에서 level과 parent_id를 입력받아 dynamic query를 구성한다**

  - 특정 level에 대한 dynamic query를 구성한다

    - **parent_id가 만약에 주어진다면, 그 부모하의 해당 level 을 필터링하도록 한다**

    ```python
    def get_dynamic_sale_range_query(level_grade, parent_id=None):
        sahs = SalesAreaHierarchy.query.filter(SalesAreaHierarchy.level_grade == level_grade)
        if parent_id is not None:
            sahs = sahs.filter_by(parent_id=parent_id)
    
        return sahs.order_by(SalesAreaHierarchy.id).all()
    ```

  - baseform에서는 외부인자를 받기 위해 cls 메서드로 정의한다

    ```python
    class BaseForm(Form):
        def reset_select_field(self):
            self.dept_ranges.query = get_dynamic_dept_ranges_query()
            self.sale_range_province.query = get_dynamic_sale_range_query(3)
            self.sale_range.query = get_dynamic_sale_range_query(4)
    
        @classmethod
        def get_sale_range_by_parent(cls, level_grade, parent_id):
            return get_dynamic_sale_range_query(level_grade, parent_id)
    
    ```

  - **항상오늘 level은 path로 받고, 안올 수도 있는 parent_id는 querystring으로 받아 사용한다**

    ```python
    @organization.route('/user/get_sale_range_by_parent/<int:level_grade>')
    def get_sale_range_by_parent(level_grade):
        parent_id = request.args.get('parent_id', '__None')
        if parent_id == "__None":
            parent_id = None
        else:
            parent_id = int(parent_id)
    
        sa_array = {}
        for sa in BaseForm.get_sale_range_by_parent(level_grade, parent_id):
            sa_array[sa.id] = sa.name
        json_data = json.dumps(sa_array)
        app.logger.info("return from get_sale_range_by_province [%s]" % json_data)
    
        return json_data
    ```

  - view

    ```js
    	//organization.user 
    	$("#select_sale_range_province").change(function(){
    		var province_id=$(this).children('option:selected').val()
    		var level_grade=4
    		var data = {
    			"parent_id":province_id,
    		};
    		$.ajax({
    			type: 'GET',
    			url: '/organization/user/get_sale_range_by_parent/'+level_grade,
    			data: data, 
    			dataType: 'json', 
    			beforeSend:function(){
    				$("#loading").css("display", "");
    				$("#select_sale_range").attr("disabled","disabled");
    			},
    			success: function(json_array) { 
    				var json = eval(json_array);
    				$("#select_sale_range option").remove()
    				$("#select_sale_range").append("<option selected value='__None'></option>");
    				$.each(json, function (key,value) {
    					$("#select_sale_range").append("<option value='"+key+"'>"+value+"</option>");
    				}); 
    			},
    			error: function(xhr, type) {
    				alert("级联销售范围获取失败,请直接选择")
    			},
    			complete: function(xhr, type) {
    				$("#loading").css("display", "none");
    				$("#select_sale_range").removeAttr("disabled");
    			}
    		});
    	});
    })
    
    ```

    

  

###### views.py [ searchform의 이용해서 검색]

- 검색폼에 department에 대해 form에 담긴 

  - departments가 여러개로 담겨오는 경우, form.query필드`.data`에서 depart_ids를 추출하고
  - 검색 데이터가 한개도 안담아오면 -> 전체를 검색하도록 depart_ids를 form.query필드`.query`에서 depart_ids를 추출해서
    - User .join(  User.departments)  filter ( Department`. in_`)으로 검색한다

  ```python
  # --- user service ---
  @organization.route('/user/index')
  @organization.route('/user/index/<int:page>')
  def user_index(page=1):
      form = UserSearchForm(request.args)
      form.reset_select_field()
      if form.user_type.data == "None":
          form.user_type.data = "3"
  
      us = db.session.query(distinct(User.id)).filter(User.user_or_origin == form.user_type.data)
      if form.email.data:
          us = us.filter(User.email.like(form.email.data + "%"))
      if form.name.data:
          us = us.filter(User.nickname.like("%" + form.name.data + "%"))
  
      if form.user_type.data == "3":
          if form.dept_ranges.data and form.dept_ranges.data != [""]:
              dh_array = [dh_data.id for dh_data in form.dept_ranges.data]
          else:
              dh_array = [dh_data.id for dh_data in form.dept_ranges.query]
          us = us.join(User.departments).filter(DepartmentHierarchy.id.in_(dh_array))
      else:
          if form.sale_range.data and form.sale_range.data != "" and form.sale_range.data != "None":
              us = us.join(User.sales_areas).filter(SalesAreaHierarchy.id == form.sale_range.data.id)
  
      us = User.query.filter(User.id.in_(us)).order_by(User.id)
      pagination = us.paginate(page, PAGINATION_PAGE_NUMBER, False)
  
      return render_template('organization/user_index.html', user_type=form.user_type.data, user_infos=pagination.items,
                             pagination=pagination, form=form)
  ```



###### 복수department를 route에서 add/update 등 => User.관계속성.append()/remove()/extends 등을 활용





- user 생성시 **department를 여러개 선택할 경우, Many관계속성(list취급).append (   ) 해준다.**

  - form.query필드`.data`에 담긴 배열을 순회하면서

    - 개별 department를 .first()로 가져와서
    - 해당user에 .add( )해준다

    ```python
    @organization.route('/user/new', methods=['GET', 'POST'])
    def user_new():
        if request.method == 'POST':
            try:
                form = UserForm(request.form, meta={'csrf_context': session})
                form.reset_select_field()
                app.logger.info("form: [%s]" %  form.join_dealer.data)
    
                if form.nickname.data == "":
                    form.nickname.data = form.name.data
    
                if form.validate() is False:
                    app.logger.info("form valid fail: [%s]" % form.errors)
                    raise ValueError(form.errors)
    
                if User.query.filter_by(email=form.email.data).first():
                    raise ValueError("邮箱[%s]已被注册,请更换!" % form.email.data)
    
                ui = UserInfo(name=form.name.data, telephone=form.phone.data, address=form.address.data,
                              title=form.title.data)
    
    
                u = User(email=form.email.data, user_or_origin=int(form.user_type.data), nickname=form.nickname.data)
                u.password = form.password.data
                u.user_infos.append(ui)
    
                u.set_join_dealer(str(form.join_dealer.data))
    
                if form.user_type.data == "3":
                    app.logger.info("into 3 : [%s]" % form.dept_ranges.data)
                    for dh_data in form.dept_ranges.data:
                        dh = DepartmentHierarchy.query.filter_by(id=dh_data.id).first()
                        if dh is None:
                            raise ValueError("所属部门错误[%s]" % dh_data.id)
                        u.departments.append(dh)
                else:
                    app.logger.info("into 2 : [%s]" % form.sale_range.data.id)
                    sah = SalesAreaHierarchy.query.filter_by(id=form.sale_range.data.id).first()
                    if sah is None:
                        raise ValueError("销售区域错误[%s]" % form.sale_range.data.name)
                    u.sales_areas.append(sah)
    
                u.save
    
                flash("添加 %s,%s 成功" % (u.email, u.nickname))
                # return render_template('organization/user_new.html', form=form)
                return redirect(url_for('organization.user_index'))
            except Exception as e:
                flash(e)
                app.logger.info("organization.user_new exception [%s]" % (traceback.print_exc()))
    
                return render_template('organization/user_new.html', form=form)
        else:
            form = UserForm(meta={'csrf_context': session})
            form.reset_select_field()
            form.is_anonymous.data = 0
            return render_template('organization/user_new.html', form=form)
    ```

- **`복수`인 user의 departments에다가 `update로서 department가 추가/삭제`된다면**

  - `.data`에 현재 depart가 없으면 **`u.departs 복수.remove( d )`**
    - **현재부서도 이중for문으로 순회하면서 처리해야한다**
- **지우고 난 나머지는 `u.남은departs.extends( .data )`로 추가한다**
  
  ```python
  @organization.route('/user/update/<int:user_id>', methods=['GET', 'POST'])
  def user_update(user_id):
      u = User.query.filter_by(id=user_id).first()
      if u is None:
          flash("非法用户id")
          return redirect(url_for('organization.user_index'))
      auth_msg = current_user.authority_control_to_user(u)
      if auth_msg is not None:
          flash(auth_msg)
          return redirect(url_for('organization.user_index'))
  
      if request.method == 'POST':
          try:
              form = UserForm(request.form, user_type=u.user_or_origin, meta={'csrf_context': session})
              form.reset_select_field()
  
              app.logger.info("user_type[%s] , password[%s]" % (form.user_type.data, form.password_confirm.data))
              if form.nickname.data == "":
                  form.nickname.data = form.name.data
  
              if form.validate() is False:
                  app.logger.info("form valid fail: [%s]" % form.errors)
                  raise ValueError(form.errors)
  
              u.email = form.email.data
              u.nickname = form.nickname.data
  
              if len(u.user_infos) == 0:
                  ui = UserInfo()
              else:
                  ui = u.user_infos[0]
  
              ui.name = form.name.data
              ui.telephone = form.phone.data
              ui.address = form.address.data
              ui.title = form.title.data
  
              u.set_join_dealer(str(form.join_dealer.data))
  
              # 只有 admin 才能修改用户是否禁用
              if current_user.get_max_level_grade() == 1:
                  u.set_is_anonymous(str(form.is_anonymous.data))
  
              if len(u.user_infos) == 0:
                  u.user_infos.append(ui)
  
              if u.user_or_origin == 3:
                  dh_array = [dh_data.id for dh_data in form.dept_ranges.data]
                  if sorted([i.id for i in u.departments]) != sorted(dh_array):
                      for d in u.departments:
                          # 判断是否存在 管理的销售区域,不允许修改掉
                          if d.name == "销售部" and d not in form.dept_ranges.data:
                              if u.sales_areas.first():
                                  raise ValueError("此用户尚有管理的销售地区,请在'组织架构及权限组模块'中先行删除")
                          u.departments.remove(d)
                      # for d_id in dh_array:
                      # u.departments.append(DepartmentHierarchy.query.filter_by(id=d_id).first())
                      u.departments.extend(form.dept_ranges.data)
                      cache.delete_memoized(u.is_authorized)
                      app.logger.info("delete user.is_authorized cache")
              else:
                  if u.sales_areas.count() == 0 or u.sales_areas.first().id != form.sale_range.data.id:
                      if not u.sales_areas.count() == 0:
                          u.sales_areas.remove(u.sales_areas.first())
                      sah = SalesAreaHierarchy.query.filter_by(id=form.sale_range.data.id).first()
                      u.sales_areas.append(sah)
  
              u.save
  
              flash("修改 %s,%s 成功" % (u.email, u.nickname))
              # return render_template('organization/user_update.html', form=form, user_id=u.id)
              return redirect(url_for('organization.user_update', user_id=u.id))
          except ValueError as e:
              flash(e)
              return render_template('organization/user_update.html', form=form, user_id=u.id)
      else:
          form = UserForm(obj=u, user_type=u.user_or_origin, meta={'csrf_context': session})
          form.reset_select_field()
          if len(u.user_infos) == 0:
              pass
          else:
              ui = u.user_infos[0]
              form.name.data = ui.name
              form.address.data = ui.address
              form.phone.data = ui.telephone
              form.title.data = ui.title
  
              app.logger.info("join_delaer: [%s]" % form.join_dealer.default)
          if u.sales_areas.first() is not None:
              form.sale_range.default = u.sales_areas.first().id
          if u.departments.first() is not None:
              form.dept_ranges.default = u.departments.all()
  
          if u.is_join_dealer():
              form.join_dealer.data = 1
          else:
              form.join_dealer.data = 0
  
          if u.is_anonymous():
              form.is_anonymous.data = 1
          else:
              form.is_anonymous.data = 0
  
          return render_template('organization/user_update.html', form=form, user_id=u.id)
  ```







#### 4 [ItManHarry](https://github.com/ItManHarry)/**[blog](https://github.com/ItManHarry/blog)**Public



##### model -> root여부 필드를 추가 + path개념을 code필드로 구성

- root여부를 boolean으로
- **parent 속성**을 i`f self.parent_id가 존재하면  parent객체를 호출하도록 .get()  query`로 구성 아니면 None
- **children 속성**을 name순으로 `내가 parent_id인 것들을 골라서 .all() query`로  구성

```python
class BizDepartment(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    code = db.Column(db.String(24))
    name = db.Column(db.String(128))
    root = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.String(32))
    @property
    def parent(self):
        return BizDepartment.query.get(self.parent_id) if self.parent_id else None
    @property
    def children(self):
        return BizDepartment.query.filter(BizDepartment.parent_id == self.id).order_by(BizDepartment.name).all()
```



##### form => parent_id 필드를 옵셔널로 구성

- parent를 optional로 구성

```python
class DepartmentForm(FlaskForm):
    id = HiddenField()
    name = StringField('部门名称', validators=[DataRequired('请输入部门名称！！！'), Length(1, 128, '部门名称字数请保持在1-128之间!!!')])
    root = BooleanField('顶级部门')
    parents = SelectField('上级部门', [validators.optional()], choices=[])
```





##### views

- add

  - **form에서 `parend_id가 None`으로 안들어오면, `root로서 root = True`를 넣어준다 **

  - root면, 코드앞에 `""`빈문자열 + **현재존재하면 root department만큼의 len()을 구해 code로 등록한다**

  - root가 아니면, parent department를 찾고, `parent.code` + parent를  parent로 가지는 `나와 동급레벨의 parent자식들`갯수를 len으로 세서 코드를 만들어준다

    ```python
    @bp_department.route('/add', methods=['GET', 'POST'])
    @login_required
    def add():
        form = DepartmentForm()
        form.parents.choices = [(department.id, department.name) for department in BizDepartment.query.order_by(BizDepartment.code).all()]
        if form.validate_on_submit():
            name = form.name.data
            root = form.root.data
            parent_id = form.parents.data
            if parent_id is None:
                root = True
            if root:
                code = generate_code('', len(BizDepartment.query.filter(BizDepartment.root == True).all()))
            else:
                parent = BizDepartment.query.get(parent_id)
                code = generate_code(parent.code, len(BizDepartment.query.filter(BizDepartment.parent_id == parent_id).all()))
            print('Department name is {}, is root {}, parent id {}.'.format(name, root, parent_id))
            department = BizDepartment(
                id=uuid.uuid4().hex,
                code=code,
                name=name,
                root=root,
                parent_id=parent_id if parent_id and not root else ''
            )
            db.session.add(department)
            db.session.commit()
            flash('部门信息添加成功!')
            return redirect(url_for('.index'))
        return render_template('department/edit.html', form=form)
    ```

    ```python
    def generate_code(parent_cd, parent_size):
        if parent_size < 10:
            return parent_cd+'0'+str(parent_size)
        else:
            return parent_cd+str(parent_size)
    ```

    

  - index

    - code를 기준으로 정렬한다.

    ```python
    @bp_department.route('/index', methods=['GET', 'POST'])
    @login_required
    def index():
        departments = BizDepartment.query.order_by(BizDepartment.code).all()
        return render_template('department/index.html', departments=departments)
    ```

  - edit

    - 현재 department의 id에 대해 form을 채워줄때는 
      - **나를 제외하고 and, 나의 자식들(parent_id 가 나)를 제외하고 form의  choice에 담아준다**

    - **root로 변경한다면, 나의 parent_id를 비워준다**
      - root가 아니라면, 선택된 parent_id를 넣어준다

    ```python
    @bp_department.route('/edit/<id>', methods=['GET', 'POST'])
    @login_required
    def edit(id):
        department = BizDepartment.query.get(id)
        form = DepartmentForm()
        # 剔除自身及子部门
        form.parents.choices = [(department.id, department.name) for department in BizDepartment.query.filter(BizDepartment.id != id, BizDepartment.parent_id != id).order_by(BizDepartment.code).all()]
        if request.method == 'GET':
            form.name.data = department.name
            form.root.data = department.root
            form.parents.data = department.parent_id
        if form.validate_on_submit():
            department.name = form.name.data
            department.root = form.root.data
            if form.root.data:
                department.parent_id = ''
            else:
                department.parent_id = form.parents.data
            db.session.commit()
            flash('部门信息编辑成功!')
            return redirect(url_for('.index'))
        return render_template('department/edit.html', form=form)
    ```

    ![image-20221224170751842](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221224170751842.png)

    

##### THEME 처리 참고) response에 쿠키로 theme를 담아보내고, 그것에 따라 url_for를 변수화해서 

```python
#主题切换
@bp_blog.route('/theme/<theme_name>')
def theme(theme_name):
    if theme_name not in current_app.config['BLOG_THEMES'].keys():
        abort(404)
    response = make_response(redirect_back())
    response.set_cookie('theme', theme_name, max_age=30*24*60*60)
    return response
```

```html
<!-- 宏加载静态资源文件 -->
{% macro static_file(type, file_or_url, local=True) %}
    {% if local %}
        {% set file_or_url = url_for('static', filename = file_or_url) %}
    {% endif %}
    {% if type == 'css' %}
        <link rel = "stylesheet" type = "text/css" href = "{{file_or_url}}">
    {% endif %}
    {% if type == 'icon' %}
        <link rel = "icon" type = "image/x-icon" href = "{{file_or_url}}">
    {% endif %}
    {% if type == 'js' %}
        <script type = "text/javascript" src = "{{file_or_url}}"></script>
    {% endif %}
{% endmacro %}
```



```jinja2
{% from 'macros/macros.html' import static_file with context %}

{{static_file('css','css/themes/%s.min.css' %request.cookies.get('theme', 'bootstrap'))}}

```

![image-20221224171536228](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221224171536228.png)













#### 5 **[pittsburgh-purchasing-suite](https://github.com/codeforamerica/pittsburgh-purchasing-suite)**Public archive

##### 참고 지져스 Mixin + opertionahistory용 Listen 총정리

- https://github.com/codeforamerica/pittsburgh-purchasing-suite/blob/9552eda6df396746feedc9ce45f35842a716de6a/purchasing/database.py#L57

##### 참고 컨피그에 S3 등 다 있음

##### Department가 아니라 ContractBase에 parent_id가 있고, parent = aliaed()를 활용해서 subquery를 만들어 부모정보를 join한다

```python
contract_user_association_table = Table(
    'contract_user_association', Model.metadata,
    Column('user_id', db.Integer, db.ForeignKey('users.id'), index=True),
    Column('contract_id', db.Integer, db.ForeignKey('contract.id'), index=True),
)

class ContractBase(RefreshSearchViewMixin, Model):
    '''Base contract model

    Attributes:
        id: Primary key unique ID
        financial_id: Financial identifier for the contract.
            In Pittsburgh, this is called the "controller number"
            because it is assigned by the City Controller's office
        expiration_date: Date when the contract expires
        description: Short description of what the contract covers
        contract_href: Link to the actual contract document
        followers: A many-to-many relationship with
            :py:class:`~purchasing.users.models.User` objects
            for people who will receive updates about when the
            contract will be updated
        is_archived: Whether the contract is archived. Archived
            contracts do not appear by default on Scout search

        contract_type_id: Foreign key to
            :py:class:`~purchasing.data.contracts.ContractType`
        contract_type: Sqlalchemy relationship to
            :py:class:`~purchasing.data.contracts.ContractType`
        department_id: Foreign key to
            :py:class:`~purchasing.users.models.Department`
        department: Sqlalchemy relationship to
            :py:class:`~purchasing.users.models.Department`

        opportunity: An :py:class:`~purchasing.opportunities.models.Opportunity`
            created via conductor for this contract

        is_visible: A flag as to whether or not the contract should
            be visible in Conductro
        assigned_to: Foreign key to
            :py:class:`~purchasing.users.models.User`
        assigned: Sqlalchemy relationship to
            :py:class:`~purchasing.users.models.User`
        flow_id: Foreign key to
            :py:class:`~purchasing.data.flows.Flow`
        current_flow: Sqlalchemy relationship to
            :py:class:`~purchasing.data.flows.Flow`
        current_stage_id: Foreign key to
            :py:class:`~purchasing.data.stages.Stage`
        current_stage: Sqlalchemy relationship to
            :py:class:`~purchasing.data.stages.Stage`
        parent_id: Contract self-reference. When new work is started
            on a contract, a clone of that contract is made and
            the contract that was cloned is assigned as the new
            contract's ``parent``
        children: A list of all of this object's children
            (all contracts) that have this contract's id as
            their ``parent_id``
    '''
    __tablename__ = 'contract'

    # base contract information
    id = Column(db.Integer, primary_key=True)
    financial_id = Column(db.String(255))
    expiration_date = Column(db.Date)
    description = Column(db.Text, index=True)
    contract_href = Column(db.Text)
    followers = db.relationship(
        'User',
        secondary=contract_user_association_table,
        backref='contracts_following',
    )
    is_archived = Column(db.Boolean, default=False, nullable=False)

    # contract type/department relationships
    contract_type_id = ReferenceCol('contract_type', ondelete='SET NULL', nullable=True)
    contract_type = db.relationship('ContractType', backref=backref(
        'contracts', lazy='dynamic'
    ))
    department_id = ReferenceCol('department', ondelete='SET NULL', nullable=True, index=True)
    department = db.relationship('Department', backref=backref(
        'contracts', lazy='dynamic', cascade='none'
    ))

    opportunity = db.relationship('Opportunity', uselist=False, backref='opportunity')

    # conductor information
    is_visible = Column(db.Boolean, default=True, nullable=False)
    assigned_to = ReferenceCol('users', ondelete='SET NULL', nullable=True)
    assigned = db.relationship('User', backref=backref(
        'assignments', lazy='dynamic', cascade='none'
    ), foreign_keys=assigned_to)
    flow_id = ReferenceCol('flow', ondelete='SET NULL', nullable=True)
    current_flow = db.relationship('Flow', lazy='joined')
    current_stage_id = ReferenceCol('stage', ondelete='SET NULL', nullable=True, index=True)
    current_stage = db.relationship('Stage', lazy='joined')
    parent_id = Column(db.Integer, db.ForeignKey('contract.id'))
    children = db.relationship('ContractBase', backref=backref(
        'parent', remote_side=[id], lazy='subquery'
    ))
```

- user

```python
class User(UserMixin, SurrogatePK, Model):
	#...
    department_id = ReferenceCol('department', ondelete='SET NULL', nullable=True)
    department = db.relationship(
        'Department', backref=backref('users', lazy='dynamic'),
        foreign_keys=department_id, primaryjoin='User.department_id==Department.id'
    )

    @classmethod
    def department_user_factory(cls, department_id):
        return cls.query.filter(
            cls.department_id == department_id,
            db.func.lower(Department.name) != 'equal opportunity review commission'
        )
```



##### model (no parent_id)  => query_factory를 만들어서 미리 피터링 할 것 있으면 하도록 =>  choices를 blank들어서 준다.

```python
class Department(SurrogatePK, Model):
    '''Department model
    Attributes:
        name: Name of department
    '''
    __tablename__ = 'department'

    name = Column(db.String(255), nullable=False, unique=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def query_factory(cls):
        '''Generate a department query factory.
        Returns:
            Department query with new users filtered out
        '''
        return cls.query.filter(cls.name != 'New User')

    @classmethod
    def get_dept(cls, dept_name):
        '''Query Department by name.
        Arguments:
            dept_name: name used for query
        Returns:
            an instance of Department
        '''
        return cls.query.filter(db.func.lower(cls.name) == dept_name.lower()).first()

    @classmethod
    def choices(cls, blank=False):
        '''Query available departments by name and id.
        Arguments:
            blank: adds none choice to list when True,
                only returns Departments when False. Defaults to False.
        Returns:
            list of (department id, department name) tuples
        '''
        departments = [(i.id, i.name) for i in cls.query_factory().all()]
        if blank:
            departments = [(None, '-----')] + departments
        return 
```







##### form queryselectfield 구성을 희한하게 함. cls로 정의한 query_factory도 사용

```python
class UserAdmin(AuthMixin, BaseModelViewAdmin):
    form_columns = ['email', 'first_name', 'last_name', 'department', 'role']

    form_extra_fields = {
        'department': sqla.fields.QuerySelectField(
            'Department', query_factory=Department.query_factory,
            allow_blank=True, blank_text='-----'
        ),
        'role': sqla.fields.QuerySelectField(
            'Role', query_factory=Role.no_admins,
            allow_blank=True, blank_text='-----'
        )
    }

    def get_query(self):
        '''Override default get query to limit to assigned contracts
        '''
        return super(UserAdmin, self).get_query().join(
            Role, User.role_id == Role.id
        ).filter(
            db.func.lower(Role.name) != 'superadmin'
        )

    def get_count_query(self):
        '''Override default get count query to conform to above
        '''
        return super(UserAdmin, self).get_count_query().join(
            Role, User.role_id == Role.id
        ).filter(
            db.func.lower(Role.name) != 'superadmin'
        )

class UserRoleAdmin(SuperAdminMixin, BaseModelViewAdmin):
    form_columns = ['email', 'first_name', 'last_name', 'department', 'role']

    form_extra_fields = {
        'department': sqla.fields.QuerySelectField(
            'Department', query_factory=Department.query_factory,
            allow_blank=True, blank_text='-----'
        ),
        'role': sqla.fields.QuerySelectField(
            'Role', query_factory=Role.query_factory,
            allow_blank=True, blank_text='-----'
        )
    }

```

```python
class NewContractForm(Form):
    '''Form for starting new work on a contract through conductor

    Attributes:
        description: The contract's description
        flow: The :py:class:`~purchasing.data.flows.Flow` the
            contract should follow
        assigned: The :py:class:`~purchasing.users.models.User`
            the contract should be assigned to
        department: The :py:class:`~purchasing.users.models.Department`
            the contract should be assigned to
        start: The start time for the first
            :py:class:`~purchasing.data.contract_stages.ContractStage`
            for the contract
    '''
    description = TextField(validators=[DataRequired()])
    flow = QuerySelectField(
        query_factory=Flow.nonarchived_query_factory,
        get_pk=lambda i: i.id,
        get_label=lambda i: i.flow_name,
        allow_blank=True, blank_text='-----'
    )
    assigned = QuerySelectField(
        query_factory=User.conductor_users_query,
        get_pk=lambda i: i.id,
        get_label=lambda i: i.email,
        allow_blank=True, blank_text='-----'
    )
    department = QuerySelectField(
        query_factory=Department.query_factory,
        get_pk=lambda i: i.id,
        get_label=lambda i: i.name,
        allow_blank=True, blank_text='-----'
    )
    start = DateTimeField(default=get_default)
```





##### 복잡한 SQL과 sqlalchemy

###### ContractBase의 subquery에 id + 부모속성 + 부모객체를 얻어놓고 outerjoin하기

- **index.py** (`ContractBase`에 대한 것인 듯)

  - subquery => **parent정보를 `parent_specs`의 subquery로 만든다**

    - parent로서 aliased(ContraceBase)를 만들어놓는다.
    - ContractBase에
      - ContractProperty(key, value)을 join하는데, **ContractBase의 parent_id의 property를 `join`한다**
        - 기본적으로 `내.id`가 있고,  **`다음에 붙일 parent를 위해, 내.부모_id와 일차하는 ContractProperty를 미리 붙임`**
        - parent를 join하되 parent에 parent의 속성까지 붙인 상태로 join하지말고, **나의 부모의 정보(계약속성)을 먼저 붙이고 -> 부모도 붙이는 작전?**
      - 자신의 **parent를 `join`**하는데, ContractBase.parent로 제시하면 된다
      - **없을 수도 있는** MN관계인 **Company를 outerjoin**하는데, 내가 아니라 부모의 Company를 join하기 위해 **parent(부모관계객체).companes(MN관계객체)**를 joinkey로 던져준다
      - join된 ContractProperty가 있는데, **부모의 ContractProperty가 join된 상태인데 filter를 그냥 Entity로 걸어서** 중 (부모의)ContractProperty.key 를 db.fun.lower()한 뒤, spec_number가 동일하고 +  내가 이미 ContractBase로서 fk를 가지고 있는 One인 ContractType을 필드를 join없이 바로 필터로 건다

  - in_progress 

    - 연결키가 없을 수 있는 (주체가 부서를 안가질 수 있는) **Department를 outerjoin**한 뒤

    - 나(Contract) - Stage에게 MN으로 딸린 하위 **ContractStage(관계테이블이자 new테이블)를 join**하되
      - 조건을, MN 관계테이블.stage_id == 나의 현재 stage_id
      - 관계테이블.contract_id == 나의.id
      - 관계테이블.flow_id  == 나의.flow_id
      - **JOIN을 MN관계로하면 카사디안곱되니까, `나와는 1:M관계인 관계테이블을 join시켜 outerjoin처럼.. (전체)one에 (많지만 일부라 곱x)Many를 붙인다?**
    - Stage만의 정보도 얻기 위해 join
    - Flow정보 join
    - **subquery와 달리**, 나의 **ContractProperty**를 **outerjoin**
      - 주체인 나의 경우 **하위entity(속성)을 가지는 놈도 있을 수 있어서?** join은 left에 연결key가 없는 경우 삭제되기 때문에, **하위entity를 right로 붙이되, 하위정보가 없는 놈도 주체로서 살릴 때는 outerjoin** =>  subquery 부모contract는 속성없는 놈들은 날라간 상태임?!
    - **`부모속성, 부모`를 소유한 `내.id기준 subquery ==parent_spect`를 outerjoin하며 `joinkey는 내.id == 내.id와 동시에 부모속성, 부모id를 소유한subq.c.내id`**로 연결하여, **주제entity의 `각 id들이 가지는 부모정보, 부모`를 해당id에 붙여준다**

    - One에 해당하는 User를 그냥 join해준다(주체entity는 user의 하위라서 join시 key연결 안되어 사라질 데이터가 없음)
    - Where조건을
      - 나의  flow_id == MN 테이블.flow_id
      - MN테이블.entered 가 none아님
      - 나.assigned_to가 none아님 
      - 나의 visible = False
      - 나의 is_archived False
    - group_by
      - 내id별
      - 내 속의 value(spec_number)별
      - 내 부모의 value(parent_spec)별
      - 내 부모의 만료기한 별
      - 내 부모의 계약href별
      - 내 descriptjon 별
      - Flow의 flow_name별
      - Stage name별
      - ContractStage.entered여부별
      - User의 first_name별
      - user의 email별
      - Department의 name별 
    - distinct(내.id)별 각 groupby별 **db.func.array_removed( db.func.array_agg( 부모스펙.c.company_name)**, None) 
      - **id별 모든 종류별 `company_name`을 집계**

    ```python
    @blueprint.route('/')
    @requires_roles('conductor', 'admin', 'superadmin')
    def index():
        '''Main conductor index page/splash view
    
        Renders two tables that conductors can use to track their progress:
        ``in_progress``, which contains all of the
        :py:class:`~purchasing.data.contracts.ContractBase` objects that are
        currently being worked on by a conductor. ``in_progress`` contracts
        are generated by selecting only :py:class:`~purchasing.data.contracts.ContractBase`
        objects that have a ``parent_id``, have an existing ``flow``,
        non-null ``entered`` current contract stage, and are neither ``is_archived`` nor
        ``is_visible``.
    
        ``all_contracts`` contains all contracts that are eligible
        to show up in conductor to be worked on. These are filtered based on the
        :py:class:`~purchasing.data.contracts.ContractType`
        ``managed_by_conductor`` field. Additionally, these are
        filtered by having no ``children``, and ``is_visible`` set to True
    
        .. seealso:: :py:class:`~purchasing.data.contracts.ContractBase`,
            :py:class:`~purchasing.data.contract_stages.ContractStage`,
            :py:class:`~purchasing.data.flows.Flow`
    
        :status 200: Render the main conductor index page
        '''
        parent = aliased(ContractBase)
    
        parent_specs = db.session.query(
            ContractBase.id, ContractProperty.value,
            parent.expiration_date, parent.contract_href,
            Company.company_name
        ).join(
            ContractProperty,
            ContractBase.parent_id == ContractProperty.contract_id
        ).join(
            parent, ContractBase.parent
        ).outerjoin(
            Company, parent.companies
        ).filter(
            db.func.lower(ContractProperty.key) == 'spec number',
            ContractType.managed_by_conductor == True
        ).subquery()
    
        in_progress = db.session.query(
            db.distinct(ContractBase.id).label('id'),
            ContractProperty.value.label('spec_number'),
            parent_specs.c.value.label('parent_spec'),
            parent_specs.c.expiration_date.label('parent_expiration'),
            parent_specs.c.contract_href.label('parent_contract_href'),
            ContractBase.description, Flow.flow_name,
            Stage.name.label('stage_name'), ContractStage.entered,
            User.first_name, User.email,
            Department.name.label('department'),
            db.func.array_remove(
                db.func.array_agg(parent_specs.c.company_name),
                None
            ).label('companies')
        ).outerjoin(Department).join(
            ContractStage, db.and_(
                ContractStage.stage_id == ContractBase.current_stage_id,
                ContractStage.contract_id == ContractBase.id,
                ContractStage.flow_id == ContractBase.flow_id
            )
        ).join(
            Stage, Stage.id == ContractBase.current_stage_id
        ).join(
            Flow, Flow.id == ContractBase.flow_id
        ).outerjoin(
            ContractProperty, ContractProperty.contract_id == ContractBase.id
        ).outerjoin(
            parent_specs, ContractBase.id == parent_specs.c.id
        ).join(User, User.id == ContractBase.assigned_to).filter(
            ContractStage.flow_id == ContractBase.flow_id,
            ContractStage.entered != None,
            ContractBase.assigned_to != None,
            ContractBase.is_visible == False,
            ContractBase.is_archived == False
        ).group_by(
            ContractBase.id,
            ContractProperty.value.label('spec_number'),
            parent_specs.c.value.label('parent_spec'),
            parent_specs.c.expiration_date.label('parent_expiration'),
            parent_specs.c.contract_href.label('parent_contract_href'),
            ContractBase.description, Flow.flow_name,
            Stage.name.label('stage_name'), ContractStage.entered,
            User.first_name, User.email,
            Department.name.label('department')
        ).all()
    ```

    

  - all_contracts

    - One인 **ContractType**을 **join**
    - **One이지만 fk nullable=True한 User**는 User를 안가지는 주체Entity(ContractBase)가 있을 수 있기 때문에 **outerjoin**
      - User.id == ContractBase.**assgined_to**
    - MN관계인 company를 Outerjoin
      - MN관계는 당연히 주체입장에서는 **1:M에서 (많지만 나의 일부범위)many가 join되는 것으로 연결key에 내가 없을 수 있기 때문에 outerjoin**
    - **One이지만 fk nullable=True한 Department**는 outerjoin
    - 나의 하위 Many인 **ContractProperty**는 Outerjoin
    - where
      - 계약타입에 감독관이 있으면서
      - 계약속성에 spec number면서
      - **계약에 (하위계약) children이 없는 최종 계약으로서**
      - is_visible한 것
    - groupby
      - id별 description별 financial_id별 만료기한별 value별
      - 계약href별, 계약부서별, 유저이름별, 유저메일별
    - select
      - **company_name의 집합**

    ```python
    all_contracts = db.session.query(
        ContractBase.id, ContractBase.description,
        ContractBase.financial_id, ContractBase.expiration_date,
        ContractProperty.value.label('spec_number'),
        ContractBase.contract_href, ContractBase.department,
        User.first_name, User.email,
        db.func.array_remove(
            db.func.array_agg(Company.company_name),
            None
        ).label('companies')
    ).join(ContractType).outerjoin(
        User, User.id == ContractBase.assigned_to
    ).outerjoin(Company, ContractBase.companies).outerjoin(
        Department, Department.id == ContractBase.department_id
    ).outerjoin(
        ContractProperty, ContractProperty.contract_id == ContractBase.id
    ).filter(
        ContractType.managed_by_conductor == True,
        db.func.lower(ContractProperty.key) == 'spec number',
        ContractBase.children == None,
        ContractBase.is_visible == True
    ).group_by(
        ContractBase.id, ContractBase.description,
        ContractBase.financial_id, ContractBase.expiration_date,
        ContractProperty.value.label('spec_number'),
        ContractBase.contract_href, ContractBase.department,
        User.first_name, User.email
    ).order_by(ContractBase.expiration_date).all()
    ```





##### ContractBase는 자신의 self.department_id로 build_scribers들을 구성한다?!

- ContractBase

  - **build_subscribers** 

    - **인스턴스메서드로서 각 계약 객체마다 `자신의 부서`를 인자로해서 `User Entity`를 이용하여 해당 department_user를 구할 수 있다.**

      ```python
      def build_subscribers(self):
          '''Build a list of subscribers and others to populate contacts in conductor
              '''
          department_users, county_purchasers, eorc = User.get_subscriber_groups(self.department_id)
      
          if self.parent is None:
              followers = []
              else:
                  followers = [i for i in self.parent.followers if i not in department_users]
      
                  subscribers = {
                      'Department Users': department_users,
                      'Followers': followers,
                      'County Purchasers': [i for i in county_purchasers if i not in department_users],
                      'EORC': eorc
                  }
                  return subscribers, sum([len(i) for i in subscribers.values()])
      ```

- User

  - **get_subscriber_groups**

    - **class method로서, cls(User)를 이용한 `타entity_현entity_factory`를 구성하되 department_id를 외부(계약이 속한 department_id)에서 입력받아 데이터를 list로 출력받는다**

    ```python
        @classmethod
        def get_subscriber_groups(cls, department_id):
            return [
                cls.department_user_factory(department_id).all(),
                cls.county_purchaser_factory().all(),
                cls.eorc_user_factory().all()
            ]
    
    ```

  - **department_user_factory**

    - class method로서, cls(User)를 이용한 **`외부입력 department_id`를 입력받아서, cls(User)가 가진 .department_idㅇ가 같은 user를 반환해줄 것이다.**

    ```python
    @classmethod
    def department_user_factory(cls, department_id):
        return cls.query.filter(
            cls.department_id == department_id,
            db.func.lower(Department.name) != 'equal opportunity review commission'
        )
    ```





- route에서는 contract_id를 받아서

  - contract를 구하고

    - 계약에 관계된 사람들을 구하자고 호출하면
    - 계약이 가지고 있는 department_id => 해당 department_id를 가진  user를 들고와서 반환한다

    ```python
    @blueprint.route('/contract/<int:contract_id>', methods=['GET', 'POST'])
    @blueprint.route('/contract/<int:contract_id>/stage/<int:stage_id>', methods=['GET', 'POST'])
    @requires_roles('conductor', 'admin', 'superadmin')
    def detail(contract_id, stage_id=-1):
        contract = ContractBase.query.get(contract_id)
        if not contract:
            abort(404)
            
        # ...
        subscribers, total_subscribers = contract.build_subscribers()
    
    ```

    

##### DepartmentForm의 QuerySelectField의 옵션엔 query_factory 이외에 pk, label, blank도 정해줄 수 있다.

```python
# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms.fields import TextField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from purchasing.users.models import Department

class DepartmentForm(Form):
    '''Allows user to update profile information

    Attributes:
        department: sets user department based on choice of available
            departments or none value
        first_name: sets first_name value based on user input
        last_name: sets last_name value based on user input
    '''
    department = QuerySelectField(
        query_factory=Department.query_factory,
        get_pk=lambda i: i.id,
        get_label=lambda i: i.name,
        allow_blank=True, blank_text='-----'
    )
    first_name = TextField()
    last_name = TextField()

```



##### User모델의 department를 nullable=True, ondelete='SET NULL'로 준다

```python
class User(UserMixin, SurrogatePK, Model):
    '''User model

    Attributes:
        id: primary key
        email: user email address
        first_name: first name of user
        last_name: last name of user
        active: whether user is currently active or not
        role_id: foreign key of user's role
        role: relationship of user to role table
        department_id: foreign key of user's department
        department: relationship of user to department table
    '''

    __tablename__ = 'users'
    email = Column(db.String(80), unique=True, nullable=False, index=True)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    active = Column(db.Boolean(), default=True)

    role_id = ReferenceCol('roles', ondelete='SET NULL', nullable=True)
    role = db.relationship(
        'Role', backref=backref('users', lazy='dynamic'),
        foreign_keys=role_id, primaryjoin='User.role_id==Role.id'
    )

    department_id = ReferenceCol('department', ondelete='SET NULL', nullable=True)
    department = db.relationship(
        'Department', backref=backref('users', lazy='dynamic'),
        foreign_keys=department_id, primaryjoin='User.department_id==Department.id'
    )
    #...
```





##### filter/department_id by SQL  + FULL OUTER JOIN

![image-20221225011511572](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225011511572.png)

- 주의점

  - 둘째, 조인을 여러 번 해야하는데 **시작을 LEFT JOIN으로 했다면 보통의 경우는 나머지 조인도 LEFT JOIN**을 합니다.

  - `NULL`값에 관련 없이, 모든 테이블의 모든 행을 반환하고 싶다면 `FULL OUTER JOIN`을 사용한다

    - mariadb는 full outer join없음

      - 여의치 않을 경우, `LEFT JOIN`과 `RIGHT JOIN`의 결과셋을 `UNION`으로 포개준다

    -  **`FULL OUTER JOIN`을 명시적으로 사용하여 일치 하는 행과 함께 두 테이블에서 누락된 모든 행을 반환한다**

    - ```sql
      select d.deptno, d.dname, e.ename
      	from dept d full outer join emp e
          on d.deptno = e.deptno
      ```

      ![image-20221225013716928](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225013716928.png)

      ```sql
      select d.deptno, d.dname, e.ename
      	from dept d left join emp e
          on d.deptno = e.deptno
      UNION
      select d.deptno, d.dname, e.ename
      	from dept d right join emp e
          on d.deptno = e.deptno
      ```

      ![image-20221225013723139](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225013723139.png)

- [주의점2](https://m.blog.naver.com/alucard99/221309683468)

  - 뒤 테이블연결에 필요한 left outerjoin이 아니라 메인에 정보박아주는 용도라면 **inner다 끝나고 outerjoin을 넣어서, 교집합데이터를 다 구한 상태에서 맨 마지막에 outerjoin하자**

    ![image-20221225015431241](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225015431241.png)

  - **`left로 추가정보를 박을 때, 필요한 right데이터만` 박고 싶다면 `outerjoin 그자리에서 and 박는테이블.필드== 조건`을 추가하자.**

    - **만약, `join이 다 끝나고 where에 조건을 추가`한다면 `주체entity에서 해당조건을 만족하는 정보만 남아 교집합innerjoin`처럼 해당조건의 데이터만 남게된다.**

      ![image-20221225015802168](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225015802168.png)



- path로 온 department_id로 department 객체를 먼저 찾고, 

  - 없으면 abort(404)

- db.session.execute()로 **해당 department_id소속 contracts**를 뽑아올 수 있다.

  - from contract

  - **`Left outer join`  관계테이블**

    - contract_user_association(관계테이블) - 내입장에선 1:Many이므로 주체 entity 데이터가 안없어지게 outerjoin

    - On contract.id = contract_user_association.contract_id

      ![image-20221225014244710](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225014244710.png)

  - **`FULL outer join` 나머지N테이블**

    - users - **MN 나머지 테이블을 직접 join할 땐, 나머지entity를 MN테이블에 full outer join 한다**
      - MN테이블입장에선 user는 One이고, 관계테이블에는 없지만, **오른쪽 user테이블만 있는 user데이터는 또 살려두고 나머지를 null로 채워 날아가지 않게 붙인다?** 
    - On users.id = **contract_user_association**.user_id

    ![image-20221225014914570](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225014914570.png)

  - join

    - department - **user에 대해서는 One**이라서 join으로 데이터가 손실될 염려가 적다?
    - On **users**.department_id = department.id
    
  - **교집합의 inner join을  MN데이터 `full outer join으로 남은 user전체`에 join key를 걸어서, `부서를 가진 User데이터기준으로 남긴다`**
    
  - user에 대해 department가 있는 데이터만, department정보를 붙여서 골라낸다
  
    ![image-20221225020420635](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225020420635.png)
  
- where
  
  - 특정 `department_id`필터링하고 
  
  ![image-20221225020910096](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225020910096.png)
  
- groupby를 1,2번 칼럼인
  
  - 계약id별, description별로
  
- select 
  
  - **관계테이블 속 user_id 명수를 센다**
  
- having을 
  
    - 계약id별, description별 **계약id가 1개이상인 데이터만 집계한다**
    - right outer join된 user기준으로 join 했으므로
  - contract가 비어있는 부분도 있어서 제거한다
  
  

```python
@blueprint.route('/filter', methods=['GET'])
def filter_no_department():
    '''The landing page for filtering by departments

    :status 200: Renders the appropriate landing page.
    '''
    return render_template(
        'scout/filter.html',
        search_form=SearchForm(),
        results=[],
        choices=Department.choices(),
        path='{path}?{query}'.format(
            path=request.path, query=request.query_string
        )
    )

@blueprint.route('/filter/<int:department_id>', methods=['GET'])
def filter(department_id):
    '''Filter contracts by which ones have departmental subscribers

    :param department_id: Department's unique ID
    :status 200: Renders template with all contracts followed by that department
    :status 404: When department is not found with the specified ID
    '''
    department = Department.query.get(int(department_id))

    if department:
        pagination_per_page = current_app.config.get('PER_PAGE', 50)
        page = int(request.args.get('page', 1))
        lower_bound_result = (page - 1) * pagination_per_page
        upper_bound_result = lower_bound_result + pagination_per_page

        contracts = db.session.execute(
            '''
            SELECT
                contract.id, description,
                count(contract_user_association.user_id) AS follows
            FROM contract
            LEFT OUTER JOIN contract_user_association
                ON contract.id = contract_user_association.contract_id
            FULL OUTER JOIN users
                ON contract_user_association.user_id = users.id
            JOIN department
                ON users.department_id = department.id
            WHERE department.id = :department
            GROUP BY 1,2
            HAVING count(contract_user_association.user_id) > 0
            ORDER BY 3 DESC, 1 ASC
            ''', {'department': int(department_id)}
        ).fetchall()

        if len(contracts) > 0:
            pagination = SimplePagination(page, pagination_per_page, len(contracts))
            results = contracts[lower_bound_result:upper_bound_result]
        else:
            pagination = None
            results = []

        current_app.logger.info('WEXFILTER - {department}: Filter by {department}'.format(
            department=department.name
        ))

        return render_template(
            'scout/filter.html',
            search_form=SearchForm(),
            results=results,
            pagination=pagination,
            department=department,
            choices=Department.choices(),
            path='{path}?{query}'.format(
                path=request.path, query=request.query_string
            )
        )
    abort(404)
```





### 6 [ItManHarry](https://github.com/ItManHarry)/**[itpm](https://github.com/ItManHarry/itpm)** (admin/12341234) 

![image-20221225205153491](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225205153491.png)

#### model - parent_id를 안쓰고  Rel Entity를 따로 빼서, 부모Department - 자식Department를 다대다관계테이블에 joined로 부모/자식을  정의 + property

- 부모-자식 다대다 관계테이블

  ```python
  '''
  部门层级关系
  '''
  class RelDepartment(BaseModel, db.Model):
      parent_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
      parent_department = db.relationship('BizDepartment', foreign_keys=[parent_department_id], back_populates='parent_department', lazy='joined')    # 父部门
      child_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
      child_department = db.relationship('BizDepartment', foreign_keys=[child_department_id], back_populates='child_department', lazy='joined')       # 子部门
  ```

- Department

  - set_parent_department
    - 일단 관계테이블에서 **내가 자식으로 등록된 관계 객체를 조회**하고**내가 자식이면, 그 관계를 제거한다**
    - **외부에서 주어진 `department`를 부모로, `나`를 자식으로 관계를 새로 생성한다**
  - get_parent_department - @property
    - 관계테이블에서 나를 자식으로 가진 관계객체를 조회한 뒤
    - 그 **관계가 있으**면 **ref.parent_department로 관계에서 부모**를 꺼낸다. **없으면 none으로 반환**한다
      - **관계객체는 1차 joined로 연결**되어있어서 바로 꺼낼 수 있다
  - set_child_department
    - **외부에서 주어진 department를 자식으로 가지고 있는 `주어진놈의 부모`의 관계객체**를 조회한다
    - 조회되면 삭제하고, **나를 부모로 관계객체를 생성한다**
  - get_child_department - @property
    - 나를 부모로가지는 관계를 조회한 뒤,전체를 반환한다?
    - **나를 부모로 하는 관계객체를 조회한 뒤, 거기에 걸린 자식들을을 반환해야할 듯?**

  ```python
  
  '''
  部门
  '''
  class BizDepartment(BaseModel, db.Model):
      code = db.Column(db.String(32))                                         # 部门代码
      name = db.Column(db.Text)                                               # 部门名称
      company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))  # 所属法人ID
      company = db.relationship('BizCompany', back_populates='departments')   # 所属法人
      employees = db.relationship('BizEmployee', back_populates='department')
      
      parent_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.parent_department_id], back_populates='parent_department', lazy='dynamic', cascade='all')  # 父部门
      child_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.child_department_id], back_populates='child_department', lazy='dynamic', cascade='all')     # 子部门
      # 设置父部门
      def set_parent_department(self, department):
          '''
          逻辑：首先判断是否已经维护父部门，如果存在则执行删除后新增
          :param dept:
          :return:
          '''
          ref = RelDepartment.query.filter_by(child_department_id=self.id).first()
          if ref:
              db.session.delete(ref)
              db.session.commit()
          parent = RelDepartment(id=uuid.uuid4().hex, child_department=self, parent_department=department)
          db.session.add(parent)
          db.session.commit()
      @property
      def get_parent_department(self):
          dept = RelDepartment.query.filter_by(child_department_id=self.id).first()
          return dept.parent_department if dept else None
      # 设置子部门
      def set_child_department(self, department):
          '''
          逻辑：首先解除子部门原有的部门关系，然后再添加到当前部门下
          :param dept:
          :return:
          '''
          ref = RelDepartment.query.filter_by(child_department_id=department.id).first()
          if ref:
              db.session.delete(ref)
              db.session.commit()
          child = RelDepartment(id=uuid.uuid4().hex, child_department=department, parent_department=self)
          db.session.add(child)
          db.session.commit()
      @property
      def get_child_department(self):
          return RelDepartment.query.filter_by(parent_department_id=self.id).order_by(RelDepartment.createtime_loc.desc()).all()
  ```
```python

'''
雇员信息
'''
class BizEmployee(BaseModel, db.Model):
    code = db.Column(db.String(32))     # 职号
    name = db.Column(db.String(128))    # 姓名
    email = db.Column(db.String(128))   # 邮箱
    phone = db.Column(db.String(20))    # 电话
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))          # 所属法人ID
    company = db.relationship('BizCompany', back_populates='employees')             # 所属法人
    department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))    # 所属部门ID
    department = db.relationship('BizDepartment', back_populates='employees')       # 所属部门
```

```python
'''
法人信息表
'''
class BizCompany(BaseModel, db.Model):
    code = db.Column(db.String(10))                         # 法人代码
    name = db.Column(db.String(128))                        # 法人名称
    enterprise_id = db.Column(db.String(32), db.ForeignKey('biz_enterprise.id'))
    enterprise = db.relationship('BizEnterprise', back_populates='companies')
    users = db.relationship('SysUser', back_populates='company')
    roles = db.relationship('SysRole', back_populates='company')
    departments = db.relationship('BizDepartment', back_populates='company')
    employees = db.relationship('BizEmployee', back_populates='company')
    # 初始化法人
    @staticmethod
    def init_companies():
        # 数据说明：法人代码 法人名称 事业处代码
        companies = (
            ('01920601', 'HDICC', 'HDI'),
            ('01920773', 'HDCFL', 'HDI'),
            ('01920052', 'HDISD', 'HDI'),
            ('01920000', 'HDICI', 'HDI'),
        )
        for item in companies:
            company = BizCompany.query.filter_by(code=item[0]).first()
            enterprise = BizEnterprise.quetrery.filter_by(code=item[2]).first()
            if company is None:
                company = BizCompany(
                    id=uuid.uuid4().hex,
                    code=item[0],
                    name=item[1],
                    enterprise_id=enterprise.id if enterprise else ''
                )
                db.session.add(company)
                db.session.commit()
```

#### Department route

- add시

  - **department의 상위 company를 `로그인한 current_user에서 빼서 넣어 fomr에 동적으로 주입`**
  - **Department객체를 먼저 `생성 add commit까지 한 뒤에 form.has_parent를 확인해서 DB데이터에 들어간 것에 대해 .set_parent_department()`메서드 호출**

  ```python
  @bp_department.route('/add', methods=['GET', 'POST'])
  @login_required
  @log_record('新增部门信息')
  def add():
      print('Request method is : ', request.method)
      form = DepartmentForm()
      enterprises, enterprise_options = get_enterprises()
      form.enterprise.choices = enterprise_options
      if not current_user.is_admin:
          form.enterprise.data = current_user.company.enterprise.id
          form.company_id.data = current_user.company.id
          form.company.data = current_user.company.name
      if form.validate_on_submit():
          department = BizDepartment(
              id=uuid.uuid4().hex,
              code=form.code.data.lower(),
              name=form.name.data,
              company_id=form.company_id.data if current_user.is_admin else current_user.company.id,
              create_id=current_user.id
          )
          db.session.add(department)
          db.session.commit()
          has_parent = form.has_parent.data
          if has_parent and form.parent_id.data is not None:
              department.set_parent_department(BizDepartment.query.get(form.parent_id.data))
          flash('部门信息添加成功！')
          return redirect(url_for('.index'))
      return render_template('biz/organization/department/add.html', form=form)
  ```

- 조회시

  - **주석처리 됬지만, admin이 아닐 경우, `현재로그인 유저의 company`를 특정One객체로서 (Company)에 `거기에 속한 Department만 반환하고 싶다면 where( with_parent( 부모One객체-company,  One객체.many관계속성))`를 명시해서  부모에 속한 many들만 필터링 할 수 있다.**

  ```python
  @bp_department.route('/index', methods=['GET', 'POST'])
  @login_required
  @log_record('查询部门清单')
  def index():
      form = DepartmentSearchForm()
      if request.method == 'GET':
          page = request.args.get('page', 1, type=int)
          try:
              code = session['department_view_search_code'] if session['department_view_search_code'] else ''  # 组织代码
              name = session['department_view_search_name'] if session['department_view_search_name'] else ''  # 组织名称
          except KeyError:
              code = ''
              name = ''
          form.code.data = code
          form.name.data = name
      if request.method == 'POST':
          page = 1
          code = form.code.data
          name = form.name.data
          session['department_view_search_code'] = code.strip()
          session['department_view_search_name'] = name.strip()
      per_page = current_app.config['ITEM_COUNT_PER_PAGE']
      pagination = BizDepartment.query.filter(BizDepartment.code.like('%' + code.strip() + '%'), BizDepartment.name.like('%' + name.strip() + '%')).order_by( BizDepartment.code).paginate(page, per_page)
      '''
      if current_user.is_admin:
          pagination = BizDepartment.query.filter(BizDepartment.code.like('%'+code.strip()+'%'), BizDepartment.name.like('%'+name.strip()+'%')).order_by(BizDepartment.code).paginate(page, per_page)
      else:
          pagination = BizDepartment.query.with_parent(current_user.company).filter(BizDepartment.code.like('%' + code.strip() + '%'), BizDepartment.name.like('%' + name.strip() + '%')).order_by(BizDepartment.code).paginate(page, per_page)
      '''
      departments = pagination.items
      return render_template('biz/organization/department/index.html', pagination=pagination, departments=departments, form=form)
  ```



- edit

  - **주어진 특정id의 department를 먼저조회한 뒤**
  - form에 동적으로 필드들에 .data에 삽입하는데
  - **`특정department의 get_parent_departemnt를 조회`해서 있으면, **
    - **`form.has_parent.data` = True + **
    - **form.parent_id.data = parent.id**
    - form.parent.data = parent.name을 대입해준다

  ```python
  @bp_department.route('/edit/<id>', methods=['GET', 'POST'])
  @login_required
  @log_record('修改部门信息')
  def edit(id):
      form = DepartmentForm()
      enterprises, enterprise_options = get_enterprises()
      form.enterprise.choices = enterprise_options
      department = BizDepartment.query.get_or_404(id)
      if request.method == 'GET':
          form.id.data = department.id
          form.code.data = department.code
          form.name.data = department.name
          form.enterprise.data = department.company.enterprise.id
          form.company_id.data = department.company.id
          form.company.data = department.company.name
          parent = department.get_parent_department
          if parent:
              form.has_parent.data = True
              form.parent_id.data = parent.id
              form.parent.data = parent.name
      if form.validate_on_submit():
          department.code = form.code.data
          department.name = form.name.data
          department.company_id = form.company_id.data
          department.update_id = current_user.id
          department.updatetime_utc = datetime.utcfromtimestamp(time.time())
          department.updatetime_loc = datetime.fromtimestamp(time.time())
          db.session.commit()
          has_parent = form.has_parent.data
          if has_parent and form.parent_id.data is not None:
              department.set_parent_department(BizDepartment.query.get(form.parent_id.data))
          else:
              print('删除上级部门更新')
              parent_department = RelDepartment.query.filter_by(child_department_id=id).first()
              db.session.delete(parent_department)
              db.session.commit()
          flash('部门信息更新成功！')
          return redirect(url_for('.index', id=form.id.data))
      return render_template('biz/organization/department/edit.html', form=form)
  ```

  

#### 대박) POST용 재귀메서드로 자식조회해서 반환해주기

##### 자식들을 다모으려면, (부모, `나포함 자식들누적용 list` )을 인자로 받는 재귀메서드를 먼저 정의한다

- 내 자식들의 **(나를 부모로하는)내 자식들이 `자식으로 속한 Ref관계객체들`**을 `.get_child_department` property로 구할 수 있다.
- 내 자식들의 자식으로 속한 관계객체들이 있다면
  - 자식들을 1명씩 순회하며, 자식의 id만 `.child_department_id`로 뽑아올 수 있다
  - **이것을 인자로 넘어온 누적list**에 append해서 기존데이터와 합치게 한다
  - **해당 자식id로 자식department를 조회한 뒤, 자식객체를 부모로, 기존 누적list는 그대로** 다시 한번 재귀메서드를 호출해서 누적list에 계속 쌓이게 한다
- 자식들의 자식으로 속한 관계객체가 없다면, 누적list children을 그대로 반환한다

```python
# 递归获取子部门(多级部门)
def get_child_departments(parent, children):
    child_departments = parent.get_child_department
    if child_departments:
        for child in child_departments:
            children.append(child.child_department_id)
            get_child_departments(BizDepartment.query.get(child.child_department_id), children)
    else:
        return children
```



#### add or edit form 속 부모부서를 선택해야할 때, view에서 POST요청을 처리하는 route

- **view에서는 add or edit인지 action파라미터를 같이 보내준다**
- add form속에서 부모부서를 호출 했다면
  - **`자신이 속한 company(ONE)에 속하는 모든 department`를 `with_parent()`로 조회하고 code순 정렬해서 반환한다**
- edit form 속에서 부모부서를 호출 했다면
  - **현재부서 department_id를 params에서 받아 `누적id_list`로 준비한다**
  - **현재부서 department_id로 `부서객체`를 찾는다**
  - `현재부서` + `현재부서id부터 누적list`를 가지고 **get_child_departments 재귀메서드를 호출**하여
    - 현재나 + 나의 자식들 id list들을 누적list에 보관한다
  - 현재부서객체.company로 **부모객체를 with_parent()에 올려, 같은 부모 기업에 속하는 `모든 부서들을 조회`한다**
  - **모든 부모서들을 1개씩 순회하면서**
    - **`나 + 나의자식 누적 id_list`**에 **속하지 않는 부서들만 골라, parent_department with default select option에 append한다**
    - select 옵션으로 갈 거라 `(id, name)` 튜플리스트로 구성한다

```python
@bp_department.route('/parents', methods = ['POST'])
@log_record('获取法人部门信息信息')
def get_parents():
    parent_departments = [('000000', '---请选择---')]
    params = request.get_json()
    action = params['action']
    company = BizCompany.query.get(params['company_id'])
    if action == 'add':
        departments = BizDepartment.query.with_parent(company).order_by(BizDepartment.code).all()
    if action == 'update':
        self_and_children = [params['department_id']]
        edit_department = BizDepartment.query.get(params['department_id'])
        get_child_departments(edit_department, self_and_children)  # 递归获取子部门及子子部门
        print('Self and child department ids : ', self_and_children)
        departments = BizDepartment.query.with_parent(edit_department.company).order_by(BizDepartment.code).all()
        for department in departments:
            if department.id not in self_and_children:
                parent_departments.append((department.id, department.name))
    for department in departments:
        parent_departments.append((department.id, department.name))
    return jsonify(parent_departments)
```





###### view에서 ajax로 넘겨주는 코드

```js
$('#choose_parent').click(function(){
    flag = 1
    var company_id = $('#company_id').val()
    //alert('Company id : '+company_id)
    $.ajax({
        type:'post',
        url:'/department/parents',
        data:JSON.stringify({action:'add',company_id:company_id,department_id:''}),
        contentType:'application/json;charset=UTF-8',
        success:function(data){
            $('#choose').empty()
            for(var i = 0; i < data.length; i++){
                $('#choose').append("<option value='"+data[i][0]+"'>"+data[i][1]+"</option>")
            }
            $('#selectModel').modal('show')
        },
        error:function(){
            $.alert({
                type:'red',
                title:'系统提示',
                content: '系统错误,请联系管理员',
                onClose:function(){

                }
            })
        }
    })
})
```

![image-20221225151919464](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225151919464.png)



```js
        $('#choose_parent').click(function(){
            flag = 1
            var company_id = $('#company_id').val()
            //alert('Company id : '+company_id)
            $.ajax({
                type:'post',
                url:'/department/parents',
                data:JSON.stringify({action:'update',company_id:company_id,department_id:$('#id').val()}),
                contentType:'application/json;charset=UTF-8',
                success:function(data){
                    $('#choose').empty()
                    for(var i = 0; i < data.length; i++){
                        $('#choose').append("<option value='"+data[i][0]+"'>"+data[i][1]+"</option>")
                    }
                    $('#selectModel').modal('show')
                },
                error:function(){
                    $.alert({
                       type:'red',
                       title:'系统提示',
                       content: '系统错误,请联系管理员',
                       onClose:function(){

                       }
                   })
                }
            })
        })
```



#### employee 등록/수정시, form에 department choices 튜플리스트로 채워주기

```python
def get_departments():
    departments = BizDepartment.query.with_parent(current_user.company).order_by(BizDepartment.name).all()
    department_options = []
    for department in departments:
        department_options.append((department.id, department.name))
    return (departments, department_options)
```

```python
@bp_employee.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增雇员')
def add():
    form = EmployeeForm()
    departments, department_options = get_departments()
    form.department.choices = department_options
    form.company.data = current_user.company.id
    if form.validate_on_submit():
        employee = BizEmployee(
            id=uuid.uuid4().hex,
            code=form.code.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            company_id=current_user.company.id,
            department_id=form.department.data,
            create_id=current_user.id
        )
        db.session.add(employee)
        db.session.commit()
        flash('雇员添加成功！')
        '''
        # 生成二维码
        from pm.utils import gen_qrcode
        data = "{'code'='123456789', 'name'='Compute'}"
        gen_qrcode(current_app.config['QR_CODE_PATH']+'\\'+'test.png', data)
        '''
        return redirect(url_for('.index'))
    return render_template('biz/organization/employee/add.html', form=form)
@bp_employee.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改雇员信息')
def edit(id):
    form = EmployeeForm()
    employee = BizEmployee.query.get_or_404(id)
    departments, department_options = get_departments()
    form.department.choices = department_options
    if request.method == 'GET':
        form.id.data = employee.id
        form.code.data = employee.code
        form.name.data = employee.name
        form.email.data = employee.email
        form.phone.data = employee.phone
        form.company.data = employee.company_id
        form.department.data = employee.department_id
    if form.validate_on_submit():
        employee.code = form.code.data.upper()
        employee.name = form.name.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.department_id = form.department.data
        employee.update_id = current_user.id
        employee.updatetime_utc = datetime.utcfromtimestamp(time.time())
        employee.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('雇员修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/organization/employee/edit.html', form=form)
```





#### 상태는 form에서 뺀 뒤 POST로 바꾸는 버튼 + location().reload 활용

![image-20221225154617134](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225154617134.png)



```python
@bp_department.route('/status/<id>/<int:status>', methods=['POST'])
@log_record('更改部门状态')
def status(id, status):
    department = BizDepartment.query.get_or_404(id)
    department.active = True if status == 1 else False
    department.update_id = current_user.id
    department.updatetime_utc = datetime.utcfromtimestamp(time.time())
    department.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='状态更新成功!')
```

```html
  <tbody>
    {% if departments %}
        {% for department in departments %}
            <tr>
                <td>{{department.company.name}}</td>
                <td>{{department.code}}</td>
                <td>{{department.name}}</td>
                <td>{{department.get_parent_department.code if department.get_parent_department else '/'}}</td>
                <td>{{department.get_parent_department.name if department.get_parent_department else '/'}}</td>
                <td>{%if department.active%}<span class="text-success">在用</span>{%else%}<span class="text-danger">停用</span>{%endif%}</td>
                <td class="text-center">
                    <a href="{{url_for('department.edit', id=department.id)}}" class="btn btn-link text-info" title="编辑"><i class="bi bi-pencil-square"></i></a>&nbsp;
                    <button class="btn btn-link text-danger {%if not department.active%}disabled{%endif%}" title="停用" onclick="status('{{department.id}}', 0)"><i class="bi bi-x-circle"></i></button>&nbsp;
                    <button class="btn btn-link text-success {%if department.active%}disabled{%endif%}" title="启用" onclick="status('{{department.id}}', 1)"><i class="bi bi-check-circle"></i></button>
                </td>
            </tr>
        {%endfor%}
    {% else %}
        <tr>
            <td colspan="7" class="text-center"><small>没有记录!!!</small></td>
        </tr>
    {% endif %}
  </tbody>
</table>
{{render_pagination(pagination, align='right')}}
{% endblock %}
{% block script %}
    {{ super() }}
    function status(id, status){
        $.ajax({
            type:'post',
            url:'/department/status/'+id+'/'+status,
            //data:JSON.stringify({code:$.trim($("#code").val()), name:$.trim($("#name").val()), password:$.trim($("#password").val())}),
            contentType:'application/json;charset=UTF-8',
            success:function(data){
                if(data.code == 1)
                    location.reload()
            },
            error:function(){
                $.alert({
                   type:'red',
                   title:'系统提示',
                   content: '系统错误,请联系管理员',
                   onClose:function(){

                   }
               })
            }
        })
    }
{% endblock %}
```





##### 참고) utc_to_locale/barcode/qrcode 등  util

```python
'''
    系统工具函数
'''
from flask import request, redirect, url_for
from urllib.parse import urlparse, urljoin
from pm.plugins import db
from pm.models import SysUser, SysModule, SysMenu
import time, datetime, os, uuid
def utc_to_locale(utc_date):
    '''
    utc时间转本地
    :param utc_date:
    :return:
    '''
    now_stamp = time.time()
    locale_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = locale_time - utc_time
    locale_date = utc_date + offset
    return locale_date
def get_time():
    '''
    获取当前时间
    :return:
    '''
    return 'Now is : %s' %time.strftime('%Y年%m月%d日')
def get_date():
    '''
    获取日期
    :return:
    '''
    return time.strftime('%Y%m%d')
def format_time(timestamp):
    '''
    格式化日期
    :param timestamp:
    :return:
    '''
    return utc_to_locale(timestamp).strftime('%Y-%m-%d %H:%M:%S')
def is_safe_url(target):
    '''
    判断地址是否安全
    :param target:
    :return:
    '''
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http','https') and ref_url.netloc == test_url.netloc
def redirect_back(default='main.index', **kwargs):
    '''
    通用返回方法(默认返回博客首页)
    :param default:
    :param kwargs:
    :return:
    '''
    target = request.args.get('next')
    if target and is_safe_url(target):
        return redirect(target)
    return redirect(url_for(default, **kwargs))
def random_filename(filename):
    '''
    重命名文件
    :param filename:
    :return:
    '''
    ext = os.path.splitext(filename)[1]
    new_file_name = uuid.uuid4().hex + ext
    return new_file_name
def get_options(code):
    '''
    根据字典代码获取枚举下拉值
    :param code:
    :return:
    '''
    from pm.models import SysDict
    dictionary = SysDict.query.filter_by(code=code).first()
    enums = dictionary.enums
    options = []
    for enum in enums:
        options.append((enum.id, enum.display))
    return options
def get_current_user(id):
    '''
    获取当前用户
    :param id:
    :return:
    '''
    return SysUser.query.get(id)
def get_current_module(id):
    '''
    获取当前模块
    :param id:
    :return:
    '''
    return SysModule.query.get(id)
def get_current_menu(id):
    '''
    获取当前菜单
    :param id:
    :return:
    '''
    return SysMenu.query.get(id)
def change_entity_order(new_order, action, entity):
    '''
    自动调整排序
    注：实体表的排序字段名必须为order_by,且为整型
    :param new_order:新的排序号
    :param action:执行操作：0:新增 1:更新
    :param entity:要编辑的表实例
    :return:
    '''
    if action == 0:
        '''
        如果是新增，则将大于等于当前排序号的加一保存
        '''
        if isinstance(entity, SysModule):
            entities = SysModule.query.filter(SysModule.order_by >= new_order).all()
        if isinstance(entity, SysMenu):
            # entities = SysMenu.query.with_parent(entity.module).filter(SysMenu.order_by >= new_order).all()
            entities = None
        if entities:
            for item in entities:
                item.order_by = item.order_by + 1
                db.session.commit()
    if action == 1:
        '''
            如果是更新，首先判断是由小变大还是由大变小
            由小变大：将大于当前要修改的module排序号同时小于等于新排序号的模块排序号减一保存
            由大变小：将小于当前要修改的module排序号同时大于等于新排序号的模块排序号加一保存
        '''
        if entity.order_by < new_order:
            if isinstance(entity, SysModule):
                entities = SysModule.query.filter(SysModule.order_by > entity.order_by, SysModule.order_by <= new_order).all()
            if isinstance(entity, SysMenu):
                entities = SysMenu.query.with_parent(entity.module).filter(SysMenu.order_by > entity.order_by, SysMenu.order_by <= new_order).all()
            if entities:
                for item in entities:
                    item.order_by = item.order_by - 1
                    db.session.commit()
        else:
            if isinstance(entity, SysModule):
                entities = SysModule.query.filter(SysModule.order_by < entity.order_by, SysModule.order_by >= new_order).all()
            if isinstance(entity, SysMenu):
                entities = SysMenu.query.with_parent(entity.module).filter(SysMenu.order_by < entity.order_by, SysMenu.order_by >= new_order).all()
            if entities:
                for item in entities:
                    item.order_by = item.order_by + 1
                    db.session.commit()
def get_uuid():
    '''
    生产UUID
    :return:
    '''
    return uuid.uuid4().hex
def gen_barcode(path, code):
    '''
    生成条形码
    :param path:
    :param code:
    :return:
    '''
    import barcode
    from barcode.writer import ImageWriter
    print('Provided codes : ', barcode.PROVIDED_BARCODES)
    BARCODE_EAN = barcode.get_barcode_class('code39')
    ean = BARCODE_EAN(code, writer=ImageWriter())
    full_name = ean.save(path + '\\' + code, options=dict(font_size=14, text_distance=2))
    return full_name
def gen_qrcode(file, data):
    '''
    生成二维码
    :param file:
    :param data:
    :return:
    '''
    import qrcode
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file)
```





##### 참고 ) 로그기록 decorator + SysLog 테이블

```python
from flask import request
from functools import wraps
from flask_login import current_user
from pm.models import SysLog
from pm.plugins import db
import uuid
'''
    写入日志
'''
def log_record(content):
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            log = SysLog(id=uuid.uuid4().hex, url=request.path, operation=content, user=current_user, create_id=current_user.id)
            db.session.add(log)
            db.session.commit()
            return function(*args, **kwargs)
        return decorated_function
    return decorator
```

```python
@bp_department.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改部门信息')
def edit(id):
```

```python
class SysLog(BaseModel, db.Model):
    url = db.Column(db.String(250))             # 菜单url
    operation = db.Column(db.Text)              # 操作内容
    user_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))
    user = db.relationship('SysUser', back_populates='logs')
```

```python
def execute_send_mail(app, message):
    '''
    执行发送邮件
    :param app:
    :param message:
    :return:
    '''
    with app.app_context():
        user = SysUser.query.filter_by(user_id='admin').first()
        try:
            mail.send(message)
            log = SysLog(id=uuid.uuid4().hex, url='null', operation='邮件提醒发送成功', create_id=user.id, user_id=user.id)
            db.session.add(log)
        except Exception as e:
            log = SysLog(id=uuid.uuid4().hex, url='null', operation='邮件提醒发送失败;Exception is : '+e, create_id=user.id, user_id=user.id)
            db.session.add(log)
        db.session.commit()
```



##### 참고) Base모델에 datetime.now와 datetime.utcnow를 동시에 기록하도록 필드

```python
class BaseModel():
    id = db.Column(db.String(32), primary_key=True)                     # 表主键ID
    active = db.Column(db.Boolean, default=True)                        # 是否使用(默认已使用)
    createtime_utc = db.Column(db.DateTime, default=datetime.utcnow)    # 创建时间(UTC标准时间)
    createtime_loc = db.Column(db.DateTime, default=datetime.now)       # 创建时间(本地时间)
    create_id = db.Column(db.String(32))                                # 创建人员
    updatetime_utc = db.Column(db.DateTime, default=datetime.utcnow)    # 更新时间(UTC标准时间)
    updatetime_loc = db.Column(db.DateTime, default=datetime.now)       # 更新时间(本地时间)
    update_id = db.Column(db.String(32))                                # 更新人员
```



##### 참고) flask init안에 db.create_all() + admin 계정 생성

![image-20221225140744514](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221225140744514.png)

```python
import click, uuid
from pm.plugins import db
def register_webapp_shell(app):
    @app.shell_context_processor
    def config_shell_context():
        return dict(db=db)
def register_webapp_commands(app):
    @app.cli.command()
    @click.option('--admin_code', prompt=True, help='管理员账号')
    @click.option('--admin_password', prompt=True, help='管理员密码', hide_input=True, confirmation_prompt=True)
    def init(admin_code, admin_password):
        from pm.models import \
            SysUser, SysRole, SysModule, SysMenu, SysDict, SysEnum, BizEnterprise, BizCompany
        click.echo('执行数据库初始化......')
        db.create_all()
        click.echo('数据库初始化完毕')
        click.echo('创建超级管理员角色......')
        role = SysRole.query.first()
        if role:
            click.echo('管理员角色已存在，跳过创建')
        else:
            role = SysRole(id=uuid.uuid4().hex, name='Administrator')
            db.session.add(role)
            db.session.commit()
        click.echo('创建超级管理员......')
        user = SysUser.query.first()
        if user:
            click.echo('管理员已存在，跳过创建')
        else:
            user = SysUser(
                id=uuid.uuid4().hex,
                user_id=admin_code.lower(),
                user_name='Administrator',
                is_admin=True,
                role_id=role.id
            )
            user.set_password(admin_password)
            db.session.add(user)
            db.session.commit()
        click.echo('超级管理员创建成功')
        click.echo('初始化系统模块')
        modules = SysModule.query.all()
        if modules:
            click.echo('系统模块已创建，跳过')
        else:
            modules = (
                ('sys', '系统管理', 1),
                ('org', '组织管理', 2),
            )
            for module_info in modules:
                module = SysModule(
                    id=uuid.uuid4().hex,
                    code=module_info[0],
                    name=module_info[1],
                    order_by=module_info[2],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(module)
                db.session.commit()
        click.echo('系统模块初始化完成')
        click.echo('初始化系统菜单')
        # 菜单名称, URL地址, 菜单描述, 菜单图标, 模块所属, 对应模块下菜单显示顺序
        menus = (
            ('SY001', '用户管理', 'user.index', '管理系统用户(添加、修改、启用/停用等)', 'bi bi-person', 'sys', 1),
            ('SY002', '角色管理', 'role.index', '管理系统角色(新增/修改等)', 'bi bi-mortarboard', 'sys', 2),
            ('SY003', '模块管理', 'module.index', '管理系统模块(新增/修改等)', 'bi bi-columns-gap', 'sys', 3),
            ('SY004', '菜单管理', 'menu.index', '管理系统菜单(新增/修改/停用等)', 'bi bi-menu-button', 'sys', 4),
            ('SY005', '字典管理', 'dict.index', '管理系统下拉选项，包括新增、修改等', 'bi bi-book', 'sys', 5),
            ('HR001', '事业处管理', 'enterprise.index', '事业处信息(新增/修改/停用等)', 'bi bi-building', 'org', 1),
            ('HR002', '法人管理', 'company.index', '法人信息(新增/修改/停用等)', 'bi bi-bank', 'org', 2),
            ('HR003', '部门管理', 'department.index', '部门信息(新增/修改/停用等)', 'bi bi-diagram-3', 'org', 3),
            ('HR004', '雇员管理', 'employee.index', '雇员信息(新增/修改/停用等)', 'bi bi-people', 'org', 4),
        )
        if SysMenu.query.all():
            click.echo('系统菜单已创建，跳过')
        else:
            for menu_info in menus:
                menu = SysMenu(
                    id=uuid.uuid4().hex,
                    code=menu_info[0],
                    name=menu_info[1],
                    url=menu_info[2],
                    remark=menu_info[3],
                    icon=menu_info[4],
                    module=SysModule.query.filter_by(code=menu_info[5]).first(),
                    order_by=menu_info[6],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(menu)
                # 设定角色
                role.menus.append(menu)
                db.session.commit()
            click.echo('菜单初始化完成')
        click.echo('初始化系统字典')
        dicts = SysDict.query.all()
        if dicts:
            click.echo('系统字典已创建，跳过')
        else:
            dicts = (
                ('D001', '是否'),
            )
            for d in dicts:
                dictionary = SysDict(
                    id=uuid.uuid4().hex,
                    code=d[0],
                    name=d[1],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(dictionary)
                db.session.commit()
            click.echo('系统字典初始化完成')
        click.echo('初始化字典枚举值')
        enums = SysEnum.query.all()
        if enums:
            click.echo('字典枚举已维护，跳过')
        else:
            enums = (
                ('1', '是', 'D001', 1),
                ('2', '否', 'D001', 2),
            )
            for enum in enums:
                enumeration = SysEnum(
                    id=uuid.uuid4().hex,
                    item=enum[0],
                    display=enum[1],
                    dictionary=SysDict.query.filter_by(code=enum[2]).first(),
                    order_by=enum[3],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(enumeration)
                db.session.commit()
            click.echo('字典枚举初始化完成')
        click.echo('初始化事业处信息')
        BizEnterprise.init_enterprises()
        click.echo('事业处初始化完成')
        click.echo('初始化法人信息')
        BizCompany.init_companies()
        click.echo('法人初始化完成')
        click.echo('系统初始化完成')
```







##### 참고) breacrumb를 macro로 처리하기 (static_file도)

```html
{# 使用宏函数加载静态资源 #}
{% macro static_file(type, file_or_url, local=True) %}
    {% if local %}
        {% set file_or_url = url_for('static', filename = file_or_url) %}
    {% endif %}
    {% if type == 'css' %}
        <link rel="stylesheet" type="text/css" href="{{ file_or_url }}">
    {% endif %}
    {% if type == 'icon' %}
        <link rel="icon" type="image/x-icon" href="{{ file_or_url }}">
    {% endif %}
    {% if type == 'js' %}
        <script type="text/javascript" src="{{ file_or_url }}"></script>
    {% endif %}
{% endmacro %}

{# 使用宏函数实现当前导航 #}
{% macro current_location(location) %}
    {% set active_module = session.get('active_module') %}
    {% set active_menu = session.get('active_menu') %}
    <div class="clearfix">
        <small style="color:#888;" class="float-left">
            <i class="{{get_current_menu(active_menu).icon}}"></i>&nbsp;&nbsp;{{get_current_module(active_module).name}}&nbsp;&nbsp;/&nbsp;&nbsp;
            <span class="text-secondary">{{get_current_menu(active_menu).name}}</span>
            {% if location %}
            &nbsp;&nbsp;/&nbsp;&nbsp;
            <span class="text-secondary">{{ location }}</span>
            {% endif %}
        </small>
    </div>
    <hr>
{% endmacro %}
```

- 세션에 박힌 현재 active_된 모듈/menu => 변수화 => 2개를 미리 박아놓고 시작하는 듯.



- utils.py에는 **session에 박힌 모듈, 메뉴이름에 대해, 실제 객체를 불러다준다**

  ```python
  def get_current_module(id):
      '''
      获取当前模块
      :param id:
      :return:
      '''
      return SysModule.query.get(id)
  def get_current_menu(id):
      '''
      获取当前菜单
      :param id:
      :return:
      '''
      return SysMenu.query.get(id)
  ```

- 해당모듈들을 global로 만들어 app.context_processor에서 넘긴다

  - web_globals.py
  - **app객체를 받으니, init.py의 create_app에서 import 될 듯**

  ```python
  from flask import url_for, redirect
  from pm.utils import get_time, format_time, get_current_user, get_current_module, get_current_menu
  def register_webapp_global_path(app):
      '''
      注册系统全局路径
      :param app:
      :return:
      '''
      @app.route('/')
      def index():
          return redirect(url_for('auth.login'))
      @app.before_request
      def request_intercept_before():
          print('Before the request...')
          pass
  def register_webapp_global_context(app):
      '''
      注册系统全局上下文(后台&前台页面均可用)
      :param app:
      :return:
      '''
      @app.context_processor
      def config_template_context():
          return dict(get_time=get_time,
                      format_time=format_time,
                      get_current_user=get_current_user,
                      get_current_module=get_current_module,
                      get_current_menu=get_current_menu)
  ```

- init.py

  ```python
  from flask import Flask
  from pm.configs import configurations
  from pm.regs.web_errors import register_webapp_errors
  from pm.regs.web_globals import register_webapp_global_context, register_webapp_global_path
  from pm.regs.web_plugins import register_webapp_plugins
  from pm.regs.web_views import register_webapp_views
  from pm.regs.web_shells import register_webapp_shell, register_webapp_commands
  
  def create_app(config=None):
      if(config == None):
          config = 'dev_config'
      app = Flask('pm')
      app.config.from_object(configurations[config])
      register_webapp_plugins(app)
      register_webapp_global_path(app)
      register_webapp_global_context(app)
      register_webapp_errors(app)
      register_webapp_views(app)
      register_webapp_shell(app)
      register_webapp_commands(app)
      return app
  ```

  

- 등록은 route를 통해 하는 것 같은데 아직 파악x

  ```python
  '''
  执行跳转至对应的功能画面
  '''
  @bp_main.route('/to_uri/<module_id>/<menu_id>')
  @login_required
  def to_uri(module_id, menu_id):
      print('Parameter module id is : ', module_id)
      print('Parameter menu id is : ', menu_id)
      session['active_module'] = module_id    # 用于head导航栏栏nav active判断
      session['active_menu'] = menu_id        # 用于左侧菜单menu active判断
      menu = SysMenu.query.get_or_404(menu_id)
      print('Menu url is : ', menu.url)
      print('Menu name is : ', menu.name)
      return redirect(url_for(menu.url))
      # return render_template('main/index.html')
  @bp_main.route('/to_function', methods=['GET', 'POST'])
  @login_required
  def to_function():
      # 使用过的菜单项
      used_menus = current_user.used_menus
      # 已授权菜单ID数据:code list
      authed_menus = current_user.menus
      for menu in used_menus:
          if menu.code not in authed_menus:
              current_user.used_menus.remove(menu)
              db.session.commit()
      # 重新获取已使用的菜单项
      used_menus = current_user.used_menus
      if request.method == 'POST':
          menu_code = request.form['menu_code']
          menu = SysMenu.query.filter_by(code=menu_code.upper()).first()
          if menu:
              # 判断是否具有权限
              if menu_code.upper() in current_user.menus:
                  session['active_module'] = menu.module.id
                  session['active_menu'] = menu.id
                  if menu not in current_user.used_menus:
                      current_user.used_menus.append(menu)
                      db.session.commit()
                  return redirect(url_for(menu.url))
              else:
                  flash('您没有该功能画面权限，请联系管理员！')
          else:
              flash('功能代码错误,没有对应的画面！')
      return render_template('main/home.html', used_menus=used_menus)
  ```

  - auth.py

  ```python
  from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app
  from flask_login import login_user, logout_user, current_user
  from pm.forms.auth import LoginForm
  from pm.plugins import db
  from pm.models import SysUser, SysLog, SysMenu
  import uuid, jpype
  bp_auth = Blueprint('auth', __name__)
  @bp_auth.route('/login', methods=['GET', 'POST'])
  def login():
      '''
      系统登录
      :return:
      '''
      #interfaces current_user.is_authenticated:
          #return redirect(url_for('main.index'))
      form = LoginForm()
      if form.validate_on_submit():
          user_id = form.user_id.data
          user_pwd = form.user_pwd.data
          # print('User id is %s, password is %s' %(user_id, user_pwd))
          user = SysUser.query.filter_by(user_id=user_id.lower()).first()
          if user:
              if user.active:
                  if user.is_ad:
                      # AD验证
                      jvm_path = current_app.config['JVM_PATH']
                      ad_jar_path = current_app.config['AD_JAR_PATH'] + '\\ad.auth.module-1.0.jar'
                      # 如果已启动，捕捉异常后跳过启动JVM
                      try:
                          jpype.startJVM(jvm_path, '-ea', '-Djava.class.path=' + ad_jar_path)
                      except:
                          pass
                      jpype.java.lang.System.out.println('Hello world from JAVA!!!')
                      package = jpype.JPackage('DSGAuthPkg')
                      auth = package.Auth("authsj.corp.doosan.com", "dsg\\" + user_id, user_pwd)
                      validate_ok = auth.validateUser(user_id, user_pwd)
                  else:
                      validate_ok = user.validate_password(user_pwd)
                  if validate_ok:
                      login_user(user, True)
                      log = SysLog(id=uuid.uuid4().hex, url='auth.login', operation='登录系统', user=user)
                      db.session.add(log)
                      db.session.commit()
                      # 类GMES跳转
                      # return redirect(url_for('main.to_function'))
                      # 传统布局使用以下跳转
                      modules = current_user.authed_modules
                      if modules:
                          for module in modules:
                              print('Module name : ', module.name)
                          module_menu = current_user.authed_menus
                          for module, menu in module_menu.items():
                              print('Module id : ', module, ', menus : ', menu)
                          module_id = current_user.authed_modules[0].id
                          return redirect(url_for('main.to_uri', module_id=module_id, menu_id=current_user.authed_menus[module_id][0].id))
                      else:
                          flash('该用户没有分配任何系统权限，请联系管理员！')
                          return render_template('main/not-authed.html')
                  else:
                      flash('密码错误！')
              else:
                  flash('用户已停用！')
          else:
              flash('用户不存在！')
      return render_template('auth/sign_in.html', form=form)
  @bp_auth.route('/logout')
  def logout():
      logout_user()
      return redirect(url_for('.login'))
  ```

  



- 사용

  ```html
  {% extends 'base.html' %}
  {% block content %}
  {{current_location('添加')}}
  <div class="clearfix text-center">
  ```







-