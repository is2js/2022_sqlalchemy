from sqlalchemy.exc import NoResultFound
from infra.entities.filmes import Filmes


class FilmesRepository:
    def __init__(self, ConnectionHandler) -> None:
        self.__ConnectionHandler = ConnectionHandler

    def select(self):
        with self.__ConnectionHandler() as db:
            data = db.session.query(Filmes).all()
            return data

    def select_drama_filmes(self):
        with self.__ConnectionHandler() as db:
            try:
                data = db.session\
                    .query(Filmes)\
                    .filter(Filmes.genre == "Drama")\
                    .one()
                return data
            except NoResultFound:
                return None
            except Exception as exception:
                db.session.rollback()
                raise exception

    def insert(self, title, genre, age):
        with self.__ConnectionHandler() as db:
            try:
                data_insert = Filmes(title=title, genre=genre, age=age)
                db.session.add(data_insert)
                db.session.commit()
                return data_insert
            except Exception as exception:
                db.session.rollback()
                raise exception

    def delete(self, title):
        with self.__ConnectionHandler() as db:
            db.session.query(Filmes).filter(Filmes.title == title).delete()
            db.session.commit()

    def update(self, title, age):
        with self.__ConnectionHandler() as db:
            db.session.query(Filmes).filter(Filmes.title == title).update({"age": age})
            db.session.commit()

