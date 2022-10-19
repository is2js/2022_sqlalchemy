from faker import Faker
from faker.providers import internet

if __name__ == '__main__':
    my_faker = Faker('ko_KR')
    Faker.seed(40)

    # print(my_faker.name())
    # print(my_faker.address())
    # print(my_faker.profile())
    # print(my_faker.simple_profile())
    # print(my_faker.simple_profile(sex='F'))
    # 양경수
    # 인천광역시 광진구 강남대708길 (순옥강리)
    # {'job': '사회과학 연구원', 'company': '(유) 김', 'ssn': '280821-1605532', 'residence': '대구광역시 구로구 양재천29길 (진우김최마을)', 'current_location': (Decimal('67.1211015'), Decimal('-175.195113')), 'blood_group': 'A-', 'website': ['https://www.jusighoesa.com/', 'https://ibagcoe.org/', 'http://www.jusighoesa.kr/', 'http://ju.kr/'], 'username': 'seonghoi', 'name': '박지우', 'sex': 'F', 'address': '부산광역시 동대문구 역삼0길 (민석박읍)', 'mail': 'ejang@naver.com', 'birthdate': datetime.date(1948, 12, 9)}
    # {'username': 'seojuni', 'name': '박상호', 'sex': 'M', 'address': '경기도 고성군 도산대길 (정희김안면)', 'mail': 'gimjeongsig@daum.net', 'birthdate': datetime.date(1962, 3, 25)}
    # {'username': 'yeongmi32', 'name': '양경희', 'sex': 'F', 'address': '광주광역시 북구 압구정203가 (성훈조동)', 'mail': 'hyeonsug28@daum.net', 'birthdate': datetime.date(1962, 3, 25)}

    param = ["username", "name", "sex", "blood_group", "website"]
    print(my_faker.profile(fields=param, sex='F'))
    # {'blood_group': 'AB-', 'website': ['http://www.gimi.org/', 'https://jusighoesa.kr/', 'http://www.ju.kr/'], 'username': 'ogim', 'name': '김서현', 'sex': 'F'}


    # print(my_faker.word())#  no ko
    # print(my_faker.words()) # no ko
    # print(my_faker.sentence()) # no ko
    # print(my_faker.sentences()) # no ko
    # print(my_faker.paragraph()) # no ko
    # print(my_faker.text()) # no ko
    # officia
    # ['neque', 'minima', 'doloribus']
    # Consectetur expedita sunt ipsam adipisci.
    # ['Animi dicta provident sed.', 'Debitis non beatae.', 'Corporis maiores rerum sunt atque soluta.']
    # Dolorem corrupti cum est repudiandae iure. Tempora distinctio inventore aperiam. Dignissimos recusandae ab iusto esse deleniti dolores iste.
    # Numquam iste sed totam voluptates doloribus. Rem non deleniti. Autem quasi deleniti accusantium laboriosam tenetur temporibus.

    # my_words = ['조재성', '조재경', '조아라']
    # for _ in range(3):
    #     print(my_faker.sentence(ext_word_list=my_words))
    # 조재경 조재경 조재성 조재경 조재경 조재성 조아라.
    # 조아라 조재경 조재성 조아라 조재성.
    # 조재경 조재경 조아라 조재성 조재경.

    # from faker.providers import internet
    # my_faker.add_provider(internet)
    # print(my_faker.ipv4_private())
    # print(my_faker.ipv4())
    # 172.17.4.226
    # 115.77.36.194

    # print(my_faker.bothify(text='ID asdfasdf: ???-###'))
    # print(my_faker.bothify(text='ID asdfasdf: ???-###', letters='AB'))
    # print(my_faker.bothify(text='010-####-####'))
    # ID asdfasdf: AAB-798
    # 010-3254-7082

    # print(my_faker.license_plate()) # 7 글자의 특문영어숫자조합 라이센스
    # ZUY6022

