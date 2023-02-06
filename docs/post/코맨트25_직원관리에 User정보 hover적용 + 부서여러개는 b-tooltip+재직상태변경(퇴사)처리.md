### 직원관리에서 User정보 드러내기



#### 기존 부서정보 admin/employee.html에서 user정보는 제거하고 나중에 javascript로 보여주기

- employee.user로 시작하는 것들 주석처리
- **employee.get_dept_and_position_list()를  front에서 호출해서 tag형식으로 부서(직책)을 뿌려준다?**
  - backend에서 미리 같이 날리려면 scalars 말고 execute?
  - 그러려면 메서드를 hybrid-property로 만든 뒤 select()절에 올려주고나서, execute?

![image-20230112164408214](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230112164408214.png)





#### baseModel에서 to_dict시 inspect로 사용했다가 관계필드까지 조회하다가 DetachedError -> self.table.columns로 변환하기

```python
class BaseModel(Base):
    __abstract__ = True

    add_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pub_date = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def to_dict(self):
        # inspect(self)시 관계필드까지 조회하는데, form이나 front에서 DetachedError난다.
        # <-> 반면 self.__table__.columns는 관계필드를 조회안한다.
        return {c.name: getattr(self, c.name) for c in self.__table__.columns
                if c.name not in []  # 필터링 할 칼럼 모아놓기
                }
        # return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

```



#### employee.user.role로 조회하는 것을 메서드 or hybrid_property로 조회하도록 반영하기

```python
#### with other entity
@hybrid_property
def role(self):
    with DBConnectionHandler() as db:
        stmt = (
            select(Role)
            .where(Role.users.any(User.id == self.user_id))
        )
        role = db.session.scalars(stmt).first()
        return role

    #### with other entity
    @hybrid_property
    def is_staff(self):
        return self.role.is_(Roles.STAFF)

    #### with other entity
    @hybrid_property
    def is_executive(self):
        return self.role.is_(Roles.EXECUTIVE)

```



#### user상태에서, 마이페이지에 직원정보 조회를 위해, if 직원정보가 있는지 확인하는 메서드 구현

- .is_staff는 User상태에서 주어질 수 있는 역할(직위)를  언제든지 줄 수 있지만, employee가 된 것은 아니다. **직원인지 구분하려면 직원정보가 있는지 확인해야한다.**

```python
@hybrid_property
def is_employee_active(self):
    with DBConnectionHandler() as db:
        stmt = (
            exists()
            .where(Employee.user_id == self.id)
            .where(Employee.is_active == True)
            .select()
        )
        return db.session.scalar(stmt)
```



```html
{% if g.user.is_employee_active %}
<li>
    <a class="{% if  '/employeeinfo' in request.path %}is-active{% endif %}"
       href="{{ url_for('auth.employeeinfo') }}">
        직원정보
    </a>
</li>
{% endif %}
```

![image-20230112174817842](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230112174817842.png)





### 직원관리에서 User정보를 popover로 보여주기

- youtube: https://www.youtube.com/watch?v=l4NzFmDiRjw&list=PLHqnUR3OCFAmqY936a5bb7OJ7fuUjCjKB&index=23
- 메가튜토리얼 : https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xx-some-javascript-magic



