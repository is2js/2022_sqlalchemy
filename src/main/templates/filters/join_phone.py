def join_phone(phone: str, delimiter='-'):
    if phone:
        return delimiter.join([phone[:3], phone[3:7], phone[7:]])
    return phone


if __name__ == "__main__":
    print(join_phone('01046006243'))
    print(join_phone('01046006243', delimiter=' '))