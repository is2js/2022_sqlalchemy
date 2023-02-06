wikidocs 반영해나가기



### employee 직원관리 만들기


#### submenu에 User관리 말고 직원관리 만들기

- admin/index.html

  

```html
<!-- 직원 관리 for chiefstaff -->
{% if g.user.is_chiefstaff %}
<li>
    <a class="{% if 'password' in request.path %}is-active{% endif %}"
       href="{{ url_for('admin.employee') }}">
        <span class="icon"><i class="mdi mdi-lock-outline"></i></span>
        직원 관리
    </a>
</li>
{% endif %}
```



#### employee select - executive부터 입장 ( 나중에 부서관리로 나오면, chiefstaff가)

##### route

```python
@admin_bp.route('/employee')
@login_required
@role_required(allowed_roles=[Roles.EXECUTIVE])
def employee():
    page = request.args.get('page', 1, type=int)

    stmt = select(User) \
        .where(User.is_staff) \
        .order_by(User.add_date.desc())

    pagination = paginate(stmt, page=page, per_page=10)
    employee_list = pagination.items

    return render_template('admin/employee.html',
                           employee_list=employee_list, pagination=pagination)

```

##### user와는 다르게 추가되는 정보들

```
<!-- 가입일은 안쓰고,
     (1) 입사일(user_form : user-> staff수정시 입력되도록 해야함 + 직원추가시 입력되도록 해야함.)
     (2) 퇴사일(직원수정form에서만 -> 퇴사체크시 자동으로 입력)
     (3) 퇴사여부(퇴사클릭시 -> user로 밴 + 퇴사여부y + 퇴사일기록)를 추가 -->
     
<!-- 작업 수정삭제에  + (4)퇴사버튼 추가 -->
```

![image-20221214133800469](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221214133800469.png)

- 일단 role을 staff이상이 되는 순간 **db에선 User를 위해 nullable이지만, `User-> staff   or   staff로 추가`하는 순간부터는** 
  - 기존`phone`, `address`의 선택정보들을 -> **form에선 필**수로
  - `입사일`, `퇴사일`, 퇴사여부 -> `재직상태`(default 재직중, 휴직중, 퇴사) 외에 
  - `주민등록번호`
  - `이름`, `영어이름`을 추가로 입력 받는다.
- **그냥 User수정시 에서 staff로 role변경하지말고, `직원으로 추가`버튼을 누를때 `기존User정보를 받는 직원생성form`으로 가도록 하자**





### Role별 추가정보를 1:1 Table을 만들어서 저장하고, 직원route들에서는 User정보 + 해당정보를 묶어서 불러오는 cls method로 get_employee하기

#### Medi-Point의 모델과  role정보 찾는 방법

- Medi-Point 에서 User-Paitent정보-Doctor정보를 가져오는데서 차용

  - https://github.com/Dipali96/Medi-Point-Main/blob/master/app/models.py

  ![image-20221214175124495](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221214175124495.png)

- model

  ```python
  class User_Details(models.Model):
      
  	username = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
  	aadhaar = models.CharField(max_length=16,unique=True)
  	f_name = models.CharField(max_length=25, blank=True)
  	l_name = models.CharField(max_length=25, blank=True)
  	phone_no = models.IntegerField(blank=True,unique=True)
  	gender = models.CharField(max_length=1)
  	is_doctor = models.BooleanField(default = False)
  	is_patient = models.BooleanField(default = False)
  	g = geocoder.ip('me')
  	lat = models.FloatField(default=g.latlng[0])
  	lng = models.FloatField(default=g.latlng[1])
  
  	def __str__(self):
  		return self.username.username
  
  class Doctor(models.Model):
  	doctor = models.OneToOneField(User_Details, on_delete=models.CASCADE, primary_key=True)
  	field = models.ForeignKey(Speciality, on_delete=models.CASCADE)
  	is_sos = models.BooleanField(default = False)
  	min_fee = models.IntegerField(default=0)
  	yoe = models.IntegerField(default=0)
  	license_no = models.TextField(max_length=100, blank=True,unique=True)
  	is_approved = models.BooleanField(default = False)
  	qualification = models.CharField(max_length=100, blank=True)
  	def __str__(self):
  		return (self.doctor.username.username+" - "+ self.field.field)
  ```

- create / get -> **user를 받고, 그 user객체를 통해 생성한다.**

  - **생성시라면, `user정보 + 직원정보 다 받고` -> `user객체를 먼저 생성`하고 -> `user객체를 인자로 넣은 doctor`를 생성하는 과정을 가진다. **
    - **직접 직원생성은 생략할 듯. 무조건 User로 가입받고 `직원으로 버튼`을 통해 추가정보만 받아서 생성**

  ```python
  def dregister(request):
  	f = Speciality.objects.all()
  	if request.method=="POST":
  		username = request.POST['username']
  		password = request.POST['password']
  		if validate_mobile(request):
  			return render(request, "dregister.html",{'error_message':'Enter valid mobile number ', "f":f})
  		if validate_aadhaar(request):
  			return render(request, "dregister.html",{'error_message':'Enter valid Aadhaar number ', "f":f})
  		try:
  			with transaction.atomic():
  				user = User.objects.create_user(username=username, password=password)
  				profile = User_Details()
  				profile.username = user
  				profile.is_doctor = True
  				profile.aadhaar = request.POST['aadhaar']
  				profile.f_name = request.POST['f_name']
  				profile.l_name = request.POST['l_name']
  				profile.address = request.POST['address']
  				profile.gender = request.POST['gender']
  				profile.phone_no = request.POST['phone_no']
  				profile.save()
  				doc = Doctor()
  				doc.doctor = profile
  				field = request.POST['field']
  				if doc.is_sos :
  					doc.is_sos  =  request.POST['is_sos']
  				doc.min_fee = request.POST['min_fee']
  				doc.license_no = request.POST['license_no']
  				doc.yoe = request.POST['yoe']
  				fi = Speciality.objects.get(field=field)
  				doc.field = fi
  				doc.save()
  				return redirect("login")
  ```

  - 프로필정보에 user정보가 필요한 경우, Doctor정보만 넣을게 아니라 **user객체로 검색해서 찾는다.**

  ```python
  @login_required
  def dprofile(request):
  	user = request.user
  	print(user)
  	user_profile = User_Details.objects.get(username=user)
  	doc = Doctor.objects.get(doctor=user_profile)
      
  	if request.method=="POST":
  		user_profile.aadhaar = request.POST['aadhaar']
  		user_profile.f_name = request.POST['f_name']
  		user_profile.l_name = request.POST['l_name']
  		user_profile.address = request.POST['address']
  		user_profile.gender = request.POST['gender']
  		user_profile.phone_no = request.POST['phone_no']
  		user_profile.save()
  
  	return render(request, "dprofile.html",{"profile": user_profile, "doc":doc})
  ```

#### doctoerlyapi(REST)

