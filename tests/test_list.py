from itertools import islice

import pytest

from libgolf.list import List


def test_basic():
    # no args = empty
    l = List()
    assert not list(l)

    l = List(range(10))
    assert list(l) == list(range(10))


def test_reiterable():
    l = List(range(10))
    assert iter(l) is not l
    assert list(l) == list(l) == list(range(10))


def test_concurrent_iteration():
    l = List(range(10))
    assert list(zip(l, l)) == list(zip(range(10), range(10)))


def test_lazy():
    def generator():
        yield from range(10)
        nonlocal generator_executed
        generator_executed = True
        yield from range(10, 20)

    generator_executed = False
    i = iter(List(generator()))
    for _ in range(10):
        next(i)
    assert not generator_executed
    assert list(i) == list(range(10, 20))
    assert generator_executed


def test_exhaust():
    generator_executed = False
    def generator():
        nonlocal generator_executed
        yield from "hello"
        generator_executed = True

    l = List(generator())
    assert l[:5] == "hello"
    assert not generator_executed
    assert not l.finished
    assert l.exhaust() is l
    assert generator_executed
    assert l.finished


def test_compare():
    for op in (
        (lambda x, y: x < y),
        (lambda x, y: x <= y),
        (lambda x, y: y > x),
        (lambda x, y: y >= x),
        (lambda x, y: not (y < x)),
        (lambda x, y: not (y <= x)),
        (lambda x, y: not (x > y)),
        (lambda x, y: not (x >= y)),
        (lambda x, y: not (x == y)),
        (lambda x, y: not (y == x)),
        (lambda x, y: x != y),
        (lambda x, y: y != x),
    ):
        assert op(List("apple"), List("banana"))
        assert op(List("apple"), List("apply"))
        assert op(List("apple"), List("apples"))
        assert op(List(()), List("apple"))

    assert List("apple") == List("apple")

    sentence = "the duck walked up to the lemonade stand and he stands".split()
    assert sorted(sentence, key=List) == sorted(sentence)

    # check converts properly
    assert List("apple") < "banana"
    assert List("apple") == "apple"

    with pytest.raises(TypeError):
        List("apple") < 2


def test_compare_identical():
    def generator():
        yield
        pytest.fail("generator should not be iterated")
    l = List(generator())
    assert l == l
    assert not (l != l)


def test_index():
    l = List(range(10))
    assert l[0] == 0
    assert l[7] == 7
    assert l[13] == 3
    assert l[-1] == 9

    def generator():
        yield from range(10)
        nonlocal generator_executed
        generator_executed = True

    generator_executed = False
    l = List(generator())
    assert l[0] == 0
    assert l[9] == 9
    assert l[9] == 9
    assert not generator_executed
    # exhaustion is required only when doing modular indexing
    assert l[10] == 0
    assert generator_executed

    generator_executed = False
    assert List(generator())[9] == 9
    assert not generator_executed
    assert List(generator())[-1] == 9
    assert generator_executed


def test_slice():
    l = List(range(10))
    assert l[:] == range(10)
    assert l[:0] == []
    assert l[:3] == [0, 1, 2]
    assert l[2:] == range(2, 10)
    assert l[1:4] == [1, 2, 3]
    assert l[1:6:2] == [1, 3, 5]
    assert l[::2] == [0, 2, 4, 6, 8]
    assert l[::-1] == reversed(range(10))
    assert l[::-2] == [9, 7, 5, 3, 1]
    assert l[-2::-2] == [8, 6, 4, 2, 0]
    assert l[1::-2] == [1]

    # ensure lazy
    generator_executed = False

    def generator():
        nonlocal generator_executed
        yield from range(10)
        generator_executed = True

    assert List(generator())[:10] == range(10)
    assert not generator_executed
    assert List(generator())[:11] == range(10)
    assert generator_executed
    generator_executed = False
    assert List(generator())[:][:10] == range(10)
    assert not generator_executed
    assert List(generator())[:] == range(10)
    assert generator_executed

    # ensure lazy even from the beginning
    generator_executed = False

    def generator():
        nonlocal generator_executed
        generator_executed = True
        yield from range(10)

    # don't evaluate
    List(generator())[:]
    List(generator())[-1:]
    List(generator())[:-1]
    List(generator())[::-1]
    assert not generator_executed


def test_reversed():
    assert list(reversed(List(range(10)))) == list(reversed(range(10)))


def test_len():
    assert len(List(range(10))) == 10


def test_repr():
    assert repr(List(range(10))) == repr(list(range(10)))


