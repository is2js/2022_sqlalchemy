모델과 사용

### 7 [dan-hill](https://github.com/dan-hill)/**[jabberfire](https://github.com/dan-hill/jabberfire)**



#### model 과 exist부터 정의하여 save에 활용하기 (다양한 classmethod)

```python
from app import db


class Department(db.Model):
    """ Department data model.
    Attributes:
    id (int):
      Unique identifier for the department. This number is used internally int eh database.
    parent_id (int):
      The id of the department that the department belongs under. If the department is at the
      top of the tree structure, this should be None.
    name (string):
      The name of the department. Should not have the name of the parent department prefixed to it.
    sub_departments (list of departments):
      A list of department objects that are directly under this department in the organizational tree
      structure.
    """

    # TODO change sub_departments to children to more concretely describe the tree nature of the relationship.

    __tablename__ = 'department'

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.parent_id = kwargs.get('parent_id')


    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))

    children = db.relationship(
        'Department',
        cascade='all',
        backref=db.backref('parent', remote_side='Department.id'))

    def exists(self):

        if Department.query.filter_by(id=self.id).first():
            return True
        return False

    def save(self):
        db.session.add(self)
        db.session.commit()

        if not self.exists():
            return False
        return True

    def delete(self):
        db.session.delete(self)
        db.session.commit()

        if self.exists():
            return False

        return True

    @staticmethod
    def list():
        return db.session.query(Department).all()

    @staticmethod
    def find(**kwargs):
        return db.session.query(Department).filter_by(**kwargs).first()
```



#### tree_dict만들어서, jstree로 뿌리기 (사용까진 없음)

```python
from flask_security import current_user


def get_tree(base_department, tree_dict):

    # TODO Protect this function from accidental infinite recurrsion.

    tree_dict = {}

    tree_dict['id'] = base_department.id
    tree_dict['text'] = base_department.name
    tree_dict['icon state'] = {'opened': False, 'disabled': False, 'selected': False}
    tree_dict['children'] = []
    tree_dict['li_attr'] = {}
    tree_dict['a_attr'] = {}

    children = base_department.sub_departments

    if len(children) > 0:
        for child in children:
            tree_dict['children'].append(get_tree(child, tree_dict))

    return tree_dict

```





### 8 [s-tar](https://github.com/s-tar)/**[PromTal](https://github.com/s-tar/PromTal)** - jinja2재귀로 해결하는 부서(React도 섞여있는 듯)



#### model - user에 의해 탄생하는 Many면서, 하위 users를 들고 다

- many인 **users를 `joined`로 연결하여 department.users를 바로 조회**되도록 한다

```python
from application.db import db
from application.models.mixin import Mixin
from application.models.user import User


class Department(db.Model, Mixin):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    # 자신을 부모로 nullable True
    parent_id = db. Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    # 특정 user에 의해 생성되는 Many지만
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    parent = db.relationship('Department', remote_side=[id],  backref="subdepartment")
    # department.user는, department를 만든 user
    user = db.relationship("User", backref="managed_department", foreign_keys=[user_id], lazy='joined')
```

- user

  ```python
  class User(db.Model, AuthUser, Mixin):
      '''
      при добавлении полей не забыть их добавить в
      application/models/serializers/users.py для корректной валидации данных
      '''
  
      __tablename__ = 'users'
  
      (
          STATUS_ACTIVE,
          STATUS_DELETED,
      ) = range(2)
  
      STATUSES = [(STATUS_ACTIVE, 'Active'), (STATUS_DELETED, 'Deleted')]
  
      id = db.Column(db.Integer, primary_key=True)
      email = db.Column(db.String)  # TODO Add constraint on length; can't be nullable in future
      full_name = db.Column(db.String(64))
      login = db.Column(db.String(64), unique=True)
      status = db.Column(db.Integer, default=STATUS_ACTIVE)
      mobile_phone = db.Column(db.String, nullable=True)  # TODO Add constraint on length and format
      inner_phone = db.Column(db.String, nullable=True)   # TODO Add constraint on length and format
      birth_date = db.Column(db.DateTime, nullable=True)  # TODO Add default value
      skype = db.Column(db.String(64), nullable=True)
      
      department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
      position = db.Column(db.String(255))
      photo_id = db.Column(db.Integer, db.ForeignKey('file.id'))
      is_admin = db.Column(db.Boolean, default=False)
      news_notification = db.Column(db.Boolean, default=False)
      reg_date = db.Column(db.DateTime, default=datetime.now)
      permissions = db.relationship("Permission", secondary=user_permission_associate, backref="users", lazy='dynamic')
      roles = db.relationship("Role", secondary=user_role_associate, backref="users", lazy='dynamic')
      # department.users == works (만든 user를 제외)
      department = db.relationship("Department", backref="users", foreign_keys=[department_id])
      photo = db.relationship("File", lazy="joined")
  
      def __repr__(self):
          return "<User {login}>".format(login=self.login)
  
      @classmethod
      def get_by_id(cls, uid):
          return cls.query.filter_by(id=uid).first()
  
      @classmethod
      def get_by_email(cls, email):
          return cls.query.filter_by(email=email).first()
  
      @classmethod
      def get_by_login(cls, login):
          return cls.query.filter_by(login=login).first()
  
      @classmethod
      def count_users_in_department(cls, department):
          return cls.query.filter_by(department_id=department).count()
  
      @classmethod
      def find_user(cls, dep_id, name):
          return cls.query.filter(or_(User.department_id == None, User.department_id != dep_id)).filter(User.full_name.ilike('%'+name+'%')).limit(5).all()
  
      @classmethod
      def get_new(cls):
          today = date.today()
          delta = today - timedelta(days=30)
          return cls.query.filter(User.reg_date > delta, or_(User.status != User.STATUS_DELETED, User.status==None)).order_by(User.reg_date.desc(), User.full_name).all()
  
      @classmethod
      def get_birthday(cls):
          today = date.today()
          tomorrow = today + timedelta(days=1)
          return cls.query.filter(
              or_(
                  and_(extract('month', User.birth_date) == today.month, extract('day', User.birth_date) == today.day),
                  and_(extract('month', User.birth_date) == tomorrow.month, extract('day', User.birth_date) == tomorrow.day)
              ), or_(User.status != User.STATUS_DELETED, User.status==None)).order_by(User.birth_date.desc(), User.full_name).all()
  
      @classmethod
      def set_user_is_admin(cls, user_id):
          u = cls.query.filter_by(id=user_id).first()
          u.is_admin = True
          u.roles = []
          db.session.add(u)
          db.session.commit()
  
      @classmethod
      def set_user_role(cls, user_id, role_id):
          u = cls.query.filter_by(id=user_id).first()
          r = Role.get_by_id(role_id)
          u.roles = []
          u.roles.append(r)
          u.is_admin = False
          db.session.add(u)
          db.session.commit()
  
      @classmethod
      def get_user_role_id(cls, user_id):
          u = cls.query.filter_by(id=user_id).first()
          if u.is_admin:
              return 0
          elif u.roles and len(u.roles.all()):
              return u.roles[0].id
          return ''
  
      @classmethod
      def set_user_per(cls, user_id, per_string):
          if per_string == "None":
              per_list = []
          else:
              per_list = per_string.split(',')
          u = cls.query.filter_by(id=user_id).first()
          u.permissions = []
          for per_id in per_list:
              p = Permission.get_by_id(per_id)
              u.permissions.append(p)
          db.session.add(u)
          db.session.commit()
  
      @classmethod
      def get_user_permissions_id(cls, user_id):
          u = cls.query.filter_by(id=user_id).first()
          permissions_list = []
          for per in u.permissions:
              permissions_list.append(per.id)
          return permissions_list
  
      @classmethod
      def add_user2dep(cls, dep_id, user_id):
          u = cls.query.filter_by(id=user_id).first()
          if dep_id == 0:
              dep_id = None
          u.department_id = dep_id
          db.session.add(u)
  
      @classmethod
      def edit_user(cls, uid, full_name=full_name,
                              position=position,
                              mobile_phone=mobile_phone,
                              inner_phone=inner_phone,
                              email=email,
                              birth_date=birth_date,
                              skype=skype,
                              photo=photo):
          u = cls.query.filter_by(id=uid).first()
          if u:
              u.full_name = full_name
              u.position = position
              u.mobile_phone = mobile_phone
              u.inner_phone = inner_phone
              u.email = email
              if birth_date:
                  u.birth_date = birth_date
              else:
                  u.birth_date = None
              u.skype = skype
  
              db.session.add(u)
              if photo:
                  p = u.photo = u.photo or File.create(name='photo.png', module='users', entity=u)
                  p.makedir()
                  p.update_hash()
                  image.thumbnail(photo, width = 100, height = 100, fill = image.COVER).save(p.get_path(sufix="thumbnail"))
                  image.resize(photo).save(p.get_path())
          return u
  
      def get_permissions(self):
          return set([permission.name for permission in self.permissions]).union(
              set([permission.name for role in self.roles for permission in role.permissions])
          )
  
      def has_role(self, role):
          return role in self.roles
  
      @property
      def age(self):
          today, born = date.today(), self.birth_date
          return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
  
      def to_json(self):
          return user_schema.dump(self)
  ```

  

