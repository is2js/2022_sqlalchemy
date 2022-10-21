from src.infra.config.db_creator import create_db, Session, engine, Base

from src.infra.tutorial import *


def _load_fake_data(session):
    ...


def create_database(load_fake_data: bool = False):
    create_db()

    if load_fake_data:
        _load_fake_data(Session())