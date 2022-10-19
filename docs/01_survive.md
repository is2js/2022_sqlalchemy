## 개발 순서

### 01 raw_sqlalchemy.py로 DB 및 CRUD 구현

```python
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. entitymodel가 상속해야할 Base 클래스 -> DB로 매핑할 때 클래스가 상속해야할 Class
Base = declarative_base()

# 3. entitymodel을 orm커맨드들의 commit/rollback을 담당해줄 session객체는
#  => (1) db와 직접연결된 engine이 필요로 한다 (enigne혼자 sql execute는 가능)
#     (2) sesionmaker로 engine을 넣어서 Session클래스를 만든다.
#     (3) Session클래스로 session객체를 만든다.
engine = create_engine("mysql+pymysql://root:root@localhost:3306/cinema")
Session = sessionmaker(bind=engine)
session = Session()


# 2. Base클래스를 상속한 entity모델을 정의한다.
class Filmes(Base):
    __tablename__ = 'filmes'

    title = Column(String, primary_key=True)
    genre = Column(String, nullable=False)
    age = Column(Integer, nullable=False)

    def __repr__(self):
        return f"Filme (title={self.title}, age={self.age})"

# 4. engine -> sessionmaker -> Session클래스 -> session객체로
#    ORM 커맨드를 날릴 수 있다. sessino객체를 만들었다면, .close()부터 해놓고 들어가자.
## 4-3. Insert : entity모델객체를 만들고 -> add + commit
data_insert = Filmes(title="Batman", genre="Drama", age=2022)
session.add(data_insert)
session.commit()

## 4-4. delete : pk or uniquekey로 fileter를 해서 골라낸 뒤 -> .delete() 후 commit한다
## => filter_by가 아니라 filter(Entity.필드=)로 한다.
## => filter에 걸리는 게 없어도 에러는 안난다.
session.query(Filmes).filter(Filmes.title=="alguma coisa").delete()
session.commit()

## 4-5. update: filter(entity.필드)는 여러개 데이터가 걸릴 수 있다
##             => .update({})로 바꾸고 싶은 필드만 지정해서 한꺼번에 바꾼다.
session.query(Filmes).filter(Filmes.genre == "Drama").update({"age": 2000})
session.commit()

## 4-2. Select
data = session.query(Filmes).all()
print(data)


## 4-1. session객체는 직접 생성하면, -> 작업후 직접 close()해줘야한다.
session.close()
```

### 02 구조 구성하기
1. infra > config > base.py 구현
2. infra > config > connection.py 구현
   1. DBConnectionHandler class 정의
   2. self.__connection_string 에 DB_URI 정의
   3. self.__engine = self.__create_database_engine() 정의
   4. def __create_database_engine(self) 정의
   5. def get_engine 정의
   6. self.session = None 정의
   7. enter/exit에서 session객체 생성하여 self.session 할당 -> .close()
3. infra > entities > table.py 정의
   1. infra.config.base의 Base객체 상속해서 구현
4. infra > repository > table_repository.py 정의
   1. infra.entities.table의  EntityModel + infra.config.connection의 DBConnectionHandler의 db객체의 session필드 사용
   2. raw_sqlalchemy에서 정의한 CRUD를 메서드로 정의(method 1개 개발마다 run.py 실행하여 테스트)
      1. select부터 개발하고, run.py에서 내려놓고, 나머지 위쪽에서 구현하면서 select 재활용, 다 순서대로 재활용
      2. select -> insert -> delete -> update
   3. run.py 정의
      1. infra.repository.table_repository의 TableRepository를 import
      2. repository객체.crud()메서드들을 정의한 것을 확인하면서 구현

### 03 ManyEntity 추가
1. 기존 것 drop 후 sql script실행해서 DB 테이블부터 다 생성
2. entities > OneEntity 복붙해서 ManyEntity 정의
   - 미리 생성한 DB의 column명과 완전히 동일하게 field명을 입력해야한다.
