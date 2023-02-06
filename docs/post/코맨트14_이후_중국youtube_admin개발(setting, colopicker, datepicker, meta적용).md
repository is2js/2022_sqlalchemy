### settings

#### 일단 settings에 적어야할 meta항목 살펴보기

##### meta관련 필드들

- meta관련 필드들
  - title: `<title>`태그에 올라갈 단어들로 **병원명 | 설명**으로 
    - 우아한한의원 | 허리디스크 협착증 목디스크 근육통 무릎 어깨 등 퇴행성 척추 관절 치료
  - description: `<meta name="Description" content="">`및 `meta property="og:description" content="">` 의 content 를 채울 설명들로 **한방병원(or한의원) 허리 목 디스크 척추관협착증 퇴행성 척추관절치료 - 부위들,  교통사고, MRI, 추나요법, 입원, 한약, 통증 | 병원이름** 형식으로 채운다.
    - 한의원 허리 목 디스크 척추관협착증 퇴행성 척추 관절 치료 - 무릎, 어깨, 턱관절, 교통사고, 추나요법, 입원, 한약, 통증 | 우아한한의원
  - keywords: `<meta name="Keywords" content="">`를 채울 설명으로 **지역한의원, 지역교통사고병원, 지역추나, 지역허리디스크, 지역목디스크, 지역협착증, 지역xxxx병원, 지역어깨무릎관절, 지역통증치료, 지역xx병원**형식으로 **지역+ 단어를 콤마로** 채운다
    - 성남한의원, 분당한의원, 성남추나, 분당추나, 성남허리디스크, 분당허리디스크, 성남목디스크, 분당목디스크, 성남협착증, 분당협착증, 성남어깨무릎관절, 분당어깨무릎관절, 성남통증치료, 분당통증치료, 성남교통사고병원, 분당교통사고병원
  - url: `<meta property="og:url" content="">`를 채울 url로서 **실제 접속할 최종 url**
    - "https://www.woowahani.co.kr"
  - image: `<meta property="og:image" content="">`를  **실제 접속할 최종url에서 가져오는 logo image(1200x650.jpg)**
    - https://www.jaseng.co.kr/images/logo/new/logo10000.jpg
  - site_name: `<meta property="og:site-name" content="">`에 들어갈 병원이름
    - 우아한한의원
  - 인증관련
    - google_site_verification: `<meta name="google-site-verification" content="">`
    - naver_site_verification: `<meta name="naver-site-verification" content="">`
  - 통계관련
    - google_static_script: `<script type="text/javascript" async src="https://www.google-analytics.com/analytics.js"></script>`의 src에 들어갈
  - extend_meta: 추가필드

- 웹

  ![image-20221204021846467](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204021846467.png)

- 모바일

  ![image-20221204022048068](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204022048068.png)

- 검색결과

  ![image-20221204022102518](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204022102518.png)



##### 전반적 이용 필드들

![image-20221204025038135](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204025038135.png)

- domain(중복)
- logo(중복)
- ceo 대표명: 
  - 신준식
- business_license_number: 사업자등록번호
  - 211-90-11471
- call_number: 병원전화번호: 
  - 1577-0117
- address:
  -  [06110] 서울시 강남구 강남대로 536 (논현동)
- copyright: 
  - 본사이트의 모든 컨텐츠는 저작권법에 의해 보호를 받는 저작물이므로 무단전제와 무단복제를 엄금합니다.
    ©Jaseng Hospital of Korean Medicine. All rights reserved.
- start_date: 개원 일자(yyyy-mm-dd)
- has_naver_blog: 블로그 사용유무
- has_youtube: 유튜브 사용유무





#### settings model

- infra > admin > settings.py

  ![image-20221204171735066](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221204171735066.png)

- 유동적으로 **칼럼이 생기고 바뀌는, 1row짜리 데이터인 `사이트 전용 환경변수들`**은 **`dict`로 DB에 저장하기 위해, `entity를 id외 setting_key와 setting_value`로 구성한다**
  - python에서는 dict로, db에서는 개별key들을 1row씩 저장하게 된다.

- **unique하며, 항상 검색해야하니 index를 준다**
- **add_date, pub_date를 달아주는 BaseModel이 아닌 일반 `Base를 상속`하도록 하는 유일한 모델이다**

```python
from sqlalchemy import Column, Integer, String, select

from src.infra.config.base import Base
from src.infra.config.connection import DBConnectionHandler


# class Setting(BaseModel):
class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(64), index=True, unique=True)
    setting_value = Column(String(800), default='')

    def __repr__(self) -> str:
        return f'{self.id}=>{self.setting_key}'
    
	# get관련 entity method는 filter(where)에 id를 조회 & select에 entity명을 적어야하는 cls method로 만든다.
    @classmethod
    def to_dict(cls):
        # setting의 모든 data(key, value)를 -> 1개의 dict에 담아서 반환한다
        ret = {}
        with DBConnectionHandler() as db:
            for setting in db.session.scalars(select(cls)):
                ret[setting.setting_key] = setting.setting_value
            return ret

```





### setting edit(create겸용)



#### 특이하게 setting은 db와 form의 필드구조가 다르고, form필드가 select할 데이터를 결정하여 -> form + edit(create겸용)부터 만들고 -> select

##### edit의 <db객체를 가져와 채운 form객체로 form필드들로 구성된 화면>을 먼저 구성한다

- db는 화면을 구성할 객체를 넘겨주지 못하므로 



#### settings form

- **`db칼럼은 key, value`로만 구성되지만, `form에서는 각 key별로 개별field`를 가져야 `route에서 받아서 dict로 만들어 쓴다` **

- **db 및 dict의 key들은 `form의 필드들로 결정`된다.**
  - css에 진자쓰기 : https://code-maven.com/slides/python/flask-no-session
- **string or textareafield로 구성된다**
- **`당장 입력힘든 필드는 string+nullable`필드로서**
  1. **`DataRequired()를 제거`하고**
  2. **`filters=[lambda x: x or None]`으로 빈문자열 입력을 방지한다**

