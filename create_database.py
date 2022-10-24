from src.infra.config.db_creator import create_db, Session
from src.infra.entities import *
from faker import Faker


def _load_fake_data(session: Session):
    ## 1) 1:M 에서 [M의 fk]로 쓰일 [1의 객체]부터 먼저 생성한다.
    ## 2) N:M 에서 relationship칼럼이 없는 Entity부터 먼저 생성한다.
    # -> lessons.relationship칼럼.append( groups )
    group1 = Groups(group_name='1-MDA-7')
    group2 = Groups(group_name='1-MDA-9')
    session.add(group1)
    session.add(group2)

    ## 3) N:M에서 종류가 제한적인 것을 미리 만들어놓고
    ##    반복문을 돌면서, 생성하여, 반대entity는 append로 등록해준다.
    lesson_names = ['수학', '프로그래밍', '철학', '알고리즘 및 데이터 구조', '선형대수학', '통계', '체육']
    for key, it in enumerate(lesson_names):
        lesson = Lessons(lesson_title=it)
        lesson.groups.append(group1)
        if key % 2 == 0:
            lesson.groups.append(group2)
        session.add(lesson)

    faker = Faker('ko_KR')
    ## 4) 랜덤으로 택1시키려면, list로 미리 쏴두고 -> faker.random.choice
    group_list = [group1, group2]

    ## 중간에 끊겨도 되는 지점을 commit해준다.
    session.commit()

    ## 5) student를 50개 만든다. fk에 해당하는 group.id를 group_list에서 택1한 뒤 id만 뽑아쓴다.
    for _ in range(50):
        full_name = faker.name().split(' ')
        age = faker.random.randint(16, 25)
        address = faker.address()
        group = faker.random.choice(group_list)  #

        student = Students(full_name, age, address, group.id)
        session.add(student)

    session.commit()

    session.close()
#

def create_database(load_fake_data: bool = True):
    create_db()

    if load_fake_data:
        _load_fake_data(Session())
