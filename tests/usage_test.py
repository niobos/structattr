import attr
import pytest
import structattr
from structattr.types import UInt, Bool, FixedPointSInt, Enum, SInt, Bytes


# Start of by defining your data structure
# Decorate the class with both @attr.s and @structattr.add_methods
# Note the order of decorations: @attr.s must be applied first (i.e. must be
# the closest to the class definition
@structattr.add_methods
@attr.s(slots=True, auto_attribs=True)
class MyMessage:
    # Inside the class, you can define your fields
    # You can either use attr's auto_attribs feature, or specify them
    # explicitly using attr.ib() syntax

    header: UInt(8)
    # This specifies that the first byte (8 bits) is to be interpreted as an
    # unsigned integer (i.e. range 0-255)
    # alternatively: header = attr.ib(type=UInt(8))

    # The second byte is split up:
    flag: Bool
    # The first bit is a boolean flag

    class Mode(Enum(2)):
        Off = 0
        On = 1
        # not defined = 2
        Timer = 3
    mode: Mode
    # The next 2 bits are decoded as an Enum.
    # Note that not all possibilities need to be defined
    # Undefined values raise a ValueError on decode (but see
    # test_invalid_data_forced below)

    value: SInt(5)
    # The last 5 bits of the second byte are a signed integer
    # (2's complement, i.e. range -16 -> 15)

    fvalue: FixedPointSInt(integer_bits=6, fractional_bits=2)
    # The next byte contains a fixed point signed integer with 6 integer bits,
    # and 2 bits for the fractional part. This can represent numbers from
    # -32.00 to 31.75 in increments of 0.25

    blob: Bytes(2)
    # 2 bytes (not bits) of arbitrary data


def test_usage():
    b = b'\x12\xbf\xfe\xab\xcd'
    m = MyMessage.from_bytes(b)
    assert m.to_bytes() == b

    assert m.header == 0x12
    assert m.flag == True
    assert isinstance(m.mode, MyMessage.Mode)
    assert m.mode == MyMessage.Mode.On
    assert m.value == -1
    assert m.fvalue == -0.5
    assert m.blob == b'\xab\xcd'

    m.header = UInt(8)(0x13)
    m.validate()
    assert m.to_bytes() == b'\x13\xbf\xfe\xab\xcd'

    m.header = 0x14
    # ^^^ While not correct, this will usually just work
    assert m.to_bytes() == b'\x14\xbf\xfe\xab\xcd'
    with pytest.raises(ValueError):
        # but fail validation
        m.validate()
    # You can attempt to convert it
    m.validate(convert=True)
    assert m.header.__class__ == UInt(8)


def test_invalid_data():
    b = b'\x12\xcf\xfe\xab\xcd'
    with pytest.raises(ValueError):
        m = MyMessage.from_bytes(b)


def test_invalid_data_forced():
    b = b'\x12\xdf\xfe\xab\xcd'
    m = MyMessage.from_bytes(b, force=True)
    assert m.to_bytes() == b

    assert m.header == 0x12
    assert m.flag == True

    assert not isinstance(m.mode, MyMessage.Mode)

    assert m.value == -1
    assert m.fvalue == -0.5

    assert m.blob == b'\xab\xcd'

    with pytest.raises(ValueError):
        m.validate()  # field is in Raw mode

    with pytest.raises(ValueError):
        m.validate(convert=True)  # can't be converted


def test_too_short():
    b = b'\x12\xcf\xfe'
    with pytest.raises(ValueError):
        m = MyMessage.from_bytes(b)


def test_too_long():
    b = b'\x12\xbf\xfe\xab\xcd\x00'
    with pytest.raises(ValueError):
        m = MyMessage.from_bytes(b)

    m = MyMessage.from_bytes(b, consume=True)
    assert m.header == 0x12

    b = bytearray(b)
    m = MyMessage.from_bytes(b, consume=True)
    assert m.header == 0x12
    assert b == b'\x00'
