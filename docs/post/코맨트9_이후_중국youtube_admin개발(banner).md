### banner



#### Banner model in entity/admin

- **일반적으로 사용하는 모델이 아니라 admin에서만 업로드할 것이므로 `admin패키지`를 따로 파서 만든다**

  ![image-20221126031306277](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126031306277.png)



- Type class는 `enum.IntEnum`이고 칼럼은 `entity에 정의해놓은 IntEnum`클래스이므로 **기본enum을 `Enum대신 enumIntEnum`으로 쓰자**

  ```python
  import enum
  
  from sqlalchemy import Column, Integer, String
  from src.infra.tutorial3.common.base import BaseModel
  from src.infra.tutorial3.common.int_enum import IntEnum
  
  
  class BannerType(enum.IntEnum):
      """defining Banner Types: 0 main용, 1 modal용"""
      MAIN = 0
      MODAL = 1
  
      # type은 form에서 radio필드의 choices를 지정해줄때, enum.IntEnum의 (.value, .name)을 넘겨줄 수 있도록 메서드를 정의한다.
      # -> 폼에 넘겨준 튜플리스트는 jinja에서 (subfield.data, subfield.label)올 쓰인다.
      @classmethod
      def choices(cls):
          return [(choice.value, choice.name) for choice in cls]
  
  class Banner(BaseModel):
      __tablename__ = 'banners'
  
      id = Column(Integer, primary_key=True)
      # 1) 아바타와 달리 반드시 있어야한다. avatar = Column(String(200), nullable=True)
      img = Column(String(200), nullable=False)
      desc = Column(String(200), nullable=True)
      url = Column(String(300), nullable=True)
      # 2) 원본외 추가칼럼
      banner_type = Column(IntEnum(BannerType), default=BannerType.MAIN, nullable=False)
      # 3) main고정 여부 추가칼럼
      is_fixed = Column(Boolean, default=False, nullable=False)
  
      #### 예비 칼럼들
      # title/subtitle
      # is_sticky = Column(Boolean(), nullable=False)  # 항상 띄워두어야할 필수 공지냐
      # exp_start_date = Column(DateTime, index=True, default=datetime.datetime.now)
      # exp_end_date = Column(DateTime)
  
      def __repr__(self) -> str:
          info: str = f"{self.__class__.__name__}" \
                      f"[{self.id} => {self.img}]"
          return info
  ```

  

##### 모델추가시 main.py 옵션끄고 실행



- **새로운 모델 추가시마다**

  - entity패키지의 init에 추가하면 된다. 

    - db생성모듈(create_databse은 from entity import *)

    - db생성 실행모듈(main.py -> from create_databse import *)

    - admin/init

      ```python
      from .banners import Banner, BannerType
      ```

    - entity/init

      ```python
      from .comments import Comment
      from .menus import Menu
      from .notices import Notice, BannerType
      from .categories import Category, Post, PostPublishType, posttags, Tag
      from .auth import User
      from .admin import Banner, BannerType
      ```

      

- **flask db migrate는 생략한다**

- **나의 main.py를 실행시켜 없는 db는 생성되게 한다**

  - 옵션을 다 False로 놓고 실행시키면 없는 것만 생성
  - main.py

  ```python
  from create_database_tutorial3 import *
  
  if __name__ == '__main__':
      session = Session()
      create_database(truncate=False, drop_table=False, load_fake_data=False)
  
  ```

  ![image-20221126032046065](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126032046065.png)





##### 상단노출기능을 main is_fixed로

