## MN관계 model -> create_table with fake data

### create_database 구현
1. models 폴더에 database.py에 
   1. DATABASE_NAME, engine, Session, Base 객체 생를성하고 **create_db() 메서드**를 정의한다
      - my) Base객체를 생성해놓는 곳에서 create_db메서드까지 정의해놓고, 호출은 다른데서 한다.
2. models 폴더에 각 entitymodel.py를 정의하되, `database.py`에 정의해놓은 `Base객체를 import후 상속`해서 정의한다 
   1. students.py, groups.py
3. lessons.py는 groups와 M:N관계의 entitymodel이 될 애정인데([참고 블로그](https://edykim.com/ko/post/getting-started-with-sqlalchemy-part-2/))
   1. groups에 비해 M:N관계 중 **늦게 생긴 table**을 **`OneEntity`로 보자.**
      1. 늦게 생긴 OneEntity.py에 `association_table`도 같이 정의해준다.
      2. 늦게 생긴 OneEntity에 `relationship()` + `secondary=`assocation_tale + 한쪽만 관계를 명시해줘도 되는 `backref=`group_lesson 3를 지정해준다.
      3. **먼저 생긴 ManyEntity(groups)에는 아무것도 안해도 된다.**
         - 1:M관계라면, ManyEntity(groups)에서는 FK를 지정해줘야하지만, 협력테이블(with secondary=)이 있는 상황이라면 생략할 수 있다.
      
   2. lesson을 정의하기에 앞서, lessons & groups `association table`부터 작성한다. 
      1. **lessons와 groups사이의 association table(name) `assocication`은 Table()객체로 만들 수 있다.**
      2. 2번째인자에는 Base.metadata를 주고
      3. 각 table_id를 fk로 명시한다.
         ```python
         association_table = Table('asscociation', Base.metadata,
                           Column('lesson_id', Integer, ForeignKey('lessons.id')),
                           Column('group_id', Integer, ForeignKey('groups.id')),
                           )
         ```
         ```
         다대다 관계를 정의하는 기능은 secondary 키워드로 연관 테이블인 Table객체를 참조한다. 이 테이블은 단순히 양측의 관계를 참고하는 형태며 만약 다른 컬럼이 있다면, 예를 들어 자체 primary key가 있거나 foreign key를 가진다면 연관 객체(association object) 라는 다른 형태의 사용패턴을 사용해야 한다. 연관 객체 문서 참고.
         ```
   3. lessons를 groups에 대한 `OneEntity`라고 생각하고
      1. relationship을 준다. (여기를 OneEntity로 생각?! )
      2. secondary= 에 관계 테이블 변수를 준다.
      3. backref= 에 groups가 가질 필드명을 준다 (back_populates=와 달리 1쪽에서 관계명만 정해주면 된다.)
      4. groups에는 아무것도 하지 않는다(ForeignKey 지정조차도) 
         ```python
         class Lessons(Base):
            __tablename__ = 'lessons'

            id = Column(Integer, primary_key=True)
            lesson_title = Column(String)
            groups = relationship('Groups', secondary=association_table, backref='group_lessons')

            def __repr__(self):
               return f"Lesson [ID: {self.id}, LessonTitle: {self.lesson_title}]"
         ```


4. db생성 뿐만 아니라 `faker를 통한 데이터 삽입하여 생성`도 가능하게 하기 위해 root에 `create_database.py`를 
   1. models폴더에 있는 Base + engine의 `create_db 메서드`와 sesionmaker+engine으로 만든 `Session 클래스`를 import하고
   2. create_db() 호출에 대해 load_fake_data: bool = True를 선택형인자로하여 `create_database`메서드를 만든다
      - 해당메서드는 create_db()는 일단 호출하고
      - load_fake_data가 True일 경우를 확인해서, `_load_fake_data` method를 다시 호출하여 데이터를 faker로 채울 것이다.
      - _load_fake_data 메서드는 session객체가 필요한가보다.
      ```python
      from models.database import create_db, Session 


      def _load_fake_data(session: Session):
         ...


      def create_database(load_fake_data: bool = True):
         create_db()

         if load_fake_data:
            _load_fake_data(Session())
      ```

5. Base.create_all(engine)을 호출하는 곳에서, **사용되지 않더라도 `생성될 EnttityModel들`은 `메모리에 import`되어있어야한다**
   - Base.create_all(engine)이 존재하는 models>database.py가 아니더라도 괜찮다. 
   - root > create_database.py에 entity 모델들을 import해놓자
   ```python
   from models.database import create_db, Session

   from models.lessons import Lessons
   from models.students import Students
   from models.groups import Groups

   def _load_fake_data(session: Session):
      ...


   def create_database(load_fake_data: bool = True):
      create_db()
   ```

6.  _load_fake_data를 구현하기 전에, **실행파일로서 `main.py`를 정의해서 fake_data없이 생성해본다.**
   1. os와 models>database.py에 정의해둔 DATABASE_NAME를 import해서, db존재여부를 확인한다.
      ```python
      import os
      from models.database import DATABASE_NAME


      if __name__ == '__main__':
         is_db_created = os.path.exists(DATABASE_NAME)
      ```
   2. 해당path에 sqlite가 없을 경우만, 생성하도록 한다. **root의 create_database.py를 `as db_creator`로 import하는 것이 인상적**
      ```python
      import create_database as db_creator

      if __name__ == '__main__':
         is_db_created = os.path.exists(DATABASE_NAME)
         if not is_db_created:
            db_creator.create_database()
      ```

7. main을 실행한다.
   1. relationship 칼럼과, backref는 DB에는 존재하지 않는다. -> `다대다`에서는 `DB상 서로에 대한 칼럼을 가지지 않는다` -> 필요시 참조테이블에서 조회만한다.
      ![20221015171018](https://raw.githubusercontent.com/is3js/screenshots/main/20221015171018.png)
   2. Column ForeignKey는 DB에 존재한다.
      ![20221015171147](https://raw.githubusercontent.com/is3js/screenshots/main/20221015171147.png)

   3. db생성이 확인되었으면, fake데이터와 함꼐 생성하기 위해 지운다.


8. `create_database.py`로 가서 _load_fake_data 메서드를 구현한다

### load_fake_data 구현
1. 실시간으로 데이터를 다루어야하니, Session이 필요하다.
2. 1:M관계가 있을 경우, M이 실존하는 FK를 가지기 위해 `OneEntity부터 데이터 생성`해놓고 -> `생성된 실존 id를 바탕으로 ManyEntity를 생성`해야한다
   1. Students에 대한 FK인 Groups객체부터 생성한다.
   ```python
   def _load_fake_data(session: Session):
       group1 = Groups(group_name='1-MDA-7')
       group2 = Groups(group_name='1-MDA-9')
       session.add(group1)
       session.add(group2)
   ```
3. M:N관계가 있을 경우, `association + relationship을 정의하지 않는 Entity`를 먼저 객체를 생성하고
   - `association + relationship을 정의한 Entity`에서 DB에는 표기안되지만, `가상칼럼으로 작용할 relationship칼럼`에 `append`로 등록해준다.
   - my) association + relationship을 `정의하지 않는 Entity가 OneEntity처럼 먼저 생성`되어야한다.``
      - Lessons에 대해 Groups를 먼저 생성한다. 
   - relationship칼럼은 주로 OneEntity 속에서 `ManyEntity보유할 칼럼`으로서 `append()`로 여러개를 추가할 수 있다.
   ```python
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
   ```


### query 연습 in main.py
- main에서 sqlite db 생성은, DB_NAME으로 저장된 경로에 sqlite파일이 없을 경우만 생성되므로, 하단에서 실행시키며 query테스트를 해도 된다.
- 쿼리를 날리려면 `session객체가` 필요하다. close()를 직접해줘야한다. `Session 클래스`를 `engine + sessionmaker`로 변수로 미리 만들어놓았었다. import해서 사용한다
- 쿼리를 날리려면, `entity model 클래스`가 필요하다. `association`은 create_all()시에는 굳이 메모리에 올릴 필요없었지만, 여기서는 사용해야하므로 필요하다
- DB쿼리 날릴 때 필요한 것
   1. session
   2. entityModel with associationEntity

   ```python
   from models.database import DATABASE_NAME, Session

   from models.lessons import Lessons, association_table
   from models.students import Students
   from models.groups import Groups
   ```

```python
is_db_created = os.path.exists(DATABASE_NAME)
if not is_db_created:
   db_creator.create_db()

## 쿼리 연습 -> session객체가 필요하다.
session = Session()

## 1) session.query()까지만 iter에서 찍을 시, 각각의 객체들이 나와서 repr로 찍힌다.
for it in session.query(Lessons):
   print(it, type(it))
print('*' * 30)

# Lesson [ID: 1, LessonTitle: 수학] <class 'models.lessons.Lessons'>
# Lesson [ID: 2, LessonTitle: 프로그래밍] <class 'models.lessons.Lessons'>
# Lesson [ID: 3, LessonTitle: 철학] <class 'models.lessons.Lessons'>
# Lesson [ID: 4, LessonTitle: 알고리즘 및 데이터 구조] <class 'models.lessons.Lessons'>
# Lesson [ID: 5, LessonTitle: 선형대수학] <class 'models.lessons.Lessons'>
# Lesson [ID: 6, LessonTitle: 통계] <class 'models.lessons.Lessons'>
# Lesson [ID: 7, LessonTitle: 체육] <class 'models.lessons.Lessons'>

## 2) filter까지 날려서 iter로 찍기
for it in session.query(Lessons).filter(Lessons.id > 3):
   print(it)
print('*' * 30)

# Lesson [ID: 4, LessonTitle: 알고리즘 및 데이터 구조]
# Lesson [ID: 5, LessonTitle: 선형대수학]
# Lesson [ID: 6, LessonTitle: 통계]
# Lesson [ID: 7, LessonTitle: 체육]
# ******************************

## 3) and_로 filter에 2개 조건 주기
for it in session.query(Lessons).filter(and_(Lessons.id >= 3,
                                             Lessons.lesson_title.like('체%'))):
   print(it)
print('*' * 30)
# Lesson [ID: 7, LessonTitle: 체육]
# ******************************

## 4) Student와 Group join한 뒤, Group.group_name으로 조건 주기
for it in session.query(Students).join(Groups).filter(Groups.group_name == '1-MDA-7'):
   print(it)
print('*' * 30)
# ******************************
# Student [name: 박예원 None None, age: 21, adress: 강원도 괴산군 석촌호수29로 (현준김동), ID group: 1 ]
# Student [name: 송예원 None None, age: 23, adress: 전라북도 과천시 언주가, ID group: 1 ]
# Student [name: 박종수 None None, age: 19, adress: 울산광역시 서구 역삼18가, ID group: 1 ]

## 5) 2개 Table을 tuple으로 query(,)하면, 카다시언으로 조합이 나온다?!
# -> SAWarning: SELECT statement has a cartesian product between FROM element(s) "students" and FROM element "groups".
# Apply join condition(s) between each element to resolve.
for it, gr in session.query(Students, Groups):
   print(it, gr)
print('*' * 30)

# Student [name: 박지원 None None, age: 16, adress: 제주특별자치도 용인시 기흥구 강남대가, ID group: 2 ] Group [ID: 1, GroupName: 1-MDA-7]
# Student [name: 박지원 None None, age: 16, adress: 제주특별자치도 용인시 기흥구 강남대가, ID group: 2 ] Group [ID: 2, GroupName: 1-MDA-9]
# Student [name: 박예원 None None, age: 21, adress: 강원도 괴산군 석촌호수29로 (현준김동), ID group: 1 ] Group [ID: 1, GroupName: 1-MDA-7]
# Student [name: 박예원 None None, age: 21, adress: 강원도 괴산군 석촌호수29로 (현준김동), ID group: 1 ] Group [ID: 2, GroupName: 1-MDA-9]

## 6) 다대다 관계의 테이블을 2개를 올리되, 특정칼럼만 찍히게 한다
for it, gr in session.query(Lessons.lesson_title, Groups.group_name):
   print(it, gr)
print('*' * 30)
# 수학 1-MDA-7
# 수학 1-MDA-9
# 프로그래밍 1-MDA-7
# 프로그래밍 1-MDA-9

## 6) 다대다 관계의 테이블을 2개를 특정 칼럼만 찍히게 올리되
## => filter로 관계테이블.c를 통해 일치시킨다?
## => m x n 조합 중에, 관계테이블에서 서로 일치하는 것만 나올 것이다.
for it, gr in session.query(Lessons.lesson_title, Groups.group_name).filter(and_(
        association_table.c.lesson_id == Lessons.id,
        association_table.c.group_id == Groups.id,
)):
   print(it, gr)
print('*' * 30)

# 수학 1-MDA-7
# 프로그래밍 1-MDA-7
# 철학 1-MDA-7
# 알고리즘 및 데이터 구조 1-MDA-7
# 선형대수학 1-MDA-7
# 통계 1-MDA-7
# 체육 1-MDA-7
# 수학 1-MDA-9
# 철학 1-MDA-9
# 선형대수학 1-MDA-9
# 체육 1-MDA-9

## 7) association_table에 2개 테이블을 join해놓고, .with_entities()로 원하는 정보만 추출할 수 도 있다.
# =>  ManyEntity select시, One의 정보1줄을 붙일 때 사용한다.
# => iter의 for변수에는 with_entities()에 적힌 갯수만큼 튜플로 나오니 나눠서 받을 수 있다.
for lesson, group in session.query(association_table)
   .join(Lessons, association_table.c.lesson_id == Lessons.id)
   .join(Groups, association_table.c.group_id == Groups.id)
   .with_entities(
      Lessons.lesson_title,
      Groups.group_name):
print(lesson, group)
print('*' * 30)
# 수학 1-MDA-7
# 프로그래밍 1-MDA-7
# 철학 1-MDA-7
# 알고리즘 및 데이터 구조 1-MDA-7
# 선형대수학 1-MDA-7
# 통계 1-MDA-7
# 체육 1-MDA-7
# 수학 1-MDA-9
# 철학 1-MDA-9
# 선형대수학 1-MDA-9
# 체육 1-MDA-9
# ******************************

## 8) 다대다를 query(A, B). filter( 관계테이블.c.)로 만들 때,
##    filter에 원하는 조건 1개만 더 추가하면 원하는 얻을 수 있따.
for it, gr in session.query(Lessons.lesson_title, Groups.group_name).filter(and_(
        association_table.c.lesson_id == Lessons.id,
        association_table.c.group_id == Groups.id,
        Groups.group_name == '1-MDA-9'
)):
   print(it, gr)
print('*' * 30)

# 수학 1-MDA-9
# 철학 1-MDA-9
# 선형대수학 1-MDA-9
# 체육 1-MDA-9
# ******************************

## 9) query에 2개 테이블을 다 안올려도, filter+관계테이블 조건만으로 한쪽테이블의 정보만 얻을 수 있다.
## => Filter에만 올려도 Groups테이블ㅇ 전체가 인식되나보다.
## => 그래도 query에 같이 올리고, 안쓸라면 _로 받아서 출력만 안하면 된다.
# for it in session.query(Lessons.lesson_title).filter(and_(
for it, _ in session.query(Lessons.lesson_title, Groups.group_name).filter(and_(
        association_table.c.lesson_id == Lessons.id,
        association_table.c.group_id == Groups.id,
        Groups.group_name == '1-MDA-9'
)):
   print(it)
print('*' * 30)
# ('수학',)
# ('철학',)
# ('선형대수학',)
# ('체육',)

# 수학
# 철학
# 선형대수학
# 체육

```