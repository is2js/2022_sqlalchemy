import datetime
import os

from sqlalchemy import select

from src.infra.config.connection import DBConnectionHandler
from src.infra.config.pyechart_wrapper import Chart
from src.infra.config.query import StaticsQuery
from src.infra.tutorial3 import *
from src.main.config import create_app

app = create_app(os.getenv('APP_CONFIG') or 'default')


# flask shell에 객체들을 미리 던져놓는다.
@app.shell_context_processor
def make_shell_context():
    db = DBConnectionHandler()
    Session = db.get_current_session()
    db.session = Session()

    return dict(db=db, select=select,
                User=User, Role=Role, Post=Post, Category=Category, Tag=Tag, posttags=posttags,
                StaticsQuery=StaticsQuery,
                chart=Chart(),
                today=datetime.date.today()
                )
