### 모델변화

#### user에 개발중인 성별/이메일/주소/인삿말 데이터 추가

![image-20221202162550015](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221202162550015.png)

#### settings 모델 추가

- pampa 참고

  ![image-20221202224524677](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221202224524677.png)

- **현재 app에 대해 2row이상 늘어날 일이 없고**

  - **칼럼으로 세팅값을 넣어 db를 구성한다면, 세팅값 증가시마다 db구조가 바뀌므로**
  - **각 app세팅정보를 db에는 row별로 key칼럼 value칼럼으로 매핑하여 `세팅값 변화에 유동적으로 대처하는 dict매핑db`가 되도록한다**

### 기존 데이터 백업 in db_creator.py

#### dump_sqlalchemy메서드 with MyJSONEncoder클래스

- medatdata에서 뽑아온 table정보를 이용하면

  - `table.name` -> table이름정보
  - `[dict(row) for row in engine.execute(table.select())]` -> 테이블 데이터를 dict list로

- 모든 테이블을 데이터를 각 key에 dict list로 저장할 tables = {}를 선언해서 채워준다.

  - table_name= 인자가 오면, tables 안에 해당 table만 저장한다
  - is_id_change= 가 오면, pk중복에 걸리는 것을 방지하여 10000을 더한 id를 반환한다

- json.dumps()로 json정보로 바꿀 때

  - `default = 메핑메서드` or `cls=default메서드를 가진 class`를 지정해줘서 **datetime이나 float타입을 에러없이 JSON 시리얼라이즈 시킨다**

  

```python
class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime,)):
            return {"val": obj.isoformat(), "_spec_type": "datetime"}
        elif isinstance(obj, (decimal.Decimal,)):
            return {"val": str(obj), "_spec_type": "decimal"}
        ## banner_type의 IntEnum타입이 super().default(obj)에 걸리면, 에러나서 나머지들은 그냥 통과해도 된다.?!
        # else:
        #     return super().default(obj)
        ## datetime은 한번더 json에 감싸서 저장된다. for json.loads
        # "add_date": {
        #                 "val": "2022-11-28T00:02:50.816838",
        #                 "_spec_type": "datetime"
        #             },


def dump_sqlalchemy(table_name=None, is_id_change=False):

    metadata = Base.metadata

    tables = {}
    for table in metadata.sorted_tables:
        if table_name and table_name != table.name:
            continue

        # 데이터를 뻥튀기를 위해, 백업후 bulk_insert할 때, pk제약조건에 걸릴시 -> id + 10000로 백업함. # ex> "id": 10001,
        if is_id_change:
            row_dict_list = []
            for row_dict in [dict(row) for row in engine.execute(table.select())]:
                row_dict["id"] = row_dict["id"] + 10000
                row_dict_list.append(row_dict)

            tables[table.name] = row_dict_list
        else:
            tables[table.name] = [dict(row) for row in engine.execute(table.select())]

        # https://www.geeksforgeeks.org/python-difference-between-json-dump-and-json-dumps/
        # 객체 or stringdump는 dumps 저장은 dump
        # datetime은 default를 지정안하면, 에러난다.
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable/36142844#36142844
        # return json.dumps(result, ensure_ascii=False, indent=4, default=str)
        # => https://www.bogotobogo.com/python/python-json-dumps-loads-file-read-write.php

    file_name = f'./backup_{datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")}.json'
    # tables_json = json.dumps(tables, ensure_ascii=False, indent=4, default=default)
    tables_json = json.dumps(tables, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
    with open(file_name, "w", encoding='utf-8') as f:
        f.write(tables_json)
        print("저장>>>", file_name)

```



#### bulk_insert_from_json



##### load_dump 메서드 with object_hook메서드 + CONVERTERS 함수객체 dict

- 백업한 json을 다시 tables dict로 로드하는데
  - **MyJSOEncoder로  type정보를 입력해줬던 것을 인식해서, 각각의 parser 함수객체를 이용하여  해당 type이 오면, 호출해서 파싱한다**

```python
CONVERTERS = {
    'datetime': dateutil.parser.parse,
    'decimal': decimal.Decimal,
}

def object_hook(obj):
    _spec_type = obj.get('_spec_type')
    if not _spec_type:
        return obj

    if _spec_type in CONVERTERS:
        return CONVERTERS[_spec_type](obj['val'])
    else:
        raise Exception('Unknown {}'.format(_spec_type))

def load_dump(file_name):
    tables = {}
    with open(file_name, "r", encoding='utf-8') as f:
        tables = json.load(f, object_hook=object_hook)

    return tables
```





