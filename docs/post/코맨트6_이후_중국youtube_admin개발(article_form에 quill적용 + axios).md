### article_form(post_form)에 quill js + axios.js 적용하기

- [axios 참고](https://tuhbm.github.io/2019/03/21/axios/)



#### 1 admin/article_form.html에 

##### 상속자식입장에서, 부모들 살펴보고,  js block열어주는 부모 확인하여 사용하기

- admin/article_form.html

  ![image-20221123222432976](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123222432976.png)

- admin/article.hmtl

  ![image-20221123222513970](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123222513970.png)

- admin/index.html

  ![image-20221123222546842](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123222546842.png)

- base.html

  ![image-20221123222606708](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123222606708.png)



- **base.html에서 `extra_head_style` block을 열어놓고 있으니, `자식들은 자기 필요할 때 여기에 js나 css를 채우면`된다.**



##### article_form.html에서 extra_head_style block열고 사용할 css/ js 입력하기

- 나는 현재 `jquery -> selectize`를 쓰고 있었다.

  - jquery는 base.html로 옮길지 검토해본다.

  ![image-20221123223011820](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123223011820.png)

```html
{% extends 'admin/article.html' %}

{% block extra_head_style %}
<!-- selectize css & jquery -> js   -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/css/selectize.min.css">
<script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/js/standalone/selectize.min.js"></script>

<!--quill & axios js-->
<link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet" />
<script src="https://unpkg.com/axios/dist/axios.min.js"></script>
{% endblock extra_head_style %}

```





##### form.context 구성요소 내부에 div#editor 공간 추가

```html
    <div class="field">
        {{ form.content.label(class='label') }}
        <div class="control">
            <!-- form input 중에 textarea는 class='input' 대신 class='textarea' + rows=''를 준다.  -->
            {{ form.content(class='textarea', rows="10", placeholder='Contents') }}
            <!--  markdown적용할 필드의 form.필드 input태그아래에 rich editor를 위한 div개설-->
            <div id="editor" style="height: 500px;"> </div>
        </div>
    </div>
```



##### extra_foot_script를 열어, quill js 추가 (css만 head에...)

```html
{% block extra_foot_script %}
<!--selectize init -->
<script>
    $(function () {
        // select태그를 selectize화 시켜서, tags들을 여러개 선택할 수 있게 한다.
        $('select#tags').selectize({
            plugins: ['remove_button'],
        });
    });
</script>

<!--quill js 추가(아마도 axios불러오고나서 해야되서?) -->
<script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
{% endblock extra_foot_script %}

```



#### 2 article_form.html에  [최초] vue_script block을 열어서 editor 초기화

- base.html

  - base에서는 **자신은 없지만 자식들마다 추가될 수도 있는 block을 만들어두었다.**
  - 이외에 자신이 있지만, 자식들에선 변경될 수 있는 부분도 block으로 만들어 내용을 채웠었다.

  ![image-20221123224428952](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123224428952.png)

##### quil객체 만들기



- vue_script야 말고 일반적으로 js를 작성하는 곳??

```html
<!--quill js 초기화 in vue block-->
{% block vue_script %}
<script>
    var quill = new Quill('#editor', {
        //debug: 'info',
        // modules: {
        //     toolbar: toolbarOptions
        // },
        theme: 'snow',
        placeholder: '내용을 작성해주세요.',
        readOnly: false,
        formats: {}
    })
</script>
{% endblock vue_script %}

```

- **현재까진 modules를 주석처리한 상태**만 화면이 뜬다.

  ![image-20221123225544492](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123225544492.png)

  - 주석을 풀면 현재는 에러뜬다.

    ![image-20221123230056881](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123230056881.png)

  - `toolbarOptions` 변수를 정의해줘야한다.



##### toolbar options 주기

```html
{% block vue_script %}
<script>
        var toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike', 'link'],        // toggled buttons
        ['blockquote', 'code-block', 'image'],

        // [{ 'header': 1 }, { 'header': 2 }],               // custom button values
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        // [{ 'script': 'sub'}, { 'script': 'super' }],      // superscript/subscript
        [{ 'indent': '-1'}, { 'indent': '+1' }],          // outdent/indent
        [{ 'direction': 'rtl' }],                         // text direction

        // [{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],

        [{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
        [{ 'font': [] }],
        [{ 'align': [] }],

        ['clean']                                         // remove formatting button
    ];
    var quill = new Quill('#editor', {
        //debug: 'info',
        modules: {
            toolbar: toolbarOptions
        },
        theme: 'snow',
        placeholder: '내용을 작성해주세요.',
        readOnly: false,
        formats: {}
    })
</script>
{% endblock vue_script %}

```

##### quill객체.on()옵션으로 onChange를 걸어, 작성마다 {{form.content}}로 만든 textrea#content의 id를 가진 html에 innerHTML로 내용 실시간 넣어주기

![image-20221123233013874](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123233013874.png)



```javascript
    // Listen to rich text and sync to the form
    quill.on('text-change', function (delta, oldDelta, source) {
        content.innerHTML = quill.container.firstChild.innerHTML;
    });
</script>
```



![image-20221123233255101](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123233255101.png)



##### 기존 content필드의 내용을 quill객체에 주입하기

```js
    // 기존 내용을 주입하기 위해, html요소들 미리 변수화
    var html = quill.container.firstChild.innerHTML;
    var content = document.querySelector("textarea[name='content']");

    // Listen to rich text and sync to the form
    quill.on('text-change', function (delta, oldDelta, source) {
        content.innerHTML = quill.container.firstChild.innerHTML;
    });

    // textarea[name='content']로 잡은 태그의 내용인.value로 quill에 집어넣기 by .pasteHTML
    quill.pasteHTML(content.value)

```

![image-20221123233938416](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123233938416.png)



##### debug: 'info' 옵션을 켜두고, 이미지 어떻게 올라가나 확인하기

- image를 업로드하면, base64로 텍스트로 기록된다.

  ![image-20221123234354403](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123234354403.png)



#### 3 이미지 업로드 처리

##### js

1. toolbar모듈을 변수로 얻어온 뒤

2. toolbar.addHandler('image',  함수객체변수 ) ;를 걸어준다

   ```js
   // upload image를 위한 handler 함수 추가
   var toolbar = quill.getModule('toolbar');
   toolbar.addHandler('image', showImageUI);
   ```

   

3. 그보다 위에 해당 함수객체변수를 = function() {} 로 정의해준다

   ```js
   // upload image를 위한 함수 선언
   var showImageUI = function () {
       console.log('asdkjlfalsd')
   }
   
   // upload image를 위한 handler 함수 추가
   var toolbar = quill.getModule('toolbar');
   toolbar.addHandler('image', showImageUI);
   ```

   - toolbar의 image를 클릭했을때 로그가 찍히는지 확인한다.

     ![image-20221123234824124](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221123234824124.png)

4. 애초에 file input태그가 존재하는지 받아본다

   ```js
   var showImageUI = function () {
       // 1. 애초에 file input태그가 존재하는지 받아본다. quill에서는 input class="ql-image" type="file"로 존재하나보다.
       var fileInput = this.container.querySelector('input.ql-image[type=file]')
       console.log(fileInput)
   }
   
   ```

   



5. **file input태그가 없으면 실시간으로 만들어줘야한다.**

   - 태그를 만들고

   - `.setAttribute(,)`로 속성을 주되 `type`과 `accept`까지 줘야한다.

   - `.classList.add()`로 class를 추가한다

     ```js
     var showImageUI = function () {
         // console.log('asdkjlfalsd')
         // 1. 애초에 file input태그가 존재하는지 받아본다. quill에서는 input class="ql-image" type="file"로 존재하나보다.
         var fileInput = this.container.querySelector('input.ql-image[type=file]')
         // console.log(fileInput)
         // 2. file input태그가 없으면 실시간 생성해야한다.
         if (fileInput == null) {
             fileInput = document.createElement('input');
             fileInput.setAttribute('type', 'file');
             fileInput.setAttribute('accept', 'image/png, image/gif, image/jpeg, image/jpeg, image/bmp, image/x-icon');
             fileInput.classList.add('ql-image');
         }
         console.log(fileInput)
     }
     ```

     

   ![image-20221124000338992](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124000338992.png)





6. **upload는 `file input`태그에 `change`를 addEventListener를 달아서 `aixos로 post`요청을 보낸다.**

   - 단 input태그의 `.files` 및 `.files[0]`이 null이 아닐때만이다.
   - 순서대로 진행하되, 마지막 fileInput태그를 click()까지 그림을 선택한다.

   ```js
   //3. fileInput태그에 change listener를 달아서
   // (1) fileinput에 든 files files[0]이 null이 아니라면,
   // (2) new Formdata()객체를 만들고
   // (3) fileinput에 있는 files[0]을 formdata에 'upload'이름으로 append하고
   // (4) axios()로 post요청을 보낸다. -> route완성전에는 log만 찍어본다.
   fileInput.addEventListener('change', function () {
       if (fileInput.files != null && fileInput.files[0] != null) {
   
           const formData = new FormData();
           formData.append('upload', fileInput.files[0]);
   
           axios({
               url: '',
               method: 'post',
               data: formData,
               headers: {'content-type': 'multipart/form-data'},
           }).then(res => {
               console.log('res>>>' + res);
           }).catch(err => {
               console.log('err>>>' + err);
           });
       }
   });
   
   // 4. fileINnput태그를 click()까지 해줘야 그림창이 열리고 -> change가 작동하게 된다.
   fileInput.click();
   ```

   ![image-20221124010454141](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124010454141.png)

   



##### app.py에 axios가 formdata를 post로 보낼 공통 upload route 만들기

- 원본에서는 admin.upload로 만드는데

- **upload자체는 main이든, admin이든 어디서든 일어날 수 있으므로 download_file처럼 `main > config > app.py`에 만든다?**

  - blueprint가 없으니 `@app.route`로 정의해야할 듯

- **`/uploads`폴더에 upload한 파일을 다운받기 위한 `/uploads/<path:filename>`은 `폴더명과 동일하게 url구성`해서 view에서 `url_for('uploads', filename=)`으로만 쓰기 위해서 이렇게 작명했지만**

- **파일업로드를 위한 `POST용 '/upload/'` route는 **

  - **실제 POST로 온 data에서는 file객체를**

  - querystring이 아닌 **path로 오는 directory_name을 받아, `업로드폴더하위, 파일을 저장할 개별폴더`로 지정할 수 있게 한다**

  - **그렇다며느, axios로 post요청할 때, post + url_path로 개별폴더를 지정해줘야할 것이다.**

    ```js
    axios({
        url: '{{ url_for("upload", directory_name="post") }}',
    ```

  

- src>main>config>app.py

  ```python
  # upload route
  # 1. POST로 FormData를 받긴 하지만, upload요청마다 '/uploads/`폴더 속 `개별디렉토리이름`은 요청마다 달라진다.
  # -> POST지만, path로 directory_name을 받아서, 업로드폴더의 하위 개별폴더로 지정해서 저장하도록 한다
  @app.route('/upload/<path:directory_name>', methods=['POST'])
  @login_required
  def upload(directory_name):
      if request.method == 'POST':
          # 2. 파일객체는 new FormData()객체 속 'upload'로 append했는데
          # -> request.files.get('upload')로 받아낼 수 있다.
          f = request.files.get('upload')
          # 3. file객체를 .read()로 내용물을 읽고 file size를 젠 뒤
          # -> file객체의 읽은 위치를 다시 처음으로 초기화해놓는다.(읽고 커서가 뒤로 갔지만, 다시 원위치
          file_size = len(f.read())
          f.seek(0)
          # 4. 업로드 파일 사이즈를 체크한다. form에서는 validators= [FileSize(max_size=2048000))]으로 해결
          # -> 사이즈가 넘어가면 alert를 띄울 수있게 message를 같이 전달한다.
          if file_size > 2048000:
              return {
                  'code': 'err',
                  'message': '파일크기가 2M를 넘을 수 없습니다.'
              }
          # 5. upload유틸을 이용해서, '/uploads/`폴더에 붙을 '개별디렉토리', file객체를 넣어주면
          # -> save할 path와 filename이 주어진다.
          # -> 그렇다면, front에서 upload할 개별디렉토리도 보내줘야한다?!
          upload_path, filename = upload_file_path(directory_name=directory_name, file=f)
          # print(upload_path, filename)
          # C:\Users\is2js\pythonProject\2022_sqlalchemy\uploads\post\28d12f83306f4bf6984c9b6bcef7dda5.png 28d12f83306f4bf6984c9b6bcef7dda5.png
  
          # 6. 저장 후 ok return 시  jsonify없이 그냥 dict로 반환한다?
          # -> 반환시 view에서 볼 img저장경로를 넘겨줘야, 거기서 표시할 수 있을 것이다.
         f.save(upload_path)
         # print(url_for('download_file', filename=f'{directory_name}/{filename}'))
         # /uploads/post/862e406dd33a48b6aed55e64e68586ff.png
        return {
         'code': 'ok',
         # 'url': f'/uploads/{directory_name}/{filename}',
         'url': url_for('download_file', filename=f'{directory_name}/{filename}'),
         }

  
  ```

  





##### js에 생성한 url_for + directory_name으로 요청을 보내서 찍어보기

```js
axios({
    url: '{{ url_for("upload", directory_name="post") }}',
    method: 'post',
    data: formData,
    headers: {'content-type': 'multipart/form-data'},
}).then(res => {
    console.log( res);
    console.log(res['url'])
}).catch(err => {
    console.log( err);
});
```

![image-20221124021817172](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124021817172.png)

- **res['url'] null이다**
- **`res.data['url']`에서 이미지 url을 가져와야한다**



##### 업로드후 저장경로의 img를 현재위치의 quill에 집어넣기

```js
axios({
    url: '{{ url_for("upload", directory_name="post") }}',
    method: 'post',
    data: formData,
    headers: {'content-type': 'multipart/form-data'},
}).then(res => {
    // (6)  route 자체에서 파일크기제한으로 'code': 'err'가 올 수 있다.
    if (res.data.code == 'err') {
        alert(res.data.message)
        return
    }
    // (7) 정상으로 이미지 url이 올경우, quill에서, 현재위치를 찾은 뒤, 넣고 다음칸으로
    var curr = quill.getSelection(true);
    quill.insertEmbed(curr.index, 'image', res.data.url);
    quill.setSelection(curr.index + 1);
}).catch(err => {
    console.log( err);
});
```

![image-20221124024249496](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124024249496.png)

![image-20221124024311807](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124024311807.png)





##### 정상 imgupload되었고, onchange로 인해 form.content에 데이터가 잘 찬다면, form.content는 display:none; 속성으로 돌린다.

```js
// 기존 내용을 주입하기 위해, html요소들 미리 변수화
var html = quill.container.firstChild.innerHTML;
var content = document.querySelector("textarea[name='content']");

//7. 작동확인이 끝나서, 자동으로 채워지는 content는 display:none으로 돌린다
content.setAttribute('style', 'display:none');

```

![image-20221124030157468](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221124030157468.png)

- html 코드를 포함하는 text의 경우 jinja에서 |safe를 줘서 표기하고 있어서 코드가 아닌, markdown이 정상 표기된다.







#### 4 front - 46_article_form_change_after_upload_route(quill).html



```html
{% block extra_head_style %}

<!-- selectize css & jquery -> js   -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/css/selectize.min.css">
<script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.1/js/standalone/selectize.min.js"></script>

<!--quill css & axios js-->
<link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet"/>
<script src="https://unpkg.com/axios/dist/axios.min.js"></script>

{% endblock extra_head_style %}









{% block extra_foot_script %}
<!--selectize init -->
<script>
    $(function () {
        // select태그를 selectize화 시켜서, tags들을 여러개 선택할 수 있게 한다.
        $('select#tags').selectize({
            plugins: ['remove_button'],
        });
    });
</script>

<!--quill js 추가(아마도 axios불러오고나서 해야되서?) -->
<script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
<!--<script src="https://cdn.quilljs.com/2.0.0-dev.3/quill.js"></script>-->
{% endblock extra_foot_script %}









<!--quill js 초기화 in vue block-->
{% block vue_script %}
<script>
    var toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike', 'link'],        // toggled buttons
        ['blockquote', 'code-block', 'image'],

        // [{ 'header': 1 }, { 'header': 2 }],               // custom button values
        [{'list': 'ordered'}, {'list': 'bullet'}],
        // [{ 'script': 'sub'}, { 'script': 'super' }],      // superscript/subscript
        [{'indent': '-1'}, {'indent': '+1'}],          // outdent/indent
        [{'direction': 'rtl'}],                         // text direction

        // [{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
        [{'header': [1, 2, 3, 4, 5, 6, false]}],

        [{'color': []}, {'background': []}],          // dropdown with defaults from theme
        [{'font': []}],
        [{'align': []}],

        // table 1 : https://dalezak.medium.com/using-tables-in-quill-js-with-rails-and-stimulus-ddd0521ab0cb
        // ['table', 'column-left', 'column-right', 'row-above', 'row-below', 'row-remove', 'column-remove'],

        ['clean']                                         // remove formatting button
    ];
    var quill = new Quill('#editor', {
        debug: 'info',
        modules: {
            toolbar: toolbarOptions,
            // table: true
        },
        theme: 'snow',
        placeholder: '내용을 작성해주세요.',
        readOnly: false,
        formats: {}
    })

    // 기존 내용을 주입하기 위해, html요소들 미리 변수화
    var html = quill.container.firstChild.innerHTML;
    var content = document.querySelector("textarea[name='content']");

    //7. 작동확인이 끝나서, 자동으로 채워지는 content는 display:none으로 돌린다
    content.setAttribute('style', 'display:none');

    // Listen to rich text and sync to the form
    quill.on('text-change', function (delta, oldDelta, source) {
        content.innerHTML = quill.container.firstChild.innerHTML;
    });

    // textarea[name='content']로 잡은 태그의 내용인.value로 quill에 집어넣기 by .pasteHTML
    quill.pasteHTML(content.value)

    // upload image를 위한 함수 선언
    var showImageUI = function () {
        // console.log('asdkjlfalsd')
        // 1. 애초에 file input태그가 존재하는지 받아본다. quill에서는 input class="ql-image" type="file"로 존재하나보다.
        var fileInput = this.container.querySelector('input.ql-image[type=file]')
        // console.log(fileInput)
        // 2. file input태그가 없으면 실시간 생성해야한다.
        if (fileInput == null) {
            console.log("fileInput없다")
            fileInput = document.createElement('input');
            fileInput.setAttribute('type', 'file');
            fileInput.setAttribute('accept', 'image/png, image/gif, image/jpeg, image/jpeg, image/bmp, image/x-icon');
            fileInput.classList.add('ql-image');
        } else {
            console.log("fileInput있다")
        }
        //3. fileInput태그에 change listener를 달아서
        // (1) fileinput에 든 files files[0]이 null이 아니라면,
        // (2) new Formdata()객체를 만들고
        // (3) fileinput에 있는 files[0]을 formdata에 'upload'이름으로 append하고
        // (4) axios()로 post요청을 보낸다. -> route완성전에는 log만 찍어본다.
        fileInput.addEventListener('change', function () {
            if (fileInput.files != null && fileInput.files[0] != null) {

                const formData = new FormData();
                formData.append('upload', fileInput.files[0]);

                axios({
                    url: '{{ url_for("upload", directory_name="post") }}',
                    method: 'post',
                    data: formData,
                    headers: {'content-type': 'multipart/form-data'},
                }).then(res => {
                    // 5. route 자체에서 파일크기제한으로 'code': 'err'가 올 수 있다.
                    if (res.data.code == 'err') {
                        alert(res.data.message)
                        return
                    }
                    // 6.  정상으로 이미지 url이 올경우, quill에서, 현재위치를 찾은 뒤, 넣고 다음칸으로
                    var curr = quill.getSelection(true);
                    quill.insertEmbed(curr.index, 'image', res.data.url);
                    quill.setSelection(curr.index + 1);
                }).catch(err => {
                    console.log( err);
                });
            }
        });

        // 8. 원본에는 동적생성한 코드를 quill에 append해주는데, 딱히, 업로드의 역할만 하는거라서 안해줘도 된다?
        // this.container.appendChild(fileInput);
        // 만약 해주면, 글 수정시 file input태그가 있는 것으로 인식될 것이다?
        // 기본 wtf form에서 내려주는 input태그가 아니므로 안찍히게 된다. => 생략


        // 4. fileINnput태그를 click()까지 해줘야 그림창이 열리고 -> change가 작동하게 된다.
        fileInput.click();
    };

    // pload image를 위한 handler 함수 추가
    var toolbar = quill.getModule('toolbar');
    toolbar.addHandler('image', showImageUI);



</script>
{% endblock vue_script %}

```

