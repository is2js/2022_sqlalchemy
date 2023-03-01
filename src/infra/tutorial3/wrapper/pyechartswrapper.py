import calendar
import datetime
import enum
from collections import defaultdict

from sqlalchemy.orm import Session

unit_name_map = {
    'ko': {
        'day': '일',
        'month': '월',
        'year': '년',
    },
    'en': {
        'day': 'th',
        'month': '(month)',  # 이것만 예외처리되서 축약형으로 들어감.
        'year': 'year'
    }
}


def get_unit_name_convert_method(unit, unit_name):
    if unit == 'day':
        # 2002-02-10 => 10일, 10th
        return lambda x: f'{int(x.split("-")[-1])}{unit_name_map[unit_name][unit]}'
    elif unit == 'month':
        # 2002-02 => 2월, 2month(X) Feb(예외처리)
        if unit_name == 'en':
            return lambda x: calendar.month_abbr[int(x.split("-")[-1])]
        return lambda x: f'{int(x.split("-")[-1])}{unit_name_map[unit_name][unit]}'
    elif unit == 'year':
        # 2002 => 2002년
        return lambda x: f'{x}{unit_name_map[unit_name][unit]}'
    else:
        raise NotImplementedError(f'Invalid unit: {unit}')


def get_model_name(model):
    return model.__table__.comment if model.__table__.comment \
        else model.__class__.name


def get_count_word(unit_name):
    return "수" if unit_name == "ko" else "count"


