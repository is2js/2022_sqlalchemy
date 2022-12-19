import os
import uuid

from bs4 import BeautifulSoup
from flask import send_from_directory
from werkzeug.utils import secure_filename

from src.config import project_config


def _file_path(directory_name):
    # UPLOAD_FOLDER = "/uploads/"
    file_path = project_config.UPLOAD_FOLDER / f'{directory_name}'
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    return file_path


def update_filename(f):
    # 3-1) filename에 실행파일 등이 존재할 수 있으므로, secure_filename메서드를 이용해 한번 필터링 받는다
    filename = secure_filename(f.filename)
    # print(f"filename>>> {secure_filename(f.filename)}")
    # 3-2) filename을 os.path.split  ext()를 이용하여, 경로 vs 확장자만 분리한 뒤, ex> (name, .jpg)
    #      list()로 변환한다.
    _, ext = os.path.splitext(filename)
    # print(f"name, ext>>> {_, ext}")
    # 3-3) name부분만 uuid.uuid4()로 덮어쓴 뒤, 변환된 filename을 반환한다
    # https://dpdpwl.tistory.com/77
    # -> uuid로 생성된 랜덤에는 하이픈이 개입되어있는데 split으로 제거한 뒤 합친다. -> replace로 처리하자
    filename = str(uuid.uuid4()).replace('-', '') + ext
    # print(f"uuid + ext>>> {filename}")
    return filename


# 1) 개별 directory 직접입력 + form.필드.data으로부터 file객체 자체가 입력된다.
def upload_file_path(directory_name, file):
    # 2) 개별 directory 이름 -> uploads폴더와 연결한 뒤, 디렉토리가 없으면 생성하고, 경로를 반환받는다.
    file_path = _file_path(directory_name)
    # 3) file(file객체)를 입력받아, db저장용 filename으로 변경한다.
    filename = update_filename(file)
    # 4) file_paht + filename  및  단독 filename 2개를 tuple로 return한다.
    #  file save용 전체경로(개별폴더경로까지) + 변경filename ,   변경filename만
    print("업로드된 파일>>>", file_path / filename)
    return file_path / filename, filename


#### 추가: db.field에    /uploads/ 이후 값을 받아 파일이 존재하면 삭제한다.
# -> 3.8부터는 Path.unlink()의 missing_ok가 가능한데, 직므 3.7이라서 os로 한다.
# https://stackoverflow.com/questions/6996603/how-do-i-delete-a-file-or-folder-in-python
def delete_uploaded_file(directory_and_filename):
    # 애초에 avatar가 없다가 추가하는 경우, directory_and_filename = user.avatar에는 
    # -> None으로 경로가 들어온다 미리  예외처리하여 종료
    if not directory_and_filename:
        return
    # project_config.UPLOAD_FOLDER == '~/uploads/'까지의 경로
    file_path = project_config.UPLOAD_FOLDER / directory_and_filename
    # file_paht == '~/uploads/' + 'avatar/uuid4.파일명'
    if os.path.isfile(file_path):
        os.remove(file_path)
    # Path(file_path).unlink(missing_ok=True) # python3.8부터
    print("삭제된 파일>>>", file_path)


def delete_files_in_img_tag(text):
    soup = BeautifulSoup(text, 'html.parser')
    page_imgs = [image["src"] for image in soup.findAll("img")]
    if page_imgs:
        for img in page_imgs:
            # '/uploads/post/4787c8a891334d8ebb372244b2f93000.png'
            directory_and_filename = '/'.join(img.split('/')[2:])  # 앞에 img src=""  중 "/uploads/" 부분을 제거
            delete_uploaded_file(directory_and_filename)


def download_file(filename):
    return send_from_directory(project_config.UPLOAD_FOLDER, filename)