##### get_class_by_tablename

- `Base.registry.mappers`에는 각각의 mapper된 정보가 있으며, **`.class_`로 해당 Entity cls를 불러올 수 있다.**
  - 순회하면서, **`cls.__table__name`과 입력한 tablename이 일치하면, 해당 class를 넘겨준다.**

```python
def get_class_by_tablename(tablename):
    """Return class reference mapped to table.

    :param tablename: String with name of table.
    :return: Class reference or None.
    """
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__') and cls.__tablename__ == tablename:
            # print(cls.__tablename__)
            return cls
    raise ValueError('해당 tablename을 가진 Entity가 존재하지 않음.')

```



##### bulk_insert_from_json

- load_dump로 불러온 tables dict에 있는 각 table데이터를 **`session.bulk_insert_mappings( Entity, 데이터 dictlist)`로 입력한다**

```python
def bulk_insert_from_json(file_name, table_name=None):
    metadata = Base.metadata
    session = Session()

    tables = load_dump(file_name)

    # engine.execute(foreign_key_turn_off[engine_name])
    for table in metadata.sorted_tables:
        if table_name and table.name != table_name:
            continue
        table_datas = tables[table.name]
        # print(table_datas) # [{'add_date': datetime.datetime(2022, 11, 25, 17, 58, 41, 579745),
        session.bulk_insert_mappings(
            get_class_by_tablename(table.name),
            table_datas
        )

    session.commit()
    # engine.execute(foreign_key_turn_on[engine.name])

```



#### create_databse.py에서 만든 모듈 import 

```python
from src.infra.config.db_creator import create_db, Session, dump_sqlalchemy, bulk_insert_from_json

```





#### 백업 수행

- main.py에서 수행한다

```python
from create_database_tutorial3 import *

if __name__ == '__main__':
    # dump_sqlalchemy('users',is_id_change=True)
    dump_sqlalchemy()
    
    
# 저장>>> ./backup_2022-12-02_224324.json    
```



### DB 모델 변화

#### auth / users.py

```python
class SexType(enum.IntEnum):
    미정 = 0
    남자 = 1
    여자 = 2

    # form을 위한 choices에는, 선택권한을 안준다? -> 없음 0을 제외시킴
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls if choice.value]


class User(BaseModel):
    __tablename__ = 'users'
    # 가입시 필수
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    password = Column(String(320), nullable=False)

    # 가입후에 수정 -> nullable = True
    is_super_user = Column(Boolean, nullable=True, default=False)
    is_active = Column(Boolean, nullable=True, default=True)
    is_staff = Column(Boolean, nullable=True, default=False)
    avatar = Column(String(200), nullable=True)

    ## 추가
    # email/phone은 선택정보이지만, 존재한다면 unique검사가 들어가야한다.
    # => form에서 unique를 검증하고  추가정보로서 unique키를 주면 안된다(None대입이 안되서 unique제약조건에 걸림)
    sex = Column(IntEnum(SexType), default=SexType.미정, nullable=True)
    # email = Column(String(128), nullable=True, unique=True)
    email = Column(String(128), nullable=True)
    address = Column(String(60), nullable=True)
    # phone = Column(String(11), nullable=True, unique=True)
    phone = Column(String(11), nullable=True)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}]"
        return info

```





#### admin/ settings.py

```python
from sqlalchemy import Column, Integer, String, Boolean
from src.infra.tutorial3.common.base import BaseModel


class Setting(BaseModel):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    skey = Column(String(64), index=True, unique=True)
    svalue = Column(String(800), default='')

    def __repr__(self) -> str:
        return f'{self.id}=>{self.skey}'

```



##### 새로 생긴 모델은 자신패키지의 init -> infra 패키지의 init에 올려주기 (create_databse 및 main은 infra자체를 import *)

- 자신의 init

  ```python
  from .banners import Banner, BannerType
  from .settings import Setting
  
  ```

- infra 패키지의 init

  ```python
  from .comments import Comment
  from .menus import Menu
  from .notices import Notice, BannerType
  from .categories import Category, Post, PostPublishType, posttags, Tag
  from .auth import User
  from .admin import Banner, BannerType, Setting
  ```

  

#### users 모델만 백업 -> db 삭제 ->  create_database로 users + 데이터채우기,  settings 모델 만들기

```python
from create_database_tutorial3 import *

if __name__ == '__main__':

    session = Session()
    create_database(truncate=False, drop_table=False, load_fake_data=False)
    bulk_insert_from_json('./backup_2022-12-02_211719.json', 'users')
```

