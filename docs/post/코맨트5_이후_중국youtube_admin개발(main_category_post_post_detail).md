### main 타고 들어가는 Category -> Post

#### 1 category id select + many Posts

- admin에서는 admin.category 였지만, 
- main에서는 main.category(id)이며, category에 딸린 many post들을 다 보여준다
- **category가 게시판의 종류라 생각하면 될 것 같다.**



##### main.category(id) route  + with posts

- **현id category자기자신 + 딸린 posts다 조회**하기 위해  subquery 조인이 아니라
  - category 먼저 찾고 -> posts도 각각 찾아서 반환한다.
  - 찾은 many posts에 대해서는 paginate한다

```python
@main_bp.route("/category/<int:id>")
def category(id):
    # 1. category 찾기
    with DBConnectionHandler() as db:
        category = db.session.get(Category, id)

    # 2. 딸린 posts 찾고, pagination적용
    page = request.args.get('page', 1, type=int)
    stmt = (
        select(Post)
        .where(Post.category_id == category.id)
        .order_by(Post.add_date.desc())
    )
    pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    # 3. category + 딸린 post_list 한꺼번에 반환
    return render_template('main/category_list.html',
                           category=category,
                           post_list=post_list, pagination=pagination)

```



##### category.html

- templates > main 안에 생성해준다.

  ![image-20221123152811034](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123152811034.png)



##### front - 39_category_extends_base_after_main_category_id_route.html

