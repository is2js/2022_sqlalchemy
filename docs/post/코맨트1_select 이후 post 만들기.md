### 코맨트 select 이후 post 만들기

1. Flask-WTF**==**0.15.1 설치

   ```pythoon
   pip3 install flask_wtf 
   ```

   

2. flask와 관련이므로 `main > forms`패키지 만들고

   ![image-20221028021524002](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221028021524002.png)

   1. comments.py 만들어서 form 정의하기

   2. **같은 comment지만, comment(최상위댓글)과 reply(대댓글)의 form을 나눈다**

      1. Comment는 Post detail에서 보여지는 form이고
      2. Reply는 댓글에서 대댓글 클릭시 보여지는 form

      ```python
      from flask_wtf import FlaskForm
      from wtforms import StringField, TextAreaField
      from wtforms.validators import InputRequired
      
      
      class CommentForm(FlaskForm):
          author = StringField(validators=[InputRequired()])
          text = TextAreaField(validators=[InputRequired()])
      
      
      class ReplyForm(FlaskForm):
          author = StringField(validators=[InputRequired()])
          text = TextAreaField(validators=[InputRequired()])
      
      ```

      ```python
      from .comments import CommentForm, ReplyForm
      ```



3. GET에서 **POST method 추가후** route에서 **view가 포함된 form객체**를 만들어

   - GET시 form객체를 같이보내준다.

     ```python
     @api_routes_bp.route("/", methods=["GET", "POST"])
     def index():
         comment_form = CommentForm()
         reply_form = ReplyForm()
         #...
     ```

     ```python
         return render_template("comment.html", comments=comments, comments2=comments2
                                , comment_form=comment_form
                                , reply_form=reply_form
                                )
     
     ```

     



4. comment.html에 

   - comment_form 객체 + form태그를 이용해서, form view를 작성한다.

   ```jinja2
           <!-- POST       -->
           <div class="shadow p-4 mb-4 col-lg-12 col-sm-6">
               <form action="{{request.path }}" method="POST">
                   {{ comment_form.csrf_token }}
                   <div class="form-group mt-2">
                       {{comment_form.author(class="form-control", placeholder="Author")}}
                   </div>
                   <div class="form-group mt-2">
                       {{comment_form.text(class="form-control" ,placeholder="Comment")}}
                   </div>
                   <button type="submit" class="btn btn-primary mt-2">Post comment</button>
               </form>
           </div>
   ```

   

5. form 속 crsf 사용을 위해 flask sqlaclehmy secret key 설정을 추가한다.

   1. `.env`에 환경변수 추가

   ```yaml
   # sqlalchemy for flask app
   SECRET_KEY = 'secret-key'
   # SQLALCHEMY_DATABASE_URI = "sqlite:///replies.db"
   # SQLALCHEMY_TRACK_MODIFICATIONS = True
   ```

   2. src> config > settings.py 속에
      - DB class에 넣지말고 FlaskConfig class를 생성해서 넣어주자

   ```python
   class FlaskConfig:
       SECRET_KEY = os.getenv("SECRET_KEY")
   
   
   project = Project()
   db = DB()
   auth = Auth()
   flask_config = FlaskConfig()
   ```

   ```python
   from .settings import db, auth, project, flask_config
   ```

   3. src>config>app.py 로 가서, app에 설정을  추가해주자.

   ```python
   #...
   from src.config import flask_config
   #...
   
   app = Flask(__name__, template_folder=template_dir)
   CORS(app)
   app.config["SECRET_KEY"] = flask_config.SECRET_KEY
   #...
   ```

6. view로 들어가보면

   ![image-20221028023328023](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221028023328023.png)





6. 이제 comment_form을 post submit을 받아줘야한다.

   - POST 이면서 form이 잘 왓을 경우

     - author와 text로 댓글을 생성하고 **.save()를 통해 path와 함께 작성되도록 한다**

     ```python
     @api_routes_bp.route("/", methods=["GET", "POST"])
     def index():
         comment_form = CommentForm()
         reply_form = ReplyForm()
     
         if request.method == 'POST' and comment_form.validate_on_submit():
             author = comment_form.author.data
             text = comment_form.text.data
     
             comment = Comment(text=text, author=author)
             comment.save()
     
             flash("comment posted", "success")
     
         with DBConnectionHandler() as db:
     ```

   - 이 때, flash()도 던지는데, **base.html**에서 받아주는 코드가 있다.

   ![image-20221028040518799](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221028040518799.png)





### feed타임 필터 만들어서 적용하기