```python
class SettingForm(FlaskForm):
    #### 병원관련 설정
    logo = FileField("로고", validators=[
        # FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'bmp', 'png', 'gif', 'svg'], message="jpg/jpeg/bmp/png/gif/svg 형식만 지원합니다"),
        FileSize(max_size=2048000, message="2M 이하의 파일만 업로드 가능합니다")],
                     description="파일크기가 2M이하의 logo를 업로드해주세요. 1200x650px의 jpg를 권장합니다.")

    #### meta 정보지만, 병원이름으로 들어갈 거라 앞에 선언 
    site_name = StringField('병원 이름', validators=[DataRequired()],
                            description="예시) 우아한한의원",
                            render_kw={"placeholder": "우아한한의원"},
                            )
    theme_color = StringField('테마 색', validators=[DataRequired()],
                              render_kw={"placeholder": "#FFFFFF"},
                              )

    ceo = StringField('대표명', validators=[DataRequired()],
                      description="대표자명을 입력해주세요. ex> 홍길동 ",
                      render_kw={"placeholder": "홍길동"},
                      )

    business_license_number = StringField('사업자등록번호', validators=[DataRequired()],
                                          description="사업자 등록번호를 입력. ex> 211-00-00470",
                                          render_kw={"placeholder": "211-00-00470"},
                                          )
    call_number = StringField('병원 전화번호', validators=[DataRequired()],
                              description="환자가 걸 병원 전화번호 입력. ex> 1577-0117",
                              render_kw={"placeholder": "1577-0117"},
                              )

    address = StringField('병원 주소', validators=[DataRequired()],
                          description="ex> [06110] 서울시 00구 00대로 123 (논현동)",
                          render_kw={"placeholder": "[06110] 서울시 00구 00대로 123 (논현동)"},
                          )
    #### 당장입력이 어려운 string 필드 ->
    # (1) nullable 필드는 front 필수입력 검사 => DataRequired() 를 제거
    # (2)  string+nullable로서, 빈문자열 안들어가게 =>  filters=[lambda x: x or None]를 추가한다
    copyright = TextAreaField('저작권 문구', validators=[],
                              description="추후 입력가능!! 저작권 관련 문구를 작성해주세요 ex> 본사이트의 모든 컨텐츠는 저작권법에 의해 보호를 받는 저작물이므로 무단전제와 무단복제를 엄금합니다.©우아한 한의원. All rights reserved.",
                              render_kw={
                                  "placeholder": "본사이트의 모든 컨텐츠는 저작권법에 의해 보호를 받는 저작물이므로 무단전제와 무단복제를 엄금합니다.©우아한 한의원. All rights reserved."},
                              filters=[lambda x: x or None],
                              )
    start_date = StringField('개원 일자', validators=[DataRequired()],
                             description="개원 시작일 ex> 2023-01-01",
                             render_kw={"placeholder": "2023-01-01"},
                             )

    naver_blog_url = StringField('Naver Blog Url', validators=[],
                                 description="해당없을시 빈칸!! 네이버 블로그 주소를 입력",
                                 render_kw={"placeholder": "https://blog.naver.com"},
                                 filters=[lambda x: x or None],
                                 )
    youtube_url = StringField('Youtube Url', validators=[],
                              description="해당없을시 빈칸!!유튜브 채널 주소를 입력",
                              render_kw={"placeholder": "https://www.youtube.com/channel/UChZt76JR2Fed1EQ_Ql2W_cw"},
                              filters=[lambda x: x or None],
                              )

    #### 사이트 meta 설정
    title = TextAreaField('사이트 제목', validators=[],
                          description="추후입력 가능!! 검색될 사이트의 제목을 [병원명 | 설명] 형식으로 ex> 우아한한의원 | 허리디스크 협착증 목디스크 근육통 무릎 어깨 등 퇴행성 척추 관절 치료",
                          render_kw={"placeholder": "우아한한의원 | 허리디스크 협착증 목디스크 근육통 무릎 어깨 등 퇴행성 척추 관절 치료"},
                          filters=[lambda x: x or None],
                          )
    # site_name -> 병원이름과 동일해서 병원정보에서 입력받음

    description = TextAreaField('사이트 설명', validators=[],
                                description="추후입력 가능!! ex> 한방병원(or한의원) 허리 목 디스크 척추관협착증 퇴행성 척추관절치료 - 부위들,  교통사고, MRI, 추나요법, 입원, 한약, 통증 | 병원이름",
                                render_kw={
                                    "placeholder": "한의원 허리 목 디스크 척추관협착증 퇴행성 척추 관절 치료 - 무릎, 어깨, 턱관절, 교통사고, 추나요법, 입원, 한약, 통증 | 우아한한의원"},
                                filters=[lambda x: x or None],
                                )
    keywords = TextAreaField('검색 키워드', validators=[],
                             description="추후입력 가능!! 예상 검색 단어를 [지역+word]형식을 콤마들로 연결 ex> 지역한의원, 지역교통사고병원, 지역추나, 지역허리디스크, 지역목디스크, 지역협착증, 지역xxxx병원, 지역어깨무릎관절, 지역통증치료, 지역xx병원",
                             render_kw={
                                 "placeholder": "성남한의원, 분당한의원, 성남추나, 분당추나, 성남허리디스크, 분당허리디스크, 성남목디스크, 분당목디스크, 성남협착증, 분당협착증, 성남어깨무릎관절, 분당어깨무릎관절, 성남통증치료, 분당통증치료, 성남교통사고병원, 분당교통사고병원"},
                             filters=[lambda x: x or None],
                             )
    # image -> logo와 동일해서 병원정보에서 logo로 입력받되, 나중에 사용시 logo필드를 사용할 것

    #### 관리자 문의 설정
    url = StringField('접속할 최종 url', validators=[],
                      description="추후 입력가능!! 예시) https://www.woowahani.co.kr",
                      render_kw={"placeholder": "https://www.woowahani.co.kr"},
                      filters=[lambda x: x or None],
                      )
    google_site_verification = StringField('구글 인증 코드', validators=[],
                                           description='관리자 문의로 입력!! <meta name="google-site-verification" content="">',
                                           render_kw={"placeholder": "abcde"},
                                           filters=[lambda x: x or None],
                                           )
    naver_site_verification = StringField('네이버 인증 코드', validators=[],
                                          description='관리자 문의로 입력!! <meta name="google-naver-verification" content="">',
                                          render_kw={"placeholder": "abcde"},
                                          filters=[lambda x: x or None],
                                          )
    google_static_script = StringField('구글 통계 코드', validators=[],
                                       description='관리자 문의로 입력!! <script type="text/javascript" async src="https://www.google-analytics.com/analytics.js"></script>',
                                       render_kw={"placeholder": "abcde"},
                                       filters=[lambda x: x or None],
                                       )

    #### 특이하게 해당entity객체 대신 dict1개가 넘어와서 form객체를 채운다.
    #### 특이하게 create(add)용 객체안받는 form객체를 생성하지 않고 수정용form만 사용된다.?
    def __init__(self, s_dict=None, *args, **kwargs):
        self.s_dict = s_dict
        if self.s_dict:
            #### 특이하게 .__dict__를 안해도 된다.
            # super().__init__(**self.tag.__dict__)
            super().__init__(**self.s_dict)
        else:
            super().__init__(*args, **kwargs)

    #### form class의 인스턴스 메서드로 form데이터 -> dict로 변환한다.
    # -> csrf_token, submit의 name을 가진 필드는 제외하고, 데이터를 뽑아 dict에 넣어 반환한다.
    def to_dict(self):
        ret = {}
        for name in self._fields:
            if name in ['csrf_token', 'submit']:
                continue
            ret[name] = self._fields[name].data
        return ret

```