#### property 들

##### 1 부서설립자를 제외한 소속직원들 workers

- user
  - 설립자

- workers
  - **joined된 Many `self.users`를  `소속된 유저들` 순회하여, ` self.user` 로 department를 만든 사람을 제외하고 뽑아낸다**

```python
@property
def workers(self):
    return [user for user in self.users if user != self.user]

def __repr__(self):
    return "<Department {name}>".format(name=self.name)

```

##### 2 route에서  list defaultdict에 parent_id  key마다 자식department객체들을 append한 것을 render하여, jinja2에서 dict.get() + 재귀 + loop.depth를 이용한 level구분한다 (대박 모든부서 재귀dict)

```python
@module.get("/show")
def show_structure():
    departments = defaultdict(list)
    for department in Department.all():
        departments[department.parent_id].append(department)
    return render_template('company_structure/show.html', departments=departments)
```



```html
{% extends "layout.html" %}
{% import "macros/user.html" as user %}

{% block content %}
<div class="container-fluid company-structure">
    <div class="frame">
        <h3 class="title">Структура компании</h3>
    </div>
    <div class="structure loading">
        <ul class="level-0">
        {% for dep in departments.get(None, []) recursive %}
            <li>
                <div class="lines"></div>
                <div class="department frame">
                    <div class="title">{{ dep.name or '' }}</div>
                    {% if dep.user %}
                    <div class="user">
                        {{ user.icon(dep.user) }}
                        <span class="worker-info">
                            <a href="{{ url_for("user.profile", user_id=dep.user.id) }}" title="{{ dep.user.full_name }}">{{ dep.user.full_name }}</a>
                            {% if dep.user.position %}<span class="position">{{ dep.user.position }}</span>{% endif %}
                        </span>
                    </div>
                    {% endif %}
                    {% if  dep.workers|length %}
                    <div class="workers">
                        <div class="workers-toggle">
                            <a href="#" class="show-link">Сотрудники ({{ dep.workers|length }})</a>
                            <a href="#" class="hide-link">Скрыть сотрудников</a>
                        </div>
                        <div class="workers-list">
                        {% for worker in dep.workers %}
                        <div class="user">
                            {{ user.icon(worker) }}
                            <span class="worker-info">
                                <a href="{{ url_for("user.profile", user_id=worker.id) }}" title="{{ worker.full_name }}">{{ worker.full_name }}</a>
                                {% if worker.position %}<span class="position">{{ worker.position }}</span>{% endif %}
                            </span>
                        </div>
                        {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
                <ul class="level-{{ loop.depth }}">{{ loop(departments.get(dep.id, [])) }}</ul>
            </li>
        {% endfor %}
        </ul>
    </div>
</div>
{% endblock %}
```

```python
{% extends "admin/layout.html" %}

{% block title %}Structure{% endblock %}
{% block content %}
<div class="container-fluid">
    <h2>Company structure</h2>
    {% if departments %}
        <ul>
        {%- for dep in departments recursive %}
            <li>
                <p>{{ dep.name }}
                    <a href="{{ url_for('admin.department_info', dep_id=dep.id) }}"><span class="glyphicon glyphicon-user"></span></a>
                    <a href="{{ url_for('admin.edit_structure', dep_id=dep.id) }}"><span class="glyphicon glyphicon-pencil"></span></a>
                    <a href="{{ url_for('admin.add_structure', dep_id=dep.id) }}"><span class="glyphicon glyphicon-plus"></span></a>
                    <a href="{{ url_for('admin.delete_structure', dep_id=dep.id) }}"><span class="glyphicon glyphicon-minus"></span></a>
                </p>
            {%- if dep.dep_list -%}
                <ul><p>{{ loop(dep.dep_list) }}</p></ul>
            {%- endif %}</li>
        {%- endfor %}
        </ul>
    {% endif %}
</div>
{% endblock %}
```

```python
{% extends "admin/layout.html" %}

{% block title %}Структура компании{% endblock %}
{% block content %}
<div class="container-fluid">
    <h2>Структура компании <span id="roll-btn" class="glyphicon glyphicon-resize-small" onclick="roll_btn_click() "></span></h2>
    <ul class="metisFolder">
    {%- for dep in departments recursive %}
        <li class="active">
          <a href="#">
            {%- if dep.dep_list -%}
                <span class="fa fa-minus-square-o"></span>
            {%- else %}
                <span class="fa fa-square-o"></span>
            {%- endif %}
            {{ dep.name }}
            <!--div class="glyphicon glyphicon-list" onClick="window.location.href = '{{ url_for('admin.department_order', dep_id=dep.id) }}';"></div-->
            <div class="glyphicon glyphicon-user" onClick="window.location.href = '{{ url_for('admin.department_info', dep_id=dep.id) }}';"></div>
            <div class="glyphicon glyphicon-pencil" onClick="window.location.href = '{{ url_for('admin.edit_structure', dep_id=dep.id) }}';"></div>
            <div class="glyphicon glyphicon-plus" onClick="window.location.href = '{{ url_for('admin.add_structure', dep_id=dep.id) }}';"></div>
            <div class="glyphicon glyphicon-minus" onClick="window.location.href = '{{ url_for('admin.delete_structure', dep_id=dep.id) }}';"></div>
          </a>
                
        {%- if dep.dep_list -%}
            <ul><p>{{ loop(dep.dep_list) }}</p></ul>
        {%- endif %}</li>
    {%- endfor %}
    </ul>
</div>
<script>
$(document).ready(function() {
  $('.metisFolder').metisMenu({
    toggle: false
  });

  roll_btn_click = function() {
    btn = $("#roll-btn")
    metis = $(".metisFolder")
    if (btn.hasClass('glyphicon-resize-small')) {
        btn.removeClass('glyphicon-resize-small').addClass('glyphicon-resize-full');
        metis.find('li.active').has('ul').children('ul').removeClass('collapse in').addClass('collapse');
        metis.find('li').children('a').children('span.fa-minus-square-o').removeClass('fa-minus-square-o').addClass('fa-plus-square-o');
        metis.find('li.active').removeClass('active');
    } else {
        btn.removeClass('glyphicon-resize-full').addClass('glyphicon-resize-small');
        metis.find('li').not('.active').has('ul').children('ul').removeClass('collapse').addClass('collapse in');
        metis.find('li').children('a').children('span.fa-plus-square-o').removeClass('fa-plus-square-o').addClass('fa-minus-square-o');
        metis.find('li').not('.active').addClass('active');
    }
  }

});
</script>
{% endblock %}
```



##### 3 company조회시 department전체로 재귀메서드로 만든 dict를 호출하기 도 한다

