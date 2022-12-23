def join_phone(phone: str, delimiter='-'):
    if phone:
        return delimiter.join([phone[:3], phone[3:7], phone[7:]])
    return phone


def join_birth(birth: str, delimiter='-'):
    if birth:
        return delimiter.join([birth[:6], birth[6:]])
    return birth


if __name__ == "__main__":
    print(join_phone('01046006243'))
    print(join_phone('01046006243', delimiter=' '))
