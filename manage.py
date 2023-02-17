import datetime
import os

from pyecharts.charts.chart import Chart
from sqlalchemy import select, inspect
from sqlalchemy.orm import aliased

from src.config import db_config
from src.infra.config.connection import DBConnectionHandler, db
from src.infra.tutorial3 import *
from src.infra.tutorial3.common.base_query import StaticsQuery
from src.main.config import create_app


app = create_app(os.getenv('APP_CONFIG') or 'default')


# flask shell에 객체들을 미리 던져놓는다.
@app.shell_context_processor
def make_shell_context():

    return dict(db=db,
                select=select, inspect=inspect, aliased=aliased,
                User=User, Role=Role, Post=Post, Category=Category, Tag=Tag, posttags=posttags,
                StaticsQuery=StaticsQuery,
                chart=Chart(),
                today=datetime.date.today(),
                )