- [참고 링크](https://pybo.kr/pybo/question/detail/904/)

```python
다음은 pybo.kr의 Question 테이블입니다.

class Question(models.Model):
    class Meta:
        ordering = ['id']

    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='author_question')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True, blank=True)
    modify_date = models.DateTimeField(null=True, blank=True)
    voter = models.ManyToManyField(CustomUser, related_name='voter_question', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_question')
    view_count = models.IntegerField(null=True, blank=True, default=0)
    notice = models.BooleanField(default=False)  # 공지사항 여부

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse('pybo:question_detail', args=[self.id])

    def get_recent_comments(self):
        return self.comment_set.all().order_by('-create_date')[:5]
그리고 공지사항 정렬은 다음과 같이 합니다.

_question_list = _question_list.order_by('-notice', '-create_date')
```



#### Banner select

##### banner  route

```python
@admin_bp.route('/banner')
@login_required
def banner():
    page = request.args.get('page', 1, type=int)

    stmt = select(Banner).order_by(Banner.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    banner_list = pagination.items

    return render_template('admin/banner.html',
                           banner_list=banner_list, pagination=pagination)
```

###### **is_fixed로 상단고정여부필드를 도입한 순간부터는 order_by에 `고정여부필드.desc()를 우선`으로 정렬해서 먼저 나오게 한다**

![image-20221127004940103](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127004940103.png)

```python
@admin_bp.route('/banner')
@login_required
def banner():
    page = request.args.get('page', 1, type=int)

    stmt = select(Banner).order_by(Banner.is_fixed.desc(), Banner.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    banner_list = pagination.items

    return render_template('admin/banner.html',
                           banner_list=banner_list, pagination=pagination)
```







##### admin / banner.html

##### front - 58_banner_extends_admin_index_after_banner_route.html

```html
{% extends 'admin/index.html' %}

{% block member %}
<div class="is-block">
    <div class=" is-pulled-left">
        <h1 class=" is-size-4">
            <span class="icon">
                <i class="mdi mdi-image-multiple"></i>
            </span>
            Banner 관리
        </h1>
    </div>

    {% block button %}
    <div class=" is-pulled-right">
        <!--        <a href="xx url_for('admin.banner_add') yy" class=" button is-primary is-light">-->
        <a href="" class=" button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>Add Banner</span>
        </a>
    </div>
    {% endblock button %}
    <div class="is-clearfix"></div>
    <div class=" dropdown-divider"></div>

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
</div>

{% block table_content %}
<div class="table-container">
    <table class="table is-fullwidth is-hoverable is-striped">
        <thead>
        <tr>
            <th>ID</th>
            <th>Img</th>
            <th>Url</th>
            <th>Desc</th>
            <th>Type</th>
            <th>고정</th>
            <th>생성일</th>
            <th>작업</th>
        </tr>
        </thead>
        <tbody>

        {% for banner in banner_list %}
        <tr>
            <td>{{ banner.id }}</td>
            <td>
                <figure class="image is-16by9">
                    <!--                        <img src="xx url_for('download_file', filename= banner.img) yy">-->
                    <img src="{{url_for('static', filename='img/placeholders/1280x960.png') }}">
                </figure>
            </td>
            <td>{{ banner.url }}</td>
            <td>{{ banner.desc }}</td>
            <td>{{ banner.banner_type.name }}</td>
			<td>
                {% if banner.is_fixed %}
                <span class="icon has-text-success-dark">
                            <i class="mdi mdi-check"></i>
                </span>
                {% else %}
                <span class="icon has-text-danger-dark">
                            <i class="mdi mdi-close"></i>
                </span>
                {% endif %}
            </td>
            <td>{{ banner.add_date }}</td>
            <td>
                <div class="tags">
                    <!--                        <a href="xx url_for('admin.banner_edit', banner_id=id) yy" class="tag is-success is-light">-->
                    <a href="" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
                    <!--                        <a href="xx url_for('admin.banner_delete', banner_id=id) yy" class="tag is-danger is-light">-->
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

<!-- table_content 내부에서 div.table-container끝나면  pagination선택-->
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.banner') }}?page={{ pagination.prev_num }}" class="pagination-previous"
       title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('admin.banner') }}?page={{ pagination.next_num }}" class="pagination-next">Next page</a>
    {% endif %}

    <ul class="pagination-list">
        {% for page in pagination.iter_pages() %}
        {% if page %}
        {% if page != pagination.page %}
        <li>
            <a href="{{ url_for('admin.banner') }}?page={{ page }}" class="pagination-link" aria-label="Page 1"
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



- `http://localhost:5000/admin/banner`

  ![image-20221126233137679](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126233137679.png)

##### front - 59_index_change_after_banner_select.html

- 이번엔 특이하게 span>i를 왼쪽메뉴에 추가했다.

```html
<p class="menu-label">
    <span class="icon"><i class="mdi mdi-cog-outline"></i></span>
    Banner
</p>
<ul class="menu-list">
    <li>
        <a class="{% if 'banner' in request.path %}is-active{% endif %}"
           href="{{ url_for('admin.banner') }}">
            <span class="icon"><i class="mdi mdi-image-sync-outline"></i></span>
            Banner 관리
        </a>
    </li>
</ul>
```

![image-20221126200656695](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126200656695.png)









#### Banner create

##### BannerForm

- 파일을 가지는 model은 **모델field에서는 개별폴더/파일이름이지만**

  - **form에서는 FileField**를 가진다.

- **user의 avatar와 달리, 2M가 아니 3M까지 허용한다**

  - 3:1비율을 권장한다고 일단 적시한다

- 동적으로 많은 것들 중 택1은 dropdown으로 펼쳐지는 SelectField를 쓰지만

  ![image-20221126210916393](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126210916393.png)

  - **정해진 종류 중 택1은`model IntEnum -> form RadioField`를 쓴다**

    ![image-20221126211004957](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126211004957.png)

- **type의 enum.IntEnum을 가지는 formfield는 choices를 튜플리스트로 조항들을, default에는 단일 .value만 넘겨주는 radiofield를 가진다 **

- **urlfield의 require_tld: 정규식을 이용해서 `앞에 www.같은 호스트까지 포함하는 url인지 검사여부`를 결정하는데, `False로 줘서 localhost도 허용하도록 준다`(기본True)**

  ![image-20221126214036732](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126214036732.png)

  ![image-20221126214136762](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126214136762.png)

  - [장고 참고 - 벨로그](https://velog.io/@qlgks1/Django-Model-%ED%95%84%EB%93%9Cfiled-%EB%AA%A8%EC%9D%8C%EC%A7%91)

    - CharField와 동일하나, URLValidator를 사용한다. url 패턴에 매칭이되는 Regex(정규식)이 조건으로 걸려 있다.

  - required_tld:

    - Whether to reject non-FQDN hostnames

    - FQDN은 '절대 도메인 네임' 또는 '전체 도메인 네임' 이라고도 불리는

      도메인 전체 이름을 표기하는 방식을 의미한다.

      ```
      웹 사이트 주소를 예로 들어보자.
      
       
      1. www.tistory.com  
      
      2. onlywis.tistory.com
      
      
      
      위의 두 주소 중 www 와 onlywis 부분이 '호스트'이고, tistory.com 부분이 '도메인'이다.
      
      위에 쓴 것처럼 호스트와 도메인을 함께 명시하여 전체 경로를 모두 표기하는 것을 FQDN 이라 한다.
      
       
      FQDN와 달리 전체 경로명이 아닌 하위 일부 경로만으로 식별 가능하게 하는 이름을 PQDN(Partially~)라 한다.
      
       
      쿠버네티스의 경우 다른 Pod를 찾을 시 동일 네임스페이스 안에서 찾을 때에는 PQDN을 사용할 수 있지만,
      
      네임스페이스 외부에서 찾을 때에는 FQDN을 사용해야 한다.
      ```

- **~여부Boolean필드**에 대한 form필드는 체크여부인 **Boolean필드**를 똑같이 쓴다.

###### postfrom의 type-radiofield와 createuserform의 fieldfield가 합쳐졌으며, url필드가 새로 생김



###### 생성form에서 file필수라도, 수정form재활용(not file객체, file경로가 참)을 위해서 FileRequired는 빼야한다. -> 대신 validate_img필드를 넣고, 생성시에만 field.data(None)이면, 에러내도록 해준다.

```python
class BannerForm(FlaskForm):
    img = FileField("Banner", validators=[
        ## 수정시에는 파일경로만 form에 담겨와서, 그대로가기 때문에, file이 없어도 허용해야한다.
        ## -> 만약, fileRequired 대신 validate_img로 생성시에만 필수로 해준다.
        # FileRequired(message="배너는 그림이 필수 입니다."),
        FileAllowed(['jpg', 'png', 'gif'], message="jpg/png/gif 형식만 지원합니다"),
        FileSize(max_size=3 * 1024 * 1000, message="3M 이하의 파일만 업로드 가능합니다")],
                    description="파일크기가 3M이하만 지원합니다. 또한, jpg/png/gif 형식만 지원합니다，빈칸으로 두는 경우, 수정하지 않습니다！ 비율은 3:1을 권장합니다")
    

    # type필드에 대한 form필드는 택1인 radio를 쓴다.
    banner_type = RadioField('Banner Type',
                             # enum.IntEnum의 cls메서드로 (.value, .name) list를 form필드객체에 넘겨준다
                             # -> jinja에서는 (subfield.data, subfield.label)로 쓰인다.
                             choices=BannerType.choices(),
                             # choices와 달리, defautld에는 .data가 되는 값 1개만 .value로 넘겨줘야한다.
                             default=BannerType.MAIN.value,
                             coerce=int,
                             )
	# ~여부Boolean필드에 대한 form필드는 체크여부인 Select필드를 쓴다.
    is_fixed = BooleanField("고정 여부")
    
    desc = StringField('Description', validators=[
        # DataRequired(message="필수 입력"),
        Length(max=200, message="최대 200글자 입력 가능！")
    ])

    # URL필드는 wtforms.validators의 URL(정규표현식으로 url검사)으로 검증한다
    url = URLField("Url", validators=[
        # localhost를 허용하려면 required_tld=False 필수
        URL(require_tld=False, message="정확한 url을 입력해주세요."),
        Length(max=300, message="최대 300글자 입력 가능！")])

    # 수정form을 위한 생성자 재정의
    def __init__(self, banner=None, *args, **kwargs):
        self.banner = banner
        if self.banner:
            # fk가 없으므로 바로 객체를 .__dict__로 만들고 **로 키워드풀어서 대입
            super().__init__(**self.banner.__dict__)
        else:
            super().__init__(*args, **kwargs)

	## 생성시에만, form에 file객체가 없을 때 에러를 낸다.
    # -> 수정시는, file객체대신 file경로가 form.field에 들어가서, 이미지 수정안해서 file객체 없어도 그대로 둬야한다
    def validate_img(self, field):
        if self.banner:  # 수정시
            pass
        else:  # 생성시
            if not field.data:
                raise ValidationError('Banner 생성시 이미지 업로드는 필수입니다.')
```





##### banner_add route 

###### form + fileupload가 포함된 route로서 user_add route를 참고

```python
@admin_bp.route('/banner/add', methods=['GET', 'POST'])
@login_required
def banner_add():
    form = BannerForm()

    if form.validate_on_submit():
        # 파일이 없을 수는 없지만, user처럼 이미지 없는 경우도 있을 수 있으므로 해당필드는 나중에 f가 있으면 채운다.
        banner = Banner(
            desc=form.desc.data,
            url=form.url.data,
            banner_type=form.banner_type.data,
            is_fixed=form.is_fixed.data
        )

        f = form.img.data
        if f:
            banner_path, filename = upload_file_path(directory_name='banner', file=f)
            f.save(banner_path)
            banner.img = f'banner/{filename}'

        with DBConnectionHandler() as db:
            db.session.add(banner)
            db.session.commit()

        flash(f'{form.desc.data} Banner 생성 성공!')
        return redirect(url_for('admin.banner'))

    return render_template('admin/banner_form.html', form=form)
```





##### admin / banner_form.html

![image-20221126221813391](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126221813391.png)





###### 이번에는 filefield의 Input을 b-가 붙은 Buefy의 component + vue코드를 사용한다

- [buefy문서](https://buefy.org/documentation/upload/)

- form
  - div.field
    - form.img.label
    - div.control
      - `<b-field class="file">`
        - `<b-upload v-model="file" name="img" expanded>`
          - **v-model="file"은  vue객체가 data: { file: {}}을 최소한 생성해놓은 상태에서, 그쪽으로 넘겨준다는 의미이다.**
          - `<a class="button`
            - `<b-icon icon="upload"></b-icon>`
            - `<span>{$ file.name || "{% if banner %}{{ banner.img }}{% else %}Click to upload{% endif %}" $}</span>`
              - **여기서  `{$ $}`는 vue코드**
              - **v-model인 file에게 file객체가 넘어갔으므로 {$ file $}로 쓴다.**
            - p태그(설명)





##### front-60_banner_form_extends_admin_banner_after_banner_add_route.html

```html
{% extends 'admin/banner.html' %}

{% block button %}{% endblock button %}


{% block table_content %}
<form action="" method="post" class="mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}
    <div class="field">
        {{ form.img.label(class='label') }}
        <div class="control">
            <b-field class="file">
                <b-upload v-model="file" name="img" expanded>
                    <a class="button is-primary is-fullwidth">
                        <b-icon icon="upload"></b-icon>
                        <span>{$ file.name || "{% if banner %}{{ banner.img }}{% else %}Click to upload{% endif %}" $}</span>
                    </a>
                </b-upload>
            </b-field>
            <p class="help has-text-grey-light">
                {{ form.img.description }}
            </p>
        </div>
    </div>

    <div class="field is-horizontal">
        {{ form.banner_type.label(class='label') }}
        <div class="field-body ml-4">
            <div class="control">
                <!--  radio 필드는 input필드를 직접 구현해야 생성시 default 와 edit시 현재값이 checked를 확인할 수 있다.-->
                {% for subfield in form.banner_type %}
                <input {%if subfield.checked %}checked {% endif %} type="radio"
                       id="{{ subfield.id }}" name="{{ form.banner_type.id }}" value="{{ subfield.data }}">
                {{ subfield.label }}
                {% endfor %}
            </div>
        </div>
    </div>
    
    
    <div class="field">
        <label class="checkbox">
            {{ form.is_fixed.label(style='font-weight:600') }}
            {{ form.is_fixed }}
        </label>
    </div>

    <div class="field">
        {{ form.url.label(class='label') }}
        <div class="control">
            {{ form.url(class='input', placeholder='url을 입력해주세요. ex>') }}
            <p class="help has-text-grey-light">
                {{ form.url.description }}
            </p>
        </div>
    </div>

    <div class="field">
        {{ form.desc.label(class='label') }}
        <div class="control">
            {{ form.desc(class='input', placeholder='Banner 설명을 입력해주세요.') }}

            <p class="help has-text-grey-light">
                {{ form.desc.description }}
            </p>
        </div>
    </div>

    <div class="is-block">
        <div class="box has-background-light is-shadowless level">
            <button class=" is-danger button level-left">다시 입력</button>
            <div class="level-right">
                <a href="{{ url_for('admin.banner') }}" class="button is-primary is-light mr-2">뒤로가기</a>
                <input type="submit" value="완료" class=" button is-success">
            </div>
        </div>
    </div>
</form>
{% endblock table_content %}
```



- test: `localhost:5000/admin/banner/add`![image-20221126223345841](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126223345841.png)



##### front - 61_banner_change_after_banner_add_route.html

```html
{% block button %}
<div class=" is-pulled-right">
    <a href="{{ url_for('admin.banner_add') }}" class=" button is-primary is-light">
        <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
        <span>Add Banner</span>
    </a>
</div>
{% endblock button %}
```









#### Vue코드로 bulma upload 처리하기

![image-20221127000223179](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127000223179.png)

- **vue의 문법에서 사용할 file변수가 없다고 한다. `vue객체가 data에서 file:{}`로 초기화해줘야한다**





##### base.html 상속 자식이라면, 어느페이지든지 new Vue객체를 뿌려주는 중

##### vue객체는 html에서 하는 동적인 처리를 받아줄 대기역할이다.

![image-20221126235207033](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126235207033.png)



##### b-upload태그는 vue와 jinja를 둘다 쓰는 중

###### vue객체는 data초기화 변수 -> v-model을 통해 특정 html 동적 데이터를 변수에 받아준 뒤, 자신의 delimiters사용하여 받은 데이터를 사용하게 해준다.

- **수정form인 경우 form의 self.banner로 해당객체정보를 받아놓기 때문에, form.banner의 유무로 수정폼인지 확인한다.**

```html
<b-upload v-model="file" name="img" expanded>
    <a class="button is-primary is-fullwidth">
        <b-icon icon="upload"></b-icon>
        <span>{$ file.name || "{% if form.banner %}{{ form.banner.img }}{% else %}Click to upload{% endif %}" $}</span>
    </a>
</b-upload>
```

- **v-model(data:file:{})**에서 갖다쓰는 **file**의 **.name**이 있으면(b-upload에 업로드 된 상태) 해당 파일네임을

  - [vue logical operate](https://stackoverflow.com/questions/54076874/vue-js-how-to-use-the-logical-operators-in-a-template)

    ```
    
    
    You could use them in the same v-if directive e.g.
    
    && = Logical Operator AND
    
    || = Logical Operator OR
    
    && means both conditions have to be true for the div to show.
    
    <div class="o-overlay" v-if="show && visible">
        <div class="o-overlay__bg" @click="hide"></div>
    </div>
    || means only one of the conditions have to be true for the div to show.
    
    <div class="o-overlay" v-if="show || visible">
        <div class="o-overlay__bg" @click="hide"></div>
    </div>
    ```

    

- **vue or인 `||`에 의해** file.name이 없으면, or의 default값 개념으로서

  - if **수정form이라서** **banner객체가 함께** 제대로 넘어왔다면, banner.img로 경로를
  - **banner가 안넘어온 생성form**이라면 Click to upload를 표시한다.



##### 어떤페이지든 존재하는 base.html의 Vue객체에서 자식사용변수 초기화해주기

- 기존 body끝에 걸린 vue script

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
  {% block vue_script %}{% endblock vue_script %}
  </body>
  ```

  

###### delimiters를 직접 정의해주기

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],
        data: {},
        methods: {}
    })
</script>
```



- **`dilimeter만 정의해준 상태에서 file변수가 없다면`아예 검은화면이 되어버린다**

  ![image-20221127000511494](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127000511494.png)

- **그래서 delimiter를 미리 안정해줬구나.**



###### data에는, 상속 자식들이 사용하는 vue 변수라면,  일단 base에서 빈값{}으로 초기화해주기

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
        },
        methods: {}
    })
</script>
```

![image-20221127000641339](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127000641339.png)

![image-20221127000729857](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127000729857.png)

![image-20221127002510125](../../../Users/is2js/AppData/Roaming/Typora/typora-user-images/image-20221127002510125.png)





##### front - 62_base_change_after_banner_form.html

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
        },
        methods: {}
    })
</script>
```



##### front - 63_banner_change_after_base_vue_bupload.html

```html
<td>{{ banner.id }}</td>
<td>
    <figure class="image is-16by9">
        <img src="{{url_for('download_file', filename= banner.img) }}">
    </figure>
</td>
```

![image-20221127002045380](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127002045380.png)





#### banner update

##### banner_edit route

```python
@admin_bp.route('/banner/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def banner_edit(id):
    with DBConnectionHandler() as db:
        banner = db.session.get(Banner, id)

    form = BannerForm(banner)

    if form.validate_on_submit():
        f = form.img.data
        # 수정안되서 경로 그대로 오는지 vs 새 파일객체가 오는지 구분
        if f != banner.img:
            banner_path, filename = upload_file_path(directory_name='banner', file=f)
            f.save(banner_path)

            delete_uploaded_file(directory_and_filename=banner.img)

            banner.img = f'banner/{filename}'

        # 나머지 필드도 변경
        banner.banner_type = form.banner_type.data
        banner.is_fixed = form.is_fixed.data
        banner.desc = form.desc.data
        banner.url = form.url.data

        with DBConnectionHandler() as db:
            db.session.add(banner)
            db.session.commit()

        flash(f'{form.desc.data} Banner 수정 완료.')
        return redirect(url_for('admin.banner'))

    return render_template('admin/banner_form.html', form=form)
```





##### front - 64_banner_change_after_banner_edit_route.html

```html
<a href="{{url_for('admin.banner_edit', id=banner.id)}}" class="tag is-success is-light">
    <span class="icon">
        <i class="mdi mdi-square-edit-outline"></i>
    </span>
    수정								
</a>
```





#### banner delete

##### banner delete route

- file경로 field를 가지는 entity의 경우 **삭제시 파일도 같이 삭제**

```python
@admin_bp.route('/banner/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def banner_delete(id):
    with DBConnectionHandler() as db:
        banner = db.session.get(Banner, id)

        if banner:
            # 필드에 file을 가지고 있는 entity는 file도 같이 삭제한다.
            delete_uploaded_file(directory_and_filename=banner.img)
            db.session.delete(banner)
            db.session.commit()
            flash(f'{banner.desc} Banner 삭제 완료.')
            return redirect(url_for('admin.banner'))
```





##### front - 65_banner_change_after_banner_delete_route.html

```html
<a href="{{url_for('admin.banner_delete', id=banner.id)}}" class="tag is-danger is-light">
    <span class="icon">
        <i class="mdi mdi-trash-can-outline"></i>
    </span>
    삭제
</a>
```





























##### 왼쪽메뉴 아이콘 검색 사이트

1. https://materialdesignicons.com/ 검색
2. css/materialdesignicons.css에서 검색되는지 확인
3. span>i로 적용

![image-20221126201012272](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221126201012272.png)





##### front - 66_index_change_menus_icon.html

```html
{% block menus %}
<aside class="menu">
    <p class="menu-label">
        <span class="icon"><i class="mdi mdi-google-assistant"></i></span>
        Dashboard | {{request.path}}
    </p>
    <ul class="menu-list">
        <li>
            <a class="{% if request.path == '/admin/' %}is-active{% endif %}"
               href="{{ url_for('admin.index') }}">
                <span class="icon"><i class="mdi mdi-home-variant-outline"></i></span>
                Home
            </a>
        </li>
    </ul>
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
    <p class="menu-label">
        <span class="icon"><i class="mdi mdi-clipboard-text-multiple-outline"></i></span>
        Article
    </p>
    <ul class="menu-list">
        <li>
            <a class="{% if 'article' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.article') }}">
                <span class="icon"><i class="mdi mdi-clipboard-text-outline"></i></span>
                Post 관리
            </a>
        </li>
        <li>
            <a class="{% if 'tag' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.tag') }}">
                <span class="icon"><i class="mdi mdi-tag-plus-outline"></i></span>
                Tag 관리
            </a>
        </li>
    </ul>

    <p class="menu-label">
        <span class="icon"><i class="mdi mdi-account-group-outline"></i></span>
        User
    </p>
    <ul class="menu-list">
        <li>
            <a class="{% if 'user' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.user') }}">
                <span class="icon"><i class="mdi mdi-account-outline"></i></span>
                User 관리
            </a>
        </li>
        <li>
            <a class="{% if 'password' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.user') }}">
                <span class="icon"><i class="mdi mdi-lock-outline"></i></span>
                비밀번호 변경
            </a>
        </li>
    </ul>


    <p class="menu-label">
        <span class="icon"><i class="mdi mdi-cog-outline"></i></span>
        Banner
    </p>
    <ul class="menu-list">
        <li>
            <a class="{% if 'banner' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.banner') }}">
                <span class="icon"><i class="mdi mdi-image-sync-outline"></i></span>
                Banner 관리
            </a>
        </li>
    </ul>

</aside>
{% endblock menus %}
```

