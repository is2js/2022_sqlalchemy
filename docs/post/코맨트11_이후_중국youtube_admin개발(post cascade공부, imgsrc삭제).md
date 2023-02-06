



### category(1) - Post(many) 삭제



#### 현재 category(1) 삭제시 Post들이 걸려있는 경우, 제약조건 에러가 난다

- post가 부모를 분류3을 잡고 있다면

  ![image-20221128022854565](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128022854565.png)

- 분류3 삭제시 에러

  - 원래는 fk 제약조건이 걸려야하는데, Many table쪽 not null된다고 에러뜨는 중.

  ![image-20221128022909050](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128022909050.png)
  ![image-20221128023147887](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128023147887.png)



#####  현재 models

###### 1) category는 posts들을 모두 subquery로 들고 있지 않은 lazy=True

###### 2) category는 posts에게는 bacref를 주면서 subquery로 다 들고 있게

```python
class Category(BaseModel):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    icon = Column(String(128), nullable=True)

    posts = relationship('Post', backref=backref('category', lazy='subquery'), lazy=True)

```





### sqlite에 제약조건 적용되도록 설정하기

- DB_URI에 `sqlite`가 포함되는 경우
  - **engine에 event.listen()을 method로 걸어주는데**
  - 매번 `pragma foreign_keys=ON`를 수행시켜야한다

- **DBConnectionHandler**

  ```python
  class DBConnectionHandler:
      #... 
      def __create_database_engine(self, echo):
          # engine = create_engine(self.__connection_string)
          engine = create_engine(self.__connection_string, echo=echo)
  
          #### sqlite 인 경우, qeuery 날릴 때마다, 아래 문장을 execute해야, cascade가 정상작동한다
          # 1) many에서 ondelete='cascade' -> # 2) one에서 passive_deletes=True 로만 작동할 수있게 매번 제약조건 날려준다
          if 'sqlite' in self.__connection_string:
              def _fk_pragma_on_connect(dbapi_con, con_record):
                  dbapi_con.execute('pragma foreign_keys=ON')
  
              event.listen(engine, 'connect', _fk_pragma_on_connect)
  
          return engine
  ```

  



#### 참고블로그) cascade delete는 db와 달리 여러단계로 진행

