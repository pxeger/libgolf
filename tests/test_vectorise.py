from libgolf.list import List
from libgolf.vectorise import vectorise


def decad(*args):
    assert len(args) == 10
    return "+".join(args)


def l(*a):
    return List(a)


def test_vectorise():
    assert vectorise(lambda: "hello")() == "hello"

    assert vectorise(lambda x: x)(4) == 4
    assert vectorise(lambda x: x)(List()) == ()
    assert vectorise(lambda x: x)(List((1, 2, 3))) == (1, 2, 3)
    assert vectorise(lambda x: 0)(
        l(1, l(1), l(1, 1, l(1)), l(l(l(1))), 1)
    ) == [0, [0], [0, 0, [0]], [[[0]]], 0]

    assert vectorise(lambda x, y: x + y)("x", List("abc")) == ("xa", "xb", "xc")
    assert vectorise(lambda x, y: x + y)(List("abc"), "x") == ("ax", "bx", "cx")
    assert vectorise(lambda x, y: x + y)(List("abc"), List("xyz")) == ("ax", "by", "cz")

    assert vectorise(decad)(
        *map(List, ["ab", "cd", "ef", "gh", "ij", "kl", "mn", "op", "qr", "st"])
    ) == ["a+c+e+g+i+k+m+o+q+s", "b+d+f+h+j+l+n+p+r+t"]
