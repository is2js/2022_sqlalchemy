from infra.config.connection import DBConnectionHandler
from infra.entities.artists import Artists
from infra.entities.filmes import Filmes


class ArtistsRepository:

    def select(self):
        with DBConnectionHandler() as db:
            data = db.session \
                .query(Artists) \
                .join(Filmes, Artists.title_filmes == Filmes.title)\
                .with_entities(
                    Artists.name,
                    Filmes.genre,
                    Filmes.title,
                )\
                .all()
            # SAWarning: SELECT statement has a cartesian product between FROM element(s) "artists" and FROM element "filmes".  Apply join condition(s) between each element to resolve.
            #   Filmes.title,
            # [('Tom Hanks', 'Drama', 'Forest Gump')]
            # =>
            # [('Tom Hanks', 'Drama', 'Forest Gump'), ('algumAtor', 'Drama', 'Forest Gump')]
            # [('Tom Hanks', 'Drama', 'Forest Gump'), ('algumAtor', 'Drama', 'Forest Gump'), ('something', 'Drama', 'Forest Gump')]
            return data

    def insert(self, name, title_filmes):
        with DBConnectionHandler() as db:
            data_insert = Artists(name=name, title_filmes=title_filmes)
            db.session.add(data_insert)
            db.session.commit()

    def delete(self, id):
        with DBConnectionHandler() as db:
            db.session.query(Artists).filter(Artists.id == id).delete()
            db.session.commit()

    def update(self, id, name):
        with DBConnectionHandler() as db:
            db.session.query(Artists).filter(Artists.id == id).update({"name": name})
            db.session.commit()
