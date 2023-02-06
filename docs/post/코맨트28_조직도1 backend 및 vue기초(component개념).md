### backend

#### .get_roots(cls): 일단 root(level=0) 객체들 부터 찾기

- **front에서 component를 사용한 재귀**를 돌리려면, `root 객체들`부터  한번더 dict화 해서, 내려보내줘야한다.

  - 일단 root객체들을 parent_id = None으로 찾아야한다

  ```python
  @classmethod
  def get_roots(cls):
      with DBConnectionHandler() as db:
          stmt = (
              select(cls)
              .where(cls.status == 1)
              .where(cls.parent_id.is_(None))
          )
  
          return db.session.scalars(stmt).all()
  ```

  

#### .get_all_tree(cls): 각 root객체들 기준으로 tree를 만든 뒤, tree_list를 dict로 한번 더 포장하기

- **json을 내려보내줄 땐, `data=`에 최종 데이터 dict를 할당해 내려보낸다.**

```python
@classmethod
def get_all_tree(cls):
    root_departments = cls.get_roots()

    tree_list = []
    for root in root_departments:
        tree_list.append(root.get_self_and_children_dict())

        return dict(data=tree_list)
```



##### .get_self_and_children_dict(self): 각 root객체들을 재귀로 개별 tree 만들기

1. 자신을 dict화 한 dict를 만든다.
2. `자식들`을 돌면서, 자식들이 있으면, `children`key안에 list안에 자식들을 넣고, 재귀를 태워서 dict화 하여 넣는다.
   - 자식들은 `.where(with_parent(self, Department.children))`를 활용하여 내자신 + 자식관계필드를 where절에 걸면 된다.

```python
    def get_self_and_children_dict(self):
        result = self.to_dict(delete_columns=['pub_date', 'path', 'type', ])

        children = self.get_children()
        if len(children) > 0:
            result['children'] = list()
            for child in children:
                # 내 자식들을 dict로 변환한 것을 내 dict의 chilren key로 관계필드 대신 넣되, 자식들마다 다 append로 한다.
                result['children'].append(child.get_self_and_children_dict())
        return result
```



##### .to_dict( delete_columns=[]): 각 객체들이 자신을 dict화 시킬 때, 사용하지 않을 칼럼들을 넘겨준다

- 일단 BaseModel에 정의해준 to_dict()로 전체필드를 dict화 시켜놓고

  - **BaseModel의 to_dict()에서 datetime/date 타입을 미리 string으로 변환시켜놓자**

  ```python
  def to_dict(self):
      # (2) dict comp쓰지말고, for문으로 돌면서, date/datetime 변환하기
      # return {c.name: getattr(self, c.name) for c in self.__table__.columns
      #         if c.name not in []  # 필터링 할 칼럼 모아놓기
      #         }
      data = dict()
  
      for col in self.__table__.columns:
          _key = col.name
          _value = getattr(self, _key)
  
          if isinstance(_value, datetime.datetime):
              _value = format_datetime(_value)
              elif isinstance(_value, datetime.date):
                  _value = format_date(_value)
  
                  data[_key] = _value
  
                  return data
  ```

  

- 필요없는 칼럼들은 인자로 입력받아 삭제한다.

- 그 이후, 필요한 데이터들을 커스텀하여 key로 넣어준다

```python
    def to_dict(self, delete_columns: list = []):
        # to_dict를 r.__table__.columns로 하면 관계필드는 알아서 빠져있다.
        data = super().to_dict()
        for col in delete_columns:
            if col in data:
                del data[col]

        #### 필드 Custom ####

        # 부서장 존재 확인용 -> 부서장이 있따면, 부서 전체 직원 - 1을 해서 [순수 부서원 수]만 내려보낸다.
        direct_leader_id = self.get_leader_id()
        # [순수 부서원 수] count_xxxx 메서드는 scalar()에서 알아서 없으면 0 처리된다.
        data['employee_count'] = self.count_employee() - (1 if direct_leader_id else 0)
        # [순수 하위 부서 수]만 카운팅 한다.
        data['only_children_count'] = self.count_only_children()
        # [순수 부서원 + 하위 부서장과 부서원 수]
        data['all_employee_count'] = self.count_self_and_children_employee() - (1 if direct_leader_id else 0)
        # view에서 level별 color / offset 설정을 위한 변수
        data['level'] = self.level

        # [부서장이 있다면, 부서장을 / 없다면 상위부서 부서장의 정보 추출]
        from . import Employee
        leader_id = self.get_leader_id_recursively()

        if leader_id:
            leader: Employee = Employee.get_by_id(leader_id)
            data['leader'] = {
                'id': leader.id, 'name': leader.name, 'avatar': leader.user.avatar,
                'position': leader.get_position_by_dept_id(self.id),
                'job_status': leader.job_status.name,
                'email': leader.user.email,
            }
        else:
            data['leader'] = None

        # [순수 부서원들의 정보만 추출]
        employee_id_list = self.get_employee_id_list(except_leader=True)
        if employee_id_list:
            employees = Employee.get_by_ids(employee_id_list)
            data['employees'] = []
            for emp in employees:
                data['employees'].append({
                    'id': emp.id, 'name': emp.name, 'avatar': emp.user.avatar,
                    'position': emp.get_position_by_dept_id(self.id),
                    'job_status': emp.job_status.name,
                })
        else:
            data['employees'] = None

        # [부모 부서의 sort]  부모색에 대한 명도만 다른 색을 입히기 위해, 색을 결정하는 부모의 sort도 추가
        parent_id = self.parent_id
        if parent_id:
            data['parent_sort'] = Department.get_by_id(parent_id).sort
        else:
            data['parent_sort'] = None

        return data
```



#### route

````python
from src.infra.tutorial3 import Department

dept_bp = Blueprint("department", __name__, url_prefix='/department')


@dept_bp.route("/organization", methods=['GET'])
def organization():
    tree = Department.get_all_tree()

    return render_template('department/organization.html',
                           tree=tree
                           )

````





### component 공부

#### 블로그 4개 개념 다지기

1. https://jw910911.tistory.com/m/67
2. https://jeonst.tistory.com/m/4
3. https://jaemin-lim.tistory.com/m/73
4. (v-for key쓰는이유): https://goodteacher.tistory.com/525



##### 기본 문법 정리