![image-20221202232208185](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221202232208185.png)



### model변화에 따른, admin/ user crud 수정

#### 일단은 추가정보라 admin에서 관리할 필요가 없을 것이라 판단되어 보류 중.

- 현재 user 관리

  ![image-20221203035320650](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203035320650.png)





### 일반유저용 추가정보 수정 UserinfoForm 개설

#### admin용 CreateUserForm / 일단가입 필수정보용 RegisterForm과 다른, 추가정보기입용 UserInfoForm 만들기

##### User model중 추가정보필드로만  formfield로 구성

- 기존에 있던 admin민용 `avatar도 추가정보라 포함`해야할듯.

- `username`은 수정은 안하지만 정보란에 보여주기용으로서 `render_kw=dict(disabled=True)`로 비활성화된 input으로 내려주기 위해 추가

  - route에서 .dataㄷ받고 수정은 하는 행위 X

- **선택 필드의 추가사항**

  - validators에 **`Optional()`을 추가하여 `데이터 입력안한상태로 POST 허용`하게 한다**
    - Radio필드의 경우 선택안하면 기본적으로 validation error가 난다
  - **String필드의 경우, `""`빈문자열이 오는 경우를 `None으로 처리되게 하기 위해 filters=[lambda x: x or None]`를 추가한다**
    - radio의 경우 coerce=int로 주면, 선택안함 None => int => 0으로 들어온다
      - **0이 default(미정)으로 되어있어서 그대로 두면 된다.?!**

  - **phone같이 `입력된 정보를 추가처리`해야하는 경우 `filters`에 들어갈 메서드를 정의해서 넣어준다.**
    - **validate_phone필드할때도 filters로 처리된 데이터를 검증한다**



- **Optional일 경우, unique검사를 위한 validate_ 메서드를 안타니, 따로 None데이터일때는 안타도록 처리 안해도 된다.**

  ```python
      def validate_phone(self, field):
          #### 추가정보는 데이터가 있을때만 하자.
          # if not field.data:
          #     return
          print("옵셔널필드의 경우 입력안할시 validate_ 메서드를 타나?")
  
  ```

  - **입력안하면 안탐**

    - 중복된 phone번호를 입력한 경우

      ![image-20221203231137505](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203231137505.png)

    - 아예 phone을 입력안한 경우

      ![image-20221203231201851](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203231201851.png)



##### 추가정보라서 "" emptystring으로 오는 `StringField + nullable =True`에는 filters = [lambda x: x or None] 걸어주기

- 하지 않으면 db에는 `추가정보 수정안한사람 null` vs `추가정보 수정했는데 빈값으로 온 ""` 나눠서 들어온다

  ![image-20221203173636621](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203173636621.png)

- filters를 걸어주고, 추가정보 입력없이 완료 눌렀을 때

  ![image-20221203173712541](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203173712541.png)



#### UserInfoForm