1. employee.html에 jquery, popper.js , boostrap.js를 추가함

   - **jquery는 bs4홈피의 `slim버전 사용지 $ jquery문법 사용 불가`라서 `no slim일반 버전으로 수정`**
   - boostrap.js보다 **popper.js를 더 위에서 추가**
   - boostrap.js는 popper만 있으면 될까지 싶어서 뺐더니 hover안되서 **추가** 
   - **boostrap.css는 예쁜모양만 배껴올라고 일단 추가후, `dispose 주석처리상태로 뜬 상태에서 style복붙후 주석처리`**

   ```html
   {% block extra_head_style %}
   <!--css는 모양만 확인하고 주석처리 -->
   <!--<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css"-->
   <!--      integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">-->
   
   <style>
       .popover {
           position: absolute;
           top: 0;
           left: 0;
           z-index: 1060;
           display: block;
           max-width: 276px;
           font-style: normal;
           font-weight: 400;
           line-height: 1.5;
           text-align: left;
           text-align: start;
           text-decoration: none;
           text-shadow: none;
           text-transform: none;
           letter-spacing: normal;
           word-break: normal;
           word-spacing: normal;
           white-space: normal;
           line-break: auto;
           font-size: .875rem;
           word-wrap: break-word;
           background-color: #fff;
           background-clip: padding-box;
           border: 1px solid rgba(0, 0, 0, .2);
           border-radius: 0.3rem;
           /* 그림자나 화살표까진 복사안되서 그림자만 추가*/
           box-shadow:2px 2px 4px 0;
       }
   </style>
   ```

   

   ```html
   <!--용량을 줄이려고 boostrap4에 있는 slim 빌드 jQuery를 사용했었는데, slim 빌드를 사용하게되면, $.ajax()를 사용할 수 없다.-->
   <!-- jQuery first (not slim for $.ajax) -> then Popper.js,->  then Bootstrap JS -->
   <!--    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>-->
   <script src="https://code.jquery.com/jquery-3.2.1.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/popper.js@1.12.9/dist/umd/popper.min.js"
           integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q"
           crossorigin="anonymous"></script>
   <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js"
           integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl"
           crossorigin="anonymous"></script>>-->
   {% endblock extra_head_style %}
   ```

   

2. **hover를 적용할 table 칼럼에 `span.user_popup`  > `a태그`안에 text를 주자**

   ```html
   <td>
       <strong>
           <span class="user_popup">
               <a href="{{ url_for('admin.user_popup', name=employee.name) }}">
                   {{ employee.name }}
               </a>
           </span>
       </strong>
   </td>
   ```

3. **javascript로 `.user_popup`을 가진 span태그를 찾아 hover적용하되, `elem.first()`로는 a태그를  `.text()`로는 employee.name을 찾을 수 있게 한다**

   ```js
   {% block extra_foot_script %}
   <script>
       $(function() {
           $('.user_popup').hover(
               function(event) {
                   // mouse in event handler
                   var elem = $(event.currentTarget);
                   console.log(elem)
                   // hover된 span태그의 first() a태그의 name text()
                   console.log(elem.first().text().trim())
   
               },
               function(event) {
                   // mouse out event handler
                   var elem = $(event.currentTarget);
                   console.log(elem)
                   console.log(elem.first().text().trim())
               }
           )
       });
   </script>
   {% endblock extra_foot_script %}
   ```

   ![image-20230112221826921](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230112221826921.png)



4. **hover에 잡히는 employee.name을 가지고  user정보 + html을 뿌려줄 route 개설**

   ```python
   @admin_bp.route('employee/<name>/user_popup')
   @login_required
   def user_popup(name):
       employee = Employee.get_by_name(name)
       user = employee.user
   
       return render_template('admin/employee_user_popup.html', user=user)
   
   ```

   

5. `employee_user_popup.html`에 내용 채우기

   - 확인용

     ```html
     <!DOCTYPE html>
     <html lang="en">
     <head>
         <meta charset="UTF-8">
         <title>Title</title>
     </head>
     <body>
     {{user}}
     </body>
     </html>
     ```

   - avatar 및 기본 정보

     ```html
     <table class="table">
         <tr>
             <td width="64" style="border: 0px;">
                 <figure class="image is-48x48">
                     <img class="is-rounded" style="height: 100%;"
                          src="
                                 {% if user.avatar %}
                                  {{url_for('download_file', filename=user.avatar)}}
                                  {% else %}
                                  {{url_for('static', filename='/img/user/default_avatar.svg')}}
                                  {% endif %}
                                 "
                          alt="{{ user.username }}">
                 </figure>
             </td>
             <td style="border: 0px;">
                 <p>
                     {{ user.username }}
                 </p>
                 <small>
                     <p> 최근 접속일 : {{ user.last_seen | feed_datetime(is_feed=True) }}</p>
                     <p>직위: {{ user.role.name }}</p>
                     <p>email: {{ user.email }}</p>
                     <p>성별: {{ user.sex.name }}</p>
                     <p>주소: {{ user.address }}</p>
                     <p>휴대폰: {{ user.phone | join_phone }}</p>
                 </small>
             </td>
         </tr>
     </table>
     ```

   - 클릭 or 해당 route로 넘어갈 때

     - 포함되지 않는 그냥 html코드만 있어서, 스타일은 적용안된다

     ![image-20230112234547798](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230112234547798.png)
     ![image-20230112234556296](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230112234556296.png)

