import os
from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path("./.env")
load_dotenv(dotenv_path=dotenv_path)


class Settings:
    # project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION")

    # database
    DB_CONNECTION = os.getenv("DB_CONNECTION").lower()

    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_SERVER = os.getenv("DB_SERVER", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "test")

    ## sqlite인 경우 양식이 다르다.
    if DB_CONNECTION == "sqlite":
        ## sqlite를 메모리로 쓰는 경우 for fake data + CRUD 연습
        if DB_NAME == 'memory':
            DATABASE_URL = f"sqlite:///:memory:"
        ## sqlite를 file로 쓰는 경우
        else:
            DATABASE_URL = f"sqlite:///{DB_NAME}.db"
    else:
        DATABASE_URL = f"{DB_CONNECTION}://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}"
    print("*" * 15 + f"DATABASE_URL: {DATABASE_URL}" + "*" * 15)

    # jwt. Watch out -> int( None )
    TOKEN_KEY = os.getenv("TOKEN_KEY")
    EXP_TIME_MIN = int(os.getenv("EXP_TIME_MIN", "30"))
    REFRESH_TIME_MIN = int(os.getenv("REFRESH_TIME_MIN", "15"))


settings = Settings()
