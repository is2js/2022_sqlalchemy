### carousel

#### vue 정리 블로그

- https://whitepro.tistory.com/242

  

#### base가 아닌 main / index.html에서 carousel의 test를 구현

- extends base.html만 한 상태

  ![image-20221127152358667](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127152358667.png)

- base.html의 구조

  ![image-20221127152813520](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127152813520.png)



1. **base.html의 hero를 주석처리 하고, `vue_script block` + `hero block`을 b-carousel + v-for로 구현한다**

   - base의 hero block -> **`section.hero > div.hero-body`로만 구성**

   ```html
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
   ```

   

2. **main/index.html에서 hero block을 구현**한다

   ```html
   {% extends 'base.html' %}
   
   {% block hero %}
   hero test
   {% endblock hero %}
   ```

   ![image-20221127152732705](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127152732705.png)



3. **base.html의 vue객체 생성과 함께 `carousels`변수를 초기화한다**

   ```html
   <script>
       var app = new Vue({
           el: '#app',
           delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
           data: {
               file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
               carousels: [], // admin/index에서 b-carousel-item에서 슬 변 수
           },
           methods: {}
       })
   </script>
   ```

4. **main/index.html에서는 초기화변수 carousels에 초기데이터를 삽입한다**

   - `app`이라는 초기화 vue객체에 `._data`로 접근하면 data로 초기화한 변수들에 접근할 수 있다.

   ```html
   <script>
       // 초기화된 app(vue객체)의 data는 ._data로 접근할 수있고 .변수로 base에서 초기화된 데이터에 데이터를 삽입할 수 있다.
       app._data.carousels = [
           {text: 'Slide 1', color: 'primary'},
           {text: 'Slide 2', color: 'info'},
           {text: 'Slide 3', color: 'success'},
           {text: 'Slide 4', color: 'warning'},
           {text: 'Slide 5', color: 'danger'},
       ]
   </script>
   ```

5. **here block에**

   - `template`

     - `b-carousel`

       - `<b-carousel-item v-for="(carousel, i) in carousels" :key="i">`

         - 돌아갈 b-carousel-item을 **v-for로 돌리되, index숫자가 key속성에 바인드 되기 위해서, 튜플형태로 돌리면서 :key=i를 넣어준다**
         - `<section :class="``hero is-medium is-${carousel.color}``">`
           - `<div class="hero-body has-text-centered">`
             - `<h1 class="title">{$ carousel.text $}</h1>`

         

   - **속성을 바인딩하고 싶다면, `:속성 = "바로변수"`를 쓰면 되지만**
     - **속성에 문자열과 섞어서 바인딩**하고 싶다면
       - **`:속성="``문자열 is-${변수}``"`**형식으로
         - ~가 쌍따옴표 양쪽으로 들어가고
         - 변수에는 `${}`를 붙여서 쓰면 된다.

   ```html
   <template>
       <b-carousel>
           <b-carousel-item v-for="(carousel, i) in carousels" :key="i">
               <section :class="`hero is-medium is-${carousel.color}`">
                   <div class="hero-body has-text-centered">
                       <h1 class="title">{$ carousel.text $}</h1>
                   </div>
               </section>
           </b-carousel-item>
       </b-carousel>
   </template>
   {% endblock hero %}
   
   ```

   ![image-20221127164834732](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127164834732.png)

   



##### front 67_base_change_for_carousel_test.html

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
            carousels: [], // admin/index에서 b-carousel-item에서 슬 변 수
        },
        methods: {}
    })
</script>
```



##### front 68_index_change_for_carousel_test.html

```html
{% extends 'base.html' %}

{% block hero %}
<!--1차) template > b-carousel > b-carousel-item안에 v-for로  base의 section태그를 돌린다. -->
<template>
    <b-carousel>
        <b-carousel-item v-for="(carousel, i) in carousels" :key="i">
            <section :class="`hero is-medium is-${carousel.color}`">
                <div class="hero-body has-text-centered">
                    <h1 class="title">{$ carousel.text $}</h1>
                </div>
            </section>
        </b-carousel-item>
    </b-carousel>
</template>
{% endblock hero %}