def test_lazy_length_compare():
    assert List(range(10)).length_compare_length(range(10)) == 0
    assert List(range(10)).length_compare_length(range(11)) == -1
    assert List(range(10)).length_compare_length(range(9)) == +1

    assert List(range(10)).length_compare_int(10) == 0
    assert List(range(10)).length_compare_int(11) == -1
    assert List(range(10)).length_compare_int(9) == +1

    # check properly lazy

    def generator():
        yield from range(10)
        nonlocal generator_executed
        generator_executed = True

    generator_executed = False

    assert List(generator()).length_compare_length(range(9)) == +1
    assert not generator_executed

    assert List(generator()).length_compare_length(range(11)) == -1
    assert generator_executed

    generator_executed = False
    assert List(generator()).length_compare_length(range(10)) == 0
    assert generator_executed


def test_repeat():
    assert isinstance(List.repeat("hi", 10), List)
    assert list(List.repeat("hi", 10)) == ["hi"] * 10
    x = object()
    # -1 means infinite
    l = iter(List.repeat(x, -1))
    assert all(next(l) is x for _ in range(100))


def test_nones():
    assert isinstance(List.nones(10), List)
    assert list(List.nones(10)) == [None] * 10
    # -1 means infinite
    l = iter(List.nones(-1))
    assert all(next(l) is None for _ in range(100))


def test_substitute():
    assert List("abcdef").substitute(4, "q") == "abcdqf"
    assert List("abcdef").substitute(9, "q") == "abcdef"
    assert List().substitute(0, "x") == ()

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert List(generator()).substitute(3, "x")[:5] == "helxo"
    assert not generator_executed


def test_insert():
    assert List("abcdef").insert(0, "q") == "qabcdef"
    assert List("abcdef").insert(5, "q") == "abcdeqf"

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert List(generator()).insert(4, "x")[:6] == "hellxo"
    assert not generator_executed


def test_append():
    assert List("hello").append("!") == "hello!"

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert List(generator()).append("!")[:5] == "hello"
    assert not generator_executed


def test_prepend():
    assert List("hello").prepend("¡") == "¡hello"

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert List(generator()).prepend("¡")[:6] == "¡hello"
    assert not generator_executed


def test_extend():
    assert List("hello").extend(", world") == "hello, world"

    # ensure lazy
    generator_executed = set()

    def generator(s):
        yield from s
        generator_executed.add(s)

    assert List(generator("hello")).extend(generator(", world"))[:12] == "hello, world"
    assert generator_executed == {"hello"}


def test_chain():
    assert List.chain() == ()
    assert List.chain("hello", "there", "", "!") == "hellothere!"


def test_flat():
    assert List([1, List(), 3, List([6, 7]), 2, 4, List([List([8]), List([5, 9])])]).flat() == [1, 3, 6, 7, 2, 4, 8, 5, 9]
    assert List([1, List(), 3, List([6, 7]), 2, 4, List([List([8]), List([5, 9])])]).flat(maxdepth=2) == [1, 3, 6, 7, 2, 4, 8, 5, 9]
    assert List([1, List(), 3, List([6, 7]), 2, 4, List([List([8]), List([5, 9])])]).flat(maxdepth=1) == [1, 3, 6, 7, 2, 4, (8,), (5, 9)]


def test_prefixes():
    assert List("hello").prefixes(include_empty=False) == ["h", "he", "hel", "hell", "hello"]
    assert List("hello").prefixes(include_empty=True) == ["", "h", "he", "hel", "hell", "hello"]

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert list(islice(List("hello").prefixes(False), 5)) == ["h", "he", "hel", "hell", "hello"]
    assert not generator_executed


def test_find_substrings():
    assert List("hello").find_substrings("el") == [1]
    assert List("hello").find_substrings("l") == [2, 3]
    assert List("hello").find_substrings("yo") == []
    assert List("hello").find_substrings("hey") == []
    assert List("hello").find_substrings("") == range(6)
    assert List("aaa").find_substrings("aa") == [0]
    assert List("aaaaaa").find_substrings("aa") == [0, 2, 4]
    assert List("").find_substrings("hi") == []
    assert List("").find_substrings("") == [0]

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert next(iter(List(generator()).find_substrings("e"))) == 1
    assert not generator_executed


def test_find():
    assert List("hello").find("l") == (2, 3)
    assert List("hello").find("x") == ()
    assert List("hello").find("ll") == ()
    assert List("").find("a") == ()
    assert List("").find(()) == ()

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert List(generator()).find("o")[0] == 4
    assert not generator_executed


