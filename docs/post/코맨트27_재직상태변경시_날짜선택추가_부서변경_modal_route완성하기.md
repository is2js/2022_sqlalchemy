



### 재직상태변경시 날짜를 선택하도록 modal에 추가

#### 재직상태변경시 날짜를 선택해야한다. modal UI가 깨지므로 inline props를 달아서 만든다.



![image-20230113212813986](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230113212813986.png)



- 오픈형식으로하면, modal에서 스크롤이 생기므로 `inline`옵션을추가한다

  ![image-20230117021729380](C:\Users\is2js\AppData\Roaming\Typora\typora-user-images\image-20230117021729380.png)

  ![image-20230117021923078](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230117021923078.png)



```html
<!-- INPUT3:  -->
<b-field label="날짜">
    <b-datepicker
                  inline
                  icon="calendar-today"
                  v-model="date"
                  >
    </b-datepicker>
</b-field>
<!-- date로 작성하면 => base에서 stringDate로 watch로 보고있다 -->
<input type="hidden" name="date" v-model="stringDate">
```

```js
{% block vue_script %}
<script>
    app._data.date = new Date()
</script>
{% endblock vue_script %}
```



- **buefy의 b-select(재직상태)와 달리 `b-datepicker`는 input태그를 내포하지 않고 있다.**
  - **그래서 hidden으로 name을 주고 만든다.**
