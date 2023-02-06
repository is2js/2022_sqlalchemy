### 권한처리(auth_route)

#### load_logged_in_user(@auth_bp.before_app_request)

##### 매 요청마다 확인하는 load_logged_in_user에서 로그인한 g.user에게 동적 필드로 권한부여

- 로그인한 유저 g.user객체에 **동적으로 권한필드를 매번 부여하며, 해당url에 접근할 수 있는지 없는지를 판단한다** 
  - 4) ~ 5) 
  - 권한처리1~2

```python
@auth_bp.before_app_request
def load_logged_in_user():
    # 4) [권한처리1]: 관리자는 모든 url가능이지만, 일반사용자는 [@login_required]가 붙은 것 중 [승인된url만] 가도록 권한을 구현한다.
    urls = ['/auth/'] # 일반사용자에게 @login_required 붙은 것 중 승인된 url

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

        # 5) [권한처리2]: 로그인된 유저들 중에서 [권한필드 -> 권한확인후 동적으로 .has_perm필드에 동적으로 권한부여]한다.
        #    -> 값은 urls 목록의 url에 대한 액세스 권한이 있는지 확인하는 데 사용됩니다.
        # 5-1) 활동 중 & 관리자는 권한 1(접속허용)을 동적으로 .has_perm에 부여한다.
        if g.user.is_active and g.user.is_super_user:
            g.user.has_perm = 1
        # 5-2) 활둥 중 & ban안당한 & 일반사용자 wnd & 승인된url인 /auth/를 달고 잇을때만 .has_perm에 부여한다
        # -> 다른 url에 대해서는 1이 안들어가서 권한0이 들어갈 것이다.
        elif g.user.is_active and not g.user.is_staff and \
                not g.user.is_super_user and request.path in urls:
            g.user.has_perm = 1
        # 5-3) 위 2가지 경우가 아니면, 해당 로그인한 유저(g.user)는 권한(.has_perm) 0을 가져, 접속이 안될 예정이다.
        else:
            g.user.has_perm = 0
```

##### 사실상 load_logged_user는 g.user에 객체획득 + 권한부여까지 하는 역할



#### login_required

##### route접근시마다 g.user.has_perm에 권한이 결정된 상태(load_logged_user)에서, @login_required 데코레이터를 타서 권한이 없으면, 대기중인 view_func실행대신, 권한없음 문자열을 반환한다.

- 추가2)
- 권한처리3

```python
def login_required(view_func):
    @functools.wraps(view_func)
    def wrapped_view(**kwargs):
        if not g.user:
            # return redirect(url_for('auth.login'))
            # 추가1) login이 필요한 곳에 로그인 안한상태로 접속시, request.path를 이용해, redirect 전 현재요청url을 쿼리스트링으로 기억
            redirect_to = f"{url_for('auth.login')}?redirect_to={request.path}"
            return redirect(redirect_to)
        # return view_func(**kwargs)
        # 추가2) [권한처리3] logged_user이후 로그인요구route를 탈 때, 로그인되어있으면 바로 view_func을 타러갔었으나
        # -> 로그인된 유저라도 권한을 확인하고 view_func으로 갈지 vs route없이 바로 권한없음을 반환할지로 나뉜다.
        # -> 외부에서 데코wrapper함수를 실행하면, 문자열만 나와서 반환될 것이다?!
        if g.user.has_perm:
            return view_func(**kwargs)
        else:
            return '<h1> 권한이 없습니다 </h1>'
    return wrapped_view

```

#### test

1. 관리자가 아닌 유저를 생성

   ![image-20221125172345115](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125172345115.png)

   ![image-20221125172351426](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125172351426.png)

2. **일반유저는 허용된 urls가 아니면 권한이 0으로 먹어서 접속이 안될 것이다.**

   - user로 로그인해서 admin에 들어가보자

     ![image-20221125172708987](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125172708987.png)

     - g.user는 획득했지만
     - **@login_required가 아닌 곳은 편하게 접근 가능(main_route)**
     - 활동중 & 밴안당함 & 일반사용자 중 &**request.path in urls**가 **아니라서**
       - **logged_user에서 .has_perm을 0을 부여**받아
       - **login_required**에서 route못들어가고 **빠꾸**당한다

   ##### 사실상 @login_required는  로그인(g.user) + /auth/ (일반 승인urls)외 super_user required가 된 것