6. hover 이벤트에서 해당 route로 get요청을 보내, html통째로 받아오도록 수정하기

   - 일단 ~~1초~~ 0.5초이상 머무를 때 정보조회로 판단하고  요청을 보낸다

   ```js
   <script>
       $(function () {
           var timer = null;
   
           $('.user_popup').hover(
               function (event) {
                   // mouse in event handler
                   var elem = $(event.currentTarget);
                   // console.log(elem)
                   // hover된 span태그의 first() a태그의 name text()
                   // console.log(elem.first().text().trim())
   
                   // 갖다대자마자 요청보내는게 아니라 1초 머무를 경우, 정보조회로 판단하고 요청보내도록 1초 timer를 건다
                   timer = setTimeout(function () {
                       timer = null;
                       // popup logic goes here
                   }, 500);
   
               },
               function (event) {
                   // mouse out event handler
                   var elem = $(event.currentTarget);
                   if (timer) {
                       clearTimeout(timer);
                       timer = null;
                   }
               }
           )
       });
   </script>
   ```

7. 최종 요청

   - html을 받아오는 get요청으로서 route url로 요청을 보낸다.
   - 예제와 달리 jquery버전이 4.1 이상이면 'dispose'로 팝업을 제거한다

   ```js
   {% block extra_foot_script %}
   <script>
       $(function () {
           var timer = null;
   
           $('.user_popup').hover(
               function (event) {
                   // mouse in event handler
                   var elem = $(event.currentTarget);
                   // console.log(elem)
                   // hover된 span태그의 first() a태그의 name text()
                   // console.log(elem.first().text().trim())
   
                   // 갖다대자마자 요청보내는게 아니라 1초 머무를 경우, 정보조회로 판단하고 요청보내도록 1초 timer를 건다
                   timer = setTimeout(function () {
                       timer = null;
                       // popup logic goes here
                       //@admin_bp.route('employee/<name>/user_popup')
                       xhr = $.ajax(
                           '/admin/employee/' + elem.first().text().trim() + '/user_popup')
                           .done(
                               function (data) {
                                   xhr = null;
                                   // create and display popup here
                                   elem.popover({
                                       trigger: 'manual',
                                       html: true,
                                       animation: false,
                                       container: elem,
                                       content: data
                                   }).popover('show');
                                   // flask_moment_render_all();
                               });
                   }, 500);
   
               },
               function (event) {
                   // mouse out event handler
                   var elem = $(event.currentTarget);
                   if (timer) {
                       clearTimeout(timer);
                       timer = null;
                   } else if (xhr) {
                       xhr.abort();
                       xhr = null;
                   } else {
                       // destroy popup here
                       // elem.popover('destroy');
                       // $pop.popover('destroy'); // jQuery < 4.1
                       // $pop.popover('dispose'); // jQuery > 4.1
                       elem.popover('dispose');
                   }
   
               }
           )
       });
   </script>
   {% endblock extra_foot_script %}
   ```

   ![image-20230113005226962](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113005226962.png)

