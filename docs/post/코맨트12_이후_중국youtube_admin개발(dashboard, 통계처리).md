### dashboard

#### admin.index  route에서 count query로 집계한다

##### count query는 select(func.count(Entity.id)) or select(func.count().select_from(Entity))로 하며, db.session.scalar() 단수로 뽑으면 된다.

```python
@admin_bp.route('/')
@login_required
def index():
    with DBConnectionHandler() as db:
        user_count = db.session.scalar(select(func.count(User.id)))
        post_count = db.session.scalar(select(func.count(Post.id)))
        category_count = db.session.scalar(select(func.count(Category.id)))
    # print(user_count)
    # print(post_count)
    # print(category_count)
    return render_template('admin/index.html',
                           user_count=user_count,
                           post_count=post_count,
                           category_count=category_count,
                           )
```

```
127.0.0.1 - - [28/Nov/2022 19:05:37] "GET /admin/ HTTP/1.1" 200 -
3
7
2
```





#### admin / index.html 수정

##### front - 71_index_change_after_index_route_coute.html

```html
    <div class="column">
        {% block member %}
        <div class="tile is-ancestor">
            <div class="tile is-parent">
                <article class="tile is-child notification is-info is-light">
                    <div class="content">
                        <p class="title">{{post_count}}</p>
                        <p class="subtitle">Post 수</p>
                        <div class="content">
                            <!-- Content -->
                        </div>
                    </div>
                </article>
            </div>
            <div class="tile is-parent">
                <article class="tile is-child notification is-success is-light">
                    <div class="content">
                        <p class="title">{{user_count}}</p>
                        <p class="subtitle">사용자 수</p>
                        <div class="content">
                            <!-- Content -->
                        </div>
                    </div>
                </article>
            </div>
            <div class="tile is-parent">
                <article class="tile is-child notification is-warning is-light">
                    <div class="content">
                        <p class="title">{{category_count}}</p>
                        <p class="subtitle">카테고리 수</p>
                        <div class="content">
                            <!-- Content -->
                        </div>
                    </div>
                </article>
            </div>
        </div>
        {% endblock member %}
    </div>
```



![image-20221128190811812](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128190811812.png)





### pyechart

