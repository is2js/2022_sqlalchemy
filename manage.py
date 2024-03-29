import datetime
import os

import pyecharts
from dateutil.relativedelta import relativedelta
from flask import request
from sqlalchemy import select, inspect, func, text
from sqlalchemy.orm import aliased

from src.infra.config.connection import db, DBConnectionHandler
from src.infra.tutorial3 import *
from src.infra.tutorial3.auth import TodoType, Todo
from src.infra.tutorial3.mixins.base_query import BaseQuery
from src.infra.tutorial3.wrapper.chartwrapper import Chart
from src.main.config import create_app


app = create_app(os.getenv('APP_CONFIG') or 'default')


# flask shell에 객체들을 미리 던져놓는다.
@app.shell_context_processor
def make_shell_context():

    return dict(db=db,
                select=select, inspect=inspect, aliased=aliased, func=func, text=text,
                User=User, Role=Role, Post=Post, Category=Category, Tag=Tag, posttags=posttags,
                Banner=Banner,
                PostPublishType=PostPublishType,
                EmployeeDepartment=EmployeeDepartment,
                Employee=Employee,
                Department=Department,
                EmployeeInvite=EmployeeInvite,
                JobStatusType=JobStatusType,
                Roles=Roles,
                Comment=Comment,
                TodoType=TodoType,
                Todo=Todo,
                BaseQuery=BaseQuery,
                Chart=Chart,
                today=datetime.date.today(),
                relativedelta=relativedelta,
                pyecharts=pyecharts,
                DBConnectionHandler=DBConnectionHandler,
                )
