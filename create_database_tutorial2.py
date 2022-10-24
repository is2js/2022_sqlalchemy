from src.infra.config.db_creator import create_db, Session
from src.infra.tutorial2 import *


def _load_fake_data(session: Session):
    ...


def create_database(load_fake_data: bool = True):
    create_db()

    if load_fake_data:
        _load_fake_data(Session())
