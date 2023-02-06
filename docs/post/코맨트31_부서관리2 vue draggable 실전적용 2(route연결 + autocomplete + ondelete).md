### route와 연계해서 실제 데이터로 만들기



#### Get

##### jinja로 던질 땐 dict(data=)에 array를 넣어서 dict로 반환하고 view에서  {{tree | json}}으로 받아서 .data 로 array꺼낸 것을 this.depts(공급데이터)로 넣어주기

- **roots로서 맨바깥에 array = []를 json으로 보내기 위해 `{ data : [ ] }`형태의 dict를 `json`으로 보낸다.**
  - **view에선 `보낸데이터tree.data`로 사용해야한다.**

1. 기존 `조직도`에서 쓰이는 메서드 `get_all_tree(cls)`는 status = 1 만 가져오는데 **관리에서는 다 필요하므로, 인자를 추가해서 status 상관없이 다 가져오게 한다.**

   ```python
   @classmethod
   def get_all_tree(cls, with_inactive=False):
       root_departments = cls.get_roots(with_inactive=with_inactive)
   
       tree_list = []
       for root in root_departments:
           tree_list.append(root.get_self_and_children_dict())
   
           return dict(data=tree_list)
   ```

   ```python
   # root부서들부터 자식들 탐색할 수 있게 먼저 호출
   @classmethod
   def get_roots(cls, with_inactive=False):
       with DBConnectionHandler() as db:
           stmt = (
               select(cls)
               .where(cls.parent_id.is_(None))
           )
           if not with_inactive:
               stmt = stmt.where(cls.status == 1)
   
               return db.session.scalars(stmt).all()
   ```

   ```python
   @dept_bp.route("/management", methods=['GET'])
   def management():
   
       tree = Department.get_all_tree(with_inactive=True)
   
       return render_template('department/component_test.html',
                              tree=tree)
   ```

   



##### created에서 axios.get 대신 jinja로 초기데이터 받기

- `tree.data`를 json으로 파싱하여 root array를 공급변수 `this.depts`에 넣어준다.

```js
getDepts() {

    this.depts = JSON.parse('{{ tree.data | tojson }}')
    this.updateTreeData();
    // 초기화데이터에 넣는 것은 밖에서 따로 함.
},
```

![image-20230131232955123](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131232955123.png)

​	![image-20230131233155351](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131233155351.png)

##### 예시데이터와 다른점 수정 



1. 에러는 **`자식이 없는 놈도 children`이라는 필드를 가지고 있고 조회되도록 `tree컴포넌트`가 설계되었기 때문에 `children.length`로 자식여부를 확인한다.**

   - .children을 사용하는 곳에서 children 가졌는지 확인부터 하도록 수정해보기

   

2. backend에서 항상 빈 children이라도 만들도록 수정

   ```python
   def get_self_and_children_dict(self):
       # result = self.row_to_dict
       result = self.to_dict(delete_columns=['pub_date', 'path', ])
   
       children = self.get_children()
   
       #### view의 tree컴포넌트는 항상 children을 가지고 있고, children.length로 자식여부를 판단하므로
       #### => 항상 children을 빈list라도 만들어서 반환하도록 수정
       # if len(children) > 0:
       result['children'] = list()
       for child in children:
           # 내 자식들을 dict로 변환한 것을 내 dict의 chilren key로 관계필드 대신 넣되, 자식들마다 다 append로 한다.
           result['children'].append(child.get_self_and_children_dict())
   
           return result
   
   ```

   ![image-20230131234032199](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131234032199.png)





3. **dept.text.length에서 걸린 것 같다. `dept.name.length`가 되도록 수정해야한다.**
   - dept.text => dept.name으로 모두 수정
   - **`오류 해결`**



4. **sort순으로 정렬시켜서 보내야 일치됨.**

   ```python
   @classmethod
   def get_roots(cls, with_inactive=False):
       with DBConnectionHandler() as db:
           stmt = (
               select(cls)
               .where(cls.parent_id.is_(None))
               .order_by(cls.path) # view에선 sort순이 중요함.
           )
           if not with_inactive:
               stmt = stmt.where(cls.status == 1)
   
               return db.session.scalars(stmt).all()
   ```

5. **backend에선 `parent_id` => front에선 `parentId`로 사용하므로, 변경해서 보내줘야함.**

   1. `조직도`만들 땐 jinja라서 `parent_id`로 썼으므로, **to_dict()가 서로 달라야한다.**

      1. **재귀가 아니라면, 다른 방법도 많은데...**

         ```python
         mydict[k_new] = mydict.pop(k_old)
         
         ```

         

         ```python
         >>> d = {0:0, 1:1, 2:2, 3:3}
         >>> {"two" if k == 2 else k:v for k,v in d.items()}
         {0: 0, 1: 1, 'two': 2, 3: 3}
         ```

   2. **찾아보니 `조직도`에서는 `parent_id`를 사용하지 않는다. -> to_dict에서 변경해서 보내주자**

      - to_dict에서는 사용하고 있으니, 아래와 같이 더 아래서 처리하자.

      ```python
              # [부모 부서의 sort]  부모색에 대한 명도만 다른 색을 입히기 위해, 색을 결정하는 부모의 sort도 추가
              parent_id = self.parent_id
              if parent_id:
                  data['parent_sort'] = Department.get_by_id(parent_id).sort
              else:
                  data['parent_sort'] = None
      
              #### 부서관리 tree용: parent_id -> parentId로 보내준다. ####
              data['parentId'] = data.pop('parent_id')
      
      
              return data
      ```

      ![image-20230201000625686](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201000625686.png)





##### 필요한 정보 view에 추가하고, 안쓸 정보는 안받기?!

![image-20230201001412106](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201001412106.png)



- 관리창

  - `.only_children_count` : 하위부서수 => 열기/접기 옆에
  - `.leader.name`
  - `.all_employee_count` : **`부서장 제외 직원수` + `하위부서장/하위직원은 모두`**
    - **부서장 외 `N명`이 됨.**
    - **부서장 외 N명 표시의 v-if 기준이 됨.**

  - `.level`, `.parent_sort` : **색깔 나타내기 위해 필요**

- 상세정보창 -> axios요청으로 받아올 듯.

  - `leader` : 팀장정보
    - 
  - `add_date`: 부서 생성일
  - `type`: 부서타입 
  - `all_employee_count` : 나 포함 모든 사원수 
  - `employees` : 직원들정보





##### getTextColorToLevelandSort( .level, .sort, .parent_sort ) base.html에 텍스트color용으로 추가

- 연한색, 노란색 XX -> 색상변경

```js
getTextColorToLevelAndSort(level, parentSort, sort) {
    let boldColor = [
        'has-text-dark has-text-weight-bold ',
        'has-text-primary has-text-weight-bold ',
        'has-text-info has-text-weight-bold ',
        'has-text-danger has-text-weight-bold ',
        'has-text-success has-text-weight-bold ',
    ];

    boldColor = boldColor.concat(...boldColor);

    let normalColors = [
        'has-text-dark  ',
        'has-text-primary ',
        'has-text-info  ',
        'has-text-danger  ',
        'has-text-success  ',
    ];

    normalColors = normalColors.concat(...normalColors);

    if (level === 0) {
        return boldColor[level]
    } else if (level === 1) {
        return boldColor[sort]

    } else {
        if (level % 2 === 0) {
            return normalColors[parentSort]
        } else {
            return boldColor[parentSort]
        }
    }
},
```

- 부서관리

```html
<!-- Name or Input-->
<span :id="'node-' + dept.id"
      :class=" dept.id !== idOfSelectedDept ? getTextColorToLevelAndSort(dept.level, dept.parent_sort, dept.sort) : 'abc' "
      >
```

![image-20230201034402440](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201034402440.png)





##### 버그fix : sort변환시, backend에선 알아서 자식sort도 변할 예정 <-> but front에선 자식의 parent_sort아 안변하면, 자식들의 색깔은 직전자리로 유지됨

##### treeChanged에서 dept.sort변경될 시,~~bfs로~~ 자식들 순회하며 parent_sort 바꿔주기

- 바로 직후의 parent_sort만 바꿔주면 된다.  자식의 자식들은 자식의 sort + level로 결정되기 때문

![image-20230201034416411](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201034416411.png)

```js
node.sort = payload.afterSort;
// 자식들 색을 위해 자식들의 .parent_sort도 다 바꿔주기
for (let child of node.children) {
    child.parent_sort = node.sort;
}
```



- 문제는 같이 바뀌는 놈도 같이 처리해줘야한다.

![image-20230201034918581](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201034918581.png)

```js
let myParentChildren = node.parent ? node.parent.children : this.treeData;
for (const [index, node] of myParentChildren.entries()) {
    const mySort = index + 1;
    // 바뀌는 놈들
    if (mySort !== node.sort) {
        node.sort = mySort;
        // 바뀌는 놈들은 그놈의 자식들의 .parent_sort도 같이 바꿔주기
        for (let child of node.children) {
            child.parent_sort = node.sort;
        }
    }
}
```



![image-20230201035131618](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201035131618.png)



##### parentId -> parent_id로 변경 + children 강제로 만들어주는 것 복구

- 어차피 다 필드명으로 쓰고 있어서 backend변경말고, front껄 parentId => parent_id로 변경하자.
  - `.parentId` -> .parent_id로 변경
  - form object속 parentId -> parent_id로 변경