```python
def get_departments(parent_id=None):
    dep_list = []
    departments = db.session.query(Department).filter_by(parent_id=parent_id).all()
    for dep in departments:
        dep_dict = row2dict(dep)
        dep_dict['dep_list'] = get_departments(dep.id)
        dep_list.append(dep_dict)
    if len(departments):
        return dep_list
    else:
        return None


@module.get('/company-structure')
def company_structure():
    departments = get_departments()
    return render_template('admin/company_structure/structure.html', departments=departments)


@module.get('/company-structure-show')
def company_structure_show():
    departments = get_departments()
    return render_template('admin/company_structure/structure_show.html', departments=departments)

```



##### 4  get_parent_all은, department edit ROUTE에서, 선택된 부서에 대해 부모부서들을 골라내기 위함이다

```python
@module.get('/company-structure/edit/<int:dep_id>')
def edit_structure(dep_id):
    department = Department.get_by_id(dep_id)
    dep_parents = Department.get_parent_all(dep_id)
    return render_template('admin/company_structure/edit_structure.html',
                            department=department,
                            dep_parents = dep_parents)

```

- **자신을 제외하고 골라낼 뿐인데 이게 부모 부서?**

```python

    @classmethod
    def get_by_id(cls, uid):
        return cls.query.filter_by(id=uid).first()

    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_parent_all(cls, uid):
        return cls.query.filter(Department.id!=uid).order_by(Department.name).all()
```





- edit에는 AJAXFORM이라는 것을 react로 사용했따

  ```html
  {% extends "admin/layout.html" %}
  
  {% block title %}Edit Department{% endblock %}
  {% block content %}
  <script type="text/jsx">
  React.render(
      <AJAXForm action="{{ url_for('admin.edit_structure_post') }}" method="post" className="form-signin" onSuccess={wellDone}>
          <Input className="ninja" type="hidden" name="department_id" value="{{department.id}}" />
          <Input className="form-control" type="text" name="name_structure" defaultValue="{{department.name}}" placeholder="Название структуры"/>
  
          <select name="parent" className="form-control" onClick={clickUsers}>
              <option value="0" selected> - </option>
            {% for p in dep_parents %}
                <option value="{{ p.id }}" {% if p.id == department.parent_id %}selected{% endif %}>{{ p.name }}</option>
            {% endfor %}
          </select>
  
          <Input className="btn btn-lg btn-primary btn-block" type="submit" value="Сохранить"/>
      </AJAXForm>,
      document.getElementById('edit-structure'))
  
  function wellDone(){
      window.location.href = "{{ url_for('admin.company_structure') }}";
  }
  function clickUsers(){
      console.log("clickUsers");
  }
  </script>
  <div class="row">
      <div class="col-sm-6 col-md-4 col-md-offset-4">
          <h1 class="text-center login-title">Edit Department</h1>
          <div class="account-wall">
              <div id="edit-structure"></div>
          </div>
      </div>
  </div>
  {% endblock %}
  ```





##### 5 department edit post를 처리하는 route에서 사용되는 rename/set_parent

- edit를 ajaxform으로 POST로 보낸 것을 처리하는 ROUTE

  ```python
  @module.post('/company-structure/edit-post/')
  def edit_structure_post():
      v = Validator(request.form)
      v.field("name_structure").required()
      if v.is_valid():
          name_structure = v.valid_data.name_structure
          Department.rename(request.form.get("department_id"), name_structure)
          Department.set_parent(request.form.get("department_id"), request.form.get("parent"))
          return jsonify({"status": "ok"})
      return jsonify({"status": "fail",
                      "errors": v.errors})
  ```

- 현재부서, 부모부서의 id가 인자로 와서

  - 자신을 찾고
  - **p_id가 0이 아닐때, 집어넣어준다. 0이면 None**

```python


    @classmethod
    def get_all(cls):
        return cls.query.order_by(Department.name).all()

    @classmethod
    def set_parent(cls, uid, pid):
        dep = cls.query.filter_by(id=uid).first()
        if pid == '0':
            dep.parent_id = None
        else:
            dep.parent_id = pid
        db.session.add(dep)
        db.session.commit()

    @classmethod
    def rename(cls, uid, new_name):
        dep = cls.query.filter_by(id=uid).first()
        dep.name = new_name
        db.session.add(dep)
        db.session.commit()

    @classmethod
    def add(cls, uid, new_name):
        dep = Department(parent_id=uid, name=new_name)
        db.session.add(dep)
        db.session.commit()

```





##### 6 add_head4dep : 선택부서, 선택유저를 팀장으로 

- 팀장후보 user가**현재 팀장으로 소속된 부서들을 찾은 뒤, 팀장자리를 비워둔다**
  - 반복문돌면서 add까지만 해주기
- **선택부서를 찾아서**, 옵션에 따라, 해당 유저를 팀장으로 배정한다

```python
@classmethod
def add_head4dep(cls, option, dep_id, user_id):
    # 원래 팀장으로 있떤 부서들을 찾아서, 비워둔다
    deps = cls.query.filter_by(user_id=user_id).all()
    for dep in deps:
        dep.user_id = None
        db.session.add(dep)
    dep = cls.query.filter_by(id=dep_id).first()
    if option == 1:
        dep.user_id = user_id
    elif option == 2:
        dep.user_id = None
    db.session.add(dep)
    db.session.commit()
```



- ROUTE는 POST용인가보다 jsonify로 보내준다

```python
@module.get('/company-structure/set-head-dep/<int:option>/<int:dep_id>/<int:user_id>/')
def set_user_head_dep(option, dep_id, user_id):
    Department.add_head4dep(option, dep_id, user_id)
    return jsonify({'status': 'ok'})

```



- VIEW에서는 department에서 해당 유저가 선택되면 ajax로 보낸다

```html
{% extends "admin/layout.html" %}

{% block title %}Структура{% endblock %}
{% block content %}
<script type="text/jsx">
React.render(
    <ManageUsers dep_id="{{ department.id }}" />,
    document.getElementById('manage-users'))

function wellDone(){
    window.location.href = "{{ url_for('user.profile') }}";
}
</script>
<div class="container-fluid">
    <h2>{{ department.name }} <!--a class="btn btn-primary" href="{{ url_for('admin.manage_users', dep_id=department.id ) }}" role="button"><span class="glyphicon glyphicon-user"></span> Добавить работника</a--></h2>

    <div id="manage-users"></div>

    <!--ul class="media-list">
      <li class="media">
        <div class="media-left">
            <img src="{{ current_user.photo.get_url('thumbnail') if current_user.photo else '/static/img/no_photo.jpg' }}" class="media-object foto-small" alt="Фото {{ current_user.full_name }}">
        </div>
        <div class="media-body">
          <h4 class="media-heading">Media heading</h4>
          Отдел
        </div>
      </li>
      <li class="media">
        <div class="media-left">
            <img src="{{ current_user.photo.get_url('thumbnail') if current_user.photo else '/static/img/no_photo.jpg' }}" class="media-object foto-small" alt="Фото {{ current_user.full_name }}">
        </div>
        <div class="media-body">
          <h4 class="media-heading">Media heading</h4>
          Отдел
        </div>
      </li>
      <li class="media">
        <div class="media-left">
            <img src="{{ current_user.photo.get_url('thumbnail') if current_user.photo else '/static/img/no_photo.jpg' }}" class="media-object foto-small" alt="Фото {{ current_user.full_name }}">
        </div>
        <div class="media-body">
          <h4 class="media-heading">Media heading</h4>
          Отдел
        </div>
      </li>
    </ul>



    <h2>{{ department.name }} <a class="btn btn-primary" href="#" role="button"><span class="glyphicon glyphicon-user"></span> Добавить работника</a></h2-->
    <table id="users_datatables" class="table table-striped table-hover dt-responsive table-admin table-manage table-department">
        <thead>
            <tr>
                <th>ID </th>
                <th>Имя</th>
                <th>Email</th>
                <th>Логин</th>
                <th>Мобильный</th>
                <th>Внутренний телефон</th>
                <th>Управление</th>
                <th>Начальник</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    </table>
</div>
<script type="text/javascript">
window.onload = function() {
    $(document).ready(function() {
        $('#users_datatables').DataTable({
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": "{{ url_for('admin.dep_users_json', dep_id=department.id ) }}"
        });
    } );

    $('.selectpicker').selectpicker({
      style: 'btn-default',
      size: 5
    });

    window.change_user_dep = function(dep_user){
        $.ajax({
          url: "/admin/company-structure/set-user-dep/"+dep_user+"/",
          success: function(json) {
                if(json.status == 'ok'){
                    console.log("OK");
                    location.reload();
                }
          }
        });
    }
    //change_user_dep('0', '818');

    window.change_head_dep = function(self, dep_id, user_id){
      var option = 1;
      if($(self).prop("checked")){
        console.log("1", user_id, dep_id);
        option = 1;
        $('input:checkbox').prop('checked', false);
        $(self).prop('checked', true);
      } else {
        console.log("2", user_id, dep_id);
        option = 2;
      }

      $.ajax({
        url: "/admin/company-structure/set-head-dep/"+option+"/"+dep_id+"/"+user_id,
        success: function(json) {
              if(json.status == 'ok'){
                  console.log("OK");
              }
        }
      });

    }
}
</script>
</div>

{% endblock %}
```



