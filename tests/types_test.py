import attr
import pytest
import structattr
from structattr.types import UInt, SInt, FixedPointSInt, Bool


def test_bounds():
    f = UInt(8)(0)
    with pytest.raises(ValueError):
        f = UInt(8)(-1)
    f = UInt(8)(255)
    with pytest.raises(ValueError):
        f = UInt(8)(256)

    f = SInt(8)(-128)
    with pytest.raises(ValueError):
        f = SInt(8)(-129)
    f = SInt(8)(127)
    with pytest.raises(ValueError):
        f = SInt(8)(128)

    T = FixedPointSInt(integer_bits=7, fractional_bits=1)
    f = T(-64)
    with pytest.raises(ValueError):
        f = T(-65)
    f = T(63.5)
    with pytest.raises(ValueError):
        f = T(64)


def test_fixed_point():
    with pytest.raises(ValueError):
        T = FixedPointSInt()

    with pytest.raises(ValueError):
        T = FixedPointSInt(total_bits=8)

    T = FixedPointSInt(integer_bits=7, fractional_bits=1)
    assert T.from_signed_int(1) == 0.5

    T = FixedPointSInt(integer_bits=7, fractional_bits=1, total_bits=8)
    assert T.from_signed_int(1) == 0.5

    with pytest.raises(ValueError):
        T = FixedPointSInt(integer_bits=8, fractional_bits=1, total_bits=8)

    T = FixedPointSInt(total_bits=8, integer_bits=7)
    assert T.from_signed_int(1) == 0.5

    T = FixedPointSInt(total_bits=8, fractional_bits=1)
    assert T.from_signed_int(1) == 0.5
