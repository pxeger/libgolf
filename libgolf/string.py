from libgolf.list import List


class Character(str):
    def __new__(cls, arg):
        if isinstance(arg, int):
            arg = chr(arg)
        c = super().__new__(cls, arg)
        if len(c) != 1:
            raise ValueError("character must be of length 1")
        return c

    def __int__(self):
        return ord(self)


class String(List):
    _HASH = 0x9f6366ef3114f318

    def __init__(self, arg=()):
        super().__init__(Character(c) for c in arg)

    def __str__(self):
        return "".join(self)

    def __repr__(self):
        return repr(str(self))
