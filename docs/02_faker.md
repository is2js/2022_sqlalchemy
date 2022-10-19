## faker

### 01 faker 기본 제공 기능 모음

1. Faker(`ko_KR`)을 넘겨주면, name/address/profile-residence, company 정도가 한글로 나온다

```python
my_faker = Faker('ko_KR')
Faker.seed(40)

print(my_faker.name())
print(my_faker.user_name())
print(my_faker.address())
print(my_faker.profile())
print(my_faker.simple_profile())
print(my_faker.simple_profile(sex='F'))
# 양경수
# 인천광역시 광진구 강남대708길 (순옥강리)
# {'job': '사회과학 연구원', 'company': '(유) 김', 'ssn': '280821-1605532', 'residence': '대구광역시 구로구 양재천29길 (진우김최마을)', 'current_location': (Decimal('67.1211015'), Decimal('-175.195113')), 'blood_group': 'A-', 'website': ['https://www.jusighoesa.com/', 'https://ibagcoe.org/', 'http://www.jusighoesa.kr/', 'http://ju.kr/'], 'username': 'seonghoi', 'name': '박지우', 'sex': 'F', 'address': '부산광역시 동대문구 역삼0길 (민석박읍)', 'mail': 'ejang@naver.com', 'birthdate': datetime.date(1948, 12, 9)}
# {'username': 'seojuni', 'name': '박상호', 'sex': 'M', 'address': '경기도 고성군 도산대길 (정희김안면)', 'mail': 'gimjeongsig@daum.net', 'birthdate': datetime.date(1962, 3, 25)}
# {'username': 'yeongmi32', 'name': '양경희', 'sex': 'F', 'address': '광주광역시 북구 압구정203가 (성훈조동)', 'mail': 'hyeonsug28@daum.net', 'birthdate': datetime.date(1962, 3, 25)}

param = ["username", "name", "sex", "blood_group", "website"]
print(my_faker.profile(fields=param, sex='F'))
# {'blood_group': 'AB-', 'website': ['http://www.gimi.org/', 'https://jusighoesa.kr/', 'http://www.ju.kr/'], 'username': 'ogim', 'name': '김서현', 'sex': 'F'}
```

```python
print(my_faker.word())#  no ko
print(my_faker.words()) # no ko
print(my_faker.sentence()) # no ko
print(my_faker.sentences()) # no ko
print(my_faker.paragraph()) # no ko
print(my_faker.text()) # no ko
# officia
# ['neque', 'minima', 'doloribus']
# Consectetur expedita sunt ipsam adipisci.
# ['Animi dicta provident sed.', 'Debitis non beatae.', 'Corporis maiores rerum sunt atque soluta.']
# Dolorem corrupti cum est repudiandae iure. Tempora distinctio inventore aperiam. Dignissimos recusandae ab iusto esse deleniti dolores iste.
# Numquam iste sed totam voluptates doloribus. Rem non deleniti. Autem quasi deleniti accusantium laboriosam tenetur temporibus.

my_words = ['조재성', '조재경', '조아라']
for _ in range(3):
    print(my_faker.sentence(ext_word_list=my_words))
# 조재경 조재경 조재성 조재경 조재경 조재성 조아라.
# 조아라 조재경 조재성 조아라 조재성.
# 조재경 조재경 조아라 조재성 조재경.
```

```python
from faker.providers import internet
my_faker.add_provider(internet)
print(my_faker.ipv4_private())
print(my_faker.ipv4())
# 172.17.4.226
# 115.77.36.194
```

```python
# print(my_faker.bothify(text='ID asdfasdf: ???-###'))
print(my_faker.bothify(text='ID asdfasdf: ???-###', letters='AB'))
print(my_faker.bothify(text='010-####-####'))
# ID asdfasdf: AAB-798
# 010-3254-7082

print(my_faker.license_plate()) # 7 글자의 특문영어숫자조합 라이센스
# ZUY6022
```


### 02 제한된 종류 안에서(enum등)의 랜덤값으로 객체 제작  by Provider

#### 제한된 종류의 필드들은 enum으로 만들어놓고 모델 준비하기

1. faker_xxx_builder.py 생성
2. Enum, auto로 제한된 종류별 카테고리 클래스를 `1부터 배정`되도록 만든다.
   - value로 찍어보면 1부터 순서대로 배정된다.
   - 저장만 .value로 하고, 출력은 .name으로 변수명이 나오게 할 예정이다.
   ```python
   from enum import Enum, auto


   class PizzaDoughDepth(Enum):
      THIN = auto()
      THICK = auto()


   class PizzaDoughType(Enum):
      WHEAT = auto()
      CORN = auto()
      RYE = auto()


   class PizzaSauceType(Enum):
      PESTO = auto()
      WHITE_GARLIC = auto()
      BARBEQUE = auto()
      TOMATO = auto()


   class PizzaTopLevelType(Enum):
      MOZZARELLA = auto()
      SALAMI = auto()
      BACON = auto()
      MUSHROOMS = auto()
      SHRIMPS = auto()

   ```
3. 해당enum필드를 포함한 Pizza 클래스를 만든다.
   - faker로 enum중 1개가 채워질 필드들은 모두, None 혹은 [] 로 초기화하고, name만 입력받도록 하자.
   - repr에는 각 필드에 채워질 enum의 .name을 활용해서 찍는다.
      ```python
      class Pizza:
         def __init__(self, name):
            self.name = name
            self.dough = None
            self.sauce = None
            self.topping = []
            self.cooking_time = None # in minutes

         def __repr__(self):
            return f"{self.__class__.__name__} name: {self.name!r}\n" \
                     + f"dough type: {self.dough.DoughDepth.name!r} & {self.dough.DoughType.name!r} \n" \
                     + f"sauce type: {self.sauce.name!r}] \n" \
                     + f"topping: {[it.name for it in self.topping]!r}] \n" \
                     + f"cooking time: {self.cooking_time!r}\n"
      ```

