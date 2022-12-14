def format_datetime(value, fmt='%Y-%m-%d %H:%M'):
    formatted = value.strftime(fmt.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    return formatted

def format_date(value, fmt='%Y-%m-%d'):
    formatted = value.strftime(fmt.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    return formatted


def format_timedelta(td):
    seconds = int(td.total_seconds())
    periods = [
        ('년', 60 * 60 * 24 * 365),
        ('월', 60 * 60 * 24 * 30),
        ('일', 60 * 60 * 24),
        ('시', 60 * 60),
        ('분', 60),
        # ('초', 1)
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            # has_s = 's' if period_value > 1 else ''
            strings.append("%s%s" % (period_value, period_name))

    return "".join(strings) + " 남음"