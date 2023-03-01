import datetime

from sqlalchemy.orm import Session


class Chart:

    def __init__(self, module) -> None:
        self._charts = module.charts
        self._options = module.options

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

        2. 해당model에 filter추가
        c = Chart(pyecharts)
        c.count_bar(User, 'add_date', 7, 'day', filter_by=dict(is_administrator__eq=False))
        """

        # end_date가 명시안되면 오늘로
        if not end_date:
            end_date = datetime.date.today()

        # 모델의 expressionmixin의 'date'/'count' dict 반환
        result_map = model.count_for_interval(date_attr, end_date, interval, unit, srt_date=srt_date,
                                              include_end_date=include_end_date, count_attr=count_attr,
                                              filter_by=filter_by, session=session, unit_name=unit_name)
        if not result_map:
            raise Exception('count_for_interval method error in ExpressionMixin')

        # result + module로 차트 생성
        return (
            self._charts.Bar()
            .add_xaxis(result_map['date'])
            .add_yaxis(f'{self.get_model_name(model)} {self.get_count_word(unit_name)}',
                       result_map['count'])
        )

    def get_model_name(self, model):
        return model.__table__.comment if model.__table__.comment \
            else model.__class__.name

    def get_count_word(self, unit_name):
        return "수" if unit_name == "ko" else "count"


    def count_bars(self, models,
                  date_attr, interval, unit, end_date=None, srt_date=None,  # series + count_per_date_unit
                  include_end_date=True,  # series
                  count_attr=None, filter_by_per_model=None,  # filter_by -> filter_by_per_model
                  session: Session = None, unit_name='ko'
                  ):
        """
        1. models(1개 or list여러개) 및 model별 filter_by를 dict로입력받는다.
        c = Chart(pyecharts)
        c.count_bars([User, Category], 'add_date', 7, 'day',
                filter_by_per_model={User : dict(is_administrator__eq=False) }
            )

        """
        # model 1개시 처리
        if not isinstance(models, (list, tuple, set)):
            models = [models]

        # end_date가 명시안되면 오늘로
        if not end_date:
            end_date = datetime.date.today()

        # 미리 xaxis, yaxis안채운 bar개체 생성
        bar = self._charts.Bar()

        # date는 1번만 채우면 된다.
        filled_date = False
        for model in models:
            filter_by = None
            if model in filter_by_per_model:
                filter_by = filter_by_per_model[model]

            result_map = model.count_for_interval(date_attr, end_date, interval, unit, srt_date=srt_date,
                                                  include_end_date=include_end_date, count_attr=count_attr,
                                                  filter_by=filter_by, session=session, unit_name=unit_name)
            if not result_map:
                raise Exception('count_for_interval method error in ExpressionMixin')

            if not filled_date:
                bar  = bar.add_xaxis(result_map['date'])
            bar = bar.add_yaxis(f'{self.get_model_name(model)} {self.get_count_word(unit_name)}',
                       result_map['count'])

        return bar