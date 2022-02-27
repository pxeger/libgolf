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

    def __add__(self, other):
        return NotImplemented

    __mul__ = __rmul__ = __radd__ = __mod__ = __add__


class String(List):
    _HASH = 0x9f6366ef3114f318

    def __init__(self, arg=()):
        super().__init__(Character(c) for c in arg)

    def __str__(self):
        return "".join(self)

    def __repr__(self):
        return repr(str(self))

    def __ascii__(self):
        return ascii(str(self))

    @List._wrap
    def lower(self):
        return (c.lower() for c in self)

    @List._wrap
    def upper(self):
        return (c.upper() for c in self)
