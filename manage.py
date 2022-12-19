import os

from src.infra.config.connection import DBConnectionHandler
from src.infra.tutorial3 import User, Role
from src.main.config import create_app

app = create_app(os.getenv('APP_CONFIG') or 'default')


# flask shell에 객체들을 미리 던져놓는다.
@app.shell_context_processor
def make_shell_context():
    return dict(db=DBConnectionHandler(), User=User, Role=Role)
