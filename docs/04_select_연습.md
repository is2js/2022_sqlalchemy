## SELECT QUERY 연습
### 만약, 기존 FAKE DATA DB 말고, 새로 DB 변경하고 싶다면
1. 기존 것을 남기고 싶다면, 새로운 sqlite DB 생성을 위해, DB_NAME을 변경하자
    ![20221016001142](https://raw.githubusercontent.com/is3js/screenshots/main/20221016001142.png)
2. main.py에 작성해둔 db_creator.create_database()의 옵션 `load_fake_data`를 `False`로 주고 새로운 db를 생성하자.
    ![20221016001021](https://raw.githubusercontent.com/is3js/screenshots/main/20221016001021.png)
    ```python
    import os

    from sqlalchemy import and_

    from models.database import DATABASE_NAME, Session
    from models.lessons import Lessons, association_table
    from models.students import Students
    from models.groups import Groups

    import create_database as db_creator

    if __name__ == '__main__':
        is_db_created = os.path.exists(DATABASE_NAME)
        if not is_db_created:
            # db_creator.create_database()
            db_creator.create_database(False)
    ```
   
### SELECT 연습
```python
import os
from typing import List

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session as SQLSession

from models.database import DATABASE_NAME, Session
from models.lessons import Lessons, association_table
from models.students import Students
from models.groups import Groups

import create_database as db_creator

if __name__ == '__main__':
    is_db_created = os.path.exists(DATABASE_NAME)
    print(is_db_created)
    if not is_db_created:
        db_creator.create_database()
        # db_creator.create_database(False)

    ## 쿼리 연습 -> session객체가 필요하다.
    ###### Students
    ## 1) session의 type을 지정해주기 위해서는, 내가 sessionmaker + engine으로 만든 Session클래스와는 다른이름으로
    ##    .orm패키지의 Session을 as SQLSession 으로 다른이름으로 import한다.(Interface  Import)
    session: SQLSession = Session()
    # session.close()
    ## 2) .count
    print(f"학생 수: {session.query(Students).count()}")
    # 학생 수: 50

    ## 3) filter and_ like first
    student = session.query(Students).filter(and_(
        Students.surname.like('이%'),
        Students.age > 18
    )).first()
    print(student)
    # Student [name: 이현우 None None, age: 25, adress: 인천광역시 서초구 오금거리 (경희강리), ID group: 1 ]

    ## 4) 쿼리실행없이 query만 for문으로
    students = session.query(Students).filter(and_(
        Students.surname.like('이%'),
        Students.age > 16
    ))
    for it in students:
        print(it)
    # Student [name: 이현우 None None, age: 25, adress: 인천광역시 서초구 오금거리 (경희강리), ID group: 1 ]
    # Student [name: 이현우 None None, age: 25, adress: 인천광역시 서초구 오금거리 (경희강리), ID group: 1 ]
    # Student [name: 이영진 None None, age: 24, adress: 충청북도 성남시 서초대가 (옥순김배면), ID group: 2 ]
    # Student [name: 이정훈 None None, age: 25, adress: 전라북도 시흥시 잠실05로, ID group: 1 ]
    # Student [name: 이은지 None None, age: 18, adress: 제주특별자치도 증평군 영동대131로 (경숙윤리), ID group: 2 ]
    # Student [name: 이민준 None None, age: 17, adress: 서울특별시 노원구 서초중앙3가, ID group: 2 ]
    # Student [name: 이영환 None None, age: 17, adress: 광주광역시 도봉구 개포길, ID group: 1 ]
    # Student [name: 이성진 None None, age: 21, adress: 경상북도 제천시 봉은사10길 (진우이홍마을), ID group: 2 ]
    # Student [name: 이순자 None None, age: 18, adress: 대전광역시 강북구 영동대49로 (윤서김이읍), ID group: 1 ]
    # Student [name: 이하윤 None None, age: 22, adress: 충청남도 가평군 역삼가 (은서박송면), ID group: 2 ]
    # Student [name: 이상철 None None, age: 19, adress: 경기도 동해시 잠실로 (옥순김남읍), ID group: 2 ]
    # Student [name: 이경자 None None, age: 18, adress: 세종특별자치시 도봉구 양재천8거리 (종수황리), ID group: 1 ]

    ## 5) query만 출력하면 => SQL문이 나온다.
    print(students)
    # SELECT students.id AS students_id, students.surname AS students_surname, students.name AS students_name, students.patronymic AS students_patronymic, students.age AS students_age, students.address AS students_address, students."group" AS students_group
    # FROM students
    # WHERE students.surname LIKE ? AND students.age > ?

    ## 6) 쿼리실행은 안했지만, list comp에 넣고 list를 출력
    # => 객체list로 나온다.
    students_list: List[Students] = [it for it in students]
    print(students_list)
    # [Student [name: 이현우 None None, age: 25, adress: 인천광역시 서초구 오금거리 ...
    print('*' * 30)
    ## 7) filter or_
    students = session.query(Students).filter(or_(
        Students.surname.like('권%'),
        Students.surname.like('박%'),
    ))
    for it in students:
        print(it)
    # Student [name: 권민수 None None, age: 24, adress: 울산광역시 중랑구 백제고분5길, ID group: 1 ]
    # Student [name: 박건우 None None, age: 18, adress: 부산광역시 종로구 오금거리 (현주양김동), ID group: 1 ]
    # Student [name: 박현숙 None None, age: 24, adress: 경상남도 삼척시 테헤란564로 (미영하읍), ID group: 1 ]
    # Student [name: 박현숙 None None, age: 20, adress: 인천광역시 서대문구 봉은사63로 (보람김서리), ID group: 2 ]
    # Student [name: 박중수 None None, age: 20, adress: 경기도 김포시 압구정거리 (병철이마을), ID group: 1 ]
    # Student [name: 박미정 None None, age: 17, adress: 충청북도 태안군 오금61길 (민준황마을), ID group: 1 ]
    # Student [name: 박진호 None None, age: 25, adress: 전라남도 고양시 도산대로 (상호한면), ID group: 2 ]
    # Student [name: 박영환 None None, age: 17, adress: 전라남도 용인시 수지구 학동길 (상현이읍), ID group: 1 ]

    ## 8) join with only 1 FK -> no ON clause
    # https://edykim.com/ko/post/getting-started-with-sqlalchemy-part-2/
    # session.query(User).join(Address).\
    #         filter(Address.email_address=='jack@gmail.com').\
    #         all()
    # Query.join()은 User와 Address 사이에 있는 하나의 외래키를 기준으로 join한다. 만약 외래키가 없거나 여러개라면 Query.join() 아래같은 방식을 써야한다.
    # query.join(Address, User.id==Address.user_id)   # 정확한 상태를 적어줌
    # query.join(User.addresses)                      # 명확한 관계 표기 (좌에서 우로)
    # query.join(Address, User.addresses)             # 동일, 명확하게 목표를 정해줌
    # query.join('addresses')                         # 동일, 문자열 이용

    print('*' * 30)
    student_query = session.query(Students).join(Groups).filter(Groups.group_name == '1-MDA-9')
    for it in student_query:
        print(it)
    # ******************************
    # Student [name: 강서윤 None None, age: 22, adress: 인천광역시 용산구 도산대05가, ID group: 2 ]
    # Student [name: 김예지 None None, age: 22, adress: 전라북도 수원시 논현거리 (민지김고마을), ID group: 2 ]
    # Student [name: 김성현 None None, age: 22, adress: 경상북도 부여군 백제고분거리, ID group: 2 ]
    # ...

    ## 9) join한 query를 count
    print(f"1-MDA0-9를 듣는 학생 수: {student_query.count()}")
    print('*' * 30)

    ###### Lessons
    for it in session.query(Lessons):
        print(it)
    print('*' * 30)
    # Lesson [ID: 1, LessonTitle: 수학]
    # Lesson [ID: 2, LessonTitle: 프로그래밍]
    # Lesson [ID: 3, LessonTitle: 철학]
    # Lesson [ID: 4, LessonTitle: 알고리즘 및 데이터 구조]
    # Lesson [ID: 5, LessonTitle: 선형대수학]
    # Lesson [ID: 6, LessonTitle: 통계]
    # Lesson [ID: 7, LessonTitle: 체육]

    for it in session.query(Lessons).filter(Lessons.id > 3):
        print(it)
    print('*' * 30)
    # Lesson [ID: 4, LessonTitle: 알고리즘 및 데이터 구조]
    # Lesson [ID: 5, LessonTitle: 선형대수학]
    # Lesson [ID: 6, LessonTitle: 통계]
    # Lesson [ID: 7, LessonTitle: 체육]

    for it in session.query(Lessons).filter(and_(
            Lessons.id >= 3,
            Lessons.lesson_title.like('통%')
    )):
        print(it)
    print('*' * 30)
    # Lesson [ID: 6, LessonTitle: 통계]

    ## 9) filter + 관계테이블을 활용한 MN관계테이블 만족 정보 찾기
    for it, _ in session.query(Lessons.lesson_title, Groups.group_name).filter(and_(
            association_table.c.lesson_id == Lessons.id,
            association_table.c.group_id == Groups.id,
            Groups.group_name == '1-MDA-9',
    )):
        print(it)
    # 수학
    # 철학
    # 선형대수학
    # 체육
    # **************************
    print('*' * 30)

    ## 10) get을 통한 id로 찾기
    print(session.query(Students).get(45))

    session.close()

```
