## main-front개발 for banner buetify + materialicon

### 설정



#### template 다운로드

- https://github.com/LiuShiYa-github/FlaskBlog/tree/master/app/blog/static

  - css: 기존 코멘트/menu/navbar와 해깔릴 수 있으니 `main폴더`를 팜

    ![image-20221110144522731](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110144522731.png)

  - js: 

    ![image-20221110172145485](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110172145485.png)

  

#### bp 개설 및 static 관련 설정을 Blueprint에 걸어주기 -> cancel

- 기존: main/config/app.py에서

  - `app`객체에 옵션으로 걸어줬었고, bp등록 따로했었음

    ![image-20221110144723335](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110144723335.png)

- **변경: **

  1. main> routes> main_route.py 생성 및 init에 걸어주기

  2. **static folder, template folder`bp`객체에 걸어주고**

     ![image-20221110145647877](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110145647877.png)

  3. **일단 templates에 하위 main을 만들어서 걸어주기**

     ![image-20221110145912119](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110145912119.png)

  3. main>config>app.py에는 bp만 등록

     ![image-20221110145813519](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110145813519.png)





#### templates/main폴더 생성 -> 기존을 templates/menu폴더 생성하여 옮기기

1. index.html 생성해서 route에서 render해서 경로잡히나 확인하기

   ![image-20221110150136928](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110150136928.png)

2. `flask run` or `python run.py`

   - 기존 app객체에 걸어둔 경로를 해당bp가 덮어쓰기 못해서 에러난다

3. 기존 api_route.py도 직접 bp에 static경로(main빼고) 걸어주고, app객체에 등록은 삭제하자

   ![image-20221110150540646](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110150540646.png)

   ![image-20221110150606367](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110150606367.png)



4. **html이름을 상위폴더와 겹치면 그쪽으로 가는 경향이 있음.**

   - template경로가 bp마다 달라도, 등록된 상위를 먼저 찾는 경향이 있다.

   ![image-20221110151438183](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110151438183.png)

   - 예제 코드도 모두 templates에 직접 폴더명을 붙이고, 경로는 통일 된 것으로 한다.

     ![image-20221110152156724](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110152156724.png)