- 컴포넌트 템플릿이라면 

  - `v-on:click` => `@click`으로 바꿀 수있다.

  - `v-bind:class` => `:class`

    - 컴포넌트 data() : { return { class바인드변수: '값' } }

      ![image-20230125224156018](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230125224156018.png)

    - 기본 HTML속성 앞에 :(콜론) 붙이면 데이터나 자바스크립트의 표현식을 값으로 쓸 수 있다.

  - `v-show=""`

    - v-show는` display:none`으로 template의 display를 설정한다.
      - 이는 **레이아웃의 구성에 큰 영향을 미치기 때문에 해당 엘리먼트가 없어져야되는 상황**인지 단순에 눈에 보이지 않아야 되는 상황인지 잘 판단하여 사용하여야 한다.
    - v-if는 주석으로 template의 display를 설정한다.

##### 보간법과 computed 속성

- **보간법에서 게산하지말고, computed에서 `()`를 붙여서 `return`해주고, 보간법에서 사용하자**

- **computed 값이 캐싱이 되기 때문**에

  - computed는 data값과 같은 일반 데이터를 바로 사용하는 것이 아니라 javascript로 가공하여 사용할때 이용

  - 예를들어 템플릿의 data값이 바뀌게되면 Template 전체를 다시 그리게 되는데, 이떄 result.reduce...로 시작하는 계산부분도 같이 수행되게 된다. (재실행)

    만약 계산작업이 예를들어 10초이상소요될경우 메세지만 바꿨는데도 10초 이상 걸릴수도 있다. 

    이런 부분을 computed로 처리하면 캐싱된 계산값이 다시 사용되기때문에 좀더 template을 렌더링할때 부하가 걸리지 않늗다.

    위 compated안의 average()처럼 선언하면 computed는 result가 바뀌었을때 자동적으로 수행되며 template의 message가 바뀌었을때는 캐싱된 값을 사용하게 된다.

  - **뷰에서는 computed가 매우 중요하다 (성능에 직접적인 영향)**

![image-20230125230323866](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230125230323866.png)




#### vue 템플릿으로 정리

##### vue 인스턴스 생성

```js
// 보간법
{{변수명}}

// 문법
new Vue({
 el : '#test',
 data : {},    // 데이터 변수
 methods : {},  // 함수
 computed : {} // 계산식
})
```



##### v-bind:속성 =""

```html
// v-html
new Vue({
 el : '#test',
 data : {
   tag : '<p>test</p>'
 }
})

<div id="test">
  <div v-html="tag">
   //div 안에 tag의 할당된 태그가 넣어짐.
  </div>
</div>
```

```html
// v-bind:속성=""
<div id="test">
  <a v-bind:href="site"> {{ site }} </a>
</div>

// :속성=""에 일반 텍스트는 'text'와 결합
<a href="" :class="'test' + index"> 링크 </a>
```



##### v-on:약속된event  or @약속된event



```html
// js
new Vue({
 el : '#test',
 data : {
   age: 30
 },
 method : {
  plus : function(inc) {
    this.age += inc;
  },
  minus : function (dec) {
    this.age -= dec;
  }
 }
})

// v-on:click, v-on:dblllllclick
// @click, @dblcik으로 대체 가능
// @click.once => 한번만 실행
// @click.prevent => 기본 element의 기능은 수행하지 않음. ex> submit
<div id="test">
  <p>{{age}}</p>
  <button v-on:click="plus(10)">10살 더 먹기</button>
  <button v-on:dblclick="minus(10)">10살 덜 먹기</button>
</div>
```

```html
// js
new Vue({
 el : '#canvas',
 data : {
   x : 0,
   y : 0
 },
 method : {
  eventXY : function(event) {
    this.x = event.offsetX;
    this.y = event.offsetY;
  }
 }
})

// v-on:mousemove
// => 기본적으로 메서드명만 적으면 event가 인자로 날아온다
// => 인자와 함꼐 하고 싶다면, ($event, 인자)
<div id="canvas" v-on:mousemove="eventXY">
  {{x}}, {{y}}
</div>
```

```html
// v-on:keyup 아무키나
// v-on:keyup.enter => enter키를
// v-on:keyup.alt.enter => alt + enter키를
// => 해당 키를 치고 나올 경우 실행.
<input type="text" v-on:keyup="keyupEvent"> // keyup의 경우 keyupEvent 실행
<input type="text" v-on:keyup.enter="keyupEvent"> // keyup중 enter키일 경우 keyupEvent 실행
<input type="text" v-on:keyup.alt.enter="keyupEvent"> // keyup중 alt+enter키일 경우 keyupEvent 실행
```



##### v-model: 양방향 바인딩

- 원래 바인딩은  전역 변수 => 해당 component로만 주는데
- **양방향 바인딩은 input태그등에서, 사용자입력 => 전역 변수로도 전달하여, 외부 다른 태그에서도 사용할 수 있다.**

```html
// js
new Vue({
 el : '#test',
 data : {
  name : ''
 }
})

// html
<input type="test" id="test" v-model="name">
<p>{{name}}</p>
// input 입력된 문자가 p에서 나타난다.  
```

##### v-if => v-else-if => v-else

```html
error : false,
success : false 

<p v-if="error">error is true</p>
<p v-else-if="success">other condition</p>
<p v-else>error is false</p>
```



##### v-show

\- 값을 true, false로 간단히 **show/hide 기능**을 만들어 낼 수 있다.

```html
value : false
<p v-show="value">안보여요</p>

value : true
<p v-show="value">보여요</p>
```



##### json을 (val, key)로 돌리는 v-for와 template

- v-for를 돌릴 때, **in에 json이 올 경우, val, key 조합으로 돌릴 수 있다**

```html
// new Vue
ary : [
  {name : 'name1', age : 10},
  {name : 'name2', age : 20},
  {name : 'name3', age : 30}
]

// template 
<template v-for="data in ary">
 <div v-for="(val, key) in data">
    <h1 class="name">{{val}}</h1>
  <p>{{key}}</p>
 </div>
</template>
```



##### v-for에서 :key="중복되지 않는 값(value.id or index를 꺼내서)"해주면 매칭되는 사용자 입력값도 같이 움직여진다.