#### setting edit route

- edit route는 **db객체를 가져와 채운 form객체로 화면을 만든다.**

- **dict를 key, value로 저장하는 DB는 `dict로 다시 변환해야지만, 일반 entity객체 개념으로서 쓸 수 있다`**
  - Entity.to_dict() -> dict를 form에 건네준다.

```python
@admin_bp.route('/setting/edit', methods=['GET', 'POST'])
@login_required
def setting_edit():
    setting_dict = Setting.to_dict()
    form = SettingForm(setting_dict)

    # print(setting_dict) # {}
    # return 'ok'

    return render_template('admin/setting_form.html', form=form)
```

##### 수정용 form처리를 위한 form 생성자 재정의

```python
#### 특이하게 해당entity객체 대신 dict1개가 넘어와서 form객체를 채운다.
#### 특이하게 create(add)용 객체안받는 form객체를 생성하지 않고 수정용form만 사용된다.?
def __init__(self, s_dict=None, *args, **kwargs):
    self.s_dict = s_dict
    if self.s_dict:
        #### 특이하게 .__dict__를 안해도 된다.
        # super().__init__(**self.tag.__dict__)
        super().__init__(**self.s_dict)
    else:
    	super().__init__(*args, **kwargs)

```



### setting select

#### 화면 구성을 위해 생성한 form기반으로 select부터 처리해본다



#### setting route

```python
@admin_bp.route('/setting', methods=['GET'])
@login_required
def setting():
    s_dict = Setting.to_dict()

    # db객체 list대신 dict를 건네준다.
    return render_template('admin/setting.html', s_dict=s_dict)
```



#### setting.html 

##### tab + b-upload를 가진 userinfo.html을 복사해서 수정

- userinfo.html(select)를 상속한 userinfo_form.html에 대해서
- userinfo.html을 복사한 settings.html





##### setting.html은 나중에 채울 거지만, 상속을 위해 먼저 정의

- auth/userinfo.html와 비슷해서 복사해서 정의한다

##### jinja는 빈문자열->None으로 처리했어도, None을 그대로 출력하므로  {{ dict.get() or 'default문자열' }}로 준다.

##### front - 77_setting_extends_index_after_setting_route.html

```html
{% extends 'admin/index.html' %}

<!-- admin/index.html 중 왼쪽칼럼2개짜리 메뉴의 실제 aside태그부분-->
{% block menus %}
<aside class="menu">
    <p class="menu-label">
        Setting
    </p>
    <ul class="menu-list">
        <li>
            <a class="{% if  '/setting' in request.path %}is-active{% endif %}"
               href="{{ url_for('admin.setting') }}">
                사이트 설정
            </a>
        </li>
        <li>
            <a class="" href="">
                세부 페이지 설정
            </a>
        </li>
        <li>
            <a class="" href="">
                관리자 문의
            </a>
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
            <!--            <li>{{ error }}：{{ v[0] }}</li>-->
            <li>{{ v[0] }}</li>
            {% endfor %}
        </ul>
    </b-message>
    {% endif %}
    <!-- setting_form에서 달라질 부분 block개설  -->


    {% block tab_content %}

    <div class="columns is-mobile" >
        <!-- logo -->
        <!--                <div class="column">-->
        <!--                    <figure class="image is-96x96">-->
        <!-- figure를  is-사이즈x사이즈가 아닌 is-2by1의 비율로 만드려면, 상위 column이 is-3 등으로 자리를 고정적으로 차지하고 있어야한다 -->
        <!-- 만약, column에 is-3을 주지 않고 figure에 is-2by1의 비율만 주면, 안나타난다. -->
        <div class="column is-3">
            <figure class="image is-2by1">
                <!--                        <img class="is-rounded" style="height: 100%;"-->
                <img class="" style="height: 80%;"
                     src="
                         {% if s_dict.get('logo', None) %}
                         {{url_for('download_file', filename=s_dict.logo)}}
                         {% else %}
                         {{url_for('static', filename='/img/placeholders/1200x650.png')}}
                         {% endif %}
                        "
                >
            </figure>
        </div>

        <div class="column is-narrow">
            <div style="padding-top: 1.5rem;">
                <h1 class="title is-size-4">{{ s_dict.get('site_name') or '병원 이름 미설정'  }}</h1>
                <p class="subtitle is-size-6"> ← 병원 로고</p>
            </div>
        </div>


        <div class="column is-narrow-mobile">
            <a class=" button is-primary is-pulled-right"
               href="{{url_for('admin.setting_edit') }}"
               style="margin-top: 1.8rem">설정 수정</a>
        </div>
    </div>


    <b-tabs type="is-boxed" expanded>
        <!-- 탭1 병원관련 정보 -->
        <b-tab-item label="병원관련 정보" icon="hospital-building">

            <div class="columns" style="padding:1rem 0; ">
                <!-- 병원 정보들 -->
                <div class="column is-2">
                    <p>병원 정보</p>
                </div>
                <div class="column">
                     <!-- 병원 이름 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">병원 이름</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('site_name') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 테마 색 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">테마 색</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('theme_color') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 대표명 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">대표명</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('ceo') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 사업자등록번호 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">사업자등록번호</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('business_license_number') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 병원 전화번호 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">병원 전화번호</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('call_number') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 병원 주소 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">병원 주소</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('address') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 저작권 문구 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">저작권 문구</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('copyright') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 개원 일자 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">개원 일자</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('start_date') or '미설정' }}</span>
                        </div>
                    </div>
                </div>
            </div>
            <!--  SNS관련 정보들  -->
            <div class="columns" style="padding:1rem 0; ">
                <div class="column is-2">
                    <p>SNS관련 정보</p>
                </div>
                <div class="column">
                    <!-- Naver Blog Url  -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">Naver Blog Url</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('naver_blog_url', '미운영') }}</span>
                        </div>
                    </div>
                    <!-- Youtube Url -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">Youtube Url</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('youtube_url', '미운영') }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </b-tab-item>
        <!-- 탭1 끝 -->

        <!-- 탭2 Site Meta 정보 -->
        <b-tab-item label="Site Meta 정보" icon="hospital">

            <div class="columns" style="padding:1rem 0; ">

                <div class="column">
                    <!-- 사이트 제목 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">사이트 제목</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('title') or '미설정' }}</span>
                        </div>
                    </div>

                    <!-- 사이트 설명 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">사이트 설명</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('description') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 검색 키워드 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">검색 키워드</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('keywords') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 접속할 최종 url -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">접속할 최종 url</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('url') or '미설정' }}</span>
                        </div>
                    </div>
                    <!--구글 인증 코드-->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">구글 인증 코드</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('google_site_verification') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 네이버 인증 코드 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">네이버 인증 코드</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('naver_site_verification') or '미설정' }}</span>
                        </div>
                    </div>
                    <!-- 구글 통계 스크립트 -->
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">구글 통계 스크립트</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">{{ s_dict.get('google_static_script') or '미설정' }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </b-tab-item>
        <!-- 탭2 끝 -->

    </b-tabs>
    {% endblock tab_content %}
</template>
{% endblock member %}


{% block vue_script %}{% endblock vue_script %}
```

