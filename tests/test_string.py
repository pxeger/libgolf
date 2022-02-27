import pytest

from libgolf.list import List
from libgolf.string import Character, String


def test_character():
    assert issubclass(Character, str)

    assert Character(1) == "\x01"
    assert type(Character(1)) is Character is not str
    assert Character(0x10FFFF) == "\U0010FFFF"

    assert Character("a") == "a"
    assert type(Character("a")) is Character is not str

    assert int(Character(100)) == 100

    assert repr(Character("a")) == "'a'"
    assert str(Character("a")) == "a"
    assert type(str(Character)) is str is not Character

    for x in ["abc", "", -1, 0x10FFFF + 1]:
        with pytest.raises(ValueError):
            Character(x)

    # operator overloads
    with pytest.raises(TypeError):
        Character("a") + Character("b")
    with pytest.raises(TypeError):
        Character("a") + "b"
    with pytest.raises(TypeError):
        Character("a") * 2
    with pytest.raises(TypeError):
        2 * Character("a")
    with pytest.raises(TypeError):
        Character("a") % ()


def test_string():
    assert issubclass(String, List)

    assert String("hello") == "hello"
    assert String() == ""
    assert all(isinstance(c, Character) for c in String("hello"))

    assert str(String("hello")) == "hello"
    assert type(str(String("hello"))) is str is not String

    assert repr(String("hello")) == "'hello'"
    assert type(repr(String("hello"))) is str is not String

    assert String("Hello").upper() == "HELLO"
    assert String("Hello").lower() == "hello"


def test_hash():
    assert hash(String("hello")) != hash(List("hello"))
