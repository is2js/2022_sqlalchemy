admin - 모든 entity별 route+form+template개발(auth관련은 미리 만들었음)

- admin는 index부터 모든 route들이 @login_required다

### Category(one)

#### 6 category entity select

#####  category select route

```python
@admin_bp.route('/category')
@login_required
def category():
    
    return render_template('admin/category.html')
```



##### admin /category.html 생성

![image-20221113171113451](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113171113451.png)



##### category.html 구성하며 알아보기

1. 일단 base.html을 상속받고 **`box` block만 바꿔채우는 `admin/index.html`**를 상속하여  **`member`block만 `각 entity.html들`이 채운다.**

   - admin/indxr.html

     ![image-20221113173920185](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113173920185.png)

   - admin/category.html

     ![image-20221113174001494](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113174001494.png)

     ![image-20221113174041367](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113174041367.png)





2. **member block 내부에서 `div.is-block`을 만들고, `div.is-pulled-left`로 제목을 작성한다.**

   - 제목은 div안에 **`h1태그`안에 `span>i`와 `텍스트`로 작성**한다

   ```html
   {% extends 'admin/index.html' %}
   
   {% block member %}
   <div class="is-block">
       <div class="is-pulled-left">
           <h1 class="is-size-4">
               <span class="icon">
                   <i class="mdi mdi-receipt-outline"></i>
               </span>
               Category 관리
           </h1>
       </div>
   </div>
   {% endblock member %}
   ```

   

   ![image-20221113175403120](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113175403120.png)







3. **`나를 상속할 category_form.html`을 생각하며 `달라지는 부분으로서 block개설하면서` div.is-pulled-right로 button을 단다**

   - 제목(div안에 **`h1태그`안에 `span>i`와 `텍스트`로 작성**)과 달리
   - 버튼은 div안에 **`a태그`안에 `span>i`와 `span>텍스트`로 작성**

   ```html
   {% extends 'admin/index.html' %}
   
   {% block member %}
   <div class="is-block">
       <!-- 제목 -->
       <div class="is-pulled-left">
           <h1 class="is-size-4">
               <span class="icon"><i class="mdi mdi-receipt-outline"></i></span>
               Category 관리
           </h1>
       </div>
       <!-- 버튼(상속할 form에선 달라짐) -> block개설 -->
       {% block button %}
       <div class="is-pulled-right">
           <a href="" class="button is-primary is-light">
               <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
               <span>Category 추가</span>
           </a>
       </div>
       {% endblock button %}
   </div>
   {% endblock member %}
   ```

   

   ![image-20221113180138749](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113180138749.png)

4. **분류선을 주되 위쪽에서 pulled를 썼다면 div.is-clearfix가 필수다**

   ```html
   {% extends 'admin/index.html' %}
   
   {% block member %}
   <div class="is-block">
       <!-- 제목 -->
       <div class="is-pulled-left">
           <h1 class="is-size-4">
               <span class="icon"><i class="mdi mdi-receipt-outline"></i></span>
               Category 관리
           </h1>
       </div>
       <!-- 버튼(상속할 form에선 달라짐) -> block개설 -->
       {% block button %}
       <div class="is-pulled-right">
           <a href="" class="button is-primary is-light">
               <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
               <span>Category 추가</span>
           </a>
       </div>
       {% endblock button %}
       <!--  분류선 by div2개: pulled-쓰과서 is-clearfix는 필수  -->
       <div class="is-clearfix"></div>
       <div class="dropdown-divider"></div>
   </div>
   {% endblock member %}
   ```

   - is-clearfix안주면

     ![image-20221113180600516](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113180600516.png)

   - 주면

     ![image-20221113180617074](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113180617074.png)

5. 아래쪽 table의 처리에 대한 flash메세지를  위쪽 `div.is-block`끝에서 처리

   ```html
       <!-- 아래쪽 table의 처리에 대한 flash 메세지를 위쪽에서   -->
       {% with messages = get_flashed_messages() %}
       <b-message type="is-success">
         {% if messages %}
         <ul class=flashes>
           {% for message in messages %}
           <li>{{ message }}</li>
           {% endfor %}
         </ul>
         {% endif %}
       </b-message>
       {% endwith %}
   </div>
   {% endblock member %}
   ```

   

6. 나를 상속할 category_form에 대비하여 **table_content block개설**하여 **category 데이터 만들 자리 만들기**

   ```html
       {% endwith %}
   </div>
   
   <!-- 위쪽 아래쪽 table or form 공간 -->
   {% block table_content %}
   asdf
   {% endblock table_content %}
   
   
   {% endblock member %}
   ```

   

   ![image-20221114013007878](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114013007878.png)

7. **table or form block공간 table로 채우기 -> `for`안에 있는 jinja는 주석처리 안해줘도 된다. 그러나 route돌릴때 바로 에러나니까 `처리용td의 a태그들의 href 주석처리`**

   - div.table-container
     - table.table
       - thead
         - tr ( 칼럼별 이름은 하드코딩으로 작성한다.)
           - 칼럼별 이름 td
           - **객체 처리용 클릭div>a태그들의 이름 td ** 
       - tbody
         - **객체list 반복문** 
         - tr
           - 객체값별td
           - **객체 처리를 위한 클릭a td들**
             - div.tags
               - a
                 - span.icon>i
                 - 텍스트

   ```html
   <!-- 위쪽 아래쪽 table or form 공간 -->
   {% block table_content %}
   <div class="table-container">
       <table class="table is-fullwidth is-hoverable is-striped">
           <thead>
           <tr>
               <th>Id</th>
               <th>이름</th>
               <th>아이콘</th>
               <th>생성일</th>
               <th>작업</th>
           </tr>
           </thead>
           <tbody>
           <!--  route에서 cateogry객체들을 id역순으로 넘겨주면, for문이 돌아가면서 a태그 에러가 걸리게 됨.  -->
           <!--  a태그-href들 주석처리된 상태  -->
           {% for cate in category_list %}
           <tr>
               <td>{{ cate.id }}</td>
               <td>{{ cate.name }}</td>
               <td>{{ cate.icon }}</td>
               <td>{{ cate.add_date }}</td>
               <td>
                   <div class="tags">
   <!--                    <a href="xx url_for('admin.category_edit', cate_id=cate.id) xx" class="tag is-success is-light">-->
                       <a href="" class="tag is-success is-light">
                               <span class="icon">
                                   <i class="mdi mdi-square-edit-outline"></i>
                               </span>
                           编辑
                       </a>
   <!--                    <a href="xx url_for('admin.category_del', cate_id=cate.id) xx" class="tag is-danger is-light">-->
                       <a href="" class="tag is-danger is-light">
                               <span class="icon">
                                    <i class="mdi mdi-trash-can-outline"></i>
                               </span>
                           删除
                       </a>
                   </div>
               </td>
           </tr>
           {% endfor %}
           </tbody>
       </table>
   </div>
   {% endblock table_content %}
   ```

   ![image-20221114013934390](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114013934390.png)

###### table부턴 route랑 협업

7. **entity select html은 `route에서 데이터를 넘겨줘`서 `빈 table`을 구성하면서 만들어야한다.**

   ```python
   @admin_bp.route('/category')
   @login_required
   def category():
       with DBConnectionHandler() as db:
           # admin- table에는 id역순으로 제공해줘야 최신순으로 보인다.
           category_list = db.session.scalars((
               select(Category)
               .order_by(Category.id.desc())
           )).all()
   
       return render_template('admin/category.html', category_list=category_list)
   
   ```

   ![image-20221114014856689](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114014856689.png)

   

8. **jinja를 주석처리한 페이지네이션을 div.table-container밖에 `nav.pagination`태그로 추가한다**

   ```html
       </table>
   </div>
   
   <nav class="pagination is-small" role="navigation" aria-label="pagination">
   <!--xx if pagination.has_prev xx-->
   <!--    <a href="xx url_for('admin.category') xx?page=xx pagination.prev_num xx" class="pagination-previous" title="This is the first page">Previous</a>-->
   <a href="" class="pagination-previous" title="This is the first page">Previous</a>
   <!--xx endif xx-->
   <!--xx if pagination.has_next xx-->
   <!--    <a href="xx url_for('admin.category') xx?page=xx pagination.next_num xx" class="pagination-next">Next page</a>-->
   <a href="" class="pagination-next">Next page</a>
   <!--xx endif xx-->
   
   <ul class="pagination-list">
   <!--    xx for page in pagination.iter_pages() xx-->
   <!--        xx if page xx-->
   <!--            xx if page != pagination.page xx-->
               <li>
   <!--                <a href="xx url_for('admin.category') xx?page=xx page xx" class="pagination-link" aria-label="Page 1" aria-current="page">xx page xx</a>-->
                   <a href="" class="pagination-link" aria-label="Page 1" aria-current="page">1</a>
               </li>
   <!--            xx else xx-->
               <li>
   <!--                <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">xx page xx</a>-->
                   <a class="pagination-link is-current" aria-label="Page 1" aria-current="page"> 1 </a>
               </li>
   <!--            xx endif xx-->
   <!--        xx else xx-->
               <span class=pagination-ellipsis>&hellip;</span>
   <!--        xx endif xx-->
   <!--    xx endfor xx-->
   
   </ul>
   </nav>
   
   {% endblock table_content %}
   ```

   ![image-20221114020317723](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114020317723.png)



##### front - 09_category_extends_admin.index.html_after_category.route.html