##### 7 is_user_head는 dataTable처리에서  head_department를 판단하는데 쓰인다?

```python

@classmethod
def is_user_head(cls, dep_id, user_id):
    dep = cls.query.filter_by(id=dep_id).first()
    if dep.user_id == user_id:
        return True
    return False
```



```python
@module.get('/dep_users_json/<int:dep_id>')
def dep_users_json(dep_id):
    columns = []
    columns.append(ColumnDT('id', filter=_default_value))
    columns.append(ColumnDT('full_name', filter=_default_value))
    columns.append(ColumnDT('email', filter=_default_value))
    columns.append(ColumnDT('login', filter=_default_value))
    columns.append(ColumnDT('mobile_phone', filter=_default_value))
    columns.append(ColumnDT('inner_phone', filter=_default_value))
    query = db.session.query(User).filter_by(department_id=dep_id)
    rowTable = DataTables(request, User, query, columns)
    json_result = rowTable.output_result()
    departments = Department.get_all()
    for row in json_result['aaData']:
        row_id = row['0']
        last_columns = str(len(columns))
        dep_html = ''
        for dep in departments:
            sel = 'selected' if dep.id == dep_id else ''
            dep_html += "<option value='"+str(dep.id)+"/"+row_id+"' "+sel+">"+dep.name+"</option>"
        manage_html = """
          <select onchange="change_user_dep(this.value)" id="first-disabled" class="selectpicker" data-hide-disabled="true" data-live-search="true" data-width="200px">
            <optgroup label="Доп возможности">
              <option value="0/"""+row_id+"""">Удалить из отдела</option>
            </optgroup>
            <optgroup label="Отделы">"""+dep_html+"""</optgroup>
          </select>
          <script type="text/javascript">$('.selectpicker').selectpicker({style: 'btn-default',size: 5});</script>
          """
        row[last_columns] = manage_html
        src_foto = ''
        user = User.get_by_id(row_id)
        if user.photo:
            src_foto = user.photo.get_url('thumbnail')
        else:
            src_foto = '/static/img/no_photo.jpg'
        row['1'] = """<img src="{src}" class="foto-small-struct">""".format(src = src_foto) + "<a href='"+url_for('user.profile')+"/"+row_id+"'>"+row['1']+"</a>"
        head_dep = str(len(columns)+1)
        if Department.is_user_head(dep_id, int(row_id)):
            checked = "checked"
        else:
            checked = ''
        row[head_dep] = "<input onclick='change_head_dep(this, "+str(dep_id)+", "+row_id+")' type='checkbox' id='head_check' "+checked+">"
    return jsonify(**json_result)

```



##### 8 get_dep_if_user_head + count_users_in_dep_tree + get_head_user_in_dep_tree  => 유저프로필 ROUTE에서 사용된다

```python
@module.get("/profile")
@module.get("/profile/<int:user_id>")
def profile(user_id=None):
    user = auth.service.get_user() if user_id is None else User.get_by_id(user_id)
    if user is None:
        abort(404)
    user_department = Department.get_dep_if_user_head(user.id)
    count_users = ''
    if user_department:
        count_users = Department.count_users_in_dep_tree(user_department.id)
    if user.department_id:
        head_user = Department.get_head_user_in_dep_tree(user.department_id, user.id)
    else:
        dep = db.session.query(Department).filter_by(parent_id=None).first()
        head_user = Department.get_head_user_in_dep_tree(dep.id, user.id)
    return render_template('profile/profile.html', user=user,
                                                   user_department=user_department,
                                                   count_users=count_users,
                                                   head_user=head_user)
```





- `get_dep_if_user_head(user.id)`
  - **내 id로 first()로 조회해서 없으면 None이므로, return에 바로 붙인다.**
  - **내가 팀장인 부서가 있다면, `count_users_in_dep_tree`를 이용해서 팀원들의 수를 센다**
    - 없는 경우 안센다
  - **내 소속부서가 있다면, `get_head_user_in_dep_tree`를 이용해서 head_user(팀장)을 구한다**

- 내가 팀장인 부서가 있을 때, `count_users_in_dep_tree(user_department.id)`
  - 내가팀장인 팀을 조회한 뒤
  - **User** Entity에서 `count_users_in_department`를 이용해서 해당부서에 속한 유저를 센다
  - **내부 메서드 `count_users_recursively(dep)`를 이용해서 `부서를 재귀인자로` 자식부서들의 팀원들을 누적한 뒤 -1 을 해서 나빼고 센다**
- **if 나의 소속 부서가 있을 때** `get_head_user_in_dep_tree`를 이용해서 **소속부서 or 그 이상의 팀장**을 골라낸다
  - 소속부서의 객체를 조회한 뒤
  - **내부 메서드 `head_user_recursively`를 이용해서 `부서를 재귀인자로`**
    - **부서의 user_id(팀장)이 있으면 바로 반환한다**
      - 팀장 없는 부서라면 계쏙 재귀를 타서, 팀장있는 부서의 팀장까지 찾아가나보다
    - **부서의 부모부서가 있으면 부모부서객체를 찾아서, 다시 재귀를 때린다**
    - 둘다 안걸리는 순간에는 return None을 최종반환되게 한다?
- **else 내 소속부서가 없는 경우**
  - **`parent_id=None으로 검색하여 최상위부서(1개인듯)`를 검색한 뒤**
  - 최상위부서의 팀장을 반환한다.

```python
@classmethod
def get_dep_if_user_head(cls, user_id):
    return cls.query.filter_by(user_id=user_id).first()

@classmethod
def count_users_in_dep_tree(cls, dep_id):
    dep = cls.query.filter_by(id=dep_id).first()
    c_u = User.count_users_in_department(dep_id)
    def count_users_recursively(dep):
        dep_childs = cls.query.filter_by(parent_id=dep.id).all()
        count_users = 0
        for dep_child in dep_childs:
            count_users += User.count_users_in_department(dep_child.id)
            count_users += count_users_recursively(dep_child)
        return count_users
    c_u += count_users_recursively(dep)
    return c_u - 1

@classmethod
def get_head_user_in_dep_tree(cls, dep_id, user_id):
    dep = cls.query.filter_by(id=dep_id).first()
    def head_user_recursively(dep):
        if dep.user_id:
            return User.get_by_id(dep.user_id)
        if dep.parent_id:
            dep_parent = cls.query.filter_by(id=dep.parent_id).first()
            return head_user_recursively(dep_parent)
        return None
    if dep.user_id == user_id:
        if dep.parent_id:
            dep_parent = cls.query.filter_by(id=dep.parent_id).first()
            return head_user_recursively(dep_parent)
        return None
    return head_user_recursively(dep)
```



