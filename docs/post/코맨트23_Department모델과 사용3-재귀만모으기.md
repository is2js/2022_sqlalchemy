### 6번

#### 현재부서 + 자식부서들의 id를 누적하는 재귀

1. 일단 **현재부서 -> 자식부서list를 뽑아서 순회해야지** `자식부서가 반복문 안에서 다음재귀에서 현재부서 역할`을 할 수 있게 된다.

   - 자기참조면 .children으로 가능하다

   - 대신 children relationship에 부서조회시 필수정렬을 .path로 설정해주자.

```python
    @property
    def get_child_department(self):
        return RelDepartment.query.filter_by(parent_department_id=self.id).order_by(RelDepartment.createtime_loc.desc()).all()
```

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







##### 사용예시 : 수정form에서 선택가능한 부모부서 options 추출  : 전체부서 - (나, 자식id)제외 -> jsonify로 내려주는 POST처리

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





### 8번

#### 부서객체list -> dict_list로 변환하여 jinja에서 재귀로 뿌리기

1. 해당객체를 지연함수 lambda `row2dict`()에 넣어서 **객체가 오면 `객체.__table__.columns`를 순회하며, `getattr(객체, column.name)`을 str()으로 다 만들어서 dict generator로 만든다.**

```python
row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}

```

2. 이 때 자신의 id를 건네주면, **내부에서 알아서 자식들만 순회 -> `자식들 dict list를 반환해주는 재귀메서드`에 `자신id`를 인자로 넣어, `자신의 dict + 자식들의 dict_list with dep_list key`로 만든 dict list를 반환해준다.**
   - 자식들 dep_list (dict_list)가 없는 경우에는 `None`을 반환하여, `dep_list`key에는 None이 들어가게 한다

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



##### 사용예시 : 조회화면에서 dict_list를 jinja에 반환

```python
@module.get('/company-structure')
def company_structure():
    departments = get_departments()
    return render_template('admin/company_structure/structure.html', departments=departments)
```



###### view에서는 dict_list 를 jinja 재귀로 순회한다

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



- 일반적인 조회분만 아니라 상세보기?에서도 jinja 재귀로 순회한다

```html
@module.get('/company-structure-show')
def company_structure_show():
    departments = get_departments()
    return render_template('admin/company_structure/structure_show.html', departments=departments)


```



#### (팀장용) 특정부서_id -> 현 부서 + 자식부서들 팀원수 누적하기

1. dep_id를 받아, dep객체를 찾고

2. dep객체로 User의 cls메서드로 **부서객체에 있는 직원 user수를 센다**

   ```python
   def count_users_in_department(cls, department):
       return cls.query.filter_by(department_id=department).count()
   ```

3. 현부서를 받아,  자식들의 직원수를 누적카운팅하는 재귀메서드를 통해

   1. 자식부서들을 순회하면서, 각 부서들의 직원수들을 누적한다
   2. **시작부서인 현부서의 수의 직원수를 1명 뺀다? 아니면 팀장으로서 직원수만 세기위해 팀장 -1명을 뺀다?**

```python
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
```



#### (직원용) 특정부서id, 유저id -> 있다면 부모부서로 재귀하면서, 특정유저의 소속부서 팀장 골라내기

1. dep_id, user_id를 받아서
2. dep객체를 찾은 뒤, dep의 팀장 == user_id로 동일하여 **받은 유저가, 받은 부서팀장인지 확인한 뒤**
   1. 팀장이 아니면 **재귀를 통해 **
      1. **부서의 팀장이 있다면, 그 팀장을 User에서 찾는다.**
      2. **(팀장은 없는데) 상위부서가 있다면, 상위부서를 찾은 뒤, 다시 팀장을 찾는 재귀를 돌린다**
   2. 팀장이면
      1. 해당부서의 **상위부서가 있는지 확인한 뒤, 해당부서를 `부서 -> 팀장찾는 재귀`를 톨린다**
      2. (팀장인데, 상위부서가 없으면) None을 반환한다?
   3. (팀장이 아니면) 팀장을 찾는 재귀를 돌린다

```python
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



##### 사용예시 : 특정직원의 정보 프로필

1. 현재유저가 팀장인 부서를 찾는다. `user_department`
   1. 현재유저가 팀장인 부서가 있다면, **현 + 자식부서들의 직원수를 누적count한다.**
      - 없으면 string 빈문자열로 둔다 `count_users`
2. if 현재유저의 소속부서가 있다면
   1. `현재유저의 소속부서` + `현재유저`를 인자로하여 **부모부서까지 재귀로 뒤져 팀장을 골라낸다**
3. else 현재유저의 소속부서가 없다면 
   1. 최상위 부서(1개)를 fist로 뽑고, 
   2. `최상위부서` + `현재유저`를 인자로하여 **(없지만 부모부서까지 재귀로 뒤져) 팀장을 골라낸다**
4. `현재유저` + `현재유저가 팀장인 부서 및 하위모든부서 팀원수` + `소속부서의 팀장`까지 골라낸다

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



##### userprofile.html

- `if`로 다 시작한다
  - 소속부서
  - 소속position
  - `소속부서의 팀장`이면
    - 소속부서 팀장.name
  - `내가 팀장인 부서`가 있으면
    - `내가 팀장인 부서` + `하위부서 직원수`

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

