import random

from flask import Blueprint, render_template, request, make_response
from sqlalchemy import select, exists

from src.infra.config.connection import DBConnectionHandler
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


@dept_bp.route("/delete", methods=['DELETE'])
def delete():
    dept_info = request.get_json()
    result, message = Department.delete_by_id(dept_info['dept_id'])

    return make_response(dict(message=message))


@dept_bp.route("/sort", methods=['PUT'])
def change_sort():
    payload = request.get_json()
    # print(payload)
    # {'dept_id': 1, 'before_sort': 2, 'after_sort': 1}

    result, message = Department.change_sort(payload['dept_id'], payload['after_sort'])

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)


@dept_bp.route("/name", methods=['PUT'])
def change_name():
    payload = request.get_json()
    print(payload)
    # {'dept_id': 1, 'target_name': '병원장2'}

    with DBConnectionHandler() as db:
        try:
            exists_name = db.session.scalar(
                exists()
                .where(Department.name == payload['target_name'])
                .select()
            )
            if exists_name:
                return make_response(dict(message='이미 해당 이름의 부서가 존재합니다.'), 409)

            target_dept = db.session.get(Department, payload['dept_id'])
            target_dept.name = payload['target_name']

            db.session.commit()

            return make_response(dict(message='부서 이름 변경을 성공했습니다.'), 200)

        except Exception as e:
            db.session.rollback()
            return make_response(dict(message='부서 이름 변경에 실패했습니다.'), 409)


@dept_bp.route("/status", methods=['PUT'])
def change_status():
    payload = request.get_json()
    # print(payload)
    # {'dept_id': 1}
    # TODO : dept status 변경
    result, message = Department.change_status(payload['dept_id'])

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)
