wikidocs 반영해나가기



### user

#### generate_password, check_password 로직을 user내부로 setter.propery, 인스턴스메서드로 옮기기



1. `current_user.is_authenticated ` 대신 `g.user`를 사용하여 로그인여부를 확인하는 중

2. **user의 password에 `외부에서 generate_password_hash`하던 것을 -> `@property`를 이용하여 getter시 에러 / `setter시 내부 generate_password_hash`후에 필드 저장하도록 변경하기**

   1. user모델에 property추가하기

      ```python
          @property
          def password(self):
              raise AttributeError('비밀번호는 읽을 수 없습니다.')
      
          @password.setter
          def password(self, password):
              self.password = generate_password_hash(password)
      ```

   2. `password = generate_password_hash(form.password.data or '1234') ` **사용처(alt+F7)들을 모두 찾아, generate_password_hash 제거하기**

      ![image-20221209000352427](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209000352427.png)

      ![image-20221209000235366](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209000235366.png)

      ![image-20221209000243887](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209000243887.png)

   3. `check_password_hash()`도 User내부에 verify_password로 변경하기

      1. user 모델에 인스턴스 메서드  만들기(**인스턴스 모델은 이미 session내부에서 사용되는 거라 with db 필요없음**)

         ```python
         def verify_password(self, password):
             return check_password_hash(self.password, password)
         ```

      2. **check_password_hash사용처 찾아서 `객체.verify_password`로 변경하기**

         - **현재 비번확인은, 로그인 form에서 올라올때 해주고 있다**

           ![image-20221209000723859](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209000723859.png)

           ![image-20221209000735516](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209000735516.png)

           ![image-20221209000800699](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209000800699.png)

      3. **password필드와, propery password가 `필드명과 동일`하다면, `verify_password()`호출시 `self.password를 property로 인식`되어 에러가 난다**

         ![image-20221209001250630](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209001250630.png)

         ![image-20221209001303046](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209001303046.png)

      

      4. **db password필드명을 `password_hash`로 변경**

         - 필드명 사용처 다 변경

         ```python
         class User(BaseModel):
             __tablename__ = 'users'
             # 가입시 필수
             id = Column(Integer, primary_key=True)
             username = Column(String(128), unique=True, nullable=False)
             # password = Column(String(320), nullable=False)
             password_hash = Column(String(320), nullable=False)
             #...
             
             @property
             def password(self):
                 raise AttributeError('비밀번호는 읽을 수 없습니다.')
         
             @password.setter
             def password(self, password):
                 self.password_hash = generate_password_hash(password)
         
             def verify_password(self, password):
                 return check_password_hash(self.password_hash, password)
         ```

         ![image-20221209001814643](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209001814643.png)





#### role(1) - permissions(Many) 만들기

##### permission의 종류

- 아래단계부터 int 1을 부여하며, 그 다음단계는 1+1 -> 2 -> 2+2로 늘어나서, **`특정 역할을 빼면, 그 직전 역할로 갈 수 있도록 배수로 구성하여 [여러역할] -> 1개의 int로 나타낼 수 있게`**한다
  - 1 follow: 최하위 역할
  - 2 comment: 댓글다는 권리
  - 4 write: 쓰는 권리
    - **여기까지 기본 권리**
  - 8 clean: 댓글 soft delete 권리
    - **준 관리자 권리**
  - 16 admin: 주인권리?



##### permissions묶음으로 구성되는 role의 종류

- 'User'
  - follow + comment + write
- 'Cleaner'
  - follow + commnet + write (User)
  - Clean
- Administrator
  - follow + commnet +  write (User) + Clean(Cleaner) + Admin



##### 나한테 맞게 커스텀

- 1 follow: 최하위 역할
- 2 comment: 댓글다는 권리
- 4 write: 쓰는 권리
  - **여기까지 User 권리**
- 8 clean: 댓글 soft delete 권리
- 16 reservation: 예약관리
  - **여기까지 Staff, doctors 권리**
- 32 Attendance management: 직원근태 관리
  - **여기까지 ChiefStaff권리**
- 64 employee management:
  - 여기까지 **executive(임원) 권리**
- 128 admin: 
  - 여기까지 **admin**권리



- 'User'
  - follow + comment + write
- 'Staff', 'Doctors'
  - follow + commnet + write (User)
  - Clean
  - reservation
- 'ChiefStaff'
  - follow + commnet + write (User)
  - Clean
  - reservation
  - Attendance management
- executive
  - follow + commnet + write (User)
  - Clean
  - reservation
  - Attendance management
  - employee management
- 'Administrator'
  - admin

##### Permission IntEnum + Roles entity

```python
class Permission(enum.IntEnum):
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4  # User
    CLEAN = 8
    RESERVATION = 16  # Staff, Doctor
    ATTENDANCE = 32  # ChiefStaff
    EMPLOYEE = 64  # Executive
    ADMIN = 128  # Admin


class Role(BaseModel):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    # User 생성시, default객체가 User인지를 컴퓨터는 알길이 없기에
    # 우리가 정해둔 default role을 검색해서, User생성시 배정할 수 있게 한다
    default = Column(Boolean, default=False, index=True)
    permissions = Column(Integer)

    # 여러 사용자가 같은 Role을 가질 수 있다.
    users = relationship('User', backref='role', lazy='dynamic')
```



##### 정의한 permission묶음의 role dict를 전체 데이터로서 한번에  주입할 classmethod insert_roles 정의

```python
    ## Role을 생성(수정시도 생성)할 때, Role객체 생성시 따로 permissions= int값(enum)을 입력하지 않는다면,
    ## - permission을 int 0으로 채워둔다.
    ## - 사실 Role객체를 미리 생성할 일은 없고, 나중에 일괄생성하는데, 그때 0부터 채우도록 하는 것
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.permissions:
            self.permissions = 0

    ## role마다 주어지는 permission 묶음을 마련해놓고, int값으로 계산하여 role 전체를 1번에 생성
    ## -> 조회가 들어가서 insert임에도 불구하고, cls메서드로 정의한다.
    @classmethod
    def insert_roles(cls):
        # 1) 각 role(name)별  permission 묵음 dict를 미리 마련한다
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],

            'Staff': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                      Permission.CLEAN, Permission.RESERVATION],
            'Doctor': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                       Permission.CLEAN, Permission.RESERVATION],

            'ChiefStaff': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                           Permission.CLEAN, Permission.RESERVATION,
                           Permission.ATTENDANCE
                           ],

            'Executive': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                          Permission.CLEAN, Permission.RESERVATION,
                          Permission.ATTENDANCE,
                          Permission.EMPLOYEE
                          ],

            'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                              Permission.CLEAN, Permission.RESERVATION,
                              Permission.ATTENDANCE,
                              Permission.EMPLOYEE,
                              Permission.ADMIN,
                              ],
        }
        # 2) role dict묶음을 돌면서, 이미 존재하는지 조회하고, 없을 때 Role객체를 생성하여 role객체를 유지한다
        with DBConnectionHandler() as db:
            # 8) role마다 default role인 User인지 아닌지를 확인하기 위해 선언
            default_role = 'User'

            for role_name in roles:
                role = db.session.scalars(select(cls).filter_by(name=role_name)).first()
                if not role:
                    role = cls(name=role_name)
                # 3) 이미 존재하든, 새로 생성했든 해당role객체의 permissions필드를 0으로 초기화한다
                role.reset_permissions()
                # 4) 해당role_name에 해당하는 int permission들을 순회하면서 필드에 int값을 누적시킨다
                for perm in roles[role_name]:
                    role.add_permission(perm)
                # 7) 해당role에 default role인 User가 맞는지 확인하여 필드에 넣어준다.
                role.default = (role.name == default_role)

                db.session.add(role)
            db.session.commit()

    def reset_permissions(self):
        self.permissions = 0

    # 5) add할 때, 이미 가지고 있는지 확인한다(중복int를 가지는 Perm도 생성가능하다고 생각할 수 있다)
    def has_permission(self, perm):
        return self.permissions & perm == perm

    def add_permission(self, perm):
        # 6) 해당 perm을 안가지고 잇을때만 추가한다
        if not self.has_permission(perm):
            self.permissions += perm

    # repr은 ‘Representation’
    def __repr__(self):
        return '<Role %r>' % self.name

```



##### auth init, entity 패키지 init에 올린 뒤, main.py에서  일괄생성 테스트

```python
if __name__ == '__main__':

    session = Session()
    create_database(truncate=False, drop_table=False, load_fake_data=False)

    Role.insert_roles()



```



![image-20221209121005927](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209121005927.png)

- 16까지 권한을 가지는 Staff와 Doctor는 **하위 permission을 아무리 더해도(31), 32의 ChiefStaff를 못따라간다**

  ![image-20221209121240627](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209121240627.png)



#### Role(1)에 대한 User(Many)가 fk가지기

- user의 `is_super_user`를 대신하는 `role`칼럼이지만, **먼저 추가하고 나서 나중에 기능 대체하며 삭제해야할 것 같다**



##### role.id (fk) role칼럼은 nullable으로 만들고, 외부에서 keyword입력안하고 생성자 재정의에서 자동 default입력 가능하게?

![image-20221209175413533](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175413533.png)



##### role을 안넣어주고 만들면, 환경변수 ADMIN_EMAIL에 안걸리는 user는 default Role을 가진 user로 채워서 넣어준다 by 생성자 재정의



```python
class User(BaseModel):
    #...
    email = Column(String(128), nullable=True, index=True)
    
    ## 추가2-1 role에 대한 fk 추가
    ## - user입장에선 정보성 role을 fk로 가졌다가, role entity에서 정보를 가져오는 것이지미나
    ## - role입장에선 1:m이다. 1user는 1role,  1role은 여러유저들에게 사용
    role_id = Column(Integer, ForeignKey('roles.id'))
    
    
    ## 추가2-2 user생성시, role=관계객체를 입력하지 않은 경우, default인 User Role객체를 가져와 add해서 생성되도록 한다
    ## -> if 환경변수의 ADMIN_EMAIL에 해당하는 경우, 관리자 Role객체를 가져와 add해서 생성되게 한다
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ## 원본대로 생성했는데, 따로 role객체를  role = Role( )로 부여하지 않았다면,
        ## (2) 그게 아니라면 role중에 default=True객체(default User객체)를 Role객체로 찾아 넣어준다.
        if not self.role:
                ## (1) ADMIN_EMAIL인지 확인하여, admin Role객체를 부여한다
            if self.email == project_config.ADMIN_EMAIL:
                condition = Role.name == 'Administrator'
            else:
                condition = Role.default == True
            with DBConnectionHandler() as db:
                self.role = db.session.scalars(select(Role).where(condition).first()

```

```yml
#### 비워둘거면 아예 주석처리해야 빈문자열이 안가서 python내부 default값이 적용된다.
#### config####  development or testing or production 
# (주석처리시 default key값인 development)
APP_CONFIG=development

#### project####  
# = upload_path를 비워두면, base + 'uploads/'를 업로드 폴더로 간주한다.
# PROJECT_NAME=
# PROJECT_VERSION=
ADMIN_EMAIL='tingstyle1@gmail.com'
# UPLOAD_PATH=

```