<!-- vue객체(app) 초기화 아래를 차지하는 vue_script block에 예시데이터를 만든다. -->
{% block vue_script %}
<script>
    // 초기화된 app(vue객체)의 data는 ._data로 접근할 수있고 .변수로 base에서 초기화된 데이터에 데이터를 삽입할 수 있다.
    app._data.carousels = [
        {text: 'Slide 1', color: 'primary'},
        {text: 'Slide 2', color: 'info'},
        {text: 'Slide 3', color: 'success'},
        {text: 'Slide 4', color: 'warning'},
        {text: 'Slide 5', color: 'danger'},
    ]
</script>
{% endblock vue_script %}
```



#### banner to carousel 구현

##### main.index route

- banner_list를 그대로 넘길게 아니라 **`img경로` + `url`의  `dict list -> json.dump -> json object`로 넘겨야한다.**



- 기존 index route

  - post_list와 pagination객체를 넘기고 있음.

  ```python
  @main_bp.route("/")
  def index():
      # post_list = [1, 2, 3, 4, 5, 6]
      page = request.args.get('page', 1, type=int)
  
      stmt = select(Post).order_by(Post.add_date.desc())
      pagination = paginate(stmt, page=page, per_page=9)
  
      post_list = pagination.items
  
      # 이미 내장된 img의 경로를 db에 존재하지 않는 필드지만 동적으로 삽입
      # -> error가능성) sample의 k보다 post가 많아지는 경우? 해당이 안될 수 있다.
      img_path_list = [f'img/post/post-{i}.jpg' for i in range(1, 15 + 1)]
      for post, img_path in zip(post_list, random.sample(img_path_list, k=len(post_list))):
          post.img = img_path
  
      return render_template('main/index.html', post_list=post_list, pagination=pagination)
  ```



- **banner의 `공지부터 앞 5개만` 조회한 뒤, json으로 변경해서 넘겨야 vue가 데이터를 받을 수 있다.**

  - 나중에는 기간에 해당하는 것으로 또 추려야할 듯

  - **json.dumps()시, 기본 한글이 아닌 유니코드로 저장되며 json.load()로 다시 한글로 복구된다. view로 넘겨서 쓸 것이기 때문에 `ensure_ascii=False`를 지정해준다.**

    ```python
    @main_bp.route("/")
    def index():
        # post_list = [1, 2, 3, 4, 5, 6]
        page = request.args.get('page', 1, type=int)
    
        stmt = select(Post).order_by(Post.add_date.desc())
        pagination = paginate(stmt, page=page, per_page=9)
    
        post_list = pagination.items
    
        # 이미 내장된 img의 경로를 db에 존재하지 않는 필드지만 동적으로 삽입
        # -> error가능성) sample의 k보다 post가 많아지는 경우? 해당이 안될 수 있다.
        img_path_list = [f'img/post/post-{i}.jpg' for i in range(1, 15 + 1)]
        for post, img_path in zip(post_list, random.sample(img_path_list, k=len(post_list))):
            post.img = img_path
    
        ## banner to json
        stmt = select(Banner).order_by(Banner.is_fixed.desc(), Banner.add_date.desc()) \
            .limit(5)
        with DBConnectionHandler() as db:
            banner_list = db.session.scalars(stmt).all()
        # baner객체들을 img, url만 가진 dict_list로 변환
        banner_list = [{'img': f'{url_for("download_file", filename=banner.img)}', 'url': banner.url} for banner in
                       banner_list]
        # json.load()로 읽어올 것이 아니라면, ensure_ascii=False를 필수로 해줘야 view에서 한글로 받을 수 있다.
        banner_list = json.dumps(banner_list, ensure_ascii=False)
    
        return render_template('main/index.html', post_list=post_list, pagination=pagination,
                               banner_list=banner_list)
    ```

    

##### div태그의 text부분에서 넣고 확인하기



```html
{% extends 'base.html' %}

{% block hero %}
<!-- backend에서 넘겨준 json을 div#banner_list + display:none;으로 banner_list를 받아본다-->
<!--<div id="banner" style="display:none;">-->
<div id="banner_list">
    {{ banner_list }}