- [참고](https://goodteacher.tistory.com/525)



##### 2개의 vue 인스턴스는 js처럼 변수.데이터로 접근하여 서로 변경

```js
var one = new Vue({
  el: '#vue-app-one',
  data : {
    title : 'one'
  },
  methods : {

  },
  computed : {
    greet : function() {
      return "hello one";
    }
  }
});

var two = new Vue({
  el: '#vue-app-two',
  data : {
    title : 'two'
  },
  methods : {
    changeTitle : function() {
      one.title = 'changed title';
    }
  },
  computed : {
    greet : function() {
      return "hello two";
    }
  }
});
```

##### component 등록

```js
//10-1.
Vue.component('greeting',  {
  template : '<p>Hello {{name}} </p>', // root 엘리먼트가 하나 있어야함. 연달아 형제엘리먼트 추가 못함.
  data : function() {
    return {
      name : 'Jeon'
    }
  }
});
//10-2.
var ary = {
  name : 'jeon', age: 30
};

Vue.component('greeting',  {
  template : '<p>Hello {{name}} </p>', // root 엘리먼트가 하나 있어야함. 연달아 형제엘리먼트 추가 못함.
  data : function() {
    return ary
  }
});
```

##### ref="변수" 속성 =>  this.$ref.변수명.(dom속 element ex> .value, .innterText 등) 으로 사용

- refs 속성 사용 (ex: this.$refs.input2.value)
  - input 에 기입된 ref는 vue의 속성으로 dom을 불러온 후엔 나오지 않는다.
  - ref 속성으로 vue 참고 객체를 만들어서 사용하는 것으로 판단?
  - 다른 자료들을 보면 $ref로 dom에 접근이 가능하지만, vue.js 자체는 백엔드가 dom을 다루지 않는게 목적이기 때문에 사용을 지양한다.

```html
<div id="vue-app">
  <input type="text" name="" id="" ref="input2">
  <button v-on:click="readRefs">submit</button>
  <p>{{output}} <-</p>
</div>



new Vue({
  el: '#vue-app',
  data : {
    output : 'test'
  },
  methods : {
    readRefs : function() {
      this.output = this.$refs.input2.value; 
    }
  },
  computed : {
  }
});
```

- **결론 : $refs 로 DOM에 접근가능하나, VUE의 목적엔 어긋난다**

```html
<div id="app">
	<h1>{{ message }}</h1>
	<button ref="myButton" @click="clickedButton">Click Me!</button>
</div>


var vm = new Vue({
	el: '#app',
	data: {
		message: 'Hello World!'
	},
	methods: {
		clickedButton: function() {
			console.log(this.$refs);
			this.$refs.myButton.innerText = this.message;
		}
	}
});

```





#### 컴포넌트 기본 개념

- Vue 컴포넌트는 다음과 같이 작성한다. (**파스칼 케이스나 케밥케이스**를 사용)

  - `Vue.component(‘word-replay’);`

    ```
    kebab-case : Vue.component(‘word-relay’)
    Pascal-case : Vue.component(‘WordRelay’)
    
    camel-case : Vue.component(‘wordRelay’) (x)
    ```

    

- 일반 new Vue 인스턴스에서 `data: {}`의 객체리터럴 선언과를 달리, **컴포넌트는 `data() { return { data : }}` data() 메서드가 data객체리터럴을 return하는 함수형태로 선언한다**

  ```js
  // 일반 Vue객체에서의 Data (객체 리터럴)
  const app = new Vue({
    data: {
      word: '안녕하세요',
      result: '',
      value: '',  
    }
  });
  
  // 컴포넌트에서의 Data (return 객체 리터럴)
  export default() { 
    data() {
      return {
        data: {
          word: '안녕하세요',
          result: '',
          value: '',
        }
      };
    },
  }
  ```

  

- 컴포넌트는 **`template` 속성에서는 최상위 root element를 `<div>`태그 혹은 `<template>`태그가 1개만 존재해야한다**

  - **`CDN`을 통한 import는 `<template>가 불가`**

- **`불필요하게 <div>로 감싸줘야 할 때에는 <div>대신 <template>를 사용`할 수 있다.**

  - template를 사용하면 실제 해당 `<template>가 없는 것처럼 인식`된다.
  - 가장 위에 있는 template 최상단 안에 있는 template는 사용할 수 없다.
  - `쓸데없이 감싸지 않는 방법은 있지만 <div>로 감싸는게 가장 편하다.`
  - Chorme inspector화면에서 template가 사라진것을 확인할 수 있다

  ```html
  <template>
    <div>
    <div id="screen" :class="state" @click="onClickScreen">{{message}}</div>
      <template v-show="result.length">
        <div>평균 시간: {{average}}ms</div>
        <button @click="onReset">리셋</button>
      </template>
    </div>
  </template>
  ```

  

  - webpack의 import는 둘다 지원한다
  - `template: `속성을 **직접 정의할 때는 백틱(`)으로 작성하여 줄바꿈**을 편하게 한다.

- **vue인스턴스 선언보다 먼저 선언**되어야한다

  ```js
  Vue.component('word-relay', {
    template: `
       <template>  <!-- <template> 또는 <div>가 옴. (root element는 무조건 1개) -->
         <div>{{word}}</div>
            <form v-on:submit="onSubmitForm">
              <input type="text" ref="answer" v-model="value">
              <button type="submit">입력!</button>
            </form>
         <div>{{result}}</div>
       </template>
    `,
    data() {
    ...
    }
  ```

  ```js
  const app = new Vue({ // 컴포넌트가 Vue의 선언보다 앞서서 선언되어야 함 
    el: '#root',
  });
  ```

- Vue 컴포넌트의 선언 위치는 **`Vue.component(전역  컴포넌트)`가 `new Vue() (인스턴스 선언)` 보다는 상단에 와야 동작**한다. 
  - 해당 [Vue.component](http://vue.component/)를 전역 컴포넌트라고 부른다.
  - 서버는 모든 컴포넌트를 처음에 내려받고 화면을 랜더링한다.
    (이미 화면은 처음부터 정해져있다, 데이터만 변경되는것이다)





##### props

- 전체적인 큰 틀은 같은 컴포넌트면 중복되지만 그 안의 내용이 다른 부분이 있는 경우에는 컴포넌트 선언시 **props속성을 이용**하여 각각 다른 내용을 **`부모(전역) => 자식` 으로 전달한다**
- **props는 `컴포넌트 template의 html 내부에서는 kebab-case로 속성`로만 작성해야한다.**
  - HTML Tag의 속성은 대소문자를 구별하지 않는다. 따라서 Vue의 컴포넌트나 props등을 등을 가져오기위해 HTML에서 태그를 사용할때는 **반드시 kebab case를 사용**해야한다.
- **템플릿에서 사용된 props들은 `컴포넌트 선언시에는 props: 속성에서 arrays [] 안에 camel-case`로 작성해서 전달시킨다**
  - props는 컴포넌트의 선언시의 {props: [배열]} 형식의 속성값으로 들어간다.

- **자식이 props를 등록할 땐, `부모변수인 camelCase변수`로 등록하고, 자기는 `부모component내부에서 kekbab-case로 받아간다`**



```js
<div id="root">
    // component를 사용하는데, props속성에는 서로 다른 값을 전달 시킨다.
  <word-relay start-word="제로초"></word-relay> <!-- 컴포넌트나 props는 kebab-case로 표현함 -->
  <word-relay start-word="초밥"></word-relay>
  <word-relay start-word="바보"></word-relay>
</div>


//자바스크립트 쪽에서는 camel-case로 받을수 있다. (알아서 뷰가 처리를 해준다)
  Vue.component('word-relay', {
    template: `...`,
    props: ['startWord'], // camel-case로 props전달 받음
 } 
```



##### props(자식에 정의)와 반대인 emit (자식 => 부모)

###### props

- [참고](https://jeonst.tistory.com/m/39)

- props

  1. **`부모 컴포넌트 내부에서 사용중인 자식컴포넌트`에 `내 변수를 kekbab-case 자식에 등록한 props`에 할당하여 넘긴다**

     - 여러변수를 넘길거면, `:kebab-case="부모변수"`를 여러개 작성한다.

     ```html
     /* 부모 컴포넌트 */
     <div id="parentComponent">
     	<child-component :age="age" :name="name"></child-component>
     </div>
     
     var parentComponent = {
     	template: '#parentComponent',
     	data: function() {
     		return {
     			age: '30',
     			name: 'Jeon'
     		}
     	}
     }
     ```

  2. **자식은 `부모변수를 받아주는 props`를 자식의 component에 선언한 뒤, `내변수 처럼 사용`한다.**

     - 부모변수를 받아주는 props는 kebab-case로 정의해줘야한다
       - **어떤 것은 array에 어떤 것은 json형태로 정의하네?!**

     ```html
     /* 자식 컴포넌트 */
     <div id="childComponent">
     	<p>내 이름은 {{ name }} 이다. 내 나이는 {{ age }}이다.</p>
     </div>
     
     var childComponent = {
     	template: '#childComponent',
     	props: {
     		name: {
     			type: String
     		}, 
     		age: {
     			type: Number,
     			default: 0
     		}
     	}
     }
     ```

- 부모컴포넌트에서 : (v-bind) 를 통해서 받은 값으로 자식컴포넌트에서 사용 가능하다.

  - 단, **props로 받은 값은 자식 컴포넌트에서 수정이 불가하다.**

  - **타입을 정해주면 유효성이 검증되기 때문에 주로 사용**한다.
  - props 명은 
    - 자식컴포넌트에서는 **carmelCase**을 사용하며 
    - 부모컴포넌트의 템플릿 안에서는 **kebab-case**을 사용한다. (Vue.js 공식 추천 네이밍 방법)



##### emit => 자식메서드에서 this.$emit('부모의 @약속된(kebab-case)event', 'this.자식변수값')으로 넘긴다. => 부모는 @약속된event="받을메서드(넘어온 자식값)"으로 처리한다. => 자식은 @event="emitXXX메서드"로, 부모는 @약속된이벤트=""안의 메서드(인자)로 받는다.

- 여기서는 자식컴포넌트 정의시 **@click시 method를 통해, 메서드 내부에서 `this.$emit('부모의 @약속된(kebab-case)event', 'this.자식변수값')`**으로 넘긴다.



1. 자식은 **이벤트가 발생하는 tag들의 내부에 `@event=" emit메서드 "`로 자신의 컴포넌트 내부에 정의하고**

   ```html
   /* 자식 컴포넌트 */
   <div id="childComponent">
   	<button type="button" @click="emitParent">부모로 이름 보내기</button>
   </div>
   ```

2. 자식은 **emit메서드 내부에서, 넘길 변수를 `this.$emit( '부모의 @약속event', this.변수);`로 넘긴다**

   ```js
   var childComponent = {
   	template: '#childComponent',
   	data: function() {
   		return {
   			name: '홍길동'
   		}
   	},
   	methods: {
   		emitParent: function() {
   			this.$emit('child-click', this.name);
   			// 부모의 child-click 이벤트로 this.name을 받는다.
               // kekbab-case로 이벤트명을 지정한다.
   		}
   	}
   }
   ```

3. 부모컴포넌트는 **`부모 내부의 자식컴포넌트 안에서 @emit받아주는약속된event=" 받아처리메서드(받을 변수)"를 사용`하면 된다.**

   ```html
   /* 부모컴포넌트 */
   <div id="parentComponent">
   	<h1>내 이름은 {{ name }} 이다.</h1>
       <!-- (kebab-case) event -->
   	<child-component @child-click="getChildName(value)"></child-component>
   </div>
   ```

4. 부모는 emit된 변수를 method로 처리하면 된다.

   - **받아서 내 변수에 할당한다.**

   ```js
   var parentComponent = {
   	template: '#parentComponent',
   	data: function() {
   		return {
   			name: null
   		}
   	},
   	methods: {
   		getChildName: function(value) {
   			this.name = value;
   		}
   	}
   }
   ```

   

- emit 방식의 경우 **자식에서 어떠한 액션으로 이벤트를 통해서 데이터**를 보낸다.

  - 부모컴포넌트에서 이를 **@ (v-on)**으로 **자식에서 선언된 이벤트로 받아서 부모에서 정의된 메소드에 연결되는 방식으로 진행**된다.
  - **자식에서 전달해주는 데이터가 없다면 value부분을 제외**하고 쓰면 된다.

  - Vue.js의 템플릿(html)내에서는 **kabab-case**를 지원하기 때문에 자식에서 부모로 emit을 할때는 **kabab-case**로 작성한다.



##### Eventbus

- 위의 두가지 방식에도 불구하고 컴포넌트간 데이터 전달 방식에서 우리는 갈증을 느낀다.

  너무 폐쇄적이며 또한 부모에서 자식..자식...자식 수많은 부모와 자식이 생겨나면서

  서로간 알아야 할 데이터들이 많아지기 때문이다.

  이럴때 어디 한군데 수정하게 되면 연쇄적으로 여러군데를 수정해야하는 경우가 생긴다.

  결국 우리에게 닥칠 상황은 **휴먼 에러😢**...

  그렇게해서 나온 전달방식이 **Event Bus**🚌인 것이다.

   

  Event bus는 빈 컴포넌트를 하나를 만든다.

  그리고 그 안에 내가 원하는 값을 넣어서 다른 곳에서도 동적으로 가져와 사용할 수 있다.

  즉, 부모 + 자식 또는 자식 + 자식간에도 주고 받을 수 있다는 말이다.

  ## 코드

  ```
  EventBus.$emit(이벤트이름, 값) : 이벤트 트리거 (이벤트 시)
  EventBus.$on(이벤트이름, 데이터) : 이벤트 감지 (created에 붙이기)
  ```

  Event bus를 만드는 방법은 다음과 같다.

   

  1. **Event bus 컴포넌트를 만든다.**

     ```js
     // EventBus.js
     import Vue from 'vue';
     
     const EventBus = new Vue();
     
     export default EventBus;
     ```

     

  2. **Event bus가 필요한 컴포넌트(주/받 둘다)에서 import 시킨다.**

     ```js
     <script>
     import EventBus from '../EventBus';
     ```

     

  3. **받는 쪽의 created()에 $on, 주는 쪽의 메서드 내부에 $emit으로 해당 Event bus에 이벤트를 담고, 감지하여 쓴다.**

     - 주는 쪽

       ```js
       methods:{
           clickBtn(){
             EventBus.$emit('push-msg', '안녕');
           },
           changeComponent(){
             this.isComponent = !this.isComponent;
           }
       ```

     - 받는 쪽

       ```js
       created(){
               EventBus.$on('push-msg', (payload)=>{
                   this.msg = payload;
                   this.count++;
                   console.log(this.count);
               });
       ```

  4. **받는 쪽의 beforeDestory()에 $off을 컴포넌트가 사라질 때 이벤트를 삭제합니다.**

     - https://kdinner.tistory.com/53

       ```js
           created(){
               EventBus.$on('push-msg', (payload)=>{
                   this.msg = payload;
                   this.count++;
                   console.log(this.count);
               });
           },
           beforeDestroy(){
               EventBus.$off('push-msg');
           }
       ```

       

  📢**Tip**

  Event bus내에 **this**는 Event bus컴포넌트를 뜻한다.

  그렇기 때문에 Event bus 위에서 this를 변수에 담아 써야한다. (아래 예시)

  ```js
  var self = this;
  EventBus.$emit('eventBus', (payload) => {
  	self.msg = payload;
  });
  ```

- 참고
  - https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=dktmrorl&logNo=222080919891
  - https://kdinner.tistory.com/53



#### slot/ slot-cope /v-slot

##### slot => 부모에서 자식을 쓸 때, 자식 태그안에 새로운 내용을 적으면, 자식이 받아간다.

- [참고1 slot](https://kyounghwan01.github.io/blog/Vue/vue/slot/#%E1%84%80%E1%85%B5%E1%84%87%E1%85%A9%E1%86%AB)
- [참고2 slot-scope](https://idlecomputer.tistory.com/181)



- 기본

  1. 부모 컴포넌트에서 `자식컴포넌트 태그 사이에 새로운 내용의 태그`을 추가

     ```html
     <template>
       <!--부모 컴포넌트-->
       <ChildComponent>
         <button>버튼</button>
       </ChildComponent>
     </template>
     ```

  2. 자식 컴포넌트는 **빈 `<slot>`태그**를 만들어서, 부모에서 정의한 새로운 내용을 받아간다.

     ```html
     <template>
       <div>
         <!--부모에서 정의한 '버튼'이 위치합니다 -->
         <slot></slot>
       </div>
     </template>
     ```

- 이름이 있는 슬롯

  1. 부모가 쓰는 자식컴포넌트 내부에 **`새로운 내용을 slot=""속성과 함께 추가`한다**

     ```html
     <template>
       <!--부모 컴포넌트-->
       <ChildComponent>
         <button slot="left">왼쪽 버튼</button>
         <button slot="right">오른쪽 버튼</button>
       </ChildComponent>
     </template>
     ```

  2. 자식은 **`slot태그에 name=""`으로 부모가 사용한 slot속성명을 명시**에서 부모의 새로운 내용을 받아온다.

     ```html
     <template>
       <div>
         <!--부모에서 정의한 '왼쪽 버튼'이 위치합니다 -->
         <slot name="left"></slot>
     
         <!--부모에서 정의한 '오른쪽 버튼'이 위치합니다 -->
         <slot name="right"></slot>
       </div>
     </template>
     ```



##### slot-scope => 자식이 넘겨주는 데이터를 slotProps를 챙겨받는 template slot="" slot-scoped="자식data"로  자식내부 새로운 내용을 자식data.데이터로 작성

1. 부모가 쓰는 자식컴포넌트 내부에 **`<template slot=" " slot-scope=" "> 안에다가`로 `새로운 내용을 작성`하는데**

   - slot-scope=" `slotProps` "로서 props를 명시하며
   - `slotProps`내부에는 **자식에게 정의된 `:부모에게 넘겨줄 변수="자식변수"`들로서, 자식변수값들을 `slotProps.넘겨준변수`를 사용하여 새로운 내용을 작성한다**

   ```html
   <template>
     <div>
       <BaseModal>
         <!--자식에서 사용하던 name="child"로 감싸진 태그의 함수, 변수 모두 가져옵니다.-->
         <!-- template slot=""은 자식 내용을 채우는 공간이면서 slot-scope=""는 자식의 내용을 모두 가져와 => 자식의 데이터로서 새로운 내용을 작성한다. -->
         <template slot="child" slot-scope="slotProps">
           <button @click="slotProps.close">닫기</button>
           <!-- { childData: 'child' } -->
           {{ slotProps }}
         </template>
         <p slot="body">바디입니다.</p>
       </BaseModal>
     </div>
   </template>
   ```

   - 새로운 내용 template > button의 `slotPros.close`안에는 자식의 close변수값이 들어강 ㅣㅆ다.

   - `{{ slotProps }}`내부에서는 **자식이 넘겨주는 모든 props들**이 들어가있다.

     - **원래 props**는 **부모** => 자식에게 부모변수를 넘겨줄 때, kebab-case로 작성한다

       ```html
       <div id="parentComponent">
       	<child-component :age="age" :name="name"></child-component>
       </div>
       ```

     - **원래 자식**은, props를 정의해서 받고 => 자식컴포넌트내에서 자신의 변수로서 사용한다.

       ```html
       /* 자식 컴포넌트 */
       <div id="childComponent">
       	<p>내 이름은 {{ name }} 이다. 내 나이는 {{ age }}이다.</p>
       </div>
       
       var childComponent = {
       	template: '#childComponent',
       	// 부모변수를 받아주는 props
       	props: {
       		name: {
       			type: String
       		}, 
       		age: {
       			type: Number,
       			default: 0
       		}
       	}
       }
       ```

       

2. 자식은 부모의 새로운 내용을 `<slot name="">`으로 받아오되, **`:부모에게 넘겨줄 props="내 변수or 함수"`로 내부를 작성한다.**

   ```html
   <template>
     <div>
       <header>
         
           <!-- 부모내용을 받는 slot에 props가 정의되어있다면, 부모에게 넘겨주는 것 --> 
         <slot name="child" :childData="childData" :close="close">
           <button>버튼</button>
         </slot>
           
       </header>
       <div>
         <slot name="body">
           <p>기본 바디</p>
         </slot>
       </div>
     </div>
   </template>
   
   <script>
   export default {
     name: "BaseModal",
     data() {
       return {
         childData: "child",
         active: false
       };
     },
     methods: {
       close() {
         this.active = false;
       }
     }
   };
   </script>
   ```





##### v-slot => 부모의 slot="슬롯명" slot-scopred="slotProps" 대신 v-slot:slot명="slotProps" 로 작성 

###### 주의! `slot`, `slot-scope`는 이후 업데이트 될 Vue 3에서는 공식적으로 삭제된다고 하니 Vue에서 공식적으로 지원 할 `v-slot`만 사용하도록 합니다.

1. 부모는 **자식컴포넌트를 사용할 때  `<template v-slot:"자식이받을 슬롯명"="자식이 넘겨줄 slotProps명">` 를 먼저 씌우고 내용을 추가**한다.

   - 자식의 변수를 `slotProps.변수 or 메서드명`으로 새로운 내용을 작성하면 된다.

   ```html
   <template>
     <div>
       <BaseModal>
         <template v-slot:child="slotProps">
           <button @click="slotProps.close">닫기</button>
           <!-- { hello: 'hello' } -->
           {{ slotProps }}
         </template>
         <template v-slot:body>
           <p>바디입니다.</p>
         </template>
       </BaseModal>
     </div>
   </template>
   ```

2. 자식컴포넌트는 내부에  `부모에게 slotProps로 넘겨줄 변수/메서드들`을 

   1. `<slot name="부모v-slot명"`
   2. `:slotProps에채워질변수명="자식변수 or 메서드"`로 여러개 채워서 slot을 만들어놓는다.

   ```html
   <template>
     <div>
       <header>
         
           <!-- 부모내용을 받는 slot에 props가 정의되어있다면, 부모에게 넘겨주는 것 --> 
         <slot name="child" :childData="childData" :close="close">
           <button>버튼</button>
         </slot>
           
       </header>
       <div>
         <slot name="body">
           <p>기본 바디</p>
         </slot>
       </div>
     </div>
   </template>
   
   <script>
   export default {
     name: "BaseModal",
     data() {
       return {
         childData: "child",
         active: false
       };
     },
     methods: {
       close() {
         this.active = false;
       }
     }
   };
   </script>
   ```

   



#### 웹팩 사용 이유(cdn vs npm 웹팩과 비교하기)

- 웹팩을 사용해야 되는 이유(느끼게되는 이유는) JS파일이 커지다보면 js파일을 `<script></script>로 import해서 계속 사용하고 점점 커지게 되는데, 코드의 복잡성이 증가하고 꼬이게 되는 문제`가 발생한다. 
- 그래서 나온것이 `CommonJS`, `RequiredJS`이다.
- 웹팩이 나오면서 **스크립트가 여러개 있을때 하나로 합쳐주는 역활**을 한다



##### npm 설치

1. node.js 다운로드 및 설치

2. vscode 에 터미널로 프로젝트를 할 폴더에 npm install (vscode에 Veter 설치)

3. 터미널

   - 찾아보니 vscode가 기본으로 설정되는 **터미널이 파워쉘을 쓴다고 해서 문제**가 된 듯하다. 기본 터미널을 cmd로 바꿔줘야한다고 한다.
   - vscode 에서 ctrl+shift+p 로 shell default 를 cmd로 변경해도 같은 오류가 나서 결국 cmd 창을 켜서 했더니 프로젝트 만들어진다.

   ```shell
   vue install -g @vue/cli​ // vue-cli 설치
   vue create 프로젝트명 // 프로젝트 생성
   ```

   - **npm을 통해 다운로드한 모듈을 다음에도 패키지로 다운로드 할 수 있게 추가하려면?** (dependencies 추가)

     ```shell
     npm install 패키지이름 --save
     
     ```

   - **패키지에 저장해둔 모듈에 업데이트가 있다면?**

     ```
     npm update
     ```

   

##### cdn사용시와 다른 점

- cdn

  ```js
  <script src="https://cdn.jsdelivr.net/npm/vue/dist/vue.js"></script>
  
  const app = new Vue({
      el: '#root',
  })
  ```

- npm 실행

  ```js
  import Vue from 'vue';
  import NumberBaseball from './NumberBaseball.vue'; // 숫자야구 vue 컴포넌트 불러오기
  
  new Vue(NumberBaseball).$mount('#root'); // 숫자야구 vue컴포넌트를 html의 root로 삽입
  ```

  



- **Npm을 이용한 Vue 설치후 프로젝트 구조 잡기**

  - npm을 이용하여 vue를 사용할때 3가지 파일로 나눠서 코딩한다.

    - **main.js**는 Vue 인스턴스를 로딩하기 위해서 사용한다.

    - **.vue** 파일들은 각각 vue에 대한 Component들이다.

    - **.html** 파일은 컴포넌트가 삽입될 HTML 템플릿이다.

      - <숫자야구 예제에서의 파일구조>

      ```js
      * main.js // Vue 인스턴스 수행
      * NumberBaseball.html // Vue 컴포넌트가 삽입되는 최상위 HTML 템플릿
      * NumberBaseball.vue // 숫자야구 컴포넌트
      * package.json
      * package-lock.json
      * webpack.config.js
      ```

- 웹펙에서 빌드할때는 **main.js와 NumberBaseball.vue를 합쳐서` app.js`로 번들링**하고 해당 **js파일을 html에서 import하도록 설정**하여 사용할 수 있다.



- **Vue 컴포넌트 파일 구조 이해하기**

  - `.vue`로 끝나는 파일은 **컴포넌트를 만들기 위하여 사용되는 자바스크립트 코드**이다.

  - .vue파일은 크게 3가지 부분으로 나눠진다. 

    - **template** : 템플릿은 해당 Component를 구성하는 실제 컴포넌트에 대한 HTML 코드를 작성하는 부분이다.
    - **script** : 실제 해당 컴포넌트에 대한 data와 실제 동작을 정의하는 JS 파일이다.
    - **style** : template에 대한 element의 스타일을 지정할 때 사용한다.

  - **CDN으로 사용**할때는 Vue.component 함수 하나에 위의 template, script, style이 다 있었는데 **해당 부분이 각각 분리되어서 사용**된다고 생각하면 된다.

    - NumberBaseball.vue 코드 

      ```js
      <template>
        <div>
          <h1>{{result}}</h1>
          <form @submit.prevent="onSubmitForm">
            <input ref="answer" minlength="4" maxlength="4" v-model="value"/>
            <button>입력</button>
          </form>
          <div>시도: {{tries.length}}</div>
          <ul>
            <li v-for="t in tries">
              <div>{{t.try}}</div>
              <div>{{t.result}}</div>
            </li>
          </ul>
        </div>
      </template>
      
      <script>
        const getNumbers = () => {
          const candidates = [1, 2, 3, 4, 5, 6, 7, 8, 9];
          const array = [];
          for(let i = 0; i < 4; i += 1) {
            // Math.random => 0 ~ 1 사이의 실수를 뽑아
            const chosen = candidates.splice(Math.floor(Math.random() * (9 - i)), 1)[0];
            array.push(chosen);
          }
      
          return array;
        };
      
      
        export default {
          data() {
            return {
              answer: getNumbers(), // ex [1, 5, 3, 4]
              tries: [], // 시도
              value: '',
              result: '',
            }
          },
          methods: {
            onSubmitForm() {
              if (this.value === this.answer.join('')) { // 정답 맞췄으면
                this.tries.push({
                  try:this.value,
                  result: '홈런'
                });
                this.result = '홈런';
                alert('[정답[게임을 다시 실행합니다.');
                this.value = '';
                this.answer = getNumbers();
                this.tries = [];
                this.$refs.answer.focus();
              } else {
                if (this.tries.length >= 9) {
                  this.result = `10번 넘게 틀려서 실패! 답은 ${this.answer.join(',')}였습니다.`
                  alert('게임을 다시 실행합니다.')
                  this.value = '';
                  this.answer = getNumbers();
                  this.tries = [];
                  this.$refs.answer.focus();
                  console.log('zz');
                  return ;
                }
      
                let strike = 0;
                let ball = 0;
                // 문자열을 숫자 배열로 바꿔줌.
                const answerArray = this.value.split('').map(v => parseInt(v));
                for (let i = 0; i < 4; i += 1) {
                  if (answerArray[i] === this.answer[i]) { // 숫자 자릿수 모두 정답
                    strike++;
                  } else if (this.answer.includes(answerArray[i])) { // 숫자만 정답
                    ball++;
                  }
                }
                this.tries.push({
                  try: this.value,
                  result: `${strike} 스트라이크, ${ball} 볼입니다.`,
                });
                this.value = '';
                this.$refs.answer.focus();
              }
            }
          }
        }
      </script>
      
      <style>
        #computer {
          width: 142px;
          height: 200px;
          background-position: 0 0;
        }
      </style>
      ```

##### NPM 패키지 모듈 설정하기

- webpack 설정을 위해 **webpack, webpack-cli, vue-loader, vue-template-compiler**에 대한 npm install을 진행합니다.

- package.json을 보면 다음과 같습니다.

  - 추가적으로 **vue-template-comfiler**의 버전와 **vue**의 버전은 항상 일치 시켜야 합니다.

  ```js
  {
    "name": "number-baseball",
    "version": "1.0.0",
    "description": "",
    "main": "index.js",
    "scripts": {
      "build": "webpack"
    },
    "author": "",
    "license": "ISC",
    "dependencies": {
      "vue": "^2.6.10"
    },
    "devDependencies": {
      "vue-loader": "^15.7.2",
      "vue-template-compiler": "^2.6.10",
      "webpack": "^4.41.2",
      "webpack-cli": "^3.3.10"
    }
  }
  ```

  

##### Webpack.Config.Json 파일 설정하기

- mode
  - development 모드를 선언합니다.
- entry
  - 현재 디렉토리의 main.js라는 파일을 기준으로 번들링 작업을 수행합니다.
- module 
  - .vue(확장자)로 끝나는 모든 파일을 경로에서 탐색한뒤 Bundling합니다.
    - test : **`/\`**는 시작 **`$/`**는 끝을 의미합니다. 
    - loader: vue-loader를 사용하겠다고 선언합니다. vue-loader는 npm으로 앞에서 다운받은 모듈을 의미합니다.
    - vue-loader는 vue의 component를 일반적인 자바스크립트 모듈로 변환할 수 있도록해주는 webpack loader입니다.
      - **즉, vue파일을 읽어서, js파일로 빌드해주는 역할**
    - 
- plugin 
  - Vue Loader를 사용하기 위해 추가적으로 VueLoaderPlugin을 명시해주어야 한다. (vue-loader 15버전 이상부터)
  - 추가적으로 plugin과 loader의 차이는 다음과 같습니다.
    - plugin : 파일을 해석하고 변환하는 과정에 관여하여 모듈을 처리합니다. (즉 vue컴포넌트 파일을 번들링)
    - loader : 번들링된 결과물의 형태를 바꾸는 역활을 합니다. 즉 번들링된 파일을 압축하거나, 파일 복사, 추출 등 부가작업을 하거나 파일별 커스텀 기능을 위해 사용합니다.
  - output
    - 결과로 번들링된 파일의 이름과 해당 번들링 파일이 저장될 경로
    - entry에서 선언한 key의 이름이 [name]에 들어갑니다.
    - 즉 webpack을 수행하면 app.js라는 파일이 dist/ 폴더 안에 생깁니다.

```js
const VueLoaderPlugin = require('vue-loader/lib/plugin');
const path = require('path');

module.exports = {
  mode: 'development',
  entry: {
    app: path.join(__dirname, 'main.js')
  },
  module: {
    rules: [{
      test: /\.vue$/,
      loader: 'vue-loader', 
    }],
  },
  plugins: [
    new VueLoaderPlugin(),
  ],
  output: {
    filename: '[name].js',
    path: path.join(__dirname, 'dist'),
  },
};
```

- webpack 설정시 발생할수 있는 에러 해결

  - webpack을 이용하여 vue를 구성할때 아래와 같은 에러를 만날수 있는데 각각 해결방법은 다음과 같습니다.

  1. 아래와 같은 에러 발생시에는 **vue-template-compiler**를 설치하여 줍니다.

  ```
  /* Vue-Template-Comfiler를 설치하라 */
  ERROR in ./NumberBaseball.vue
  Module Error (from ./node_modules/vue-loader/lib/index.js):
  [vue-loader] vue-template-compiler must be installed as a peer dependency, or a compatible compiler implementation must be passed via options.
   @ ./main.js 2:0-50
  ```

  2. 아래와 같은 에러 발생시에는 **VueLoaderPlugin**을 webpack.config.js의 plugin으로 등록하여 줍니다. (vue-loader안에 존재)

  ```
  /* VueLoaderPlugin을 webpack.config.js 안에 넣어라 */
  ERROR in ./NumberBaseball.vue
  Module Error (from ./node_modules/vue-loader/lib/index.js):
  vue-loader was used without the corresponding plugin. Make sure to include VueLoaderPlugin in your webpack config.
  ```

   

 

##### webpack watch로 실시간 코드변경 확인

- watch 옵션을 붙여주면 소스코드가 변경될 때마다 webpack이 자동으로 소스코드를 빌드한다.
  - 따라서 항상 빌드할 필요가 없이 소스코드를 변경후 바로 결과를 확인할 수 있다.

```js
"scripts": {
  // "build": "webpack"
  "build": "webpack --watch"
}
```



##### Style을 사용하기 위한 CSS 모듈 Webpack.config.js 처리

```js
// css-loader 설치
npm i css-loader -D

// vue-style-loader 설치
npm i vue-style-loader -D
```

- module에 추가

  ![image-20230125224332012](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230125224332012.png)

  - CSS모듈을 사용하지 않으면 에러가 발생하는데 css-loader와 vue-style-loader 모듈을 설치하여 해결할 수 있다.

  - - CSS처리를 하기위해서는 css-loader와 vue-style-loader 2개 모두 필요하다. 

      (Javascript가 아닌 파일을 처리하기 때문)

    - webpack 빌드시 설치해야하는 모듈이기 때문에 -D옵션을 붙여서 개발자 모드로 해당 모듈을 install한다.

  - 로더의 갯수는 많아질 수 밖에 없는데 vue로더는 vue만 담당하고, CSS로더는 CSS만 담당하고 이렇게 로더마다 역할이 분리되어 있기 때문이다.

  - 이후 CSS전처리기인 sass, less등이나, postcss와 같은 로더를 처리할때 로더가 추가될 수도 있다.

  - 로더는 각각 하나의 역할을 하기 때문에, 앱이 커지면 여러 역할을 처리해야하는데, 각각 매칭되는 로더를 모두 설정해주어야한다.



##### webpack.config.json에서 module과 plugin의 차이점

-  module 설정은 자바스크립트 파일 output으로 나오기 전에 압축하는 역할이라던지, 압축된 js파일을 HTML파일안에 스크립트로 추가할수 있는 역할 등 부차적인 역할을 수행한다.

- - module설정이 webpack의 대부분의 역할을 차지한다고 생각하면 편리하다.
  - webpack이 javascript를 하나로 합쳐주는 역활을 하는데, 자바스크립트가 아닌 파일들 (ex: .vue, .css)와 같은 파일을 자바스크립트로 만들어 주는 역할을 하는데 이 역할이 무척 큰 역할이다.

- plugin은 부가적인 역활을 한다.

##### style scoped

- 보통 CSS를 적용할때 ID나 Class를 생성하면 모든 HTML Element들이 해당 CSS를 사용하게 되는데, vue를 사용할 때 컴포넌트 단위로만 CSS를 적용하고 싶을때는 `<style scoped>`를 이용하여 선언하여 주면 해당 CSS는 Scoped를 선언한 템플릿 안에서만 유효하다. 이를 Vue의 Scoped Style이라고 부른다.
  - 크폼 인스펙터로 확인해 보면 `id나 class뒤에 data-v:22c711ee.` 와 같이 랜덤한 속성값이 붙은 것을 확인할 수 있다.
  - 보통 Scoped는 전역으로 CSS를 사용할때 아니면 왠만하면 써주는 것이 좋다.



##### 웹펙 Dev Server 설정하기

- webpack 빌드 시 `--watch` 옵션을 통해 자동으로 빌드 해줄수도 있지만, 그래도 `브라우저 상에서 계속 새로고침을 해줘야 하는 번거로움`이 있다. 이럴때 webpack-dev-server을 npm에서 설치해서 이용하면, `새로고침 없이 좀더 편리하게 빌드를 진행`할수 있다.
- npm으로 webpack-dev-server을 install 한뒤 빌드 명령어를 `package.json의 script 옵션안의 dev 속성에 추가`하여 준다.
- webpack dev-server을 설치후에 `webpack.config.json 파일의 output 옵션`의 publicPath 속성값을 dist(파일의 아웃폿) 경로로 추가하여 준다.
- `npm run dev`를 수행하면, `로컬호스트 서버(port: 8080)`가 돌면서 코드의 수정이 일어났을 때, `브라우저상에 바로 반영되며, 자동으로 갱신`된다. 
- **개발할때 위처럼 설정하여 많이 사용하는 편이다.**

```js
//npm으로 webpack-dev.server 설치
npm install -D webpack-dev-server
```

![image-20230125225711394](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230125225711394.png)

![image-20230125225719628](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230125225719628.png)