```html
{% extends 'admin/index.html' %}

{% block member %}
<!-- 위쪽 제목 공간 -->
<div class="is-block">
    <!-- left 제목 -->
    <div class="is-pulled-left">
        <h1 class="is-size-4">
            <span class="icon"><i class="mdi mdi-receipt-outline"></i></span>
            Category 관리
        </h1>
    </div>
    <!-- right 버튼(상속할 form에선 달라짐) -> block개설 -->
    {% block button %}
    <div class="is-pulled-right">
        <!--  route) category_add route 및 category_form.html 개발 후 href채우기  -->
        <a href="" class="button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>Category 추가</span>
        </a>
    </div>
    {% endblock button %}
    <!--  분류선 by div2개: pulled-쓰과서 is-clearfix는 필수  -->
    <div class="is-clearfix"></div>
    <div class="dropdown-divider"></div>

    <!-- 아래쪽 table의 처리에 대한 flash 메세지를 위쪽에서   -->
    {% with messages = get_flashed_messages() %}
    <b-message type="is-success">
        {% if messages %}
        <ul class=flashes>
            {% for message in messages %}
            <li>{{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </b-message>
    {% endwith %}
</div>

<!-- 위쪽 아래쪽 table or form 공간 -->
{% block table_content %}
<div class="table-container">
    <table class="table is-fullwidth is-hoverable is-striped">
        <thead>
        <tr>
            <th>Id</th>
            <th>이름</th>
            <th>아이콘</th>
            <th>생성일</th>
            <th>작업</th>
        </tr>
        </thead>
        <tbody>
        <!--  route) 에서 cateogry객체들을 id역순으로 넘겨주면, for문이 돌아가면서 a태그 에러가 걸리게 됨.  -->
        <!--  a태그-href들 주석처리된 상태  -->
        {% for cate in category_list %}
        <tr>
            <td>{{ cate.id }}</td>
            <td>{{ cate.name }}</td>
            <td>{{ cate.icon }}</td>
            <td>{{ cate.add_date }}</td>
            <td>
                <div class="tags">
<!--                    <a href="xx url_for('admin.category_edit', cate_id=cate.id) xx" class="tag is-success is-light">-->
                    <a href="" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
<!--                    <a href="xx url_for('admin.category_del', cate_id=cate.id) xx" class="tag is-danger is-light">-->
                    <a href="" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
                </div>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
<!-- route) 에서 category_list외에 [pagination]객체도 던져줘야한다-->
<nav class="pagination is-small" role="navigation" aria-label="pagination">
<!--xx if pagination.has_prev xx-->
<!--    <a href="xx url_for('admin.category') xx?page=xx pagination.prev_num xx" class="pagination-previous" title="This is the first page">Previous</a>-->
<a href="" class="pagination-previous" title="This is the first page">Previous</a>
<!--xx endif xx-->
<!--xx if pagination.has_next xx-->
<!--    <a href="xx url_for('admin.category') xx?page=xx pagination.next_num xx" class="pagination-next">Next page</a>-->
<a href="" class="pagination-next">Next page</a>
<!--xx endif xx-->

<ul class="pagination-list">
<!--    xx for page in pagination.iter_pages() xx-->
<!--        xx if page xx-->
<!--            xx if page != pagination.page xx-->
            <li>
<!--                <a href="xx url_for('admin.category') xx?page=xx page xx" class="pagination-link" aria-label="Page 1" aria-current="page">xx page xx</a>-->
                <a href="" class="pagination-link" aria-label="Page 1" aria-current="page">1</a>
            </li>
<!--            xx else xx-->
            <li>
<!--                <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">xx page xx</a>-->
                <a class="pagination-link is-current" aria-label="Page 1" aria-current="page"> 1 </a>
            </li>
<!--            xx endif xx-->
<!--        xx else xx-->
            <span class=pagination-ellipsis>&hellip;</span>
<!--        xx endif xx-->
<!--    xx endfor xx-->

</ul>
</nav>

{% endblock table_content %}


{% endblock member %}
```



##### category view route에 pagination 처리하기

