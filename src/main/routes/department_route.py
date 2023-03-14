import datetime
import random

from flask import Blueprint, render_template, request, make_response, jsonify
from sqlalchemy import select, exists

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import Department, Employee

dept_bp = Blueprint("department", __name__, url_prefix='/department')


@dept_bp.route("/organization", methods=['GET'])
def organization():


    tree = Department.get_tree_of_roots()


    return render_template('department/organization.html',
                           tree=tree
                           )

# @dept_bp.route("/organization", methods=['GET'])
# def organization():
#     tree = Department.get_all_tree()
#
#     return render_template('department/organization.html',
#                            tree=tree
#                            )


@dept_bp.route("/management", methods=['GET'])
def management():
    tree = Department.get_tree_of_roots()
    # tree = Department.get_all_tree()

    return render_template('department/component_test.html',
                           tree=tree)


@dept_bp.route("/all", methods=['GET'])
def all():
    tree = Department.get_all_tree(with_inactive=True)

    if tree:
        return make_response(dict(tree=tree, message='서버에서 데이터를 성공적으로 받았습니다.'), 200)
    else:
        return make_response(dict(message='데이터 전송 실패'), 409)


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
    # is_cross_level Flag를 확인해서 서로 다른 메서드를 호출한다.
    # {'dept_id': 13, 'after_sort': 1, 'is_cross_level': True, 'after_parent_id': None}
    # {'dept_id': 6, 'after_sort': 2, 'is_cross_level': False, 'after_parent_id': None}
    # print(payload['is_cross_level'], "payload['is_cross_level']")

    if payload['is_cross_level']:
        # print("change_sort_cross_level")
        result, message = Department.change_sort_cross_level(dept_id=payload['dept_id'],
                                                             after_parent_id=payload['after_parent_id'],
                                                             after_sort=payload['after_sort'])
    else:
        # print("change_sort")
        result, message = Department.change_sort(dept_id=payload['dept_id'], after_sort=payload['after_sort'])

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)


@dept_bp.route("/name", methods=['PUT'])
def change_name():
    payload = request.get_json()
    # print(payload)
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


@dept_bp.route("/employees", methods=['GET'])
def employees():
    # args = request.args # ImmutableMultiDict([('myParams[emp_name]', '조ㅈ')])
    params = request.args.to_dict()

    employees = Employee.get_by_name_as_dict(params.get('emp_name'))

    # return jsonify(employees=employees, message='직원 조회 성공')
    return jsonify(employees=employees)


@dept_bp.route("/employees/add", methods=['POST'])
def add_employee():
    payload = request.get_json()
    # print(payload)
    # {'emp_id': 16, 'after_dept_id': 16, 'as_leader': False}
    employee = Employee.get_by_id(payload['emp_id'])

    result, message = employee.change_department(
        current_dept_id=None,
        after_dept_id=payload['after_dept_id'],
        as_leader=payload['as_leader'],
        target_date=datetime.date.today()
    )

    if result:
        position = employee.get_position_by_dept_id(payload['after_dept_id'])

        new_emp = {
            'id': employee.id,
            'name': employee.name,
            'job_status': employee.job_status.name,
            'avatar': employee.user.avatar,
            'position': position,
        }
        return make_response(dict(new_emp=new_emp, message="직원을 추가했습니다."), 200)
    else:
        return make_response(dict(message=message), 409)


@dept_bp.route("/employees/dismiss", methods=['POST'])
def dismiss_employee():
    payload = request.get_json()
    # print(payload)
    employee = Employee.get_by_id(payload['emp_id'])

    result, message = employee.change_department(
        current_dept_id=payload['current_dept_id'],
        after_dept_id=None,
        as_leader=None,
        target_date=datetime.date.today()
    )

    if result:
        return make_response(dict(message=message), 200)
    else:
        return make_response(dict(message=message), 409)


@dept_bp.route("/employees/change/job_status", methods=['PUT'])
def change_employee_job_status():
    payload = request.get_json()
    # print(payload)
    employee = Employee.change_job_status(payload['emp_id'], payload['job_status'], datetime.date.today())


    if employee:
        return make_response(dict(message='재직상태가 변경되었습니다.'), 200)
    else:
        return make_response(dict(message='재직상태 변경에 실패하였습니다.'), 409)