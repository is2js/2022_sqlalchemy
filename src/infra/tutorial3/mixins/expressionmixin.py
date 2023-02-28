from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.infra.tutorial3.mixins.crudmixin import CRUDMixin

# selects를 포함시켜 expression_based로 만들고 execute()로 수행하자.
class ExpressionMixin(CRUDMixin):
    __abstract__ = True

    ################
    # cls.실행메서드 # => obj + query 생성 후 -> self.실행메서드까지
    ################
    @classmethod
    def count_until(cls, date_attr, end_date,
                    count_attr=None,
                    session: Session = None,
                    ):
        """
        1. 칼럼을 지정하지 않는 경우, 첫번째 자동검색 pk 칼럼을 count (not distinct)
        Category.count_until('add_date', today).scalar() # 6
        Category.count_until('add_date', today).filter_by(id__ne=2).scalar()
        # 5

        2. 칼럼을 지정해서 카운팅( attr명에 집계함수 count를 작성하지 않으면, count를 집게)
           => distinct가 아니라면, id든, uk든, 일반칼럼이든 [똑같이 중복허용해서 센다는 소리]
        Category.count_until('add_date', today, count_attr='icon').scalar()
         # 5 (112, 112, 3, 3, 3)

        3. distinct를 붙이고 싶다면, 직접 count_attr='not pk or uk칼럼__count_distinct'
           => [distinct + not id/uk칼럼]이라면, [중복을 제외하고 센다]는 소리 (id/uk는 distinct해도 중복안나옴)
        Category.count_until('add_date', today, count_attr='icon__count_distinct').scalar()
        # 2 (112, 3)

        """
        # 1) count_attr이  주어지지 않으면, pk칼럼으로 카운팅할 준비를 한다.
        if not count_attr:
            count_column_expr = cls.create_column_expr(cls, cls.first_primary_key_name + '__' + 'count', cls.SELECT)
        else:
            if cls.COUNT not in count_attr:
                count_attr += '__' + cls.COUNT
            count_column_expr = cls.create_column_expr(cls, count_attr, cls.SELECT)

        srt_date_column = cls.create_column_expr(cls, date_attr, cls.FILTER_BY)

        query = (
            select(count_column_expr)
            .select_from(cls) # 필수
            .where(func.date(srt_date_column) <= end_date)
        )

        obj = cls.create_obj(session=session, query=query)

        print('obj._expression_based  >> ', obj._expression_based)
        print('obj._query  >> ', obj._query)


        return obj