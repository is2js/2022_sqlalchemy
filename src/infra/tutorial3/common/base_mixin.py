"""
base_query 기반으로 각 model들의 쿼리들을 실행할 수 있는 mixin 구현
"""
from sqlalchemy.orm import Session

from src.infra.config.base import Base
from src.infra.config.connection import db
from src.infra.tutorial3.common.base_query import BaseQuery


# 1. model들이 자신의 정보를 cls.로 사용할 예정(객체 만들어서 chaining)이라면, Base를 상속해서 Mixin을 만들고, model은 Mixin을 상ㅅ속한다.
# => 그외 객체생성없이 메서드만 추가할 Mixin은 부모상속없이 그냥 만들면 된다.
# 1-2. 정의해준 BaseQuery의 class메서드들을 쓸 수 있게 한다?! => 그냥 import한 것으로 사용만할까?
class BaseMixin(Base, BaseQuery):
    __abstract__ = True  # Base상속 model인데, tablename안정해줄거면 있어야한다.

    # : https://stackoverflow.com/questions/20460339/flask-sqlalchemy-constructor
    # 2. 각 sqlalchemy model들은 사실상 cls()로 객체를 생성해도 init이나 new를 실행하지 않는다.
    # => 그 이유는 keyword만 칼럼정보로 받아 처리하기 때문이다.
    # => 하지만, 상태패턴처럼 .filter_by() 이후, 정보를 .order_by(), .first()에 넘기려면
    #   부모의 인자그대로 오버라이딩 후 => self._query의 필드를 가지고 있어야 chaning할 수 있다.
    """
    User(session=db.session, username='조재성').session 
    => <sqlalchemy.orm.session.Session object at 0x000002286C7A64E0>
    User(session=db.session, username='조재성').username
    => '조재성'
    """

    # 4. 자식으로서 chaning시 객체가 생성될 텐데, 그 때 넘겨주고 싶으면 인자를 **kwargs 앞에 너어주면 된다.
    def __init__(self, session=None, **kwargs):
        # 3. super() 인자 생략하면, super(나, self)로서 => [나의 상위(super)]에서부터 찾아쓰게
        # 인자 super(나 or 부모class중 택1, self)를 줘서 구체적인 부모를 지정할 수 있다.
        # => 나를 첫번째 인자로 주면, 나(BaseMixin)의 부모(super) -> Base부터 찾는다는 뜻이다.
        super(BaseMixin, self).__init__(**kwargs)
        self._query = None
        # 4. 객체를 생성하는 순간 chaining이 시작될 땐, 외부에서 사용중이던 session이 안들어오면 새 session을 배급한다.
        # => 배급한 session은 실행메서드들이 close를 꼭 해줄 것이다.
        self.session = db.get_session() if not session else session
        self._served = False

    #### 5. Create/Get/Filter는 내부에서 객체생성 with session => 실행까지 될 예정이므로
    ####   @classmethod로 작성한다.
    ####   first()/all()/count() 등의 실행메서드는 생성된 객체.method()로 작동하므로 일반 self메서드로 작성한다.
    @classmethod
    def get(cls, session: Session = None, **kwargs):
        ...
