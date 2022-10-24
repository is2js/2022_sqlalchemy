### Regex
- 정규식 패턴 검사 문서: https://docs.python.org/3/howto/regex.html
- 정규식 의미 문서: https://docs.python.org/3/library/re.html

### 학습 정리
#### 01 String and Regex
1. mask_email
   - @를 기준으로 name과 domail으로 split하고, name의 [0], [-1] 사이에 hash#을 채운 문자열을 반환한다
2. is_valid_email
   - re.search(p, txt)를 활용하면 해당 패턴에 부합하는지를 확인할 수 있다.(re.Match객체 or None)
   - `^문자열`과 `문자열$`은 전체 txt의 시작과 끝을 확인한다.
   - `\w`는 숫자+영어+유니코드 1글자를 의미한다. `+`는 1글자 이상을 의미한다.
     - `^\w+`는 `1글자 이상의 문자`로 `시작`을 의미한다
   - `()` 소괄호는 group관련이므로 `무시하고 해석`한다
   - `\.`은 `.`자체가 모든 1글자이므로, escape를 단 실제 `.`을 의미한다.
   - `[]` 대괄호는 문자열1개에 대해 `OR개념`을 넣어주는 것이다.
     - `[amk]` -> a or m or k / `[\.-]`? -> 실제. or - 가 0개or1개 => 있을수도 없을 수도
   - `?`는 0개 or 1개이다. **앞에 달릴 수도 안달릴 수도 있다면, `[\.-]?\w+`처럼 1개이상의 글자 앞에 []?를 달아주자.** 
   - `(\.\w{2,3})+$` => .문자2~3개가 1개이상 반복되며 끝나야한다. => .ab or .abc.com 로 끝내기가 가능하다
     - 끝낼때의 규칙을 .abc, .ab.cd 형식으로 만들 땐 $를 붙여서 끝내자.
   - re.search대신 readable한 정규식을 작성하고 싶다면, `re.compile() -> .match()`로 패턴여부를 확인한다.
     1. `re.compile(r"", re.VERBOSE | re.IGNORECASE)`를 통해, compile객체를 만들고
     2. `compile객체.match(txt)`로 re.Match객체를 반환받아서 사용하면 된다.

#### 학습 출저
1. [유튜브 1: AppliedAiCourse](https://www.youtube.com/watch?v=z0QUnFfaJXo)
2. [유튜브 2: PyMoondra](https://www.youtube.com/watch?v=yqwYTSNJFLg)
