import attr
import pytest
import structattr
from structattr.types import UInt, Bool, FixedPointSInt, Enum, SInt


def test_not_byte_aligned():
    @structattr.add_methods
    @attr.s(slots=True, auto_attribs=True)
    class MyMessage:
        header: UInt(7)

    b = b'\xfe'

    with pytest.raises(TypeError):
        m = MyMessage.from_bytes(b)


def test_no_bits_method():
    @structattr.add_methods
    @attr.s(slots=True, auto_attribs=True)
    class MyMessage:
        field: int

    b = b'\xfe'
    with pytest.raises(AttributeError):
        m = MyMessage.from_bytes(b)


def test_no_from_method():
    class MyType:
        @classmethod
        def bits(cls):
            return 8

        def to_int(self):
            return 0

    @structattr.add_methods
    @attr.s(slots=True, auto_attribs=True)
    class MyMessage:
        field: MyType

    b = b'\xfe'
    with pytest.raises(TypeError):
        m = MyMessage.from_bytes(b)


def test_no_to_method():
    class MyType:
        @classmethod
        def bits(cls):
            return 8

        @classmethod
        def from_int(cls, data: int):
            return cls()

    @structattr.add_methods
    @attr.s(slots=True, auto_attribs=True)
    class MyMessage:
        field: MyType

    b = b'\xfe'
    with pytest.raises(TypeError):
        m = MyMessage.from_bytes(b)
