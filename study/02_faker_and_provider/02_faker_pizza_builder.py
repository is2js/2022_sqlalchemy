from collections import namedtuple
from enum import Enum, auto

from faker import Faker
from faker.providers import BaseProvider

PizzaBase = namedtuple('PizzaBase', ['DoughDepth', 'DoughType'])


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


class Pizza:
    def __init__(self, name):
        self.name = name
        self.dough = None
        self.sauce = None
        self.topping = []
        self.cooking_time = None  # in minutes

    def __repr__(self):
        return f"{self.__class__.__name__} name: {self.name!r}\n" \
               + f"dough type: {self.dough.DoughDepth.name!r} & {self.dough.DoughType.name!r} \n" \
               + f"sauce type: {self.sauce.name!r}] \n" \
               + f"topping: {[it.name for it in self.topping]!r}] \n" \
               + f"cooking time: {self.cooking_time!r}\n"


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



if __name__ == '__main__':
    my_faker = Faker()
    my_faker.add_provider(PizzaProvider)

    for i in range(6):
        print('*'*10 + f'{i}' + '*'*10)
        print(my_faker.create_fake_pizza())