def test_replace_substrings():
    # sanity check that our string comparisons work at all
    assert List("hello") == "hello"

    assert List("hello").replace_substrings("e", "a") == "hallo"
    assert List("hello").replace_substrings("hello", "goodbye") == "goodbye"
    assert List("hello").replace_substrings("goodbye", "welcome") == "hello"
    assert List("hello").replace_substrings("o", "o") == "hello"
    assert List("hello").replace_substrings("l", "y") == "heyyo"
    assert List("abbccbbdddbbb").replace_substrings("bb", "xyz") == "axyzccxyzdddxyzb"
    assert List("abaaaaa").replace_substrings("aa", "q") == "abqqa"
    assert List("abaaaaa").replace_substrings("aa", "") == "aba"
    assert List("hellllo").replace_substrings("l", "y", maxcount=2) == "heyyllo"
    # although I used strings for ease of readability, this should work with any type
    assert List(range(6)).replace_substrings((3, 4), ("hi",)) == (0, 1, 2, "hi", 5)

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert "".join(islice(List(generator()).replace_substrings("l", "y"), 3)) == "hey"
    assert not generator_executed


def test_replace():
    assert List("hello").replace("e", "a") == "hallo"
    assert List("hello").replace("l", "y") == "heyyo"
    assert List("hello").replace("el", "q") == "hello"
    assert List("").replace("el", "q") == ""
    assert List.nones().replace(None, "a")[:10] == ["a"] * 10
    assert List.nones().replace(None, "a", maxcount=3)[:10] == ["a"] * 3 + [None] * 7

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert "".join(List(generator()).replace("l", "y")[:4]) == "heyy"
    assert not generator_executed


def test_unique():
    assert List(()).unique() == ()
    assert List("abc").unique() == "abc"
    assert List("abcdabce").unique() == "abcde"
    # unhashables
    a = dict()
    b = dict()
    assert a is not b
    assert a == b
    assert List((a, b, a)).unique() == (a,)
    # ensure always takes the first instance of equal items
    assert List((a, b, a)).unique()[0] is a is not b
    assert List((b, a, a)).unique()[0] is b is not a


def test_product():
    assert List.product() == ((),)
    assert List.product("abc") == "abc"
    assert List.product("abc", "def") == ("ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf")
    assert List.product(()) == ()
    assert List.product("abc", ()) == ()
    assert List.product("a", "b") == ("ab",)

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "abc"
        nonlocal generator_executed
        generator_executed = True

    assert List.product(generator(), "def")[:9] == ("ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf")
    assert not generator_executed


def test_power():
    assert List("abc").power(2) == ("aa", "ab", "ac", "ba", "bb", "bc", "ca", "cb", "cc")
    assert List("abc").power(1) == "abc"
    assert List("abc").power(0) == ((),)
    assert len(List("abc").power(5)) == len("abc") ** 5


def test_combinations():
    assert List("abc").combinations(0) == ()
    assert List("abc").combinations(1) == ("a", "b", "c")
    assert List("abc").combinations(2) == ("ab", "ac", "bc")
    assert List("abc").combinations(3) == ("abc",)
    assert List("abc").combinations(4) == ()

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "abc"
        nonlocal generator_executed
        generator_executed = True

    assert List(generator()).combinations(2)[:2] == ("ab", "ac")
    assert not generator_executed


def test_bool():
    assert bool(List()) is False
    assert bool(List("abc")) is True
    assert bool(List([False])) is True

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "a"
        nonlocal generator_executed
        generator_executed = True
        yield from "bc"

    assert bool(List(generator())) is True
    assert not generator_executed

    assert bool(List.nones()) is True


def test_hash():
    l = List("abc")
    l2 = List("def")
    assert hash(l) == hash(l2)
    h = hash(l)
    l.exhaust()
    assert hash(l) == h == hash(l2)

    l = List("abc")
    l2 = List("def")
    l.exhaust()
    l2.exhaust()
    assert hash(l2) != hash(l)

    l3 = List("abc")
    l3.exhaust()
    assert hash(l) == hash(l3)


def test_integers():
    assert List.integers()[:100] == range(100)
    assert List.integers(1)[:100] == range(1, 101)


def test_powerset():
    assert List().powerset() == [[]]
    assert List((1,)).powerset() == [[], [1]]
    assert List(range(4)).powerset() == [[], [0], [1], [0, 1], [2], [0, 2], [1, 2], [0, 1, 2], [3], [0, 3], [1, 3], [0, 1, 3], [2, 3], [0, 2, 3], [1, 2, 3], [0, 1, 2, 3]]

    # ensure lazy
    generator_executed = 0

    def generator():
        nonlocal generator_executed
        for generator_executed in range(1, 5):
            yield generator_executed

    o = List(generator()).powerset()
    assert o[0] == []
    assert generator_executed == 0
    assert o[:2] == [[], [1]]
    assert generator_executed == 1
    assert o[:8] == [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]
    assert generator_executed == 3
    o.exhaust()
    assert generator_executed == 4
