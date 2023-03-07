from flask import request, url_for, Blueprint

from src.main.decorators.decorators import login_required
from src.main.utils import upload_file_path

util_bp = Blueprint("util", __name__, url_prefix='/util')


# upload route
# 1. POST로 FormData를 받긴 하지만, upload요청마다 '/uploads/`폴더 속 `개별디렉토리이름`은 요청마다 달라진다.
# -> POST지만, path로 directory_name을 받아서, 업로드폴더의 하위 개별폴더로 지정해서 저장하도록 한다

@util_bp.route('/upload/<path:directory_name>', methods=['POST'])
@login_required
def upload(directory_name):
    if request.method == 'POST':
        # 2. 파일객체는 new FormData()객체 속 'upload'로 append했는데
        # -> request.files.get('upload')로 받아낼 수 있다.
        f = request.files.get('upload')
        # 3. file객체를 .read()로 내용물을 읽고 file size를 젠 뒤
        # -> file객체의 읽은 위치를 다시 처음으로 초기화해놓는다.(읽고 커서가 뒤로 갔지만, 다시 원위치
        file_size = len(f.read())
        f.seek(0)
        # 4. 업로드 파일 사이즈를 체크한다. form에서는 validators= [FileSize(max_size=2048000))]으로 해결
        # -> 사이즈가 넘어가면 alert를 띄울 수있게 message를 같이 전달한다.
        if file_size > 2048000:
            return {
                'code': 'err',
                'message': '파일크기가 2M를 넘을 수 없습니다.'
            }
        # 5. upload유틸을 이용해서, '/uploads/`폴더에 붙을 '개별디렉토리', file객체를 넣어주면
        # -> save할 path와 filename이 주어진다.
        # -> 그렇다면, front에서 upload할 개별디렉토리도 보내줘야한다?!
        upload_path, filename = upload_file_path(directory_name=directory_name, file=f)
        # print(upload_path, filename)
        # C:\Users\is2js\pythonProject\2022_sqlalchemy\uploads\post\28d12f83306f4bf6984c9b6bcef7dda5.png 28d12f83306f4bf6984c9b6bcef7dda5.png

        # 6. 저장 후 ok return 시  jsonify없이 그냥 dict로 반환한다?
        # -> 반환시 view에서 볼 img저장경로를 넘겨줘야, 거기서 표시할 수 있을 것이다.
        f.save(upload_path)
        # print(url_for('download_file', filename=f'{directory_name}/{filename}'))
        # /uploads/post/862e406dd33a48b6aed55e64e68586ff.png

        return {
            'code': 'ok',
            # 'url': f'/uploads/{directory_name}/{filename}',
            'url': url_for('download_file', filename=f'{directory_name}/{filename}'),
        }
