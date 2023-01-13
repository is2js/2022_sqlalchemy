#  flask createsuperuser


import click
from flask import Flask
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.config import project_config
from src.infra.config.connection import DBConnectionHandler

from create_database_tutorial3 import *


# from src.infra.tutorial3 import User, Role


# app객체를 받아 초기화해주는 메서드
def init_script(app: Flask):
    # app -> terminal용 flask adminuser생성 command를 method형태로 추가
    #     -> terminal용 [flask 메서드명]으로 사용하기 때문에 소문자이어서 지정
    # click -> flask 명령어 사용시 옵션으로 받을 값을 지정

    #### create_db 만들어놓기
    @app.cli.command("create_db")
    @click.option("--truncate", prompt=True, default=False)
    @click.option("--drop_table", prompt=True, default=False)
    @click.option("--load_fake_data", prompt=True, default=False)
    def createdb(truncate, drop_table, load_fake_data):
        create_database(
            truncate=True if truncate in ['y', 'yes'] else truncate,
            drop_table=True if drop_table in ['y', 'yes'] else drop_table,
            load_fake_data=True if load_fake_data in ['y', 'yes'] else load_fake_data
        )
        click.echo(f'db.create_all() 완료')

    #### admin user 만들기 전에 role도 파이선으로 생성가능하도록 명령어로 만들기
    @app.cli.command()
    def createrole():
        click.echo('기본 Role들을 python으로 생성합니다.')
        try:
            Role.insert_roles()
            click.echo(f'초기 Role 테이블 데이터들이 생성되었습니다.')
        except IntegrityError:
            # 이미 생성할때 존재하면 생성안하도록 순회해서 걸릴 일은 없을 것 이다.
            click.echo(f'Warning) 이미 Role 데이터가 존재합니다.')
        except:
            click.echo(f'Warning) 알수없는 이유로 Role 데이터 생성에 실패했습니다.')


    @app.cli.command("create_admin_user")
    @click.option("--username", prompt=True, help="사용할 username을 입력!")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="사용할 password를 입력!")
    def create_admin_user(username, password):
        click.echo('관리자 계정을 생성합니다.')
        with DBConnectionHandler() as db:
            # user = User(username=username, password=generate_password_hash(password), is_super_user=True)
            # user = User(username=username, password=password, is_super_user=True)
            try:
                role_admin = db.session.scalars(select(Role).where(Role.name == 'ADMINISTRATOR')).first()

                user_admin = User(username=username, password=password, email=project_config.ADMIN_EMAIL,
                                  role=role_admin)
                db.session.add(user_admin)

                #### 관리자도 직원정보를 가져야하므로 생성
                # print(user_admin.id)  # add만 해도 id가 부여된다.? => 안된다.
                db.session.flush()
                #### commit()을 하든 flush()를 하던 한번 갔다와야지 id부여된다.

                employee_admin = Employee(user_id=user_admin.id, name='관리자', sub_name='Administrator',
                                          birth='9910101918111',
                                          join_date=datetime.date.today(), job_status=JobStatusType.재직,
                                          reference='관리자 계정')

                db.session.add(employee_admin)
                db.session.commit()

                click.echo(f'관리자 계정 [{username}]이 성공적으로 생성되었습니다.')

            except IntegrityError:
                db.session.rollback()

                click.echo(
                    f'Warning) Username[{username}]  or Email[{project_config.ADMIN_EMAIL}]이 생성에 실패했습니다.(이미 존재 하는 정보)')

            except:
                db.session.rollback()

                click.echo(f'Warning) 알 수 없는 이유로 관리자계정 생성에 실패하였습니다.')


    #### 예제 부서 만들기
    @app.cli.command('create_department')
    def createdepartment():
        click.echo('예제 부서들을 python으로 생성합니다.')
        try:
            병원장 = Department(name='병원장', type=DepartmentType.부장).save()

            진료부 = Department(name='진료부', type=DepartmentType.부장, parent=병원장).save()
            #### 진료부 하위 부서 - 팀장없이
            한방진료실 = Department(name='한방진료실', type=DepartmentType.원장단, parent=진료부).save()
            탕전실 = Department(name='탕전실', type=DepartmentType.실, parent=진료부).save()

            간호부 = Department(name='간호부', type=DepartmentType.부장, parent=병원장).save()
            #### 간호부 하위 부서 - 팀장없이
            외래 = Department(name='외래', type=DepartmentType.치료실, parent=간호부).save()
            병동 = Department(name='병동', type=DepartmentType.치료실, parent=간호부).save()

            행정부 = Department(name='행정부', type=DepartmentType.부장, parent=병원장).save()
            #### 행정부 하위 부서 - 팀장없이
            원무 = Department(name='원무', type=DepartmentType.팀, parent=행정부).save()
            총무 = Department(name='총무', type=DepartmentType.팀, parent=행정부).save()

            click.echo(f'예제 부서들이 생성되었습니다.')
            click.echo("""******************************
 [ 병원장 ]  
     [ 간호부 ]  
         [ 외래 ]  
         [ 병동 ]  
     [ 행정부 ]  
         [ 원무 ]  
         [ 총무 ] 
     [ 진료부 ]  
         [ 탕전실 ] 
         [ 한방진료실 ] 
******************************
            """)
        except IntegrityError:
            # 이미 생성할때 존재하면 생성안하도록 순회해서 걸릴 일은 없을 것 이다.
            click.echo(f'Warning) 이미 예제 부서 데이터들이 존재합니다.')
        except:
            click.echo(f'Warning) 알수없는 이유로 예제 부서 데이터 생성에 실패했습니다.')