- Pagination class를 정의한다.

  - route에서 pagination.`items` 를 뽑아서 category_list=로 직접 전달하는 것외에

  - html에서 pagination객체가 직접 사용되는 예는

    - `.has_prev`, `prev_num`

    - `.has_next`, `next_num`

    - `.iter_pages()`

      - page

      - **이전에는 pages -> 끝번호를 반환하도록 하고 -> range(1, )부터 돌렸었다**

        ![image-20221114030737157](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114030737157.png)

      - [flask구현부](https://github.com/pallets-eco/flask-sqlalchemy/blob/main/src/flask_sqlalchemy/pagination.py)

  - **총 5개 필드와 1개의 메서드가 필수다**

- **일단 `infra> commons` 에 base.py와 더불어 `pagination.py`을 추가해본다**

```python
from __future__ import annotations

import math
import typing

from sqlalchemy import select, func

from src.config import db_config
from src.infra.config.connection import DBConnectionHandler


class Pagination:
    # https://parksrazor.tistory.com/457
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.page = page
        self.total = total

        # 이전 페이지를 가지고 있으려면, 현재page - 1 = 직전페이지 계산결과가, 실존 해야하는데, 그게 1보다 크거나 같으면 된다.
        #  0 [ 1 2 page ]
        self.has_prev = page - 1 >= 1
        # 이전 페이지 존재유무에 따라서 이전페이지 넘버를 현재page -1 or None 로 만든다.
        self.prev_num = (self.has_prev and page - 1) or None

        # 다음 페이지를 가지고 있으려면, 갯수로 접근해야한다.
        # (1) offset할 직전페이지까지의 갯수: (현재page - 1)*(per_page)
        # (2) 현재페이지의 갯수: len(items) => per_page를 못채워서 더 적을 수도 있다.
        # (3) total갯수보다 현재페이지까지의 갯수가 1개라도 더 적어야, 다음페이지로 넘어간다
        self.has_next = ((page - 1) * per_page + len(items)) < total
        # 다음페이지를 갖고 있다면 + 1만 해주면된다.
        self.next_num = page + 1 if self.has_next else None

        # total pages 수는, per_page를 나눠서 math.ceil로 올리면 된다.
        # self.pages = math.ceil(total / per_page) + 1
        self.pages = math.ceil(total / per_page) if total else 0

        # https://github.com/pallets-eco/flask-sqlalchemy/blob/main/src/flask_sqlalchemy/pagination.py

    def iter_pages(self, *,
                   left_edge: int = 2,  # 1페 포함 보여질 갯수,
                   left_current: int = 2,  # 현재로부터 왼쪽에 보여질 갯수,
                   right_current: int = 4,  # 현재로부터 오른쪽에 보여질 갯수,
                   right_edge: int = 2,  # 마지막페이지 포함 보여질 갯수
                   ) -> typing.Iterator[int | None]:

        # 1) 전체 페이지갯수를 바탕으로 end특이점을 구해놓는다.
        pages_end = self.pages + 1
        # 2) end특이점 vs1페부터보여질 갯수+1을 비교해, 1페부터 끝까지의 특이점을 구해놓는다.
        left_end = min(left_edge + 1, pages_end)
        # 3) 1페부터 특이점까지를 1개씩 yield로 방출한다.
        yield from range(1, left_end)
        # 4) 만약 페이지끝 특이점과 1페끝 특이점이 같으면 방출을 마친다.
        if left_end == pages_end:
            return
        # 5) 선택한 page(7) - 왼쪽에 표시할 갯수(2) (보정x 현재로부터 윈도우만큼 떨어진 밖.== 현재 제외 윈도우 시작점) -> 5 [6 7]
        #    과 left끝특이점 중 max()를 mid시작으로 본다.
        #   + 선택한page(7) + 오른쪽표시갯수(4) == 11 == 현재포함윈도우밖 == 현재제외 윈도우의 끝점 vs 전체페이지끝특이점중 min을 mid_end로 보낟
        mid_start = max(left_end, self.page - left_current)
        mid_end = min(pages_end, self.page + right_current)
        # 6) mid 시작과 left끝특이점 비교하여 mid가 더 크면, 중간에 None을 개설한다
        if mid_start - left_end > 0:
            yield None
        # 7) mid의 시작~끝까지를 방출한다.
        yield from range(mid_start, mid_end)
        # 8) mid_end와  (페이지끝특이점 - 우측에서 보여질 갯수)를 비교하여 더 큰 것을 right 시작점으로 본다.
        right_start = max(mid_end, pages_end - right_edge)
        # 9) mid_end(특이점)과 right시작점이 차이가 나면 중간에  None을 개설한다.
        if right_start - mid_end > 0:
            yield None
        # 10) right_start부터, page_end까지 방출한다.
        yield from range(right_start, pages_end)





def paginate(stmt, page=1, per_page=db_config.COMMENTS_PER_PAGE):
    if page <= 0:
        raise AttributeError('page needs to be >= 1')
    if per_page <= 0:
        raise AttributeError('per_page needs to be >= 1')

    with DBConnectionHandler() as db:
        # 이미 select된 stmt의 column에 func.count(.id)만 추가할 수 없으니
        # => select된 것을 subquery로 보고 select_from에 넣어서 count를 센다
        total = db.session.scalar(
            select(func.count('*'))
            .select_from(stmt.subquery())
        )

        items = db.session.scalars(
            stmt.limit(per_page)
            .offset((page - 1) * per_page)
        ).all()

    return Pagination(items, total, page, per_page)

```



- admin_route.py의 category라우트에서 **id역순 전체 Category조회를 paginate메서드로 Pagination객체를 만든 뒤 `.items`와 `.iter_pages()`를 사용해서 출력해본다**

  ```python
  @admin_bp.route('/category')
  @login_required
  def category():
      # 직접 추출대신 pagination으로 처리하기
      stmt = select(Category).order_by(Category.id.desc())
      pagination = paginate(stmt, 1, per_page=10)
  
      category_list = pagination.items
      print(category_list)
      print([x for x in pagination.iter_pages()])
  
      return render_template('admin/category.html', category_list=category_list)
  ```

  ![image-20221114165025985](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114165025985.png)



- per_page= 1 로 바꾸면, 1페이지의 1개 아이템만 반환되며, 총 3page가 나와야한다.

  ![image-20221114165135722](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114165135722.png)





- **entity객체list는 route에서 따로 뽑아서 + pagination객체를 같이 넘겨준다.**
  
- 그냥 pagination객체를 넘겨서 jinja 반복문에 category_list대신 pagination.items를 돌려도 될 것 같은데..
  
- **paginate()메서드의 page= 인자가 요청에 따라 바뀔 것이다.**

  - page=변수로 추출하며
  - querystring으로 **request.args.get('page')를 받아서 넣어주되 `최초 접속은 1페이지를 기본값으로` 입력되도록 만든다.**
    - 기본값이 있는 page변수를 통해 클릭안해도 1페이지, 클릭하면 n페이지가 되게 해준다.

  

```python
@admin_bp.route('/category')
@login_required
def category():
    # querystring의 page에서 page값 받고, int변환하되, 기본값 1
    page = request.args.get('page', 1, type=int)

    # 직접 추출대신 pagination으로 처리하기 (id역순으로 전체조회)
    stmt = select(Category).order_by(Category.id.desc())
    # pagination = paginate(stmt, 1, per_page=1)
    pagination = paginate(stmt, page=page, per_page=10)

    category_list = pagination.items

    return render_template('admin/category.html',
                           category_list=category_list, pagination=pagination)

```



- pagination view를 완성하기 전에 `url에 querystring`을 주고 per_page를 2페이지까지 나올 수 있게 만들어서 확인한다.

  ![image-20221114165940733](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114165940733.png)

- view적용후 per_page를 2개로 유지하다가, 나중에 바꿔준다.





##### 10_category_change_after_pagination객체넘기기.html

- if .has_prev가 있으면 **a.pagination-previous태그로 prev버튼을** querystring에 현재페이지?page= `.prev_num`을 걸어서 만든다.
- if .has_next가 있으면 **a.pagination-next태그로 next버튼을** querystring에 현재페이지?page= `.next_num`을 걸어서 만든다.
- **ul.pagination-list태그** 안에
  - `.iter_pages()`를 for `page`로 순회하면서
    - if 해당 `page`가 존재
      - if `page`가 `pagination.page`아니면
        - **li>a.pagination-link태그**로 다른page를 querystring에 **href에 걸어** page를 찍는다.
      - else 현재페이지면
        - **li>a.pagination-link태그**로 **href없이** page를 찍는다.
    - else 해당 `page`가 **None으로 생략**된 상태라면
      - **span.pagination-ellipsis태그**로 ...을 찍는다.

```html
<!-- route) 에서 category_list 던지기가 끝나면, [pagination]객체도 던져줘야한다-->
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.category') }}?page={{pagination.prev_num}}" class="pagination-previous"
       title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('admin.category') }}?page={{pagination.next_num}}" class="pagination-next">Next</a>
    {% endif %}

    <ul class="pagination-list">
        {% for page in pagination.iter_pages() %}
        {% if page %}
        {% if page != pagination.page %}
        <li>
            <a href="{{ url_for('admin.category') }}?page={{ page }}" class="pagination-link" aria-label="Page 1"
               aria-current="page">{{page}}</a>
        </li>
        {% else %}
        <li>
            <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">{{page}}</a>
        </li>
        {% endif %}
        {% else %}
        <span class=pagination-ellipsis>&hellip;</span>
        {% endif %}
        {% endfor %}

    </ul>
</nav>
```

![image-20221114171210923](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114171210923.png)

![image-20221114171219610](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114171219610.png)

- 데이터 추가하고 per_page=1로 주면, `iter_pages()`결과 나오는 `None`이 `...`으로 찍힌다.

  ![image-20221114174343164](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114174343164.png)



##### front - admin/index.html에서 a href걸어주기

```html
<p class="menu-label">
    Category
</p>
<ul class="menu-list">
    <!-- 각 entity별 select route/tempalte완성시 마다 걸어주기 -->
    <li><a href="{{ url_for('admin.category') }}">Category 관리</a></li>
</ul>
```





#### 7 category entity create

##### category_add route

```python
@admin_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
def category_add():
    
    return render_template('admin/category_form.html')
```



##### front 11_category_form_extends_cateogry_after_category_add_route.html

```html
{% extends 'admin/category.html' %}

<!-- category select화면에서의 select버튼 제거 -->
{% block button %}{% endblock button %}


{% block table_content %}
    <form action="" method="post" class="mt-4">
<!--        xx form.csrf_token xx-->
        <!-- form 필드별 변수명 확인 -->
        <div class="field">
<!--            xx form.name.label(class='label') xx-->
            <label for="name" class="label">카테고리 이름</label>
            <div class="control">
                <input id="name" maxlength="128" name="name" placeholder="Name" required="required" type="text" value="" class="input">
<!--                xx form.name(class='input', placeholder='Name') xx-->
            </div>
        </div>
        <div class="field">
<!--            xx form.icon.label(class='label') xx-->
            <label for="name" class="label">icon</label>
            <div class="control">
                <input id="icon" maxlength="128" name="icon" placeholder="Icon" type="text" value="" class="input">
<!--                xx form.icon(class='input', placeholder='Icon') xx-->
            </div>
        </div>
        <div class="is-block">
            <div class="box has-background-light is-shadowless level">
                <!--  현재페이지를 새로고침함으로써, 입력들을 다 지운다. -->
                <a href="" class=" is-danger button level-left">다시 입력</a>
                <div class="level-right">
					<!-- add클릭전 select화면 href걸기 -->
                    <a href="" class="button is-primary is-light mr-2">뒤로가기</a>
                    <input type="submit" value="생성" class=" button is-success">
                </div>
            </div>
        </div>

    </form>
{% endblock table_content %}
```

![image-20221114221517666](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114221517666.png)



##### CategoryForm for entity create view(GET)는 생성 화면-> form부터 개발

- main/forms/admin/forms.py에 Category 생성을 위한 Form 만들기

![image-20221114210650494](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114210650494.png)



- Category Entity 중에 id필드르 제외하고 입력하도록 form을 만들어야한다.

  - **nullable=True인 필드는 form에서 DataRequired가 빠진다.**

  ![image-20221114210743004](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114210743004.png)

```python
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class CategoryForm(FlaskForm):

    name = StringField('카테고리 이름', validators=[
        DataRequired(message='필수 입력'),
        Length(max=128, message='최대 128 글자까지 입력 가능')
    ])
    icon = StringField('icon', validators=[
        Length(max=128, message='최대 128 글자까지 입력 가능')
    ])
```

- init에 등록

- **아직 validate_field method 정의 안해줬다.**

  - id or unique 필드의 존재유무 확인

  

##### create를 위한 category_add(/category/add) route

- 아직 form에 예외처리가 안되서  -> **route에서 에러들 담아서 뿌려주기 아직 적용 안됬다.**



```python
@admin_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
def category_add():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, icon=form.icon.data)
        with DBConnectionHandler() as db:
            db.session.add(category)
            db.session.commit()
        flash(f'{form.name.data} Category 생성 성공!')
        return redirect(url_for('admin.category'))

    return render_template('admin/category_form.html', form=form)
```



##### my) form validate method 추가 /route erros넘겨주기/ 부모html에서  flash message 아래에 form의 erros message 코드 추가

1. 생성존재유무를 name으로 하려면 **name이 id를 대체하는 unique여야한다.**

   ```python
   name = Column(String(128), nullable=False, unique=True)
   ```

2. form name이 exists시 에러내는 validate_name method를 작성한다

   - login - regiserform을 참고

   ```python
       def validate_name(form, field):
           with DBConnectionHandler() as db:
               exists_cate = db.session.scalars(
                   exists().where(Category.name == field.data).select()
               ).one()
   
           if exists_cate:
               raise ValidationError('이미 존재하는 Category입니다')
   ```

3. .rotue에 form에 있는 모든 필드에 대한 errors추출하여 넘겨주기

   ```python
   errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
       
       return render_template('admin/category_form.html', form=form, errors=errors)
   ```

4. 부모인 category.html의 **flash message자리 아래에  error출력 코드** 추가

   ```python
       <!-- form validation errors -->
       {% for field in errors %}
       <b-message type="is-danger">
           <ul class="errors">
               {% for message in field.messages %}
               <li> {{ message }}</li>
               {% endfor %}
           </ul>
       </b-message>
       {% endfor %}
   ```





![image-20221114223041145](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114223041145.png)





##### front 12_category_form_change_after_category.form.html

- 여기서는 고정된input을 아래 코드로 대체한다
- **{{ `form.name`(class='input') }}이 `input태그`였다면 **
  - **{{ `form.name.label`(class='label') }}은 `label태그`이며, login/register화면에선 안넣어줫었음. **



- div.field태그 아래
  - label태그 by form
  - div.control
    - input태그 by form

```html
{% extends 'admin/category.html' %}

<!-- category select화면에서의 select버튼 제거 -->
{% block button %}{% endblock button %}


{% block table_content %}
    <form action="" method="post" class="mt-4">
        {{ form.csrf_token }}
        <!-- form 필드별 변수명 확인 -->
        <div class="field">
            {{ form.name.label(class='label') }}
            <div class="control">
                {{ form.name(class='input', placeholder='Name') }}
            </div>
        </div>
        <div class="field">
            {{ form.icon.label(class='label') }}
            <div class="control">
                {{ form.icon(class='input', placeholder='Icon') }}
            </div>
        </div>
        <div class="is-block">
            <div class="box has-background-light is-shadowless level">
                <a href="" class=" is-danger button level-left">다시 입력</a>
                <div class="level-right">
                    <a href="{{ url_for('admin.category') }}" class="button is-primary is-light mr-2">뒤로가기</a>
                    <input type="submit" value="생성" class=" button is-success">
                </div>
            </div>
        </div>

    </form>
{% endblock table_content %}
```

![image-20221114223612982](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114223612982.png)





####  8 category entity update

- 수정 역시 form을 통해 한다.
  - 생성form이나 수정form이나 양식은 동일하므로 재활용한다.



##### category_edit route (table or detail에서 url속id를 받아, 객체찾아 데이터를 채운form을 화면으로)

- select는 추가url + id인자가 아예 없고
- add는 추가url만 있고 id는 내부에서 발행하고
- **edit, delete는 추가url + id가 인자로 들어온다.**
  - **`select view클릭 -> url을 통한 id`를 받아서 **
    - **`GET 화면`**
      1. **찾은 객체의 `데이터를 바탕으로 form`을 채워서 만들고 화면에 뿌려준다**
      2. **form이 post로 오면 수정하고 관리하면으로 보내준다.**
- **category_form.html은 `생성/수정시 재활용`된다.**

```python
@admin_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def category_edit(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    with DBConnectionHandler() as db:
        category = db.session.get(Category, id)

    # 2) 찾은 객체의 데이터를 바탕으로 form을 만들어서 GET 화면에 뿌려준다.
    form = CategoryForm(name=category.name, icon=category.icon)
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
    # return render_template('admin/category_form.html', form=form, errors=errors)

    # 3) form에서 달라진 데이터로 POST가 들어오면, 수정하고 커밋한다.
    if form.validate_on_submit():
        category.name = form.name.data
        category.icon = form.icon.data
        with DBConnectionHandler() as db:
            db.session.add(category)
            db.session.commit()
        flash(f'{form.name.data} Cateogry 수정 완료.')
        return redirect(url_for('admin.category'))
	
    # 4) 검증이 들어간 form에 대한 erros는 if form.validate_on_submit()보다 아래에 둔다.
    errors = [{'field': key, 'messages': for.errors[key]} for key in form.errors.keys()] if form.errors else []]
    
    return render_template('admin/category_form.html', form=form, errors=errors)
```





##### front - 13_category_change_after_category_edit_route.html

- 각 table데이터의 수정a태그에 `category/edit/id`인 `admin.category, url인자=id`로   url_for를 건다



```html
            <td>
                <div class="tags">
                    <a href="{{url_for('admin.category_edit', id=cate.id) }}" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
                    <!--                    <a href="xx url_for('admin.category_del', cate_id=cate.id) xx" class="tag is-danger is-light">-->
                    <a href="" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
                </div>
            </td>
```

![image-20221114234328257](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114234328257.png)
![image-20221114234336531](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114234336531.png)

![image-20221114234411223](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221114234411223.png)

##### 생성form 재활용시 validate문제 생성자 오버라이딩으로 해결하기

- **문제점: 생성form에서 `name 존재유무 검사` -> `수정시에도 적용되어 내name이 존재검사에 걸림`**
  - **생성form**에서는 **db전체에서 존재검사**
  - **수정form**이라는 신호가 있으면, **내 field값을 제외한 db전체에서 존재검사**
- **form의 생성자를 오버라이딩해서 `id=` keyword를 받았다면 `객체 찾아서 form채워서 활용하는 edit form`으로 인식하기** 
  - [form 생성자 오버라이딩으로 추가keyword받기](https://stackoverflow.com/questions/63580110/how-to-reuse-a-wtform-for-updating-and-adding-records-in-the-database)
  - [참고- 생성자오버라이딩으로 필드를 추가하여 choices필드를 다른entity에서 목록 받아오기](https://wikidocs.net/106745)



1. 주석내용을 확인. form 수정

   ```python
   class CategoryForm(FlaskForm):
       name = StringField('카테고리 이름', validators=[
           DataRequired(message='필수 입력'),
           Length(max=128, message='최대 128 글자까지 입력 가능')
       ])
       icon = StringField('icon', validators=[
           Length(max=128, message='최대 128 글자까지 입력 가능')
       ])
   
       # 1) 생성자를 오버라이딩하여, (form필드 추가도 가능) edit에서 사용되는지 여부 -> id= keyword로 받기
       # => editform으로서 id=가 객체.id로 들어온다면, self.id에 보관하기
       def __init__(self, id=None, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.id = id
   
       def validate_name(self, field):
           # 2) id가 들어오면 edit form으로 인식해서, db 존재검사를 [나를 제외한 db 존재 검사]
           if self.id:
               condition = and_(Category.id != self.id, Category.name == field.data)
           # 3) is_edit가 아닐 때는, 기존 생성form으로서 [db전체 존재유무 검사]
           else:
               condition = Category.name == field.data
   
           with DBConnectionHandler() as db:
               exists_cate = db.session.scalars(
                   exists().where(condition).select()
               ).one()
   
           if exists_cate:
               raise ValidationError('이미 존재하는 Category name입니다')
   ```



2. **edit route에선 `클릭 -> url속 id -> 객체찾기 -> 객체데이터로 form채워서 만들기`의 과정에서 `id=까지 추가로 입력된다면 editform`으로 인식하게 하기**

   ```python
   @admin_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
   @login_required
   def category_edit(id):
       # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
       with DBConnectionHandler() as db:
           category = db.session.get(Category, id)
   
       # 2) 찾은 객체의 데이터를 바탕으로 form을 만들어서 GET 화면에 뿌려준다.
       # => 이 때, form에 id= 키워드를 주면, edit용 form으로 인식해서 validate를 나를 제외하고 하도록 한다
       form = CategoryForm(name=category.name, icon=category.icon, id=category.id)
       # return render_template('admin/category_form.html', form=form, errors=errors)
   
       # 3) form에서 달라진 데이터로 POST가 들어오면, 수정하고 커밋한다.
       if form.validate_on_submit():
           category.name = form.name.data
           category.icon = form.icon.data
           with DBConnectionHandler() as db:
               db.session.add(category)
               db.session.commit()
           flash(f'{form.name.data} Category 수정 완료.')
           return redirect(url_for('admin.category'))
   
       # 4) 검증이 들어간 form에 대한 erros는 if form.validate_on_submit()보다 아래에 둔다.
       errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []
   
       return render_template('admin/category_form.html', form=form, errors=errors)
   
   ```



##### form 생성시 객체로 넘겨서 판단하도록 변경하기

```python
@admin_bp.route('/category/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def category_edit(id):
    with DBConnectionHandler() as db:
        category = db.session.get(Category, id)

    # form = CategoryForm(name=category.name, icon=category.icon, id=category.id)
    form = CategoryForm(category)
```

```python
class CategoryForm(FlaskForm):
    name = StringField('카테고리 이름', validators=[
        DataRequired(message='필수 입력'),
        Length(max=128, message='최대 128 글자까지 입력 가능')
    ])
    icon = StringField('icon', validators=[
        Length(max=128, message='최대 128 글자까지 입력 가능')
    ])

    # 1) 생성자를 오버라이딩하여, (form필드 추가도 가능) edit에서 사용되는지 여부 -> id= keyword로 객체로 받기
    # => editform으로서 category=가 객체.id로 들어온다면, self.id필드에 보관하기
    # 2차)
    def __init__(self, category=None, *args, **kwargs):
        if category:
            # 2-1) 객체가 넘어와서, 가 필드들을 dict로 만들어, **로 keyword인자로 ㅁ나들어서 넘겨준다
            # => 이 때, category.id를 self.id에 주입못한다. self.id는 FormField가 아니라서 자동으로 안채워진다.
            super().__init__(**category.__dict__)
        else:
            # 2-2) init 재정의를 한다면, 반드시 부모 것을 초기화해줘야 기본사용 가능하다.
            super().__init__(*args, **kwargs)

        # 2-3) 밸리데이션 검사를 위해, 없을 때도 필드가 존재해야 validate 메서드에서 검사한다.
        #    + form필드를 개설하는게 아니므로, super().__init__(**category.__dict__)시 자동으로 self.id에는 안채워져서 직접 넣어줘야한다.
        self.id = category.id if category else None
```



##### 객체로 받아서 where조건에만 .id로  걸어주기로 변경

```python
    def __init__(self, category=None, *args, **kwargs):
        self.category = category

        if self.category:
            super().__init__(**self.category.__dict__)
        else:
            super().__init__(*args, **kwargs)


    def validate_name(self, field):

        if self.category:
            ## filter조건으로 Category != self.category로 비교하면 조건으로 안들어간다. sqlalchemy의 where에는
            ## 객체비교가 아닌 필드로 명시해줘야한다.
            condition = and_(Category.id != self.category.id, Category.name == field.data)
```



##### default None인 필드에 대해 view갔다오면 ''을 가지고 오므로 route에서  None으로 다시 변환하여 저장

- 안하면 DB:None -> view '' -> route '' -> DB: '' 로 저장됨

  ```python
  if form.validate_on_submit():
      category.name = form.name.data
      category.icon = form.icon.data if len(form.icon.data) > 0 else None # 수정form화면에서 암것도 없으면 ''이 올 것이기 때무네
  ```

  



- 결과

  - 자신의 name은 이미 존재해도, 검사에 안걸려서 수정이 가능하다.

    ![image-20221115011632492](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115011632492.png)

    ![image-20221115011651730](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115011651730.png)

  - 자신의 name을 제외한, 기존에 db에 존재하는 분류이름은 에러가 뜬다.

    ![image-20221115011721673](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115011721673.png)

    ![image-20221115011742117](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115011742117.png)

    





#### 9 category entity delete

##### category_delete route

- **delete는 select -> id를 받아 -> 객체 조회 -> 존재검사후 삭제하면 되며**

  - **따로 form을 이용한 데이터 받기가 `POST method`가 필요없다**
  - **객체 존재시 삭제후 select로 redirect를 해준다**

  

  ```python
  @admin_bp.route('/category/delete/<int:id>')
  @login_required
  def category_delete(id):
      # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
      with DBConnectionHandler() as db:
          category = db.session.get(Category, id)
  
      if category:
      	db.session.delete(category)
          db.session.commit()
          flash(f'{category.name} Category 삭제 완료.')
          return redirect(url_for('admin.category'))
  
  ```

  

##### front - 14_category_change_after_category_delete_route.html

- 작업 - 삭제 a href를 해당 라우터 admin.category_delete로 걸어준다.



```html
            <td>
                <div class="tags">
                    <a href="{{url_for('admin.category_edit', id=cate.id) }}" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
                    <a href="{{url_for('admin.category_delete', id=cate.id) }}" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
                </div>
            </td>
```

![image-20221115142553343](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115142553343.png)



#### 10 entity 끝날때마다 admin/index.html의 메뉴 a태그에 route 및 is-active class걸어주기

- active여부를 class로 걸어주는데 **`request.path`에**
  - view가 1개 밖에 없는 admin.index는 `== '/admin/'`으로
  - view가 여러개 있는 entity관련 메뉴는 `'entity명' in `로 확인해준다.
    - select  : `/admin/category`
    - create : `/admin/category/add`
    - update : `/admin/category/edit`
    - delete: 화면 없음.
  - request.path는 port번호 이후로 `/` or `/prefix/` 형태로 **/시작 /끝으로 출력되는 것 같다**
    - querystring은 안찍힌다.
    - `<int:id>`류의 인자는 찍힌다

##### front - 15_index_change_after_category_crud.html

```html
<ul class="menu-list">
    <!-- 각 entity별 select route/tempalte완성시 마다 걸어주기 -->
    <li><a class="{% if 'category' in request.path %}is-active{% endif %}"
           href="{{ url_for('admin.category') }}">Category 관리</a></li>
</ul>
```

![image-20221115143932500](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115143932500.png)

![image-20221115143947603](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115143947603.png)

![image-20221115144032217](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115144032217.png)







### Article(Post, Many, MantToMany)

- category를 많이 참고해서 만든다.



#### 11 article(post)  select

##### article route

- /category를 복사해와서 수정한다

- entity crud관련은 모두 `admin_route.py`에 정의한다

- **select는 pagination으로 조회한다**
  - querystring page= default 1처리
  - entity pagatinate로 가져오기
  - .items로 entity_list 따로  / pagination객체 따로 render

```python
@admin_bp.route('/article')
@login_required
def article():
    page = request.args.get('page', 1, type=int)

    stmt = select(Post).order_by(Post.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    return render_template('admin/article.html',
                           post_list=post_list, pagination=pagination)

```



##### admin / article.html 생성

![image-20221116023554291](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221116023554291.png)

- category.html 최초코드를 복사해서 post.필드로 바꿔준다

  - **enum필드는 `.name`까지 붙여서 td에 표기한다**

    ![image-20221116024751971](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221116024751971.png)

  - **`일대다에서 부모인 일에서 정의한 relationship칼럼` 속 `.의backref`로 td에 표기한다**

    ![image-20221116024822663](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221116024822663.png)

  - **`다대다에서 내가 relationship칼럼을 가진 상태(일의상태)로`의 `.관계칼럼명`을 td에 표기한다.**

    - **자식들을 다 가지고 오는 일의 입장이라면 lazy='subquery'로 정의되어있어서 `.관계칼럼명(=다 table)`으로 `자식 객체들`을 다가져올 수 있다**
    - 이 때, **td에서는 ` | join(',')`의 jinja filter를 써서 여러 자식들을 묶어준다.**

    ![image-20221116024841991](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221116024841991.png)



##### front -  16_article_after_admin.article_route.html

```html
{% extends 'admin/index.html' %}

{% block member %}
<!-- 위쪽 제목 공간 -->
<div class="is-block">
    <!-- left 제목 -->
    <div class="is-pulled-left">
        <h1 class="is-size-4">
            <span class="icon"><i class="mdi mdi-receipt-outline"></i></span>
            Article 관리
        </h1>
    </div>
    <!-- right 버튼(상속할 form에선 달라짐) -> block개설 -->
    {% block button %}
    <div class="is-pulled-right">
        <!--  route) category_add route 및 article_form.html 개발 후 href채우기  -->
        <a href="" class="button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>Post 추가</span>
        </a>
    </div>
    {% endblock button %}
    <!--  분류선 by div2개: pulled-쓰과서 is-clearfix는 필수  -->
    <div class="is-clearfix"></div>
    <div class="dropdown-divider"></div>

    <!-- 아래쪽 table의 처리에 대한 flash 메세지를 위쪽에서   -->
    {% with messages = get_flashed_messages() %}
    <b-message type="is-success">
        {% if messages %}
        <ul class=flashes>
            {% for message in messages %}
            <li>{{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </b-message>
    {% endwith %}
	
	<!-- my) form validation errors -->
    {% for field in errors %}
    <b-message type="is-danger">
        <ul class="errors">
            {% for message in field.messages %}
            <li> {{ message }}</li>
            {% endfor %}
        </ul>
    </b-message>
    {% endfor %}
</div>

<!-- 위쪽 아래쪽 table or form 공간 -->
{% block table_content %}
<div class="table-container">
    <table class="table is-fullwidth is-hoverable is-striped">
        <thead>
        <tr>
            <th>Id</th>
            <th>Title</th>
            <th>Status</th>
            <th>Category</th>
            <th>Tag</th>
            <th>생성일</th>
            <th>작업</th>
        </tr>
        </thead>
        <tbody>
        <!--  route) 에서 post객체들을 id역순으로 넘겨주면, for문이 돌아가면서 a태그 에러가 걸리게 됨.  -->
        <!--  a태그-href들 주석처리된 상태  -->
        {% for post in post_list %}
        <tr>
            <td>{{ post.id }}</td>
            <td>{{ post.title }}</td>
            <!-- enum이라 .name -->
            <td>{{ post.has_type.name }}</td>
            <!-- 다대일으로 부모domain객체(lazy='subquery')의 name만 -->
            <td>{{ post.category.name }}</td>
            <!-- 다대다라 join으로 붙인다. -->
            <td>{{ post.tags | join(',') }}</td>
            <td>{{ post.add_date }}</td>
            <td>
                <div class="tags">
<!--                    <a href="xx url_for('admin.article_edit', id=post.id) xx" class="tag is-success is-light">-->
                    <a href="" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
<!--                    <a href="xx url_for('admin.article_del', id=cate.id) xx" class="tag is-danger is-light">-->
                    <a href="" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
                </div>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
<!-- route) 에서 category_list외에 [pagination]객체도 던져줘야한다-->
<nav class="pagination is-small" role="navigation" aria-label="pagination">
<!--xx if pagination.has_prev xx-->
<!--    <a href="xx url_for('admin.category') xx?page=xx pagination.prev_num xx" class="pagination-previous" title="This is the first page">Previous</a>-->
<a href="" class="pagination-previous" title="This is the first page">Previous</a>
<!--xx endif xx-->
<!--xx if pagination.has_next xx-->
<!--    <a href="xx url_for('admin.category') xx?page=xx pagination.next_num xx" class="pagination-next">Next page</a>-->
<a href="" class="pagination-next">Next page</a>
<!--xx endif xx-->

<ul class="pagination-list">
<!--    xx for page in pagination.iter_pages() xx-->
<!--        xx if page xx-->
<!--            xx if page != pagination.page xx-->
            <li>
<!--                <a href="xx url_for('admin.category') xx?page=xx page xx" class="pagination-link" aria-label="Page 1" aria-current="page">xx page xx</a>-->
                <a href="" class="pagination-link" aria-label="Page 1" aria-current="page">1</a>
            </li>
<!--            xx else xx-->
            <li>
<!--                <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">xx page xx</a>-->
                <a class="pagination-link is-current" aria-label="Page 1" aria-current="page"> 1 </a>
            </li>
<!--            xx endif xx-->
<!--        xx else xx-->
            <span class=pagination-ellipsis>&hellip;</span>
<!--        xx endif xx-->
<!--    xx endfor xx-->

</ul>
</nav>

{% endblock table_content %}


{% endblock member %}
```

![image-20221116025733260](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221116025733260.png)





#### 12 article create

##### PostForm (생성부터는 route보다 form부터)

- post model칼럼에 따라 다른 form field를 생성한다.

  - String 칼럼 -> StringField지만, 

  - **Text(content)칼럼 -> `TextAreaField`로 만든다.**

  - **`Enum칼럼 + server_default='기본enum의 value직접입력'`**한 것은

    - **`RadioField`로 만들고 **
    - **`choices=`에는 `각 Enum들.필드.name`**을 넣어준다. `.name`은 enum속 필드명들이 나오나보다.
    - **`default=`에는 칼럼에서 server_default=로 넣어준 enum의 실제value에 대한 필드명인 `enum.default필드.name`을 넣어준다.**

  - **`Integer, FK칼럼(부모 값 1개)`에 대해서는**

    - `SelectField`를 만들어, **존재하는 상위domain을 선택**하도록 할 것이다.

    - **일단 `choices=None`으로 비워두고, `form이 생성될 당시에 존재하는 상위도메인객체을 조회하여, id와 표기될값을 tuple로 넣어줄 것이다.`**

      - 원래 choices는 `(저장될값,  표시될 값)`의 tuple list를 인자로 받는다.

        ```python
        SelectField(
            choices=[(True, 'Yes'), (False, 'No')],
            validators=[InputRequired()],
            coerce=lambda x: x == 'True'
        )
        ```

    - **coerce= int**를 통해, html에서 선택된 값(fk_상위도메인id)를 int로 형변환할 것이다.

  - **`relationship칼럼 이자 다대다 칼럼`에 대해서는**

    - **`SelectMultipleField`를 만들어, `존재하는 다대다domian을 여러개 선택`할 것이다.**
    - **역시 생성당시 상대테이블로부터 객체를 얻어와야하므로 `choices=None`으로 초기화만 해둔다.**
    - **역시 타테이블 관련은 coerce=int로 만들어 id로 연결되게 한다**

  ```python
  class PostForm(FlaskForm):
      title = StringField('제목', validators=[
          DataRequired(message="필수 입력"),
          Length(max=128, message="최대 128 글자까지 입력 가능")
      ])
      desc = StringField('설명', validators=[
          DataRequired(message="필수 입력"),
          Length(max=200, message="최대 128 글자까지 입력 가능")
      ])
      content = TextAreaField('내용', validators=[
          DataRequired(message="필수 입력")
      ])
      has_type = RadioField('Post status',
                            choices=(PostPublishType.draft.name, PostPublishType.show.name),
                            default=PostPublishType.show.name)
      category_id = SelectField(
          '카테고리',
          choices=None,
          coerce=int,
          validators=[
              DataRequired(message="필수 입력"),
          ]
      )
      tags = SelectMultipleField('태그', choices=None, coerce=int)
  ```

  

- **이제 생성자를  재정의해서, form객체 생성시, 관계칼럼들의 choices들을 채워준다.**

  - **수정시 생성form을 재활용하여 해당id의 객체를 넣어서 만들 수 있게 할 예정이기 때문에 `해당객체=None`을 인자로 미리 받아준다.**

  ```python
  # 1) 수정시 생성form을 재활용하여 해당id의 객체를 넣어서 만들 수 있게 할 예정이기 때문에 `해당객체=None`을 인자로 미리 받아준다.
  def __init__(self, post=None, *args, **kwargs):
      super().__init__(*args, **kwargs)
      # 2) fk 부모domain/다대다 domain 을 가져와 -> tuple(id, name)으로 변경한 tuplelist를 choices에 넣어서 선택할 수 있게 한다.
      with DBConnectionHandler() as db:
          categories = db.session.scalars(select(Category)).all()
          tags = db.session.scalars(select(Tag)).all()
      self.category_id.choices = [(category.id, categories.name) for category in categories]
      self.tags.choices = [(tag.id, tag.name) for tag in tags]
  
  ```

  

  

##### article_add route 생성

- category_add route를 복사해서 만들어준다.

```python
@admin_bp.route('/article/add', methods=['GET', 'POST'])
@login_required
def article_add():
    form = PostForm()
    if form.validate_on_submit():
        pass
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html', form=form, errors=errors)
```



##### admin / artcle_form.html 생성

- category_form.html이 category.html을 상속해서 쓰듯이 **admin/article.html을 상속해서 쓴다.**

![image-20221118215909887](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221118215909887.png)



##### front- 17_article_form_extends_article_after_article_add_route_생성.html

```html
{% extends 'admin/article.html' %}

<!-- select 화면에서 우측상단 버튼들(add) 제거-->
{% block button %}{% endblock button %}


{% block table_content %}
<form action="" method="post" class="mt-4">
<!--    xx form.csrf_token xx-->
    <div class="field">
<!--        xx form.title.label(class='label') xx-->
        <label for="title" class="label">제목</label>
        <div class="control">
<!--            xx form.title(class='input', placeholder='Title') xx-->
        <input id="title" maxlength="128" name="title" placeholder="Title" required="required" type="text" value="" class="input">
        </div>
    </div>
    <div class="field">
<!--        xx form.desc.label(class='label') xx-->
        <label for="desc" class="label">설명</label>
        <div class="control">
<!--            xx form.desc(class='input', placeholder='Description') xx-->
            <input id="desc" maxlength="200" name="desc" placeholder="Description" required="required" type="text" value="" class="input">
        </div>
    </div>

    <div class="field">
<!--        xx form.category_id.label(class='label') xx-->
        <label for="category_id" class="label">카테고리</label>
        <div class="control">
            <div class="select is-fullwidth">
<!--                xx form.category_id xx-->
                <select id="category_id" name="category_id" required="required">
                    <option value="2">분류2</option>
                    <option value="3">분류3</option>
                    <option value="4">분류4</option>
                </select>
            </div>
        </div>
    </div>

    <div class="field">
<!--        xx form.content.label(class='label') xx-->
        <label for="content" class="label">내용</label>
        <div class="control">
<!--            xx form.content(class='textarea', rows="10", placeholder='Contents') xx-->
            <textarea id="content" name="content" placeholder="Contents" required="required" rows="10" class="textarea"></textarea>
        </div>
    </div>

    <div class="field">
<!--        xx form.tags.label(class='label') xx-->
        <label for="tags" class="label">태그</label>
        <div class="control">
            <div class="select is-fullwidth is-multiple">
<!--                xx form.tags(size='5') xx-->
                <select multiple="multiple" id="tags" name="tags" size="5">
                    <option value="1">태그1</option>
                    <option value="2">태그2</option>
                    <option value="3">태그3</option>
                </select>
            </div>
        </div>
    </div>

    <!-- label+input을 한번에 올리려면 div.field 이외에 .is-horizontal을 class로 넣어줘야한다.   -->
    <div class="field is-horizontal">
<!--        xx form.has_type.label(class='label') xx-->
        <label for="has_type" class="label">Post status</label>
        <div class="field-body ml-4">
            <div class="control">
                <!--  radio타입은 전체label외에 개별 input마다 label을 또 챙기며, label태그안에 input태그를 넣는다.-->
                <label class="radio">
                    <input type="radio" name="has_type" value="draft">
                    초안
                </label>
                <label class="radio">
                    <input checked type="radio" name="has_type" value="show">
                    완성
                </label>
            </div>
        </div>
    </div>
    <div class="is-block">
        <div class="box has-background-light is-shadowless level">
            <a href="" class="is-danger button level-left">다시 입력</a>
            <div class="level-right">
<!--                <a href="xx url_for('admin.article') xx" class="button is-primary is-light mr-2">뒤로가기</a>-->
                <a href="" class="button is-primary is-light mr-2">뒤로가기</a>
                <input type="submit" value="생성" class=" button is-success">
            </div>
        </div>
    </div>

</form>
{% endblock table_content %}
```

![image-20221118215946025](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221118215946025.png)



##### article_add route 완성(form데이터 받아 객체 생성)

- pass한 form데이터가 들어왔을 때, 객체 생성하는 부분까지 완성하자.

  - **html을 jinja로 업뎃안해줘서 어떻게 넘어오는지는 모르지만, 작성하고 바로 확인도 못한다.**

  ![image-20221118223527678](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221118223527678.png)

- 중요한 점은, **다대다를 위해 select로 여러개 받았으면 -> `객체list를 생성`한 뒤 `동기화되는 relationship칼럼에 넣어주기`**를 따로 해줘야한다.

- **상위도메인 fk를 받았다면 -> `상위도메인 객체는 굳이 생성할 필요없이, fk(int)값을 그대로 넣어줘도된다.`**

  - **`하위, Many의 경우. 실제 fk(interger)칼럼을 가지고 있으므로 `굳이 상위도메인이 제공해주느 `.category`의 backref를 쓰려고 객체를 굳이 안만들어도 된다. **

    ![image-20221118223800741](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221118223800741.png)



```python
@admin_bp.route('/article/add', methods=['GET', 'POST'])
@login_required
def article_add():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            desc=form.desc.data,
            has_type=form.has_type.data,
            # 1)현재 input이 초반html로 만들 것이라, coerce=int가 아직 적용안된 상태
            category_id=int(form.category_id.data),
            content=form.content.data
        )

        with DBConnectionHandler() as db:
            # 2) 다대다에 해당하는 tags를 한꺼번에 추가해줘야한다. 개별객체, append보다는 객체 list를 만들어서, 넣어주자.
            # -> form에서 오는 data는, 숫자list가 될 것이다?
            print("form.category_id>>>" ,form.category_id, type(form.category_id))
            print("form.tags.data>>>", form.tags.data, type(form.tags.data))
            post.tags = [db.session.get(Tag, tag_id) for tag_id in form.tags.data]
            db.session.add(post)
            db.session.commit()
        flash(f'{form.title.data} Post 생성 성공!')
        return redirect(url_for('admin.article'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html',
                           form=form, errors=errors)
```



##### front- 18_article_form_change_after_article_add_route_완성(selectize).html

- form input 중에 **form textarea는 class='input' 대신` class='textarea' + rows='`'**를 준다
- **`SelectMultiField`에 해당하는 form select는 알아서 select태그 + option들을 채우는데, `size=''`만 준다**

- **radiofield는 `직접순회`하며, `checked`까지 가능하기 위해 `직접input필드`를 작성하도록 한다.**
  - 그냥 form.field를 풀면, 세로로 나열된다.



- **SelectMultiField를 예쁘게 표기하기 위해서**

  1. base.html에서부터 전해지는 `extra_head_style block`에 **selectize css 및 jquery -> selectize.js를 추가로 준다.**

     ```html
     {% extends 'admin/article.html' %}
     
     {% block extra_head_style %}
     <!-- selectize css   -->
     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/css/selectize.min.css">
     <!-- jqeury -> selectize Js (순서 중요)   -->
     <script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
     <script src="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/js/standalone/selectize.min.js"></script>
     {% endblock extra_head_style %}vvvvv
     ```

  2. base.html에서부터 전해지는 `extra_foot_script block`에 **jquery를 이용한 `select#해당field_id`를 selectize**시킨다.

     ```html
     {% block extra_foot_script %}
     <script>
         $(function () {
             // select태그를 selectize화 시켜서, tags들을 여러개 선택할 수 있게 한다.
             $('select#tags').selectize({
                 plugins: ['remove_button'],
             });
         });
     </script>
     {% endblock extra_foot_script %}
     ```

     

```html
{% extends 'admin/article.html' %}

{% block extra_head_style %}
<!-- selectize css   -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/css/selectize.min.css">
<!-- jqeury -> selectize Js (순서 중요)   -->
<script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/js/standalone/selectize.min.js"></script>
{% endblock extra_head_style %}


<!-- select 화면에서 우측상단 버튼들(add) 제거-->
{% block button %}{% endblock button %}


{% block table_content %}
<form action="" method="post" class="mt-4">
    {{ form.csrf_token }}
    <div class="field">
        {{ form.title.label(class='label') }}
        <div class="control">
            {{ form.title(class='input', placeholder='Title') }}
        </div>
    </div>
    <div class="field">
        {{ form.desc.label(class='label') }}
        <div class="control">
            {{ form.desc(class='input', placeholder='Description') }}
        </div>
    </div>

    <div class="field">
        {{ form.category_id.label(class='label') }}
        <div class="control">
            <div class="select is-fullwidth">
                {{ form.category_id }}
            </div>
        </div>
    </div>

    <div class="field">
        {{ form.content.label(class='label') }}
        <div class="control">
            <!-- form input 중에 textarea는 class='input' 대신 class='textarea' + rows=''를 준다.  -->
            {{ form.content(class='textarea', rows="10", placeholder='Contents') }}
        </div>
    </div>

    <div class="field">
        {{ form.tags.label(class='label') }}
        <div class="control">
            <div class="select is-fullwidth is-multiple">
                <!-- <select id='tags'> 태그가 완성되는데, selecize에 의해 이쁘게 나오게 한다-->
                {{ form.tags(size='5') }}
            </div>
        </div>
    </div>

    <!-- label+input을 한번에 올리려면 div.field 이외에 .is-horizontal을 class로 넣어줘야한다.   -->
    <div class="field is-horizontal">
        {{ form.has_type.label(class='label') }}
        <div class="field-body ml-4">
            <div class="control">
                <!-- 1) default 세로나열radio: default로는 새로로 나열되는 radio가 나온다.-->
                <!--xx form.has_type xx-->
                <!-- 2) 수동으로 label태그안에 input태그+데이터를 작성(기존html)-->
                <!-- 3) for.has_type을 순회 -> 수동label태그안에 subfield(input) + subfield.data를 jinja로 주면서 돌리기-->
                <!-- 4) for.has_type을 순회 -> subfield(input) + subfield.label( class없이 .label만) 돌리기 -->
                <!-- 5) edit시 checked까지 반영하려면, 직접input만들어주기 -->
                {% for subfield in form.has_type %}
                    <!-- xx subfield xx -->
                <input {%if subfield.checked %}checked {% endif %} type="radio"
                           id="{{ subfield.id }}" name="{{ form.has_type.id }}" value="{{ subfield.data }}">
                    {{ subfield.label }}
                {% endfor %}
            </div>
        </div>
    </div>
    <div class="is-block">
        <div class="box has-background-light is-shadowless level">
            <button class="is-danger button level-left">다시 입력</button>
            <div class="level-right">
                <a href="{{ url_for('admin.article') }}" class="button is-primary is-light mr-2">뒤로가기</a>
                <input type="submit" value="생성" class=" button is-success">
            </div>
        </div>
    </div>

</form>
{% endblock table_content %}


{% block extra_foot_script %}
<script>
    $(function () {
        // select태그를 selectize화 시켜서, tags들을 여러개 선택할 수 있게 한다.
        $('select#tags').selectize({
            plugins: ['remove_button'],
        });
    });
</script>
{% endblock extra_foot_script %}

```



##### flask shell로 Tag태그 데이터 실시간 만들기

1. **환경변수 설정**

```powershell
  $env:FLASK_APP = 'run.py' # set ~ =run.py

  $env:FLASK_ENV = 'development' # set ~ =de~

  flask shell
```



2. `from create_database_tutorial3 import *` 로 
   1. **model들 + **
   2. **Session[()]클래스 **
   3. **3create_database[(truncate=True, drop_table=False)] method** 

```python
from create_database_tutorial3 import *
```



3. **객체리스트를 만들고 -> session.bulk_save_objects( 객체list )**
   - select까지 import할라니 복잡해서 **session.query( Entity) .all()을 씀**

```python
from create_database_tutorial3 import *

session = Session()

tag_list = [Tag(name=f'tag_{x}') for x in range(1, 4)]
session.bulk_save_objects( tag_list )
session.commit()

session.query(Tag).all()

# [Tag[name='tag_1'], Tag[name='tag_2'], Tag[name='tag_3']]
```



4. create_database.py이 _load_fake_data 메서드에 추가

   ```python
   #### Tag
   tag_list = [Tag(name=f'tag_{x}') for x in range(1, 4)]
   session.bulk_save_objects(tag_list)
   session.commit()
   ```

   

##### add test

![image-20221119013650921](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221119013650921.png)

![image-20221119013700378](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221119013700378.png)

- **coerce=int**에 의해, 각 데이터를이 int로 들어왔다.

  ```python
  print("form.category_id.data>>>", type(form.category_id.data), form.category_id.data)
  print("form.tags.data>>>", type(form.tags.data[0]), form.tags.data[0], )
  
  form.category_id.data>>> <class 'int'> 3
  form.tags.data>>> <class 'int'> 1
  ```

  

![image-20221119021036312](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221119021036312.png)

##### front - 19_article_change_after_article_form.html

```html
    <div class="is-pulled-right">
        <!--  route) category_add route 및 article_form.html 개발 후 href채우기  -->
        <a href="{{ url_for('admin.article_add')}}" class="button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>Post 추가</span>
        </a>
    </div>
	
	
	
	
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.article') }}?page={{ pagination.prev_num }}" class="pagination-previous" title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('admin.article') }}?page={{ pagination.next_num }}" class="pagination-next">Next page</a>
    {% endif %}

<ul class="pagination-list">
    {% for page in pagination.iter_pages() %}
        {% if page %}
            {% if page != pagination.page %}
            <li>
                <a href="{{ url_for('admin.article') }}?page={{ page }}" class="pagination-link" aria-label="Page 1" aria-current="page">{{ page }}</a>
            </li>
            {% else %}
            <li>
                <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">{{ page }}</a>
            </li>
            {% endif %}
        {% else %}
            <span class=pagination-ellipsis>&hellip;</span>
        {% endif %}
    {% endfor %}
</ul>
</nav>
```



#### 13 article_edit

##### article_edit route (아직 submit은 pass로 미완성)

- category edit를 복사해서 수정한다

```python
@admin_bp.route('/article/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def article_edit(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    with DBConnectionHandler() as db:
        post = db.session.get(Post, id)
    # 2) form내부에서는 객체를 받는 경우 edit로 인식하여, 객체정보를 form field에 대입해줄 예정이다.
    # -> cf) post.tags는 객체말고 id만 추출해서 [id list]를 내부에서 넣어줘야 view에서 selectize에 선택된 것만 표기되게 해야한다
    # -> cf) 부모객체도 .id만 넣어줘야하고, enum도 .value를 넣어줘야한다
    form = PostForm(post)

    if form.validate_on_submit():
        pass

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html', form=form, errors=errors)
```



#### 14 급작스런 모델 변경 for DB(int) <-> model(IntEnum) for form(data+label)

- 현재 IntEnum을 사용함에도 **db저장 및 form에서 활용 모두 enum의 name인 필드명만 사용되고 있는 상황이다.**



##### Column Type으로서 IntEnum 정의

1. src>infra>entity>**common > `int_enum.py` 생성**

   ![image-20221120015714664](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221120015714664.png)

   ```python
   from sqlalchemy import TypeDecorator, Integer
   
   # https://michaelcho.me/article/using-python-enums-in-sqlalchemy-models
   class IntEnum(TypeDecorator):
       """
       Enables passing in a Python enum and storing the enum's *value* in the db.
       The default would have stored the enum's *name* (ie the string).
       """
       # 1) DB저장은 Integer로 하므로, 상속하여 구현할 기존 sqlalclehmy Colum Type을 Integer로 지정한다.
       impl = Integer
      # 2) 해당 Column(IntEnum(MyEnumclass),  nullable... )으로 쓰일 Type은 Integer의 생성자를 재정의하되
       # -> 기존 생성자를 재정의해주고 + 특정Enumclass를 인자로 받아서 self._enumtype으로 보유하고 있는다.
       def __init__(self, enumtype, *args, **kwargs):
           super(IntEnum, self).__init__(*args, **kwargs)
           self._enumtype = enumtype
           
       # 3) [field to db bind]해당Type이 value를 Enum필드객체를 가지고 있을 것이므로, int로 변환하여 db에 정의되도로고 하는 bind 메서드를 정의한다.
       # -> int값이면 그대로 sql에 bind, enum필드객체면, .value를 통해, enum에 매핑된 int값을 bind시킨다.
       # -> 데이터 생성시에만 호출되는 것 같다
       def process_bind_param(self, value, dialect):
           if isinstance(value, int):
               return value
   
           return value.value
       # 4) 반대로 [db to field]로 가는 방향을 result method로 정의해준다.
       # -> model.custom이넘필드 = int로 들어오거나,    db에서 int로 올라오는 것 -> 객체에는 enum필드객체로 유지하도록 변환해준다.
       def process_result_value(self, value, dialect):
           # 5) EnumClass(value)를 하면, 해당 Enum필드객체를 반환해준다.
   		return self._enumtype(value)
   ```



##### model의 ColumType을 내가 정의한 IntEnum으로 변경

- 기존

  ```python
  has_type = Column(Enum(PostPublishType), server_default='show', nullable=False)
  ```

  - 그냥 주어진 sqlalchemy의 `Enum`Type을 쓰면, **`Enum필드객체의 변수명`으로만 `저장`된다. IntEnum으로서의 역할을 못하고 있었다.(value가 안쓰임)**

- **int<->enum객체로 상호변환을 정의한 Custom IntEnum Type을 칼럼으로 사용하자**

  - **이 때, server_default=는 db에 저장되는 값으로 서 `절 or string or text()구분`만 받는다. -> `text() or select()를 적당히 이용해서 integer 2를 만들면 될 듯`**

    

  - **default를 enum객체로 주기 위해 server_default=대신 default를 사용한다**

  - **`어차피 default값은, form의 radiofield의 default가 view로 갈 것이기 때문에, 여기서 신경쓸 필요 없다. nullable도 False이다.`**

  ```python
  class Post(BaseModel):
      __tablename__ = 'posts'
      #...
  
      has_type = Column(IntEnum(PostPublishType), default=PostPublishType.SHOW, nullable=False)
  
  ```





##### enum.IntEnum class(PostPublishType)에  form의 choices=를 위한 @classmethod 정의해주기

- **radioField는 html에서 순회하며 사용되는데**

  - `(subfield.data, subfield.label)`로 사용되는 친구들을 **tuple list로 `choices=`인자에 넣어줘야한다.**

  ```html
  {% for subfield in form.has_type %}
  <input {%if subfield.checked %}checked {% endif %} type="radio"
         id="{{ subfield.id }}" name="{{ form.has_type.id }}" value="{{ subfield.data }}">
  {{ subfield.label }}
  {% endfor %}
  ```

- **IntEnum class의 `(.value,  .name(enum필드명)`의 tuplelist를 반환해주는 classmethod를 정의한다.**

```python
class PostPublishType(enum.IntEnum):
    DRAFT = 1  # DRAFT
    SHOW = 2  # release

    # forms.py에서 radio의 choices로 들어갈 tuple list 를 (.value, .name)으로 반환해주면   html에서는  subfield.data, subfield.label로 사용할 수 있다.
    # https://michaelcho.me/article/using-python-enums-in-sqlalchemy-models
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]
```



##### form의 RadioField에 choices= 및 default= 값 넣어주기

```python
class PostForm(FlaskForm):
    #...
    has_type = RadioField('Post status',
                          choices=PostPublishType.choices(),
                          # choces에는 (subfield.data, subfield.label)로 될 값이 같이 내려가지만,defautld에는 .data가 되는 값 1개만 넘겨줘야한다.
                          default=PostPublishType.SHOW.value,
                          coerce=int,
                          )
```



##### article_edit route 수정

1. form을 채우기위한 post객체에 이미 tags들이 차있는 상황에서

   - POST로 들어오는 tag_id들 -> Tag객체들을 중복해서 찾아야하는 상황이 문제가 된다.

   - 새롭게 post객체를 찾아서 해결했다.

2. form.has_type.data에서는 RadioField의 coerce=int에 의해 int가 올라오고

   - **int value를 객체필드에 할당해주면 알아서 변환된다.**

```python
@admin_bp.route('/article/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def article_edit(id):
    with DBConnectionHandler() as db:
        post = db.session.get(Post, id)

    form = PostForm(post)

    if form.validate_on_submit():
        # 1) 이미 처음sesion에 의해 post.tags가 차있는 상태에서,
        #   또다시 바뀐 tag_id로 Tag객체를 찾아야하는 상황 -> post객체를 새로 가져와서 해결함.
        with DBConnectionHandler() as db:

            post = db.session.get(Post, id)

            post.title = form.title.data
            post.desc = form.desc.data
            post.content = form.content.data
            # 2) form에서 올라온 value는 coerce=int에 의해 int value가 올라오고
            #   -> 그대로 집어넣으면, 알아서 enum필드객체로 변환된다.
            post.has_type = form.has_type.data
            post.category_id = form.category_id.data

            post.tags = [db.session.get(Tag, tag_id) for tag_id in form.tags.data]

            db.session.add(post)
            db.session.commit()

            flash(f'{form.title.data} Post 수정 완료.')
            return redirect(url_for('admin.article'))
#
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/article_form.html', form=form, errors=errors)
```





#### 15 다시 article_edit 진행

##### front 20_article_form_change_after_intnum_radiofield.html

```html
<!-- label+input을 한번에 올리려면 div.field 이외에 .is-horizontal을 class로 넣어줘야한다.   -->
<div class="field is-horizontal">
    {{ form.has_type.label(class='label') }}
    <div class="field-body ml-4">
        <div class="control">
            <!--  radio 필드는 input필드를 직접 구현해야 생성시 default 와 edit시 현재값이 checked를 확인할 수 있다.-->
            {% for subfield in form.has_type %}
                <input {%if subfield.checked %}checked {% endif %} type="radio"
                       id="{{ subfield.id }}" name="{{ form.has_type.id }}" value="{{ subfield.data }}">
                {{ subfield.label }}
            {% endfor %}
        </div>
    </div>
</div>
```



##### front - 21_article_change_after_article_edit_route.html

```html
<a href="{{ url_for('admin.article_edit', id=post.id) }}" class="tag is-success is-light">
```



#### 16 article_delete

##### article_delete route

- cateogry_delete를 복사해서 수정

```python
@admin_bp.route('/article/delete/<int:id>')
@login_required
def article_delete(id):
    with DBConnectionHandler() as db:
        post = db.session.get(Post, id)

    if post:
        db.session.delete(post)
        db.session.commit()
        flash(f'{post.title} Post 삭제 완료.')
        return redirect(url_for('admin.article'))
```



##### front 22_article_change_after_adricel_delete_route.html

```html
                    <a href="{{url_for('admin.article_delete', id=post.id)}}" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
```



#### 17 entity 끝날때마다 admin/index.html의 메뉴 a태그에 route 및 is-active class걸어주기

- active여부를 class로 걸어주는데 **`request.path`에**
  - view가 1개 밖에 없는 admin.index는 `== '/admin/'`으로
  - view가 여러개 있는 entity관련 메뉴는 `'article' in `로 확인해준다.
- `is-active` class를 넣어준다.

##### front - 23_index_change_after_post_crud.html

```html
                    <ul class="menu-list">
                        <li>
                            <a class="{% if 'article' in request.path %}is-active{% endif %}"
                                href="{{ url_for('admin.article') }}">
                                Post 관리
                            </a>
                        </li>
                    </ul>
```

![image-20221120233219579](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221120233219579.png)



### Tag entity

#### 18 tag select

##### route

- entity crud관련은 모두 `admin_route.py`에 정의한다

- **select는 pagination으로 조회한다**
  - querystring page= default 1처리
  - entity pagatinate로 가져오기
  - .items로 entity_list 따로  / pagination객체 따로 render
- 생성일 의 역순으로 조회한다.

```python
@admin_bp.route('/tag')
@login_required
def tag():
    page = request.args.get('page', 1, type=int)

    stmt = select(Tag).order_by(Tag.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    tag_list = pagination.items

    return render_template('admin/tag.html',
                           tag_list=tag_list, pagination=pagination)

```



##### admin / tag.html 생성

![image-20221120234256841](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221120234256841.png)



##### front 24_tag_extends_index_after_tag_route.html

```html
{% extends 'admin/index.html' %}

{% block member %}
<!-- 위쪽 제목 공간 -->
<div class="is-block">
    <!-- left 제목 -->
    <div class="is-pulled-left">
        <h1 class="is-size-4">
            <span class="icon"><i class="mdi mdi-receipt-outline"></i></span>
            Tag 관리
        </h1>
    </div>
    <!-- right 버튼(상속할 form에선 달라짐) -> block개설 -->
    {% block button %}
    <div class="is-pulled-right">
        <!--  route) tag_add route 및 tag_form.html 개발 후 href채우기  -->
        <a href="" class="button is-primary is-light">
            <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
            <span>Tag 추가</span>
        </a>
    </div>
    {% endblock button %}
    <!--  분류선 by div2개: pulled-쓰과서 is-clearfix는 필수  -->
    <div class="is-clearfix"></div>
    <div class="dropdown-divider"></div>

    <!-- 아래쪽 table의 처리에 대한 flash 메세지를 위쪽에서   -->
    {% with messages = get_flashed_messages() %}
    <b-message type="is-success">
        {% if messages %}
        <ul class=flashes>
            {% for message in messages %}
            <li>{{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </b-message>
    {% endwith %}

	<!-- my) form validation errors -->
    {% for field in errors %}
    <b-message type="is-danger">
        <ul class="errors">
            {% for message in field.messages %}
            <li> {{ message }}</li>
            {% endfor %}
        </ul>
    </b-message>
    {% endfor %}
</div>

<!-- 위쪽 아래쪽 table or form 공간 -->
{% block table_content %}
<div class="table-container">
    <table class="table is-fullwidth is-hoverable is-striped">
        <thead>
        <tr>
            <th>Id</th>
            <th>Name</th>
            <th>생성일</th>
            <th>작업</th>
        </tr>
        </thead>
        <tbody>
        <!--  route) 에서 post객체들을 id역순으로 넘겨주면, for문이 돌아가면서 a태그 에러가 걸리게 됨.  -->
        <!--  a태그-href들 주석처리된 상태  -->
        {% for post in post_list %}
        <tr>
            <td>{{ tag.id }}</td>
            <td>{{ tag.name }}</td>
            <td>{{ tag.add_date }}</td>
            <td>
                <div class="tags">
<!--                    <a href="xx url_for('admin.tag_edit', id=tag.id) xx" class="tag is-success is-light">-->
                    <a href="" class="tag is-success is-light">
                            <span class="icon">
                                <i class="mdi mdi-square-edit-outline"></i>
                            </span>
                        수정
                    </a>
<!--                    <a href="xx url_for('admin.tag_delete', id=tag.id) xx" class="tag is-danger is-light">-->
                    <a href="" class="tag is-danger is-light">
                            <span class="icon">
                                 <i class="mdi mdi-trash-can-outline"></i>
                            </span>
                        삭제
                    </a>
                </div>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
<!-- route) 에서 tag_list외에 [pagination]객체도 던져줘야한다-->
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.tag') }}?page={{ pagination.prev_num }}" class="pagination-previous" title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('admin.tag') }}?page={{ pagination.next_num }}" class="pagination-next">Next page</a>
    {% endif %}

    <ul class="pagination-list">
        {% for page in pagination.iter_pages() %}
            {% if page %}
                {% if page != pagination.page %}
                <li>
                    <a href="{{ url_for('admin.tag') }}?page={{ page }}" class="pagination-link" aria-label="Page 1" aria-current="page">{{ page }}</a>
                </li>
                {% else %}
                <li>
                    <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">{{ page }}</a>
                </li>
                {% endif %}
            {% else %}
                <span class=pagination-ellipsis>&hellip;</span>
            {% endif %}
        {% endfor %}

    </ul>
</nav>

{% endblock table_content %}
{% endblock member %}
```





#### 19 entity끝나기 전에 미리 index menu a태그 표기 -> p태그를 Post관리 말고 Article관리로 바꾼 뒤, Tag도 Post와 같은 선상에, Tag관리는 삭제

##### front 25_index_change_after_tag_route.html

```html
<p class="menu-label">
    Article
</p>
<ul class="menu-list">
    <li>
        <a class="{% if 'article' in request.path %}is-active{% endif %}"
            href="{{ url_for('admin.article') }}">
            Post 관리
        </a>
    </li>
    <li>
        <a class="{% if 'tag' in request.path %}is-active{% endif %}"
            href="{{ url_for('admin.tag') }}">
            Tag 관리
        </a>
    </li>
</ul>
<!--<p class="menu-label">-->
<!--    Tag-->
<!--</p>-->
<!--<ul class="menu-list">-->
<!--    <li><a href="">Tag 관리</a></li>-->
<!--</ul>-->
```

![image-20221121000111505](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121000111505.png)





#### 20 tag create

##### TagForm

```python
class TagForm(FlaskForm):
    name = StringField('name', validators=[
        DataRequired(message='필수 입력.'),
        Length(max=128, message="최대 200 글자까지 입력 가능")
    ])

    # 1) 수정시 재활용을 위해, form채울 객체를 받는 생성자를 재정의한다.
    def __init__(self, tag=None, *args, **kwargs):
        self.tag = tag
        if self.tag:
            # 2) post와 다대다이면서 .posts를 backref로 받지만,
            #    2-1) tag생성시, tag.posts 정보가 필요없으며 &
            #    2-2-) tag수정시, 관계칼럼의 fk입력 관계객체필드<->form입력은 관계객체.id로 달라질 일이 없으므로
            #    category처럼, 객체가 raw값들만 가지는 경우,
            #    => ** + 객체.__dict__로  바로 객체정보를 form에 keyword로 입력시킬 수 있다.
            super().__init__(**self.tag.__dict__)
        else:
            super().__init__(*args, **kwargs)
    
    # 3) category처럼, 생성시 name중복검사 <-> 수정시 자신제외 name중복검사를 해야한다.
    def validate_name(self, field):
        if self.tag: # 수정시
            condition = and_(Tag.id != self.tag.id, Tag.name == field.data)
        else: # 생성시
            condition = Tag.name == field.data

        with DBConnectionHandler() as db:
            is_exists = db.session.scalars(
                exists().where(condition).select()
            ).one()

        if is_exists:
            raise ValidationError('이미 존재하는 Tag name입니다')
```

- init에 올려준다.



##### tag_add route

```python
@admin_bp.route('/tag/add', methods=['GET', 'POST'])
@login_required
def tag_add():
    form = TagForm()

    if form.validate_on_submit():
        tag = Tag(name=form.name.data)
        with DBConnectionHandler() as db:
            db.session.add(tag)
            db.session.commit()
        flash(f'{form.name.data} Tag 생성 성공!')
        return redirect(url_for('admin.tag'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/tag_form.html', form=form, errors=errors)

```



##### admin / tag_form.html 생성

#####  front - 26_tag_form_extends_tag_after_tag_add_route.html

```html
{% extends 'admin/tag.html' %}

{% block button %}{% endblock button %}


{% block table_content %}
    <form action="" method="post" class="mt-4">
        {{ form.csrf_token }}
        <div class="field">
            {{ form.name.label(class='label') }}
            <div class="control">
                {{ form.name(class='input', placeholder='Tag name') }}
            </div>
        </div>

        <div class="is-block">
            <div class="box has-background-light is-shadowless level">
                <a class=" is-danger button level-left">다시 입력</a>
                <div class="level-right">
                    <a href="{{ url_for('admin.tag') }}" class="button is-primary is-light mr-2">뒤로가기</a>
                    <input type="submit" value="완료" class=" button is-success">
                </div>
            </div>
        </div>
    </form>
{% endblock table_content %}
```

![image-20221121145119664](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221121145119664.png)

##### front - 27_tag_change_after_tag_form.html

```html
<!-- right 버튼(상속할 form에선 달라짐) -> block개설 -->
{% block button %}
<div class="is-pulled-right">
    <!--  route) tag_add route 및 tag_form.html 개발 후 href채우기  -->
    <a href="" href="{{url_for('admin.tag_add')}}" class="button is-primary is-light">
        <span class="icon"><i class="mdi mdi-plus-thick"></i></span>
        <span>Tag 추가</span>
    </a>
</div>
{% endblock button %}
```



#### 21 tag update

##### tag_edit route

- 이미 form생성시 수정용form으로도 사용가능하므로 route부터 개발한다

```python
@admin_bp.route('/tag/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def tag_edit(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)

    form = TagForm(tag)

    if form.validate_on_submit():
        tag.name = form.name.data
        db.session.add(tag)
        db.session.commit()

        flash(f'{form.name.data} Tag 수정 완료.')
        return redirect(url_for('admin.tag'))

    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('admin/tag_form.html', form=form, errors=errors)

```



##### tag.html에 수정에 route걸기

##### front - 28_tag_change_after_tag_edit_route.html

```html
<a href="{{url_for('admin.tag_edit', id=tag.id)}}" class="tag is-success is-light">
        <span class="icon">
            <i class="mdi mdi-square-edit-outline"></i>
        </span>
    수정
</a>
```



#### 22 tag delete

##### tag_delete route

```python
@admin_bp.route('/tag/delete/<int:id>')
@login_required
def tag_delete(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)

    if tag:
        db.session.delete(tag)
        db.session.commit()
        flash(f'{tag.name} Tag 삭제 완료.')
        return redirect(url_for('admin.tag'))
```



##### front - 29_tag_change_after_tag_edit_route.html

```html
<a href="{{url_for('admin.tag_delete', id=tag.id)}}" class="tag is-danger is-light">
        <span class="icon">
             <i class="mdi mdi-trash-can-outline"></i>
        </span>
    삭제
</a>
```




