import functools

from flask import g, url_for, request, redirect, abort

from src.infra.tutorial3 import Permission, Roles


def login_required(view_func):
    @functools.wraps(view_func)
    def wrapped_view(**kwargs):
        if not g.user:
            # return redirect(url_for('auth.login'))
            # 추가1) login이 필요한 곳에 로그인 안한상태로 접속시, request.path를 이용해, redirect 전 현재요청url을 쿼리스트링으로 기억
            redirect_to = f"{url_for('auth.login')}?redirect_to={request.path}"
            return redirect(redirect_to)
        return view_func(**kwargs)
        # # 추가2) [권한처리3] logged_user이후 로그인요구route를 탈 때, 로그인되어있으면 바로 view_func을 타러갔었으나
        # # -> 로그인된 유저라도 권한을 확인하고 view_func으로 갈지 vs route없이 바로 권한없음을 반환할지로 나뉜다.
        # # -> 외부에서 데코wrapper함수를 실행하면, 문자열만 나와서 반환될 것이다?!
        # if g.user.has_perm:
        #     return view_func(**kwargs)
        # else:
        #     return '<h1> 권한이 없습니다 </h1>'

    return wrapped_view


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


def role_required(allowed_roles=[]):
    if not allowed_roles:
        raise ValueError('allowed_roles=은 반드시 list형태로 입력해야합니다')

    if not isinstance(allowed_roles, list):
        raise ValueError('allowed_roles=[]는 list형태로 입력해주세요')

    # if any(allowed_role not in roles for allowed_role in allowed_roles):
    if any(allowed_role not in Roles for allowed_role in allowed_roles):
        raise ValueError(
            f"""
            allowed_roles=[]의 인자에는
            {', '.join([role.name for role in Roles])} 중 하나를 입력해야합니다. 
            """''
        )

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