- backend도 변경
  - route
  - to_dict에서 보내는 것도 복구





#### Add

- add는 modal -> `submitDeptForm`으로 이루어진다
  - **submitDeptForm을 `submitDeptAddForm`으로 변경하자.**



##### .save()메서드 수정 (검증 추가 및 (self or False, message) 튜플반환으로 수정) + flush관련 내용

- **sessin.add만 하고 구성했었지만, `parent_id -> .parent`연동을 위해 flush를 써서, id + parent객체 연동이 되게하고, `실패시 .rollback()`을 써줬다.**
  - flush를 하지 않으면, parent_id=  입력으로 .parent연동이 안됨.
  - rollback하면 id+parent연동 사라져서 복구됨.

1. 검증1: 기존 `이미 존재하는 부서인지 확인`

   ```python
   def save(self):
   
       # 검증1: 이미 존재하는 부서
       if self.exists():
           # print(f"{self.name}는 이미 존재하는 부서입니다.")
           return False, f"{self.name}는 이미 존재하는 부서입니다."
   ```

   

2. 검증2:  **`부모 or 부모가 없으면 root들의 갯수를 10개로 제한`**

   ```python
   if self.parent:
       # [검증2-1] 이미 해당 부모의 자식이 10명이 채워진 경우, 11번부터 생성못하게 막기
       # =>  flush() 이후의 실패는 rollback() 달아서, 연동했던 것 취소하기
       if len(self.parent.children) > 10 :
           db.session.rollback()
           return False, "한 부모아래 자식부서는 10개를 초과할 수 없습니다."
   ```

   ```python
   else:
       sort_count = db.session.scalar(
           select(func.count(Department.id)).where(Department.parent_id.is_(None))
       )
       # [검증2-2] 부모 없는 경우 root부서의 갯수가 10명이 채워진 경우, 11번부터 생성못하게 막기
       # =>  flush() 이후의 실패는 rollback() 달아서, 연동했던 것 취소하기
       if sort_count > 10:
           db.session.rollback()
           return False, "최상위 부서는 10개를 초과할 수 없습니다."
   ```

   

##### submitDeptAddForm axios 요청을 route에서 처리하기

1. Department( ) `.save()`시, **생성 실패에 대한 flag(객체 or False) + message를 내려주자.**

   - route에서 message를 작성하면, False에 어떤 실패인지 모르게 됨.

   ```python
   return self, "부서 생성에 성공하였습니다."
   ```

2. **생성된 dept를 to_dict로 만들어서 보내줘야한다.**

   - **array가 아니기 때문에, dict(data=)로 감싸주지 않아도 된다?**
   - **make_reponse( ) 안에는 `dict`가 들어가야하며, `message=도 함께`넣어줘야하기 때문에 `to_dict된 데이터 + key` + `message=message`를 같이 묶어서 dict로 보내줘야 `front에서 response.data 안에 .데이터key,  .message`를 읽을 수 있다. **

3. **반환된 flag에 객체로서 존재할 때만 객체와 함께보낸다.**

   - **flag가 실패일 땐, status코드를 200 초과하게 보내자**
   - **make_reponse(  dict(key=, message= ) `for res.data`,  `STATUS_CODE`)로 마지막 인자로 주면 된다.**

   ```python
   @dept_bp.route("/add", methods=['POST'])
   def add():
       dept_info = request.get_json()
   
       new_dept, message = Department(
           name=dept_info['name'],
           type=int(dept_info['type']),  # type만 b-select로 인해 "3" 문자열로 온다.
           parent_id=dept_info['parent_id']).save()
   
       if new_dept:
           return make_response(dict(new_dept=new_dept.to_dict(), message=message), 201)
       else:
           return make_response(dict(message=message), 409)
   ```

   ![image-20230201171411322](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201171411322.png)

   ![image-20230201171734556](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201171734556.png)



##### fix: route에서 new_dept.to_dict()를 치면, 이미 session에서 떨어졌는데 to_dict의 get(self, _key)시 sessionDetached뜬다. => .save()반환시 내부에서  to_dict()한 dict를 반환

- **생성해놓고, 자신의 정보만 반환한 .save() => new_depts(객체)가 아니라 `.save() 속 session으로 to_dict까지 하고 반환`**

  ```python
  # .save() 
  
  return self.to_dict(delete_columns=['pub_date', 'path', ]), "부서 생성에 성공하였습니다."
  
  ```

  ```python
  # router
  if new_dept:
      return make_response(dict(new_dept=new_dept, message=message), 201)
  else:
      return make_response(dict(message=message), 409)
  
  ```



##### view 코드 처리하기

```js
// modal용 submit메서드
submitDeptAddForm(e) {
    //1. 로딩을 띄워서 send버튼 비활성화
    this.isLoading = true;
    // console.log("this.form", this.form) // 부서type option을 int로 넣어줬어도, b-select가 문자열로 보냄.

    //2.
    axios({
        url: '{{ url_for("department.add") }}',
        method: 'post',
        data: this.form,
        headers: {'Content-type': 'application/json;charset=utf-8'},
    }).then(res => {
        // 통신성공 but 로직 실패(200대 외)
        if (res.status >= 300) {
            this.toast(res.data.message, 'is-danger')
            return;
        }

        // 통신 성공 + (DB생성)로직 성공 -> tree에 생성된 자식 push -> 공급/초기데이터도 업뎃
        // TODO: 부서생성되었으니, tree도 업뎃?!
        // (1) 생성된 데이터를 받는다.
        let newDept = res.data.new_dept;

        // (2) 연동데이터인 해당부모 or root에 push한다.
        const parentChildren = this.selectedDept
        ? this.selectedDept._vm.data.children
        : this.treeData;
        parentChildren.push(newDept);

        // (3) tree를 업뎃한다.
        this.treeUpdated(); // tree(vm) 자체 ----getPureData------> this.depts
        this.initialDepts = this.depts; // this.depts -------> this.initialDepts


        // 성공시에만 (1) 모달끄기 (2) form데이터 초기화
        this.isDepartmentModalActive = false; // 로직 성공시에만 모달창 닫기
        this.initObject(this.form); // 로직 성송시에만 form속 데이터 초기화


        this.toast(res.data.message)

    }).catch(err => {
        console.log(err)
        // 특별히 err에 response가 내려온다면. 거기서 메세지를 꺼내서
        this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');

    }).finally(() => {
        this.isLoading = false; // 로딩 끄기
    });

},
```





##### depth (level5, depth6)제한 주기 -> self.path를 채운 뒤쪽에 self.level을 쓸 수 있다.

```python
self.sort = sort_count

prefix = self.parent.path if self.parent else ''
self.path = prefix + f"{self.sort:0{self._N}d}"

#### level은 self.path 완성후 사용할 수 있다.
# [검증4] parent에 의해 결정되는 level이 7(depth8단계) 초과부터는 안받는다.
if self.level > 5:
    db.session.rollback()
    return False, "최대 깊이는 6단계 까지입니다."

db.session.commit() # 검증(flush 이후 rollback) 통과시에만 commit

return self.to_dict(delete_columns=['pub_date', 'path', ]), "부서 생성에 성공하였습니다."

```



![image-20230201174751783](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201174751783.png)

![image-20230201174718667](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230201174718667.png)





####  Delete

- 참고: `코맨트22_Department모델과사용2 - 9 delete는  나의 자식 부서가 없으면서 and 해당부서이하의 User들을 누적한 count가 0일때만, 해당부서를 찾아서 삭제한다.`

  ```python
  
  @module.get('/company-structure/delete/<int:dep_id>')
  def delete_structure(dep_id):
      Department.delete(dep_id)
      return redirect(url_for('admin.company_structure'))
  
  
  @classmethod
  def delete(cls, uid):
      parent_dep = cls.query.filter_by(parent_id=uid)
      if (parent_dep.count() == 0) and (User.count_users_in_department(uid) == 0):
          cls.query.filter_by(id=uid).delete()
          db.session.commit()
  ```

- **multidepth 구조에서 부모가 삭제된다면**

  - **자식들 입장에선 같이지워지거나**
    - `참사`
  - **안지워지고, parent_id(부모)를 ondelete에 set null로 둔다면, root가 되어버린다.**
    - `참사2`
  - **`애초에 자식있으면 안지워지게 하는 것이 기본인 듯하다.`**



##### backend에서  cls .delete(dept_id) 메서드 구현하기

- 조회 `gey_by_id(dept_id)`처럼 지워질 대상의 `dept_id`만 받으면 된다.
- **검증1: 존재해야한다. => **
  - **`여기서 객체를 찾아 session.delete(  only객체만 )`에 활용한다**
  - 자식 검사나, 취임정보검사에서도 활용할 수 있다 ( 순수 stmt안써도 된다?)
- **검증2: 딸린 자식이 없어야한다.**
- **검증2: 관계테이블(부서취임 정보)에 취임중인 직원이 없어야한다.**

```python
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
        if employee_count:
            return False, "재직 중인 직원이 존재하면 삭제할 수 없습니다."

        #### 검증1, 2, 3  통과시 [존재검사시 사용했던 객체]로 삭제
        db.session.delete( target_dept )
        db.session.commit()

        return True, "부서를 삭제했습니다."
```





##### session.delete(객체)시  dept.id를 fk로 가지는 2곳:  Department.id + EmployeeDepartment.department_id에 검사가 걸린다 ( stmt시 안걸림 )