- [몇분전 등 feed 스타일 참고](https://velog.io/@bae-code/python-%EB%AA%87%EB%B6%84%EC%A0%84-%EB%AA%87%EC%8B%9C%EA%B0%84%EC%A0%84-%EA%B2%8C%EC%8B%9C%EA%B8%80-%ED%91%9C%EC%8B%9C): 사실상 이것은 사용안함
- 내 템플릿 중에, 시간을 년/월/일 큰 순부터 잘라먹어서 시간변환하는 template 참고
  - algo_datetime_timedelta를 시간단위string으로 나누기
- **[filter 만드는 방법 참고](https://sooooooyn.tistory.com/4?category=863481)**



1. entity/ comments.py에서 서버시간이 아니라 현재컴퓨터시간 기준으로 작성되도록 필드옵션을 변경한다.

   ```
   default=datetime.datetime.now
   ```

   - server_default =  func.now()로 메서드호출까지 해야하지만
   - default = 컴터시간은 메서드호출하면 값이 넘어가므로 now 함수객체를 전달한다
   - **main.py에서 테이블을 새로 생성**



2. commons에 `feed_datetime.py`를 만들고 작성한다

   - init에 올린다.

   ```python
   import datetime
   
   
   def feed_datetime(feed_time, is_feed=True):
       formatted = ''
       if not is_feed:
           weekdays = ['월', '화', '수', '목', '금', '토', '일']
           wd = weekdays[feed_time.weekday()]
           ymd_format = "%Y년 %m월 %d일 %H시 %M분 ({})".format(wd)
           formatted = feed_time.strftime(ymd_format.encode('unicode-escape').decode()).encode().decode('unicode-escape')
       else:
           current_time = datetime.datetime.now()
           ## total 초로 바꾼다.
           total_seconds = int((current_time - feed_time).total_seconds())
           ## 어느 단위에 걸리는지 확인한다.
           periods = [
               ('year', 60 * 60 * 24 * 365, '년 전'),
               ('week', 60 * 60 * 24 * 7, '주 전'),
               ('day', 60 * 60 * 24,'일 전'),
               ('hour', 60 * 60, '시간 전'),
               ('minute', 60, '분 전'),
               ('second', 1, '초 전'),
           ]
           prev_unit = 0
           prev_ment = '방금 전'
           for period, unit, ment in reversed(periods):
               if total_seconds < unit:
                   # (1) 큰 것부터 보면서 잘라먹고 나머지 다시 처리하는 식이 아니라
                   # 작은단위부터 보고 그것을 못 넘어선 경우, 그 직전단위 prev_unit로 처리해야한다.
                   # , 해당단위보다 클 경우, (ex> 61초 -> 1초보다, 60(1분)보단 큰데 60*60(1시간보단)작다  => 60,60직전의 1분으로처리되어야한다)
                   #    나머지하위단위들을 total_seconds에 업뎃해서 재할당한다. -> 버린다.
   
                   # (3) 1초보다 작아서, prev 0으로 나누는 경우는 그냥 방금전
                   if not prev_unit:
                       value = ''
                   else:
                       value, _ = divmod(total_seconds, prev_unit)
                   # (2) 몫 + 멘트를 챙긴다
                   formatted = str(value) + prev_ment
                   break
               else:
                   ## 현재단위보다 크면, 다음단위로 넘어가되 prev업뎃
                   prev_unit = unit
                   prev_ment = ment
   
       return formatted
   
   if __name__ == "__main__":
       print(feed_datetime(datetime.datetime.now() - datetime.timedelta(seconds=62), is_feed=False))
       print(feed_datetime(datetime.datetime.now() - datetime.timedelta(seconds=119)))
   ```

   



3. src>main> config>app.py로 가서

   - **app에 jinja2 필터 추가옵션을 준다.**

   ```python
   app.jinja_env.filters["feed_datetime"] = feed_datetime
   ```

4. comment.html 로 가서 comment.timestamp에 `|feed_datetime` 혹은 옵션까지 준다

   ```jinja2
   <p class="m-0"><b>{{comment.author}}</b>님 {{comment.timestamp | feed_datetime(is_feed=True)}}</p>
   
   {{comment.timestamp | feed_datetime}}
   ```

   ![image-20221028041159965](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221028041159965.png)





### 대댓글 collapse로 작성할  수 있게 하기

```
Example
Click the buttons below to show and hide another element via class changes:

.collapse hides content
.collapsing is applied during transitions
.collapse.show shows content

Generally, we recommend using a button with the 
data-bs-target attribute. 
While not recommended from a semantic point of view, you can also use a link with the 
href attribute (and a role="button")

In both cases, the data-bs-toggle="collapse" is required.
```

- **컬랩스 a태그**에서 요구되는 것은 

  - `data-bs-toggle="collapse"` 속성과 `role="button"`
  - `href="#{나타날공간이 받을 id}"`

- **컬랩스 나타날 공간 div태그에 요구되는 것은**

  - `class="collapse w-50"`

  - `id="{컬랩스트리거 a태그의 href속성값에서 #을 뺀 문자열}"`

    

1. 대댓글 아이콘인 `<i class="bi bi-reply"></i>`를 **컬랩스a태그 조건에 맡게 감싼다**

   ```html
   <a class="" data-bs-toggle="collapse" href="#comment-{{comment.id}}"
      role="button" aria-expanded="false" aria-controls="collapseExample">
       <i class="bi bi-reply"></i>
   </a>
   ```

   

2. **댓글전체의 div공간과 같은 수준(`border-start border-primary`와 같은 내부)에서의 `새로운 div태그`를 `컬랩스 나타나는 조건`에 맞추어 추가한다**

   ![image-20221029042925049](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221029042925049.png)

   ```html
   <!--[2] 대댓글 form이 나타날 공간 div -->
   <!--(1) class="collapse w-50" 속성 -->
   <!--(2) id="{컬랩스트리거 a태그의 href속성값에서 #을 뺀 문자열}" -->
   <div class="collapse w-50" id="comment-{{comment.id}}">
   
   </div>
   ```

   



3. **미리 만들어서 view로 보내줬떤 `reply_form`으로 을 통해 form을 만든다.**

   - **이 때 보내줘야할 것은 대댓글생성POST route**이다.
     - comment생성 route함수를 `index`로 지어놓고  `url_for('api_routes.index')`로 보냈었다.
     - reply 생성 route함수는 **부모comment.id를 받아서 가야한다**
       - **`url_for('api_routes.register_reply', comment_id = comment.id)`로 보내자.**

   ```python
   <div class="collapse w-50" id="comment-{{comment.id}}">
       <form action="{{url_for('api_routes.egister_reply', comment_id=comment.id) }}" method="POST">
           {{ reply_form.csrf_token }}
           <div class="form-group mt-2">
               {{reply_form.author(class="form-control", placeholder="Author")}}
           </div>
           <div class="form-group mt-2">
               {{reply_form.text(class="form-control" ,placeholder="Comment")}}
           </div>
           <button type="submit" class="btn btn-primary mt-2 btn-sm">Post Reply</button>
       </form>
   </div>
   ```





4. route function이 없으면 페이지 확인이 안된다.

   1. **해당 form의 객체를 `view가 필요없는 POST 상황에서도 새로 생성해야 넘어오는 데이터 획득이 가능`하다.**
   2. **route에 넘어오는comment_id를  url에 `comments/<int:comment_id>`로 명시하고** 
   3. **부모객체를 찾아, 관계컬럼 parent=에 넣어서 대댓글reply(Comment)**
   4. **다시 해당화면으로 `redirect`해서 다 다시 뿌려주도록 한다**

   ```python
   @api_routes_bp.route("/comments/<int:comment_id>", methods=["POST"])  # ,strict_slashes=False)
   def register_reply(comment_id):
       reply_form = ReplyForm()
   
       if request.method == 'POST' and reply_form.validate_on_submit():
           author = reply_form.author.data
           text = reply_form.text.data
   
           # comment = Comment(text=text, author=author)
           with DBConnectionHandler() as db:
               stmt = (
                   select(Comment)
                   .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
                   .where(Comment.id == comment_id)
               )
               parent = db.session.scalars(stmt).one()
   
           reply = Comment(parent=parent, text=text, author=author)
           reply.save()
   
           flash("reply posted", "success")
           return redirect(url_for('api_routes.index'))
   ```

   



![image-20221029045248243](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221029045248243.png)

![image-20221029045342188](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221029045342188.png)



5. 디자인 변경

   1. 댓글 아이콘 `bi bi-chat-left-dots`
   2. 대댓글 아이콘 `bi bi-reply`
   3. 아이콘색은 부트스트랩색상과 무관하게 **style="color:"로 바꾼다**
   4. 댓글 작성자는 b태그 대신  **span태그 + `class="label label-색상"`을 주고**
      - **base.html style에 `label-색상에서는 backrground`를 꾸며준다**
   5. 댓글 border는 
      1. border-5 형태로 테두리 두께를
      2. border-부트색상 으로 테두레 색상을 정해준다.

   ![image-20221030001058768](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030001058768.png)

   1. jinja custom filter `feed_datetime.py`에서 일주일 이상되면 년월일로 표시하도록 변경함
      - 1일 이상 되면으로 설정후 확인도어, 변수로 뽑았다가 일주일로 변경함



### entity객체.level() 계산식을 @hybrid_property로 변경

- [참고사이트](https://martinheinz.dev/blog/28)

  - **이미 소유한 칼럼으로 계산을 해서 가상필드를 만들어주는 속성**
  - case 문 or filter() 쓸 조건식을 계산해서 만들 수 있다.

- **entity 실제칼럼의 변화가 아니여서 `db 삭제후 재생성해서 쓸  필요`가 없어진다.**

- 객체를 받아 사용하는 jinja2에서는 `comment.level()` -> `comment.level`로 바꿔 쓰면 된다.

  

```python
def level(self):
    return len(self.path) // self._N - 1

@hybrid_property
def level(self):
    return len(self.path) // self._N - 1
```

```html
col-{{12 - comment.level()}} offset-{{comment.level()}}

# int not callable

col-{{12 - comment.level}} offset-{{comment.level}}
```



### 댓글의 삭제

- 해당 댓글이 삭제될 때 -> **해당path 모두 삭제되어야한다**

  - **이미 `Column(Integer, ForeignKey(id, ondelete='CASCADE'))`dl 걸려잇기 때문에, `나를 fk로 가진 자식들이 자동 같이 삭제`된다.**
  - **수정시만 like(self.path + '%')를 통해, 해당패스 아래에 있는 놈들을 같이 수정**해야한다.
  - [관련 사이트](https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy): save시 활용되는 group칼럼 수정 -> threaed_vote 수정 및 그룹데이터들 다 같이 수정

  ```python
  class Comment(db.Model):
      def change_vote(vote):
          for comment in Comment.query.filter(Comment.path.like(self.path + '%')):
              self.thread_vote = vote
              db.session.add(self)
          db.session.commit()
  ```

  

- **최상위든, 하위든, 무조건 `.save()시는 부모를 활용해서 저장`한다면**

  - **`삭제는 부모없이 자신만`으로 -> `자식객체들 by ondelete`로  다 골라내서 삭제하면 된다.**
    - 코멘트는 백업하지 않는다 - >soft_delete용 칼럼 제공X 따로처리 X
    - 코멘트는 수정하지 않는다 -> updated_timestamp 칼럼 제공X 따로처리 X





1. view에서 x bi icon을 넣어주자.

   - 아이콘은 i태그 + `bi bi-xxx` + style="color:색상"으로 조절
     - style="color:" 대신 base.html의 style에 .danger color 색상정의

   ```html
   <!-- base.html의 <style>태그 -->
   /* 아이콘 색상을 위한 color속성   */
   .danger {
   	color: #d9534f;
   }
   
   
   <p class="my-2">{{comment.text}} <i class="bi bi-x-square danger"></i></p>
   ```

   ![image-20221030132137850](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030132137850.png)





2. X아이콘을 누를시 delete요청을 보내야한다.

   - **form이라도 GET, POST밖에 안되는데, `ajax등을 이용하지 않는 a태그를 통한 route요청은 GET으로 요청`밖에 안된다.**

   - 일단 a태그에서 url_for로 delete_comment라우트로 전송

     ```html
     <p class="my-2">{{comment.text}} <a href="{{url_for('api_routes.delete_comment', comment_id=comment.id)}}" class="bi bi-x-square danger"></a></p>
     
     ```

   - **GET으로 가더라도 `url`은 `다른route와 똑같아도 된다` -> `route함수명만 다르게 정의`**

     - methods는 생략해서 GET으로 가도록

     ```python
     @api_routes_bp.route("/comments/<int:comment_id>") 
     def delete_comment(comment_id):
         print(f"delete comment {comment_id}")
         flash("comment delete", "success")
     ```

     

   - 찍어보기

     ![image-20221030133513074](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030133513074.png)





3. **route에서는 삭제에 대한 로직만 작성해주면, 알아서 자식들도 삭제된다.**

   ```python
   @api_routes_bp.route("/comments/<int:comment_id>")  # ,strict_slashes=False)
   def delete_comment(comment_id):
       print(f"delete comment {comment_id}")
   
       with DBConnectionHandler() as db:
           stmt = (
               select(Comment)
               .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
               .where(Comment.id == comment_id)
           )
           target = db.session.scalars(stmt).one()
           #print(target)
           db.session.delete(target)
           db.session.commit()
   
           flash("comment delete with children", "success")
       return redirect(url_for('api_routes.index'))
   
   ```

   

### 페이지네이션

- 참고 코드: https://topic.alibabacloud.com/a/several-pagination-methods-of-sqlalchemy-and-flask-sqlalchemy_8_8_30013584.html
- [참고 블로그: mega](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ix-pagination)
- [참고 블로그2: digital ocean](https://www.digitalocean.com/community/tutorials/how-to-query-tables-and-paginate-data-in-flask-sqlalchemy)

- **[pagnation객체화 블로그 패스트코드](https://parksrazor.tistory.com/457)**
  - 도커 설치 및, cls메서드 사용 [booster.py](https://parksrazor.tistory.com/456)도 있다.
  - [sqlalchemy](https://parksrazor.tistory.com/search/sqlalchemy)

#### select + paginate method



1. comment들을 보여주는 **`/` `index`route를 복사**해서, `/explore` `explore` route를 만들고

2. **select한 이후 limit과 offset으로 갯수로 구간을 만들고, 갯수만큼만 가져와야한다**

   - 이미 filter와 orderby는 직접 적용한 stmt를 만들고
   - limit에 `per_page`만큼만 가져와야하고
   - offset으로 (`page(1, 2, ...) - 1`) * `per_page`만큼 앞에를 건너띄어야한다.
   - **나중에 url로 page=1,2,3..가 들어와야하므로 `메서드로 미리 정의`해놓는다.**
     - 현재 commons패키지에 정의해놓음.

   ```python
   def paginate(stmt, page=1, per_page=10):
       # apply per_page to limit (offset이후 나올 총 갯수)
       if per_page:
           # stmt = stmt.limit(per_page)
           # limit은 기본적으로order_by와 함께 쓰인다.
           stmt = stmt.limit(per_page)
   
       # apply page to offset ( (page-1) * page_size = 넘겨야할 총 갯수)
       ## ex> page =2 를 보고싶다 -> 앞에 1 page ( per_page갯수만큼 )  pass해야한다.
       ##    => 보고싶은 page  == (page-1 * page당갯수)만큼 건너띈다.
       if page:
           stmt = stmt.offset((page - 1) * per_page)
   
       return stmt
   ```

   

3. **`PER_PAGE`는 사용자 맘대로 정의해놔야하므로 환경변수 -> config>setting.py에 `POSTS_PER_PAGE`, `COMMENTS_PER_PAGE`갯수를 정의해놓자**

   ```python
   class DB:
       # database
           
       POST_PER_PAGE = int(os.getenv("POST_PER_PAGE", "10"))
       COMMENTS_PER_PAGE = int(os.getenv("COMMENTS_PER_PAGE", "20"))
   ```

4. `. env`에도 추가해주자

   ```yaml
   # database===
   # DB_CONNECTION=mysql+pymysql
   # DB_NAME=cinema
   # DB_USER=root
   # DB_PASSWORD=564123
   # DB_HOST= 
   # DB_PORT=
   # POST_PER_PAGE = 10
   # COMMENTS_PER_PAGE = 20
   
   ```

5. pagiante 메서드에 `per_page값`을 환경변수에서 가져와 설정해주자.

   - dbhandler의 db와 config의 db객체가 이름이 동일해서 변수명_config로 싹다 변경

   ```python
           stmt = paginate(stmt, page=1, per_page=db_config.COMMENTS_PER_PAGE)
   
   ```

   

6. **`explore` route에서 comments들을 다 불러 온 뒤, paginate method를 적용한 stmt를 반환받아 실행하게 한다**

   - pagination을 거치기 전에 **`order_by`까지 미리 다 해놔야한다**

   ```python
   @api_routes_bp.route("/explore", methods=["GET", "POST"])
   def explore():
       comment_form = CommentForm()
       reply_form = ReplyForm()
   
   
       with DBConnectionHandler() as db:
           stmt = (
               select(Comment)
               .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
               .order_by(Comment.thread_timestamp.desc(), Comment.path.asc(), Comment.id.asc())
           )
   
           # select()객체, execute(), scalars()모두 paginate()메서드가 없음 => 직접 정의
           stmt = paginate(stmt, page=1, per_page=db.COMMENTS_PER_PAGE)
           comments = db.session.scalars(stmt).all()
   ```

7. 접속해보면, comments에는 20개의 댓글만 들어가있다.

   ![image-20221030154448316](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030154448316.png)





#### querystring + reqeust.args.get('page', 1, type=int)

- **flaks의 querystring은 `request.args`에서 뽑아쓰면 되는데**
  - request.args.**`to_dict()`로 dict**로 만든 뒤, **.keys()로 검사해서 사용하면 된다.**
  - 혹은 **`request.args.get( , 기본값, type=)`을 적어서, `type지정 및 없을때의 기본값`을 지정해서 사용할 수 있다.**



1. **comments들을 보는 `첫번째 진입 page의 url`은 `page=1 쿼리스트링이 없어도 pagination`이 되도록 `request.args.get('page', 1, type=int)`로 뽑아쓰면 된다.**

   - per_page갯수는 이미 환경변수로 정해놨다
   - **진입페이지(index) 및 페이지네이션용 라우터 (explore) 둘다 `없으면 1을 page변수로 뽑아쓸 수 있도록 request.args.get`을 사용한다**

   - index, explore

   ```python
   page = request.args.get('page', 1, type=int)
   stmt = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)
   ```

   - 위쪽 4개가 동일한 url이 된다.
     - **Page 1, implicit: *http://localhost:5000/***
     - **Page 1, explicit: *http://localhost:5000/?page=1***
     - **Page 1, implicit: *http://localhost:5000/explore***
     - **Page 1, explicit: *http://localhost:5000/explore?page=1***
     - Page 3: *http://localhost:5000/index?page=3*

   ![image-20221030183621421](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030183621421.png)

   ![image-20221030183631852](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030183631852.png)

   - **?page=3**을 입력해보면 **`?`로 시작하는 querystring**이 잘 작동해서 먹힌다

     ![image-20221030184003956](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030184003956.png)







#### pagination.py + has_next, has_prev 등  Pagination객체

- [참고블로그](https://parksrazor.tistory.com/457)

- flask-sqlalchemy는 **query.`paginate()`결과  ->`Pagination`객체를 반환해서 아래와 같은속성을 사용하게 해준다.**
  - `items`: 현재 페이지의 Entity객체들을
  - `has_next`: True if there is at least one more page after the current one
  - `has_prev`: True if there is at least one more page before the current one
  - `next_num`: page number for the next page
  - `prev_num`: page number for the previous page
  - **total: pagination하기 전 총 갯수를 추가하자**
  - **pages =  전체 패이지 갯수를 올림해서 가지고 있자**
- **우리는 stmt에 paginate()를 직접할 수 없으므로**
  - **paginate(stmt, ) 메서드를 개발한 뒤** 
  - **관련 속성들을 또 메서드로 하나씩 만들지말고, Pagnation객체를 만들어서 내부에 소유하게 하자.**



1. src>infra>commons 패키지를 만들고, 거기다가 pagination.py를 만든다.

   ![image-20221030195319188](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030195319188.png)

2. **pagination.py에 `stmt를 받아 Pagination객체를 생성해줄 factory method`를 정의한다.**

   - **page, per_page는 1이상 이므로 `0이하시 에러`를 발생시킨다.**
   - 이 때, **이미 select객체가 된 것에 count칼럼을 만들어 scalar로 변경할 수 없으니 `select객체를 subquery로 취급하여 새로운 select( fun.count())`를 만들어 갯수를 센다**

   ```python
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

3. pagination.py의 객체는 

   - items와 total은 그대로 들고 있으나
   - `page, per_page`를 이용해 **아래 5개 필드를 만들어낸다.**
     - `has_next`: True if there is at least one more page after the current one
     - `has_prev`: True if there is at least one more page before the current one
     - `next_num`: page number for the next page
     - `prev_num`: page number for the previous page
     - `pages`: 전체 페이지 수

   ```python
   class Pagination:
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
           self.pages = math.ceil(len(items) / per_page) + 1
   ```

   - init.py에 올리고 route에서 import해 stmt에 사용한다

     ```python
     from .pagination import paginate
     ```

     

#### routes -> view에는 pagination객체 대신 entity객체들(.items)와 url_for객체(or None)만 넘겨주자

- [digital ocean은 pagination객체를 건네주는 예](https://www.digitalocean.com/community/tutorials/how-to-query-tables-and-paginate-data-in-flask-sqlalchemy)

- [mega블로그는 .items + next_url, prev_url객체를 만들어서 넘겨주는 예](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ix-pagination)

```python
        # stmt = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)
        # comments = db.session.scalars(stmt).all()
        # 1) comments객체 대신 pagination객체를 받아와서 -> comments key에 pagination.items를 넘겨준다
        comment_pagination = paginate(stmt, page=page, per_page=db_config.COMMENTS_PER_PAGE)
    
    # 2) prev_url, next_url 객체를 url_for()를 이용해 미리 만들어서 같이 넘겨준다.
    #   (만약 미리 만들지 않으면, view(html)에서 pagination객체를 받아 .속성을 이용해 url_for()를 만들어야 해서 복잡?)
    # => 여기서는 view에는 pagination객체 말고, entity객체와 url_for객체를 미리 만들어서 넘겨주자
    # 2-1) if .has_next 면 .next_num을 page=keyword에 넣어서 url_for객체를, 
    #     아니면 None을 넣어서 next_url객체를 만든다.
    next_url = url_for('api_routes.explore', page=comment_pagination.next_num) \
        if comment_pagination.has_next else None 
    prev_url = url_for('api_routes.explore', page=comment_pagination.prev_num) \
        if comment_pagination.has_prev else None 
    # 3) 현재page번호 및 만들어준 pages필드도 같이 넘겨준다.
    return render_template("comment.html"
                           , comment_form=comment_form
                           , reply_form=reply_form
                           , comments=comment_pagination.items
                           , next_url=next_url
                           , prev_url=prev_url
                           , current_page=comment_pagination.page
                           , pages=comment_pagination.pages
```

- index와 explore route 2개다 똑같은 처리를 해준다.

  

#### view에선 next / prev  등 페이지네이션 처리해주기

- 넘겨받은 next_url, prev_url , pages를 활용한다



1. **댓글이 보이는 곳에서 내부에 div를 text-center class로추가해준다.**

   ![image-20221030212243544](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030212243544.png)

2. bootstrap5 bi에서 화살표를 고르고

   - next_url, prev_url 존재유무에 따라 아이콘이 뜨게 만들어준다.
   - a태그에는 href 로 **{{ next_url객체 or prev_url객체 }}를 넣어주고**
     - a태그 내부에 i태그로 아이콘을 만든다.

   ```html
   <!--  COMMENT pagination     -->
   <div class="text-center">
       {% if prev_url %}
       <a href="{{ prev_url }}"><i class="bi bi-caret-left default" ></i></a>
       {% endif %}
       {% if next_url %}
       <a href="{{ next_url }}"><i class="bi bi-caret-right default"></i></a>
       {% endif %}
   </div>
   ```

   ![image-20221030214721283](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221030214721283.png)

3. 중간에는 pages를 숫자표기할 것인데, 현재page를 중심으로 양옆 2개만 표시해보자.

   - range(1, )로 pages를 순회하면서

     - if  jinja 2수의 차이를 괄호치고 | abs필터

       

   ```html
   <!--  COMMENT SELECT and REPLY POST     -->
   <div class="shadow-sm p-4 col-lg-12 col-sm-6">
       <!--  COMMENT pagination     -->
       <div class="text-center mb-3">
           <!--  이전 페이지가 있으면, 이전url객체 + 아이콘     -->
           {% if prev_url %}
               <a href="{{ prev_url }}"><i class="fs-5 bi bi-caret-left-fill danger" ></i></a>
           {% endif %}
   
           <!--  전체페이지 중에 가운데 숫자 current_page와 차이 2개까지 표시     -->
           {% for number in range(1, pages) %}
               {% if ((number - current_page) | abs)  <= 2 %}
                   <span class="{{'danger fs-3 fw-bold' if number == current_page else 'default'}}">
                   {{ number }}
                   </span>
               {% endif %}
           {% endfor %}
   
           <!--  다음 페이지가 있으면, 다음url객체 + 아이콘     -->
           {% if next_url %}
               <a href="{{ next_url }}"><i class="fs-5 bi bi-caret-right-fill danger"></i></a>
           {% endif %}
       </div>
   
   ```

   ![image-20221031002951733](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031002951733.png)



### 자기참조(depth 가진)  Menu만들기

#### model

- [참고 gist](https://gist.github.com/sujeetkv/b36a1be5776a6c6229229a9faf9453e8)

1. comments.py를 복사해서 menus.py를 만들고 init에 올린다.

   1. depth는 최대 3까지 준다
   2. 부모의 ~~category를 통해 그룹칼럼인 thread_category~~를 만들 것이다.
      - **그룹칼럼은 최상위들의 생성순서대로 나올 수 있는 `timestamp` 혹은 `created_at`으로 만들어주자.**

   ```python
   import datetime
   
   from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Boolean
   from sqlalchemy.ext.hybrid import hybrid_property
   from sqlalchemy.orm import relationship, backref
   
   from src.infra.config.base import Base
   
   # https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy
   from src.infra.config.connection import DBConnectionHandler
   
   
   class Menu(Base):
       __tablename__ = 'menus'
       _N = 3
   
       id = Column(Integer, primary_key=True)
       category = Column(String(140))
       title = Column(String(140))
       icon = Column(String(32))
       endpoint = Column(String(32))
       is_visible = Column(Boolean())
       timestamp = Column(DateTime(), default=datetime.datetime.now, index=True)
       ####  group gatecogry 칼럼 == thread_gatecogry
       ### => 최상위레벨 기준으로 정렬되는 칼럼으로 해야한다.. category로 했다간.. 카테고리정렬이되어.. 생성 순서대로 안나온다.
       thread_timestamp = Column(DateTime())
   
       parent_id = Column(Integer, ForeignKey(id, ondelete='CASCADE'))
       submenus = relationship('Menu'
                              , backref=backref('parent', remote_side=[id], passive_deletes=True)
                              , cascade="all"  # [3] backref가 아닌, replies 자신에게 준다
                              , join_depth=3  # 필수1
                              , lazy='subquery'  # 필수2
                              )
       path = Column(Text, index=True)
   
   
       @hybrid_property
       def level(self):
           return len(self.path) // self._N - 1
   
   
       def save(self):
           with DBConnectionHandler() as db:
               db.session.add(self)
               db.session.flush()
   
               prefix = self.parent.path if self.parent else ''
               self.path = prefix + f"{self.id:0{self._N}d}"
   
               self.thread_timestamp = self.parent.thread_timestamp if self.parent else self.timestamp
   
               db.session.commit()
   
       def __repr__(self):
           info: str = f"{self.__class__.__name__}" \
                       f"[id={self.id!r}," \
                       f" category={self.category!r}," \
                       f" title={self.title!r}," \
                       f" endpoint={self.endpoint!r}," \
                       f" level={self.level!r}]"
           return info
   
   ```

   

##### level도 메서드가 아니라 hybrid 속성 + expression으로 order_by가능하게

```python
    ## 21.
    @hybrid_property
    def level(self):
        return len(self.path) // self._N - 1

    ## 22. 이것까지 줘야 계측칼럼도 정렬할 수 잇음. by classmethod로서 entity를 cls로 이용
    ## if return return일 경우 case문으로 처리
    ## len(self.필드) => func.length(cls.필드) , 나누기 -> func.div -> sqlite에선 지원안함.
    @level.expression
    def level(cls):
        # 0 division 가능성이 있으면 = (cls.path / case([(cls._N == 0, null())], else_=cls.colC)
        # /는 지원되나 //는 지원안됨. func.round()써던지 해야할 듯.?
        return func.length(cls.path) / cls._N - 1
```

```python
stmt = (
    select(Comment)
    .options(lazyload('*'))  # 현재 lazy="subquery"y로 되어있기 때문에, jinja용 path이용한다면, 다 가져올 필요없음. flat 조회
    .order_by(Comment.thread_timestamp.desc(), Comment.level, Comment.timestamp.desc()) # (특정최상위 선택안할시 그룹칼럼별), level별, 원하는 순서
)
```



#### vscode + youtube로 boostrap5 navbar

- [참고사이트 coding yaar:](https://www.youtube.com/watch?v=V5MquVuKlU4) 

- [부트스트랩 navbar 시작코드](https://getbootstrap.com/docs/5.2/components/navbar/)

![image-20221031152212349](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031152212349.png)

1. `<ul class="dropdown-menu">`를 div태그로 바꾸고 

   1. hr divider 태그는 삭제하고

   2. 각각의 li태그 바깥에 ul태그를 입혀준다

   3. 각각의 li태그들은 복붙해서 메뉴들을 늘려준다

      ![image-20221031151255398](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031151255398.png)

   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta http-equiv="X-UA-Compatible" content="IE=edge">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Document</title>
       <!-- Bootstrap CSS -->
       <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Zenh87qX5JnK2Jl0vWa8Ck2rdkQ2Bzep5IDxbcnCeuOxjzrPF/et3URy9Bv1WTRi" crossorigin="anonymous">
       <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-OERcA2EqjJCMA+/3y+gxIOqMEjwtxJY7qPCqsdltbNJuaOe923+mo//f6V8Qbsw3" crossorigin="anonymous"></script>
       <link rel="stylesheet" href="../static/css/navbar.css">
   </head>
   <body>
       
   </body>
   </html>
   <nav class="navbar navbar-expand-lg bg-light">
       <div class="container-fluid">
         <a class="navbar-brand" href="#">Navbar</a>
         <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
           <span class="navbar-toggler-icon"></span>
         </button>
         <div class="collapse navbar-collapse" id="navbarSupportedContent">
           <ul class="navbar-nav me-auto mb-2 mb-lg-0">
             <li class="nav-item">
               <a class="nav-link active" aria-current="page" href="#">Home</a>
             </li>
             <li class="nav-item">
               <a class="nav-link" href="#">Link</a>
             </li>
             <li class="nav-item dropdown">
               <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                 Dropdown
               </a>
               <div class="dropdown-menu">
                 <ul>
                     <li><a class="dropdown-item" href="#">Action</a></li>
                     <li><a class="dropdown-item" href="#">Action</a></li>
                     <li><a class="dropdown-item" href="#">Action</a></li>
                     <li><a class="dropdown-item" href="#">Action</a></li>
                 </ul>
                 <ul>
                     <li><a class="dropdown-item" href="#">Another action</a></li>
                     <li><a class="dropdown-item" href="#">Another action</a></li>
                     <li><a class="dropdown-item" href="#">Another action</a></li>
                     <li><a class="dropdown-item" href="#">Another action</a></li>
                 </ul>
                 <ul>
                     <li><a class="dropdown-item" href="#">Something else here</a></li>
                     <li><a class="dropdown-item" href="#">Something else here</a></li>
                     <li><a class="dropdown-item" href="#">Something else here</a></li>
                     <li><a class="dropdown-item" href="#">Something else here</a></li>
                 </ul>
               </div>
             </li>
             <li class="nav-item">
               <a class="nav-link disabled">Disabled</a>
             </li>
           </ul>
           <form class="d-flex" role="search">
             <input class="form-control me-2" type="search" placeholder="Search" aria-label="Search">
             <button class="btn btn-outline-success" type="submit">Search</button>
           </form>
         </div>
       </div>
     </nav>
   ```

   

2. 연결된 css에서

   1. .dropdown-menu 아래 `ul`태그에 대해서 line-style과 padding을 제거해준다.

      ![image-20221031151440551](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031151440551.png)

   2. .dropdown-menu`.show`로 보이는 공간을 display:flex로 바꿔, 각각의 ul태그들을 한 card로 간주한다.

      ![image-20221031151649381](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031151649381.png)

   3. dropdown-menu의 `li:first-child`의 `a`태그에 대해서 글자스타일을 수정해준다

      ![image-20221031152159831](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031152159831.png)

   4. 바로 위에서 dropdown-menu의  모든 `li` `a`태그에 대해서 글자색과 패딩 조절

      ![image-20221031152505544](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031152505544.png)

   5. .dropdown-menu 공간 자체에 대해서 테투리곡선0 패딩, 박스쉐도우를 준다

      ![image-20221031152805872](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031152805872.png)

      - 쉐도우를 준 뒤, border를 none으로 제거한다

        ![image-20221031152854813](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031152854813.png)

   6. 맨 아래에 .dropdown-menu가 작을 때는, flex(card처럼)로 작동되지 않도록 min-width를 주는 **@media쿼리 내부로 `.dropdown-menu.show`속성을 잘라내기 해서 옮겨** 그 때만 작동하게 한다.

      - 기존

        ![image-20221031153246621](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031153246621.png)

      - 옮긴 뒤 

        ![image-20221031153554892](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031153554892.png)

      - 이제 큰 상태에서의 조정은 @media 내에서 해야한다.

   7. dropdown-menu가 아니라 더 상위의 `.dropdown `class에 대해 `.hover`시 `.dropdown-menu`가 display: flex;로 나타나도록  @media의 맨 위에 추가한다

   8. 이제 max-width를 min-witdh 보다 1px 작게하여 지정한 뒤,
      햄버거 메뉴일 떄, `.dropdown-menu.show`가 무한정 길어지지 않도록 높이설정 + y축 스크롤 설정을 @media쿼리를 추가해서 해준다.

      ![image-20221031155741704](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031155741704.png)

   ```css
   .dropdown-menu {
       border-radius: 0;
       padding: .5em;
       box-shadow: 0 3px 6px rgba(0, 0, 0, .23);
       border: none;
   }
   
   .dropdown-menu ul {
       list-style: none;
       padding: 0;
   }
   
   .dropdown-menu li a{
       color: gray;
       padding: .5em 1em;
   }
   
   .dropdown-menu li:first-child a{
       font-weight: bold;
       font-size: 1.2em;
       color: #000;
   }
   
   @media screen and (min-width:993px) {
       .dropdown:hover .dropdown-menu {
           display: flex;
       }
       
       .dropdown-menu.show {
           display: flex;
       }
   }
   @media screen and (max-width:992px) {
       .dropdown-menu.show {
           max-height: 30vh;
           /* max-height: 350px; */
               overflow-y: scroll;
       }
   }
   ```

   

   



3. 색깔 관련 styling을 처리해준다.

   - navbar의 배경을 바꾸기 위해서는 `nav태그`에서 `bg-light`(회색배경) class를 삭제하고 `style="background: "`를 준다.

     ![image-20221031160251229](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031160251229.png)

     

   - 준 배경색 그대로 `.dropdown-menu li:first-child a`의 글자색으로 준다.

     - 이어서, text-transformation: uppercase; 옵션을 주면, 항상 대문자로 변경된다.

     ![image-20221031160409402](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031160409402.png)

     ![image-20221031160530343](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031160530343.png)

   - 검색 버튼의 색상을 하얀색으로 바꾸기 위해 `btn-outline-success`를 `btn-outline-light`로 변경해준다.

     - 기존

       ![image-20221031160723118](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031160723118.png)

     - 변경후

       ![image-20221031160736661](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031160736661.png)



- underline hover 적용
  - [유튜브](https://www.youtube.com/watch?v=y7A1IUpqDaU&list=PLEGWy2sQ80YteTylA0vinRlvF-n-LuIHg&index=7)

1. 일단 level 0 메뉴들인 nav-item을 parent로 사용하기 위해 position을 relative로 주고 nav-item::after를 position absolute로 줘서 자식으로 이용한다

   - position absolute는 block으로 되어서 after된 요소가 원본의 바로 밑에 위치하게 된다.

     - 일반은 relative로 줘서, 가장 가까운부모의 처음부터 시작하게 하고
     - after속성은, absolute로 block으로서 바로 아래에서 시작하게 한다

     ![image-20221031201643289](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031201643289.png)

     ![image-20221031202014697](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031202014697.png)

2. after에는 content가 필수라서 '...'으로 주고, **height 4px** width 100% background를  원하는 호버색으로 준다.

   ![image-20221031200853101](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031200853101.png)

   - content를 빈문자열로 바꿔준다

3. 부모로부터 얼마만큼 반대방향으로 떨어질지 의미하는 bottom, top, left, right에서

   - bottom0 으로 부모의 맨아래에서 위로 안떨어지고  부모의 가장 아래에 붙게 만든다.
   - left, right도 마찬가지

   ![image-20221031202657039](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031202657039.png)

4. width100% ::after의 hover를 만들어서 주고, 원래 after는 0으로 시작한다

   ![image-20221031202808708](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031202808708.png)

   ![image-20221031202814361](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031202814361.png)





5. underline과 각 전체navbar간의  **위아래 약간의 gap**이 있는 이유는, 가장 큰 바깥태그인 nav-bar자체에 padding을 넣어놔서 각 nav-item이 넓어졌기 때문이다.

   ![image-20221031204337907](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031204337907.png)

   - 전체의 padding을 삭제하고, 

     ![image-20221031204206735](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031204206735.png)

   - 이렇게 되면 각 nav-item/nav-link(a태그)에 다 달라붙어있어서 안예쁘다.

     - **가장 안쪽의 a태그인 nav-link에 padding을 줘서 underline 꽉채움을 유지하면서 각각 거리를 벌린다**

       - nav-item에 padding

         ![image-20221031204631922](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031204631922.png)

       - nav-link에 padding

         ![image-20221031204705521](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031204705521.png)

6. padding 조절(navbar 제거 nav-link에 옮김)은 작은화면에서의 햄버거메뉴에는 적용되길 원치 않으니, @media쿼리로 2개 정의를 옮겨준다.

7. ::after에 transition: all .5s;를 주면 hover에 대해 천천히 hover된다 

8. hover가 좌측->우측으로 작동하는데, **after원본에 margin 0 auto로 좌우정렬을 해놓으면, 알아서 가운데에서부터 transition이 작동한다.**

9. 글자부분만 underline hover가 생기려면

   - nav-link(a)태그의 padding 중 좌우만 0으로 준다
   - nav-item의 바깥 margin을 padding에서 뺀만큼 준다.

```css
/* 2. level 0(nav-item) underline hover */

@media screen and (min-width:993px) {
    .navbar {
        padding: 0;
    }
    .navbar .navbar-nav .nav-link {
        /* padding: 1rem; */
        padding: 1rem 0;
    }    
    .navbar .navbar-nav .nav-item {
        /* padding: 1rem; */
        margin: 0 1rem;
    }    
}

.navbar .navbar-nav .nav-item {
    position: relative;
}
.navbar .navbar-nav .nav-item::after {
    position: absolute;
    /* content: '...'; */
    bottom: 0;
    left: 0;
    right: 0;
    content: '';
    background-color: #062F87;
    /* width: 100%; */
    width: 0%;
    height: 4px;
    transition: all .5s;
    margin: 0 auto;
}

.navbar .navbar-nav .nav-item:hover::after {
    width: 100%;
}
```





- 로고를 사용하고 메뉴들을 가운데로
  - [유튜브](https://www.youtube.com/watch?v=hK6dMdxt3hQ&list=PLEGWy2sQ80YteTylA0vinRlvF-n-LuIHg&index=5)



1. logo를 쓰기 위해 `a태그인 navbar-brand`에 텍스트를 지우고 img scr=""태그를 넣는다.

   - 이미지 크기를 조절하지 않으니 

     ![image-20221031223813683](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031223813683.png)

2. `a태그인 navbar-brand`를 `ul navbar-nav`내부 **li와 동일선상으로 복사해서 원하는 위치**로 옮기고, **기존 위치의 로고는 주석처리내놓는다(for 햄버거)**

   ![image-20221031224909485](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031224909485.png)

3. css로 `.nav-brand img {}`로서 해당a태그 class내부의 img태그에 대해서 **width로 그림크기를 조절한다**

   - **나는 일단 height를 navbar item들에 맞게 56px로 맞춤**

   ![image-20221031225630363](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031225630363.png)

4. `ul태그인 navbar-nav`에 **mx-auto** class만 넣어주면, 가운데로 모인다.

   ![image-20221031230050413](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031230050413.png)
   ![image-20221031230747288](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031230747288.png)

5. `a태그 .navbar-brand` 우측에 margin이 생겨서 벌어진다면, margin-right를 0으로 줘서 조절한다. (.navbar-brand 종특일 것 같다)

   ![image-20221031231030771](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031231030771.png)
   ![image-20221031231120490](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031231120490.png)

6. **`ul navbar-nav`를 보면 flex로서 자식들인 `li nav-item들`을 align-items:center;** 로 정렬할 수 있다.

   - ~~나는 그림을 좀더 키우고, 세로축정렬을 flex-end로 했다.~~
     - underline hover가 있기 때문에
   - **만약, lg에서 아래쪽 정렬하고 싶다고, flex-end를 선택하면, 햄버거에서도 우측정렬되기 때문에, 따로 처리할 예정** 

   ![image-20221031232232545](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221031232232545.png)



7. 기존 주석처리했떤 원래위치의 logo태그를 살리고, 확인한 뒤,

   - **img태그에 `d-lg-none` class를 줘서 lg모드에선 안보이게 한다**
     ![image-20221101014933261](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221101014933261.png)

     ![image-20221101015044598](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221101015044598.png)

     ![image-20221101015054442](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221101015054442.png)

8. 가운데 logo는 **원래는 안보이는데, lg에서만 보이도록`d-none d-lg-block`class를 준다**

   ![image-20221101015309340](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221101015309340.png)

   ![image-20221101015349258](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221101015349258.png)





9. **글자의 스타일을 `a태그인 .nav-link`**에다가 준다. color, font-size, padding

   - **이 때, 맨안쪽 .nav-link의 좌우패딩은 0 -> 대신 .nav-item의 margin으로 간격을 준 상태다(`underline hover가 글자에만 가득차도록`)**

     - color와 font-size, **필요하다면 `link의 세로padding` or `item의 가로 margin`만 `media쿼리`에서 조정**

     

10. **일관된 logo img태그를  와이드 <-> 햄버거 다르게 하기 위해서**

    1. logo img태그를 똑같이 복사한 뒤
    2. **현재 크기를 와이드에만 적요하기 위해 @미디어쿼리에서 잘라넣고**
    3. 기존 img태그의 크기를 줄여준다
       - 그대로 있던 것이 햄버거용 사이즈이며 조금 줄여준다
       - **기존img태그라고 해도 영향을 미쳐서.. @media쿼리안에 넣어주고, lg일때는 더 위쪽에 빼서 선언해줬다.**
    4. my) 기존img태그 == 햄버거용 img태그를 가운데 정렬되게 하고 싶어서
       1. 햄버거태그는 더 위에 놓아서 왼쪽으로 가게하고
       2. 로고태그는 `mx-auto`를 통해 햄버거를 제외하고 가운데정렬임시처리





11. **dropdown이 부모의 왼쪽으로만 되는 것 수정하기(가운데보다 우측일 땐, 왼쪽으로 dropdown하기) - 필수를 붙여서 만듦**
    1. 가운데어서 우측메뉴에 대해 hover뿐만 아니라 hover에는 안먹히지만 **클릭시 우측으로 내려오려면, `<div class="dropdown-menu" ~ >태그 에  dropdown-menu-end`를 추가한다** 
    2. **hover(.dropdown-menu)를 부모(.dropdown) end정렬하려면, `부모인 .dropdown:hover`를 `flex`로 만들고, `자식들이 end정렬`될 수있게 한다**
    3. end정렬은 부모의 아래우측이 아니라, 우측에서부터 시작하므로 **자식들(.dropdown-menu)은 top속성으로 부모로부터 아래로 좀 내려와야한다.**
       - **top:100%로 호버 추후 해결함**
    4. 위우 모든 것들이 lg상태에서만 이루어지게 **3번 top속성을 제외하고 @media쿼리**에 넣는다.
    5. 자식들마다 border-left줬던 것을 lg @media로 옮긴다
    6. sm햄버거에서 글자를 가운데 정렬하기위해 **모든 `a태그 nav-link`에 `text-center` class를 추가한다**
    7. 먼저나온 왼쪽메뉴hover가 오른쪽메뉴 클릭시 안보이기 때문에 hover에 대해서 z-index를 준다.

```css
/* 1. nav-item dropdown -> hover + mega menu */
.dropdown-menu {
    border-radius: 0;
    padding: .5em;
    /* box-shadow: 0 3px 6px rgba(0, 0, 0, .23); */
    border: none;
    /* border-top: 4px solid #062F87!important; */
    /* border-bottom: 2px solid #062F87!important; */
    /* dropdown 메뉴들 텍스트 정렬 */
    text-align: center;
    /* 부모의 right에 정렬 */
}

.dropdown-menu ul {
    list-style: none;
    padding: 0;
    /* 1.5 dropdown-menu 속 ul마다 border-left주기 */
    /* lg로 이동 */
    /* border-left: 1px solid #dde1ee; */
}

/* 1.6 첫번째는 안주기 */
.dropdown-menu ul:first-child {
    border-left: none;
}

.dropdown-menu li a{
    color: gray;
    padding: .5em 1em;
    /* font-size: small; */
    font-size: 0.6em;
    font-weight: bold;
}

.dropdown-menu li:first-child a{
    color: #062F87;
    font-size: 0.7em;
    font-weight: bold;
    text-transform: uppercase;
}

@media screen and (min-width:993px) {
    .dropdown:hover .dropdown-menu {
        display: flex;
        /* 필수 9: hover일 때 z-index줘서 가장 위로 -> 뒷메뉴 떠있을때, 앞메뉴호버는 더 위로 감 */
        z-index:5555
    }
    /* 필수2: 부모가 flex가 되어, 자식들을 나의 end에 정렬한다. */
    /* li nav-item dropdown은 부모로서 display:flex로 만들고, 자식들(dropdown-menu)는 end에 오게 한다 */
    /* 이 때, 모든.dropdown이 아니라 .dropdown 내부 .dropdown-menu에-end를 달고 있는 놈들만 */
    .dropdown:hover:has(div.dropdown-menu-end){
        display: flex; 
        justify-content: end;
    }
    
    .dropdown-menu.show {
        display: flex;
    }

    /* 2. level 0(nav-item) underline hover */
    .navbar {
        padding: 0;
    }
    .navbar .navbar-nav .nav-link {
        /* padding: 1rem; */
        padding: 1rem 0;
    }    
    .navbar .navbar-nav .nav-item {
        /* padding: 1rem; */
        margin: 0 0.6rem;
    }
    
    .dropdown-menu ul {
        /* 1.5 -> 필수5. dropdown-menu 속 ul마다 border-left주기 */
        /* lg로 이동 */
        border-left: 1px solid #dde1ee;
    }

/* 필수 5. underline은 lg일때만 작동하도록 변경(dropdown열릴때와 아래쪽이 겹침) */
    .navbar .navbar-nav .nav-item::after {
        position: absolute;
        /* content: '...'; */
        /* bottom: 0; */
        bottom: 10%; /* unlderline 높이<-> 메뉴와의 거리**/
        left: 0;
        right: 0;
        content: '';
        background-color: black;
        /* width: 100%; */
        width: 0%;
        height: 3px; /* underline hover*/
        transition: all .3s;
        margin: 0 auto;
        
    }

    .navbar .navbar-nav .nav-item {
        position: relative;
    }
}

/* 3. 3번대 로고 크기 조절 */
.navbar-brand img {
    width: 200px;
    margin-bottom: 20px;
}

@media screen and (max-width:992px) {
    .dropdown-menu.show {
        max-height: 30vh;
        /* max-height: 350px; */
        overflow-y: scroll;
    }


    /* 3번대 햄버거 로고 크기 조절 */
    .navbar-brand img {
        width: 180px;
        margin-bottom: 5px;
    }

}



@media screen and (min-width:993ppx) {
    
}


.navbar .navbar-nav .nav-item:hover::after {
    width: 100%;
}

/* 3. 로고 사진 및 메뉴 정렬 */

/* 로고를 가운데 위치시킬 때  왼쪽시위치의 margin을 제거낄 때,  */
.navbar-brand {
    margin-right:0;
}
/* 로고의 글자들 세로 정렬 ul navbar-nav 속 li들은 flexbox들임. */
/* 만약, lg에서 아래쪽 정렬하고 싶다고, flex-end를 선택하면, 햄버거에서 block들로서 오른쪽 정렬된다. */
.navbar-nav {
    align-items: center;
    /* align-items: flex-end; */
}

/* menu 글자들 스타일 지정. 좌우padding만 주지말자 for underline hover */
.navbar .navbar-nav .nav-link {
    color: black;
    font-size: 0.9em;
    font-weight: bold;
}




/* 5. 왼쪽으로 dropdown 시도 */
/* 필수1: 클릭시 그대로 보존되려면 <div class="dropdown-menu" 에  dropdown-menu-end class 달아주고 오기 */
/* -> 가운데 로고보다 더 오른쪽메뉴의 dropdown-menu에 대해서만 달아주기 */


/* 필수3: end정렬은 아래가 아니라 부모의 오른쪽벽에 붙어서 시작하므로
부모의 top으로부터 떨어져야함. */
.dropdown-menu {
    top: 53px; /* dropdown <-> menu 사이 거리: 너무 멀어지면 hover에서 클릭이 어렵다*/
    /*top:100%로 해결<===========*/
}

/* 필수4: 이 모든 것들이 large상태일때만으로 다시 이동 */


/* 필수6~7. 햄버거에서 dropdown a nav-link show 가 될때, 가운데 정렬이 안되고 삐져나감 */
/* a.nav-link.show {
    justify-content: center;
} */
/* 필수7. 넣었어도 hover가 작동하여.. flex가 되어 좌우로 갈라짐. -> 필수 2가 햄버거에도 영향*/
/* -> 필수2를 lg에 집어놓고 */
/* => 햄버거에서 a태그 nav-link에는 모두 text-center가 있어야한다. 평소에도 다 집어넣자 */

/* 필수8. lg에서는 dropdown 클릭시 고정되는 div기능 아예 빼자 by d-none?*/
/* -> 일케 하면, 메뉴선택이 빡세서, 나오게 함 + hover에 z-index */

```





#### menu 모델에 level_seq칼럼 추가

```python
    # 23. 그룹별 / level별 / 따로 [변경가능한 level별메뉴순서]를 칼럼으로 새로 만든다.
    # => 외부에서 전체조회시 order_by( 그룹칼럼, level칼럼, level_seq칼럼)순으로 모은다
    # - unique를 준다면, 변경시 에러날 것 같아서 안줌.
    # - level별 seq는 부모빼고 다 주면 될듯??
    level_seq = Column(Integer)

```



#### 어차피 그룹은 변하지 않을  timestamp(created_at)으로 할테니, category는 삭제하고, template_name 칼럼을 만들어서 연달아서 작성되도록 한다.

- 부모는 default ''을 줘서 treatment_.html이 되게 한다?

- 자식은 template_name을 이용해 treatment_cervial.html이 되게한다

  - **자신의 template_name => setter용필드로 full_template_name이 있어야한다**

  ```python
  # 26. category는 path로 대체할 수 있으니 삭제한다?
  #    endpoint도 같이 삭제하고 template_name으로 대체한다.
  self.full_template_name = (self.parent.template_name + '_' + self.template_name) if self.parent else self.template_name
  
  ```

  

  ![image-20221102021215310](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221102021215310.png)



### 폰트 적용 정리

1. [한림대학교 홈페이지](https://www.hallym.ac.kr/hallym_univ/sub04/cP5/sCP4/tab4.html)에서 폰트 다운

2. static > **font폴더 생성 후 갖다놓기** 

   ![image-20221107234203108](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221107234203108.png)

3. static > css >  **font.css 생성후 아래 코드 적용하기**

   ```css
   /* @import "url(https://fonts.googleapis.com/earlyaccess/notosanskr.css)"; */
   /* https://www.hallym.or.kr/common/css/HallymM.woff */
   
   @font-face {
       font-family: 'HallymR';
       src: url('../font/HallymR.eot');
       src: url('../font/HallymR.eot?#iefix') format('embedded-opentype'),
       url('../font/HallymR.woff') format('woff');
       font-weight: normal;
       font-style: normal;
   }
   
   @font-face {
       font-family: 'HallymM';
       src: url('../font/HallymM.eot');
       src: url('../font/HallymM.eot?#iefix') format('embedded-opentype'),
       url('../font/HallymM.woff') format('woff');
       font-weight: normal;
       font-style: normal;
   }
   
   
   @font-face {
       font-family: 'HallymB';
       src: url('../font/HallymB.eot');
       src: url('../font/HallymB.eot?#iefix') format('embedded-opentype'),
       url('../font/HallymB.woff') format('woff');
       font-weight: normal;
       font-style: normal;
   }
   
   table, ul, li, dl, dd, dt, ol, table, th, tr, td, thead, tbody, h1, h2, h3, h4, div, p, span, html, form, input, button, select, textarea, checkbox, fieldset {
       font-family: "HallymR", sans-serif !important;
   }
   ```

4. header에 맨 밑에 font.css 걸어주기

   ```html
       <link rel="stylesheet" href="../static/css/navbar.css">
       <link rel="stylesheet" href="../static/css/font.css">
   </head>
   ```

   



### 과정 스샷

![image-20221102031612623](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221102031612623.png)

![553f3e2c-1627-4050-8a08-62cfee0e2996](https://raw.githubusercontent.com/is3js/screenshots/main/553f3e2c-1627-4050-8a08-62cfee0e2996.gif)





![440fca52-8f9e-455a-9840-b75b1f8b2a2f](https://raw.githubusercontent.com/is3js/screenshots/main/440fca52-8f9e-455a-9840-b75b1f8b2a2f.gif)







### html css 수정

- menu3에 대해 border를 첫번째 ul제외하고 다 ul로 그리던 것을

  ```css
  .dropdown-menu ul:first-child{
      border-left: none;
  }
  ```

- **첫번째 ul제외,  첫번째li제외(menu2),  각 li들(menu3)에 맞춰서 그리도록 변경**

  ```css
  /*.dropdown-menu ul {*/
  /* 커스텀: menu2말고 menu3들 중에서도 li태그들에만 줘서 글자들 있는 곳에만*/
  .dropdown-menu ul:not(:first-child) > li:not(:first-child) {
      /* 1.5 -> 필수5. dropdown-menu 속 ul마다 border-left주기 */
      /* lg로 이동 */
      /*border-left: 1px solid rgba(228, 231, 241, 0.91);*/
      border-left: 1px solid rgba(228, 231, 241, 0.85);
  }
  
  ```

  





### 메가메뉴로 변경

1. `li nav-item dropdown`태그에 **`has-megamenu` custom class를 추가한다**

   - `div dropdown-menu`태그에 **`megamenu` class 밑 `role="menu"`를 추가한다**
     - 기존의 조건에 따른 dropdown-menu-end 달아주던 수식을 삭제한다

2. lg @media 쿼리에 `.navbar .has-megamenu` 및 `.navbar .megamenu` CSS를 추가한다

   - 왼쪽 정렬되던 것을 가운데정렬하기 위해 justify-content: center; 추가함

   ```css
   .navbar .has-megamenu{position:static!important;}
   .navbar .megamenu{left:0; right:0; width:auto; margin-top:0; justify-content: center; }
   ```

3. 이렇게만 할 경우 nav-item에 걸리던 underline 이 meganu로 엄청 넓어짐

   - lg media에 있던 **`nav-item`에 걸어둔 underline관련 after, padding 등 모든 css를 `nav-link`(한단계 위)로 변경**해준다



### 메뉴1별 img넣어주기

- menu model에

  - has_img
  - img_url 을 추가하고
  - has_img일 경우, 맨앞에 보여주도록 변경해야할 듯
  - **has_img일 경우, 업로드된 img번호를 img/menu/에 파일명과 함께 보관해야할듯**

  ![image-20221105180322279](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221105180322279.png)



#### 배경 기록

![image-20221105214817269](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221105214817269.png)

- 안쪽 `.dropdown-menu ul {`
  - sm과 공통
- 바깥넓은면 `.dropdown-menu {`





- **현재는 바깥 -> 안쪽에 border-top을 줌**

  - 그림 넣으려했더니 효과없이 주려니 별로임

  ![image-20221105223202388](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221105223202388.png)

  ![image-20221105224936548](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221105224936548.png)

#### 배경넣어보기(lg만 완성 미완, 캐러샐 + MainBanner 게시판에서 재료받아와서 처리할듯)

https://www.youtube.com/watch?v=W87XNjvXiWw



1. div masthead에  div

   ```html
   <div
        class="masthead"
        style="background-image: url('../static/img/bg1.png');"
        >
       <div class="color-overlay d-flex justify-content-center align-items-center">
           Test
       </div>
   </div>
   ```

2. masthead css로 납닥한 div 키워주기

   ![image-20221106034744817](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221106034744817.png)

![4224c5e9-98fe-4666-9b1b-1e53a642c052](https://raw.githubusercontent.com/is3js/screenshots/main/4224c5e9-98fe-4666-9b1b-1e53a642c052.gif)

![4f501710-7acc-44d4-aa4b-953c9aa4bd11](https://raw.githubusercontent.com/is3js/screenshots/main/4f501710-7acc-44d4-aa4b-953c9aa4bd11.gif)





#### 트랜지션 주기

1. lg 미디어 쿼리에서 **`.dropdown-menu(hover전)`에 `display:flex;`를 명시해줘야함**
   - 자식들이 block이면 block으로 줘야하는 듯. 일단 명시
2. **`.dropdown-menu(hover전)`에 opacity 0 으로 만들고**
   - **opacity 이외에 height등으로 하면 안됨. 그 내부요소들이 모두 flex라.. 넘쳐버림**
3. **`.dropdown:hover .dropdown-menu`(hover후)에는 opacity1에 + transition을 줘야함.**
4. **버그발생: hover전으 놈을 `display:flex`를 줌으로 인해, opacity0이라도 요소들이 살아있어 빈영역(banner쪽에 마우스를 가져다되도 매뉴가 뜸) -> `opacity외에 flex는 visibility : hidden도 줘야한다`**
   - **이제hover쪽에서는 `opacity 1 이외에 visibility: visible`도 줘야한다.**

```css
	.dropdown:hover .dropdown-menu {
     
    /* 생략 */
        
        /*t필수3: hover시 transition을 줘야한다.*/
        opacity: 1 ;
        /*transform: translateZ(0);*/
        /*필수5: flex는 opacity0이외에 visible hidden까지 줘야하므로, 다시 살려준다*/
        visibility: visible;
        transition: all 0.4s ;
    }
    /* transtition 주기 위해 hover이전에는 opacity 0 + transition */
    .dropdown-menu {
        opacity: 0 ; /*t필수2: hover전, 투명도를 0*/
         /*transform: translate3d(0, -5%, 0);*/
        display: flex; /* t필수1: hover전, display를 똑같은 것으로 지정해줘야한다*/
        /*t필수4: hover전이 flex로 변함으로 인해, opacity 0이라도 가상으로 살아있게 되어버려, hover가 아래쪽에서 발생하여 banner가 안보임 -> hidden*/
        visibility: hidden;
    /*  flex를 이용하는 이상, 안에 구조물때문에 height조정은 못함.*/
    /*    transition을 주다보면, hover로 메뉴걸러들어가는게 잘안될 수 있ㅇ므.*/
    }
```



![d1ef7fd7-5eb5-436e-ad32-764fac27f740](https://raw.githubusercontent.com/is3js/screenshots/main/d1ef7fd7-5eb5-436e-ad32-764fac27f740.gif)



### 메뉴1별 img넣기 css 수정

- 넣어주되, 위쪽 menu2 의 ul border로서는 제거
  - `:not` `:has`를 입혀서 제외하고 border그리도록
- **동적으로 크기 맞추려면 relative -> absolut  + min-height100%**으로 주면 되는데 **absolute로서 떠버리니, 직접 또 옮겨줘야하는 불편함.**
  - 그냥 이미지 크기를 통일해서 만들도록 해야할 듯

```css
/*lg일때만, ul==menu2 위마다 border */
/*.dropdown-menu ul {*/
/*border-top: 1px solid gray;*/
/*    }*/

/* lg ul==menu1의 그림 추가할 땐 border안뜨도록 제외하고 그리기..*/
/*img태그를 가지지has 않는 not*/
.dropdown-menu ul:not(:has(img)){
    border-top: 1px solid gray;
}
```

![image-20221107011333068](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221107011333068.png)

![image-20221107011340790](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221107011340790.png)

![95409c73-1799-49be-8b18-68600a33470b](https://raw.githubusercontent.com/is3js/screenshots/main/95409c73-1799-49be-8b18-68600a33470b.gif)





### menu1의 img url필드를 삭제하고, full_template_name으로 사용대체한다

- front에서는 .png로 통일하며, **나중에는 메뉴작성 업로드시 해당파일을 저장폴더 / full_template_name.png로 저장하게 해야할 듯.** 



1. menu model에서 has_img만 남겨두고, img_url 필드를 삭제한다.

2. 데이터 생성시 url작성은 할 필요 없다.

3. main.py에서도 초기데이터에서 img_url=필드 입력은 삭제한다

4. src>img>**menu폴더를 만들고, level 0 menu1의 `full_template_name.png`로 메뉴이미지들을 마련해놓는다.** 

   ![image-20221107235454738](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221107235454738.png)
   ![image-20221107235540600](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221107235540600.png)

   ![image-20221108000804723](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108000804723.png)

5. 프론트에선 has_img True일 경우, menu1의 이미지를 고정된 + full_template_name으로 뿌리도록 변경

   ![image-20221108003407394](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108003407394.png)

   ![image-20221108001001246](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108001001246.png)

   ![f5990aa6-3314-4574-b4c2-8f44439bf74a](https://raw.githubusercontent.com/is3js/screenshots/main/f5990aa6-3314-4574-b4c2-8f44439bf74a.gif)



#### sm 햄버거일때, 배경 및 각 아이템 간격 주기

```css
/*sm일때 navbar-nav의 배경 추가 */
.navbar-nav {
    background-color: rgba(255, 255, 255, 0.80) !important;
}
/*sm일때도 hover오픈 메뉴 z-index추가*/
.dropdown .dropdown-menu {
    z-index: 999 !important;
    /*sm일 때, 배경 추가*/
    border: 1px solid rgba(228, 231, 241, 0.95);
    border-radius:15px;
}
/* sm일때 각각의 menu에 margin추가  */
.dropdown-item {
    margin: 2px;
}
```

![image-20221108183111622](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108183111622.png)
![image-20221108183118286](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108183118286.png)



#### sm 햄버거일때만(d-lg-none)을 menu2파란색 메뉴 앞쪽에 달아주기

![image-20221108185051194](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108185051194.png)

![image-20221108185105084](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108185105084.png)

- border랑 배경줌

  ![image-20221108192700069](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108192700069.png)
  ![image-20221108192710659](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108192710659.png)



- 메뉴 노가다 끝
  ![image-20221108234036961](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221108234036961.png)



### 공지+배너의 Notice 설계

#### 01 위키 + ERD (model) + linewalks(metho) 참고 설계

- [flask 위키 참고](https://wikidocs.net/106238)

- [ERD 참고](https://www.erdcloud.com/d/A8SPzXyvcxr6WAZBv)
  - 배너 vs 공지를 따로 있는데 합쳐서 반영함
- [linewalks 참고](https://github.com/linewalks/Flask-Skeleton/blob/master/main/models/board.py)
  - create/update/soft delete반영함
  - **`get(id, is_delete)` `class method`로 시 classmethod로  id이외에 `delete_time이 없는 것을 가져오도록 where에` 걸어서 가져와야함.**
  - **`entity객체.update(title=, content= 등)`시 `inst method`로 `update_time에 현재시간 자동반영`해야함**
  - **`entity객체.delete()`시 `inst method`로 `delete_time에 현재시간 자동반영`해야함**

##### class Notice

1. src> infra > entities(tutorial3)에 `notices.py`를 생성

2. 모델 정의

   ```python
   class BannerType(enum.Enum):
       """defining Banner Types"""
   
       MAIN = "main"
       MODAL = "modal"
   
   
   class Notice(Base):
       __tablename__ = 'notices'
   
       id = Column(Integer, primary_key=True)
       is_sticky = Column(Boolean(), nullable=False)  # 항상 띄워두어야할 필수 공지냐
       is_banner = Column(Boolean())  # 배너용이냐? == 이미지도 있느냐
       title = Column(String(200), nullable=False)
       body = Column(Text)
       # body_html = Column(Text) # Bleach용
   
       hit = Column(Integer, nullable=False, default=0)
       # timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
       # 수정되는 날짜도 확인해야함. 수정자도 있어야 함.
       created_time = Column(DateTime, nullable=False, default=datetime.datetime.now)
       updated_time = Column(DateTime, nullable=False, default=datetime.datetime.now)
       deleted_time = Column(DateTime, index=True)  # 삭제 되지 않은 프로젝트 검색시 쿼리 성능 향상을 위한 index
   
       banner_title = Column(String(30))
       # img_url -> 배너용 title 존재하면   banner/ + banner_title . png로 save()에서 자동으로 채워준다.
       img_url = Column(Text)
       banner_type = Column(Enum(BannerType))  # main용이냐, modal용이냐
       exp_start_date = Column(DateTime, index=True, default=datetime.datetime.now)
       exp_end_date = Column(DateTime)
   
       # 작성자 와 좋아요 -> 인증 전까지 생략
       # register_author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
       # change_author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
       # like = db.relationship('User', secondary=post_recommend, backref='like_posts')
   ```





##### soft_delete된 것을 제외하고 골라오는 class get method

```python
@classmethod
def get(cls, notice_id, is_delete=False):
    # IS NULL, IS NOT NULL은  python None과 비교하면 된다.
    # .filter(User.name != None)
    # -> Entity.칼럼.is_()  와 .isnot( ) 도 존재한다.
    delete_condition = cls.deleted_time.is_(None) if not is_delete else cls.deleted_time.isnot(None)

    stmt = (
        select(cls)
        .where(and_(
            cls.id == notice_id, 
            delete_condition
        ))
    )

    with DBConnectionHandler() as db:
        return db.session.scalars(stmt).all()
```



#### 02 쿼리참고: akamatsu(dynamicMenu창시) + 패스트코드(pagination/booster.py) 

- [akamatsu](https://github.com/rmed/akamatsu/blob/master/akamatsu/models.py)
- [패스트코드](https://parksrazor.tistory.com/456)



##### setattr(객체, 칼럼명, value) 연습해보기

```python
class Node:
    def __init__(self):
        self.a = None
        self.b = None
        self.c = None

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[a={self.a!r}," \
                    f" b={self.b!r}," \
                    f" c={self.c!r}]"
        return info

if __name__ == '__main__':
    attrs = {
        'a' : '조',
        'b' : '재',
        'c' : '성',
    }
    node = Node()
    for column, value in attrs.items():
        setattr(node, column, value)

    print(node)
    # Node[a='조', b='재', c='성']
```



##### update시 필수 update_time자동입력을 이외에 is_banner아닌 경우, 안채워지는 필드가 많으므로, kwarg -> setattr(Entity-self, )를 이용한 인스턴스메서드로 입력된 것만 저장하도록 하기

```python
# (3) .update는 update_time 을 고려하여 정의하며,  인스턴스메서드로서, entity객체가 select된 상황에서, 객체.update()를 쳐준다.
def update(self, **kwargs):
    """Update instance attributes from dictionary.
    Key and value validation should be performed beforehand!
    """
    for k, v in kwargs.items():
        setattr(self, k, v)

    self.updated_time = datetime.datetime.now()

    with DBConnectionHandler() as db:
        # 객체 내부에서 read를 제외한 것은 모두 commit()하는 경우,
        # try except 씌워야한다. -> 성공하면 해당 객체를 반환해보자.?
        try:
            db.session.commit()
            # 객체에 연동되므로 굳이 반환안해도 될듯..?
            return self
        except Exception as e:
            db.session.rollback()
            raise e
```



##### soft_delete inst method -> self.필드를 채워서 commit()

```python
# (4) soft delete는 비어있는 delete_time을 채워주면 된다.
def soft_delete(self):
    self.deleted_time = datetime.datetime.now()
    with DBConnectionHandler() as db:
        try:
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e
```



##### .save(self)도 객체만들고.save()하면 내부에서 add commit하도록 맞춰주기 + 여기서img_url 자동으로 채워주기 (comments, menus와 통일)

```python
# (1) menu -> .save(self) 시 인스턴스메서드로서 add() flush() 후  self.객체필드 써서 추가필드 자동으로 작성되게 했었음.
def save(self):
    with DBConnectionHandler() as db:
        try:
            db.session.add(self)
            if self.is_banner:
                self.img_url = 'banner/' + self.banner_title + '.png'
                db.session.commit() 

                return self
            except Exception as e:
                db.session.rollback()
                raise e
```

![image-20221110005253083](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110005253083.png)

##### .영구삭제/pagination도 정의

- [linewalks 참고](https://github.com/linewalks/Flask-Skeleton/blob/master/main/controllers/board.py)







#### 03 연결설정 후 model 생성해서 테스트

##### 연결 설정



1. entities init에 올린다.

   ```python
   from .comments import Comment
   from .menus import Menu
   from .notices import Notice
   ```

   - **이것만 올려주면, 알아서 create_database -> main까지 사용될 entity들이 알아서 import**된다.

     ![image-20221110000303498](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110000303498.png)

2. 다른entity의 alt + F7로 import 중인 것 확인하기

   ![image-20221110000101175](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110000101175.png)

   - api_route.py

     ![image-20221110000134201](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110000134201.png)

3. **`기존 entity들이 생성코드`는  `main_xx.py로 백업`해두고 `truncate=True를 대비하여 create_database.py의 load_fake_data로 기존entity 생성코드를 load_fake_data로` 옮겨준다** 

   - 기존entity제외하고 **현재entity만 import -> truncate해도 기존entity 데이터들 모두 다 삭제**된다.

   ![image-20221110004143378](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110004143378.png)

   ![image-20221110004206866](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110004206866.png)





##### main.py에서 데이터 생성

```python
from create_database_tutorial3 import *
from src.infra.tutorial3.notices import BannerType

if __name__ == '__main__':
    # 1. init data가 있을 땐: load_fake_data = True
    # 2. add() -> commit() method save 등장부터는, 싹다 지우고 시작할 땐: truncate = True
    # 3. 테이블구조가 바뀌는 상황엔, 모든 table 지웠다 새로 생성: drop_table = True
    # create_database(truncate=True, drop_table=False)
    session = Session()
    create_database(truncate=True, drop_table=False)

    n1 = Notice(
        is_sticky=False,
        is_banner=False,
        title="개원 인사드립니다.",
        body="ㅎㅎㅎㅎㅎ"
    )

    n2 = Notice(
        is_sticky=False,
        is_banner=True,
        title="개원 이벤트: 패키지 상품을 10만원에 !",
        body="개원 기념 ~부터 ~까지 패키지 이벤트가 시행되었습니다.",

        banner_title='우아한 11월 이벤트',
        banner_type=BannerType.MAIN,
        exp_start_date=datetime.datetime(2022, 11, 1, 00, 00, 00),
        exp_end_date=datetime.datetime(2022, 11, 15, 23, 59, 59),
    )

    for n in [
        n1, n2
    ]:
        n.save()
```

![image-20221110005440283](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221110005440283.png)



#### sm일때 navbar 투명 감당안되서 그냥 배경 흰색으로 고정

```css
@media screen and (max-width: 992px) {
    /* sm일때 navbar의 색상변화 (기본은 투명)*/
    .navbar {
        background-color: rgba(255, 255, 255, 1) !important;
    }

```

![image-20221115021151469](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115021151469.png)

![image-20221115021157989](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115021157989.png)||![image-20221115021204921](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221115021204921.png)



### 다음 할 거

1. mainBanner로 올라갈 그림파일 업로드되는 게시판 생성

   1. 메인고정여부 필드 추가하기.(조회시 먼저 조회수, 나머지들 조회하여 결합?)

   2. banner용 부제필드 추가하여 캐러셀에 뿌려지게 하기?

   3. 이벤트게시물여부 + 시작/종료일(혹은 기간으로 자동계산?) 필드 추가하기

   4. 이벤트 외 공지는 위쪽에 한번더 보이기

      ![image-20221109013746399](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221109013746399.png)

      1. wiki
      2. linewalks
      3. 미구엘 것 참고하여 모델짜기

2. rocks 나 boostrap5 유튜브 참고해서 carousel 적용하기

3. 로그인 결합

4. 대댓글과 결합

5. 메뉴(글자색필드, menutype(level, link, blog 등)) 완성되면 app에 등록 dynamicmenu참고해서 flask 구동시 자동으로 올라가게 하기

6. 대댓글과 합치기

7. 로그인

8. **개별 template파일이 아닌 markdown으로 만들어서 수정도 가능하게?**

   - How To Use Python-Markdown with Flask and SQLite | DigitalOcean - https://www.digitalocean.com/community/tutorials/how-to-use-python-markdown-with-flask-and-sqlite
   - **[Flask] Using Markdown on Flask - https://hdevstudy.tistory.com/149**
   - python-markdown
   - https://stackoverflow.com/questions/36247335/why-my-flask-pagedown-cant-has-a-newline-why-i-write-code-by-markdown
     - https://blog.miguelgrinberg.com/post/flask-pagedown-markdown-editor-extension-for-flask-wtf
     - **https://wikidocs.net/106238 대박인듯? 미구엘 wikidocs에 푸는데, 잘 정리된 듯**



