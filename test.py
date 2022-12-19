class Node:
    def __init__(self):
        self.a = None
        self.b = None
        self.c = None

    def __repr__(self):
        info: str = f"{self.__class__.__name__}" \
                    f"[a={self.a!r}," \
                    f" b={self.b!r}," \
                    f" c={self.c!r}]"
        return info

if __name__ == '__main__':
    attrs = {
        'a' : '조',
        'b' : '재',
        'c' : '성',
    }
    node = Node()
    for column, value in attrs.items():
        setattr(node, column, value)

    print(node)
    # Node[a='조', b='재', c='성']