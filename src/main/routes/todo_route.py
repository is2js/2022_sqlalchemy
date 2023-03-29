from dateutil.parser import parse
from flask import Blueprint, request, make_response, jsonify
from src.infra.tutorial3 import Comment, Todo

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

    result, msg = todo.update(
        todo=payload['todo'].strip(),
        type=payload['type'],
        target_date=parse(payload['target_date']),
    )

    if result:
        updated_todo = result.to_dict2(hybrid_attrs=True)

        return make_response(dict(updated_todo=updated_todo, message="할 일 수정 완료."), 200)
    else:
        return make_response(dict(message="할 일 수정 실패"), 409)

#
# @comment_bp.route("/blind", methods=['PUT'])
# def blind():
#     payload = request.get_json()
#     comment = Comment.filter_by(id=payload['id']).first()
#     if not comment:
#         return make_response(dict(message='해당 부서가 존재하지 않습니다'), 409)
#
#     result, msg = comment.update(status=0)
#
#     if result:
#         updated_comment = result.to_dict2(nested=Comment._MAX_LEVEL, relations='replies',
#                                           hybrid_attrs=True,
#                                           exclude=['path', 'sort'])
#
#         return make_response(dict(updated_comment=updated_comment, message="대댓글이 존재하여 BLIND 처리."), 200)
#     else:
#         return make_response(dict(message="댓글 삭제 실패"), 409)
#
#
# @comment_bp.route("/remove", methods=['DELETE'])
# def remove():
#     payload = request.get_json()
#
#     comment = Comment.filter_by(id=payload['id']).first()
#     if not comment:
#         return make_response(dict(message='해당 부서가 존재하지 않습니다'), 409)
#
#     result, msg = comment.delete()
#
#     if result:
#         return make_response(dict(message='댓글 삭제 성공'), 200)
#     else:
#         return make_response(dict(message='댓글 삭제 실패'), 409)
