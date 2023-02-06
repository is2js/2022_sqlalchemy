### 특정 route의 전체view에 다 항시필요한 정보 -> @bp.context_processor로 등록

- menu인 category는 특정route가 아니라 **모든 화면에 필요한 정보 -> app.context_precessor로 처리**

  ![image-20221124144722665](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124144722665.png)

  ```python
  def inject_category():
      with DBConnectionHandler() as db:
          stmt = (
              select(Category)
              .order_by(Category.id.asc())
              .limit(6)
          )
  
          categories = db.session.scalars(stmt).all()
      return dict(categories=categories)
  
  
  app.context_processor(inject_category)
  
  ```

  

- app_menu가 아닌 **admin, auth제외 main에만 떠있는 정보 -> main_route의 `main_bp`에만 `항시떠있는 정보를 @main_bp.context_processor`**로 처리한다.

  ![image-20221124144643922](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124144643922.png)



### main - archive외 inject

#### main_route에 -> inject_archive() 메서드 정의

- archive는 년-월의 날짜별로 post를 모아주는 것이다?

  ![image-20221124145238348](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124145238348.png)

##### dates for archive

- jinja에 순회될 객체를 list대신 set으로 보내줘도 된다.
  - 년월일시분초에서 년 월로만 변환하면 중복이 많으니 set으로 만들어서 보낸다

```python
@main_bp.context_processor
def inject_archive():
    with DBConnectionHandler() as db:
        ## archive
        # 1) post를 시간 역순 for 최신글 정렬해놓고 -> 생성일add_date에서 %Y년 %월의 string으로 변경한 다음
        # -> 년 월일 추출이므로 역순으로 정렬해도 상관없다.
        # 2) set으로 중복을 제거한 dates를 준비한다.
        posts = db.session.scalars(select(Post).order_by(Post.add_date.desc())).all()
        date_format = '%Y년 %m월'.encode('unicode-escape').decode()

        dates = set(post.add_date.strftime(date_format).encode().decode('unicode-escape') for post in posts)
     
        print(dates)
        
    return dict(dates=dates)
```

![image-20221124153556218](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124153556218.png)

```html
<ul>
    {% for date in dates %}
    <!-- archive 아직 미개발 -->
    <li class="pl-2">
        <!--                    <a href="xx url_for('main.archive', date=date) yy">xx date yy</a>-->
        <a href=""> {{date}} </a>
    </li>
    <div class="dropdown-divider"></div>
    {% endfor %}
</ul>
```





##### tags

- entity 모델객체에, html에서 필요한 요소들을 동적으로 필드를 만들어서 보내줄 수 있다.
  - html쓸 꾸며주는 class를 객체.style = [] 리스트로 넣어서 보내고, html에서는 | random()으로 1개르 뽑아서 쓴다.

```python
@main_bp.context_processor
def inject_archive():
    with DBConnectionHandler() as db:
        ## archive
        posts = db.session.scalars(select(Post).order_by(Post.add_date.asc())).all()

        date_format = '%Y년 %m월'.encode('unicode-escape').decode()
        dates = set(post.add_date.strftime(date_format).encode().decode('unicode-escape') for post in posts)

        ## tags
        tags = db.session.scalars(select(Tag)).all()
        for tag in tags:
            tag.style = ['is-success', 'is-danger', 'is-black', 'is-light', 'is-primary', 'is-link', 'is-info', 'is-warning']

    return dict(dates=dates, tags=tags)
```

```html
<div class="tags">
    {% for tag in tags %}
    <!-- tag 아직 미개발 -->
    <a class="tag {{ tag.style | random() }}" href="">
        {{ tag.name }}
    </a>
    {% endfor %}
</div>
```



![image-20221124154301454](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124154301454.png)



##### new_posts for 최신글

- 미리 역순정렬해놨으니, 인덱싱으로 5개만 뽑으면 된다.