![image-20221205025148506](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221205025148506.png)

### 다시 setting edit

#### setting_form.html

##### front -  78_setting_form_extends_setting_after_setting_edit_route.html

```html
{% extends 'admin/setting.html' %}


{% block tab_content %}
<!-- form 추가 시작 -->
<form action="" method="post" class="mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}

    <div class="columns is-mobile">
        <div class="column is-3">
            <figure class="image is-2by1">
                <img class="" style="height: 80%;"
                     :src="
                         img_file_url ? img_file_url :
                         `
                         {% if form.s_dict.logo %}
                         {{url_for('download_file', filename=form.s_dict.logo)}}
                         {% else %}
                         {{url_for('static', filename='/img/placeholders/1200x650.png')}}
                         {% endif %}
                         `
                        "
                >
            </figure>
        </div>
        <!-- 업로드 버튼 -->
        <div class="column is-narrow is-7">
            <div style="padding-top: 1.5rem;">
                <b-field>
                    <b-field class="file is-primary" :class="{'has-name': !!file}">
                        <b-upload
                                class="file-label" rounded
                                v-model="img_file"
                                name="logo"
                        >
                                      <span class="file-cta">
                                        <b-icon class="file-icon" icon="upload"></b-icon>
                                        <span class="file-label">{$ img_file.name || "병원 로고 업로드" $}</span>
                                      </span>
                        </b-upload>
                    </b-field>
                </b-field>
            </div>
            <p class="help has-text-grey-light">
                {{ form.logo.description }}
            </p>
        </div>
    </div>


    <!--    <b-tabs type="is-boxed" expanded>-->
    <!--        &lt;!&ndash; 탭1 병원관련 정보 &ndash;&gt;-->
    <!--        <b-tab-item label="병원관련 정보" icon="hospital-building">-->

    <div class="columns">
        <!-- 병원 정보들 -->
        <div class="column is-2">
            <p>병원 정보</p>
        </div>
        <div class="column">

            <!-- 병원 이름 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.site_name.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.site_name(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.site_name.description }}
                    </p>
                </div>
            </div>

            <!-- 테마 색 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.theme_color.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.theme_color(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.theme_color.description }}
                    </p>
                </div>
            </div>
            <!-- 대표명 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.ceo.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.ceo(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.ceo.description }}
                    </p>
                </div>
            </div>


            <!-- 사업자등록번호 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.business_license_number.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.business_license_number(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.business_license_number.description }}
                    </p>
                </div>
            </div>

            <!-- 병원 전화번호 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.call_number.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.call_number(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.call_number.description }}
                    </p>
                </div>
            </div>

            <!-- 병원 주소 -->

            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.address.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.address(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.address.description }}
                    </p>
                </div>
            </div>

            <!-- 저작권 문구 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.copyright.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.copyright(class='textarea', rows="3")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.copyright.description }}
                    </p>
                </div>
            </div>

            <!-- 개원 일자 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.start_date.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.start_date(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.start_date.description }}
                    </p>
                </div>
            </div>

        </div>
    </div>
    <!--  SNS관련 정보들  -->
    <div class="columns">
        <div class="column is-2">
            <p>SNS관련 정보</p>
        </div>
        <div class="column">
            <!-- Naver Blog Url  -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.naver_blog_url.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.naver_blog_url(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.naver_blog_url.description }}
                    </p>
                </div>
            </div>
            <!-- Youtube Url -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.youtube_url.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.youtube_url(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.youtube_url.description }}
                    </p>
                </div>
            </div>

        </div>
    </div>

    <div class="columns">
        <div class="column is-2">
            <p>Meta 정보</p>
        </div>
        <div class="column">
            <!-- 사이트 제목 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.title.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.title(class='textarea', rows="4")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.title.description }}
                    </p>
                </div>
            </div>


            <!-- 사이트 설명 -->

            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.description.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.description(class='textarea', rows="4")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.description.description }}
                    </p>
                </div>
            </div>

            <!-- 검색 키워드 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.keywords.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.keywords(class='textarea', rows="5")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.keywords.description }}
                    </p>
                </div>
            </div>

            <!-- 접속할 최종 url -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.url.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.url(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.url.description }}
                    </p>
                </div>
            </div>


            <!--구글 인증 코드-->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.google_site_verification.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.google_site_verification(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.google_site_verification.description }}
                    </p>
                </div>
            </div>

            <!-- 네이버 인증 코드 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.naver_site_verification.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.naver_site_verification(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.naver_site_verification.description }}
                    </p>
                </div>
            </div>

            <!-- 구글 통계 스크립트 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.google_static_script.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.google_static_script(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.google_static_script.description }}
                    </p>
                </div>
            </div>

        </div>
    </div>
    <!-- 수정완료 submit -->
    <!-- column을 가운데 놓으려면, columns가 is-centered -->
    <div class="columns is-mobile is-centered">
        <div class="column is-narrow">
            <a href="{{ url_for('admin.setting') }}"
               class="button is-light">
                뒤로가기
            </a>
        </div>
        <div class="column is-narrow">
            <input type="submit" value="수정완료"
                   class="button is-primary"
            >
        </div>
    </div>
</form>
{% endblock tab_content %}


{% block vue_script %}{% endblock vue_script %}
```

![image-20221205025242985](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221205025242985.png)



![image-20221205025251373](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221205025251373.png)





#### setting_edit route

##### form필드정보들을 다시 dict로 만들고, key+value순회하면서,1) key가 db에 이미 존재시, 없뎃여부 보고 update 2) key가 db에 없으면, value None이라도 일단 객체 생성해서 저장

- **아직 로고처리는 안했음.**

