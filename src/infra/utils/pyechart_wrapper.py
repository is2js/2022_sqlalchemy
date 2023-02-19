from collections import defaultdict

import pyecharts

from src.infra.tutorial3.mixins.base_query import StaticsQuery


class Chart:

    def __init__(self) -> None:
        # 주입으로 변경하기
        self._charts = pyecharts.charts
        self._opts = pyecharts.options

    #########
    # Bar   # -> only count
    #########
    def create_count_bar(self, model, date_column_name, end_date,
                         interval_unit=None, interval_value=None, start_date=None,
                         filters=None,
                         add_korean=True
                         ):
        """
        chart.create_count_bar(User, 'add_date', date.today(),
                                                 interval_unit='day', interval_value=7,
                                                 filters={'and': [('is_administrator', '==', False)]}
                                                 )
        <pyecharts.charts.basic_charts.bar.Bar object at 0x0000024D3D6FEF98>
        dir() -> 'chart_id', 'colors', 'dump_options', 'dump_options_with_quotes', 'extend_axis', 'get_options', 'height', 'js_dependencies', 'js_functions', 'js_host', 'load_javascript', 'options', 'overlap', 'page_title', 'render', 'ren
        der_embed', 'render_notebook', 'renderer', 'reversal_axis', 'set_colors', 'set_global_opts', 'set_series_opts', 'theme', 'width']

        """
        # result : {
        #             'date': ['3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월', '1월', '2월'],
        #             'count': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        #         }
        result = StaticsQuery.count_for_interval(model, date_column_name, end_date, interval_unit=interval_unit,
                                                 interval_value=interval_value, start_date=start_date, filters=filters,
                                                 add_korean=add_korean)

        # 이미 동적으로 comment를 채워주지만, 동적 comment채움을 적용하지 않는 model에 대해서, cls.__nname__으로 대체
        model_comment = model.__table__.comment if model.__table__.comment else model.__class__.name

        bar_chart = (
            self._charts.Bar()
            .add_xaxis(result['date'])
            .add_yaxis(f'{model_comment} 수', result['count'])
        )
        # print('user_chart  >> ', user_chart)

        return bar_chart

    # model -> models  + filters -> filter_with_model로 바뀐다.
    def create_count_bars(self, models, date_column_name, end_date,
                          interval_unit=None, interval_value=None, start_date=None,
                          filters_with_model=None,
                          add_korean=True):
        """
        chart.create_count_bars([User, Employee, Post, Category, Banner, Tag], 'add_date', date.today(), interval_unit='month', interval_value=12,
                                             filters_with_model={
                                                 User: {'and': [('is_administrator', '==', False)]},
                                                 Employee: {'and': [('name', '==', '관리자')]},
                                             })
        <pyecharts.charts.basic_charts.bar.Bar object at 0x0000024D3D6FEF98>
        dir() -> 'chart_id', 'colors', 'dump_options', 'dump_options_with_quotes', 'extend_axis', 'get_options', 'height', 'js_dependencies', 'js_functions', 'js_host', 'load_javascript', 'options', 'overlap', 'page_title', 'render', 'ren
        der_embed', 'render_notebook', 'renderer', 'reversal_axis', 'set_colors', 'set_global_opts', 'set_series_opts', 'theme', 'width']

        """
        # result : {
        #             'date': ['3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월', '1월', '2월'],
        #             'count': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        #         }
        # 혹시나 model만 입력한 경우, 혹은 1개 처리를 대신할 경우
        if not isinstance(models, (list, tuple, set)):
            models = [models]

        has_date = None
        bar_chart = self._charts.Bar()

        for model in models:
            filters = None
            if model in filters_with_model:
                filters = filters_with_model[model]

            temp_result = StaticsQuery.count_for_interval(model, date_column_name, end_date,
                                                          interval_unit=interval_unit,
                                                          interval_value=interval_value, start_date=start_date,
                                                          filters=filters,
                                                          add_korean=add_korean)
            # 한번 date를 구하면 안구한다.
            if not has_date:
                bar_chart = bar_chart.add_xaxis(temp_result['date'])
            # 각 model별 count를 한국테이블명(comennt)와 함께 count list를 넣어준다.
            model_comment = model.__table__.comment if model.__table__.comment else model.__class__.name
            bar_chart = bar_chart.add_yaxis(f'{model_comment} 수', temp_result['count'])

        return bar_chart

    #########
    # pie   # -> not only count
    #########

    #### 외부용
    def create_pie(self, model, col_name, agg='count',
                   filters=None,
                   is_distinct=False,
                   descending=True,
                   limit=5):
        """
        - agg=''에는 StaticQuery.agg()의  agg_dict = {'칼럼명' : ['집계', '종류']}의 집계종류를 넣어주자.
        - 데이터가 없는 경우 [('데이터없음', 0)]의 tuple list가 들어간다.
        chart.create_pie(User, 'sex', agg='count',
                                              filters={'and': [('is_administrator', '==', False)]}
                                              )


        """

        # pie chart=> .agg() 집계 중에 col_name에 대한 1개 집계만 한다.
        # result = [('미정', 1)]
        # result = [] 이 나올 수 있다.
        result = StaticsQuery.agg(model, col_name, agg_dict={col_name: agg},
                                  filters=filters,
                                  is_distinct=is_distinct,
                                  descending=descending,
                                  limit=limit
                                  )

        # pie chart data [('미정', 1)] 대신 [] 가 나올 경우 아예 => pyechart에서 에러처리 안해 에러가 난다
        #   IndexError: list index out of range 가 뜬다.
        # cf) [()]를 넣어줄 경우,
        #   data = [{"name": n, "value": v} for n, v in data_pair]
        #   ValueError: not enough values to unpack (expected 2, got 0)
        # => 해당 분류에 대해 enum이라면, 종류별로 집계 0을 만들어줄 수 있다.
        # => 일반칼럼이라면, 어떤 sex가 몇개가 들어갈지 모르므로 그냥 default [ ('없음',0)]을 넣어주자.

        # 분류칼럼의 comment를 model로부터 찾아들어가서, comment만 얻는다.
        # >>> User.__table__.columns
        # <sqlalchemy.sql.base.ImmutableColumnCollection object at 0x000001A0AFF0A258>
        # >>> User.__table__.columns['username']
        # Column('username', String(length=128), table=<users>, nullable=False)
        # >>> User.__table__.columns['username'].comment
        column_comment = model.__table__.columns[col_name].comment

        if not result:
            result = [('데이터 없음', 0)]
            pie_chart = (
                self._charts.Pie()
                .add(f'{column_comment}', result)
                .set_series_opts(label_opts=self._opts.LabelOpts(formatter="{b}"))
                .set_global_opts(legend_opts=self._opts.LegendOpts(pos_left=True, orient='vertical'))
            )

        else:
            # 옵션들
            # {b}: 튜플[0] 카테고리명 /  {d} => 현재 튜플[1] count / 전체 튜플[1]의 합 => 다 0일 때, 0/0으로 undefined됨.
            pie_chart = (
                self._charts.Pie()
                .add(f'{column_comment}', result)
                .set_series_opts(label_opts=self._opts.LabelOpts(formatter="{b}"))
                .set_global_opts(legend_opts=self._opts.LegendOpts(pos_left=True, orient='vertical'))
            )

        return pie_chart