```python
@main_bp.context_processor
def inject_archive():
    with DBConnectionHandler() as db:
        ## archive
        # 1) post를 시간 역순 for 최신글 정렬해놓고 -> 생성일add_date에서 %Y년 %월의 string으로 변경한 다음
        # -> 년 월일 추출이므로 역순으로 정렬해도 상관없다.
        # 2) set으로 중복을 제거한 dates를 준비한다.
        posts = db.session.scalars(select(Post).order_by(Post.add_date.desc())).all()
        # https://onlytojay.medium.com/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%82%A0%EC%A7%9C-%ED%91%9C%ED%98%84-%ED%95%9C%EA%B8%80-%EC%97%90%EB%9F%AC-44aea1ae66d8
        date_format = '%Y년 %m월'.encode('unicode-escape').decode()
        dates = set(post.add_date.strftime(date_format).encode().decode('unicode-escape') for post in posts)

        ## tags
        tags = db.session.scalars(select(Tag)).all()
        # 3) entity 모델객체에, html에서 필요한 요소들을 동적으로 필드를 만들어서 보내줄 수 있다.
        # -> html쓸 꾸며주는 class를 객체.style = [] 리스트로 넣어서 보내고, html에서는 | random()으로 1개르 뽑아서 쓴다.
        for tag in tags:
            tag.style = ['is-success', 'is-danger', 'is-black', 'is-light', 'is-primary', 'is-link', 'is-info', 'is-warning']

        ## new_posts
        # -> 역순으로 정렬된 상태이므로 limit(flask) or 인덱싱으로 추출만 하면 된다.
        new_posts = posts[:5]
        print(new_posts)

    return dict(dates=dates, tags=tags, new_posts=new_posts)
```

```html
<ul>
    <!-- 최근 posts 아직 미개발  -->
    {% for post in new_posts %}
    <li class="pl-2">
        <span class=" has-text-grey-light">{{ loop.index }}.</span>
        <a href="">
            {{post.title}}
        </a>
    </li>
    <div class="dropdown-divider"></div>
    {% endfor %}
</ul>
```



![image-20221124155635858](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124155635858.png)



##### front - 46_category_change_after_inject_archive.html

```html
            <ul>
                {% for date in dates %}
                <!-- archive 아직 미개발 -->
                <li class="pl-2">
<!--                    <a href="xx url_for('main.archive', date=date) yy">xx date yy</a>-->
                    <a href=""> {{date}} </a>
                </li>
                <div class="dropdown-divider"></div>
                {% endfor %}
            </ul>





            <div class="tags">
            {% for tag in tags %}
                <!-- tag 아직 미개발 -->
                <a class="tag {{ tag.style | random() }}" href="">
                    {{ tag.name }}
                </a>
            {% endfor %}
            </div>








            <ul>
                <!-- 최근 posts 아직 미개발  -->
                {% for post in new_posts %}
                <li class="pl-2">
                    <span class=" has-text-grey-light">{{ loop.index }}.</span>
                    <a href="">
                        {{post.title}}
                    </a>
                </li>
                <div class="dropdown-divider"></div>
                {% endfor %}
            </ul>
```





#### recent article 처리( route없이 post_detail로 href링크만)

- archive는 `년월`입력에 따라 다르게 post_list 데이터구성 + pagination url_for로 **새로운 화면 구성**해야하며

- tag역시 **해당 tag를 가지는 post_list 데이터로 화면을 새로 구성**해야한다

- 하지만 new_posts 는 **클릭시 새로운화면 구성X post_detail로만 연결하면 된다.**

  ```python
  @main_bp.context_processor
  def inject_archive():
      with DBConnectionHandler() as db:
          #...
      
      new_posts = posts[:5]
  
      return dict(dates=dates, tags=tags, new_posts=new_posts)
  
  ```



##### front - 47_category_change_after_inject_archive_new_posts.html

- **post_detail로 연결할 땐, `category/categoy_id/(post)id`형식으로 하위entity로서 `부모를 breadcrumb용`으로 가지고 조회한다**

```html
<ul>
    <!-- 최근 posts 아직 미개발  -->
    {% for post in new_posts %}
    <li class="pl-2">
        <span class=" has-text-grey-light">{{ loop.index }}.</span>
        <a href="{{ url_for('main.post_detail', category_id=post.category.id, id=post.id) }}">
            {{post.title}}
        </a>
    </li>
    <div class="dropdown-divider"></div>
    {% endfor %}
</ul>
```







#### archive(date) /category/string:date  route

##### db에는 없는 상위카테고리를 backend에서 만들고,  만든 그룹으로 route에 입력받아 조회되게 한다