</div>
```



![image-20221127172139207](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127172139207.png)





##### 새로운 방법( backend no json.dump -> vue에서도 편하게 쓸 수 있는 `dict_list | tojson` 필터만 적용하기)

- **json.dump하지말고 `dict_list`를 그대로 넘긴 뒤, `jinja의 필터 |tojson`을 활용한다**

```python
@main_bp.route("/")
def index():
    # post_list = [1, 2, 3, 4, 5, 6]
    page = request.args.get('page', 1, type=int)

    stmt = select(Post).order_by(Post.add_date.desc())
    pagination = paginate(stmt, page=page, per_page=9)

    post_list = pagination.items

    # 이미 내장된 img의 경로를 db에 존재하지 않는 필드지만 동적으로 삽입
    # -> error가능성) sample의 k보다 post가 많아지는 경우? 해당이 안될 수 있다.
    img_path_list = [f'img/post/post-{i}.jpg' for i in range(1, 15 + 1)]
    for post, img_path in zip(post_list, random.sample(img_path_list, k=len(post_list))):
        post.img = img_path

    ## banner to json
    stmt = select(Banner).order_by(Banner.is_fixed.desc(), Banner.add_date.desc()) \
        .limit(5)
    with DBConnectionHandler() as db:
        banner_list = db.session.scalars(stmt).all()
    # baner객체들을 img, url만 가진 dict_list로 변환
    banner_list = [{'img': f'{url_for("download_file", filename=banner.img)}', 'url': banner.url} for banner in
                   banner_list]
    # json.load()로 읽어올 것이 아니라면, ensure_ascii=False를 필수로 해줘야 view에서 한글로 받을 수 있다.
    # banner_list = json.dumps(banner_list, ensure_ascii=False)

    return render_template('main/index.html', post_list=post_list, pagination=pagination,
                           banner_list=banner_list)

```

```html
{% extends 'base.html' %}

{% block hero %}
<div id="banner_list">
    {{ banner_list | tojson }}
</div>
```

![image-20221127173512561](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127173512561.png)





##### base 및 index에서 실제 banner_list쓰기

- base.html

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
            // carousels: [], // admin/index에서 b-carousel-item에 test
            banner_list: [], // admin/index에서 b-carousel-item에서 슬 변 수
        },
        methods: {}
    })
</script>
{% block vue_script %}{% endblock vue_script %}
```

- main/index.html
  - **원래는 div태그에 json데이터를 박아두고, 그것을 queryselect할려했는데, 따옴표 + jinja문법을 이용해서 데이터 초기화**

```html
{% block vue_script %}
<script>
    // 초기화된 app(vue객체)의 data는 ._data로 접근할 수있고 .변수로 base에서 초기화된 데이터에 데이터를 삽입할 수 있다.
    // app._data.carousels = [
    //     {text: 'Slide 1', color: 'primary'},
    //     {text: 'Slide 2', color: 'info'},
    //     {text: 'Slide 3', color: 'success'},
    //     {text: 'Slide 4', color: 'warning'},
    //     {text: 'Slide 5', color: 'danger'},
    // ]
    // app._data.banner_list = JSON.parse(document.querySelector('#banner_list').innerHTML)
    app._data.banner_list = JSON.parse('{{ banner_list | tojson }}')
    console.log(app._data.banner_list)
</script>
{% endblock vue_script %}
```

![image-20221127180454048](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127180454048.png)





- b-carousel-item의 v-for를 **테스트변수 대신 banner_list 변수쓰기**
- **section으로 이미지만 뿌려줬떤 것을**
  - **`section대신 a태그`> figure > img**로 나타낸다

```html
<template>
    <b-carousel>
<!--        <b-carousel-item v-for="(carousel, i) in carousels" :key="i">-->
<!--            <section :class="`hero is-medium is-${carousel.color}`">-->
<!--                <div class="hero-body has-text-centered">-->
<!--                    <h1 class="title">{$ carousel.text $}</h1>-->
<!--                </div>-->
<!--            </section>-->
        <b-carousel-item v-for="(banner, i) in banner_list" :key="i">
            <a :href="banner.url">
                <figure class="image is-16by9">
                    <img :src="banner.img" alt="">
                </figure>
            </a>
        </b-carousel-item>
    </b-carousel>
</template>
```