3. **다시 user의 권한을 super로 바꾸고 admin에 접근해본다**

   1. admin으로 접속해서 user관리에서 super처리

      ![image-20221125173927831](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125173927831.png)
      ![image-20221125174002861](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125174002861.png)

   2. user로 접속해서 admin 다시 접속



#### test2: 일반유전데 허용된url에서만 동적 .has_perm  = 1로 route타기 가능 test

3. **다시 super유저를 풀지고  + `허용된 urls`을 추가해서 `일반사용자이면서 허용된 url`에 접속해보기**

   1. 나 super 자신을 풀기

      ![image-20221125175210607](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125175210607.png)

   2. 허용된 url에 `/admin/user` 추가하기

      ```python
      urls = ['/auth/', '/admin/user'] # test
      ```

      - **일반사용자라도, 허용url에 대해서는 .has_perm을 1을 동적으로 부여받는다**

        ![image-20221125175322048](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125175322048.png)

   3. /admin/에 접속시는 권한없음

      ![image-20221125175452101](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125175452101.png)

   4. 허용된 url인 `/admin/user/`에 대해서는 허용됨

      ![image-20221125175519277](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125175519277.png)



##### 응용하면, `활동중 & 직원 & not 관리자`직원에 대해서는 `직원허용url`에서 .has_perm을 1을 받게 만들면, 될 듯. 대신 시작url/ add/edit/delete까지 다 허용해줘야한다?!

- 대신 허용 url을 /admin/user 부터 **/admin/user/add**의 action route들도 다 접속허용해줘야한다

  ![image-20221125175637451](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125175637451.png)



- /admin/user   +  /admin/user/add 까지 허용해주면, user생성이 가능해진다.

  ```python
  urls = ['/auth/', '/admin/user', '/admin/user/add'] # test
  ```

  

  ![image-20221125175906155](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125175906155.png)








### UserInfo

#### auth.userinfo route (/auth/ -> 일반사용자 허용 urls에 포함)

- **어차피 현재유저의 정보는 `front의 g.user`로 처리할 것이기 때문에 html만 렌더링**
  - Userentity를불러오는 작업이 없다
- **auth의 `/` url을 가진다**

```python
@auth_bp.route('/')
@login_required
def userinfo():
    return render_template('auth/userinfo.html')
```



#### auth / userinfo.html 

- admin/index.html를 상속하여 어드민 모양을 내면서
  - **menus block을 새로 채워 왼쪽메뉴를** admin이 아닌 **일반사용자용으로 구성**
- **upload폴더 접근시 src='/uploads'로 하지말고, `url_for('download_file', filename=)`으로 구성하여, 설정된 UPLOAD_FOLDER에 의지하게 한다**

##### front 56_userinfo_extends_admin_index_after_userinfo_route.html

```html
{% extends 'admin/index.html' %}

<!-- admin/index.html 중 왼쪽칼럼2개짜리 메뉴의 실제 aside태그부분-->
{% block menus %}
<aside class="menu">
    <p class="menu-label">
        User 설정
    </p>
    <ul class="menu-list">
        <li><a class="{% if request.path == '/auth/' %}is-active{% endif %}"
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
    <b-tabs>
        <!-- 탭1 내 정보 -->
        <b-tab-item label="내 정보" icon="account-outline">
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px; padding-bottom: 1rem">
                <div class="column is-narrow">
                    <figure class="image is-96x96">
                        <img class="is-rounded" style="height: 100%;" src="{{ url_for('download_file', filename=g.user['avatar']) }}">
                    </figure>
                </div>
                <div class="column is-narrow">
                    <div style="padding-top: 1.5rem;">
                        <h1 class="title is-size-4">{{ g.user['username'] }}</h1>
                        <p class="subtitle is-size-6">등급: {{ '관리자' if g.user.is_super_user else '일반'}}</p>
                    </div>
                </div>
                <div class="column is-narrow-mobile">
                    <a class=" button is-light is-pulled-right" href="" style="margin-top: 1.8rem">정보 수정</a>
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
                            <span class=" has-text-black-ter">sex field 개발 중.</span>
                        </div>

                    </div>
                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">이메일</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">email field 개발 중.</span>
                        </div>

                    </div>

                    <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                        <div class="column is-2">
                            <span class=" has-text-grey-light">주소</span>
                        </div>
                        <div class="column is-narrow">
                            <span class=" has-text-black-ter">address field 개발 중.</span>
                        </div>

                    </div>
                </div>
            </div>

            <div class="columns" style="padding:1rem 0; ">
                <div class="column is-2">
                    <p>인사말</p>
                </div>
                <div class="column">
                    <div class="content">

                        인사말 field 개발 중.

                    </div>
                </div>
            </div>
        </b-tab-item>
        <!-- 탭1 끝 -->

    </b-tabs>
</template>
{% endblock member %}
```