```python
class UserInfoForm(FlaskForm):
    # 보여주기용 필드 추가
    username = StringField('Username', render_kw=dict(disabled=True))

    avatar = FileField("avatar", validators=[
        # FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'bmp', 'png', 'gif'], message="jpg/jpeg/bmp/png/gif 형식만 지원합니다"),
        FileSize(max_size=2048000, message="2M 이하의 파일만 업로드 가능합니다")],
                       description="파일크기가 2M이하만 지원합니다. 또한, jpg/jpeg/bmp/png/gif 형식만 지원합니다，빈칸으로 두는 경우, 수정하지 않습니다！")
    # 추가정보 radio field의 경우, 선택안한 경우도 허용하려면
    # => Optional()을 validators로 준다.
    sex = RadioField('성별', validators=[Optional()],
                     choices=SexType.choices(),
                     default=SexType.미정.value,
                     coerce=int,
                     )
    # emailfield를 이용하면 email형식을 자동으로 잡아준다.
    # nullable String은 -> filters를 걸어 "" 대신 None이 들어와야한다.
    email = EmailField("이메일", validators=[Optional()],
                       filters=[lambda x: x or None]
                       )
    address = StringField("주소", validators=[Optional()],
                          filters=[lambda x: x or None]
                          )

    def remove_phone_delimiter(phone):
        # nullable 필드라 None이 넘어올 수 있다. 애초에 데이터 없을 때.. form화면
        if phone:
            return re.sub('[-| ]', '', phone)
        else:
            # nullable String은 -> filters를 걸어 "" 대신 None이 들어와야한다.
            return None

    phone = StringField("전화번호", validators=[
        Regexp("^01\d{1}[ |-]?\d{4}[ |-]?\d{4}", message="01X로 시작하는 11자리 휴대폰번호를 입력해주세요. 하이픈(-) 사용유무는 선택입니다."),
        Optional()],
                        filters=(remove_phone_delimiter,),
                        description="[010 1234 1234], [01012341234], [011-1234-1234] 3가지 다 입력가능! 포함 숫자 11개만 주의!"
                        )



    # 수정formd를 위한  생성자 재정의
    def __init__(self, user=None, *args, **kwargs):
        self.user = user

        if self.user:
            super().__init__(**self.user.__dict__)
        else:
            super().__init__(*args, **kwargs)

    #### null가능한 추가정보라서 uniquekey로 못넣고, 폼에서 존재유무 검사 
    def validate_email(self, field):
        #### 추가정보는 데이터가 있을때만 하자.
        # if not field.data:
        #     return
        print("옵셔널필드의 경우 입력안할시 validate_ 메서드를 타나?")

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

    def validate_phone(self, field):
        #### 추가정보는 데이터가 있을때만 하자. -> Optional인 경우 안타니까
        # if not field.data:
        #     return
        print("옵셔널필드의 경우 입력안할시 validate_ 메서드를 타나?")

        # print(field.data, "<<< validate시 phone filters에 걸린 데이터가 넘어오나?")
        # 01046006243 <<< validate시 phone filters에 걸린 데이터가 넘어오나?
        # => 그렇다. validate에서는 filters를 거친 데이터가 들어온다.

        if self.user:  # 수정시 자신의 제외하고 데이터 중복 검사
            condition = and_(User.id != self.user.id, User.phone == field.data)
        else:  # 생성시 자신의 데이터를 중복검사
            condition = User.phone == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 phone 입니다')

```



### userinfo_edit route



#### user_info route는 add/delete route없이 edit route로 시작

```python
@auth_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def userinfo_edit(id):
    # with DBConnectionHandler() as db:
    #     user = db.session.get(User, id)

    form = UserInfoForm(g.user)
    return render_template('auth/userinfo_form.html',
                           form=form)
```

​	







### userinfo.html 변경사항

#### edit route 로 가는 url_for 추가

##### 현재유저 수정 -> route에서 g.user로 꺼내쓰므로, id를 안넘긴다.

```html
<div class="column is-narrow-mobile">
    <a class=" button is-light is-pulled-right"
       href="{{url_for('auth.userinfo_edit') }}"
       style="margin-top: 1.8rem">정보 수정</a>
</div>
```



#### b-tabs부분만 userinfo_form.html이 상속할 수 있도록 tab_content block열어주고, 에러 메세지 message 부분 추가하기

```html
{% block member %}
<template>

    <!-- flash message -->
    {% with messages = get_flashed_messages() %}
    <b-message type="is-success">
        {% if messages %}
        <ul class=flashes>
            {% for message in messages %}
            <li>{{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </b-message>
    {% endwith %}

    <!-- form validation -->
    {% if form and form.errors %}
    <b-message type="is-danger">
        <ul class="errors">
            {% for error, v in form.errors.items() %}
            <li>{{ error }}：{{ v[0] }}</li>
            {% endfor %}
        </ul>
    </b-message>
    {% endif %}
    <!-- userinfo_form에서 달라질 부분 block개설  -->
    {% block tab_content %}
    <b-tabs>
```



#### form에서 넘어오는 phone번호를 view화면에서 이어줄 filter추가

- templates > filters> `join_phone.py`

```python
def join_phone(phone: str, delimiter='-'):
    if phone:
        return delimiter.join([phone[:3], phone[3:7], phone[7:]])
    return phone


if __name__ == "__main__":
    print(join_phone('01046006243'))
    print(join_phone('01046006243', delimiter=' '))
```



```python
# app.py
app.jinja_env.filters["join_phone"] = join_phone
```

```html
<div class="content">
    {% if g.user.phone %}
    {{g.user.phone | join_phone }}
    {% else %}
    없음
    {% endif %}
</div>
```

![image-20221203144544110](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203144544110.png)

##### front 73_userinfo_change_after_userinfo_form.html

