import datetime
import re

from flask import g
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize, FileRequired
from sqlalchemy import select, exists, and_
from wtforms import StringField, PasswordField, RadioField, EmailField, DateField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo, Regexp, Optional, InputRequired
from werkzeug.security import check_password_hash, generate_password_hash

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import User
from src.infra.tutorial3.auth.users import SexType, JobStatusType, Role, Employee, Roles
from src.main.utils import remove_empty_and_hyphen


class LoginForm(FlaskForm):
    # 받은 값을 추가처리하여 route에 건내줄 수 있다.
    # filters=(,)옵션에 함수객체를 튜플로 건네준다.
    #### 메서드명은 상관없으나 파라미터는 self없이 필드1개 고정이다.
    def qs_username(username):
        # u = file'{username}123'
        # print(u)
        return username

    username = StringField('username', validators=[
        DataRequired(message="필수 입력"),
        Length(max=32, message="최대 32글자까지 입력 가능")
    ], filters=(qs_username,))

    password = PasswordField('password', validators=[
        DataRequired(message="필수 입력"),
        Length(max=32, message="최대 32글자까지 입력 가능")
    ])

    # 로그인 실패에 대한 validator를 form내부에서 정의
    #### validate_필드명의 method명은 고정이다.
    #### self의 인스턴스메서드로 정의하면 작동안한다 파라미터도 self없이 (form, field) 2개로 고정이다.
    # -  field를 인자로 받아 field.data로 해당 데이터를 쓸 수 있다.
    # -  form.필드명.data로 다른 필드를 사용할 수도 있다.
    # - 넘어오지 않는 name의 필드는 사용할 수없다.
    # - html에서는 특정필드에 대한 에러 {% if form.username.errors %}로 뿌리므로
    #   => id필드에 대해 몰아서 검사하자.
    def validate_username(form, field):
        # with DBConnectionHandler() as db:
        #     # id를 모르니 select문으로
        #     user = db.session.scalars((
        #         select(User)
        #         .where(User.username == field.data)
        #     )).first()
        user = User.filter_by(username=field.data).first()

        if not user:
            raise ValidationError('해당 사용자가 존재하지 않습니다.')

        # elif not check_password_hash(user.password, form.password.data):
        elif not user.verify_password(form.password.data):
            raise ValidationError('비밀번호가 틀립니다.')


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=32, message="최대 2~32글자까지 입력 가능")
    ])

    email = EmailField("이메일", validators=[
        DataRequired(message="필수 입력"),
    ], )

    password = PasswordField('password', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=32, message="대 32글자까지 입력 가능！"),
        EqualTo('password1', message='비밀번호가 동일해야합니다.')
    ])

    password1 = PasswordField('password1')

    def validate_username(form, field):
        # with DBConnectionHandler() as db:
        #     stmt = exists().where(User.username == field.data).select()
        #     exists_user = db.session.scalars(
        #         stmt
        #     ).one()
        if User.filter_by(username=field.data).exists():
            raise ValidationError('이미 존재하는 username입니다')

    def validate_email(self, field):
        # condition = User.email == field.data
        #
        # with DBConnectionHandler() as db:
        #     is_exists = db.session.scalars(
        #         exists().where(condition).select()
        #     ).one()

        if User.filter_by(email=field.data).exists():
            raise ValidationError('이미 존재하는 email 입니다')


