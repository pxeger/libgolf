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


def test_nones():
    assert isinstance(List.nones(10), List)
    assert list(List.nones(10)) == [None] * 10
    # -1 means infinite
    l = iter(List.nones(-1))
    assert all(next(l) is None for _ in range(100))


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


def test_replace():
    # sanity check that our string comparisons work at all
    assert List("hello") == "hello"

    assert List("hello").replace("e", "a") == "hallo"
    assert List("hello").replace("hello", "goodbye") == "goodbye"
    assert List("hello").replace("goodbye", "welcome") == "hello"
    assert List("hello").replace("o", "o") == "hello"
    assert List("hello").replace("l", "y") == "heyyo"
    assert List("abbccbbdddbbb").replace("bb", "xyz") == "axyzccxyzdddxyzb"
    assert List("abaaaaa").replace("aa", "q") == "abqqa"
    assert List("abaaaaa").replace("aa", "") == "aba"
    assert List("hellllo").replace("l", "y", maxcount=2) == "heyyllo"
    # although I used strings for ease of readability, this should work with any type
    assert List(range(6)).replace((3, 4), ("hi",)) == (0, 1, 2, "hi", 5)

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert "".join(islice(List(generator()).replace("l", "y"), 3)) == "hey"
    assert not generator_executed


def test_replace_instances():
    assert List("hello").replace_instances("e", "a") == "hallo"
    assert List("hello").replace_instances("l", "y") == "heyyo"
    assert List("hello").replace_instances("el", "q") == "hello"
    assert List("").replace_instances("el", "q") == ""
    assert List.nones().replace_instances(None, "a")[:10] == ["a"] * 10
    assert List.nones().replace_instances(None, "a", maxcount=3)[:10] == ["a"] * 3 + [None] * 7

    # ensure lazy
    generator_executed = False

    def generator():
        yield from "hello"
        nonlocal generator_executed
        generator_executed = True

    assert "".join(List(generator()).replace_instances("l", "y")[:4]) == "heyy"
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
