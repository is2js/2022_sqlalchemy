#  flask createsuperuser
import click
from flask import Flask
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.config import project_config
from src.infra.config.connection import DBConnectionHandler
# from src.infra.tutorial3 import User, Role
from create_database_tutorial3 import *


# app객체를 받아 초기화해주는 메서드
def init_script(app: Flask):
    # app -> terminal용 flask adminuser생성command를 method형태로 추가
    #     -> terminal용 [flask 메서드명]으로 사용하기 때문에 소문자이어서 지정
    # click -> flask 명령어 사용시 옵션으로 받을 값을 지정
    @app.cli.command()
    @click.option("--username", prompt=True, help="사용할 username을 입력!")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="사용할 password를 입력!")
    def createadminuser(username, password):
        click.echo('관리자 계정을 생성합니다.')
        with DBConnectionHandler() as db:
            # user = User(username=username, password=generate_password_hash(password), is_super_user=True)
            # user = User(username=username, password=password, is_super_user=True)
            try:
                role_admin = db.session.scalars(select(Role).where(Role.name == 'ADMINISTRATOR')).first()
                user = User(username=username, password=password, email=project_config.ADMIN_EMAIL, role=role_admin)
                db.session.add(user)
                db.session.commit()

                click.echo(f'관리자 계정 [{username}]이 성공적으로 생성되었습니다.')
            except IntegrityError:
                db.session.rollback()

                click.echo(f'Warning) Username[{username}]  or Email[{project_config.ADMIN_EMAIL}]이 이미 존재합니다.')

            except:
                db.session.rollback()

                click.echo(f'Warning) 알 수 없는 이유로 관리자계정 생성에 실패하였습니다.')

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


    #### create_db도 미리 만들어놓기
    @app.cli.command()
    @click.option("--truncate", prompt=True, default=False)
    @click.option("--drop_table", prompt=True, default=False)
    @click.option("--load_fake_data", prompt=True, default=False)
    def createdb(truncate, drop_table, load_fake_data):

        create_database(
            truncate= True if truncate in ['y', 'yes'] else truncate,
            drop_table=True if drop_table in ['y', 'yes'] else drop_table,
            load_fake_data=True if load_fake_data in ['y', 'yes'] else load_fake_data
        )
        click.echo(f'db.create_all() 완료')