8. 이제 직원관리에서 Avatar/직위 칼럼을 제거하고, popup.html 을 꾸며보자

   ![image-20230113012633727](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113012633727.png)

   ```html
   <table class="table">
       <tr>
           <td width="64" style="border: 0px;">
               <figure class="image is-48x48">
                   <img class="is-rounded" style="height: 100%;"
                        src="
                               {% if user.avatar %}
                                {{url_for('download_file', filename=user.avatar)}}
                                {% else %}
                                {{url_for('static', filename='/img/user/default_avatar.svg')}}
                                {% endif %}
                               "
                        alt="{{ user.username }}">
               </figure>
           </td>
           <td style="border: 0px;">
               <p>
                   <span class="tag is-primary">{{ user.username }}</span>
               </p>
   
               <small>
                   <p>최근 접속일 : {{ user.last_seen | feed_datetime(is_feed=True) }}</p>
                   <div class="dropdown-divider"></div>
                   <p><span class="has-text-primary-dark has-text-weight-bold">직위</span>
   
                       <span class="
                           tag
                           {% if not user.is_staff %}
                           is-white
                           {% elif user.is_executive %}
                           is-danger
                           {% else %}
                           is-info
                           {% endif %}
                            is-light">
                               {{ user.role.name}}
                           </span>
   
                   </p>
                   <p><span class="has-text-primary-dark has-text-weight-bold">email</span> {{ user.email }}</p>
                   <p><span class="has-text-primary-dark has-text-weight-bold">성별</span> {{ user.sex.name }}</p>
                   <p><span class="has-text-primary-dark has-text-weight-bold">주소</span> {{ user.address }}</p>
                   <p><span class="has-text-primary-dark has-text-weight-bold">휴대폰</span> {{ user.phone | join_phone }}</p>
               </small>
           </td>
   
       </tr>
   </table>
   ```

   

9. **name이 겹칠 경우, 첫번째 이름의 사람만 hover를 띄우게 되는 버그**

   - **name 대신 사번( --------employee_id)에 user_popup을 걸어서 substring으로 요청하도록 변경하기**

   ```html
   <td>
       <span class="user_popup">
           <a class="has-text-dark" href="{{ url_for('admin.user_popup', employee_id=employee.id) }}">
               {{ employee.employee_number }}
           </a>
       </span>
   </td>
   ```

   ```js
   xhr = $.ajax(
       '/admin/employee/' + elem.first().text().trim().substring(6,8) + '/user_popup')
       .done(
   ```

   ```python
   @admin_bp.route('employee/<int:employee_id>/user_popup')
   @login_required
   def user_popup(employee_id):
       employee = Employee.get_by_id(employee_id)
       user = employee.user
   
       return render_template('admin/employee_user_popup.html', user=user)
   
   ```

10. 사번에 employee -> user role을 확인하는 메서드로 색깔로 계급 표시하기

    - employee에 바로 role을 조회가능하도록 작성해놓았음

      ```python
          #### with other entity
          @hybrid_property
          def role(self):
              with DBConnectionHandler() as db:
                  stmt = (
                      select(Role)
                      .where(Role.users.any(User.id == self.user_id))
                  )
                  role = db.session.scalars(stmt).first()
                  return role
      
      	#### with other entity
          @hybrid_property
          def is_staff(self):
              return self.role.is_(Roles.STAFF)
      
          #### with other entity
          @hybrid_property
          def is_executive(self):
              return self.role.is_(Roles.EXECUTIVE)
      ```

    - 추가

      ```python
          #### with other entity
          @hybrid_property
          def is_chiefstaff(self):
              return self.role.is_(Roles.CHIEFSTAFF)
      
          #### with other entity
          @hybrid_property
          def is_administrator(self):
              return self.role.is_(Roles.ADMINISTRATOR)
      
      ```

      

    - chiefstaff / administor까지 추가

      - staff/chiefstaff => 파란색/찐한파란색

      - executive/administrator => 빨간색/찐한빨간색

        ![image-20230113015707991](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113015707991.png)



### 직원관리 부서 여러개인 경우, 1개만 보이고 그외는 b-tooltip으로 보이도록 변경

![image-20230113022547853](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113022547853.png)



