from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize, FileRequired
from sqlalchemy import exists, and_, select
from wtforms import StringField, TextAreaField, RadioField, SelectField, SelectMultipleField, PasswordField, \
    BooleanField, URLField, EmailField
from wtforms.validators import DataRequired, Length, ValidationError, URL
from wtforms.widgets import PasswordInput

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Category, PostPublishType, Tag, User, BannerType, Role, Roles


class CategoryForm(FlaskForm):
    name = StringField('카테고리 이름', validators=[
        DataRequired(message='필수 입력'),
        Length(max=128, message='최대 128 글자까지 입력 가능')
    ])
    icon = StringField('icon', validators=[
        Length(max=128, message='최대 128 글자까지 입력 가능')
    ])

    # 1) 생성자를 오버라이딩하여, (form필드 추가도 가능) edit에서 사용되는지 여부 -> id= keyword로 객체로 받기
    # => editform으로서 category=가 객체.id로 들어온다면, self.id필드에 보관하기
    # 2차)
    def __init__(self, category=None, *args, **kwargs):
        # 2-3) 밸리데이션 검사를 위해, 없을 때도 필드가 존재해야 validate 메서드에서 검사한다.
        #    + form필드를 개설하는게 아니므로, 자동으로 안채워져서 직접 넣어줘야한다.
        # self.id = category.id if category else None
        self.category = category

        if self.category:
            # 2-1) 객체가 넘어와서, 가 필드들을 dict로 만들어, **로 keyword인자로 ㅁ나들어서 넘겨준다
            # => 이 때, category.id를 self.id에 주입못한다. self.id는 FormField가 아니라서 자동으로 안채워진다.
            super().__init__(**self.category.__dict__)
        else:
            # 2-2) init 재정의를 한다면, 반드시 부모 것을 초기화해줘야 기본사용 가능하다.
            super().__init__(*args, **kwargs)

    def validate_name(self, field):
        # 2) id가 들어오면 edit form으로 인식해서, db 존재검사를 [나를 제외한 db 존재 검사]
        # if self.id:
        if self.category:
            ## filter조건으로 Category != self.category로 비교하면 조건으로 안들어간다. sqlalchemy의 where에는
            ## 객체비교가 아닌 필드로 명시해줘야한다.
            condition = and_(Category.id != self.category.id, Category.name == field.data)
        # 3) 객체가 들어오는 editform이 아니라 생성form일 때는, 기존 생성form으로서 [db전체 존재유무 검사]
        else:
            condition = Category.name == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 Category name입니다')


