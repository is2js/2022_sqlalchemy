from src.infra.config.connection import DBConnectionHandler
from src.infra.repository.filmes_repository import FilmesRepository
from src.infra.repository.artists_repository import ArtistsRepository

# repo = FilmesRepository()
repo = ArtistsRepository()

# repo.insert("asdf", "comedy", 2010)
# repo.delete("Batman")

# data = repo.select()
# print(data)
# [('Tom Hanks', 'Drama', 'Forest Gump') <- join().with_entities().all()로 fk테이블 정보를 1줄로 붙여서 나타낼 수 있다.

repo2 = FilmesRepository(DBConnectionHandler)
# data2 = repo2.select()
# print(data2)
# relationship에 backref=, lazy="subquery"까지 주면,
# -> 나를 fk로 가지는 자식들을 필드로 뽑아볼 수 있다.
# [Filme (title=Forest Gump, age=1994, artists=[Artists (name=Tom Hanks, filme=Forest Gump), Artists (name=algumAtor, filme=Forest Gump), Artists (name=something, filme=Forest Gump)])]


data3 = repo2.select_drama_filmes()
print(data3)
# Filme (title=Forest Gump, age=1994, artists=[Artists (name=Tom Hanks, filme=Forest Gump), Artists (name=algumAtor, filme=Forest Gump), Artists (name=something, filme=Forest Gump)])
# .one()이 없다면
# sqlalchemy.exc.NoResultFound: No row was found when one was required
# 예외처리후 None