class Chart:

    def __init__(self, module) -> None:
        self._module = module

    def count_bar(self, model,
                  date_attr, interval, unit, end_date=None, srt_date=None,  # series + count_per_date_unit
                  include_end_date=True,  # series
                  count_attr=None, filter_by=None,  # count_per_date_unit
                  session: Session = None, unit_name='ko'
                  ):
        """
        1. 모듈을 넣어서 객체를 만들고, 메서드호출시 model을 받아서 만든다.
         - end_date를 생략하면, 오늘로부터 '7' 'day'동안의 interval한 데이터를 만든다.
         - 내부 'date'(series) + 'count'칼럼으로 이루어진 row를 dict로 변경하여 생성한다.
        c = Chart(pyecharts)
        c.count_bar(User, 'add_date', 7, 'day')
        => row: [('2023-02-22', 0), ('2023-02-23', 0), ('2023-02-24', 0), ('2023-02-25', 0), ('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 1)]
        => result: {
            'date': ['2023-02-22', '2023-02-23', '2023-02-24', '2023-02-25', '2023-02-26', '2023-02-27', '2023-02-28'],
            'count': [0, 0, 0, 0, 1, 3, 1]
        }

        2. 해당model에 filter추가
        c = Chart(pyecharts)
        c.count_bar(User, 'add_date', 7, 'day', filter_by=dict(is_administrator__eq=False))
        => rows:  [('2023-02-22', 0), ('2023-02-23', 0), ('2023-02-24', 0), ('2023-02-25', 0), ('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 0)]
        => result: {
            'date': ['2023-02-22', '2023-02-23', '2023-02-24', '2023-02-25', '2023-02-26', '2023-02-27', '2023-02-28'],
            'count': [0, 0, 0, 0, 1, 3, 0]
        }
        3. unit_name='ko' or 'en'

        => 'ko' {'date': ['1월', '2월', '3월'], 'count': [0, 5, 0]})
        => 'en' {'date': ['Jan', 'Feb', 'Mar'], 'count': [0, 5, 0]}
        """

        # end_date가 명시안되면 오늘로
        if not end_date:
            end_date = datetime.date.today()

        # 모델의 expressionmixin의 'date'/'count' dict 반환
        rows = model.count_for_interval(date_attr, end_date, interval, unit, srt_date=srt_date,
                                        include_end_date=include_end_date, count_attr=count_attr,
                                        filter_by=filter_by, session=session)

        if not rows:
            raise Exception('count_for_interval method error in ExpressionMixin')

        # 5) chart용으로서, dates 따로 / count 따로 필요할 것이다. -> dict에 담아서 각각 key로 뽑아쓰게 한다.
        #   -> execute결과는 row객체로서 keys()를 가지므로, 순회하면서 getattr
        result = self.rows_to_dict_list(rows)

        # 6) unit_name을 넣어주면, result(dict)의 'date'key의 string date들에 변환을 해준다.
        # rows: [('2023-02-22', 0), ('2023-02-23', 0), ('2023-02-24', 0), ('2023-02-25', 0), ('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 0)]
        # => result: {
        #     'date': ['2023-02-22', '2023-02-23', '2023-02-24', '2023-02-25', '2023-02-26', '2023-02-27', '2023-02-28'],
        #     'count': [0, 0, 0, 0, 1, 3, 0]
        # }
        # 'ko' => {'date': ['1월', '2월', '3월'], 'count': [0, 5, 0]})
        # 'en' => {'date': ['Jan', 'Feb', 'Mar'], 'count': [0, 5, 0]}
        if unit_name:
            result['date'] = list(
                map(get_unit_name_convert_method(unit, unit_name), result['date'])
            )

        # result + module로 차트 생성
        return (
            self._module.charts.Bar()
            .add_xaxis(result['date'])
            .add_yaxis(f'{get_model_name(model)} {get_count_word(unit_name)}',
                       result['count'])
        )

    # route에서도 Chart나 chart객체가 쓸 수 있게
    @classmethod
    def rows_to_dict_list(cls, rows):
        """
        (a, b, c) -> {a=[1,2,3], b=[1,2,3]. c=[1,2,3]}
        (1, 1, 1)
        (2, 2, 2)
        (3, 3, 3)

        rows: [('2023-02-22', 0), ('2023-02-23', 0), ('2023-02-24', 0), ('2023-02-25', 0), ('2023-02-26', 1), ('2023-02-27', 3), ('2023-02-28', 1)]
        => result: {
            'date': ['2023-02-22', '2023-02-23', '2023-02-24', '2023-02-25', '2023-02-26', '2023-02-27', '2023-02-28'],
            'count': [0, 0, 0, 0, 1, 3, 1]
        }
        """
        result_map = defaultdict(list)
        for row in rows:
            for key in row.keys():
                value = getattr(row, key)
                if isinstance(value, enum.Enum):
                    value = value.name  # enum은 name이 진짜 뽑고 싶은 값

                result_map[key].append(value)
        return result_map

    def count_bars(self, models,
                   date_attr, interval, unit, end_date=None, srt_date=None,  # series + count_per_date_unit
                   include_end_date=True,  # series
                   count_attr=None, filter_by_per_model=None,  # filter_by -> filter_by_per_model
                   session: Session = None, unit_name='ko'
                   ):
        """
         models(1개 or list여러개) 및 model별 filter_by를 dict로입력받는다.
        - subquery를 통해 생성 alias_map의 obj를 생성하지 않으므로, 관계필터링이 적용되지 않으므로
        => 관계를 적용하고 싶다면, 각 모델에 .has/.any를 이용한 @hybrid_property를 정의해서 사용한다

        c = Chart(pyecharts)

        c.count_bars(User, 'add_date', 7, 'day',
            filter_by_per_model={User : dict(is_administrator__eq=False) }
        )
        2. models(list)에 여러개를 입력하는 경우
        c.count_bars([User, Category], 'add_date', 7, 'day', filter_by_per_model={User : dict(is_administrator__eq=False) })

        """
        # model 1개시 처리
        if not isinstance(models, (list, tuple, set)):
            models = [models]

        # end_date가 명시안되면 오늘로
        if not end_date:
            end_date = datetime.date.today()

        # 미리 xaxis, yaxis안채운 bar개체 생성
        bar = self._module.charts.Bar()

        # date는 1번만 채우면 된다.
        filled_date = False
        for model in models:
            filter_by = None
            if model in filter_by_per_model:
                filter_by = filter_by_per_model[model]

            rows = model.count_for_interval(date_attr, end_date, interval, unit, srt_date=srt_date,
                                            include_end_date=include_end_date, count_attr=count_attr,
                                            filter_by=filter_by, session=session)
            if not rows:
                raise Exception('count_for_interval method error in ExpressionMixin')

            result = self.rows_to_dict_list(rows)
            if not filled_date:
                if unit_name:
                    result['date'] = list(
                        map(get_unit_name_convert_method(unit, unit_name), result['date'])
                    )
                bar = bar.add_xaxis(result['date'])

            bar = bar.add_yaxis(f'{get_model_name(model)} {get_count_word(unit_name)}',
                                result['count'])

        return bar
