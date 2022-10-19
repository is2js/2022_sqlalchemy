from src.infra.config.db_creator import create_db, Session

from src.infra.models import *


def _load_fake_data(session):
    group1 = Groups(group_name='1-MDA-7')
    group2 = Groups(group_name='1-MDA-9')
    session.add(group1)
    session.add(group2)
    session.commit()
    session.close()


def create_database(load_fake_data: bool = False):
    create_db()

    if load_fake_data:
        _load_fake_data(Session())