###### 현재: fk nullable=True로, 생성은 parent_id None으로 생성 가능 <-> 삭제시 pk가 fk로서 (나, 및 Many)들의 제약조건에 걸린다. 나의 자식, 나의id를 fk로 안가지고 있어도, 제약조건에 의해 삭제가 안된다.

- `관계칼럼의 자식backref에 cascade='all'`를 줘서, 부모삭제시 다 같이 삭제되거나
- **`FK칼럼  ondelete='SET NULL'  +  관계칼럼 backref에 passive_deletes=True`를 줘서, 부모는 NULL + 자식은 살아남기를 해야한다**
  - **`나 자신은 fk제약조건과 무관하게 삭제허용` +  `자식들의 삭제를 막기` + `개별적으로 자식 존재시 삭제안되게 검증 추가`의 방법으로 방지한다.**

- plan

  ```
  1) 나 자신 삭제시 fk제약조건 발동안하게 함.
  2) 자식은 부모가 None이 될 가능성이 있지만, 자식 가질 경우 나 자신삭제가 불가능하게 검증로직 따로 추가할 예정
  ```

  



###### 검증통과시 삭제는 하긴해야하며, cascade없이 SET NULL되도록 수정하기

1. `db.session.delete( dept ) `만으로 **department.id를 fk로 가지는 `EmployeeDepartment`에서 FK NOT NULL 제약조건에 걸린다.**

   ```sql
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: employee_departments.department_id
   [SQL: UPDATE employee_departments SET pub_date=?, department_id=? WHERE employee_departments.id = ?]
   [parameters: ('2023-02-01 21:08:40.041275', None, 45)]
   (Background on this error at: https://sqlalche.me/e/14/gkpj)
   ```