- **userprofile html**

  ```html
  {% extends "layout.html" %}
  {% block content %}
  <div class="col-md-8 col-md-offset-2 frame profile">
      <div class="row">
        <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12">
          <div class="header">
              <h3 class="title">{{ user.full_name or '' }}</h3>
              {% if user.id == current_user.id %}
              <div class="edit-buttons edit-buttons-in-profile">
                  <a href="{{ url_for('user.edit_profile') }}"><span class="glyphicon glyphicon-pencil"></span> Редактировать </a> &nbsp;
                  <a href="{{ url_for('user.edit_pass') }}"><span><i class="fa fa-lg fa-key"></i></span> Изменить пароль</a>
              </div>
              {% elif current_user.is_admin or 'manage_users' in current_user.get_permissions() %}
              <div class="edit-buttons edit-buttons-in-profile">
                  <a href="{{ url_for('admin.edit_user', id=user.id) }}"><span class="glyphicon glyphicon-pencil"></span> Редактировать </a> &nbsp;
              </div>
              {% endif %}
          </div>
        </div>
      </div>
  
      <div class="row content">
        <div class="col-xs-12 col-sm-5 col-md-5 col-lg-5">
          <p>
            <img src="{{ user.photo.get_url() if user and user.photo else '/static/img/no_photo.jpg' }}" class="img-thumbnail" alt="Фото {{ user.full_name }}">
          </p>
  
        </div>
        <div class="col-xs-12 col-sm-7 col-md-7 col-lg-7">
          <table class="table table-striped">
              <tbody>
                  {% if user.department %}
                      <tr>
                          <td>Подразделение</td>
                          <td><span class="fa fa-sitemap"></span> {{ user.department.name }}</td>
                      </tr>
                  {% endif %}
                  {% if user.position %}
                      <tr>
                          <td>Должность</td>
                          <td><span class="fa fa-users"></span> {{ user.position }}</td>
                      </tr>
                  {% endif %}
                  {% if head_user %}
                      <tr>
                          <td>Кому подчиняется</td>
                          <td><span class="fa fa-star-o"></span> {{ head_user.full_name }}</td>
                      </tr>
                  {% endif %}
                  {% if user_department.name %}
                      <tr>
                          <td>Кем руководит</td>
                          <td><span class="fa fa-street-view"></span> {{ user_department.name }} ({{ count_users }})</td>
                      </tr>
                  {% endif %}
                  {% if user.inner_phone %}
                      <tr>
                          <td>Внутренний номер</td>
                          <td><span class="fa fa-phone"></span> {{ user.inner_phone }}</td>
                      </tr>
                  {% endif %}
                  {% if user.birth_date %}
                      <tr>
                          <td>Дата рождения</td>
                          <td><span class="fa fa-birthday-cake"></span> {{ user.birth_date.strftime('%d.%m') }}</td>
                      </tr>
                  {% endif %}
                  {% if user.mobile_phone %}
                      <tr>
                          <td>Номер мобильного телефона</td>
                          <td><span class="fa fa-mobile" style="font-size: 18px;margin-top: -2px;"></span> {{ user.mobile_phone }}</td>
                      </tr>
                  {% endif %}
                  {% if user.email %}
                      <tr>
                          <td>Email</td>
                          <td><span class="glyphicon glyphicon-envelope"></span> {{ user.email }}</td>
                      </tr>
                  {% endif %}
                  {% if user.skype %}
                      <tr>
                          <td>Skype</td>
                          <td><span class="fa fa-skype" style="font-size: 15px;"></span> {{ user.skype }}</td>
                      </tr>
                  {% endif %}
                  {% if user.id == current_user.id %}
                      <tr>
                          <td>Подписатсья на рассылку новостей:</td>
                          <td>
                              <input id="edit_news_notification" type="checkbox" {% if user.news_notification %}checked{% endif %}/>
                          </td>
                      </tr>
                  {% endif %}
              </tbody>
          </table>
        </div>
      </div>
  
      <div class="row content activity">
          <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6">
              <h2>Новости ({{ user.news|length }}):</h2>
              <div id="news" class="list-group"></div>
              <button id="moreNews" style="display: none" type="button" class="btn btn-default">Больше</button>
          </div>
          <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6">
              <h2>Коментарии ({{ user.comments|length }}):</h2>
              <div id="comments" class="list-group"></div>
              <button id="moreComments" style="display: none" type="button" class="btn btn-default">Больше</button>
          </div>
      </div>
  </div>
  
  <script>
  $( "#edit_news_notification").on("change", function( e ) {
      var data = $(this).is(':checked');
      $.ajax({
          url: "{{ url_for('api_v1.edit_news_notification') }}",
          type: "PUT",
          data: "subscribed="+data
      })
  });
  </script>
  
  <script>
  function renderNews ( obj ) {
      var newA = $( '<a class="list-group-item"></a>' );
      var newSpan = $( '<span class="badge"></span>' );
  
      newSpan.append( niceDateFormat(obj.created_date) );
  
      newA.attr( 'href', "{{ url_for('news.news_one', id=-1) }}".replace( '-1', obj.news_id ) );
      newA.append( obj.news_title );
      newA.append( newSpan );
  
      return newA;
  }
  
  function renderComments ( obj ) {
      var newA = $( '<a class="list-group-item"></a>' );
      var newSpan = $( '<span class="badge"></span>' );
      var newStrong = $( '<strong></strong>' );
  
      newSpan.append( niceDateFormat(obj.last_modified_date) );
      newStrong.append( ' (' + obj.comments_amount + ') ' );
  
      newA.attr( 'href', "{{ url_for('news.news_one', id=-1) }}".replace( '-1', obj.news_id ) );
      newA.append( newStrong );
      newA.append( obj.news_title );
      newA.append( newSpan );
  
      return newA;
  }
  
  $(document).ready( function () {
      var newsPaginator = new LazyPaginator({
          url: "{{ url_for('api_v1.get_user_news', id=user.id) }}",
          targetElem: $( "#news" ),
          buttonMore: $( "#moreNews" ),
          render: renderNews
      });
  
      var commentsPaginator = new LazyPaginator({
          url: "{{ url_for('api_v1.get_user_comments_in_news', id=user.id) }}",
          targetElem: $( "#comments" ),
          buttonMore: $( "#moreComments" ),
          render: renderComments
      });
  
      newsPaginator.init();
      commentsPaginator.init();
  
      newsPaginator.get();
      commentsPaginator.get();
  });
  </script>
  
  {% endblock %}
  
  
  ```

  



##### 9  delete는  나의 자식 부서가 없으면서 and 해당부서이하의 User들을 누적한 count가 0일때만, 해당부서를 찾아서 삭제한다.

```python

@module.get('/company-structure/delete/<int:dep_id>')
def delete_structure(dep_id):
    Department.delete(dep_id)
    return redirect(url_for('admin.company_structure'))


```






```python
@classmethod
def delete(cls, uid):
    parent_dep = cls.query.filter_by(parent_id=uid)
    if (parent_dep.count() == 0) and (User.count_users_in_department(uid) == 0):
        cls.query.filter_by(id=uid).delete()
        db.session.commit()
```


#### 나머지 Company_structure.py에서 사용 분석

##### 1 company_structre는 get_departments(parend_id=None) 재귀로,  부모_id =None의 최상위부터, 차근차근내려가며 row2dict

```python
@module.get('/company-structure')
def company_structure():
    departments = get_departments()
    return render_template('admin/company_structure/structure.html', departments=departments)
```

```python
def get_departments(parent_id=None):
    dep_list = []
    departments = db.session.query(Department).filter_by(parent_id=parent_id).all()
    for dep in departments:
        dep_dict = row2dict(dep)
        dep_dict['dep_list'] = get_departments(dep.id)
        dep_list.append(dep_dict)
    if len(departments):
        return dep_list
    else:
        return None
```

- 부모없는 최상위 부서들 순회하며
  - **자신을dict**로 만들고
  - 나를 부모로가지는 departments들을 **재귀 호출해서 list를 얻으면 자신의 dict의 `dep_list` key**에 넣는다.
  - 만들어진 **자신dict를 빈 list에 append**하여  반환한다. 자식들 **.all() => len()으로 검사해서 없으면 None으로 자식종착역이다.**