```html
{% extends 'admin/index.html' %}

<!-- admin/index.html 중 왼쪽칼럼2개짜리 메뉴의 실제 aside태그부분-->
{% block menus %}
<aside class="menu">
    <p class="menu-label">
        User 설정
    </p>
    <ul class="menu-list">
        <li><a class="{% if  '/auth/' in request.path %}is-active{% endif %}"
               href="{{ url_for('auth.userinfo') }}">
            내 정보</a>
        </li>
        <li>
            <a class="" href="">내 Post</a>
        </li>
        <li>
            <a class="" href="">내 댓글</a>
        </li>
    </ul>
</aside>
{% endblock menus %}

{% block member %}
<template>

    <!-- flash message -->
    {% with messages = get_flashed_messages() %}
    <b-message type="is-success">
        {% if messages %}
        <ul class=flashes>
            {% for message in messages %}
            <li>{{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </b-message>
    {% endwith %}

    <!-- form validation -->
    {% if form and form.errors %}
    <b-message type="is-danger">
        <ul class="errors">
            {% for error, v in form.errors.items() %}
            <li>{{ error }}：{{ v[0] }}</li>
            {% endfor %}
        </ul>
    </b-message>
    {% endif %}
    <!-- userinfo_form에서 달라질 부분 block개설  -->
    {% block tab_content %}
    <b-tabs>
        <!-- 탭1 내 정보 -->
        <b-tab-item label="내 정보" icon="account-outline">
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px; padding-bottom: 1rem">
                <div class="column is-narrow">
                    <figure class="image is-96x96">
                        <img class="is-rounded" style="height: 100%;"
                             src="
                                 {% if g.user.avatar %}
                                 {{url_for('download_file', filename=g.user.avatar)}}
                                 {% else %}
                                 {{url_for('static', filename='/img/user/default_avatar.svg')}}
                                 {% endif %}
                                "
                        >
                    </figure>
                </div>
                <div class="column is-narrow">
                    <div style="padding-top: 1.5rem;">
                        <h1 class="title is-size-4">{{ g.user['username'] }}</h1>
                        <p class="subtitle is-size-6">등급: {{ '관리자' if g.user.is_super_user else '일반'}}</p>
                    </div>
                </div>
                <div class="column is-narrow-mobile">
                    <a class=" button is-primary is-pulled-right"
                       href="{{url_for('auth.userinfo_edit') }}"
                       style="margin-top: 1.8rem">정보 수정</a>
                </div>
            </div>

            <div class="columns" style="padding:1rem 0; ">
                <div class="column is-2">
                    <p>내 정보</p>
                </div>
                <div class="column">
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">Username</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ g.user['username'] }}</span>
                        </div>
                    </div>
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">성별</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">
                                {% if g.user.sex.value %}
                                {{g.user.sex.name }}
                                {% else %}
                                미입력
                                {% endif %}
                            </span>
                        </div>

                    </div>
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">이메일</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">
                                {% if g.user.email %}
                                {{g.user.email  }}
                                {% else %}
                                미입력
                                {% endif %}
                            </span>
                        </div>

                    </div>

                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">주소</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">
                                {% if g.user.address %}
                                {{g.user.address  }}
                                {% else %}
                                미입력
                                {% endif %}
                            </span>
                        </div>

                    </div>
                </div>
            </div>

            <div class="columns" style="padding:1rem 0; ">
                <div class="column is-2">
                    <p>휴대폰번호</p>
                </div>
                <div class="column">
                    <div class="content">
                        {% if g.user.phone %}
                        {{g.user.phone | join_phone }}
                        {% else %}
                        미입력
                        {% endif %}
                    </div>
                </div>
            </div>
        </b-tab-item>
        <!-- 탭1 끝 -->

    </b-tabs>
    {% endblock tab_content %}
</template>
{% endblock member %}


{% block vue_script %}{% endblock vue_script %}
```







### user에게 허용되는 url을, request.path 내부에 포함되도록 검사 변경

```python
any(url in request.path for url in urls):
```





### userinfo_form.html

#### front - 74_userinfo_form_extends_userinfo_after_userinfo_edit_route.html