- [참고블로그](https://dev.to/zchtodd/sqlalchemy-cascading-deletes-8hk)

- [참고블로그2](https://esmithy.net/2020/06/20/sqlalchemy-cascade-delete/)

#### 방법1

##### one Entity에서 cascade="all"만 줘도 자식들 같이 삭제된다.

```python
class Category(BaseModel):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    icon = Column(String(128), nullable=True)
    
    posts = relationship('Post', backref=backref('category', lazy='subquery'),
                         cascade="all", # 부모에게 cascade = "all"만 줘도 자식들과 같이 삭제된다.
                         # passive_deletes=True,
                         lazy=True)
```



##### one에만 cascade="all~"걸어줬을 때의 문제점 -> ORM에서만 작동하는 방법

- db의 제약조건과 달리 **ORM에서만 작동하는 설정**으로서 **raw SQL로 one entity를 삭제하면, Many는 삭제 안된다.**

  - 자식들 삭제 -> 자신삭제를 수행한다

  ```
  DELETE FROM song WHERE song.id = %(id)s
  DELETE FROM artist WHERE artist.id = %(id)s
  ```

- **ORM으로 Many를 먼저 다 찾아서 삭제하고, one을 삭제하니 복잡한 경우 너무 느려진다**

  - **`DB에 걸린 제약조건에 의해 -> 부모만 지우면, 자식들은 DB가 자동으로 삭제하게 해야한다.`**



#### 방법2

##### many Entity에서 ondelete="cascade"를 주면, 부모 삭제시, default는 자신의 fk는 NULL로 채운다.

- fk를 nullable=False로 주면 에러나서 삭제가 안된다.

- fk를 nullable을 허용하면, **부모만 삭제후, 자식들은 null이 채워진다.**
  - 부모의id가  NULL로 세팅된다. 
  - **수정form에선 부모id가 무조건 있다고 가정**했기 때문에, 
    - **부모null허용시 -> 수정form 수정**
    - **부모null허용안할시 -> 자식들 같이 삭제**
    - 휴지통부모를 만들어 -> 부모삭제시 자식set 휴지통fk_id로 놓기?



![image-20221128034703825](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128034703825.png)

![image-20221128034823706](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128034823706.png)



##### many에만 ondelete="cascade"를 줬을 때 문제점

- **DB의 ON DELETE CASCADE**와는 다른, **default로 NULL만 채우는 체제**가 된다.

  - 즉 db 제약조건은 여전히 무시됨. 부모삭제시 set null만 수행.

  ```sql
  CREATE TABLE artist (
          id SERIAL NOT NULL, 
          PRIMARY KEY (id)
  )
  
  CREATE TABLE song (
          id SERIAL NOT NULL, 
          artist_id INTEGER, 
          PRIMARY KEY (id), 
          FOREIGN KEY(artist_id) REFERENCES artist (id) ON DELETE cascade
  )
  ```



### 해결책: DB가 삭제하도록 ManyFK ondelete + OneRelationship Passive_deletes=True(One cascade배제)

```python
class Category(BaseModel):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    icon = Column(String(128), nullable=True)

    posts = relationship('Post', backref=backref('category', lazy='subquery'),
                         # cascade="all, delete",  # 방법1)
                         passive_deletes=True,  # 해결책1 - 이것을 주면, 부모만 삭제하고, 나머지는 DB가 수동적 삭제한다
                         lazy=True)

```

```python
class Post(BaseModel):
    #...

    # 해결책1) many에 ondelete를 줘야 db제약조건과 동일해지지만, 부모삭제시 set null을 기본 수행한다
    category_id = Column(Integer,
                         # ForeignKey('categories.id'),
                         ForeignKey('categories.id', ondelete="CASCADE"),
                         nullable=False
                         )
```









#### test

##### test1:  자식 ondelete='cascade'만 주는 경우 -> session.delete( obj )의 경우만, 자식들의 fk에 set null

1. session.delete( 객체 ) -> 메모리에 올린 객체로 삭제

   1. not null 에러

   ```
   UPDATE posts SET pub_date=?, category_id=? WHERE posts.id = ?
   
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: posts.category_id
   [SQL: UPDATE posts SET pub_date=?, category_id=? WHERE posts.id = ?]
   [parameters: ('2022-11-28 15:31:59.701558', None, 10)]
   
   ```

   - **`ORM` 자식들 먼저, fk를 `None으로 update`시키고 -> 자신 delete하는데 자식들에서 nullable=False에 걸림.**
     - **자식들을 삭제하는게 아니라, `자식들 속 fk를 set null `시킨다**

2. session.execute( 필터링 stmt )

   1. FK에러

   ```
   DELETE FROM categories WHERE categories.id = :id_1
   
   
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
   [SQL: DELETE FROM categories WHERE categories.id = ?]
   [parameters: (3,)]
   (Background on this error at: https://sqlalche.me/e/14/gkpj)
   
   ```

   - **`db`의 제약조건에 의해 실패한다**





##### test2: 부모에 cascade="all, delete"를 추가하는 경우 -> session.delete( obj )의 경우만, 자식들을 찾아 set null 대신 먼저 삭제 -> DB가 수동삭제할 것이므로 배제한다

1. session.delete( 객체 ) -> 메모리에 올린 객체로 삭제

   - `cascade가 적용`된다
   - **one쪽에 cascade="" 옵션은, FK제약조건과 무관하게 `자식부터 찾아 삭제` -> `나 삭제`의 과정을 거치게 된다.**
     - 주지 않았을때는 `자식들을 찾아 set null` -> not null에 걸림
     - 주면 `자식들을 찾아 삭제` -> `나 삭제`

   ```
   DELETE FROM posts WHERE posts.id = ?
   
   DELETE FROM categories WHERE categories.id = ?
   ```

   

2. session.execute( 필터링 stmt )

   - FK에러

   ```
   DELETE FROM categories WHERE categories.id = :id_1
   
   
   sqlalchemy.exc.IntegrityError
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
   [SQL: DELETE FROM categories WHERE categories.id = ?]
   [parameters: (3,)]
   (Background on this error at: https://sqlalche.me/e/14/gkpj)
   ```

   - **cascade="all, delete"를 적용해도 DB DELETE문은 DB의 제약조건에 걸리게 된다** 
     - **DB의 DELETE ON CASCADE는 적용안된다.**



##### test3: 부모에 passive_deletes=TRUE 추가 -> session.delete( obj )가 자신만 삭제하려고한다. 자식에 ondelete="cascade"만 있으면  DB제약조건에 자동삭제된다.

1. **DB처럼 제약조건**에 걸리게 된다.

   - **ORM이** **자식들을 찾아** SET NULL or 삭제하는 **과정을 사라지게 하고** **부모만 삭제하게 한다**
   - 이제 DB가 직접 ondelete로 삭제하게 해야하는데...

   ```
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
   [SQL: DELETE FROM categories WHERE categories.id = ?]
   [parameters: (3,)]
   (Background on this error at: https://sqlalche.me/e/14/gkpj)
   
   ```

2. **DB처럼 제약조건**에 걸리게 된다.











### 필드 content(text)에 img src를 가지고 있는 경우, 미리 img태그를 찾아 src에 해당하는 파일을 삭제

#### utils 정의

- bs4를 이용한다

  ```python
  def delete_files_in_img_tag(text):
      soup = BeautifulSoup(text, 'html.parser')
      page_imgs = [image["src"] for image in soup.findAll("img")]
      if page_imgs:
          for img in page_imgs:
              # '/uploads/post/4787c8a891334d8ebb372244b2f93000.png'
              directory_and_filename = '/'.join(img.split('/')[2:])  # 앞에 img src=""  중 "/uploads/" 부분을 제거
              delete_uploaded_file(directory_and_filename)
  
  ```



#### post삭제와 관련된 route들에 배치

##### post_delete

```python
@admin_bp.route('/article/delete/<int:id>')
@login_required
def article_delete(id):
    with DBConnectionHandler() as db:
        post = db.session.get(Post, id)
        
        # img태그 속 src를 찾아, 해당 파일 경로를 추적하여 삭제
        delete_files_in_img_tag(post.content)

        if post:
            db.session.delete(post)
            db.session.commit()
            flash(f'{post.title} Post 삭제 완료.')
            return redirect(url_for('admin.article'))
```





#### category_delete -> .posts 를 순회하며 삭제

```python
@admin_bp.route('/category/delete/<int:id>')
@login_required
def category_delete(id):
    # 1) url을 통해 id를 받고 객체를 먼저 찾는다.
    with DBConnectionHandler() as db:
        category = db.session.get(Category, id)
        if category:

            # post cascading 되기 전에, content에서 이미지 소스 가져와 삭제하기
            if category.posts:
                for post in category.posts:
                    delete_files_in_img_tag(post.content)

            db.session.delete(category)
            db.session.commit()
            flash(f'{category.name} Category 삭제 완료.')
            return redirect(url_for('admin.category'))

```