- row2dict

  - datatables.py **내부에 lambda 지연실행메서드 객체로 정의**되어있다.

  ```python
  log = getLogger(__file__)
  
  row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}
  
  if sys.version_info > (3, 0):
      unicode = str
  ColumnTuple = namedtuple(
      'ColumnDT',
      ['column_name', 'mData', 'search_like', 'filter', 'searchable'])
  
  ```



- html

  - **만든 dep_list 누적 list를 recursive로 순회한다**
    - dep.**dep_list**의 자식list가 보이면 재귀를 돌린다

  ```html
  {% extends "admin/layout.html" %}
  
  {% block title %}Structure{% endblock %}
  {% block content %}
  <div class="container-fluid">
      <h2>Company structure</h2>
      {% if departments %}
          <ul>
          {%- for dep in departments recursive %}
              <li>
                  <p>{{ dep.name }}
                      <a href="{{ url_for('admin.department_info', dep_id=dep.id) }}"><span class="glyphicon glyphicon-user"></span></a>
                      <a href="{{ url_for('admin.edit_structure', dep_id=dep.id) }}"><span class="glyphicon glyphicon-pencil"></span></a>
                      <a href="{{ url_for('admin.add_structure', dep_id=dep.id) }}"><span class="glyphicon glyphicon-plus"></span></a>
                      <a href="{{ url_for('admin.delete_structure', dep_id=dep.id) }}"><span class="glyphicon glyphicon-minus"></span></a>
                  </p>
              {%- if dep.dep_list -%}
                  <ul><p>{{ loop(dep.dep_list) }}</p></ul>
              {%- endif %}</li>
          {%- endfor %}
          </ul>
      {% endif %}
  </div>
  {% endblock %}
  ```

  

##### 2 company 상세보기 in header => department 상세보기도 마찬가지로 get_departmets(parent_id) 로 얻은 dep_list자식으로 든 dict를 건네 준 뒤, metisMenu를 써서 처리한다

- 상세보는 route의 호출장소는 header.html이다
  - admin에게만 공개된 메뉴

```python
{% block nav %}
<nav class="navbar navbar-default">
    <div class="container-fluid">
        <div class="navbar-header">
          <a class="navbar-brand logo" href="/"><img src="/static/img/logo.png" alt=""/></a>
        </div>

        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse">
          <ul class="nav navbar-nav">
            <li><a href="{{ url_for('admin.s_users') }}">Пользователи </a></li>
            <li><a href="{{ url_for('admin.s_news') }}">Новости </a></li>
            {% if current_user.is_admin or ('change_company_structure' in current_user.get_permissions()) %}
                <li><a href="{{ url_for('admin.company_structure_show') }}">Структура компании </a></li>
            {% endif %}
            <li><a href="{{ url_for('admin.news_categories') }}">Разделы новостей </a></li>
          </ul>
          <div class="user-profile-header">
            <div class="user-info">
                <a class="user-name" href="{{ url_for('user.profile') }}">{{ current_user.full_name }}</a>
                <a class="user-logout" href="{{ url_for('login.logout') }}">Выход</a>
                <a class="user-logout block" href="{{ url_for('main.list_all') }}">Портал </a>
            </div>
            <div class="user-icon" {% if current_user.photo %} style="background-image: url('{{ current_user.photo.get_url('thumbnail')}}')" {% endif %}>
            <a href="{{ url_for('user.profile') }}"></a>
            </div>
          </div>
        </div>
    </div>
</nav>
{% endblock %}

```

- route

```python
@module.get('/company-structure-show')
def company_structure_show():
    departments = get_departments()
    return render_template('admin/company_structure/structure_show.html', departments=departments)


```



##### 3 department.html의 DataTable에서, 화면시작시 특정부서에 대한 ajax요청이 온다( 일단 내용 생략)

```js
$(document).ready(function() {
    $('#users_datatables').DataTable({
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": "{{ url_for('admin.dep_users_json', dep_id=department.id ) }}"
    });
} );
```

```python
@module.get('/dep_users_json/<int:dep_id>')
def dep_users_json(dep_id):
    columns = []
    columns.append(ColumnDT('id', filter=_default_value))
    columns.append(ColumnDT('full_name', filter=_default_value))
    columns.append(ColumnDT('email', filter=_default_value))
    columns.append(ColumnDT('login', filter=_default_value))
    columns.append(ColumnDT('mobile_phone', filter=_default_value))
    columns.append(ColumnDT('inner_phone', filter=_default_value))
    query = db.session.query(User).filter_by(department_id=dep_id)
    rowTable = DataTables(request, User, query, columns)
    json_result = rowTable.output_result()
    departments = Department.get_all()
    for row in json_result['aaData']:
        row_id = row['0']
        last_columns = str(len(columns))
        dep_html = ''
        for dep in departments:
            sel = 'selected' if dep.id == dep_id else ''
            dep_html += "<option value='"+str(dep.id)+"/"+row_id+"' "+sel+">"+dep.name+"</option>"
        manage_html = """
          <select onchange="change_user_dep(this.value)" id="first-disabled" class="selectpicker" data-hide-disabled="true" data-live-search="true" data-width="200px">
            <optgroup label="Доп возможности">
              <option value="0/"""+row_id+"""">Удалить из отдела</option>
            </optgroup>
            <optgroup label="Отделы">"""+dep_html+"""</optgroup>
          </select>
          <script type="text/javascript">$('.selectpicker').selectpicker({style: 'btn-default',size: 5});</script>
          """
        row[last_columns] = manage_html
        src_foto = ''
        user = User.get_by_id(row_id)
        if user.photo:
            src_foto = user.photo.get_url('thumbnail')
        else:
            src_foto = '/static/img/no_photo.jpg'
        row['1'] = """<img src="{src}" class="foto-small-struct">""".format(src = src_foto) + "<a href='"+url_for('user.profile')+"/"+row_id+"'>"+row['1']+"</a>"
        head_dep = str(len(columns)+1)
        if Department.is_user_head(dep_id, int(row_id)):
            checked = "checked"
        else:
            checked = ''
        row[head_dep] = "<input onclick='change_head_dep(this, "+str(dep_id)+", "+row_id+")' type='checkbox' id='head_check' "+checked+">"
    return jsonify(**json_result)
```