- posts의 생성일에서 년-월만 뽑아서 view에 뿌렸는데

- 해당 년-월 string을 클릭시 다시 해당 posts들을 뿌려주는 route + html이 필요하다

  ![image-20221124170616433](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124170616433.png)

  - **같은화면이지만, `년월의 변수`에 따라 `다른데이터를 route에서 query날려야`하므로 GET이지만 querysting이 아닌 path(string)로 받아야한다**

##### archive route 1차

```python
@main_bp.route('/category/<string:date>')
def archive(date):
    # 1) 정규표현식으로 년 4글자(%Y)와 월2글자(%m)을 추출한다
    # http://localhost:5000/main/category/2020년10월
    # -> ['2020', '10']
    # 1월은 안나오고 01월을 해야 추출된다.
    # 혹시 몰라서 뒤에것은 d{1,2}로 수정
    # -> 이 때, 추출단위마다 |를 씌워야, list에서 개별변수로 인식하며, 해당하는 것들을 순서대로 다찾는다
    # -> 단, 추가발견되면 추가로 나온다  ex>  2020년1월1010일 -> ['2020', '1', '1010']
    # regex = re.compile(r'\d{4}|\d{2}')
    regex = re.compile(r'\d{4}|\d{1,2}')
    dates = regex.findall(date)

    # 2) breadcrumb를 위해 path로 온 하위의 의미인 date도 같이 넘겨준다
    return render_template('main/archive.html', date=date)
```



##### main / archive.html  extends  category

- main/category를 **상속**하여 **`post_list를 뿌리는 동작을 html작성없이 데이터만 넘겨서 처리할 예정`**
  - breadcrumb는 달라진다
  - pagination도 **date가 변수가 되므로 url_for의 인자가 달라져서 구성이 달라지므로 다시 작성해야한다.**



##### front - 48_archive_extends_category_after_archive_route_1차(no pagination).html

```html
{% extends 'main/category.html' %}

{% block title %} {{ date }} Archive {% endblock title %}

{% block hero %}{% endblock hero %}

{% block breadcrumb %}
    <nav class="breadcrumb is-small" aria-label="breadcrumbs">
        <ul>
            <li><a href="/">Home</a></li>
            <li class="is-active">
                <a href="#" aria-current="page">{{ date }}</a>
            </li>
        </ul>
    </nav>
{% endblock breadcrumb %}


{% block pagination %}
{% endblock pagination %}
```



##### archive route 2차(dates 해당 post,  및 pagination)

```python
@main_bp.route('/category/<string:date>')
def archive(date):
    # 1) 정규표현식으로 년 4글자(%Y)와 월2글자(%m)을 추출한다
    # http://localhost:5000/main/category/2020년10월
    # -> ['2020', '10']
    # 1월은 안나오고 01월을 해야 추출된다.
    # 혹시 몰라서 뒤에것은 d{1,2}로 수정
    # -> 이 때, 추출단위마다 |를 씌워야, list에서 개별변수로 인식하며, 해당하는 것들을 순서대로 다찾는다
    # -> 단, 추가발견되면 추가로 나온다  ex>  2020년1월1010일 -> ['2020', '1', '1010']
    # regex = re.compile(r'\d{4}|\d{2}')
    regex = re.compile(r'\d{4}|\d{1,2}')
    dates = regex.findall(date)

    # 3) 이제 dates['2022', '01']을 이용하여 posts를 골라낸다
    # -> add_date 타입에 대해 extract('year', ) 'month'를 활용해서 where조건을 만든다.
    page = request.args.get('page', 1, type=int)
    stmt = (
        select(Post)
        .where(and_(
            extract('year', Post.add_date) == int(dates[0]),
            extract('month', Post.add_date) == int(dates[1]),
        ))
        .order_by(Post.add_date.desc())
    )
    pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    # 2) breadcrumb를 위해 path로 온 하위의 의미인 date도 같이 넘겨준다
    return render_template('main/archive.html', date=date,
                           post_list=post_list, pagination=pagination
                           )
```



- 확인만



![image-20221124185103146](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124185103146.png)



##### front - 49_archive_change_after_archive_route_pagination.html

- **pagination시 route가 달라지므로 block을 새롭게 채워야한다**

