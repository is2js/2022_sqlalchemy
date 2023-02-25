# ObjectMixin(BaseQuery) 이후로는 세팅된 Base를 사용하여, BaseModel이 Base대신 이것을 상속한다.
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint, exists
from sqlalchemy.orm import Session

from src.infra.config.base import Base
from src.infra.tutorial3.mixins.objectmixin import ObjectMixin
from src.infra.tutorial3.mixins.utils.classproperty import class_property

constraints_map = {
    'pk': PrimaryKeyConstraint,
    'fk': ForeignKeyConstraint,
    'unique': UniqueConstraint,
}


class CRUDMixin(Base, ObjectMixin):
    __abstract__ = True

    ############
    # Create   #
    ############
    @classmethod
    def create(cls, session: Session = None, auto_commit: bool = True, **kwargs):

        obj = cls.create_obj(session=session, **kwargs)

        # 1. 만들어진 [미등록 obj]내 unique=True인 칼럼의 값을 가져와, 존재하는지 검사한다.
        if obj.exists_self():
            return False, 'create fail'

        return obj.save(auto_commit=auto_commit), 'create success'

    # for create + ## 실행메서드 ##
    def exists_self(self):
        """
        등록 obj 존재검사(X), create()전 [미등록 obj의 unique 칼럼]을 바탕으로 db 존재 검사.
        =>  SELECT EXISTS (SELECT *
            FROM users
            WHERE users.username IS NULL) AS anon_1
        """

        unique_attr = getattr(self, self.unique_key_name)
        if not unique_attr:
            raise Exception(f'unique column 값을 입력하지 않았습니다.')

        expressions = self.create_filter_exprs(self.__class__,
                                               **{self.unique_key_name: unique_attr})
        stmt = self._query.where(*expressions)

        return self._session.scalar(exists(stmt).select())

    # for exists_self
    @classmethod
    def get_constraint_attr_names(cls, target='pk'):
        """
        User.get_constraint_attrs(target='unique')
        ['username']
        => 파생  User.pks / User.fks / User.uks
        """
        # 제약조건 관련은 .__table__.constrains에서 꺼내 쓴다.
        if isinstance(target, str) and target.lower() not in constraints_map.keys():
            raise NotImplementedError(f'해당 {target} 제약조건의 칼럼명 목록 조회는 구현되지 않았습니다.')

        constraints = cls.__table__.constraints
        target_constraint_class = constraints_map.get(target)
        target_constraint = next((c for c in constraints if isinstance(c, target_constraint_class)), None)

        # 해당 제약조건의 칼럼이 없으면, 그냥 빈 리스트 반환
        if not target_constraint:
            return []

        return target_constraint.columns.keys()

    # for exists_self
    @class_property
    def unique_key_names(cls):
        return cls.get_constraint_attr_names(target='unique')

    # for exists_self
    @property
    def unique_key_name(self):
        """
        User.unique_key
        """
        self_unique_key = next(
            (column_name for column_name in self.column_names if column_name in self.unique_key_names), None)
        if not self_unique_key:
            raise Exception(f'Create 전, 존재 유무 확인을 위한 unique key를 입력하지 않았습니다.')

        return self_unique_key

    # for exists_self
    @class_property
    def column_names(cls):
        return cls.__table__.columns.keys()

    @class_property
    def primary_key_names(cls):
        return cls.get_constraint_attr_names(target='pk')

    @class_property
    def foreign_key_names(cls):
        return cls.get_constraint_attr_names(target='fk')

    # for create + ## 실행메서드 ##
    def save(self, auto_commit: bool = True):
        #### try/catch는 외부세션을 넣어주는데서 할 것이다?
        self._session.add(self)
        # 1. add후 id, 등 반영하기 위해 [자체생성/외부받은 session 상관없이] flush를 때려준다.
        self._session.flush()
        # 2. 외부session인 경우, 외부의 마지막 옵션으로 더이상 사용안한다면 밖에서 auto_commit=True로 -> commit()을 때려 close시킨다.
        # => self.close()는 외부session을 flush()만 시키는데, 외부session이 CUD하는 경우, 자체적으로 commit()해야한다.
        # => 외부에서 더 쓴다면, 외부에서 sessino=sesion만 넣고 auto_commit 안하면 된다.
        if auto_commit:
            self._session.commit()

        return self


    ############
    # Read     #
    ############