5. **다른 bp or app객체에 template경로가 한번이라도 상위가 등록되면, 상위것을 우선으로 탐색하게 된다.**

   - 기존 api_route.py를 상위 template폴더 경로 등록안하면

     ![image-20221110153234217](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110153234217.png)

   - **main의 index.html을 잘 찾아간다**

     ![image-20221110153300910](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110153300910.png)

   - 다른route에서 상위template경로를 자신의 것만 등록해도

     ![image-20221110153334699](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110153334699.png)

   - 같은 주소로 접속해도, **상위의 index를 찾아가버린다.(상위가 아니라 먼저 등록된 template_folder의 html 우선 탐색된다**

     ![image-20221110153407891](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110153407891.png)

   - **상위가 아니라 app객체에 먼저 등록된 친구가 우선 적용**된다. 등록 순서를 바꾸면, **먼저 등록된 html을 먼저 찾아간다.**

     ![image-20221110154629748](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110154629748.png)

     ![image-20221110154704721](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110154704721.png)



##### template경로 지정 결론: render_template은 bp별 따로 등록하더라도, 먼저 등록된 폴더에 같은 html을 먼저 찾아가버리니, static/template경로를 app객체에 통일하고 render_template시 /하위폴더/.index.html로 하자.

1. main/config/app.py에 static과 templates folder 등록

   ![image-20221110155016272](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110155016272.png)

2. **bp별 구분은 static / template 하위폴더에 직접하고 `경로등록X`**

   ![image-20221110155054888](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110155054888.png)

3. **render_template시, 등록된 경로 + `하위폴더/` + `파일명`**으로 렌더링하자.

   ![image-20221110155224762](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110155224762.png)

4. 기존 코멘트/메뉴 관련 html들도 **앞에 하위폴더명을 적어줘야한다**

   ![image-20221110155508712](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110155508712.png)

5. **jinja의 extends 역시 기본template_folder기반이므로 `폴더명/`을 달아줘야한다.**

   ![image-20221110155906977](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110155906977.png)

   ![image-20221110155918250](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110155918250.png)



6. 이럴거면 진짜 main은 상위temtemplate폴더를 쓰고, 하위부터 render시 폴더명/지정해주는게 좋을 것 같다.??





#### bp마다 url_prefix=가 다 지정될 경우, url `/`는 app객체에 add_url_rule() + route func(view_func) 지정해준다.

1. 나는 api_routes.py 속에 menu route function을 `/`로 지정해주고 싶어서

2. routes>init.py에 해당 route function을 import시키고

   ```python
   from .api_route import api_routes_bp, menu
   from .main_route import main_bp
   ```

3. config>app.py에 해당 menu function을 view_func으로 지정해줬다

   ```python
   from src.main.routes import api_routes_bp, menu
   app.register_blueprint(api_routes_bp)
   # 기본 / url 지정 in route.py의 function
   app.add_url_rule('/', endpoint='index', view_func=menu)
   
   ```

   - 예제에서는 해당route.py를 import해서..py.bp 를 등록 py.route_function을 등록하더라

     ![image-20221110161242546](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110161242546.png)

     ![image-20221110161302610](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110161302610.png)

### 소스코드 적용

#### main/index.html

##### urlfor 주석처리한  뒤 vscode에서 확인해본다

- main/index.html에 붙여넣는다.
- `code .` 이후 live로 index.html을 연다

```html
<!DOCTYPE html>
<html lang="cn">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock title %}</title>
<!--    <link rel="stylesheet" href="{{ url_for('static', filename='css/main/style.css') }}">-->
<!--    <link rel="stylesheet" href="{{ url_for('static', filename='css/main/buefy.min.css') }}">-->
<!--    <link rel="stylesheet" href="{{ url_for('static', filename='css/main/materialdesignicons.min.css') }}">-->
    {% block extra_head_style %}{% endblock extra_head_style %}
</head>

<body>
    <div id="app" style="height:100%;">
        <div class="container is-fluid1" style="height:100%; ">
            <div class="is-block" style="height:100%;">
                <!-- 导航 -->
                {% block navbar %}
                <template>
                    <b-navbar spaced shadow>
                        <template #brand>
                            <b-navbar-item>
<!--                                <img src="{{ url_for('blog.static', filename='img/logo.png') }}" alt="FlaskBlog">-->
                            </b-navbar-item>
                        </template>
                        <template #start>
                            <b-navbar-item href="#">
                                Home
                            </b-navbar-item>
                            <b-navbar-item href="#">
                                Documentation
                            </b-navbar-item>

                            <b-navbar-dropdown label="Info">
                                <b-navbar-item href="#">
                                    About
                                </b-navbar-item>
                                <b-navbar-item href="#">
                                    Contact
                                </b-navbar-item>
                            </b-navbar-dropdown>
                        </template>

                        <template #end>
                            <b-navbar-item tag="div">
                                <div class=" buttons">
                                    <!-- 获取用户信心 -->
                                   <a class="button is-primary">
                                    <strong>
                                        Sign up
                                    </strong>
                                    </a>
                                    <a class="button is-light">
                                        Log in
                                    </a>
                                </div>
                            </b-navbar-item>
                        </template>
                    </b-navbar>
                </template>
                {% endblock navbar %}

                {% block hero %}
                <section class="hero is-medium is-primary">
                    <div class="hero-body">
                        <p class="title">
                            Large hero
                        </p>
                        <p class="subtitle">
                            Large subtitle
                        </p>
                    </div>
                </section>
                {% endblock hero %}

                {% block main %}
                <div class="box is-marginless is-shadowless is-radiusless">
                    <div class="columns is-multiline">
                        {% for post in posts %}
                        <div class="column is-4-fullhd">
                            <div class="card">
                                <div class="card-image">
                                    <figure class="image is-4by3">
                                        <img src="https://bulma.io/images/placeholders/1280x960.png"
                                        alt="Placeholder image">
                                    </figure>
                                </div>
                                <div class="card-content">
                                    <div class="media">
                                        <div class="media-content">
                                            <p class="title is-4"><a href=""> FlaskBlog博客实战</a></p>
                                        </div>
                                    </div>

                                    <div class="content">
                                        <p class="has-text-grey is-size-7">
                                            askjdflkjasldfjaskdflasdf
                                            asdlkfjlasdjflkasdfl
                                        </p>
                                        <time datetime="2022-1-1">11:09 PM - 1 Jan 2022</time>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>

                    <nav class="pagination" role="navigation" aria-label="pagination">
                        <a class="pagination-previous is-disabled" title="This is the first page">Previous</a>
                        <a class="pagination-next">Next page</a>
                        <ul class="pagination-list">
                          <li>
                            <a class="pagination-link is-current" aria-label="Page 1" aria-current="page">1</a>
                          </li>
                          <li>
                            <a class="pagination-link" aria-label="Goto page 2">2</a>
                          </li>
                          <li>
                            <a class="pagination-link" aria-label="Goto page 3">3</a>
                          </li>
                        </ul>
                    </nav>
                </div>
                {% endblock main %}



                {% block footer %}
                <div class="footer has-background-black-ter is-marginless">
                    <div class="has-text-centered has-text-grey-light">
                        © 2022 <a class="has-text-grey-light" href="http://www.lotdoc.cn/blog/topic/detail/6">FlaskBlog博客实战</a> 版权所有 备案号：陕ICP备20005686号
                    </div>
                </div>
                {% endblock footer %}
            </div>

        </div>
    </div>
    
<!--<script src="{{url_for('static', filename='js/main/vue.js')}}"></script>-->
<!--    <script src="{{url_for('static', filename='js/main/buefy.min.js')}}"></script>-->
<!--    {% block extra_foot_script %}{% endblock extra_foot_script %}-->
<!--    <script>-->
<!--        var app = new Vue({-->
<!--            el: '#app',-->
<!--            data: {},-->
<!--            methods: {}-->
<!--        })-->
<!--    </script>
</body>
</html>
```

![image-20221110170805604](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110170805604.png)



##### url_for로 static + css/main 적용하기 in 파이참

1. url_for는 `bp.route_func`으로 입력하는데, **`'static'`은 기본으로 명시되는 static폴더경로의 route func이다.**

   - 예시에는 `bp객체.static`로 지정해줫찌만 **나는 bp별로 static지정을 안하므로 'static'으로 명시해주며 `filename=에 `하위폴더/파일명`으로 직접 지정해주기로 했다**

   ```html
   <link rel="stylesheet" href="{{ url_for('static', filename='css/main/style.css') }}">
   <link rel="stylesheet" href="{{ url_for('static', filename='css/main/buefy.min.css') }}">
   <link rel="stylesheet" href="{{ url_for('static', filename='css/main/materialdesignicons.min.css') }}">
   ```

2. img src에 있는 url도 마찬가지로 적용해준다.

   ```html
   <img src="{{ url_for('static', filename='img/main/logo.png') }}" alt="FlaskBlog">
   ```

3. **static폴더마다 css/js/img폴더에 main폴더들을 확인하고 없는 것을 만들어서 넣어준다.**

4. style.css적용 확인을 위해 bg를 바꿔서 확인해본다.

   ```css
   html, body{
       height: 100%;
       /*background-color: rgb(235, 235, 235) !important;*/
       background-color: red !important;
   }
   ```

   ![image-20221110172611417](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110172611417.png)

- vuejs로 navbar를 랜더링해야 메뉴가 보이게 될 것이다.

##### url_for로 static + js/main 적용하기 in 파이참

- `</body>` 직전에 `vue.js`, `buefy.min.js` 를 걸어주고 **new Vue를 생성해주는 script를 생성해준다.**

  - 해당 주석을 풀어준다.

  ```html
  <script src="{{url_for('static', filename='js/main/vue.js}}'"></script>
  <script src="{{url_for('static', filename='js/main/buefy.min.js}}'"></script>
  {% block extra_fooot_script %}{% endblock extra_fooot_script %}
  <script>
      var app = new Vue({
          el: '#app',
          data: {},
          methods: {}
      })
  </script>
  ```

  ![image-20221110173846514](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110173846514.png)





#### route에서 가상 for post in posts의 횟수만 돌아가도록 list 전달하기

- 현재 posts가 넘어와서 반복문이 돌아야 card들이 보이게 되어있따.

  ![image-20221110174423461](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110174423461.png)

  

1. main route에 posts를 반복문돌아가도록 숫자list를 넣어서 전달

   ```python
   from flask import Blueprint, render_template
   
   
   main_bp = Blueprint("main", __name__, url_prefix='/main')
   
   
   @main_bp.route("/")
   def index():
       posts = [1, 2, 3, 4, 5, 6]
       return render_template('main/index.html', posts=posts)
   
   ```

   ![image-20221110175111656](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110175111656.png)







### main - db 설계

- [DB 7번 강의](https://www.youtube.com/watch?v=GWol-cBSImw&list=PLMm5BkIsXbts7z8ayoEMO_U3hmf5urqXz&index=7)
- [db추가 방법 내 블로그](https://blog.chojaeseong.com/python/cleanpython/project/infra/orm/database/entities/models/2022/10/14/cp03_sqlalchemy%EB%A5%BC-%ED%86%B5%ED%95%9C-infra(DB)-%EC%82%AC%EC%9A%A9-%EC%84%B8%ED%8C%85.html#05-%ED%95%99%EC%8A%B5%EC%9A%A9-db-%EB%B0%8F-%EB%AA%A8%EB%8D%B8-%EC%B6%94%EA%B0%80)

1. tutorial03에 `categories.py` 추가

2. base import해서 정의

3. onupdate = 생성시 자동시간추가(default, server_default)외에 **데이터 수정시 자동 시간 업뎃**옵션이다

   - [한국설명블로그](https://hooni-playground.com/2229/)

   ```python
   from src.infra.config.base import Base
   from src.infra.config.connection import DBConnectionHandler
   
   
   class Category(Base):
       __tablename__ = 'categories'
       id = Column(Integer, primary_key=True)
       name = Column(String(128), nullable=False)
       icon = Column(String(128), nullable=True)
       add_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
       pub_date = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
   
   
       def __repr__(self):
           info: str = f"{self.__class__.__name__}" \
                       f"[name={self.name!r}]"
           return info
   
   ```

4. **init에만 올리면**

   ```python
   from .comments import Comment
   from .menus import Menu
   from .notices import Notice
   from .categories import Category
   
   ```

5. create_database.py에서 알아서 **import ***로 들어간다

   ![image-20221110223909593](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110223909593.png)

#### 설정(나와다른) 예비 보관

![image-20221110223510677](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110223510677.png)

![image-20221110223714862](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110223714862.png)





#### flask shell로 DB-TABLE생성 및 데이터 생성  - main.py에서 하던 것을 shell에서 해보기

- Entity.query가 아닌 sqlalchemy 의 select 등을 다 쓰려면 import할게 많아져서 안좋을 듯

1. **환경변수 설정**

   ```powershell
   $env:FLASK_APP = 'run.py' # set ~ =run.py
   $env:FLASK_ENV = 'development' # set ~ =de~
   flask shell
   ```

2. **FLASK_APP은 `app객체가 init에 떠있는 package이름`을 root이후 폴더부터 명시해도 된다.**

   ```powershell
   $env:FLASK_APP = "src/main/config"
   $env:FLASK_ENV = "development"
   flask shell
   ```

   ![image-20221110225207408](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110225207408.png)

3. `from create_database_tutorial3 import *` 로 **model들 + Session[()]클래스 + create_database[(truncate=True, drop_table=False)] method** 일괄 import

   ```python
    from create_database_tutorial3 import * 
   ```

   

4. `create_database()`메서드로 기존table 보존 + **새롭게 연결된 entity에 대해 db를 생성할 수 있다.**

   ```python
   create_database()
   ```

   - flask라면 `db.create_all()`

#### BaseModel 추상Entity 설계

![image-20221110225647494](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110225647494.png)

- category와 post의 날짜들 등 중복되는 칼럼들을 가진 table정의
- 특정 entity위에서 작성해주고 나중에 entity폴더 > common > base.py로 옮길예정

1. **class BaseModel** 추상entity 생성

   ```python
   class BaseModel(Base):
       __abstract__ = True
       
       add_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
       pub_date = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
   
   
   
   class Category(Base):
       __tablename__ = 'categories'
   ```

   

2. category는 상속하고나서 중복칼럼 제거

   ```python
   class Category(BaseModel):
       __tablename__ = 'categories'
   
       id = Column(Integer, primary_key=True)
       name = Column(String(128), nullable=False)
       icon = Column(String(128), nullable=True)
   
       def __repr__(self):
           info: str = f"{self.__class__.__name__}" \
                       f"[name={self.name!r}]"
           return info
   ```

3. **파이참 F6으로 base.py로 빼서 자동move**

   ```python
   from src.infra.tutorial3.common.base import BaseModel
   
   class Category(BaseModel):
   ```

   

#### Post EntityModel 생성

1. 일단 Cateogory.py에 같이 생성한다.

   - **관계있는 테이블 작성시 같이 일단 작성한다.**

2. content 부분만 Text -> Mysql의 지정의 경우 자체 LONGTEXT를 가져올수도있다.

   ![image-20221110230919416](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110230919416.png)

   ![image-20221110231006913](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110231006913.png)

   ```python
   class Post(BaseModel):
       __tablename__ = 'posts'
   
       id = Column(Integer, primary_key=True)
       title = Column(String(128), nullable=False)
       desc = Column(String(200), nullable=False)
       content = Column(Text, nullable=False)
   
       def __repr__(self):
           info: str = f"{self.__class__.__name__}" \
                       f"[title={self.title!r}]"
           return info
   ```

   

#### Tag entitymodel 생성

- 역시 같은 곳에 몰아서 만든다.
- **Tag같은 경우 id가 아닌 name으로 검색을 자주할 것이므로 id대체검색이 가능한 unique=True로 주고 만든다.**

```python
class Tag(BaseModel):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[name={self.name!r}]"
        return info
```



#### 관계 설정

##### cate-post의 1 대 다

1. 1(Category)에서 relation칼럼을 만들고 backref를 ~~lazy로 준다~~
    - **내가 속한 post들을 불러올 땐, lazy로 주고**
    - **post들이 나를 상위로 부를 땐 `조회하면서 바로 post.category.name`을 `view에서 조회`가능하도록 `backref(, lazy='subqeury')`로 준다**

   ```python
   posts = relationship('Post', backref=backref('category', lazy='subquery'), lazy=True)

   ```

   

2. 다(Post)에서 Integer칼럼을 FK옵션을 줘서, nullable=False로 만든다

   ```python
   category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
   ```



##### post-tag의 다 대 다

1. **`기준 Post 위에` 다대다는 class가 아닌 관계테이블 Table객체로 만든다.**

   - Base상속대신, 2번째인자로 Base.metadata가 들어간다.
   - **다대다 관계 테이블에선 `자신의 id는 필요없고, 각 테이블에 대한 fk를 primary_key=True`로 정의한다**

   ```python
   posttags = Table('posttags', Base.metadata,
                    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
                    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
                   )
   
   class Post(BaseModel):
   ```

2. **둘 중에 1개의 테이블에만** **나머지 상대방테이블에 대한 relationship을 준다.**

   - **이 때, `secondary=관계테이블`을 지정해주고**

   - **기준테이블(Post)의 관계칼럼은 lazy는  subquery로 줘서 불러올때 바로** 다들고오게 joined되게 한다?

   - **상대방(Tag)에는 backref객체로 lazy=True를 줘서 `select`로 `추가조건 없이 바로 들고오게` 한다?**

     - 참고
       - lazy=True -> select -> **바로 객체들 다 가져옴(불러오고 더이상 쿼리없을 때)**
       - lazy=False -> joined -> join으로 가져옴
       - lazy=subquery -> 서브쿼리로 가져옴
       - dynamic -> **바로 객체들이 아닌 한번 더 호출해야 객체를 가져옴(이것의 이점은 filter/filter_by, order_by 등과 같은 메소드를 사용하여 원하는 것을 반환하기 위해 더 쿼리할 수 있다는 것)**
         - With SQLAlchemy version 1.4 `lazy=dynamic` is now considered legacy feature.

     ```python
     tags = relationship('Tag', secondary=posttags,
                         lazy='subquery',
                         backref=backref('posts', lazy=True)
                        )
     
     ```

     ![image-20221111021453478](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111021453478.png)





#### post 에 초안/완성여부 enum필드 등록하기

- 단순이넘 상속 말고 IntEnum을 사용해본다.
- **기본적으로 server_default로  `enum의 필드를 문자열`로 지정해서 줄 수 있다.**

```python
class PostPublishType(IntEnum):
    draft = 1 # 초안
    show = 2 # release

    
class Post(BaseModel):
    #...
    has_type = Column(Enum(PostPublishType), server_default='show', nullable=False)

```



- 필드만 추가한다고 해서 **create_all은 정상 작동하지만, 필드변화는 없다**
  - alembic migration을 담에 하든지
  - 기존데이터를 백업하고 drop_table=True를 한뒤 만들어야한다.



#### init에 entity class 1개씩 다올리기

- Base로 연결된 테이블들은 create_all()은 알아서 먹을텐데..

- init에 올려야 -> db_creator -> create_database -> main.py에서 사용이 자유롭다

  - 안올리면, flask shell, 이나 main에서 

    - **`from create_database_tutorial3 import *`을 통해 모든 `모델 다CRUD 쓰기`가 안됨**

    ![image-20221111022936505](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111022936505.png)

- **init에는 지금 category.py에 몰빵한 것들 다 올리기**

  ```python
  from .comments import Comment
  from .menus import Menu
  from .notices import Notice
  from .categories import Category, Post, PostPublishType, posttags, Tag 
  ```



### main - 설계db의 데이터 생성하기

#### shell에서 table 및 data 생성하기

- main.py에서 안하면, 코드 -> 초기화시 초기데이터로 이전 가능한 것이 안남는 단점

```powershell
$env:FLASK_APP = 'run.py' # set ~ =run.py
$env:FLASK_ENV = 'development' # set ~ =de~
flask shell
```

```powershell
>>> from create_database_tutorial3 import *
>>> session = Session()
>>> create_database()
>>> cates = ['분류2', '분류3', '분류4']
>>> for name in cates:
...     cate = Category(name=name)
...     session.add(cate)
...     session.commit()
```







### auth - db 설계

- entity패키지에 `auth`패키지를 따로 파주자

  ![image-20221111224846452](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111224846452.png)

- routes패키지 `auth_route.py`도 따로 생성해주자

  ![image-20221111224857798](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111224857798.png)



#### User Entity 정의

- baseModel 상속(add_date, pub_date필드)

  - **entity정의시 Base객체가 필요없어진다?!**

- username을 원래는.. 중복되어야할텐데, 여기선 일단 unique=True를 준다.

- password는 320자 제한, avatar는 nullable=True

- **is~ Boolean필드들은 `default=`를 주는 `nullable=True`를 준다.**

  - is_active는 생성시부터 True로 들어간다.
  - is_super_user, is_staff는 **default False로 주고, 해당하는 경우 True를 줄 예정**
  - is_staff는 백그라운드 로그인 허용여부를 의미한다?!

  

```python
from sqlalchemy import Column, Integer, String, Boolean

from src.infra.tutorial3.common.base import BaseModel
from src.infra.config.base import Base


class User(BaseModel):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    password = Column(String(320), nullable=False)
    avatar = Column(String(200), nullable=True)
    is_super_user = Column(Boolean, nullable=True, default=False)
    is_active = Column(Boolean, nullable=True, default=True)
    is_staff = Column(Boolean, nullable=True, default=False)

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[id={self.id!r}]"
        return info

```



#### 정의한 entity를 auth패키지(외부에서 auth import후 auth.users)-> entities패키지의 init에 순차적으로 올려주기?!

![image-20221111230154562](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111230154562.png)

```python
# auth init.py
from .users import User
```

```python
# entities init.py
from .comments import Comment
from .menus import Menu
from .notices import Notice
from .categories import Category, Post, PostPublishType, posttags, Tag
#from .auth import User
#import auth
#init에 올라가있는 것을 package.으로 사용해야하니..
#1) import auth.users를 하든지
#2) from .auth import users를 해야한다.
from .auth import User
```



- **create_database.py도 수정**

  - **init에 올려두는 이유 -> `외부에서 해당 패키지를 마지막으로 import package -> pacagek.xxx로 쓰기`위해서**
  - **바로 쓰려면 `외부에서 from 패키지 import *` 이 맞다**

  ```python
  # create_database.py
  
  import datetime
  
  from src.infra.config.db_creator import create_db, Session
  #from src.infra import tutorial3
  from src.infra.tutorial3 import *
  
  
  
  def _load_fake_data(session: Session):
  ```

  



- main.py에서 truncate, drop없이 create_all()로 base상 없는 테이블만 자동생성



### auth - routes 및 templates 동시 설계

1. bp부터 만든다

   ```python
   from flask import Blueprint, render_template
   
   
   auth_bp = Blueprint("auth", __name__, url_prefix='/auth')
   ```

   - 여기선 bp별, template_folder, static_foler 경로를 따로 지정하지 않음.
   - **만든 bp를 routes패키지에 init에 import**

   ```python
   from .api_route import api_routes_bp, menu
   from .main_route import main_bp
   from .auth_route import auth_bp
   ```

   

2. **만든 bp를 app객체에 등록 먼저 해준다.**

   - src>main>config > app.py

   ```python
   #...
   from src.main.routes import auth_bp
   app.register_blueprint(auth_bp)
   #...
   ```



#### (뼈대) form(post)으로 [READ]하는 login.html(get) route + html 개설

1. **src>main>templates>`auth`폴더를 만들고 render할 `login.html` 생성**

   ![image-20221111232003983](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111232003983.png)

2. login route를 만든다

   - **화면에 form이 달린 경우, GET+POST route다**
   - **우리만의 규칙으로 `(templates의)하위폴더/ .html`로 랜더링 해주기로 했다**

   ```python
   from flask import Blueprint, render_template
   
   
   auth_bp = Blueprint("auth", __name__, url_prefix='/auth')
   
   @auth_bp.route('/login', methods=['GET', 'POST'])
   def login():
       
       return render_template('auth/login.html')
   ```

3. **prefix(auth) / route_url로 접속해보기**

   ![image-20221111233011116](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111233011116.png)



#### (뼈대만 있는 login route/html를 복사) form(post)으로 [CREATE]하는 register.html(get)   route 및 html 개설

1. 뼈대 login route 복사해서 register route 생성

   ```python
   @auth_bp.route('/register', methods=['GET', 'POST'])
   def register():
   
       return render_template('auth/register.html')
   ```

   

2. 뼈대 login html복사해서 register.html 생성

   ![image-20221111233434825](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221111233434825.png)





### auth - 화면 설계

#### main의 index를 base로 변경후 templates상위 폴더로 이동하고 main/index를 새로 만들어서 필요한 블락을 채운다?

![image-20221112000704034](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112000704034.png)

![image-20221112000717364](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112000717364.png)

![image-20221112000737976](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112000737976.png)

1. base.html에 대해 `index.html`을 만들어서 **extends만 하면, base.html 그대로 반영된다.**
   - **jinja의 extends는 templates기준**으므로 **main(하위폴더)/base.html**로 지정해줘야하는 문제점이 생긴다

2. **base.html은 어느 하위폴더의 html이든 extends할수 있게 templates폴더**에 바로 두도록 이동한다

   ![image-20221112001459167](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112001459167.png)

3. main의 index.html은 main/base.html이 아닌 base.html을 상속한다

   ```jinja2
   # index.html
   {% extends 'base.html' %}
   ```

   

![image-20221112001250976](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112001250976.png)

![image-20221112001239063](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112001239063.png)





#### auth/login.html은 base를 상속하되 base의 `채워진 block`을 `빈block`으로 채워 제거하고 부분을 제거한다

1. login.html에서  base.html을 상속하면서 navbar이후로 block들 중 지울 것(hero..)을 확인한다.

   ![image-20221112002518698](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112002518698.png)

   ```jinja2
   {% extends 'base.html' %}
   
   {% block hero %} {% endblock hero %}
   ```

   ![image-20221112002308306](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112002308306.png)





##### base의 main블락을 (base의 posts순회) 말고 원하는 것으로 채워넣기

#### front - login.html

```html
{% extends 'base.html' %}

<!--logo block 빈값으로 채워 제거-->
{% block hero %} {% endblock hero %}

{% block main %}
<div class="box is-radiusless is-marginless" style="height: 80%;">
    <div class="columns is-centered">
        <div class="column is-5-fullhd">
            {% block auth_form %}
            <form action="" method="post" style="margin-top: 40%;" class="box">
                <div class="has-text-centered mb-3">
                    <p class="subtitle">Login</p>
                    <h1 class="title">FlaskBlog</h1>
                </div>
                <!-- xxx form.csrf_token -->
                <!-- message flash -->
                {% with messages = get_flashed_messages() %}
                <b-message type="is-danger">
                    {% if messages %}
                    <ul class=flashes>
                        {% for message in messages %}
                        <li>{{ message }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </b-message>
                {% endwith %}

                <!-- form validation -->
                <!--             xxx if form.username.errors -->
                <!--            <b-message type="is-danger">-->
                <!--              <ul class="errors">-->
                <!--                xxx for error in form.username.errors -->
                <!--                <li>{{ error }}</li>-->
                <!--                xxx endfor-->
                <!--              </ul>-->
                <!--            </b-message>-->
                <!--            xxx endif-->

                <div class="field">
                    <p class="control has-icons-left has-icons-right">
                        <input class="input" type="text" name="username" id="id_username"
                               maxlength="128" placeholder="Username"
                        >
                        <!--                xxx form.username(class='input', placeholder='Username')-->
                        <span class="icon is-small is-left">
                  <i class="fas fa-envelope"></i>
                </span>
                        <span class="icon is-small is-right">
                  <i class="fas fa-check"></i>
                </span>
                    </p>
                </div>
                <div class="field">
                    <p class="control has-icons-left">
                        <!--                xxx form.password(class='input', placeholder='Password')-->
                        <input class="input" type="password" name="password" id="id_password"
                               maxlength="320" placeholder="Password"
                        >
                        <span class="icon is-small is-left">
                  <i class="fas fa-lock"></i>
                </span>
                    </p>
                </div>
                <div class="field">
                    <p class="control">
                        <input class="button is-success is-fullwidth" type="submit" value="Login">
                    </p>
                </div>
            </form>
            {% endblock auth_form %}
        </div>
    </div>
</div>
{% endblock main %}
```



### auth - route <-> 화면 동시설계

#### 01 일반form의 nam속성 찍어보기 request.form.get("name속성")

1. login route에서 post로 받아 **고정된 `비flask wft` form의 name속성을 받아서 찍어본다.**

   ![image-20221112005613517](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112005613517.png)

   ```python
   @auth_bp.route('/login', methods=['GET', 'POST'])
   def login():
       if request.method == 'POST':
           username = request.form.get('username')
           password = request.form.get('password')
           print(username, password)
   
       return render_template('auth/login.html')
   ```

   ![image-20221112005831858](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112005831858.png)

   ![image-20221112005931566](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112005931566.png)





####  02 일반form login -> unique인 username로 데이터를 조회시도하여, [조회 데이터가 없으면 flash]

```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with DBConnectionHandler() as db:
            user = db.session.scalars(
                select(User)
                .where(User.username == username)
            ).first()
        if user:
            pass
        else:
            flash("해당 사용자가 존재하지 않습니다.")

    return render_template('auth/login.html')

```

![image-20221112021703021](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112021703021.png)



#### 03 일반form register -> unique인 username로 데이터를 생성시도하여, [이미 존재하면 flash] + [존재하지 않을 때, 해당정보로 객체생성 -> add로 데이터 생성]



##### user 존재 검사

- login flash작성코드를 전체복사해와서 수정한다.

- **register시에는 password이외에 `password1` name속성이 추가되서 날라오니 받아주자.**

  ```python
  @auth_bp.route('/register', methods=['GET', 'POST'])
  def register():
      if request.method == 'POST':
          username = request.form.get('username')
          password = request.form.get('password')
          password1 = request.form.get('password1')
  
          with DBConnectionHandler() as db:
              user = db.session.scalars(
                  select(User)
                  .where(User.username == username)
              ).first()
  
          if user:
              flash("해당 username의 사용자가 이미 존재합니다.")
          else:
              # User(username=username, password=password, password1=???)
              pass
  
      return render_template('auth/register.html')
  ```

  

- **User객체 생성할려고 보니, password password1로 hash해야한다.**



##### password해쉬: register 고정form에서 날라오는 password Hash하기

- `check_password_hash`, `generate_password_hash` 2개 메서드가 필요하다

- **User객체 생성시 `generate_password_hash()`로 password값을 묶어서 import시도한다.**

  ![image-20221112022836452](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112022836452.png)



##### password일치검사: password1으로 먼저 비교부터 [다르면 flash + return redirect로 밑의 다른 검사로 못가게 막기] 

- url_for는 `'bp_url_prefix. view_func'`의 문자열을 입력한다.

```python
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password1 = request.form.get('password1')

        # 비밀번호 2개 비교
        if password != password1:
            flash('비밀번호가 서로 다릅니다.')
            return redirect(url_for('auth.register'))


        with DBConnectionHandler() as db:
            user = db.session.scalars(
                select(User)
                .where(User.username == username)
            ).first()

        if user:
            flash("해당 username의 사용자가 이미 존재합니다.")
            return redirect(url_for('auth.register'))

        # User(username=username, password=password, password1=???)
        User(username=username, password=generate_password_hash(password))
            

    return render_template('auth/register.html')
```



##### 다 통과시 User생성 + pass일치검사 밑  user존재유무검사를 확인하기 위해 return rediect는 임시 주석처리

```python
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password1 = request.form.get('password1')

        # 비밀번호 일치 검사
        if password != password1:
            flash('비밀번호가 서로 다릅니다.')
            # return redirect(url_for('auth.register'))

        with DBConnectionHandler() as db:
            user = db.session.scalars(
                select(User)
                .where(User.username == username)
            ).first()

        # 이미 유저 존재 검사
        if user:
            flash("해당 username의 사용자가 이미 존재합니다.")
			# return redirect(url_for('auth.register'))

        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

    return render_template('auth/register.html')
```



#### 04 user 생성(register) 성공시 1) 자동 로그인처리를 위해 session.clear()후 session['user_id']에  현재 추가된 user객체의 id 입력 +  2) main으로 redirect

```python
# 이미 유저 존재 검사
if user:
    flash("해당 username의 사용자가 이미 존재합니다.")
    # return redirect(url_for('auth.register'))

user = User(username=username, password=generate_password_hash(password))
db.session.add(user)
db.session.commit()

# 회원가입 성공시, 로그인처리를 위해 session['user_id']에 user객체의 id 등록
session.clear()
session['user_id'] = user.id
return redirect(url_for('main.index'))
```



#### front - register.html : 

- **login.html을 extends**하는 것이 특징이다.

  - **title을 다르게 가져가면서**
  - **extends를 통해 `base상속 + logo(hero)블락제거` + `main block의 div.box > div.columns.is-centerd > div.column.is-5-fullhd`는 챙겨가되 **
    - **상속을 통한 `main block 내부 > auth_form block만 재정의`하는 기법**
  - **form이 담기는 부분(wft_form고려?)의 `auth_form block`을 다른 것으로 채운다.**

  ![image-20221112030421625](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112030421625.png)

```html
{% extends 'auth/login.html' %}

{% block title %}회원가입{% endblock title %}

{% block auth_form %}
<form action="" method="post" style="margin-top: 40%;" class="box">
<!--     xxx form.csrf_token -->
    <div class=" has-text-centered mb-3">
        <p class="subtitle">회원가입</p>
        <h1 class="title">FlaskBlog</h1>
    </div>
     <!-- message flash -->
     {% with messages = get_flashed_messages() %}
     <b-message type="is-danger">
       {% if messages %}
         <ul class=flashes>
         {% for message in messages %}
             <li>{{ message }}</li>
         {% endfor %}
         </ul>
     {% endif %}
     </b-message>
     {% endwith %}

    <div class="field">
        <p class="control has-icons-left has-icons-right">
            <input class="input" type="text" name="username" id="id_username" maxlength="128" placeholder="Username">
            <span class="icon is-small is-left">
                <i class="fas fa-envelope"></i>
            </span>
            <span class="icon is-small is-right">
                <i class="fas fa-check"></i>
            </span>
        </p>
    </div>
    <div class="field">
        <p class="control has-icons-left">
            <input class="input" type="password" name="password" id="id_password" maxlength="320" minlength="6" placeholder="Password">
            <span class="icon is-small is-left">
                <i class="fas fa-lock"></i>
            </span>
        </p>
    </div>
    <div class="field">
        <p class="control has-icons-left">
            <input class="input" type="password" name="password1" id="id_password1" maxlength="320" minlength="6" placeholder="Password1">
            <span class="icon is-small is-left">
                <i class="fas fa-lock"></i>
            </span>
        </p>
    </div>
    <div class="field">
        <p class="control">
            <input class="button is-success is-fullwidth" type="submit" value="Register">
        </p>
    </div>
</form>
{% endblock auth_form %}
```

![image-20221112030850676](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112030850676.png)



##### test해보기 

- 비밀번호는 서로 다르게 입력하면 먼저 검사한다
- **현재 데이터가 없는 상태이므로, user처음에는 등록되고 -> 또 한번 로그인 시도해보면 이미 등록된 것으로 나옴**

![image-20221112031353263](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112031353263.png)

![image-20221112031427056](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112031427056.png)



####  05 (register이후) login 해당user객체 존재시 check_password_hash로 else(if not user)이외에 elif로 [로그인 탈락검사 추가]하기

- check_password_hash( db속 user의password,  넘어온password)를 비교하여 틀리면 로그인 탈락이다.

- **탈락검사가 이어지므로, if not 통과로 탈락검사들을 early return으로 구성해야하지만,  `early return코드가 아직 안된 상태`이므로, ` if탈락검사1 elif탈락검사2 후 마지막 else에 통과상태`를 배치해놓고 확인한다.**

  ```python
  @auth_bp.route('/login', methods=['GET', 'POST'])
  def login():
      if request.method == 'POST':
          username = request.form.get('username')
          password = request.form.get('password')
  
          with DBConnectionHandler() as db:
              user = db.session.scalars(
                  select(User)
                  .where(User.username == username)
              ).first()
          # 1) 해당 유저가 조회안되면 로그인 탈락 검사1
          if not user:
              flash("해당 사용자가 존재하지 않습니다.")
              # ealry return
          # 2) (user는 존재하는데) 해당 유저 비번 vs 넘어온 비번 다르면, 로그인 탈락 검사2
          elif not check_password_hash(user.password, password):
              flash("비밀번호가 다릅니다.")
              # ealry return
          # (user존재, 비번일치)로 통과 -> early return없으니 일단 통과를 else로 처리
          else:
              pass
  
      return render_template('auth/login.html')
  ```

  ![image-20221112161816777](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112161816777.png)

##### 발생안할수도있지만 한번이라도 발생시(flag) 공통처리(not early return - flash+redirect)가 필요한 error상황마다 flash 메세지를 flag로 활용하여, 한번이라도 걸릴시 서로다른message로 공통처리되도록 구성하기

![image-20221112164102266](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112164102266.png)

- **main.index가 기본홈피라서 `/`를 add rule했다면, `url_for`의 `prefix.view_func(main.index)`대신 `redirect('/')`를 main.index로 활용하자.**

```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with DBConnectionHandler() as db:
            user = db.session.scalars(
                select(User)
                .where(User.username == username)
            ).first()
        # 한번이라도 걸릴시 공통된 로직(not early return -> flag, flash+redirect) 탈락검사는 다끝난후 결과값 flag로 에러/성공 처리한다.
        error = None

        # 1) 해당 유저가 조회안되면 로그인 탈락 검사1
        if not user:
            error = "해당 사용자가 존재하지 않습니다."
        # 2) (user는 존재) 해당 유저 비번 vs 넘어온 비번 다르면, 로그인 탈락 검사2
        elif not check_password_hash(user.password, password):
            error = "비밀번호가 다릅니다."

        # 한번도 안걸리면 early return 있는 성공처리부터
        # -> 현재 user.id를 session에 담아주는 것이 로그인 처리
        if not error:
            session.clear()
            session['user_id'] = user.id
            # return redirect(url_for('main.index'))
            return redirect('/')
        # (에러 한번이라도 걸려서 flag에 불들어온 경우) -> flash()만 내주고, 현재 로그인화면으로?
        flash(error)

    return render_template('auth/login.html')
```

![image-20221112165046558](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112165046558.png)

![image-20221112165036957](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112165036957.png)





#### 06 로그아웃 route -> session.clear()만 비워주면 된다.

- **로그인 성공시, 회원가입 성공시, 항상 먼저 `sesion.clear()`부터 하고 넣어줬다.**
  - 이미 로그인된 사람이 있는 상태에서, 옆에 사람이 새롭게 회원가입할 수 도 있으니 예외처리 정도라고 생각하자.



- **로그아웃은 해당라우트로 오면, `session.clear()이후 main.index('/')로 redirect만**

```python
@auth_bp.route('/logout')
def logout():
    session.clear()
    
    return redirect('/')
```



#### 07 session에 로그인된 유저id는 @bp.before_app_request마다 g변수의 g.user에게 User객체로 넘겨주기

- `before_app_request`와 `before_request`의 차이는.. setdefault값을 None으로 self.name으로 주느냐가 다르다.

- **session은 'user_id'에  user객체의 id값만 가지고 있었다면**
- **g는 'user'에 User객체를 요청시마다 들고 있게 한다.**
  - session이 끊어져도 g에 저장되어있으려나?

```python
@auth_bp.before_app_request
def load_logged_in_user():
    # login경험이 없으면, session.user_id는 존재하지 않으니, get으로 꺼낸다
    user_id = session.get('user_id')
    if not user_id:
        g.user = None
    else:
        with DBConnectionHandler() as db:
            g.user = db.session.get(User, user_id)
```

##### logout에서는 session만 날리지만, before_app_request로 인해, 어떠한요청 발생전에 session.user_id None이면, g도 .user객체가 None으로 바로 전환된다.

- logout 라우트에서 session을 날릴 당시에는 g.user에 객체가 살아있지만

  **redirect를 타는 순간, before_app_request에 의해 g.user에도 None으로 채워지게 된다.**

  ![image-20221112172114319](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112172114319.png)







#### 08 front - base.html - auth route g.user 설정 후, b-navbar-item의 회원가입/로그인에 로그아웃반영하기

- 기존 코드 

  ![image-20221112174252973](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112174252973.png)

- 바뀌는 코드

  - **g.user 여부에 따라 `div.buttons`를 다르게 구성한다**



##### front - base_change_b-navar-item_after_guser.html

```html
<b-navbar-item tag="div">
    <!-- g.user if 이름/내 정보/로그아웃 else 회원가입/로그인 -->
    {% if g.user %}
    <div class="buttons">
        <a class="button is-primary">
            {{g.user['username']}}
        </a>
        <a class="button is-success">
            내 정보
        </a>
        <a class="button is-danger" href="{{ url_for('auth.logout')}}">
            로그아웃
        </a>
    </div>
    {% else %}
    <div class=" buttons">
        <a class="button is-primary" href="{{ url_for('auth.register')}}">
                회원가입
        </a>
        <a class="button is-light" href="{{ url_for('auth.login')}}">
                로그인
        </a>
    </div>
    {% endif %}
</b-navbar-item>
```



![image-20221112180857340](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112180857340.png)

![image-20221112180906967](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112180906967.png)





#### 09 login_required 데코레이터 구현 (g.user 구현 > login route/page구현이후) 

- view_func들에게 달아주는 데코레이터로서,
- **실행되기 전에 `g.user에 객체가 없으면 로그인 안된 상태`로 간주하여 login으로 redirect시키는 것을 view_func호출전에 확인한다.**
- **auth_route.py에서 def load_logged_in_user바로 위, 다른route들 앞에 선언해준다.**

```python
def login_required(view_func):
    @functools.wraps(view_func)
    def wrapped_view(**kwargs):
        if not g.user:
            return redirect(url_for('auth.login'))
        return view_func(**kwargs)

    return wrapped_view
```



##### 적용은 다음에





#### 10 wtf-form 설치 및 적용

- 고정된 form에서 데이터를 받는 route들이 모두 사용할 것이다.

- 설치

  ```
  venv\Scripts\activate
  
  
  pip3 install Flask-WTF
  ```

  

- src > main > forms 패키지 생성 > auth 패키지 생성 > **forms.py에 일괄로** 만들자

  ![image-20221112222202041](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112222202041.png)

##### auth > forms.py

- 기본 패키지를 미리 복사해놓는다.

  ```python
  from flask_wtf import FlaskForm
  from wtforms import StringField, PasswordField
  from wtforms.validators import DataRequired, Length, ValidationError, EqualTo
  from werkzeug.security import check_password_hash
  ```

  

#### 11 LoginForm(FlaskForm) -> login route이 고정된 form필드를 확인해서 정의한다

![image-20221112222529316](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221112222529316.png)

- 해당 form필드들 뿐만 아니라 **filters옵션을 넣으면, 한번 변형한 것을 넘길 수 도 있다.**

```python
class LoginForm(FlaskForm):
    # 받은 값을 추가처리하여 route에 건내줄 수 있다.
    # filters=(,)옵션에 함수객체를 튜플로 건네준다.
    #### 메서드명은 상관없으나 파라미터는 self없이 필드1개 고정이다.
    def qs_username(username):
        # u = f'{username}123'
        # print(u)
        return username

    username = StringField('username', validators=[
        DataRequired(message="필수 입력"),
        Length(max=32, message="최대 32글자까지 입력 가능")
    ], filters=(qs_username,))

    password = PasswordField('password', validators=[
        DataRequired(message="필수 입력"),
        Length(max=32, message="최대 32글자까지 입력 가능")
    ])

```

- init에 올린다.





##### login route에서 하던 로그인 탈락검사들 -> forms.py내부 vadidate_id필드(username) 메서드로 이동

- user존재하지 않을시 탈락

- 비밀번호 틀릴 시 탈락

  - **validate_username(form, field)에 정의한다.**

    - 메서드명은 `validate_해당필드()`로 작성하며 인스턴스메서드가 아니라 self는 없다.
    - 파라미터는 고정이다.

  - **해당필드에 대한 error는 jinja에서 `form.해당필드.erros`에 기입된다.**

    - **id필드에 몰아서 검사시키면 된다.**

    ![image-20221113021235469](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113021235469.png)

  ```python
      # 로그인 실패에 대한 validator를 form내부에서 정의
      #### validate_필드명의 method명은 고정이다.
      #### self의 인스턴스메서드로 정의하면 작동안한다 파라미터도 self없이 (form, field) 2개로 고정이다.
      # -  field를 인자로 받아 field.data로 해당 데이터를 쓸 수 있다.
      # -  form.필드명.data로 다른 필드를 사용할 수도 있다.
      # - 넘어오지 않는 name의 필드는 사용할 수없다.
      # - html에서는 특정필드에 대한 에러 {% if form.username.errors %}로 뿌리므로
      #   => id필드에 대해 몰아서 검사하자.
      def validate_username(form, field):
          with DBConnectionHandler() as db:
              # id를 모르니 select문으로
              user = db.session.scalars((
                  select(User)
                  .where(User.username == field.data)
              )).first()
  
          if not user:
              raise ValidationError('해당 사용자가 존재하지 않습니다.')
  
          elif not check_password_hash(user.password, form.password.data):
              raise ValidationError('비밀번호가 틀립니다.')
  
  ```

  

##### login route에서 POST관련처리를 모두 form객체 생성해서 처리 + render시 form객체 전달

```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    ## wtf적용 -> form 내부 validate_xxxx로 로그인 탈락검사 넘김
    form = LoginForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            # id를 모르니 select문으로
            user = db.session.scalars((
                select(User)
                .where(User.username == form.username.data)
            )).first()

        # 이미 custom validator로 존재유무/비번검사가 끝났다고 가정 -> db속 user객체가 무조건 존재하는 상황
        session.clear()
        session['user_id'] = user.id
        return redirect('/')

    return render_template('auth/login.html',
                           form=form)
```





##### front - login_change_after_loginform.html

- 기존 주석된 csrf부분

  ![image-20221113003402989](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113003402989.png)

```html
{{ form.csrf_token }}
```



- 기존 주석된 부분 메세지부분

  ![image-20221113002539333](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113002539333.png)

  ![image-20221113002746506](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113002746506.png)

```html
              <!-- form validation errors -->
                {% if form.username.errors %}
                <b-message type="is-danger">
                    <ul class="errors">
                        {% for error in form.username.errors %}
                        <li>{{ error }}</li>
                        {% endfor %}
                    </ul>
                </b-message>
                {% endif %}
```



- 기존 고정input필드를 form객체가 제공하는 input필드로 대체

  ![image-20221113003139162](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113003139162.png)



```html
 <div class="field">
                    <p class="control has-icons-left has-icons-right">
                        <!--                        <input class="input" type="text" name="username" id="id_username"-->
                        <!--                               maxlength="128" placeholder="Username"-->
                        <!--                        >-->
                        {{ form.username(class='input', placeholder='Username') }}
                        <span class="icon is-small is-left">
                  <i class="fas fa-envelope"></i>
                </span>
                        <span class="icon is-small is-right">
                  <i class="fas fa-check"></i>
                </span>
                    </p>
                </div>
                <div class="field">
                    <p class="control has-icons-left">
                        <!--                        <input class="input" type="password" name="password" id="id_password"-->
                        <!--                               maxlength="320" placeholder="Password"-->
                        <!--                        >-->
                        {{ form.password(class='input', placeholder='Password') }}
                        <span class="icon is-small is-left">
                  <i class="fas fa-lock"></i>
                </span>
                    </p>
                </div>
```



![image-20221113003257646](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113003257646.png)

![image-20221113021516796](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113021516796.png)

![image-20221113021523057](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113021523057.png)



#### 12 RegisterForm

- 역시 username(id필드)를 대상으로 vadliate_username메서드를 만든다.
  - 회원가입 탈락검사는 
    - **db에 이미 존재하면 탈락**으로 1개만  존재한다
  - **비밀번호와 비밀번호1이 다르면 탈락인데, 탈락검사 되기 전에 `form에서 작동하는 validators에 EqualTo`가 적용으로 대체된다** 
- **password1필드가 추가되는데, 여기선 validators를 걸지 않는다.**
  - password와 다르면 탈락이 이미 적용되었다.

```python
class RegisterForm(FlaskForm):
    username = StringField('username', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=32, message="최대 32글자까지 입력 가능")
    ])

    password = PasswordField('password', validators=[
        DataRequired(message="필수 입력"),
        Length(min=2, max=32, message="超过限制字数！"),
        EqualTo('password1', message='최대 32글자까지 입력 가능')
    ])

    password1 = PasswordField('password1')

    def validate_username(form, field):
        with DBConnectionHandler() as db:
            # id를 모르니 select문으로
            user = db.session.scalars((
                select(User)
                .where(User.username == field.data)
            )).first()

        if user:
            raise ValidationError('이미 존재하는 username입니다')
```

- init에 올린다.

```python
from .forms import LoginForm, RegisterForm
```





- route에서는 기존로직을 form객체로 대체하고, form객체를 던져준다.

```python
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            user = User(username=form.username.data, password=generate_password_hash(form.password.data))
            db.session.add(user)
            db.session.commit()
            
        session.clear()
        session['user_id'] = user.id
        
        return redirect('/')
            
    
    return render_template('auth/register.html', form=form)
```



##### register는 password에 대한 validation을 포함하고 있어(EqualTo) error메세지를 다양한 필드에서 뽑아서 보내준다

```python
    form = RegisterForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            user = User(username=form.username.data, password=generate_password_hash(form.password.data))
            db.session.add(user)
            db.session.commit()

        session.clear()
        session['user_id'] = user.id

        return redirect('/')
    
	# form에서 필드별 error -> list로 만든다. 없으면 빈 list를 반환해서 순회안되게 한다
    errors = [{'field': key, 'messages': form.errors[key]} for key in form.errors.keys()] if form.errors else []

    return render_template('auth/register.html', form=form, errors=errors) # errors까지 같이 보낸다.
```





##### front - register_add_after_registerform.html

- 로그인 처럼 

  - csrf 주석을 풀어서 완성하고

  - **로그인에만 존재하던 에러메세지를 플래쉬메세지 <-> `div.field` 사이에 추가해준다.**

    - 기존

      ![image-20221113030319355](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113030319355.png)

  - 고정input필드들을 form으로 만든 input필드로 대체한다.

```html
{{ form.csrf_token }}
```

```html
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

```html
    <div class="field">
        <p class="control has-icons-left has-icons-right">
<!--            <input class="input" type="text" name="username" id="id_username" maxlength="128" placeholder="Username">-->
            {{ form.username(class='input', placeholder='Username') }}
            <span class="icon is-small is-left">
                <i class="fas fa-envelope"></i>
            </span>
            <span class="icon is-small is-right">
                <i class="fas fa-check"></i>
            </span>
        </p>
    </div>
    <div class="field">
        <p class="control has-icons-left">
<!--            <input class="input" type="password" name="password" id="id_password" maxlength="320" minlength="6"                    placeholder="Password">-->
            {{ form.password(class='input', placeholder='Password') }}
            <span class="icon is-small is-left">
                <i class="fas fa-lock"></i>
            </span>
        </p>
    </div>
    <div class="field">
        <p class="control has-icons-left">
<!--            <input class="input" type="password" name="password1" id="id_password1" maxlength="320" minlength="6"                    placeholder="Password1">-->
            {{ form.password1(class='input', placeholder='Password') }}
            <span class="icon is-small is-left">
                <i class="fas fa-lock"></i>
            </span>
        </p>
    </div>
```

![image-20221113151517091](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113151517091.png)

![image-20221113151528822](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113151528822.png)



### admin index 개발 및 login_required 변경

#### 1 admin route 추가 및 index route 개설

- src>main>routes>`admin_route.py` 생성

  ![image-20221113152629667](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113152629667.png)

```python
from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def index():
    return render_template('admin/index.html')
```

- init에 올리고, src>main>config>**app.py에 bp 등록**

```python
from .api_route import api_routes_bp, menu
from .main_route import main_bp, index
from .auth_route import auth_bp
from .admin_route import admin_bp

```

```python
from src.main.routes import admin_bp
app.register_blueprint(admin_bp)
```





#### 2 templates > admin  폴더 만들고 index화면 코드 적용

![image-20221113153129795](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113153129795.png)



#### 3 front - 08_index_extends_base_after_admin.index_route(base boxblock추가).html

- templates > base.html에서
  - post들을 순회하며 뿌려지던 공간인 `div.box`내부를 대체하도록 **box block**을 **base에서 추가 ->  해당 공간을 admin/index.html에서 대체하여 들어간다**

![image-20221113160418236](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113160418236.png)



- 08_index_after_admin.index_route(base mainblock 내부 boxblock추가).html

```html
{% extends 'base.html' %}

{% block title %}
{{ g.user['username'] }}-내 정보
{% endblock title %}

{% block hero %}{% endblock hero %}

<!--base.html에서 <block main > 내부 <div class="box is-marginless is-shadowless is-radiusless"> 바로 아래
div.box 안쪽으로  block box /endblock을 추가한다-->

{% block box %}
<div class="columns">
    <div class="column is-2">
        <div class="card is-shadowless" style="border-right:solid 1px #eee">
            <div class="card-content">
                <aside class="menu">
                    <p class="menu-label">
                        Dashboard
                    </p>
                    <ul class="menu-list">
                        <li><a class="{% if request.path == '/admin/' %}is-active{% endif %}"
                            href="{{ url_for('admin.index') }}">Home</a></li>
                        <!-- <li><a>Customers</a></li> -->
                    </ul>
                    <p class="menu-label">
                        Category
                    </p>
                    <ul class="menu-list">
                        <li><a href="">Category 관리</a></li>
                    </ul>
                    <p class="menu-label">
                        Post
                    </p>
                    <ul class="menu-list">
                        <li><a href="">Post 관리</a></li>
                    </ul>
                    <p class="menu-label">
                        Tag
                    </p>
                    <ul class="menu-list">
                        <li><a href="">Tag 관리</a></li>
                    </ul>
                    <p class="menu-label">
                        User
                    </p>
                    <ul class="menu-list">
                        <li><a href="">User 관리</a></li>
                        <li><a>비밀번호 변경</a></li>
                    </ul>
                </aside>
            </div>
        </div>
    </div>
    <div class="column">
        {% block member %}
        <div class="tile is-ancestor">
            <div class="tile is-parent">
                <article class="tile is-child notification is-info is-light">
                    <div class="content">
                        <p class="title">100</p>
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
                        <p class="title">50</p>
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
                        <p class="title">150</p>
                        <p class="subtitle">댓글 수</p>
                        <div class="content">
                            <!-- Content -->
                        </div>
                    </div>
                </article>
            </div>
        </div>
        {% endblock member %}
    </div>
</div>
{% endblock box %}
```

![image-20221113160825684](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221113160825684.png)



#### 4 admin route는 로그인한 유저(session.user_id -> g.user)를 검사(로그인 안됬으면 auth.login으로 redirect)해주는 login_required걸기

- admin_route.py의  admin.index view_func에  **auth_route.py에 정의했던 login_required 데코레이터를 가져와서 사용**

```python
from src.main.routes.auth_route import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')
```



#### 5 login_required에서 직전url querystring으로 기억하기

##### auth.login으로 가서 로그인다시 원래 url로 돌아갈 수 있게 querystring으로 [로그인전 요청url 기억]하도록 변경하기

- 현재는 **/admin 접속요청** -> /auth/login으로 redirect -> 로그인 -> /   main.index로만 이동되서,  **로그인 전 요청url로 못가는 상태다**

- **f-string을 이용해, url_for()호출 결과값에 쿼리스트링으로 묶어서 기억한다**

  - **url_for는 prefix.view_fun의 문자열을 받지만, 결과값도 결국 문자열이었다.**

  ```python
  redirect_to = f"{url_for('auth.login')}?redirect_to={request.path}"
  print(redirect_to)
  
  /auth/login?redirect_to=/admin/
  ```



```python
def login_required(view_func):
    @functools.wraps(view_func)
    def wrapped_view(**kwargs):
        if not g.user:
            # return redirect(url_for('auth.login'))
            # 추가1) login이 필요한 곳에 로그인 안한상태로 접속시, request.path를 이용해, redirect 전 현재요청url을 쿼리스트링으로 기억
            redirect_to = f"{url_for('auth.login')}?redirect_to={request.path}"
            return redirect(redirect_to)
        return view_func(**kwargs)

    return wrapped_view
```



##### login route는 직전url이 담겨있는지 querystring을 확인(request.args.get(''))해서, 있다면 main이 아닌 그곳으로 redirect

```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
	## 추가1) login route는 @login_required에 의해 올땐, 직전url을 querystring으로 담고 있으니 확인한다.
    redirect_to = request.args.get('redirect_to')

    form = LoginForm()
    if form.validate_on_submit():
        with DBConnectionHandler() as db:
            user = db.session.scalars((
                select(User)
                .where(User.username == form.username.data)
            )).first()


        session.clear()
        session['user_id'] = user.id

        ## 추가2) 직전url이 있다면 그곳으로 / (아니면) main으로로
        if redirect_to:
            return redirect(redirect_to)

        return redirect('/')

    return render_template('auth/login.html',
                           form=form)

```







### admin - 모든 entity별 route+form+template개발(auth관련은 미리 만들었음)

- admin는 index부터 모든 route들이 @login_required다



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



#### 10 entity 끝날때마다 admin/index.html의 메뉴에 route 및 is-active class걸어주기

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









#### 11 article(post)  select

##### article route

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

    stmt = select(Post).order_by(Post.id.desc())
    pagination = paginate(stmt, page=page, per_page=10)
    post_list = pagination.items

    return render_template('admin/article.html',
                           post_list=post_list, pagination=pagination)

```



##### admin > article.html 생성

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



#### front - 

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
            <!-- enum이라 .name -->
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

