from sqlalchemy import and_, or_, select

from src.infra.config.connection import DBConnectionHandler

op_dict = {
    "==": "eq",
    "!=": "ne",
    ">": "gt",
    "<": "lt",
    ">=": "ge",
    "<=": "le",
    "like": "like",
    "ilike": "ilike",
    "in": "in",
    "notilike": "notilike",
    "is": "is_",
    "isnot": "isnot",
}

class BaseQuery:

    @classmethod
    def create_columns(cls, model, columns=None):
        """
        return a list of columns from the model
        - https://vscode.dev/github/adpmhel24/jpsc_ordering_system
        :param model:
        :param columns: string list ex> ['id', 'name']
        :return:
        """
        if not columns:
            return [model]

        cols = []
        for col in columns:
            attr = getattr(model, col, None)  # 꺼내보고 None이면 에러를 내기
            if not attr:
                raise Exception(f'Invalid column name: {col}')
            cols.append(attr)

        return cols

    @classmethod
    def create_filter(cls, model, filters):
        """
        재귀를 이용하여, and_or_or(key)의 내부들을 연결한다.
        return sqlalchemy's filter
        :param model:
        :param filters: filter dict -> 기본적으로 {'and': [(col_name, op, value)]} , {'or': { 'and': 조건1, 'and': 조건2} } 형식으로 사용한다.
            filters = {
                'or_1':{
                    'and': [('id', '>', 5), ('id', '!=', 3)],
                    'and': [('name', '==', 'cho')]
                },
                'and': [ ('age', '>', 20)]
            }
        :return: sqlalchemy's filter
        """
        # 1. where(* cls.method) 형태로 unpack될 것이므로, 아무것도 없다면, 빈 list가 풀어지게 하자.
        # -> 또한 재귀의 종착역?!
        if not filters:
            return []

        # 2.
        filt = []
        for filter_op in filters:
            # 1) dict의 value가 dict면, key가 'and' -> value dict 요소들을 [ value를 자신인자(filters)로 재귀메서드호출->list반환->*unpacking]한 뒤, and_()로 연결 / key가 'or' -> or_()로 연결이다.
            ## 재귀(바로 결과물 filt list가 반환된다)
            if type(filters[filter_op]) == dict:
                if 'and' in filter_op:
                    filt.append(
                        and_(*cls.create_query_filter(model, filters[filter_op]))
                    )
                elif 'or' in filter_op:
                    filt.append(
                        or_(*cls.create_query_filter(model, filters[filter_op]))
                    )
                else:
                    raise Exception(f'invalid filter operator: {filter_op}')

                continue
            ## continue로 인한 비재귀(value가 tuple list)인 경우 -> key(and or)에 따라 filter묶음을 만들어서 순서대로 append해주면 된다.
            # -> 한번에 조건들을 filt_aux에 순서대로 append해놓고, key에 따라 전체를 and_() 하거나 or_()로 묶을 것이다.
            filt_aux = []
            for raw in filters[filter_op]:
                # 1) try로 unpack가능한 (,,)인지 확인
                try:
                    col_name, op_name, value = raw
                except:
                    raise Exception(f'Invalid filter: {raw}')

                # 2) model.column 꺼내기
                column = getattr(model, col_name)
                if not column:
                    raise Exception(f'Invalid column: {col_name}')

                # 3) op string -> op attribute로 변환
                if op_name not in op_dict:
                    raise Exception(f'Invalid filter operator: {op_name}')

                # 3-1) in연산자만 attr확인없이 1개의 sqlachemy연산이 되므로 바로 filt_aux에 추가하면 된다.
                if op_dict[op_name] == 'in':
                    filt_aux.append(column.in_(value))
                    continue

                # 3-2) in이 아닌 다른 연산자들은 연산메서드(attribute)로 바꿔서 적용한 filter를 append
                #      -> hasattr()로 확인한 결과 연산메서드가 하나도 안나오면 에러를 낸다.
                # try:
                #     op = op_dict[op_name]
                #     attr = list(filter(lambda x: hasattr(column, x), [op, f'{op}_', f'__{op}__']))[0]
                #     print(attr)
                # except IndexError:
                #     raise Exception(f'Invalid operator name {op_name}')
                # 3.6+ 버전 -> next( (generator by comp) , None) -> 없으면 None이 나옴. 있다면 true인 것 첫번째가 나올 것이다.
                #             next( (generator by comp)) -> 없으면 StopIteration으로 except를 catch해도 된다.
                operator = op_dict[op_name]
                attr = next((op for op in (operator, f'{operator}_', f'__{operator}__') if hasattr(column, op)), None)
                if not attr:
                    raise Exception(f'Invalid filter operator name: {op_name}')

                # 4) value가 json의 null이 올 수도
                if value == 'null':
                    value = None

                # filt_aux에 해당column의  해당연산메서드attr를 꺼내서, value를 호출한 filter를 append
                filt_aux.append( getattr(column, attr)(value))

            # 5. filt_aux에 모아진 column.operatr(value) 필터내용들을, 비재귀 tuple list의 key(filter_op)로 통합
            if 'and' in filter_op:
                filt.append(and_(*filt_aux))
            elif 'or' in filter_op:
                filt.append(or_(*filt_aux))
            else:
                raise Exception(f'Invalid filter operator: {filter_op}')

        return filt

    # columns, filters를 둘다 받아 내부에서 사용 + 실행은 안한 쿼리 -> .first()일지 .all()일지도 밖에서 결정한다.
    @classmethod
    def create_select_query(cls, model, columns=None, filters=None):
        with DBConnectionHandler() as db:
            return db.session.scalars(
                select(*cls.create_columns(model, columns=columns))
                .where(*cls.create_filter(model, filters))
            )