- [참고유튜브1](https://www.youtube.com/watch?v=OGZfGHyJURA&list=PLCemT-oocgamluuCUblhe87HC5M69DtVM&index=16)
- [참고유튜브2](https://www.youtube.com/watch?v=tePEIgEDJ7c)



#### echarts 

##### 세팅

- echarts: https://echarts.apache.org/en/index.html

  - https://echarts.apache.org/handbook/en/get-started/

- pyecharts: https://pyecharts.org

  ![image-20221129012751452](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129012751452.png)





1. download -> 맨아래 커스텀 build -> 최소한만 선택하고 다운로드

   ![image-20221129013132869](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129013132869.png)

2. **static / js / admin폴더에 추가**

   ![image-20221129013312248](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129013312248.png)





##### admin/ index.html 적용

1. 추가적인 head - script는 `{% block extra_head_style %}`에 적용한다

   ```html
   {% block extra_head_style %}
   <!-- echart js & axios -->
   <script src="{{url_for('static', filename='js/admin/echarts.min.js')}}"></script>
   <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
   {% endblock extra_head_style %}
   ```

   

2. **해당페이지 실행 js코드는 vue객체 초기화 이후인 `{% block vue_script %}`에 작성해준다.**

   - **참고 `{% block extra_foot_script %}`에는 import해야할 js코드** script를 넣는 것으로 정하자.

     - **admin/index.html를 상속하는 놈들이 해당 block을 그대로 가져가므로 `상속 자식들은 빈block들로 처리해줘야한다`**

       ![image-20221129042345604](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129042345604.png)

   - https://echarts.apache.org/handbook/en/get-started/

     - 의 예시 js코드를 참고해서 작성한다.

       

   ```html
   {% block vue_script %}
   <!-- Prepare a DOM with a defined width and height for ECharts -->
   <!--<div id="main" style="width: 600px;height:400px;"></div>-->
   <script type="text/javascript">
       // Initialize the echarts instance based on the prepared dom
       var myChart = echarts.init(document.getElementById('main'));
   
       // Specify the configuration items and data for the chart
       var option = {
           title: {
               text: 'ECharts Getting Started Example'
           },
           tooltip: {},
           legend: {
               data: ['sales']
           },
           xAxis: {
               data: ['Shirts', 'Cardigans', 'Chiffons', 'Pants', 'Heels', 'Socks']
           },
           yAxis: {},
           series: [
               {
                   name: 'sales',
                   type: 'bar',
                   data: [5, 20, 36, 10, 10, 20]
               }
           ]
       };
   
       // Display the chart using the configuration items and data just specified.
       myChart.setOption(option);
   </script>
   {% endblock vue_script %}
   ```

3. **bulma의 tile시스템을 이용해서 `is-parent`단위로 1개씩 카드를 구성한다**

   ```html
   <!-- chart를 위한 tile 깔기 -->
   <!-- is-ancestor > 아래 개별요소마다 sm에서 각각 나눠지는 is-parent까지만 구분-->
   <div class="tile is-ancestor">
       <div class="tile is-parent">
           <article class="tile is-child notification is-white"
                    style="border: 1px solid lightgray;"
                    >
               <div class="content">
                   <p class="title is-size-5">📜Post 통계</p>
                   <p class="subtitle is-size-6 ml-1 my-1">카테고리별 Post 수 집계</p>
                   <div class="content">
                       <!-- Content -->
                       chart
                   </div>
                   <div class="content">
                       <!-- Content -->
                       table
                   </div>
               </div>
           </article>
       </div>
       <div class="tile is-parent">
           <article class="tile is-child notification is-white"
                    style="border: 1px solid lightgray;"
                    >
               <div class="content">
                   <p class="title is-size-5">✨예약 통계</p>
                   <p class="subtitle is-size-6 ml-1 my-1">일별 예약자 수 집계</p>
                   <div class="content">
                       <!-- Content -->
                       chart
                   </div>
                   <div class="content">
                       <!-- Content -->
                       table
                   </div>
               </div>
           </article>
       </div>
   </div>
   ```

   ![image-20221129024040681](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129024040681.png)













##### 반응형으로 적용

1. **이제 chart가 들어갈 `div id=""`와 js에서 찾는 id를 일치시키며, `height만 직접 지정`해줘야한다** 

   - **`반응형으로 적용`하려면**

     - **너비는 100% 고정높이는 min-height로 지정한다**
       - `width:100%; min-height:300px`

     ```html
     <div id="post_chart" class="content" style="width: 100%; min-height: 300px">
         <!-- Content -->
         chart
      </div>
     ```

   - **js에서는 `echarts.init()`한 뒤 받은 변수를 `window.onresize=`의 function으로 등록한다**

     ```html
     <script type="text/javascript">
         let postChart = echarts.init(document.querySelector('#post_chart'));
     
         // 차트를 반응형으로 (width:100%, min-height:300px)상태에서
         window.onresize = function () {
             postChart.resize();
         };
     
     ```

     ![image-20221129050732927](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129050732927.png)

     ![image-20221129050740678](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129050740678.png)

- post_chart로 id를 통일
- **height:300px로 고정**
- **title과 legend가 겹치니 title옵션은 삭제**

```html
<div class="content">
    <p class="title is-size-5">📜Post 통계</p>
    <p class="subtitle is-size-6 ml-1 my-1">카테고리별 Post 수 집계</p>
    <div id="post_chart" class="content" style="height:300px;">
        <!-- Content -->
        chart
    </div>
    <div class="content">
        <!-- Content -->
        table
    </div>
</div>
```

```html
<script type="text/javascript">
    // Initialize the echarts instance based on the prepared dom
    var postChart = echarts.init(document.getElementById('post_chart'));
```

![image-20221129030908017](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129030908017.png)





##### route에서 xAxis-data, yAxis-data 넘기기

- xdatas와 ydatas를 갯수를 일치시켜 넘기되 **python list로 jinja에 넘기고, `JSON.parse('{{x_datas | tojson}}')`필터 + 파서를 쓰자**
  - 아니면 json.dumps( , ensure_ascii=False)로 json으로 만들어서 넘겨서 그대로 받을 수 있다.

- **A별 B의 count는**
  - **B에서 fk_A별 count를 세어서 subquery로 만들고**
  - **A에다가 fk_A별 집계 subquery를 join해주면 된다.**
  - **`만약, join후 name, count를 select하면, post가 없어서 join안되는 category의 경우 innerjoin시 생략`되어버린다.**

```python
@admin_bp.route('/')
@login_required
def index():
    with DBConnectionHandler() as db:
        user_count = db.session.scalar(select(func.count(User.id)).where(User.is_super_user == True))
        post_count = db.session.scalar(select(func.count(Post.id)))
        category_count = db.session.scalar(select(func.count(Category.id)))
        banner_count = db.session.scalar(select(func.count(Banner.id)))

        # 연결되어있는 것도  sql문으로하려면, 직접 where에 연결해줘야한다(꽁join 아니면)
        # stmt = select(Category.name, func.count(Post.id).label('count')) \
        #     .where(Post.category_id == Category.id) \
        #     .group_by(Post.category_id)

        ## post 갯수0짜리도 찍히게 하려면,[사실상 one별 many의 집계] => many에서 fk별 집계한 뒤, one에 fk==id로 붙인다.
        ##  (1) Post에서 subquery로 미리 카테고리id별 count를 subquery로 계산
        ##  (2) Category에 category별 count를 left outer join
        ## => main_06_subquery_cte_기본.py 참고

        subq = select(Post.category_id, func.count(Post.id).label('count')) \
            .group_by(Post.category_id) \
            .subquery()
        stmt = select(Category.name, subq.c.count) \
            .join_from(Category, subq)\
            .order_by(subq.c.count.desc())


        # [('분류1', 5), ('22', 2)]
        post_count_by_category = db.session.execute(stmt)
        x_datas = []
        y_datas = []
        for category, post_cnt_by_category in post_count_by_category:
            x_datas.append(category)
            y_datas.append(post_cnt_by_category)

    return render_template('admin/index.html',
                           user_count=user_count,
                           post_count=post_count,
                           category_count=category_count,
                           banner_count=banner_count,

                           x_datas=x_datas,
                           y_datas=y_datas,
                           )
```



##### index.html에서 python_list를  `"{{ list  |  tojson }}"`으로 받은 것을 JSON.parse( )에 넣으면, json.dumps( ensure_ascii=False)안써도 된다.

```html
<script type="text/javascript">
    // Initialize the echarts instance based on the prepared dom
    let postChart = echarts.init(document.querySelector('#post_chart'));

    // 차트를 반응형으로 (width:100%, min-height:300px)상태에서
    window.onresize = function () {
        postChart.resize();
    };


    // Specify the configuration items and data for the chart
    var option = {
        // title: {
        //     text: 'ECharts Getting Started Example'
        // },
        tooltip: {},
        legend: {
            data: ['카테고리'] // series의 name과 일치해야한다
        },
        xAxis: {
            data: JSON.parse('{{x_datas | tojson}}')
        },
        yAxis: {},
        series: [
            {
                name: '카테고리',
                type: 'bar',
                data: JSON.parse('{{y_datas | tojson}}')
            }
        ]
    };

    // Display the chart using the configuration items and data just specified.
    postChart.setOption(option);
</script>
{% endblock vue_script %}
```



##### bar에 색넣기 -> series 옵션에서 itemStyle로 주되, color를 func으로 정의해준다

```js
series: [
    {
        name: '카테고리',
        type: 'bar',
        data: JSON.parse('{{y_datas | tojson}}'),
        // bar에 색 넣기
        itemStyle: {
            color: function (param) {
                const color = ['#76b143', '#7d7c6a', '#0065b3', '#7d7c6a',];
                // param.value[0] is the x-axis value
                // param.value is data 값
                // param.dataIndex is 0부터 순서
                console.log(param)
                return color[param.dataIndex % color.length]
            }
        },
    }
]
```

![image-20221129052612735](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129052612735.png)



##### echarts examples에서 line chart 추가하기



![image-20221129145120669](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129145120669.png)



###### html



- user line chart

```html
<article class="tile is-child notification is-white"
         style="border: 1px solid lightgray;"
         >
    <div class="content">
        <p class="title is-size-5">✨유저수 통계</p>
        <p class="subtitle is-size-6 ml-1 my-1">일별 등록된 유저 수 집계</p>
        <div id="user_chart" class="content" style="width: 100%; min-height: 300px">

            <!-- Content -->
            chart
        </div>
        <div class="content">
            <!-- Content -->
            table
        </div>
    </div>
</article>
```



```html
<script type="text/javascript">
    // category별 post
    let postChart = echarts.init(document.querySelector('#post_chart'));
    let userChart = echarts.init(document.querySelector('#user_chart'));

    // 차트를 반응형으로 (width:100%, min-height:300px)상태에서
    window.onresize = function () {
        postChart.resize();
        userChart.resize();
    };


    // Specify the configuration items and data for the chart
    let postChartOption = {
        // title: {
        //     text: 'ECharts Getting Started Example'
        // },
        tooltip: {},
        legend: {
            data: ['카테고리'] // series의 name과 일치해야한다
        },
        xAxis: {
            data: JSON.parse('{{x_datas | tojson}}')
        },
        yAxis: {},
        series: [
            {
                name: '카테고리',
                type: 'bar',
                data: JSON.parse('{{y_datas | tojson}}'),
                // bar에 색 넣기
                itemStyle: {
                    color: function (param) {
                        const color = ['#76b143', '#7d7c6a', '#0065b3', '#7d7c6a',];
                        // param.value[0] is the x-axis value
                        // param.value is data 값
                        // param.dataIndex is 0부터 순서
                        // console.log(param)
                        return color[param.dataIndex % color.length]
                    }
                },
            }
        ]
    };

    let userChartOption = {
        xAxis: {
            type: 'category',
            data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        },
        yAxis: {
            type: 'value'
        },
        series: [
            {
                data: [150, 230, 224, 218, 135, 147, 260],
                type: 'line'
            }
        ]
    }

    // Display the chart using the configuration items and data just specified.
    postChart.setOption(postChartOption);
    userChart.setOption(userChartOption);
</script>
```

![image-20221129150208070](../../../Users/is2js/AppData/Roaming/Typora/typora-user-images/image-20221129150208070.png)



###### route

- **시간별 추출**
  - https://stackoverflow.com/questions/52699990/how-to-get-row-count-per-day-in-sqlalchemy



###### querying with dates 

- https://www.youtube.com/watch?v=yDuuYAPCeoU

![image-20221129161251129](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161251129.png)

- date관련 filter 와 between

  - datetime import

    ![image-20221129154522163](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129154522163.png)

    ![image-20221129154739688](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129154739688.png)

  - filter onedate - datefield -> **==** 

    ![image-20221129154606946](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129154606946.png)

  - filter onedate  date**time**field -> **func.date**

    ![image-20221129154426145](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129154426145.png)

  - between two date - datefield

    ![image-20221129154451048](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129154451048.png)

  - between two date - datetimefield -> no func.date 안써도 된다.

    ![image-20221129154917134](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129154917134.png)

- **지난 XXX**

  1. datetime.date.today()를 기준으로

  2. datetime.timedelta( 단위= 갯수) 를 빼고

  3. where에서  date칼럼 ( 오늘로부터 - 지난 1주의 **시작일**)과 비교해서 **더 큰 것을** 가져온다

     ![image-20221129160959208](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129160959208.png)

  4. days, week은 단위가 있찌만 month가 없으므로 days=30을 1달 기준으로 한다

     ![image-20221129161037575](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161037575.png)

- **일별 집계**

  - groupby에 date를 올리고, select에는 date, 집계

  ![image-20221129161220924](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161220924.png)
  ![image-20221129161318875](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161318875.png)

  ![image-20221129161355083](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161355083.png)

  ![image-20221129161401708](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161401708.png)



- 연도별 합 집계

  - **func.strftime("%Y", date칼럼)을 통해 연도만 추출한 뒤 집계한다**
  - 숫자로 추출할 거면 `extract('year', Post.add_date) == int(dates[0]),`처럼 extract로 해도 될듯?

  ![image-20221129161645595](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161645595.png)
  ![image-20221129161703027](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161703027.png)



- 월별 누적합 집계

  - **func.strftime("%Y-%m")을 통해 상위연도를 끼어서 집계해야한다**
    - 그렇지 않으면, 작년%m과 올해%m이 같은값으로 추출된다.

  ![image-20221129161829419](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221129161829419.png)

###### 하지만, date필드에 기록되지 않는 모든 1일별로 처리하려면 generate_series를 미리 해야한다?!

- https://stackoverflow.com/questions/49200845/sqlalchemy-group-by-date-and-aggregate-on-count-how-to-fill-in-missing-dates





##### generate_series로 미리 모든일자를 만들어놓기

- https://stackoverflow.com/questions/52699990/how-to-get-row-count-per-day-in-sqlalchemy
  - sql

  ```python
  from sqlalchemy import text
  
  q = text(
        """
        SELECT d.date, count(se.id)
        FROM (
          SELECT to_char(date_trunc('day', (current_date - offs)), 'YYYY-MM-DD') AS date 
          FROM generate_series(0, <NUMBER_OF_DAYS>, 1) AS offs
       ) d 
       LEFT OUTER JOIN some_table se 
         ON d.date = to_char(date_trunc('day', se.created), 'YYYY-MM-DD'))  
       GROUP BY d.date;
       """
  )
  session.execute(q).all()
  ```

  

- https://stackoverflow.com/questions/49200845/sqlalchemy-group-by-date-and-aggregate-on-count-how-to-fill-in-missing-dates

  - sqlalchemy

  Use [`generate_series()`](https://www.postgresql.org/docs/current/static/functions-srf.html) to generate all dates in the desired range and left join the data, coalescing missing values to 0:

  ```css
  series = db.session.query(
  	db.func.generate_series(db.func.min(Pomo.timestamp),
      db.func.max(Pomo.timestamp),
      timedelta(days=1)).label('ts')).\
       subquery()
  
  values = db.session.query(Pomo.timestamp,
  	db.func.count(Pomo.id).label('cnt')).\
      group_by(Pomo.timestamp).\
      subquery()
  
  db.session.query(series.c.ts,
      db.func.coalesce(values.c.cnt, 0)).\
      outerjoin(values, values.c.timestamp == series.c.ts).\
      order_by(series.c.ts).\
      all()
  
  
  [(datetime.datetime(2018, 3, 2, 0, 0), 1),
   (datetime.datetime(2018, 3, 3, 0, 0), 0),
   (datetime.datetime(2018, 3, 4, 0, 0), 0),
   (datetime.datetime(2018, 3, 5, 0, 0), 0),
   (datetime.datetime(2018, 3, 6, 0, 0), 0),
   (datetime.datetime(2018, 3, 7, 0, 0), 1),
   (datetime.datetime(2018, 3, 8, 0, 0), 6)]
  ```



- 다른 sqlalchemy

  - https://stackoverflow.com/questions/53137019/using-function-output-in-sqlalchemy-join-clause

  ```sql
  SELECT array_agg(counts.count), places.name 
  FROM generate_series('2018-11-01', '2018-11-04', interval '1 days') as day 
  CROSS JOIN  places 
  LEFT OUTER JOIN counts on counts.day = day.day AND counts.PlaceID = places.id 
  GROUP BY places.name;
  ```

  

  ```python
  date_list = select([column('generate_series')])\
  .select_from(func.generate_series(backthen, today, '1 day'))\ 
  .alias('date_list')
  
  time_series = db.session.query(Place.name, func.array_agg(Count.count))\
  .select_from(date_list)\
  .outerjoin(Count, (Count.day == date_list.c.generate_series) & (Count.placeID == Place.id ))\
  .group_by(Place.name)
  ```

  



- text to subquery

  - **text("sql") columns(  ).subquery('subq_name')**
  - https://stackoverflow.com/questions/34169993/sqlalchemy-making-a-subquery-of-query-from-statementtext-raising-attribu
  - https://groups.google.com/g/sqlalchemy/c/70oGKE9rqY8/m/Onke3WDJAQAJ

  ```python
  I'm working on raw SQL feature, and it has to support distinct and sort. Instead of parsing and modifying user query, I'm wrapping it as subquery and then do distinct and sort.
  
  ​```
  user_query = 'select "FirstName", from "Customer"'
  stmt = text(user_query)
  stmt = select('*').select_from(stmt.columns().alias())
  stmt = stmt.distinct() # and order_by(user_columns)
  print(stmt)
  
  SELECT DISTINCT *
  FROM (select "FirstName",  from "Customer") AS anon_1
  ​```
  
  So, any better way to implement it? I'm thinking about extracting column names from a query and using them in select(). Is it possible in sqlalchemy?
  
  you have to extract the column names from the text if you want to perform further manipulations with them.
  
  from sqlalchemy import text, select, column
  
  
  user_query = 'select "FirstName", from "Customer"'
  stmt = text(user_query).columns(column("FirstName"))
  
  subq = stmt.alias("subq")
  
  stmt = select([subq])
  stmt = stmt.distinct()
  stmt = stmt.order_by(subq.c.FirstName)
  print(stmt)
  
  ```

- 참고 - 기간별

  ```python
  def getRange(start, end, aggregate):
          query = db.select([
                  func.max(Simulation.timestamp).label('timestamp'),
                  func.sum(Simulation.PVPowerOutput).label('PVPowerOutput'),
                  func.sum(Simulation.ACPrimaryLoad).label('ACPrimaryLoad')\
              ])\
              .where(Simulation.timestamp >= start)\
              .where(Simulation.timestamp <= end)\
  
          if aggregate == 'hourly':
              # do nothing
              query = query.group_by(Simulation.timestamp)
          elif aggregate == 'daily':
              # group by date
              query = query.group_by(func.date(Simulation.timestamp))
          elif aggregate == 'monthly':
              # group by month
              query = query.group_by(func.date_part('month', Simulation.timestamp))
          else:
              raise ValueError('invalid aggregation')
          return [dict(r) for r in db.session.execute(query).fetchall()] 
  ```

  





- sqlite3 func.strftime  postgre to_char

  ```sql
  Given a format like "Mar 12 18:07:22",
  
  PostgreSQL version using to_char function:
  
  psql -c "SELECT to_char(time,'Mon DD HH24:MI:SS ') FROM mytable;" 
  SQLite version using strftime function (with the help of awk):
  
  sqlite3 'SELECT strftime("%s", time, "localtime") FROM mytable;' \
    |  awk '{print strftime("%b %e %H:%M:%S",$1) }' 
  ```

  



### sqlite3 용  datetime칼럼 기준 count집계 로직



#### value Entity의 집계가 붙을 generaete_series_subquery(series)만들기

1. sqlite3에서는 generate_series view_function이 사용이 안되므로 **raw sql cte recursive**로 만들어야한다

   - 기준을 해당일 YYYY-mm-dd의 **date**로 두고, **+1 interval**씩 증가시키는 재귀를 돈다
     - year 단위면  시작일 2019-11-11 기준으로 2020-11-11 , 2012-11-11로 증가시킨다
   - **text()로 작성한 sql문을 subquery로 만드려면**
     1. **재귀 밑에 select문에 `;`로 끝내지 않는다.(subquery로서 들어갈 예정)**
     2. **text()다음에 `.columns(  column('date'))`를 붙여 TextClause를 먼저 만들고**
     3. **`.subquery('name')`을 통해 최종 서브쿼리를 만든다.**
     4. 만들어진 subquery를 찍어보려면 `.select()`를 달아서 **`.execute(  subquery ) .all()`**로만 찍어볼수 있다.(scalars X)
   - subquery명은 `series`, 날짜칼럼명은 `date`로 통일하여 join에 대비한다

   ```python
   def generate_series_subquery(start_date, end_date, interval='day'):
       if interval == 'day':
           strftime_format = '%Y-%m-%d'
       if interval == 'month':
           strftime_format = '%Y-%m'
       elif interval == 'year':
           strftime_format = '%Y'
   
       # select date form dates담에 ;를 넘으면 outer join시 에러
       stmt = text(f"""
           WITH RECURSIVE dates(date) AS (
                 VALUES (:start_date)
             UNION ALL
                 SELECT date(date, '+1 {interval}')
                 FROM dates
                 WHERE date < :end_date
           )
           SELECT strftime('{strftime_format}', date) AS 'date' FROM dates
           """).bindparams(start_date=to_string_date(start_date), end_date=to_string_date(end_date))
       return stmt.columns(column('date')).subquery('series')
   ```

   



#### valueEntity에서는 대상데이터 where필터 기준은 date로변환(고정) 후  <->필터링후  집계기준은 date변환 or Y-m변환 or Y변환 을 선택한다

- **2 datetime필드라서 `.between(, )`으로 처리하려고 했찌만, `datetime필드를 date로 변환하면서 필터링`해야하므로 between으로는 변환필터링불가**

  

1. 일단 **오늘(필터링기준은 date)을 end_date**로 잡고, `relativedelta(단위=int)`를 기준으로 **start_date**를 구한다

   ```python
   def get_datas_count_by_date(db, entity, date_column_name, interval='day', period=7):
       end_date = date.today() # end_date는 datetime칼럼이라도, date기준으로
       if interval == 'day':
           start_date = end_date - relativedelta(days=period)
       elif interval == 'month':
           start_date = end_date - relativedelta(months=period)
       elif interval == 'year':
           start_date = end_date - relativedelta(years=period)
       else:
           raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')
   
   ```

   

2. **inetrval단위에 따라 , value Entity group_by 기준 format**도 미리 정해준다

3. **일단 집계데이터를 할 대상을 `where`로 필터링할 때, `반드시, datetime필드를 date로 변환 후 필터링`한다**

   - **만약, datetime필드를  start_date, end_date로 필터링하면**
     - 2022-11-11 (end_date)와
     - 2022-11-11 23:59:30 (add_date datetime필드)를 **필터링시 배제**된다
       - **필드를 `func.date()`를 통해 date형으로 변환하여 where로 필터링한 기준에 걸리게 한다**

4. **`group_by의 기준은 func.strftime( format )`으로 interval단위에 의해 정해진다.**

   - **select시에는 `.label('date')`를 통해 series subquery와 같은 필드로 outer join되도록 하자.**

   ```python
   def count_by_date_subquery(interval, entity, date_column_name, end_date, start_date):
       if interval == 'day':
           strftime_format = '%Y-%m-%d'
       elif interval == 'month':
           strftime_format = '%Y-%m'
       elif interval == 'year':
           strftime_format = '%Y'
       else:
           raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')
   
       return (
           select(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'),
                  func.count(entity.id).label('count'))
           .where(and_(
               start_date <= func.date(getattr(entity, date_column_name)),
               func.date(getattr(entity, date_column_name)) <= end_date)
           )
           .group_by(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'))
           .subquery()
       )
   ```

   ```python
   .group_by(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'))
   ```





#### series subq와 values subq의   left outer join + fun.coalesce( ,0)

- **subquery끼리만 `.outer_join( , 연결key 지정)`이 있는 것** 같다.

  - AttributeError: 'Select' object has no attribute 'outer_join'

    - Entity + subquery(fk들고있음)의 outer_join은 **join_from + isouter=True**

    ```python
    stmt = select(Category.name, subq.c.count) \
        .join_from(Category, subq, isouter=True) \
        .order_by(subq.c.count.desc())
    ```

- series에 values를 date label 칼럼 기준으로 집어넣는다.
  - **이 때,  func.coalesce(붙을칼럼, 0)으로 `붙을 value칼럼이 Outer시 None으로 못붙는 경우 0`으로 채워준다.**

```python
stmt = (
    select(series.c.date, func.coalesce(values.c.count, 0).label('count'))
    .outerjoin(values, values.c.date == series.c.date)
    .order_by(series.c.date)
)
```



#### 결과를 x_datas, y_datas로 나눠주되, x_datas를 각 interval 단위만 표기해준다



```python
    x_datas = []
    y_datas = []
    for day, user_count in db.session.execute(stmt):
        x_datas.append(day)
        y_datas.append(user_count)
    # 집계대상 필터링은 Y-m-d(date) -> group_by strftime으로 (day) or Y-m-d/(month)Y-m/(year)Y 상태
    # 이미 문자열로 Y-m-d  or Y-m  or Y 중 1개로 정해진 상태다. -> -로 split한 뒤 마지막거만 가져오면 interval 단위
    # => 출력을 위해 day단위면, d만 / month단위면 m만 나가도록 해준다 (year는 이미 Y)
    if interval == 'day':
        x_datas = list(map(lambda x: x.split('-')[-1] + '일', x_datas))
    elif interval == 'month':
        x_datas = list(map(lambda x: x.split('-')[-1] + '월', x_datas))  # 이미 Y-m그룹화 상태
    elif interval == 'year':
        x_datas = list(map(lambda x: x + '년', x_datas))
    return x_datas, y_datas
```



```python
user_x_datas, user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='day', period=7)
```

![image-20221130032338827](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221130032338827.png)



##### postgre라면?

```python
Given a format like "Mar 12 18:07:22",

PostgreSQL version using to_char function:

psql -c "SELECT to_char(time,'Mon DD HH24:MI:SS ') FROM mytable;" 
SQLite version using strftime function (with the help of awk):

sqlite3 'SELECT strftime("%s", time, "localtime") FROM mytable;' \
  |  awk '{print strftime("%b %e %H:%M:%S",$1) }' 

In the prior example,

The printed format will be Mar 12 18:07:22
The sqlite column time was a TEXT type as ISO8601 strings.
The postgres column time was type time_stamp .
```



### PyEcharts 사용해서 option 정보를 backend에서 처리하기



![image-20221130034738172](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221130034738172.png)





1. 패키지 설치

   ```powershell
   pip install pyecharts
   ```

2. 공식홈페이지의 [Platform suport - flask](https://pyecharts.org/#/en-us/flask)를 보면된다.

   ![image-20221130150750276](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221130150750276.png)

#### html에서는 공간 + options를 백엔드 jinja로 받는다.

```html
<!-- 년간 chart 1줄 -->
<div class="tile is-ancestor ">
    <div class="tile is-parent">
        <article class="tile is-child notification is-white"
                 style="border: 1px solid lightgray;"
                 >
            <div class="content">
                <p class="title is-size-5">🗓 년간 통계</p>
                <p class="subtitle is-size-6 ml-1 my-1">1년동안 월별 데이터 수 확인</p>
                <div id="year_chart" class="content" style="width: 100%; min-height: 300px">
                    <!-- Content -->
                    chart
                </div>
            </div>
        </article>
    </div>
</div>
```



- **이 때, `chart.setOption( )`을 js변수가 아닌 `{{ jinja | safe}}`로 받는다.**

```js
let yearChart = echarts.init(document.querySelector('#year_chart'));

window.onresize = function () {
    //
    yearChart.resize();
};


yearChart.setOption({{ year_options | safe }})
```



#### route에서는   chart객체를 만들고 .add_xaxis( list ) 기본에, 원하는 카테고리만큼 .add_yaxis( 'name', list)를 넣어준다

##### jinja로는 chart객체.dump_options()만 넘긴다

```python
        # < 월별 연간 통계 by pyerchart>
        year_x_datas, year_post_y_datas = get_datas_count_by_date(db, Post, 'add_date', interval='month', period=12)
        _, year_user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='month', period=12)
        _, year_category_y_datas = get_datas_count_by_date(db, Category, 'add_date', interval='month', period=12)
        _, year_banner_y_datas = get_datas_count_by_date(db, Banner, 'add_date', interval='month', period=12)
        _, year_tag_y_datas = get_datas_count_by_date(db, Tag, 'add_date', interval='month', period=12)
        
        year = (
            Bar()
            .add_xaxis(year_x_datas)
            .add_yaxis('포스트 수', year_post_y_datas) # y축은 name먼저
            .add_yaxis('유저 수', year_user_y_datas)
            .add_yaxis('카테고리 수', year_category_y_datas)
            .add_yaxis('배너 수', year_banner_y_datas)
            .add_yaxis('태그 수', year_tag_y_datas)
        )

    return render_template('admin/index.html',
                           #...
                           year_options = year.dump_options()
                           )

```



![image-20221130155203471](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221130155203471.png)



#### 그외에 jinja로 대체할 수 있는 부분(참고만)

- chart객체마다 .chart_id가 있어서, **js변수 및 div의 id**에 jinja를 활용할 수있다.

  ```python
  print(year_chart.chart_id)
  # 218e34f27976413582d5ced8a071381e
  ```

  ```js
  var myChart_{{ chart_id }} = echarts.init(document.getElementById('{{ chart_id }}'), null, {renderer: '{{ renderer}}'});
  {{ custom_function }}
  var option_{{ chart_id }} = {{ options | safe }};
  ```

  

##### chart객체마다 script import부분도 대체할 수있다. 

```python
from pyecharts.constants import DEFAULT_HOST



@app.route("/")
def hello():
    _bar = bar_chart()
    javascript_snippet = TRANSLATOR.translate(_bar.options)
    return render_template(
        "pyecharts.html",
        chart_id=_bar.chart_id,
        host=REMOTE_HOST,
        renderer=_bar.renderer,
        my_width="100%",
        my_height=600,
        custom_function=javascript_snippet.function_snippet,
        options=javascript_snippet.option_snippet,
        script_list=_bar.get_js_dependencies(),
    )

```



```html
    {% for jsfile_name in script_list %}
        <script src="{{ host }}/{{ jsfile_name }}.js"></script>
    {% endfor %}
```





#### 기존 것도 backend에서 객체 -> options 넘겨주기

![image-20221130171844253](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221130171844253.png)

![image-20221201032138007](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221201032138007.png)



### 통계 - tag별 post의 갯수 및 누적 조회수



#### query참고

##### cate - items  (one to many) 딸린 자식들의 합을 hybrid_propery로 만들어, One의 order_by에 사용할 수 있다.(실제쿼리로 쓰기엔 성능안좋음. -> 실제쿼리는 groupby에 집계문 올려서 원래하는것처럼)

- https://stackoverflow.com/questions/70957938/sqlalchemy-aggregate-sum-of-related-table-column-values

- **many관계속성`.with_entities(  select구문 ).scalar()`를 통해, 연결된 many테이블의 값 집계가 가능하다.**

- **expression은 Many입장에서 join없이 where로 부모를 걸고 집계한다**

  - **join없이 select2개 join대체해서 처리한다.**

  ```python
  stmt = (
      select(func.sum(Post.has_type))
      .where(Post.category_id == Category.id)
      .label("items_price")
  )
  print(stmt)
  ```

  ```sql
  (SELECT sum(posts.has_type) AS sum_1
  FROM posts, categories
  WHERE posts.category_id = categories.id)
  ```

  

```python
1


#You can implement it as a hybrid property (you have to set also relationship differently by adding lazy='dynamic').

from sqlalchemy import func, select

class Cart(Base):
    items = relationship("Item", backref="cart", lazy="dynamic")

    @hybrid_property
    def items_price(self):
        return self.items.with_entities(func.sum(Item.price)).scalar()

    @items_price.expression
    def items_price(cls):
        return (
            select(func.sum(Item.price))
            .where(Item.cart_id == cls.id)
            .label("items_price")
        )


class Item(Base):
    price = Column(Integer, default=0)
    cart_id = Column(
        Integer,
        ForeignKey(
            "Cart.id",
            ondelete="CASCADE",
        ),
    )
#You can now use items_price in a query:

carts = session.query(Cart).order_by(Cart.items_price.desc())
#However, the performance of this approach is not great. So if your db is large, you should try something like that:

cart_price = func.sum(Item.price)
# result query is a list of tuples (<cart_id>, <cart_price>)
carts_price = session.query(
                    Item.cart_id,
                    cart_price
                ).group_by(
                    Item.cart_id
                ).order_by(
                    cart_price.desc()
                )
```



#### many to many 집계하기



##### asso - 집계대상을 정보성One(Post)으로 취급하여 일반join =>  집계One(Tag)의 fk로 보유한 상태에서 집계 => One에 outerjoin with coalesce



- tags - posts 에 대해서

  - tag별 post의 count, 숫자칼럼의 sum을 구하는 상황
  - 1:M같은 경우, **Many의 fk(One id)별 집계 -> One에다가 outerjoin**

- **M:N의 경우**

  1. association에 있는 tag_id, post_id에 대해서 **association `join` post에서 집계할 정보를 붙인다.**

     - association의 tag_id를 fk라 보고 fk별 집계할 **post데이터를 post_id로 join**한다. **이 때, join해도 데이터가 LEFT(asso_post_id), RIGHT(post.id)한쪽에만 있는 것은 없을 테니, 일반 join으로 한다**
     - my) asso에는 원래있던 id정보들 중 일부가 들어가 있고, Right인 Post가 더 큰 범위일테니, **작은데 붙이는 join으로서 일반join한다.**
     - asso중 일부칼러만 쓰더라도, **tag에 붙일 연결고리인 tag_id는 필수로 포함**되어야한다.

     ```python
     stmt = select(posttags, Post.has_type) \
                 .join(Post)
     ```

     ```sql
     # SELECT posttags.tag_id, posttags.post_id, posts.has_type
     # FROM posttags
     #     JOIN posts ON posts.id = posttags.post_id
     # (1, 3, <PostPublishType.SHOW: 2>)
     # (4, 3, <PostPublishType.SHOW: 2>)
     # (1, 6, <PostPublishType.SHOW: 2>)
     # (1, 5, <PostPublishType.SHOW: 2>)
     # (1, 4, <PostPublishType.SHOW: 2>)
     # (1, 8, <PostPublishType.SHOW: 2>)
     ```

  2. **Tag에 붙이기 전, `타테이블의 fk(tag_id) 상태에서 집계`가 이루어져야한다**

     - 미리 정보를 다 붙이면, 집계가 힘들 수 있다. right에는 없는 outerjoin 정보가 left엔 None으로 남아있어서, **`outerjoin붙이기 전, fk + 집계대상정보들이 교집합 상태`인 `fk로 보유테이블에서 집계`한다.**

     - **집계는 subq로 만들건데, `집계subq는 outerjoin시 c.칼럼명으로 쓰이기 때문에 label을 붙이면 좋을 것이다`**
       - **하지만 `label없이  func.count(), func.sum()으로 만든 subq -> subq.c.count / subq.c.sum으로 사용됨을 확인`했다.**

     ```python
     subq = select(posttags.c.tag_id, func.count(posttags.c.post_id), func.sum(cast(Post.has_type, Integer))) \
         .join(Post) \
         .group_by(posttags.c.tag_id)
     ```

     ```sql
     # SELECT posttags.tag_id, count(posttags.post_id) AS count, sum(CAST(posts.has_type AS INTEGER)) AS sum
     # FROM posttags JOIN posts ON posts.id = posttags.post_id GROUP BY posttags.tag_id
     # (1, 5, 10)
     # (4, 1, 2)
     ```

  3. **A별 B의 칼럼집계는 A_fk별 B집계를 끝내고 `A에다가 B에는 없던 id들을 0으로 포함시키는 outerjoin`을 해야한다.**

     - outerjoin에는 3가지 방법이 있다.
       1. **select에서 left right가 명확하지 않는 경우** 
          - `join_from(left, right, isouter=True)`
       2. **select에 left만 올라가서 명확한 경우**
          - `join(right, isouter=True)`
          - **`.outerjoin(right) `**
     - **A에다가 A_fk별B칼럼집계 subquery를 right로 outerjoin하며, `select에는 A의 fk제외정보칼럼 + subq.c.집계`를 고를 것이므로 A가 select에 명확히 올라간다**
       - **`.outerjoin(subq) `**를 쓰면 된다.
     - **`집계 최종query로서 label을 써야  tuple list같은 execute().all()도 칼럼처럼 인덱싱`이 가능해진다.**

     ```python
     stmt = select(Tag.name, func.coalesce(subq.c.count, 0).label('count'), func.coalesce(subq.c.sum, 0).label('sum')) \
         .outerjoin(subq) \
         .order_by(subq.c.count.desc()) \
         .limit(3)
     print(stmt)
     for d in db.session.execute(stmt):
         print(d.name, d.count, d.sum)
     ```

     - .outerjoin(subq) 

       ```sql
       SELECT tags.name, coalesce(anon_1.count_1, :coalesce_1) AS count, coalesce(anon_1.sum_1, :coalesce_2) AS sum 
       FROM tags LEFT OUTER JOIN (SELECT posttags.tag_id AS tag_id, count(posttags.post_id) AS count_1, sum(CAST(posts.has_type AS INTEGER)) AS sum_1
       FROM posttags JOIN posts ON posts.id = posttags.post_id GROUP BY posttags.tag_id) AS anon_1 ON tags.id = anon_1.tag_id ORDER BY anon_1.count_1 DESC
        LIMIT :param_1
        
       tag_1 6 12
       태그1 2 4
       11 1 2
       ```

     - join(subq, isouter=True)

       ```sql
       SELECT tags.name, coalesce(anon_1.count_1, :coalesce_1) AS count, coalesce(anon_1.sum_1, :coalesce_2) AS sum 
       FROM tags LEFT OUTER JOIN (SELECT posttags.tag_id AS tag_id, count(posttags.post_id) AS count_1, sum(CAST(posts.has_type AS INTEGER)) AS sum_1
       FROM posttags JOIN posts ON posts.id = posttags.post_id GROUP BY posttags.tag_id) AS anon_1 ON tags.id = anon_1.tag_id ORDER BY anon_1.count_1 DESC
        LIMIT :param_1
        
       tag_1 6 12
       태그1 2 4
       11 1 2
       ```

     - join_from(Tag, subq, isouter=True) 

       ```sql
       SELECT tags.name, coalesce(anon_1.count_1, :coalesce_1) AS count, coalesce(anon_1.sum_1, :coalesce_2) AS sum 
       FROM tags LEFT OUTER JOIN (SELECT posttags.tag_id AS tag_id, count(posttags.post_id) AS count_1, sum(CAST(posts.has_type AS INTEGER)) AS sum_1
       FROM posttags JOIN posts ON posts.id = posttags.post_id GROUP BY posttags.tag_id) AS anon_1 ON tags.id = anon_1.tag_id ORDER BY anon_1.count_1 DESC
        LIMIT :param_1
        
       tag_1 6 12
       태그1 2 4
       11 1 2
       
       ```

       ![image-20221202053137624](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221202053137624.png)



##### asso를 무시하고 2테이블이라 생각하고, join에 [left.right관계명]을 입력해서 outerjoin후 집계하기

- https://stackoverflow.com/questions/33335922/how-can-i-construct-a-count-aggregation-over-a-join-with-sqlalchemy



##### 일단 join명시 개념

```python
# Query.join()은 User와 Address 사이에 있는 하나의 외래키를 기준으로 join한다. 만약 외래키가 없거나 여러개라면 Query.join() 아래같은 방식을 써야한다.
query.join(Address, User.id==Address.user_id)   # 정확한 상태를 적어줌
query.join(User.addresses)                      # 명확한 관계 표기 (좌에서 우로)
query.join(Address, User.addresses)             # 동일, 명확하게 목표를 정해줌
query.join('addresses')                         # 동일, 문자열 이용

```



```python
# .outerjoin(left.right관계명) 후 집계
stmt = select(Tag.name, func.coalesce(func.count(Post.id), 0).label('count'), func.sum(cast(Post.has_type, Integer)).label('sum')) \
    .outerjoin(Tag.posts) \
    .group_by(Tag.id) \
    .order_by(literal_column('count').desc()) \
    .limit(3)
print(stmt)
for d in db.session.execute(stmt):
    print(d)
```

```python
# 이것도 동일하다. 즉, join기준을 backref로
# .join(Right, Left.Right관계명)
.join(Post, Tag.posts, isouter=True) \
```

```python
# 이것도 동일하다. select에 이미 2테이블이 들어가있을 경우
# join에는 right table을 명시해줘야하는데
# fk가 없거나 여러개인 경우 + assoc테이블인 경우
# Left테이블.Right테이블관계명을 명시해주면 알아서 join을 수행한다.
# => left.right 관계명시의 join을 어디서 쓰나 했더니 MN관계에서 쓰면 유옹
.join(Tag.posts, isouter=True) \
```





##### asso + right join subq 이후 outerjoin   vs   left.right관계명으로 outerjoin query비교

- **집계를 outerjoin전  subq  vs  outerjoin후 하느냐만 다르지**
- **`assoc + right(Post)를 inner join하는 것은 동일`하다**

![image-20221202145710319](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221202145710319.png)

```sql
SELECT tags.name, coalesce(count(posts.id), :coalesce_1) AS count, sum(CAST(posts.has_type AS INTEGER)) AS sum 
FROM tags LEFT OUTER JOIN (posttags AS posttags_1 JOIN posts ON posts.id = posttags_1.post_id) ON tags.id = posttags_1.tag_id GROUP BY tags.id ORDER BY coun
t DESC
 LIMIT :param_1
 
('tag_1', 6, 12)
('태그1', 2, 4)
('tag_2', 1, 2)

```

```sql
SELECT tags.name, coalesce(anon_1.count_1, :coalesce_1) AS count, coalesce(anon_1.sum_1, :coalesce_2) AS sum 
FROM tags LEFT OUTER JOIN (SELECT posttags.tag_id AS tag_id, count(posttags.post_id) AS count_1, sum(CAST(posts.has_type AS INTEGER)) AS sum_1
FROM posttags JOIN posts ON posts.id = posttags.post_id GROUP BY posttags.tag_id) AS anon_1 ON tags.id = anon_1.tag_id ORDER BY anon_1.count_1 DESC
 LIMIT :param_1
```





##### test

- outer join시 select에 2개 entity가 있을 경우, join에 **right테이블 or left.right테이블관계명을 명시해준다.**
  - **fk가 없거나 여러개면, right + 직접 기준key를 입력해야하고**
  - **fk가 여러개면, join대상 테이블의 left.right관계명만 입력해야한다.**
  - **MtoM상황에서는, fk가 없는 상태같지만, `fk가 있다고 가정하고 left.right관계명`으로 join걸면 된다.**

```python
stmt = select(Tag.name, Post.id) \
    .outerjoin(Tag.posts) \

print(stmt)
for d in db.session.execute(stmt):
    print(d)
    
SELECT tags.name, posts.id 
FROM tags LEFT OUTER JOIN (posttags AS posttags_1 JOIN posts ON posts.id = posttags_1.post_id) ON tags.id = posttags_1.tag_id
('11', 15)
('123', None)
('tag_1', 3)
('tag_1', 4)
('tag_1', 5)
('tag_1', 6)
('tag_1', 8)
('tag_1', 15)
('tag_2', 15)
('ㅇㅇㅇㅇ', 15)
('태그1', 3)
('태그1', 15)

```

```python
stmt = select(Tag.name, Post.id) \
    .join(Tag.posts) \

print(stmt)
for d in db.session.execute(stmt):
    print(d)

SELECT tags.name, posts.id 
FROM tags JOIN posttags AS posttags_1 ON tags.id = posttags_1.tag_id JOIN posts ON posts.id = posttags_1.post_id
('tag_1', 3)
('태그1', 3)
('tag_1', 6)
('tag_1', 5)
('tag_1', 4)
('tag_1', 8)
('태그1', 15)
('11', 15)
('ㅇㅇㅇㅇ', 15)
('tag_2', 15)
('tag_1', 15)

```

- right를 tag로 바꾼 outerjoin은.. Post에 tag가 없는 것들도 와장창 나올 것이다

```python
stmt = select(Tag.name, Post.id) \
    .outerjoin(Post.tags) \
    
SELECT tags.name, posts.id 
FROM posts LEFT OUTER JOIN (posttags AS posttags_1 JOIN tags ON tags.id = posttags_1.tag_id) ON posts.id = posttags_1.post_id
('tag_1', 3)
('태그1', 3)
('tag_1', 4)
('tag_1', 5)
('tag_1', 6)
('tag_1', 8)
(None, 10)
(None, 11)
(None, 12)
(None, 13)
(None, 14)
('11', 15)
('tag_1', 15)
('tag_2', 15)
('ㅇㅇㅇㅇ', 15)

```



### 최종 index

#### route 및 관련함수
```python

def to_string_date(last_month):
    return datetime.strftime(last_month, '%Y-%m-%d')


def get_user_pie_chart(db, entity, category_column):
    # 1) sql을 groupby에 카테고리를 올리고, 갯수를 센다
    # -> group_by 집계시에는 label을 못단다?
    # [(False, 2), (True, 2)]
    datas = db.session.execute(
        select(getattr(entity, category_column), func.count(entity.id))
        .group_by(getattr(entity, category_column))
    ).all()

    # print(datas)
    # [(False, 2), (True, 2)]

    # 2)카테고리 종류가 눈에 들어오기 슆게 바꿔야한다.
    datas = list(map(lambda x: ('관리자' if x[0] else '일반유저', x[1]), datas))
    # print(datas)
    # [('일반유저', 2), ('관리자', 2)]

    # 3) pie차트는 [ (category, count) ] tuple list를 입력으로 받는다.
    c = (
        Pie()
        .add("", datas)
    )
    return c


def get_diff_for(db, entity, interval='day', period=7):
    end_date = date.today()
    if interval == 'day':
        start_date = end_date - relativedelta(days=period)
    elif interval == 'month':
        start_date = end_date - relativedelta(months=period)
    elif interval == 'year':
        start_date = end_date - relativedelta(years=period)
    else:
        raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')

    end_count = db.session.scalar(
        select(func.count(entity.id))
        .where(and_(
            func.date(getattr(entity, 'add_date')) <= end_date)
        )
    )
    start_count = db.session.scalar(
        select(func.count(entity.id))
        .where(and_(
            func.date(getattr(entity, 'add_date')) <= start_date)
        )
    )
    # print(end_count - start_count, type(end_count))
    diff = end_count - start_count
    # start가 zero division
    try:
        rate_of_increase = round((end_count - start_count) / start_count, 2) * 100
    except:
        rate_of_increase = round(end_count * 100)
    # print(rate_of_increase)
    return diff, rate_of_increase


@admin_bp.route('/')
@login_required
def index():
    with DBConnectionHandler() as db:
        user_count = db.session.scalar(select(func.count(User.id)).where(User.is_super_user == False))
        user_count_diff, user_count_diff_rate = get_diff_for(db, User, interval='day', period=7)
        post_count = db.session.scalar(select(func.count(Post.id)))
        post_count_diff, post_count_diff_rate = get_diff_for(db, Post, interval='day', period=7)
        category_count = db.session.scalar(select(func.count(Category.id)))
        category_count_diff, category_count_diff_rate = get_diff_for(db, Category, interval='day', period=7)
        banner_count = db.session.scalar(select(func.count(Banner.id)))
        banner_count_diff, banner_count_diff_rate = get_diff_for(db, Banner, interval='day', period=7)

        # 연결되어있는 것도  sql문으로하려면, 직접 where에 연결해줘야한다(꽁join 아니면)
        ## none을 0개로 셀땐 func.coalesce(values.c.cnt, 0)
        # stmt = select(Category.name, func.count(Post.id).label('count')) \
        #     .where(Post.category_id == Category.id) \
        #     .group_by(Post.category_id)

        ## post 갯수0짜리도 찍히게 하려면,[사실상 one별 many의 집계] => many에서 fk별 집계한 뒤, one에 fk==id로 붙인다.
        ##  (1) Post에서 subquery로 미리 카테고리id별 count를 subquery로 계산
        ##  (2) Category에 category별 count를 left outer join
        ## => main_06_subquery_cte_기본.py 참고
        #### < 1-1 category별 post 갯수>
        subq = select(Post.category_id, func.coalesce(func.count(Post.id), 0).label('count')) \
            .group_by(Post.category_id) \
            .subquery()
        stmt = select(Category.name, subq.c.count) \
            .join_from(Category, subq, isouter=True) \
            .order_by(subq.c.count.desc())
        # [('분류1', 5), ('22', 2)]
        post_count_by_category = db.session.execute(stmt)
        post_by_category_x_datas = []
        post_by_category_y_datas = []
        for category, post_cnt_by_category in post_count_by_category:
            post_by_category_x_datas.append(category)
            post_by_category_y_datas.append(post_cnt_by_category)
        #### < 1-2 post가 가장 많이 걸린 tag> -> Tag별 post갯수세기 -> 중간테이블이라서 바로 집계되지만, name을 얻으려면 left join
        #### => left.right관계명으로 assoc table무시하고, outerjoin을 건다(내부에서 assoc 와 right(Post)를 일반join한 뒤 outerjoin한다)
        # stmt = select(Tag.name, func.coalesce(Post.id, 0).label('count'), func.coalesce(cast(Post.has_type, Integer), 0).label('sum')) \
        stmt = select(Tag.name, func.coalesce(func.count(Post.id), 0).label('count'), func.sum(cast(Post.has_type, Integer)).label('sum')) \
            .join(Tag.posts, isouter=True) \
            .group_by(Tag.id) \
            .order_by(literal_column('count').desc()) \
            .limit(3)
        tag_with_post_count = db.session.execute(stmt).all()

        #### < 2-1 일주일 user 수>
        user_chart = get_user_chart(db)
        # <2-2-2 user 성별 piechart > 아직 성별칼럼이 없으니 직원수 vs 일반 유저로 비교해보자.
        user_sex_pie_chart = get_user_pie_chart(db, User, 'is_super_user')

        ### 만약, df로 만들거라면 row별로 dict()를 치면 row1당 column:value의 dict list가 된다.
        # print([dict(r) for r in db.session.execute(stmt)])

        #### < 월별 연간 통계 by pyerchart>
        year_x_datas, year_post_y_datas = get_datas_count_by_date(db, Post, 'add_date', interval='month', period=12)
        _, year_user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='month', period=12)
        _, year_category_y_datas = get_datas_count_by_date(db, Category, 'add_date', interval='month', period=12)
        _, year_banner_y_datas = get_datas_count_by_date(db, Banner, 'add_date', interval='month', period=12)
        _, year_tag_y_datas = get_datas_count_by_date(db, Tag, 'add_date', interval='month', period=12)
        year_chart = (
            Bar()
            .add_xaxis(year_x_datas)
            .add_yaxis('유저 수', year_user_y_datas)  # y축은 name먼저
            .add_yaxis('포스트 수', year_post_y_datas)
            .add_yaxis('카테고리 수', year_category_y_datas)
            .add_yaxis('배너 수', year_banner_y_datas)
            .add_yaxis('태그 수', year_tag_y_datas)
        )



    return render_template('admin/index.html',
                           user_count=(user_count, user_count_diff_rate),
                           post_count=(post_count, post_count_diff_rate),
                           category_count=(category_count, category_count_diff_rate),
                           banner_count=(banner_count, banner_count_diff_rate),

                           post_by_category=(post_by_category_x_datas, post_by_category_y_datas),
                           tag_with_post_count=tag_with_post_count,

                           user_count_bar_options=user_chart.dump_options(),
                           user_sex_pie_options=user_sex_pie_chart.dump_options(),
                           year_options=year_chart.dump_options(),

                           chart=[user_chart, user_sex_pie_chart]
                           )


def get_user_chart(db):
    user_x_datas, user_y_datas = get_datas_count_by_date(db, User, 'add_date', interval='day', period=7)
    #
    user_chart = (
        Bar()
        .add_xaxis(user_x_datas)
        .add_yaxis('유저 수', user_y_datas)
    )
    return user_chart


def get_datas_count_by_date(db, entity, date_column_name, interval='day', period=7):
    end_date = date.today()  # end_date는 datetime칼럼이라도, date기준으로
    if interval == 'day':
        start_date = end_date - relativedelta(days=period)
    elif interval == 'month':
        start_date = end_date - relativedelta(months=period)
    elif interval == 'year':
        start_date = end_date - relativedelta(years=period)
    else:
        raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')

    series = generate_series_subquery(start_date, end_date, interval=interval)
    ### subquery를 확인시에는 .select()로 만들어서 .all()후 출력
    # print(db.session.execute(series.select()).all())
    # print(ts, type(ts))
    ## 3) User의 생싱일date별 count 집계하기
    # [('2022-11-19', 1), ('2022-11-25', 2)]
    ## ==> datetime필드를, date기준으로 filtering하고 싶다면
    ##     칼럼.between()에 못넣는다.
    ## ==> datetime -> date로 칼럼을 변경하고 filter해야지, 오늘13시도, today()에 걸린다
    ## 만약, today() 2022-11-29를   2022-11-29 13:00:00 datetime필드로 필터링하면
    ##  오늘에 해당 데이터가 안걸린다. 데이터를 일단 변환하고 필터링에 넣어야한다.
    # select(func.date(User.add_date).label('date'), func.count(User.id).label('count')) \
    values = count_by_date_subquery(interval, entity, date_column_name, end_date, start_date)
    # print(db.session.execute(values.select()).all())

    # .group_by(func.strftime("%Y", User.add_date).label('date'))\
    # => [('2022', 4)]
    # .group_by(func.date(User.add_date).label('date'))\
    # .group_by(func.date(User.add_date))
    # print(db.session.execute(values.select()).all())
    # [('2022-11-19', 1), ('2022-11-25', 2), ... ('2022-11-29', 1)]
    ## 3) series에 values르 outerjoin with 없는 데이터는 0으로
    stmt = (
        select(series.c.date, func.coalesce(values.c.count, 0).label('count'))
        .outerjoin(values, values.c.date == series.c.date)
        .order_by(series.c.date.asc())
    )
    ## scalars()하면 date만 나온다.
    # print(db.session.scalars(stmt).all())
    # [('2022-10-29', 0), ('2022-10-30', 0), ... ('2022-11-25', 2), ('2022-11-26', 0), ('2022-11-27', 0), ('2022-11-28', 0), ('2022-11-29', 1)]
    # print(db.session.execute(stmt).all())
    x_datas = []
    y_datas = []
    for day, user_count in db.session.execute(stmt):
        x_datas.append(day)
        y_datas.append(user_count)
    # 집계대상 필터링은 Y-m-d(date) -> group_by strftime으로 (day) or Y-m-d/(month)Y-m/(year)Y 상태
    # 이미 문자열로 Y-m-d  or Y-m  or Y 중 1개로 정해진 상태다. -> -로 split한 뒤 마지막거만 가져오면 interval 단위
    # => 출력을 위해 day단위면, d만 / month단위면 m만 나가도록 해준다 (year는 이미 Y)
    if interval == 'day':
        x_datas = list(map(lambda x: x.split('-')[-1] + '일', x_datas))
    elif interval == 'month':
        x_datas = list(map(lambda x: x.split('-')[-1] + '월', x_datas))  # 이미 Y-m그룹화 상태
    elif interval == 'year':
        x_datas = list(map(lambda x: x + '년', x_datas))
    return x_datas, y_datas


def count_by_date_subquery(interval, entity, date_column_name, end_date, start_date):
    if interval == 'day':
        strftime_format = '%Y-%m-%d'
    elif interval == 'month':
        strftime_format = '%Y-%m'
    elif interval == 'year':
        strftime_format = '%Y'
    else:
        raise ValueError('invalid aggregation interval(string, day or month or year) & period=int')

    return (
        select(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'),
               func.count(entity.id).label('count'))
        .where(and_(
            start_date <= func.date(getattr(entity, date_column_name)),
            func.date(getattr(entity, date_column_name)) <= end_date)
        )
        .group_by(func.strftime(strftime_format, getattr(entity, date_column_name)).label('date'))
        .subquery()
    )


def generate_series_subquery(start_date, end_date, interval='day'):
    if interval == 'day':
        strftime_format = '%Y-%m-%d'
    if interval == 'month':
        strftime_format = '%Y-%m'
    elif interval == 'year':
        strftime_format = '%Y'

    # select date form dates담에 ;를 넘으면 outer join시 에러
    _text = text(f"""
        WITH RECURSIVE dates(date) AS (
              VALUES (:start_date)
          UNION ALL
              SELECT date(date, '+1 {interval}')
              FROM dates
              WHERE date < :end_date
        )
        SELECT strftime('{strftime_format}', date) AS 'date' FROM dates
        """).bindparams(start_date=to_string_date(start_date), end_date=to_string_date(end_date))
    # func.to_char(orig_datetime, 'YYYY-MM-DD HH24:MI:SS
    # SELECT strftime('%Y', date) FROM dates

    # with DBConnectionHandler() as db:
    #     print(db.session.execute(stmt.columns(column('date')).label('date')).subquery('series').select()).all())
    ## output 1 - date는 date타입이지만, 출력은 문자열로 된다.
    # unit=day
    # [('2022-10-29',), ('2022-10-30',),... ('2022-11-28',), ('2022-11-29',)]

    # unit=month
    # [('2022-10-29',), ('2022-11-29',)]
    # unit=year
    # [('2021-11-30',), ('2022-11-30',)]
    ## output 2 - sqlite SELECT strftime('%Y', CURRENT_TIMESTAMP)으로
    ##            그외는  SELECT EXTRACT(YEAR FROM CURRENT_DATE) 를 쓴다.
    # => month일땐, Y-m으로  / year일땐, Y로만 나와야, 거기에 맞춘 values를 outer_join 시킬수 있을 것이다.
    # => text.columns(column()) 지정시 func.extract로 변경하자.
    # [('2021-11-30',), ('2022-11-30',)]
    # if interval == 'year':
    #     return stmt.columns(extract('year',column('date'))).subquery('series')

    return _text.columns(column('date')).subquery('series')
```

#### admin/index.html
##### front - 72_index_change_after_index_route_static.html
```html
{% extends 'base.html' %}

{% block title %}
{{ g.user['username'] }}-내 정보
{% endblock title %}

{% block extra_head_style %}
<!-- echart js & axios -->
<!--suppress BadExpressionStatementJS -->
<script src="{{url_for('static', filename='js/admin/echarts.min.js')}}"></script>
<script src="https://unpkg.com/axios/dist/axios.min.js"></script>
<script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
{% endblock extra_head_style %}

{% block hero %}{% endblock hero %}

<!--base.html에서 <block main > 내부 <div class="box is-marginless is-shadowless is-radiusless"> 바로 아래
div.box 안쪽으로  block box /endblock을 추가한다-->

{% block box %}
<div class="columns">
    <!-- admin의 왼쪽메뉴 column 2칸 -->
    <div class="column is-2">
        <div class="card is-shadowless" style="border-right:solid 1px #eee">
            <div class="card-content">
                <!--  aside왼쪽메뉴를 채우는 block( 자식중에 나를 상속해서 다르게 채울 수 있는 block -->
                {% block menus %}
                <aside class="menu">
                    <p class="menu-label">
                        <span class="icon"><i class="mdi mdi-google-assistant"></i></span>
                        Dashboard | {{request.path}}
                    </p>
                    <ul class="menu-list">
                        <li>
                            <a class="{% if request.path == '/admin/' %}is-active{% endif %}"
                               href="{{ url_for('admin.index') }}">
                                <span class="icon"><i class="mdi mdi-home-variant-outline"></i></span>
                                Home
                            </a>
                        </li>
                    </ul>
                    <p class="menu-label">
                        <span class="icon"><i class="mdi mdi-shape-outline"></i></span>
                        Category
                    </p>
                    <ul class="menu-list">
                        <!-- 각 entity별 select route/tempalte완성시 마다 걸어주기 -->
                        <li>
                            <a class="{% if 'category' in request.path %}is-active{% endif %}"
                               href="{{ url_for('admin.category') }}">
                                <span class="icon"><i class="mdi mdi-menu"></i></span>
                                Category 관리
                            </a>
                        </li>
                    </ul>
                    <p class="menu-label">
                        <span class="icon"><i class="mdi mdi-clipboard-text-multiple-outline"></i></span>
                        Article
                    </p>
                    <ul class="menu-list">
                        <li>
                            <a class="{% if 'article' in request.path %}is-active{% endif %}"
                               href="{{ url_for('admin.article') }}">
                                <span class="icon"><i class="mdi mdi-clipboard-text-outline"></i></span>
                                Post 관리
                            </a>
                        </li>
                        <li>
                            <a class="{% if 'tag' in request.path %}is-active{% endif %}"
                               href="{{ url_for('admin.tag') }}">
                                <span class="icon"><i class="mdi mdi-tag-plus-outline"></i></span>
                                Tag 관리
                            </a>
                        </li>
                    </ul>

                    <p class="menu-label">
                        <span class="icon"><i class="mdi mdi-account-group-outline"></i></span>
                        User
                    </p>
                    <ul class="menu-list">
                        <li>
                            <a class="{% if 'user' in request.path %}is-active{% endif %}"
                               href="{{ url_for('admin.user') }}">
                                <span class="icon"><i class="mdi mdi-account-outline"></i></span>
                                User 관리
                            </a>
                        </li>
                        <li>
                            <a class="{% if 'password' in request.path %}is-active{% endif %}"
                               href="{{ url_for('admin.user') }}">
                                <span class="icon"><i class="mdi mdi-lock-outline"></i></span>
                                비밀번호 변경
                            </a>
                        </li>
                    </ul>


                    <p class="menu-label">
                        <span class="icon"><i class="mdi mdi-cog-outline"></i></span>
                        Banner
                    </p>
                    <ul class="menu-list">
                        <li>
                            <a class="{% if 'banner' in request.path %}is-active{% endif %}"
                               href="{{ url_for('admin.banner') }}">
                                <span class="icon"><i class="mdi mdi-image-sync-outline"></i></span>
                                Banner 관리
                            </a>
                        </li>
                    </ul>

                </aside>
                {% endblock menus %}
            </div>
        </div>
    </div>
    <div class="column">
        {% block member %}
        <!-- 내부요소들의 text 모두 가운데 정렬:has-text-centered -->
        <div class="tile is-ancestor">

            <div class="tile is-parent">
                <article class="tile is-child notification is-warning is-light">
                    <div class="content">
                        <p class="subtitle is-size-6 mb-5">
                            📑 카테고리 수
                        </p>
                        <p class="title has-text-black">
                            {{category_count[0]}}
                            <span class="is-size-6">
                                {% if category_count[1] > 0 %}
                                <span class="has-text-success-dark">
                                            {{category_count[1]}}%
                                            <i class="mdi mdi-trending-up"></i>
                                </span>
                                {% elif category_count[1] == 0 %}
                                <span class="has-text-grey">
                                            {{category_count[1]}}%
                                            <i class="mdi mdi-trending-neutral"></i>
                                </span>
                                {% else %}
                                <span class="has-text-danger-dark">
                                            {{category_count[1]}}%
                                            <i class="mdi mdi-trending-down"></i>
                                </span>
                                {% endif %}
                            </span>
                        </p>
                    </div>
                </article>
            </div>

            <div class="tile is-parent">
                <article class="tile is-child notification is-info is-light">
                    <div class="content">
                        <p class="subtitle is-size-6 mb-5">
                            🧾 Post 수
                        </p>
                        <p class="title has-text-black">
                            {{post_count[0]}}
                            <span class="is-size-6">
                                {% if post_count[1] > 0 %}
                                <span class="has-text-success-dark">
                                            {{post_count[1]}}%
                                            <i class="mdi mdi-trending-up"></i>
                                </span>
                                {% elif post_count[1] == 0 %}
                                <span class="has-text-grey">
                                            {{post_count[1]}}%
                                            <i class="mdi mdi-trending-neutral"></i>
                                </span>
                                {% else %}
                                <span class="has-text-danger-dark">
                                            {{post_count[1]}}%
                                            <i class="mdi mdi-trending-down"></i>
                                </span>
                                {% endif %}
                            </span>
                        </p>
                    </div>
                </article>
            </div>
            <div class="tile is-parent">
                <article class="tile is-child notification is-danger is-light">
                    <div class="content">
                        <p class="subtitle is-size-6 mb-5">
                            👦 유저 수
                        </p>
                        <p class="title has-text-black">
                            {{user_count[0]}}
                            <span class="is-size-6">
                                {% if user_count[1] > 0 %}
                                <span class="has-text-success-dark">
                                            {{user_count[1]}}%
                                            <i class="mdi mdi-trending-up"></i>
                                </span>
                                {% elif user_count[1] == 0 %}
                                <span class="has-text-grey">
                                            {{user_count[1]}}%
                                            <i class="mdi mdi-trending-neutral"></i>
                                </span>
                                {% else %}
                                <span class="has-text-danger-dark">
                                            {{user_count[1]}}%
                                            <i class="mdi mdi-trending-down"></i>
                                </span>
                                {% endif %}
                            </span>
                        </p>
                    </div>
                </article>
            </div>
            <div class="tile is-parent">
                <article class="tile is-child notification is-light">
                    <div class="content">
                        <p class="subtitle is-size-6 mb-5">
                            📸 배너 수
                        </p>
                        <p class="title has-text-black">
                            {{banner_count[0]}}
                            <span class="is-size-6">
                                {% if banner_count[1] > 0 %}
                                <span class="has-text-success-dark">
                                            {{banner_count[1]}}%
                                            <i class="mdi mdi-trending-up"></i>
                                </span>
                                {% elif banner_count[1] == 0 %}
                                <span class="has-text-grey">
                                            {{banner_count[1]}}%
                                            <i class="mdi mdi-trending-neutral"></i>
                                </span>
                                {% else %}
                                <span class="has-text-danger-dark">
                                            {{banner_count[1]}}%
                                            <i class="mdi mdi-trending-down"></i>
                                </span>
                                {% endif %}
                            </span>
                        </p>
                    </div>
                </article>
            </div>
        </div>

        <!-- column - 2 chart 2개를 위한 tile 깔기 -->
        <!-- is-ancestor > 아래 개별요소마다 sm에서 각각 나눠지는 is-parent까지만 구분-->
        <div class="tile is-ancestor ">
            <!-- 사이즈는 is-parent에선 나눠가지면 되고 일단 맨 왼쪽놈만 주면 된다.-->
            <div class="tile is-parent is-5 ">
                <article class="tile is-child notification is-white"
                         style="border: 1px solid lightgray;"
                >
                    <div class="content">
                        <p class="title is-size-5">📚 카테고리 통계</p>
                        <!--                        <p class="subtitle is-size-6 ml-1 my-1">카테고리별 Post 수 집계</p>-->
                        <div id="post_chart" class="content"
                             style="width: 100%; min-height: 250px">
                            <!-- Content -->
                            chart
                        </div>
                        <p class="title is-size-5">🔖 태그 통계</p>
                        <!--                        <p class="subtitle is-size-6 ml-1 my-1">tag별 post 수 집계</p>-->
                        <div class="content has-text-centered"
                             style="width: 100%; min-height: 150px"
                        >
                            <!-- post 딸린 수 상위 2개 Tag table -->
                            <table class="table is-fullwidth is-hoverable is-striped">
                                <thead>
                                <tr>
                                    <th>랭킹</th>
                                    <th>태그이름</th>
                                    <th>Post수</th>
                                    <th>누적조회수</th>
                                </tr>
                                </thead>
                                <tbody>
                                {% for tag in tag_with_post_count %}
                                <tr>
                                    <td>
                                        <div class="tags">
                                            <span class="tag is-light">
                                              {{loop.index}}위
                                            </span>
                                        </div>
                                    </td>
                                    <td>
                                        <div class="tags">
                                            <span class="tag is-primary is-light">
                                                {{ tag.name }}
                                            </span>
                                        </div>
                                    </td>
                                    <td>{{ tag.count }}</td>
                                    <td>{{ tag.sum }}</td>
                                </tr>
                                {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </article>
            </div>
            <div class="tile is-parent">
                <!--  notification class를 빼면 내부 tab의 밑줄이 사라짐. 그러면 정렬이 깨짐 -->
                <!--                <article class="tile is-child is-white"-->
                <article class="tile is-child notification is-white"
                         style="border: 1px solid lightgray;"
                >
                    <div class="content">
                        <p class="title is-size-5">✨ 유저 통계</p>
                        <!-- 일주일간 유저 수 -->
                        <p class="subtitle is-size-6 ml-1 my-1">지난 7일 등록 유저 수</p>
                        <div id="user_count_bar_chart" class="content" style="width: 100%; min-height: 250px"
                        >
                            <!-- Content -->
                            chart
                        </div>
                        <!-- chart2 유저 성별별 카운트 -->
                        <p class="subtitle is-size-6 ml-1 my-1">성별별 유저 수</p>
                        <div id="user_sex_pie_chart" class="content" style="width: 100%; min-height: 150px;"
                        >

                        </div>

                    </div>
                </article>

            </div>

        </div>

        <!-- 년간 chart 1줄 -->
        <div class="tile is-ancestor ">
            <div class="tile is-parent">
                <article class="tile is-child notification is-white"
                         style="border: 1px solid lightgray;"
                >
                    <div class="content">
                        <p class="title is-size-5">🗓 년간 통계</p>
                        <p class="subtitle is-size-6 ml-1 my-1">월별 데이터 변화</p>
                        <div id="year_chart" class="content" style="width: 100%; min-height: 300px">
                            <!-- Content -->
                            chart
                        </div>
                    </div>
                </article>
            </div>
        </div>

        {% endblock member %}
    </div>
</div>
{% endblock box %}

{% block vue_script %}
<script type="text/javascript">

    // category별 post
    let postChart = echarts.init(document.getElementById('post_chart'));

    let tab_0 = document.getElementById('user_count_bar_chart');
    let userChart1 = echarts.init(tab_0);
    let tab_1 = document.getElementById('user_sex_pie_chart');
    let userChart2 = echarts.init(tab_1);

    let yearChart = echarts.init(document.getElementById('year_chart'));

    // 차트를 반응형으로 (width:100%, min-height:300px)상태에서
    window.onresize = function () {
        console.log("window.onresize")
        postChart.resize();
        userChart1.resize();
        userChart2.resize();
        yearChart.resize();
    };

    // pyecharts 사용시,option을 backend에서 받은 것을 |safe로
    //user_count_bar_options | safe
    userChart1.setOption({{user_count_bar_options | safe}})
    //user_sex_pie_options | safe
    userChart2.setOption({{user_sex_pie_options | safe}})
    //year_options | safe
    yearChart.setOption({{year_options | safe}})


    // Specify the configuration items and data for the chart
    let postChartOption = {
        // title: {
        //     text: 'ECharts Getting Started Example'
        // },
        tooltip: {},
        legend: {
            data: ['카테고리'] // series의 name과 일치해야한다
        },
        xAxis: {
            data: JSON.parse('{{post_by_category[0] | tojson}}')
        },
        yAxis: {},
        series: [
            {
                name: '카테고리',
                type: 'bar',
                data: JSON.parse('{{post_by_category[1] | tojson}}'),
                // bar에 색 넣기
                itemStyle: {
                    color: function (param) {
                        const color = ['#76b143', '#7d7c6a', '#0065b3', '#7d7c6a',];
                        // param.value[0] is the x-axis value
                        // param.value is data 값
                        // param.dataIndex is 0부터 순서
                        // console.log(param)
                        return color[param.dataIndex % color.length]
                    }
                },
            }
        ]
    };


    // Display the chart using the configuration items and data just specified.
    postChart.setOption(postChartOption);

</script>

{% endblock vue_script %}
```