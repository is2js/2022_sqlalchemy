from sqlalchemy import select
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. entitymodel 클래스 -> DB로 매핑할 때 클래스가 상속해야할 Class
Base = declarative_base()

# 3. entitymodel을 orm커맨드들의 commit/rollback을 담당해줄 session객체는
#  => (1) db와 직접연결된 engine이 필요로 한다 (enigne혼자 sql execute는 가능)
#     (2) sesionmaker로 engine을 넣어서 Session클래스를 만든다.
#     (3) Session클래스로 session객체를 만든다.
engine = create_engine("mysql+pymysql://root:564123@localhost:3306/cinema")
Session = sessionmaker(bind=engine)
session = Session()


# 2. Base클래스로 entity모델을 정의한다.
class Filmes(Base):
    __tablename__ = 'filmes'

    title = Column(String, primary_key=True)
    genre = Column(String, nullable=False)
    age = Column(Integer, nullable=False)

    def __repr__(self):
        return f"Filme (title={self.title}, age={self.age})"


# 4. engine -> sessionmaker -> Session클래스 -> session객체로
#    SQL 커맨드를 날릴 수 있다.


## 4-2. Insert : entity모델객체를 만들고 -> add + commit
# data_insert = Filmes(title="Batman", genre="Drama", age=2022)
# session.add(data_insert)
# session.commit()

## 4-4. delete : pk or uniquekey로 fileter를 해서 골라낸 뒤 -> .delete() 후 commit한다
## => filter_by가 아니라 filter(Entity.필드=)로 한다.
## => filter에 걸리는 게 없어도 에러는 안난다.
session.query(Filmes).filter(Filmes.title=="alguma coisa").delete()
session.commit()

## 4-5. update: filter(entity.필드)는 여러개 데이터가 걸릴 수 있다
##             => .update({})로 바꾸고 싶은 필드만 지정해서 한꺼번에 바꾼다.
session.query(Filmes).filter(Filmes.genre == "Drama").update({"age": 2000})
session.commit()



## 4-1. Select
data = session.query(Filmes).all()
print(data)


## 4-3. session객체는 직접 생성하면, -> 작업후 직접 close()해줘야한다.
session.close()
