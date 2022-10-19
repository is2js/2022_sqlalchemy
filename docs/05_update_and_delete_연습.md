## UPDATE/DELETE QUERY 연습

### UPDATE DELETE 연습
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

class MyException(Exception):
    ...


if __name__ == '__main__':
    is_db_created = os.path.exists(DATABASE_NAME)
    print(is_db_created)
    if not is_db_created:
        db_creator.create_database()
        # db_creator.create_database(False)

    ## 쿼리 연습 -> session객체가 필요하다.
    session: SQLSession = Session()


    # try:
    #     pass
    #     session.commit()
    # except MyException:
    #     session.rollback()
    # finally:
    #     session.close()

    try:
        pass
        session.commit()
    except MyException:
        session.rollback()
    finally:
        session.close()
    student = session.query(Students).get(20)
    print(student)
    ## 1) update1: .get(id)로 Model객체  조회후 -> 필드 값 재할당으로 변경하고 -> commit
    # student.age = 16
    print(student)

    ## 2) update2: filter로 조회된 상태에서 +  .update({}) dict로 처리
    ## => .update({}) 의 key는    Model.필드  or   '필드명' => 2개다 가능하다.
    ## => 기존에서 업뎃하는 개념을 챙기기 위해서는 Model.필드로 생각하자.
    # => filter 를 안붙이면, 모든 학생들의 나이 + 1
    # session.query(Students).filter(Students.id == 20).update({'age': Students.age + 1})
    session.query(Students).filter(Students.id == 20).update({Students.age : Students.age + 1})
    print(student)
    session.query(Students).update({'age': Students.age + 1})
    print(student)
    # print(session.query(Students).get(20))

    ## 3) age로 필터링하고, 그사람들만. 나이 +=1
    session.query(Students).filter(Students.age <= 18).update({Students.age : Students.age + 1})
    print(student)

    ## 4) delete는 전체삭제를 방지하기 위해
    ##   => update1번처럼, 객체 조회후 -> session.delte( Model객체 ) 로 하자
    ##   => session.delete는 commit안하면, 객체에 데이터는 유지된다.
    # session.delete(student)
    print('*'*30)
    print(student)
    print(session.query(Students).get(20))
    # ******************************
    # Student [name: 이민준 None None, age: 19, adress: 서울특별시 노원구 서초중앙3가, ID group: 2 ]
    # Student [name: 이민준 None None, age: 19, adress: 서울특별시 노원구 서초중앙3가, ID group: 2 ]
    session.commit()
    # 커밋후 => AttributeError: 'NoneType' object has no attribute 'age'

    print(f"학생 수 :{session.query(Students).count()}")
    # 학생 수 :49
    ## 5) 필터링 후 delete => 옵션을 줘야한다.
    # session.query(Students).filter(Students.surname.like('%조')).delete()
    # => sqlalchemy.exc.InvalidRequestError: Could not evaluate current criteria in Python: "Cannot evaluate BinaryExpression with operator <function like_op at 0x0000021CBE8371E0>". Specify 'fetch' or False for the synchronize_session execution option.
    session.query(Students).filter(Students.surname.like('박%')).delete(synchronize_session='fetch')
    print(f"학생 수 :{session.query(Students).count()}")
    # 학생 수 :42
    session.commit()

    ## 6) CUD는 실패시 rollback()을 해야하므로,
    ## 1) MyException class를 정의하고,  -> try: commit() except MyException: rollback()  finllay.close()안에서 수행되어야한다
    # try:
    #     pass
    #     session.commit()
    # except MyException:
    #     session.rollback()
    # finally:
    #     session.close()


    session.close()

```
