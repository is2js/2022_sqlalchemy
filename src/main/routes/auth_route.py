import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g, abort
from sqlalchemy import select, update, delete
from sqlalchemy.orm import contains_eager

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import User, EmployeeInvite, Role, Employee
from src.main.forms.auth import LoginForm, RegisterForm, UserInfoForm
from src.main.forms.auth.forms import EmployeeForm, EmployeeInfoForm
from src.main.utils import upload_file_path, delete_uploaded_file, redirect_url
from src.main.utils.decorators import login_required

auth_bp = Blueprint("auth", __name__, url_prefix='/auth')


@auth_bp.before_app_request
def load_logged_in_user():
    # 4) [권한처리1]: 관리자는 모든 url가능이지만, 일반사용자는 [@login_required]가 붙은 것 중 [승인된url만] 가도록 권한을 구현한다.
    # urls = [
    #     '/auth/',  # 일반사용자에게 @login_required 붙은 것 중 승인된 url
    #     '/auth/edit/',  # 일반사용자에게 auth.userinfo(id)의 url도 허용
    # ]
    # urls = ['/auth/', '/admin/user', '/admin/user/add'] # test

    # 1) login route를 들러왔으면, session에 user_id에 user존재유무 확인하면서 받은 user.id가 들어가있다
    # 2) 그것을 이용해 모든 app_request호출전마다 User객체를 불러와, g.user에 넣어준다.
    # 3) base.html admin/index.html 등에서 g.user 객체로 로그인 유무/ 로그인정보를 얻어온다.
    # login경험이 없으면, session.user_id는 존재하지 않으니, get으로 꺼낸다
    user_id = session.get('user_id')
    if not user_id:
        g.user = None
    else:
        with DBConnectionHandler() as db:
            g.user = db.session.get(User, user_id)
            # 1) 내부 db 세션으로 ping하고 -> 여기 db 세션으로 user를 배정하면 -> 세션 중복
            # 2) 여기 db 세션으로 g.user 배정 후, 해당 객체를 update한다고 접근하면 -> subquery 1회 이미 사용된 것으로 에러
            #  => g.user가 g.user가 g.user.role 등을 required를 처리할 때 db를 조회해야한다
            #  => last_seen업뎃은 g.user와 별개로 따로 해줘야한다.

        # g.user와 별개세션으로 로그인된 유저의 ping() -> last_seen 업뎃
        User.ping_by_id(user_id)

        #
        # # 5) [권한처리2]: 로그인된 유저들 중에서 [권한필드 -> 권한확인후 동적으로 .has_perm필드에 동적으로 권한부여]한다.
        # #    -> 값은 urls 목록의 url에 대한 액세스 권한이 있는지 확인하는 데 사용됩니다.
        # # 5-1) 활동 중 & 관리자는 권한 1(접속허용)을 동적으로 .has_perm에 부여한다.
        # if g.user.is_active and g.user.is_super_user:
        #     g.user.has_perm = 1
        # # 5-2) 활둥 중 & ban안당한 & 일반사용자 wnd & 승인된url인 /auth/를 달고 잇을때만 .has_perm에 부여한다
        # # -> 다른 url에 대해서는 1이 안들어가서 권한0이 들어갈 것이다.
        # elif g.user.is_active and not g.user.is_super_user and \
        #         not g.user.is_staff and  any(url in request.path for url in urls):
        #     g.user.has_perm = 1
        # # 5-3) 위 2가지 경우가 아니면, 해당 로그인한 유저(g.user)는 권한(.has_perm) 0을 가져, 접속이 안될 예정이다.
        # else:
        #     g.user.has_perm = 0
        #


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    ## wtforms 및 내부 validate도입으로 인해 주석처리
    # if request.method == 'POST':
    #     username = request.form.get('username')
    #     password = request.form.get('password')
    #
    #     with DBConnectionHandler() as db:
    #         user = db.session.scalars(
    #             select(User)
    #             .where(User.username == username)
    #         ).first()
    #     # 한번이라도 걸릴시 공통된 로직(not early return -> flag, flash+redirect) 탈락검사는 다끝난후 결과값 flag로 에러/성공 처리한다.
    #     error = None
    #
    #     # 1) 해당 유저가 조회안되면 로그인 탈락 검사1
    #     if not user:
    #         error = "해당 사용자가 존재하지 않습니다."
    #     # 2) (user는 존재) 해당 유저 비번 vs 넘어온 비번 다르면, 로그인 탈락 검사2
    #     elif not check_password_hash(user.password, password):
    #         error = "비밀번호가 다릅니다."
    #
    #     # 한번도 안걸리면 early return 있는 성공처리부터
    #     # -> 현재 user.id를 session에 담아주는 것이 로그인 처리
    #     if not error:
    #         session.clear()
    #         session['user_id'] = user.id
    #         return redirect('/')  # add rule 사용
    #     # (에러 한번이라도 걸려서 flag에 불들어온 경우) -> flash()만 내주고, 현재 로그인화면으로?
    #     flash(error)
    # return render_template('auth/login.html')

    ## 추가1) login route는 @login_required에 의해 올땐, 직전url을 querystring으로 담고 있으니 확인한다.
    redirect_to = request.args.get('redirect_to')

    ## wtf적용 -> form 내부 validate_xxxx로 로그인 탈락검사 넘김
    form = LoginForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            # id를 모르니 select문으로
            user = db.session.scalars((
                select(User)
                .where(User.username == form.username.data)
            )).first()

            # 이미 custom validator로 존재유무/비번검사가 끝났다고 가정
            # -> db속 user객체가 무조건 존재하는 상황
            session.clear()
            session['user_id'] = user.id

        ## 추가2) 직전url이 있다면 그곳으로 / (아니면) main으로로
        if redirect_to:
            return redirect(redirect_to)

        return redirect('/')

    return render_template('auth/login.html',
                           form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # if request.method == 'POST':
    #     username = request.form.get('username')
    #     password = request.form.get('password')
    #     password1 = request.form.get('password1')
    #
    #     # 1) 비밀번호 일치안하면 회원가입 탈락 검사1
    #     if password != password1:
    #         flash('비밀번호가 서로 다릅니다.')
    #         return redirect(url_for('auth.register'))
    #
    #     with DBConnectionHandler() as db:
    #         user = db.session.scalars(
    #             select(User)
    #             .where(User.username == username)
    #         ).first()
    #
    #     # 2) 이미 유저 존재시 회원가입 탈락 검사2
    #     if user:
    #         flash(f"해당 username{user}의 사용자가 이미 존재합니다.")
    #         return redirect(url_for('auth.register'))
    #
    #     # 3) (비번일치 & 유저안존재 상황) user 등록
    #     user = User(username=username, password=generate_password_hash(password))
    #     db.session.add(user)
    #     db.session.commit()
    #
    #     # 회원가입 성공시, 로그인처리를 위해 session['user_id']에 user객체의 id 등록
    #     session.clear()
    #     session['user_id'] = user.id
    #     return redirect(url_for('main.index'))
    # return render_template('auth/register.html')

    form = RegisterForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            # user = User(username=form.username.data, password=generate_password_hash(form.password.data))
            user = User(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.add(user)
            db.session.commit()

            session.clear()
            session['user_id'] = user.id

        # return redirect('/')
        #### 회원가입 완료시, userinf_edit로 가서, 추가정보 입력하게 하기
        return redirect(url_for('auth.userinfo_edit'))

    # form에서 필드별 error -> list로 만든다. 없으면 빈 list를 반환해서 순회안되게 한다
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('auth/register.html', form=form, errors=errors)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# @auth_bp.route('/')
# @login_required
# def userinfo():
#     # db정보가 아니라 g.user  객체에서 정보를 꺼내서 jinja로 표기하여
#     # db조회가 없다.
#     return render_template('auth/userinfo.html')


@auth_bp.route('/edit/', methods=['GET', 'POST'])
@login_required
def userinfo_edit():
    ## 현재 접속중인 유저 정보는 url id -> db에서 가져오는게 아니라, g.user에서 꺼내쓴다.
    # with DBConnectionHandler() as db:
    #     user = db.session.get(User, id)

    form = UserInfoForm(g.user)
    if form.validate_on_submit():
        ## 정보 수정시에는 g.user가 아닌, 해당g.user의 id로 찾는 user객체로
        with DBConnectionHandler() as db:
            user = db.session.get(User, g.user.id)
            # file관련 avatar 제외 다른 필드 없데이트
            # print(f"form.phone.data >> {form.phone.data}")
            # formfield가 옵셔널로 선택안한 경우, radio의 coerce=int 0, 나머지는 None으로 들어온다

            user.phone = form.phone.data
            user.sex = form.sex.data
            user.email = form.email.data
            user.address = form.address.data

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

            flash(f'{form.username.data}님 정보 수정 완료.')
            return redirect(url_for('auth.userinfo'))

    return render_template('auth/userinfo_form.html',
                           form=form)


@auth_bp.route('/')
@login_required
def userinfo():
    #### tab + tab별 html반환 route가 존재할 경우,
    #### 시작route는 tab에 대한 list를 미리 내려보내주자
    # => list pyecharts list를 건네주고 jinja | tojson => JSON.parse('{{ | tojson}}')활용
    # => 또는 json.dumps 활용
    # 필요한 내용은 바뀌는 끝url? 바뀌는 full url 를 dict list로
    # b-tabs를 구성하는 요소들로 명칭들을 짰다. : https://github.com/buefy/buefy/issues/122
    #  <b-tabs>
    #     <b-tab-item
    #         v-for="article in articles"
    #         :key="article.id"
    #         :label="article.name">
    #         {{article.description}}
    #     </b-tab-item>
    # </b-tabs>

    tab_list = [
        {
            'key': 1,
            'label': '기본 정보',
            'url': url_for('auth.userinfo_subpages', sub_path='userinfo_main'),
            'tabItemId': 'userinfo_main',
            'icon': 'account-outline',
        },
        {
            'key': 2,
            'label': '받은 초대',
            'url': url_for('auth.userinfo_subpages', sub_path='userinfo_invitee'),
            'tabItemId': 'userinfo_invitee',
            'icon': 'email-outline',
        },
    ]

    init_html = userinfo_subpages(sub_path=tab_list[0].get('tabItemId'))
    return render_template('auth/userinfo.html',
                           tab_list=tab_list,
                           # init_html=render_template('auth/userinfo_main.html'),
                           init_html=init_html,
                           )


@auth_bp.route('/userinfo/<path:sub_path>')
@login_required
def userinfo_subpages(sub_path):
    # 정적페이지면 바로 sub_path로 템플릿만 넘기면 되는데... sub_path들이 각각의 data를 필요로 할 것이다.
    data = {}
    if sub_path == 'userinfo_invitee':
        with DBConnectionHandler() as db:
            # emp_info_stmt = select(Employee).join(User)
            # subq = (
            #     emp_info_stmt
            # ).subquery()
            # print(emp_info_stmt)
            # print(db.session.scalars(emp_info_stmt).all())
            # SELECT anon_1.add_date, anon_1.pub_date, anon_1.id, anon_1.user_id, anon_1.name, anon_1.sub_name, anon_1.birth, anon_1.join_date, anon_1.job_status, anon_1.resign_date
            # FROM (SELECT employees.add_date AS add_date, employees.pub_date AS pub_date, employees.id AS id, employees.user_id AS user_id, employees.name AS name, employees.sub_name AS sub_name, employee
            # s.birth AS birth, employees.join_date AS join_date, employees.job_status AS job_status, employees.resign_date AS resign_date
            # FROM employees JOIN users ON users.id = employees.user_id) AS anon_1
            # print(db.session.scalars(subq).all())
            # [datetime.datetime(2022, 12, 15, 23, 54, 43, 409401), datetime.datetime(2022, 12, 16, 0, 0, 32, 298367), datetime.datetime(2022, 12, 16, 2, 58, 23, 283108), datetime.datetime(2022, 12, 16, 2,
            #  59, 10, 739363), datetime.datetime(2022, 12, 16, 3, 0, 17, 634098), datetime.datetime(2022, 12, 16, 13, 10, 20, 494766), datetime.datetime(2022, 12, 17, 2, 25, 7, 688872)]

            # stmt = (
            #     select(User)
            #     .join(User.employee)
            # )
            # for u in db.session.scalars(stmt):
            #     print(u.employee)
            #     print(u.employee.name) # one -> many인 u.employee의 필드에 접근하려면 uselist=False는 필수

            #### joinedload는 객체만 내부적으로채우지, where등의 필터를 적용할 수 없는 상태다? => where를 하려면, join + conatins_eager를 명시해서 entity를 채운다.?
            # https://stackoverflow.com/questions/47243397/sqlalchemy-joinedload-filter-column
            #### join + conains_eager를 쓰는 주entity에 모든 정보를 닮을 땐, 2detph이상이면, contains_eager( A.b, B.c)형태로 넣으면 된다ㅏ?
            # https://stackoverflow.com/questions/14414345/specifying-the-full-path-to-an-entity-with-inheritance-hierarchies-in-contains-e
            #### 나는, 주Entity에 lazy='subquery'없이 join된 내용을 담고 싶지만, invite.inviter(User)는 되지만,       inviter에 employee정보를 담을 때,  Invite.inviter.employee(X), User.employee(X)이라서
            # => 주entity에 Employee의 .name을 execute로 실행하여 따로 dict로 보내주지 않는 이상 안되서.. 걍 subquery + uselist=False로 사용하자.(REST가 아니기 때문)

            stmt = (
                # select(Invite, subq.c.name)
                select(EmployeeInvite)

                # select(Invite, Employee.name)
                # .join(Invite.inviter)
                # # .join(User, Invite.inviter_id == User.id)
                # .outerjoin(Employee, Invite.inviter_id == Employee.user_id)
                # # FROM invites JOIN users ON users.id = invites.inviter_id LEFT OUTER JOIN employees ON invites.inviter_id = employees.user_id
                # # WHERE :param_1 = invites.invitee_id
                # # [(<Invite 24=>35 >, None), (<Invite 20=>35 >, '123'), (<Invite 1=>35 >, None)]
                #
                # .options(
                #     contains_eager(Invite.inviter)
                #     .contains_eager(Invite.inviter.employee)
                # )

                # FROM invites LEFT OUTER JOIN users AS users_1 ON users_1.id = invites.inviter_id
                # WHERE :param_1 = invites.invitee_id
                # [<Invite 24=>35 >, <Invite 20=>35 >, <Invite 1=>35 >]
                # Parent instance <User at 0x1879a19a860> is not bound to a Session;
                # lazy load operation of attribute 'employee' cannot proceed

                .where(EmployeeInvite.invitee == g.user)
                # => join이 붙으면, 보다 늦게 일어난다. => 주체entity로 생각하지말고, join된 통합table(no releationship필드) 생각한다
                #     .where(EmployeeInvite.is_not_expired)
                .where(EmployeeInvite.is_valid)
                # .add_columns(Invite, Employee.name)

                #  [] 님의 가 도착했습니다. 21시간 전
                # [<Employee 8>] 님의 가 도착했습니다. 40분 전

                #### join을 아무리해도, 주entity 1개에 타고들어가는 거에 반영이 안됬다.(추가칼럼으로 붙는다 => orm을 이용하는게 더 좋다)
                #### 기존 T1의 where는 join이 붙는 순간, 다 join하고 where를 탄다. S F J W??
                # from 부터 볼 건데 join이 올 수 도 있다.
                # where로 조건을 줘서 어떤 범위들을 볼 지 조건으로 지정하고
                # group by로 그룹별로 묶어서 보고
                # having 그룹 중 어떤 그룹을 볼지 조건으로 지정하고
                # f(j)-w/g-h으로 만들어진 데이터 중 select으로 어떤 데이터만 골라서 볼 것이며
                # select이후 order by, limit으로 어떤 정렬로, 얼만큼 짤라 볼 것인지 지정한다

                #### 직원정보가 없는 admin 등도 초대할 수있기 때문에, Invite-inviter(User)에 <- Employee를 join해서 .name을 가져오는 것은 하지말자
                # .join(subq, Invite.inviter_id == subq.c.user_id)
                # OR .join_from(Invite, subq, Invite.inviter_id == subq.c.user_id)
                # [<Employee 8>] 님의 가 도착했습니다. 40분 전

                # (X) .join_from(User, Employee)# 결합안하고, User를 새로운 from절의 entity로인식한다
                #### 참고1) T2-T3로 T3정보를 얻기 위해 => T1.T2관계객체를 일단 join할 수 있고
                # employee 정보를 얻기위해, user정보를 관계객체로 join시켜본다 ( subquery관계라 바로 얻을 수도 있음)
                # .join(Invite.inviter) # JOIN users ON users.id = invites.inviter_id
                #  [] 님의 가 도착했습니다. 21시간 전
                # [<Employee 8>] 님의 가 도착했습니다. 40분 전

                # (X) Employee를 그냥 join시키면 교집합만 나오게 되어, left에 있던 직원정보없는 직원의 초대는 없어진다
                # .join(Employee) # JOIN employees ON users.id = employees.user_id
                # [<Employee 8>] 님의 가 도착했습니다. 40분 전

                #### 참고2) T2-T3로 T3정보를 얻기 위해 => T1.T2관계객체를 일단 join이후 T2-T3를 join할 수 있다.
                # .outerjoin(Employee) # LEFT OUTER JOIN employees ON users.id = employees.user_id  # join대상인 left Inviter-User 중에 employee가 아닌 사람도 허용된다
                #  [] 님의 가 도착했습니다. 21시간 전
                # [<Employee 8>] 님의 가 도착했습니다. 40분 전

                # .options(joinedload(Employee)) # Parent instance <User at 0x219ee485c50> is not bound to a Session; lazy load operation of attribute 'employee' cannot proceed
                # FROM invites
                # LEFT OUTER JOIN users AS users_1 ON users_1.id = invites.inviter_id
                # LEFT OUTER JOIN employees AS employees_1 ON users_1.id = employees_1.user_id

                # .join(Employee)
                # sqlalchemy.exc.InvalidRequestError: Don't know how to join to <Mapper at 0x1a651021470; Employee>. Please use the .select_from() method to establish an explicit left side, as well as providing an explicit ON clause if not present already to help resolve the ambiguity.

                # .select_from(User).join(User.employee)
                # SELECT invites.id, invites.type, invites.inviter_id, invites.invitee_id, invites.is_answered, invites.is_accepted, invites.create_on, invites.key
                # FROM invites, users JOIN employees ON users.id = employees.user_id
                # WHERE :param_1 = invites.invitee_id
                #  SAWarning: SELECT statement has a cartesian product between FROM element(s) "invites" and FROM element "employe
                # es".  Apply join condition(s) between each element to resolve.
                # .join(subq )
                # Please use the .select_from() method to establish an explicit left
                # side, as well as providing an explicit ON clause if not present already to help resolve the ambiguity.
                # .select_from(Invite)
                # .join(subq, Invite.inviter_id == subq.c.user_id)
            )
            # invite.inviter.employee

            # print(stmt)

            # data['invite_list'] = db.session.execute(stmt).all()
            data['invite_list'] = db.session.scalars(stmt).all()
            # for x in data['invite_list']:
            #     print(x.is_not_expired)

            # print(data['invite_list'])
            # print(data['invite_list'][1])
            # print(data['invite_list'][1].inviter.employee)
            # <Invite 20=>35 >
            # [<Employee 8>]
            # print(data['invite_list'][1].inviter.employee.name)
            ## 쿼리에 employee까지 join시켜놔도, Inviter -> User -> Employee객체의 필드까지는 못들어간다
            # AttributeError: 'InstrumentedList' object has no attribute 'name'

            # print(data['invite_list'][1].inviter.employee.__dict__)

    if sub_path == 'userinfo_invitee':
        data['invite_list'] = EmployeeInvite.get_by_invitee(g.user)
    return render_template(f'auth/{sub_path}.html', **data)


@auth_bp.route('/invite/invitee/')
@login_required
def invite_invitee():
    invite_list = EmployeeInvite.get_by_invitee(g.user)

    return render_template('auth/userinfo_invitee.html', invite_list=invite_list)


# 최근방문시간 -> model ping메서드 -> auth route에서 before_app_request에 로그인시 메서드호출하면서 수정하도록 변경
# 방문할 때마다 최근 방문시간을 갱신한다.
# @auth_bp.before_app_request
# def before_request():
#     # user_id = session.get('user_id')
#     # User.ping_by_id(user_id)
#     pass


@auth_bp.route('/invite/employee/accept/<int:id>/', methods=['GET', 'POST'])
@login_required
def employee_invite_accept(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)
        # 1) 수락했으면, [해당 invite]에서 invitee와, role을 가져와 수정한다
        #  => 모든 정보가 입력되면 is_answered된 상태 & is_accepted 처리까지 해줘야한다.
        # invite.is_answered = True
        # invite.is_accepted = True
        # db.session.add(invite)

        # 2) 수락했으면, invitee인 [User]의 기본정보를 위해  user객체를 구해온다
        invitee_user = db.session.get(User, invite.invitee_id)
        # 3) 수락했으면, invter 정보 대신 role_id로 해당 [Role]을 배정해줘야한다
        role = db.session.get(Role, invite.role_id)

        form = EmployeeForm(invitee_user, role=role)

    if form.validate_on_submit():
        is_re_join = False
        #### Employ정보를 생성하기 전에, 퇴사후 재입사인 경우 user:emp 1:1관계를 유지하기 위해
        #### => 기존  employee정보를 검색해서 있으면 삭제해준다
        with DBConnectionHandler() as db:
            # 1) invite id -> invite -> invitee_id 값 찾기
            user_id_scalar = (
                select(EmployeeInvite.invitee_id)
                .where(EmployeeInvite.id == id)
            ).scalar_subquery()
            # 2) invite_id값과 user_id가 일치하는 Employee데이터 조회하기
            stmt = (
                select(Employee)
                .where(Employee.user_id ==
                       user_id_scalar
                       )
            )
            # SELECT employees.add_date, employees.pub_date, employees.id, employees.user_id, employees.name, employees.sub_name, employees.birth, employees.join_date, employees.job_status, employees.resign_date
            # FROM employees
            # WHERE employees.user_id = (SELECT employee_invites.invitee_id AS user_id
            #                               FROM employee_invites
            #                               WHERE employee_invites.id = :id_1)
            prev_employee = db.session.scalars(
                stmt
            ).first()
            # print(stmt)
            # print(prev_employee)
            if prev_employee:
                # print("기존 입사정보가 있어서, 삭제하고 재입사 처리합니다.")
                is_re_join = True
                db.session.delete(prev_employee)
                db.session.commit()
            else:
                # print("기존 입사정보 없이, 신규입사입니다.")
                pass

        with DBConnectionHandler() as db:
            invite = db.session.get(EmployeeInvite, id)
            invitee_user = db.session.get(User, invite.invitee_id)
            #### user ####
            user_info = {
                'email': form.email.data,
                'sex': form.sex.data,
                'phone': form.phone.data,
                'address': form.address.data,
                'role_id': form.role_id.data,
            }
            invitee_user.update(user_info)
            f = form.avatar.data
            if f != invitee_user.avatar:
                avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
                f.save(avatar_path)
                delete_uploaded_file(directory_and_filename=invitee_user.avatar)
                invitee_user.avatar = f'avatar/{filename}'

            #### employee ####
            # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
            employee = Employee(
                user=invitee_user,
                name=form.name.data,
                sub_name=form.sub_name.data,
                birth=form.birth.data,
                join_date=form.join_date.data,
                job_status=form.job_status.data,
            )

            # Employee검사에서 재입사면, nullable인 reference 비고필드를 채워준다.
            if is_re_join:
                employee.reference = '재입사'
            else:
                employee.reference = '신규입사'

            #### invite ####
            invite.is_answered = True
            invite.is_accepted = True

            db.session.add(invite)

            db.session.add(invitee_user)
            db.session.add(employee)
            #### invite 처리####
            db.session.commit()

        #### 나머지 초대들 삭제처리하기
        with DBConnectionHandler() as db:
            invite1 = db.session.get(EmployeeInvite, id)
            invitee_user1 = db.session.get(User, invite1.invitee_id)

            #### 수락한 초대를 제외한, 나에게 보낸 [다른 직원초대들 일괄 거절 + 응답] 처리
            stmt = (
                update(EmployeeInvite)
                .where(EmployeeInvite.id != id)  # 현재 초대를 제외한
                # .where(EmployeeInvite.is_not_expired)  # 아직 유효한 것들 중
                .where(EmployeeInvite.is_valid)  # 아직 유효한 것들 중
                .where(EmployeeInvite.invitee == invitee_user1)  # 나에게 보낸 직원초대들
                .values({EmployeeInvite.is_accepted: False, EmployeeInvite.is_answered: True})
            )
            # print(stmt)
            # UPDATE employee_invites SET is_answered=:is_answered, is_accepted=:is_accepted WHERE employee_invites.id != :id_1 AND employee_invites.create_on >= :create_on_1 AND :param_1 = employee_invites.invitee_id

            db.session.execute(stmt)
            db.session.commit()
            flash("직원 전환 성공")

        return redirect(url_for('auth.userinfo'))

    return render_template('auth/employee_invite_accept_form.html',
                           form=form)


@auth_bp.route('/invite/employee/reject/<int:id>/', methods=['POST'])
@login_required
def employee_invite_reject(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)

        invite.is_answered = True
        invite.is_accepted = False

        db.session.add(invite)
        db.session.commit()

        flash("초대를 거절했습니다.", category='is-danger')

        return redirect(redirect_url())


@auth_bp.route('/invite/employee/postpone/<int:id>/', methods=['POST'])
@login_required
def employee_invite_postpone(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)

        invite.create_on = invite.create_on + datetime.timedelta(days=EmployeeInvite._INVITE_EXPIRE_DAYS)

        db.session.add(invite)
        db.session.commit()

        flash(f"초대를 {EmployeeInvite._INVITE_EXPIRE_DAYS}일 연기했습니다.", category='is-info')

        return redirect(redirect_url())


@auth_bp.route('/employeeinfo/')
@login_required
def employeeinfo():
    with DBConnectionHandler() as db:

        stmt = (
            select(Employee)
            .where(Employee.is_active == True)
            .where(Employee.user_id == g.user.id)
        )

        # jinja2.exceptions.UndefinedError: 'None' has no attribute 'user'
        #### user정보가 없는 employee가 있다? 일단 admin으로 접속하면, 기본user정보가 없다?

        employee = db.session.scalars(stmt).first()

        if not employee:
            return "active 직원 정보가 없습니다."

        # print(g.user.id)
        # print(employee.user_id)
        # print(employee)
    return render_template('auth/userinfo_employeeinfo.html',
                           employee=employee
                           )


@auth_bp.route('/employeeinfo/edit/', methods=['GET', 'POST'])
@login_required
def employeeinfo_edit():
    with DBConnectionHandler() as db:
        stmt = (
            select(Employee)
            .where(Employee.user_id == g.user.id)
        )

        employee = db.session.scalars(stmt).first()


        form = EmployeeInfoForm(employee=employee)

    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            stmt = (
                select(Employee)
                .where(Employee.user_id == g.user.id)
            )

            employee = db.session.scalars(stmt).first()
            employee.name = form.name.data
            employee.sub_name = form.sub_name.data
            employee.birth = form.birth.data

            db.session.add(employee)
            db.session.commit()

            flash('직원 정보 수정 성공', category='is-success')



    return render_template('auth/userinfo_employeeinfo_form.html',
                           form=form)