```html
{% extends 'base.html' %}

{% block title %} {{ category.name }} {% endblock title %}

{% block hero %}{% endblock hero %}

{% block box %}
<div class="columns">
    <div class="column is-9" style="border-right:solid 1px #eee ;">
        <div class="box is-shadowless has-background-light">
            <!-- new breadcrumb block  -->
            {% block breadcrumb %}
            <nav class="breadcrumb is-small" aria-label="breadcrumbs">
                <ul>
                    <!-- Home만 addrule /로 직접 걸어주고 -->
                    <li><a href="/">Home</a></li>
                    <!-- 이후로는 직접 객체로 걸어주는데, [현재]면 #으로 걸고, .name만 / [부모]도 껴있으면 부모객체 -->
                    <li class="is-active"><a href="#" aria-current="page">{{ category.name }}</a></li>
                </ul>
            </nav>
            {% endblock breadcrumb %}
        </div>

        <!-- new 해당domain_box block 안에서 하위들을 돌린다. -->
        {% block cate_box %}
        {% for post in post_list %}
        <div class="pl-2">
            <h1 class="is-size-4">
<!--                <a href="xx url_for('main.detail', cate_id=post.category.id, post_id=post.id) yy">{{ post.title }}</a>-->
                <a href="">{{ post.title }}</a>
            </h1>
            <p class="has-text-grey-light is-size-6 mt-1">
                <span class="icon"><i class="mdi mdi-clipboard-text-clock-outline"></i></span>{{ post.add_date }}
                <span class="icon"><i class="mdi mdi-shape-outline"></i></span>{{ post.category.name }}
                <span class="icon"><i class="mdi mdi-tag-heart-outline"></i></span>{{ post.tags|join(',') }}
            </p>
            <div class="has-text-grey mt-1">{{ post.desc }}</div>
        </div>
        <div class=" dropdown-divider mb-3"></div>
        {% endfor %}

        {% block pagination %}
        <nav class="pagination is-small" role="navigation" aria-label="pagination">
            {% if pagination.has_prev %}
            <!-- 현재route를 걸어줘야한다 -->
            <a href="{{ url_for('main.category', id=cate.id ) }}?page={{ pagination.prev_num }}"
               class="pagination-previous" title="This is the first page">Previous</a>
            {% endif %}
            {% if pagination.has_next %}
            <a href="{{ url_for('main.category', id=cate.id ) }}?page={{ pagination.next_num }}"
               class="pagination-next">Next page</a>
            {% endif %}

            <ul class="pagination-list">
                {% for page in pagination.iter_pages() %}
                {% if page %}
                {% if page != pagination.page %}
                <li>
                    <a href="{{ url_for('main.category', id=cate.id) }}?page={{ page }}" class="pagination-link"
                       aria-label="Page 1" aria-current="page">{{ page }}</a>
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
        {% endblock pagination %}
        {% endblock cate_box %}
    </div>

    <div class="column">
        <div class="box is-shadowless" style="border:solid 1px #eee ;">
            <h1 class="is-size-6 icon-text">
                <span class="icon"><i class="mdi mdi-search-web"></i></span>
                검색
            </h1>
            <div class=" dropdown-divider"></div>
            <!-- 검색 아직 미개발 -->
<!--            <form action="xx url_for('main.search') yy" method="get">-->
            <form action="" method="get">
                <div class="field has-addons">
                    <div class="control">
<!--                        <input class="input" type="search" value="xx words yy" name="words" placeholder="검색keyword 입력">-->
                        <input class="input" type="search" value="" name="words" placeholder="검색keyword 입력">
                    </div>
                    <div class="control">
                        <input type="submit" value="Search" class="button is-info">
                    </div>
                </div>
            </form>
        </div>

        <div class="box is-shadowless" style="border:solid 1px #eee ;">
            <h1 class="is-size-6 icon-text">
                <span class="icon"><i class="mdi mdi-calendar-month-outline"></i></span>
                Archive
            </h1>
            <div class="dropdown-divider"></div>
            <ul>
                {% for date in dates %}
                <!-- archive 아직 미개발 -->
                <li class="pl-2">
<!--                    <a href="xx url_for('main.archive', date=date) yy">xx date yy</a>-->
                    <a href=""> date </a>
                </li>
                <div class="dropdown-divider"></div>
                {% endfor %}
            </ul>
        </div>

        <div class="box is-shadowless" style="border:solid 1px #eee ;">
            <h1 class="is-size-6 icon-text">
                <span class="icon"><i class="mdi mdi-tag-multiple-outline"></i></span>
                Tag
            </h1>
            <div class=" dropdown-divider"></div>
            {% for tag in tags %}
            <div class="tags">
                <!-- tag 아직 미개발 -->
                <a class="tag" href="">
                    tag
                </a>
<!--                <a class="tag xx tag.style|random() yy" href="xx url_for('main.tags', id=tag.id) yy">-->
<!--                    xx tag.name yy-->
<!--                </a>-->
            </div>
            {% endfor %}
        </div>
        <div class="box is-shadowless" style="border:solid 1px #eee ;">
            <h1 class="is-size-6 icon-text">
                <span class="icon"><i class="mdi mdi-calendar-month-outline"></i></span>
                Recent Article
            </h1>
            <div class=" dropdown-divider"></div>
            <ul>
                <!-- 최근 posts 아직 미개발  -->
                {% for post in new_posts %}
                <li class="pl-2">
                    <span class=" has-text-grey-light">{{ loop.index }}.</span>
                    <a href="">
                        post.title
                    </a>
<!--                    <a href="xx url_for('main.detail', id=post.category.id, post_id=post.id) yy">-->
<!--                        xx post.title yy-->
<!--                    </a>-->
                </li>
                <div class="dropdown-divider"></div>
                {% endfor %}
            </ul>
        </div>
    </div>
</div>
{% endblock box %}
```



- 아직 base.html의 메뉴에 link를 안걸어준 상태기 때문에, 직접 들어가서 확인

  ![image-20221123163635516](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123163635516.png)



##### front - 40_base_change_after_category.html

```html
{% for category in categories %}
<b-navbar-item href="{{ url_for('main.category', id=category.id) }}">
    {{category.name }}
</b-navbar-item>
```

![image-20221123164253551](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123164253551.png)





#### 2 categories와category와 , 특정route접속시 건네주는 category_id를 비교하여 menu에 색상표시

##### index route 에 category_id만 추가 render

- 이미 app_menu로서 categories -> for category돌고 있고,  route에서 category를 넘겨주고 있으니 category.id하면 for의 category와 겹치므로

  ```python
     # 4. categories(app_menu)와 상시비교되지만 평소에는 None으로 표기안됨. 진입시만 표기되로고
      #    category.id == category_id로 비교할 현재 category_id 넘겨주기
      return render_template('main/category.html',
                             category=category,
                             post_list=post_list, pagination=pagination,
                             category_id=category.id
                             )
  ```

##### base.html에서 평소에 안넘어가지만 해당변수를 써주면 None으로써 알아서 생략됨

##### front - 41 base_change_after_index_route_add_category_id.html

