from datetime import datetime


def to_string_date(last_month):
    return datetime.strftime(last_month, '%Y-%m-%d')
