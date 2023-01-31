import random

from flask import Blueprint, render_template, request, make_response

from src.infra.tutorial3 import Department

dept_bp = Blueprint("department", __name__, url_prefix='/department')


@dept_bp.route("/organization", methods=['GET'])
def organization():
    tree = Department.get_all_tree()

    return render_template('department/organization.html',
                           tree=tree
                           )


@dept_bp.route("/management", methods=['GET'])
def management():
    # TODO: view의 예시데이터 대신, 부서데이터 내려주기
    return render_template('department/component_test.html')


@dept_bp.route("/add", methods=['POST'])
def add():
    #### HTML FORM으로 보낼 때 ####
    # print(request.form) # html form이 아닌 submit메서드 + axios로 보냄
    # ImmutableMultiDict([('parentId', None), ('type', 1), ('name', '부서추가test')])
    #### axios POST로 보낼 때 ####
    # print(request.data)
    # b'{"parentId":2,"type":"1","name":"222"}'
    # print(request.get_json())
    # {'parentId': 2, 'type': '1', 'name': '222'}
    # {'parentId': None, 'type': '2', 'name': '222'}
    # => type은 b-select에서 string으로 보냄.
    # => parentId가 None으로 넘어오면  int()시 에러남.
    # => dict의 .get으로는 type지정못함. 직접변환
    dept_info = request.get_json()
    if dept_info['parentId']:
        dept_info['parentId'] = int(dept_info['parentId'])


    # TODO: 예시데이터 -> 생성된 부서데이터 to_dict()로 내려보내고 + 예외처리하기
    id_ = random.randint(100, 199)
    sample = {
        'id': id_,
        'parentId': dept_info['parentId'],
        'level': 0,
        'sort': 1,
        'text': dept_info['name'],
        'open': False,
    }

    return make_response(dict(dept=sample, message='부서가 추가되었습니다.'))


@dept_bp.route("/sort", methods=['PUT'])
def change_sort():
    payload = request.get_json()
    # print(payload)
    # {'deptId': 1, 'beforeSort': 1, 'afterSort': 2}

    # TODO: dept 순서변경 -> 다른부서들도 바뀌는지 확인해서 같이 변경해줘야한다.

    return make_response(dict(message='부서 순서 변경에 성공했습니다.'))

@dept_bp.route("/status", methods=['PUT'])
def change_status():
    payload = request.get_json()
    # print(payload)
    # {'deptId': 1}
    # TODO : dept status 변경


    return make_response(dict(message='부서 활성여부 변경을 성공했습니다.'))