- **v-model에 선택된 값은 string의 긴 값(`Thu Jan 19 2023 00:00:00 GMT+0900 (한국 표준시) <class 'str'>)`으로서 **
  1. base.html에서 **`watch`를 통해 `javascrip convert메서드`로 변환시킨 `stringDate`를 input태그에 `v-model`로 투입되게 해야한다**





#### route에선 buefy date(긴 문자) -> watch + js -> stirngDate로 변환한 String Y-m-d를 type에서 lambda함수를 통해 바로 변환한다

- 변환시 datime.date에는 strptime이 없기 때문에, datetime.datetime.strptime으로 변환 후 .date()를 붙여서 date형식으로 바꾼다.
  - form에서는 form필드 자동변환

```python
@admin_bp.route('/employee/job_status', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_job_status_change():
    employee_id = request.form.get('employee_id', type=int)
    job_status = request.form.get('job_status', type=int)
    target_date = request.form.get('date',
                                   type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
                                   )

```

#### target_date가 넘어오면, 복직은 휴직일이후, 퇴사는 입사일 이후만 가능하도록 조건을 추가한다

```python
    with DBConnectionHandler() as db:
        employee = db.session.get(Employee, employee_id)

        if not employee.role.is_under(g.user.role):
            flash('자신보다 하위 직위의 직원만 수정할 수 있습니다.', category='is-danger')
            return redirect(redirect_url())

        if employee.job_status == JobStatusType.퇴사:
            flash(f'퇴사자는 재직상태변경이 불가하며 User관리에서 직원초대로 새로 입사해야합니다. ', category='is-danger')
            return redirect(redirect_url())

        #### new => 퇴직은 입사일보다 더 이전에는 할 수 없도록 검사하기
        if job_status == JobStatusType.퇴사 and target_date < employee.join_date:
            flash(f'입사일보다 더 이전으로 퇴사할 수 없습니다. ', category='is-danger')
            return redirect(redirect_url())

        if job_status == JobStatusType.재직 and employee.job_status != JobStatusType.휴직:
            flash(f'복직은 휴직자만 선택할 수 있습니다. ', category='is-danger')
            return redirect(redirect_url())

        #### new => 복직은 최종 휴직일(in emp)보다 더 이전에는 할 수 없도록 검사하기
        if job_status == JobStatusType.재직 and target_date < employee.leave_date:
            flash(f'휴직일보다 더 이전으로 복직할 수 없습니다. ', category='is-danger')
            return redirect(redirect_url())

        if employee.job_status == job_status:
            flash(f'같은 상태로 변경할 수 없습니다. ', category='is-danger')
            return redirect(redirect_url())
```

####  Employee.change_job_status(employee_id, job_status, target_date) 로서 내부 today쓰던 것을 target_date로 변환한다

```python
@classmethod
def change_job_status(cls, emp_id: int, job_status: int, target_date):

    if job_status == JobStatusType.퇴사:
        with DBConnectionHandler() as db:
            emp: Employee = cls.get_by_id(emp_id)

                emp.job_status = job_status
                # emp.resign_date = datetime.date.today()
                emp.resign_date = target_date

```





### 부서변경 처리 modal 및 중간 axios 로직 완성하기

#### 관련 메서드들 구현 in users.py

```python

    #### with other entity
    def get_my_departments(self, as_leader=False, as_employee=False, as_min_level=False, except_dept_id=None):
        with DBConnectionHandler() as db:

            subq_stmt = (
                select(EmployeeDepartment.department_id)
                .where(EmployeeDepartment.dismissal_date.is_(None))
                .where(EmployeeDepartment.employee.has(Employee.id == self.id))
            )
            
			#### 부서 변경시, 현재부서를 제외한 부서들을 조회하기 위한 keyword 및 stmt 추가 
            if except_dept_id:
                subq_stmt = subq_stmt.where(EmployeeDepartment.department_id != except_dept_id)
                
			#...

            #### ValueError: None is not a valid DepartmentType
            #### 아예 부서정보가 조회안됬는데 as_min_level=True로 집계한다면 오류가 난다.
            # 일단 try except로 잡아보자.
            try:
                return db.session.scalars(
                    stmt
                    .order_by(Department.path)
                ).all()
            except ValueError:
                return []
```

```python
 #### with other entity
    def change_department_with_promote_or_demote(self, after_dept_id, target_date,
                                                 before_dept_id=False,
                                                 as_leader=False,
                                                 ):
        #### after_dept_id는 해당부서가 반드시 존재해야하므로, 존재 검사를 한다
        if not Department.get_by_id(after_dept_id):
            return False, "해당 부서는 사용할 수 없는 부서입니다."

        with DBConnectionHandler() as db:
            #### 부서처리 전에, 승진/강등 여부에 따라, role변경해주기
            # -> 관계객체에 접근시 이미 해당데이터가 있기 때문에, 할당시에는 같은 객체를 불러오면 안된다.
            # -> 외부에서 is_demote가 되려면 STAFF가 아닐 때부터 처리해야한다.
            if self.is_demote(as_leader=as_leader, current_dept_id=before_dept_id):
                self.user.role = Role.get_by_name('STAFF')
                db.session.add(self)
                print("강등입니다.")
            if self.is_promote(as_leader=as_leader):
                self.user.role = Role.get_by_name('CHIEFSTAFF')
                db.session.add(self)
                print("승진입니다.")

            #### 이전 부서가 있는 경우, 이전부서에 해임처리
            # => 위에서 self를 add라느라 썼다면, 쓰지말고 id(value)만 넘겨서 처리되도록 하자.
            if before_dept_id:
                before_emp_dept: EmployeeDepartment = EmployeeDepartment.get_by_emp_and_dept_id(self.id, before_dept_id)
                before_emp_dept.dismissal_date = target_date

                db.session.add(before_emp_dept)


            after_emp_dept: EmployeeDepartment = EmployeeDepartment(employee_id=self.id,
                                                                    department_id=after_dept_id,
                                                                    is_leader=as_leader,
                                                                    employment_date=target_date)
            result, message_after_save = after_emp_dept.save()

            if result:
                # 만약 after성공했다면, 취임정보.save()의 메세지 대신, 부서변경 메세지로 반환
                db.session.commit()
                return True, f"부서 변경을 성공하였습니다."
            else:
                # 만약 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환
                db.session.rollback()
                return False, message_after_save


    #### with other entity
    def is_promote(self, as_leader=False):
        #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & as_leader =True(최초 팀장으로 가면) => 승진
        #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
        depts_as_leader = self.get_my_departments(as_leader=True)
        return as_leader and len(depts_as_leader) == 0

    #### with other entity
    def is_demote(self, as_leader=True, current_dept_id=None):
        #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & as_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
        #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
        other_depts_as_leader = self.get_my_departments(as_leader=True, except_dept_id=current_dept_id)
        return not as_leader and len(other_depts_as_leader) == 0

```







#### (front) 직원관리에 부서변경 버튼 추가

- employee.html 재직상태 변경 버튼을 보고 참고해서 작성한다

  ```html
  <a href="javascript:;"
     @click="isDepartmentModalActive = true; employee_id = {{employee.id}};"
     class="tag is-primary is-light"
     >
      <span class="icon">
          <i class="mdi mdi-google-assistant"></i>
      </span>
      부서
  </a>
  ```

- `@click`에 사용한 변수들을 base.html에 추가한다

  ```js
              //employee.html modal 띄우는 변수
              isJobStatusModalActive: false,
              isDepartmentModalActive: false,
              employee_id: null,
              //employee.html modal 속 제출 처리 변수
              isLoading: null,
  ```

  

#### (front) 부서변경 모달 완성하기

#### modal



![image-20230119171824657](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119171824657.png)

- b-modal의 `v-model`에 isModalActive(true/false)를 넣어주고
- delete X버튼, 닫기 버튼에는 사용변수 `isModalActive` , `employee_id`, `isSwitchedCustom`변수를 처음상태로 초기화한다
- form내부에서는
  - 보낼 변수 `employee_id`를 `hidden input + :value`로 넣어준다
  - **부서변경시, 2개의 b-select를 넣어줄 것인데**
    - 1개 field에 다 집어넣고 horizontal로 넣어주면 b-field의 label때문에 못생기게 된다
    - **그래서 `columns`로 5(b-select) 2(화살표) 5(b-select)를 짠 뒤**
      - 각각의 b-select의 1개의 b-field를 넣어주고, `label-position`옵션으로 b-select에 붙게 한다
      - 화살표는 icon으로 넣되, `column is-2`에 **`is-flex + is-align-items-center`**를 넣어 icon이 세로 정렬되게 한다.
        - icon의 크기는 span에 text크기인 `is-size-크기` 와  `has-text-색상`으로 준다
      - 각각의 b-select에는 `name`을 넣어줘야한다
  - 팀장여부는 b-field안에 b-switch로 줬는데
    - **b-field의 label 크기는 `custom-class="is-크기"`로 조절할 수 있다.**
    - **b-switch 등 `buefy input의 크기`는 `size="is-크기"`로 조절할 수 있다.**
  - 부서변경일 날짜는 b-field안에 b-datepicker로 작성하는데
    - 기본적으로 v-model 변수로 `date` in b-datepicker와 + watch에서 보고 자동변환하는 `stringDate`변수를 hideen input을 name="date"로 아래 추가 생성해서 string date를 받는다.
    - modal은 datepicker가 펼쳐지게 하면 이상해지니 b-input인`b-datepicker에 inline`옵션을 준다

```html
<!-- 부서 변경 모달 -->
<b-modal
        v-model="isDepartmentModalActive"
        has-modal-card
        trap-focus
        aria-role="dialog"
        aria-label="Department Select Modal"
        aria-modal>
    <!--    <form action="{{url_for('admin.employee_job_status_change') }}"-->
    <form action=""
          method="post"
          @submit.prevent="submitForm"
    >
        <div class="modal-card is-" style="width: auto">
            <header class="modal-card-head">
                <p class="modal-card-title is-size-5">
                    부서 변경
                </p>
                <button
                        type="button"
                        class="delete"
                        @click="isDepartmentModalActive = false; employee_id = null; isSwitchedCustom='부서원';"/>
            </header>
            <section class="modal-card-body">
                <!-- INPUT1: HIDEEN 모달클릭시 v-bind변수에 담아놨던 변수로, form에 포함될 변수로서 id를 반영 -->
                <input type="hidden" name="employee_id" :value="employee_id">


                <!-- 현재부서 => 변경부서 선택-->
                <!-- INPUT2: 2개의 select를 1개 field에 horizontal로 주면 label이 깨지므로, columns에서 각각을 나누어, 개별 field+select를 각각 준다.-->
                <div class="columns">
                    <div class="column is-5">
                        <b-field
                                label="현재 부서"
                                label-position="on-border"
                        >
                            <b-select
                                    size="is-small"
                                    name="job_status"
                                    placeholder="현재 부서 선택"
                                    rounded
                            >
                                {% for job_status in job_status_list %}
                                <option value="{{job_status[0]}}">{{job_status[1]}}</option>
                                {% endfor %}
                            </b-select>
                        </b-field>
                    </div>
                    <!-- 컬럼의 내용물을 세로정렬(세로 정렬) 하려면, flex + align-items 를 둘다 column 클래스에 추가 -->
                    <div class="column is-2 is-align-items-center is-flex">
                                <span class="icon is-size-3 has-text-primary ">
                                    <i class="mdi mdi-arrow-right-bold"></i>
                                </span>
                    </div>

                    <div class="column">
                        <b-field
                                label="변경 부서"
                                label-position="on-border"
                        >
                            <b-select
                                    size="is-small"
                                    name="job_status"
                                    placeholder="좌측 먼저 선택"
                                    rounded
                            >
                                {% for job_status in job_status_list %}
                                <option value="{{job_status[0]}}">{{job_status[1]}}</option>
                                {% endfor %}
                            </b-select>
                        </b-field>
                    </div>
                </div>


                <!-- INPUT3: 팀장여부 -->
                <!-- switch에 따로 name을 지정해줘야한다. -->
                <div class="columns">
                    <div class="column is-7">
                    </div>
                    <!-- 가로정렬(가로 정렬)은 flex+is-align이 아니라 has-text-centered (is-center(ed)는 안먹더라)-->
                    <div class="column has-text-centered">
                        <b-field
                                custom-class="is-small"
                                label=""
                                label-position="on-border"
                        >
                            <b-switch
                                    size="is-small"
                                    v-model="isSwitchedCustom"
                                    true-value="부서장"
                                    false-value="부서원"
                                    name="as_leader"
                            >
                                {$ isSwitchedCustom $}
                            </b-switch>
                        </b-field>
                    </div>
                </div>
                <!-- INPUT4:  -->
                <b-field label="부서변경일"
                         custom-class="is-default"
                >
                    <b-datepicker
                            inline
                            icon="calendar-today"
                            v-model="date"
                    >
                    </b-datepicker>
                </b-field>
                <!-- date로 작성하면 => base에서 stringDate로 watch로 보고있다 -->
                <input type="hidden" name="date" v-model="stringDate">


            </section>
            <footer class="modal-card-foot">
                <!-- b-button들을 넣으면 1개 이후 사라지는 버그 => a태그 + input(submit) 조합으로 변경-->
                <a class="button is-primary is-light mr-2"
                   @click="isDepartmentModalActive = false; employee_id = null; isSwitchedCustom='부서원';"
                >
                    닫기
                </a>
                <input type="submit"
                       class="button is-primary"
                       value="완료"
                       :disabled="isLoading"
                >
            </footer>
        </div>

    </form>
</b-modal>
```







#### 부서변경 버튼에 isModalActive = true;로 modal을 바로 띄우지말고 메서드로 감싸서, [현재부서]가 오면 띄우도록 처리하기

- 참고: https://stackoverflow.com/questions/64797990/how-data-toggle-target-wait-for-axios-success-fail-in-vue

  

- 기본적으로 **modal클릭 => method작동 => axios.post가 성공하면 isModalActive=true;로 띄워지게 하는 방식을 사용할 것이다.**



1. base.html에서 axios를 쓰더라도, 호출되는 html(employee.html)에 cdn 추가하기

   ```html
   <!-- 부서변경시 부서정보 받아오기 위한 axios -->
   <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
   ```

   

2. 부서변경 버튼에 메서드로 치환하기

   - 메서드에 인자가 없다면 ()없이 `메서드명`
   - 메서드에 인자가 있다면 `메서드명(인자)` -> jinja로 현재line속 `{{employee.id}}`를 바로 넘기면 된다.
   - 클릭된 요소까지 같이 쓰려면 `메서드명($event, 인자)`
     - articleform에서는 $event에서 적힌 id를 뽑아와서 사용했었음.

   ```html
   <a href="javascript:;"
      @click="getCurrentDepartments({{employee.id}})"
      class="tag is-primary is-light"
      >
       <span class="icon">
           <i class="mdi mdi-google-assistant"></i>
       </span>
       부서
   </a>
   ```

3. base.html에 메서드 정의하기

   - **url의 jinja로 route를 뽑아올건데, url_for가 완성되어야하며, 중간에 + js변수 + 를 못넣는다.**
     - 인자를 비워두고 url_for를 완성시키되 **보통 <int:employee_id>지만, 빈 문자열로 넣고 js문자열emp_id를 더해주기위해서 route에서 int를 못쓴다( employee=None)으로 줘도 인식안됨.**

   ```js
   //employee.html 부서변경 버튼 클릭시 정보를 받고 modal을 띄우기
   getCurrentDepartments(emp_id) {
       console.log(emp_id)
       axios({
           url: '{{ url_for("admin.get_current_departments", employee_id="")}}' + emp_id,
           method: 'get',
           // dataType: 'html',
           // headers: {'content-type': 'application/json;charset=utf-8'},
       }).then(res => {
           alert("성공")
           console.log('res.data >> ', res.data);
           // alert(res.data)
           // tab_item.innerHTML = res.data
       }).catch(err => {
           alert("실패")
           console.log(err)
           // tab_item.innerHTML = ('페이지를 찾을 수 없습니다.');
       });
   
   },
   ```

4. route에서 employee_id를 문자열로 들어오게 하고 작성한다

   ```python
   @admin_bp.route('/departments/<employee_id>', methods=['GET', 'POST'])
   @login_required
   def get_current_departments(employee_id):
   
       return "응답"
   ```

   ![image-20230119181344773](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119181344773.png)







#### route와 연결완성후, route에서 현재부서 정보 내려보내기



![image-20230119182434188](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119182434188.png)

![image-20230119182457855](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119182457855.png)

- As of Flask `1.1.0`부터는 dict든 jsonfy(dict)든 2개다 return가능하다.

- 상태코드가 같이 보내고 싶다면, `make_response( dict or jsonify , 상태코드)`로 보내면 된다.

  ![image-20230119183458435](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119183458435.png)

  ![image-20230119183527211](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119183527211.png)

- make_repsponse(, 200)을 스고, code를 지운 뒤, view에서는 **res.status == 200**으로 확인하자

- id, 부서명 list로 건네줘도 => [ id, name]의 array로 간다

  ![image-20230119184258866](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119184258866.png)

  - 각각을 dict로 만들어서 id, name으로 출력가능하게 보내자

    ![image-20230119185702036](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119185702036.png)



1. route에서 각 부서정보를 string으로 접근할 수 있게 dict list로 반환한다.

   ```python
   @admin_bp.route('/departments/<employee_id>', methods=['GET'])
   @login_required
   def get_current_departments(employee_id):
       emp: Employee = Employee.get_by_id(int(employee_id))
       current_depts = emp.get_my_departments()
       current_dept_infos = [{'id': x.id, 'name': x.name} for x in current_depts]
   
       return make_response(
           dict(deptInfos=current_dept_infos),
           200
       )
   ```

2. base.html에서 현재부서를 받을 변수를 선언한다

   ```js
   var app = new Vue({
       el: '#app',
       delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
       components: {},
       data: {
           
           //..
           
           //employee.html modal 띄우는 변수
           isJobStatusModalActive: false,
           isDepartmentModalActive: false,
           employee_id: null,
           //employee.html modal 속 제출 처리 변수
           isLoading: null,
           //employee.html modal 속 스위치의 Y/N시 들어갈 값을 받아주는 변수 (각 html파일에서 초기화하고, swtich내에서 true-value, false-value를 정의함
           isSwitchedCustom: null, //app._data.isSwitchedCustom = '팀원';
           //employee.html modal 속 현재부서 option list(axios로 받아짐)
           currentDeptList: null,
       },
   ```

3. 모달클릭 메서드에서 `res.data`에 있는 `.deptInfos`(dict반환 keyword명)을 `this.currentDeptList` 변수에 넣어준다.

   - 부서정보를 넣으면서 **modal을 띄우고, modal속 변수를 초기화한다.**

   ```js
   //employee.html 부서변경 버튼 클릭시 정보를 받고 modal을 띄우기
   getCurrentDepartments(emp_id) {
       console.log(emp_id)
       axios({
           url: '{{ url_for("admin.get_current_departments", employee_id="")}}' + emp_id,
           method: 'get',
           // dataType: 'html',
           // headers: {'content-type': 'application/json;charset=utf-8'},
       }).then(res => {
           // alert("성공")
           console.log('res.status >> ', res.status);
           console.log('res.data >> ', res.data);
   
           this.currentDeptList = res.data.deptInfos;
           console.log('this.currentDeptList >> ', this.currentDeptList);
   
           this.isDepartmentModalActive = true;
           this.employee_id = emp_id;
           this.isSwitchedCustom = '부서원';
   
       }).catch(err => {
           alert("서버 연결이 올바르지 않습니다.")
           console.log(err)
       });
   
   },
   ```

4. employee.html의 **modal의 현재부서 b-select에서**

   1. `placeholder`를 bind시켜 vue변수 및 vue문법을 쓸 수 있게 만든 뒤

      - **현재부서정보가 존재하고(null아님 받아왔음) 부서정보가 1개 이상 있을 때만 `?현재부서 선택` 없거나 부서정보list가 0개일 때 `:현재부서 없음`을 삼항연산자로 만들어준다.**

        ```js
        :placeholder="currentDeptList && currentDeptList.length ? '현재부서 선택' : '현재부서 없음'"
        ```

   2. `option`태그 정보를 `v-for`로 현재부서정보로 돌리면서 :value에 .id를  text에 .name을 넣어준다.

      ```html
      <b-field
               label="현재 부서"
               label-position="on-border"
               >
          <!-- placeholder="현재 부서 선택"-->
          <b-select
                    size="is-small"
                    name="current_dept_id"
                    :placeholder="currentDeptList && currentDeptList.length ? '현재부서 선택' : '현재부서 없음'"
                    rounded
                    >
              <option v-for="dept in currentDeptList" :value="dept.id"> {$ dept.name $}</option>
          </b-select>
      </b-field>
      ```

      ![image-20230119193623061](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119193623061.png)

      ![image-20230119193638201](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119193638201.png)







#### 한쪽의 b-select => 다른 쪽 b-select 채우기

- 현재 **b-select에서 선택된 value**를 가져오게 하려면

  1. `v-model`="변수"추가 후 `data 변수 선언`
  2. 해당v-model 변수의 변화를 감지하여 넘길 수 있게 하는 `@change="on변수Change"` 추가 후 `method `선언을 해준다

  ```html
  <b-select
            size="is-small"
            name="current_dept_id"
            :placeholder="currentDeptList && currentDeptList.length ? '현재부서 선택' : '현재부서 없음'"
            rounded
            v-model="currentDeptId"
            @change="onCurrentDeptIdChange"
            >
  ```

  ```js
  //employee.html 부서modal 속 선택된 현재부서 id
  CurrentDeptId: null,
  ```

  ```js
  onCurrentDeptIdChange() {
      console.log(this.CurrentDeptId)
  },
  ```

  

- **`일반태그`에서는 @click, @change가 먹히지만, `b-field내 b-input들`은 @input으로 입력된 v-model을 받는다.**

  ```html
  <!-- @change="onCurrentDeptIdChange"-->
  <!-- 일반태그에서는 @click, @change가 먹히지만, b-field내 b-input들은 @input으로 입력된 v-model을 받는다.-->
  <b-select
            size="is-small"
            name="current_dept_id"
            :placeholder="currentDeptList && currentDeptList.length ? '현재부서 선택' : '현재부서 없음'"
            rounded
            v-model="currentDeptId"
            @input="onCurrentDeptIdChange"
            >
  ```

  ![image-20230119200909100](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119200909100.png)

  - 데이터는 잘뽑아오지만, **element에서 해당 메서드를 확인할 순 없다**

  ![image-20230119201008956](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119201008956.png)





- 이제 `onCurrentDeptIdChange`에서 after dept 후보들 정보를 가져와야한다.

  - main.py에서 테스트할 땐, tuple list로 가져왔으나, dict list를 반환하도록 변경한다
  - 인스턴스 메서드라서 객체를 찾아서 가져오자.

  ```python
  def get_selectable_departments(self):
      departments = Department.get_all()
      selectable_parent_departments = [{'id': x.id, 'name': x.name} for x in departments if
                                       x.id not in self.get_self_and_children_id_list()]
      return selectable_parent_departments
  ```

  ```python
  @admin_bp.route('/departments/selectable/<department_id>', methods=['GET'])
  @login_required
  def get_selectable_departments(department_id):
  
      current_dept : Department = Department.get_by_id(int(department_id))
      selectable_depts_infos = current_dept.get_selectable_departments()
  
      return make_response(
          dict(deptInfos=selectable_depts_infos),
          200
      )
  ```

  



- 이제 onCurrentDeptIdChange에서 axios요청을 통해 route에서 내려준 데이터를 받아본다.

  - res.data.deptInfos를 받아줄 v-model변수를 선언

    ```js
    selectableDeptList: null,
    ```

  - onCurrentDeptIdChange에서 axios호출하여 `this.selectableDeptList`에 넣어준다.

    ```js
    //employee.html 부서변경 modal에서 첫번재 부서 선택시
    onCurrentDeptIdChange() {
        console.log(this.currentDeptId)
    
        axios({
            url: '{{ url_for("admin.get_selectable_departments", department_id="")}}' + this.currentDeptId,
            method: 'get',
            // dataType: 'html',
            // headers: {'content-type': 'application/json;charset=utf-8'},
        }).then(res => {
            // alert("성공")
            console.log('res.status >> ', res.status);
            console.log('res.data >> ', res.data);
    
            this.selectableDeptList = res.data.deptInfos;
            console.log('this.selectableDeptList >> ', this.selectableDeptList);
    
        }).catch(err => {
            alert("서버 연결이 올바르지 않습니다.")
            console.log(err)
        });
    
    },
    ```

    

  ![image-20230119202307464](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119202307464.png)

- 받은 선택가능 부서정보들을 b-select에 넣어준다.

  - `name`속성만 추가한다. 
    - 여기선 @input으로 선택된 값 변화 감지 => v-model에 넣고 선택된 값을 사용하지 않는다.
    - **select태그는 사용자가 선택되면 그게 `value로 자동으로 가고` 개발자는 `name만 정의`해주면 된다.**

  ```html
  <b-field
           label="변경 부서"
           label-position="on-border"
           >
      <b-select
                size="is-small"
                name="after_dept_id"
                placeholder="좌측 먼저 선택"
                rounded
                >
          <option v-for="dept in selectableDeptList" :value="dept.id"> {$ dept.name $}</option>
  
      </b-select>
  </b-field>
  ```

  

  ![image-20230119202736523](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230119202736523.png)



#### 선택된 현재부서외에, 해당직원의 소속부서까지 필터링 시키기 위해 employee_id도 같이 보내기

##### 가짜 form html을 만들 것 아니면 get은 불가능하다

![image-20230120002552770](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120002552770.png)

![image-20230120002602664](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120002602664.png)

- category.html의 `HTML get form`은 submit하면 querystring => `request.args.get`으로 가져올 수 있었다.
  - **하지만, js에서 `new FormData()`로 보낼 것이라면 `get요청은 무조건 에러`난다. `post`고정이다.**
  - **file이 포함되지 않는다면 headers를 추가할 필요 없이 그냥 보내고 `request.form.get`으로 받으면 된다.**

##### js로 new FormData 만들어서, post로 2개 id보내기

```js
onCurrentDeptIdChange() {
    //employee_id까지 같이 FormData로 만들어서 보내기
    const formData = new FormData();
    formData.append('current_dept_id', this.currentDeptId);
    formData.append('employee_id', this.employee_id);

    axios({
        // url: '{{ url_for("admin.get_selectable_departments", department_id="")}}' + this.currentDeptId,
        url: '{{ url_for("admin.get_selectable_departments")}}',
        method: 'post', //new FormData()로 보낼 것이라면 get요청은 무조건 에러난다.
        data: formData,
        // form에 파일이 없다면 headers는 생략해도 된다.

    }).then(res => {
        // alert("성공")
        console.log('res.status >> ', res.status);
        console.log('res.data >> ', res.data);

        this.selectableDeptList = res.data.deptInfos;
        console.log('this.selectableDeptList >> ', this.selectableDeptList);

    }).catch(err => {
        // alert("서버 연결이 올바르지 않습니다.")
        console.log(err)
        console.log(err.response.data) // return dict(json)
        console.log(err.response.data.message)
    });

},
```



##### route는 GET대신 POST로 수정하고, path변수도 삭제 + 필터링 추가

- 선택가능한 부서는 1개에 대한 처리만 하고 있다.
  - **하지만 `여기서 선택되지 않은 employee_id직원의 현재소속부서들까지 제외`시켜야한다.**
  - emp_id를 받아서, 현재 소속부서들의 id를 제외시키고 얻어오자.

- **Department의 메서드에서 Employee를 import하면 importError난다. 그냥 route에서 각각 처리되게 하자.**

```python
@admin_bp.route('/departments/selectable/', methods=['POST'])
@login_required
def get_selectable_departments():
    # print(request.form) # ImmutableMultiDict([('current_dept_id', '5'), ('employee_id', '16')])
    # print(request.args) # ImmutableMultiDict([])
    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    # print(employee_id, current_dept_id)  # None, None
    if not employee_id or not current_dept_id:
        return make_response(dict(message='잘못된 요청입니다.'), 403)

    current_dept: Department = Department.get_by_id(current_dept_id)
    selectable_depts_infos = current_dept.get_selectable_departments()

    #### 선택된 현재부서 => 가능한 부서들을 뽑아왔는데,
    #### => emp_id까지 추가로 받아서, 가능한 부서들  - ( 직원의 선택안된 현재 부서들id 제외시켜주기 )
    current_employee: Employee = Employee.get_by_id(employee_id)
    current_dept_ids = [dept.id for dept in current_employee.get_my_departments()]

    # 필터링
    selectable_depts_infos = [dept for dept in selectable_depts_infos if dept.get('id') not in current_dept_ids]

    return make_response(
        dict(deptInfos=selectable_depts_infos),
        200
    )

```

- 병원장의 또다른 부서 진료부를 선택했는데, 가능목록에 병원장이 빠진 것을 확인할 수 있다.

  ![image-20230120003233904](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120003233904.png)





##### modal 닫을 때, 사용된 변수 공통 v-model 변수 다 초기화해주기

- 현재 부서없는 사람을 선택했는데, 직전에 사용된 v-model변수에 직전사람의 선택가능 부서가 차있음

  ![image-20230120003436190](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120003436190.png)

  ![image-20230120003537369](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120003537369.png)

```html
<header class="modal-card-head">
    <p class="modal-card-title is-size-5">
        부서 변경
    </p>
    <!-- 닫기버튼시 사용된 변수 다 초기화 -->
    <button
            type="button"
            class="delete"
            @click="isDepartmentModalActive = false; employee_id = null; isSwitchedCustom='부서원';currentDeptList=null;currentDeptId=null;selectableDeptList=null;"/>
</header>
```



```html
<footer class="modal-card-foot">
    <!-- b-button들을 넣으면 1개 이후 사라지는 버그 => a태그 + input(submit) 조합으로 변경-->
    <a class="button is-primary is-light mr-2"
       @click="isDepartmentModalActive = false; employee_id = null; isSwitchedCustom='부서원';currentDeptList=null;currentDeptId=null;selectableDeptList=null;"
       >
        닫기
    </a>
    <input type="submit"
           class="button is-primary"
           value="완료"
           :disabled="isLoading"
           >
</footer>
```







#### 현재부서없을 경우 => 모든 부서를 불러오도록 처리

![image-20230120004318637](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120004318637.png)

- 부서가 없는 직원을 부서변경 버튼을 클릭할 경우, `@click="getCurrentDepartments({{employee.id}})"`에 의해 아래와 같은 데이터가 출력된다.

  - **`this.currentDeptList`를 aixos로 받아왔는데, 현재부서list가 .length ==0일 경우, axios =>  모든 부서 조회 route로 `this.selectableDeptList`를 채우면 될 것이다.**

  ![image-20230120004424104](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120004424104.png)





```python
@classmethod
def get_all_infos(cls):
    with DBConnectionHandler() as db:
        depts = db.session.scalars(
            select(cls)
            .where(cls.status == 1)
            .order_by(cls.path)
        ).all()
        return [{'id': x.id, 'name': x.name} for x in depts]
```

```python
@admin_bp.route('/departments/all', methods=['GET'])
@login_required
def get_all_departments():
    dept_infos = Department.get_all_infos()
    if not dept_infos:
        return make_response(dict(message='선택가능한 부서가 없습니다.'), 500)

    return make_response(dict(deptInfos=dept_infos), 200)
```

```js
// 현재부서가 없을 경우, -> 새롭게 axios로 모든 부서 요청해서 => this.selectableDeptList에 넣기
if (this.currentDeptList.length === 0) {
    axios({
        url: '{{ url_for("admin.get_all_departments") }}',
        method: 'get',
    }).then(res => {
        console.log('res.status >> ', res.status);
        console.log('res.data >> ', res.data)
    });
}
```



![image-20230120005328835](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120005328835.png)

- 이제 받은 모든 부서를 `this.selectableDeptList`에 넣고 확인한다

  ```js
  // 현재부서가 없을 경우, -> 새롭게 axios로 모든 부서 요청해서 => this.selectableDeptList에 넣기
  if (this.currentDeptList.length === 0) {
      axios({
          url: '{{ url_for("admin.get_all_departments") }}',
          method: 'get',
      }).then(res => {
          console.log('res.status >> ', res.status);
          console.log('res.data >> ', res.data)
          this.selectableDeptList = res.data.deptInfos;
      }).catch(err => {
          console.log(err.response.data.message)
          alert(err.response.data.message)
      });
  }
  ```

  

  ![image-20230120005606531](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120005606531.png)

#### 변경부서가 선택됨을 감지 + 부서원  or  부서장 클릭시, 승진여부를 판단해야한다

##### submit만될거라 v-model, @input감지가 없었던, 선택부서 b-select에 추가 도입하기

```html
<b-select
          size="is-small"
          name="after_dept_id"
          placeholder="좌측 먼저 선택"
          rounded
          v-model="selectedDeptId"
          @input="onSelectedDeptIdChange"
          >
```

- 도입하는 순간

  1. base.html data변수/method에 초기화
  2. 닫기버튼 2개에 변수만 초기화

  



##### 승진/강등 여부에 필요한 변수 확인하여 추가하기

- `employee_id`  +  `current_dept_id`   + **`as_leader`라는 부서장 여부**
  - 부서원 선택 + `현재부서`를 제외하고 나머지 팀장으로 소속된 부서가 없는 팀장은 -> 팀원으로 강등되는 것이다

```python
십팔번_emp.is_promote(as_leader=False)
십팔번_emp.is_demote(as_leader=True, current_dept_id=십팔번_before_dept_id)
```

- **as_leader를 b-swtich에 v-model로 도입하고 초기화까지 해준다.**

  - **하지만 현재 `isSwitchedCustom`로 string으로 쓰고 있다?!**
  - 그대로 string으로 쓰고, backend에서 바꿔주자.

- FormData 객체에 대한 설명은 MDN에 위와 같이 안내되어 있다. 단순한 객체가 아닌 XMLHttpRequest 전송을 위해 설계된 특수한 객체 형태라고 볼 수 있다.

  따라서 문자열화할 수 없는 객체이기 때문에 console.log를 사용해서 프린트할 수 없다.

  만약 전송 전에 FormData의 값을 확인하고 싶다면, 아래와 같이 FormData의 메소드를 사용해야 한다.

  ```javascript
  // FormData의 key 확인
  for (let key of formData.keys()) {
    console.log(key);
  }
  
  // FormData의 value 확인
  for (let value of formData.values()) {
    console.log(value);
  }
  ```

- **부서없는 경우, current_dept_id가 초기화값 null을 유지한다.**

  ![image-20230120011702773](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120011702773.png)

```js
//employee.html 부서변경 modal에서 2번째 부서 선택시
            onSelectedDeptIdChange(){
                console.log('선택부서 선택함.')
                const formData = new FormData();
				formData.append('current_dept_id', this.currentDeptId); //null
                formData.append('employee_id', this.employee_id); // 12
                formData.append('as_leader', this.isSwitchedCustom); //부서원

                axios({
                    url: '{{ url_for("admin.determine_promote")}}',
                    method: 'post', //new FormData()로 보낼 것이라면 get요청은 무조건 에러난다.
                    data: formData,

                }).then(res => {
                    console.log('res.status >> ', res.status);
                    console.log('res.data >> ', res.data);

                }).catch(err => {
                    alert(err.response.data.message)
                    console.log(err.response.data.message)
                });
            },
```







##### backend에서 변수받고 판단하기

```python
@admin_bp.route('/departments/promote/', methods=['POST'])
@login_required
def determine_promote():
    current_dept_id = request.form.get('current_dept_id', type=int)
    employee_id = request.form.get('employee_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)

    # print(selected_dept_id, employee_id, as_leader)
    # None 12 False
    
    if not employee_id or:
        return make_response(dict(message='잘못된 요청입니다.'), 403)

    return make_response('성공', 200)
```

- 이제 **employee객체를 찾아서, 선택된부서를 가지고 승진여부/강등여부를 각각 판단한다**

```python
@admin_bp.route('/departments/promote/', methods=['POST'])
@login_required
def determine_promote():
    current_dept_id = request.form.get('current_dept_id', type=int)
    employee_id = request.form.get('employee_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)

    # print(selected_dept_id, employee_id, as_leader)
    # None 12 False

    current_employee: Employee = Employee.get_by_id(employee_id)
    is_promote = current_employee.is_promote(as_leader=as_leader)
    is_demote = current_employee.is_demote(as_leader=as_leader, current_dept_id=current_dept_id)

    # print(is_promote, is_demote)
    
    if not employee_id:
        return make_response(dict(message='잘못된 요청입니다.'), 403)

    return make_response(dict(isPromote=is_promote, isDemote=is_demote), 200)
```



- 부서없음 => 부서장 클릭하는 경우

  ![image-20230120013622752](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120013622752.png)

  ![image-20230120013635343](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120013635343.png)

  

- 특정부서1개의 팀장 => 부서원으로 가는 경우

  ![image-20230120013730280](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120013730280.png)

  ![image-20230120013746367](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120013746367.png)



##### determine_promote는 스위치 값이 바뀔때마다 @input감지하여 호출되어야한다

- `onSelectedDeptIdChange`와 로직이 완전히 동일하므로, **`onSelectedDeptIdOrSwitchChange`**로 메서드명을 변경한다

  ```html
  <b-select
            size="is-small"
            name="after_dept_id"
            placeholder="좌측 먼저 선택"
            rounded
            v-model="selectedDeptId"
            @input="onSelectedDeptIdOrSwitchChange"
            >
      <option v-for="dept in selectableDeptList" :value="dept.id"> {$ dept.name $}</option>
  
  </b-select>
  ```

  

  ```html
  <b-switch
            size="is-small"
            v-model="isSwitchedCustom"
            true-value="부서장"
            false-value="부서원"
            name="as_leader"
            @input="onSelectedDeptIdOrSwitchChange"
            >
  ```

  

- 행정부장 => 다른부서 팀원으로 가면 isDemote: true  /  팀장으로 가면 false가 뜬다

  ![image-20230120014213122](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120014213122.png)

  ![image-20230120014222049](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120014222049.png)

- 부서없음 => 다른부서 팀장으로 가면 isPromote: true  / 팀원으로 가면  false가 뜬다.

  ![image-20230120014331948](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120014331948.png)
  ![image-20230120014321627](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120014321627.png)

#### 강등조건 추가됨. (현재부서 존재  + 현재부서에 대해 팀장이라는 조건 확인 추가)

```python
    #### with other entity
    def is_promote(self, as_leader):
        #### (0) 팀장으로 가는 경우가 아니면 탈락이다.
        if not as_leader:
            return False
        #### (1) 팀장으로 가는데, 이미 팀장인 부서가 있다면 탈락이다.

        #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & as_leader =True(최초 팀장으로 가면) => 승진
        #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
        depts_as_leader = self.get_my_departments(as_leader=True)
        return len(depts_as_leader) == 0

    #### with other entity
    def is_demote(self, as_leader, current_dept_id):
        #### (0) 팀원으로가는 경우가 아니면 애초에 탈락이다.
        if as_leader:
            return False
        #### 강등에는 현재부서에 대해 팀장이라는 조건이 필요하다.
        #### (1) 현재부서가 없다면 강등에서 먼저 탈락이다.
        current_dept = Department.get_by_id(current_dept_id)
        if not current_dept :
            return False

        #### (2) 현재부서 있더라도, 팀장이 아니면 탈락이다.
        is_current_dept_leader = self.is_leader_in(Department.get_by_id(current_dept_id))
        if not is_current_dept_leader:
            return False

        #### (3) 현재부서의 팀장인 상태에서, 제외하고 다른팀 팀장이면 강등에서 탈락이다.


        #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & as_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
        #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
        other_depts_as_leader = self.get_my_departments(as_leader=True, except_dept_id=current_dept_id)

        return len(other_depts_as_leader) == 0
```





#### 승진: true  OR   강등: true일 경우, 알려주기 buefy dialog - Confirm

- **diaglog는 `this.$buefy.dialog.confirm`으로 바로 띄울 수 있다.**
  - toast도 그런 식이니, 나중에 error날때 바꿔주자.
  - **isPromote, isDemote를 가져와서 if true인 것이 `change_position`에 문자열로 들어가게 해준다.**
    - 빈문자열로 초기화해놓고, 아무것도 안들어가면 아무상황도 아니다. **js도 빈문자를 if문에서 null로 취급한다.**
  - confirm에서 No를 누르면 isSwitchedCusotm을 반대로 바꿔줘야한다.
  - true/false가 아니라 string을 쓰고 있기 때문에 삼항연산자로 바꿔준다.



```js
onSelectedDeptIdOrSwitchChange(){
    console.log('선택부서 선택함.')
    const formData = new FormData();
    formData.append('current_dept_id', this.currentDeptId); //null
    formData.append('employee_id', this.employee_id); // 12
    formData.append('as_leader', this.isSwitchedCustom); //부서원

    axios({
        url: '{{ url_for("admin.determine_promote")}}',
        method: 'post', //new FormData()로 보낼 것이라면 get요청은 무조건 에러난다.
        data: formData,

    }).then(res => {
        console.log('res.status >> ', res.status);
        console.log('res.data >> ', res.data);
        // 승진이나 강등시 confirm으로 알려주기
        let change_position = '';
        if (res.data.isPromote){
            change_position = '승진';
        }
        if (res.data.isDemote){
            change_position = '강등';
        }
        // console.log(change_position) // js도 ''빈문자열을 if false로 취급하는 것으로 작동한다.
        if (change_position) {
            this.$buefy.dialog.confirm({
                message: '직위가 변해요!<br/><b>' + change_position + '</b>의 상황이 맞는지 확인해주세요.',
                confirmText: '계속',
                // onConfirm: () => this.$buefy.toast.open('Account deleted!'),
                cancelText: '취소',
                onCancel: () => this.isSwitchedCustom = this.isSwitchedCustom === '부서장' ? '부서원' : '부서장',
                type: 'is-danger',
                hasIcon: true,
            });
        }

    }).catch(err => {
        alert(err.response.data.message)
        console.log(err.response.data.message)
    });
},
```



![image-20230120022050658](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120022050658.png)



### 최종 부서변경처리 submit 및 route 처리하기 + reference에 텍스트 추가하기

#### form으로 넘어오는 데이터 확인용 초안 route 만들기

- 재직상태변경 route를 참고하여 작성한다

  ```python
  @admin_bp.route('/departments/change', methods=['POST'])
  @login_required
  @role_required(allowed_roles=[Roles.CHIEFSTAFF])
  def department_change():
      print(request.form)
      
      flash(f'부서 변경이 완료되었습니다.', category='is-success')
      # ImmutableMultiDict([('employee_id', '18'), ('current_dept_id', '5'), ('after_dept_id', '8'), ('as_leader', 'false'), ('date', '2023-01-20')])
  
      return redirect(redirect_url())
  ```

  

#### modal 속 form에 route명 적어주고, 각 input들의  name확인하기

- modal 속 form은 **`@submit.prevent="메서드명"`를 통해, 바로 제출을 금지하고, 해당 메서드에서 `e`를 받아서 제출하는 상황**

  - in employee.html

    ```html
    <form action=""
          method="post"
          @submit.prevent="submitForm"
          >
    ```

  - in base.html

    ```js
    submitForm(e) {
        // console.log(e)
        // e.preventDefault();
        // 1) 클릭되면 isLoading에 True가 들어가 button이 disable된다
        this.isLoading = true
    
        // 2) 다시 도로 제출
        e.target.submit();
    
        // 2) 1초후에 false가 되 button 돌아온다
        setTimeout(() => {
            this.isLoading = false
        }, 1000)
    },
    ```

- 모달이 제출시 각 input의 name이 `request.form`으로 넘어올 것이기 때문에 확인해준다.

  - employee_id, current_dept_id, after_dept_id, as_leader(<-isSwichedCustom), date(<-stringDate)

    ```python
    ImmutableMultiDict([('employee_id', '18'), ('current_dept_id', '5'), ('after_dept_id', '8'), ('as_leader', 'false'), ('date', '2023-01-20')])
    ```

  

##### b-switch의 v-model은 input type="checkbox"의 value의 값과 무관하게 switch span에만 사용되니, 따로 name과 함께 `native-value`를 설정 및 매핑되도록 `: native-value`를 추가한다.

- **`b-switch의 v-model`은 custom문자열(부서원, 부서장)으로 처리되었지만, `form에서는 true/false 문자열`로 넘어오네?**

  - **더 테스트하니까, `:value`에 매핑해도 이미 `v-model`이 value에 매핑하는 놈으로서 다른 곳에서 매핑한다.**

    ![image-20230120184516063](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120184516063.png)

    

```html
<!-- b-switch는 v-model이 data변수 + [input type="checkbox"의 value]로 매핑되는 것이 아니라 input태그아래의 스위치를 담당하는 span태그의 text를 변경시킨다. -->
<b-switch
          size="is-small"
          true-value="부서장"
          false-value="부서원"
          v-model="isSwitchedCustom"
          @input="onSelectedDeptIdOrSwitchChange"
          name="as_leader"
          :native-value="isSwitchedCustom"
          >
```

![image-20230120223050192](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120223050192.png)

![image-20230120223100839](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120223100839.png)

- 이렇게 해도 switch 터지안하면 안넘어감.

#### [bug fix] b-switch는 form에서 name으로 보내는 용도가 아님 => 일단 hidden input태그 + :value= switch변수로 대체

```
ix switch #683.
You should use native-value prop for switch and checkbox but of course when value is false option you'll have any values (as native element).
```

- value가 false옵션일 때만 native value를 쓸 수 있다. 

  - `:native-value`를 넣으면.. 1가지 상태에서만 value="false"로 고정으로 채워지며 false만 들어감.

  ```html
  <b-switch
            size="is-small"
            v-model="isSwitchedCustom"
            @input="onSelectedDeptIdOrSwitchChange"
            true-value="부서장"
            false-value="부서원"
            >
      {$ isSwitchedCustom $}
  </b-switch>
  <input type="hidden" name="as_leader" :value="isSwitchedCustom">
  ```

- backend

  ```python
  # 체크안할시
  ImmutableMultiDict([('employee_id', '16'), ('current_dept_id', '9'), ('after_dept_id', '7'), ('as_leader', '부서원'), ('date', '2023-01-20')])
  16 9 7 부서원 False 2023-01-20
  
  # 체크할시
  ImmutableMultiDict([('employee_id', '4'), ('current_dept_id', '5'), ('after_dept_id', '4'), ('as_leader', '부서장'), ('date', '2023-01-20')])
  4 5 4 부서장 False 2023-01-20
  
  ```





#### backend에서 부서변경 처리

```python
@admin_bp.route('/departments/change', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def department_change():
    # print(request.form) 
    # ImmutableMultiDict([('employee_id', '4'), ('current_dept_id', '5'), ('after_dept_id', '4'), ('as_leader', '부서장'), ('date', '2023-01-20')])
    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    after_dept_id = request.form.get('after_dept_id', type=int)
    # b-switch 아래 hidden input은 isSwitchedCustom에 의해 부서장 or 부서원이 들어옴
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    target_date = request.form.get('date',
                                   type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
                                   )

    with DBConnectionHandler() as db:
        employee: Employee = db.session.get(Employee, employee_id)

        # (bool, msg) 반환
        result, message = employee.change_department(after_dept_id, as_leader, target_date,
                                                     current_dept_id=current_dept_id)
        if result:
            flash(f'부서 변경이 완료되었습니다.', category='is-success')
        else:
            flash(message, category='is-danger')

        return redirect(redirect_url())
```

- 원래는 **employee.change_department_with_promote_or_demote()였는데 is_promote/is_demote를 미리 판단하게 되었으므로 메서드 추가해서 사용함.**



- 이미 차있는 1명 가능, `병원장`으로 변경시

  ![image-20230120234303159](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120234303159.png)

- 이미 부서장이 차있는 곳에 `부서장`으로 갈 때

  ![image-20230120234413965](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120234413965.png)

- **자동으로 부서장이 되는 부/장급 부서에 배정시 `승진여부 및 role변경`이 되도록 수정하기**

  - 지금은 STAFF를 진료부 진료부장으로 취임시켰는데, 그대로 STAFF이다.

    ![image-20230120235228138](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230120235228138.png)





#### 선택된 부서가 부/장급라면, backend에서 항상 as_leader True로 고려되도록 변경하기 위해 after_dept_id 추가보내기 => front에선 isPromote: true인데, 부서원으로 체크되어있다면, 부서장으로 항상 돌려놓기

- 지금까지는 `현재 소속된 부서(들)`의 상황 +`as_leader`여부로 결정됬지만

- **`선택된 after부서`가 부/장급일 땐 자동으로 `as_leader`가 True가 되도록 해야한다.**

```js
onSelectedDeptIdOrSwitchChange(e) {
    // console.log('선택부서 선택함.')
    const formData = new FormData();
    formData.append('current_dept_id', this.currentDeptId); //null
    formData.append('employee_id', this.employee_id); // 12
    formData.append('as_leader', this.isSwitchedCustom); //부서원
    // 부/장급 부서의 선택시, 무조건 as_leader로의 변경이므로 is_promote반영되도록 추가해서 보내기
    formData.append('after_dept_id', this.selectedDeptId); 
```



- as_leader의 선택여부와 상관없이 무조건 True로 덮어씌우기

```python
@admin_bp.route('/departments/promote/', methods=['POST'])
@login_required
def determine_promote():
    current_dept_id = request.form.get('current_dept_id', type=int)
    employee_id = request.form.get('employee_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    
    # 부/장급부서는 자동으로 as_leader = True를 박기 위해 추가로 받음.
    after_dept_id = request.form.get('after_dept_id', type=int)
    # 부/장급부서를 변경부서로 선택했다면, 넘어오는 as_leader를 무조건 True로 반영하기
    after_dept :Department = Department.get_by_id(after_dept_id)
    if after_dept.type == DepartmentType.부장:
        as_leader = True

    current_employee: Employee = Employee.get_by_id(employee_id)
    is_promote = current_employee.is_promote(as_leader=as_leader)
    is_demote = current_employee.is_demote(as_leader=as_leader, current_dept_id=current_dept_id)

    if not employee_id:
        return make_response(dict(message='잘못된 요청입니다.'), 403)

    return make_response(dict(isPromote=is_promote, isDemote=is_demote), 200)

```

![image-20230121000200285](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121000200285.png)

![image-20230121000219964](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121000219964.png)



- 현재부서가 없는 상태로 판단할 수 있는데, 



- 문제는 backend에서는 as_leader로 취급되지만, **front에서는 그대로 부서원으로 유지된다**

  - **backend에서는 after_dept_id를 받지말고, front에서 부장급 부서에 대해 무조건 부서장 고정+disabled를 할 수있을까?**
    - 그러려면, 부장급 dept id list가 따로 필요하고, front가 복잡해진다
  - **axios 성공시 `backend에서 승진의 상황으로 판단`되었는데 `부서원`으로 체크되져있다면,**
    - **`해당 변수를 무조건 부서장으로 고정`해버리자.**
  - 다행히도, 부서원으로 다시 변경시, on메서드가 작동하여 승진여부 판단 및 부서장 고정을 한다.

  

  ##### backend가 승진의 상황으로 판단됬는데 && 부서원으로 체크되어있으면 (부/장급부서)로 => [부서장]상태로 바꿔놓자

  

  ```js
  onSelectedDeptIdOrSwitchChange(e) {
      const formData = new FormData();
      formData.append('current_dept_id', this.currentDeptId); //null
      formData.append('employee_id', this.employee_id); // 12
      formData.append('as_leader', this.isSwitchedCustom); //부서원
      // 부/장급 부서의 선택시, 무조건 as_leader로의 변경이므로 is_promote반영되도록 추가해서 보내기
      formData.append('after_dept_id', this.selectedDeptId);
  
  
      axios({
          url: '{{ url_for("admin.determine_promote")}}',
          method: 'post', //new FormData()로 보낼 것이라면 get요청은 무조건 에러난다.
          data: formData,
  
      }).then(res => {
          console.log('res.status >> ', res.status);
          console.log('res.data >> ', res.data);
          let change_position = '';
          if (res.data.isPromote) {
              change_position = '승진';
          }
          if (res.data.isDemote) {
              change_position = '강등';
          }
  
          if (change_position) {
              let appended_message = res.data.isPromote? '부서관리의 책임이 생깁니다. 확인해주세요.' : '부서관리의 책임이 사라져요. 확인해주세요.';
  
              //부장급부서로 인해, 부서원상태에서도 -> 승진이 된다. 
                          // => 승진의 상황으로 판단됬는데 && 부서원으로 체크되어있으면 (부/장급부서)로 => [부서장]상태로 바꿔놓자
              if (res.data.isPromote && this.isSwitchedCustom === '부서원') {
                  this.isSwitchedCustom = '부서장';
                  appended_message = appended_message + '<br/><b>부/장급 부서</b>는 1인(CHIEFSTAFF 이상)만 등록됩니다.';
              }
  
              this.$buefy.dialog.confirm({
                  message: '<b>' + this.isSwitchedCustom + '</b>으로 <b>' + change_position + '</b>할시 직위가 변해요.' + '<br/>' + appended_message,
                  type: 'is-danger',
                  hasIcon: true,
                  confirmText: '계속',
                  cancelText: '취소',
                  onCancel: () => this.isSwitchedCustom = this.isSwitchedCustom === '부서장' ? '부서원' : '부서장',
              });
          }
  
      }).catch(err => {
          alert(err.response.data.message)
          console.log(err.response.data.message)
      });
  },
  ```



#### 현재부서선택시 변경부서목록 넘겨줄때, [부서 추가]시 currentp_dept_id None을 허용했으므로 nullable한 변수를 처리해준다.



![image-20230121014122116](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121014122116.png)



```python
@admin_bp.route('/departments/selectable/', methods=['POST'])
@login_required
def get_selectable_departments():

    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    
    #### 현재부서에서 [부서 추가]시 current_dept_id가 None으로 들어올 수 있다.
    # if not employee_id or not current_dept_id:
    if not employee_id:
        return make_response(dict(message='직원id가 잘못되었습니다.'), 403)

    #### 현재부서가 None => [부서 추가]로 판단하여, 변경부서를 모든 부서를 건네준다.
    if current_dept_id:
        current_dept: Department = Department.get_by_id(current_dept_id)
        selectable_depts_infos = current_dept.get_selectable_departments()
    else:
        selectable_depts_infos = Department.get_all_infos()

    #### 선택된 현재부서 => 가능한 부서들을 뽑아왔는데,
    #### => emp_id까지 추가로 받아서, 가능한 부서들  - ( 직원의 선택안된 현재 부서들id 제외시켜주기 )
    #### => [부서 추가]의 상황에서도  현재 소속부서들은 그대로 빼준다.
    current_employee: Employee = Employee.get_by_id(employee_id)
    current_dept_ids = [dept.id for dept in current_employee.get_my_departments()]

    # 필터링
    selectable_depts_infos = [dept for dept in selectable_depts_infos if dept.get('id') not in current_dept_ids]

    return make_response(
        dict(deptInfos=selectable_depts_infos),
        200
    )
```



![image-20230121014341427](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121014341427.png)

#### 부서선택없이, 부서장여부 swtich클릭으로 승진여부 판단이 날아올 수 있다 => 현재부서 or 변경부서 모두가 None이라면, 돌려보내도록 수정

```python
@admin_bp.route('/departments/promote/', methods=['POST'])
@login_required
def determine_promote():
    current_dept_id = request.form.get('current_dept_id', type=int)
    employee_id = request.form.get('employee_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    # 부/장급부서는 자동으로 as_leader = True를 박기 위해 추가로 받음.
    after_dept_id = request.form.get('after_dept_id', type=int)

    # 필수 인자들이 안들어오면 에러다.
    if not employee_id:
        return make_response(dict(message='잘못된 요청입니다.'), 403)

    # => 현재부서/변경부서는 둘중에 1개는 없을 수 있다. => 둘다 없으면 판단 못한다. => 부서장여부 스위치만 건들인 경우?
    # if not current_dept_id and not after_dept_id:
    if not (current_dept_id or after_dept_id):
        return make_response(dict(message='부서를 선택한 뒤, 부서장여부를 결정해주세요.'), 403)

    # 부/장급부서를 변경부서로 선택했다면, 넘어오는 as_leader를 무조건 True로 반영하기
    after_dept: Department = Department.get_by_id(after_dept_id)
    if after_dept.type == DepartmentType.부장:
        as_leader = True

    current_employee: Employee = Employee.get_by_id(employee_id)
    if as_leader:
        is_promote = current_employee.is_promote(as_leader=as_leader)
    else:
        # 부서장여부는, 부/장급이면 자동으로 True로 채워졌는데, 그래도 False라면, 승진은 절대 아니므로 배제하고 쿼리날릴 필요도 없이 무조건 False로
        is_promote = False

    if current_dept_id:
        is_demote = current_employee.is_demote(as_leader=as_leader, current_dept_id=current_dept_id)
    else:
        # 현재부서는 nullable이고, 현재부서가 없다면, 쿼리날리기도 전에 강등은 있을 수 없어서 무조건 False
        is_demote = False

    return make_response(dict(isPromote=is_promote, isDemote=is_demote), 200)

```

```js
}).catch(err => {
    // 승진여부판단시 잘못된 요청이 날아올 수 있으며 안내해야한다. (부서선택안하고 switch만 조절해서 넘어가는 경우)
    // alert(err.response.data.message)
    this.$buefy.toast.open({
        duration: 5000,
        message: err.response.data.message,
        position: 'is-top',
        type: 'is-danger'
    });
    // console.log(err.response.data.message)
});
```



![image-20230121003441851](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121003441851.png)

![image-20230121003735498](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121003735498.png)\

#### 변경부서에 [부서제거]도입시 after_dept_id는 없을 수도 있으니, if 존재시만 쿼리날리도록 조건 추가

```python
# 부/장급부서를 변경부서로 선택했다면, 넘어오는 as_leader를 무조건 True로 반영하기
# => 현재부서 -> 변경부서 [부서제거] 선택도입시 nuabllable한 after_dept_id로서, if 존재할때만 쿼리 날리기
if after_dept_id:
    after_dept: Department = Department.get_by_id(after_dept_id)
        if after_dept.type == DepartmentType.부장:
            as_leader = True
```

#### [부서제거]를 선택함에도 is_promote는 변경부서가 있다는 전제하에 현재부서_id + as_leader로만 판단 => after_dept_id 역시 존재해야 is_promote 승진여부판단하도록 조건 추가

```python
    # 승진여부판단에선 (전제 변경부서가 선택)이므로 => 변경부서가 [부서제거]-None가 아닌 [실제 값]으로 존재할때만 판단하도록 변경
    # if as_leader:
    if after_dept_id and as_leader:
        is_promote = current_employee.is_promote(as_leader=as_leader)
    else:
        # 부서장여부는, 부/장급이면 자동으로 True로 채워졌는데, 그래도 False라면, 승진은 절대 아니므로 배제하고 쿼리날릴 필요도 없이 무조건 False로
        is_promote = False
```





### 각 b-select에 [부서 추가] / [부서 제거] 하기

#### [부서추가]는 현재부서에서, 부서가없는 사람도, 부서가 있는 사람도 항상 필요하다. 

##### 조심! option태그에 value를 안준다고 v-model값에 null이 넘어가진 않는다. => text가 넘어가더라도 => value=""로 줘야 v-model에 null로 인식된다.

```html
<b-select
          size="is-small"
          name="current_dept_id"
          :placeholder="currentDeptList && currentDeptList.length ? '현재부서 선택' : '현재부서 없음'"
          rounded
          v-model="currentDeptId"
          @input="onCurrentDeptIdChange"
          >
    <option v-for="dept in currentDeptList" :value="dept.id"> {$ dept.name $}</option>

    <!-- value가 없어서 id가 None으로 가면 부서추가의 상황으로?!-->
    <!-- option에 value가 없으면 v-model에 text인 [부서추가]가 v-model에 입력되어 버린다.-->
    <!-- option에 value="" 로 놓아야 ===>  None취급당한다-->
    <option value=""> [부서 추가] </option>
</b-select>
</b-field>
```

#### [부서제거]는 v-if current_dept_id가 채워져있을 때(현재부서 선택)될때만 나타나야한다. 이것도 value=""로 after_dept_id가 null이 되게 하자.

```html
<b-select
          size="is-small"
          name="after_dept_id"
          placeholder="좌측 먼저 선택"
          rounded
          v-model="selectedDeptId"
          @input="onSelectedDeptIdOrSwitchChange"
          >
    <option v-for="dept in selectableDeptList" :value="dept.id"> {$ dept.name $}</option>
    <!-- 현재부서에 부서가 선택된 상태일때만 등장하도록 + value=""으로 주기-->
    <option v-if="currentDeptId" value=""> [부서 제거] </option>

</b-select>
```

#### route에서 after_dept_id도 nullable하며, current있고, after없으면 부서제거 상황으로 인식하기

##### 부서변경 하기 전에 퇴사한 사람은 제외시키도록, get메서드 정의 후, 필터링하자

```python
@classmethod
def get_not_resigned_by_id(cls, id):
    with DBConnectionHandler() as db:
        stmt = (
            select(cls)
            .where(cls.id == id)
            .where(cls.job_status != JobStatusType.퇴사)
        )

        return db.session.scalars(stmt).first()
```

```python
@admin_bp.route('/departments/change', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def department_change():

    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    after_dept_id = request.form.get('after_dept_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    target_date = request.form.get('date',
                                   type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
                                   )

    # with DBConnectionHandler() as db:
    #     employee: Employee = db.session.get(Employee, employee_id)
    employee: Employee = Employee.get_not_resigned_by_id(employee_id)
    #### 해당 직원이 is_active필터링이 안걸리면 퇴사상태의 직원으로 간주하고, 변경불가하다고 돌려보내기
    if not employee:
        flash('퇴사한 직원은 부서 변경이 불가능 합니다.', category='is-danger')
        return redirect(redirect_url())
    
    # (bool, msg) 반환
    result, message = employee.change_department(after_dept_id, as_leader, target_date,
                                                 current_dept_id=current_dept_id)
    if result:
        flash(f'부서 변경이 완료되었습니다.', category='is-success')
    else:
        flash(message, category='is-danger')

    return redirect(redirect_url())

```





![image-20230121025152759](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121025152759.png)

##### employee.change_department 메서드 내부에서 [부서 제거]의 조건은 current는 not None(선택함 + 부서추가 아님) && after는 None (부서제거)일때만 이다.

```python
@admin_bp.route('/departments/change', methods=['POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def department_change():
    employee_id = request.form.get('employee_id', type=int)
    current_dept_id = request.form.get('current_dept_id', type=int)
    after_dept_id = request.form.get('after_dept_id', type=int)
    as_leader = request.form.get('as_leader', type=lambda x: True if x == '부서장' else False)
    target_date = request.form.get('date',
                                   type=lambda x: datetime.strptime(x, '%Y-%m-%d').date()
                                   )


    employee: Employee = Employee.get_not_resigned_by_id(employee_id)
 
    if not employee:
        flash('퇴사한 직원은 부서 변경이 불가능 합니다.', category='is-danger')
        return redirect(redirect_url())
    
    result, message = employee.change_department(after_dept_id, as_leader, target_date,
                                                 current_dept_id=current_dept_id)
    if result:
        flash(message, category='is-success')
    else:
        flash(message, category='is-danger')

    return redirect(redirect_url())
```

```python
def change_department(self, current_dept_id, after_dept_id, as_leader, target_date):
    #### after_dept_id는 해당부서가 반드시 존재해야하므로, 존재 검사를 한다
    ### => 부서제거로 인해, nullable해졌다.
    # if not Department.get_by_id(after_dept_id):
    #     return False, "해당 부서는 사용할 수 없는 부서입니다."

    with DBConnectionHandler() as db:
        # (1) 현재부서가 선택되었다면 해임처리(나중에 현재부서가 None으로서, 변경부서를 부서추가로 쓸 수있으니 선택형으로 둠)
        # => 현재부서가 [부서추가]None만 아니면, (1-1) 다른부서 -> 부서변경으로 해임처리 (1-2) 부서제거 -> 부서제거로 해임처리 해야한다. 어느경우든 해임해야한다.
        # if current_dept_id:
        if current_dept_id :
            before_emp_dept: EmployeeDepartment = EmployeeDepartment.get_by_emp_and_dept_id(self.id, current_dept_id)
                before_emp_dept.dismissal_date = target_date

                db.session.add(before_emp_dept)

                # (2)
                #     (2-1) after부서가 있다면 -> 부서변경으로 부서정보 생성 /
                #     (2-2) after부서가 없다면 -> [부서제거]로서 아무것도 안하고 route로 메세지를 반환되어야한다.
                # (2-1) after부서가 없는 [부서제거] 상태
                if not after_dept_id:
                    db.session.commit()
                    return True, "부서 제거를 성공하였습니다."

                # (2-2) (after부서가 있는 상태: [부서변경] or [부서추가] -> 후반부서 취임정보 생성)
                after_emp_dept: EmployeeDepartment = EmployeeDepartment(employee_id=self.id,
                                                                        department_id=after_dept_id,
                                                                        is_leader=as_leader,
                                                                        employment_date=target_date)
                    result, message_after_save = after_emp_dept.save()

                    if result:
                        # (3) 만약 after부서에 취임 성공했다면, 취임정보.save()에서 나온 성공메세지 대신 => 부서변경 성공 메세지를 반환
                        db.session.commit()
                        # => current부서가 선택안됬다면, 부서추가 / 선택됬다면 부서 변경
                		return True, ( "부서 변경을 성공하였습니다." if current_dept_id else "부서 추가를 성공하였습니다.")

                    else:
                        # (2-2) 만약  after부서에 취임 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환 => route에서 그대로 취임실패 메세지를 flash
                        db.session.rollback()
                        return False, message_after_save
```

![image-20230121030929553](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121030929553.png)

![image-20230121031516358](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121031516358.png)

![image-20230121031538523](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121031538523.png)

![image-20230121031544188](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121031544188.png)

#### b-select placeholder들도 각 dept_id가 None으로 들어오므로, required 붙여서, [부서추가], [부서제거]의 None(value="")과 못겹치게 하기

```html
<b-select
          size="is-small"
          name="current_dept_id"
          :placeholder="currentDeptList && currentDeptList.length ? '현재부서 선택' : '현재부서 없음'"
          rounded
          v-model="currentDeptId"
          @input="onCurrentDeptIdChange"
          required
          >
```



![image-20230121031958038](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121031958038.png)



- **현재부서가 비어있는 경우, required 넣고, [부서 추가] 선택하면 선택안한 것으로 나와서 제거함.**



#### 어차피 승진/강등여부 정보를 한번 더 emp.change_departments 내부에서 이루어져서 role도 업데이트 해야한다.

##### 승진/강등여부 메서드 쓰기 전 조건 확인하기

- 부서추가: current X -> after O
- 부서제거: current O -> after X

- 승진 확인의 조건
  - after O여야하며
    - after 의 type을 판단해서 as_leader가 변경될 수 있다.
  - after O and as_leader가 O일 때 메서드로 확인한다
- 강등 확인의 조건
  - current O 여야하며
    - after는 None이어도 상관없다.
  - current O and as_leader X일 때 메서드로 확인한다

- **애초에 인자로 넘겨줘서 is_promote, is_demote 내부에서 판단하도록 변경하자(main.py 수정해야할 듯)**

##### 기존 route에서 덧붙인 로직

```python
@admin_bp.route('/departments/promote/', methods=['POST'])
@login_required
def determine_promote():
    
    #...
    
   # 부/장급부서를 변경부서로 선택했다면, 넘어오는 as_leader를 무조건 True로 반영하기
    # => 현재부서 -> 변경부서 [부서제거] 선택도입시 nuabllable한 after_dept_id로서, if 존재할때만 쿼리 날리기
    if after_dept_id:
        after_dept: Department = Department.get_by_id(after_dept_id)
        if after_dept.type == DepartmentType.부장:
            as_leader = True

    current_employee: Employee = Employee.get_by_id(employee_id)

    # 승진여부판단에선 (전제 변경부서가 선택)이므로 => 변경부서가 [부서제거]-None가 아닌 [실제 값]으로 존재할때만 판단하도록 변경
    # if as_leader:
    if after_dept_id and as_leader:
        is_promote = current_employee.is_promote(as_leader=as_leader)
    else:
        # 부서장여부는, 부/장급이면 자동으로 True로 채워졌는데, 그래도 False라면, 승진은 절대 아니므로 배제하고 쿼리날릴 필요도 없이 무조건 False로
        is_promote = False

    # 강등여부판단은 전제가 [변경부서선택 with 부서원] OR  변경부서선택을 => [부서제거]로 None이어도 상관없다.
    # => 내부에서 1개 팀장인데 && 부서원으로 뿐만 아니라 1개 팀장인데 && after_dept_id가 None도 추가해야할 듯하다.
    if current_dept_id:
        # 1) 현재부서  +  선택부서가 부서원으로 판단
        is_demote = current_employee.is_demote(as_leader=as_leader, current_dept_id=current_dept_id)
        # 2) 현재부서 + 선택부서가 None으로 해지를 추가할 예정
    else:
        # 현재부서는 nullable이고, 현재부서가 없다면, 쿼리날리기도 전에 강등은 있을 수 없어서 무조건 False
        is_demote = False

    return make_response(dict(isPromote=is_promote, isDemote=is_demote), 200)
```

- is_promote()

  ```python
  #### with other entity
  def is_promote(self, as_leader):
      #### (0) 팀장으로 가는 경우가 아니면 탈락이다.
      if not as_leader:
          return False
      #### (1) 팀장으로 가는데, 이미 팀장인 부서가 있다면 탈락이다.
  
      #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & as_leader =True(최초 팀장으로 가면) => 승진
      #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
      depts_as_leader = self.get_my_departments(as_leader=True)
      return len(depts_as_leader) == 0
  ```

- is_demote()

  ```python
  #### with other entity
  def is_demote(self, as_leader, current_dept_id):
      #### (0) 팀원으로 가는 경우가 아니면 애초에 탈락이다.
      if as_leader:
          return False
      #### 강등에는 현재부서에 대해 팀장이라는 조건이 필요하다.
      #### (1) 현재부서가 없다면 강등에서 먼저 탈락이다.
      current_dept = Department.get_by_id(current_dept_id)
      if not current_dept:
          return False
  
      #### (2) 현재부서 있더라도, 팀장이 아니면 탈락이다.
      is_current_dept_leader = self.is_leader_in(Department.get_by_id(current_dept_id))
      if not is_current_dept_leader:
          return False
  
      #### (3) 현재부서의 팀장인 상태에서, 제외하고 다른팀 팀장이면 강등에서 탈락이다.
  
      #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & as_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
      #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
      other_depts_as_leader = self.get_my_departments(as_leader=True, except_dept_id=current_dept_id)
  
      return len(other_depts_as_leader) == 0
  ```

  

##### 승진/강등 로직 정리하여 메서드 수정하기

1. is_promote에 after_dept_id가 필수로 들어가야한다

   - **이미 CHIEFSTAFF이상의 직위면 탈락이다.**

   - after가 None이라면, [부서제거]로서 승진탈락이다
   - after가 active하지 않은 부서라서 조회안되면 탈락이다
   - after가 부/장급이라면, 미리 as_leader를 True로 돌려 놓는다.
   - as_leader가 False면 탈락이다
   - 현재 팀장으로소속된 부서가 있으면 탈락이다

2. is_demote에 current_dept_id외 after_dept_id( ->부장급 부서 판별 -> as_leader True)을 위해서  필수로 들어가야한다

   - **EXECUTIVE 이상의 직원은 관리자급으로서, 부서변경과 무관하게 role변경시키면 안된다.**
   - **이미 CHIEFSTAFF 미만 직위의 직원(STAFF)면 강등 탈락이다.**
   - current가 None이라면, [부서추가]로서 강등 탈락이다.
     - after는 None이라도, [부서 제거]로서, 부서선택+부서원과 동급으로 고려대상이라 상관없다.
   - current가 active하지 않은 부서라서 조회안되면 탈락이다
   - 현재current부서외에 또다른 부서에 팀장으로 있다면 탈락이다.
   - 현재current부서만 가지고 있더라도, 팀장이 아니라 팀원이면 탈락이다.
   - after가 O인데, 부장급 부서라면, 무조건 as_leader True로 할당되어 as_leader 판별시 자동 탈락이다. 
   - as_leader가 True탈락이다.

```python
    #### with other entity
    def is_promote(self, after_dept_id, as_leader):
        # 추가 -> (1) 이미 직위가 CHIEFSTAFF이상이면 탈락이다.
        if self.is_chiefstaff:
            return False

        # 추가 -> (2) 변경할 부서가 없으면 [부서제거]이므로 승진은 탈락이다.
        if not after_dept_id:
            return False
        # 추가 -> (3) after부서가 부/장급일 땐, as_leader가 부서원으로 왔어도 True로 미리 바꿔놔야한다.
        after_dept: Department = Department.get_by_id(after_dept_id)
        #            그 전에, active부서가 아니면 탈락이다.
        if not after_dept:
            return False
        
        if after_dept.type == DepartmentType.부장:
            as_leader = True

        # (4) (부서가있더라도) 팀장으로 가는 경우가 아니면 탈락이다.
        if not as_leader:
            return False

        # (5) 팀+장으로 가는데, 이미 팀장인 부서가 있다면 탈락이다. => 없어야 통과다
        #### 승진: 만약, before_dept_id를 [포함]하여 팀장인 부서가 없으면서(아무도것도 팀장X) & as_leader =True(최초 팀장으로 가면) => 승진
        #### - 팀장인 부서가 1개도 없다면, 팀원 -> 팀장 최초로 올라가서, 승진
        depts_as_leader = self.get_my_departments(as_leader=True)
        if depts_as_leader:
            return False

        return True
```

```python

    #### with other entity
    def is_demote(self, current_dept_id, after_dept_id, as_leader):
        # (1) 이미 CHIEFSTAFF 미만 직위의 직원(STAFF)면 강등 탈락이다.
        if not self.is_chiefstaff:
            return False

        # (2) 현재부서가 없다면 [부서 추가]의 상황으로 강등 탈락.
        if not current_dept_id:
            return False
        # (3) 현재부서가 있더라도, 조회시 active한 부서가 아니라면 강등 탈락이다.
        current_dept = Department.get_by_id(current_dept_id)
        if not current_dept:
            return False

        # (4) current외 다른 부서의 팀장으로 소속되어 있다면 강등 탈락이다.
        #### 강등: 만약, before_dept_id를 [제외]하고 팀장인 부서가 없으면서(현재부서만 팀장) & as_leader =False(마지막 팀장자리 -> 팀원으로 내려가면) => 강등
        #### - 선택된 부서외 팀장인 다른 부서가 있다면, 현재부서만 팀장 -> 팀원으로 내려가서, 팀장 직책 유지
        other_depts_as_leader = self.get_my_departments(as_leader=True, except_dept_id=current_dept_id)
        if other_depts_as_leader:
            return False

        # (5) (팀장인 또다른 부서X)현부서만 가지고 있더라도, 팀장이 아니라면 강등 탈락이다.
        is_current_dept_leader = self.is_leader_in(Department.get_by_id(current_dept_id))
        if not is_current_dept_leader:
            return False

        # (6) after부서가 None이어도 되는데, 만약 있는데 부/장급 부서라면 as_leader True를 할당해야하며
        # -> as_leader 판단시 True면 [부서원or부서제거]의 상황이 아니므로 탈락이다.
        if after_dept_id:
            after_dept: Department = Department.get_by_id(after_dept_id)
            if after_dept.type == DepartmentType.부장:
                as_leader = True

        # (7) as_leader가 True면 CHIEFSTAFF이상으로 가는 거라 탈락이다.
        if as_leader:
            return False

        return True
```



#### 승진/강등 메서드 정리후, emp.change_departments 내부에 반영하여 role변경 시키기

- **부서변경과 무관하게 먼저 승진/강등여부 -> Role부터 바꿔놓는다.**
  - 아래에서 부서변경 다되면 commit될 것이다.

```python
def change_department(self, current_dept_id, after_dept_id, as_leader, target_date):

    with DBConnectionHandler() as db:
        #### 부서변경/추가/제거와 무관하게 승진/강등여부를 통해 role 변경해놓기
        if self.is_demote(current_dept_id, after_dept_id, as_leader):
            self.user.role = Role.get_by_name('STAFF')
            db.session.add(self)

        if self.is_promote(after_dept_id, as_leader):
            self.user.role = Role.get_by_name('CHIEFSTAFF')
            db.session.add(self)
            
        # ...
```



![image-20230121043349269](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121043349269.png)

![image-20230121043538213](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121043538213.png)

![image-20230121043453652](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121043453652.png)

![image-20230121043516682](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121043516682.png)

![image-20230121043525192](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230121043525192.png)



#### 부서변경 완료시마다 reference도 채워주면서, emp.change_department() 코드 정리하기

- 현재 퇴사에서도 reference 빠진 상태라 추가함.
- 현재 emp (self)자체의 필드변화는 승진/강등여부시 **self의 role변화 후 add(self)**했었는데
  - 주석처리하고, 부서변경 상태(변경/추가/제거)에 따라 `.reference` 등록하고 commit전에 add해준다.

```python
    def change_department(self, current_dept_id, after_dept_id, as_leader, target_date):

        with DBConnectionHandler() as db:
            ## 부서의 [제거 or 변경/추가] 와 무관하게 승진/강등여부 판단 => role필드 변화해놓기
            # => cf) 관계객체(user)의 .role필드에는 해당 데이터가 불러와 있으니, 같은 객체를 get조회해서 대입할시 에러 나니 조심.
            if self.is_demote(current_dept_id, after_dept_id, as_leader):
                self.user.role = Role.get_by_name('STAFF')
                # db.session.add(self) # 뒤에 self.reference변경때문에 add를 좀 더 뒤에서

            if self.is_promote(after_dept_id, as_leader):
                self.user.role = Role.get_by_name('CHIEFSTAFF')
                # db.session.add(self)

            ## 현재 취임정보를 제거할 상황(부서변경or부서제거)을 찾아 먼저 제거하기
            # (1) 현재부서가 선택되었다면, [부서추가]가 아닌 [부서변경] OR  [부서제거]상황이다.
            #    => 둘다 현재부서 취임정보를 해임시켜야한다.
            if current_dept_id:
                current_emp_dept: EmployeeDepartment = EmployeeDepartment.get_by_emp_and_dept_id(self.id, current_dept_id)
                current_emp_dept.dismissal_date = target_date

                db.session.add(current_emp_dept)

            ## 다음 취임정보를 생성하지 않는 상황(부서 제거) 먼저 처리하기
            # (2) after 부서가 선택안되었다면 (current는 무조건 선택된) => [부서제거]의 상황으로 취임정보 생성 없이
            #     현재 취임정보 삭제된 상태를 commit하고 끝낸다.
            #    1) after부서가 없다면 -> [부서제거]로서 취임정보 생성 없이 바로 return해야한다.
            #    =>  after부서가 없는 [부서제거] 상태 ( current는 무조건 있음 )를 처리한다.
            #    2) after부서가 있다면 -> [부서변경] or [부서추가]의 상황으로 취임정보 새로 생성되어야한ㄷ다
            # (2-1)
            if not after_dept_id and current_dept_id:
                # 부서제거시, 부서제거 refence입력하고 add
                current_dept: Department = Department.get_by_id(current_dept_id)
                self.update_reference(f"[{current_dept.name}]부서 해임({format_date(target_date)})")
                db.session.add(self)

                db.session.commit()
                return True, f"[{current_dept.name}]부서 제거를 성공하였습니다."

            ## 다음 취임정보를 생성하는 상황(부서 변경 or 부서 추가)
            # (2-2) (after부서가 있는 상태): current O[부서변경] or current X [부서추가] -> after 부서 취임정보 생성
            after_emp_dept: EmployeeDepartment = EmployeeDepartment(employee_id=self.id,
                                                                    department_id=after_dept_id,
                                                                    is_leader=as_leader,
                                                                    employment_date=target_date)
            result, message_after_save = after_emp_dept.save()

            if result:
                ## result가 True라는 말은, after부서가 있어서 => 새로운 부서 취임정보 생성 완료
                after_dept: Department = Department.get_by_id(after_dept_id)
                # (3) current부서 O : 부서 변경 / current부서 X : 부서 추가
                # (4) 취임정보.save()에서 나온 성공1/실패N 메세지 중 [취임정보 생성 성공1]에 대해
                # => current O/X에 따라 부서변경/ 부서추가의 메세지 따로 반환
                if current_dept_id:
                    current_dept: Department = Department.get_by_id(current_dept_id)
                    self.update_reference(f"[{current_dept.name}→{after_dept.name}]부서 변경({format_date(target_date)})")

                    message = f"부서 변경[{current_dept.name}→{after_dept.name}]을 성공하였습니다."

                else:
                    self.update_reference(f"[{after_dept.name}]부서 취임({format_date(target_date)})")
                    message = f"부서 추가[{after_dept.name}]를 성공하였습니다."

                db.session.add(self)
                db.session.commit()

                return True, message

            ## save에 실패하면 message_after_save의 이유로 실패했다고 rollback하고  반환한다.
            # (5) 최종 저장여부를 결정하는 것은 부서변경여부다. .save()가 실패하여 result가 False로 올경우 rollback한다.
            else:
                # (2-2) 만약  after부서에 취임 실패한다면, 취임정보.save()에서 나온 에러메세지를 반환 => route에서 그대로 취임실패 메세지를 flash
                db.session.rollback()
                return False, message_after_save
```

