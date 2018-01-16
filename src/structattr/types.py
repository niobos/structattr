"""
Some widely used types

For a type to be usable as field type, it needs several methods:

* return the number of bits this field consumes or produces:
      cls.bits() -> int
  Note: this is a method call to be compatible with Enum-base classes

* decode data. Either of these (in order of preference):
      cls.from_int(data: int) -> cls
      cls.from_signed_int(data: int) -> cls
      cls.from_bytes(data: bytes) -> cls
  Note: the data in from_bytes is left-aligned (only relevant if bits() % 8 != 0)

* encode data. Either of these (in order of preference):
      obj.to_int() -> int
      obj.to_signed_int() -> int
      obj.to_bytes() -> bytes
  Note: the data from to_bytes must be left-aligned (only relevant if bits() % 8 != 0)


All variable-width type classes are wrapped in Memoized functions. This
guarantees that the *same* class is returned for two UInt(8) types, instead
of a different but otherwise identical class, yielding strange results
(enums not being equal, for example)
"""
import enum
import functools


@functools.lru_cache(maxsize=None)
def Enum(bits: int):
    """
    Returns a Enum-like class with the needed methods
    """
    class EnumBits(enum.Enum):
        @classmethod
        def bits(cls):
            return bits

        @classmethod
        def from_int(cls, data: int):
            return cls(data)

        def to_int(self) -> int:
            return self.value

    return EnumBits


class Zero(Enum(1)):
    """
    Bit that must be clear
    """
    Zero = 0


class One(Enum(1)):
    """
    Bit that must be set
    """
    One = 1


@functools.lru_cache(maxsize=None)
def UInt(bits: int):
    """
    Returns a class holding a fixed width unsigned integer
    """
    class UInt(int):
        @classmethod
        def bits(cls):
            return bits

        @classmethod
        def from_int(cls, data: int):
            return cls(data)

        def to_int(self):
            return self

        def __new__(cls, number):
            if number < 0:
                raise ValueError("UInt does not support negative numbers")
            if number >= 2 ** bits:
                raise ValueError(f"Value too large to fit in {bits} bits")
            return super().__new__(cls, number)

    return UInt


Bool = UInt(1)


@functools.lru_cache(maxsize=None)
def SInt(bits: int):
    """
    Returns a class holding a fixed width signed (2's complement) integer
    """
    class UInt(int):
        @classmethod
        def bits(cls):
            return bits

        @classmethod
        def from_signed_int(cls, data: int):
            return cls(data)

        def to_signed_int(self):
            return self

        def __new__(cls, number):
            if number < -(2 ** (bits-1)):  # -1 for sign bit
                raise ValueError(f"Value too small to fit in {bits} bits")
            if number >= 2 ** (bits-1):  # -1 for sign bit
                raise ValueError(f"Value too large to fit in {bits} bits")
            return super().__new__(cls, number)

    return UInt


@functools.lru_cache(maxsize=None)
def FixedPointSInt(total_bits: int = None,
                   integer_bits: int = None,
                   fractional_bits: int = None,
                   scale_factor: float = None,
                   ):
    """
    Returns a class holding a fixed point signed (2's complement) integer
    """
    try:
        if total_bits is None:
            total_bits = integer_bits + fractional_bits

        if scale_factor is None:
            if fractional_bits is None:
                fractional_bits = total_bits - integer_bits
            scale_factor = 1 / (2. ** fractional_bits)
    except TypeError:
        raise ValueError("Underspecified FixedPointInt")

    try:
        if total_bits != integer_bits + fractional_bits:
            raise ValueError("Overspecified conflicting FixedPointInt")
    except TypeError as e:
        pass

    class FixedPointSInt(float):
        @classmethod
        def bits(cls):
            return total_bits

        @classmethod
        def from_signed_int(cls, data: int):
            return cls(data * scale_factor)

        def to_signed_int(self):
            return int(self / scale_factor)

        def __new__(cls, number):
            if number / scale_factor < -(2 ** (total_bits - 1)):  # -1 for sign bit
                raise ValueError(f"Value too small")
            elif number / scale_factor >= 2 ** (total_bits - 1):  # -1 for sign bit
                raise ValueError(f"Value too large")
            return super().__new__(cls, number)

    return FixedPointSInt


@functools.lru_cache(maxsize=None)
def Bytes(num_bytes: int):
    class Bytes(bytes):
        @classmethod
        def bits(cls):
            return num_bytes * 8

        @classmethod
        def from_bytes(cls, data: bytes):
            return cls(data)

        def to_bytes(self) -> bytes:
            return self

    return Bytes
