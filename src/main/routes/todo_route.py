from functools import cmp_to_key

from dateutil.parser import parse
from flask import Blueprint, request, make_response, jsonify
from src.infra.tutorial3 import Comment, Todo, Employee, TodoType
from src.main.utils.format_date import format_date

todo_bp = Blueprint("todo", __name__, url_prefix='/todo')


@todo_bp.route("/employee/<int:employee_id>", methods=['GET'])
def all(employee_id):
    todos = Todo.filter_by(employee_id=employee_id).all()
    todos = [todo.to_dict2(hybrid_attrs=True) for todo in todos]

    # if todos is not None:
    return make_response(dict(todos=todos, message='서버에서 데이터를 성공적으로 받았습니다.'), 200)
    # else:
    #     return make_response(dict(message='댓글 데이터 전송 실패'), 409)


@todo_bp.route("/add", methods=['POST'])
def add():
    payload = request.get_json()
    # payload  >>  {'employee_id': 1, 'type': '개인', 'todo': 'fasdfsa', 'target_date': None}
    # payload  >>  {'employee_id': 1, 'type': 0, 'todo': 'ㅇㅇㅇㅇㅇㅇ', 'target_date': '2023. 3. 31.'}

    payload['todo'] = payload['todo'].strip()
    # payload['target_date'] = parse(payload['target_date'])
    if payload.get('target_date'):
        payload['target_date'] = parse(payload['target_date'])


    result, msg = Todo.create(**payload)

    if result:
        new_todo = result.to_dict2(hybrid_attrs=True)

        return make_response(dict(new_todo=new_todo, message='할일 등록 완료!'), 201)
    else:
        return make_response(dict(message='댓글 등록 실패!'), 409)


@todo_bp.route("/edit", methods=['PUT'])
def edit():
    payload = request.get_json()
    # print('payload  >> ', payload)
    # payload  >>  {'id': 1, 'type': 1, 'todo': 'ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ2', 'target_date': '2023-03-29T15:00:00.000Z'}
    # payload  >>  {'id': 32, 'type': 1, 'todo': 'ㅇㅇㅇ', 'target_date': '2023. 3. 28.'}

    todo = Todo.filter_by(id=payload['id']).first()
    if not todo:
        return make_response(dict(message='해당 할일이 존재하지 않습니다'), 409)

    args_map = dict(
        todo=payload['todo'].strip(),
        type=payload['type'],
    )
    if payload.get('target_date'):
        args_map['target_date'] = parse(payload['target_date'])

    result, msg = todo.update(
        **args_map
    )

    if result:
        updated_todo = result.to_dict2(hybrid_attrs=True)

        return make_response(dict(updated_todo=updated_todo, message="할 일 수정 완료."), 200)
    else:
        return make_response(dict(message="할 일 수정 실패"), 409)


@todo_bp.route("/delete", methods=['DELETE'])
def delete():
    payload = request.get_json()

    todo = Todo.filter_by(id=payload['id']).first()
    if not todo:
        return make_response(dict(message='해당 할 일이 존재하지 않습니다'), 409)

    result, msg = todo.delete()

    if result:
        return make_response(dict(message='할 일 삭제 성공'), 200)
    else:
        return make_response(dict(message='할 일 삭제 실패'), 409)


@todo_bp.route("/delete_completed", methods=['DELETE'])
def delete_completed():
    payload = request.get_json()
    # payload  >>  {'ids': [27, 29, 31]}
    todos = Todo.filter_by(id__in=payload['ids']).all()
    if not todos:
        return make_response(dict(message='삭제할, 완료된 할 일이 존재하지 않습니다'), 409)

    session = Todo.get_scoped_session()

    total_result = True
    for todo in todos:
        result, msg = todo.delete(session=session, auto_commit=False)
        if not result:
            total_result = False

    if not total_result:
        session.rollback()
        return make_response(dict(message='완료된 할 일 삭제 실패'), 409)

    session.commit()
    return make_response(dict(message='완료된 할 일 삭제 성공'), 200)


@todo_bp.route("/complete", methods=['PUT'])
def complete():
    payload = request.get_json()

    todo = Todo.filter_by(id=payload['id']).first()
    if not todo:
        return make_response(dict(message='해당 할일이 존재하지 않습니다'), 409)

    result, msg = todo.update(complete_date=parse(payload['complete_date']))

    if result:
        updated_todo = result.to_dict2(hybrid_attrs=True)

        return make_response(dict(updated_todo=updated_todo, message="할 일 완료."), 200)
    else:
        return make_response(dict(message="할 일 완료 실패."), 409)


@todo_bp.route("/restore", methods=['PUT'])
def restore():
    payload = request.get_json()

    todo = Todo.filter_by(id=payload['id']).first()
    if not todo:
        return make_response(dict(message='해당 할일이 존재하지 않습니다'), 409)

    result, msg = todo.update(complete_date=None)

    if result:
        updated_todo = result.to_dict2(hybrid_attrs=True)

        return make_response(dict(updated_todo=updated_todo, message="할 일 복원 완료."), 200)
    else:
        return make_response(dict(message="할 일 복원 실패."), 409)

def compare(a, b):
    if b['department_min_level'] == a['department_min_level']:
        if b['is_min_level_dept_leader'] == a['is_min_level_dept_leader']:
            # 3) 부장여부 내림차순
            return b['is_any_dept_leader'] - a['is_any_dept_leader']
        # 2) min레벨 부장여부 내림차순
        return b['is_min_level_dept_leader'] - a['is_min_level_dept_leader']
    # 1) min레벨 오름차순
    return a['department_min_level'] - b['department_min_level']

@todo_bp.route("/group_todos/<int:department_id>/", methods=['GET'])
def group_todos(department_id):
    session = Employee.get_scoped_session()
    group_todos = []
    for employee in Employee.filter_by(upper_department_id=department_id, session=session).all():
        data = dict()
        data['name'] = employee.name
        data['avatar'] = employee.avatar
        data['departments'] = []

        min_level = float('inf')
        min_level_dept = None
        is_any_dept_leader = False
        for d in employee.get_departments(session=session):
            data['departments'].append(d.name + f'({employee.get_position(d, session=session, close=False)})')
            if d.level < min_level:
                min_level = d.level
                min_level_dept = d
            if employee.is_leader_in(d, session=session):
                is_any_dept_leader = True
        data['department_min_level'] = min_level
        data['is_min_level_dept_leader'] = employee.is_leader_in(min_level_dept, session=session)
        data['is_any_dept_leader'] = is_any_dept_leader

        data['todos'] = []
        todos = Todo.filter_by(employee=employee, type=TodoType.그룹.value, complete_date=None, session=session).order_by(
            'pub_date').all()
        for todo in todos:
            data['todos'].append(dict(todo=todo.todo, pub_date=format_date(todo.pub_date)))

        group_todos.append(data)
    session.close()

    group_todos = sorted(group_todos, key=cmp_to_key(compare))

    if group_todos is not None:
        return make_response(dict(group_todos=group_todos, message="그룹 할일 조회 성공"), 200)
    else:
        return make_response(dict(message="그룹 할일 조회 실패."), 409)