```html
<b-navbar-item
               {% if category.id ==  category_id %}
               class="has-text-primary"
               {% endif %}
               href="{{ url_for('main.category', id=category.id) }}">
    {{category.name }}
    {{category_id}}
</b-navbar-item>
```



![image-20221123193226668](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123193226668.png)

![image-20221123193409492](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123193409492.png)

#### 3 post_detail (category_id, id)  (1cate - 1post)

- category_id는 **부모객체를 찾아서 넘기기 위함인데, `확인된 바로는 breadcrumb`에 `category.id, + category.name를 넘기는 것만 사용`된다.**

  - 현재 자신의 부모를 찾아가는 것을 breadcrumb로 하고
  - 그것을 만들기 위해서는 부모객체가 필요하니, 부모id도 필요하다.

  

##### main.post_detail(category_id, id) route

- category(id)는 자신 + 자신으로부터 하위posts들
- **post(id)는 자신 + 상위부모id 1개**로 구성된다.
- **`상위entity를 타고 들어가야하는 소속된 하위 entity`의 url은 `/상위entity/상위entity_id/` + `자신_id`로 구성한다**
  - 단독 `entity/id`는 이미 admin에서 가지기 때문



```python
# 1) 상위entity를 타고 들어가야하는 소속된 하위 entity의 url은 /상위entity/상위entity_id/ + /자신_id로 구성한다
# -> 단독 entity/id는 이미 admin_route에서 가지기 때문
@main_bp.route("/category/<int:category_id>/<int:id>")
def post_detail(category_id, id):
    # 2) 타고 들어가는 하위의 경우, 부모도 먼저 찾고 -> 나 찾기
    with DBConnectionHandler() as db:
        category = db.session.get(Category, category_id)
        post = db.session.get(Post, id)

    return render_template('post_detail.html', 
                           category=category, post=post)
```





##### post_detail.html

