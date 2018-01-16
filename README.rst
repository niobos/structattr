StructAttr
==========

StructAttr is a decorator for classes that adds a deserializer method
`from_bytes()` and a serializer method `to_bytes()` to the class. It also adds
a `validate()` method, which verifies if all the fields are of the correct
type, and optionally tries to convert them to the correct type.

It is designed to work in close cooperation with `attrs` module, but can used
independently. See `tests/usage_test.py` for examples


Field types
-----------

For a type to be usable as field type, it needs several methods:

* return the number of bits this field consumes or produces:
      cls.bits() -> int
  Note: this is a method call to be compatible with Enum-derived classes

* decode data. Either of these (in order of performance):
      cls.from_int(data: int) -> cls
      cls.from_signed_int(data: int) -> cls
      cls.from_bytes(data: bytes) -> cls
  Note: the data in from_bytes is left-aligned (only relevant if bits() % 8 != 0)

* encode data. Either of these (in order of preference):
      obj.to_int() -> int
      obj.to_signed_int() -> int
      obj.to_bytes() -> bytes
  Note: the data from to_bytes must be left-aligned (only relevant if bits() % 8 != 0)


Use without `attrs`
-------------------

Although this module is designed to work on top of attr-classes, you can use
it independently as well. You need to provide an additional parameter to
`from_bytes()` and `to_bytes()` to indicate the encoding of the class
properties from/to bytes.

The extra parameter is a list (or tupple) of objects with the following
properties:

 * o.name : attribute name to use when accessing the field
 * o.type : type of the field