1. 부서list를 다 for문 돌지말고 

   1. 부서list의 길이를 set 변수로 잡아놓고
   2. 부서가 1개이상일 때, 부서를 표기하며, **첫번째만 뽑아서 칼럼에 값으로 출력**
   3. **부서가 2개이상일 때, 외 n-1개로 표시 후**
   4. b-tooltip내에서 돌린다
      - 기본 b-toolip코드에서 **type=""이 말풍선 색이며**
      - position을 정해준다
      - template v-slot:content 내에서 for문을 돌리며
      - **내장 b-button을 무시하고, 외 n개 부서의 span태그를 달면 된다.**

   ```html
   <td>
       <span class="is-size-7">
           <!--                    <div class="tags">-->
           {% set dept_count = (employee.get_dept_and_position_list() | length) %}
           {% if dept_count > 0  %}
           <span class="tag is-primary is-light">
               {{employee.get_dept_and_position_list()[0][0]}} ({{employee.get_dept_and_position_list()[0][1]}})
           </span>
           {% if dept_count > 1 %}
           <b-tooltip
                      position="is-right"
                      type="is-primary">
               <template v-slot:content>
                   {% for dept_and_pos in employee.get_dept_and_position_list() %}
                   <span class="has-text-white">
                       {{dept_and_pos[0]}} ({{dept_and_pos[1]}})
                   </span></br>
               {% endfor %}
               </template>
   
           <!--                            <b-button label="Action" type="is-light" class="button is-inverted"/>-->
           <span class="has-text-primary">외 {{dept_count - 1}}개 부서</span>
           </b-tooltip>
       {% endif %}
       {% else %}
       -
       {% endif %}
   </span>
   </td>
   ```

   





### 퇴사시 Employee정보(재직상태변경/퇴직일/Role)  퇴직처리 비활성화 뿐만 아니라, EmpDept정보(해임일 추가로 비활성화) 해임처리도 해야한다.

![image-20230113161439036](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113161439036.png)

- 현재 퇴사처리

  - Employee의 `job_status`변경

  ```python
  #### 퇴사처리1) 직원의 재직상태를 퇴사로 변경
  employee.job_status = job_status
  if job_status == JobStatusType.퇴사:
      #### 퇴사처리2) 직원의 퇴직일(resign_date)가 찍히게 된다.
      employee.resign_date = date.today()
  
      #### 퇴사처리3) 직원의 Role을 STAFF이상 => User(deafult=True)로 변경한다.
      # 퇴사처리시 role을 user로 다시 바꿔, 직원정보는 남아있되, role이 user라서 접근은 못하게 한다
      role = db.session.scalars(
          select(Role)
          .where(Role.default == True)
      ).first()
      employee.user.role = role
  
  ```



#### employee 퇴사처리 메서드 => 외부에서 재직상태를 주니까, 재직상태변경 메서드로 구현

##### 01 Employee.change_status(emp_id, job_status)

```python
    ### with other entity
    @classmethod
    def change_job_status(cls, emp_id: int, job_status: int):
        #### 퇴사상태로 변경하는 경우 -> job_stauts 변경외
        # -> resign_date 할당 + (other entity)role을 default인 USER로 변경이다.
        # => 관계entity의 속성을 변경해야하므로, sql으로 하지 않고, 객체를 찾아서 변경하도록 변경한다.
        if job_status == JobStatusType.퇴사:
            with DBConnectionHandler() as db:
                emp: Employee = cls.get_by_id(emp_id)

                emp.job_status = job_status
                emp.resign_date = datetime.date.today()
                emp.user.role = Role.get_by_name('USER') # emp.role은 User의 role을 가져오는 식이므로 변경에 못쓴다.

                db.session.add(emp)
                db.session.commit()
```



##### 02 bug fix:  퇴사상태에서 다시 퇴사처리시 => Can't attach instance <Role>; another instance with key is already present in this session.

- `emp.user.role = Role.get_by_name('USER')`

  - **이미 `emp.user.role`의 관계객체에 USER Role객체를 가져**왔는데, **또 Role.get_by_name('USER')로 찾아버리니까** 이미 session에 존재하는 것을 가져왔다고 에러 뜬다
  - **이미 소지하고 있는 관계필드 -> 똑같은 객체를 조회해서 가져오면 안되므로 `이미 퇴사 처리된 상태인지 확인한 뒤 update시키도록 처리문`을 만들어야한다**

  ```python
      with DBConnectionHandler() as db:
          employee = db.session.get(Employee, employee_id)
  
          if not employee.role.is_under(g.user.role):
              flash('자신보다 하위 직위의 직원만 수정할 수 있습니다.', category='is-danger')
              return redirect(redirect_url())
  
          #### 이미 해당 재직상태인데 같은 것으로 변경하는 것을 막기 위한 처리문
          # => 이것을 처리해줘야 emp.user.role  <-> Role.get_by_name('USER')시 session내 같은 객체 조회를 막을 수 있다
          if employee.job_status == job_status:
              flash(f'같은 상태로 변경할 수 없습니다. ', category='is-danger')
              return redirect(redirect_url())
  
      Employee.change_job_status(employee_id, job_status)
  ```

  