3. ManyRepository 정의 > method개발마다 run.py에 돌려 테스트
4. Many의 select는
   1. fk필드 옵션으로 ForeignKey("fk_tablename.primary_ket")) 설정 후 
   2. fk repository에서 select시 .join(FkEntityModel, Many.fk칼럼 == One.pk칼럼 ).with_entities().all()으로  
   3. 자식들정보에 부모정보들을 1:1매칭 1줄에 모조리 나타낼 수 있다.
5. One의 select는 
   1. 새로운필드 relationship("EntityName", backref="field로쓸명", lazy="subquery")로 
   2. 나를 fk로 가지는 children객체들을 필드로 추출할 수 있다.


### 04 Error처리는 Repository내 session필드로 / 단순CRUD외 메서드도 개발
1. DBConnectionHandler() 객체는 with절에서 .session필드에 세션을 달고 있으며, 예외발생시 
   1. session.rollback()한다
   2. raise exception을 발생시킨다.
2. 예외처리 순서
   1. where가 없는 단순 select -> .all() -> [] 반환으로 조회시 에러는 없다.
   2. insert -> Exception + rollback + raise 로 예외처리
   3. **`select_by_특정필드` 구현(여기선 특정필드값으로 구현 `select_특정필드값`**) == where있는 select -> (원래는 pk, uk를 통한 검색만) .one() -> NoResultFound
      1. select를 복사해서 구현한다
      2. except NoResultFound return None을 주더라도
      3. except Exception + rollback + raise 로 처리 한번 더 한다

