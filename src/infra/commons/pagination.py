from __future__ import annotations

import math
import typing

from sqlalchemy import select, func

from src.config import db_config
from src.infra.config.connection import DBConnectionHandler


class Pagination:
    # https://parksrazor.tistory.com/457
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.page = page
        self.total = total

        # 이전 페이지를 가지고 있으려면, 현재page - 1 = 직전페이지 계산결과가, 실존 해야하는데, 그게 1보다 크거나 같으면 된다.
        #  0 [ 1 2 page ]
        self.has_prev = page - 1 >= 1
        # 이전 페이지 존재유무에 따라서 이전페이지 넘버를 현재page -1 or None 로 만든다.
        self.prev_num = (self.has_prev and page - 1) or None

        # 다음 페이지를 가지고 있으려면, 갯수로 접근해야한다.
        # (1) offset할 직전페이지까지의 갯수: (현재page - 1)*(per_page)
        # (2) 현재페이지의 갯수: len(items) => per_page를 못채워서 더 적을 수도 있다.
        # (3) total갯수보다 현재페이지까지의 갯수가 1개라도 더 적어야, 다음페이지로 넘어간다
        self.has_next = ((page - 1) * per_page + len(items)) < total
        # 다음페이지를 갖고 있다면 + 1만 해주면된다.
        self.next_num = page + 1 if self.has_next else None

        # total pages 수는, per_page를 나눠서 math.ceil로 올리면 된다.
        # self.pages = math.ceil(total / per_page) + 1
        self.pages = math.ceil(total / per_page) if total else 0

        # https://github.com/pallets-eco/flask-sqlalchemy/blob/main/src/flask_sqlalchemy/pagination.py

    def iter_pages(self, *,
                   left_edge: int = 2,  # 1페 포함 보여질 갯수,
                   left_current: int = 2,  # 현재로부터 왼쪽에 보여질 갯수,
                   right_current: int = 4,  # 현재로부터 오른쪽에 보여질 갯수,
                   right_edge: int = 2,  # 마지막페이지 포함 보여질 갯수
                   ) -> typing.Iterator[int | None]:

        # 1) 전체 페이지갯수를 바탕으로 end특이점을 구해놓는다.
        pages_end = self.pages + 1
        # 2) end특이점 vs1페부터보여질 갯수+1을 비교해, 1페부터 끝까지의 특이점을 구해놓는다.
        left_end = min(left_edge + 1, pages_end)
        # 3) 1페부터 특이점까지를 1개씩 yield로 방출한다.
        yield from range(1, left_end)
        # 4) 만약 페이지끝 특이점과 1페끝 특이점이 같으면 방출을 마친다.
        if left_end == pages_end:
            return
        # 5) 선택한 page(7) - 왼쪽에 표시할 갯수(2) (보정x 현재로부터 윈도우만큼 떨어진 밖.== 현재 제외 윈도우 시작점) -> 5 [6 7]
        #    과 left끝특이점 중 max()를 mid시작으로 본다.
        #   + 선택한page(7) + 오른쪽표시갯수(4) == 11 == 현재포함윈도우밖 == 현재제외 윈도우의 끝점 vs 전체페이지끝특이점중 min을 mid_end로 보낟
        mid_start = max(left_end, self.page - left_current)
        mid_end = min(pages_end, self.page + right_current)
        # 6) mid 시작과 left끝특이점 비교하여 mid가 더 크면, 중간에 None을 개설한다
        if mid_start - left_end > 0:
            yield None
        # 7) mid의 시작~끝까지를 방출한다.
        yield from range(mid_start, mid_end)
        # 8) mid_end와  (페이지끝특이점 - 우측에서 보여질 갯수)를 비교하여 더 큰 것을 right 시작점으로 본다.
        right_start = max(mid_end, pages_end - right_edge)
        # 9) mid_end(특이점)과 right시작점이 차이가 나면 중간에  None을 개설한다.
        if right_start - mid_end > 0:
            yield None
        # 10) right_start부터, page_end까지 방출한다.
        yield from range(right_start, pages_end)





def paginate(stmt, page=1, per_page=db_config.COMMENTS_PER_PAGE):
    if page <= 0:
        raise AttributeError('page needs to be >= 1')
    if per_page <= 0:
        raise AttributeError('per_page needs to be >= 1')

    with DBConnectionHandler() as db:
        # 이미 select된 stmt의 column에 func.count(.id)만 추가할 수 없으니
        # => select된 것을 subquery로 보고 select_from에 넣어서 count를 센다
        total = db.session.scalar(
            select(func.count('*'))
            .select_from(stmt.subquery())
        )

        items = db.session.scalars(
            stmt.limit(per_page)
            .offset((page - 1) * per_page)
        ).all()

    return Pagination(items, total, page, per_page)