```html
{% extends 'main/category.html' %}

{% block title %} {{ date }} Archive {% endblock title %}

{% block hero %}{% endblock hero %}

{% block breadcrumb %}
<nav class="breadcrumb is-small" aria-label="breadcrumbs">
    <ul>
        <li><a href="/">Home</a></li>
        <li class="is-active">
            <a href="#" aria-current="page">{{ date }}</a>
        </li>
    </ul>
</nav>
{% endblock breadcrumb %}


{% block pagination %}
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('main.archive', date=date ) }}?page={{ pagination.prev_num }}" class="pagination-previous"
       title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('main.archive', date=date) }}?page={{ pagination.next_num }}" class="pagination-next">Next
        page</a>
    {% endif %}

    <ul class="pagination-list">
        {% for page in pagination.iter_pages() %}
        {% if page %}
        {% if page != pagination.page %}
        <li>
            <a href="{{ url_for('main.archive', date=date) }}?page={{ page }}" class="pagination-link"
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
```



![image-20221124193720554](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124193720554.png)



##### front - 50_category_change_after_archive_route.html

```html
<ul>
    {% for date in dates %}
    <li class="pl-2">
        <a href="{{ url_for('main.archive', date=date) }}"> {{date}} </a>
    </li>
    <div class="dropdown-divider"></div>
    {% endfor %}
</ul>
```





#### tag(int:id) route

- category 화면에서 tag를 클릭했을 때, 해당tag_id를 가지는 post_list를 뿌려줘야한다
  - **특정 tag를 클릭할 때, 그 id로 처리**해야한다
    - 어차피 tags -> tag객체를 돌고 있으니, **href로 tag.id를 입력**해줄 것이다.
  - archive의 경우, 날짜이며 entity객체가 아니라서 string으로 넘겨줘서 파싱해서 처리했다.
- tag_id -> Tag객체 -> Tag.posts로 바로 관련된 것을 뽑아올 수 있다.
  - **tag_id를 가진 post를 바로 찾아도 되지만, `breadcrumb 및 pagination을 위해, 딸린posts만 찾을게 아니라 부모인 Tag도 객체를 찾아야한다`**



```python
@main_bp.route('/tag/<int:id>')
def tag(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)
    post_list = tag.posts
    print(post_list)
    return ''
```





##### Post Entity 에러

###### test시 lazy에러 `(1차 backend lazy=True) tag.posts` -> `(2차 front에서 필드접근 -> subquery필요 ) for post in posts에서 개별post.필드 접근`시 에러 

