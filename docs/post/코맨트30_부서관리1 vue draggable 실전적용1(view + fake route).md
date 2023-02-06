#### 적용



##### created에서 외부데이터 => 공급데이터/treeData/백업데이터 3개 만들기

1. 원래는 컴포넌트 정의시 선언하지만, **메인에서** 외부에에서 받는 공급용 변수 `depts`와 tree 자체 변수 `treeData`를 선언한다

   ```js
   
   data() {
       return {
           depts: [], // 외부 => treeData에 공급할 변수
           treeData: [], // tree 자체 변수
   ```

   

2. `this.depts`를 외부에서 채우는 메서드 `getDepts()`는

   - 원래는 컴포넌트 정의시 created에 넣어야하지만 **메인 created에서 사용되어** 메서드 내부에서 this.depts를 채운 뒤, **성공적으로 채웠으면, 백업용 데이터 `this.initialDepts`와 `확인해보니 변수에 변수할당 연결 안되지만` 채운다.**
     - [객체비교 정리본](https://mine-it-record.tistory.com/446)

   ```js
   created()  {
       // this.getDepts()
       //     .then(() => {
       //         this.initialDepts = this.depts;
       //     });
       this.getDepts();
       this.initialDepts = this.depts;
       })
   },
   ```

   - 백업용 변수 `this.initialDepts = []`배열 + isLoading flag변수를 초기화해주고

     ```js
     data() {
         return {
     
             depts: [], // 외부 => treeData에 공급할 변수
             treeData: [], // tree 자체 변수
             initialDepts: [], // 외부공급 depts를 받을 때 백업 변수
             isLoading: false, // getDepts요청시 로딩처리 flag
     ```

   - `getDepts()`를 정의한다. 

     - 원래는 axios로 받아와야하지만, 지금은 바로 넣어준다.
     - **`외부 -> this.depts(공급용 변수)`를 받아온 순간 `tree용 자체데이터 this.treeData`도 같이 업데이트해줘야하는데, `this.updateTreeData()`메서드로 처리한다.**

     ```js
     getDepts() {
     
         // this.loading = true;
         // const url = `${this.getDeptsUrl}?page=${this.page}`;
         //
         // return this.$axios.get(url).then(response => {
         //     this.depts = response.data.depts;
         //     this.updateTreeData();
         //     this.loading = false;
         // })
     
         this.depts = [
             {id: 1, level: 0, sort: 1, text: 'node 1', open: false},
             {id: 2, level: 0, sort: 2, text: 'node 2', open: false},
             {id: 3, level: 0, sort: 3, text: 'node 3 undraggable', draggable: false, open: false},
             {id: 4, level: 0, sort: 4, text: 'node 4 undroppable', droppable: false, open: false},
             {
                 id: 5, level: 0, sort: 5,
                 text: 'node 5', children: [
                     {id: 6, level: 1, sort: 1, text: 'node 6'},
                     {id: 7, level: 1, sort: 2, text: 'node 7'},
                 ], open: false
             },
         ];
     
         this.updateTreeData();
     },
     ```

3. getDepts로 외부에서 `this.depts를 채우고 나면 -clone한뒤 ->  this.treeData`도 그대로 채워줘야하는데, **`updateTreeData()`를 정의**한 뒤, **외부용 this.depts를 `clone()해서 this.treeData를 채워` 서로 연계안되게 한다**.

   - clone은 정의해줘도 되지만, import한 `th`에 모듈로 들어가있다.
   - initialDepts는 그냥 할당 / treeData는 클론해서 할당한다.

   ```js
   updateTreeData() {
       console.log("updateTreeData")
   
       this.treeData = th.clone(this.depts);
   },
   ```



###### 정리

- created 안에서 
  - getDepts ( 외부 => this.depts) -> 
    - updateTreeData ( this.depts =clone=> this.treeData) -> 
  - 백업용 this.depts=>this.initialDepts



![image-20230128181628017](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128181628017.png)



4. 이제 메인html에서 컴포넌트를 사용하면서

   1. `ref = "tree"`를 통해 **외부에서 tree에 직접 접근**할 수 있게 한다
   2. `:data ="treeData"`로 **미리 제공되는 props `:data`에 `treeData`를 넣어줘서 컴포넌트 내부에서 사용할 수 있게 해준다.**

   ```html
   <tree
         draggable
   
         ref="tree"
         :data="treeData"
   ```

   ![image-20230128182332184](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128182332184.png)





##### 사용자에 의한 컴포넌트 내부 treeData 변화 -> 공급데이터 this.depts로 반영하기

5. **사용자에 의한 treeData의 변화는 `제공되는 부모의 kebab-case emit event으로`받아야한다. [공식문서](https://github.com/phphe/vue-draggable-nested-tree#node_properties)를 보면 `Tree event로 @change`에 의해 감지**하여 메서드를 실행한다. 이 때, **변화된 내부treeData를 => 메인의 this.depts에 반영되어야한다.**

   - 공식문서

     ```js
     // store is the tree vm
     drag(node), // on drag start.
     drop(node, targetTree, oldTree), // after drop.
     change(node, targetTree, oldTree), // after drop, only when the node position changed
     nodeOpenChanged(node); // on a node is closed or openㅇ
     ```

   - **메인에서 컴포넌트 사용에 @change를 정의하고 `"treeChanged"메서드`를 정의하자**
     - emit시 `node, tree` 2개를 넘겨준다.

   ```html
   <tree
         draggable
         ref="tree"
         :data="treeData"
   
         @change="treeChanged"
   ```

   

6. **`treeChanged`는 사용자에 의해 변화된 내부treeData를 감지하여 가져올 예정인데 `유효한 변화인지` 먼저 판단해야한다.**

   1. **유효하지 않을 경우, `외부공급this.depts -> 내부변화된 this.treeData를 다시 덮어쓰기`하도록 `this.updateTreeData()`를 한번 더 호출한다.**
   2. 유효할 경우, `내부변화 this.treeData -> this.depts`로 외부로 가져와야하는데 **새롭게 `this.treeUpdated(tree);` 메서드를 구현한다.**

   ```js
   treeChanged(node, tree) {
       console.log('treeChanged----')
       // 유효하지 않으면, 유효X내부 tree데이터를 <- 기존 공급된 depts데이터로 덮어써서 없앰
       if (!this.validate()) {
           this.updateTreeData();
           return;
       }
       // 유효한 경우, 유효O내부 tree데이터를 -> 외부공급 this.depts로 가져옮 
       this.treeUpdated(tree);
       console.log('treeChanged====')
   },
   ```

7. **이 때, treeChanged의 인자로 넘어오는`node와 tree`는 `선택node + 바뀐 tree`로 넘어오는 것이 확인되었지만,  validate는 따로 인자를 안받고, `컴포넌트 내부데이터인 this.treeData`를 활용한다. `아마도 전역변수this.treeData로 검증하여, 다른곳에서도 쓸 수 있게?! 인자없는 전역메서드로 만듦`**

   - **`this.treeData`는 tree와 연동된다.**

     ![image-20230128185005581](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128185005581.png)

   - 예제의 검증은 **외부에서 root라고 생각했으면서 &&  이동된 위치가 root의 1번째인데 자식이 있으면 탈락을 검증**한다

     - **즉, `첫메뉴로 자식이 있는 놈을 옮겨서는 안된다.`**

     ![image-20230128220038888](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128220038888.png)

     - 내부 `this.treeData`를 1개씩 node별로 `th.dfs`로 탐색하며
     -  `node`.**parent.children.indexOf(**  `node`) 를 통해서 **부모의 자식들을 대상으로 `자신의 순서`를 찾고**
       - **tree와 연동된 this.treeData는 for문 돌리면 자동으로 node가 들어가있다. `.parent`로 바로 찾으면 된다.**
     - `node`**._vm.level**로  **`자신의 depth`**를 찾고
       - **tree와 관련된 `node의 정보` 중 `.level`/ `.store(tree정보)` 는 `._vm`에서 찾으면 된다.**
     - 외부에서 넘어오는 flag structureExpectsRoot -> expecsRoot를 바탕으로 `자신의 depth(level) === 1` && `index == 0`일 때, isRoot를 true로 만든 뒤
       - 자식이 있으면 false, 자식이 없으면 true가 반환되게 한다
       - 즉, root인데 자식이 없어야지 true로 유지되고, **하나라도 자식있는 root가 나타나면 false로 탈락이다.**

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

   - 나의 경우, 첫 node가 자식있어도 상관없으므로 `validateFirstNotParent()`로 변경하고, **부모가 같은 조건을 검증한 validateSameParent()**를 하나 더 만들어서 넣어주고 싶은데

     - **node의 원래 가지고 있던 parent_id와, 바뀐 node.parent.id를 비교해서 서로 다르면 유효하지 않는 이동이라 취급한다.**

       - 그러려면 node정보를 인자로 받아야한다.

     - 먼저, node의 정보로서 기존 parent_id를 가짜로 넣어준다.

       ```json
       {
           id: 5, depth: 0, sort: 5, text: 'node 5', 
           children: [
               {id: 6, parent_id: 5, depth: 1, sort: 1, text: 'node 6'},
               {id: 7, parent_id: 5, depth: 1, sort: 2, text: 'node 7'},
           ], o
       ```

     - **tree속에서 parent가 없을 경우, .id를 찍으면 null이 아닌 `undefined`로 떠서 `null`과 다르다고 나오니 `null초기화 이후, 해당변수 if로 확인 후 있으면 대입` 처리해줘아야한다**

     - **추가 버그 => 자식이 있는 root node는 undefined라 뜬다 => 처리해줘야한다**

       ![image-20230128222059274](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128222059274.png)

   - treeChanged

     ```js
     treeChanged(node, tree) {
         console.log('treeChanged----')
     
         // 유효하지 않으면, 유효X내부 tree데이터를 <- 기존 공급된 depts데이터로 덮어써서 없앰
         // if (!this.validateFirstNotParent()) {
         if (!this.validateSameParent(node)) {
             this.toast('동일한 부모 부서아래 순서이동만 가능합니다.', 'is-danger')
             this.updateTreeData();
             return;
         }
         // 유효한 경우, 유효O내부 tree데이터를 -> 외부공급 this.depts로 가져옮
         this.toast('유효한 treeChanged.')
         this.treeUpdated(tree);
     
         console.log('treeChanged====')
     },
     
     ```

   - **`validateSameParent(node)`**

     ```js
     validateSameParent(node) {
         console.log('validateSameParent----')
         let isValid = true;
     
         // 원래 root는 null로 들어오는데, 자식이 있는 root는 undefine으로 뜬다.
         // let before_parent_id = node.parent_id;
         let before_parent_id = null;
         if (node.parent_id){
             before_parent_id = node.parent_id;
         }
     
     
         let after_parent_id = null; // db에 root의 parent_id는 null;이라고 기본값으로 줌.
         // node.parent로만 검사하면 level0에서도 parent는 존재하는 것으로 검사됨.
         if (node.parent.id) {
             after_parent_id = node.parent.id;
         }
         console.log('before_parent_id, after_parent_id >> ', before_parent_id, after_parent_id);
     
         if (before_parent_id !== after_parent_id) {
             isValid = false;
         }
     
         console.log('validateSameParent====')
         return isValid;
     },
     ```

8. **이제 유효한 변화에 대해서 tree에 의해 외부공급데이터 this.depts가  `this.treeData => this.depts`로 업데이트가 되어야한다.**

   - 외부 -> tree연동 데이터: `updateTreeData()`
   - **tree -> 외부 데이터 : `treeUpdated(tree)`**
     - tree가 인자로 들어오면 예비로 **ref에 걸어둔 tree에서도 default로 걸어준다.**
     - **tree속에서 연동되면서 추가정보가 붙는 this.treeData와 달리 `.getPureData()`만 뽑아서 `this.depts`를 업데이트 시킨다.**

   ```js
   treeUpdated(tree) {
       console.log('treeUpdated(tree -> this.depts)----')
       tree = tree || this.$refs.tree;
       // 연동데이터 this.treeData(.parent, _vm.level 등 자동 생성)과 달리 순수 데이터만 뽑아낸다.
       this.depts = tree.getPureData();
   
       console.log('this.depts >> ', this.depts);
       console.log('treeUpdated======================')
   },
   
   ```



###### 정리

- 사용자 tree변화
  - 유효한 변화인지 확인
  - `this.treeData` -> .getPureData -> `this.depts`

![image-20230128225631458](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128225631458.png)



##### (미적용) ondragstart에서, node에 set을 통해  droppable을 유효하지 않을 경우 false로 줘서, 못 내리게 만들기

```js
treeDragstart(node) {
    // Support for maxDepth.
    // Adapted from https://github.com/phphe/vue-draggable-nested-tree/blob/a5bcf2ccdb4c2da5a699bf2ddf3443f4e1dba8f9/src/examples/MaxLevel.vue#L56-L75
    let nodeLevels = 1;
    th.depthFirstSearch(node, (childNode) => {
        if (childNode._vm.level > nodeLevels) {
            nodeLevels = childNode._vm.level;
        }
    });
    nodeLevels = nodeLevels - node._vm.level + 1;
    const childNodeMaxLevel = this.maxDepth - nodeLevels;
    th.depthFirstSearch(this.treeData, (childNode) => {
        if (childNode === node) return;
        const index = childNode.parent.children.indexOf(childNode);
        const level = childNode._vm.level;
        const isRoot = this.expectsRoot && level === 1 && index === 0;
        const isBeyondMaxDepth = level > childNodeMaxLevel;
        let droppable = true;
        if (isRoot || isBeyondMaxDepth) droppable = false;
        this.$set(childNode, 'droppable', droppable);
    });
```



##### expadnAll, collaseAll은 bfs로 돌면서, tree연동 내부데이터 this.treeData의 각 node에 .open 값을 조절

```html
<div class="column">
    <div class="buttons">
        <b-button class="is-outlined is-rounded has-text-grey"
                  size="is-small"
                  @click="collapseAll"
                  >모두 접기
        </b-button>
        <b-button class="is-outlined is-dark is-rounded"
                  size="is-small"
                  @click="expandAll"

                  >모두 열기
        </b-button>
    </div>
</div>
```



```js
collapseAll: function () {
    console.log('collapseAll');

    th.breadthFirstSearch(this.treeData, node => {
        if (node.children && node.children.length) {
            node.open = false;
        }
    });

}
,
    expandAll: function () {
        // th의 내부에 hp.isArray => Array.isArray로 모두 수정
        console.log('expandAll');

        th.breadthFirstSearch(this.treeData, node => {
            if (node.children && node.children.length) {
                node.open = true;
            }
        });
    },
```







#### 다른 프로젝트(Vue.draggble) 예제로 select 상태 만들기

- [codepen](https://codesandbox.io/s/draggable-jmhrm?file=/src/components/itemTree.vue:106-115)

![image-20230128231143879](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230128231143879.png)



##### 개별node @click시 select를 만들어야, 그것을 부모로 한  addDept도 할 수 있다.

1. 단순히 active class를 추가하는 것이 목적이라면, 아래와 같이할 수 있다

   - 하지만 택1이 아니라 개별 선택이며, 되돌릴 수 없다.

     ```html
     @click="dept.active = !dept.active;"
     :class="{'active': dept.active}"
     ```

2. **여러개 중 택1을 해야한다면**

   1. 전역 selelctedId변수를 만들어, @click시 넣어주고

   2. :class 매핑에 조건문을 달아서, selectedId와 , 현재id가 같을 경우 class를 추가하게 한다.

      - true일때만 추가한다면 `:class={ 'class명' : 변수}`로 매핑해줘도 되지만
      - 조건문으로 true/false로 나눠야한다면 statement로서 `:class=" 변수 ? true : false "`

   3. **이 때, 다시 클릭시 토글되어야한다면, 전역id변수 === 개별item.id가 같을 경우, 전역변수를 초기화하는 작업까지 해줘야한다**

      ```js
      selectedDeptId: null,
      ```

      ```html
      <div slot-scope="{data: dept, store, vm}"
           ref="node"
      
           @click="selectedDeptId === dept.id ? selectedDeptId = null : selectedDeptId = dept.id"
           :class="{'active has-text-primary': dept.id === selectedDeptId}"
           class="p-2"
      >
      ```

   4. 이제 클릭했을때 입혀질 `active`의 css를 정의해준다.

      ```css
      /* 선택된 node에 표시 */
      .tree-node-inner > .active {
          font-weight: bold;
          border: solid 2px;
      }
      ```

      ![image-20230129024400528](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230129024400528.png)

   5. @click의 statemtn를 `selectNode( dept.id )`로 빼주자

      ```js
      // node관련
      selectNode(deptId) {
          // 선택되지 않은 dept라면, 할당 -> 선택됬다면 null로 선택 풀기
          if (this.selectedDeptId !== deptId) {
              this.selectedDeptId = deptId;
              return;
          }
          this.selectedDeptId = null;
      },
      
      ```

      ```html
      <div class="p-2"
           slot-scope="{data: dept, store, vm}"
           ref="node"
      
           @click="selectNode(dept.id)"
           :class="{'active has-text-primary': dept.id === selectedDeptId}"
           >
      ```

      





##### @dblclick시 node이름을 바꾸는 input태그를 보이게 + focuc <->  name보여주는 span태그 보이도록 만들기

1. @dblclick event emit을 받을 메서드 **`showNameInput( dept.id )`로 정의**하여 달아준다.

   ```html
   <div class="p-2"
        slot-scope="{data: dept, store, vm}"
        ref="node"
        @click="selectNode(dept.id)"
        :class="{'active has-text-primary': dept.id === selectedDeptId}"
   
        @dblclick="showNameInput(dept.id)"
        >
   ```

2. **없다가 보여질 `input태그` <-> 있던 것이 display:none; 될 `name출력용 span태그`는 dept.id로 `같은 dept.id지만 다른 #id`를 부여해줘야한다.**

   - **또한, `display: 'block'과 display:'none'`이 제대로 적용되려면 `부모태그가 inline-block`이어야한다**

   1. 2개의 태그를 하나의 `is-inline-block`으로 묶어줄 span태그를 씌운 뒤

   2. **각각에 `:id=`매핑을 `'#node'-dept.id` 와 `'#name'-dept.id`를 만들어서 넣어준다.**

      - 추가적으로 input태그에는 현재name을 :value에 / input크기창을 현재name + 3정도로 :size에 /  처음에는 안보이도록 style=display:none;을 지정해준다.

      ```html
      <!-- display:none; 이후 공간차지 없으려면  inline-block으로 바깥에 한번 씌워서 2개를 한꺼번에 집어넣어준다 -->
      <span class="pl-2 is-inline-block">
          <span :id="'node-' + dept.id">
              {$ dept.text $}
          </span>
          <input type="text"
                 :id="'name-' + dept.id"
                 :value="dept.text"
                 :size="dept.text.length + 3"
                 style="display: none;"
                 >
      </span>
      ```

3. **이제 showNameInput에서 각각의 요소를 찾은 뒤 dislay를 swap해줘야한다.**

   - 각 요소를 id로 찾아서 `.style.display = ''`로 none 혹은 block을 대입해준다.
     - **각자 요소를 찾는 코드는 hideNameInput시 반복되므로 메서드로 만들어주자.**
   - **DOM을 다 찾고난뒤 focus를 해주기 위해, `this.$nextTick( () => );`콜백함수에 input에 focusing을 해야한다.**

   ```js
   getNodeElement(deptId) {
       return document.querySelector("#node-" + deptId);
   },
   
       getNameInput(deptId) {
           return document.querySelector("#name-" + deptId);
       },
   
           showNameInput(deptId) {
               let nodeElement = this.getNodeElement();
               nodeElement.style.display = 'none'
   
               let nameInput = this.getNameInput(deptId);
               nameInput.style.display = 'block'
   
               this.$nextTick(() => nameInput.focus());
           },
   ```

   ![image-20230129034101593](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230129034101593.png)

   



##### @dblclick시 input focus에 대해,input의  @blur로 focusing 사라지면 [수정취소]로서 꺼지게 만들기

![image-20230129034740691](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230129034740691.png)

![image-20230129034747881](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230129034747881.png)



1. **@dblclick으로 input창 띄우는 것은 branch에서 했지만, blur로 포커싱 제거시 복구는 `input태그 자체에 @blur:hideNameInput(dept.id)`를 달아준다.**

   ```html
   <input type="text"
          :id="'name-' + dept.id"
          :value="dept.text"
          :size="dept.text.length + 3"
          style="display: none;"
   
          @blur="hideNameInput(dept.id)"
          >
   ```

2. 보이게할 때는 focus가 추가 / **취소로 안보이게 할 때는 변경된 값 말고, 원본값을 넣어줘야한다. **

   ```js
   hideNameInput(deptId) {
       let nodeElement = this.getNodeElement(deptId);
       nodeElement.style.display = 'block';
   
       let nameInput = this.getNameInput(deptId);
       nameInput.style.display = 'none';
       // 수정 취소이므로 안보이게 되는 input에 원본 값으로 재할당해주기
       nameInput.value = nodeElement.innerText;
   },
   ```

3. **추가로 keyboard로 esc를 누를 때도 취소가 되게 한다.**

   ```html
   <input type="text"
          :id="'name-' + dept.id"
          :value="dept.text"
          :size="dept.text.length + 3"
          style="display: none;"
   
          @blur="hideNameInput(dept.id)"
          @keydown.esc="hideNameInput(dept.id)"
          >
   ```



4. **추가로, input창을 클릭할 때, `바깥 부모의 @click으로 select하는 로직이 작동안되게` 하려면, `자식요소에서 @click.stop`을 지정해주면 된다.**

   - input태그 및 접기/열기 span에도 @click.stop을 지정해준다.

   ```html
   <input type="text"
          :id="'name-' + dept.id"
          :value="dept.text"
          :size="dept.text.length + 3"
          style="display: none;"
   
          @blur="hideNameInput(dept.id)"
          @keydown.esc="hideNameInput(dept.id)"
          @click.stop
          >
   ```

   ```html
   <!-- 열기 접기 -->
   <div class="is-pulled-right pr-3"
        v-if="dept.children && dept.children.length"
        @click.stop="store.toggleOpen(dept)">
       <small class="has-text-grey">
           {$ dept.open ? '접기 ▶' : '열기 ▼' $}
       </small>
   </div>
   ```

   



##### input @keypress.enter로 수정을 진행할 예정인데, validate부터 진행해서 유효하지 않으면, 진행안되어야한다.

- **dept객체의 필드값을 수정하면, `tree와 연동(this.treeData)`는 되지만, `treeChanged는 호출안된다.`** 
- **tree연동 객체 dept를 변경해야하므로 `dept.id가 아닌 dept객체 자체를 인자`로 받는다.**
- input에 입력된 값을 검사해야하므로, $event -> event.target.value로 받을수도 있지만, **input태그를 display조절해야하므로, queryselect메서드로 대체해서 .value로 가져오면 된다.**
- **검증은**
  1. 글자수 체크 -> null도 검사된다.
  2. 같은 값으로의 변경
  3. **이미 존재하는지 bfs로 검사**
     - 이 때, 전체tree를 돌아야하는데 **`node -> node._vm.store`가 node에서 tree데이터를 가져올 수 있다.**
     - 하지만, **this.treeData의 전역tree연동데이터가 있기 때문에 이것으로 돌면 된다.**
       - **th.bfs 순회를 멈추려면 내부 익명함수에서 return false;를 하면 된다.**
       - **검증실패를 알리는 flag를 활용한다.**
- 검증이 끝난 tree데이터를 **this.depts 외부공급변수도 같이 변경해준다.**
  - tree로 업데이트하는 `this.treeUpdated( tree )`를 호출한다
    - 이 때, tree를 까보면, this.treeData가 아니라 tree컴포넌트며, `tree.getPureData()`로 `this.depts`를 업데이트 할 것이다.
  - `this.treeData`를 넣어줘도 되고, `node._vm.store`를 넣어줘도 된다.
    - **인자 없이 넣어줘도, 메서드 내부에서 `|| this.$refs.tree`로 tree데이터를 가져간다.**

```html
<input class="is-size-7"
       type="text"
       :id="'name-' + dept.id"
       :value="dept.text"
       :size="dept.text.length + 3"
       style="display: none;"

       @blur="hideNameInput(dept.id)"
       @keydown.esc="hideNameInput(dept.id)"
       @click.stop

       @keypress.enter="validateName(dept)"
       >
</span>
```

```js
// dept의 필드를 변경해야하기 때문에, 연동(객체 및 tree까지)되는 객체를 인자로받는다.
validateName(dept) {
    console.log('validateName----')

    // console.log('event.target.value >> ', event.target.value);
    let nodeElement = this.getNodeElement(dept.id);
    let nameInput = this.getNameInput(dept.id);
    let targetName = nameInput.value.trim();

    // 글자수 체크
    if (targetName.length > 10 || targetName.length < 2) {
        this.toast('이름은 2~10자로 입력해주세요.', 'is-danger');
        this.hideNameInput(dept.id);
        return;
    }
    // 같은 값으로 변경
    if (targetName === dept.text) {
        this.toast('같은 이름으로 변경할 수 없습니다.', 'is-danger');
        this.hideNameInput(dept.id);
        return;
    }


    // 이미 존재하는 명칭으로 변경 => bfs로 하나씩 돌면서 찾아본다.

    let isValid = true;
    th.breadthFirstSearch(this.treeData, node => {
        if (targetName === node.text) {
            // bfs handler(익명함수)에, return false하면 멈춘다.
            isValid = false;
            return false;
        }
    });
    if (!isValid) {
        this.toast('이미 존재하는 이름으로 변경할 수 없습니다.', 'is-danger');
        this.hideNameInput(dept.id);
        return;
    }
    dept.text = targetName;

    nodeElement.style.display = 'block';
    nameInput.style.display = 'none';
    this.treeUpdated(dept._vm.store)

    console.log('validateName====')
},
```



###### 갖가지 검증 로직들을 따로 메서드로 빼준다.



#### 다시 기존 프로젝트로 와서 부서 추가 버튼 추가



##### 부서추가 button => is-pulled-right를 쓰려면 부모는 is-block이어야한다

- 만약, `특정 부서를 선택했다면, 하위 부서 추가`로 나타낸다

```html
<div class="buttons is-block m-0">
    <b-button class="is-outlined is-rounded has-text-grey p-1"
              size="is-small"
              @click="collapseAll">
        <small>모두 접기</small>
    </b-button>
    <b-button class="is-outlined is-dark is-rounded p-1"
              size="is-small"
              @click="expandAll">
        <small>모두 열기</small>
    </b-button>

    <b-button class=" is-primary is-rounded is-pulled-right mr-2"
              size="is-small">
        {$ selectedDeptId ? '하위 부서 추가' : '부서 추가' $}
    </b-button>
</div>

<div class="is-clearfix"></div>
<div class="dropdown-divider"></div>
```



##### 부서 추가 로직 -> modal ->submit 통해 (선택된 targetParent , 내부정보)를 보냈다가 -> 예제데이터를 받아온다

1. 모달띄우기 위한 버튼에 `@click=" is해당ModalActive = true;"`를 넣고 전역변수 isModalActive를 만든다.

   - 원래는 개별item마다 선택된 id도 넘겨줘야하지만, 여기서는 전역변수 selectedDeptId를 전역으로 가지고 있다.

   ```html
   <b-button class=" is-primary is-rounded is-pulled-right mr-2"
             size="is-small"
             @click="isDepartmentModalActive = true;">
       <span class="icon">
           <i class="mdi mdi mdi-plus-thick mr-1"> </i>
       </span>
       {$ selectedDeptId ? '하위 부서 추가' : '부서 추가' $}
   </b-button>
   ```

   ```js
   isDepartmentModalActive: false, // 부서추가시 띄울 모달 flag
   ```

   

2. isModalActive가 true일 때 띄워질 body 끝에 modal html을 작성한다.

   - 닫기로직에선 flag를 false로 하고 만든다.

     ![image-20230129223029675](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230129223029675.png)

     ```html
     <!-- 부서추가 모달 -->
     <b-modal
             v-model="isDepartmentModalActive"
             has-modal-card
             trap-focus
             aria-role="dialog"
             aria-label="Department Add Modal"
             aria-modal
     >
         <form action=""
               method="post"
               @submit.prevent=""
         >
             <div class="modal-card is-" style="width: auto">
                 <header class="modal-card-head">
                     <p class="modal-card-title is-size-5">
                         부서 추가
                     </p>
                     <!-- 닫기버튼시 사용된 변수 다 초기화 -->
                     <button
                             type="button"
                             class="delete"
                             @click="isDepartmentModalActive = false; "/>
                 </header>
                 <section class="modal-card-body">
                     <!-- INPUT1: hidden을 부서추가시에는 미리 정해져있는 부모를 보낸다. -->
                     <input type="hidden" name="parentId" :value="selectedDeptId">
     
                     <!-- INPUT2: 부서 타입 고르기 -->
                     <div class="columns">
                         <div class="column is-mobile">
                             <b-field
                                     label="부서 타입"
                                     label-position="on-border"
                             >
                                 <b-select
                                         size="is-small"
                                         name="type"
                                         :placeholder="'부서 타입 선택'"
     
                                 >
                                     <optgroup label="1인 부서">
                                         <option value="0"><b>~부/~장</b>(ex> 병원장, 진료부, 간호부, 수련부)</option>
                                     </optgroup>
                                     <optgroup label="행정관련 부서">
                                         <option value="1"><b>~실</b>(ex> 탕제실, 홍보실, 적정진료관리실)</option>
                                         <option value="2"><b>~팀</b>(ex> 교육팀, 홍보팀, 총무팀, 기획홍보팀)</option>
                                         <option value="3"><b>~과</b>(ex> 원무과, 행정과)</option>
                                     </optgroup>
                                     <optgroup label="의료관련 부서">
                                         <option value="4"><b>~치료실</b>(ex> 병동, 외래, 집중간호실)</option>
                                         <option value="5"><b>~원장단</b>(ex> 한방원장단, 양방원장단)</option>
                                         <option value="6"><b>~과</b>(ex> 재활의학과, 피부미용과, 안면마비과)</option>
                                         <option value="7"><b>의료센터</b>(ex> 재활센터, 피부미용센터, 암센터)</option>
                                     </optgroup>
                                     <optgroup label="연구/관리 부서">
                                         <option value="8"><b>~연구소</b>(ex> 의학연구소, 교육연구소, 중앙연구소)</option>
                                         <option value="9"><b>~센터</b>(ex> 임상연구윤리센터, 임상시험센터)</option>
                                         <option value="10"><b>~위원회</b>(ex> 임상시험윤리위원회 등)</option>
                                     </optgroup>
                                 </b-select>
                             </b-field>
                         </div>
                     </div>
     
                     <!-- INPUT3: 부서명  -->
                     <div class="columns">
                         <div class="column is-mobile">
                             <b-field  label="부서명"
                                       label-position="on-border"
                             >
                                 <b-input type="text"
                                          name="name"
                                          size="is-small"
                                          minlength="2"
                                          maxlength="10"
                                          placeholder="이름을 2~10자로 입력해주세요."
                                 >
                                 </b-input>
                             </b-field>
                         </div>
                     </div>
     
                 </section>
                 <!-- 일반적인 태그 가운데 정렬은 is-justify-content-center 을 쓰면 된다.-->
                 <footer class="modal-card-foot is-justify-content-center">
                     <!-- b-button들을 넣으면 1개 이후 사라지는 버그 => a태그 + input(submit) 조합으로 변경-->
                     <a class="button is-primary is-light mr-2 is-size-7"
                        @click="isDepartmentModalActive = false"
                     >
                         닫기
                     </a>
                     <input type="submit"
                            class="button is-primary is-size-7"
                            value="생성"
                            :disabled="isLoading"
                     >
                 </footer>
             </div>
     
         </form>
     </b-modal>
     ```

     

3. **@submit시 `@submit.prevet="메서드"`를 통해  `action을 보류하면서, e를 받아 method`로 갔다가 => `method 내부에서 로직 처리후 e.target.submit()으로 form action그제서야 수행`**한다

   - submit은 `input type="submit"`으로 인해 form정보로 날아가게 하는데 **클릭시 isLoading 여부에 따라 :disabled 되게 한다**

     ```html
     <a class="button is-primary is-light mr-2 is-size-7"
        @click="isDepartmentModalActive = false"
        >
         닫기
     </a>
     <input type="submit"
            class="button is-primary is-size-7"
            value="생성"
            :disabled="isLoading"
            >
     ```

   - ##### form에서 @submit.prevet로 일단 form action을 막고 메서드를 태운다.

     ```html
     <form action=""
           method="post"
           @submit.prevent="submitForm"
     >
     ```

   - **`submitForm`메서드는 base.html에 있는 공통로직**으로서

     1. isLoading을 true로 만들어 -> 생성(제출)버튼의 재클릭을 방지하고
     2. prevent한 form action을 수행한다

     ```js
     submitForm(e) {
     
         // 1) 클릭되면 isLoading에 True가 들어가 button이 disable된다
         this.isLoading = true
     
         // 2) 다시 도로 제출
         e.target.submit();
     
         // 2) 1초후에 false가 되 button 돌아온다
         setTimeout(() => {
             this.isLoading = false
         }, 1000)
     },
     ```

4. **route를 만들고, form action을 정해준다.**

   - `request.form`으로 들어온 데이터를 전체 확인 먼저 해봐야한다.

     - 확인되면 parent_id로 넣어준다.

     ```python
     @dept_bp.route("/add", methods=['POST'])
     def add():
         print(request.form)
     
         # TODO: 예시데이터 -> 생성된 부서데이터 to_dict()로 내려보내고 + 예외처리하기
         id_ = random.randint(100, 199)
         sample = {
             'id': id_,
             'parentId': None,
             'level': 0,
             'sort': 1,
             'text': '병원장',
             'open': False,
         }
     
         return make_response(dict(data=sample message='부서가 추가되었습니다.'))
     
     ```

   - form의 action에 해당 route를 입력하고 날려본다.

     ```html
     <form action="{{url_for('department.add') }}"
           method="post"
           @submit.prevent="submitForm"
     >
     ```

     ![image-20230129230135561](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230129230135561.png)

     ```python
     ImmutableMultiDict([('parentId', ''), ('type', '1'), ('name', '부서추가test')])
     
     ```

     - **parent_id에 view `selectedDeptId`선택안될 때는 null대신 빈문자열로 날아오네**



#### [통신방식 변경] form html을 통해 post vs submit메서드+axios+this.data로 post

- 예시의 add 대신 save메서드

  - **예시에서는 `tree에 add를 먼저한 뒤, changed emit을 바깥`으로 내보내서 `save/cancel`이 가능한 상태로 만들어 `save`로 서버에 add한다.**

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

  - **나는 바로 서버에 add하고, 성공되면 tree에 반영되게 할 예정이다.**



1. **기존 base.html의 `submitForm`메서드는 `form action => route redirect(직전)`로 데이터를 받는 구조가 아니다.**
   - flash만 같이줘서 message만 띄우는 구조.
2. **그렇다면, `새로운 submitForm메서드`를 만들고 -> axios로 post를 보내서 데이터를 받을 때 view처리까지 해줘야한다.**



##### @submit메서드에서 form인풋값을 받기 위해, form Object 변수 생성 -> form의 input value들을 모두 form.name에 해당하는 필드로 v-model화 시키기

- [참고 블로그](https://goddino.tistory.com/92)

1. form태그의 action을 지운다.

   ```html
   <form method="post" @submit.prevent="submitForm" >
   ```

   

2. 보내는 **form의 input을 각각의 필드로 하는 object `form`변수** 생성

   ```js
   // form에 입력되는 input을 v-model로 받아줄 form object
   form : {
       parentId: null,
       type: '',// dropdown으로 선택되면 value가 숫자라도 문자열이 되어서 입력됨.
       name: '',
   },
   ```

3. form html에서 **`value=""의 기본값`은 두고  `v-model="form.필드명"`으로 변경**하고, name 삭제하기

   - `기존 전역변수의 값을 받는 변수는 :value`로 매핑한다? -> **v-model과 충돌**
     - selectedDeptId의 값을 문자열로만 넣으면 되니 `백틱 + ${}`의 python formatting으로 넣어도 안들어감
     - **v-model에 부모id를 할당문으로 넣어서 `v-model="form.연동필드 = 초기값변수"`을 활용해야한다.**

   ```html
   <!-- INPUT1: hidden을 부서추가시에는 미리 정해져있는 부모를 보낸다. -->
   !<--<input type="hidden" :value="selectedDeptId" v-model="form.parentId">-->
   
    <!-- INPUT1: hidden에 부모부서를 넣어줘야하는데, v-model과 연동시키려면 :value가 불가능 => v-model에 할당문으로 넣어준다.-->
   <input type="hidden" v-model="form.parentId = selectedDeptId">
   ```

   ![image-20230130011044415](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130011044415.png)

   ```html
   <b-select
             size="is-small"
             :placeholder="'부서 타입 선택'"
             v-model="form.type"
             >
   ```

   ```html
   <b-input type="text"
            size="is-small"
            minlength="2"
            maxlength="10"
            placeholder="이름을 2~10자로 입력해주세요."
            v-model="form.name"
            >
   ```

   

4. **v-model은 양방향 매핑으로서, 한번쓰고 그대로 채워져있으므로 `form변수를 초기화하는 initObject` 메서드를 따로 구현한다.**

   - object는 인자로 받아서, key의 value만 변화시켜도 변화가 유지된다. (return 덮어쓰기 안해도)

   ```js
   initObject(obj) {
       console.log('initObject----')
       for (const key in obj) {
           if (typeof obj[key] === "number") {
               obj[key] = null;
           } else if (typeof obj[key] === "string") {
   			obj[key] = null; // :placeholder때문에 ""는 삼항연자에서 true로 먹음
           } else if (typeof obj[key] === "boolean") {
               obj[key] = false;
           } else if (Array.isArray(obj[key])) {
               obj[key] = [];
           } else {
               obj[key] = {};
           }
       }
       console.log('initObject====')
   }
   ```

   

5. **이제 submitForm 대신 `submitDeptForm`을 새로 만들어서 axios로 post로 보내서, 데이터를 받도록 하자.**

   ```js
   <form method="post" @submit.prevent="submitDeptForm">
   ```

   1. 일단 axios 모듈을 import해야한다.

      ```html
      <!-- axios js-->
      <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
      ```

      

6. **`submitDeptForm` method의 send처리**는

   1. send 시작시 isLoading true로 버튼을 비활성화 해야한다. 
      - 성공/실패 상관없이 finally에서  다시 false로 변경
   2. axios로 통신해야한다
      - data에는 내 전역변수(object)를 넣어주면, json으로 변환되어 날아갈 수 있다.(stringify로 날아가지만, backend에서 `request.get_json()`으로 받을 수 있다.
   3. **then 성공은 통신 성공**이다.
      - **200번대에서는 로직 성공**
        - **`로직성공시에만 (1) modal창끄기 (2) this.form데이터 초기화`를 해준다.**
      - **그외에는 로직실패로서 내려오는 message를 띄워준다.**
      - **data는 `response.data`의 object 안에서 찾아야한다.**
      - **statuscode(로직 상태)는 `response.status`로 찾으면 된다.**
      - **`추후 tree 및 공급데이터, 초기데이터 다 업뎃해줘야한다.`**
      - **통신 성공시만 modal을 닫을 수 있게 flag를 false로 바꾼다.**
   4. **catch는 통신실패다.**
      - err 메세지를 띄워준다.
   5. **finally는 통신 성공/실패 여부와 상관없이 수행한다.**
      - **일단 loading을 제거해서 send버튼을 활성화시킨다.**

   ```js
   // modal용 submit메서드
   submitDeptForm(e) {
       //1. 로딩을 띄워서 send버튼 비활성화
       this.isLoading = true;
   
       // console.log(this.form) // 부서type option을 int로 넣어줬어도, b-select가 문자열로 보냄.
   
       //2.
       axios({
           url: '{{ url_for("department.add") }}',
           method: 'post',
           data: this.form,
           headers: {'Content-type': 'application/json;charset=utf-8'},
       }).then(res => {
           // 통신성공 but 로직 실패(200외)
           if (res.status >= 300) {
               this.toast(res.data.message)
               return;
           }
           // 통신 성공 + 로직 성공
           
           // TODO: 부서생성되었으니, tree도 업뎃?!
           // console.log(res.data.dept);
           
           this.toast(res.data.message)
           this.isDepartmentModalActive = false; // 성공시에만 모달창 닫기
           this.initObject(this.form); // 로직 성송시에만 form속 데이터 초기화
   
       }).catch(err => {
           this.toast(err + '서버와 연결할 수 없습니다.');
       }).finally(() => {
           this.isLoading = false; // 로딩 끄기
       });
   
   },
   ```

7. **통신 + 로직 성공시마다 (1)모달 닫기 (2) this.form 초기화해줬지만, `통신안하고 닫을때도 this.form을 초기화해줘야한다.`**

   - 닫기버튼, 2개에 `this.form`을 `this.initObject()`로 초기화해준다.

   ```html
   <button
           type="button"
           class="delete"
           @click="isDepartmentModalActive = false; initObject(form);"/>
   
   
   <a class="button is-primary is-light mr-2 is-size-7"
      @click="isDepartmentModalActive = false; initObject(form);"
      >
       닫기
   </a>
   ```

8. **route에서는 parentId에 대해서, 존재한다면 int()변환시켜줘야한다. None은 int()시 에러난다.**

   ```python
   @dept_bp.route("/add", methods=['POST'])
   def add():
       #### HTML FORM으로 보낼 때 ####
       # print(request.form) # html form이 아닌 submit메서드 + axios로 보냄
       # ImmutableMultiDict([('parentId', None), ('type', 1), ('name', '부서추가test')])
       #### axios POST로 보낼 때 ####
       # print(request.data)
       # b'{"parentId":2,"type":"1","name":"222"}'
       # print(request.get_json())
       # {'parentId': 2, 'type': '1', 'name': '222'}
       # {'parentId': None, 'type': '2', 'name': '222'}
       # => type은 b-select에서 string으로 보냄.
       # => parentId가 None으로 넘어오면  int()시 에러남.
       # => dict의 .get으로는 type지정못함. 직접변환
       dept_info = request.get_json()
       if dept_info['parentId']:
           dept_info['parentId'] = int(dept_info['parentId'])
   
   
       # TODO: 예시데이터 -> 생성된 부서데이터 to_dict()로 내려보내고 + 예외처리하기
       id_ = random.randint(100, 199)
       sample = {
           'id': id_,
           'parentId': dept_info['parentId'],
           'level': 0,
           'sort': 1,
           'text': dept_info['name'],
           'open': False,
       }
   
       return make_response(dict(dept=sample, message='부서가 추가되었습니다.'))
   ```

   - **parentId와 text가 반영되어 sample데이터가 내려온다.**
     ![image-20230130041401892](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130041401892.png)





#### 내려온 sample데이터를 tree에반영 => this.depts + this.initialDepts에도 반영하기

##### selectedDeptId 대신, selectedDept (node)자체를 전역변수에 보관해야, .parent를 가져올 수 있다. => selectNode(dept)를 id대신 객체를 받고, .id를 computed를 만들어야 :class 등에서 null검사(삼항연산자안됨)없이 있으면id 없으면null로 바로 사용할 수 있게 수정한다.

1. view에서 `selectNode(dept.id)` => `selectNode(dept)`로 변경

   ```html
   <div class="p-2"
        slot-scope="{data: dept, store, vm}"
        ref="node"
        @click="selectNode(dept)"
   ```

2. **객체 존재확인하여 .id를 없으면 null을 반환하는 `computed`를 만들어준다.**

   ```js
   selectedDept: null, // 선택된 부서
   ```

   

   - **view의 변수 조건문에서 삼항연산자가 안먹히기 때문에 computed로 만들어놔야한다.**

   - base.html에서 이미 selectedDeptId가 전역변수로 사용중이기 때문에 **임시로 `idOfSelectedDept`를 정의한다.**

     ```js
     computed: {
         idOfSelectedDept() {
             return this.selectedDept ? this.selectedDept.id : null
         }
     },
     ```

     

3. **`기존에 selectedDeptId`가 사용된 곳에 `computed인 idOfSelectedDept`로 변경해서 사용한다.**

```js
// node관련
selectNode(dept) {
    // 선택되지 않은 dept라면, 할당 -> 선택됬다면 null로 선택 풀기
    if (this.idOfSelectedDept !== dept.id) {
        this.selectedDept = dept;
        return;
    }
    this.selectedDept = null;
},
```



1. **selectedDeptId가 사용된 곳 모두를 selectedDept.id로 변경하기**

   ```html
   
   {$ selectedDept ? '하위 부서 추가' : '부서 추가' $}
   
   
   :class="{'active is-bordered has-text-primary has-text-weight-bold': dept.id === idOfSelectedDept}"
   
   
   <input type="hidden" v-model="form.parentId = idOfSelectedDept">
   
   
   ```

   









##### 부모 node객체를 받았어도 node.parent(단순node정보)에 push하는게 아니다. node._vm(Vue컴포넌트).data가 연동되는 부모다.

###### 만약 선택된 부모node가 없다면, 연동data  this.treeData를 root부모객체로 가진다.

- `부모vm객체.data.children`에 push
  - 부모가 없다면 `this.treedata`에 push 한다

```js
//2.
axios({
    url: '{{ url_for("department.add") }}',
    method: 'post',
    data: this.form,
    headers: {'Content-type': 'application/json;charset=utf-8'},
}).then(res => {
    // 통신성공 but 로직 실패(200대 외)
    if (res.status >= 300) {
        this.toast(res.data.message)
        return;
    }

    // 통신 성공 + (DB생성)로직 성공 -> tree에 생성된 자식 push -> 공급/초기데이터도 업뎃
    // TODO: 부서생성되었으니, tree도 업뎃?!
    const parentChildren = this.selectedDept
    ? this.selectedDept._vm.data.children
    : this.treeData;

    let newDept = res.data.dept;
    parentChildren.push(newDept);

    this.treeUpdated(); // tree 자체 ----getPureData----> this.depts
    this.initialDepts = this.depts; // this.depts -------> this.initialDepts


    this.toast(res.data.message)

    this.isDepartmentModalActive = false; // 로직 성공시에만 모달창 닫기
    this.initObject(this.form); // 로직 성송시에만 form속 데이터 초기화

}).catch(err => {
    console.log(err)
    // 특별히 err에 response가 내려온다면. 거기서 메세지를 꺼내서
    this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
}).finally(() => {

    this.isLoading = false; // 로딩 끄기
});
```

![image-20230130161439439](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130161439439.png)



#### 동일부모아래 유효한 순서변경을 route 통신입히기

1. **일단 동일부모검사에 안걸리면, `현재Sort` + `바뀐Sort`  + `대상id`를 axios post를 날려서 순서변경을 요청하고, 성공시 tree도 변경되게 해야한다.**

   - treeChanged에 넘어오는`node, tree`는 **`이미 바뀐 node`일 뿐**이다.
   - **기존 필드정보인 `node.id`, `node.sort`로 => `대상` + `이전sort`를 뽑아낸다.**
   - **`node.parent.children.index( node )`에 `+1`을 해서 =>  `바뀐sort`를 알아낸다.**
     - **`tree.dplh.parent.children`에는 바뀐 순서의 tree가 있지만, `tree.dplh는 node가 아니라서 기존정보 + node들과 순서비교로 sort알아내기 가 불가능하다.`**
       - **.indexOf()`에는실제 node정보인 `node`를 넣어줘서 sort를 알아낼 수 있다.**

   ```js
   treeChanged(node, tree) {
       console.log('treeChanged----') // 제자리에 둘 땐 호출되지 않는다.
   
       // 유효하지 않으면, 유효X내부 tree데이터를 <- 기존 공급된 depts데이터로 덮어써서 없앰
       // if (!this.validateFirstNotParent()) {
       if (!this.validateSameParent(node)) {
           this.toast('동일한 부모 부서아래 순서이동만 가능합니다.', 'is-danger')
           this.updateTreeData(); // 기존 this.depts -> this.treeData 덮어쓰기
           return;
       }
   
       // 유효한 경우, 유효O내부 tree데이터를 -> 외부공급 this.depts로 가져옮
       // (1) 유효한 순서변경 => 변경할 route에 가서 순서를 변경하고 온다.
       //     payload를 만들어서, 필요한 것만 담아보낸다.
       //    { 해당deptId,  이전sort, 바뀐sort }
       const payload = {
           deptId: node.id,
           beforeSort: node.sort,
           afterSort: node.parent.children.indexOf(node) + 1
       }
   
   ```





2. **axios.post로는 payload객체를 만들어서, deptId + beforeSort + afterSort를 보낸다.**

   - level간의 변환이 없으므로, afterLevel은 없어도 된다.
   - PUT으로 보낸다.

   ```js
   axios({
       url: '{{ url_for("department.change_sort") }}',
       method: 'put',
       data: payload,
       headers: {'Content-type': 'application/json;charset=utf-8'},
   }).then(res => {
       // 통신성공 but 로직 실패(200대 외) -> tree되돌려야함.
       // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
       if (res.status >= 300) {
           this.toast(res.data.message)
           return;
       }
   
       // 통신 성공 + (DB 순서변경)로직 성공 -> 그제서야 실제 tree도 변해야함.  =
       // TODO: 부서 순서 변경되었음 => 이미 tree가 바뀌었다면, 아무것도 안해도됨(차후 성공시 tree변경 -> this.depts + 초기데이터도 변경해줘야함.)
   
   
       // this.treeUpdated(); // tree 자체 ----getPureData------> this.depts
       // this.initialDepts = this.depts; // this.depts -------> this.initialDepts
   
       this.toast(res.data.message)
   
   }).catch(err => {
       // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
       console.log(err)
       this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
   
   }).finally(() => {
   });
   ```

   



3. **PUT 순서변경을 받아주는 route를 만들고, 넘어오는 payload를 찍어본 뒤, 응답해준다.**

   ```python
   @dept_bp.route("/sort", methods=['PUT'])
   def change_sort():
       payload = request.get_json()
       # print(payload)
       # {'deptId': 1, 'beforeSort': 1, 'afterSort': 2}
   
       # TODO: dept 순서변경 -> 다른부서들도 바뀌는지 확인해야함.
   
       return make_response(dict(message='부서 순서 변경에 성공했습니다.'))
   ```

   ![image-20230130182358910](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130182358910.png)

   ![image-20230130182554289](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130182554289.png)



##### ~~treeChanged에서 drag를 처리하면, 검증실패 + 통신실패 + 로직실패시 canceld해줘야한다. => ondragend 훅에서 처리하여, 실패시 return false;로 tree안바뀌게 막자.~~

1. 기존에 treeChanged 발생시, `this.treeUpdated(tree)`로 tree(vm) -> this.depts 업뎃만 남겨놓고, **순서변경하는 로직은 ondragend로 옮긴다.**

2. **`실패하는 곳(검증실패, 통신실패, 통신O로직실패)에서는 return false로 treeChanged가 안일어나게 막는다`.**

   - **`treeChanged(node, tree)`에서 node와 tree는 `이동후 node`**
   - **`ondragend(node, helper)`에서 node와 tree는 `이동전 node`**
     - **`기존node => dplh로 변경해서 처리`해야한다**
       - `this.validateSameParent(node)`에 들어가는 node부터 이동후 dplh로 변경해줘야한다.

3. ondragend(node, helper) **`이동 전node` 나 `helper` 가지곤 `placeholder의 위치나 바뀐 tree`에 접근할 수 없다.** 

   - **그래서 ref로 걸어둔 `this.$refs.tree`를 이용해 `.dplh`으로 `이동 후 위치나 tree`정보를 가져와야한다.**

   - dplh은 node로서의 `id 및 자체필드들`은 없지만, **`.parent(실제node)` 외 .children 등을 가진다.**

     - 근데 dplh의 parent도 root면 id는 안가지네?! root면 null / 아니면 id를 가진다.

     ![image-20230130203524145](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130203524145.png)

     ![image-20230130203831823](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230130203831823.png)

   - ~~해당로직도 없을 땐 ? null 있으면 뽑아쓰는 것이므로computed에 등록해보자.~~

     - 인자를따로 받지 않고, 현재 placeholder의 부모id를 얻는다.
     - **root일 때도 빈 parent key가 등록되어있으므로 .id까지 찍어서 확인한다.**
     - **따로 null을 반환해주지 않으면 undefined가 내려가 null null root로서 같은지 비교가 안되니 직접 null을 반환한다.**

     ```js
     let after_parentId = null; 
     if (this.$refs.tree.dplh.parent.id) {
         after_parentId = this.$refs.tree.dplh.parent.id;
     }
     ```

   - **computed로 넣고 했더니 `reutn false;로 treeData가 안바뀌니 -> computed가 값을 캐싱`하고 있어서 `after_parent_id`가 안변하는 버그가 발생한다.**





##### 확인결과. ondragend 훅에서 this.$refs.tree.dplh으로는, parent(node)정보는 얻을 수 있지만, 거기 children에서 placeholder(node정보는X)의 순서를 알아낼 방법이 없다 => 다시 treeChanged에서 순서변경을 처리하되, 3가지 실패시, cancel(기존.this.dept -> this.treeData 뒤엎기) by this.updateTree()



##### treeChanged에서 검증실패/통신실패/로직실패마다, 공급데이터(this.depts)로 덮어써서 this.treeData를 복구하도록 로직 추가

```js
treeChanged(node, tree) {
    console.log('treeChanged----') // 제자리에 둘 땐 호출되지 않는다.

    // 유효하지 않으면, 유효X내부 tree데이터를 <- 기존 공급된 depts데이터로 덮어써서 없앰
    // if (!this.validateFirstNotParent()) {
    // if (!this.validateSameParent(node)) { // => treeChanged는 sort안변하면 여기가 호출안되서 생략함.
    if (!this.validateSameParent(node)) {
        this.toast('동일한 부모 부서아래 순서이동만 가능합니다.', 'is-danger')
        // [cancel 1] 검증 실패 => tree변경 취소 (기존 this.depts -> this.treeData 덮어쓰기)
        this.updateTreeData();
        return;
    }

    // 유효한 경우 => DB에서변경 => 성공시 바뀐 tree데이터를 -> 외부공급 this.depts로 가져옮
    // (1) 유효한 순서변경 => 변경할 route에 가서 순서를 변경하고 온다.
    // console.log(this.treeData)

    const payload = {
        deptId: node.id,
        beforeSort: node.sort,
        afterSort: node.parent.children.indexOf(node) + 1
    }

    console.log('payload >> ', payload);

    axios({
        url: '{{ url_for("department.change_sort") }}',
        method: 'put',
        data: payload,
        headers: {'Content-type': 'application/json;charset=utf-8'},
    }).then(res => {
        // 통신성공 but 로직 실패(200대 외) -> tree되돌려야함.
        // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
        if (res.status >= 300) {
            this.toast(res.data.message)
            // [cancel 2] 통신성공 BUT 로직실패  => tree변경 취소(기존 this.depts -> this.treeData)
            this.updateTreeData();
            return;
        }

        // 통신 성공 + (DB 순서변경)로직 성공 -> 그제서야 실제 tree도 변해야함.  =
        // TODO: 부서 순서 변경되었음 => 이미 tree가 바뀌었다면, 아무것도 안해도됨(차후 성공시 tree변경 -> this.depts + 초기데이터도 변경해줘야함.)

        this.treeUpdated(tree); // tree 자체 ----getPureData------> this.depts
        this.initialDepts = this.depts; // this.depts -------> this.initialDepts

        this.toast(res.data.message)
        // this.toast('순서변경에 성공하였습니다.')

    }).catch(err => {
        // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
        console.log(err)
        this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');
        // [cancel 3] 통신실패  => tree변경 취소(기존 this.depts -> this.treeData)
        this.updateTreeData();

    }).finally(() => {
    });


    console.log('treeChanged====')
},
```



#### 순서변경 성공시, 위치바꾼Node의 .sort 필드 + 같이 변하는 모든 node들의 sort도 서버에서 내려준 정보로 바꿔야한다.

- level상관없이 node를 바꾼다면, bfs로 달라진 level, sort를 찾아야하지만
  - **같은 부모 아래에서 타겟node의 순서만 바뀌기 때문에, `타겟node의 부모의 children`에서 sort를 비교한다.**

```js
then(res => {
    // 통신성공 but 로직 실패(200대 외) -> tree되돌려야함.
    // TODO: 부서 순서 변경실패(통신은 됬는데 DB실패) => 이미 tree가 바뀌었다면, cancel해야함.
    if (res.status >= 300) {
        this.toast(res.data.message)
        // [cancel 2] 통신성공 BUT 로직실패  => tree변경 취소(기존 this.depts -> this.treeData)
        this.updateTreeData();
        return;
    }

    // 통신 성공 + (DB 순서변경)로직 성공 -> 그제서야 실제 tree도 변해야함.  =
    // TODO: 부서 순서 변경되었음 => 이미 tree가 바뀌었다면, (1) 관련된 모든 놈들의 .sort값 변경 (2) this.depts 변경 + this.initialDepts 변경)
    node.sort = payload.afterSort;
    // TODO: 관련 node들도 DB에서 받아서 다 sort바꿔주기 -> 어차피 같은 부모(level)에서만 달라지기 때문에, BFS말고 해당부모의 node만 바꿔주면 된다?!
    // th.breadthFirstSearch(this.treeData, node => {
    //     let myParentChildren = node.parent ? node.parent.children : this.treeData;
    //     let mySort = myParentChildren.indexOf(node) + 1;
    //     if (mySort !== node.sort) {
    //         console.log(`원래sort(${node.sort})와 현재sort${mySort}가 달라요.`)
    //         node.sort =  mySort;
    //     }
    // });
    let myParentChildren = node.parent ? node.parent.children : this.treeData;
    for (const [index, node] of myParentChildren.entries()) {
        const mySort = index + 1;
        if (mySort !== node.sort) {
            console.log(`원래sort(${node.sort})와 현재sort${mySort}가 달라요.`)
            node.sort = mySort;
        }
    }



    console.log('this.treeData, payload.afterSort >> ', this.treeData, payload.afterSort);

    this.treeUpdated(tree); // tree 자체 ----getPureData------> this.depts
    this.initialDepts = this.depts; // this.depts -------> this.initialDepts

    this.toast(res.data.message)
    // this.toast('순서변경에 성공하였습니다.')

})
```



#### 삭제 

##### 버튼

- 내부에 넣으려니 안이뻐지고, 나중에 하위부서수 직원수 등이 올거라 버튼으로 뺌
- **선택부서이을 때만 보이게**

```html
<!-- 부서 삭제-->
<b-button v-if="selectedDept"
          class="is-primary is-light is-rounded is-pulled-right mr-2"
          size="is-small"
          >
    <span class="icon">
        <i class="mdi mdi mdi-trash-can-outline mr-1"> </i>
    </span>
    삭제
</b-button>
```

![image-20230131010206134](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131010206134.png)

##### node삭제는 node._vm(node컴포넌트).store(tree컴포넌트)에서 .deleteNode( node )로 한다.

1. 추가는 modal을 띄워서했지만, 삭제는 바로 @click에서 **`deleteSelectedNode` 메서드를** 부른다.

   - **메서드의 인자는 필요없는 듯. this.selectedDept가 전역변수라서**

   ```js
   @click="deleteSelectedNode"
   
   
   // node 삭제
   deleteSelectedNode(e) {
       let tree = this.selectedDept._vm.store;
       tree.deleteNode(this.selectedDept);
       console.log('this.treeData >> ', this.treeData);
       console.log('this.selectedDept >> ', this.selectedDept);
   },
   ```

   

2. **확인해보니,`treeData에서는 해당node가 삭제`되고, `this.selectedDept`는 남아있다.**

​	![image-20230131011020574](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131011020574.png)





3. **삭제되었으면, `같은 부모아래`의 `나보다 뒤에 부서들은 모두 sort를 1칸씩 땅긴다`**

   - **이 때, `tree가 삭제 연동된 상태`이므로 `순회index + 1로 sort를 만들어선 안된다.`**
     - **사라진 node.sort vs 현재node의 .sort값으로 비교한다.**
   - **`tree의 node와 필드 연동`시킬려면 `for only key in`이 아닌 `for value of 부모object`로 돌아야한다.**

   ```js
   // node 삭제
   deleteSelectedNode(e) {
       //1. tree에서 선택node 삭제
       let tree = this.selectedDept._vm.store;
       tree.deleteNode(this.selectedDept);
   
       // console.log('this.treeData >> ', this.treeData); // 연동되어, 해당node만 삭제
       // console.log('this.selectedDept >> ', this.selectedDept);// 유지 + .parent에선 사라진 현재 tree연동됨.
   
       //2. 선택node보다 더 뒤에 sort를 1칸씩 당긴다.
       const standardSort = this.selectedDept.sort;
       let myParentChildren = this.selectedDept.parent ? this.selectedDept.parent.children : this.treeData;
   
       // for (const node in myParentChildren) {
       // [조심!] 일반 for in 으로 돌면 -> key값만 도는 것이다.
       for (const node of myParentChildren) {
           // 여기서는 index로 sort를 만들면 안된다. 이미 트리에서 1개가 빠진 상태에서 순회하기 때문
           if (node.sort > standardSort) {
               // console.log(`현재sort${node.sort}를 한칸씩 -1 합니다.`)
               node.sort = node.sort - 1;
           }
       }
       // 3. selected된거 없으니 비워주기
       this.selectedDept = null;
   
       //4. 변경된 tree를 -> this.depts -> this.initialDepts에 반영
       this.treeUpdated(tree);
       this.initialDepts = this.depts;
   
   },
   ```



##### 데이터가 없을 때(treeData) v-if 글자로 표시 ~~v-else tree컴포넌트~~ => tree컴포넌트가 없어지면,  this.$refs.tree로 tree 컴포넌트를 끌어오지 못하므로 쓰면 안된다.

```html
<div v-if="!treeData || !treeData.length "
     class="container"
     >
    <span class="is-size-6 has-text-primary has-text-weight-bold"> 부서가 없습니다. 최상위 부서를 생성해주세요.</span>
</div>


<tree
      draggable
      :class="'is-size-7'"
      ref="tree"
      :data="treeData"
      @change="treeChanged"
```



![image-20230131014350789](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131014350789.png)

​	![image-20230131015202472](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131015202472.png)





##### tree가 비었을 때 최초 생성시 오류 잡기 => v-else로 dom이 사라지면서 생김 => v-else를 제거하고 visibility hidden을 적용함.

![image-20230131015527407](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131015527407.png)

![image-20230131015549687](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131015549687.png)

![image-20230131020711944](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131020711944.png)	

```html
<tree
      draggable
      :class="'is-size-7'"
      :style="{visibility: treeData.length ? 'visible' : 'hidden'}"
```



##### 삭제시, 검증 + 검증통과시 +  confirm까지 받아서 처리되게 하기

- 검증
  1. 하위부서가 존재하면 confirm까지 가기 전에 return
  2. TODO 재직중인 직원이 있다면, 확인하고 진행
  3. 검증 다 통과시 confirm하여 yes시 진행



1. 삭제시 confirm의 결과로 진행되려면 **confirm 내부에서 `this.deleteSelectedode()`호출되어야하므로, `삭제버튼에서는 vadliateDelete()`를 호출하여 `검증 + confirm`을 거치도록 한다.**

   ```html
   <!-- 부서 삭제-->
   <b-button v-if="selectedDept"
             class="is-primary is-light is-rounded is-pulled-right mr-2"
             size="is-small"
             @click="validateDelete"
             >
       <span class="icon">
           <i class="mdi mdi mdi-trash-can-outline mr-1"> </i>
       </span>
       삭제
   </b-button>
   ```

   ```js
   // node 삭제
   validateDelete() {
       // 삭제 진행 전 검증하기
       const targetDept = this.selectedDept;
       // [검증1] 하위 부서 존재여부
       // 일단 자식없는 node라도 .children는 빈 어레이로 가지고 있음.
       if (targetDept.children.length) {
           this.toast('하위 부서가 존재할 경우 삭제할 수 없습니다.', 'is-danger')
           return;
       }
   
       // TODO: [검증2] (하위부서X)부서의 직원이 존재할 경우, [있다면 해임시키게 될 건데] confirm받기
       // this.confirm('삭제할 경우, 해당 부서원들은 금일부 해임됩니다. 진행하시겠습니까?', async () => await this.deleteSelectedNode() );
   
       // [검증3] 정말 삭제할 것인지 confirm 받기
       this.confirm('정말 삭제하시겠습니까?', () => this.deleteSelectedNode() );
   },
   ```

2. **buefy의 confirm은 `onConfirm`속성에 실행될 함수를 입력해줘야해서 `base.html`에 아래와 같이 정의했다.**

   ```js
   confirm(message, _function=(()=>{}), type = 'is-primary', confirmText = '예', cancelText = '아니오') {
       this.$buefy.dialog.confirm({
           type: type,
           size: 'is-small',
           message: message,
           confirmText: confirmText,
           cancelText: cancelText,
           onConfirm: _function,
       });
   },
   ```

   ![image-20230131160132315](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131160132315.png)

   ![image-20230131160146939](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131160146939.png)







#### status 개발

1. 초기데이터에서 open을 다 status로 변경

   ```js
   this.depts = [
       {id: 1, parentId: null, level: 0, sort: 1, text: '병원장', status: true},
       {id: 2, parentId: null, level: 0, sort: 2, text: '이사회', status: true},
       {
           id: 3,
           parentId: null,
           level: 0,
           sort: 3,
           text: 'node 3 undraggable',
           draggable: false,
           status: true
       },
       {
           id: 4,
           parentId: null,
           level: 0,
           sort: 4,
           text: 'node 4 undroppable',
           droppable: false,
           status: true
       },
       {
           id: 5,
           level: 0,
           sort: 5,
           text: 'node 5',
           children: [
               {
                   id: 6,
                   parentId: 5,
                   level: 1,
                   sort: 1,
                   text: 'node 6',
                   status: false
               },
               {
                   id: 7,
                   parentId: 5,
                   level: 1,
                   sort: 2,
                   text: 'node 7',
                   status: false
   
               },
           ], status: true
       },
   ];
   
   ```

   





##### b-swtich 도입

- 개별node의 열기/접기 같은 선상르ㅗ `is-pulled-right`로 b-swtich를 도입한다

- **v-model을 `dept.status`의 개별dept `.status`로 지정한다.**

  - **buefy이므로 부모의 이벤트 안먹게 `@click.native.stop`으로 메서드를 작성한다.**
  - **더블클릭은 아예 방지 + stop까지 같이 한다. `@dblcick.native.prevent.stop`**

  ```html
  <!-- 활성/비활성 -->
  <div class="is-pulled-right pr-2"
       >
      <b-switch
                size="is-small"
                type="is-success"
                v-model="dept.status"
                @click.native.stop="(event) => {event.stopPropagation();toast('asdf');}"
                @dblclick.native.prevent.stop
                >
      </b-switch>
  </div>
  ```

  ![image-20230131210313990](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131210313990.png)



##### confirm(삭제와 마찬가지로 직원들 해임 + 확인용) 이후에 비활성화 예정이므로 @click.native.stop에 valiate메서드를 먼저 호출해야하지만, b-switch가 prevent안하면 먼저 넘어가서 @click.native.prevent.stop으로 처리한다

```js
validateStatusChange(dept) {
    // TODO: [검증1] (하위부서X)부서의 직원이 존재할 경우, [있다면 해임시키게 될 건데] confirm받기
    // this.confirm('비활성화할 경우, 해당 부서원들은 금일부 해임됩니다. 진행하시겠습니까?', async () => await this.deleteSelectedNode() );

    // 비활성 -> 활성 경우, 그냥 토글한다.
    if (!dept.status) {
        dept.status = !dept.status
        return;
    }
    // [검증2] 활성상태일때만, 정말 비할성화 것인지 confirm 받기
    this.confirm('정말 비활성화하시겠습니까??', () => dept.status = !dept.status);
},
```

![image-20230131213437972](https://raw.githubusercontent.com/is2js/screenshots/main/image-20230131213437972.png)





##### depts.status를 axios로 요청후 성공하면 바꾸도록 changeStatus 메서드 만들어서 validate메서드에서 호출하기 => 내부에서는 axios 성공시 dept.status 토글후 공급데이터 update

```js
                validateStatusChange(dept) {
                    // TODO: [검증1] (하위부서X)부서의 직원이 존재할 경우, [있다면 해임시키게 될 건데] confirm받기
                    // this.confirm('비활성화할 경우, 해당 부서원들은 금일부 해임됩니다. 진행하시겠습니까?', async () => await this.deleteSelectedNode() );

                    // 비활성 -> 활성 경우, 그냥 토글한다.
                    if (!dept.status) {
                        this.changeStatus(dept);
                        return;
                    }
                    // [검증2] 활성상태일때만, 정말 비할성화 것인지 confirm 받기
                    this.confirm('정말 비활성화하시겠습니까??', () => this.changeStatus(dept));
                },
```



```js
changeStatus(dept) {
    const payload = {
        deptId: dept.id
    }
    axios({
        url: '{{ url_for("department.change_status") }}',
        method: 'put',
        data: payload,
        headers: {'Content-type': 'application/json;charset=utf-8'},
    }).then(res => {
        // 통신성공 but 로직 실패(200대 외)
        if (res.status >= 300) {
            this.toast(res.data.message)
            return;
        }

        // 통신 성공 + (status변경)로직 성공 -> tree에 생성된 자식 push -> 공급/초기데이터도 업뎃
        dept.status = !dept.status

        this.treeUpdated(); // tree(vm) 자체 ----getPureData------> this.depts
        this.initialDepts = this.depts; // this.depts -------> this.initialDepts

        this.toast(res.data.message)

    }).catch(err => {
        console.log(err)
        // 특별히 err에 response가 내려온다면. 거기서 메세지를 꺼내서
        this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');

    }).finally(() => {

    });
},
```



##### route

```python
@dept_bp.route("/status", methods=['PUT'])
def change_status():
    payload = request.get_json()
    # print(payload)
    # {'deptId': 1}
    # TODO : dept status 변경


    return make_response(dict(message='부서 활성여부 변경을 성공했습니다.'))

```





#### 이름변경도 enter시 validateName(dept)이후 axios 통신 달기

##### html

- 현재 html

  ```html
  <!-- 더블클릭시 나타나는 이름변경 input -->
  <input class="is-size-7"
         type="text"
         :id="'name-' + dept.id"
         :value="dept.text"
         :size="dept.text.length + 3"
         style="display: none;"
  
         @blur="hideNameInput(dept.id)"
         @keydown.esc="hideNameInput(dept.id)"
         @click.stop
  
         @keypress.enter="validateName(dept)"
         >
  ```

- 현재js

  ```js
  validateName(dept) {
      console.log('validateName----')
  
      // console.log('event.target.value >> ', event.target.value);
      let nodeElement = this.getNodeElement(dept.id);
      let nameInput = this.getNameInput(dept.id);
      let targetName = nameInput.value.trim();
  
      // 글자수 체크
      if (this.checkInvalidNameLength(targetName)) {
          this.toast('이름은 2~10자로 입력해주세요.', 'is-danger');
          this.hideNameInput(dept.id);
          return;
      }
      // 같은 값으로 변경
      if (!this.checkNotSameName(targetName, dept)) {
          this.toast('같은 이름으로 변경할 수 없습니다.', 'is-danger');
          this.hideNameInput(dept.id);
          return;
      }
  
      // 이미 존재하는 명칭으로 변경 => bfs로 하나씩 돌면서 찾아본다.
      if (this.existNameInTree(targetName)) {
          this.toast('이미 존재하는 이름으로 변경할 수 없습니다.', 'is-danger');
          this.hideNameInput(dept.id);
          return;
      }
      dept.text = targetName;
  
      nodeElement.style.display = 'block';
      nameInput.style.display = 'none';
      this.treeUpdated(dept._vm.store)
  
      console.log('validateName====')
  },
  ```

  

##### validate통과후 (dept)외에 얻어낸 (검증통과 targetName)을 받는 changeName메서드를 내부호출되게 파서, axios로 변경요청후, 성공시 hideInput도 해준다

```js
// dept의 필드를 변경해야하기 때문에, 연동(객체 및 tree까지)되는 객체를 인자로받는다.
validateName(dept) {
    console.log('validateName----')

    // console.log('event.target.value >> ', event.target.value);
    let nameInput = this.getNameInput(dept.id);
    let targetName = nameInput.value.trim();

    // 글자수 체크
    if (this.checkInvalidNameLength(targetName)) {
        this.toast('이름은 2~10자로 입력해주세요.', 'is-danger');
        this.hideNameInput(dept.id);
        return;
    }

    // 같은 값으로 변경
    if (!this.checkNotSameName(targetName, dept)) {
        this.toast('같은 이름으로 변경할 수 없습니다.', 'is-danger');
        this.hideNameInput(dept.id);
        return;
    }

    // 이미 존재하는 명칭으로 변경 => bfs로 하나씩 돌면서 찾아본다.
    if (this.existNameInTree(targetName)) {
        this.toast('이미 존재하는 이름으로 변경할 수 없습니다.', 'is-danger');
        this.hideNameInput(dept.id);
        return;
    }

    this.changeName(dept, targetName);


    console.log('validateName====')
},

    changeName(dept, targetName) {
        console.log('changeName----')

        const payload = {
            deptId: dept.id,
            targetName: targetName
        }
        axios({
            url: '{{ url_for("department.change_name") }}',
            method: 'put',
            data: payload,
            headers: {'Content-type': 'application/json;charset=utf-8'},
        }).then(res => {
            // 통신성공 but 로직 실패(200대 외)
            if (res.status >= 300) {
                this.toast(res.data.message)
                return;
            }

            // 통신 성공 + (name변경)로직 성공
            dept.text = targetName;
            // 성공시 해당 input을 안보이게 + view는 보이게 다시 변경
            this.hideNameInput(dept.id);

            this.treeUpdated(dept._vm.store); // tree(vm) 자체 ----getPureData------> this.depts
            this.initialDepts = this.depts; // this.depts -------> this.initialDepts

            this.toast(res.data.message)

        }).catch(err => {
            console.log(err)
            // 특별히 err에 response가 내려온다면. 거기서 메세지를 꺼내서
            this.toast(err.response ? err.response.data.message : '서버와 연결이 올바르지 않습니다.');

        }).finally(() => {

        });


        console.log('changeName====')
    },

```