```python
@admin_bp.route('/setting/edit', methods=['GET', 'POST'])
@login_required
def setting_edit():
    s_dict = Setting.to_dict()
    form = SettingForm(s_dict)

    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            # 1) form의 to_dict메서드를 활용하여, form 모든 정보를 key, value로서 순회할 수 있게 한다
            return_s_dict = form.to_dict()


            for key, value in return_s_dict.items():

                # 1) 각 key,value는 1row로서 Setting의 1개의 객체에 해당하므로
                #    setting객체를 만들어 입력할텐데,
                #    1-1) [이미 꺼냈떤 s_dict에서 이미 존재하는 key]이면 => 조회후 객체필드 변경(update)
                #    1-2) 없던 key는 새객체만들어서 add를 나눠서 해준다.
                if key in s_dict:
                    print(key, "는 이미 존재인데")
                    setting = Setting.get_by_key(key)
                    # 1-1-2) 이미 존재해서 꺼냈을 때 값을 비교해서 다르면 업데이트
                    if setting.setting_value == value:
                        print(key, "같은 값이라서 continue")
                        continue
                    else:
                        print(key, "값이 달라져서 update")
                        setting.setting_value = value
                        #### 객체 필드변경후 commit만 하면 자동반영X -> session이 달라서
                        #### => 수정이든, 새로생성이든 아래에서 공통적으로 session.add()해야함.

                else:
                    print(key, "없어서  새로 생성 -> value가 None이도 None으로 넣을 것임.")
                    setting = Setting(
                        setting_key=key,
                        setting_value=value
                    )


                db.session.add(setting)

            db.session.commit()
            flash(f'세팅 수정 완료.')

            return redirect(url_for('admin.setting'))


    return render_template('admin/setting_form.html', form=form)

```



##### image 업로드 처리로직 추가 (dict 순회전에 logo key를 업뎃해준다 )

```python
@admin_bp.route('/setting/edit', methods=['GET', 'POST'])
@login_required
def setting_edit():
    s_dict = Setting.to_dict()
    form = SettingForm(s_dict)

    if form.validate_on_submit():
        with DBConnectionHandler() as db:

            return_s_dict = form.to_dict()

            #### 파일업로드 처리 -> dict를 하나씩 보기 전에 처리, dict의 key에 할당
            f = return_s_dict["logo"]
            # 수정안되서 경로 그대로 오는지 vs 새 파일객체가 오는지 구분
            # 최초 수정시에는  db에 logo key가 아예 없을 수 있기 때문에 s_dict는 get으로 얻어오기
            if f != s_dict.get("logo", None):
                logo_path, filename = upload_file_path(directory_name='logo', file=f)
                f.save(logo_path)

                delete_uploaded_file(directory_and_filename=s_dict.get("logo", None))

                return_s_dict["logo"] = f'logo/{filename}'


            for key, value in return_s_dict.items():

                # 1) 각 key,value는 1row로서 Setting의 1개의 객체에 해당하므로
                #    setting객체를 만들어 입력할텐데,
                #    1-1) [이미 꺼냈떤 s_dict에서 이미 존재하는 key]이면 => 조회후 객체필드 변경(update)
                #    1-2) 없던 key는 새객체만들어서 add를 나눠서 해준다.
                if key in s_dict:
                    print(key, "는 이미 존재인데")
                    setting = Setting.get_by_key(key)
                    # 1-1-2) 이미 존재해서 꺼냈을 때 값을 비교해서 다르면 업데이트
                    if setting.setting_value == value:
                        print(key, "같은 값이라서 continue")
                        continue
                    else:
                        print(key, "값이 달라져서 update")
                        setting.setting_value = value
                        #### 객체 필드변경후 commit만 하면 자동반영X -> session이 달라서
                        #### => 수정이든, 새로생성이든 아래에서 공통적으로 session.add()해야함.

                else:
                    print(key, "없어서  새로 생성 -> value가 None이도 None으로 넣을 것임.")
                    setting = Setting(
                        setting_key=key,
                        setting_value=value
                    )


                db.session.add(setting)

            db.session.commit()
            flash(f'세팅 수정 완료.')

            return redirect(url_for('admin.setting'))


    return render_template('admin/setting_form.html', form=form)

```

![image-20221205040125854](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221205040125854.png)





### settings를 index.html에 편입시키기

![image-20221205043713413](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221205043713413.png)

#### admin/index.html 메뉴수정

##### front - 79_index_change_after_setting_complete.html

```html
<p class="menu-label">
    <span class="icon"><i class="mdi mdi-image-outline"></i></span>
    BANNER
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

<p class="menu-label">
    <span class="icon"><i class="mdi mdi-cog-outline"></i></span>
    SETTING
</p>
<ul class="menu-list">
    <li>
        <a class="{% if 'setting' in request.path %}is-active{% endif %}"
           href="{{ url_for('admin.setting') }}">
            <span class="icon"><i class="mdi mdi-window-shutter-cog"></i></span>
            Site 관리
        </a>
    </li>
</ul>
```



#### setting.html, setting_form.html 수정

##### front - 80_setting_change_after_index로병합.html

