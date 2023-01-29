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
    def create_department():
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


    #### 예제 메뉴 만들기
    @app.cli.command('create_menu')
    def createmenu():
        click.echo('예제 menu들을 python으로 생성합니다.')
        try:
            #### level0 #####
            m1 = Menu(
                title='우아한치료법',
                icon='pencil-square',
                template_name='treatment',
                has_img=True,
                level_seq=1
            )
            m1.save()

            m2 = Menu(
                title='클리닉',
                icon='capsule',
                template_name='clinic',
                has_img=True,
                level_seq=2
            )
            m2.save()

            m3 = Menu(
                title='척추질환',
                icon='person-lines-fill',
                template_name='spinedisease',
                has_img=True,
                level_seq=2
            )
            m3.save()

            m4 = Menu(
                title='관절 질환',
                icon='brush',
                template_name='jointdisease',
                has_img=True,
                level_seq=4
            )
            m4.save()

            m5 = Menu(
                title='우아한한약',
                icon='cup-hot',
                template_name='medicine',
                has_img=True,
                level_seq=5
            )
            m5.save()

            m6 = Menu(
                title='병원소개',
                icon='hospital',
                template_name='hospitalinfo',
                has_img=True,
                level_seq=6
            )
            m6.save()

            m7 = Menu(
                title='예약•상담•자가진단',
                icon='calendar-check',
                template_name='reservation',
                has_img=True,
                level_seq=6
            )
            m7.save()

            m8 = Menu(
                title='연재물',
                icon='blog',
                template_name='contents',
                has_img=True,
                level_seq=8
            )
            m8.save()
            # https://fontawesome.com/v6/search?q=blog&m=free

            #### 우아한 치료법 ####
            ## https://fontawesome.com/search?o=r&m=free
            m11 = Menu(
                parent=m1,
                title='척추관절 치료',
                icon='person-rays',
                template_name='spine',
                has_img=False,
                level_seq=1
            )

            m111 = Menu(
                level_seq=1,
                parent=m11,
                title='비수술 보존치료',
                icon='pencil-square',
                template_name='nonsurgery',
                has_img=False
            )
            m112 = Menu(
                level_seq=2,
                parent=m11,
                title='우아한의 역사',
                icon='pencil-square',
                template_name='history',
                has_img=False
            )
            m113 = Menu(
                level_seq=3,
                parent=m11,
                title='치료기간',
                icon='pencil-square',
                template_name='period',
                has_img=False
            )
            m114 = Menu(
                level_seq=4,
                parent=m11,
                title='치료후 연구',
                icon='pencil-square',
                template_name='aftersurgery',
                has_img=False
            )

            m12 = Menu(
                parent=m1,
                title='허리 치료법',
                icon='person-falling-burst',
                template_name='lowback',
                has_img=False,
                level_seq=2
            )

            m121 = Menu(
                level_seq=1,
                parent=m12,
                title='추나요법',
                icon='pencil-square',
                template_name='chuna',
                has_img=False
            )
            m122 = Menu(
                level_seq=2,
                parent=m12,
                title='신경근회복술',
                icon='pencil-square',
                template_name='nerveroot',
                has_img=False
            )

            m123 = Menu(
                level_seq=3,
                parent=m12,
                title='우아침법',
                icon='pencil-square',
                template_name='acupuncture',
                has_img=False
            )

            m124 = Menu(
                level_seq=4,
                parent=m12,
                title='우아한약',
                icon='pencil-square',
                template_name='medicine',
                has_img=False
            )
            m125 = Menu(
                level_seq=5,
                parent=m12,
                title='우아 약침•봉침',
                icon='pencil-square',
                template_name='herbacupuncture',
                has_img=False
            )
            m126 = Menu(
                level_seq=6,
                parent=m12,
                title='도인운동요법',
                icon='pencil-square',
                template_name='doin',
                has_img=False
            )

            m13 = Menu(
                parent=m1,
                title='목 치료법',
                icon='head-side-virus',
                template_name='cervical',
                has_img=False,
                level_seq=3
            )

            m131 = Menu(
                level_seq=1,
                parent=m13,
                title='추나요법',
                icon='pencil-square',
                template_name='chuna',
                has_img=False
            )
            m132 = Menu(
                level_seq=2,
                parent=m13,
                title='우아침',
                icon='pencil-square',
                template_name='acupuncture',
                has_img=False
            )

            m133 = Menu(
                level_seq=3,
                parent=m13,
                title='우아한약',
                icon='pencil-square',
                template_name='medicine',
                has_img=False
            )
            m134 = Menu(
                level_seq=4,
                parent=m13,
                title='우아 약침•봉침',
                icon='pencil-square',
                template_name='herbacupuncture',
                has_img=False
            )
            m135 = Menu(
                level_seq=5,
                parent=m13,
                title='도인운동요법',
                icon='pencil-square',
                template_name='doin',
                has_img=False
            )

            m14 = Menu(
                parent=m1,
                title='턱관절 치료법',
                icon='head-side-mask',
                template_name='jaw',
                has_img=False,
                level_seq=4
            )

            m141 = Menu(
                level_seq=1,
                parent=m14,
                title='추나요법',
                icon='pencil-square',
                template_name='chuna',
                has_img=False
            )
            m142 = Menu(
                level_seq=2,
                parent=m14,
                title='우아침',
                icon='pencil-square',
                template_name='acupuncture',
                has_img=False
            )

            m143 = Menu(
                level_seq=3,
                parent=m14,
                title='우아한약',
                icon='pencil-square',
                template_name='medicine',
                has_img=False
            )
            m144 = Menu(
                level_seq=4,
                parent=m14,
                title='도인운동요법',
                icon='pencil-square',
                template_name='doin',
                has_img=False
            )

            m15 = Menu(
                parent=m1,
                title='관절 치료법',
                icon='person-praying',
                template_name='joint',
                has_img=False,
                level_seq=5
            )
            m151 = Menu(
                level_seq=1,
                parent=m15,
                title='추나요법',
                icon='pencil-square',
                template_name='chuna',
                has_img=False
            )
            m152 = Menu(
                level_seq=2,
                parent=m15,
                title='우아침',
                icon='pencil-square',
                template_name='acupuncture',
                has_img=False
            )

            m153 = Menu(
                level_seq=3,
                parent=m15,
                title='우아한약',
                icon='pencil-square',
                template_name='medicine',
                has_img=False
            )
            m154 = Menu(
                level_seq=4,
                parent=m15,
                title='우아 약침•봉침',
                icon='pencil-square',
                template_name='herbacupuncture',
                has_img=False
            )
            m155 = Menu(
                level_seq=5,
                parent=m15,
                title='도인운동요법',
                icon='pencil-square',
                template_name='doin',
                has_img=False
            )

            m16 = Menu(
                parent=m1,
                title='입원 집중치료',
                icon='bed',
                template_name='hospitalization',
                has_img=False,
                level_seq=6
            )
            m161 = Menu(
                level_seq=1,
                parent=m16,
                title='입원실',
                icon='pencil-square',
                template_name='admissionroom',
                has_img=False
            )
            m161 = Menu(
                level_seq=1,
                parent=m16,
                title='입원실 소개',
                icon='pencil-square',
                template_name='admissionroom',
                has_img=False
            )
            m162 = Menu(
                level_seq=2,
                parent=m16,
                title='입원 절차 안내',
                icon='pencil-square',
                template_name='admissionprocess',
                has_img=False
            )

            m17 = Menu(
                parent=m1,
                title='양방 협력 진료',
                icon='hospital',
                template_name='yangbang',
                has_img=False,
                level_seq=7
            )
            m171 = Menu(
                level_seq=1,
                parent=m17,
                title='협력 병원 안내',
                icon='pencil-square',
                template_name='convention',
                has_img=False
            )
            m172 = Menu(
                level_seq=2,
                parent=m17,
                title='주위 병원 안내',
                icon='pencil-square',
                template_name='around',
                has_img=False
            )
            m18 = Menu(
                parent=m1,
                title='치료 효과',
                icon='hand-holding-heart',
                template_name='effect',
                has_img=False,
                level_seq=8
            )
            m181 = Menu(
                level_seq=1,
                parent=m18,
                title='허리 디스크',
                icon='pencil-square',
                template_name='lowbackdisc',
                has_img=False
            )
            m182 = Menu(
                level_seq=2,
                parent=m18,
                title='터진 디스크',
                icon='pencil-square',
                template_name='burstdisc',
                has_img=False
            )
            m183 = Menu(
                level_seq=3,
                parent=m18,
                title='목 디스크',
                icon='pencil-square',
                template_name='cervicaldisc',
                has_img=False
            )
            m184 = Menu(
                level_seq=4,
                parent=m18,
                title='척추관 협착증',
                icon='pencil-square',
                template_name='stenosis',
                has_img=False
            )
            m185 = Menu(
                level_seq=5,
                parent=m18,
                title='척추 수술 실패 증후군',
                icon='pencil-square',
                template_name='surgeryfailuresyndrome',
                has_img=False
            )
            m186 = Menu(
                level_seq=6,
                parent=m18,
                title='우아한약',
                icon='pencil-square',
                template_name='medicine',
                has_img=False
            )
            m187 = Menu(
                level_seq=7,
                parent=m18,
                title='우아침법',
                icon='pencil-square',
                template_name='acupuncture',
                has_img=False
            )
            m188 = Menu(
                level_seq=8,
                parent=m18,
                title='우아 약침•봉침',
                icon='pencil-square',
                template_name='herbacupuncture',
                has_img=False
            )
            m19 = Menu(
                parent=m1,
                title='치료 사례',
                icon='file-signature',
                template_name='case',
                has_img=False,
                level_seq=9
            )
            m191 = Menu(
                level_seq=1,
                parent=m19,
                title='우아 비수술 치료영상',
                icon='pencil-square',
                template_name='herbacupuncture',
                has_img=False
            )
            m192 = Menu(
                level_seq=2,
                parent=m19,
                title='원장단 치료 경험',
                icon='pencil-square',
                template_name='experience',
                has_img=False
            )
            m193 = Menu(
                level_seq=3,
                parent=m19,
                title='환자가 직접 쓴 치료후기',
                icon='pencil-square',
                template_name='treatmentreview',
                has_img=False
            )
            m194 = Menu(
                level_seq=4,
                parent=m19,
                title='안면신경마비 치료결과',
                icon='pencil-square',
                template_name='faceresult',
                has_img=False
            )

            #### 클리닉 ####
            m21 = Menu(
                parent=m2,
                title='안면신경마비',
                icon='face-flushed',
                template_name='face',
                has_img=False,
                level_seq=1
            )
            m211 = Menu(
                level_seq=1,
                parent=m21,
                title='정의',
                icon='face-flushed',
                template_name='definition',
                has_img=False
            )
            m212 = Menu(
                level_seq=2,
                parent=m21,
                title='주요 특징',
                icon='face-flushed',
                template_name='sharacteristics',
                has_img=False
            )
            m213 = Menu(
                level_seq=3,
                parent=m21,
                title='주요 치료법',
                icon='face-flushed',
                template_name='treatment',
                has_img=False
            )
            m214 = Menu(
                level_seq=4,
                parent=m21,
                title='치료효과',
                icon='face-flushed',
                template_name='effect',
                has_img=False
            )
            m22 = Menu(
                parent=m2,
                title='피로',
                icon='fire',
                template_name='fatigure',
                has_img=False,
                level_seq=2
            )
            m221 = Menu(
                level_seq=1,
                parent=m22,
                title='정의',
                icon='fire',
                template_name='definition',
                has_img=False
            )
            m222 = Menu(
                level_seq=2,
                parent=m22,
                title='치료 대상',
                icon='fire',
                template_name='target',
                has_img=False
            )
            m223 = Menu(
                level_seq=3,
                parent=m22,
                title='진료 절차',
                icon='fire',
                template_name='process',
                has_img=False
            )
            m23 = Menu(
                parent=m2,
                title='수술후통증',
                icon='bed-pulse',
                template_name='surgery',
                has_img=False,
                level_seq=3
            )
            m231 = Menu(
                level_seq=1,
                parent=m23,
                title='정의',
                icon='bed-pulse',
                template_name='definition',
                has_img=False
            )
            m232 = Menu(
                level_seq=2,
                parent=m23,
                title='치료효과',
                icon='bed-pulse',
                template_name='effect',
                has_img=False
            )
            m24 = Menu(
                parent=m2,
                title='청소년',
                icon='tornado',
                template_name='Adolescence',
                has_img=False,
                level_seq=4
            )
            m241 = Menu(
                level_seq=1,
                parent=m24,
                title='체형교정',
                icon='tornado',
                template_name='bodyshape',
                has_img=False
            )
            m242 = Menu(
                level_seq=2,
                parent=m24,
                title='턱관절 장애',
                icon='tornado',
                template_name='jawdisorder',
                has_img=False
            )
            m243 = Menu(
                level_seq=3,
                parent=m24,
                title='성장',
                icon='tornado',
                template_name='grow',
                has_img=False
            )
            m244 = Menu(
                level_seq=4,
                parent=m24,
                title='체력&면역력 강화',
                icon='tornado',
                template_name='reinforcement',
                has_img=False
            )
            m25 = Menu(
                parent=m2,
                title='골프 부상',
                icon='golf-ball-tee',
                template_name='golf',
                has_img=False,
                level_seq=5
            )
            m251 = Menu(
                level_seq=1,
                parent=m25,
                title='정의',
                icon='golf-ball-tee',
                template_name='definition',
                has_img=False
            )
            m252 = Menu(
                level_seq=2,
                parent=m25,
                title='치료 프로그램',
                icon='golf-ball-tee',
                template_name='program',
                has_img=False
            )
            m26 = Menu(
                parent=m2,
                title='비만',
                icon='bread-slice',
                template_name='obesity',
                has_img=False,
                level_seq=6
            )
            m261 = Menu(
                level_seq=1,
                parent=m26,
                title='지방감소&디톡스',
                icon='bread-slice',
                template_name='fatdetox',
                has_img=False
            )
            m262 = Menu(
                level_seq=2,
                parent=m26,
                title='식욕억제',
                icon='bread-slice',
                template_name='appetitesuppression',
                has_img=False
            )
            m27 = Menu(
                parent=m2,
                title='산전•산후',
                icon='person-pregnant',
                template_name='pregnant',
                has_img=False,
                level_seq=7
            )
            m271 = Menu(
                level_seq=1,
                parent=m27,
                title='임신 준비',
                icon='person-pregnant',
                template_name='ready',
                has_img=False
            )
            m272 = Menu(
                level_seq=2,
                parent=m27,
                title='임신 관리',
                icon='person-pregnant',
                template_name='management',
                has_img=False
            )
            m273 = Menu(
                level_seq=3,
                parent=m27,
                title='산후 관리',
                icon='person-pregnant',
                template_name='aftermanagement',
                has_img=False
            )
            m28 = Menu(
                parent=m2,
                title='갱년기',
                icon='person-cane',
                template_name='climacteric',
                has_img=False,
                level_seq=8
            )
            m281 = Menu(
                level_seq=1,
                parent=m28,
                title='정의',
                icon='person-cane',
                template_name='definition',
                has_img=False
            )
            m282 = Menu(
                level_seq=2,
                parent=m28,
                title='치료 프로그램',
                icon='person-cane',
                template_name='program',
                has_img=False
            )
            m29 = Menu(
                parent=m2,
                title='성장',
                icon='person-arrow-up-from-line',
                template_name='grow',
                has_img=False,
                level_seq=9
            )
            m291 = Menu(
                level_seq=1,
                parent=m29,
                title='진단 프로그램',
                icon='person-arrow-up-from-line',
                template_name='diagnosis',
                has_img=False
            )
            m292 = Menu(
                level_seq=2,
                parent=m29,
                title='맞춤 한약',
                icon='person-arrow-up-from-line',
                template_name='medicine',
                has_img=False
            )
            m2_10 = Menu(
                parent=m2,
                title='수험생',
                icon='graduation-cap',
                template_name='student',
                has_img=False,
                level_seq=10
            )
            m2_10_1 = Menu(
                level_seq=1,
                parent=m2_10,
                title='체력&집중력 강화',
                icon='graduation-cap',
                template_name='reinforce',
                has_img=False
            )
            m2_10_2 = Menu(
                level_seq=2,
                parent=m2_10,
                title='스트레스 해소',
                icon='graduation-cap',
                template_name='stress',
                has_img=False
            )
            m2_11 = Menu(
                parent=m2,
                title='코로나/독감',
                icon='head-side-cough',
                template_name='corona',
                has_img=False,
                level_seq=11
            )
            m2_11_1 = Menu(
                level_seq=1,
                parent=m2_11,
                title='정의',
                icon='head-side-cough',
                template_name='definition',
                has_img=False
            )
            m2_11_2 = Menu(
                level_seq=2,
                parent=m2_11,
                title='맞춤 한약',
                icon='head-side-cough',
                template_name='medicine',
                has_img=False
            )

            #### 척추질환
            m31 = Menu(
                parent=m3,
                title='우아한치료의 특징',
                icon='cubes',
                template_name='specialty',
                has_img=False,
                level_seq=1
            )
            m311 = Menu(
                level_seq=1,
                parent=m31,
                title='근거기반 문진',
                icon='cubes',
                template_name='evidence',
                has_img=False
            )
            m312 = Menu(
                level_seq=2,
                parent=m31,
                title='부부 동일치료',
                icon='cubes',
                template_name='couple',
                has_img=False
            )

            m32 = Menu(
                parent=m3,
                title='허리 질환',
                icon='person-falling-burst',
                template_name='lowback',
                has_img=False,
                level_seq=2
            )
            m321 = Menu(
                level_seq=1,
                parent=m32,
                title='허리 디스크',
                icon='person-lines-fill',
                template_name='lowbackdisc',
                has_img=False
            )
            m322 = Menu(
                level_seq=2,
                parent=m32,
                title='퇴행성 디스크',
                icon='person-lines-fill',
                template_name='degenerativedisc',
                has_img=False
            )
            m323 = Menu(
                level_seq=3,
                parent=m32,
                title='척추관 협착증',
                icon='person-lines-fill',
                template_name='stenosis',
                has_img=False
            )
            m323 = Menu(
                level_seq=3,
                parent=m32,
                title='척추 전방전위증',
                icon='person-lines-fill',
                template_name='spondylolisthesis',
                has_img=False
            )
            m324 = Menu(
                level_seq=4,
                parent=m32,
                title='척추 측만증',
                icon='person-lines-fill',
                template_name='scoliosis',
                has_img=False
            )
            m325 = Menu(
                level_seq=5,
                parent=m32,
                title='척추 전만증',
                icon='person-lines-fill',
                template_name='lordosis',
                has_img=False
            )
            m326 = Menu(
                level_seq=6,
                parent=m32,
                title='척추 후만증',
                icon='person-lines-fill',
                template_name='kyphosis',
                has_img=False
            )

            m33 = Menu(
                parent=m3,
                title='목 질환',
                icon='head-side-virus',
                template_name='cervical',
                has_img=False,
                level_seq=3
            )
            m331 = Menu(
                level_seq=1,
                parent=m33,
                title='목 디스크',
                icon='head-side-virus',
                template_name='cervicaldisc',
                has_img=False
            )
            m332 = Menu(
                level_seq=2,
                parent=m33,
                title='일자목 증후군',
                icon='head-side-virus',
                template_name='turtle neck',
                has_img=False
            )
            m333 = Menu(
                level_seq=3,
                parent=m33,
                title='VDT 증후군',
                icon='head-side-virus',
                template_name='vdt',
                has_img=False
            )
            m334 = Menu(
                level_seq=4,
                parent=m33,
                title='퇴행성 목 디스크',
                icon='head-side-virus',
                template_name='degenerativecervicaldisc',
                has_img=False
            )

            m34 = Menu(
                parent=m3,
                title='교통사고 후유증',
                icon='car-burst',
                template_name='car',
                has_img=False,
                level_seq=4
            )
            m341 = Menu(
                level_seq=1,
                parent=m34,
                title='후유증 관리',
                icon='car-burst',
                template_name='aftereffect',
                has_img=False
            )
            m342 = Menu(
                level_seq=2,
                parent=m34,
                title='외래 치료',
                icon='car-burst',
                template_name='outpatient',
                has_img=False
            )
            m343 = Menu(
                level_seq=3,
                parent=m34,
                title='입원 치료',
                icon='car-burst',
                template_name='inpatient',
                has_img=False
            )

            m41 = Menu(
                parent=m4,
                title='우아한치료의 특징',
                icon='cubes',
                template_name='specialty',
                has_img=False,
                level_seq=1
            )

            m411 = Menu(
                level_seq=1,
                parent=m41,
                title='근거기반 문진',
                icon='cubes',
                template_name='evidence',
                has_img=False
            )
            m412 = Menu(
                level_seq=2,
                parent=m41,
                title='부부 동일치료',
                icon='cubes',
                template_name='couple',
                has_img=False
            )

            m42 = Menu(
                parent=m4,
                title='턱 질환',
                icon='head-side-mask',
                template_name='jaw',
                has_img=False,
                level_seq=2
            )
            m421 = Menu(
                level_seq=1,
                parent=m42,
                title='턱관절 장애',
                icon='head-side-mask',
                template_name='disorder',
                has_img=False
            )
            m422 = Menu(
                level_seq=2,
                parent=m42,
                title='교정 프로그램',
                icon='head-side-mask',
                template_name='program',
                has_img=False
            )
            m43 = Menu(
                parent=m4,
                title='무릎 질환',
                icon='person-praying',
                template_name='knee',
                has_img=False,
                level_seq=3
            )

            m431 = Menu(
                level_seq=1,
                parent=m43,
                title='퇴행성관절염',
                icon='person-praying',
                template_name='degenerativearthritis',
                has_img=False
            )
            m432 = Menu(
                level_seq=2,
                parent=m43,
                title='반월상연골손상',
                icon='person-praying',
                template_name='meniscusinjury',
                has_img=False
            )
            m433 = Menu(
                level_seq=3,
                parent=m43,
                title='슬개골연골연화증',
                icon='person-praying',
                template_name='patellarchondromalacia',
                has_img=False
            )
            m434 = Menu(
                level_seq=4,
                parent=m43,
                title='슬개골인대손상',
                icon='person-praying',
                template_name='patellarligamentinjury',
                has_img=False
            )
            m435 = Menu(
                level_seq=5,
                parent=m43,
                title='무릎점액낭염',
                icon='person-praying',
                template_name='kneebursitis',
                has_img=False
            )
            m44 = Menu(
                parent=m4,
                title='어깨 질환',
                icon='child-reaching',
                template_name='shoulder',
                has_img=False,
                level_seq=4
            )
            m441 = Menu(
                level_seq=1,
                parent=m44,
                title='오십견',
                icon='child-reaching',
                template_name='fiftyshoulder',
                has_img=False
            )
            m442 = Menu(
                level_seq=2,
                parent=m44,
                title='석회화건염',
                icon='child-reaching',
                template_name='calcifictendinitis',
                has_img=False
            )
            #
            m443 = Menu(
                level_seq=3,
                parent=m44,
                title='회전근개파열',
                icon='child-reaching',
                template_name='rotatorcufftear',
                has_img=False
            )
            m444 = Menu(
                level_seq=4,
                parent=m44,
                title='어깨충돌증후군',
                icon='child-reaching',
                template_name='shoulderimpingementsyndrome',
                has_img=False
            )
            m445 = Menu(
                level_seq=5,
                parent=m44,
                title='어깨점액낭염',
                icon='child-reaching',
                template_name='shoulderbursitis',
                has_img=False
            )
            m45 = Menu(
                parent=m4,
                title='몸통 질환',
                icon='circle-nodes',
                template_name='body',
                has_img=False,
                level_seq=5
            )
            m451 = Menu(
                level_seq=1,
                parent=m45,
                title='고관절질환',
                icon='circle-nodes',
                template_name='hipjointdisease',
                has_img=False
            )
            m452 = Menu(
                level_seq=2,
                parent=m45,
                title='관절연골손상',
                icon='circle-nodes',
                template_name='articularcartilagedamage',
                has_img=False
            )
            m453 = Menu(
                level_seq=3,
                parent=m45,
                title='스포츠상해',
                icon='circle-nodes',
                template_name='sportsinjury',
                has_img=False
            )
            m46 = Menu(
                parent=m4,
                title='손/발 질환',
                icon='hand',
                template_name='handfoot',
                has_img=False,
                level_seq=6
            )

            m461 = Menu(
                level_seq=1,
                parent=m46,
                title='손목터널증후군',
                icon='circle-nodes',
                template_name='carpaltunnelsyndrome',
                has_img=False
            )
            #
            m462 = Menu(
                level_seq=2,
                parent=m46,
                title='족저근막염',
                icon='circle-nodes',
                template_name='plantarfasciitis',
                has_img=False
            )
            m463 = Menu(
                level_seq=3,
                parent=m46,
                title='무지외반증',
                icon='circle-nodes',
                template_name='halluxvalgus',
                has_img=False
            )

            m47 = Menu(
                parent=m4,
                title='팔꿈치 질환',
                icon='person-breastfeeding',
                template_name='elbow',
                has_img=False,
                level_seq=7
            )

            m471 = Menu(
                level_seq=1,
                parent=m47,
                title='테니스엘보·골프엘보',
                icon='circle-nodes',
                template_name='elbow',
                has_img=False
            )

            m48 = Menu(
                parent=m4,
                title='염증 질환',
                icon='burst',
                template_name='inflammation',
                has_img=False,
                level_seq=8
            )

            m481 = Menu(
                level_seq=1,
                parent=m48,
                title='요추·손목·발목염좌',
                icon='burst',
                template_name='sprains',
                has_img=False
            )

            m482 = Menu(
                level_seq=2,
                parent=m48,
                title='류머티스관절염',
                icon='burst',
                template_name='rheumatoidarthritis',
                has_img=False
            )

            m483 = Menu(
                level_seq=3,
                parent=m48,
                title='통풍성관절염',
                icon='burst',
                template_name='goutyarthritis',
                has_img=False
            )

            m51 = Menu(
                parent=m5,
                title='우아한 한약',
                icon='plate-wheat',
                template_name='info',
                has_img=False,
                level_seq=1
            )
            m511 = Menu(
                level_seq=1,
                parent=m51,
                title='근골격계',
                icon='plate-wheat',
                template_name='musculoskeletal',
                has_img=False
            )
            m512 = Menu(
                level_seq=2,
                parent=m51,
                title='소화기계',
                icon='plate-wheat',
                template_name='digestive',
                has_img=False
            )
            m513 = Menu(
                level_seq=3,
                parent=m51,
                title='호흡기계',
                icon='plate-wheat',
                template_name='respiratory',
                has_img=False
            )
            m514 = Menu(
                level_seq=4,
                parent=m51,
                title='비뇨기계',
                icon='plate-wheat',
                template_name='urinary',
                has_img=False
            )
            m52 = Menu(
                parent=m5,
                title='우아한 보약',
                icon='person-circle-plus',
                template_name='plus',
                has_img=False,
                level_seq=3
            )
            m521 = Menu(
                level_seq=1,
                parent=m52,
                title='성인 보약',
                icon='person-circle-plus',
                template_name='adult',
                has_img=False
            )
            m522 = Menu(
                level_seq=2,
                parent=m52,
                title='수험생 보약',
                icon='person-circle-plus',
                template_name='student',
                has_img=False
            )
            m523 = Menu(
                level_seq=3,
                parent=m52,
                title='여성 보약',
                icon='person-circle-plus',
                template_name='student',
                has_img=False
            )
            m524 = Menu(
                level_seq=4,
                parent=m52,
                title='어린이 보약',
                icon='person-circle-plus',
                template_name='children',
                has_img=False
            )
            m53 = Menu(
                parent=m5,
                title='안전성',
                icon='shield-heart',
                template_name='safety',
                has_img=False,
                level_seq=2
            )

            m531 = Menu(
                level_seq=1,
                parent=m53,
                title='처방 근거',
                icon='shield-heart',
                template_name='evidence',
                has_img=False
            )
            m532 = Menu(
                level_seq=2,
                parent=m53,
                title='약재 품질',
                icon='shield-heart',
                template_name='quality',
                has_img=False
            )

            m54 = Menu(
                parent=m5,
                title='우아한 탕전실',
                icon='building-wheat',
                template_name='bathroom',
                has_img=False,
                level_seq=4
            )
            m541 = Menu(
                level_seq=1,
                parent=m54,
                title='외부 탕전실',
                icon='building-wheat',
                template_name='outsourcing',
                has_img=False
            )

            m61 = Menu(
                parent=m6,
                title='의료진 소개',
                icon='user-doctor',
                template_name='info',
                has_img=False,
                level_seq=1
            )
            m611 = Menu(
                level_seq=1,
                parent=m61,
                title='원장단 소개',
                icon='user-doctor',
                template_name='doctors',
                has_img=False
            )
            m612 = Menu(
                level_seq=2,
                parent=m61,
                title='간호부 소개',
                icon='user-doctor',
                template_name='therapist',
                has_img=False
            )

            m62 = Menu(
                parent=m6,
                title='병원 소개',
                icon='hospital',
                template_name='notice',
                has_img=False,
                level_seq=2
            )
            m621 = Menu(
                level_seq=1,
                parent=m62,
                title='진료 일정표',
                icon='hospital',
                template_name='timetable',
                has_img=False
            )
            m622 = Menu(
                level_seq=2,
                parent=m62,
                title='둘러보기',
                icon='hospital',
                template_name='tour',
                has_img=False
            )
            m623 = Menu(
                level_seq=3,
                parent=m62,
                title='길찾기',
                icon='hospital',
                template_name='map',
                has_img=False
            )

            m63 = Menu(
                parent=m6,
                title='병원 소식',
                icon='newspaper',
                template_name='news',
                has_img=False,
                level_seq=3
            )
            m631 = Menu(
                level_seq=1,
                parent=m63,
                title='공지/이벤트',
                icon='newspaper',
                template_name='notice',
                has_img=False
            )
            m632 = Menu(
                level_seq=2,
                parent=m63,
                title='병원 소식',
                icon='newspaper',
                template_name='news',
                has_img=False
            )
            m633 = Menu(
                level_seq=3,
                parent=m63,
                title='패키지 상품',
                icon='newspaper',
                template_name='package',
                has_img=False
            )
            m64 = Menu(
                parent=m6,
                title='병원 이용안내',
                icon='info',
                template_name='info',
                has_img=False,
                level_seq=4
            )
            m641 = Menu(
                level_seq=1,
                parent=m64,
                title='진료 안내',
                icon='info',
                template_name='medical',
                has_img=False
            )
            m642 = Menu(
                level_seq=2,
                parent=m64,
                title='입원 안내',
                icon='info',
                template_name='admission',
                has_img=False
            )
            m643 = Menu(
                level_seq=3,
                parent=m64,
                title='증명서 발급',
                icon='info',
                template_name='certificate',
                has_img=False
            )
            m644 = Menu(
                level_seq=4,
                parent=m64,
                title='비급여 안내',
                icon='info',
                template_name='uninsured',
                has_img=False
            )
            m645 = Menu(
                level_seq=5,
                parent=m64,
                title='자주 묻는 질문',
                icon='info',
                template_name='faq',
                has_img=False
            )
            m65 = Menu(
                parent=m6,
                title='사회공헌',
                icon='people-carry-box',
                template_name='social',
                has_img=False,
                level_seq=4
            )
            m651 = Menu(
                level_seq=1,
                parent=m65,
                title='봉사활동',
                icon='people-carry-box',
                template_name='volunteer',
                has_img=False
            )
            m652 = Menu(
                level_seq=2,
                parent=m65,
                title='지역 MOU',
                icon='people-carry-box',
                template_name='mou',
                has_img=False
            )

            m71 = Menu(
                parent=m7,
                title='실시간 예약',
                icon='calendar-check',
                template_name='reservation',
                has_img=False,
                level_seq=1
            )
            m711 = Menu(
                level_seq=1,
                parent=m71,
                title='실시간 예약하기',
                icon='calendar-check',
                template_name='reserve',
                has_img=False
            )
            m712 = Menu(
                level_seq=2,
                parent=m71,
                title='예약 확인하기',
                icon='calendar-check',
                template_name='confirm',
                has_img=False
            )

            m72 = Menu(
                parent=m7,
                title='자가진단',
                icon='check',
                template_name='selfdiagnosis',
                has_img=False,
                level_seq=2
            )
            m721 = Menu(
                level_seq=1,
                parent=m72,
                title='우아한 문진',
                icon='check',
                template_name='ask',
                has_img=False
            )
            m722 = Menu(
                level_seq=2,
                parent=m72,
                title='자녀 키 예상',
                icon='check',
                template_name='height',
                has_img=False
            )

            m723 = Menu(
                level_seq=3,
                parent=m72,
                title='비만도 체크(BMI)',
                icon='check',
                template_name='bmi',
                has_img=False
            )
            m724 = Menu(
                level_seq=4,
                parent=m72,
                title='외래환자 설문',
                icon='check',
                template_name='outpatient',
                has_img=False
            )
            m725 = Menu(
                level_seq=5,
                parent=m72,
                title='입원환자 설문',
                icon='check',
                template_name='inpatient',
                has_img=False
            )

            m73 = Menu(
                parent=m7,
                title='고객상담실',
                icon='headset',
                template_name='consult',
                has_img=False,
                level_seq=3
            )
            m731 = Menu(
                level_seq=1,
                parent=m73,
                title='의료 상담',
                icon='headset',
                template_name='medical',
                has_img=False
            )
            m732 = Menu(
                level_seq=2,
                parent=m73,
                title='입원 상담',
                icon='headset',
                template_name='confirm',
                has_img=False
            )
            m733 = Menu(
                level_seq=3,
                parent=m73,
                title='고객의 소리',
                icon='headset',
                template_name='confirm',
                has_img=False
            )

            m81 = Menu(
                parent=m8,
                title='블로그 연재',
                icon='blog',
                template_name='blog',
                has_img=False,
                level_seq=1
            )
            m811 = Menu(
                level_seq=1,
                parent=m81,
                title='최근 글(5개)',
                icon='blog',
                template_name='recent',
                has_img=False
            )
            m82 = Menu(
                parent=m8,
                title='유튜브 영상',
                icon='video',
                template_name='youtube',
                has_img=False,
                level_seq=2
            )
            m821 = Menu(
                level_seq=1,
                parent=m82,
                title='최근 영상(5개)',
                icon='video',
                template_name='recent_',
                has_img=False
            )

            for menu in [
                # 우아한치료법
                m11, m12, m13, m14, m15, m16, m17, m18, m19,
                m111, m112, m113, m114,
                m121, m122, m123, m124, m125, m126,
                m131, m132, m133, m134, m135,
                m141, m142, m143, m144,
                m151, m152, m153, m154, m155,
                m161, m162,
                m171, m172,
                m181, m182, m183, m184, m185, m186, m187, m188,
                m191, m192, m193, m194,

                # 클리닉
                m21, m22, m23, m24, m25, m26, m27, m28, m29, m2_10, m2_11,
                m211, m212, m213, m214,
                m221, m222, m223,
                m231, m232,
                m241, m242, m243, m244,
                m251, m252,
                m261, m262,
                m271, m272, m273,
                m281, m282,
                m291, m292,
                m2_10_1, m2_10_2,
                m2_11_1, m2_11_2,

                # 척추질환
                m31, m32, m33, m34,
                m321, m322, m323, m324, m325, m326,
                m331, m332, m333, m334,
                m341, m342, m343,

                # 관절질환
                m41, m42, m43, m44, m45, m46, m47, m48,
                m411, m412,
                m421, m422,
                m431, m432, m433, m434, m435,
                m441, m442, m443, m444, m445,
                m451, m452, m453,
                m461, m462, m463,
                m471,
                m481, m482, m483,

                # 우아한한약
                m51, m52, m53, m54,
                m511, m512, m513, m514,
                m521, m522, m523, m524,
                m531, m532,
                m541,

                # 병원소개
                m61, m62, m63, m64, m65,
                m611, m612,
                m621, m622, m623,
                m631, m632,
                m641, m642, m643, m644, m645,
                m651, m652,

                # 실시간 예약상담
                m71, m72, m73,
                m711, m712,
                m721, m722, m723, m724, m725,
                m731, m732, m733,

                # 연재Contents
                m81, m82,
                m811,
                m821,

            ]:
                menu.save()


            click.echo(f'예제 메뉴들이 성공적으로 생성되었습니다.')


        except IntegrityError:
            # 이미 생성할때 존재하면 생성안하도록 순회해서 걸릴 일은 없을 것 이다.
            click.echo(f'Warning) 이미 예제 메뉴 데이터들이 존재합니다.')
        except:
            click.echo(f'Warning) 알수없는 이유로 예제 메뉴 데이터 생성에 실패했습니다.')