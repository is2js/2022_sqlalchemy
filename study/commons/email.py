import re


def mask_email(email):
    """
    :param email: input email
    :return: a#####(5)b@domain 형식으로 email을 마스킹해서 반환
    """
    if '@' in email:
        name, domain = email.split("@")
        return f"{name[0]}#####{name[-1]}@{domain}"


def is_valid_email(email):
    """
    :param email:email
    :return: T/F
    """
    regex_verbose = re.compile(r"""                  # VERY readable and easy to understand. Software maintanability.
                ^\w+([\.-]?\w+)*              # start, \w+,
                @                             # single @ sign
                \w+([\.-]?\w+)*               # Domain name
                (\.\w{2,3})+$                 # .com, .ac.in,
                 """, re.VERBOSE | re.IGNORECASE)

    res = regex_verbose.match(email)
    if res:
        return True
    else:
        return False
