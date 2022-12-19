# import datetime
# from pathlib import Path
#
# from flask import Flask, send_from_directory, request, url_for
# from flask_cors import CORS
# from sqlalchemy import select
#
# from src.config import app_config, project_config
#
# from src.infra.config.connection import DBConnectionHandler
# from src.infra.tutorial3 import Category, Setting
# from src.main.routes.auth_route import login_required
# from src.main.templates.filters import feed_datetime, join_phone
# from src.main.utils import upload_file_path
#
# ## Path.cwd()는 실행파일(root의 run.py)의 위치가 찍힌다 -> root부터 경로잡기
# # -> path는 joinpath시 끝이 디렉토리라면 / 까지 넣어줘야한다.
# template_dir = str(Path.cwd().joinpath('src/main/templates/'))
# static_dir = str(Path.cwd().joinpath('src/main/static/'))
#
# print(f"template_dir: {template_dir}")
# print(f"static_dir: {static_dir}")
# app = Flask(__name__,
#             template_folder=template_dir, static_folder=static_dir)
# CORS(app)
#
# app.config["SECRET_KEY"] = app_config.SECRET_KEY
#
# app.jinja_env.filters["feed_datetime"] = feed_datetime
# app.jinja_env.filters["join_phone"] = join_phone
#
# from src.main.routes import main_bp, index
#
# app.register_blueprint(main_bp)
#
# from src.main.routes import api_routes_bp, menu  # menu == "/"용 view_func
#
# app.register_blueprint(api_routes_bp)
#
# from src.main.routes import auth_bp
#
# app.register_blueprint(auth_bp)
#
# from src.main.routes import admin_bp
#
# app.register_blueprint(admin_bp)
#
# # 기본 / url 지정 in route.py의 function
# app.add_url_rule('/', endpoint='index', view_func=index)
#
#
# # root의 uploads폴더에 있는 파일들을 인식하여 파일로 반환할 수 있도록 route 개설
# # https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
# # https://ryanking13.github.io/2018/05/22/pathlib.html
# def download_file(filename):
#     return send_from_directory(project_config.UPLOAD_FOLDER, filename)
#
#
# app.add_url_rule('/uploads/<path:filename>', endpoint='download_file', view_func=download_file)
#
#
# # upload route
# # 1. POST로 FormData를 받긴 하지만, upload요청마다 '/uploads/`폴더 속 `개별디렉토리이름`은 요청마다 달라진다.
# # -> POST지만, path로 directory_name을 받아서, 업로드폴더의 하위 개별폴더로 지정해서 저장하도록 한다
# @app.route('/upload/<path:directory_name>', methods=['POST'])
# @login_required
# def upload(directory_name):
#     if request.method == 'POST':
#         # 2. 파일객체는 new FormData()객체 속 'upload'로 append했는데
#         # -> request.files.get('upload')로 받아낼 수 있다.
#         f = request.files.get('upload')
#         # 3. file객체를 .read()로 내용물을 읽고 file size를 젠 뒤
#         # -> file객체의 읽은 위치를 다시 처음으로 초기화해놓는다.(읽고 커서가 뒤로 갔지만, 다시 원위치
#         file_size = len(f.read())
#         f.seek(0)
#         # 4. 업로드 파일 사이즈를 체크한다. form에서는 validators= [FileSize(max_size=2048000))]으로 해결
#         # -> 사이즈가 넘어가면 alert를 띄울 수있게 message를 같이 전달한다.
#         if file_size > 2048000:
#             return {
#                 'code': 'err',
#                 'message': '파일크기가 2M를 넘을 수 없습니다.'
#             }
#         # 5. upload유틸을 이용해서, '/uploads/`폴더에 붙을 '개별디렉토리', file객체를 넣어주면
#         # -> save할 path와 filename이 주어진다.
#         # -> 그렇다면, front에서 upload할 개별디렉토리도 보내줘야한다?!
#         upload_path, filename = upload_file_path(directory_name=directory_name, file=f)
#         # print(upload_path, filename)
#         # C:\Users\is2js\pythonProject\2022_sqlalchemy\uploads\post\28d12f83306f4bf6984c9b6bcef7dda5.png 28d12f83306f4bf6984c9b6bcef7dda5.png
#
#         # 6. 저장 후 ok return 시  jsonify없이 그냥 dict로 반환한다?
#         # -> 반환시 view에서 볼 img저장경로를 넘겨줘야, 거기서 표시할 수 있을 것이다.
#         f.save(upload_path)
#         # print(url_for('download_file', filename=f'{directory_name}/{filename}'))
#         # /uploads/post/862e406dd33a48b6aed55e64e68586ff.png
#
#         return {
#             'code': 'ok',
#             # 'url': f'/uploads/{directory_name}/{filename}',
#             'url': url_for('download_file', filename=f'{directory_name}/{filename}'),
#         }
#
#
# # template context에서 전역사용할 menu객체를 dict로 반환하여 등록
# #### app_menu & settings
# @app.context_processor
# def inject_category():
#     with DBConnectionHandler() as db:
#         stmt = (
#             select(Category)
#             .order_by(Category.id.asc())
#         )
#
#         categories = db.session.scalars(stmt).all()
#
#         # site setings정보도 같이 올려준다
#         settings = Setting.to_dict()
#
#     return dict(
#         categories=categories,
#         settings=settings,
#     )
#
#
# @app.context_processor
# def inject_today_date():
#     return {'today_date': datetime.date.today}
#
# # app.context_processor(inject_category_and_settings)
#
#
# # flask createadminuser 명령어 추가
# from src.main.utils import init_script
# init_script(app)