```html
{% extends 'auth/userinfo.html' %}


{% block tab_content %}

<b-tabs>
    <!-- 탭1 내 정보 -->
    <b-tab-item label="내 정보" icon="account-outline">
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
                                 {% if g.user.avatar %}
                                 {{url_for('download_file', filename=g.user.avatar)}}
                                 {% else %}
                                 {{url_for('static', filename='/img/user/default_avatar.svg')}}
                                 {% endif %}
                                "
                        >
                    </figure>
                </div>
                <div class="column is-narrow">
                    <div style="padding-top: 1.5rem;">
                        <h1 class="title is-size-4">{{ g.user['username'] }}</h1>
                        <p class="subtitle is-size-6">등급: {{ '관리자' if g.user.is_super_user else '일반'}}</p>
                    </div>
                </div>

                <!-- avatar  -->
                <!-- column 에 is- 를 줘야, 넘어가면 내부 p태그안의 글자가 newline으로 찍힌다 -->
                <!--                    <div class="column is-narrow">-->
                <div class="column is-narrow is-7">
                    <div style="padding-top: 1.5rem;">
                        <!--                            <b-field label="{{form.avatar.label.text}}">-->
                        <b-field>
                            <b-field class="file is-primary" :class="{'has-name': !!file}">
                                <!-- preview를 위한 v-model="" 추가 / upload를 위한 name=""속성 추가 -->
                                <b-upload
                                        class="file-label" rounded
                                        v-model="file"
                                >
                                      <span class="file-cta">
                                        <b-icon class="file-icon" icon="upload"></b-icon>
                                        <span class="file-label">{$ file.name || "아바타 사진 업로드" $}</span>
                                      </span>
                                </b-upload>
                            </b-field>
                        </b-field>
                    </div>
                    <p class="help has-text-grey-light">
                        {{ form.avatar.description }}
                    </p>
                </div>


            </div>
            <!-- phone -->
            <div class="columns" style="padding:1rem 0; ">
                <div class="column is-2 is-align-items-center is-flex">
                    <p>{{ form.phone.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.phone(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.phone.description }}
                    </p>
                </div>
            </div>
            <div class="columns" style="padding:1rem 0; ">
                <div class="column is-2">
                    <p>추가 정보</p>
                </div>
                <div class="column">
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <!-- input말고 label column만 is-align-items-center is-flex 를 줘서, 가운데 정렬시킨다.-->
                        <div class="column is-2 iis-align-items-center is-flex">
                            <span class=" has-text-grey-light">{{form.username.label(class='label')}}</span>
                        </div>
                        <div class="column is-narrow is-align-items-center is-flex">
                            <span class=" has-text-black-ter">{{form.username(class='input')}}</span>
                        </div>
                    </div>
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2 is-align-items-center is-flex">
                            <span class=" has-text-grey-light">{{form.sex.label(class='label')}}</span>
                        </div>
                        <div class="column is-narrow">
                            <!-- 성별 radio form -->
                            {% for subfield in form.sex %}
                            <input {%if subfield.checked %}checked {% endif %} type="radio"
                                   id="{{ subfield.id }}" name="{{ form.sex.id }}"
                                   value="{{ subfield.data }}">
                            {{ subfield.label }}
                            {% endfor %}
                        </div>

                    </div>
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2 is-align-items-center is-flex ">
                            <!-- email form -->
                            <span class=" has-text-grey-light">{{form.email.label(class='label')}}</span>
                        </div>
                        <div class="column is-6">
                            <span class=" has-text-black-ter">{{ form.email(class='input') }}</span>
                            <p class="help has-text-grey-light">
                                {{ form.email.description }}
                            </p>
                        </div>

                    </div>

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

            <!-- 수정완료 submit -->
            <!-- column을 가운데 놓으려면, columns가 is-centered -->
            <div class="columns is-mobile is-centered">
                <div class="column is-narrow">
                    <input type="submit" value="수정완료"
                           class="button is-primary"
                           style="margin-top: 1.8rem"
                    >
                </div>
            </div>
            <!-- form 끝 -->
        </form>

    </b-tab-item>
    <!-- 탭1 끝 -->

</b-tabs>
{% endblock tab_content %}


{% block vue_script %}{% endblock vue_script %}
```





### 대박 upload preview기능 추가

1. type file input에 @change를 메서드로 달고 -> **url변수에 file url을 동적으로 주입-> img태그에 v-if url을 쓰라는 조언**
   - **b-upload에는 이미 완성된 놈이라 `input에 @click=메서드 다는 것이 불가` -> `url 변수 동적할당후 v-if로 뿌려주는 것 차용`**
   - https://stackoverflow.com/questions/59219113/buefy-how-to-get-binary-contents-of-file-uploaded-with-b-upload
2. **b-upload태그에 `v-model=file`변수를 잡은 상태에서 `file변수를 watch를 걸고` -> `변수로 들어오는 file객체를 처리`**하라는 글
   - https://stackoverflow.com/questions/59219113/buefy-how-to-get-binary-contents-of-file-uploaded-with-b-upload

3. (url)변수 변화에 따른 v-if v-else 적용 3가지 방법 정리
   - https://stackoverflow.com/questions/46921903/vuejs-src-with-a-v-if-condition

#### 정리

