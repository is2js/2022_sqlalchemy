from dataclasses import dataclass

from faker import Faker


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