![image-20221127182034984](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221127182034984.png)

##### front - 69_base_change_for_carousel_banner.html

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
            // carousels: [], // admin/index에서 b-carousel-item에 test
            banner_list: [], // admin/index에서 b-carousel-item에서 슬 변 수
        },
        methods: {}
    })
</script>
{% block vue_script %}{% endblock vue_script %}
```



##### front - 70_index_change_for_carousel_banner.html

```html
<template>
    <b-carousel>
<!--        <b-carousel-item v-for="(carousel, i) in carousels" :key="i">-->
<!--            <section :class="`hero is-medium is-${carousel.color}`">-->
<!--                <div class="hero-body has-text-centered">-->
<!--                    <h1 class="title">{$ carousel.text $}</h1>-->
<!--                </div>-->
<!--            </section>-->
        <b-carousel-item v-for="(banner, i) in banner_list" :key="i">
            <a :href="banner.url">
                <figure class="image is-16by9">
                    <img :src="banner.img" alt="">
                </figure>
            </a>
        </b-carousel-item>
    </b-carousel>
</template>






{% block vue_script %}
<script>
    // 초기화된 app(vue객체)의 data는 ._data로 접근할 수있고 .변수로 base에서 초기화된 데이터에 데이터를 삽입할 수 있다.
    // app._data.carousels = [
    //     {text: 'Slide 1', color: 'primary'},
    //     {text: 'Slide 2', color: 'info'},
    //     {text: 'Slide 3', color: 'success'},
    //     {text: 'Slide 4', color: 'warning'},
    //     {text: 'Slide 5', color: 'danger'},
    // ]
    // app._data.banner_list = JSON.parse(document.querySelector('#banner_list').innerHTML)
    app._data.banner_list = JSON.parse('{{ banner_list | tojson }}')
    console.log(app._data.banner_list)
</script>
{% endblock vue_script %}
```









#### custom indicator carousel 적용하기

- 똑같이 적용해주는데, **`template #indicators="props`태그가 추가되며**
  - v-for의 바깥이지만, **`props.i`를 통해 현재carousel의 번호**를 알 수 있다.
  - **methods를 이용해 banner_list[i]의 정보를 빼서 indicator에 표기한다**



##### base.html에서 indicator-props.i로 banner_list[i]를 꺼내올 메서드  및 truncate filter 정의

```html
<script>
    var app = new Vue({
        el: '#app',
        delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
        data: {
            file: {}, // admin/banner_form에서 b-upload에 쓰이는 변수
            // carousels: [], // admin/index에서 b-carousel-item에 test
            banner_list: [], // admin/index에서 b-carousel-item에서 슬 변 수
        },
        methods: {
            // main/index에서 props.i 정보 -> banner_list[i]로 banner객체를 얻게해주는 메서드
            getBannerImg(value) {
                return `${this.banner_list[value].img}`
            },
            getBannerTitle(value) {
                return `${this.banner_list[value].desc}`
            }
        },
        filters: {
            // main/index에서 너무긴 배너정보를 잘라주는 메서드
            truncate: function (text, length, suffix) {
                if (text.length > length) {
                    return text.substring(0, length) + suffix;
                } else {
                    return text;
                }
            },
        }
    })
</script>
```



##### main / index.html - indicator를 포함한 buefy carousel 도입

- indicator내부에서는 props.i + method로 banner정보를 가져오기

```html
<template>
    <b-carousel :indicator-inside="false">
        <b-carousel-item v-for="(banner, i) in banner_list" :key="i">
            <!--            <b-image class="image is-16by9" :src="banner.img"> </b-image>-->
            <a :href="banner.url">
                <figure class="image is-16by9">
                    <img :src="banner.img" alt="">
                </figure>
            </a>
        </b-carousel-item>
        <template #indicators="props">
            <b-image class="al image" :src="getBannerImg(props.i)" :title="props.i"></b-image>
            <h1 class="is-size-6 has-text-centered" style="color:black;">
                {$ getBannerTitle(props.i) | truncate(15, '...') $}
            </h1>
        </template>
    </b-carousel>
</template>
```



![image-20221128015348547](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128015348547.png)

![image-20221128015422574](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221128015422574.png)