3. 추가 처리는 [backend-python](https://github.com/is2js/backend-python/blob/master/src/infra/repo/user_repository.py) 레포지토리 참고

### 05 Repository method TEST를 위해 가짜session도입 및 Repository 구조 변경
1. pip3 install `mock-alchemy`, `pytest` 설치
2. xxx_repository_test.py 생성
   1. UnifiedAlchemyMagicMock로 [가짜 session] 객체 생성
   2. unittest의 mock으로 [테스트할 query] 작성(비워두면 3번 데이터 전체가 나오게 됨.)
   3. EntityModel로 만드는, 2번 테스트할 query를 날릴시 나와야할 [예상 정답]
   4. test_method 내부에서 [가짜session으로 테스트query를 날릴시 예상정답이 나오는지 response print]
   ```python
   # 1. 가짜 session 생성
   session = UnifiedAlchemyMagicMock(
       data=[
           (
               [
                   # 2. 테스트할 쿼리
                   mock.call.query(Filmes),
                   mock.call.filter(Filmes.genre == "MMM"),
               ],
               # 3. 테스트쿼리시 나와야할 데이터
               [Filmes(title="Rafael", genre="MMM", age=12), Filmes(title="Rafael1", genre="MMM", age=12)]
           )
       ]
   )
   ```
3. **repository를 `가짜session객체`으로 테스트하려면,  `session을 필드에 담는 객체를 만들어주는 DBConnectionHanlder가 respository로 주입`되도록 변경해야한다**
   1. 생성자가 없던 Repository class에 **생성자를 생성**하고 **import로 의존하던 DBConnectionHandler**를 import대신 생성자로 받는다.
      - 내부에서는 with () as db: 로 그대로 사용되어야하므로, 객체주입이 아닌, **Class자체를 주입**받는다?
      - DBConnectionHandler import를 지우고, self.__ConnectionHandler를 with절에 사용한다.
   2. 생성자가 추가됨으로 인해 **기존에 Repository를 인자없이 생성했떤 사용처들 모두, DBConnectionHandler를 import하고 Class를 주입해서 사용하도록 변경한다**

4. repo_test.py의 UnifiedAlchemyMagicMock는 session을 생성해줄 뿐이므로 **가짜session을 context manager로 품을 `ConnectionHandlerMock`클래스를 정의한다**
   1. ConnectionHandlerMock은 원본처럼, with절에서만 session이 유지되었다가 끊어지게할 필요없이 session을 유지해도 된다.
      - with절에 사용되므로 enter/exit는 원본에서 복붙해서 가져오되, **생성자의 `self.ssesion = `에 바로 UnifiedAlchemyMagicMock()로 만든 구문을 옮긴다.
      - enter에서는 return self만 있으면 되고, exit에서는 self.session.close()만 해주자.
   2. repository를 import하고, 각 method test에서, mock handler클래스를 주입하여, 가짜session을 사용해서 작동하도록 한다
   ```python
   class ConnectionHandlerMock:
       def __init__(self) -> None:
           # 1. 가짜 session 생성
           self.session = UnifiedAlchemyMagicMock(
               data=[
                   (
                       [
                           # 2. 테스트할 쿼리
                           mock.call.query(Filmes),
                           mock.call.filter(Filmes.genre == "MMM"),
                       ],
                       # 3. 테스트쿼리시 나와야할 데이터
                       [Filmes(title="Rafael", genre="MMM", age=12), Filmes(title="Rafael1", genre="MMM", age=12)]
                   )
               ]
           )
   
       def __enter__(self):
           return self
   
       def __exit__(self, exc_type, exc_val, exc_tb):
           self.session.close()
   ```
5. **repo의 개별 method를 test하게 될 때**
   1. UnifiedAlchemyMagicMock의 data는 **해당 method내부에서 실제 호출하는 쿼리 -> 테스트쿼리로 미리 입력/정답까지 넣어놔야한다**
      - select 메서드 내부 쿼리
           
          ![image-20221013004621063](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013004621063.png)
      - UnifiedAlchemyMagicMock의 data에 repo method의 테스트 쿼리 입력 -> 그에 따른 정답도 넣어놓기
          ![image-20221013005128536](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013005128536.png)

   2. setting한 예상정답이 잘 나오는지 print(response)부터 해보고 난 뒤, assert 작성 
   3. **method test를 늘일 때 마다 mock handler의 `UnifiedAlchemyMagicMock( data=[ ( ), ( )]`튜플로 -> 테스트할쿼리 + 예상정답**을 점차 늘려준다.

       ![image-20221013005711754](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013005711754.png)
       ![image-20221013005657608](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013005657608.png)
       ![image-20221013005729071](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013005729071.png)

6. **assert문 작성**시 유의할 사항 -> select 등에서 `예상정답 []`안에 `콤마없이, 모델객체 1개만 있다면 -> list가 아닌 해당 객체 1개만 return`된다.
       ![image-20221013010028787](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013010028787.png)
   1. return의 갯수에 따라 
      1. assert `isinstance(response, list)` + `isinstance(response[0], EntityModel)` or 
      2. assert `isinstance (response, EntityModel)` + `response.중요필드 == 예상정답객체필드값`으로 비교한다
         ![image-20221013010512432](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013010512432.png)

7. 사실상 entityModel이 나와야하는 select 이외에는 mock-alchemy가 딱히 안쓰이는 것 가탇
   1. insert -> 그대로 반환되니, 넣은 필드값을 검사하면 될듯
   2. update -> ?
   3. delete -> ?

### 06 alembic 으로 migration(DB 버전관리하기)
- [참고블로그](https://blog.neonkid.xyz/257?category=656103)

1. (venv) `pip3 install alembic`
2. `alembic init alembic`
   1. root에 alembic.ini 생성
   2. root에 alembic 폴더 생성

#### revision 생성과 구조
3. Create a migration script
   - `alembic revision -m "message"`
   - alembic > script.py.mako 에 있는 양식대로
   - alembic > versions > xxxx_message.py에 기록된다.
   - **revision을 만들어놓고 거기에 upgrade/downgrade작업을 명시해놓고, 시행할 예정이다**
     1. 인스턴스 이전
     2. 특정 entity 변경 ex> 칼럼 추가/삭제
     3. 칼럼, 테이블명 변경
     4. 데이터 추가/삭제

#### sqlalchemy.url 설정
4. **sqlalchemy.url 설정**
   - root > `alembic.ini` 파일은 ini파일로서 정적인 텍스트밖에 사용하지 못한다.
     - sqlalchemy.url 예시를 주석처리한다.
   - alembic > `env.py`에서 alembic 에서 제공하는 context -> config 객체를 통해 `sqlalchemy.url`을 python형태로 지정해줄 수 있다.
     1. DBConnectionHandler의 self.__connection_string 필드에 정의해둔 or 환경변수에 정의해둔 `db_url`을 사용할 수 있다.
        ```python
        from alembic import context

        # ...
        config = context.config        
        # ...
        # set sqlalchemy.url
        db_url = "mysql+pymysql://root:564123@localhost:3306/cinema"
        if not config.get_main_option('sqlalchemy.url'):
            config.set_main_option('sqlalchemy.url', db_url)
        ```

#### 예제1 수동 table 생성/삭제 revision으로 upgrade
5. 예제1: alembic 제공 op로 객체로 table 생성을 upgrade -> table삭제를 downgrade 직접 작성 
   1. 만든 revision_message.py  내부 upgrade()에 table 생성 코드를 작성한다
      ```python
       def upgrade() -> None:
           op.create_table(
               'account',
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.String(50), nullable=False),
               sa.Column('description', sa.Unicode(200))
           )
      ```
      
   2. `alembic upgrade head`를 통해, 현재 가리키는 revision의 업그레이드를 시행한다.
      - **문제는 이런 방식으로 db를 생성하면, entity도 직접 생성해줘야한다..?!**
          ![image-20221013223318236](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013223318236.png)
          ![image-20221013223434306](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013223434306.png)
   3. revision_message.py에 dowgrade()를 대비한 코드도 작성해줘야한다.
      ```python
       def downgrade() -> None:
           op.drop_table('account')
      ```
   4. `alembic downgrade -1`로 직전(None)으로 돌아가는 다운그레이드를 통해, upgrade행위를 반대로 시행한다
      ![image-20221013223910830](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221013223910830.png)

   5. 다음 예시를 위해 현재 head가 가리키는 revision(first)로 업그레이드 해준다.
      - `alembic upgrade head`
      
#### 예제2 repo객체로 데이터 추가/삭제 revision 만들기
6. 예제2: revision second를 `repository`를 통한 데이터추가/삭제를 up/downgrade로 지정
   1. revision을 생성한다 `alembic -m "second"`
   2. 생성된 revisionhash_message.py에 repository import 후 upgrade/downgrade 작성
      ```python
       from infra.repository.filmes_repository import FilmesRepository
       from infra.config.connection import DBConnectionHandler
       
       
       # revision identifiers, used by Alembic.
       revision = '771ed7ecd00f'
       down_revision = '9b8e38bf91e3'
       branch_labels = None
       depends_on = None
       
       
       def upgrade() -> None:
           filmes_repository = FilmesRepository(DBConnectionHandler)
           filmes_repository.insert(title='JJS', genre='Drama', age=123)
       
       
       def downgrade() -> None:
           filmes_repository = FilmesRepository(DBConnectionHandler)
           filmes_repository.delete('JJS')
      ```
   3. `alembic upgarde head`
      - upgrade head는 최신revision까지 다 반영한다는 뜻이다?!
      - OneEntity에 ManyEntity가 relation으로 등록되어있으면, ManyEntity도 import해줘야 오류가 안난다


#### 예제3 DBConnectionHandler가 뱉어내는 engine으로 execute + sql query로 데이터 추가/삭제
1. `alembic revision -m "third"`
2. _third.py에 DBConnectionHandler import -> get_engine -> execute
      ```python
      from infra.config.connection import DBConnectionHandler
      
      # revision identifiers, used by Alembic.
      revision = 'a4b4d5f611ea'
      down_revision = '771ed7ecd00f'
      branch_labels = None
      depends_on = None
      
      
      def upgrade() -> None:
          db_connection_handler = DBConnectionHandler()
          engine = db_connection_handler.get_engine()
          engine.execute(
              """
              INSERT INTO filmes (title, genre, age)
              VALUES 
              ('JJS1', 'Drama',  777);
              """
          )
      
      
      def downgrade() -> None:
          db_connection_handler = DBConnectionHandler()
          engine = db_connection_handler.get_engine()
          engine.execute(
              """
              DELETE FROM filmes
              WHERE title='JJS1';
              """
          )      
      ```
3. `alembic upgrade head`

#### None으로 downgrade 연속적으로 하기

1. `alembic upgrade -1` 3번
2. `alembic history`
771ed7ecd00f -> a4b4d5f611ea (head), third
9b8e38bf91e3 -> 771ed7ecd00f, second
<base> -> 9b8e38bf91e3, first


#### 01 alembic 없이 ORM -> DB create(only)

##### 전체 Entity 한번에 생성(Base + engine + Entities)

1. **python console**을 열고

2. **Base**객체와 engine객체 생성을 위한 **DBConnnectionHandler** import

3. **Entity들을 메모리에 올리기**위한 entity import

4. **Base.metadata.create_all( engnine )**명령어로 생성

   ```python
   from infra.config.base import Base
   from infra.config.connection import DBConnectionHandler
   
   from infra.entities import *
   
   #with DBConnectionHandler() as db:
   #    Base.metadata.create_all(db.get_engine())
   engine = DBConnectionHandler().get_engine()
   Base.metadata.create_all(engine)
   ```

   

   

##### 특정 Entity만 + engine으로 생성

1. **python console**을 열고

2. engine객체 생성을 위한 **DBConnnectionHandler** import

3. **특정 entity** import

4. Entity.`__table__`.create( **engine** )

   ```python
   from infra.config.connection import DBConnectionHandler
   
   from infra.entities import Entity
   
   
   Entity.__table__.create_db(engine)
   ```

   



#### 02 alembic을 이용한 ORM -> DB 수정

1. **terminal**을 열고

2. alembic 설치 및 alembic 초기화

   ```shell
   pip3 install alembic
   
   alembic init alembic
   ```

3. alembic 설정

   1. ./**alembic.init 내부 sqlalchemy.url 주석** 처리

   2. ./**alembic/versions/env.py 설정**

      1. **config객체에 sqlalchemy.url** main_option 추가

         ```python
         config = context.config        
         
         # set sqlalchemy.url
         db_url = "mysql+pymysql://root:564123@localhost:3306/cinema"
         if not config.get_main_option('sqlalchemy.url'):
             config.set_main_option('sqlalchemy.url', db_url)
         ```

      2. **target_metadata**에 **Base의 .metadata** 할당 및 **`entity들 메모리에 띄워두기`(필수)**

         ```python
         # target_metadata = None
         
         from infra.config.base import Base
         from infra.entities import *
         
         target_metadata = Base.metadata
         ```

      3. **run_migrations_online**메서드에 **칼럼Type까지 비교**하도록 **context.configure에 `compare_type=True` 추가하기**

         ```python
         def run_migrations_online() -> None:
             #...
             with connectable.connect() as connection:
                 context.configure(
                     #...
                     compare_type=True
                 )
         
         ```

4. **DB생성해놓은 상태에서 revision최초 하나 만들어주기**

   ```powershell
   alembic revision -m "init entites"
   alembic upgrade head
   ```

5. **Entity모델들을 수정한 뒤, alembic으로 DB 업데이트하기**

   - **절대 DB를 수작업으로 건들면 안된다.**
     - ORM수정에 따른 01 ORM으로 DB생성은 무시하면서 인식유지되더라
   - **`Entity .py를 삭제`할 땐, `init에 걸어둔 것도 같이삭제`하자**

   ```powershell
   # entity 수정후
   alembic revision --autogenerate -m "add column"
   alembic upgrade head
   ```

   

   

   