- http://localhost:5000/main/tag/1
- sqlalchemy.orm.exc.DetachedInstanceError: **Parent instance <Tag at 0x1f43e7a37b8> is not bound to a Session; lazy load operation of attribute 'posts' cannot proceed (Background on this error at: https://sqlalche.me/e/14/bhk3)**

```python
class Post(BaseModel):
    __tablename__ = 'posts'
    # ...
	tags = relationship('Tag', secondary=posttags,
                        lazy='subquery',
                        # backref=backref('posts', lazy=True)
                        backref=backref('posts', lazy='subquery')
                        )

```

```
[Post[title='첫글'], Post[title='최신글'], Post[title='test']]
```



##### 다시 tag route

```python
@main_bp.route('/tag/<int:id>')
def tag(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)
    post_list = tag.posts

    return render_template('main/tag.html', post_list=post_list, tag=tag)
```



###### front - 51_tag_extends_category_after_tag_route(no pagination).html

```html
{% extends 'main/category.html' %}

{% block title %}{{ tag.name }} {% endblock title %}

{% block hero %}{% endblock hero %}

{% block breadcrumb %}
    <nav class="breadcrumb is-small" aria-label="breadcrumbs">
        <ul>
            <li><a href="/">Home</a></li>
            <li class="is-active"><a href="#" aria-current="page">{{ tag.name }}</a></li>
        </ul>
    </nav>
{% endblock breadcrumb %}

{% block pagination %}

{% endblock pagination %}
```



###### front - 52_category_change_after_tag_route.html

```html
<!-- tag  -->
<div class="tags">
    {% for tag in tags %}
    <a class="tag {{ tag.style | random() }}"
       href="{{ url_for('main.tag', id=tag.id) }}">
        {{ tag.name }}
    </a>
    {% endfor %}
</div>
```



##### Post Entity 에러2

###### tag.posts --(subquery해결)--> for post in posts -> (1차 subquery) post.tags  `(2차 front) | join(',')`

- **{{ post.tags }}**만 썼다면 에러 안나지만,
  - post -> .tags -> **개별 tag**를 str()하여 join하는 **접근**이 이루어지므로 **`post입장에서 join이 2번이 일어난다`**

- sqlalchemy.orm.exc.DetachedInstanceError: **Parent instance <Post at 0x299301926d8> is not bound to a Session**; lazy load operation of **attribute 'tags'** cannot proceed (Background on this error at: https://sqlalche.me/e/14/bhk3)

  ![image-20221124232143074](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124232143074.png)





###### post입장에서 .tags(subquery) 이후 tag들의 .name들을 join(2차 subquery) -> `join_depth=2`로 수정

```python
class Post(BaseModel):
    __tablename__ = 'posts'
    #...
    tags = relationship('Tag', secondary=posttags,
                        # lazy='subquery',
                        lazy='subquery', join_depth=2,
                        # backref=backref('posts', lazy=True)
                        backref=backref('posts', lazy='subquery')
                        )
```

![image-20221124235607799](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124235607799.png)

##### my) backref 내 정리

- backend에서 접근하여 쓸 거면 backref lazy=True == lazy='select?'로 충분하지만
- **backend에서 객체.관계객체로 받은 뒤  -> `front로 넘겨서 사용될 예정인 .관계객체`라면,  `backref - subquery`를 도입하면 된다.**
- **그러나, `front에 넘겨서 객체.안에관계객체`가 사용될 예정이라면 객체(post).필드 뿐만 아니라 `객체(post).관계객체(tags) -> 관계객체(tags).필드(자기필드)` 를 쓸거면 `첫번째 시작객체(post)가 backref(tags)를 넘겨줄 때, subquery + join_depth=2`를 써서 구성되어야한다.**

```python
class Post(BaseModel):
    __tablename__ = 'posts'
    tags = relationship('Tag', secondary=posttags,
                        # (front) for post -> post.tags -> tags |join(',')
                        lazy='subquery', join_depth=2, 
                         # post_list =  tag.posts로 넘길 때 
                        backref=backref('posts', lazy='subquery')
                       )

```

![image-20221125000613753](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125000613753.png)

- subquery로 충분히
  - (back)**tag.posts -> (front) for post in post_list**
- subquery + **`join_depth=2`**
  - (front 1차) for post -> **post.tags** 
  - (front 2차) tags | **`join(,)`**
    - **`for tag`** in tags -> tag.name을 쓰는 것과 마찬가지





##### pagination 적용

- **이미 tag.posts로 추출된 상태에서 pagination을 적용해보자.**

  - **tag.posts**
    - `<class 'sqlalchemy.orm.collections.InstrumentedList'>`
  - **db.session.scalars(select(Post)).all()**
    - `<class 'list'>`
  - main
    - `<class 'sqlalchemy.sql.selectable.Select'>`
  - category
    - `<class 'sqlalchemy.sql.selectable.Select'>`

- **순회시키는 `.many관계객체` or  `scalars().all()`의 타입이 다르므로, select문인지 아닌지 확인한다**

  ![image-20221125010143901](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125010143901.png)







##### paginate(stmt, ~) 함수에 객체도 허용해보기

```python
def paginate(stmt, page=1, per_page=db_config.COMMENTS_PER_PAGE):
    if page <= 0:
        raise AttributeError('page needs to be >= 1')
    if per_page <= 0:
        raise AttributeError('per_page needs to be >= 1')

    # print(type(stmt)) # <class 'sqlalchemy.sql.selectable.Select'>
    # print(isinstance(stmt, Select)) # True
    if not isinstance(stmt, Select):
        total = len(stmt) # list의 갯수
        # 1) offset: 앞에서쩨낄 구간의 갯수 = (page - 1(1부터오면 offset구간0되게) )  *  구간의열갯수 만큼 건너띄기
        # 1-1) 직접하기 위해선 per_page(pair)==구간의 열갯수를 이용해서 전체 구간갯수를 구한다.
        # pages = math.ceil(total / per_page)
        # 그러나, 유효성검사는 생략한다.  [알아서 1번]부터 들어오고, Pagination객체 내부에서 존재할때만 page를 내어주기 때문
        # 1-2) 열갯수 * (원하는페이지 -1)만큼을 offset하여 그 이후로 시작하게 한다.
        offset = per_page * (page - 1)
        items = stmt[offset:]
        # 2) limit으로서, 현재시작에서 열갯수만큼만 가져온다
        # ->  슬라이싱하면, 꽉채워 없으면, 있는것만큼만 가져와준다.
        items = items[:per_page]

        return Pagination(items, total, page, per_page)

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



##### tag route에 pagination 적용

```python
@main_bp.route('/tag/<int:id>')
def tag(id):
    with DBConnectionHandler() as db:
        tag = db.session.get(Tag, id)
    #post_list = tag.posts

    page = request.args.get('page', 1, type=int)
    # stmt대신 객체list를 건네서 paginate 수행
    pagination = paginate(tag.posts, page=page, per_page=10)
    post_list = pagination.items

    return render_template('main/tag.html', post_list=post_list, tag=tag,
                           pagination=pagination)

```



##### front - 53_tag_change_after_tag_route_pagination.html

```html
{% block pagination %}
<nav class="pagination is-small" role="navigation" aria-label="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('main.tag', id=tag.id ) }}?page={{ pagination.prev_num }}" class="pagination-previous"
       title="This is the first page">Previous</a>
    {% endif %}
    {% if pagination.has_next %}
    <a href="{{ url_for('main.tag', id=tag.id) }}?page={{ pagination.next_num }}" class="pagination-next">Next
        page</a>
    {% endif %}

    <ul class="pagination-list">
        {% for page in pagination.iter_pages() %}
        {% if page %}
        {% if page != pagination.page %}
        <li>
            <a href="{{ url_for('main.tag', id=tag.id) }}?page={{ page }}" class="pagination-link"
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
```

![image-20221125020105068](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125020105068.png)











#### search

##### search는 정렬/필터링에 해당하므로 querystring으로 처리해야한다.

```
Query String VS Path Variable
Path Variable은 특정 인덱스에 대한 조회.

 

Query String 은 특정 값으로 필터링.

 

Example) 아이디가 20번인 유저 조회  ->  Path Variable 사용 -> GET  /user/:userid

이름이 james이고 20살인 유저 조회  -> Query String 사용  ->  GET /user?userName=james&?age=20

 

만약 어떤 resource를 식별하고 싶으면 Path Variable을 사용하고...
정렬이나 필터링을 한다면 Query Parameter를 사용하는 것이 가장 이상적 입니다!
```

```
일반적으로 우리가 어떤 자원(데이터)의 위치를 특정해서 보여줘야 할 경우 Path variable을 쓰고, 정렬하거나 필터해서 보여줘야 할 경우에 Query parameter를 쓴다. 아래가 바로 그렇게 적용한 사례이다.

/users # Fetch a list of users
/users?occupation=programer # Fetch a list of programer user
/users/123 # Fetch a user who has id 123
위의 방식으로 우리는 어디에 어떤 데이터(명사)를 요청하는 것인지 명확하게 정의할 수 있다. 하지만, 그 데이터를 가지고 뭘 하자는 것인지 동사는 빠져있다. 그 동사 역할을 하는 것이 GET, POST, PUT, DELETE 메소드이다.

즉, Query string과 Path variable이 이들 메소드와 결합함으로써 "특정 데이터"에 대한 CRUD 프로세스를 추가의 엔드포인트 없이 완결 지울 수 있게 되는 것인다.
(가령, users/create 혹은 users?action=create를 굳이 명시해 줄 필요가 없다.)

/users [GET] # Fetch a list of users
/users [POST] # Create new user
/users/123 [PUT] # Update user
/users/123 [DELETE] # remove user
물론 위와 같은 규칙을 지키지 않더라도 잘 돌아가는 API를 만들 수 있다. 하지만 지키지 않을 경우 서비스 엔드포인트는 복잡해 지고, 개발자간/외부와 커뮤니케이션 코스트가 높아져 큰 잠재적 손실을 초래할 수 있으니 이 규칙은 잘 지켜서 사용하는 것이 필수라 하겠다.
```

```
검색 기능을 구현하기 전에 검색 기능을 GET 방식으로 구현해야 하는 이유에 대해서 잠시 알아보자. 다음은 앞에서 kw를 사용한 코드의 일부이다.

kw = request.args.get('kw', type=str, default='')  # 검색어
kw는 keywords의 줄임말이다.

즉, kw는 다음처럼 GET방식으로 전달되어야 index함수에서 읽을 수 있다.

http://localhost:5000/?kw=파이썬&page=1

kw를 POST로 전달하는 방법은 추천하고 싶지 않다. 왜냐하면 kw를 POST 방식으로 전달하면 page 역시 POST 방식으로 전달해야 하기 때문이다.

kw는 POST 방식으로 전달하면서 page는 GET 방식으로 전달하는 방법은 없다.

또한 POST 방식으로 검색, 페이징 기능을 만들면 웹 브라우저에서 "새로고침" 또는 "뒤로가기"를 했을 때 "만료된 페이지" 오류를 종종 만난다. POST 방식은 같은 POST 요청이 발생하면 중복을 방지하기 때문이다. 예를 들어 2페이지에서 3페이지로 갔다가 "뒤로가기"를 하면 2페이지로 갈 때 "만료된 페이지" 오류를 만날 수 있다. 이러한 이유로 게시판을 조회하는 목록 함수는 GET 방식을 사용해야 한다.

그러면 본격적으로 검색 기능을 만들어 보자.
```



##### archive의 경우, 정렬/필터링이 아니라, db없이 동적으로 만드는 상위entity id개념으로서 path_variable을 썼다. -> where로 필터링하는 것처럼 보이지만, 가상부모id로 조회이며, breadcrumb에도 쓰인다.

```python
@main_bp.route('/category/<string:date>')
def archive(date):
```



##### search 관련 내용 설명

- [Question-User + Answer-User + outerjoin.distinct 답글 포함해서 검색 pybo](https://wikidocs.net/81067)

- [Post-User + Reply-User +  + outerjoin.distinct 플라스크로 만드는 blog](https://wikidocs.net/106743)

  ```python
  kw = request.args.get('kw', type=str, default='')  # 검색어
  
  # 검색
  search = '%%{}%%'.format(kw)
  sub_query = db.session.query(Answer.question_id, Answer.content, User.username)\
      .join(User, Answer.user_id == User.id).subquery()
  question_list = Question.query\
      .join(User)\
      .outerjoin(sub_query, sub_query.c.question_id == Question.id)\
      .filter(Question.subject.ilike(search) |      # 질문제목
              Question.content.ilike(search) |      # 질문내용
              User.username.ilike(search) |         # 질문작성자
              sub_query.c.content.ilike(search) |   # 답변내용
              sub_query.c.username.ilike(search)    # 답변작성자
              )\
      .distinct()
  ```

  ```python
  	search = request.args.get('search', type=str, default='')  
      
  	if search != '':        
          search_word = '%%{}%%'.format(search)
  
          sub_query = db.session.query(Reply.post_id, Reply.body, User.username)\
              .join(User, Reply.author_id == User.id).subquery()
          post_list = Post.query\
              .join(User)\
              .outerjoin(sub_query, sub_query.c.post_id == Post.id)\
              .filter(Post.subject.ilike(search_word) |       # 글제목
                      Post.body.ilike(search_word) |          # 글내용
                      User.username.ilike(search_word) |      # 작성자
                      sub_query.c.body.ilike(search_word) |   # 답변내용
                      sub_query.c.username.ilike(search_word) # 답변작성자
                      )\
              .distinct()
  ```

  - SQLAlchemy의 query 객체의 filter 메소드를 통해 **LIKE**나 **ILIKE(case sensitive LIKE)** 쿼리

    ```python
    with engine_session_scope() as session:
        query = session.query(TblUsers).filter(
            or_(
                TblUsers.name.like('jo%'), # name이 'jo', 'Jo', 'jO', 'JO'로 시작하는 경우
                TblUsers.name.ilike('Kim%') # name이 'Kim'으로 시작하는 경우
            )
        )
    ```

    

##### main search route

- **search.html에 현재 검색된 단어의 표기 및 breadcrumb를 위해? word도 같이 넘겨준다**

```python
@main_bp.route('/search')
def search():
    page = request.args.get('page', 1, type=int)
    word = request.args.get('word', '', type=str)
    
    # breadcrumb를 위해 들어온 순수 word와 별개의 변수로 정의
    search_word = f'%{word}%'
    stmt = (
        select(Post)
        .where(or_(
            Post.title.like(search_word),
            Post.content.like(search_word),
        ))
    )
    pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    return render_template('main/search.html', post_list=post_list, pagination=pagination, word=word)

```



#####  main / search.html

![image-20221125034708447](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221125034708447.png)

##### front - 54_search_extends_category_after_search_route.html

```html
{% extends 'main/category.html' %}

{% block title %}{{ words }} 검색결과 {% endblock title %}

{% block hero %}{% endblock hero %}

{% block breadcrumb %}
    <nav class="breadcrumb is-small" aria-label="breadcrumbs">
        <ul>
            <li><a href="/">Home</a></li>
            <li class="is-active"><a href="#" aria-current="page">{{ word }} 검색결과</a></li>
        </ul>
    </nav>
{% endblock breadcrumb %}

{% block pagination %}
    <nav class="pagination is-small" role="navigation" aria-label="pagination">
        {% if pagination.has_prev %}
            <a href="{{ url_for('blog.search') }}?page={{ pagination.prev_num }}&words={{ words }}" class="pagination-previous" title="This is the first page">Previous</a>
        {% endif %}
        {% if pagination.has_next %}
            <a href="{{ url_for('blog.search') }}?page={{ pagination.next_num }}&words={{ words }}" class="pagination-next">Next page</a>
        {% endif %}

        <ul class="pagination-list">        
            {% for page in pagination.iter_pages() %}
                {% if page %} 
                    {% if page != pagination.page %}
                        <li>
                            <a href="{{ url_for('blog.search') }}?page={{ page }}&words={{ words }}" class="pagination-link" aria-label="Page 1" aria-current="page">{{ page }}</a>
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
```



- test

  `http://localhost:5000/main/search?word=글`



##### front - 55_category_change_after_search.html

- 검색 html은 다음과 같이 구성한다
- category.html이라는 post_list를 뿌려주는 화면 안에
  - .box태그
    - h1태그
    - .dropdown-divider 태그
    - **form태그 method="get" action="검색라우터"** -> `get form은 쿼리스트링으로 날아간다`
      - .field태그
        - .control태그
          - input태그 **type="search"** value="(쿼리스트링value)" **name="쿼리스트링key"**
        - .control태그
          - input태그 type="submit"

```html
<!-- 검색 -->
<div class="box is-shadowless" style="border:solid 1px #eee ;">
    <h1 class="is-size-6 icon-text">
        <span class="icon"><i class="mdi mdi-search-web"></i></span>
        검색
    </h1>
    <div class=" dropdown-divider"></div>
    <form action="{{url_for('main.search')}}" method="get">
        <div class="field has-addons">
            <div class="control">
                <input class="input" type="search" value="{{word}}" name="word" placeholder="검색keyword 입력">
            </div>
            <div class="control">
                <input type="submit" value="Search" class="button is-info">
            </div>
        </div>
    </form>
</div>

```







#### 참고) post_detail에 markdown-css 적용하기

- main/post_detail.html

  - github markdown css주기

    ```python
    {% extends 'main/category.html' %}
    
    {% block extra_head_style %}
    <link
      rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown-light.min.css"
      integrity="sha512-zb2pp+R+czM7GAemdSUQt6jFmr3qCo6ikvBgVU6F5GvwEDR0C2sefFiPEJ9QUpmAKdD5EqDUdNRtbOYnbF/eyQ=="
      crossorigin="anonymous"
      referrerpolicy="no-referrer"
    />
    {% endblock extra_head_style %}
    ```

  - css가 정의한 css class를 post.context를 구성하는 div에 걸어주기

    ```html
    <!-- markdown 적용예정인 필드는 |safe를 달아준다.   -->
    <!--        <div class="content has-text-grey mt-1 ">{{ post.content | safe }}</div>-->
    <div class="markdown-body mt-1">{{ post.content | safe }}</div>
    ```

    

  