```html
{% extends 'admin/index.html' %}

{% block member %}
<div class="is-block">
    <div class=" is-pulled-left">
        <h1 class=" is-size-4">
            <span class="icon">
                <i class="mdi mdi-window-shutter-cog"></i>
            </span>
            Site 관리
        </h1>
    </div>

    {% block button %}{% endblock button %}
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
<!-- setting_form에서 달라질 부분 block개설  -->
<div class="columns is-mobile mt-3">
    <!-- columns에는 margin을 줄 수 없어서 column들 모두 똑같은 my-5를 줬다. -->
    <div class="column is-3 my-5">
        <figure class="image is-2by1" style="border: 1px solid rgb(190, 190, 190);">
            <!--                        <img class="is-rounded" style="height: 100%;"-->
            <img class="" style="height: 100%;"
                 src="
                     {% if s_dict.get('logo', None) %}
                     {{url_for('download_file', filename=s_dict.logo)}}
                     {% else %}
                     {{url_for('static', filename='/img/placeholders/1200x650.png')}}
                     {% endif %}
                    "
            >
        </figure>
    </div>

    <div class="column is-4 my-5">
        <div style="padding-top: 1rem;">
            <h1 class="title is-size-4">{{ s_dict.get('site_name') or '병원 이름 미설정' }}</h1>
            <p class="subtitle is-size-6"> ← 병원 로고</p>
        </div>
    </div>


    <div class="column is-narrow-mobile my-5">
        <a class=" button is-primary"
           href="{{url_for('admin.setting_edit') }}"
           style="margin-top: 1.8rem">수정</a>
    </div>
</div>


<b-tabs type="is-boxed">
    <!-- 탭1 병원관련 정보 -->
    <b-tab-item label="병원관련 정보" icon="hospital-building">

        <div class="columns" style="padding:1rem 0; ">
            <!-- 필수 정보들 -->
            <div class="column is-2">
                <p>필수 정보</p>
            </div>
            <div class="column">
                <!-- 병원 이름 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">병원 이름</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('site_name') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 테마 색 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">테마 색</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('theme_color') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 대표명 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">대표명</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('ceo') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 사업자등록번호 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">사업자등록번호</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('business_license_number') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 병원 전화번호 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">병원 전화번호</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('call_number') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 병원 주소 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">병원 주소</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('address') or '미설정' }}</span>
                    </div>
                </div>

                <!-- 개원 일자 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">개원 일자</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('start_date') or '미설정' }}</span>
                    </div>
                </div>
            </div>
        </div>
        <!--  추가정보들  -->
        <div class="columns" style="padding:1rem 0; ">
            <div class="column is-2">
                <p>추가 정보</p>
            </div>
            <div class="column">
                <!-- 저작권 문구 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">저작권 문구</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('copyright') or '미설정' }}</span>
                    </div>
                </div>
                <!-- Naver Blog Url  -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">Naver Blog Url</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('naver_blog_url') or '미운영' }}</span>
                    </div>
                </div>
                <!-- Youtube Url -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">Youtube Url</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('youtube_url') or '미운영' }}</span>
                    </div>
                </div>
            </div>
        </div>
    </b-tab-item>
    <!-- 탭1 끝 -->

    <!-- 탭2 Site Meta 정보 -->
    <b-tab-item label="Site Meta 정보" icon="hospital">

        <div class="columns" style="padding:1rem 0; ">

            <div class="column">
                <!-- 사이트 제목 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">사이트 제목</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('title') or '미설정' }}</span>
                    </div>
                </div>

                <!-- 사이트 설명 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">사이트 설명</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('description') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 검색 키워드 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">검색 키워드</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('keywords') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 접속할 최종 url -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">접속할 최종 url</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('url') or '미설정' }}</span>
                    </div>
                </div>
                <!--구글 인증 코드-->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">구글 인증 코드</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('google_site_verification') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 네이버 인증 코드 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">네이버 인증 코드</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('naver_site_verification') or '미설정' }}</span>
                    </div>
                </div>
                <!-- 구글 통계 스크립트 -->
                <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                    <div class="column is-2">
                        <span class=" has-text-grey-light">구글 통계 스크립트</span>
                    </div>
                    <div class="column is-narrow">
                        <span class=" has-text-black-ter">{{ s_dict.get('google_static_script') or '미설정' }}</span>
                    </div>
                </div>
            </div>
        </div>
    </b-tab-item>
    <!-- 탭2 끝 -->

</b-tabs>
{% endblock table_content %}
{% endblock member %}


{% block vue_script %}{% endblock vue_script %}

```



##### front - 81_setting_form_change_after_index로병합.html



```html
{% extends 'admin/setting.html' %}

{% block button %}{% endblock button %}


{% block table_content %}
<!-- form 추가 시작 -->
<form action="" method="post" class="mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}

    <div class="columns is-mobile" >
        <!-- columns에는 margin을 줄 수 없어서 column들 모두 똑같은 my-5를 줬다. -->
        <div class="column is-3 my-5">
            <figure class="image is-2by1" style="border: 1px solid rgb(190, 190, 190);">
                <img class="" style="height: 100%;"
                     :src="
                         img_file_url ? img_file_url :
                         `
                         {% if form.s_dict.logo %}
                         {{url_for('download_file', filename=form.s_dict.logo)}}
                         {% else %}
                         {{url_for('static', filename='/img/placeholders/1200x650.png')}}
                         {% endif %}
                         `
                        "
                >
            </figure>
        </div>
        <!-- 업로드 버튼 -->
        <div class="column is-narrow is-7  my-5">
            <div style="padding-top: 1rem;">
                <b-field>
                    <b-field class="file is-primary" :class="{'has-name': !!file}">
                        <b-upload
                                class="file-label" rounded
                                v-model="img_file"
                                name="logo"
                        >
                                      <span class="file-cta">
                                        <b-icon class="file-icon" icon="upload"></b-icon>
                                        <span class="file-label">{$ img_file.name || "병원 로고 업로드" $}</span>
                                      </span>
                        </b-upload>
                    </b-field>
                </b-field>
            </div>
            <p class="help has-text-grey-light">
                {{ form.logo.description }}
            </p>
        </div>
    </div>


    <!--    <b-tabs type="is-boxed" expanded>-->
    <!--        &lt;!&ndash; 탭1 병원관련 정보 &ndash;&gt;-->
    <!--        <b-tab-item label="병원관련 정보" icon="hospital-building">-->

    <div class="columns">
        <!-- 병원 정보들 -->
        <div class="column is-2">
            <p>병원 정보</p>
        </div>
        <div class="column">

            <!-- 병원 이름 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.site_name.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.site_name(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.site_name.description }}
                    </p>
                </div>
            </div>

            <!-- 테마 색 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.theme_color.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.theme_color(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.theme_color.description }}
                    </p>
                </div>
            </div>
            <!-- 대표명 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.ceo.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.ceo(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.ceo.description }}
                    </p>
                </div>
            </div>


            <!-- 사업자등록번호 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.business_license_number.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.business_license_number(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.business_license_number.description }}
                    </p>
                </div>
            </div>

            <!-- 병원 전화번호 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.call_number.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.call_number(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.call_number.description }}
                    </p>
                </div>
            </div>

            <!-- 병원 주소 -->

            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.address.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.address(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.address.description }}
                    </p>
                </div>
            </div>


            <!-- 개원 일자 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.start_date.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.start_date(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.start_date.description }}
                    </p>
                </div>
            </div>

        </div>
    </div>
    <!--  SNS관련 정보들  -->
    <div class="columns">
        <div class="column is-2">
            <p>추가 정보</p>
        </div>

        <div class="column">
          <!-- 저작권 문구 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.copyright.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.copyright(class='textarea', rows="3")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.copyright.description }}
                    </p>
                </div>
            </div>
            <!-- Naver Blog Url  -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.naver_blog_url.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.naver_blog_url(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.naver_blog_url.description }}
                    </p>
                </div>
            </div>
            <!-- Youtube Url -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.youtube_url.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.youtube_url(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.youtube_url.description }}
                    </p>
                </div>
            </div>

        </div>
    </div>

    <div class="columns">
        <div class="column is-2">
            <p>Meta 정보</p>
        </div>
        <div class="column">
            <!-- 사이트 제목 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.title.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.title(class='textarea', rows="4")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.title.description }}
                    </p>
                </div>
            </div>


            <!-- 사이트 설명 -->

            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.description.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.description(class='textarea', rows="4")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.description.description }}
                    </p>
                </div>
            </div>

            <!-- 검색 키워드 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.keywords.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.keywords(class='textarea', rows="5")}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.keywords.description }}
                    </p>
                </div>
            </div>

            <!-- 접속할 최종 url -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.url.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.url(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.url.description }}
                    </p>
                </div>
            </div>


            <!--구글 인증 코드-->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.google_site_verification.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.google_site_verification(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.google_site_verification.description }}
                    </p>
                </div>
            </div>

            <!-- 네이버 인증 코드 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.naver_site_verification.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.naver_site_verification(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.naver_site_verification.description }}
                    </p>
                </div>
            </div>

            <!-- 구글 통계 스크립트 -->
            <div class="columns">
                <div class="column is-2">
                    <p>{{ form.google_static_script.label(class='label')}}</p>
                </div>
                <div class="column is-6 ">
                    <div class="content">
                        {{form.google_static_script(class='input')}}
                    </div>
                    <p class="help has-text-primary-dark">
                        {{ form.google_static_script.description }}
                    </p>
                </div>
            </div>

        </div>
    </div>
    <!-- 수정완료 submit -->
    <!-- column을 가운데 놓으려면, columns가 is-centered -->
    <div class="columns is-mobile is-centered">
        <div class="column is-narrow">
            <a href="{{ url_for('admin.setting') }}"
               class="button is-light">
                뒤로가기
            </a>
        </div>
        <div class="column is-narrow">
            <input type="submit" value="수정완료"
                   class="button is-primary"
            >
        </div>
    </div>
</form>
{% endblock table_content %}

```



