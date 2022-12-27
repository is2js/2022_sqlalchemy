import datetime
import json
import re
import time

from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc, \
    union_all, update, delete, or_

# .env
# DB_CONNECTION=sqlite
# DB_NAME=tutorial3
from sqlalchemy.dialects import postgresql, mysql, oracle
from sqlalchemy.orm import aliased, relationship, with_parent, selectinload, lazyload

from create_database_tutorial3 import *
from src.infra.tutorial3.notices import BannerType

if __name__ == '__main__':
    # 1. init data가 있을 땐: load_fake_data = True
    # 2. add() -> commit() method save 등장부터는, 싹다 지우고 시작할 땐: truncate = True
    # 3. 테이블구조가 바뀌는 상황엔, 모든 table 지웠다 새로 생성: drop_table = True
    # create_database(truncate=True, drop_table=False)
    session = Session()
    # create_database(truncate=False, drop_table=False, load_fake_data=False)
    # bulk_insert_from_json('./backup_2022-12-02_211719.json', 'users')
    # 4. 현재 데이터들을 table별로 json으로 백업하기
    # https://stackoverflow.com/questions/47307873/read-entire-database-with-sqlalchemy-and-dump-as-json
    # dump_sqlalchemy('users',is_id_change=True)
    # dump_sqlalchemy('users')
    # 5. 백업json을 table별로 key로하는 dict로 불러오기
    # load_dump("./backup_2022-12-02_211719.json") # print(type(tables)) # <class 'dict'>
    # 6. 백업json -> dict로 load한 뒤, Entity별 bulk_insert_mappings(Entity, dict list)
    # bulk_insert_from_json('./backup_2022-12-03_172847.json', 'users')

    # Role.insert_roles()


    #### 필드추가 전 1) 필드 추가전 먼저 dump   ( 테이블은 미리 추가하면 안된다!!!!!! )
    # dump_sqlalchemy() # User last_seen, ping_by_id() # Employee entity 추가전
    # dump_sqlalchemy('employees')
    # 저장>>> ./backup_2022-12-14_193544.json

    #### 필드추가 전 2) nullable 필드 code 추가 (테이블추가 아님!!!!!!!!!)
    #### => entity에 nullable로 필드 코드 추가
    #last_seen = Column(DateTime, default=datetime.datetime.now, nullable=True)

    #### 필드추가 전 3) 필드를 nullable로 생성된를 drop_table=True로 테이블 생성 -> bulk insert
    # create_database(truncate=False, drop_table=True, load_fake_data=False)
    # bulk_insert_from_json('./backup_2022-12-23_132512.json')
    ####  OR  테이블 1개만 수동 삭제 =>  drop_table=False로 생성 + 특정테이블 insert
    # create_database(truncate=False, drop_table=False, load_fake_data=False)
    # bulk_insert_from_json('./backup_2022-12-23_134339.json', table_name='employees')


    #### 필드추가 전 4) nullable 필드 수동 채우기 or flask shell에서 코드로 채우기
    # @app.shell_context_processor
    # def make_shell_context():
    #     return dict(db=DBConnectionHandler(), User=User, Role=Role)

    # Role.insert_roles()
    #
    # (venv) flask shell
    # admin_role = Role.query.filter_by(name='Administrator').first()
    # default_role = Role.query.filter_by(default=True).first()
    # for u in User.query.all():
    #     if u.role is None:
    #             if u.email == app.config['MYBLOG_ADMIN']:
    #                     u.role = admin_role
    #             else:
    #                     u.role = default_role
    #
    # db.session.commit()

    #### 필드추가 전 6) nullable =False로 변경하고 나중에 migrate
    #last_seen = Column(DateTime, default=datetime.datetime.now, nullable=False)


    #### 필드추가 전 7) 테이블 code 추가

    #### 필드추가 전 8) 테이블 추가는 drop_table = False상태로 생성
    # create_database(truncate=False, drop_table=False, load_fake_data=False)



    ######## department, employeedepartment 설정
    # create_database(truncate=False, drop_table=False, load_fake_data=False)
    # 조직도 참고: https://www.medical.or.kr/suwon/contentsInfo.do?brd_mgrno=0&menu_no=717
    # 병원장 / 실장 / 원무과, 간호과, 원장단 /

    #### (1) 부서 생성
    병원장_부서 = Department(name='병원장', leader_id=20)
    최상위_경영단_부서 = Department(name='경영단', leader_id=20)
    # session.add(병원장)
    # A. 생성시 add로 하지말고 .save()로
    병원장_부서.save() # 부모가 없어 level==0인 부서는 나를 포함하여 0개로서 sort 순서가 정해집니다 / id대신 sort로 채운 path: 000
    최상위_경영단_부서.save()

    이사회_부서 = Department(name='이사회', parent=최상위_경영단_부서)
    이사회_부서.save()
    이사회_부서2 = Department(name='이사회2', parent=최상위_경영단_부서)
    이사회_부서2.save()
    # A. 생성시 .save()안에  commit하지 않은 객체를 self exitst로 중복검사 해야할 듯. -> 안하면 DB의 .name unique제약만 걸림.


    Department(name='행정과', parent=병원장_부서).save()
    Department(name='원무과', parent=병원장_부서).save()
    진료부장_부서 = Department(name='진료부장', parent=병원장_부서).save()

    Department(name='약제과', parent=진료부장_부서).save()
    Department(name='간호과', parent=진료부장_부서).save()
    Department(name='진료각과', parent=진료부장_부서).save()