class PostForm(FlaskForm):
    title = StringField('제목', validators=[
        DataRequired(message="필수 입력"),
        Length(max=128, message="최대 128 글자까지 입력 가능")
    ])

    desc = StringField('설명', validators=[
        DataRequired(message="필수 입력"),
        Length(max=200, message="최대 200 글자까지 입력 가능")
    ])

    content = TextAreaField('내용', validators=[
        DataRequired(message="필수 입력")
    ])

    has_type = RadioField('Post status',
                          choices=PostPublishType.choices(),
                          # choces에는 (subfield.data, subfield.label)로 될 값이 같이 내려가지만,defautld에는 .data가 되는 값 1개만 넘겨줘야한다.
                          default=PostPublishType.SHOW.value,
                          coerce=int,
                          )

    category_id = SelectField(
        '카테고리',
        choices=None,
        coerce=int,
        validators=[
            DataRequired(message="필수 입력"),
        ]
    )

    tags = SelectMultipleField('태그', choices=None, coerce=int)

    def __init__(self, post=None, *args, **kwargs):
        # 1) post를 self.post로 받아주고, 기존 code들을 post가 없는 상황 == 생성form으로 else에 처리한다.
        self.post = post
        # 2) category와 달리, **self.post.__dict__로 넣어주면 안된다. 객체가 value가 아닌 타테이블의 객체 or enum을 물고 있는 경우 직접 넣어줘야한다
        # => category와 달리, edit를 객체로 초기화 하는 대신, 공통 초기화를 일단 해주고, 개별로 채워줘야한다.

        # 1-1) edit form
        if self.post:
            # 3) 가진fk객체는 부모객체.id를 / 가진enum은.value를/ 가진 tags객체list는  id list로 변환해서 대입한다.
            # => self.title은 FormField라서 직접 대입하면 안되고, 생성자를 통해서 keyword로 대입해야한다.
            # self.title = self.post.title
            info = dict(
                title=self.post.title,
                desc=self.post.desc,
                content=self.post.content,

                # has_type=self.post.has_type.value,
                # has_type=self.post.has_type.name,
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


class TagForm(FlaskForm):
    name = StringField('name', validators=[
        DataRequired(message='필수 입력.'),
        Length(max=128, message="최대 200 글자까지 입력 가능")
    ])

    # 1) 수정시 재활용을 위해, form채울 객체를 받는 생성자를 재정의한다.
    def __init__(self, tag=None, *args, **kwargs):
        self.tag = tag
        if self.tag:
            # 2) post와 다대다이면서 .posts를 backref로 받지만,
            #    2-1) tag생성시, tag.posts 정보가 필요없으며 &
            #    2-2-) tag수정시, 관계칼럼의 fk입력 관계객체필드<->form입력은 관계객체.id로 달라질 일이 없으므로
            #    category처럼, 객체가 raw값들만 가지는 경우,
            #    => ** + 객체.__dict__로  바로 객체정보를 form에 keyword로 입력시킬 수 있다.
            super().__init__(**self.tag.__dict__)
        else:
            super().__init__(*args, **kwargs)

    # 3) category처럼, 생성시 name중복검사 <-> 수정시 자신제외 name중복검사를 해야한다.
    def validate_name(self, field):
        if self.tag:  # 수정시
            condition = and_(Tag.id != self.tag.id, Tag.name == field.data)
        else:  # 생성시
            condition = Tag.name == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 Tag name입니다')


# auth/forms.py의 registerform과는 다르게, default로 주는 혹은 admin이 주는 설정들을 다 가지고 있다.
class CreateUserForm(FlaskForm):
    username = StringField('username', validators=[
        DataRequired(message="필수 입력"),
        Length(max=32, message="최대 32글자 입력 가능！")
    ])

    password = PasswordField('password', validators=[
        # DataRequired(message="필수입력"),
        Length(max=32, message="최대 32글자 입력 가능！")
    ], description="빈칸으로 두는 경우, 수정하지 않습니다！")

    email = EmailField("이메일", validators=[
        DataRequired(message="필수 입력"),
    ], )

    ## admin에서 생성시 or Register 후 -> 수정시 추가하는 필드
    #### admin의 form(생성, 수정 둘다)에서만 role역할부여 (생성자에서 choices를 채움)
    # -> fk라 form오 _id 형식으로 잡음.
    # role_id = SelectField(
    #     '역할',
    #     choices=None,
    #     coerce=int,
    #     validators=[
    #     ],
    # )
    #### role부여는 순수User 추가시에는 제거하기

    is_super_user = BooleanField("관리자여부")
    is_active = BooleanField("활동여부", default=True)  # 생성시에는 데이터가 없지만 체크될 수 있게 만들어놓는다.
    is_staff = BooleanField("Ban여부")

    avatar = FileField("avatar", validators=[
        # FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'bmp', 'png', 'gif'], message="jpg/jpeg/bmp/png/gif 형식만 지원합니다"),
        FileSize(max_size=2048000, message="2M 이하의 파일만 업로드 가능합니다")],
                       description="파일크기가 2M이하만 지원합니다. 또한, jpg/jpeg/bmp/png/gif 형식만 지원합니다，빈칸으로 두는 경우, 수정하지 않습니다！")

    # 수정form를 위한  생성자 재정의
    # def __init__(self, user=None, *args, **kwargs):
    #### [ROLE1] role 추가 밑, 현재유저보다 낮은 role을 부여하도록 choices에서 필터링하기 위해
    ## - 외부 g.user -> 내부 current_user를 받는다.
    # def __init__(self, current_user, user=None, *args, **kwargs):
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        # 수정시
        if self.user:
            # 따로 변형된 값(with 다른entity객체->.id) 등이 필요없으므로 바로 dict -> keyword로 만들어서 넣어준다.
            super().__init__(**self.user.__dict__)
            # 추가) 수정일땐, username변경 못하게 disabled 속성 주기
            self.username.render_kw = dict(disabled=True)
            # passwordfield는 내부 InputWidget의 hidden_value=True로 어차피 못채운다.
        else:
            super().__init__(*args, **kwargs)

        # with DBConnectionHandler() as db:
            # roles = db.session.scalars(select(Role)).all()
            # self.role_id.choices = [(role.id, role.name) for role in roles if role.name != Roles.ADMINISTRATOR.name]
            #### [ROLE2] 입력받은 현재유저의 role보다 낮은 것을 준다.
            # roles_under_current_user = db.session.scalars(
            #     select(Role)
            #     .where(Role.is_less_than(current_user.role))
                # .where(Role.permissions < current_user.role.permissions)
            # ).all()

            # self.role_id.choices = [(role.id, role.name) for role in roles_under_current_user]

    def validate_username(self, field):
        if self.user:  # 수정시
            condition = and_(User.id != self.user.id, User.username == field.data)
        else:  # 생성시
            condition = User.username == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 User name입니다')

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


class BannerForm(FlaskForm):
    img = FileField("Banner", validators=[
        ## 수정시에는 파일경로만 form에 담겨와서, 그대로가기 때문에, file이 없어도 허용해야한다.
        ## -> 만약, fileRequired 대신 validate_img로 생성시에만 필수로 해준다.
        # FileRequired(message="배너는 그림이 필수 입니다."),
        FileAllowed(['jpg', 'jpeg', 'bmp', 'png', 'gif'], message="jpg/jpeg/bmp/png/gif 형식만 지원합니다"),
        FileSize(max_size=3 * 1024 * 1000, message="3M 이하의 파일만 업로드 가능합니다")],
                    description="파일크기가 3M이하만 지원합니다. 또한, jpg/jpeg/bmp/png/gif 형식만 지원합니다，빈칸으로 두는 경우, 수정하지 않습니다！ 비율은 16:9을(1920x1080) 권장합니다")

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