1. `b-upload`태그에 **`v-model`을 다른 이미지 업로드 file변수와 겹칠 수 있으니 `userinfo_file`이라고 정의해준다.**

   - 추후 **b-upload에 file input태그에 들어갈 `name="form필드명(avatar)"`도 미리 명시해준다.**

   ```html
   <b-field>
       <b-field class="file is-primary" :class="{'has-name': !!file}">
           <b-upload
                     v-model="userinfo_file"
                     name="avatar"
                     class="file-label" rounded
                     >
               <span class="file-cta">
                   <b-icon class="file-icon" icon="upload"></b-icon>
                   <span class="file-label">{$ userinfo_file.name || "아바타 사진 업로드" $}</span>
               </span>
           </b-upload>
       </b-field>
   </b-field>
   ```

2. **base.html에  `userinfo_file`변수 및 해당 파일을 watch한 뒤, 파일이 들어오면 url를 뽑아줄 `userinfo_file_url` 변수와 `watch 정의`를 해준다.**

   ```js
   var app = new Vue({
       el: '#app',
       delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
       data: {
           file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
           // carousels: [], // main/index에서 b-carousel-item에 test
           banner_list: [], // main/index에서 b-carousel-item에서 슬 변 수
           // activeTab: 0,
           
           // auth/userinfo_form에서 preview를 위한 메서드
           userinfo_file: {},
           userinfo_file_url: null,
       },
   
       watch: {
           userinfo_file: function (file, n) {
               this.userinfo_file_url = URL.createObjectURL(file);
           }
       },
   ```

3. **기존 avatar를 나타내는 img태그의 src를**

   1. `:src`로 v**-bind를 적용시키는 순간 `:src=" vue공간 "` 의 `쌍따옴표 내부는 v-model을 쓰는 vue공간`이 된다.**

   2. **기존 현재유저의 avatar의 경로 유무 -> 이미지 가져오기를 하는데, `기존 src=""안의 문자열들은 아트스트로퍼~ 처리를 해줘야한다.**

      ```html
      <img class="is-rounded" style="height: 100%;"
           :src="
                 `
                 {% if g.user.avatar %}
                 {{url_for('download_file', filename=g.user.avatar)}}
                 {% else %}
                 {{url_for('static', filename='/img/user/default_avatar.svg')}}
                 {% endif %}
                 `
                 "
           >
      ```

      

   3. **vue변수인 userinfo_file_url은 `null초기화에서 file url에 주입됬다면 그 주소로 뿌리도록 삼항연산자로 v-if 바인딩src v-else 일반src를 대신`한다**

      ```html
      <img class="is-rounded" style="height: 100%;"
           :src="
                 userinfo_file_url ? userinfo_file_url :
                 `
                 {% if g.user.avatar %}
                 {{url_for('download_file', filename=g.user.avatar)}}
                 {% else %}
                 {{url_for('static', filename='/img/user/default_avatar.svg')}}
                 {% endif %}
                 `
                 "
           >
      ```

      ![image-20221203172413563](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203172413563.png)

      ![image-20221203172425701](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203172425701.png)



#### route에서 file upload 업로드 기능 추가

1. **b-upload태그에 `name="필드명(avatar)"`을 추가한다**

   ```html
   <b-upload
             class="file-label" rounded
             v-model="userinfo_file"
             name="avatar"
             >
   ```

   

2. **route에서 처리**

   1. form.name속성.data를 f (파일객체)로 받는다.
   2. (업로드 안건들일시)기존필드에 있던 경로가 그대로 넘어왔는지 vs 다른 파일로 업로드로 파일객체가 넘어왔는지 **서로 다르면, 업로드 한 것**이다.
   3. 업로드된 파일을 지정해둔 폴더에 업로드하고
   4. 기존필드상의 경로를 **필드 덮어쓰기 전에  기존경로의 파일 삭제**한 뒤
   5. 필드를 업뎃한다.

   ```python
   #### 파일업로드 처리
   f = form.avatar.data
   # 수정안되서 경로 그대로 오는지 vs 새 파일객체가 오는지 구분
   if f != user.avatar:
       avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
       f.save(avatar_path)
   
       delete_uploaded_file(directory_and_filename=user.avatar)
   
       user.avatar = f'avatar/{filename}'
   
       db.session.add(user)
       db.session.commit()
   
   ```

   

##### front - 75_userinfo_edit_change_for_b-upload_preview적용.html

```html
<b-upload
          class="file-label" rounded
          v-model="userinfo_file"
          name="avatar"
          >
    
    
    
    