class UserInfoForm(FlaskForm):
    # 보여주기용 필드 추가
    username = StringField('Username', render_kw=dict(disabled=True))

    # emailfield를 이용하면 email형식을 자동으로 잡아준다.
    #### email은 필수필드로 변경
    email = EmailField("이메일",
                       validators=[DataRequired()],
                       # validators=[Optional()],
                       # filters=[lambda x: x or None]
                       )

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
    # nullable String은 -> filters를 걸어 "" 대신 None이 들어와야한다.
    address = StringField("주소", validators=[Optional()],
                          filters=[lambda x: x or None]
                          )

    phone = StringField("휴대폰", validators=[
        Regexp("^01\d{1}[ |-]?\d{4}[ |-]?\d{4}", message="01X로 시작하는 11자리 휴대폰번호를 입력해주세요. 하이픈(-) 사용유무는 선택입니다."),
        Optional()],
                        filters=(remove_empty_and_hyphen,),
                        description="[010 1234 1234], [01012341234], [011-1234-1234] 3가지 다 입력가능! 포함 숫자 11개만 주의!"
                        )

    # 수정form를(model과 같은 필드명으로 할당으로 채워지기) 위한  생성자 재정의
    # def __init__(self, user=None, *args, **kwargs):
    # def __init__(self, *args, **kwargs):
    #     self.user = g.user
    # 다시 수정 -> 직원form이 상속할 때, g.user를 수정할 유저로 들어가버리니,
    # user=None이 명시적으로 필요한 듯. 들어오는 user가 없을 때만, g.user현재유저로 취급
    def __init__(self, user=None, *args, **kwargs):
        # g.user의 특정user [직원전환]일 경우, 현재유저가 수정대상이 아닐 수 있다.
        # -> user=로 넘어오는 User객체를 수정용으로 우선 반영하여, [직원전환]에 대응
        if not user:
            self.user = g.user
        else:
            self.user = user
        if self.user:
            # super().__init__(**self.user.__dict__)
            super().__init__(**self.user.__dict__, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    #### null가능한 추가정보라서 uniquekey로 못넣고, 폼에서 존재유무 검사
    def validate_email(self, field):
        #### 추가정보는 데이터가 있을때만 하자.
        # if not field.data:
        #     return
        # print("옵셔널필드의 경우 입력안할시 validate_ 메서드를 타나?")

        if self.user:  # 수정시 자신의 제외하고 unique로 데이터 중복 검사
            # condition = and_(User.id != self.user.id, User.email == field.data)
            filter_data = dict(id__ne=self.user.id, email=field.data)
        else:  # 생성시 unique로 자신의 데이터를 중복검사
            # condition = User.email == field.data
            filter_data = dict(email=field.data)

        # with DBConnectionHandler() as db:
        #     is_exists = db.session.scalars(
        #         exists().where(condition).select()
        #     ).one()
        #
        # if is_exists:
        if User.filter_by(**filter_data).exists():
            raise ValidationError('이미 존재하는 email 입니다')

    def validate_phone(self, field):
        #### 추가정보는 데이터가 있을때만 하자. -> Optional인 경우 안타니까
        # if not field.data:
        #     return
        # print("옵셔널필드의 경우 입력안할시 validate_ 메서드를 타나?")

        # print(field.data, "<<< validate시 phone filters에 걸린 데이터가 넘어오나?")
        # 01046006243 <<< validate시 phone filters에 걸린 데이터가 넘어오나?
        # => 그렇다. validate에서는 filters를 거친 데이터가 들어온다.

        if self.user:  # 수정시 자신의 제외하고 데이터 중복 검사
            # condition = and_(User.id != self.user.id, User.phone == field.data)
            filter_data = dict(id__ne=self.user.id, phone=field.data)
        else:  # 생성시 자신의 데이터를 중복검사
            # condition = User.phone == field.data
            filter_data = dict(phone=field.data)

        # with DBConnectionHandler() as db:
        #     is_exists = db.session.scalars(
        #         exists().where(condition).select()
        #     ).one()
        #
        # if is_exists:
        if User.filter_by(**filter_data).exists():
            raise ValidationError('이미 존재하는 phone 입니다')


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
    # employee_form 수정시 rendering에러 => v-model로 인해, string이 채워진체로 form이 렌더링 될 시 문제가 된다.
    # => filter를 통해, 혹시 string이 form의 value에 들어가더라도, 필터링을 거친 value(date)로만 렌더링 되게 한다.
    # ---- datefield는 외부에서 값을 받을 땐, 자기고유 format yyyy-m-d 형식의  자기고유타입 string만 받더라. -->
    # ----  fix: forms.py에서 deafult로 date값이 들어가 -> date로 rendering OK-->
    # ----       view에서 stringDate를 넣어서 보내는 것 OK-->
    # ----  BUT  이미 DB에 date로 전달됬는데, watch -> v-model에 stringDate가 들어가 렌더링 => ERROR -->
    # ----   => forms.py에서 filter를 걸어주면, value에 string이 차있어도, filter를 거친 뒤, date로 채워 렌더링 된다?! -->
    def convert_to_date(date):
        if not isinstance(date, (datetime.datetime, datetime.date, datetime.time)):
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()
        return date

    join_date = DateField('입사일',
                          description='Will be stored as UTC',
                          # format='%Y-%m-%d %H:%M',
                          format='%Y-%m-%d',
                          # 이것은 wtf datepicker가 올려주는 형식과 동일해야해서 고정이다. 받는 것도 string만 받는다. 하지만 return는 filter없이도 date로 가져간다.
                          # default=datetime.datetime.now().date(),  # default는 vue에서 알아서 준다.
                          default=datetime.date.today(),  # default는 vue에서 알아서 준다.
                          filters=(convert_to_date,)  # 필수! 수정시 v-model에 string을 value에 채운체로 rendering되면 에러난다.
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
    def __init__(self, user,
                 role=None,  # 초대수락 or 직원전환시 -> 상사객체 OR 직원초대시, role객체 =>  role을 선택할 수 있거나 role을 미리 채운다
                 employee=None,  # 수정을 위한 미리생성된 user의 employee객체
                 *args, **kwargs):
        ## employee=가 있다면, 직원정보 수정/ 없다면 직원 생성
        ## role=이 있다면, 직원초대 수락으로 작성 / role이 없다면, employer의 직원전환
        # 1) employer가 직원전환을 강제로 하는 경우 self.employer + 자신의 롤 + 수정(or재입사)라면 employee
        # 2) role= 1개를 입력받아 -> 초대로 진원전환을 직접하는 경우 self.role +  수정(재입사)라면 employee
        self.employee = employee
        self.role = role
        # role=1개가 안주어져야, [employer]의 [직원전환]으로서 if self.employer에 g.user가 잡히고 그에 따른 role들이 반영
        self.employer = g.user if not role else None
        #### 수정(or재입사)인 경우
        if self.employee:
            # super().__init__(user, **self.employee.__dict__) => error
            ## 1) employee를 **kwargs로 보내주면, employee내부 user필드가 또 있어서, 겹치게 된다.
            # => user를 따로 보내주는 대신, employee내부.user를 부모form사용하도록 user보내주는 것을 막음.
            ## 2) 또한, 부모의 user속 '_sa_instance_state'와, employee속 '_sa_instance_state'도 겹치게 된다.
            # print(self.employee.serialize())
            # {'add_date': datetime.datetime(2022, 12, 21, 21, 50, 11, 114650), 'pub_date': datetime.datetime(2022, 12, 21, 21, 50, 11, 114650), 'id': 12, 'user_id': 37, 'name': '투자자', 'sub_name': '투자자', 'birth': '2010233349192', 'join_date': datetime.da
            # te(2022, 12, 21), 'job_status': <JobStatusType.재직: 1>, 'resign_date': None, 'user': User[id=37]}
            # print(self.employee.serialize())
            # super().__init__(user, **self.employee.to_dict(without_id=True))
            super().__init__(user, **self.employee.to_dict2(exclude=['add_date', 'pub_date', 'id']))
        # Employee 생성 상황이지만, 부모인 UserInfoForm은 수정상태다.
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

        # 1) employer=는 직접 [직원전환]버튼을 누른 상태로서, role을 해당 employer 범위안에서 결정한다
        if self.employer:
            # 직원전환하는 경우, STAFF이상 ~ 상사의 아래 단계 role들을 채운다.
            roles_under_employee = Role.filter_by(is_=Roles.STAFF, is_under=self.employer.role).all()
            # print('roles_under_employee  >> ', roles_under_employee)

            self.role_id.choices = [(role.id, role.name) for role in roles_under_employee]
            # with DBConnectionHandler() as db:
            #     #### 직원전환시 USER는 옵션에서 제외해야한다. -> 나보다는 낮지만,  STAFF이상으로 -> where. Role.is_STAFF 추가
            #     roles_under_employee = db.session.scalars(
            #         select(Role)
            #         .where(Role.is_under(self.employer.role))
            #         .where(Role.is_(Roles.STAFF))
            #     ).all()
            #     self.role_id.choices = [(role.id, role.name) for role in roles_under_employee]
            #     #### 자신이 들고있는 role은 기본값으로 줘놔야한다. 안그러면 select의 첫 값으로 잡힌다
            #     # self.role_id.data = user.role_id
            #     # self.role_id.name = user.role.name

        # 2) role=은 [직원초대]를 보낼 때 EmployeeInvite에 담긴 role_id => 해당role 1개만 지정되며 수정불가능하게 비활성화한다.
        elif self.role:
            #### select는 필드의 값을 미리 채울 때, .data가 아니라 .choices에 tuple1개 list를 1개만 넘기면 된다.
            # cf) view에서는 subfield.data, subfield.label로 쓰임
            self.role_id.choices = [(role.id, role.name)]
            # role의 choie를 1개만 배정해놓고, 더이상 수정 불가능하게 막아주자.
            self.role_id.render_kw = dict(disabled=True)
            # choice만 주면, 기존user정보로 필드의.data가 채워진 상태로, 보이기만  choices1개만 보여지게 된다.
            self.role_id.data = role.id

        #### 재입사시, 기존 직원들 정보로 미리 채우는 것 추가
        # => 여기서 채워버리니까, 직원정보 수정 -> form에 데이터를 입력해도 여기 입력 데이터를 backend로가져온다
        # =>
        # if self.user and self.user.has_employee_history:
        #     prev_emp: Employee = Employee.get_by_user_id(self.user.id)
        #     if not prev_emp:
        #         return
        #     self.name.data = prev_emp.name
        #     self.sub_name.data = prev_emp.sub_name
        #     self.birth.data = prev_emp.birth

    def validate_birth(self, field):
        # 수정시 자신의 제외하고 데이터 중복 검사
        if self.employee:
            #### 수정이 아닌, 재입사인 경우에도 이미 employee데이터가 존재하므로 같이 처리된다.
            # condition = and_(Employee.id != self.employee.id, Employee.birth == field.data)
            exists_conditions = dict(
                id__ne=self.employee.id,
                birth=field.data
            )
        # 생성시 자신의 데이터를 중복검사
        else:
            # condition = Employee.birth == field.data
            exists_conditions = dict(
                birth=field.data
            )

        # 재입사로서 self.user => Employee에 정보가 있을 경우, 해당 데이터 제외하고 검사
        # print(self.user, self.user.has_employee_history)
        # User[id=32] True
        # if self.user.has_employee_history:
        #     condition = and_(Employee.user_id != self.user.id, Employee.birth == field.data)

        # with DBConnectionHandler() as db:
        #     is_exists = db.session.scalar(
        #         exists().where(condition).select()
        #     )
        if Employee.filter_by(**exists_conditions).exists():
            raise ValidationError('이미 존재하는 주민등록번호 입니다')


class EmployeeInfoForm(FlaskForm):
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

    def __init__(self, employee=None, *args, **kwargs):

        self.employee = employee
        if self.employee:
            super().__init__(*args, **self.employee.__dict__, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def validate_birth(self, field):
        if self.employee:  # 수정시 자신의 제외하고 데이터 중복 검사
            # condition = and_(Employee.id != self.employee.id, Employee.birth == field.data)
            exists_conditions = dict(
                id__ne=self.employee.id,
                birth=field.data
            )
        else:  # 생성시 자신의 데이터를 중복검사
            # condition = Employee.birth == field.data
            exists_conditions = dict(
                birth=field.data
            )

        if Employee.filter_by(**exists_conditions).exists():
            raise ValidationError('이미 존재하는 주민등록번호 입니다')