2. [스택오버플로우](https://stackoverflow.com/questions/34497812/how-to-nullify-childres-foreign-key-when-parent-deleted-using-sqlalchemy)를 참고하면, 

   ```python
   # 기존 문제 있는 코드
   
   class Parent(db.Model):
       __tablename__ = 'parents'
   
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String)
   
   
   class Child(db.Model):
       __tablename__ = 'children'
   
       id = db.Column(db.Integer, primary_key=True)
       parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)
       parent = db.relationship('Parent', backref=db.backref('children', cascade='all,delete'))
       name = db.Column(db.String)
       
   ```

   

   1. `ORM level`에서는 **`fk 칼럼의 ForeignKey('', )에  nullable=True만 추가`하면 끝난다.**

      - 이 때, 바로 밑 `backref주는 관계칼럼`에 **Many에게 자식에게 건네주는 backref( , ) 내부에 `cascade='all, delete'` 등을 `주면 안된다`.**
        - `all`은 save-update, merge, refresh-expire, expunge, delete의 동의어이므로 all, delete는 단순히 all과 동일합니다.

      ```python
      class Child(db.Model):
          __tablename__ = 'children'
      
          id = db.Column(db.Integer, primary_key=True)
          parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=True)
          parent = db.relationship('Parent', backref=db.backref('children'))
          name = db.Column(db.String)
      ```

   2. `DB level`로 주려면 **`fk 칼럼의 ForeignKey('', )에  ondelete='SET NULL'을 추가함`**으로서 `DB에 ON DELETE SET NUL 제약조건`이 추가된다.

      - **사실은 이것은 fk라면 default이다.**
      - **하지만, `자식에게 backref를 주는 관계칼럼에 passive_delete=True or 'all'을 추가로 줘야한다.`**
        - **즉, 관계칼럼의 passive_delelete=True는, 부모의 fk칼럼 정의시 주는 ondelete 행위를 수동적으로 따른다는 뜻이다.**

      ```python
      class Child(db.Model):
          __tablename__ = 'children'
      
          id = db.Column(db.Integer, primary_key=True)
          parent_id = db.Column(db.Integer, db.ForeignKey('parents.id', ondelete='SET NULL'), nullable=True)
          parent = db.relationship('Parent', backref=db.backref('children', passive_deletes=True))
          name = db.Column(db.String)
      ```

      

###### 내 모델에 적용 -> 같이 다지워지는 참사를 방지 + session.delete( 객체 )가 작동하도록 -> 객체의 id를 fk로 가지는 곳에 ondelete='SET NULL' 적용하기

1. **일단 `db.sessin.delete ( new_dept )`를 치면, department.id를 fk로 가지고 있는 `EmployeeDepartment`에서 FK NOT NULL 제약조건이 먼저 걸린다.**

   ```sql
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: employee_departments.department_id
   [SQL: UPDATE employee_departments SET pub_date=?, department_id=? WHERE employee_departments.id = ?]
   [parameters: ('2023-02-01 21:08:40.041275', None, 45)]
   (Background on this error at: https://sqlalche.me/e/14/gkpj)
   ```

2. **`EmployeeDepartment`entity**의 기존과 변경코드

   1. **fk칼럼**에서 **`nullable=False` 제거 후**

      1. **fk칼럼**에서 **db level의 `ForeignKey() 정의부 ondelete='SET NULL'` 추가**
      2. **fk관계칼럼**에서 **`backref에 passive_deletes=True ` 추가**

      ```python
      class EmployeeDepartment(BaseModel):
      	# ...
          # 변경 전
          department_id = Column(Integer, ForeignKey('departments.id'), nullable=False, index=True)
          department = relationship("Department", backref="employee_departments", foreign_keys=[department_id],
      
      
          # 변경 후
          department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), index=True)
      	department = relationship("Department", backref=backref("employee_departments",  passive_deletes=True), foreign_keys=[department_id],
      
      ```

3. **또 에러가 난다. Department자체에 있는 `parent_id` fk 제약조건**

   ```sql
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
   [SQL: DELETE FROM departments WHERE departments.id = ?]
   [parameters: (2,)]
   (Background on this error at: https://sqlalche.me/e/14/gkpj)
   
   ```

4. **`Department`entity**의 기존과 변경코드

   1. 기본적으로 **fk칼럼**에서 **ORM레벨의 `nullable=True`가 붙어있는 체로**
      1. **fk칼럼**에서 **db level의 `ForeignKey() 정의부 ondelete='SET NULL'` 추가**
   2. ORM레벨에서 nullable여부와 상관없이 **`부모삭제시 자식도 같이 삭제하는 cascade='all' 제거`후 **
      1. **fk칼럼**에서 **db level의 `ForeignKey() 정의부 ondelete='SET NULL'` 추가**
      2. **fk관계칼럼**에서 **`backref에 passive_deletes=True ` 추가**

   ```python
   class Department(BaseModel):
       _N = 3
       # ...
       # 변경 전
       parent_id = Column(Integer, ForeignKey('departments.id'), comment="상위 부서 id", nullable=True)  # 5 # parent_id에 fk입히기
   	children = relationship('Department', backref=backref(
           'parent', remote_side=[id], lazy='subquery',
           cascade='all',  # 7
       ), order_by='Department.path')
       
       # 변경 후
       parent_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), comment="상위 부서 id", nullable=True)  # 5 # parent_id에 fk입히기
       children = relationship('Department', backref=backref(
           'parent', remote_side=[id], lazy='subquery',
           # cascade='all',  # 7
           passive_deletes=True,
       ), order_by='Department.path')
   ```

5. **나머지 pk를 fk로 들고 있는 `EmployeeDepartment`에도, `ORM level의 nullable=True`를 필수로 해줘야한다**

   - **DB Level보다 ORM레벨의 `nullable=True`가 더 필수**

   ```python
   class EmployeeDepartment(BaseModel):
       #...
       department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), index=True, nullable=True)
   ```

   

   

     ![56034735-6d3f-440a-8db8-552d3504362a](https://raw.githubusercontent.com/is3js/screenshots/main/56034735-6d3f-440a-8db8-552d3504362a.gif)



##### view - validateDelete 검증 => deleteSelectNode에 axios 추가

- 부서장이나 하위 직원이 존재하면 삭제 불가

  - **현재 leader에는 직접 리더가 없으면 상사가 올라오는 상황이다.**

    - 아래 보이는 사진에서 `leader`는 **상사도 없을 경우 null이다.**

    ![image-20230202002405089](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230202002405089.png)

    - **`has_direct_leader` T/F로 정보를 to_dict에서 추가한다.**

      ```python
      # 부서장 존재 확인용 -> 부서장이 있따면, 부서 전체 직원 - 1을 해서 [순수 부서원 수]만 내려보낸다.
      direct_leader_id = self.get_leader_id()
      if direct_leader_id:
          data['has_direct_leader'] = True
          else:
              data['has_direct_leader'] = False
      ```

      ![image-20230202003030149](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230202003030149.png)

    - **이참에 view에서 부서장 표시도 바꿔준다.**

    ```html
    <!-- 부서장 외 (부서장 제외 직원 + 하위부서장 + 하위직원 수) : all_employee_count-->
    <small v-if="dept.has_direct_leader"> {$ dept.leader.name $}</small>
    <small v-else>(부서장 공석) </small>
    <small v-show="dept.all_employee_count">외 직원 {$ dept.all_employee_count $}명</small>
    ```

    

  - 직원 존재유무는 `employees`의 .length로 알수 있다.

![image-20230202002201146](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230202002201146.png)

​	

###### validateDelete

- TODO였던 검증2에 부서장/ 직원 확인하기

```js
validateDelete() {
    // 삭제 진행 전 검증하기
    const targetDept = this.selectedDept;
    // [검증1] 하위 부서 존재여부
    // 일단 자식없는 node라도 .children는 빈 어레이로 가지고 있음.
    if (targetDept.children && targetDept.children.length) {
        this.toast('하위 부서가 존재할 경우 삭제할 수 없습니다.', 'is-danger')
        return;
    }

    // [검증2] (하위부서X)부서의 직원이 존재할 경우, [있다면 해임시키게 될 건데] confirm받기
    // console.log('targetDept.has_direct_leader >> ', targetDept.has_direct_leader);
    if (targetDept.has_direct_leader ){
        this.toast('부서장이 존재할 경우 삭제할 수 없습니다.', 'is-danger')
        return;
    }
    if (targetDept.employees && targetDept.employees.length > 0){
        this.toast('재직 중인 직원이 존재할 경우 삭제할 수 없습니다.', 'is-danger')
        return;
    }
    // this.confirm('삭제할 경우, 해당 부서원들은 금일부 해임됩니다. 진행하시겠습니까?', async () => await this.deleteSelectedNode() );

    // [검증3] 정말 삭제할 것인지 confirm 받기
    this.confirm('정말 삭제하시겠습니까?', () => this.deleteSelectedNode());
},
```

![image-20230202005757761](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230202005757761.png)

![image-20230202005807962](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230202005807962.png)





###### deleteSelectedNode

```js
deleteSelectedNode() {
    //1. tree VM으로 선택node 삭제
    const targetDept = this.selectedDept;

    // TODO: 서버에 삭제요청 보내기
    const payload = {
        dept_id: targetDept.id
    }
    axios({
        url: '{{ url_for("department.delete") }}',
        method: 'delete',
        data: payload,
        headers: {'Content-type': 'application/json;charset=utf-8'},
    }).then(res => {
        // 통신성공 but 로직 실패(200대 외)
        if (res.status >= 300) {
            this.toast(res.data.message, 'is-danger');
            return;
        }

        // 통신 성공 + (status변경)로직 성공
        //tree에서 해당 node 삭제
        let tree = targetDept._vm.store; // node로부터 전체 tree얻기
        tree.deleteNode(targetDept);

        // console.log('this.treeData >> ', this.treeData); // 연동되어, 해당node만 삭제
        // console.log('this.selectedDept >> ', this.selectedDept);// 유지 + .parent에선 사라진 현재 tree연동됨.

        //2. 선택node보다 더 뒤에 sort를 1칸씩 당긴다.
        const standardSort = targetDept.sort;
        let myParentChildren = targetDept.parent ? targetDept.parent.children : this.treeData;
        // for (const node in myParentChildren) {
        // [조심!] 일반 for in 으로 돌면 -> key값만 도는 것이다.
        for (const node of myParentChildren) {
            // 여기서는 index로 sort를 만들면 안된다. 이미 트리에서 1개가 빠진 상태에서 순회하기 때문
            if (node.sort > standardSort) {
                // console.log(`현재sort${node.sort}를 한칸씩 -1 합니다.`)
                node.sort = node.sort - 1;
            }
        }
        // 3. selected된거 없으니 비워주기
        this.selectedDept = null;

        //4. 변경된 tree를 -> this.depts -> this.initialDepts에 반영
        this.treeUpdated(tree);
        this.initialDepts = this.depts;

        this.toast(res.data.message);

    }).catch(err => {
        console.log(err)
        // 특별히 err에 response가 내려온다면. 거기서 메세지를 꺼내서
        this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');

    }).finally(() => {

    });


},
```







##### route - delete method

- 성공시에도 실패시에도 message만 반환하므로 return문이 1개

```python
@dept_bp.route("/delete", methods=['DELETE'])
def delete():
    dept_info = request.get_json()
    result, message = Department.delete_by_id(dept_info['dept_id'])

    return make_response(dict(message=message))
```





#### Change Sort

##### class method: change_sort(dept_id, after_sort)

```python
    @classmethod
    def change_sort(cls, dept_id, after_sort, before_sort=None):
        # before_sort는 이미 객체에 .sort로 정보가 있기 때문에, 인자로 받을 필요없다.
        # 하지만, 나중에 level별 변화가 발생할 경우, 전 level의 before_sort를 알아야, 그쪽으로 들어갈 수 있다?
        # => 어차피 알게 될 듯.
        with DBConnectionHandler() as db:
            target_dept = db.session.get(cls, dept_id)

            if not target_dept:
                raise ValueError('해당 부서는 존재하지 않습니다.')

            if not before_sort:
                before_sort = target_dept.sort

            if not isinstance(before_sort, int) or not isinstance(after_sort, int):
                raise ValueError('sort가 정수여야 합니다.')

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
```



##### view

- treeChanged는 이미 발생한다.
  - **실패로직에 `this.updateTreeData();`로 덮어쓰기를 다 넣어줘야한다.**
  - 이미 로직은 완성된 상태 route에 반영만 해주면 된다.



##### router

```python
@dept_bp.route("/sort", methods=['PUT'])
def change_sort():
    payload = request.get_json()
    # print(payload)
    # {'dept_id': 1, 'before_sort': 2, 'after_sort': 1}

    result, message = Department.change_sort(payload['dept_id'], payload['after_sort'])
    
    return make_response(dict(message=message))

```



#### Change Name, Change status

###### validate의 return으로 끝내기 외, 통신실패/로직실패 등에서 tree 롤백해주기 by this.updateTreeData()

- validate에서 실패시 아예 시도안하지만, **통신 실패에도 롤백**





##### change_name router

```python
@dept_bp.route("/name", methods=['PUT'])
def change_name():
    payload = request.get_json()
    # print(payload)
    # {'dept_id': 1, 'target_name': '병원장2'}

    with DBConnectionHandler() as db:
        try:
            exists_name = db.session.scalar(
                exists()
                .where(Department.name == payload['target_name'])
                .select()
            )
            if exists_name:
                return make_response(dict(message='이미 해당 이름의 부서가 존재합니다.'), 409)

            target_dept = db.session.get(Department, payload['dept_id'])
            target_dept.name = payload['target_name']

            db.session.commit()

            return make_response(dict(message='부서 이름 변경을 성공했습니다.'), 200)

        except:
            db.session.rollback()
            return make_response(dict(message='부서 이름 변경에 실패했습니다.'), 409)
```



##### change_status 검증추가 => 부서장OR직원 존재할경우 불가는 valiate => delete와 동일해서 복붙수정

```js
// status 변화
validateStatusChange(dept) {
    // TODO: [검증1] (하위부서X)부서의 직원이 존재할 경우, [있다면 해임시키게 될 건데] confirm받기
    // this.confirm('비활성화할 경우, 해당 부서원들은 금일부 해임됩니다. 진행하시겠습니까?', async () => await this.deleteSelectedNode() );
    // => delete와 같은 로직이라 복붙함.
    if (dept.has_direct_leader) {
        this.toast('부서장이 존재할 경우 비활성화 할 수 없습니다.', 'is-danger')
        return;
    }
    if (dept.employees && dept.employees.length > 0) {
        this.toast('재직 중인 직원이 존재할 경우 비활성화 할 수 없습니다.', 'is-danger')
        return;
    }

    // 비활성 -> 활성 경우, 그냥 토글한다.
    if (!dept.status) {
        this.changeStatus(dept);
        return;
    }
    // [검증2] 활성상태일때만, 정말 비할성화 것인지 confirm 받기
    this.confirm('정말 비활성화하시겠습니까??', () => this.changeStatus(dept));
},

```



##### status변경은 재직중 직원 확인 로직이 따로 들어간다 + tree가 안바뀌고 통신성공시만 토글하여, 롤백 안넣어줘도 된다. => 대신 로직실패를 명확하게 따로 return해줘야한다.



```python
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
```



```python
@dept_bp.route("/status", methods=['PUT'])
def change_status():
    payload = request.get_json()
    # print(payload)
    # {'dept_id': 1}
    # TODO : dept status 변경
    result, message = Department.change_status(payload['dept_id'])

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)

```



![image-20230202223018552](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230202223018552.png)







#### Change Sort cross level

##### method 따로파기. 로직이 다르다. (change_sort_cross_level)

![image-20230203004528620](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230203004528620.png)

1. 검증
   1. 대상부서 존재 / **`같은 부모아래 이동이 아님`** / **`하위부서로는 이동못하도록`**
2. 로직 : dept_id, **after_parent_id**, after_sort
   1. 대상부서 + 자식들 미리 select
   2. `이동 전` 같은 부모 아래 나보다 sort가 뒤에있는 것들 미리 select
   3. `이동 후` 부모들 아래 나보다 sort가 **같거나** 뒤에있는 것들 미리 **역순** select
   4. 이동 전 select들 위로 1칸 올려주기 update
   5. 이동 후 select들 아래로 1칸 (역순) 내려주기 update
   6. `대상부서`는 **길이가 달라지는 new_path**를 가지며 update되므로
      1. **대상부서만 따로 `.sort` 변경  +  `.parent_id` 변경**
         - 같은부모아래 변경시에는 child와 같이 변경했다.
      2. **parent_id -> `parent객체 찾아서 -> parent.path -> 새로운 path prefix로 취급`**
      3. **대상부서의 `.path 변경 전, before_path로 미리 빼놓는다.`**
         - **child 업뎃시 `대상부서의 before_path의 길이만큼, 앞에를 잘라내야한다`**
      4. **대상부서의 자식들만 순회하며, new_paht + before_부모path길이만큼 짤라낸 자신만의path**로 업데이트한다.

```python
    @classmethod
    def change_sort_cross_level(cls, dept_id, after_parent_id, after_sort, before_level=None, before_sort=None):
        with DBConnectionHandler() as db:
            try:
                target_dept: Department = db.session.get(cls, dept_id)

                if not target_dept:
                    raise ValueError('해당 부서는 존재하지 않습니다.')

                if target_dept.parent_id == after_parent_id:
                    raise ValueError('같은 부서내 이동은 change_sort를 이용. 로직이 다름(제거/추가가 아닌 삽입/삭제)')

                if target_dept.parent_id in target_dept.get_self_and_children_id_list():
                    raise ValueError('하위 부서로 이동은 불가능 합니다.')

                if not before_sort:
                    before_sort = target_dept.sort

                if not before_level:
                    before_level = target_dept.level

                if not isinstance(after_sort, int) or not isinstance(before_level, int) or not isinstance(before_sort, int):
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
```





##### view에서, dept_id + after_sort 이외에 after_level + parent_id까지 같이보내면, cross_level이다

###### node._vm.level에는, 바뀐후의 level이 안찍히는 버그 -> node.parent.level로, 바뀐부모의 level필드로 +1을 시켜 현재 level을 알아내자.

1. 동일부모 검증을 axios내부로 보내서 payload를 다르게 보낸다

   1. **payload에 `is_cross_level = false;`플래그를 만들고, 동일부모아닐 때, 추가필드를 채워넣는 식으로 구현**
   2. **이 때, `node._vm.level`로 보면, 변경후 level이 제대로 안나와서 `node.parent._vm.data`속 `.level필드`를 사용하여 기존에 적힌 부모의 level을 활용한다**
   3. **parent가 root인지 아닌지 확인하는 필드가 애매하므로 `node.parent(vm).isRoot`를 활용해서 root가 아닐 경우, 필드데이터를 이용해 `id, level + 1`을 빼온다.**

   ```js
   treeChanged(node, tree) {
   
       console.log('treeChanged----') // 제자리에 둘 땐 호출되지 않는다.
   
       let payload = {
           dept_id: node.id,
           after_sort: node.parent.children.indexOf(node) + 1,
   
           is_cross_level: false, // cross_level인지 아닌지 구분하는 flag 생성
           after_parent_id: null,
       }
   
       // 동일부모가 아닌 경우 => cross level chang sort로서, 추가필드르 채워준다.
       if (!this.validateSameParent(node)) {
           payload.is_cross_level = true;
           if (!node.parent.isRoot) {
               payload.after_parent_id = node.parent._vm.data.id;
           } else {
               payload.after_parent_id = null;
           }
       }
   ```

   

##### backend에서는 is_cross_level로 서로 다른 메서드를 호출한다.

```python
@dept_bp.route("/sort", methods=['PUT'])
def change_sort():
    payload = request.get_json()
    # print(payload)
    # is_cross_level Flag를 확인해서 서로 다른 메서드를 호출한다.
    ## cross_level인 경우
    # {'dept_id': 13, 'after_sort': 1, 'is_cross_level': True, 'after_parent_id': None}
    ## 같은 부모인 경우
    # {'dept_id': 6, 'after_sort': 2, 'is_cross_level': False, 'after_parent_id': None}

```

- 메서드들에서 필요없는 before_sort, before_level은 인자에서 제거해준다.

```python
@dept_bp.route("/sort", methods=['PUT'])
def change_sort():
    payload = request.get_json()
    # print(payload)
    # is_cross_level Flag를 확인해서 서로 다른 메서드를 호출한다.
    # {'dept_id': 13, 'after_sort': 1, 'is_cross_level': True, 'after_parent_id': None}
    # {'dept_id': 6, 'after_sort': 2, 'is_cross_level': False, 'after_parent_id': None}

    if payload['is_cross_level']:
        result, message = Department.change_sort_cross_level(dept_id=payload['dept_id'], after_parent_id=payload['after_parent_id'], after_sort=payload['after_sort'])
    else:
        result, message = Department.change_sort(dept_id=payload['dept_id'], after_sort=payload['after_sort'])

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)

```





##### view에서 cross_level까지 다 바꾸지말고, 성공시 db내용을 this.getDepts로 받아오도록 jinja route외 GET route를 만들어보자.

 

- route부터

  ```python
  @dept_bp.route("/all", methods=['GET'])
  def all():
      tree = Department.get_all_tree(with_inactive=True)
  
      if tree:
          return make_response(dict(tree=tree, message='서버에서 데이터를 성공적으로 받았습니다.'), 200)
      else:
          return make_response(dict(message='데이터 전송 실패'), 409)
  ```

  ![image-20230203022943143](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230203022943143.png)



#####  view에서, treeChanged(순서변경) 성공시 this.getUpdatedDepts() 호출하기

```js
axios({
    url: '{{ url_for("department.change_sort") }}',
    method: 'put',
    data: payload,
    headers: {'Content-type': 'application/json;charset=utf-8'},
}).then(res => {
    // 통신성공 but 로직 실패(200대 외) -> tree되돌려야함 by this.updateTreeData();
    // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
    if (res.status >= 300) {
        this.toast(res.data.message)
        // [cancel 2] 통신성공 BUT 로직실패  => tree변경 취소(기존 this.depts -> this.treeData)
        this.updateTreeData(); // 변경된 tree 롤백
        return;
    }

    this.getUpdatedDepts();

    this.toast(res.data.message)
}).catch(err => {
    // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
    console.log(err)
    this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
    // [cancel 3] 통신실패  => tree변경 취소(기존 this.depts -> this.treeData)
    this.updateTreeData();

}).finally(() => {
});

```



###### 아니다. tree는 이미 changed되었으니, 새로 this.treeData받지말고, this.depts와 this.initial만 수정하자. 실패시 롤백만

```js
// this.getUpdatedDepts();
this.treeUpdated(tree); // tree 자체 ----getPureData------> this.depts
this.initialDepts = this.depts; // this.depts -------> this.initialDepts

```



#### 선택한 부서정보 + 재직인원 나타내기

![image-20230203221633511](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230203221633511.png)

```html
<!-- bulma list css -->
<link href="https://cdn.jsdelivr.net/npm/bulma-list/css/bulma-list.css" rel="stylesheet"/>
```



##### 선택된 부서 정보 html

- [bulma list](https://bluefantail.github.io/bulma-list/)

![image-20230204200730069](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230204200730069.png)

1. columns는 flex라서 column들을 가로배치하지만 **column내부는 block요소다**
   1. `magin auto`로 가운데 정렬한다.
2. column  block안에서 다시 가로배치하려면, `container` + `is-flex` + `is-justify-content-center`로 가운데 정렬하는 가로배치를 만든다.
3. 직원 list는 bulma list css를 활용한다
   1. 각 list의 시작을 세로배치하기 위해 `container` + `is-flex` + `is-flex-direction-column`으로 만들어놓고, 가운데 정렬하기 위해 `is-align-items-center`로 만든다.

```html
<!-- 부서 상세정보       -->
<!-- block요소는 margin auto로 가운데정렬한다.       -->
<div class="column mx-auto mt-4">
    <!-- 내부 요소들을 가로배치하려면 또다시 is-inline-flex or is-flex로 가로 배치 -->
    <!--  flex: 내부요소들이 가로배치 / inline-flex: 컨테이너들도 가로 배치 -->
    <!-- https://wooncloud.tistory.com/10-->

    <div class="container is-flex is-justify-content-center">
        <!-- 직원 검색  -->
        <b-field
                 custom-class="is-small"
                 label="직원 검색"
                 label-position="on-border"
                 >
            <b-autocomplete
                            size="is-small"
                            rounded
                            v-model="name"
                            :data="filteredDataArray"
                            placeholder="e.g. 홍길동"
                            icon="account"
                            clearable
                            @select="option => selected = option">
                <template #empty>
                    No results found
                </template>
            </b-autocomplete>
        </b-field>
        <!-- 부서장 여부  -->
        <b-field class="pt-1 ml-4">
            <b-checkbox size="is-small">부서장</b-checkbox>

        </b-field>
        <!--                    v-if="selectedDept"-->
        <b-button class="is-primary is-light is-rounded is-pulled-right ml-2"
                  size="is-small"
                  @click="validateDelete"
                  >
            <span class="icon">
                <i class="mdi mdi-plus-thick mr-1"> </i>
            </span>
            직원 추가
        </b-button>
    </div>

    <div class="container has-text-centered has-background-light mt-4"
         style="border-radius: 5%; width: 150px;">

        <!--                     :class="getColorToLevelAndSort(item.level, item.parent_sort, item.sort)"-->
        <div class="list-item-title mb-1 py-1 tag has-text-centered is-block is-size-7"
             >
            부서명
        </div>
        <!-- root에서는 상사 leader가 없을 수 있기 때문에 조건문 걸어줘야 한다. -->
        <figure class="image is-inline-block py-0 "
                style="height: 40px; width: 40px;margin-right: -2px;">
            <!--                         :src="item.leader ? '../uploads/'+item.leader.avatar : '/static/img/user/default_avatar.svg'"-->
            <!--                         :alt="item.leader ? item.leader.name : ''"-->
            <img class="is-rounded has-background-white" style="height: 40px; width: 100%;"
                 >
        </figure>

        <div class="is-size-7 pb-1">
            <small>직위</small>
            </br>
        <span class="has-text-weight-bold"
              style="color:black">부서장</span>
    </div>
</div>

<div class="container has-text-centered mt-2">
    <!-- 총괄직원은 .children가 있는 상위부서일 때만 나타나도록 -->
    <!--                     :class="getColorToLevelAndSort(item.level, item.parent_sort, item.sort)"-->
    <!--                     v-if="item.children"-->
    <div class="tag is-rounded"
         >
        <small>
            총괄 직원 : 0
        </small>
    </div>
    <div class="tag is-rounded"
         >
        <small>
            직원 수 : 0
        </small>
    </div>
</div>


<!--  직원 list          -->
<!--  flex로서 세로 배치(is-flex-direction-column) 한다면, 가운데 정렬은 is-align-items-center로 해야한다 -->
<div class="container is-flex is-flex-direction-column is-align-items-center mt-2 ">
    <div class="list has-visible-pointer-controls has-hoverable-list-items">
        <div class="list-item">
            <div class="list-item-image is-primary">
                <figure class="image"
                        style="height: 30px; width: 30px;">
                    <!--                                 :src="item.leader ? '../uploads/'+item.leader.avatar : '/static/img/user/default_avatar.svg'"-->
                    <!--                                 :alt="item.leader ? item.leader.name : ''"-->
                    <img class="is-rounded has-background-white" style="height: 30px; width: 100%;"
                         src="/static/img/user/default_avatar.svg"
                         >
                </figure>
            </div>
            <div class="list-item-content is-size-7">
                <div class="list-item-title ">List item</div>
                <div class="list-item-description ">List item description</div>
            </div>
            <div class="list-item-controls ml-4 is-size-7">
                <div class="tags is-right">
                    <a href=""
                       class="tag is-warning is-light">
                        휴직
                    </a>
                    <a href=""
                       class="tag is-danger is-light">
                        해임
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
</div>
```



#### b-autocomplete 데이터 연결하기

1. data변수들 선언하기

   1. `입력값`을 받아줄 **v-model** : `employeeName = '',`

   2. 차후 `검색된 obj들`을 받아놓을 **:data용** 변수 : `employees=[],`

   3. 검색된 obj중에 `선택된 obj` : `selectedEmployee: null`,

      ```js
      // 직원 검색 autocomplete
      employeeName: '', // 입력될 값 -> v-model
      employees: [], // 입력된 값에 따라 검색 값 -> :data or 필터링 -> field=특정필드값만 나타내기 가능
      selectedEmployee: null, // <- 선택된 값
      ```

2. b-autocomplete에 설정하고, 화면에 찍어보기

   ```html
   <!-- 직원 검색  -->
   <p> employeeName : {$ employeeName $}<br/>
       employees : {$ employees $}<br/>
       selectedEmployee : {$ selectedEmployee $}<br/>
   </p>
   <b-field
            custom-class="is-small"
            label="직원 검색"
            label-position="on-border"
            >
       <b-autocomplete
                       size="is-small"
                       rounded
                       icon="account"
                       placeholder="e.g. 홍길동"
                       clearable
                       v-model="employeeName"
                       :data="employees"
                       @select="option => selectedEmployee = option"
                       >
   ```

   ![image-20230205005730845](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205005730845.png)



4. @input대신 `@typing`으로 글자인식해서 메서드호출하기

   ```js
   @typing="toast(employeeName);"
   ```

   ![image-20230205010338368](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205010338368.png)

   - 입력에 대해 호출될 메서드 `getEmployees` 생성
     - 통신실패시마다 데이터 `this.employees`를 비워준다.
     - 시작과 동시에 loading flag를, 성공/실패 상관없이 finally에서 flag를 꺼준다.
     - backend로는 trim한 값을 넘겨준다.
     - **get요청시 쿼리스트링을 `params`옵션으로 obj를 넘길 수 있다.**
       - 계층이 깊어지면 따로 처리해줘야한다.

   ```js
   @typing="getEmployees"
   :loading="isFetching"
   ```

   ```js
   // autocomplte시 타이핑 name으로 get 요청
   getEmployees(name) {
       console.log('getEmployees====')
   
       this.isFetching = true;
   
       const myParams = {
           emp_name: name.trim()
       }
   
       axios({
           url: '{{ url_for("department.employees") }}',
           method: 'get',
           params: myParams,
           headers: {'Content-type': 'application/json;charset=utf-8'},
       }).then(res => {
           // 통신성공 but 로직 실패(200대 외)
           if (res.status >= 300) {
               this.toast(res.data.message)
               this.employees = [];
               return;
           }
   
           // console.log('res.data >> ', res.data);
           // this.toast(res.data.employees)
           // this.toast(res.data.message)
   
           this.employees = res.data.employees;
   
       }).catch(err => {
           // 통신실패
           console.log(err)
           this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
           this.employees = [];
       }).finally(() => {
           this.isFetching = false;
       });
   },
   ```

   

##### GET router + request.args

- params or querystring으로 건너온 것은 `request.args.get()` 혹은 **`request.args.to_dict()`로 만든 뒤 dict에서 빼내기**

- jsonify로 데이터를 건네줘야한다.

  - **employee를 like 필터링으로 골라낸 뒤, todict까지 해주는 class method를 만들어보자.**

  

```python
@classmethod
def get_by_name_as_dict(cls, name):

    with DBConnectionHandler() as db:
        employees = db.session.scalars(
            select(Employee)
            .where(Employee.job_status != JobStatusType.퇴사)
            .where(Employee.name.like('%' + name + '%'))
            .order_by(Employee.join_date)
        ).all()

        # view에 보내기 전에 처리해주기
        results = []
        for emp in employees:
            emp_dict = emp.to_dict()
            ## 민감정보 삭제
            del emp_dict['birth']
            ## value -> enum(valuee)-> .name으로 변환
            # emp_dict['job_status'] = JobStatusType[emp_dict['job_status']].name
            #### job_status에는 이미 enum이 들어가 있다.
            emp_dict['job_status'] = emp_dict['job_status'].name

            results.append( emp_dict)

        return results

```



```python
@dept_bp.route("/employees", methods=['GET'])
def employees():
    # args = request.args # ImmutableMultiDict([('myParams[emp_name]', '조ㅈ')])
    params = request.args.to_dict()

    employees = Employee.get_by_name_as_dict(params.get('emp_name'))

    # return jsonify(employees=employees, message='직원 조회 성공')
    return jsonify(employees=employees)

```





![image-20230205025108174](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205025108174.png)



```python
@dept_bp.route("/employees", methods=['GET'])
def employees():
    # args = request.args # ImmutableMultiDict([('myParams[emp_name]', '조ㅈ')])
    params = request.args.to_dict()

    employees = Employee.get_by_name_as_dict(params.get('emp_name'))

    # return jsonify(employees=employees, message='직원 조회 성공')
    return jsonify(employees=employees)

```





##### b-autocomplete에 group-field 추가하여, 그룹별로 보이게 하기

```html
<b-autocomplete
                size="is-small"
                rounded
                icon="account"
                placeholder="빈칸 입력시 전체직원"
                clearable
                v-model="employeeName"
                :data="employees"
                @select="option => selectedEmployee = option"
                @typing="getEmployees"
                :loading="isFetching"
                field="name"
                group-field="job_status"
                >
```

![image-20230205044656807](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205044656807.png)





###### 부서장, 직원 추가버튼은 selectedEmployee가 있을대만 활성화

- b-checkbox는 `.native`붙여야 적용됨.

```html
<b-checkbox size="is-small"
            :disabled.navite="!selectedEmployee"
            >

    <b-button class="is-primary is-light is-rounded is-pulled-right ml-2"
              size="is-small"
              @click="validateDelete"
              :disabled="!selectedEmployee"
              >
```

![image-20230205045115240](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205045115240.png)







#### 부서 선택시에만 부서정보가 나타나도록 수정

```html
<!-- 부서 상세정보       -->
<!-- block요소는 margin auto로 가운데정렬한다.       -->
<div class="column mx-auto mt-4"
     v-if="selectedDept"
     >
```

```html
<div class="container has-text-centered is-bordered has-background-light mt-4"
     style="border-radius: 5%; width: 150px;">
    <div class="list-item-title mb-1 py-1 tag has-text-centered is-block is-size-6"
         :class="getTextColorToLevelAndSort(selectedDept.level, selectedDept.parent_sort, selectedDept.sort)"
         >
        {$ selectedDept.name $}
    </div>
    <!-- root에서는 상사 leader가 없을 수 있기 때문에 조건문 걸어줘야 한다. -->
    <figure class="image is-inline-block py-0 "
            style="height: 50px; width: 50px;margin-right: -2px;">
        <img class="is-rounded has-background-white" style="height: 50px; width: 100%;"
             :src="selectedDept.has_direct_leader ? '../uploads/' + selectedDept.leader.avatar : '/static/img/user/default_avatar.svg'"
             :alt="selectedDept.has_direct_leader ? selectedDept.leader.name : ''"
             >
    </figure>

    <div class="is-size-7 pb-1">
        <small>{$ selectedDept.has_direct_leader ? selectedDept.leader.position : '' $}</small>
        </br>
    <span class="has-text-weight-bold"
          style="color:black">
        {$ selectedDept.has_direct_leader ? selectedDept.leader.name : '부서장 공석' $}
    </span>
</div>
</div>
```

```html
<div class="container has-text-centered mt-2">
    <!-- 총괄직원은 .children가 있는 상위부서일 때만 나타나도록 -->
    <div class="tag is-rounded"
         :class="getTextColorToLevelAndSort(selectedDept.level, selectedDept.parent_sort, selectedDept.sort)"
         v-if="selectedDept.children.length"
         >
        <small>
            총괄 직원 : {$ selectedDept.all_employee_count $}
        </small>
    </div>
    <div class="tag is-rounded"
         :class="getTextColorToLevelAndSort(selectedDept.level, selectedDept.parent_sort, selectedDept.sort)"
         >
        <small>
            직원 수 : {$ selectedDept.employee_count $}
        </small>
    </div>
</div>
```

##### employees 돌리기

![image-20230205171412701](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205171412701.png)

![image-20230205174543457](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205174543457.png)

![image-20230205175453378](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205175453378.png)

#### 직원 추가/삭제

##### view에서 일단push로 추가하기

```html
<b-button class="is-primary is-light is-rounded is-pulled-right ml-2"
          size="is-small"
          @click="addEmployee"
          :disabled="!selectedEmployee"
          >
```



- **`this.selectedDepts`에 `.employees`가 null일때는 빈 배열을 생성해서 `서버로부터 받은 employee정보 중 1개인 this.selectedEmployee`를 push해보자.**

  ```js
  addEmployee() {
      console.log(this.selectedDept)
  
      console.log(this.selectedEmployee)
  
      if (!this.selectedDept.employees) {
          this.selectedDept.employees = []
      }
      this.selectedDept.employees.push(this.selectedEmployee);
  
  },
  ```

  ![image-20230205221507546](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205221507546.png)



##### 선택한 직원 vs  push될 소속된 직원 정보의 괴리 확인하기

- 원래 각 부서마다 속해있는 `employees`

  ![image-20230205221545645](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205221545645.png)

- **autocomplete로 선택된 직원 `this.selectedEmployee`**

  ![image-20230205221625638](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205221625638.png)



- **직원 추가를 통해, 새로운 부서를 소속시키고, 빠진 `id` + `avatar` + `position`까지 `추가된 직원 정보에 포함`된 것을 받아서 push해야한다.**

  - 이렇게 push한다고해서, tree와는 연동되진 않음.

    ![image-20230205221846139](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205221846139.png)





##### axios로 보내서, 직원을 부서에 취임시키고, 필요한정보를 받아와서 push하기

- 일단 autocomplete용 to_dict에서 삭제한 id 복구하기

  ```python
  def to_dict(self):
      d = super().to_dict()
      del d['add_date']  # base공통칼럼을 제외해야 keyword가 안겹친다
      del d['pub_date']
      # del d['user']  # 관계필드는 굳이 필요없다. -> inspect안써서 더이상 관계필드 조홰 안한다.
      # del d['id']
      return d
  ```

  

- isLoading도 diabled 조건 추가

  ```html
  <b-button class="is-primary is-light is-rounded is-pulled-right ml-2"
            size="is-small"
            :disabled="!selectedEmployee || isLoading"
            @click="addEmployee"
            >
  ```

- 직원의 부서변경에 필요한 정보 부서변경 route에서 확인하기

  - **current_dept_id는 None으로 사용해서 `항상 부서 추가 상황`으로 사용하고**
  - **target_date는 route에서 today를 사용하자.**

  ```python
  employee.change_department(current_dept_id, after_dept_id, as_leader, target_date)
  ```

- checkbox의 v-model value를 `asLeader`변수 선언해서 사용하기

  ```html
  <b-checkbox size="is-small"
              :disabled.navite="!selectedEmployee"
              v-model="asLeader"
              >
  ```

  ```js
  asLeader: false, // 직원 추가시 부서장 여부
  ```

  





- addEmployee

  ```js
  addEmployee() {
      this.isLoading = true;
  
      let payload = {
          emp_id: this.selectedEmployee.id,
          after_dept_id: this.selectedDept.id,
          as_leader: this.asLeader,
      }
      console.log('payload >> ', payload);
  
      axios({
          url: '{{ url_for("department.add_employee") }}',
          method: 'post',
          data: payload,
          headers: {'Content-type': 'application/json;charset=utf-8'},
      }).then(res => {
          // 통신성공 but 로직 실패(200대 외)
          if (res.status >= 300) {
              this.toast(res.data.message)
              // [cancel 2] 통신성공 BUT 로직실패  => tree변경 취소(기존 this.depts -> this.treeData)
              // this.updateTreeData(); // 변경된 tree 롤백
              return;
          }
  
          // 통신 성공 + (DB 순서변경)로직 성공
          // 현재 선택된 부서에 employees에 직원 추가
          console.log('res.data.new_emp >> ', res.data.new_emp);
          if (!this.selectedDept.employees) {
              this.selectedDept.employees = []
          }
          // this.selectedDept.employees.push(this.selectedEmployee);
  
          this.toast(res.data.message);
          // this.treeUpdated(tree); // tree 자체 ----getPureData------> this.depts
          // this.initialDepts = this.depts; // this.depts -------> this.initialDepts
  
      }).catch(err => {
          console.log(err)
          this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
          // [cancel 3] 통신실패  => tree변경 취소(기존 this.depts -> this.treeData)
          // this.updateTreeData();
  
      }).finally(() => {
          this.isLoading = false;
          this.asLeader = false;
      });
  
  
  },
  
  ```

  

- route

  ```python
  @dept_bp.route("/employees/add", methods=['POST'])
  def add_employee():
      payload = request.get_json()
      # print(payload)
      # {'emp_id': 16, 'after_dept_id': 16, 'as_leader': False}
      employee = Employee.get_by_id(payload['emp_id'])
  
      result, message = employee.change_department(None, payload['after_dept_id'], payload['as_leader'], datetime.date.today())
  
      if result:
          position = employee.get_position_by_dept_id(payload['after_dept_id'])
  
          new_emp = {
              'id': employee.id,
              'name': employee.name,
              'job_status': employee.job_status,
              'avatar': employee.user.avatar,
              'position': position,
          }
          return make_response(dict(new_emp=new_emp, message=message), 200)
      else:
          return make_response(dict(message=message), 409)
  ```

  ![image-20230205232107930](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230205232107930.png)

- 받은 정보를 push

  ```js
  if (!this.selectedDept.employees) {
      this.selectedDept.employees = []
  }
  this.selectedDept.employees.push(res.data.new_emp);
  ```

- **받은 정보 중에 재직상태는 한글로 변환해서 넣기**

  ```python
  new_emp = {
              'id': employee.id,
              'name': employee.name,
              'job_status': employee.job_status.name, # enum의 name
              'avatar': employee.user.avatar,
              'position': position,
          }
  ```

  

#### 해임 view에서 제거 -> route까지 처리하기



##### view에서 employees 해임시 1개씩 삭제하기 by array.findIndex

```html
<a href="#"
   class="tag is-danger is-light"
   @click="dismissEmployee(employee.id)"
   >
    해임
</a>
```

- 배열`.findIndex ( 함수형 => return )`으로 **return이 true인 것(obj)의 index를 찾아낸다.**
  - **배열`.splice( 시작idex, 1칸)`으로 해당 원소를 제거할 수 있다.**

```js
dismissEmployee(emp_id) {
    console.log('this.selectedDept.employees >> ', this.selectedDept.employees);
    let targetIndex = this.selectedDept.employees.findIndex(employee => {
        return employee.id === emp_id
    });
    console.log('targetIndex >> ', targetIndex);
    if (targetIndex > -1) {
        this.selectedDept.employees.splice(targetIndex, 1);
    }
    console.log('this.selectedDept.employees >> ', this.selectedDept.employees);
}
```

![image-20230206004831323](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206004831323.png)





##### axios 통신 성공시 제거

- 부서를 제거하려면 `emp_id`에 대해, `current_dept_id` 가 가고 after_dept_id는 None이 되어야한다.
  - as_leader는 필요없고? target_date도 백엔드해서 처리한다.



```js
dismissEmployee(emp_id) {
    this.isLoading = true;

    let payload = {
        emp_id: emp_id,
        current_dept_id: this.selectedDept.id,
    }
    console.log('payload >> ', payload);

    axios({
        url: '{{ url_for("department.dismiss_employee") }}',
        method: 'post',
        data: payload,
        headers: {'Content-type': 'application/json;charset=utf-8'},
    }).then(res => {
        // 통신성공 but 로직 실패(200대 외)
        if (res.status >= 300) {
            this.toast(res.data.message)
            // [cancel 2] 통신성공 BUT 로직실패  => tree변경 취소(기존 this.depts -> this.treeData)
            // this.updateTreeData(); // 변경된 tree 롤백
            return;
        }

        // 통신 성공 + (DB 순서변경)로직 성공
        // 현재 선택된 부서에 employees를 해임(부서제거)
        let targetIndex = this.selectedDept.employees.findIndex(employee => {
            return employee.id === emp_id
        });
        if (targetIndex > -1) {
            this.selectedDept.employees.splice(targetIndex, 1);
        }


        this.toast(res.data.message);
        // this.treeUpdated(tree); // tree 자체 ----getPureData------> this.depts
        // this.initialDepts = this.depts; // this.depts -------> this.initialDepts

    }).catch(err => {
        console.log(err)
        this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
        // [cancel 3] 통신실패  => tree변경 취소(기존 this.depts -> this.treeData)
        // this.updateTreeData();

    }).finally(() => {
        this.isLoading = false;
    });


},
```

```python
@dept_bp.route("/employees/dismiss", methods=['POST'])
def dismiss_employee():
    payload = request.get_json()
    # print(payload)
    employee = Employee.get_by_id(payload['emp_id'])

    result, message = employee.change_department(
        current_dept_id=payload['current_dept_id'],
        after_dept_id=None,
        as_leader=None,
        target_date=datetime.date.today()
    )

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)

```



#### 부서장 해임 => optional 인자 추가해서 처리하기

- this.selectedDepts.employees와 달리 `this.selectedDept.leader`에 속해있기 때문에 해임시 로직이 다르다.
  - axios 요청로직은 같다.


##### html

- 해임 이후 .leader가 null이 될 수 있끼 때문에 .name, .position에 추가조건을 걸어준다.

```html
<!-- root에서는 상사 leader가 없을 수 있기 때문에 조건문 걸어줘야 한다. -->
<figure class="image is-inline-block py-0 "
        style="height: 50px; width: 50px;margin-right: -2px;">
    <img class="is-rounded has-background-white" style="height: 50px; width: 100%;"
         :src="selectedDept.has_direct_leader && selectedDept.leader ? '../uploads/' + selectedDept.leader.avatar : '/static/img/user/default_avatar.svg'"
         :alt="selectedDept.has_direct_leader && selectedDept.leader ? selectedDept.leader.name : ''"
         >
</figure>

<div class="pb-1 is-size-7">
    <small>{$ selectedDept.has_direct_leader && selectedDept.leader ? selectedDept.leader.position : '' $}</small>
    <br/>
    <span class="has-text-weight-bold"
          style="color:black">
        {$ selectedDept.has_direct_leader && selectedDept.leader ? selectedDept.leader.name : '부서장 공석' $}
    </span>
    <br/>
    <a
       v-if="selectedDept.has_direct_leader && selectedDept.leader"
       class="tag is-danger is-light mt-1"
       @click.prevent ="dismissEmployee(selectedDept.leader.id, isLeader = true)">
        <small>해임</small>
    </a>
</div>
```

![image-20230206024049227](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206024049227.png)



- leader를 null로 채움과 동시에 **`this.selectedDept.has_direct_leader = false;`까지 처리해주자.**

```js
dismissEmployee(emp_id, isLeader = false) {
    
   // ...
    
    // 통신 성공 + (DB 순서변경)로직 성공
    // 현재 선택된 부서에 employees를 해임(부서제거)
    // isLeader 여부에 따라, 다르게 처리
    // 1) 직원 해임
    if(!isLeader) {
        let targetIndex = this.selectedDept.employees.findIndex(employee => {
            return employee.id === emp_id
        });
        if (targetIndex > -1) {
            this.selectedDept.employees.splice(targetIndex, 1);
        }
    } else {
        //2) 리더 해임
        this.selectedDept.leader = null;
        this.selectedDept.has_direct_leader = false;
    }

```



- 리더정보도 왓다갔다하니, tree정보에서 출력안하기

  ![image-20230206025159403](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206025159403.png)



#### 부서장 직원추가시, route에서 leader양식에 맞게 받아서 넣어주기

```js
// 1) 직원 추가
if (!this.asLeader) {
    if (!this.selectedDept.employees) {
        this.selectedDept.employees = []
    }
    this.selectedDept.employees.push(res.data.new_emp);
} else {
    // 2) 부서장 추가
    this.selectedDept.has_direct_leader = true;
    this.selectedDept.leader = res.data.new_emp;
}
```





#### 휴직/복직 처리하기

- `change_job_status(cls, emp_id: int, job_status: int, target_date)`를 활용할 것이므로

  - emp_id와 변경할 job_status만 건네주면 된다.

    ```python
    class JobStatusType(enum.IntEnum):
        대기 = 0
        재직 = 1
        휴직 = 2
        퇴사 = 3
    ```

- front에서는 .job_status에 문자열 상태가 있으며, 반대의 문자열을 건네서, payload에서 반대 int를 건네준다.

  ```html
  <a href=""
     class="tag is-warning is-light"
     v-if="employee.job_status === '재직' "
     @click.prevent="changeJobStatus(employee.id, '휴직')"
     >
      휴직
  </a>
  <a href=""
     class="tag is-success is-light"
     v-else
     @click.prevent="changeJobStatus(employee.id, '복직')"
     >
      복직
  </a>
  ```

- **복직일 때, 성공하면, 재직상태로 변경해서 넣어줘야한다.**

  ```js
  // 통신 성공 + (DB 순서변경)로직 성공
  // -> 객체를 받았을 때, 필드변경 연동 확인 됨
  // => 복직이 target_status일 땐, 재직으로 변경해서 넣어주기
  if (target_status === '복직') target_status = '재직';
  emp.job_status = target_status;
  ```

  



##### js changeJobStatus 메서드

```js
changeJobStatus(emp, target_status){
    let job_status = 1;
    if (target_status === '휴직' ) {
        job_status = 2;
    }

    let payload = {
        emp_id: emp.id,
        job_status: job_status,
    }
    // console.log('payload >> ', payload);

    axios({
        url: '{{ url_for("department.change_employee_job_status") }}',
        method: 'put',
        data: payload,
        headers: {'Content-type': 'application/json;charset=utf-8'},
    }).then(res => {
        // 통신성공 but 로직 실패(200대 외)
        if (res.status >= 300) {
            this.toast(res.data.message)
            // [cancel 2] 통신성공 BUT 로직실패  => tree변경 취소(기존 this.depts -> this.treeData)
            // this.updateTreeData(); // 변경된 tree 롤백
            return;
        }

        // 통신 성공 + (DB 순서변경)로직 성공
        // -> 객체를 받았을 때, 필드변경 연동 확인 됨
        // => 복직이 target_status일 땐, 재직으로 변경해서 넣어주기
        if (target_status === '복직') target_status = '재직';
        emp.job_status = target_status;


        this.toast(res.data.message);
        // this.treeUpdated(tree); // tree 자체 ----getPureData------> this.depts
        // this.initialDepts = this.depts; // this.depts -------> this.initialDepts

    }).catch(err => {
        console.log(err)
        this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
        // [cancel 3] 통신실패  => tree변경 취소(기존 this.depts -> this.treeData)
        // this.updateTreeData();

    }).finally(() => {

    });

},
```



##### route

```python

@dept_bp.route("/employees/change/job_status", methods=['PUT'])
def change_employee_job_status():
    payload = request.get_json()
    # print(payload)
    employee = Employee.change_job_status(payload['emp_id'], payload['job_status'], datetime.date.today())


    if employee:
        return make_response(dict(message='재직상태가 변경되었습니다.'), 200)
    else:
        return make_response(dict(message='재직상태 변경에 실패하였습니다.'), 409)
```







#### 1인 부서 선택시, 자동으로 직원추가의 부서장 체크해놓고, diasbled?

```js
selectNode(dept) {
    // 선택되지 않은 dept라면, 할당 -> 선택됬다면 null로 선택 풀기
    if (this.idOfSelectedDept !== dept.id) {
        this.selectedDept = dept;

        // 선택된 부서가 1인 부서라면, 부서장 체크하기
        if (this.selectedDept.type === 0){
            this.asLeader = true;
        } else {
            this.asLeader = false;
        }

        return;
    }
    this.selectedDept = null;
},
```

##### 1인 부서라면, 소속된 직원이 없습니다. 대신 다른 멘트로 변경

```html
<!--  직원 없을 때 -->
<div class="list"
     v-if="!selectedDept.employees || (selectedDept.employees && !selectedDept.employees.length)">
    <div class="list-item">
        <div class="list-item-content is-size-7">
            <div class="list-item-description ">
                {$ selectedDept.type === 0 ? '1인 부서로 부서장만 추가 가능합니다.' : '소속된 직원이 없습니다.' $}
            </div>
        </div>
    </div>
</div>
```

![](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206163059320.png)

![](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206163106707.png)

##### tree에  부서type에 따라 어떤부선지 알려주기

![image-20230206163421695](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206163421695.png)

![image-20230206163436442](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206163436442.png)



```html
<span :id="'node-' + dept.id"
:class=" dept.id !== idOfSelectedDept ? getTextColorToLevelAndSort(dept.level, dept.parent_sort, dept.sort) : 'abc' "
>
    <!-- name -->
    {$ dept.name $}
    <span class="has-text-weight-light ml-1"
    :class="dept.id !== idOfSelectedDept ? 'has-text-grey' : 'has-text-white'"
    >
    	<small>{$ getDeptCategory(dept) $}</small>
    </span>
</span>
```

```js
getDeptCategory(dept){
    if (dept.type === 0){
        return '1인 부서'
    } else if (1 <= dept.type <= 3 ){
        return '행정 부서'
    } else if (4 <= dept.type <= 7 ){
        return '의료관련 부서'
    } else if (8 <= dept.type ){
        return '연구관련 부서'
    }
},
```

![image-20230206164752834](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230206164752834.png)