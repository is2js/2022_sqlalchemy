import datetime


def feed_datetime(feed_time, is_feed=True):
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    wd = weekdays[feed_time.weekday()]
    # ymd_format = "%Y.%m.%d %H:%M({})".format(wd)
    ymd_format = "%Y.%m.%d %H:%M".format(wd)

    k = 1  # k일 이상부터는, 년월일, 그전에는 피드시간

    if not is_feed:
        formatted = feed_time.strftime(ymd_format.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    else:
        current_time = datetime.datetime.now()
        ## total 초로 바꾼다.
        total_seconds = int((current_time - feed_time).total_seconds())
        ## 어느 단위에 걸리는지 확인한다.
        periods = [
            ('year', 60 * 60 * 24 * 365, '년 전'),
            ('week', 60 * 60 * 24 * 7, '주 전'),
            ('day', 60 * 60 * 24,'일 전'),
            ('hour', 60 * 60, '시간 전'),
            ('minute', 60, '분 전'),
            ('second', 1, '초 전'),
        ]
        prev_unit = 0
        prev_ment = '방금 전'
        for period, unit, ment in reversed(periods):
            if total_seconds < unit:
                # (1) 큰 것부터 보면서 잘라먹고 나머지 다시 처리하는 식이 아니라
                # 작은단위부터 보고 그것을 못 넘어선 경우, 그 직전단위 prev_unit로 처리해야한다.
                # , 해당단위보다 클 경우, (ex> 61초 -> 1초보다, 60(1분)보단 큰데 60*60(1시간보단)작다  => 60,60직전의 1분으로처리되어야한다)
                #    나머지하위단위들을 total_seconds에 업뎃해서 재할당한다. -> 버린다.

                # (3) 1초보다 작아서, prev 0으로 나누는 경우는 그냥 방금전
                if not prev_unit:
                    value = ''
                else:
                    value, _ = divmod(total_seconds, prev_unit)
                # (2) 몫 + 멘트를 챙긴다
                formatted = str(value) + prev_ment
                # (3) [k][일] 이상 지나간, 년월일로 하자
                
                late_unit = 60 * 60 * 24
                if prev_unit == late_unit and value >= k:
                    formatted = feed_time.strftime(ymd_format.encode('unicode-escape').decode()).encode().decode(
                        'unicode-escape')
                break
            else:
                ## 현재단위보다 크면, 다음단위로 넘어가되 prev업뎃
                prev_unit = unit
                prev_ment = ment

    return formatted

if __name__ == "__main__":
    print(feed_datetime(datetime.datetime.now() - datetime.timedelta(seconds=62), is_feed=False))
    print(feed_datetime(datetime.datetime.now() - datetime.timedelta(seconds=119)))