- datatable.py

  ```python
  # -*- coding: utf-8 -*-
  import sys
  from sqlalchemy.sql.expression import asc, desc
  from sqlalchemy.sql import or_, and_
  from sqlalchemy.orm.properties import RelationshipProperty
  from sqlalchemy.orm.collections import InstrumentedList
  from sqlalchemy.sql.expression import cast
  from sqlalchemy import String
  from collections import namedtuple
  from logging import getLogger
  from copy import deepcopy
  
  
  log = getLogger(__file__)
  row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}
  if sys.version_info > (3, 0):
      unicode = str
  ColumnTuple = namedtuple(
      'ColumnDT',
      ['column_name', 'mData', 'search_like', 'filter', 'searchable'])
  
  
  def get_attr(sqla_object, attribute):
      output = sqla_object
      for x in attribute.split('.'):
          if type(output) is InstrumentedList:
              output = ', '.join([getattr(elem, x) for elem in output])
          else:
              output = getattr(output, x)
      return output
  
  
  class ColumnDT(ColumnTuple):
      def __new__(cls, column_name, mData=None, search_like=None,
                  filter=str, searchable=True):
          return super(ColumnDT, cls).__new__(cls, column_name, mData, search_like, filter, searchable)
  
  
  class DataTables:
      def __init__(self, request, sqla_object, query, columns):
          self.request_values = deepcopy(dict(request.args))
          for key in self.request_values:
              self.request_values[key] = self.request_values[key][0]
          for key, value in self.request_values.items():
              try:
                  self.request_values[key] = int(value)
              except ValueError:
                  if value in ("true", "false"):
                      self.request_values[key] = value == "true"
          self.sqla_object = sqla_object
          self.query = query
          self.columns = columns
          self.results = None
          self.cardinality_filtered = 0
          self.cardinality = 0
          self.run()
  
  
      def output_result(self):
          output = {}
          output['sEcho'] = str(int(self.request_values['sEcho']))
          output['iTotalRecords'] = str(self.cardinality)
          output['iTotalDisplayRecords'] = str(self.cardinality_filtered)
          output['aaData'] = self.results
          return output
  
  
      def run(self):
          self.cardinality = self.query.count()
          rez = []
          for row in self.query.all():
              rez.append(row)
          self.filtering()
          self.sorting()
          self.paging()
          rez = []
          for row in self.query.all():
              rez.append(row2dict(row))
          self.results = rez
          formatted_results = []
          for i in range(len(rez)):
              row = dict()
              for j in range(len(self.columns)):
                  col = self.columns[j]
                  tmp_row = self.results[i][col.column_name]
                  if col.filter:
                      if sys.version_info < (3, 0) \
                              and hasattr(tmp_row, 'encode'):
                          tmp_row = col.filter(tmp_row.encode('utf-8'))
                      tmp_row = col.filter(tmp_row)
                  row[col.mData if col.mData else str(j)] = tmp_row
              formatted_results.append(row)
          self.results = formatted_results
  
  
      def filtering(self):
          search_value = self.request_values.get('sSearch')
          condition = None
  
  
          def search(idx, col):
              tmp_column_name = col.column_name.split('.')
              for tmp_name in tmp_column_name:
                  if tmp_column_name.index(tmp_name) == 0:
                      obj = getattr(self.sqla_object, tmp_name)
                      parent = self.sqla_object
                  elif isinstance(obj.property, RelationshipProperty):
                      parent = obj.property.mapper.class_
                      obj = getattr(parent, tmp_name)
                  if not hasattr(obj, 'property'):
                      sqla_obj = parent
                      column_name = tmp_name
                  elif isinstance(obj.property, RelationshipProperty):
                      sqla_obj = obj.mapper.class_
                      column_name = tmp_name
                      if not column_name:
                          column_name = obj.property.table.primary_key.columns \
                              .values()[0].name
                  else:
                      sqla_obj = parent
                      column_name = tmp_name
              return sqla_obj, column_name
          if search_value:
              search_value_list = str(search_value).split()
              for search_val in search_value_list:
                  conditions = []
                  for idx, col in enumerate(self.columns):
                      if self.request_values.get('bSearchable_%s' % idx) in (
                              True, 'true') and col.searchable:
                          sqla_obj, column_name = search(idx, col)
                          conditions.append(
                              cast(get_attr(sqla_obj, column_name), String).ilike('%%%s%%' % search_val))
                  condition = or_(*conditions)
                  if condition is not None:
                      self.query = self.query.filter(condition)
          conditions = []
          for idx, col in enumerate(self.columns):
              search_value2 = self.request_values.get('sSearch_%s' % idx)
              if search_value2:
                  sqla_obj, column_name = search(idx, col)
                  if col.search_like:
                      conditions.append(
                          cast(get_attr(sqla_obj, column_name), String).ilike('%%%s%%' % search_value2))
                  else:
                      conditions.append(
                          cast(get_attr(sqla_obj, column_name), String).__eq__(search_value2))
                  if condition is not None:
                      condition = and_(condition, and_(*conditions))
                  else:
                      condition = and_(*conditions)
          if condition is not None:
              self.query = self.query.filter(condition)
              self.cardinality_filtered = self.query.count()
          else:
              self.cardinality_filtered = self.cardinality
  
  
      def sorting(self):
          sorting = []
          Order = namedtuple('order', ['name', 'dir'])
          if self.request_values.get('iSortingCols') > 0:
              for i in range(int(self.request_values['iSortingCols'])):
                  sorting.append(Order(self.columns[int(self.request_values['iSortCol_' + str(i)])].column_name, self.request_values['sSortDir_' + str(i)]))
          for sort in sorting:
              tmp_sort_name = sort.name.split('.')
              for tmp_name in tmp_sort_name:
                  if tmp_sort_name.index(tmp_name) == 0:
                      obj = getattr(self.sqla_object, tmp_name)
                      parent = self.sqla_object
                  elif isinstance(obj.property, RelationshipProperty):
                      parent = obj.property.mapper.class_
                      obj = getattr(parent, tmp_name)
                  if not hasattr(obj, "property"):
                      sort_name = tmp_name
                      if hasattr(parent, "__tablename__"):
                          tablename = parent.__tablename__
                      else:
                          tablename = parent.__table__.name
                  elif isinstance(obj.property, RelationshipProperty):
                      sort_name = tmp_name
                      if not sort_name:
                          sort_name = obj.property.table.primary_key.columns \
                              .values()[0].name
                      tablename = obj.property.table.name
                  else:
                      sort_name = tmp_name
                      if hasattr(parent, "__tablename__"):
                          tablename = parent.__tablename__
                      else:
                          tablename = parent.__table__.name
  
              sort_name = "%s.%s" % (tablename, sort_name)
              self.query = self.query.order_by(
                  asc(sort_name) if sort.dir == 'asc' else desc(sort_name))
  
  
      def paging(self):
          pages = namedtuple('pages', ['start', 'length'])
          if (self.request_values['iDisplayStart'] != "") \
                  and (self.request_values['iDisplayLength'] != -1):
              pages.start = int(self.request_values['iDisplayStart'])
              pages.length = int(self.request_values['iDisplayLength'])
          offset = pages.start + pages.length
          self.query = self.query.slice(pages.start, offset)
  ```



##### 4 edit를 post로 날릴 때, .rename / .set_parent를 순차적으로 호출한다. set_parent는 현재 존재하는 것을 찾고나서, 거기다가 부모를 박으므로

```python
@module.get('/company-structure/edit/<int:dep_id>')
def edit_structure(dep_id):
    department = Department.get_by_id(dep_id)
    dep_parents = Department.get_parent_all(dep_id)
    return render_template('admin/company_structure/edit_structure.html',
                            department=department,
                            dep_parents = dep_parents)


@module.post('/company-structure/edit-post/')
def edit_structure_post():
    v = Validator(request.form)
    v.field("name_structure").required()
    if v.is_valid():
        name_structure = v.valid_data.name_structure
        Department.rename(request.form.get("department_id"), name_structure)
        Department.set_parent(request.form.get("department_id"), request.form.get("parent"))
        return jsonify({"status": "ok"})
    return jsonify({"status": "fail",
                    "errors": v.errors})
```

```python
   @classmethod
    def rename(cls, uid, new_name):
        dep = cls.query.filter_by(id=uid).first()
        dep.name = new_name
        db.session.add(dep)
        db.session.commit()
        
    @classmethod
    def set_parent(cls, uid, pid):
        dep = cls.query.filter_by(id=uid).first()
        if pid == '0':
            dep.parent_id = None
        else:
            dep.parent_id = pid
        db.session.add(dep)
        db.session.commit()

```





##### 5 add를 post로 날릴 때 .add가 호출된다

```python
@module.get('/company-structure/add/<int:dep_id>')
def add_structure(dep_id):
    department = Department.get_by_id(dep_id)
    return render_template('admin/company_structure/add_structure.html', department=department)


@module.post('/company-structure/add-post/')
def add_structure_post():
    v = Validator(request.form)
    v.field("name_structure").required()
    if v.is_valid():
        name_structure = v.valid_data.name_structure
        Department.add(request.form.get("department_id"), name_structure)
        return jsonify({"status": "ok"})
    return jsonify({"status": "fail",
                    "errors": v.errors})
```





```python
@classmethod
def add(cls, uid, new_name):
    dep = Department(parent_id=uid, name=new_name)
    db.session.add(dep)
    db.session.commit()
```







##### 6 특정부서에 user를 할당할 때, User.find_user를 이용해서, [부서가 없거나 다른부서에 속한 사람들을 name으로 검색]해서 목록을 골라낸다

```python
@classmethod
def find_user(cls, dep_id, name):
    return cls.query.filter(or_(User.department_id == None, User.department_id != dep_id)).filter(User.full_name.ilike('%'+name+'%')).limit(5).all()
```