##### 03 EmpDept정보 변경로직도 추가하기 => 내가 속한 모든 부서취임 정보list를 가져와서 -> 모드 해임일을 입력하여 비활성화 시킨다.



- 퇴사시 Employee정보이외에 `EmployeeDepartment`정보도 변경해줘야한다.

  - **`dismissal_date추가로 비활성화`를 알려야한다**
  - 이것만 추가되면 지난 데이터가 된다.

- 직원id를 가지고 해당직원의 모든 취임정보 가져오기

  ```python
  class EmployeeDepartment(BaseModel):
      #...
  	# with other entity
      @classmethod
      def get_by_emp_id(cls, emp_id):
          with DBConnectionHandler() as db:
              stmt = (
                  select(cls)
                  .where(cls.dismissal_date.is_(None))
                  .where(cls.employee_id == emp_id)
              )
              return db.session.scalars(stmt).all()
  ```

- **취임정보에 모두 dismissal_date 할당하여 비활성화 시키기**

  ```python
  
      @classmethod
      def change_job_status(cls, emp_id: int, job_status: int):
   		#...
          if job_status == JobStatusType.퇴사:
              with DBConnectionHandler() as db:
                  #...
  
                  #### 해당부서에 해임까지 시키기 => 내가 속한 모든 부서취임 정보list를 가져와서
                  # -> 모드 해임일을 입력하여 비활성화 시킨다.
                  emp_dept_list: list = EmployeeDepartment.get_by_emp_id(emp.id)
                  for emp_dept in emp_dept_list:
                      emp_dept.dismissal_date = datetime.date.today()
  
                  db.session.add_all(emp_dept_list)
  
                  db.session.commit()
  
  ```

- test

  ![image-20230113175550108](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113175550108.png)

  ![image-20230113175656311](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113175656311.png)





####  연차 계산시, if 퇴사일이 있다면, today대신 퇴사일까지 계산해야한다

```python
    # 근무개월 수 (다음달 해당일시 차이가 1달로 +1)
    @property
    def months_and_days_from_join_date(self):
        #### 이 사람이 퇴사했다면, 퇴사일을 기준으로 근무개월수를 세어야한다
        if self.resign_date:
            today_date = self.resign_date
        else:
            today_date = datetime.date.today()
        #...
```



![image-20230113182101786](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113182101786.png)

![image-20230113182203292](https://raw.githubusercontent.com/is3js/screenshots/main/image-20230113182203292.png)

- 재입사의 경우 **기존 prev_employee정보를 삭제하고 resign_date가 없는  새 데이터로 덮어쓰기 때문에, 근무일수 계산에서 고려하지 않아도 된다.**





### 퇴사자는 상태변경(재직, 휴직)등이 안되고 무조건 [User관리의 직원초대]로부터 가능하게 하자

```python
@admin_bp.route('/employee/job_status', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_job_status_change():
    employee_id = request.form.get('employee_id', type=int)
    job_status = request.form.get('job_status', type=int)

    with DBConnectionHandler() as db:
        employee = db.session.get(Employee, employee_id)

        if not employee.role.is_under(g.user.role):
            flash('자신보다 하위 직위의 직원만 수정할 수 있습니다.', category='is-danger')
            return redirect(redirect_url())
        
        #### 퇴사자는 재직상태 변경 못하고, 직원초대로만 가능하도록 early return
        if employee.job_status == JobStatusType.퇴사:
            flash(f'퇴사자는 재직상태변경이 불가하며 User관리에서 직원초대로 새로 입사해야합니다. ', category='is-danger')
            return redirect(redirect_url())
```

