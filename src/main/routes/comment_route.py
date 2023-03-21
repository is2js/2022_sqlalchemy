from flask import Blueprint, request, make_response, jsonify
from src.infra.tutorial3 import Comment

comment_bp = Blueprint("comment", __name__, url_prefix='/comment')


@comment_bp.route("/post/<int:post_id>", methods=['GET'])
def all(post_id):
    tree = Comment.get_tree_from(post_id)

    if tree:
        return make_response(dict(tree=tree, message='서버에서 데이터를 성공적으로 받았습니다.'), 200)
    else:
        return make_response(dict(message='댓글 데이터 전송 실패'), 409)


@comment_bp.route("/add", methods=['POST'])
def add():
    payload = request.get_json()
    # {'post_id': '8', 'author_id': '1', 'parent_id': None, 'content': 'ff'}
    payload['content'] = payload['content'].strip()

    result, msg = Comment.create(**payload)

    if result:
        new_comment = result.to_dict2(nested=Comment._MAX_LEVEL, relations='replies',
                                      hybrid_attrs=True,
                                      exclude=['path', 'sort'])
        return make_response(dict(new_comment=new_comment, message='댓글 등록 완료!'), 201)
    else:
        return make_response(dict(message='댓글 등록 실패!'), 409)