![image-20221205043841699](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221205043841699.png)





### 테마색에 colorpicker/ 개원일에는 datepicker 적용하고, app context에 inject해서 사용하기

#### 둘다 수정form에만 나타나는 거라 setting_form.html을 먼저 수정한다



#### color picker

##### :value= +  @input="input데이터 들어올 때 작동 method 객체" 대신 `<v-> or <b->`태그 사용 시 `v-model=""`로 다 해결한다

```html
<b-field>
    <b-colorpicker
                   v-model="selectedColor"
                   />
</b-field>
```



##### v-model에 사용할 변수는 전역변수로서 base.html에 초기화해준다.

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            //...

            // admin/setting_form에서 쓰는 b-colorpicker v-model 변수
            selectedColor: null,
        },
```





##### 특정html에만 render되는 edit form data를 전역변수에 초기화하려면, 해당 html의 block vue_script를 활용한다

```html
{% block vue_script %}
<script>
    app._data.selectedColor = "{{ form.theme_color.data }}"
</script>
{% endblock vue_script %}

```



- buefy colopicker를 복사해서 수정form.html에 추가한다

  ![image-20221207004858269](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207004858269.png)



##### flask wtform이 vue의 v-model변수를 받으려면, input태그 랜더링시 kwargs(별별dict)로 `:value` : `'v-model변수'`를 주면, 실시간 변수변화값을 받아들인다.

```html
{{form.theme_color(class='input', **{':value':'selectedColor'}) }}
```

##### `v-model`을 속성으로 줘도 적용된다.

```html
{{form.theme_color(class='input', **{'v-model':'selectedColor'}) }}
```



![image-20221206231352551](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221206231352551.png)

##### 최초 수정시 edit form에서 None으로 내려올때는 흰색을 초기값을 주도록 v-model변수를 초기화한다

```html
{% block vue_script %}
<script>
    app._data.selectedColor = "{{ form.theme_color.data or '#ffffff'}}"
</script>
{% endblock vue_script %}

```



- db값을 초기화해서 None이 내려오게 하고 살펴본다

  ![image-20221207010021616](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207010021616.png)

  ![image-20221207010912911](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207010912911.png)





##### 수정완료후 setting.html에 배경색으로 보이도록 html 수정하기

- 기존에는 그냥 미설정

  - 미설정 -> 배경 기본값 #ffffff  + 검은색 미설정 
  - 설정 -> 설정 배경값 + 흰색 색코드

  ![image-20221207011522012](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207011522012.png)



```html
<div class="column is-narrow">
    <span class="tag has-text-white-ter "
          style="background-color: {{ s_dict.get('theme_color') or '#ffffff' }}"
          >
        {% if s_dict.get('theme_color') %}
        {{s_dict.get('theme_color')}}
        {% else %}
        미설정
        {% endif %}

    </span>
</div>
```



##### 기존 color를 받는 form의 input은  수정form에서만 동적으로 숨기기 위해 `type='hidden'`을 주면 된다.

- 원본 type="input"이 덮어쓰여지는 것 같다

```html
{{form.theme_color(class='input', type='hidden', **{'v-model':'selectedColor'}) }}
```

![image-20221207012443751](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207012443751.png)





#### date picker

##### 마찬가지로 수정form에서 v-model -> base null 초기화 -> 수정form 변수초기화 



##### buefy의 b-datetpicker를 가져온 뒤 v-model을 사용한다

```html
<b-field>
    <b-datepicker
                  icon="calendar-today"
                  editable
                  v-model="date"
                  >
    </b-datepicker>
</b-field>
{{form.start_date(class='input')}}
```

![image-20221207111004078](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207111004078.png)

##### 렌더html에서 해당 변수를 수정form의 data로 초기화해준다. datepicker에는 js date객체로 넣어줘야한다.



- db string to front date

  ```html
  <script>
  
      // app._data.date = "{{ form.start_date.data}}"
      // db string to front date
      app._data.date = new Date("{{ form.start_date.data }}")
  </script>
  ```

  ![image-20221207093907298](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207093907298.png)

  `Thu Nov 03 2022 00:00:00 GMT+0900 (한국 표준시) <class 'str'>`



##### 참고) v-model 제한사항들

- v 컴포넌트에 **@change='메서드 변수"는 작동안함**
- **v-model변수에 | 필터** 정의 후 **적용 안됨**
- **watch안의 함수에서 | this.필터 적용안됨**



##### v-model을 사용하려면 base.html에 해당변수를 null로 초기화해서 쓰는데, date에는 특이한형태의 문자열date가 차있다. 이것을 다시 js date형태로 만든 뒤 stringDate(yyyy-mm-dd)로 만들어 쓰기 위해,  데이터 변환을 위해 stringDate변수  + 변환을 처리해줄 watch도 같이 정의한다

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            //...

            // admin/setting_form에서 쓰는 b-colorpicker, b-datepicker v-model 변수
            selectedColor: null,
            date: null,
            stringDate: null,
        },
        watch: {
            // 
            // admin/setting_form에서 쓰는 b-datepicker v-model date -> stringDate에 변환해서 채우도록 한다.
            date: function (date) {
                // console.log(date)
                //Tue Nov 15 2022 00:00:00 GMT+0900 (한국 표준시) // 이미 date가 아닌 상태로 온다..
                this.stringDate = this.convertDateYyyymmdd(date)
            },
        },
```