- `localhost:5000/auth`+`/`

![image-20221125232319178](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125232319178.png)



##### 중간) view에 있던 src='/uploads/ 개별폴더+파일명 from 객체.경로필드'  를  모두 url_for('download_file', filename='')으로 변경

- 그래야 view_func에 있는 upload경로를 그대로 타고가서, 경로가 바뀌더라도 알아서 인식될 것이다.

- `app.py upload route`

  ```python
  f.save(upload_path)
  # print(url_for('download_file', filename=f'{directory_name}/{filename}'))
  # /uploads/post/862e406dd33a48b6aed55e64e68586ff.png
  
  return {
      'code': 'ok',
      # 'url': f'/uploads/{directory_name}/{filename}',
      'url': url_for('download_file', filename=f'{directory_name}/{filename}'),
  }
  ```

- `auth / user.html`

  ```python
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
  ```

  

##### 이제 base.html 로그인시 관리자면(admin) / 일반사용자면(내정보)가 나오도록 조건 추가

- avatar도 표기하도록 추가

##### front - 57_base_change_after_userinfo.html

```html
<!-- g.user if  avatar/
이름 + 내 정보/
(g.user.is_super_user if   admin)/
로그아웃
else 회원가입/
로그인 -->
<b-navbar-item tag="div">
    {% if g.user %}
    <!-- avatar -->
    <figure class="image mx-2" style="border: none;">
        <!--                                     style="height: 100%"-->
        <img class="is-rounded"
             src="
                  {% if g.user.avatar %}
                  {{url_for('download_file', filename=g.user.avatar)}}
                  {% else %}
                  {{url_for('static', filename='/img/user/default_avatar.svg')}}
                  {% endif %}
                  "
             alt="{{ g.user.username }}">
    </figure>

    <div class="buttons">
        <!-- 닉네임 + 내 정보-->
        <a class="button is-primary"
           href="{{ url_for('auth.userinfo') }}"
           >
            {{g.user['username']}}님 정보
        </a>
        <!-- 관리자면 admin 추가 -->
        {% if g.user.is_super_user %}
        <a class="button is-success"
           href="{{ url_for('admin.index') }}">
            Admin
        </a>
        {% endif %}
        <!-- 로그아웃 -->
        <a class="button is-danger" href="{{ url_for('auth.logout')}}">
            로그아웃
        </a>
    </div>
    {% else %}
    <div class=" buttons">
        <a class="button is-primary" href="{{ url_for('auth.register')}}">
            회원가입
        </a>
        <a class="button is-light" href="{{ url_for('auth.login')}}">
            로그인
        </a>
    </div>
    {% endif %}
</b-navbar-item>
```



##### front - style.css에 base.html navbar-item 하위 버튼 이미지  투명화

```css
/* .navbar-item 하위 프로필이미지 + 버튼들 속성 수정 */
.navbar-item .image img {
  max-height: 2.4rem;
}

/* 버튼들로 나타내지만 다 배경 투명(호버시 색 알아서 나옴) */
.navbar-item .button {
  background: transparent;
}
/* 닉네임 표시 or (회원가입) */
.navbar-item .is-primary {
  color: hsl(256, 60%, 56%);
}
/* 관리자 or 내 정보 */
.navbar-item .is-success {
  color: hsl(184, 79%, 41%);;
}
/* 로그아웃 */
.navbar-item .is-danger {
  color: hsl(348, 86%, 61%);;
}
/* 로그인 */
.navbar-item .is-link {
  color: hsl(256, 60%, 56%);
}
.navbar-item .image img {
  max-height: 2.4rem;
}
```

