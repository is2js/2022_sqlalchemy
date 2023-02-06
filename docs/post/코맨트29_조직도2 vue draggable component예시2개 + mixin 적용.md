### 예시1. x-template로 직접 component 정의(view-20-tree-view)  (조직도 용)

- **[codepen 예시](https://codesandbox.io/embed/github/vuejs/v2.vuejs.org/tree/master/src/v2/examples/vue-20-tree-view?codemirror=1&hidedevtools=1&hidenavigation=1&theme=light)**



![image-20230126024358583](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230126024358583.png)

#### 자식컴포넌트 template 정의 in head => 만들어 나가기

1. vue를 cdn import된 상태라 가정하고

2. **head에 script태그를 `type="text/x-template"` + `id="컴포넌트 등록시 template:속성에 입력될 id"`로 `자식 컴포넌트의 템플릿을 정의`한다.**

   ```html
       <!-- item template -->
       <script type="text/x-template" id="item-template">
         <li>
           <div
             :class="{bold: isFolder}"
             @click="toggle"
             @dblclick="makeFolder">
             {{ item.name }}
             <span v-if="isFolder">[{{ isOpen ? '-' : '+' }}]</span>
           </div>
           <ul v-show="isOpen" v-if="isFolder">
             <tree-item
               class="item"
               v-for="(child, index) in item.children"
               :key="index"
               :item="child"
               @make-folder="$emit('make-folder', $event)"
               @add-item="$emit('add-item', $event)"
             ></tree-item>
             <li class="add" @click="$emit('add-item', item)">+</li>
           </ul>
         </li>
       </script>
   ```

3. **@click**시 `재귀의 시작인 내 안의 자식이 나 <tree-item>`을 **`보여줄 지 말지 결정하는 v-show="isOpen" 담당 boolean변수`를  toggle 메서드에서  처리**한다.

   - 자식데이터인 `this.isFolder` (하위부서가 있는지)에 따라 `this.isOpen` 변수를 토글한다.

   ```js
   toggle: function() {
       if (this.isFolder) {
           this.isOpen = !this.isOpen;
       }
   }
   ```

4. `isOpen`은 false초기화되어 처음에는 다 접혀있고(자식 컴포넌트를 안보여줌)

   - **현재 나 자신의 isOpen이 toggle메서드에서 true로 토글되는 순간**

   - `또다른 시작인 ul태그 안`에서 `나의 .children`들을 순회하며 자식이 자신이 되는 `<tree-item>`을 v-show로 보여주게 된다.

     ```html
     <ul v-show="isOpen" v-if="isFolder">
         <tree-item
                    class="item"
                    v-for="(child, index) in item.children"
                    :key="index"
                    :item="child"
                    @make-folder="$emit('make-folder', $event)"
                    @add-item="$emit('add-item', $event)"
                    ></tree-item>
         <li class="add" @click="$emit('add-item', item)">+</li>
     </ul>
     ```

5. **@dblclick**시 `내가 !this.isFolder`로 `자식(하위부서)`를 가지지 않은 상태에서만

   1. `부모에게 내 this.item데이터(추후 input으로 처리할 json new 데이터)`를 보내는 **makeFolder (emit메서드)**를 처리한다.

      - emit메서드는 내부에서 this.$emit('`부모컴포넌트에 @약속된(kebab-case)event`, 보낼데이터')형태로 정의된다.

      ```js
      makeFolder: function() {
          if (!this.isFolder) {
              this.$emit("make-folder", this.item);
              this.isOpen = true;
          }
      }
      ```

   2. **부모는 자식의 emit데이터를 받아줄 `@약속된(kebab-case)event`를  부모내부 자식컴포넌트에 정의하여, 부모의 메서드로 받는다. 인자로는 자식이 보낸 emit데이터가 넘어온다**

      ```html
      <ul id="demo">
          <tree-item
                     class="item"
                     :item="treeData"
                     @make-folder="makeFolder"
                     @add-item="addItem"
                     ></tree-item>
      </ul>
      ```

   3. **부모의 emit을 받아주는 메서드는 내부에서 **

      1. **자신의 item에 (json변수)에 `"children"`의 key로 빈 배열을 새로 선언 한 뒤 `거기다가 push`해주는 `this.addItem( 받음데이터 )`메서드를 호출해준다.**

         ```js
         makeFolder: function(item) {
             Vue.set(item, "children", []);
             this.addItem(item);
         },
         ```

         

      2. addItem은 자신의 children 배열에 새로운 item을 push해주는 메서드로서 

         1. 현재 더블클릭으로 자식없으면 자식을 추가한 뒤 폴더(하위부서가짐)으로
         2. 아니면 자신의 level의 끝에서 `+`버튼으로 부서 추가
            - 재활용 되므로 메서드로 정의한다.

         ```js
         addItem: function(item) {
             item.children.push({
                 name: "new stuff"
             });
         }
         ```

   4. **자식 컴포넌트 내부 this.isFolder변수는 `나에게 .children변수 및 배열의 1개라도 존재하는지`를 확인하는데, 계산과정 &&이 들어가므로 computed에 캐슁되도록 정의한다.**

      ```js
      computed: {
          isFolder: function() {
              return this.item.children && this.item.children.length;
          }
      },
      ```

6. 각 item마다  `isFolder`면 + or -가 보이게 `v-if`를 정의해놓고

   - `isOpen`으로 자신이 열린 상탠지 닫힌 상태인지 따라  +  or  -가 보이게 한다

   ```html
   <div
        :class="{bold: isFolder}"
        @click="toggle"
        @dblclick="makeFolder">
       {{ item.name }}
       <span v-if="isFolder">[{{ isOpen ? '-' : '+' }}]</span>
   </div>
   ```

   

7. 자식 템플릿 내부의 또다른 자식컴포넌트는 재귀를 위한 것인데

   - **애초에 시작을 `ul(묶음의 시작점)  +  v-show`로 시작한다.**

   - **`부모 내부에서 사용되는 자식컴포넌트`로서  @부모의 약속된(kebab-case)event들도 다 정의됭있어야하며, 거기다가 외부가 아닌 자신의 children을 돌린 child를 props에 연결해준다.**

     ```html
     <ul v-show="isOpen" v-if="isFolder">
         <tree-item
                    class="item"
                    v-for="(child, index) in item.children"
                    :key="index"
                    :item="child"
                    @make-folder="$emit('make-folder', $event)"
                    @add-item="$emit('add-item', $event)"
                    ></tree-item>
         <li class="add" @click="$emit('add-item', item)">+</li>
     </ul>
     ```

   - **li로 시작하는 1개의 컴포넌트는 자식들을 v-for +재귀로 호출한 뒤 `li를끝내기 전에 자식들 다 표기한 뒤 + 자식추가`를 맨 아래에 추가한다**

     ```html
           <li>
             <div
               :class="{bold: isFolder}"
               @click="toggle"
               @dblclick="makeFolder">
               {{ item.name }}
               <span v-if="isFolder">[{{ isOpen ? '-' : '+' }}]</span>
             </div>
             <ul v-show="isOpen" v-if="isFolder">
               <tree-item
                 class="item"
                 v-for="(child, index) in item.children"
                 :key="index"
                 :item="child"
                 @make-folder="$emit('make-folder', $event)"
                 @add-item="$emit('add-item', $event)"
               ></tree-item>
               <li class="add" @click="$emit('add-item', item)">+</li>
             </ul>
           </li>
     ```

     

8. 템플릿이 head에서 완성되었다면, **`body에서 부모템플릿(#demo)` 안에서 `자식템플릿(#item-itemplate)을 사용하여 정의`한다**

   1. tree형 재귀 자식컴포넌트 => root의 자식이지만, `재귀자식의 부모`로서 자식컴포넌트 + 부모와 약속된kebab-case 메서드를 사용
   2. 부모 컴포넌트 => 자식컴포넌트 사용하여 정의 + 부모와 약속된kebab-case 메서드

   ```html
     <body>
       <p>(You can double click on an item to turn it into a folder.)</p>
   
       <!-- the demo(부모) root element -->
       <ul id="demo">
         <tree-item
           class="item"
           :item="treeData"
           @make-folder="makeFolder"
           @add-item="addItem"
         ></tree-item>
       </ul>
   ```

9. 예시데이터

   - root 트리 1개로 시작하도록 짜놨다.
   - 나중에 root가 여러개면 v-for로 돌리면 된다.

   ```js
      <script>
         // demo data
         var treeData = {
           name: "My Tree",
           children: [
             { name: "hello" },
             { name: "wat" },
             {
               name: "child folder",
               children: [
                 {
                   name: "child folder",
                   children: [{ name: "hello" }, { name: "wat" }]
                 },
                 { name: "hello" },
                 { name: "wat" },
                 {
                   name: "child folder",
                   children: [{ name: "hello" }, { name: "wat" }]
                 }
               ]
             }
           ]
         };
   ```

   

10. 이제 자식컴포넌트를 전역으로 등록하자

    ```js
    // define the tree-item component
    Vue.component("tree-item", {
        template: "#item-template",
        props: {
            item: Object
        },
        data: function() {
            return {
                isOpen: false
            };
        },
        computed: {
            isFolder: function() {
                return this.item.children && this.item.children.length;
            }
        },
        methods: {
            toggle: function() {
                if (this.isFolder) {
                    this.isOpen = !this.isOpen;
                }
            },
            makeFolder: function() {
                if (!this.isFolder) {
                    this.$emit("make-folder", this.item);
                    this.isOpen = true;
                }
            }
        }
    });
    ```

11. 이제 부모인스턴스를 자식컴포넌트보다 아래에 생성하자

    ```js
     // boot up the demo
          var demo = new Vue({
            el: "#demo",
            data: {
              treeData: treeData
            },
            methods: {
              makeFolder: function(item) {
                Vue.set(item, "children", []);
                this.addItem(item);
              },
              addItem: function(item) {
                item.children.push({
                  name: "new stuff"
                });
              }
            }
          });
        </script>
    ```

    

### 예시2 cdn(vue-draggable-nested-tree) => window로 받아서 component등록하여 사용 (부서관리용)





#### 기본 select만

![image-20230126183716898](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230126183716898.png)

- https://www.kabanoki.net/5179/



1. header에 cdn 등록

   ```html
   // npm
   // npm i vue-draggable-nested-tree
   
   // CDN
   // tree-helper.js와 함께 사용하면 트리를 열고 닫을 수 있습니다. expandAll 및 collapseAll  메소드에서 개폐 기능을 구현
   
   {% block extra_head_style %}
   <script src="https://unpkg.com/vue-draggable-nested-tree@latest/dist/vue-draggable-nested-tree.js"></script>
   <script src="https://unpkg.com/tree-helper@latest/dist/tree-helper.js"></script>
   ```

2. **static/js/entity/폴더에 저장해놓고 갖다쓰기도록 수정**하기

   ```html
   {% block extra_head_style %}
   
   <script src="{{url_for('static', filename='js/department/vue-draggable-nested-tree.js')}}"></script>
   <script src="{{url_for('static', filename='js/department/tree-helper.js')}}"></script>
   ```

   

3. script에서 component import  및 전역 compontent로 등록

   ```js
   //(1) webpack 등의 경우 [주의] 모듈 버전은 검증되지 않습니다. 
   //import {DraggableTree} from 'vue-draggable-nested-tree' 
   
   //(2) WEB 페이지의 경우 
   const th = window.treeHelper;
   const {DraggableTree} = window.vueDraggableNestedTree;
   
   Vue.component('tree', DraggableTree);
   
   ```

   - 콘솔에서 window.으로 쳐보면 관련 단어로 검색되는 것 같다.

     ![image-20230126045317919](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230126045317919.png)



4. 부모 vue 인스턴스 생성하기

   - **tree1data, tree2data 2개가 예제 데이터로 data속성에 초기화 되어있다**

     ```js
     let app = new Vue({
       el: '#app',
       data: {
         tree1data: [
           {text: 'node 1'},
           {text: 'node 2'},
           {text: 'node 3 undraggable', draggable: false},
           {text: 'node 4 undroppable', droppable: false},
           {text: 'node 5', children: [
             {text: 'node 6'},
             {text: 'node 7'},
           ]},
         ],
         tree2data: [
           {text: 'node 8', children: [
             {text: 'node 9'},
             {text: 'node 10 undroppable', droppable: false, children: [
               {text: 'node 11'},
               {text: 'node 12'},
             ]},
             {text: 'node 13', children: [
               {text: 'node 14'},
               {text: 'node 15 undroppable', droppable: false},
             ]},
             {text: 'node 16'},
             {text: 'node 17'},
             {text: 'node 18'},
           ]},
         ]
       },
       methods: {
         expandAll() {
           th.breadthFirstSearch(this.tree1data, node => {
             node.open = true
           })
         },
         collapseAll() {
           th.breadthFirstSearch(this.tree1data, node => {
             node.open = false
           })
         },
       },
     });
     ```

   - **flask용으로서 tree1data만  사용하며 `base.html의 부모 인스턴스`에 `treeData를 선언`하고 `text.html에 treeData`를 treeData1 내용( 배열으로 시작 )으로만 `초기화` 한다.**

     - root에 []배열로 할당하여 여러개가 들어간다.

     ```js
     //base.html
         var app = new Vue({
             el: '#app',
             delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
             
             data: {
     //department/부서관리용 DraggableTree .html의 컴포넌트 주입용 데이터 변수 초기화
     			treeData: null,
             },
     ```

     ```html
     <!-- test.html --> 
     <script>
         const th = window.treeHelper
         const {DraggableTree} = window.vueDraggableNestedTree;
     
         Vue.component('tree', DraggableTree);
     </script>
     {% endblock extra_foot_script %}
     
     {% block vue_script %}
     <script>
     
         app._data.treeData = [
                 {text: 'node 1'},
                 {text: 'node 2'},
                 {text: 'node 3 undraggable', draggable: false},
                 {text: 'node 4 undroppable', droppable: false},
                 {
                     text: 'node 5', children: [
                         {text: 'node 6'},
                         {text: 'node 7'},
                     ]
                 },
             ];
     </script>
     {% endblock vue_script %}
     ```

5. 컴포넌트 내부에 템플릿이 이미 head에서 cdn으로 정의되어있으니

   - **flask용으로 보간법 `{{}}`를 `{$$}`로 변경해준다.**

   ```html
   <div class="row">
       <div class="col-3">
           <tree :data="treeData" 
                 draggable="draggable" 
                 cross-tree="cross-tree">
               <div slot-scope="{data, store}">
                   <template v-if="!data.isDragPlaceHolder">
                       <b v-if="data.children && data.children.length" 
                          @click="store.toggleOpen(data)">
                           {$ data.open ? '-' : '+' $}&nbsp;
                       </b>
                       <span>{$ data.text $}</span>
                   </template>
               </div>
           </tree>
       </div>
   </div>
   ```

   - **부모 template내부에서 자식컴포넌트 `<tree>`를 사용하며, 그 내부에는 `부모 자신의 데이터를 이용해 새로운 내용을 slot으로서 추가`한다.**

   - **부모는 자식 컴포넌트를 사용할 때, 내부에 `slot-scope="자식이 넘겨준 slotProps변수"`를 받는데, 여기선 `{data, store}`로 2개의 slotProps를 전달받아, 자식데이터(변수/메서드)로 새로운 내용을 작성한다.**

     - data에서는, 개별 node
     - store에는 미리 정의된 method들이 담겨져있다.
       - `store.toggleOpen()`의 경우 인자로 개별 node `data`를 다 받아간다.
       - => 내부에서 data.children을 쓰나보다.

     ```html
     <!-- 자식이 넘겨준 변수들 -->
     <div slot-scope="{data, store}">
     ```

   - **`!data.isDragPlaceHolder`로서, 내가 들고 있지 않을 때만, 내 node 정보가 보인다.**

     - Drag로 들고 있다면, placeholder로 대체되고 내 영역은 보이지 않는다.

     ```html
     <template v-if="!data.isDragPlaceHolder">
     ```

   - bold태그로 자식 `v-if`  자식컴포넌트 `.children`이 있을 때만  `.open` 여부에 따라서  +  - 접을지 펼치를 결정한다

     ```html
     <b v-if="data.children && data.children.length" 
                            @click="store.toggleOpen(data)">
                             {$ data.open ? '-' : '+' $}&nbsp;
                         </b>
     ```



6. 기본 style을 적용해야지 잘보인다.

   ```css
   .he-tree{
     border: 1px solid #ccc;
     padding: 20px;
     width: 300px;
   }
   .tree-node-inner{
     padding: 5px;
     border: 1px solid #ccc;
     cursor: pointer;
   }
   .draggable-placeholder-inner{
     border: 1px dashed #0088F8;
     box-sizing: border-box;
     background: rgba(0, 136, 249, 0.09);
     color: #0088f9;
     text-align: center;
     padding: 0;
     display: flex;
     align-items: center;
   }
   .row .col-3 {
     float: left;
   }
   ```





### Mixin으로 Component  외 data + methods 정의하기

#### base.html에서 vue_init_script block보다 더 위에 vue_mixins block 생성

-  mixin이 없는 곳에서도 vue instance 생성시 mixins : [ Mymixin ]; 을 사용하도록 할테니 default 빈 mixin 변수를 선언해서 넣어준다.

  - **var** : 중복 선언 가능. 재할당 가능.
  - **let** : 중복 선언 불가. 재할당 가능. 
    - 중복선언 시, 해당 변수는 이미 선언되었다는 에러 메시지를 뱉는다.
  - **const** : 중복선언 불가. 재할당 불가. 

  ```html
  {% block extra_foot_script %}
  {% endblock extra_foot_script %}
  
  {% block vue_mixins %}
  <script>
      let myMixin = {};
  </script>
  {% endblock vue_mixins %}
  
  {% block vue_init_script %}
  <script>
  
      // console.log(treeItem)
      var app = new Vue({
          el: '#app',
          delimiters: ['{$', '$}'],  // jinja와 같이 쓸 vue 변수
  
          mixins: [myMixin],
  ```



- **block을 따로 생성하지 않고, **extra_foot_script block에서 초기화하여 -> 다른 곳에서 다른게 초기화하면, **상속관계에서, 덮어쓰기 되어버린다.**
  - 새로운 block을 만들어야한다.

#### 공통 data/method 등이 아니라면, 개별html에서 개별 vue_mixins에 정의해서, 공통 vue instance에 포함되도록 만든다.

- 개별html에서 `vue_mixins block`에  **개별 data, 개별 method, 개별 component를 정의**해주고, **공통 vue생성코드가 적힌`vue_init_script block`에 포함되게 한다.**

```html
{% block vue_mixins %}
<script>

    const th = window.treeHelper
    const {DraggableTree} = window.vueDraggableNestedTree;

    // Vue.component('tree', DraggableTree);
    let myMixin = {
        data() {
            return {
 
                draggableTreeData: [
                    {text: 'node 1'},
                    {text: 'node 2'},
                    {text: 'node 3 undraggable', draggable: false},
                    {text: 'node 4 undroppable', droppable: false},
                    {
                        text: 'node 5', children: [
                            {text: 'node 6'},
                            {text: 'node 7'},
                        ]
                    },
                ],
            };
        },

        components: {
            'tree': DraggableTree
        },
        methods: {
            collapseAll: function () {
                console.log('collapseAll');
            },
            expandAll: function () {
                console.log('expandAll');
            }
        }
    };
</script>
{% endblock vue_mixins %}

```



### 스타일 변경 및 버튼 추가

![image-20230127003411443](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230127003411443.png)

- css

```css
<style>
    /* tree 공간 */
    .he-tree {
        /*border: 1px solid #ccc;*/
        border-radius: 3%;
        padding: 20px;
        width: 300px;

        /*is-light*/
        background: #f5f5f5;
    }

    /* 개별 item */
    .tree-node-inner {
        padding: 7px;
        border: 1px solid #ccc;
        cursor: pointer;

        background: white;
    }

    /* drag시 item */
    .draggable-placeholder-inner {
        border: 1px dashed #0088F8;
        box-sizing: border-box;
        background: rgba(0, 136, 249, 0.09);
        color: #0088f9;
        text-align: center;
        padding: 0;
        display: flex;
        align-items: center;
    }
    
</style>
```

- 컴포넌트 사용

```html
<div class="box">
    <!-- 모두 접기 모두 열기 버튼   -->
    <div class="columns ">
        <div class="column">
            <div class="buttons ">
                <b-button class=""
                          @click="collapseAll"
                          size="is-small"
                >
                    모두 접기
                </b-button>
                <b-button class="is-outlined is-dark"
                          @click="expandAll"
                          size="is-small"
                >
                    모두 열기
                </b-button>
            </div>
        </div>
    </div>
    <!-- tree 공간   -->
    <div class="columns">
        <div class="column ">
            <tree :data="draggableTreeData"
                  draggable="draggable"
                  cross-tree="cross-tree">

                <div slot-scope="{data, store}">
                    <template v-if="!data.isDragPlaceHolder">
                        <span class="pl-2"> {$ data.text $}</span>
                        <span
                                class="is-pulled-right pr-3"
                                v-if="data.children && data.children.length"
                                @click="store.toggleOpen(data)">
                            <small class="has-text-grey">{$ data.open ? '▶' : '▼' $}</small>
                        </span>
                    </template>
                </div>

            </tree>
        </div>
    </div>
</div>

```



### 응용 1

- [응용 문서](https://vuejsexamples.com/a-vue-js-draggable-tree-component/)
- [응용 예제](https://codepen.io/phphe/pen/KRapQm)

1. 데이터 받아서 표기 [@change 내용 참고: BaseVue](https://github.com/phphe/vue-draggable-nested-tree/blob/master/src/examples/Base.vue)
1. 모두접기, 모두열기 버튼에 @click으로 method를 명시하고, `th` 를 이용하여 mixin에 개별 method를 추가한다.

   ```html
   <div class="buttons">
       <b-button class=""
                 size="is-small"
                 @click="collapseAll"
                 >모두 접기</b-button>
       <b-button class="is-outlined is-dark"
                 size="is-small"
                 @click="expandAll"
                 >모두 열기</b-button>
   </div>
   ```

   - th 변수를 이용할 때 bfs로 `this.draggableTreeData`전체를 넣어준다.
     - **순회하면서 각 node마다 `.open`변수를 true로 만들어준다.**




### 응용 2개 구조 분석

#### Page

- [컴포넌트](https://github.com/KevinduPreez/semantic-website/blob/3bd874d954a9b38dfeea9a4fa5ad21be3a50fd92/vendor/statamic/cms/resources/js/components/structures/PageTree.vue)

- [view1 ](https://github.com/KevinduPreez/semantic-website/blob/3bd874d954a9b38dfeea9a4fa5ad21be3a50fd92/vendor/statamic/cms/resources/js/components/collections/View.vue)

- [view2](https://github.com/KevinduPreez/semantic-website/blob/3bd874d954a9b38dfeea9a4fa5ad21be3a50fd92/vendor/statamic/cms/resources/js/components/navigation/View.vue)

1. **Tree 컴포넌트 정의**할 때  현재 

   1. **컴포넌트 정의시 자체 tree 변수**로서 data변수 `treeData`;를  컴포넌트에 `:data`  내부에서 사용될 약속된 props로 집어넣는다.

      ```html
      <draggable-tree
                      draggable
                      ref="tree"
                      :data="treeData"
      ```

   - data() { return } 에서 `treeData: []` 의 빈 배열로 초기화한다.

     ```js
     data() {
             return {
                 loading: false,
                 saving: false,
                 pages: [],
                 treeData: [],
     ```

     

2. **메인에서 <page-tree> 사용시, 컴포넌트 내부변수 `treeData`에 `props로 데이터를 집어넣어 주지 않는다.`**

   - 자체변수 -> props에 등록안함 -> 메인으로부터 공급안받음

   - **내부에서 treeData=[]에서 시작하여, `컴포넌트 정의시 자체적으로 공급`할 예정**한다.

     ```html
       <page-tree
                 v-if="canUseStructureTree && view === 'tree'"
                 ref="tree"
                 :has-collection="true"
                 :collections="[handle]"
                 :create-url="createUrl"
                 :pages-url="structurePagesUrl"
                 :submit-url="structureSubmitUrl"
                 :submit-parameters="{ deletedEntries, deleteLocalizationBehavior }"
                 :max-depth="structureMaxDepth"
                 :expects-root="structureExpectsRoot"
                 :site="site"
                 @edit-page="editPage"
                 @changed="markTreeDirty"
                 @saved="markTreeClean"
                 @canceled="markTreeClean"
             >
     ```



3. :data에 들어가는 tree전용 자체변수 `this.treeData`에 데이터를 공급하는 순간은 **`updateTreeData()` 메서드에서 `clone(this.pages)`을 통해서 한다.**

   1. **원본데이터 `this.pages`를 => `clone()`후  => tree용 자체변수 `this.treeData`에 집어넣는다.**

      ```js
      updateTreeData() {
                  this.treeData = clone(this.pages);
              },
      ```

   2. **이 this.pages => this.treeData**의 `updateTreeData()`는 

      1. **`외부데이터`를 받아오는 `getPages()`로 부터 공급용 변수  `this.pages`가 채워진 뒤**, **클론하여 this.treeData**를 채우거나

         ```js
         getPages() {
             this.loading = true;
             const url = `${this.pagesUrl}?site=${this.site}`;
             return this.$axios.get(url).then(response => {
                 this.pages = response.data.pages;
                 this.updateTreeData();
                 this.loading = false;
             });
         },
         ```

      2. **`사용자의 컴포넌트의 변화`로 인데 tree의 `@change="treeChanged"`가 호출 되었는데, `유효하지 않았을 때, 사용자변화를 무시하고, this.pages로 다시 덮어씌우기`를 하거나 **

         ```html
         <draggable-tree
                         draggable
                         ref="tree"
                         :data="treeData"
                         :space="1"
                         :indent="24"
                         @change="treeChanged"
         ```

         ```js
         treeChanged(node, tree) {
             if (!this.validate()) {
                 // 변화를 허용하지 않을 때, 기존 this.pages로 다시 덮어씌우기(복구용)
                 this.updateTreeData();
                 return;
             }
         
             this.treeUpdated(tree);
         },
         ```

      3. **`메인에서 어떤 동작을 취소하여, 초기데이터로 복구`할 때 호출된다.**

         ```js
         cancel() {
             if (! confirm(__('Are you sure?'))) return;
             this.pages = this.initialPages;
             this.updateTreeData();
             this.$emit('canceled');
         },
         ```

         - `cancel()`은 컴포넌트 정의 메서드지만, **메인에서는 취소 -> 컴포넌트 내부에서도 취소되어야하는데, `메인에서 tree에 직접적으로 접근하기 위해 메인 컴포넌트 사용시 ref를 걸고, ref로 tree에 접근`하는 방식을 취한다** 

           ```js
           methods: {
               cancelTreeProgress() {
                   this.$refs.tree.cancel();
                   this.deletedEntries = [];
               },
           ```

   3. **그렇다면, 공급용 `this.pages`는 어디서 가져올 까?**

      1. **컴포넌트 정의 created()**에서 **최초로 외부데이터를 가져오는데** `this.getPages()`메서드에 의해 `this.pages`를 채우고, 클론한 뒤 `this.treeData`도 업데이트한다.

         ```js
          getPages() {
                     this.loading = true;
                     const url = `${this.pagesUrl}?site=${this.site}`;
                     return this.$axios.get(url).then(response => {
                         this.pages = response.data.pages;
                         this.updateTreeData();
                         this.loading = false;
                     });
                 },
         ```

      2. `this.pages => this.treeData( 클론 )`을 채우고 난 뒤 **`공급데이터 this.pages를 this.initialPages에도 백업`한다**

         - **tree와는 연동안되도록, `this.treeData`는 클론 할당**
         - **백업데이터는 공급용 this.pages와 항상 연동되게 그냥 할당**한다

         ```js
         created() {
             this.getPages().then(() => {
                 // 외부에서 받아온 것을 initialPages도 항상 연동
                 this.initialPages = this.pages;
             })
             this.$keys.bindGlobal(['mod+s'], e => {
                 e.preventDefault();
                 this.save();
             });
         },
         ```

   4. 한편, **`tree가 @change`로 변할 때, 유효하지 않으면 기존 공급데이터 this.pages로 tree를 덮어씌우지만, 유효한다면 `this.treeUpdated(tree)`를 호출하여**

      1. **ref="tree"에 의해 `현재 tree에 접근`한 뒤**
      2. **`.getPureData()`만 가져와서**
      3. **`새로운 공급데이터로서 this.pages`에 `현재 트리데이터(this.$refs.tree.getPureData() )`를  덮어씌운다**
      4. 메인에는 $emit으로 changed가 호출되게 한다.

      ```html
      <draggable-tree
                      draggable
                      ref="tree"
                      :data="treeData"
                      :space="1"
                      :indent="24"
                      @change="treeChanged"
                      @drag="treeDragstart"
                      >
      ```

      ```js
      treeChanged(node, tree) {
                  if (!this.validate()) {
                      this.updateTreeData();
                      return;
                  }
                  // 유효할시 호출
                  this.treeUpdated(tree);
              },
      
      ```

      ```js
      treeUpdated(tree) {
                  tree = tree || this.$refs.tree;
                  this.pages = tree.getPureData();
                  this.$refs.soundDrop.play();
                  this.$emit('changed');
              },
      ```

      5. 메인에서는 @changed를 받아, `mark Tree Dirty`메서드를 호출되게 하여 `메인의 this.$dirty`에다가 추가해놓는다.

         ```html
         <page-tree
                    v-if="canUseStructureTree && view === 'tree'"
                    ref="tree"
                    :has-collection="true"
                    :collections="[handle]"
                    :create-url="createUrl"
                    :pages-url="structurePagesUrl"
                    :submit-url="structureSubmitUrl"
                    :submit-parameters="{ deletedEntries, deleteLocalizationBehavior }"
                    :max-depth="structureMaxDepth"
                    :expects-root="structureExpectsRoot"
                    :site="site"
                    @edit-page="editPage"
                    @changed="markTreeDirty"
                    @saved="markTreeClean"
                    @canceled="markTreeClean"
                    >
         ```

         ```js
         markTreeDirty() {
                     this.$dirty.add('page-tree');
                 },
         ```

   5. **유효성 검증은 @change가 호출될 때 하자.**

      - isValid를 true로 초기화해놓고, 검증에 걸리면 false로 반환, 아니면 그냥 반환되게 하는 flag를 사용한다.

      - DFS로 `this.treeData`(공급받은 자체 데이터)를 돌려서, 검증한다.

        - **각 node들은 `.parent.children`으로 나와 동급인 node들을 한데 모아놓고 .`indexOf( 현재node )`로 현재 node의 위치를 찾을 수 있다**
          - **넣어준 필드 외 `.parent`도 연동데이터 `this.treeData`에 바로 생긴다**
        - `node._vm.level`로 depth를 구한다.
          - **tree와 연계된 정보인 .level은 `.level`이 아니라 `._vm.level`로 _vm을 통해서 내부 tree속 정보를 챙긴다.**
        - tree를 의미하는 `this`에서 `.expectsRoot` 면서, level 1이면서, index === 0이면 실제 `isRoot`가 된다.
        - isRoot면서, 자식이 1개이상 있다면, valid에서 change에서 false;다 . 즉 **root면서, 자식이 있으면, 변화못하게 막는다.**

        ```js
        validate() {
            let isValid = true;
            th.depthFirstSearch(this.treeData, (childNode) => {
                const index = childNode.parent.children.indexOf(childNode);
                const level = childNode._vm.level;
                const isRoot = this.expectsRoot && level === 1 && index === 0;
                if (isRoot && childNode.children.length > 0) {
                    isValid = false;
                } 
            });
            return isValid;
        },
        ```

   6. **addPage**메서드 **컴포넌트 내부에서 정의**지만 **외부 메인에서만 `this.$ref.tree.addPages(pages, this.targetParent)`로 호출**된다.

      1. page셀럭트 뷰에서 selected로 호출

         ```html
         <page-selector
                     v-if="hasCollections && $refs.tree"
                     ref="selector"
                     :site="site"
                     :collections="collections"
                     @selected="entriesSelected"
                 />
         ```

      2. pages로 복수로 인자가 들어와 addPages( page, this.targetParent)

         ```js
         entriesSelected(pages) {
                     this.$refs.tree.addPages(pages, this.targetParent);
                 },
         ```

      3. **컴포넌트 정의시에 메서드 정의**

         - **외부에서 넣어주는 부모**가 없을 수도 있다. **판단은` 컴포넌트 정의부에 정의한 이유`로서 `외부 부모의 .data.children`이 있는지로 확인하고 없으면 `컴포넌트 내부 자체 this.treeData`를 대신 할당해주어, parent를 tree자체로 취급한다.?!**
         - 이제 여러 pages(node들)을 forEach로 순회하면서, **각 page를 parent로서, node object를 push해준다.**
         - 역시 컴포넌트 정의부로서 **바뀐 treeData를 => 공급data인 this.pages에 같이 업데이트까지** 해준다.
         - **`tree내부의 여러요소를 사용하기 위해, 외부에서 인자들이 갖추어지지만, [ 공급데이터 수정 후 => 내부데이터를 this.treeUpdated()로 반영]하기 위해 tree내부 메서드 정의 후 tree내부 메서드를 ref로 호출해서 처리하는 중`**

         ```js
         addPages(pages, targetParent) {
             const parent = targetParent
             ? targetParent.data.children
             : this.treeData;
             pages.forEach(selection => {
                 parent.push({
                     id: selection.id,
                     title: selection.title,
                     slug: selection.slug,
                     url: selection.url,
                     edit_url: selection.edit_url,
                     children: []
                 });
             });
             this.treeUpdated();
         },
         ```

      4. addPages()는 [외부 다른view](https://github.com/KevinduPreez/semantic-website/blob/3bd874d954a9b38dfeea9a4fa5ad21be3a50fd92/vendor/statamic/cms/resources/js/components/navigation/View.vue)에서 

         1. dropdown 중 1개  vm없는 addLink()  -> vm없는 linkPage() -> -> 부모(vm)없는 addPages()

         2. tree속 자식 컴포넌트 -> vm을 받는 컴포넌트 속 dropdown -> vm을  this.targetParent 전역변수에 -> 부모 있는

            ```html
             <dropdown-list :disabled="! hasCollections">
                                <template #trigger>
                                    <button
                                        class="btn"
                                        :class="{ 'flex items-center pr-2': hasCollections }"
                                        @click="addLink"
                                    >
                                        {{ __('Add Link') }}
                                        <svg-icon name="chevron-down-xs" class="w-2 ml-2" v-if="hasCollections" />
                                    </button>
                                </template>
                                <dropdown-item :text="__('Link to URL')" @click="linkPage()" />
                                <dropdown-item :text="__('Link to Entry')" @click="linkEntries()" />
                            </dropdown-list>
            ```

            

            ```js
            addLink() {
                // 부모없는 경우
                if (!this.hasCollections)
                    // vm인자 없이 this.linkPage호출
                    this.linkPage();
            },
                // vm을 받아 add될 놈의 부모로 뽑아내는 경우
            ```

            ```html
            <template #branch-options="{ branch, removeBranch, orphanChildren, vm, depth }">
                <dropdown-item
                               v-if="depth < maxDepth"
                               :text="__('Add child link to URL')"
                               @click="linkPage(vm)" />
                <dropdown-item
                               v-if="depth < maxDepth"
                               :text="__('Add child link to entry')"
                               @click="linkEntries(vm)" />
                <dropdown-item
                               :text="__('Remove')"
                               class="warning"
                               @click="deleteTreeBranch(branch, removeBranch, orphanChildren)" />
            </template>
            ```

            ```js
            linkPage(vm) {
                // vm을 받아 부모로 취급.
                this.targetParent = vm;
                this.openPageCreator();
            },
            ```

      5. 삭제는 커스텀branch 자식컴포넌트에서 시작된다.

         1. branch컴포넌트 내부 dropdown에서 **더 자식 dropdown-list 컴포넌트에서 `remove-branch`를 emit으로 받으면t**에서 remove-branch prop이 작동하여, **branch는 자신의 `remove`메서드를 호출**한다

            ```html
            <dropdown-list class="ml-2" v-if="!isRoot">
                <slot name="branch-options"
                      :branch="page"
                      :depth="depth"
                      :remove-branch="remove"
                      :orphan-children="orphanChildren"
                      />
            </dropdown-list>
            ```

         2. **branch remove는 공급데이터 this.page에서 `._vm.store`를 통해, store를 변수로 받고**

            - `store.deleteNode`(this.page)를 통해 node를 삭제한다?!
            - 그리고 tree에게 **emit removed에게 `store`를 반환**한다

            ```js
            remove() {
                const store = this.page._vm.store;
                store.deleteNode(this.page);
                this.$emit('removed', store);
            },
            ```

         3. tree는 **branch 자식컴포넌트에게 store를 전달받은 @removed = ""프롭스를 통해 "`pageRemoved`"메서드를 `store를 받아서 호출`한다**

            ```html
            <tree-branch
                         slot-scope="{ data: page, store, vm }"
                         :page="page"
                         :depth="vm.level"
                         :vm="vm"
                         :first-page-is-root="expectsRoot"
                         :hasCollection="hasCollection"
                         @edit="$emit('edit-page', page, vm, store, $event)"
                         @removed="pageRemoved"
                         @children-orphaned="childrenOrphaned"
                         >
            ```

         4. tree는 store를 tree로 간주하고, pageRemoved에서 tree를 인자로 받아 **store에서, 공급데이터 this.page를 삭제한 store(emit) -> tree로 받은 것을 `.getPureData()로 받아 공급데이터 this.page`에 덮어씌운다.**

            - 즉, 자식으로부터 점점 node가 삭제된 store == tree를 받아 tree 속 공급데이터 this.pages를 재할당해준다.
            - 그리곤 메인으로 changed가 호출되게 한다.

            ```js
            pageRemoved(tree) {
                this.pages = tree.getPureData();
                this.$emit('changed');
            },
            ```

         5. 메인 속 tree는 데이터가 없는 신호 emit changed -> 메인의 markTree dirty메서드를 호출해서 끝낸다.

            ```html
            <page-tree
                       v-if="canUseStructureTree && view === 'tree'"
                       ref="tree"
                       :has-collection="true"
                       :collections="[handle]"
                       :create-url="createUrl"
                       :pages-url="structurePagesUrl"
                       :submit-url="structureSubmitUrl"
                       :submit-parameters="{ deletedEntries, deleteLocalizationBehavior }"
                       :max-depth="structureMaxDepth"
                       :expects-root="structureExpectsRoot"
                       :site="site"
                       @edit-page="editPage"
                       @changed="markTreeDirty"
                       @saved="markTreeClean"
                       @canceled="markTreeClean"
                       >
            ```

         6. 바뀐 page-tree를 dirty에 추가한다.

            ```js
            markTreeDirty() {
                this.$dirty.add('page-tree');
            },
            ```

      6. **메인에서는 `v-if`로 `this.$dirty에 page-tree가 차있다`면**

         1. 취소 a태그 클릭이 가능해진다
         2. save버튼 클릭이 가능해진다.
         3. 확인은 computed에서 한다.

         ```js
         computed: {
                 treeIsDirty() {
                     return this.$dirty.has('page-tree');
                 },
         ```

         ```html
         <div class="btn-group mr-2" 
              v-if="canUseStructureTree && !treeIsDirty">
             <button class="btn px-2" @click="view = 'tree'" :class="{'active': view === 'tree'}" v-tooltip="__('Tree')">
                 <svg-icon name="structures" class="h-4 w-4"/>
             </button>
             <button class="btn px-2" @click="view = 'list'" :class="{'active': view === 'list'}" v-tooltip="__('List')">
                 <svg-icon name="assets-mode-table" class="h-4 w-4" />
             </button>
         </div>
         
         <template v-if="view === 'tree'">
         
             <a
                class="text-2xs text-blue mr-2 underline"
                v-if="treeIsDirty"
                v-text="__('Discard changes')"
                @click="cancelTreeProgress"
                />
         ```

      7. **메인에서 dirty가 차서 취소**를 누르면, tree ref를 이용해 내부 cancel()메서드를 호출한다.

         ```js
         cancelTreeProgress() {
             this.$refs.tree.cancel();
             this.deletedEntries = [];
         },
         
         ```

         - **tree의 cancel메서드는 초기저장데이터를 공급데이터로 다시 바꾸고, tree도 업데이트해준 뒤, 메인에 canceled를 데이터 없이 emit한다**

           ```js
           cancel() {
               if (! confirm(__('Are you sure?'))) return;
               this.pages = this.initialPages;
               this.updateTreeData();
               this.$emit('canceled');
           },
           ```

         - 메인으로 @canceled가 넘어오면 markTreeClean을 호출하여 dirty에서 page-tree를 제거한다.

           ```html
           <page-tree
                      v-if="canUseStructureTree && view === 'tree'"
                      ref="tree"
                      :has-collection="true"
                      :collections="[handle]"
                      :create-url="createUrl"
                      :pages-url="structurePagesUrl"
                      :submit-url="structureSubmitUrl"
                      :submit-parameters="{ deletedEntries, deleteLocalizationBehavior }"
                      :max-depth="structureMaxDepth"
                      :expects-root="structureExpectsRoot"
                      :site="site"
                      @edit-page="editPage"
                      @changed="markTreeDirty"
                      @saved="markTreeClean"
                      @canceled="markTreeClean"
                      >
           ```

           ```js
           markTreeClean() {
               this.$dirty.remove('page-tree');
           },
           ```

      8. **메인에서 dirty가 차서 save버튼**를 누르면,  메인 `saveTree`메서드가 호출되며, 내부에서 조건확인 후 performTreeSaving()이 한번 더 호출되고, **메인에서 ref.tree를 이용해서 tree속 .save()메서드를 호출한다.**

         ```js
         saveTree() {
             if (this.sites.length === 1 || this.deletedEntries.length === 0) {
                 this.performTreeSaving();
                 return;
             }
             this.showLocalizationDeleteBehaviorConfirmation = true;
             this.localizationDeleteBehaviorConfirmCallback = (behavior) => {
                 this.deleteLocalizationBehavior = behavior;
                 this.showLocalizationDeleteBehaviorConfirmation = false;
                 this.$nextTick(() => this.performTreeSaving());
             }
         ```

         ```js
         performTreeSaving() {
             this.$refs.tree
                 .save()
                 .then(() => (this.deletedEntries = []))
                 .catch(() => {});
         },
         ```

         - tree의 save는 **saving 플래그 + tree공급데이터인 this.pages를 가진 payload를 만들어서 post로 보내고, main에 saved를 emit한다.**
           - **save가 성공하면, `this.initialpages = this.pages`로서 초기데이터를 현재 데이터로 바꿔준다.**
           - **성공/실패 상관없이 .finally로 saving 플래그를 false로 바꿔준다.**
             - 아마 save중임을 나타내는 변수인 것 같은데 쓰이진 않는다.

         ```js
         save() {
                     this.saving = true;
                     const payload = { pages: this.pages, site: this.site, expectsRoot: this.expectsRoot, ...this.submitParameters };
                     return this.$axios.post(this.submitUrl, payload).then(response => {
                         this.$emit('saved');
                         this.$toast.success(__('Saved'));
                         this.initialPages = this.pages;
                         return response;
                     }).catch(e => {
                         this.$toast.error(e.response ? e.response.data.message : __('Something went wrong'));
                         return Promise.reject(e);
                     }).finally(() => this.saving = false);
                 },
         ```





#### 적용





#### vue_dynamic_tree

- [컴포넌트](https://github.com/Atmden/vue_dynamic_tree/blob/main/resources/js/components/DynTreeComponent.vue)

- [view](https://github.com/Atmden/vue_dynamic_tree/blob/main/resources/views/profile/my_referals.blade.php)
- 