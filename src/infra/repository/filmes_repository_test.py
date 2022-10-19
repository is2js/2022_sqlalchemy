from unittest import mock
from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from infra.entities.filmes import Filmes
from infra.entities.artists import Artists
from infra.repository.filmes_repository import FilmesRepository


class ConnectionHandlerMock:
    def __init__(self) -> None:
        # 1. 가짜 session 생성
        self.session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        # 2. 테스트할 쿼리
                        mock.call.query(Filmes),
                        mock.call.filter(Filmes.genre == "Drama"),
                    ],
                    # 3. 테스트쿼리시 나와야할 데이터
                    [Filmes(title="Rafael", genre="Drama", age=12)]
                ),
                (
                    [mock.call.query(Filmes)],
                    [Filmes(title="Rafael", genre="Drama", age=12), Filmes(title="Rafael", genre="Drama", age=12)]
                )
            ]
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


# 4. 가짜session으로 쿼리 날리면, 가짜DB 중 가짜query로 모은 데이터에서, 결과를 추출한다
# => repr는 내가 정의한 대로 그대로 가져온다.
# => relationship이 있다면, 그 Model도 import는 해놔야 에러가 안난다.
# def test_select():
#     response = session.query(Filmes).filter(Filmes.genre == "MMM").all()
#     print()
#     print(response)
#     response = session.query(Filmes).all()
#     print()
#     print(response)
#     # Filme (title=Forest Gump, age=1994, artists=[Artists (name=Tom Hanks, filme=Forest Gump), Artists (name=algumAtor, filme=Forest Gump), Artists (name=something, filme=Forest Gump)])
#

def test_select_drama_filmes():
    filmes_repository = FilmesRepository(ConnectionHandlerMock)
    response = filmes_repository.select_drama_filmes()
    print()
    print(response)
    # 예상정답: [Filmes(title="Rafael", genre="Drama", age=12)]
    assert isinstance(response, Filmes)
    assert response.title == 'Rafael'


def test_select():
    filmes_repository = FilmesRepository(ConnectionHandlerMock)
    response = filmes_repository.select()
    print()
    print(response)
    # 예상정답: [Filmes(title="Rafael", genre="Drama", age=12), Filmes(title="Rafael", genre="Drama", age=12)]
    assert isinstance(response, list)
    assert isinstance(response[0], Filmes)

def test_insert():
    filmes_repository = FilmesRepository(ConnectionHandlerMock)
    response = filmes_repository.insert(title="abc", genre="asdf",age=12)
    print()
    print(response)
    assert response.title == "abc"

