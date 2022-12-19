def format_datetime(value, fmt='%Y-%m-%d %H:%M'):
    formatted = value.strftime(fmt.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    return formatted

def format_date(value, fmt='%Y-%m-%d'):
    formatted = value.strftime(fmt.encode('unicode-escape').decode()).encode().decode('unicode-escape')
    return formatted