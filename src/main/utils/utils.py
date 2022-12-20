import re
from flask import request, url_for


def remove_empty_and_hyphen(phone):
    # nullable 필드라 None이 넘어올 수 있다. 애초에 데이터 없을 때.. form화면
    if phone:
        return re.sub('[-| ]', '', phone)
    else:
        # nullable String은 -> filters를 걸어 "" 대신 None이 들어와야한다.
        return None


def redirect_url(endpoint='main.index'):
    """
    querystring에 next= or redirect_to=를 가졋거나
    (없다면) 요청 full url (request.referrer http://localhost:5000/admin/user)
    (없다면) url_for(bp.index)
    :param default:
    :return:
    """
    return request.args.get('next') or \
           request.args.get('redirect_to') or \
           request.referrer or \
           url_for(endpoint)