4. self.dough 필드에은, 2가지 enum을 한꺼번에 입력하기 위해, namedTuple을 활용해서 PizzaBase라 이름짓는다.
   ```python
   PizzaBase = namedtuple('PizzaBase', ['DoughDepth', 'DoughType'])
   ```

#### faker.providers의 BaseProvider를 상속한 Provider클래스 및 create_faker_xxx메서드 구현하기

1. BaseProvider를 상속한 `XXXProvider 클래스` 정의
2. 내부에서 enum속  모든필드값을 모은 list -> 종류별 [`enum필드 list`]들을 `class변수`로 선언하기
   ```python
   class PizzaProvider(BaseProvider):
    # 각 필드별 제한된종류의 카테고리들을 상수list로 모은다.
    NAMES = ['조재성피자', '김석영피자', '조재경피자']

    DOUGH_DETPH = [PizzaDoughDepth.THIN, PizzaDoughDepth.THICK]
    DOUGH_TYPE = [PizzaDoughType.RYE, PizzaDoughType.WHEAT, PizzaDoughType.CORN]

    SAUCE = [PizzaSauceType.TOMATO, PizzaSauceType.BARBEQUE, PizzaSauceType.PESTO, PizzaSauceType.WHITE_GARLIC]
    
    TOPPING = [
        PizzaTopLevelType.MOZZARELLA,
        PizzaTopLevelType.BACON,
        PizzaTopLevelType.SALAMI,
        PizzaTopLevelType.MUSHROOMS,
        PizzaTopLevelType.SHRIMPS,
        ]
   ```

3. BaseProvider 내부에 정의하는 method `def create_fake_xxx(self)`내부에서, `self.random_element()`와 `self.random_int(a,b)` 등을 활용해서 `self.클래스변수` enum list 중 n개를 뽑아서 필드에 박아 Pizza객체를 만들어 반환한다.
   - 여기서 self는 faker객체가 된다.
   - Pizza객체의 필드를 setter개념으로 채워넣고 반환한다
      ```python
      def create_fake_pizza(self):
         pizza = Pizza(self.random_element(self.NAMES))
         
         pizza.dough = PizzaBase(
            self.random_element(self.DOUGH_DETPH),
            self.random_element(self.DOUGH_TYPE),
         )
         pizza.sauce = self.random_element(self.SAUCE)
         
         rand_amount_topping = self.random_int(2, len(self.TOPPING))
         for _ in range(rand_amount_topping):
            pizza.topping.append(self.random_element(self.TOPPING))
            
         pizza.cooking_time = self.random_int(10, 20)
         return pizza
      ```

4. faker객체에 .add_provider( )에 BaseProvider를 상속해서 만든 PizzaProvider를 인자로 주고 `faker객체.create_fake_pizza()`를 호출한다
```python
if __name__ == '__main__':
    my_faker = Faker()
    my_faker.add_provider(PizzaProvider)

    for i in range(6):
        print('*'*10 + f'{i}' + '*'*10)
        print(my_faker.create_fake_pizza())

# **********5**********
# Pizza name: '조재성피자'
# dough type: 'THICK' & 'WHEAT' 
# sauce type: 'BARBEQUE'] 
# topping: ['BACON', 'BACON', 'BACON']] 
# cooking time: 10
```


### 03 종류 제한이 없을 땐, provider없이 개별method로 랜덤객체 생성 구현하기
####  @dataclass로 편하게 객체 준비(생성자가 필요 없음)
```python
from dataclasses import dataclass


@dataclass
class Student:
    name: str
    age: int
    course: int
    group_name: str
    address: str
    vk_url: str

    def __repr__(self):
        info: str = f"Name: {self.name} \n" \
                    f"Age: {self.age}\n" \
                    f"course: {self.course}\n" \
                    f"group_name: {self.group_name}\n" \
                    f"address: {self.address}\n" \
                    f"vk_url: {self.vk_url}\n"
        return info

```

#### 객체생성을 위한 단독메서드 구현. faker객체를 인자로 받는다.
- string이 양식이 있을 땐, faker.bothify(text= ,letters=)를 쓰면 된다.
- 특정필드가 이전필드의 값에 영향을 받을 땐, 이전필드를 변수로 미리 만들어놓고 객체 생성에는 그 변수를 활용한다.

```python
def create_faker_student(faker: Faker) -> Student:
    course = faker.random.randint(1, 4)
    return Student(
        name=faker.name(),
        age=faker.random.randint(16, 25),
        # course=faker.random.randint(1, 4),
        course=course,
        group_name=faker.bothify(text=f'{course}-???-##', letters='MDATI'),
        address=faker.address(),
        vk_url='https://vk.com/' + faker.user_name()
    )


if __name__ == '__main__':
    my_faker = Faker('ko_KR')
    for i in range(6):
        print('*'*10 + f'{i}' + '*'*10)
        print(create_faker_student(my_faker))

# **********0**********
# Name: 송도현 
# Age: 23
# course: 4
# group_name: 4-DAI-75
# address: 충청남도 수원시 장안구 양재천거리 (지혜이김읍)
# vk_url: https://vk.com/gimyeongja
```