```python
class Project:
    # project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION")
    # user생성시 role안넣은 상태에서, email이 정해진 email이면, 관리자 Role을 넣어준다.
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL")

```



#### user table 삭제후 데이터 복붙후 role 처리해보기

##### ㅠ_ㅜ 칼럼 추가(meta정보 변환)하기 전에, dump부터 했어야한다

- dump_sqlalchemy -> 칼럼 추가 -> 데이터 삭제 -> bulk_insert_from_json?

![image-20221209175109030](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175109030.png)



##### table삭제전에 데이터 복붙

```
2022-11-25 17:58:41.579745,2022-12-03 23:11:24.727490,1,admin,pbkdf2:sha256:260000$mBUwOreye5PL9OAV$9984c6307e71e67565c5a59f045517cafd555ff14c7a2212cc60095781f30045,1,1,0,avatar/aab9efd21d1347ecb51fdf9e72b5da9e.png,1,,전남 나주시,
2022-11-25 17:58:41.579745,2022-12-03 23:43:47.403360,2,user,pbkdf2:sha256:260000$SJGRdkrPTUYKCqYI$62749de0f1bcf46296ff71006b361570da06bdc9e77743db79cc05bba549643d,0,1,0,avatar/fb2d6d74de684d74bb0f69e6cdc59aa8.png,1,tingstyle1@gmail.com,123,01046111111
2022-11-29 19:37:28.655367,2022-12-03 15:40:26.155357,4,user777,pbkdf2:sha256:260000$z25B1FUgVqAQGD7v$e4927664e9f57bab265823f08426a13c976bba1a712122c738ef63abef90958c,1,1,0,,1,"","",01046006242
2022-12-03 17:53:07.907102,2022-12-03 18:00:41.005980,11,111,pbkdf2:sha256:260000$r0iyHzveRqZMJo1q$30856fb151f12ae1d9e67f90eed5ac8d4ef25d564dcb0044ca5dfcd8be717f63,0,1,0,avatar/0330e885c0e04417b1086eb0ced29a47.png,2,quartz0117@naver.com,,01012341234
2022-12-03 18:04:00.307104,2022-12-03 18:04:24.183828,12,abc1,pbkdf2:sha256:260000$DI2mtk0mcvhdWVmd$1e09df85a542ffdcb952067cec21d3c781cbc1bb6c75c122d2a31d3e9feb69ce,0,1,0,,1,,전남 나주시,01046006245
2022-12-03 18:12:19.623404,2022-12-03 18:12:50.563344,14,재기,pbkdf2:sha256:260000$0BuinZePoNr8B5jp$2404e0edd85298a80bb07d89fc4c27ec1dbf84416030c12d9559fd7ec465ab0b,0,1,0,avatar/a4b3f579d4b34c93aa54c9617a09bb13.png,2,,전남 나주시,01046006249
2022-12-08 00:27:06.098875,2022-12-08 00:27:06.099875,15,admin2,pbkdf2:sha256:260000$TaQXlIkFyIrzU2Ig$cd32d64757847546f27ce572a124ef09ad55fd49168f8c856d7d47b26ffc8005,1,1,0,,0,,,

```

![image-20221209175159350](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175159350.png)



##### table삭제후 main에서 자동생성 -> 데이터 복붙

- 다행히 새로생긴 칼럼이 맨끝에 위치해서..

![image-20221209175257383](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175257383.png)



##### 기존 form으로 role없이 유저를 추가한다면? default Role이 차있어야한다

![image-20221209175651484](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175651484.png)

![image-20221209175705909](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175705909.png)

##### admin email의 유저를 추가한다면? email은 추가정보로서, User객체 생성시 입력을 안받으니 안되는 상황 ->

![image-20221209175833292](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221209175833292.png)



###### 회원가입시 ㄴㄴ admin의 user add form에서는 email을 필수로 받아야, admin을 결정할 수있다.

- 일반유저 가입용 auth > class RegisterForm이 아니라
  - 여기선 Role을 입력안받음 -> User객체 생성시 Role= 안들어옴 - > 생성자에서 default로 들어감
  - **여기선 Role입력은 없지만, 추가정보에 email이 있다면? (추가정보로는 User생성자를 안타는 시점이라... ADMIN_EMAIL이 작동ㄴㄴ)**
    - **유저가입시에도 비번찾기 위해 email을 입력받게 만들어야** 한다



- **admin 유저 추가용 admin > class CreateUserForm에서 `email필드를 추가`하자**
  - 추가로 **`Role select 필드`도 추가**해야한다.
  - admin에서 미정으로 할 일은 없다



#### admin UserAdd용 CreateUserForm  email 및 role 필드 추가

- email필드는, 추가정보 form (userinfo)에서 -> admin용 createUserForm과 가입용 Registerform으로 ~~옮겨야한다~~ 추가해서, userinfo에도 개인정보 수정시 수정가능하게 해야한다.?
- role필드는 추가해야한다



1. CreateUserForm에 email을 추가하되 더이상 nullable이 아니므로 **validators에 Optional + filters 빈문자열 None처리를 제거해준다**

   ```python
   class CreateUserForm(FlaskForm):
       #...
   	email = EmailField("이메일", validators=[
           DataRequired(message="필수 입력"),
       ], )
       
       def validate_email(self, field):
   ```

##### form 필드추가시 template 수정 -> add route/edit route 수정도 같이한다

1. admin용 user.html에 email필드 추가

   ![image-20221210115920529](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221210115920529.png)

2. user_form.html에 email필드 추가

   ```html
   <div class="field">
       {{ form.email.label(class='label') }}
       <div class="control">
           <!-- edit일 경우, form-->
           {{ form.email(class='input', placeholder='email') }}
       </div>
   </div>
   ```

   

   ![image-20221210120451755](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221210120451755.png)

3. admin.user_add route/ user_edit route에서 email정보를 user객체에 추가해서 생성

   ```python
   user = User(
       username=form.username.data,
       password=form.password.data,
       email=form.email.data,
   ```

   ```python
   # 나머지 필드도 변경
           user.email = form.email.data
   ```

   ![image-20221210120752865](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221210120752865.png)



##### db에서 email의 데이터를 다 채운 후 -> entity에서  nullable =False로 변경

![image-20221210120144302](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221210120144302.png)

```python
    # 추가정보 -> 필수정보로 변경(nullable 제거
    email = Column(String(128), index=True)
```





##### (db필드추가시) form부터 role필드 추가하기

1. 일단 role은 다른entity에서 받아와서 고르는데, **고정된  종류 택1의 Radio필드보다는 `동적인 종류 택1의 SelectField`를 `생성자에서 query불러와 .choices에 추가`해야할 것 같다**

