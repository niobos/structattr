import attr
import pytest
import structattr
from structattr.types import UInt, Bool, FixedPointSInt, Enum, SInt, Bytes


@structattr.add_methods
@attr.s(slots=True, auto_attribs=True)
class MyMessage:
    first: UInt(8)


@structattr.add_methods
@attr.s(slots=True, auto_attribs=True)
class MyMessageDeriv(MyMessage):
    second: UInt(8)


def test_usage():
    b = b'\x12\x34'
    m = MyMessageDeriv.from_bytes(b)
    assert m.to_bytes() == b

    assert m.first == 0x12
    assert m.second == 0x34