- **새로운 영역(breadcrumb + sidebar column(검색, 최근기사) 등을 위해 `부모entity의 html을 상속해서 사용`한다**
  - base.html만 templates에 있고, 부모인 category.html은 `templates/main`에 있으므로 **extends의 기준인 templates이후 `main/category.html`로 상속해야한다.**
- category를 타고 내려가는 post개별로서, breadcrumb에 부모정보를 입력해준다.



##### front 41_post_detail_extends_category_after_post_detail_route.html

```html
{% extends 'main/category.html' %}

{% block title %}
    {{ post.title }}
{% endblock title %}

{% block breadcrumb %}
    <nav class="breadcrumb is-small" aria-label="breadcrumbs">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="{{ url_for('main.category', id=category.id) }}">{{ category.name }}</a></li>
            <li class="is-active"><a href="#" aria-current="page">{{ post.title }}</a></li>
        </ul>
    </nav>
{% endblock breadcrumb %}

{% block cate_box %}
<div class="pl-2">
    <h1 class="is-size-3">
        {{ post.title }}
    </h1>
    <p class="has-text-grey-light is-size-6 mt-1">
        <span class="icon"><i class="mdi mdi-clipboard-text-clock-outline"></i></span>{{ post.add_date }}
        <span class="icon"><i class="mdi mdi-shape-outline"></i></span>{{ post.category.name }}
        <span class="icon"><i class="mdi mdi-tag-heart-outline"></i></span>{{ post.tags|join(',') }}
    </p>
    <!-- markdown 적용예정인 필드는 |safe를 달아준다.   -->
    <div class="content has-text-grey mt-1">{{ post.content | safe }}</div>
</div>

<hr>
<!-- NEW 이전글 다음글을 div.level태그 안에 left/right로 만들어준다.-->
<div class="level">
    <div class="level-left">
        {% if prev_post %}
<!--            이전 글：<a href="xx url_for('main.post_detail', category_id=prev_post.category.id, id=prev_post.id) yy">xx prev_post.title yy</a>-->
            이전 글：<a href="">  이전 글 </a>
        {% endif %}
    </div>
    <div class="level-right">
        {% if next_post %}
<!--            다음 글：<a href="xx url_for('main.post_detail', category_id=next_post.category.id, id=next_post.id) yy"> {{ next_post.title }} </a>-->
            다음 글：<a href="">다음 글</a>
        {% endif %}
    </div>
</div>
{% endblock cate_box %}
```



- 아직 외부에서 링크를 안걸어줫으므로 url `/category/1/1`로 접속해본다.



##### front 42_base_change_after_post_detail.html

- **base로는 category를 안넘기므로, 반복문 속 post에서 category_id를 빼내면 된다.**

```html
                            <div class="card-content">
                                <div class="media">
                                    <div class="media-content">
                                        <p class="title is-4"><a href="{{url_for('main.post_detail', category_id=post.category_id, id=post.id) }}">{{ post.title }}</a></p>
                                    </div>
                                </div>
```



##### front 43_category_change_after_post_detail.html

```html
        {% for post in post_list %}
        <div class="pl-2">
            <h1 class="is-size-4">
                <a href="{{ url_for('main.post_detail', category_id=post.category_id, id=post.id) }}">{{ post.title }}</a>
            </h1>
```



##### main.post_detail route (이전글, 다음글 적용)

```python
# 1) 상위entity를 타고 들어가야하는 소속된 하위 entity의 url은 /상위entity/상위entity_id/ + /자신_id로 구성한다
# -> 단독 entity/id는 이미 admin_route에서 가지기 때문
@main_bp.route("/category/<int:category_id>/<int:id>")
def post_detail(category_id, id):
    # 2) 타고 들어가는 하위의 경우, 부모도 먼저 찾고 -> 나 찾기
    with DBConnectionHandler() as db:
        category = db.session.get(Category, category_id)
        #### cateogory.posts에서  넘어온 post의 id로 post객체를 골라낼 수 있다.
        # post = [cate_post for cate_post in  category.posts if cate_post.id == id][0]
        # -> 하지만, lazy로 찾은 객체를 view에 넘겨서 post.title 등을 사용하면 session연결이 끊긴 객체라 뜬다.
        # -> view에 넘겨줄 객체는 한번 더 찾자.
        post = db.session.get(Post, id)

        # 3) detail에서 이전글, 다음글을 [1]해당category안에서 [2]id작은것들 가장 큰 것(역순1번째) [2] id큰것들 중 정순 1번재를 찾으면 된다.
        # ==> 이미 찾아놓은 category, post를 stmt로 쿼리날리면, 경고가 뜬다. 이미 .post와 post.category로 연결된 사이라고
        # -> category.posts를 이용해서 필터링해서 이전글을 찾는다.
        prev_posts = sorted([cate_post for cate_post in category.posts if cate_post.id < post.id],
                            key=lambda x: x.id, reverse=True)
        next_posts = sorted([cate_post for cate_post in category.posts if cate_post.id > post.id],
                            key=lambda x: x.id)
        # 필터링안걸리면 빈list로서 [0] 첫번째 객체를 indexing할 수없기 때문에 조건문으로 준다. 
        prev_post = prev_posts[0] if prev_posts else None
        next_post = next_posts[0] if next_posts else None
        # prev_stmt = select(Post)\
        #     .where(and_(Category.id == post.category_id, Post.id < post.id))\
        #     .order_by(Post.id.desc())\
        #     .limit(1)
        # next_stmt = select(Post)\
        #     .where(and_(Category.id == post.category_id, Post.id > post.id))\
        #     .order_by(Post.id.asc())\
        #     .limit(1)
        # prev_post = db.session.scalars(prev_stmt).first()
        # next_post = db.session.scalars(next_stmt).first()


    print(post, prev_post, next_post)
    
    return render_template('main/post_detail.html',
                           category=category, post=post,
                           prev_post=prev_post, next_post=next_post)
```

- 첫번째글은 이전글이 없어야한다.

  ![image-20221123185512323](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123185512323.png)

  ![image-20221123185526134](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123185526134.png)



- 마지막글은 다음글이 없어야한다.

  ![image-20221123185542112](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123185542112.png)





##### front - 44_post_detail_change_after_post_detail_이전글다음글완성.html

```html
<!-- NEW 이전글 다음글을 div.level태그 안에 left/right로 만들어준다.-->
<div class="level">
    <div class="level-left">
        {% if prev_post %}
            이전 글：<a href="{{ url_for('main.post_detail', category_id=prev_post.category_id, id=prev_post.id) }}">{{ prev_post.title }}</a>
        {% endif %}
    </div>
    <div class="level-right">
        {% if next_post %}
            다음 글：<a href="{{ url_for('main.post_detail', category_id=next_post.category_id, id=next_post.id) }}"> {{ next_post.title }} </a>
        {% endif %}
    </div>
</div>
{% endblock cate_box %}
```