```python
@module.get('/company-structure/get-users/<int:dep_id>/<user_name>/')
def get_list_users(dep_id, user_name):
    department = Department.get_by_id(dep_id)
    users = User.find_user(dep_id, user_name)
    users_list = []
    a = {"users":[]}
    for u in users:
        src_foto, dep_name = '', ''
        user = User.get_by_id(u.id)
        if user.photo:
            src_foto = user.photo.get_url('thumbnail')
        else:
            src_foto = '/static/img/no_photo.jpg'
        if u.department_id:
            dep_name = u.department.name or ''
        else:
            dep_name = ''
        a["users"].append({"u_id":u.id,
                           "full_name":u.full_name,
                           "dep_name":dep_name,
                           "src_foto":src_foto})
    return jsonify(**a)
```

- view에서는 react로 userName이 변할때마다 해당부서의, 가용 유저를 골라내나보다

  ```js
  var ManageUsers = React.createClass({displayName: "ManageUsers",
  
      getInitialState: function(){
          return { userName: '', userList: []};
      },
  
      userNameChange: function(e){
          this.setState({userName:e.target.value});
          var name = e.target.value;
          var self = this;
          console.log(name);
  
          $.ajax({
            url: "/admin/company-structure/get-users/"+self.props.dep_id+"/"+name+"/",
            success: function(data){
              //console.log(data['users']);
              self.setState({userList:[]});
              var arr = data['users']
              self.setState({userList:data['users']});
              console.log(self.state.userList);
            }
          });
  
      },
  ```







##### 7  user를 부원으로  dept에 박을때 User.add_user2dep / user를 dept 팀장으로 박을 땐 Department.add_head4dep

```python
@module.get('/company-structure/set-user-dep/<int:dep_id>/<int:user_id>/')
def set_user_to_dep(dep_id, user_id):
    User.add_user2dep(dep_id, user_id)
    return jsonify({'status': 'ok'})
```



```python
@classmethod
def add_user2dep(cls, dep_id, user_id):
    u = cls.query.filter_by(id=user_id).first()
    if dep_id == 0:
        dep_id = None
    u.department_id = dep_id
    db.session.add(u)
    # commit 빠트린듯?
```





- 팀장으로 박을 때

```python
@module.get('/company-structure/set-head-dep/<int:option>/<int:dep_id>/<int:user_id>/')
def set_user_head_dep(option, dep_id, user_id):
    Department.add_head4dep(option, dep_id, user_id)
    return jsonify({'status': 'ok'})
```



```python
    @classmethod
    def add_head4dep(cls, option, dep_id, user_id):
        deps = cls.query.filter_by(user_id=user_id).all()
        for dep in deps:
            dep.user_id = None
            db.session.add(dep)
        dep = cls.query.filter_by(id=dep_id).first()
        if option == 1:
            dep.user_id = user_id
        elif option == 2:
            dep.user_id = None
        db.session.add(dep)
        db.session.commit()
```





- html에서는 각각을 department.html에서 change시 ajax처리

  ```js
      window.change_user_dep = function(dep_user){
          $.ajax({
            url: "/admin/company-structure/set-user-dep/"+dep_user+"/",
            success: function(json) {
                  if(json.status == 'ok'){
                      console.log("OK");
                      location.reload();
                  }
            }
          });
      }
      //change_user_dep('0', '818');
  
      window.change_head_dep = function(self, dep_id, user_id){
        var option = 1;
        if($(self).prop("checked")){
          console.log("1", user_id, dep_id);
          option = 1;
          $('input:checkbox').prop('checked', false);
          $(self).prop('checked', true);
        } else {
          console.log("2", user_id, dep_id);
          option = 2;
        }
  
        $.ajax({
          url: "/admin/company-structure/set-head-dep/"+option+"/"+dep_id+"/"+user_id,
          success: function(json) {
                if(json.status == 'ok'){
                    console.log("OK");
                }
          }
        });
  
      }
  ```

  



##### 8 department-order와 manage-users는 따로 페이지를 두고 nestedSortable로 처리되는 것 같은데 미완성인 것 같다

```python
@module.get('/department-order/<int:dep_id>')
def department_order(dep_id):
    department = Department.get_by_id(dep_id)
    return render_template('admin/company_structure/edit_order.html', department=department)


@module.get('/company-structure/manage-users/<int:dep_id>')
def manage_users(dep_id):
    department = Department.get_by_id(dep_id)
    return render_template('admin/company_structure/manage_users.html', department=department)
```



- edit_order.html

  ```html
  {% extends "admin/layout.html" %}
  
  {% block title %}Структура{% endblock %}
  {% block content %}
  <div class="container-fluid">
      <h2>{{ department.name }}</h2>
      <div id="manage-users"></div>
      <ol class="sortable">
        <li><div>Some content</div></li>
        <li>
            <div>Some content</div>
            <ol>
                <li><div>Some sub-item content</div></li>
                <li><div>Some sub-item content</div></li>
            </ol>
        </li>
        <li><div>Some content</div></li>
      </ol>
  </div>
  <script type="text/javascript">
  $(document).ready(function(){
  
      $('.sortable').nestedSortable({
          handle: 'div',
          items: 'li',
          toleranceElement: '> div'
      });
  
  });
  </script>
  
  
  {% endblock %}
  ```

  

- manage-users.html은 angualar로 된 것 같은데 길어서 생략



####  참고) fill_db.py를 logger + decorator와 함께

```python
import logging
import sys

from application import db, ldap, create_app
from application.models.user import User
from application.models.department import Department


logger = logging.getLogger('filldb')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s: %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def logging_wrapper(func):
    def wrapper(*args, **kwargs):
        logger.info("Start filling DB ...")
        func(*args, **kwargs)
        logger.info("DB has been filled successfully.")

    return wrapper


@logging_wrapper
def add_all_users():
    for user_attr in ldap.get_all_users():
        user = User(login=user_attr.get('cn', [''])[0],
                    full_name=user_attr.get('displayName', [''])[0],
                    mobile_phone=user_attr.get('mobile', [''])[0],
                    inner_phone=user_attr.get('telephoneNumber', [''])[0],
                    email=user_attr.get('mail', [''])[0])
        db.session.add(user)
    db.session.commit()


@logging_wrapper
def add_all_departments():
    for department_name in ldap.get_all_departments():
        department = Department(name=department_name)
        db.session.add(department)
    db.session.commit()


@logging_wrapper
def add_departments_members():
    for department_name, usernames in ldap.get_department_info().items():
        department = Department.get_by_name(department_name)
        for user in User.query.filter(User.login.in_(usernames)):
            user.department = department
    db.session.commit()


COMMANDS = {
    'users': add_all_users,
    'departments': add_all_departments,
    'departments-members': add_departments_members
}


def fill_db():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        logger.error("Wrong argument passed.")
    else:
        COMMANDS[sys.argv[1]]()

if __name__ == '__main__':
    app = create_app('default')
    with app.app_context():
        fill_db()

```



#### 참고) DataTable로 변형하는 기술



#### 참고) Thumbnail 처리 기술



#### 참고) Vote를 Mixin으로 소유하는 복잡한 기술



### 9 [spark8899](https://github.com/spark8899)/**[ops-system](https://github.com/spark8899/ops-system)**



#### model

- parent 관계칼럼에 `remote_side=`를 id외에 name까지
- name에는  unique= , index= True 2개다

```python
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    department = db.relationship('Department', backref=db.backref('users'))

    def __repr__(self):
        return '<User %r>' % self.email

    def __str__(self):
        return self.email

    # Custom User Payload
    def get_security_payload(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'last_login_at': self.last_login_at,
            'current_login_at': self.current_login_at,
            'last_login_ip': self.last_login_ip,
            'current_login_ip': self.current_login_ip,
            'login_count': self.login_count,
            'confirmed_at': self.confirmed_at
        }


class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    description = db.Column(db.String(128))

    parent = db.relationship("Department", remote_side=[id, name])
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Department %r>' % self.name

    def __str__(self):
        return self.name
```