2. 동적으로 choices추가는, [2가지 경우가능하다 - 예시 참고](https://stackoverflow.com/questions/31619747/dynamic-select-field-using-wtforms-not-updating/)

   1. 생성자에서 채워도 되고 **나의 경우, db쿼리 갖다쓰는 경우, 생성자에서**

      - ex> PostForm에서 category(부모)  및 tag(다대다)를 selectmultiplefield에 집어넣을 때 생성자에서 

        ```python
            def __init__(self, post=None, *args, **kwargs):
                self.post = post
                # 1-1) 수정 form
                if self.post:
                    info = dict(
                        title=self.post.title,
                        desc=self.post.desc,
                        content=self.post.content,
                        has_type=self.post.has_type,
                        category_id=self.post.category.id,
                        tags=[tag.id for tag in self.post.tags],
                    )
        
                    super().__init__(**info)
        
                # 1-2) 생성 form
                else:
                    super().__init__(*args, **kwargs)
        
                # 3) 생성/수정 무관하게 choices선택사항은 관계객체들로부터 전체가 준비되어있어야한다.
                # -> 하지만, edit form 필드값 초기화 이후 넣어줘야, 정상적으로 selectize가 정상표기된다.
                with DBConnectionHandler() as db:
                    categories = db.session.scalars(select(Category)).all()
                    tags = db.session.scalars(select(Tag)).all()
        
                self.category_id.choices = [(category.id, category.name) for category in categories]
                self.tags.choices = [(tag.id, tag.name) for tag in tags]
        
        ```

        

   2. 해당필드의 choices=인자로 채워도 된다. **나의 경우, IntEnum에서 바로 불러올 수 있는 경우**

      - ex> PostForm에서 radio를 채울 때 

        ```python
        class PostForm(FlaskForm):
            #...
            has_type = RadioField('Post status',
                                  choices=PostPublishType.choices(),
                                  # choces에는 (subfield.data, subfield.label)로 될 값이 같이 내려가지만,defautld에는 .data가 되는 값 1개만 넘겨줘야한다.
                                  default=PostPublishType.SHOW.value,
                                  coerce=int,
                                  )
        ```

        

- **admin용 user 생성/수정폼인 CreateUserForm에 `fk_id 폼 필드 + 생성자에서 choicse(id, name)채우기`**

  ```python
  class CreateUserForm(FlaskForm):
      #...
      role_id = SelectField(
          '역할',
          choices=None,
          coerce=int,
          validators=[
              DataRequired(message="필수 입력"),
          ]
      )
      #...
      
      def __init__(self, user=None, *args, **kwargs):
  
          #...
          with DBConnectionHandler() as db:
              roles = db.session.scalars(select(Role)).all()
              self.role_id.choices = [(role.id, role.name) for role in roles]
  ```





##### form필드 추가에 따른 admin/user_form -> admin_user.html 변경하기

###### user_form.html

- article_form.html에 상위카테고리 고를 때, select 를 썼으니 참고한다

  - **`div.field`안에 `div.select`안에 form.필드를 풀면 알아서 dropdown으로 나온다**

  ```html
  <div class="field">
      {{ form.role_id.label(class='label') }}
      <div class="control">
          <!-- <div class="select is-fullwidth">-->
          <div class="select is-half">
              {{ form.role_id }}
          </div>
      </div>
  </div>
  ```

  

  ![image-20221212004932469](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212004932469.png)

  ![image-20221212005008758](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212005008758.png)

###### user.html 수정

```html
<td>{{ user.role }}</td>
```

![image-20221212005256063](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212005256063.png)

```
I had the same problem with Celery. Adding lazy='subquery' to relationship solved my problem.
```

- **user.role을 진자에서 부를 거면, One에서 관계칼럼 -> many에게 줄때, lazy="subqeury"로 만들어놔야한다**



```python
# 처음
users = relationship('User', backref='role', lazy='dynamic')
# 잘못해서 one에게 줌
users = relationship('User', backref='role', lazy='subquery')
# many에게 backref()객체에 씌워서'role'을 줄 때 lazy=subquery로 줘야함
    users = relationship('User', backref=backref('role', lazy='subquery'), lazy='dynamic')

```

![image-20221212005945122](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212005945122.png)



- tag처럼 주려면 div.tags > span.tag.is-색깔.is-light로 형식을 갖추어야하며 td태그에 class를 달면 안된다.

```html
<td>
    <div class="tags">
        <span class="tag is-dark is-light">
            {{ user.role.name }}
        </span>
    </div>
</td>
```



![image-20221212010525075](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212010525075.png)



##### form -> form.html -> 던진 것을 반영하기 위해 route 수정

```python
# user_add route
role_id=form.role_id.data,


# user_edit route
user.role_id = form.role_id.data
```

![image-20221212010804973](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212010804973.png)



##### role 색깔 변화주기

```html
<span class="tag {% if user.role.name == 'User' %}is-dark{% elif user.role.name == 'Administrator' %}is-danger{% else %}is-info{% endif %} is-light">

```

![image-20221212011058430](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212011058430.png)



####  일반회원 가입용 UserInfoForm 및 Registerform에 email필드  필수필드로 변경

- auth/forms.py의 **추가정보 입력form인 **
  - **`UserInfoForm`에서 Optional()이었던 것을 필수로 **
- **가입시 필수폼인 `RegisterForm`에 필드 추가** 
  - 추가정보였던 email 필드를 Optional() validators를 제거하고 필수폼으로 이동

#####  UserInfoForm에서 email필드를 Optional() 제거 

- nullable 필드가 아니므로

  - validators = [ **Optional() 대신 DataRequired()**]
  - filters = 미입력(빈문자열)시 or None으로 보내기 삭제

  ```python
  email = EmailField("이메일",
                     validators=[DataRequired()],
                     # validators=[Optional()],
                     # filters=[lambda x: x or None]
                    )
  ```

  ![image-20221212125630655](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212125630655.png)

  ![image-20221212125620878](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212125620878.png)

##### RegisterForm에 email필드 추가하여 가입시 필수로 받기

- email필드 추가 + validate 추가

  ```python
  class RegisterForm(FlaskForm):
      #...
      email = EmailField("이메일", validators=[
          DataRequired(message="필수 입력"),
      ], )
      
      def validate_email(self, field):
          if self.user:  # 수정시 자신의 제외하고 데이터 중복 검사
              condition = and_(User.id != self.user.id, User.email == field.data)
          else:  # 생성시 자신의 데이터를 중복검사
              condition = User.email == field.data
  
          with DBConnectionHandler() as db:
              is_exists = db.session.scalars(
                  exists().where(condition).select()
              ).one()
  
          if is_exists:
              raise ValidationError('이미 존재하는 email 입니다')
  
  ```

  

##### 생겨난 필드를 route에서 처리 추가

```python
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
    
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            # user = User(username=form.username.data, password=generate_password_hash(form.password.data))
            user = User(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
```

##### 생겨난 필드를 html에 입력 추가 register.html

```html
    <div class="field">
        <p class="control has-icons-left has-icons-right">
            {{ form.email(class='input', placeholder='e-mail 입력') }}
            <span class="icon is-small is-left">
                <i class="mdi mdi-email-outline"></i>
            </span>
        </p>
    </div>
```

![image-20221212133625746](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212133625746.png)

![image-20221212133602334](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212133602334.png)



##### Registerform에 중복검사 되는지 확인하기

- 안하고 있어서 추가하기
- **registerform은 수정으로 사용되지 않으므로, 자신제외하고  중복검사 for수정용은 없ㅇ이 하기**



```python
    def validate_email(self, field):
        condition = User.email == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 email 입니다')
```

![image-20221212133901833](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212133901833.png)





#### role과 email을 필수필드로 처리했다면, db에 다채우고나서, fk에 nullable=False 주기

![image-20221212134103103](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212134103103.png)

```python
role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
```





### 권한처리

#### auth_route의 데코레이터를 main>utils>decorators.py로 옮기자

##### session

세션에 대해 잠시 생각해 보자. session은 request와 마찬가지로 플라스크가 자체적으로 생성하여 제공하는 객체이다. 브라우저가 플라스크 서버에 요청을 보내면 request 객체는 요청할 때마다 새로운 객체가 생성된다. 하지만 session은 request와 달리 한번 생성하면 그 값을 계속 유지하는 특징이 있다.

> 세션은 서버에 브라우저별로 생성되는 메모리 공간이라고 할수 있다.

따라서 세션에 사용자의 id 값을 저장하면 다양한 URL 요청에 이 세션에 저장된 값을 읽을 수 있다. 예를 들어 세션 정보를 확인하여 현재 요청한 주체가 로그인한 사용자인지 아닌지를 판별할 수 있다



**쿠키와 세션 이해하기**



웹 프로그램은 [웹 브라우저 요청 → 서버 응답] 순서로 실행되며, 서버 응답이 완료되면 웹 브라우저와 서버 사이의 네트워크 연결은 끊어진다. 하지만 수 많은 브라우저가 서버에 요청할 때마다 매번 새로운 세션이 생성되는 것이 아니라 동일한 브라우저의 요청에서 서버는 동일한 세션을 사용한다.

그렇다면 서버는 도대체 어떻게 웹 브라우저와 연결 고리(세션)를 맺는걸까?

그 해답은 쿠키(Cookie)에 있다. **쿠키는 서버가 웹 브라우저에 발행하는 값**이다. 웹 브라우저가 서버에 어떤 요**청을 하면 서버는 쿠키를 생성하여 전송**하는 방식으로 응답한다. 그러면 **웹 브라우저는 서버에서 받은 쿠키를 저장**한다. 이후 **서버에 다시 요청을 보낼 때는 저장한 쿠키를 HTTP 헤더에 담아서 전송**한다. 그러면 서버는 웹 브라우저가 보낸 **쿠키를 이전에 발행했던 쿠키값과 비교하여 같은 웹 브라우저에서 요청한 것인지 아닌지를 구분**할 수 있다. 이때 **세션은 바로 쿠키 1개당 생성되는 서버의 메모리 공간**이라고 할 수 있다.





`@bp.before_app_request`를 적용한 함수는 **auth_views.py의 라우팅 함수 뿐만 아니라 모든 라우팅 함수보다 항상 먼저 실행**된다.

load_logged_in_user 함수에서 사용한 `g`는 플라스크의 컨텍스트 변수이다. 이 변수는 request 변수와 마찬가지로 [요청 → 응답] 과정에서 유효하다. 코드에서 보듯 session 변수에 user_id값이 있으면 데이터베이스에서 사용자 정보를 조회하여 `g.user`에 저장한다. 이렇게 하면 이후 사용자 로그인 검사를 할 때 session을 조사할 필요가 없다. `g.user`에 값이 있는지만 확인하면 된다. `g.user`에는 User 객체가 저장되어 있으므로 여러 가지 사용자 정보(username, email 등)를 추가로 얻어내는 이점이 있다.

> g.user에는 User 객체가 저장된다.



##### g객체는 flask당 1개지만, g.user를 요청시마다 `브라우저별 쿠키별 1session에 의해 동적으로 바뀌`는 중

- 로그인된 브라우저 -> g.user가 로그인한 것으로 찍힌다

  ![image-20221212144920895](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212144920895.png)

- **로그인 안된 브라우저 -> flask의 g객체에 g.user가 안들어가있다**

  ![image-20221212145006249](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212145006249.png)



- **다른 아이디로 로그인한 다른 브라우저 -> 같은 g객체를 이용하지만, `매 요청마다 g.user를 바꿔낀다`**

  ![image-20221212145256945](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212145256945.png)

  ![image-20221212145112529](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212145112529.png)



##### g객체는 브라우져별-쿠키별-1세션보다 더 작은 1request에만 존재하며, 1request단위에서 jinja와 동시적으로 활용하도록 User객체를 g객체에 넣어 사용한다

- https://stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask

`g` is a [thread local](http://flask.pocoo.org/docs/advanced_foreword/#thread-locals-in-flask) and is per-request (See [A Note On Proxies](http://flask.pocoo.org/docs/reqcontext/#notes-on-proxies)). The `session` is *also* a thread local, but in the default context is persisted to a MAC-signed cookie and sent to the client.

The problem that you are running into is that **`session` is rebuilt on each request (since it is sent to the client and the client sends it back to us)**, **while data set on `g` is only available for the lifetime of *this* request.**

The *simplest* thing to do (note `simple != secure` - if you need secure take a look at [Flask-Login](https://flask-login.readthedocs.org/en/latest/)) is to simply add the user's ID to the session and load the user on each request:

```python
@app.before_request
def load_user():
    if session["user_id"]:
        user = User.query.filter_by(username=session["user_id"]).first()
    else:
        user = {"name": "Guest"}  # Make it better, use an anonymous User instead

    g.user = user
```



##### 현재 로그인 및 권한처리

1. auto_route.py에 있는

   `@auth_bp.before_app_request def load_logged_in_user():`에서  **매 요청마다** session에 있는 user_id를 확인하여, `g.user`에 `User객체를 찾아` 넣고, **동적으로 g.user에게 `.has_perm`을 준다**

   - user객체의 `is_active`를 필수로 확인하며
     - `is_super_user`인 경우 동적으로 **관리자는 바로 g.user.has_perm** = 1을
     - **(관리자가 아닌 경우)** `is_super_user`가 아니면서
       - `is_staff(is_ban)`이 아니면서
       - 현재요청route의`request.path`가  일반유저허용 `urls`안에 포함되어있으면
         - (urls -> url들을 확인하여  request.path가 url를 포함하고 있으면)
         - **동적으로 g.user.has_perm = 1**
     - 위의 경우가 아니라면, **g.user.has_perm = 0**을 넣는다.

   ```python
   @auth_bp.before_app_request
   def load_logged_in_user():
       urls = [
           '/auth/',  # 일반사용자에게 @login_required 붙은 것 중 승인된 url
           '/auth/edit/',  # 일반사용자에게 auth.userinfo(id)의 url도 허용
       ]
       
       user_id = session.get('user_id')
       if not user_id:
           g.user = None
       else:
           with DBConnectionHandler() as db:
               g.user = db.session.get(User, user_id)
   
           if g.user.is_active and g.user.is_super_user:
               g.user.has_perm = 1
   
           elif g.user.is_active and not g.user.is_super_user and \
                   not g.user.is_staff and  any(url in request.path for url in urls):
               g.user.has_perm = 1
   
           else:
               g.user.has_perm = 0
   ```

   

2. 데코레이터 decorators.py안에 있는 `def login_required(view_func):`는 해당route에 대해

   - **g.user가 없으면 로그인으로 early return redirect**
   - **(g.user가 있어 로그인된 상태)라면**
     - 동적 g.user.has_perm이 1로 허용된 경우만 해당 viewfunc으로 넘어가고
     - 동적 g.user.has_perm이 0인 경우(관리자X or 일반유저가 허용url아닌 경우) **권한없다고 한다**

   ```python
   def login_required(view_func):
       @functools.wraps(view_func)
       def wrapped_view(**kwargs):
           if not g.user:
               redirect_to = f"{url_for('auth.login')}?redirect_to={request.path}"
               return redirect(redirect_to)
   
           if g.user.has_perm:
               return view_func(**kwargs)
           else:
               return '<h1> 권한이 없습니다 </h1>'
   
       return wrapped_view
   
   ```

   



#### Permission or Role로 권한처리

##### Permission으로 기능별  view에서 그 이상int 가지면 가능한 권한처리

- [위키독스 MyBlog](https://wikidocs.net/106184)

1. permission을 인자로 받는 데코레이터를 만들고,  **로그인된 g.user가 `.can(permission)`을 호출해서 권한이 없으면 abort(403)을 내고, 그렇지 않으면 route로 통과하게 만든다.**

   ```python
   def permission_required(permission):
       def decorator(f):
           @functools.wraps(f)
           def decorated_function(*args, **kwargs):
               if not g.user.can(permission):
                   abort(403)
               return f(*args, **kwargs)
           return decorated_function
       return decorator
   ```

2. **User entity에 `.can(permission)`을 만든다**

   - user가 role객체를 갖고 있으면 **Role의 필드인 int permissions를 이용하기 위해 `role.has_permission(permission)`으로 확인한다**

   ```python
   class User(BaseModel):
       #...
   
       # permission_required에서 사용되는 권한확인용
       def can(self, permission):
           if not self.role:
               return False
           return self.role.has_permission(permission)
   ```

3. **Role entity에서 `.has_permission`으로 확인한다**

   - 1, 2, 4 아무리 기존에 누적되어도, 추가될 8보다 크거나 같을 순 없다
   - **1, 2, 4, 8을 가진 상태에서 16보다 작은 8(같은 permission)수준은 이미 소유한것으로 간주한다**

   ```python
   class Role(BaseModel):
       __tablename__ = 'roles'
   	# 5) add할 때, 이미 가지고 있는지 확인한다
       # -> perm == perm의 확인은, (중복int를 가지는 Perm도 생성가능하다고 생각할 수 있다)
       def has_permission(self, perm):
           return self.permissions & self.permissions >= perm
   ```

4. **권한체크 데코레이터를 이용해서, `각Role별상한permission_required 일반메서드`를 정의하고, 내부에서 `데코레이터를 호출까지 해주는 역할`을 해준다**

   - **이렇게 정의해도 데코레이터가 되나보다**
   - **직전 role은 못가지는 현재role의 상한permission을 permission_required에 넣어준다.**

   ```python
   def permission_required(permission):
       def decorator(f):
           @functools.wraps(f)
           def decorated_function(*args, **kwargs):
               if not g.user.can(permission):
                   abort(403)
               return f(*args, **kwargs)
   
           return decorated_function
   
       return decorator
   
   
   def admin_required(view_func):
       return permission_required(Permission.ADMIN)(view_func)
   
   ```





##### permission_required -> admin_required 테스트를 위해, 동적 .has_perm을 주입하는 load_logged_in_user 및 동적 .has_perm을 확인하는 login_required 일부 주석처리하여 테스트

- auth_route.py의 `load_logged_in_user`

  ![image-20221212163000725](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163000725.png)

- decorators.py의 `login_required`

![image-20221212163119944](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163119944.png)
![image-20221212163242284](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163242284.png)

​	



- **동적 .has_perm 확인이 없으면 `일반유저도 admin강제 접속가능한 상태`**

  ![image-20221212163331875](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163331875.png)



##### login_required밑에 추가로 admin_required를 걸어준다.

![image-20221212163450321](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163450321.png)



![image-20221212163503680](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163503680.png)

- abort(403)이 작동해서 forbidden이 뜬다.

- admin계정으로 들어가면 잘 작동한다.

  ![image-20221212163635574](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163635574.png)

- executive계정으로 들어간다면, forbidden이 떠야할 것이다.

  ![image-20221212163706681](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163706681.png)

  ![image-20221212163733260](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163733260.png)

  - view에서는 admin으로 뜬 상태(`view에선 아직 is_super_user 사용중`)로 들어가면, 금지 뜬다.

  ![image-20221212163808179](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212163808179.png)



- **admin route를 임원까지는 허용하도록 `executive_required`로 만들고, executive접속, admin접속 해보자**

  - 직원관리가 executive의 가장높은 권한이므로, 이것으로 만들어준다.

    ![image-20221212164139194](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212164139194.png)

    ![image-20221212164206488](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212164206488.png)

    ```python
    def executive_required(view_func):
        return permission_required(Permission.EMPLOYEE)(view_func)
    ```

    ![image-20221212164306955](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212164306955.png)

    ![image-20221212164317871](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212164317871.png)



- **role들마다 최고Permission으로 메서드를 매번 만들 수 없으니, role을 입력하면, 해당role의 최고권한으로 required가 걸리도록 해보자.**





##### Role로 특정Role(들)이상 허용하도록 권한처리

- [참고 깃허브 소스](https://github.com/Reason2020/doctorAppointmentBookingSystem/blob/main/DABS/core/decorators.py)





##### roles dict를 이용해서 각 role의 마지막권한을 permission으로 하는 메서드 만들기

1. `auth > users.py` User Entity 내부에 있는 dict를 외부로 빼고 init에 올리기

   ![image-20221212191512488](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212191512488.png)

   ```python
   #...
   from .auth import User, Role, Permission, roles
   #...
   ```

2. **admin_required와 유사하지만, `role name`을 입력으로 받고, `roles dict`에서 최고permission을 받아와, 그것을 permission_required로 확인하여, 여러개라면 `하나의 role이라도 현재유저가 g.user.can(최고permission)`을 `성공하면 ealry return으로 view_func을 타도록` 을 `다돌아도 ealry return 못했으면 abort(403)`을 태우도록 작성한다**

   - **permission_required처럼, 데코레이터가 @아랫줄에 적힐 view_func이외의 `추가 인자를 받으려면, 데코레이터를 한번더 덮는 메서드`가 필요하다**
     - **admin_required는 데코덮는메서드들 한번 더 덮는 대신, view_func을 인자로 받고, 내부에서는 `데코덮메서드( 정해진 인자)  + (view_func)으로 데코레이터 호출까지` 해줘야했었다.**
   - **role_required는 `추가인자를 받기 위해 데코덮 메서드 + g.user.can()시 return view_func`을 해주기만 하면 되므로  `1번만 데코덮 메서드`로 정의한다** 
     - **성공여부는 `g.user.can( 해당role의 최고permssion )`으로 결정된다**

   ```python
   def role_required(allowed_roles=[]):
       if not allowed_roles:
           raise ValueError('allowed_roles=은 반드시 list형태로 입력해야합니다')
   
       if not isinstance(allowed_roles, list):
           raise ValueError('allowed_roles=[]는 list형태로 입력해주세요')
   
       if any(allowed_role not in roles for allowed_role in allowed_roles):
           raise ValueError(
               f"""
               allowed_roles=[]의 인자에는
               {', '.join(roles.keys())} 중 하나를 입력해야합니다. 
               """''
           )
   
       def decorator(view_func):
           @functools.wraps(view_func)
           def decorated_function(*args, **kwargs):
   
               for allowed_role in allowed_roles:
                   role_name = allowed_role
                   role_highest_permission = roles[role_name][-1]
                   print(role_name, role_highest_permission)
   
                   if g.user.can(role_highest_permission):
                       return view_func(*args, **kwargs)
               abort(403)
   
           return decorated_function
   
       return decorator
   ```

   - utils init에 올리기

   ```python
   #...
   from .decorators import admin_required, role_required
   ```

3. admin_route에서 테스트하기

   ```python
   @admin_bp.route('/')
   @login_required
   @role_required(allowed_roles=['Executive'])
   def index():
       with DBConnectionHandler() as db:
   ```

4. **여러 role을 적어도, 1개만 role의 최고permission을 g.user.can()할 수 있으면 통과이므로 `최소한의 role만 적어도 된다`**

   ```python
   @login_required
   @role_required(allowed_roles=['Executive'])
   ```

   - Executive를 넣는 경우

     - staff접속 강제접속시

       ![image-20221212194853611](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212194853611.png)

     - Executive 접속시

       ![image-20221212200819281](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212200819281.png)

       

##### 정리: role별 최고permission을 내부에 넣은 각 role별 메서드 개별정의하기 vs role이름으로 알아서 최고권한을 따오는 메서드 -> 둘중 편한 것으로 사용하기

```python
@admin_bp.route('/')
@login_required
@role_required(allowed_roles=['Executive'])


@admin_bp.route('/')
@login_required
@executive_required
```



```python
def permission_required(permission):
    def decorator(view_func):
        @functools.wraps(view_func)
        def decorated_function(*args, **kwargs):
            if not g.user.can(permission):
                abort(403)
            return view_func(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(view_func):
    return permission_required(Permission.ADMIN)(view_func)
```





```python
def role_required(allowed_roles=[]):
    if not allowed_roles:
        raise ValueError('allowed_roles=은 반드시 list형태로 입력해야합니다')

    if not isinstance(allowed_roles, list):
        raise ValueError('allowed_roles=[]는 list형태로 입력해주세요')

    if any(allowed_role not in roles for allowed_role in allowed_roles):
        raise ValueError(
            f"""
            allowed_roles=[]의 인자에는
            {', '.join(roles.keys())} 중 하나를 입력해야합니다. 
            """''
        )

    def decorator(view_func):
        @functools.wraps(view_func)
        def decorated_function(*args, **kwargs):

            for allowed_role in allowed_roles:
                role_name = allowed_role
                role_highest_permission = roles[role_name][-1]
                print(role_name, role_highest_permission)

                if g.user.can(role_highest_permission):
                    return view_func(*args, **kwargs)
            abort(403)

        return decorated_function

    return decorator
```



##### admin route에  staff or executive  or  admin  role허용으로 데코레이터 다 달아주기

- `@role_required(allowed_roles=['Executive'])`를 달면 Executive + 그 이상의 role까지 다 허용된다.
- **admin도 staff는 허용하되, 자기 Permission에 맞는 것만 메뉴에 뜨도록 menu도 수정해준다.**
  - index: 직원급부터 admin 입장가능
  - category(menu) : 임원급
  - article(post), tag: 직원급
  - user
    - select : 직원급
    - edit부터는 : Chief직원급
    - **차후 직원들만 따로 분리부터는 select부터 Cheif직원급**
  - banner: 직원급
  - settings: admin만

##### 사실 route는 기능별로 분류되어있으므로 PermissionRequired를 쓰면 더 쉽다

- **PERMISSION에 `BANNER_DELETE = 를 세분화했다면`가 있다면,  banner_delete route에는 `@permission_required(BANNER_DELETE)`를 쓰면 된다.**
  - 나중에 적용해보자.





#### 현재 모든 entity의 세부기능을 permission으로 나누지 않았으므로, role로 처리할 수 있도록 g.user.can( perm )에 버금가는 g.user.is_role( 'role_name') 만들어주기 ->  db조회(취소) -> dict조회(살리기)

- 이렇게 되면, is_( 'User' ) 등을 확인할 때마다 db를 조회해야한다
- **has_permission은, db조회없이.. 매핑된 int로 바로 비교하기 때문에 빠를 것이다.**

```python
class User(BaseModel):
    __tablename__ = 'users'
    #...
    
    # permission_required에서 사용되는 권한확인용
    def can(self, permission):
        if not self.role:
            return False
        return self.role.has_permission(permission)

    # 기능별 permission대신, role로 확인가능하도록
    # => 이퀄비교를 하면, 해당role만 정확하게 찾는다.
    # => 그 이상으로 가능하도록 처리해야한다.
    # => role_name에 해당하는 Role객체 -> permissions를 구하고
    #   현재유저의 permissions가 크거나 같으면 허용해야한다...
    def is_(self, role_name):
        # with DBConnectionHandler() as db:
        #     role_perm = db.session.execute(select(Role.permissions).where(Role.name == role_name)).scalar()
        #### db로 조회하는 대신, roles dict로 최고권한을 조회한다
        role_perm = roles[role_name][-1]
        # print(self.role.permissions, role_perm)
        return self.role.permissions >= role_perm
```



##### role_required에서 g.user.can(perm) 대신 g.user.is_(role_name)으로 변경해서 사용하기 -> role_name으로 Role전체를 검색해서 permission으로 비교해야하므로 취소 -> roles dict를 이용해서 permission 가져와서 다시 살림

```python
def role_required(allowed_roles=[]):
    #...

    def decorator(view_func):
        @functools.wraps(view_func)
        def decorated_function(*args, **kwargs):

            for allowed_role in allowed_roles:
                # role_name = allowed_role
                # role_highest_permission = roles[role_name][-1]
                # print(role_name, role_highest_permission)

                # if g.user.can(role_highest_permission):
                #     return view_func(*args, **kwargs)
                #### 권한으로 확인한다면, 해당role의 최고권한 가져오는 로직은 없어진다.
                #### => but role_name -> Role조회 -> permissions조회 -> 유저가가진 permission >= 일때 성공
                #### => db를 한번더 조회해야하므로 보류
                if g.user.is_(allowed_role):
                    return view_func(*args, **kwargs)
            abort(403)

        return decorated_function
    return decorator
```



#### Permission Int만 inject할게 아니라, Role도 객체(enum)으로 보내기 위해 dict에서 일반enum화 시켜보기

1. dict를 Enum으로 만들기

   ```python
   class Roles(enum.Enum):
       # 각 요소들이 결국엔 int이므로, deepcopy는 생각안해도 된다?
       #### 미리 int들을 안더하는 이유는, 순회하면서, permission이 같은 것은 누적 또 하면 안되기 때문
       USER: list = [
           Permission.FOLLOW,
           Permission.COMMENT,
           Permission.WRITE
       ]
   
       STAFF: list = list(USER) + [
           Permission.CLEAN,
           Permission.RESERVATION
       ]
       #...
   ```

2. **dict key와,  Roles Enum의 name을 일치시키기 위해 roles db의 name을 변경하기**

   - default_role은 enum객체`.name`으로 접근해야 string이 된다.

   ```python
   class Role(BaseModel):
       #...
       @classmethod
       def insert_roles(cls):
           # 1) 각 role(name)별  permission 묵음 dict를 미리 마련한다
           # roles = {
           #     'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
           #
   
           # 2) role dict묶음을 돌면서, 이미 존재하는지 조회하고, 없을 때 Role객체를 생성하여 role객체를 유지한다
           with DBConnectionHandler() as db:
               # 8) role마다 default role인 User인지 아닌지를 확인하기 위해 선언
               # default_role = 'User'
               default_role = str(Roles.USER.name)
               # print(Roles.USER)
               # print(Roles.USER.name)
               # print(str(Roles.USER.name))
               # Roles.USER
               # USER
               # USER
   
               # for role_name in roles:
               for role_enum in Roles:
                   role = db.session.scalars(select(cls).filter_by(name=role_enum.name)).first()
                   if not role:
                       role = cls(name=role_enum.name)
                   # 3) 이미 존재하든, 새로 생성했든 해당role객체의 permissions필드를 0으로 초기화한다
                   role.reset_permissions()
                   # 4) 해당role_name에 해당하는 int permission들을 순회하면서 필드에 int값을 누적시킨다
                   # for perm in roles[role_name]:
                   for perm in role_enum.value:
                       role.add_permission(perm)
                   # 7) 해당role에 default role인 User가 맞는지 확인하여 필드에 넣어준다.
                   role.default = (role.name == default_role)
   
                   db.session.add(role)
               db.session.commit()
   ```

3. main.py에서 생성

   ![image-20221212224601752](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212224601752.png)

4. g.user.is_( dict key 대신 **Role Enum객체**)

   ```python
       def is_(self, role_enum):
           # with DBConnectionHandler() as db:
           #     role_perm = db.session.execute(select(Role.permissions).where(Role.name == role_name)).scalar()
           #### db로 조회하는 대신, roles dict로 최고권한을 조회한다
           # role_perm = roles[role_name][-1]
           #### dict-> enum으로 바뀌었을때 최고권한
           role_perm = role_enum.value[-1]
           # print(self.role.permissions, role_perm)
           return self.role.permissions >= role_perm
   ```

5. role_required(allowed_roles = [ ])  dict key 대신 enum객체

   ```python
   def role_required(allowed_roles=[]):
       if not allowed_roles:
           raise ValueError('allowed_roles=은 반드시 list형태로 입력해야합니다')
   
       if not isinstance(allowed_roles, list):
           raise ValueError('allowed_roles=[]는 list형태로 입력해주세요')
   
       # if any(allowed_role not in roles for allowed_role in allowed_roles):
       if any(allowed_role not in Roles for allowed_role in allowed_roles):
           raise ValueError(
   ```

6. **form의 choices에 들어가는 것은, DB에서 가져오므로 roles dict가 안쓰였다**

   ![image-20221212225435901](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212225435901.png)

7. **같은 value를 가진 enum이 iter시 안나타나는 현상 관련**

   - https://stackoverflow.com/questions/31537316/python-enums-with-duplicate-values
   - **ENUM순회시  `for enum객체 in Enum`이 아니라 ** 
     - **`for enum_name, enum객체 in Enum.__members__.items()`로 순회해야하며**
     - enum의 value를 뽑으려면 `enum_객체.value`로 반복문 내부에서 한번 더 가야한다

   ```python
   for role_name, role_enum in Roles.__members__.items():
   	#...
       print(role_name, role_enum, type(role_enum))
       # USER,  Roles.USER,   <enum 'Roles'>
       print(role_enum.value)
       # [<Permission.FOLLOW: 1>, <Permission.COMMENT: 2>, <Permission.WRITE: 4>]
   ```

   - **순회에서도 `중복된 value를 가진 enum`은 가장 맨 뒤에 나타난다**

   ![image-20221212231859551](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212231859551.png)

   - role의 id순서가 달라졌으니.. 기존user의 role_id가 다르게 물리게 되니 수정해줘야한다

     ![image-20221213005505467](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213005505467.png)

   - 태그색을 내는 기준도 enum의 name인 대문자로 바꿔줘야한다

     ```html
     <td>
         <div class="tags">
             <span class="tag {% if user.role.name == 'User' %}is-white{% elif user.role.name in ['ADMINISTRATOR', 'EXECUTIVE'] %}is-danger{% else %}is-info{% endif %} is-light">
                 {{ user.role.name }}
             </span>
         </div>
     </td>
     ```

8. `for enum객체 in Roles`로 순회하는 것들을 찾아서 `for role_name, role_enum in  Roles.__members__.items()`로 변경하고 **enum객체.name은 for role_name로, .value는 그대로 .value를 쓰게 한다 **

   ```python
   class User(...)
   
       @classmethod
       def insert_roles(cls):
           with DBConnectionHandler() as db:
               default_role = str(Roles.USER.name)
               for role_name, role_enum in Roles.__members__.items():
                   role = db.session.scalars(select(cls).filter_by(name=role_name)).first()
                   if not role:
                       role = cls(name=role_name)
                   role.reset_permissions()
                   
                   for perm in role_enum.value:
                       role.add_permission(perm)
                       
                   role.default = (role.name == default_role)
   
                   db.session.add(role)
               db.session.commit()
   ```

9. role_required에서 객체로 비교시에는 중복value의 enum객체가 true로 뜰 것이다?

   - 순회할때만 중복된 value의 enum객체가 안나오지, in으로 확인할 때는  그대로 사용된다

   ```python
   def role_required(allowed_roles=[]):
       if not allowed_roles:
           raise ValueError('allowed_roles=은 반드시 list형태로 입력해야합니다')
   
       if not isinstance(allowed_roles, list):
           raise ValueError('allowed_roles=[]는 list형태로 입력해주세요')
   
       # if any(allowed_role not in roles for allowed_role in allowed_roles):
       if any(allowed_role not in Roles for allowed_role in allowed_roles):
   ```



10. role_reqruied에 Roles.DOCTOR 넣고,doctor로 접속해서 확인하기

    ```python
    @admin_bp.route('/')
    @login_required
    @role_required(allowed_roles=[Roles.DOCTOR])
    def index():
    ```

    ![image-20221212233340782](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221212233340782.png)







#### manage.py에서 flask shell에  db, Role, User객체 미리 던져놓고, 최초시작시 Role을 python을 통한 data생성하게 하기

- manage.py

  ```python
  import os
  
  from src.infra.config.connection import DBConnectionHandler
  from src.infra.tutorial3 import User, Role
  from src.main.config import create_app
  
  app = create_app(os.getenv('APP_CONFIG') or 'default')
  
  
  # flask shell에 객체들을 미리 던져놓는다.
  @app.shell_context_processor
  def make_shell_context():
      return dict(db=DBConnectionHandler(), User=User, Role=Role)
  
  ```

  

- `flask shell`

  ```powershell
  >>> db
  <src.infra.config.connection.DBConnectionHandler object at 0x000001A7344C46D8>
  >>> User
  <class 'src.infra.tutorial3.auth.users.User'>
  >>> Role
  <class 'src.infra.tutorial3.auth.users.Role'>
  ```

  ```powershell
   Role.insert_roles()
  ```

  ![image-20221213101854657](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213101854657.png)

  - 이번엔 DOCTOR가 정순으로 나오네..
    - 다시 User관리에서 기존 User들의 Role_id 고쳐주기



##### flask shell에서 User의 새로운 필드role을 default or 로 추가해주기



```python
(venv) flask shell
>>> admin_role = Role.query.filter_by(name='Administrator').first()
>>> default_role = Role.query.filter_by(default=True).first()
>>> for u in User.query.all():
...     if u.role is None:
...             if u.email == app.config['MYBLOG_ADMIN']:
...                     u.role = admin_role
...             else:
...                     u.role = default_role
...
>>> db.session.commit()
```





#### utils > init_script.py에서 flask createadminsuer 명령어에 필수가된 email필드를 환경변수ADMIN_EMAIL로 채우고, is_super_user=True대신 Role로 Admin 명시해서 ADMINISRATOR USER 생성

- 기존

  ```python
  def init_script(app: Flask):
      @app.cli.command()
      @click.option("--username", prompt=True, help="사용할 username을 입력!")
      @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="사용할 password를 입력!")
      def createadminuser(username, password):
          click.echo('관리자 계정을 생성합니다.')
          with DBConnectionHandler() as db:
              user = User(username=username, password=password, is_super_user=True)
              db.session.add(user)
              db.session.commit()
          click.echo(f'관리자 계정 [{username}]이 성공적으로 생성되었습니다.')
  ```

- **email필드 및 role추가**

  - 명령어에 언더스코어 넣으려했는데 **인식안됨. 소문자 1줄만 가능한듯**

  ```python
  def init_script(app: Flask):
      @app.cli.command()
      @click.option("--username", prompt=True, help="사용할 username을 입력!")
      @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="사용할 password를 입력!")
      def createadminuser(username, password):
          click.echo('관리자 계정을 생성합니다.')
          
          with DBConnectionHandler() as db:
              role_admin = db.session.scalars(select(Role).where(Role.name == 'ADMINISTRATOR')).first()
              user = User(username=username, password=password, email=project_config.ADMIN_EMAIL, role=role_admin)
              db.session.add(user)
              db.session.commit()
              
          click.echo(f'관리자 계정 [{username}]이 성공적으로 생성되었습니다.')
  ```

- 실행전 환경변수 입력해주고 실행

  ```powershell
   .\venv\Scripts\activate
   .\run.ps1  
   
   flask createadminuser
  ```

![image-20221213104536005](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213104536005.png)

- **id를 다르게 생성하면, 생성이 된다.**

  - 이메일 중복검사는 form에서만 수행하는 중이라

  - **DB에서도 중복검사하도록 unique=True를 따로 준다.**

    ```python
    email = Column(String(128), nullable=False, index=True, unique=True)
    ```

- id를 동일하게 생성하면 에러난다

  ![image-20221213104706508](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213104706508.png)





- **unique관련 에러는 INtegrityError로 잡아서 try/Except 적용하기**

  - https://stackoverflow.com/questions/52075642/how-to-handle-unique-data-in-sqlalchemy-flask-pyhon
  - try commit, except rollaback을 기억하자

  ```python
  with DBConnectionHandler() as db:
      try:
          role_admin = db.session.scalars(select(Role).where(Role.name == 'ADMINISTRATOR')).first()
          user = User(username=username, password=password, email=project_config.ADMIN_EMAIL, role=role_admin)
          db.session.add(user)
          db.session.commit()
  
          click.echo(f'관리자 계정 [{username}]이 성공적으로 생성되었습니다.')
          except IntegrityError:
              db.session.rollback()
  
              click.echo(f'Warning) Username[{username}]  or Email[{project_config.ADMIN_EMAIL}]이 이미 존재합니다.')
  
              except:
                  db.session.rollback()
  
                  click.echo(f'Warning) 알 수 없는 이유로 관리자계정 생성에 실패하였습니다.')
  ```

  ![image-20221213105030708](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213105030708.png)



##### admin User add시 administrator는  보기에서 빼서,  명령어로만 생성할 수 있게하고, 추가 생성을 일단 막자

- form에서 selectfield에 안주면 된다.

  ```python
  class CreateUserForm(FlaskForm):
      #...
      def __init__(self, user=None, *args, **kwargs):
          #...
          with DBConnectionHandler() as db:
              roles = db.session.scalars(select(Role)).all()
              # self.role_id.choices = [(role.id, role.name) for role in roles]
              self.role_id.choices = [(role.id, role.name) for role in roles if role.name != Roles.ADMINISTRATOR.name]
  ```

  ![image-20221213105518280](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213105518280.png)



#### flask createrole도 만들어 놓기

```python
#### admin user 만들기 전에 role도 파이선으로 생성가능하도록 명령어로 만들기
@app.cli.command()
def createrole():
    click.echo('기본 Role들을 python으로 생성합니다.')
    try:
        Role.insert_roles()
        click.echo(f'초기 Role 테이블 데이터들이 생성되었습니다.')
        except IntegrityError:
            # 이미 생성할때 존재하면 생성안하도록 순회해서 걸릴 일은 없을 것 이다.
            click.echo(f'Warning) 이미 Role 데이터가 존재합니다.')
            except:
                click.echo(f'Warning) 알수없는 이유로 Role 데이터 생성에 실패했습니다.')
```



#### flask createdb도 만들어 놓기

```python
from create_database_tutorial3 import *
#...

    #### create_db도 미리 만들어놓기
    @app.cli.command()
    @click.option("--truncate", prompt=True, default=False)
    @click.option("--drop_table", prompt=True, default=False)
    @click.option("--load_fake_data", prompt=True, default=False)
    def createdb(truncate, drop_table, load_fake_data):

        create_database(
            truncate= True if truncate in ['y', 'yes'] else truncate,
            drop_table=True if drop_table in ['y', 'yes'] else drop_table,
            load_fake_data=True if load_fake_data in ['y', 'yes'] else load_fake_data
        )

```

![image-20221213112028882](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213112028882.png)



#### jinja에서 g.user.can(permission)로 기능별 Permission체크, g.user.is_(role)로 역할별 Permission체크를 하기 위해 @app_context_processor로  Permission(IntEnum), Role(Enum) inject해주기

- main > config > `__init__.py`속에 create_app에서

  ```python
  def inject_permission_and_roles():
      return dict(
          Permission=Permission,
          Roles=Roles,
      )
  
  ```

  ```python
      ## app context단위로 항상 떠있는 entity 객체value의 dict 반환 method 주입
      app.context_processor(inject_category_and_settings)
      app.context_processor(inject_today_date)
      app.context_processor(inject_permission_and_roles)
  ```



- view에서는 g.user.can (  **injtect된 IntEnum.해당기능Permission** ) or g.user.is_( **inject된 Enum.역할**)로 권한을 확인한다.







### view(jinja)에서 .is_super_user를  g.user.can() g.user.is_()로 대체하기

##### base.html

- staff도 admin이 보이기 시작

  ```html
  {% if g.user.is_(Roles.STAFF) %}
  ```

  

  ![image-20221213115850007](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213115850007.png)



##### auth > userinfo.html,  userinfo_form.html

![image-20221213120359128](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213120359128.png)

- 등급은 staff부터 보이도록 수정

  ```html
  <div style="padding-top: 1.5rem;">
      <h1 class="title is-size-4">{{ g.user['username'] }}</h1>
      {% if g.user.is_(Roles.STAFF) %}
      	<p class="subtitle is-size-6">직급: {{ g.user.role.name }}</p>
      {% endif %}
  </div>
  ```

  ![image-20221213120636971](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213120636971.png)

- auth > userinfo_form.html 도 마찬가지

  ![image-20221213120811099](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213120811099.png)

  - 등급은 staff만 보이도록 수정

    ![image-20221213120819773](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213120819773.png)



##### admin - index.html의 서브메뉴

- index.html

  ![image-20221213121420168](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213121420168.png)

  - 각 submenu가 권한별로 보이게 변경한다

    - **route와 함께 본다**

  - category는 메뉴에 해당하며 임원급이상만 수정가능 -> 보이는 것도 입원급이상만

    ```python
    @admin_bp.route('/category')
    @login_required
    @role_required(allowed_roles=[Roles.EXECUTIVE])
    def category():
    ```

    ```html
    <!-- Category -->
    {% if g.user.is_(Roles.EXECUTIVE) %}
    <p class="menu-label">
        <span class="icon"><i class="mdi mdi-shape-outline"></i></span>
        Category
    </p>
    <ul class="menu-list">
        <!-- 각 entity별 select route/tempalte완성시 마다 걸어주기 -->
        <li>
            <a class="{% if 'category' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.category') }}">
                <span class="icon"><i class="mdi mdi-menu"></i></span>
                Category 관리
            </a>
        </li>
    </ul>
    {% endif %}
    ```

    ![image-20221213121555401](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213121555401.png)

  - aritcle(Post), tag, banner 관리는 직원부터인데, 직원부터 admin접근가능하니까 submenu에는 if문을 안건다

  - User관리는 `직원제외 일반유저`에 대해서 
    - Staff부터 select 가능하되, 
    - ChiefStaff부터 add, edit, delete가능하게 한다

  





### 갑자기 STAFF이상 vs User를 가르기위한 expression 개발

#### Role user만 골라내기엔 permission >= 특정 role 형식이므로 Staff를 기준으로 잡고, 그 반대를 User로 골라낸다

- `@hybrid_property` is_employee를 만들 때는 쉽게 **미리 정해둔 is_(role)로 정의할 수 있다.**

```python
def is_(self, role_enum):
    role_perm = role_enum.value[-1]
	return self.role.permissions >= role_perm
    
@hybrid_property
def is_employee(self):
	return self.is_(Roles.STAFF)
```



#### 문제는 expression (정의된 메서드를 활용X)

- [연결안된 entity간의 연결 case 참고](https://stackoverflow.com/questions/67489770/sqlalchemy-create-expression-for-complex-hybrid-property)



##### subq 문법 복습

- **subq 문법 참고: `main_57_관계속성exists_subquery_연결정보가~.py`**

  - **join바로 붙이는 대신 `주체entity에 타entity 데이터(필드)를 이용한 확인용 subq`등을 위해 `join이 아닌 where에 직접key를 넣어서 연결`한다.**

    

  - **`타entity가 서로 관계`되어있을 땐, 내가 직접where절에 key를 붙이지말고, `주체entity.관계속성을 where`에 주면 `알아서key를 연결`하는데, `from에 2테이블을 올린 카다시안 곱 join`이 되어버리니, `subq용으로서 관계entity만 정보처리할 땐, .correlate(주체entity)`를 뒤에 붙인다.** 

    ```python
    #### where절에 .B관계속성
    
    # (1) 원래 join이 아닌, where절에 B관계속성만 갖다대면, JOIN + ON 유추 대신,
    #    => from에 2테이블 + where에 PK==FK를 유추해준다.
    #    => 여러 테이블(카다시안 곱)을 통한 join이 완성됨.
    stmt = (
        select(User.fullname)
        .where(User.addresses)
    )
    print(stmt)
    print('*'*30)
    # SELECT user_account.fullname
    # FROM user_account, address
    # WHERE user_account.id = address.user_id
    ```

  - **where절에 `where( 주체entity. 관계entity속성. any() )`를 주면, 더이상 카다시안 join을 만들지 않고,  `연결되는 관계Entity가 있는지 exists subquery`를 만들어, `관계entity에 연결된 데이터가 있으면 select 1로 True`표시를 하여  `subq로 넘어가는 주체entity의 1row가 존재`하게 된다 **

    ```python
    # (2) where절에 B관계속성.any()를 주면, from 2테이블 + where에 pk==fk 유추는 없어지고
    #     => from tableA 세팅 + where EXIST ( ) 가 세팅된다.
    #### my) where절에 .B관계속성.any()는 tableB의 exists() subquery를 자동으로 만들어준다.
    stmt = (
        select(User.fullname)
        .where(User.addresses.any())
    )
    print(stmt)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # WHERE EXISTS (SELECT 1
    #               FROM address
    #               WHERE user_account.id = address.user_id)
    ```

  - **관계entity의 `기본조건만으로 연결데이터의 존재유무` 대신 `연결된 데이터 + 관계entity 필드를 이용한 추가조건`을 .any()에 명시하여, `관계entity필드로 만드는 추가조건으로 exists subq`를 만들고, `연결+추가 관계entity필드조건을 만족하는 주제entity data`만 필터링 할 수 있게 된다.**

    - **Many관계의 Address entity의 email필드가 특정email로 차있는(`관계entity의 조건을 any(추가조건) -> where exists subq으로 걸어`)  필터링된  User의 fullname (`관계entity의 조건으로 필터링 된 주체entity 데이터들`)**

    ```python
    # (3) where절 .B관계속성.any()를 통한 tableB exists() subquery에 any()내부에는 tableB로 추가조건을 걸 수 있다.
    #    -> exists subquery는 상호연관쿼리라 메인에 있던 tableA의 pk속성 써서  join대신 연결해주니
    #       tableB.속성으로는, 자유롭게 조건을 추가할 수 있다.
    stmt = (
        select(User.fullname)
        # .where(User.addresses.any()) # => B관계속성.any()로 mainA.pk칼럼을 where에 사용한 B의 exists subquery()가 만들어진다.
        .where(User.addresses.any(Address.email_address == 'pear1.krabs@gmail.com')) # => B에 대한 exists subquery에 B속성으로 조건을 추가한다.
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # WHERE EXISTS (SELECT 1
    #               FROM address
    #               WHERE user_account.id = address.user_id
    #                   AND address.email_address = :email_address_1)
    # ('Pearl Krabs',)
    # ******************************
    ```

  - **`관계entity와 연결안된 주체entity`를 필터링하고 싶다면, `where(  ~ subq )`로서 `where( ~  주체entity.관계속성.any() )`로 기본연결조건에 `~으로 부정어`를 주면 된다.**

    - Address 테이블에 데이터 연결이 안된 User들
      - **주로 부정어로서 연결안된 주제Entity데이터들만 뽑을 때 더 많이 사용한다고 한다**

    ```python
    #### (4) main(tablaA)에대해, 관련된 tableB 정보가 없는 tableA 데이터를 구할땐 any() + 부정어(~)로 빠르게 구한다
    stmt = (
        select(User.fullname)
        .where(~User.addresses.any()) # => pf==fk 연결된 Address 테이블 Exist가 없는 것
    )
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT user_account.fullname
    # FROM user_account
    # WHERE NOT (EXISTS (SELECT 1
    #                    FROM address
    #                    WHERE user_account.id = address.user_id))
    # ('Squidward Tentacles',)
    # ('Eugene H. Krabs',)
    # ('Pearl Krabs',)
    # ******************************
    ```
    - **즉, `주체entity 중 관계entity(자식들?) 이 없는 경우`를 찾을 땐 where( ~ .any())를 쓴다.**

  - **주체entity가 Many일땐 `one주체.Many관계속성.any()`대신 `many주체.one관계속성.has()`를 쓰면 된다.**

    - User, Role(1) 관계에서  **찾는 주체entity가 Many User**이며, 
    - Role(One)에 연결되어있으면서 and Role.permission필드에 추가조건을 달려면, **has( 추가조건 )**을 달면 된다.
      - select( User ) . where (   User.  Role.  has(  추가조건 )   )

    ```python
    #### Many(Address) to One(User) Many where절의 one에 대한 exists subquery 빠르게 구현하기
    #### => 이 때는, .B(One)관계속성.has()로 구현하면 된다.
    
    # PropComparator.has() 메서드는 PropComparator.any()와 비슷한 방식으로 작동하지만, N:1 (Many-to-one) 관계에 사용됩니다.
    # - 예시로 "pkrabs"에 속하는 모든 Address 객체를 찾으려는 경우 이와 같습니다.
    #         => 연결테이블의 속성이 "pkrabs"인 모든 Address객체
    #         => select Address하는데,   [연결정보]가 .name이 pkrabs [인]  모든 데이터=> [EXISTS subquery]
    #            "연결정보가 ~인, 존재하는, 존재하지 않는" => EXISTS Subquery 생각 => .B관계속성.any() 나. .B관계속성.has()생각
    #            2테이블이므로, join대신 subquery로 해결한다
    #            ~에 속하는,  ~인 데이터 == where exists select 1 관계테이블조건
    #            연결정보가 있는, 거기서 데이터가 ~인 [연결정보를 가지고 있는] 모든 객체 -> join or subquery로 연결된 모든 데이터 SELECT 1을 EXISTS로..
    #
    #   my)  ~ 에 속하는, ~인, ~로 존재하는, ~가 아닌 => subquery내 해당데이터 select 1 후 -> EXISTS()로 씌워서 그런 상태인 데이터 다 가져오기
    stmt = (
        select(Address)
        # .where() # => 여기서 관계테이블에 대한 exists 조건(연결정보가 ~인, 연결정보가 ~로 존재하는, 연결정보가 ~ 에 속하는)이 필요하다? => 관계속성으로 만들어본다.
        # .where(User.addresses.has()) # => Many to One이면, any() 대신 has()로 exists subquery를 만든다.
        .where(Address.user.has(User.name == 'pkrabs')) # "연결정보가 ~로 존재하는" + "name이 xxx로" => has()이후 추가조건을 내부에 건다
    )
    #### has()에 any()를 쓴다면
    # -> sqlalchemy.exc.InvalidRequestError: 'has()' not implemented for collections.  Use any().
    print(stmt)
    for it in session.execute(stmt):
        print(it)
    print('*' * 30)
    # SELECT address.id, address.email_address, address.user_id
    # FROM address
    # WHERE EXISTS (SELECT 1
    #               FROM user_account
    #               WHERE user_account.id = address.user_id
    #                   AND user_account.name = :name_1)
    
    # (Address[id=4, email_address'pear1.krabs@gmail.com', user_id=6],)
    # (Address[id=5, email_address'pearl@aol.com', user_id=6],)
    # ******************************
    ```

    

##### 연결되지 않았다고 가정한 2 entity의  One관계객체(Role)의 permissions(int)가 상수보다 User 필터링

```sql
SELECT users.add_date, users.pub_date, users.id, users.username, users.password_hash, users.email, users.is_super_user, users.is_active, users.is_staff, users.avatar, users.sex, users.address, users.phone, users.role_id 
FROM users
WHERE CASE WHEN (EXISTS (SELECT *
			FROM roles
            WHERE roles.id = users.role_id 
                 AND roles.permissions >= :permissions_1)) THEN :param_1 
            ELSE :param_2 
      END 
                
ORDER BY users.add_date DESC

```



- `where의 안쪽 subquery`에는 각  `주제entity`인 from users의 데이터가 1줄씩 들어간다고 생각한다

  - 즉 subquery의 users.role_id가 1개의 바깥쪽 데이터에 상응된다.

- **그렇다면, subq를 먼저 만들어야한다.**

  - 기본조건은 두 entity를 (`주체entity를 1row로 생각`해서) key로 연결하는 `roles.id = users.role_id`이고
  - **추가조건은 연결된 role에 대해 `(User-m:Role-1이므로 연결role은  select에선 1개만 나타난다 생각하면)` 1user -> 연결role을 select에 1개만 찾아진 상태에서 `추가조건으로 해당 role의 .permssion이 특정상수보다 크거나 같은지`를 준다**
  - **추가조건을 만족하는 role이 select에서 나타날것인데, `중요한 것은 추가조건 만족 role이 존재하느냐?`이다.**
    - 얼핏생각하기엔 True/False로 바로 받고 싶지만, 
    - select에서 연결role.permission 대해 대소비교를 시행한것이 아니고
    - **where에 걸릴 1개의 role에 대해, `추가조건을 줬을때 만족한다면 select절에 등장`하게 될 것이다.**

- **그렇다면, `SQL에서 [관계 필드의 대소비교-> True/False] `는 `subq로 타entity연결시 기본key연결 + 추가조건으로 대소비교를 걸고 -> select (타entity) 대신 해당관계데이터가 exists되느냐/ 없느냐 -> 존재하면 True/존재안하면 False`로 변환해서 생각한다**

  ```python
  #### where에 들어갈 sql식으로서 True/False를 만드려면 case문을 써야한다?
  @is_employee.expression
  def is_employee(cls):
      #### 방법1
      # cls(User)를 sub를 사용할 주체entity의 1row씩 들어온다 생각하고
      # => SQL에서 관계 필드의 대소비교-> True/False는
      #    (1) subq key 연결조건 +  추가조건으로 대소비교를 걸고 ->
      #    (2) select 대신 해당 관계데이터가 exists되느냐/ 없느냐 ->
      #    (3) 존재하면 True/존재안하면 False로  case로 변환해서 where절에 들어갈 수 있게 한다
      subq = (
          exists()
          .where(Role.id == cls.role_id)
          .where(Role.permissions >= Roles.STAFF.value[-1])
      ).correlate(cls)
  ```

- **exists()의 인자를 생략하면 select * 에 exists문을 거는데, `exists(1)`을 주면 SELECT 1에 EXISTS를 걸어 성능이 더 좋을 수 있다.**

  ```python
  subq = (
      exists(1)
      .where(Role.id == cls.role_id)
      .where(Role.permissions >= Roles.STAFF.value[-1])
  ).correlate(cls)
  ```

  

- 이제 `외부사용용 exists문`을 **case문에 넣어 True/False로 변환하여 반환하도록 한다**

  ```python
  # (4) 존재하면 True/존재안하면 False로 => case로 변환해서 주체entity의 where절에 들어갈 수 있게 한다
  # return select([case([(subq, True)], else_=False)]).label("label")
  # return select([case([(subq, True)], else_=False)])
  return case([(subq, True)], else_=False)
  ```

  ```sql
  SELECT users.add_date, users.pub_date, users.id, users.username, users.password_hash, users.email, users.is_super_user, users.is_active, users.is_staff, users.avatar, users.sex, users.address, users.phone, users.role_id 
  FROM users
  WHERE CASE WHEN (EXISTS (SELECT 1
  FROM roles
  WHERE roles.id = users.role_id AND roles.permissions >= :permissions_1)) THEN :param_1 ELSE :param_2 END ORDER BY users.add_date DESC
  ```

- **사실 `exists문`은 `[case로 T/F변환] 없이 바로 where에 거는 expression으로 넣어도 T/F로 작동`한다 **

  ```python
  # WHERE CASE WHEN (EXISTS (SELECT 1
  # return case([(subq, True)], else_=False)
  
  # (5) exists문은 case로 T/F없이 바로 필터링 expression으로 작동된다.
  # WHERE EXISTS (SELECT 1
  return subq
  ```

  

- 요약

  ```sql
  SELECT users.add_date, users.pub_date, users.id, users.username, users.password_hash, users.email, users.is_super_user, users.is_active, users.is_staff, users.avatar, users.sex, users.address, users.phone, users.role_id 
  FROM users
  WHERE EXISTS (SELECT 1
  FROM roles
  WHERE roles.id = users.role_id AND roles.permissions >= :permissions_1) ORDER BY users.add_date DESC
  ```

  ```python
  @hybrid_property
  def is_employee(self):
      return self.is_(Roles.STAFF)
  
  
  @is_employee.expression
  def is_employee(cls):
      subq = (
          exists(1)
          .where(Role.id == cls.role_id)
          .where(Role.permissions >= Roles.STAFF.value[-1])
      ).correlate(cls)
      return subq
  ```

  





##### 연결된 one-many entity라면 쉽게 [관계entity 필드에 대한 추가조건이 걸린  exists] -> 주체entity.관계entity속성.any( 관계entity필드 조건)으로   한번에 구현

```sql
SELECT users.add_date, users.pub_date, users.id, users.username, users.password_hash, users.email, users.is_super_user, users.is_active, users.is_staff, users.avatar, users.sex, users.address, users.phone, users.role_id 

FROM users
WHERE (EXISTS (SELECT 1
				FROM roles
				WHERE roles.id = users.role_id 
               		AND roles.permissions >= :permissions_1)) 
ORDER BY users.add_date DESC
```

- where에 들어갈 expression식으로서 

```python
@is_employee.expression
def is_employee(cls):
    return cls.role.has(Role.permissions >= Roles.STAFF.value[-1])
```



#### route에서는 User 전체를 골라내는게 아니라 .where( ~  User.is_employee)로 employee가 아닌 순수User들만 골라내서 전달하기

- exists의 기본조건 + 추가조건에 대한 not을 생각하기보다는 **`전체에서 - 필터링 데이터 = 나머지 데이터`를 `.where(~  expression )`으로 골라낸다고 생각하자**

```python
@admin_bp.route('/user')
@login_required
@role_required(allowed_roles=[Roles.STAFF])
def user():
    page = request.args.get('page', 1, type=int)

    # stmt = select(User).order_by(User.add_date.desc())
    stmt = select(User)\
        .where(~User.is_employee)\
        .order_by(User.add_date.desc())

    print(stmt)

    pagination = paginate(stmt, page=page, per_page=10)
    user_list = pagination.items
    print(user_list)

    return render_template('admin/user.html',
                           user_list=user_list, pagination=pagination)
```



![image-20221213194018767](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213194018767.png)



#### 만든 짐에 [backend(cls) query(where)용] 각 role별 hybrid_property와 @.expression 다 만들어놓기

- 프론트에서는 sqlalchemy whrere절을 사용할 수 없으니 **g.user.is_( Enum ) 으로 확인하던 것을 `g.user.is_staff`형식으로 바로 사용가능해진다**
  - Roles Enum을 던질 필요가 없어진다.
  - **그러나 Permission은 던져야 기능별 if문이 가능해진다.**
    - g.user.can( Permission.구체적기능 )
- 백엔드에서는 **전체** 데이터 필터링을 위해 **where(   User(cls).is_ xxx)** 를 위해 **expression**을 정의해놓는다.
- **단점: Roles `enum을 인자로 받는게 아니라 직접의존해서 구성`하므로 `Roles 이넘 및 Role entity 에 대한 의존성`을 가져 변경시 같이 변경해줘야한다.**



```python
@hybrid_property
def is_chiefstaff(self):
    return self.is_(Roles.CHIEFSTAFF)

@is_chiefstaff.expression
def is_chiefstaff(cls):
    return cls.role.has(Role.permissions >= Roles.CHIEFSTAFF.value[-1])

@hybrid_property
def is_executive(self):
    return self.is_(Roles.EXECUTIVE)

@is_executive.expression
def is_executive(cls):
    return cls.role.has(Role.permissions >= Roles.EXECUTIVE.value[-1])

@hybrid_property
def is_administrator(self):
    return self.is_(Roles.ADMINISTRATOR)

@is_administrator.expression
def is_administrator(cls):
    return cls.role.has(Role.permissions >= Roles.ADMINISTRATOR.value[-1])

```



### 다시 view로 넘어오기





##### admin - index.html의 서브메뉴

- index.html

  - 각 submenu가 권한별로 보이게 변경한다
    - **route와 함께 본다**
  - category는 메뉴에 해당하며 임원급이상만 수정가능 -> 보이는 것도 입원급이상만
  - aritcle(Post), tag, banner 관리는 직원부터인데, 직원부터 admin접근가능하니까 submenu에는 if문을 안건다

  - User관리는 `직원제외 일반유저`에 대해서 

    - Staff부터 select 가능하되, 

    - ChiefStaff부터 add, edit, delete가능하게 한다

    - **admin/user.html**에서 추가/수정/삭제 버튼들을 모두 chief로 넘긴다

      - 작성해준 **hybrid_property를 활용한다( 이게 is_(ROLE)사용하므로)**

        ```html
        <!-- CheifStaff부터 보이게   -->
        {% if g.user.is_chiefstaff %}
        <div class="is-pulled-right">
            <!--  route) user_add route 및 user_form.html 개발 후 href채우기  -->
            <a href="{{url_for('admin.user_add')}}" class="button is-primary is-light">
                <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
                <span>User 추가</span>
            </a>
        </div>
        {% endif %}
        ```

        ![image-20221213200054323](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213200054323.png)

        ![image-20221213200121426](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213200121426.png)

      - 수정삭제도 마찬가지 처리

        ![image-20221213200504994](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213200504994.png)

      - **User add form - user_form.html에서 chiefstaff라도add시 역할을 staff이상 부여하면 안됨.**

        - **Add진입은 **

  - Banner를 올리고 User 내려 순서바꾸기

  - **Settings는 executive부터 보이게 하기**



#### role이 들어가는 CreatUserForm(생성/수정)form은 생성시, 현재진입 g.user의 정보를 받아 그것보다 더 작은 역할을 select field로 선택할 수 있게 한다

- 현재는 CreatUserForm 생성자에서 **현재 유저의 role비교없이, 관리자빼고 모든 Role을 selectfield로 제공하는 중**

  ```python
  class CreateUserForm(FlaskForm):
      #...
      def __init__(self, user=None, *args, **kwargs):
          self.user = user
          if self.user:
              super().__init__(**self.user.__dict__)
              self.username.render_kw = dict(disabled=True)
          else:
              super().__init__(*args, **kwargs)
  
          with DBConnectionHandler() as db:
              roles = db.session.scalars(select(Role)).all()
              self.role_id.choices = [(role.id, role.name) for role in roles if role.name != Roles.ADMINISTRATOR.name]
  
  
  ```

- 현재 route들은 수정시에만 user정보를 받아 들어간다

  ```python
  @admin_bp.route('/user/add', methods=['GET', 'POST'])
  @login_required
  @role_required(allowed_roles=[Roles.CHIEFSTAFF])
  def user_add():
      form = CreateUserForm()
  
      
      
  @admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
  @login_required
  @role_required(allowed_roles=[Roles.CHIEFSTAFF])
  def user_edit(id):
      with DBConnectionHandler() as db:
          user = db.session.get(User, id)
  
      form = CreateUserForm(user)
  ```



##### 현재 유저의 정보가 필요한 form은 g.user를 form객체 생성시 입력

- **전달받은 user는 수정시만 있고,생성시에는 안받아서 keyword로 받았다**

- **role choices를 위한g.user는 이제 User생성시 항상 받아야한다**

  - 항상받는 것은 **args**로 받고
  - 수정시만 받는 **user객체는 kwargs로 입력**하자

  ```python
      def __init__(self, current_user, user=None, *args, **kwargs):
          self.user = user
          # 수정시
          if self.user:
              super().__init__(**self.user.__dict__)
              self.username.render_kw = dict(disabled=True)
  
          else:
              super().__init__(*args, **kwargs)
  
          with DBConnectionHandler() as db:
              #### [ROLE2] 입력받은 현재유저의 role보다 낮은 것을 준다.
              roles_under_current_user = db.session.scalars(
                  select(Role)
                  .where(Role.permissions < current_user.role.permissions)
              ).all()
              self.role_id.choices = [(role.id, role.name) for role in roles_under_current_user]
  
  ```

  



- admin -> 자신보다 작은 executive까지부여 가능

  ![image-20221213234033694](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213234033694.png)

- chiefstaff -> 자신보다 낮은 staff, doctor까지 부여가능

  ![image-20221213234143379](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221213234143379.png)

- staff는 아예 user add 권한이 없음

##### Role끼리 비교할 때, permisson value까지 직접 내려가서 where 절에 cls(Role)과 current_user.role을 where비교하려면, 외부인자를 받을 수 있는 @hybrid_method로 정의해서 쓴다.

- 객체(row)끼리의 대소비교는 lt로 
  - https://stackoverflow.com/questions/1061283/lt-instead-of-cmp
  - lt를 정의하고 난 뒤, 그것을 기준으로 다른 모든 비교의 mixin을 만들어 상속해서 쓴다.

- **where절에 들어오는 각 데이터(cls)와 외부인자를 비교하려면 `@hybrid_method`로 정의하고 `expression`을 만들면 된다.**

```python
class Role(BaseModel):
    #...
    
	@hybrid_method
    def is_less_than(self, standard_role):
        return self.permissions < standard_role.permissions

    @is_less_than.expression
    def is_less_than(cls, standard_role):
        return cls.permissions < standard_role.permissions
```

```python
roles_under_current_user = db.session.scalars(
                select(Role)
                .where(Role.is_less_than(current_user.role))
            ).all()
```







##### is_staff가 hybrid_propery랑 기존 쓸모없는 기존 필드랑 겹쳐서 에러나는 것 처리(is_staff 및 is_super_user도 삭제)

- user에서 필드 삭제(`is_super_user` + `is_staff`)
  - route -> form ->  html(view, _form)에서 다 삭제



#### 버그 수정 User생성시 [nullable 흉내내는] role관계객체 안들어오면 기본값생성 -> form에서 오는 role_id(fk)까지 안들어왔을 때로 default채우기 조건 축소

```python
class User(BaseModel):
    __tablename__ = 'users'
    
	def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ## 원본대로 생성했는데, 따로 role객체를  role = Role( )로 부여하지 않았다면,
        ## (2) 그게 아니라면 role중에 default=True객체(default User객체)를 Role객체로 찾아 넣어준다.
        # if not self.role :
        #### form에서 role_id를 받아 줬는데도, role객체로 안들어왔다고 기본값으로 생성됨 주의
        #### => 관계객체가 안들어와서 동적으로 default로 생성할 땐,
        ####    self.role 뿐만 아니라 self.role_id의 fk도 안들어오는지 같이 확인
        if not self.role and not self.role_id:
```

- `if not self.role:` -> `if not self.role and not self.role_id:`





### User관리 필터링 제작기념 -> 직원관리 만들기



#### submenu에 User관리 말고 직원관리 만들기

- admin/index.html

  

```html
<li>
    <a class="{% if 'password' in request.path %}is-active{% endif %}"
       href="{{ url_for('admin.employee') }}">
        <span class="icon"><i class="mdi mdi-lock-outline"></i></span>
        직원 관리
    </a>
</li>
```