```js
methods: {
            // ...

            convertDateYyyymmdd(value) {
                // 들어오는 value 값이 공백이면 그냥 공백으로 돌려줌
                if (value == null) return null;

                // 현재 Date 혹은 DateTime 데이터를 javaScript date 타입화
                var js_date = new Date(value);

                // 연도, 월, 일 추출
                var dd = String(js_date.getDate()).padStart(2, '0');
                var mm = String(js_date.getMonth() + 1).padStart(2, '0'); //January is 0!
                var yyyy = js_date.getFullYear();
                return yyyy  + '-' + mm + '-' +dd;
            },
        },
```



##### 최초작성시 db null -> 빈문자열 new Date("") -> datepicker NaN을 처리해줄, jinja today_date  app_context에 추가 ( 호출다해서 넘기지말고 함수객체를 넘겨, jinja에서 호출하도록 해서 실시간 today를 생성)





- front date to db string

![image-20221207103154848](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207103154848.png)





- jinja에서는 그냥 오늘날짜를 바로 부를 순 없다



- default today string을 jinja에서 바로 사용할 수 없어서, app_context로 넣어준다

  ```python
  @app.context_processor
  def inject_today_date():
      return {'today_date': datetime.date.today} # 함수객체를 넘김
  ```

  ```html
  {% block vue_script %}
  <script>
      app._data.selectedColor = "{{ form.theme_color.data or '#ffffff'}}"
      // app._data.date = "{{ form.start_date.data}}"
      // db string to front date
      app._data.date = new Date("{{ form.start_date.data or today_date() }}")
  </script>
  {% endblock vue_script %}
  
  ```

  

  ![image-20221207110021695](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207110021695.png)

  ![image-20221207110038244](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207110038244.png)

  ![image-20221207110120619](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207110120619.png)

  



![image-20221207103413849](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207103413849.png)

![image-20221207103419897](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207103419897.png)





### 완성된 Setting정보를 app_context에 올려, 메뉴logo 및 footer에 반영하기

```python
# template context에서 전역사용할 menu객체를 dict로 반환하여 등록
#### app_menu & settings
@app.context_processor
def inject_category():
    with DBConnectionHandler() as db:
        stmt = (
            select(Category)
            .order_by(Category.id.asc())
        )

        categories = db.session.scalars(stmt).all()

        # site setings정보도 같이 올려준다
        settings = Setting.to_dict()

    return dict(
        categories=categories,
        settings=settings,
    )
```



#### logo 바꾸기 in base.html

```html
<!-- logo-->
<template #brand>
    <b-navbar-item>
        <!--  <img src="{{ url_for('static', filename='img/main/logo.png') }}" alt="logo">-->
        <img src="{{ url_for('download_file', filename=settings.logo) }}" alt="{{settings.site_name}}">
    </b-navbar-item>
</template>
```



![image-20221207112926363](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207112926363.png)

![image-20221207113127880](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207113127880.png)

![image-20221207113144401](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207113144401.png)





#### footer 바꾸기 in base.html



```html
{% block footer %}
<div class="footer has-background-black-ter is-marginless">
    <div class="has-text-centered has-text-grey-light">
        <div class="columns is-centered is-mobile is-multiline"
             style="border-bottom: #ededed solid 1px; padding-bottom: 1rem">
            <div class="column is-narrow is-half">

                <div class="columns has-text-centered">
                    <div class="column is-narrow is-half">
                        <h1 class="has-text-white is-size-5">콜센터 : {{settings.call_number}}</h1>
                    </div>
                    <div class="column is-narrow is-half">
                        <h1 class="has-text-white-ter is-size-5">{{settings.site_name}}</h1>
                    </div>
                </div>

                <div class="columns has-text-centered">
                    <div class="column is-narrow is-half">
                        <h1>{{settings.address}}</h1>
                    </div>
                    <div class="column is-narrow is-half">
                        <div>
                            사업자등록번호 {{settings.business_license_number}} {{settings.ceo}}
                        </div>
                    </div>
                </div>
            </div>

            <div class="column is-narrow is-half">
                footer
                <p class="help has-text-grey-light">
                    footer content
                </p>
            </div>
        </div>
        <h1 class="has-text-grey-light" href="">
            {{settings.copyright}}
        </h1>
    </div>
</div>

{% endblock footer %}
```

![image-20221207121033589](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207121033589.png)





#### font 색깔 정도를 제한적으로 바꾸기

- sass가 아니면 primary색 전체를 못바꾼다

- **jinja2 변수는 css, scss에서 사용안된다. -> `html style태그를 직접 만들어서 적용`해야한다**

  - **하나하나 요소를 찾아서 적용해야함**

  ![image-20221207165959618](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207165959618.png)

  ```html
  {% block extra_head_style %}
  <style>
      .navbar-item .is-primary, /* 닉네임 표시 or (회원가입)  */
      .navbar-start > a:hover,  /* 상단메뉴 hover  */
      .navbar-start > a.navbar-item.has-text-primary /* 상단메뉴 active  */
      {
          color: {{settings.theme_color}}!important;
      }
  </style>
  {% endblock extra_head_style %}
  ```

  ![image-20221207170027273](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207170027273.png)

  ![image-20221207171054117](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207171054117.png)





#### meta태그 적용하기

- **url + logo의 경로를 url_for로 가져올텐데, 앞에 `/`달고 시작한다**

```html
<head>
    <!-- settings -> meta태그 적용   -->
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
    <meta http-equiv="Content-Script-Type" content="text/javascript"/>
    <meta http-equiv="Content-Style-Type" content="text/css"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="viewport"
          content="width=device-width, initial-scale=0.3, minimum-scale=0.3, maximum-scale=2.0, user-scalable=yes"/>
    <!-- google meta -->
    <meta name="google-site-verification" content="{{settings.google_site_verification}}"/>
    <meta name="naver-site-verification" content={{settings.naver_site_verification}}/>
    <!-- 병원 meta -->
    <meta name="Description"
          content="{{settings.description}}"/>
    <meta name="Keywords"
          content="{{settings.keywords}}"/>
    <meta name="Copyright" content="{{settings.copyright}}"/>

    <meta property="og:title" content="{{settings.title}}"/>
    <meta property="og:description"
          content="{{settings.description}}"/>
    <meta property="og:url" content="{{settings.url}}"/>
    <meta property="og:image" content="{{settings.url}}{{url_for('download_file', filename=settings.logo)}}"/>
    <meta property="og:site-name" content="{{settings.site_name}}"/>


```

![image-20221207172901836](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221207172901836.png)