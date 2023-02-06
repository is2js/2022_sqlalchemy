### User entity

#### 23 user select

##### user route

- user entity는 다른entity와 달리 `entity/ auth`에 따로 모아뒀었다.

```python
@admin_bp.route('/user')
@login_required
def user():
    page = request.args.get('page', 1, type=int)

    stmt = select(User).order_by(User.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    user_list = pagination.items

    return render_template('admin/user.html',
                           user_list=user_list, pagination=pagination)
```



##### img_url(avatar) 필드를 들고 있는 entity select의 경우 root에 uploads폴더에 경로부터 잡기

- [참고: Pampa](https://github.com/lovebull/Pampa/blob/64445f3990006753b72a25009e98e5386ace4ad7/app/util/utils.py)

  ![image-20221121205402187](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121205402187.png)



1. src> config> settings.py 에  Project class에 `BASE_FOLDER`를 추가시켜 Path패키지로 root를 잡는다.

   - **이후, UPLOAD_FOLDER을 root에서 잡으며, `.joinpath('uploads/')`를 통해서, `뒤에 개별폴더/파일명`을 입력가능하도록 `/`를 붙여서 upload_path를 만들어준다.**

   ```python
   class Project:
       # project
       PROJECT_NAME: str = os.getenv("PROJECT_NAME")
       PROJECT_VERSION: str = os.getenv("PROJECT_VERSION")
       # file
       BASE_FOLDER = Path(__file__).resolve().parent.parent.parent  # root
       # path로 join만 하면 [마지막을 파일명으로 취급]하여 '/'가 없다.
       # -> 뒤에 개별폴더명이 붙을 joinpath라면 + '마지막 폴더명/'을 붙여서 연결하여, 다음엔 '/'없이 파일명 or 개별폴더명/파일명만 올 수 있도록 만든다.
       UPLOAD_FOLDER = BASE_DIR.joinpath('uploads/')
   
   ```

2. **user.html에서 img태그에 적힐 `src=""`는 `root 시작`이며 root에 있는 uploads폴더를 쓸 것이다.**

   ![image-20221121211609004](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121211609004.png)

   ```html
   <figure class="image is-48x48">
       <img class="is-rounded"
            src="/uploads/{{user.avatar}}"
            alt="{{ user.username }}">
   </figure>
   ```

3. **root의 `/uploads`폴더이후의 `/개별폴더` 중 `/`만 있고 `개별폴더`는 없는 이유는 `user.avatar`필드에 `개별경로/파일명.img`형태로 저장할 것이기 때문이다.**

   - src에서는 폴더를 의미하는 `/uploads  + /`으로 끝나고, `{{ entity.img_url필드 }}`를 준다.

   ![image-20221121211814822](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121211814822.png)

4. 임시user에 적용해보기 위해
   
   1. root에 있는 `uploads`폴더 아래 `avatar`폴더를 만들고 `파일`을 하나 넣자.

![image-20221121212005109](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121212005109.png)

​		2.  **db의 user.avatar에는 `개별폴더/이미지명`으로 넣어주자**

![image-20221121212228245](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121212228245.png)

5. flask에서는 기본적으로 static 폴더내부가 아니면 src로 못가져온다.

   1. `localhost/uploads/~`로 걸리기 때문

      ![image-20221121230133893](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121230133893.png)

![image-20221121230227012](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121230227012.png)



6. **/uploads폴더 내 파일들을,  url/uploads/파일들**로 접근할 수 있도록 route를 만들어야한다.

   1. 개별 route들은 prefix가 있기 때문에, 개별  route에선 등록안한다.
   2. **src>config>app.py에서 `add_url_rule`을 통해 특정route만 등록한다**
   3. **사실상 해당폴더의 다운로드이므로 `send_from_directory()`메서드를 return하는 method를 작성하고 `view_func`에 해당method를 대입한다 **
      - endpoint는 url_for()에 사용될 name인데, view_func이랑 똑같이 주자.

   ```python
   # root의 uploads폴더에 있는 파일들을 인식하여 파일로 반환할 수 있도록 route 개설
   # https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
   # https://ryanking13.github.io/2018/05/22/pathlib.html
   def download_file(filename):
       return send_from_directory(project_config.UPLOAD_FOLDER, filename)
   
   
   app.add_url_rule('/uploads/<path:filename>', endpoint='download_file', view_func=download_file)
   ```

7. 확인해보면, static폴더가 아님에도, 해당 폴더를 route로 인식하고 개별 파일들을 가져올 수 있게 된다.

   ![image-20221121231219575](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121231219575.png)



##### css 경로 다시 잡기

- 기존 css파일들 `static/css/main/ xxx.css`
  - **이렇게 잡으면, materialdesignicon.css 및  .min.css**등이  `url('../fonts/')`로 경로를 걸어놔서, **css폴더를 부모로 잡고, 1번만 뒤로 간 뒤, fonts폴더로 들어가서 font파일들이랑 연동되어야한다.**
  - **어차피 base.html에서 해당css를 다 사용하므로 일단은 main폴더를 따로 두지 않는다.**

![image-20221121171817336](../../../Users/is2js/AppData/Roaming/Typora/typora-user-images/image-20221121171817336.png)

- js도 base.html에 걸리는 것이므로 일단 공통사용으로 개별폴더에서 뺸다.

  ![image-20221121172502618](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121172502618.png)

- **base.html에 연동된 css/js/fonts는 개별폴더가 없으나**
  
  - **templates은 개별폴더로 index를 가지므로 유지중**

![image-20221121173047275](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121173047275.png)

```html
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock title %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/buefy.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/materialdesignicons.min.css') }}">
    {% block extra_head_style %}{% endblock extra_head_style %}
</head>
```

```html
<script src="{{url_for('static', filename='js/vue.js')}}"></script>
<script src="{{url_for('static', filename='js/buefy.min.js')}}"></script>
{% block extra_foot_script %}{% endblock extra_foot_script %}
<script>
    var app = new Vue({
        el: '#app',
        data: {},
        methods: {}
    })
</script>
</body>
```



##### admin / user.html (avatar 등 그림도 표기)

- user entity에 field들 중에 표기할 것들은
  - username보다 avatar를 먼저 표시(그림)
  - **password를 빼고 table에 표시**
  - **avatar가 있다면**
    - `48x48크기의 figure태그`로 모양을 잡아놓고
      - `img태그 src="/uploads폴더/(폴더명+파일명대기) + {{user.avatar}}"`로 주고
    - 없으면 `-` 로 준다.
  - **is_super_user 여부칼럼**에 대해서는
    - True면, `span.icon태그`
      - `i.mid.mdi-check` **체크 i태그**
    - False면, `span.icon태그`
      - `i.mid.mdi--close` **엑스표 i태그**
  - 마찬가지로 is_staff여부에 대해서도 span>i태그를 활용해 아이콘으로 나타낸다



##### front - 30_user_extend_index_after_user_route_and_static_uploads.html

```html
{% extends 'admin/index.html' %}

{% block member %}
<!-- 위쪽 제목 공간 -->
<div class="is-block">
    <!-- left 제목 -->
    <div class="is-pulled-left">
        <h1 class="is-size-4">
            <span class="icon"><i class="mdi mdi-receipt-outline"></i></span>
            User 관리
        </h1>
    </div>
    <!-- right 버튼(상속할 form에선 달라짐) -> block개설 -->
    {% block button %}
    <div class="is-pulled-right">
        <!--  route) user_add route 및 user_form.html 개발 후 href채우기  -->
        <a href="" class="button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>User 추가</span>
        </a>
    </div>
    {% endblock button %}
    <!--  분류선 by div2개: pulled-쓰과서 is-clearfix는 필수  -->
    <div class="is-clearfix"></div>
    <div class="dropdown-divider"></div>

    <!-- 아래쪽 table의 처리에 대한 flash 메세지를 위쪽에서   -->
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

    <!-- my) form validation errors -->
    {% for field in errors %}
    <b-message type="is-danger">
        <ul class="errors">
            {% for message in field.messages %}
            <li> {{ message }}</li>
            {% endfor %}
        </ul>
    </b-message>
    {% endfor %}
</div>

<!-- 위쪽 아래쪽 table or form 공간 -->
{% block table_content %}
<div class="table-container">
    <table class="table is-fullwidth is-hoverable is-striped">
        <thead>
        <tr>
            <th>ID</th>
            <th>Avatar</th>
            <th>Username</th>
            <th>Active</th>
            <th>SuperUser</th>
            <th>Staff</th>
            <th>생성일</th>
            <th>작업</th>
        </tr>
        </thead>
        <tbody>
        <!--  route) 에서 post객체들을 id역순으로 넘겨주면, for문이 돌아가면서 a태그 에러가 걸리게 됨.  -->
        <!--  a태그-href들 주석처리된 상태  -->
        {% for user in user_list %}
        <tr>
        <tr>
            <td>{{ user.id }}</td>
            <td>
                {% if user.avatar %}
                <figure class="image is-48x48">
<!--                         src="/uploads/{{user.avatar}}"-->
                    <img class="is-rounded" style="height: 100%;"
                         src="{{url_for('download_file', filename=user.avatar) }}"
                         alt="{{ user.username }}">
                </figure>
                {% else %}
                -
                {% endif %}
            </td>
            <td>{{ user.username }}</td>
            <td>
                {% if user.is_active %}
                <span class="icon has-text-success-dark">
                            <i class="mdi mdi-check"></i>
                        </span>
                {% else %}
                <span class="icon has-text-danger-dark">
                            <i class="mdi mdi-close"></i>
                        </span>
                {% endif %}
            </td>
            <td>
                {% if user.is_super_user %}
                <span class="icon has-text-success-dark">
                            <i class="mdi mdi-check"></i>
                </span>
                {% else %}
                <span class="icon has-text-danger-dark">
                            <i class="mdi mdi-close"></i>
                </span>
                {% endif %}
            </td>
            <td>
                {% if user.is_staff %}
                <span class="icon has-text-danger-dark">
                            <i class="mdi mdi-lock-outline"></i>
                        </span>
                {% else %}
                <span class="icon has-text-success-dark">
                            <i class="mdi mdi-lock-open-variant-outline"></i>
                        </span>
                {% endif %}
            </td>
            <td>{{ user.add_date }}</td>

            <td>
                <div class="tags">
                    <!--                    <a href="xx url_for('admin.user_edit', id=user.id) xx" class="user is-success is-light">-->
                    <a href="" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
                    <!--                    <a href="xx url_for('admin.user_delete', id=user.id) xx" class="user is-danger is-light">-->
                    <a href="" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
                </div>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
<!-- route) 에서 user_list외에 [pagination]객체도 던져줘야한다-->
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.user') }}?page={{ pagination.prev_num }}" class="pagination-previous"
       title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('admin.user') }}?page={{ pagination.next_num }}" class="pagination-next">Next page</a>
    {% endif %}

    <ul class="pagination-list">
        {% for page in pagination.iter_pages() %}
        {% if page %}
        {% if page != pagination.page %}
        <li>
            <a href="{{ url_for('admin.user') }}?page={{ page }}" class="pagination-link" aria-label="Page 1"
               aria-current="page">{{ page }}</a>
        </li>
        {% else %}
        <li>
            <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">{{ page }}</a>
        </li>
        {% endif %}
        {% else %}
        <span class=pagination-ellipsis>&hellip;</span>
        {% endif %}
        {% endfor %}

    </ul>
</nav>

{% endblock table_content %}
{% endblock member %}
```



![image-20221121173343917](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121173343917.png)

##### admin/ index.html에 user 메뉴 걸기

##### front - 31_index_change_after_user.html

```html
<p class="menu-label">
    User
</p>
<ul class="menu-list">
    <li>
        <a class="{% if 'user' in request.path %}is-active{% endif %}"
           href="{{ url_for('admin.user') }}">
            User 관리
        </a>
    </li>
    <li>
        <a>비밀번호 변경</a>
    </li>
</ul>
```



#### 24 user create

##### CreateUserForm with flask_wtf.FileField

- 사용자 화면에서의  RegisterForm은 username + password만 받았음
- admin에서의 User를 생성하는 Form은 수정을 고려하여 모든 필드를 다 반영
- 또한, avatar 파일경로에 대한 File도 업로드해야한다.

- **FileField 등은 모두 flask_wtf에서 import ( not wtf)**

```python
# auth/forms.py의 registerform과는 다르게, default로 주는 혹은 admin이 주는 설정들을 다 가지고 있다.
class CreateUserForm(FlaskForm):
    username = StringField('username', validators=[
        DataRequired(message="필수 입력"),
        Length(max=32, message="최대 32글자 입력 가능！")
    ])
    password = PasswordField('password', validators=[
        # DataRequired(message="不能为空"),
        Length(max=32, message="최대 32글자 입력 가능！")
    ], description="빈칸으로 두는 경우, 수정하지 않습니다！")
    avatar = FileField("avatar", validators=[
        # FileRequired(),
        FileAllowed(['jpg', 'png', 'gif'], message="jpg/png/gif 형식만 지원합니다"),
        FileSize(max_size=2048000, message="2M 이하의 파일만 업로드 가능합니다")],
                       description="파일크기가 2M이하만 지원합니다. 또한, jpg/png/gif 형식만 지원합니다，빈칸으로 두는 경우, 수정하지 않습니다！")
    is_super_user = BooleanField("관리자여부")
    is_active = BooleanField("활동여부", default=True) # 생성시에는 데이터가 없지만 체크될 수 있게 만들어놓는다.
    is_staff = BooleanField("Ban여부")
    
        # 수정formd를 위한  생성자 재정의
    def __init__(self, user=None, *args, **kwargs):
        self.user = user

        if self.user:
            # 따로 변형된 값(with 다른entity객체->.id) 등이 필요없으므로 바로 dict -> keyword로 만들어서 넣어준다.
            super().__init__(**self.user.__dict__)            
        else:
            super().__init__(*args, **kwargs)
            
    def validate_username(self, field):
        if self.user: # 수정시
            condition = and_(User.id != self.user.id, User.username == field.data)
        else: # 생성시
            condition = User.username == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 User name입니다')
```

- init에 추가





##### user_add route

- form객체와 html만 던져줌

```python
@admin_bp.route('/user/add', methods=['GET', 'POST'])
@login_required
def user_add():
    form = CreateUserForm()

    return render_template('admin/user_form.html', form=form)
```



##### user_form.html 생성

- 다른 form들과 달리 `form태그에 enctype='multipart/form-data'`가 들어간다

- 다른 form들과 달리, form.password.description을  `p.help태그`를 통해 사용한다.

- **수정form에는 form.user필드를 생성자 재정의로 None이 아닌 체로 들어있기 때문에, 그것을 이용해서 `수정form(form.user객체 존재) &  avatar존재시 ` img를 띄운다.**

- 폼의 여부 BooleanField들은 `label.checkbox태그`로 만들고, 내부에 form.field를 넣어서 알아서`input[type='checkbox'`가 구현되게 한다..
  - 필수 택1인 RadioField -> type='radio'와 달리
  - BooleanField -> type='checkbox'는 알아서 값이 있으면 체크된다.



##### front - 32_user_form_extends_user_after_user_add_route.html

```html
{% extends 'admin/user.html' %}

{% block button %}{% endblock button %}


{% block table_content %}
<!-- file을 포함하는 form: enctype="multipart/form-data" -->
<form action="" method="post" class="mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}
    <div class="field">
        {{ form.username.label(class='label') }}
        <div class="control">
            <!-- edit일 경우, form-->
            {{ form.username(class='input', placeholder='username') }}
        </div>
    </div>
    <div class="field">
        {{ form.password.label(class='label') }}
        <div class="control">
            {{ form.password(class='input', placeholder='password') }}
            <!-- description도 추가 -->
            <p class="help has-text-grey-light">
                {{ form.password.description }}
            </p>
        </div>
    </div>
    <div class="field">
        {{ form.avatar.label(class='label') }}
        <!-- 수정form일 경우, form.user 필드를 채워놨을 것이다.(원본에는 user=user객체를 수정route에서 따로 넘김) -->
        <!-- xx if user xx-->
        <!-- 수정form일 경우, img를 띄운다. -->
        {% if form.user %}
        <!-- /uploads/{{ form.user.avatar }}-->
        <figure class="image is-96x96">
            <img class="is-rounded" style="height:100%;"
                 src="{{url_for('download_file', filename=form.user.avatar)}}"
                 alt="{{ form.user.username }}">
        </figure>
        {% endif %}
        <div class="control">
            {{ form.avatar(class='input', placeholder='avatar') }}
            <!-- description도 추가 -->
            <p class="help has-text-grey-light">
                {{ form.avatar.description }}
            </p>
        </div>
    </div>

    <div class="field">
        <label class="checkbox">
            <!-- checked를 만들려면 직접 input태그 작성?? radio는 필수 택1이라서, input구현후 .checked로 확인하여 checked속성을 넣지만 -->
            <!-- booleanField-> checkbox는 알아서 값이 있으면 {{form.field}} 구현만으로 채워진다.?!-->
            {{ form.is_super_user }}
            {{ form.is_super_user.label }}
        </label>
    </div>
    <div class="field">
        <label class="checkbox">
            {{ form.is_active }}
            {{ form.is_active.label }}
        </label>
    </div>
    <div class="field">
        <label class="checkbox">
            {{ form.is_staff }}
            {{ form.is_staff.label }}
        </label>
    </div>
    <div class="is-block">
        <div class="box has-background-light is-shadowless level">
            <a href="" class=" is-danger button level-left">다시입력</a>
            <div class="level-right">
                <a href="{{ url_for('admin.user') }}" class="button is-primary is-light mr-2">뒤로가기</a>
                <input type="submit" value="완료" class=" button is-success">
            </div>
        </div>
    </div>
</form>
{% endblock table_content %}
```

![image-20221122013612884](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122013612884.png)



##### front - 33_user_change_after_user_form.html

```html
    {% block button %}
    <div class="is-pulled-right">
        <!--  route) user_add route 및 user_form.html 개발 후 href채우기  -->
        <a href="{{url_for('admin.user_add')}}" class="button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>User 추가</span>
        </a>
    </div>
    {% endblock button %}
```





##### user_add route POST상황 채우기

- avatar로 넘어오는 파일의 경로를 따로 먼저 처리해야한다.

![image-20221122014603170](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122014603170.png)



#### 25 file저장관련 utils > upload_util.py

- main > utils 패키지> upload_util.py를 만들고 init에 올린다.

  ![image-20221122024622375](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122024622375.png)

  ```python
  import os
  import uuid
  from werkzeug.utils import secure_filename
  
  from src.config import project_config
  
  
  def _file_path(directory_name):
      # UPLOAD_FOLDER = "/uploads/"
      file_path = project_config.UPLOAD_FOLDER / f'{directory_name}'
      if not os.path.exists(file_path):
          os.makedirs(file_path)
      return file_path
  
  
  def update_filename(f):
      # 3-1) filename에 실행파일 등이 존재할 수 있으므로, secure_filename메서드를 이용해 한번 필터링 받는다
      filename = secure_filename(f.filename)
      print(f"filename>>> {secure_filename(f.filename)}")
      # 3-2) filename을 os.path.split  ext()를 이용하여, 경로 vs 확장자만 분리한 뒤, ex> (name, .jpg)
      #      list()로 변환한다.
      _, ext = os.path.splitext(filename)
      print(f"name, ext>>> {_, ext}")
      # 3-3) name부분만 uuid.uuid4()로 덮어쓴 뒤, 변환된 filename을 반환한다
      # https://dpdpwl.tistory.com/77
      # -> uuid로 생성된 랜덤에는 하이픈이 개입되어있는데 split으로 제거한 뒤 합친다. -> replace로 처리하자
      filename = str(uuid.uuid4()).replace('-', '') + ext
      print(f"uuid + ext>>> {filename}")
      return filename
  
  
  # 1) 개별 directory 직접입력 + form.필드.data으로부터 file객체 자체가 입력된다.
  def upload_file_path(directory_name, file):
      # 2) 개별 directory 이름 -> uploads폴더와 연결한 뒤, 디렉토리가 없으면 생성하고, 경로를 반환받는다.
      file_path = _file_path(directory_name)
      # 3) file(file객체)를 입력받아, db저장용 filename으로 변경한다.
      filename = update_filename(file)
      # 4) file_paht + filename  및  단독 filename 2개를 tuple로 return한다.
      #  file save용 전체경로(개별폴더경로까지) + 변경filename ,   변경filename만
      return file_path / filename, filename
  
  ```



```
filename>>> 8.png
name, ext>>> ('8', '.png')
uuid + ext>>> a45bac96baf34e6b9b9f08df26979bbe.png
avatar_path, filename >>> (WindowsPath('C:/Users/is2js/pythonProject/2022_sqlalchemy/uploads/avatar/a45bac96baf34e6b9b9
f08df26979bbe.png'), 'a45bac96baf34e6b9b9f08df26979bbe.png')

```

![image-20221122030817429](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122030817429.png)

##### 다시 user_add route 채우기

- 원본과 다르게 **파일업로드X -> form.avatar.data에 file객체X -> None에러 방지를 위해, User객체 다 채우고 난 뒤, `setter형식으로 f가 존재하면 저장하고 넣어주기` 방식을 채택함**

```python
@admin_bp.route('/user/add', methods=['GET', 'POST'])
@login_required
def user_add():
    form = CreateUserForm()

    if form.validate_on_submit():

        # print("boolean은 체크되면 뭐로 넘어오나", form.is_super_user.data)
        #-> BooleanField는 value는 'y'로 차있지만, check되면 True로 넘어온다
        user = User(
            username=form.username.data,
            # 3) password는 hash로 만들어서 넣어야한다.
            password=generate_password_hash(form.password.data),
            # 4) db에 저장한 update된 '개별폴더/filename'으로 한다.
            #  -> file이 없는 경우를 대비해서 setter형식으로 넣어주자.
            # avatar=f'avatar/{filename}',
            is_super_user=form.is_super_user.data,
            is_active=form.is_active.data,
            is_staff=form.is_staff.data,
        )

        # 1) file 업로드 관련 유틸을 import한뒤,
        #   form에서 받은 file객체f 를 통해 -> 저장full경로 + filename만 반환받는다.
        f = form.avatar.data
        if f:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            print(f"avatar_path, filename >>> {avatar_path, filename}")
            # 2) f(file객체)를 .save( 저장경로 )로 저장한다.
            f.save(avatar_path)
            user.avatar = f'avatar/{filename}'


        with DBConnectionHandler() as db:
            db.session.add(user)
            db.session.commit()
        flash(f'{form.username.data} User 생성 성공!')
        return redirect(url_for('admin.user'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)

```

![image-20221122030951391](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122030951391.png)



#### 26 user update

##### user_edit route

- 일단 form만 채워서 user_form을 채워지는지 확인한다.

```python
@admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    with DBConnectionHandler() as db:
        user = db.session.get(User, id)

    form = CreateUserForm(user)
    
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)

```

##### user.html 수정버튼에 route link 걸기

##### front - 34_user_change_after_user_edit_route.html

```html
                    <a href="{{url_for('admin.user_edit', id=user.id)}}" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
```

![image-20221122152711745](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122152711745.png)



#### 27 user 수정 form에만 default_avatar  적용해보기

1. 구성 static파일이므로 statc > img > admin >에 `default_avatar.svg`을 준비한다.

   ![image-20221122153629959](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122153629959.png)

2. **user_form.html에서**

   1. form안에 user객체가 들어가 잇는 수정form일 경우
      - figure+ img태그가 나오는데
        1. **form.user.avatar**를 이미 가지는 유저는 `{{url_for('download_file', filename=form.user.avatar)}}`
        2. **else로 없는 경우는 `url('static', filename='/img/user/default_avatar.svg'`를 img태그의 src로**

   ```html
   {% if form.user %}
   <figure class="image is-96x96">
       <img class="is-rounded" style="height:100%;"
            src="
                 {% if form.user.avatar %}
                 {{url_for('download_file', filename=form.user.avatar)}}
                 {% else %}
                 {{url_for('static', filename='/img/user/default_avatar.svg')}}
                 {% endif %}
                 "
            alt="{{ form.user.username }}">
   </figure>
   {% endif %}
   ```

   

##### front - 35_user_form_change_after_default_avatar.html

```html
{% if form.user %}
<figure class="image is-96x96">
    <img class="is-rounded" style="height:100%;"
         src="
              {% if form.user.avatar %}
              {{url_for('download_file', filename=form.user.avatar)}}
              {% else %}
              {{url_for('static', filename='/img/user/default_avatar.svg')}}
              {% endif %}
              "
         alt="{{ form.user.username }}">
</figure>
{% endif %}
```



#### 28 수정form에선 username은 변경 못하도록 username.render_kw에 dict()로 속성 추가

```python
    # 수정formd를 위한  생성자 재정의
    def __init__(self, user=None, *args, **kwargs):
        self.user = user

        if self.user:
            # 따로 변형된 값(with 다른entity객체->.id) 등이 필요없으므로 바로 dict -> keyword로 만들어서 넣어준다.
            super().__init__(**self.user.__dict__)
            # 추가) 수정일땐, username변경 못하게 disabled 속성 주기
            self.username.render_kw = dict(disabled=True)

            # passwordfield는 내부 InputWidget의 hidden_value=True로 어차피 못채운다.
            # 이 문장을 추가하지 않으면 사용자는 암호를 변경한 후 암호가 틀렸다는 메시지를 표시한 후 로그인할 수 없습니다.
            self.password.default = f'{user.password}'
```

![image-20221122164911074](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122164911074.png)



#### 29 다시 user update 

##### user_edit route 받은데이터 처리하기

```python
@admin_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    with DBConnectionHandler() as db:
        user = db.session.get(User, id)

    form = CreateUserForm(user)

    if form.validate_on_submit():
        # username은 수정못하게 걸어놧으니 pasword부터 처리한다.
        # password는 데이터가 들어온 경우만 -> hash걸어서 저장한다.
        # print(f"form.password.data>>>{form.password.data}")
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        # avatar의 경우, 현재 db필드인 'avatar/파일명'이 data로 들어가있지만,
        # -> 파일명(기존 user.avatar값과 동일)이 아닌 file객체가data로 온 경우만, 새롭게 upload하는 처리를 해준다.
        f = form.avatar.data
        # print(f"f>>>{f}")
        if f != user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)
            user.avatar = f'avatar/{filename}'
        # 나머지 필드도 변경
        user.is_super_user = form.is_super_user.data
        user.is_active = form.is_active.data
        user.is_staff = form.is_staff.data

        with DBConnectionHandler() as db:
            db.session.add(user)
            db.session.commit()

        flash(f'{form.username.data} User 수정 완료.')
        return redirect(url_for('admin.user'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/user_form.html', form=form, errors=errors)

```



```python
# 비번변경x, avatar 변경X(필드에서 넣어준 값 그대로 들어온다)
form.password.data>>>
f>>>avatar/b8b46e87e6b04fbfb990b3fe758cc16f.gif

# 비번변경O, avatar 변경O(file객체가 들어온다)
form.password.data>>>123123
f>>><FileStorage: '1.png' ('image/png')>

```



#### 30 기존 파일 삭제하기

##### utils > upload_util.py에  delete_uploaded_file 메서드 정의

```python
#### 추가: db.field에    /uploads/ 이후 값을 받아 파일이 존재하면 삭제한다.
# -> 3.8부터는 Path.unlink()의 missing_ok가 가능한데, 직므 3.7이라서 os로 한다.
# https://stackoverflow.com/questions/6996603/how-do-i-delete-a-file-or-folder-in-python
def delete_uploaded_file(directory_and_filename):
    # 애초에 avatar가 없다가 추가하는 경우, directory_and_filename = user.avatar에는 
    # -> None으로 경로가 들어온다 미리  예외처리하여 종료
    if not directory_and_filename:
        return
    # project_config.UPLOAD_FOLDER == '~/uploads/'까지의 경로
    file_path = project_config.UPLOAD_FOLDER / directory_and_filename
    # file_paht == '~/uploads/' + 'avatar/uuid4.파일명'
    if os.path.isfile(file_path):
        os.remove(file_path)
    # Path(file_path).unlink(missing_ok=True) # python3.8부터

    print("삭제된 파일>>>", file_path)

```

#####  route에서 user.avatar 필드 덮어쓰여지기 전에, 활용해서 삭제하기

```python
if f != user.avatar:
    avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
    f.save(avatar_path)

    # user.avatar 덮어쓰기 전에, db에 저장된 경로를 바탕으로 -> upload폴더에서 기존 file삭제
    # -> 기존 user.avatar에 암것도 없어도 안에서 바로 종료되도록 예외처리
    delete_uploaded_file(directory_and_filename=user.avatar)

    user.avatar = f'avatar/{filename}'
```



#### 31 user delete

##### user_delete route

- **file경로를가진 필드는 해당경로 file까지 같이 삭제해야한다.**

```python
@admin_bp.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def user_delete(id):
    with DBConnectionHandler() as db:
        user = db.session.get(User, id)

        if user:
            # 필드에 file을 가지고 있는 entity는 file도 같이 삭제한다.
            delete_uploaded_file(directory_and_filename=user.avatar)
            db.session.delete(user)
            db.session.commit()
            flash(f'{user.username} User 삭제 완료.')
            return redirect(url_for('admin.user'))
```



##### front - 36_user_change_after_user_delete_route.html

```html
              <a href="{{url_for('admin.user_delete', id=user.id)}}" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
```

![image-20221122181842975](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122181842975.png)





### base menu

#### 1 base에서 menu만들기

##### @app.context_processor 예시

- **해당메서드는 dict를 return해야한다**

  ```python
  @app.context_processor
  def inject_user():
      return dict(user=g.user)
  ```

- **내부에 메서드를 정의하여, 함수객체를 dict의 value로 넣어주면, template에서 method로 사용할 수 있다.**

  ```python
  @app.context_processor
  def utility_processor():
      def format_price(amount, currency="€"):
          return f"{amount:.2f}{currency}"
      
      return dict(format_price=format_price)
  ```

  ```python
  {{ format_price(0.33) }}
  ```

- 주로 전체 template에 사용될 nav용 menu가 사용된다.

  - 매번 template에 menu=menu를 전달하지 않고, 전체 template이 자연스럽게 사용가능하므로 **base.html에 사용하고, 다른 것들이 모두 상속해서 쓰면 된다.**

  ```python
  # make this object globally available in template context
  @app.context_processor
  def process_template_context():
      return dict(app_menu=app_menu)
  ```

  ```html
  <!-- render menu in template -->
  {% for item in app_menu.children recursive %}
      <li {% if item.is_active() or item.has_active_child() %} class="active"{% endif %}>
          {% if item.children %}
  ```

  



##### base.html 사용을 통해  모든 template context에 사용되는 menu객체인 category객체를 app에 반영하기

- src> main> config > app.py
  - category객체를 일부만 추출하여 dict()에 싸서 반환하고
  - **app에는 context_process로서 dict반환 함수객체만 넘겨 등록한다**

```python
# template context에서 전역사용할 menu객체를 dict로 반환하여 등록
def inject_category():
    with DBConnectionHandler() as db:
        stmt = (
            select(Category)
            .order_by(Category.id.asc())
            .limit(6)
        )

        categories = db.session.scalars(stmt).all()
    return dict(categories=categories)


app.context_processor(inject_category)

```





##### base.html에서 첫번째 b-navbar-item만 home으로서 남기고, 나머지는 categories를 돌려서 채운다.

```html
<template #start>
    <!-- home 메뉴만 수동으로 href='/' 유지-->
    <b-navbar-item href="/">
        Home
    </b-navbar-item>
    <!-- home 제외 메뉴는 전역 categories로 구성-->
    {% for category in categories %}
    <b-navbar-item href="#">
        {{category.name }}
    </b-navbar-item>
    {% endfor %}
</template>
```

![image-20221122224343801](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122224343801.png)

![image-20221122224420648](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221122224420648.png)






### main index





#### 2  base에서 post뿌려주기

##### main.index route

- main관련은 routes> `main_routes.py`에 정의하고 있다.

- 기존 post 뿌려주는 것은 반복문만 돌리고 있음

  ```python
  @main_bp.route("/")
  def index():
      posts = [1, 2, 3, 4, 5, 6]
      return render_template('main/index.html', posts=posts)
  
  ```

  

- **admin(dashboard)에서는 id역순 or 생성일 역순으로 받았지만, main에 뿌려질 것들은 생성일 역순으로 고정해서 뿌려준다**
  - 아직 pagination은 html에 없지만, 일단 같이 넘겨준다
  - **main에 최대로 보여질 갯수를 확인해서, per_page=9로 정해주었다.**
  - post_list에는 최대 9개만 들어가있는 상태다.

```python
@main_bp.route("/")
def index():
    # posts = [1, 2, 3, 4, 5, 6]
    page = request.args.get('page', 1, type=int)

    stmt = select(Post).order_by(Post.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=9)

    post_list = pagination.items

    return render_template('main/index.html', post_list=post_list, pagination=pagination)

```



- base.html에서 in posts -> post_list로 수정

  - 시작코드도 수정할 듯

  ```html
  {% for post in post_list %}
  ```

  ![image-20221123002025127](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123002025127.png)



##### base.html post객체내용으로 채우도록 수정

- time 태그에는 datetime ="" 속성과 text모두 채우기

  ![image-20221123002408738](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123002408738.png)

- **내용을 가득차게 수정해보고 확인하기**

  ![image-20221123002553146](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123002553146.png)



- 깨지는 것을 보고 그냥 `truncate( 글자수 )` 필터를 적용함

  ```jinja2
  {{ post.desc | truncate(30)}}
  ```

  ![image-20221123003857924](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123003857924.png)



#####  front - 37_base_change_after_index_route.html

```html
{% for post in post_list %}
<div class="column is-4-fullhd">
    <div class="card">
        <div class="card-image">
            <figure class="image is-4by3">
                <img src="https://bulma.io/images/placeholders/1280x960.png"
                     alt="Placeholder image">
            </figure>
        </div>
        <div class="card-content">
            <div class="media">
                <div class="media-content">
                    <p class="title is-4"><a href="">{{ post.title }}</a></p>
                </div>
            </div>

            <div class="content">
                <p class="has-text-grey is-size-7">
                    {{ post.desc | truncate(30)}}
                </p>
                <time datetime="{{ post.add_date }}">{{ post.add_date }}</time>
            </div>
        </div>
    </div>
</div>
{% endfor %}
```





#### 3 base의 post img

##### entity에는 img필드가 없게 설정됨. static에 있는 img를 마련해놓고, random으로 per_page만큼 뽑아서 동적으로 post.img필드를 만들어 박아준다

- img필드를 박으려면(avatar처럼)
  - entity에 img_url필드 생성
  - form에 filefield 생성
  - route에서 form에서 받은 파일객체를 이용해 .save(), blog/파일명으로 필드에 저장
  - 나중에 content에 markdown으로 포함될 이미지 1개를 추출한다고 가정하고, 미리 준비된 img로 처리해보자.



1. static폴더안에 개별폴더 `post`를 만들고, post이미지를 9장 이상 준비한다.

   - [이미지출저](https://github.com/lovebull/Pampa/tree/64445f3990006753b72a25009e98e5386ace4ad7/app/blog/static/images/post)

     ![image-20221123013133310](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123013133310.png)

2. **route에서는 가진 img수만큼 img_path_list를 만들어낸 뒤**

   - 그 경로는 static 기본에 filename=으로 `img/post/post-1.jpg`형식으로 만들어낸다.
   - **현재 pagination으로 가지는 .items의 갯수만큼만 비복원으로 추출해서, `post.img`필드를 동적으로 생성하여 할당해준다.**

   ```python
   @main_bp.route("/")
   def index():
       # post_list = [1, 2, 3, 4, 5, 6]
       page = request.args.get('page', 1, type=int)
   
       stmt = select(Post).order_by(Post.add_date.desc())
       pagination = paginate(stmt, page=page, per_page=9)
   
       post_list = pagination.items
   
   	img_path_list = [f'img/post/post-{i}.jpg' for i in range(1, 15 + 1)]
       for post, img_path in zip(post_list, random.sample(img_path_list, k=len(post_list))):
           post.img = img_path
   
       return render_template('main/index.html', post_list=post_list, pagination=pagination)
   ```

   









![image-20221123021835364](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123021835364.png)

![image-20221123021842517](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123021842517.png)

##### pagination 적용

- nav태그로 적용하는 pagination은 다 똑같으니 복사해서 url_for만 잘 바꿔준다.

  - **add_rule에서 `'/'`외에 enpoint='index'옵션은 url_for에서 사용할 새로운 view_func이다**

    ![image-20221123025206629](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025206629.png)

    - url에 `/index`를 치면 안나온다.

      ![image-20221123025017910](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025017910.png)

    - url에는 `/`만 쳐야한다.

      ![image-20221123025042034](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025042034.png)

    - `url_for`에는 원래는 `'main.index'`를 써야하지만, add_rule에 의해 `'index'`를 쓸 수 있게 된다.

      ![image-20221123025150648](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025150648.png)

    - url_for에 `'main.index'`를 써도 되지만, url에는 url_prefix로 인해 /main/이 붙게 된다.

      ![image-20221123025526091](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025526091.png)

      ![image-20221123025338562](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025338562.png)

      ![image-20221123025346644](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123025346644.png)



##### front - 38_base_change_after_main.index_complete.html

```html
 {% for post in post_list %}
                    <div class="column is-4-fullhd">
                        <div class="card">
                            <div class="card-image">
                                <figure class="image is-4by3">
                                    <!--                                    <img src="https://bulma.io/images/placeholders/1280x960.png"-->
                                    <img src="{{url_for('static', filename=post.img )}}"
                                         loading="prelaod" decoding="async"
                                         alt="Placeholder image">
                                </figure>
                            </div>
                            <div class="card-content">
                                <div class="media">
                                    <div class="media-content">
                                        <p class="title is-4"><a href="">{{ post.title }}</a></p>
                                    </div>
                                </div>

                                <div class="content">
                                    <p class="has-text-grey is-size-7">
                                        {{ post.desc | truncate(30)}}
                                    </p>
                                    <time datetime="{{ post.add_date }}">{{ post.add_date }}</time>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>






                 <nav class="pagination is-small" role="navigation" aria-label="pagination">
                    {% if pagination.has_prev %}
                    <a href="{{ url_for('main.index') }}?page={{ pagination.prev_num }}" class="pagination-previous"
                       title="This is the first page">Previous</a>
                    {% endif %}
                    {% if pagination.has_next %}
                    <a href="{{ url_for('index') }}?page={{ pagination.next_num }}" class="pagination-next">Next
                        page</a>
                    {% endif %}

                    <ul class="pagination-list">
                        {% for page in pagination.iter_pages() %}
                        {% if page %}
                        {% if page != pagination.page %}
                        <li>
                            <a href="{{ url_for('index') }}?page={{ page }}" class="pagination-link"
                               aria-label="Page 1"
                               aria-current="page">{{ page }}</a>
                        </li>
                        {% else %}
                        <li>
                            <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">{{ page }}</a>
                        </li>
                        {% endif %}
                        {% else %}
                        <span class=pagination-ellipsis>&hellip;</span>
                        {% endif %}
                        {% endfor %}

                    </ul>
                </nav>
```



