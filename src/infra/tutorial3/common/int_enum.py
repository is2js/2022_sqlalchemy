import enum

from sqlalchemy import TypeDecorator, Integer

# https://michaelcho.me/article/using-python-enums-in-sqlalchemy-models
class IntEnum(TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).
    """
    # 1) DB저장은 Integer로 하므로, 상속하여 구현할 기존 sqlalclehmy Colum Type을 Integer로 지정한다.
    impl = Integer

    ## 추가
    # SAWarning: TypeDecorator IntEnum() will not produce a cache key because the
    #  ``cache_ok`` attribute is not set to True.  This can have significant performance implications including some performance degradations in comparison to pri
    # or SQLAlchemy versions.  Set this attribute to True if this type object's state is safe to use in a cache key, or False to disable this warning. (Background
    #  on this error at: https://sqlalche.me/e/14/cprf)
    cache_ok = True

    # 2) 해당 Column(IntEnum(MyEnumclass),  nullable... )으로 쓰일 Type은 Integer의 생성자를 재정의하되
    # -> 기존 생성자를 재정의해주고 + 특정Enumclass를 인자로 받아서 self._enumtype으로 보유하고 있는다.
    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype
        # print(f"self._enumtype >>> {self._enumtype}")
        # print(f"self._enumtype(1) >>> {self._enumtype(1)}, {type(self._enumtype(1))}")
        #### 1) 시작하면
        # self._enumtype >>> <enum 'PostPublishType'>
        # self._enumtype(1) >>> 1, <enum 'PostPublishType'>

    # enum객체 to db int value인듯?
    # 3) [field to db bind]해당Type이 value를 Enum필드객체를 가지고 있을 것이므로, int로 변환하여 db에 정의되도로고 하는 bind 메서드를 정의한다.
    # -> int값이면 그대로 sql에 bind, enum필드객체면, .value를 통해, enum에 매핑된 int값을 bind시킨다.
    # -> 데이터 생성시에만 호출되는 것 같다
    def process_bind_param(self, value, dialect):
        # print(f"def process_bind_param(self, value, dialect): -> value: {value}, type:{type(value)}")
        #  enum객체가 오면, .value를 통해 int value를
        #    int value가 오면, 그대로를 -> sql values(, , )에 집어넣어줌.
        #### 생성시
        # -> 수정할땐 호출안되고, 생성할때만 호출되는 듯 insert value에 해당하는?
        # def process_bind_param(self, value, dialect): -> value: 2, type:<class 'int'>
        if isinstance(value, int):
            return value

        return value.value

    # db int value to 객체  인듯?
    # 4) 반대로 [db to field]로 가는 방향을 result method로 정의해준다.
    # -> model.custom이넘필드 = int로 들어오거나,    db에서 int로 올라오는 것 -> 객체에는 enum필드객체로 유지하도록 변환해준다.
    def process_result_value(self, value, dialect):
        # print(f"process_result_value(self, value, dialect) >> value: {value} {type(value)}-> return self._enumtype(value):{self._enumtype(value)}, type{type(self._enumtype(value))}")
        ####
        # 2) 수정form을 생성하면, db int value to Post.has_type 칼럼에는 enum객체로 들어가는 듯
        # process_result_value(self, value, dialect) >> value: 3 <class 'int'>-> return self._enumtype(value):3, type<enum 'PostPublishType'>
        # class PostForm __init__ db에서 올라온 post의 self.post.has_type >>> 3


        #### one <- Many eager load시 joinedload -> outer join할 때, 해당 db가 None이면 여기서 에러난다.
        # => ValueError: None is not a valid SexType
        # for eager load
        # print('process_result_value =>>', value, dialect)
        #### outer join으로 인해, 해당칼럼에 None이 찰 수 도 있다.
        #### => 그 때, None값을 다시 객체ENum으로 만들어주는 과정이 차후 생기는데,
        #       객체Enum은  ( value )를 받아서 생성한다.
        #       여기서 customEnum( None )을 받아줄, None 대신 0을 반환하게 하고
        #       => 해당 CustomEnum에서는, NONE = 0으로 받아서 생성은 되게 default를 주자.
        if value is None:
            return 0
        #     # => 이걸 해줘도 또다른 에러남.
        #     # sqlalchemy.exc.InvalidRequestError: The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections

        return self._enumtype(value)


    @classmethod
    def choices(cls):
        # form을 위한 choices에는, 선택권한을 안준다? -> 0을 value로 잡아서 제외시킴
        return [(choice.value, choice.name) for choice in cls if choice.value]