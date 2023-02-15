import datetime
import decimal
import enum
import json

import dateutil.parser
import sqlalchemy
from sqlalchemy import inspect

from .base import Base
from .connection import DBConnectionHandler

conn = DBConnectionHandler()
engine = conn.get_engine()

Session = conn.get_current_session()

truncate_query = {
    'mysql': 'TRUNCATE TABLE {};',
    'postgresql': 'TRUNCATE TABLE {} RESTART IDENTITY CASCADE;',
    'sqlite': 'DELETE FROM {};',
}

foreign_key_turn_off = {
    'mysql': 'SET FOREIGN_KEY_CHECKS=0;',
    'postgresql': 'SET CONSTRAINTS ALL DEFERRED;',
    'sqlite': 'PRAGMA foreign_keys = OFF;',
}

foreign_key_turn_on = {
    'mysql': 'SET FOREIGN_KEY_CHECKS=1;',
    'postgresql': 'SET CONSTRAINTS ALL IMMEDIATE;',
    'sqlite': 'PRAGMA foreign_keys = ON;',
}


def create_db(truncate: bool = False, drop_table: bool = False):
    print(conn)
    metadata = Base.metadata
    engine_name = engine.name

    # https://item4.blog/2016-03-30/Truncate-All-Tables-with-SQLAlchemy/
    # if truncate:
    #     # fk(Many)가 딸려있어라도 pk(One) 데이터 강제 삭제 가능
    #     engine.execute(foreign_key_turn_off[engine.name])
    #     for table in reversed(metadata.sorted_tables):
    #         engine.execute(truncate_query[engine_name].format(table.name))
    #     # fk(Many)가 딸려있으면 삭제 불가 on
    #     engine.execute(foreign_key_turn_on[engine.name])

    # if drop_table:
    #     metadata.drop_all(engine)

    if drop_table:
        for table in reversed(metadata.sorted_tables):
            if inspect(engine).has_table(table.name):
                table.drop(engine)

    # droptable이 걸려있으면 truncate안하도록
    if not drop_table and truncate:
        # fk(Many)가 딸려있어라도 pk(One) 데이터 강제 삭제 가능
        engine.execute(foreign_key_turn_off[engine_name])
        for table in reversed(metadata.sorted_tables):
            if inspect(engine).has_table(table.name):
                engine.execute(truncate_query[engine_name].format(table.name))
        # fk(Many)가 딸려있으면 삭제 불가 on
        engine.execute(foreign_key_turn_on[engine.name])

    metadata.create_all(engine)


# https://stackoverflow.com/questions/30840129/parsing-datetime-in-python-json-loads
# date와 time까지도 https://stackoverflow.com/questions/12122007/python-json-encoder-to-support-datetime
class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return {"val": obj.isoformat(), "_spec_type": "datetime"}
        elif isinstance(obj, (decimal.Decimal,)):
            return {"val": str(obj), "_spec_type": "decimal"}
        ## banner_type의 IntEnum타입이 super().default(obj)에 걸리면, 에러나서 나머지들은 그냥 통과해도 된다.?!
        # else:
        #     return super().default(obj)
        ## datetime은 한번더 json에 감싸서 저장된다. for json.loads
        # "add_date": {
        #                 "val": "2022-11-28T00:02:50.816838",
        #                 "_spec_type": "datetime"
        #             },


def dump_sqlalchemy(table_name=None, is_id_change=False):

    metadata = Base.metadata

    tables = {}
    for table in metadata.sorted_tables:
        if table_name and table_name != table.name:
            continue

        # 데이터를 뻥튀기를 위해, 백업후 bulk_insert할 때, pk제약조건에 걸릴시 -> id + 10000로 백업함. # ex> "id": 10001,
        if is_id_change:
            row_dict_list = []
            for row_dict in [dict(row) for row in engine.execute(table.select())]:
                row_dict["id"] = row_dict["id"] + 10000
                row_dict_list.append(row_dict)

            tables[table.name] = row_dict_list
        else:
            tables[table.name] = [dict(row) for row in engine.execute(table.select())]

        # https://www.geeksforgeeks.org/python-difference-between-json-dump-and-json-dumps/
        # 객체 or stringdump는 dumps 저장은 dump
        # datetime은 default를 지정안하면, 에러난다.
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable/36142844#36142844
        # return json.dumps(result, ensure_ascii=False, indent=4, default=str)
        # => https://www.bogotobogo.com/python/python-json-dumps-loads-file-read-write.php

    file_name = f'./backup_{datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")}.json'
    # tables_json = json.dumps(tables, ensure_ascii=False, indent=4, default=default)
    tables_json = json.dumps(tables, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
    with open(file_name, "w", encoding='utf-8') as f:
        f.write(tables_json)
        print("저장>>>", file_name)


CONVERTERS = {
    'datetime': dateutil.parser.parse,
    'decimal': decimal.Decimal,
}


def object_hook(obj):
    _spec_type = obj.get('_spec_type')
    if not _spec_type:
        return obj

    if _spec_type in CONVERTERS:
        return CONVERTERS[_spec_type](obj['val'])
    else:
        raise Exception('Unknown {}'.format(_spec_type))


def load_dump(file_name):
    tables = {}
    with open(file_name, "r", encoding='utf-8') as f:
        tables = json.load(f, object_hook=object_hook)

    return tables


# https://stackoverflow.com/questions/11668355/sqlalchemy-get-model-from-table-name-this-may-imply-appending-some-function-to
def get_class_by_tablename(tablename):
    """Return class reference mapped to table.

    :param tablename: String with name of table.
    :return: Class reference or None.
    """

    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__') and cls.__tablename__ == tablename:
            print(cls.__tablename__, "테이블 bulk 중...")
            return cls
    # raise ValueError(f'해당 tablename : {tablename}을 가진 Entity가 존재하지 않음.')


# http://www.lotdoc.cn/blog/detail/178/
def bulk_insert_from_json(file_name, table_name=None):
    metadata = Base.metadata
    session = Session()
    engine_name = engine.name

    tables = load_dump(file_name)

    engine.execute(foreign_key_turn_off[engine_name])

    for table in metadata.sorted_tables:
        if table_name and table.name != table_name:
            continue
        table_datas = tables[table.name]
        # print(table_datas) # [{'add_date': datetime.datetime(2022, 11, 25, 17, 58, 41, 579745),
        cls_by_name = get_class_by_tablename(table.name)
        if not cls_by_name:
            print(f"dump json 속 {table.name} 테이블이 Base에 메핑되지 않는 것으로 확인되어 건너띕니다.")
            continue
        session.bulk_insert_mappings(
            cls_by_name,
            table_datas
        )
    session.commit()

    engine.execute(foreign_key_turn_on[engine.name])