<img class="is-rounded" style="height: 100%;"
     :src="
           userinfo_file_url ? userinfo_file_url :
           `
           {% if g.user.avatar %}
           {{url_for('download_file', filename=g.user.avatar)}}
           {% else %}
           {{url_for('static', filename='/img/user/default_avatar.svg')}}
           {% endif %}
           `
           "
     >
```



### userinfo_edit 완성후, 회원가입 성공시, main이 아니라, userinfo_edit로 보내기

```python
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            user = User(username=form.username.data, password=generate_password_hash(form.password.data))
            db.session.add(user)
            db.session.commit()

            session.clear()
            session['user_id'] = user.id

        # return redirect('/')
        #### 회원가입 완료시, userinf_edit로 가서, 추가정보 입력하게 하기
        return redirect(url_for('auth.userinfo_edit'))
```






### Banner_form.html에 preview 적용하기

1. preview 공간 추가

   ```html
   <!--   banner preview를 위한 img태그 공간 추가: columns >column is-7 안에 figure>img 추가   -->
   <div class="columns is-centered">
       <div class="column is-7" style="padding-top: 1.5rem;">
           <figure class="image is-16by9">
               <img class="" style="width:100%;min-height: 50%"
                    :src="
                          userinfo_file_url ? userinfo_file_url :
                          `
                          {% if g.user.avatar %}
                          {{url_for('download_file', filename=g.user.avatar)}}
                          {% else %}
                          {{url_for('static', filename='/img/user/default_avatar.svg')}}
                          {% endif %}
                          `
                          "
                    >
           </figure>
       </div>
   </div>
   ```

   ![image-20221203233926575](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221203233926575.png)





2. img/placeholders에 1920 x 1080 추가

   ![image-20221204001645096](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204001645096.png)

   ![image-20221204001651504](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204001651504.png)

3. **userinfo_file 및 userinfo_file_url변수는 `base.html에서 상속한다면, 고정적으로 선언되는 no block 코드`에서 매번 고정적으로 초기화 코드 호출되는 상황이므로 `변수명만 공통화해서 2개 변수를 같이 써도` 될듯**

   - banner를 userifo_file변수를 사용하고 나서, userinfo넘어오면 초기화되어서 있다.

     ![image-20221204003428695](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204003428695.png)

4. **base.html에서 초기화변수를 img_file, img_file_url로 변경한다. watch에서 보는 변수도, img_file로 변경한다**

   ```html
   <script>
       var app = new Vue({
           el: '#app',
           delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
           data: {
   
               banner_list: [], // main/index에서 b-carousel-item에서 슬 변 수
               // admin/banner_form , auth/userinfo_form 에서 쓰는 b-upload v-model변수
               img_file: {},
               img_file_url: null,
           },
       	watch: {
   
                   // admin/banner_form , auth/userinfo_form 에서 쓰는 b-upload v-model변수
                   // -> this.url변수에 동적으로 할당해주면 -> img태그의 :src에서 url에 정보유무에 따라 다른 img를 건다
                   img_file: function (file, n) {
                       this.img_file_url = URL.createObjectURL(file);
                   }
               },
   ```



5. **userinfo_html, banner_form.html에서 변수명 변경**





##### front - 76_banner_form_change_for_preview.html

```html
<form action="" method="post" class="mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}
    <div class="field">
        {{ form.img.label(class='label') }}
        <div class="control">
            <b-field class="file">
                <b-upload
                        v-model="img_file"
                        name="img" expanded>
                    <a class="button is-primary is-fullwidth">
                        <b-icon icon="upload"></b-icon>
                        <span>{$ img_file.name || "{% if form.banner %}{{ form.banner.img }}{% else %}Click to upload{% endif %}" $}</span>
                    </a>
                </b-upload>
            </b-field>
            <p class="help has-text-grey-light">
                {{ form.img.description }}
            </p>
        </div>
        <!--   banner preview를 위한 img태그 공간 추가: columns >column is-7 안에 figure>img 추가   -->
        <div class="columns is-centered">
            <div class="column is-7" style="padding-top: 1.5rem;">
                <figure class="image is-16by9">
                    <img class="" style="width:100%;min-height: 50%"
                         :src="
                             img_file_url ? img_file_url :
                             `
                             {% if form.banner.img %}
                             {{url_for('download_file', filename=form.banner.img)}}
                             {% else %}
                             {{url_for('static', filename='/img/placeholders/1920x1080.png')}}
                             {% endif %}
                             `
                            "
                    >
                </figure>
            </div>
        </div>

```



