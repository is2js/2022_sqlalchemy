import re


def remove_empty_and_hyphen(phone):
    # nullable 필드라 None이 넘어올 수 있다. 애초에 데이터 없을 때.. form화면
    if phone:
        return re.sub('[-| ]', '', phone)
    else:
        # nullable String은 -> filters를 걸어 "" 대신 None이 들어와야한다.
        return None