- [model](https://github.com/zain2323/docterlyapi/blob/f2ea4ef74223acb92826a00d946ec50a530389dc/api/doctor/routes.py)

  ```python
  class User(db.Model, UserMixin):
      __tablename__ = 'user'
      __searchable__ = ["id", "name", "email", "password", "registered_at", "confirmed", "role"]
      id = db.Column(db.Integer, primary_key=True, nullable=False)
      name = db.Column(db.String(64), nullable=False)
      email = db.Column(db.String(120), unique=True, nullable=False, index=True)
      password = db.Column(db.String(102), nullable=False)
      registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
      confirmed = db.Column(db.Boolean, default=False, nullable=False)
      # dob = db.Column(db.Date, nullable=False)
      # gender = db.Column(db.String(8), nullable=False)
      role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
      token = db.Column(db.String(32), index=True, unique=True)
      token_expiration = db.Column(db.DateTime)
      doctor = db.relationship("Doctor", backref="user", lazy=True)
      patient = db.relationship("Patient", backref="user", lazy=True)
      
      @staticmethod
      def get_user(id):
          return User.query.get(id)
      
      
      
  class Doctor(db.Model):
      __tablename__ = "doctor"
      __searchable__ = ["id", "description", "image", "rating"]
      
      id = db.Column(db.Integer, primary_key=True, nullable=False)
      description = db.Column(db.String)
      image = db.Column(db.String, nullable=False)
      user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
      rating = db.relationship("Rating", backref="doctor", lazy=True)
      slots = db.relationship("Slot", backref="doctor", lazy=True)
      # Many to Many relationship between doctor and specializations
      specializations = db.relationship(
      "Specialization", secondary=doctor_specializations,
      primaryjoin=(doctor_specializations.c.doctor_id == id),
      secondaryjoin=(doctor_specializations.c.specialization_id == Specialization.id),
      backref=db.backref("doctor", lazy='dynamic'), lazy=True, cascade="all, delete")
      # Many to Many relationship between doctor and qualifications
      qualifications = db.relationship(
      "Qualification", secondary=doctor_qualifications,
      primaryjoin=(doctor_qualifications.c.doctor_id == id),
      secondaryjoin=(doctor_qualifications.c.qualification_id == Qualification.id),
      backref=db.backref("doctor", lazy='dynamic'), lazy=True, cascade="all, delete")
  
      def __repr__(self):
          return f"doctor:id {self.id}"
      
      def get_user(self):
          return self.user
      
      def add_specialization(self, specialization):
          self.specializations.append(specialization)
          search_api.add_to_index(self)
      
      def add_qualification(self, qualification, procurement_year, institute_name):
          statement = doctor_qualifications.insert().values(doctor_id=self.id, qualification_id=qualification.id,
                  procurement_year=procurement_year, institute_name=institute_name)
          db.session.execute(statement)
          search_api.add_to_index(self)
      
      def get_doctor_qualifications_and_info(self):
          query = db.select(doctor_qualifications.c.institute_name, doctor_qualifications.c.procurement_year).filter(doctor_qualifications.c.doctor_id == self.id)
          result = db.session.execute(query).all()
          qualifications_list = self.qualifications
          procurement_year_list = []
          institute_name_list = [] 
          for info in result:
              institute_name_list.append(info[0])
              procurement_year_list.append(info[1])
          
          info_dict = {
              "qualification_name": qualifications_list,
              "procurement_year": procurement_year_list,
              "institute_name": institute_name_list
          }
          return info_dict
      
  def get_qualifications_info(self):
          query = db.select(doctor_qualifications.c.institute_name, doctor_qualifications.c.procurement_year).filter(doctor_qualifications.c.doctor_id == self.id)
          result = db.session.execute(query).all()
          qualifications_list = [str(q) for q in self.qualifications]
          procurement_year_list = []
          institute_name_list = [] 
          for info in result:
              institute_name_list.append(str(info[0]))
              procurement_year_list.append(str(info[1]))
          
          payload = {
              "qualification_name": qualifications_list,
              "procurement_year": procurement_year_list,
              "institute_name": institute_name_list
          }
          return payload
  
      def get_specializations_info(self):
          try:
              specialization = self.specializations[0]
              return {"id": str(specialization.id), "name": str(specialization.name)}
          except:
              return {}
          
  doctor_specializations = db.Table("doctor_specializations",
      db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), primary_key=True, nullable=False),
      db.Column('specialization_id', db.Integer, db.ForeignKey('specialization.id', ondelete="RESTRICT"), primary_key=True, nullable=False)
  )
  
  doctor_qualifications = db.Table("doctor_qualifications",
      db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), primary_key=True, nullable=False),
      db.Column('qualification_id', db.Integer, db.ForeignKey('qualification.id', ondelete="RESTRICT"), primary_key=True, nullable=False),
      db.Column('procurement_year', db.Date, nullable=False),
      db.Column('institute_name', db.String, nullable=False)
  )
  ```

- create

  - user를 만들고, **user객체를 넣어서 doctor를 만든다.**

  ```python
  @doctor.route("/new", methods=["POST"])
  @body(CreateNewDoctorSchema)
  @response(DoctorSchema)
  def new(kwargs):
      """Registers a new doctor"""
      description = kwargs.pop("description")
      new_user = User(**kwargs)
      password = kwargs["password"]
      new_user.set_password(password)
      new_doctor = Doctor(user=new_user, description=description, image="default_doctor_image.jpg")
      db.session.add(new_doctor)
      db.session.add(new_user)
      db.session.commit()
      update_doctor_cache(update=True)
      return new_doctor
  
  ```

- get

  - user객체를 찾거나, 현재user로 -> doctor를 찾는다

  ```python
  @doctor.route("/info", methods=["GET"])
  @authenticate(token_auth)
  @cache_response_with_token(prefix="current_doctor", token=token_auth)
  @response(DoctorInfoSchema)
  def get_current_doctor_info():
      """Get your current info"""
      current_user = token_auth.current_user()
      CACHE_KEY  = "current_doctor" + current_user.get_token()
      doctor = Doctor.query.filter_by(user=current_user).first_or_404()
      qualifications_info = doctor.get_doctor_qualifications_and_info()
      doctor_info = prepare_doctor_info(doctor, qualifications_info)
      cache.set(CACHE_KEY, DoctorInfoSchema().dump(doctor_info))
      return doctor_info
  ```

  - **user정보가 필요없다면, doctor테이블만 조회**하면 된다.

  ```python
  @doctor.route("/all", methods=["GET"])
  @authenticate(token_auth)
  @cache.cached(timeout=0, key_prefix="registered_doctors", forced_update=does_doctor_cache_needs_update)
  @response(DoctorInfoSchema(many=True))
  def get_all():
      """Returns all the doctors"""
      doctors_info = []
      doctors = Doctor.query.all()
      for doctor in doctors:
          qualifications_info = doctor.get_doctor_qualifications_and_info()
          doctor_info = prepare_doctor_info(doctor, qualifications_info)
          doctors_info.append(doctor_info)
      return doctors_info
  ```

  

#### DB User변경하는 김에,  최근접속시간 + sqlite 오류보정 코드 적용하기

- 최근접속시간 참고: https://wikidocs.net/106776

##### 최근 접속시간 추가하기

- 필드

  ```python
  # 최근방문시간 -> model ping메서드 -> auth route에서 before_app_request에 로그인시 메서드호출하면서 수정하도록 변경
      last_seen = Column(DateTime, nullable=False, default=datetime.datetime.now)
  ```

- entity 인스턴스 메서드

  ```python
  # 최근방문시간 -> model ping메서드 -> auth route에서 before_app_request에 로그인시 메서드호출하면서 수정하도록 변경
  def ping(self):
      self.last_seen = datetime.datetime.now()
      with DBConnectionHandler() as db:
          db.session.add(self)
          db.session.commit()
  ```

  

- auth_bp에다가 `before_app_request`인 **load_logged_in_user**할때 최근접속시간 갱신

  ```python
  @auth_bp.before_app_request
  def load_logged_in_user():
      user_id = session.get('user_id')
      if not user_id:
          g.user = None
      else:
          with DBConnectionHandler() as db:
              g.user = db.session.get(User, user_id)
              # 요청시마다 로그인된 유저에 한해, 최근접속시간 변경
              g.user.ping()
  ```



###### load_logged_in_user의 g.user로 ping을 호출하면 안된다!!

- g.user에 넣어준 것은 **`차후 login_required 내부사용을 위한 것`으로, 미리 g.user.ping()을 호출해버리면, db를 사용하여 detach에러가 뜬다.**
  - load_logged_in_user의 세션과 **별개 세션으로 열어서 처리**해야한다



```python
@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if not user_id:
        g.user = None
    else:
        with DBConnectionHandler() as db:
            g.user = db.session.get(User, user_id)
            # 1) 내부 db 세션으로 ping하고 -> 여기 db 세션으로 user를 배정하면 -> 세션 중복
            # 2) 여기 db 세션으로 g.user 배정 후, 해당 객체를 update한다고 접근하면 -> subquery 1회 이미 사용된 것으로 에러
            #  => g.user가 g.user.role 등을 required를 처리할 때 db를 조회해야한다
            #  => last_seen업뎃은 g.user와 별개로 따로 해줘야한다.
        
        # g.user와 별개세션으로 로그인된 유저의 ping() -> last_seen 업뎃
        User.ping_by_id(user_id)
```

```python
class User(BaseModel):
    #...
    
	@classmethod
    def ping_by_id(cls, user_id):
        with DBConnectionHandler() as db:
            stmt = (
                update(cls)
                .where(cls.id == user_id)
                .values({
                    cls.last_seen : datetime.datetime.now()
                })
            )

            db.session.execute(stmt)
            db.session.commit()
```





##### prod - postgre에서도 id가 autoincrement되기 위해 id칼럼들 다 수정

```python
id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
```



##### sqlite오류대비 네이밍컨벤션 적용하기

- 참고

  - [위키1](https://wikidocs.net/106770)

  - [위키2](https://wikidocs.net/81059#sqlite)

  - flask-sqlalchemy의 경우

    ```python
    naming_convention = {
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
    db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
    ```

- SQLite 설정 수정하기

  SQLite 데이터베이스는 ORM을 사용할 때 몇 가지 문제점이 있다. 이것은 SQLite 데이터베이스에만 해당하고 **PostgreSQL이나 MySQL 등의 다른 데이터베이스와는 상관없는 내용**이다. 앞으로의 진행을 원활하게 하기 위해 **SQLite가 발생시킬 수 있는 오류를 먼저 해결**하고 넘어가자.

  - ```python
    #__init__.py
    from flask import Flask
    from flask_migrate import Migrate
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import MetaData
    
    import config
    
    naming_convention = {
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
    db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
    migrate = Migrate()
    
    def create_app():
        app = Flask(__name__)
        app.config.from_object(config)
    
        # ORM
        db.init_app(app)
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith("sqlite"):
            migrate.init_app(app, db, render_as_batch=True)
        else:
            migrate.init_app(app, db)
        from . import models
        (... 생략 ...)
    ```

- 이와 같이 수정하면 데이터베이스의 프라이머리 키, 유니크 키, 인덱스 키 등의 이름이 변경되므로 `flask db migrate` 명령과 `flask db upgrade` 명령으로 데이터베이스를 변경해야 한다.

  > 데이터베이스에서 디폴트 값으로 명명되던 프라이머리 키, 유니크 키 등의 제약조건 이름을 수동으로 설정한 것이다.

  ```no-highlight
  (myproject) c:\projects\myproject>flask db migrate
  (myproject) c:\projects\myproject>flask db upgrade
  INFO [alembic.runtime.migration] Context impl SQLiteImpl.
  ```

  

  점프 투 플라스크

  **SQLite 버그패치**

  

  SQLite 데이터베이스에서 사용하는 인덱스 등의 제약 조건 이름은 MetaData 클래스를 사용하여 규칙을 정의해야 한다. 만약 이름을 정의하지 않으면 SQLite 데이터베이스는 다음과 같은 제약 조건에 이름이 없다는 오류를 발생시킨다.

  ```no-highlight
  ValueError: Constraint must have a name
  ```

  또 SQLite 데이터베이스는 `migrate.init_app(app, db, render_as_batch=True)`처럼 render_as_batch 속성을 True로 지정해야 한다. 만약 이 속성이 False라면 다음과 같은 오류가 발생한다.

  ```no-highlight
  ERROR [root] Error: No support for ALTER of constraints in SQLite dialectPlease refer to the batch mode feature which allows for SQLite migrations using a copy-and-move strategy.
  ```

  `pybo/__init__.py` 파일에서 수정한 내용은 SQLite 데이터베이스를 플라스크 ORM에서 정상으로 사용하기 위한 것이라고 이해하면 된다.



##### 일반 sqlalchemy에 적용하기

- [참고](https://stackoverflow.com/questions/22129457/adding-naming-convention-to-existing-database)

- infra>config>`base.py`

  ```python
  from sqlalchemy import MetaData
  from sqlalchemy.ext.declarative import declarative_base
  
  Base = declarative_base()
  
  # sqlite migrate 오류시 발생할 수 있는 버그 픽스
  naming_convention = {
      "ix": 'ix_%(column_0_label)s',
      "uq": "uq_%(table_name)s_%(column_0_name)s",
      "ck": "ck_%(table_name)s_%(column_0_name)s",
      "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
      "pk": "pk_%(table_name)s"
  }
  
  Base.metadata = MetaData(naming_convention=naming_convention)
  
  ```

  

### docterylyapi 차용해서 Employee entity에  직원용 정보추가하기

- 직원필드 참고 ERD: https://github.com/itosamto/portfolo2/blob/master/img/ERD_milvusSecurity.jpg

- model: https://github.com/zain2323/docterlyapi/blob/f2ea4ef74223acb92826a00d946ec50a530389dc/api/models.py#L65

##### role 직원추가정보 entity 만들기

- name, eng_name
- 입사일, 퇴사일, 재직상태
  - hybrid = 연차
- 주민등록번호
  - hybrid = 생일

```python
class Employee(BaseModel):
    __tablename__ = 'employees'

    # id = Column(Integer, primary_key=True)
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    # 연결고리이자, user로부터 -> employee의 정보를 찾을 때, 검색조건이 될 수 있다.
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    # 부서

    name = Column(String(40), nullable=True)
    sub_name = Column(String(40), nullable=True)
    birth = Column(String(12), nullable=True)

    job_status = Column(IntEnum(JobStatusType), default=JobStatusType.재직, nullable=True)
    join_date = Column(DateTime, nullable=True)
    resign_date = Column(DateTime, nullable=True)

    # qrcode, qrcode_img: https://github.com/prameshstha/QueueMsAPI/blob/85dedcce356475ef2b4b149e7e6164d4042ffffb/bookings/models.py#L92

    def __repr__(self):
        return '<Employee %r>' % self.id
```





```python
class User(BaseModel):
    
    #...
    
	employee = relationship('Employee', backref=backref('user', lazy='subquery'), lazy='dynamic')
```





```python
create_database(truncate=False, drop_table=False, load_fake_data=False)
```



#### 직원정보를 생성하려면, User 관리 내 [직원 전환]버튼 -> route  ->직원정보 입력form with 선택된 user 로 나가야한다

##### admin/user.html에 직원전환 버튼 추가하기

```html
<a href="{{url_for('admin.employee_add', user_id=user.id)}}" class="tag is-warning is-light">
    <span class="icon">
        <i class="mdi mdi-trash-can-outline"></i>
    </span>
    직원 전환
</a>
```



![image-20221215000736201](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221215000736201.png)



##### 직원전환 employee_add  route(GET)

- 생성임에도 불구하고 **user의 하위 entity라서 수정/삭제처럼 user_id를 받는다.**
- **일단 화면을 띄워야해서 form 부터 만든다**

```python
@auth_bp.route('/employee/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_add(user_id):
    user = User.get_by_id(user_id)

    form = EmployeeForm(user)
```



##### EmployeeForm 직원정보만 담은 form만들기 (기존 User의 필수정보는, 자체form에서 땡겨올 예정 어차피 user를 찾으니, user를 넣어서 정보 담은체)



```python
class EmployeeForm(FlaskForm):

    name = StringField('이름', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=40, message="최대 2~40글자까지 입력 가능")
    ])

    sub_name = StringField('영어 이름', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=40, message="최대 2~40글자까지 입력 가능")
    ])

    birth = StringField("주민등록번호", validators=[
        Regexp("\d{6}[ |-]?\d{6}", message="이어서 or 중간공백 or 하이픈(-)으로 숫자 12개 입력"),
        DataRequired(message="필수 입력")],
                        filters=(remove_empty_and_hyphen,),
                        description="123456-123456(하이픈) or  123456 123456(공백) or 123456123456(붙여서)"
                        )
    job_status = RadioField('성별', validators=[DataRequired()],
                            choices=JobStatusType.choices(),
                            default=JobStatusType.재직.value,
                            coerce=int,
                            )
    # 연차계산등을 위해, DateTime으로 해야한다? Date면 충분
    #### form의 default시간은 자신의 컴퓨터시간인 datetime.datetime.now()로 들어가게 하고, 백엔드에서 utc로 바꿔서 저장해야한다.
    # https://github.com/rmed/akamatsu/blob/0dbcd2a67ce865d29fb7d7049e627d322ea8e361/akamatsu/views/admin/pages.py#L127
    join_date = DateField('입사일',
                          description='Will be stored as UTC',
                          # format='%Y-%m-%d %H:%M',
                          format='%Y-%m-%d',
                          default=datetime.datetime.now()  # Will be stored as UTC
                          )

    # resign_date는 입력x

    #### role을 여기서 정한다(user add에선 삭제?)
    role_id = SelectField(
        '직위',
        choices=None,
        coerce=int,
        validators=[
            DataRequired(message="필수 선택"),
        ],
    )

    def __init__(self, current_user, employee=None, *args, **kwargs):

        self.employee = employee
        if self.employee:
            super().__init__(**self.employee.__dict__)
        else:
            super().__init__(*args, **kwargs)

        # 직원전환 상사 [current_user]로 부여할 수 잇는 role을 채운다.
        with DBConnectionHandler() as db:
            roles_under_current_user = db.session.scalars(
                select(Role)
                .where(Role.is_less_than(current_user.role))
            ).all()
            self.role_id.choices = [(role.id, role.name) for role in roles_under_current_user]

    def validate_birth(self, field):
        if self.employee:  # 수정시 자신의 제외하고 데이터 중복 검사
            condition = and_(Employee.id != self.employee.id, Employee.birth == field.data)
        else:  # 생성시 자신의 데이터를 중복검사
            condition = Employee.birth == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 주민등록번호 입니다')

```

##### employee_add route (GET) -> userInfoForm, employeeform 2개를 쓴다

```python
@admin_bp.route('/employee/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_add(user_id):
    user = User.get_by_id(user_id)

    user_form = UserInfoForm(user)
    employee_form = EmployeeForm(g.user)

    #### 직원으로 변환되면, user의 role부터 미리 선택된 것으로 바뀌어야한다.
    # user.role = Role.get_by_name('form에서 선택된 역할')
    # Employee(user=user)

    return render_template('admin/employee_form.html',
                           user_form=user_form,
                           employee_form=employee_form
                           )

```



##### user_form.html(admin)기반으로 employee_form.html을 만든 뒤, userinfo_form.html의 안쪽내용만 가져와서 복붙

- UserInfoForm

  ![image-20221215113744869](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221215113744869.png)

- UserForm

  ![image-20221215113807610](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221215113807610.png)



#### 2 Form을 한번에 submit못하니, tab에 2개걸기 vs  상속한 form쓰기?



##### form을 따로쓰되, tab에 2개form을 걸어놓고, userform추가정보가 비었으면, userform active -> post이후 employee채우라고하기

- tab을 쓴다면

  1. `b-tabs`에 `v-model 적용`, @input 적용(참고)

     ```html
     <b-tabs type="is-boxed" v-model="activeTab" @input="tabClicked(activeTab)">
     
     ```

  2. base.html에 초기변수를 index(activeTab) =0으로 주기

     - 참고: 메서드도 주기

     ```js
     data: {
           activeTab: 0,
             },
                 
     methods: {
     	tabClicked(index) {
                     if (index === 1) alert('Index 1 is the third 	button');
                 },
             },
     ```

  3. tab html에 route에서 받은 activetab을 반영하게 하기

     ```html
     {% block vue_script %}
     <script>
         app._data.activeTab = {{ active_tab or 0 }};
     </script>
     {% endblock vue_script %}
     ```

  4. route에서 시작할 tab 지정해서 내려주기

     ```python
     @admin_bp.route('/setting', methods=['GET'])
     @login_required
     @role_required(allowed_roles=[Roles.ADMINISTRATOR])
     def setting():
         s_dict = Setting.to_dict()
     
         # db객체 list대신 dict를 건네준다.
         return render_template('admin/setting.html', s_dict=s_dict, active_tab=1)
     ```

     ![image-20221215130804761](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221215130804761.png)

     ![image-20221215130814171](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221215130814171.png)





##### 아무래도, 각 정보는 User따로 Employee따로 저장하더라도, 상속한 form에서 한번에 받아서 처리하면 더 좋을 것 같다.



### 추가정보UserInfoForm를 상속한 EmployeeForm에선 부모field를 동적으로 필수필드로 만들어서 쓰기



### Employee Create





##### form 정렬 관련 정리

- [bulma column 가운데 정렬 관련](https://stackoverflow.com/questions/50398678/center-content-in-bulma-column) 

  - `<div class="columns is-centered">...</div>` centeres the column. You have to set a width for the column inside to make it work. The class is-narrow takes only the space it needs.

  - **`columns`에는 `is-centred is-vcentered`만 주면 알아서 내부요소들을 정렬시킬건데**

    - **`column`들이 크기를 줘야 `has-text-centerd`로 내부요소들이 가운데 정렬된다.**

    - **크기는 is-2,3,4, 도 가능하고 `is-narrow`로도 적용된다.**

    ```html
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.1/css/bulma.min.css" rel="stylesheet" />
    <div class="features">
      <div class="container">
        <div class="columns is-centered is-vcentered is-mobile">
          <div class="column is-narrow has-text-centered">
            <div class="circle">
              <font-awesome-icon col size="2x" :icon="['fas', 'tasks']" />
            </div>
            Features
          </div>
        </div>
      </div>
    </div>
    ```

    

  - **만약 b-field처럼 flex로 싸고 있는 내부요소는?**

    - `is-justify-content-centerd`로 주면 된다.
    - **flex가 아닌데 만들고 싶다면, `is-flex`와 같이 준다.**

  - **input의 is-4크기 vs description 풀 크기**

    - **column에 is-4를 주지말고**
      - 각 input을 싼 `span`과  dscrip을 싼 `p태그`에 `column is-4`   + `column py-0`으로  각각을 칼럼으로 취급하니 정렬됬다.
        - 참고로 my-0은 안먹고 py-0은 먹힌다

    ```html
    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
        <div class="column is-2 is-align-items-center is-flex ">
            <span class=" has-text-grey-light">{{form.phone.label(class='label')}}</span>
        </div>
         <!-- is-6삭제 -->
        <div class="column "> 
             <!-- 각각을 column으로 생각하고 input을 싼 span에는 column is-6 -->
            <span class="has-text-black-ter column is-6">{{ form.phone(class='input') }}</span>
             <!-- desc를 싼 p태그에 column + py-0 -->
            <p class="help has-text-primary-dark column py-0">
                {{ form.phone.description }}
            </p>
        </div>
    </div>
    ```



##### datefield 정리

- **`Datefiled`는 자체picker의 format이 정해져있어서, `format="%Y-%m-%d"`를 고정적으로 줘야한다.**

  ```python
  join_date = DateField('입사일',
                        description='Will be stored as UTC',
                        # format='%Y-%m-%d %H:%M',
                        format='%Y-%m-%d', 
                        default=datetime.datetime.now().date(), 
                       )
  ```

- **form.필드는 `String이면서 %Y-%m-%d로 변환된 데이터`만 받을 수 있다.**

  - buefy를 `date`변수(Date타입)으로 초기화하고
  - buefy의 받아먹는 type='hidden'을 만들 때, **watch**에서 
    - `buefy datepicker`의 v-model : `date`
    - `vue watch` : date: function ->  `stringDate`로 변환한 것을
    - `wtf DateField`의 datepicker form은 v-model: `stringDate`로 받아먹는다.

  ```html
  {% block vue_script %}
  <script>
      app._data.date = new Date('{{ form.join_date.data or today_date() }}')
  </script>
  {% endblock vue_script %}
  ```

  ```js
      data: {
          date: null,
          stringDate: null,
  
      },
      
      
      watch: {
   date: function (date) {
  
                  this.stringDate = this.convertDateYyyymmdd(date)
  
              },
                  
  methods: {
      convertDateYyyymmdd(value) {
                  if (value == null) return null;
                  var js_date = new Date(value);
  
                  // 연도, 월, 일 추출
                  var dd = String(js_date.getDate()).padStart(2, '0');
                  var mm = String(js_date.getMonth() + 1).padStart(2, '0'); //January is 0!
                  var yyyy = js_date.getFullYear();
                  return yyyy + '-' + mm + '-' + dd;
              },
  ```

- **form의 return .data는 Date타입으로 와서 필드값으로 바로 넣어줄 수 있다.**

  ```python
  if form.validate_on_submit():
      print("form.join_date.data>>>>", form.join_date.data, type(form.join_date.data))
      # form.join_date.data>>>> 2022-12-02 <class 'datetime.date'>
  ```



##### 그외 Field관련 정리

- 퇴사상태가 되면, 퇴직일이 자동으로 채워질 예정이므로 **직원생성form에는 재직상태 필드 및 퇴직일 필드가 없다**

- UserInfoForm을 상속했으므로 **상속한 부모를 super().__init--()을 호출할 건데, `UserInfoForm입장에선 기존정보를 업고가는 수정Form`이므로 `해당user`객체를 받아야한다.**

  - 따라서 EmployeeForm은 UserInfoForm(수정)을 위한 `user`객체를 받고, 동적인 role부여를 위해 `current_user(g.user)`도 인자로 받는다.

- **UserInfoForm에서는 Optional이 대부분인데 `여기서 동적으로 self.필드로 validators를 채워 필수필드`로 만든다.**

  - list기반이라, 초기화시에는 `= [DataRequired() ]`로 초기화한다

    ```python
    self.sex.validators = [DataRequired()]
    ```

- **radio같이 원래 form.필드 를 안쓰고, 순회하면서 subfield를 쓰는 경우 `동적으로 .deafult=`로 넣어주는게 아니라 `특정필드.data = 기본값`을 채워줘야한다**

  - **이 때, 수정필드로서 기존데이터를 가지고 있을 수 있으니, `if not 필드.data`시에만 채워준다.**

    ```python
    if not self.sex.data:
        self.sex.data = SexType.여자.value
    ```

- **File필드는 필수로 만들때 주의사항이 있어서 `항상 동적 필수`로 만들어야한다**

  - 필수로 만들었지만, **기존에 avatar에 파일이 아닌 경로가 저장된 유저**의 경우 **file객체가 아니라서 FileRequired에 걸린다.**

  - **수정form필드로서 `기존에 경로조차  저장안된, 아무것도 없을때만 FileRequired`를 `validators에 추가`해야한다. 이미 validators에는 많은 File관련 검사기들이 존재하기 때문**

    ```python
    if not self.avatar.data:
        # print("아바타에 아무것도 없으면 FileRequired가 적용된다.>>>", self.avatar.data)
        self.avatar.validators.append(FileRequired('직원이 될 예정이시라면, 사진을 업로드 해주세요!'))
    # else:
        # print("아바타.data에 이미 존재해서 FileRequired 생략>>>", self.avatar.data)
        # pass
    ```

- **동적으로 Role의 choices를 채울 때, current_user의 role보다 적은 지위만 포함하는데 `User`는 제외(User이상)시키도록 추가조건을 건다. 직원전환인데 User가 있으면 안된다.**

  ```python
  # 직원전환 상사 [current_user]로 부여할 수 잇는 role을 채운다.
  with DBConnectionHandler() as db:
      #### 직원전환시 USER는 옵션에서 제외해야한다. -> 나보다는 낮지만,  STAFF이상으로 -> where. Role.is_STAFF 추가
      roles_under_current_user = db.session.scalars(
          select(Role)
          .where(Role.is_less_than(current_user.role))
          .where(Role.is_(Roles.STAFF))
      ).all()
      self.role_id.choices = [(role.id, role.name) for role in roles_under_current_user]
  ```

  

#### EmployeeForm(UserInfoForm)

 ```python
class EmployeeForm(UserInfoForm):
    name = StringField('이름', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=40, message="최대 2~40글자까지 입력 가능")
    ])

    sub_name = StringField('영어 이름', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=40, message="최대 2~40글자까지 입력 가능")
    ])

    birth = StringField("주민등록번호", validators=[
        Regexp("\d{6}[ |-]?\d{6}", message="주민번호는 12자리를 이어서 or 공백 or 하이픈(-)으로 구분해서 입력해주세요"),
        DataRequired(message="필수 입력")],
                        filters=(remove_empty_and_hyphen,),
                        description="123456-123456(하이픈) or  123456 123456(공백) or 123456123456(붙여서)"
                        )
    job_status = RadioField('재직상태', validators=[DataRequired()],
                            choices=JobStatusType.choices(),
                            default=JobStatusType.재직.value,
                            coerce=int,
                            )
    # 연차계산등을 위해, DateTime으로 해야한다? Date면 충분
    #### form의 default시간은 자신의 컴퓨터시간인 datetime.datetime.now()로 들어가게 하고, 백엔드에서 utc로 바꿔서 저장해야한다.
    # https://github.com/rmed/akamatsu/blob/0dbcd2a67ce865d29fb7d7049e627d322ea8e361/akamatsu/views/admin/pages.py#L127
    join_date = DateField('입사일',
                          description='Will be stored as UTC',
                          # format='%Y-%m-%d %H:%M',
                          format='%Y-%m-%d',
                          # 이것은 wtf datepicker가 올려주는 형식과 동일해야해서 고정이다. 받는 것도 string만 받는다. 하지만 return는 filter없이도 date로 가져간다.
                          default=datetime.datetime.now().date(),  # default는 vue에서 알아서 준다.
                          )

    # resign_date는 입력x

    #### role을 여기서 정한다(user add에선 삭제?)
    role_id = SelectField(
        '직위',
        choices=None,
        coerce=int,
        validators=[
            DataRequired(message="필수 선택"),
        ],
    )

    # def __init__(self, current_user, employee=None, *args, **kwargs):
    def __init__(self, user, current_user, employee=None, *args, **kwargs):

        self.employee = employee
        if self.employee:
            # super().__init__(**self.employee.__dict__)
            super().__init__(user, **self.employee.__dict__)
        else:
            # super().__init__(*args, **kwargs)
            ## 상속한 부모 form UserInfoForm는 무조건 수정상태로 쓰니, user를 넣어준다.
            super().__init__(user, *args, **kwargs)

        #### 부모form에선 선택이었던 것들을 ===> 필수form으로 변경한다
        # - avatar의 경우 다른 Optional이외에 validators들이 존재했기 때문에 추가로 넣어준다.
        # - validators는 list를 기본폼으로 하고 잇어서, [ Optional() ]을 초기화할때 list로 쏴서 넣어주면 초기화된다. ex> = [ DataRequired() ]
        self.sex.validators = [DataRequired()]
        # self.sex.default = SexType.여자.value
        # 외부에서 직접 deafult를 줄 땐, .data에 value를 집어넣어놔야한다
        #### 이미 값이 들어가잇을 수 있기 때문에, 값이 안들어가있는 경우만 줘야한다.
        if not self.sex.data:
            self.sex.data = SexType.여자.value
        #### 근데, 이미 아바타가 존재해서 경로만 존재하는 경우 생략해야한다.
        if not self.avatar.data:
            # print("아바타에 아무것도 없으면 FileRequired가 적용된다.>>>", self.avatar.data)
            self.avatar.validators.append(FileRequired('직원이 될 예정이시라면, 사진을 업로드 해주세요!'))
        # else:
            # print("아바타.data에 이미 존재해서 FileRequired 생략>>>", self.avatar.data)
            # pass
        self.address.validators = [DataRequired("주소를 입력해주세요!")]
        self.phone.validators = [DataRequired("휴대폰 번호를 입력해주세요!")]

        # 직원전환 상사 [current_user]로 부여할 수 잇는 role을 채운다.
        with DBConnectionHandler() as db:
            #### 직원전환시 USER는 옵션에서 제외해야한다. -> 나보다는 낮지만,  STAFF이상으로 -> where. Role.is_STAFF 추가
            roles_under_current_user = db.session.scalars(
                select(Role)
                .where(Role.is_less_than(current_user.role))
                .where(Role.is_(Roles.STAFF))
            ).all()
            self.role_id.choices = [(role.id, role.name) for role in roles_under_current_user]

    def validate_birth(self, field):
        if self.employee:  # 수정시 자신의 제외하고 데이터 중복 검사
            condition = and_(Employee.id != self.employee.id, Employee.birth == field.data)
        else:  # 생성시 자신의 데이터를 중복검사
            condition = Employee.birth == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 주민등록번호 입니다')

 ```

#### employee_form.html

```html
{% extends 'admin/employee.html' %}

{% block button %}{% endblock button %}


{% block table_content %}
<!-- UserInfoForm -->
<!-- form 추가 시작 -->
<form action="" method="post" class="mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}
    <!-- 바깥 columns 에 is-multine을 줘야 칼럼이 넘어가면 다음줄로 내린다-->
    <div class="columns is-mobile is-multiline"
         style="border-bottom: #ededed solid 1px; padding-bottom: 1rem">
        <div class="column is-narrow">
            <figure class="image is-96x96">
                <img class="is-rounded" style="height: 100%;"
                     :src="
                         img_file_url ? img_file_url :
                         `
                         {% if form.user.avatar %}
                         {{url_for('download_file', filename=form.user.avatar)}}
                         {% else %}
                         {{url_for('static', filename='/img/user/default_avatar.svg')}}
                         {% endif %}
                         `
                        "
                >
            </figure>
        </div>

        <!-- username -->
        <div class="column is-narrow">
            <div style="padding-top: 1.5rem;">
                <h1 class="title is-size-4">{{ form.user.username }}</h1>
            </div>
        </div>

        <!-- avatar  -->
        <div class="column is-narrow is-7 has-text-centered">
            <div style="padding-top: 1.5rem;">
                <!-- 버튼 가운데정렬은, flex가 되는 b-field태그의 class로 주면 된다. -->
                <b-field class="file is-primary is-justify-content-center" :class="{'has-name': !!img_file}">
                    <b-upload
                            class="file-label" rounded
                            v-model="img_file"
                            name="avatar"
                    >
                                      <span class="file-cta">
                                        <b-icon class="file-icon" icon="upload"></b-icon>
                                        <span class="file-label">{$ img_file.name || "아바타 사진 업로드" $}</span>
                                      </span>
                    </b-upload>
                </b-field>
            </div>
            <p class="help has-text-grey-light">
                {{ form.avatar.description }}
            </p>
        </div>


    </div>


    <!-- 기본정보: 추가정보였던 정보들을 기본정보로서 form이 필수로 받는다.    -->
    <div class="columns" style="padding:1rem 0; ">
        <div class="column is-2">
            <p>기본 정보</p>
        </div>
        <div class="column">
            <!-- email -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.email.label(class='label')}}</span>
                </div>
                <div class="column is-5">
                    <span class=" has-text-black-ter">{{ form.email(class='input') }}</span>
                    <p class="help has-text-primary-dark">
                        {{ form.email.description }}
                    </p>
                </div>
            </div>

            <!-- sex -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.sex.label(class='label')}}</span>
                </div>
                <div class="column is-narrow">
                    {% for subfield in form.sex %}
                    <input {%if subfield.checked %}checked {% endif %} type="radio"
                           id="{{ subfield.id }}" name="{{ form.sex.id }}"
                           value="{{ subfield.data }}">
                    {{ subfield.label }}
                    {% endfor %}
                </div>
            </div>


            <!-- 전화번호  -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex ">
                    <span class=" has-text-grey-light">{{form.phone.label(class='label')}}</span>
                </div>
<!--                <div class="column">-->
                <div class="column is-4">
                    <!-- descript이 달린 경우, column에 사이즈를 주지말고, 세부요소에 column + is-   p태그에 column + py-0을 주자-->
                    <span class="has-text-black-ter">{{ form.phone(class='input') }}</span>
<!--                    <span class="has-text-black-ter column is-4">{{ form.phone(class='input') }}</span>-->
<!--                    <p class="help has-text-primary-dark column py-0">-->
<!--                        {{ form.phone.description }}-->
<!--                    </p>-->
                </div>

            </div>
            <!-- 주소   -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{ form.address.label(class='label')}}</span>
                </div>
                <div class="column is-10 ">
                    <span class=" has-text-black-ter">{{ form.address(class='input') }}</span>
                </div>
            </div>

        </div>
    </div>

    <!-- 직원정보   -->
    <div class="columns" style="padding:1rem 0; ">
        <div class="column is-2">
            <p>직원 정보</p>
        </div>
        <div class="column">
            <!-- name -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.name.label(class='label')}}</span>
                </div>
                <div class="column is-3">
                    <span class="has-text-black-ter">{{ form.name(class='input') }}</span>
                </div>
            </div>

            <!-- sub_name(영어이름) -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.sub_name.label(class='label')}}</span>
                </div>
                <div class="column is-4">
                    <span class=" has-text-black-ter">{{ form.sub_name(class='input') }}</span>
                </div>
            </div>

            <!-- 주민번호   -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex ">
                    <span class=" has-text-grey-light">{{form.birth.label(class='label')}}</span>
                </div>
                <div class="column is-5">
<!--                <div class="column">-->
                    <span class="has-text-black-ter">{{ form.birth(class='input') }}</span>
<!--                    <span class="has-text-black-ter column is-5">{{ form.birth(class='input') }}</span>-->
<!--                    <p class="help has-text-primary-dark column py-0">-->
<!--                        {{ form.birth.description }}-->
<!--                    </p>-->
                </div>
            </div>

            <!-- 직위  -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-2 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.role_id.label(class='label')}}</span>
                </div>
                <div class="column is-4">
                    <div class="select is-half">
                        {{ form.role_id }}
                    </div>
                </div>
            </div>

              <!-- 입사일 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.join_date.label(class='label')}}</p>
                </div>
                <div class="column is-4 ">
                    <div class="content">
                        <b-field>
                            <b-datepicker
                                    icon="calendar-today"
                                    editable
                                    v-model="date"
                            >
                            </b-datepicker>
                        </b-field>
                        <!-- datefield는 외부에서 값을 받을 땐, 자기고유 format yyyy-m-d 형식의  자기고유타입 string만 받더라. -->
                        {{form.join_date(class='input', type='hidden',  **{'v-model':'stringDate'})}}
                    </div>
                </div>
            </div>

        </div>
    </div>



    <div class="columns is-mobile is-centered my-3">
        <div class="column is-narrow">
            <a href="{{ url_for('admin.user') }}"
               class="button is-primary is-light mr-2">
                뒤로가기
            </a>
        </div>
        <div class="column is-narrow">
            <input type="submit" value="수정완료"
                   class="button is-primary">
        </div>
    </div>

</form>
{% endblock table_content %}



{% block vue_script %}
<script>
    app._data.date = new Date('{{ form.join_date.data or today_date() }}')
</script>
{% endblock vue_script %}

```

![image-20221215225725791](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221215225725791.png)

#### employee_add route

```python
@admin_bp.route('/employee/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_add(user_id):
    user = User.get_by_id(user_id)
    form = EmployeeForm(user, g.user)

    if form.validate_on_submit():
        flash("직원 전환 성공")
        # User정보와 Employee정보를 따로 분리해서 각각 처리한다.

        #### user ####
        # - 직원으로 변환되면, user의 role부터 미리 선택된 것으로 바뀌어야한다.
        user_info = {
            'email': form.email.data,
            'sex': form.sex.data,
            'phone': form.phone.data,
            'address': form.address.data,

            'role_id': form.role_id.data,
        }
        user.update(user_info)

        f = form.avatar.data
        if f != user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)
            delete_uploaded_file(directory_and_filename=user.avatar)
            user.avatar = f'avatar/{filename}'

        #### employee ####
        # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
        employee = Employee(
            user=user,
            name=form.name.data,
            sub_name=form.sub_name.data,
            birth=form.birth.data,
            join_date=form.join_date.data,
            # job_status는 form에는 존재하지만, 생성시에는 view에 안뿌린다. 대신 default값이 들어가있으니, 그것으로 재직되게 한다?
            job_status=form.job_status.data,
            # resign_date는 deafult값없이 form필드에도 명시안한다
        )

        with DBConnectionHandler() as db:
            db.session.add(user)
            db.session.add(employee)
            db.session.commit()

        return redirect(url_for('admin.employee'))

    return render_template('admin/employee_form.html',
                           form=form
                           )
```



#### employee select route를 User중 is_staff기준 => Employe + is_active( not 대기, not 퇴사, 휴직)으로 골라내도록 변경

- Employee기준으로 골라내도록 변경 

  ```python
  @admin_bp.route('/employee')
  @login_required
  @role_required(allowed_roles=[Roles.CHIEFSTAFF])
  def employee():
      page = request.args.get('page', 1, type=int)
  
      # stmt = select(User) \
      #     .where(User.is_staff) \
      #     .order_by(User.add_date.desc())
      #### employee정보를 기준으로 직원관리를 표시하려면 User에서 골라내는게 아니라, Employee중에서 골라야한다.
      #### - Employee도 대기상태 or 퇴사상태 데이터가 있기 때문에, 필터링을 한번 해야한다
      stmt = select(Employee) \
          .where(Employee.job_status > 0) \
          .order_by(Employee.join_date.desc())
  
      # print(stmt)
  
      pagination = paginate(stmt, page=page, per_page=10)
      employee_list = pagination.items
  
  
      return render_template('admin/employee.html',
                             employee_list=employee_list,
                             pagination=pagination)
  ```

- **hybrid_propery로 상태 검색가능하게 만들기**

  ```python
      ## employee도 대기/퇴사상태가 잇어서 구분하기 위함
      @hybrid_property
      def is_active(self):
          # return JobStatusType.대기 != self.job_status and self.job_status != JobStatusType.퇴사
          return self.job_status not in [JobStatusType.대기, JobStatusType.퇴사]
  
      @is_active.expression
      def is_active(cls):
          # 객체와 달리, expression은 and_로 2개 조건식을 나눠 써야한다.
          # return and_(JobStatusType.대기 != cls.job_status, cls.job_status != JobStatusType.퇴사)
          # return not cls.job_status.in_([JobStatusType.대기, JobStatusType.퇴사])
          return cls.job_status.notin_([JobStatusType.대기, JobStatusType.퇴사])
  
      @hybrid_property
      def is_pending(self):
          return self.job_status == JobStatusType.대기
  
      @is_pending.expression
      def is_pending(cls):
          return cls.job_status == JobStatusType.대기
      
      @hybrid_property
      def is_resign(self):
          return self.job_status == JobStatusType.퇴사
  
      @is_resign.expression
      def is_resign(cls):
          return cls.job_status == JobStatusType.퇴사
  ```

- route 수정

  ```python
  stmt = select(Employee) \
  .where(Employee.is_active) \
  .order_by(Employee.join_date.desc())
  ```



##### employee의 select 표시를 위해 hybrid_property 만들기(생일 , 연차, 사번 + 나이)

- [연차관련 백준문제](https://www.acmicpc.net/problem/23628)
  - 풀이



```python
# 근무개월 수 (다음달 해당일시 차이가 1달로 +1)
    @hybrid_property
    def months_and_days_from_join_date(self):
        today_date = datetime.datetime.now().date()
        ## self.join_date + relativedelta(months=1) 는 정확히 다음달 같은 일을 나타낸다
        # - 2월1일(join) 입사했으면, 3월1일(today)에 연차가 생기도록, (딱 1달이 되는날)
        # - 차이가 1달이라는 말은, 시작일제외하고 [시작일로부터 차이가 한달]이 지났다는 말이다.
        #    3-1 = 시작일 빼고 2일,   차이6 => 시작일포함 7일, 시작일 제외 시작일부터 6일지남
        # - 계산기준일에 relativedelta를 끼워서 계산하도록 한다.
        # - 월차휴가 계산과 동일하며, 월차는 연도제한 + 연차도 계산해야한다.
        months = 0
        while today_date >= self.join_date + relativedelta(months=1):
            today_date -= relativedelta(months=1)
            months += 1
        days = (today_date - self.join_date).days  # timedelta.days   not int()
        return months, days

    # 재직자 N년차(햇수) 1년차(0)부터 시작하며, 일한 개월수가 12가 넘어가야 2년차다
    @hybrid_property
    def years_from_join_date(self):
        months, _ = self.months_and_days_from_join_date
        years = (months // 12) + 1
        return years

    # 연차휴가 참고식: https://www.acmicpc.net/problem/23628
    # https://www.saramin.co.kr/zf_user/tools/holi-calculator
    @hybrid_property
    def working_days(self):
        months, days = self.months_and_days_from_join_date
        years, months = divmod(months, 12)  # 여기서 years는 N년차가 아니라, 0부터 시작하는 근무연수

        result = f"{days}일"
        if months:
            result = f"{months}개월" + result
        if years:
            result = f"{years}년" + result
        return result

    @hybrid_property
    def employee_number(self):
        return f"{self.join_date.year}{self.id:04d}"
```

- 근무개월수를  `현재일`이  `입사일 + 1달`(다음달 가능날)보다 크면, 1달을 채울수 있다고 판단하여 count + 1일 함. 1달을 못채우면, 카운팅을 종료하고 `나머지 일수`를 뱉어냄
  - 검사를 **매 직전달마다 + 1달을 채웠냐?** 물어보고 진입함.
    - relativedelta를 이용하기 위해 **현재일-1달 한 것을 기준으로 계속 검사함.**
- 햇수 = N년차는, 근무개월수months를 구한 것을 기준으로 12달을 나누고, 12달 못채운 것을 1로 시작함.
- 근무일 역시, 근무개월수months를 통해 계산함.
- 사번은 일단 입사년도 + 0001(Employee.id)부터 시작하게 함. 



![image-20221216031146144](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221216031146144.png)

![image-20221216031523467](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221216031523467.png)

- 나이 추가 반영

  - [참고](https://github.com/maykinmedia/open-inwoner/blob/cb0b4c08cbbc66aeaaba59a8a6d069ff3ce94b67/src/open_inwoner/accounts/models.py)

  ```python
  def get_age(self):
      if self.birthday:
          today = date.today()
          age = (
              today.year
              - self.birthday.year
              - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
          )
  
          return age
      return None
  ```







##### User관리에서 add_User시, 더이상 역할부여 안하도록 막기 => 직원전환 or 대기상태에서 전환만 역할부여 되도록 

- admin.CreateUserForm에서 role_id필드 제거

  - 동적 부여도 제거하기 위해  생성자에서 **current_user받는 것 제거**

  - **route에서 `해당role부여를 삭제`**

  - **UserEntity는 `email과 대조해서 Admin` or `기본deafult Role User`를 부여하도록 설계됨**

    - Role에는 default필드가 있고, Role일괄생성시 User가 true로 표시되어있어서, 그것을 가져온다

    ```python
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
    		# User생성시 role을 안넣어주면,
            if not self.role and not self.role_id:
                # email이 admin꺼 아니라면
                if self.email == project_config.ADMIN_EMAIL:
                    condition = Role.name == 'Administrator'
                # role 중에 default표시된 것을 
                else:
                    condition = Role.default == True
                # 가져와 User의 role에 넣어준다.
                with DBConnectionHandler() as db:
                    self.role = db.session.scalars(select(Role).where(condition)).first()
    ```

  - **user_form.html에서 역할부여 form 삭제**

    - auth.EmployeeForm에서만 User의 role_id 선택하능



### Staff가 User를 직접 전환하는게 아니라, Employee로 초대하기

#### 예시1)  Event/Invite/Proposal

- 예시1: https://stackoverflow.com/questions/20986628/flask-sqlalchemy-many-to-many-join-condition

  - 쿼리: https://stackoverflow.com/questions/21247924/sqlalchemy-check-if-object-is-in-model
  - User
  - Event
    - user_id
    - invitees
    - proposals
  - Invite
    - user_id
    - ~~event_id~~
  - Proposal
    - user_id
    - ~~event_id~~

  ```python
  #events_invitees = db.Table(
     # 'events_invitees',
     # db.Column('event_id', db.Integer(), db.ForeignKey('events.id')),
      #db.Column('user_id', db.Integer(), db.ForeignKey('users.id'))
     # )
  events_invitees = db.Table(
      'events_invitees',
      db.Column('event_id', db.Integer(), db.ForeignKey('events.id')),
      db.Column('invite_id', db.Integer(), db.ForeignKey('invites.id'))
  )
  events_proposals = db.Table(
      'events_proposals',
      db.Column('event_id', db.Integer(), db.ForeignKey('events.id')),
      db.Column('proposal_id', db.Integer(), db.ForeignKey('proposals.id'))
      )
  
  
  class EventJsonSerializer(JsonSerializer):
      pass
  
  
  class Event(EventJsonSerializer, db.Model):
      __tablename__ = 'events'
  
      id = db.Column(db.Integer, primary_key=True)
      user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
      event_name = db.Column(db.String(30))
      event_mesg = db.Column(db.Text)
      start_date = db.Column(db.Date)
      end_date = db.Column(db.Date)
      event_status = db.Column(db.Boolean)
      rsvp = db.Column(db.Date)
      created = db.Column(db.DateTime, default=get_current_time)
  
      invitees = db.relationship('Invite',
                  secondary=events_invitees,
                  backref=db.backref('events', lazy='dynamic'))
  
      events_proposals = db.relationship('Event',
                          secondary=events_proposals,
                          backref=db.backref('events', lazy='dynamic'))
  
  
  class InviteJsonSerializer(JsonSerializer):
      pass
  
  
  class Invite(InviteJsonSerializer, db.Model):
      __tablename__ = 'invites'
  
      id = db.Column(db.Integer, primary_key=True)
      created = db.Column(db.Date, default=get_current_time)
      #event_id = db.Column(db.ForeignKey('events.id'))
      user_id = db.Column(db.ForeignKey('users.id'))
  
  
  class ProposalJsonSerializer(JsonSerializer):
      pass
  
  
  class Proposal(ProposalJsonSerializer, db.Model):
      __tablename__ = 'proposals'
  
      id = db.Column(db.Integer, primary_key=True)
      created = db.Column(db.Date, default=get_current_time)
      date = db.Column(db.Date)
      #event_id = db.Column(db.ForeignKey('events.id'))
      user_id = db.Column(db.ForeignKey('users.id'))
  ```

  

- User

  - Event
    - ~~Invite~~
  - Proposal
  - Invite

  ```python
  e = events.get(1)
  u = users.get(1)
  e.invitees.append(u)
  and then in my service layer I'd like to be able to have a function like:
  
  def add_invitee(self, event, user):
      if user in self.get(event).invitees:
          raise OroposError(u'User already invited')
      event.invitees.append(user)
      return self.save(event), user
  ```





#### 예시2)  축구: 

##### User 가입시 -> Player or Refree or 둘다로 미리 등록 

```python
def create_player_query(user_id):
    player = Player(user_id=user_id)
    db.session.add(player)
    return True

def signup_query(username, password, name, surname, group_id):
    person_id = create_person_query(name, surname)
    
    user_id = create_user_query(username, password, person_id, group_id)
    
    if group_id == "1":
        create_player_query(user_id)
    if group_id == "3":
        create_referee_query(user_id)
                             
    db.session.commit()
    return user_id


@user.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    search = User.query.filter_by(username=data['username']).first()
    if search is None:
        new_user_id = signup_query(data['username'],
                                   data['password'],
                                   data['name'],
                                   data['surname'],
                                   data['group_id'])

        return {'message': 'New user created!', "new_user_id": new_user_id}
    else:
        return {'message': 'User already exist!'}
```



#####  User가 Spot을 정해 Booking을 만들 때, User를 Player로 참여 + booking별 player들을 검색할 수 있는 Player-Booking다대다 LineUp생성(LineUP중, 최초참여자가 된다. 그 이후에는 초대를 받아야, accept한경우만 해당 booking의 LineUp에 등록된다.)



```python
def add_booking_query(spot_id, day, start_time, end_time, customer_id, user):
    booking = Booking(day=day,
                      start_time=start_time,
                      end_time=end_time,
                      spot_id=spot_id,
                      customer_id=customer_id) #user_id
    db.session.add(booking)
    
    target = Player.query.filter_by(user_id=user.id).first()
    lineup = Lineup(player_id=target.player_id,
                    booking_id=booking.booking_id)
    
    db.session.add(lineup)
    db.session.commit()
    return True

@booking.route('/booking', methods=['POST'])
@token_required
def add_booking(current_user):
    data = request.get_json()
    if add_booking_query(data['spot_id'],
                         data['day'],
                         data['start_time'],
                         data['end_time'],
                         current_user.id,
                         current_user):
        return {'message': 'Booking saved!'}
```



##### spot별 내 booking들을 확인하기

```python
@booking.route('/spot/<spot_id>/booking', methods=['GET'])
@token_required
def get_spot_bookings(current_user, spot_id):
    bookings = Booking.query.filter_by(spot_id=spot_id)

    output = []

    for b in bookings:
        bookings_data = {
            'day': b.day,
            'spot_id': b.spot_id,
            'start_time': str(b.start_time),
            'end_time': str(b.end_time),
        }

        output.append(bookings_data)

    return {'bookings': output}


@booking.route('/booking/my', methods=['GET'])
@token_required
def get_my_bookings(current_user):
    bookings = Booking.query.join(Spot, Spot.id == Booking.spot_id). \
            add_columns(Booking.spot_id,
                        Booking.booking_id,
                        Spot.name,
                        Booking.day,
                        Booking.start_time,
                        Booking.end_time). \
            filter(Booking.customer_id == current_user.id)
    output = []
    for b in bookings:
        bookings_data = {
            'day': b.day,
            'id': b.booking_id,
            'spot_id': b.spot_id,
            'spot_name': b.name,
            'start_time': str(b.start_time),
            'end_time': str(b.end_time),
        }

        output.append(bookings_data)

    return {'bookings': output}
```





#####  booking에 대해 player (host, guest)2명으로 booking_id(별) 하위의 PlayerInvitation초대를 만듦. 초대는 status(T/F)와 답변여부answerd(T/F)가 잇음

```python
@player.route('/players/invites', methods=['POST'])
@token_required
def invite_player(current_user):
    data = request.get_json()
    invite = PlayerInvite(guest_id=data['guest_id'],
                          host_id=data['host_id'],
                          booking_id=data['booking_id'])
    db.session.add(invite)
    db.session.flush()
    db.session.commit()
    return {'message': 'Success!'}


```

##### 내가 받은 초대를 확인하려면, user -> player로 조회 -> guest_id로 등록된 PlayerInvite들을 조회하면 된다.

```python
def my_invites(user_id):
    player = Player.query.filter_by(user_id=user_id).first()
    invites = PlayerInvite.query.filter_by(guest_id=player.player_id)


'''
    # targets = SUPER_JOIN
    booking = Booking.query.filter_by(booking_id=i.booking_id).first()
    spot = Spot.query.filter_by(id=booking.spot_id).first()
    host_player = Player.query.filter_by(player_id=i.host_id).first()
    host_user = User.query.filter_by(id=host_player.user_id).first()
    host_person = Person.query.filter_by(id=host_user.person_id).first()  # TODO: refactor queries
'''

@player.route('/players/invites/guest', methods=['GET'])
@token_required
def get_my_invites(current_user):  # Return invites sent to the logged player.

    output = []

    for invite in my_invites(current_user.id):

        invite_data = {'booking_id': invite.booking_id,
                       'spot_name': invite.spot_name,
                       'spot_id': invite.spot_id,
                       'status': invite.status,
                       'invite_id': invite.playerinvite_id,
                       'guest_id': invite.guest_id,
                       'host_name': f'{invite.host_name} {invite.host_surname}'
                       }
        output.append(invite_data)

    return {'invites': output}

```



##### 고난도) 내가 player로서 초대완료 == 참여 booking들의 spot을 조회하려면? 

- user -> player -> **다대다의 LineUp에 내가 player_id로 포함된 LineUp(들)찾기** -> 내가 포함된 LineUp에 다대다 중 한쪽인 **booking_id로** 실제 Booking객체 찾기
  - booking 대상 부모 spot_id 찾기

```python

@booking.route('/booking/my/invited', methods=['GET'])
@token_required
def get_my_invited_bookings(current_user):
    player = Player.query.filter_by(user_id=current_user.id).first()
    lineups = Lineup.query.filter_by(player_id=player.player_id)
    output = []
    for l in lineups:
        target = Booking.query.filter_by(booking_id=l.booking_id).first()
        spot = Spot.query.filter_by(id=target.spot_id).first()
        output.append({
                'id': target.booking_id,
                'day': target.day,
                'spot_id': target.spot_id,
                'spot_name': spot.name,
                'start_time': str(target.start_time),
                'end_time': str(target.end_time)})
    return {'bookings': output}

```





##### 내가받은 초대들 중 특정 초대에 대해 accept 하며, 해당 PlayerInvite의 필드 중 .staus와 .answered에 True를 표기한다.  초대에 응해지는 순간, Booking-Player 다대다 LineUp에 포함되어, 다대다 테이블에 데이터를 추가한다

```python
@player.route('/players/invites/accept', methods=['POST'])
@token_required
def accept_invite(current_user):
    data = request.get_json()
    invite = PlayerInvite.query.filter_by(playerinvite_id=data['playerinvite_id']).first()
    invite.status = True
    invite.answered = True
    
    db.session.add(invite)
    
    lineup = Lineup(player_id=data['player_id'],
                    booking_id=data['booking_id'])
    
    db.session.add(lineup)
    db.session.commit()
    return {'message': 'Success!'}
```



##### 내가 onwer로서 소유한 spot의 모든 booking들 찾기

```python
@booking.route('/booking/my/owner', methods=['GET'])
@token_required
def get_my_spots_bookings(current_user): # TODO: refactor, create control functions to reuse in get_spot_bookings
    output = []
    my_spots = Spot.query.filter_by(owner_id=current_user.id)
    for i in my_spots:
        bookings = Booking.query.filter_by(spot_id=i.id)
        # spot_bookings = []
        for b in bookings:
            bookings_data = {
                'day': b.day,
                'spot_id': b.spot_id,
                'spot_name':i.name,
                'start_time': str(b.start_time),
                'end_time': str(b.end_time)
            }
            # spot_bookings.append(bookings_data)
            output.append(bookings_data)
    return {'bookings': output}

```



##### 특정 booking_id로, 참여자들 다 골라내기

```python
@booking.route('/booking/<booking_id>/players', methods=['GET'])
@token_required
def get_booking_players(current_user, booking_id):
    lineups = Lineup.query.filter_by(booking_id=booking_id)
    output = []
    for l in lineups:
        player = Player.query.filter_by(player_id=l.player_id).first()
        user = User.query.filter_by(id=player.user_id).first()
        person = Person.query.filter_by(id=user.person_id).first()

        player_data = {'name': person.name,
                       'surname': person.surname,
                       'matches_count': player.matches_count,
                       'average_rating': player.average_rating}
        output.append(player_data)

    return {'players': output}
```



- modes: https://github.com/pickupappufrpe/pickup-api/blob/4c8e305b85717f82213c52b136f630fa6880c132/models.py#L103

- Spot
  - user_id(owner_id)
  - ground_id
  - Schedules
  - bookings
  - ratings

- Booking
  - user_id
  - spot_id
  - refree_id
  - goalkeeper_id
  - player_inivites
  - refree_inivites
  - goalkeeper_inivites

- PlayerInvite
  - player_id(guest_id)
  - player_id(host_id)
  - booking_id
  - status(T/F)
  - answered(T/F)
- Player
  - user_id
  - position_id
  - ratings
  - gusests(PlayerInvite.guest_id)
  - hosts (PlayerInvite.host_id)
  - reported(Report.reported_id)
  - reporters(Report.reporter_id)



- Lineup: **각자 키를 당연히 안가지고 잇는 다대다 관계테이블을 LineUp테이블로 구성**
  - player_id
  - booking_id
  - 



- User(golakeeper, refree), Ground, Position
  - Spot
    - Schedule
    - `Booking`
      - PlayerInvite
    - Rating
  - `Player`
    - LineUp(player_id) <- booking_id
    - PlayerInvite(**guest_id + host_id**) <- **booking_id**
  - Team(only captain user_id)



#### 축구에서 아쉬운점 : invite에 유효기간이 있었음 좋겠따.

#### 예시3) open-inowner(정부문서관리?) 등록초대 Contact -> 등록 Invite 기록  with email + expired  / Message-inbox 

- models: https://github.com/maykinmedia/open-inwoner/blob/main/src/open_inwoner/accounts/models.py

- user는 contact에 대한 타입을 가진다( message 수신거부/수신동의 등인 듯)

  ```python
  class User
  	#...
  	contact_type = models.CharField(
          verbose_name=_("Contact type"),
          default=ContactTypeChoices.contact,
          max_length=200,
          choices=ContactTypeChoices.choices,
          help_text=_("The type of contact"),
      )
      #...
      contact_user = models.ForeignKey(
          "accounts.User",
          verbose_name=_("Contact user"),
          null=True,
          blank=True,
          on_delete=models.SET_NULL,
          related_name="assigned_contacts",
          help_text=_(
              "The user from the contact, who was added based on the contact email."
          ),
      )
      #...
  	def get_active_contacts(self):
          return self.contacts.filter(contact_user__is_active=True)
  
      def get_assigned_active_contacts(self):
          return self.assigned_contacts.filter(created_by__is_active=True)
  
      def get_extended_contacts(self):
          return Contact.objects.get_extended_contacts_for_user(me=self)
  
      def get_extended_active_contacts(self):
          return Contact.objects.get_extended_contacts_for_user(me=self).filter(
              contact_user__is_active=True, created_by__is_active=True
          )
  
  ```

- ContacfForm을 통해 현재user가 **email을 통해 contact하여 user to user Contact  데이터를 만들어낸다**

  ```python
  class ContactForm(forms.ModelForm):
      def __init__(self, user, create, *args, **kwargs):
          self.user = user
          self.create = create
          super().__init__(*args, **kwargs)
  
      class Meta:
          model = Contact
          fields = ("first_name", "last_name", "email", "phonenumber")
  
      def clean(self):
          cleaned_data = super().clean()
          email = cleaned_data.get("email")
  
          if self.create and email:
              if (
                  self.user.contacts.filter(email=email).exists()
                  or self.user.assigned_contacts.filter(created_by__email=email).exists()
              ):
                  raise ValidationError(
                      _(
                          "Het ingevoerde e-mailadres komt al voor in uw contactpersonen. Pas de gegevens aan en probeer het opnieuw."
                      )
                  )
  
      def save(self, commit=True):
          if not self.instance.pk:
              self.instance.created_by = self.user
  
          if not self.instance.pk and self.instance.email:
              contact_user = User.objects.filter(email=self.instance.email).first()
              if contact_user:
                  self.instance.contact_user = contact_user
  
          return super().save(commit=commit)
  ```

- ContactCreateView에서는 contact를 save()하고나서

  - **contact한user가  아직 User데이터에 없으면서**(이미 contact했으면, contact데이터에 남아있음) & **email은 존재할 때, invite를 보낸다**

    - form에서 contact할때, 이미 유저데이터가 있으면 Contact객체데이터에 (이미 유저로 가입되어있따는 의미의 `contact_user`)로 채워서 반환한다

      ```python
      class ContactForm(forms.ModelForm):
          #...
          def save(self, commit=True):
              if not self.instance.pk:
                  self.instance.created_by = self.user
      
              if not self.instance.pk and self.instance.email:
                  # 이미 해당email의 유저가 존재하면, [등록invite-이메일은 보낼 필요 없는 user]로 간주한다.
                  contact_user = User.objects.filter(email=self.instance.email).first()
                  if contact_user:
                      self.instance.contact_user = contact_user
      
              return super().save(commit=commit)
      ```

    - 여기 메세지는 inbox가 아닌 flash다

    ```python
    class ContactCreateView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, CreateView):
        template_name = "pages/profile/contacts/edit.html"
        model = Contact
        form_class = ContactForm
    
        @cached_property
        def crumbs(self):
            return [
                (_("Mijn profiel"), reverse("accounts:my_profile")),
                (_("Mijn contacten"), reverse("accounts:contact_list")),
                (
                    _("Maak contact aan"),
                    reverse("accounts:contact_create", kwargs=self.kwargs),
                ),
            ]
    
        def get_success_url(self):
            if self.object:
                return self.object.get_update_url()
            return reverse_lazy("accounts:contact_list")
    
        def get_form_kwargs(self):
            return {
                **super().get_form_kwargs(),
                "user": self.request.user,
                "create": True,
            }
    
        def form_valid(self, form):
            self.object = form.save()
    
            # send invite to the contact
            if not self.object.contact_user and self.object.email:
                invite = Invite.objects.create(
                    inviter=self.request.user,
                    invitee_email=self.object.email,
                    contact=self.object,
                )
                invite.send(self.request)
    
            # FIXME type off message
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(
                    "{contact} is toegevoegd aan uw contactpersonen.".format(
                        contact=self.object
                    )
                ),
            )
    
            self.log_addition(self.object, _("contact was created"))
            return HttpResponseRedirect(self.get_success_url())
    
        
        
    # 
    class ContactDeleteView(LogMixin, LoginRequiredMixin, DeleteView):
        model = Contact
        slug_field = "uuid"
        slug_url_kwarg = "uuid"
        success_url = reverse_lazy("accounts:contact_list")
    
        def get_queryset(self):
            base_qs = super().get_queryset()
            return base_qs.filter(created_by=self.request.user)
    
        def delete(self, request, *args, **kwargs):
            object = self.get_object()
            super().delete(request, *args, **kwargs)
    
            self.log_deletion(object, _("contact was deleted"))
            return HttpResponseRedirect(self.success_url)
    ```

- ContactType

  - b~ : mentor임

    ```python
    class ContactTypeChoices(DjangoChoices):
        contact = ChoiceItem("contact", _("Contactpersoon"))
        begeleider = ChoiceItem("begeleider", _("Begeleider"))
        organization = ChoiceItem("organization", _("Organisatie"))
    ```

    



##### Invite 모델

```python
class Invite(models.Model):
    inviter = models.ForeignKey(
        User,
        verbose_name=_("Inviter"),
        on_delete=models.CASCADE,
        related_name="sent_invites",
        help_text=_("User who created the invite"),
    )
    invitee = models.ForeignKey(
        User,
        verbose_name=_("Invitee"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_invites",
        help_text=_("User who received the invite"),
    )
    invitee_email = models.EmailField(
        verbose_name=_("Invitee email"),
        help_text=_("The email used to send the invite"),
    )
    contact = models.ForeignKey(
        Contact,
        verbose_name=_("Contact"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="invites",
        help_text=_("The contact the creation of which triggered sending the invite"),
    )
    accepted = models.BooleanField(verbose_name=_("Accepted"), default=False)
    key = models.CharField(verbose_name=_("Key"), max_length=64, unique=True)
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the message was created"),
    )

    class Meta:
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")

    def __str__(self):
        return f"For: {self.invitee} ({self.created_on.date()})"

    def save(self, **kwargs):
        if not self.pk:
            self.key = self.generate_key()

        return super().save(**kwargs)

    @staticmethod
    def generate_key():
        return get_random_string(64).lower()

    def send(self, request=None):
        url = self.get_absolute_url()
        if request:
            url = request.build_absolute_uri(url)

        template = find_template("invite")
        context = {
            "inviter_name": self.inviter.get_full_name(),
            "email": self.invitee_email,
            "invite_link": url,
        }

        return template.send_email([self.invitee_email], context)

    def get_absolute_url(self) -> str:
        return reverse("accounts:invite_accept", kwargs={"key": self.key})

    def expired(self) -> bool:
        expiration_date = self.created_on + timedelta(days=settings.INVITE_EXPIRY)
        return expiration_date <= timezone.now()
```



- Invite
  - inviter(host)
    - **on_delete = CASCADE**
    - backref **sent_invites**
  - invitee(guest)
    - **on_delete = SET_NULL**
    - backref  **received_invites**
  - **invitee_email**
    - The email used to send the invite
  - **contact**(contact_id) from user_id
    - The contact the creation of which triggered sending the invite
  - **accepted**
    - **default False**
      - accepted되면, db가 변화되며, 그 이후에는 `if invite.aceppted`로서 이미 끝난 invite확인용으로 사용된다.
  - **key**
    - max_length 64, unique=True
  - **created_on**
    - auto_now_add = True

- method

  - **save**()할 때, pk가 안주어진다면, generate_key()를 해서 key필드에 넣어서 저장한다

  - **genereate_key**() 메일을 보낼 때 만들어지는 key

  - **send**() + **get_absolute_url**()

    - **invite accept  템플릿 + route의 url주소를 requst객체를 이용하여 build_url하여 mail에 보낸다.**

    - templates/accounts/invite_accept.html

      ```html
      {% extends 'master.html' %}
      {% load i18n form_tags %}
      
      
      {% block content %}
      <h1 class="h1">
          {% trans "Accept an invitation" %}
      </h1>
      <p class="p">
          {% blocktranslate with inviter_name=object.inviter.get_full_name %}Accept invitation from {{ inviter_name }} and join Open Inwoner Platform {% endblocktranslate %}
      </p>
      
      {% form id="invite-form" form_object=form method="POST" submit_text=_("Aanvaard") secondary_href='root' secondary_text=_('Terug') secondary_icon='arrow_backward' secondary_icon_position="before" %}
      {% endblock content %}
      ```

- 참고 쿼리셋

  ```python
  class ContactQuerySet(QuerySet):
      def get_extended_contacts_for_user(self, me):
          """
          Returns both active contacts and active reversed contacts for the user.
          The returned queryset is annotated with:
          - reverse (bool)
          - other_user_id
          - other_user_first_name
          - other_user_last_name
          - other_user_email
          - other_user_phonenumber (Null in case of reversed contacts)
  
          If the user and other user have contacts with each other return both contacts
          """
  
          my_contacts_users = self.filter(created_by=me).values_list(
              "contact_user", flat=True
          )
          return (
              self.filter(Q(created_by=me) | Q(contact_user=me))
              .distinct()
              .annotate(reverse=Case(When(created_by=me, then=False), default=True))
              .annotate(
                  other_user_id=Case(
                      When(created_by=me, then=F("contact_user")),
                      default=F("created_by"),
                  )
              )
              .annotate(
                  other_user_first_name=Case(
                      When(created_by=me, then=F("first_name")),
                      default=F("created_by__first_name"),
                  )
              )
              .annotate(
                  other_user_last_name=Case(
                      When(created_by=me, then=F("last_name")),
                      default=F("created_by__last_name"),
                  )
              )
              .annotate(
                  other_user_type=Case(
                      When(created_by=me, then=F("contact_user__contact_type")),
                      default=F("created_by__contact_type"),
                  )
              )
              .annotate(
                  other_user_email=Case(
                      When(created_by=me, then=F("contact_user__email")),
                      default=F("created_by__email"),
                  )
              )
              .annotate(
                  other_user_phonenumber=Case(
                      When(created_by=me, then=F("phonenumber")),
                      default=Value(""),
                  )
              )
          )
  ```



- test

  ```python
      def test_registration_with_invite(self):
          email = self.user.email
          contact = ContactFactory.create(email=email, contact_user=None)
          invite = InviteFactory.create(contact=contact, invitee=None)
          self.assertFalse(User.objects.filter(email=email).exists())
  
          register_page = self.app.get(f"{self.url}?invite={invite.key}")
          form = register_page.forms["registration-form"]
  
          # check that fields are prefilled with invite data
          self.assertEqual(form["email"].value, email)
          self.assertEqual(form["first_name"].value, contact.first_name)
          self.assertEqual(form["last_name"].value, contact.last_name)
  
          form["password1"] = "somepassword"
          form["password2"] = "somepassword"
  
          response = form.submit()
  
          self.assertEqual(response.status_code, 302)
          self.assertEqual(response.url, reverse("django_registration_complete"))
          self.assertTrue(User.objects.filter(email=email).exists())
  
          user = User.objects.get(email=email)
          contact.refresh_from_db()
          invite.refresh_from_db()
  
          self.assertEqual(user.first_name, contact.first_name)
          self.assertEqual(user.last_name, contact.last_name)
          self.assertEqual(contact.contact_user, user)
          self.assertEqual(invite.invitee, user)
  
          # reverse contact checks
          self.assertEqual(user.contacts.count(), 0)
  ```

  



##### InboxView를 위한 Message모델?

- sender
- receiver
- content
- **seen**
  - 확인했는지
- **sent**
  - 보내졌는지

```python
class Message(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Unique identifier"),
    )
    sender = models.ForeignKey(
        User,
        verbose_name=_("Sender"),
        on_delete=models.CASCADE,
        related_name="sent_messages",
        help_text=_("The sender of the message"),
    )
    receiver = models.ForeignKey(
        User,
        verbose_name=_("Receiver"),
        on_delete=models.CASCADE,
        related_name="received_messages",
        help_text=_("The receiver of the message"),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the message was created"),
    )
    content = models.TextField(
        verbose_name=_("Content"),
        blank=True,
        help_text=_("Text content of the message"),
    )
    seen = models.BooleanField(
        verbose_name=_("Seen"),
        default=False,
        help_text=_("Boolean shows if the message was seen by the receiver"),
    )
    sent = models.BooleanField(
        verbose_name=_("Sent"),
        default=False,
        help_text=_(
            "Boolean shows if the email was sent to the receiver about this message"
        ),
    )
    file = models FileField(
        verbose_name=_("File"),
        blank=True,
        null=True,
        storage=PrivateMediaFileSystemStorage(),
        help_text=_(
            "The file that is attached to the message",
        ),
    )

    objects = MessageQuerySet.as_manager()

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

    def __str__(self):
        return f"From: {self.sender}, To: {self.receiver} ({self.created_on.date()})"

```



- 쿼리셋

  ```python
  class MessageQuerySet(QuerySet):
      def get_conversations_for_user(self, me: "User") -> "MessageQuerySet":
          """
          I apologize;
  
          Summary:
  
              Returns every conversation involving me, newest first.
  
          Details:
  
              A conversation is a Message, annotated with:
                  - other_user_id
                  - other_user_email
                  - other_user_first_name
                  - other_user_last_name
  
              other_user_id matches the value of either sender or receiver field,
              (based on which one  does not match me.pk).
  
              Conversations should be the newest messages with other_user_id.
  
              Conversations should be unique/distinct by other_user_id.
  
          """
          filtered_messages = (
              self.filter(Q(receiver=me) | Q(sender=me))
              .annotate(
                  other_user_id=Case(
                      When(receiver=me, then=F("sender")), default=F("receiver")
                  )
              )
              .order_by()
          )
          grouped_messages = (
              filtered_messages.filter(other_user_id=OuterRef("other_user_id"))
              .values("other_user_id")
              .annotate(max_id=Max("id"))
              .values("max_id")
          )
          result = (
              self.annotate(
                  other_user_id=Case(
                      When(receiver=me, then=F("sender")), default=F("receiver")
                  )
              )
              .filter(id=Subquery(grouped_messages))
              .annotate(
                  other_user_email=Case(
                      When(receiver=me, then=F("sender__email")),
                      default=F("receiver__email"),
                  )
              )
              .annotate(
                  other_user_first_name=Case(
                      When(receiver=me, then=F("sender__first_name")),
                      default=F("receiver__first_name"),
                  )
              )
              .annotate(
                  other_user_last_name=Case(
                      When(receiver=me, then=F("sender__last_name")),
                      default=F("receiver__last_name"),
                  )
              )
              .order_by("-pk")
          )
  
          return result
  
      def get_messages_between_users(self, me, other_user) -> "MessageQuerySet":
          """grouped by date"""
          return (
              self.filter(
                  Q(sender=me, receiver=other_user) | Q(sender=other_user, receiver=me)
              )
              .select_related(
                  "sender",
                  "receiver",
              )
              .order_by("-created_on")
          )
  
      def mark_seen(self, me, other_user) -> int:
          """
          Mark messages as seen between two users.
          Returns the number of updated messages.
          """
          return self.filter(receiver=me, sender=other_user, seen=False).update(seen=True)
  ```

- [view](https://github.com/maykinmedia/open-inwoner/blob/main/src/open_inwoner/accounts/views/inbox.py)

  ```python
  import logging
  from typing import Optional
  from urllib.parse import unquote
  
  from django.contrib.auth.mixins import LoginRequiredMixin
  from django.http import HttpResponseRedirect
  from django.shortcuts import get_object_or_404
  from django.urls import reverse_lazy
  from django.utils import formats
  from django.utils.translation import gettext as _
  from django.views.generic import FormView
  
  from furl import furl
  from privates.views import PrivateMediaView
  
  from open_inwoner.utils.mixins import PaginationMixin
  from open_inwoner.utils.views import LogMixin
  
  from ..forms import InboxForm
  from ..models import Document, Message, User
  from ..query import MessageQuerySet
  
  logger = logging.getLogger(__name__)
  
  
  class InboxView(LogMixin, LoginRequiredMixin, PaginationMixin, FormView):
      template_name = "accounts/inbox.html"
      form_class = InboxForm
      paginate_by = 10
  
      def get_context_data(self, **kwargs):
          """
          Returns the context data.
          """
          context = super().get_context_data()
  
          conversations = self.get_conversations()
          other_user = self.get_other_user(conversations)
          messages = self.get_messages(other_user)
          status = self.get_status(messages)
  
          context.update(
              {
                  "conversations": conversations,
                  "conversation_messages": messages,
                  "other_user": other_user,
                  "status": status,
              }
          )
  
          return context
  
      def get_conversations(self) -> dict:
          """
          Returns the conversations with other users (used to navigate between conversations).
          """
          conversations = Message.objects.get_conversations_for_user(self.request.user)
          return self.paginate_with_context(conversations)
  
      def get_other_user(self, conversations: dict) -> Optional[User]:
          """
          Return the User instance of the "other user" in the conversation (if any).
          """
          other_user_email = unquote(self.request.GET.get("with", ""))
  
          if not other_user_email:
              try:
                  other_user_email = conversations["object_list"][0].other_user_email
              except (AttributeError, IndexError, KeyError):
                  return
  
          return get_object_or_404(User, email=other_user_email)
  
      def get_messages(self, other_user: User) -> MessageQuerySet:
          """
          Returns the messages (MessageType) of the current conversation.
          """
          if not other_user:
              return Message.objects.none()
  
          messages = Message.objects.get_messages_between_users(
              me=self.request.user, other_user=other_user
          )
  
          return messages[:1000:-1]  # Show max 1000 messages for now.
  
      def get_status(self, messages: MessageQuerySet) -> str:
          """
          Returns the status string of the conversation.
          """
          try:
              return f"{_('Laatste bericht ontvangen op')} {formats.date_format(messages[-1].created_on)}"
          except IndexError:
              return ""
          except AssertionError:
              return ""
  
      def mark_messages_seen(self, other_user: Optional[User]):
          if not other_user:
              return
  
          total_marked = Message.objects.mark_seen(
              me=self.request.user, other_user=other_user
          )
          if total_marked:
              logger.info(
                  f"{total_marked} messages are marked as seen for receiver {self.request.user.email} "
                  f"and sender {other_user.email}"
              )
  
      def get_initial(self):
          initial = super().get_initial()
          conversations = self.get_conversations()
          other_user = self.get_other_user(conversations)
  
          if other_user:
              initial["receiver"] = other_user
  
          return initial
  
      def get_form_kwargs(self):
          kwargs = super().get_form_kwargs()
          kwargs["user"] = self.request.user
          return kwargs
  
      def form_valid(self, form):
          object = form.save()
  
          # build redirect url based on form hidden data
          url = furl(self.request.path).add({"with": form.data["receiver"]}).url
  
          self.log_addition(object, _("message was created"))
          return HttpResponseRedirect(f"{url}#messages-last")
  
      def get(self, request, *args, **kwargs):
          """Mark all messages as seen for the receiver"""
          context = self.get_context_data()
  
          # Redirect to the end of page.
          # Redirecting to a hash doesn't work, so we need to change the url.
          # Alter URL with redirected query param in order to go to the last message (#messages-last).
          if not request.GET.get("redirected"):
              return HttpResponseRedirect(
                  str(furl(request.get_full_path()).add({"redirected": True}))
              )
  
          self.mark_messages_seen(other_user=context["other_user"])
          return self.render_to_response(context)
  
  
  class InboxStartView(LogMixin, LoginRequiredMixin, FormView):
      template_name = "accounts/inbox_start.html"
      form_class = InboxForm
      success_url = reverse_lazy("accounts:inbox")
  
      def get_form_kwargs(self):
          kwargs = super().get_form_kwargs()
          kwargs["user"] = self.request.user
  
          return kwargs
  
      def form_valid(self, form):
          object = form.save()
  
          # build redirect url based on form hidden data
          url = furl(self.success_url).add({"with": form.data["receiver"]}).url
  
          self.log_addition(object, _("message was created"))
          return HttpResponseRedirect(f"{url}#messages-last")
  
      def get_initial(self):
          initial = super().get_initial()
  
          file = self.get_file()
          if file:
              initial["file"] = file
  
          return initial
  
      def get_file(self):
          document_uuid = unquote(self.request.GET.get("file", ""))
          if not document_uuid:
              return
  
          document = get_object_or_404(Document, uuid=document_uuid)
  
          return document.file
  
  
  class InboxPrivateMediaView(LogMixin, PrivateMediaView):
      model = Message
      slug_field = "uuid"
      slug_url_kwarg = "uuid"
      file_field = "file"
  
      def has_permission(self):
          """
          Override this method to customize the way permissions are checked.
          """
          object = self.get_object()
  
          if self.request.user == object.sender or self.request.user == object.receiver:
              self.log_user_action(object, _("file was downloaded"))
              return True
  
          return False
  ```

  - message는 get()될때 seen이 찍힌다.

    ```python
    def get(self, request, *args, **kwargs):
            """Mark all messages as seen for the receiver"""
            context = self.get_context_data()
    
            # Redirect to the end of page.
            # Redirecting to a hash doesn't work, so we need to change the url.
            # Alter URL with redirected query param in order to go to the last message (#messages-last).
            if not request.GET.get("redirected"):
                return HttpResponseRedirect(
                    str(furl(request.get_full_path()).add({"redirected": True}))
                )
    
            self.mark_messages_seen(other_user=context["other_user"])
            return self.render_to_response(context)
    ```

    

- MessageForm

  ```python
  class InboxForm(forms.ModelForm):
      receiver = forms.ModelChoiceField(
          label=_("Contactpersoon"),
          queryset=User.objects.none(),
          to_field_name="email",
          widget=forms.HiddenInput(
              attrs={"placeholder": _("Voer de naam in van uw contactpersoon")}
          ),
      )
      content = forms.CharField(
          label="",
          required=False,
          widget=forms.Textarea(attrs={"placeholder": _("Schrijf een bericht...")}),
      )
      file = LimitedUploadFileField(
          required=False,
          label="",
          widget=MessageFileInputWidget(attrs={"accept": settings.UPLOAD_FILE_TYPES}),
      )
  
      class Meta:
          model = Message
          fields = ("receiver", "content", "file")
  
      def __init__(self, user, **kwargs):
          self.user = user
  
          super().__init__(**kwargs)
  
          extended_contact_users = User.objects.get_extended_contact_users(self.user)
          choices = [
              [u.email, f"{u.first_name} {u.last_name}"] for u in extended_contact_users
          ]
          self.fields["receiver"].choices = choices
          self.fields["receiver"].queryset = extended_contact_users
  
      def clean(self):
          cleaned_data = super().clean()
  
          content = cleaned_data.get("content")
          file = cleaned_data.get("file")
  
          if not file and not content:
              raise ValidationError(
                  _("Either message content or file should be filled in")
              )
  
          return cleaned_data
  
      def save(self, commit=True):
          self.instance.sender = self.user
  
          return super().save(commit)
  
  ```

  - 유저들중에, 현재유저에게 contact를 허용한 유저들만 골라서 동적으로 choices에 넣고, 해당 content를 넣을 때, 현재유저를 message sender에 넣는다.



#### 예시4) petopia : notification 

- petopia sql 모음: https://github.com/choi-minju/petopia/blob/27c97364de02bc9c4bec378525496902c1395e9b/Petopia/src/main/webapp/resources/sql/remote_final2_190107.sql
- 컨트롤러

```sql
-- 알림
CREATE TABLE notification (
	not_UID       NUMBER   NOT NULL, -- 알림코드
	fk_idx        NUMBER   NOT NULL, -- 회원고유번호
	not_type     NUMBER(1) NOT NULL, -- 알림유형  0 전체공지 / 1 petcare / 2 reservation / 3 payment / 4 board / 5 화상채팅
	not_message   CLOB     NOT NULL, -- 알림내용
	not_date      DATE     NOT NULL, -- 알림발송일시
	not_readcheck NUMBER(1)   default 0 NOT NULL  -- 확인여부 확인 1 / 미확인 0ㄴ
    ,CONSTRAINT PK_notification -- 알림 기본키
		PRIMARY KEY (not_UID)
    ,CONSTRAINT CK_not_type -- 알림유형 체크제약
		check(not_type in(0,1,2,3,4))
    ,CONSTRAINT CK_not_readcheck -- 확인여부 체크제약
		check(not_readcheck in(0,1))
);

alter table notification drop constraint CK_not_type;

alter table notification
add constraint CK_not_type check (not_type in(0,1,2,3,4,5));

alter table notification
add not_remindstatus NUMBER(1) default 0 NOT NULL; -- 재알림 여부

alter table notification
add CONSTRAINT CK_not_remindstatus  check(not_remindstatus in (0,1)); -- 재알람 여부 제약조건추가

alter table notification
add not_time DATE default sysdate NOT NULL; -- 예약알림 예정시간

alter table notification
add not_URL VARCHAR2(200) default 'http://localhost:9090/petopia/notificationList.pet' NOT NULL; -- 이동url

-- 190130
alter table notification
modify not_URL 'http://localhost:9090/petopia/notificationList.pet';

-- 190213
alter table notification
modify NOT_DATE default sysdate;

create sequence seq_notification_UID --알람
start with 1
increment by 1
nomaxvalue
nominvalue
nocycle
nocache;
```

- xml(sql) -> dao -> service ->  **컨트롤러에서 사용**

  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd"> 
  
  <mapper namespace="notification">
  
  <!-- 회원의 고유번호를 이용한 안읽은 알림 갯수 나타내기 -->
  <select id="selectUnreadNotificationCount" parameterType="int" resultType="int">
  	select count(*)
  	from notification
  	where fk_idx = #{idx}
  	and not_readcheck = 0
  	and to_char(not_time, 'yyyy-mm-dd hh24:mi:ss') <![CDATA[<=]]> to_char(sysdate, 'yyyy-mm-dd hh24:mi:ss')
  </select>
  
  <!-- 회원의 고유번호를 이용한 심플 알림정보 가져오기(알림타입과 그 갯수) -->
  <resultMap type="HashMap" id="selectNotificatioSimplenListMap">
  	<result property="NOT_TYPE" column="not_type" javaType="String" />
  	<result property="COUNT" column="count" javaType="String" />
  </resultMap>
  
  <select id="selectNotificatioSimplenList" parameterType="int" resultMap="selectNotificatioSimplenListMap">
  	select not_type, count(not_type) as count
  	from notification
  	where fk_idx = #{idx}
  	and not_readcheck = 0
  	and to_char(not_time, 'yyyy-mm-dd hh24:mi:ss') <![CDATA[<=]]> to_char(sysdate, 'yyyy-mm-dd hh24:mi:ss')
  	group by not_type
  </select>
  
  <!-- 알림 리스트 가져오기 -->
  <select id="selectNotificatioList" parameterType="HashMap" resultType="com.final2.petopia.model.NotificationVO">	
  select  RNO, NOT_UID, FK_IDX, NOT_TYPE, NOT_MESSAGE, NOT_DATE, 
  		NOT_READCHECK, NOT_REMINDSTATUS, NOT_TIME, NOT_URL
  	from
  	(
  	select  ROWNUM as RNO, NOT_UID, FK_IDX, NOT_TYPE, NOT_MESSAGE, NOT_DATE, 
  			NOT_READCHECK, NOT_REMINDSTATUS, NOT_TIME, NOT_URL
  		from
  		(
  			select 	NOT_UID, FK_IDX, NOT_TYPE, NOT_MESSAGE, NOT_DATE, 
  					NOT_READCHECK, NOT_REMINDSTATUS, NOT_TIME, NOT_URL
  			from notification
  			where fk_idx = #{IDX}
  			and to_char(not_time, 'yyyy-mm-dd hh24:mi:ss') <![CDATA[<=]]> to_char(sysdate, 'yyyy-mm-dd hh24:mi:ss')
  			order by NOT_UID desc
  		) V
  	) T
  where RNO between #{STARTRNO} AND #{ENDRNO}
  </select>
  
  <!-- 전체 알림 수 가져오기 -->
  <select id="selectTotalNotCount" parameterType="int" resultType="int">
  	select count(*)
  	from notification
  	where fk_idx = #{idx}
  	and to_char(not_time, 'yyyy-mm-dd hh24:mi:ss') <![CDATA[<=]]> to_char(sysdate, 'yyyy-mm-dd hh24:mi:ss')
  </select>
  
  <!-- 알림번호 통해 알림 읽음 상태로 업데이트 -->
  <update id="updateReadcheck" parameterType="HashMap">
  	update notification set not_readcheck = 1
  	where not_uid = #{NOT_UID} and fk_idx = #{IDX}
  </update>
  
  
  <!-- 회원번호, 알림번호를 통해 재알림할 하나의 알림 select -->
  <select id="selectNotification" parameterType="HashMap" resultType="com.final2.petopia.model.NotificationVO">
  	select  NOT_UID, FK_IDX, NOT_TYPE, NOT_MESSAGE, NOT_DATE, 
  			NOT_READCHECK, NOT_REMINDSTATUS, NOT_TIME, NOT_URL
  	from notification
  	where NOT_UID = #{NOT_UID} and FK_IDX = #{IDX}
  </select>
  
  <!-- 재알림 insert -->
  <insert id="insertRemindNot" parameterType="com.final2.petopia.model.NotificationVO">
  	insert into notification(NOT_UID, FK_IDX, NOT_TYPE, NOT_MESSAGE, NOT_URL, NOT_DATE, NOT_TIME, NOT_READCHECK, NOT_REMINDSTATUS)
  	values(seq_notification_UID.nextval, #{fk_idx}, #{not_type}, #{not_message}, #{not_URL},  default, to_date(to_char((sysdate+(5/60*1/24)), 'yyyy-mm-dd hh24:mi:ss'), 'yyyy-mm-dd hh24:mi:ss'), default, 1) 
  </insert>
  
  <!-- 알림 삭제 -->
  <delete id="deleteNot" parameterType="HashMap">
  	delete from notification
  	where not_uid = #{NOT_UID} AND fk_idx = #{IDX}
  </delete>
  
  </mapper>
  ```

- controller

  ```java
  	@Controller
  public class NotificationController {
  
  	//===== 의존객체 주입(DI:Dependency Injection)  =====
  	@Autowired
  	private InterNotificationService service;
  	
  	// ----------------------------------------------------------------------------------------------------------
  	
  	// 안읽은 알림 배지 생성(AJAX) ------------------------------------------------------------------------------------
  	@RequestMapping(value="/unreadNotificationCount.pet", method= {RequestMethod.GET})
  	@ResponseBody
  	public HashMap<String, Integer> unreadNotificationCount(HttpServletRequest req, HttpServletResponse res) throws Throwable {
  		HashMap<String, Integer> returnMap = new HashMap<String, Integer>();
  		
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");		
  		int idx = loginuser.getIdx();
  		
  		// 회원의 고유번호를 이용한 안읽은 알림 갯수 나타내기
  		int unreadNotificationCount = service.selectUnreadNotificationCount(idx);
  		
  		returnMap.put("UNREADNOTIFICATIONCOUNT", unreadNotificationCount);
  		
  		// 접속한 페이지주소가 notificationList.pet 라면 카운트를 비교해서 알림리스트를 가져오는 ajax를 실행
  		
  		return returnMap;
  	}
  	
  	// 알림 아이콘 클릭 시 심플알림창 생성(AJAX) -------------------------------------------------------------------------
  	// (안읽은 알림만 생성)
  	@RequestMapping(value="/notificationSimpleList.pet", method= {RequestMethod.GET})
  	@ResponseBody
  	public List<HashMap<String, String>> requireLogin_notificationSimpleList(HttpServletRequest req, HttpServletResponse res) throws Throwable {
  		
  		List<HashMap<String, String>> notificationSimpleList = new ArrayList<HashMap<String, String>>();
  		
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");
  		int idx = loginuser.getIdx();
  		
  		// 회원의 고유번호를 이용한 심플 알림정보 가져오기(알림타입과 그 갯수)
  		List<HashMap<String, String>> n_List = service.selectNotificatioSimplenList(idx);
  		
  		// HashMap에 nvoList안의 nvo.not_type에 따라 문구 넣기
  		for(int i=0; i<n_List.size(); i++) {
  			
  			HashMap<String, String> map = new HashMap<String, String>();
  			
  			String simpleMsg = "";
  			 
  			switch (n_List.get(i).get("NOT_TYPE")) {
  			case "0":
  				simpleMsg = "댓글이 없는 상담글이 있습니다.";
  				break;
  			case "1":
  				simpleMsg = "케어 알림이 도착했습니다.";
  				break;
  			case "2":
  				simpleMsg = "예약 알림이 있습니다.";
  				break;
  			case "3":
  				simpleMsg = "결제대기 중인 예약이 있습니다.";
  				break;
  			case "4":
  				simpleMsg = "게시글에 새 댓글이 있습니다.";
  				break;
  			case "5":
  				simpleMsg = "화상상담 코드가 도착했습니다.";
  				break;
  			} // end of switch
  			
  			map.put("SIMPLEMSG", simpleMsg);
  			map.put("COUNT", n_List.get(i).get("COUNT"));
  			
  			
  			notificationSimpleList.add(map);
  		} // end of for
  		
  		return notificationSimpleList;
  	}
  	
  	// 알림 페이지 요청 -----------------------------------------------------------------------------------------------
  	@RequestMapping(value="/notificationList.pet", method= {RequestMethod.GET})
  	public String requireLogin_notificationList(HttpServletRequest req, HttpServletResponse res) {
  		
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");
  		int idx = loginuser.getIdx();
  		
  		// 전체 알림 수 가져오기
  		int totalNotCount = service.selectTotalNotCount(idx);
  		
  		req.setAttribute("totalNotCount", totalNotCount);
  		
  		return "notification/notificationList.tiles2";
  	}
  	
  	// 알림 페이지 내용 생성(AJAX) -------------------------------------------------------------------------------------
  	@RequestMapping(value="/notificationListAJAX.pet", method= {RequestMethod.GET})
  	@ResponseBody
  	public List<HashMap<String, String>> requireLogin_notificationListAJAX(HttpServletRequest req, HttpServletResponse res) throws Throwable {
  	
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");
  		int idx = loginuser.getIdx();
  		
  		String start = req.getParameter("start");
  		String length = req.getParameter("length");
  		
  		int startRno = Integer.parseInt(start);
  		int endRno = startRno + Integer.parseInt(length) - 1;
  		
  		HashMap<String, Integer> paraMap = new HashMap<String, Integer>();
  		
  		paraMap.put("IDX", idx);
  		paraMap.put("STARTRNO", startRno);
  		paraMap.put("ENDRNO", endRno);
  		
  		// 알림 리스트 가져오기
  		List<NotificationVO> notificationList = service.selectNotificationList(paraMap);
  		
  		List<HashMap<String, String>> returnMapList = new ArrayList<HashMap<String, String>>();
  		
  		if(notificationList.size() > 0) {
  			for(NotificationVO nvo : notificationList) {
  				HashMap<String, String> returnMap = new HashMap<String, String>();
  				
  				returnMap.put("NOT_UID", nvo.getNot_UID());
  				returnMap.put("NOT_TYPE", nvo.getShowNot_type());
  				returnMap.put("NOT_MESSAGE", nvo.getNot_message());
  				returnMap.put("NOT_MESSAGE_COMMENT", nvo.getShowNot_message());
  				returnMap.put("NOT_DATE", nvo.getNot_date());
  				returnMap.put("NOT_READCHECK", nvo.getNot_readcheck());
  				returnMap.put("NOT_REMINDSTATUS", nvo.getNot_remindstatus());
  				returnMap.put("NOT_TIME", nvo.getNot_time());
  				returnMap.put("NOT_URL", nvo.getNot_URL());
  				
  				returnMapList.add(returnMap);
  			}
  		}
  		
  		return returnMapList;
  	}
  	
  	// 알림 내용 클릭 시 not_readcheck 컬럼 1로 변경 -------------------------------------------------------------------------
  	@RequestMapping(value="/updateReadcheck.pet", method= {RequestMethod.POST})
  	public String requireLogin_updateReadcheck(HttpServletRequest req, HttpServletResponse res) {
  		
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");
  		int idx = loginuser.getIdx();
  		
  		int not_uid = Integer.parseInt(req.getParameter("not_uid"));
  		String not_URL = req.getParameter("not_URL");
  		
  		HashMap<String, Integer> paraMap = new HashMap<String, Integer>();
  		
  		paraMap.put("IDX", idx);
  		paraMap.put("NOT_UID", not_uid);
  		
  		// 가져온 알림번호를 통해 readcheck를 읽음상태로 업데이트
  		int n = service.updateReadcheck(paraMap);
  		
  		if(n == 1) {
  		
  			String msg = "해당 게시글로 이동합니다.";
  			
  			req.setAttribute("msg", msg);
  			req.setAttribute("loc", not_URL);
  			
  			
  		}
  		else {
  			
  			String msg = "다시 시도해주세요!";
  			
  			String loc = "javascript:history.back();";
  			
  			req.setAttribute("msg", msg);
  			req.setAttribute("loc", loc);
  			
  		}
  		
  		return "msg";
  	}
  
  	// 재알림 클릭 시 5분 뒤 시간으로 알림 insert -------------------------------------------------------------------------
  	@RequestMapping(value="/insertRemindNot.pet", method= {RequestMethod.POST})
  	public String requireLogin_insertRemindNot(HttpServletRequest req, HttpServletResponse res) {
  		
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");
  		int idx = loginuser.getIdx();
  		
  		int not_uid = Integer.parseInt(req.getParameter("not_uid"));
  		
  		HashMap<String, Integer> paraMap = new HashMap<String, Integer>();
  		
  		paraMap.put("IDX", idx);
  		paraMap.put("NOT_UID", not_uid);
  		
  		// 회원고유번호와 알림고유번호를 통해 알림정보 가져오기
  		NotificationVO nvo = service.selectNotification(paraMap);
  		
  		// 재알림 INSERT
  		int n = service.insertRemindNot(nvo);
  		
  		if(n == 1) {
  			
  			String msg = "재알람 설정이 완료되었습니다.";
  			
  			req.setAttribute("msg", msg);
  			req.setAttribute("loc", req.getContextPath()+"/notificationList.pet");
  			
  		}
  		else {
  			
  			String msg = "다시 시도해주세요!";
  			String loc = "javascript:history.back();";
  			
  			req.setAttribute("msg", msg);
  			req.setAttribute("loc", loc);
  			
  		}
  		
  		return "msg";
  	}
  	
  	// 알림삭제 -------------------------------------------------------------------------
  	@RequestMapping(value="/deleteNot.pet", method= {RequestMethod.POST})
  	public String requireLogin_deleteNot(HttpServletRequest req, HttpServletResponse res) {
  		
  		HttpSession session = req.getSession();
  		MemberVO loginuser = (MemberVO)session.getAttribute("loginuser");
  		int idx = loginuser.getIdx();
  		
  		int not_uid = Integer.parseInt(req.getParameter("not_uid"));
  		
  		HashMap<String, Integer> paraMap = new HashMap<String, Integer>();
  		
  		paraMap.put("IDX", idx);
  		paraMap.put("NOT_UID", not_uid);
  		
  		// 알림 삭제
  		int n = service.deleteNot(paraMap);
  		
  		if(n == 1) {
  			
  			String msg = "알림이 삭제되었습니다.";
  			
  			req.setAttribute("msg", msg);
  			req.setAttribute("loc", req.getContextPath()+"/notificationList.pet");
  			
  			
  		}
  		else {
  			
  			String msg = "다시 시도해주세요!";
  			String loc = "javascript:history.back();";
  			
  			req.setAttribute("msg", msg);
  			req.setAttribute("loc", loc);
  			
  		}
  		
  		return "msg";
  		
  	}
  
  }
  ```

- 이제 다른 부분(댓글 작성 등)에서 내 글에, 내가 아닌 댓글이 달릴 때 사용



#### User는 JobStatus를 [Employee를 정보는 입력하되 Status대기 작성 + role은 User를 유지]상태로 Employee에 올라갈 수 있게 한다? (Employee중에  role ==User 상태로 대기를 골라낼 수 있지만,  User들중에 JobStatus대기로 골라낼 수 도 있다? 사실상 Role더 중요해서, Role은 절대 올리면 안된다.) 그렇다면, Employee로 전환시 JobStatus는 기본 재직이지만, Employee신청시에는 Role이 User인 것은 명확하나, Jobstatus를 대기로 들어가게 만들어야할 것이다?? Jobstatus는 퇴사 등을 고려할때를 위해 필드를 유지하긴 해야한다. -> is_staff 등 확인조건들에서 jobStatus로 [role은 Staff를 유지한체 퇴사상태]를 골라내도록 변경하자.





#### User와 직원정보 입력하여 전환 요청하고 기다리기? Staff가 퇴사하기? 



##### 그게 아니라 staff가 특정User에게 초대 



#### 직원이라면, 내 정보(UserInfo)에 직원정보를 넣고,  수정시에는 직위빼고 넣어주기?

