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
    tree = Department.get_all_tree(with_inactive=True)

    return render_template('department/component_test.html',
                           tree=tree)


@dept_bp.route("/add", methods=['POST'])
def add():
    #### HTML FORM으로 보낼 때 ####
    # print(request.form) # html form이 아닌 submit메서드 + axios로 보냄
    # ImmutableMultiDict([('parent_id', None), ('type', 1), ('name', '부서추가test')])
    #### axios POST로 보낼 때 ####
    # print(request.data)
    # b'{"parent_id":2,"type":"1","name":"222"}'

    # print(request.get_json())
    # {'parent_id': None, 'type': '2', 'name': '222'}
    # {'parent_id': 11, 'type': '0', 'name': '12'}

    dept_info = request.get_json()

    new_dept, message = Department(
        name=dept_info['name'],
        type=int(dept_info['type']),  # type만 b-select로 인해 "3" 문자열로 온다.
        parent_id=dept_info['parent_id']).save()

    if new_dept:
        return make_response(dict(new_dept=new_dept, message=message), 201)
    else:
        return make_response(dict(message=message), 409)


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


@dept_bp.route("/name", methods=['PUT'])
def change_name():
    payload = request.get_json()
    # print(payload)
    # {'deptId': 1, 'targetName': '병원장2'}
    # TODO : dept name 변경

    return make_response(dict(message='부서 이름 변경을 성공했습니다.'))
