import attr
import functools
import bitstruct

from typing import List, Callable, Iterable, Union, Dict, Any


def add_methods(cls):
    """
    Decorator to add `from_bytes()` and `to_bytes()` methods to the given class
    :param cls: class to decorate
    :return: decorated class
    """
    cls.from_bytes = from_bytes.__get__(cls, cls)  # make classmethod
    cls.to_bytes = to_bytes.__get__(None, cls)  # make instance method
    cls.validate = validate.__get__(None, cls)
    cls.__len__ = get_len.__get__(cls, cls)  # make classmethod
    return cls


@attr.s(slots=True, auto_attribs=True)
class BitStructInfo:
    """
    Class containing information on how to serialize/deserialize an object.
    """
    field_name: List[str] = None
    """List of field names to access them on the object"""

    field_type: List[type] = None

    from_bitstruct: str = ''
    """bitstruct unpack() format string"""

    from_funcs: List[Callable] = None
    """
    List of function to convert the type of the attribute to something
    we can handle (int, signed int, bytes)
    """

    to_bitstruct: str = ''
    """
    bitstruct pack() format string
    Will usually be identical to from_bitstruct, but this is not enforced.
    """

    to_funcs: List[Callable] = None
    """
    List of functions to convert something we can handle (int, signed int,
    bytes) to the correct type
    """

    def __attrs_post_init__(self):
        # workaround for mutable defaults
        for a in ('field_name', 'field_type', 'from_funcs', 'to_funcs'):
            if getattr(self, a) is None:
                setattr(self, a, [])

    @property
    def num_bytes(self):
        """Return the number of bytes described in this BitStructInfo"""
        num_bits = bitstruct.calcsize(self.from_bitstruct)
        if num_bits % 8 != 0:
            raise TypeError("Attributes do not add up to a multiple of 8 bits")
        return num_bits // 8

    @classmethod
    @functools.lru_cache()
    def from_attr_class(cls, attrcls: type) -> 'BitStructInfo':
        """
        Read out the attr.ib()'s from class attrcls and generate the corresponding
        BitStructInfo object

        :param attrcls: class to inspect
        """
        bi = cls()
        for attribute in attr.fields(attrcls):
            bi.add_attr(attribute)

        # TODO: pre-compile bitstruct fmt strings

        return bi

    def add_attr(self, attribute):
        field_type = attribute.type
        self.field_type.append(field_type)
        bits = field_type.bits()
        self.field_name.append(attribute.name)
        if hasattr(field_type, 'from_int'):
            self.from_bitstruct += f'>u{bits}'
            self.from_funcs.append(field_type.from_int)
        elif hasattr(field_type, 'from_signed_int'):
            self.from_bitstruct += f'>s{bits}'
            self.from_funcs.append(field_type.from_signed_int)
        elif hasattr(field_type, 'from_bytes'):
            self.from_bitstruct += f'>r{bits}'
            self.from_funcs.append(field_type.from_bytes)
        else:
            raise TypeError(f"Attribute {attribute.name} has no suitable `from_` method")
        if hasattr(field_type, 'to_int'):
            self.to_bitstruct += f'>u{bits}'
            self.to_funcs.append(field_type.to_int)
        elif hasattr(field_type, 'to_signed_int'):
            self.to_bitstruct += f'>s{bits}'
            self.to_funcs.append(field_type.to_signed_int)
        elif hasattr(field_type, 'to_bytes'):
            self.to_bitstruct += f'>r{bits}'
            self.to_funcs.append(field_type.to_bytes)
        else:
            raise TypeError(f"Attribute {attribute.name} has no suitable `to_` method")


class RawField:
    """
    Class to indicate the field was not converted, but conversion was forced

    Simply holds the raw value and returns it. All to_*() methods are implemented,
    but it is assumed only the "correct" one will be called.
    """
    def __init__(self, data):
        self.data = data


def deserialize(data: Union[bytes, bytearray],
                bitstruct_info: BitStructInfo,
                ignore_too_long=False,
                consume: bool=False,
                force: bool=False) -> Dict[str, Any]:
    """
    Deserialize `data` according to `bitstruct_info`
    :param data: data to deserialize
    :param bitstruct_info: instructions to deserialize.
    :param ignore_too_long: ignore trailing bytes that are not decoded
    :param consume: delete the read bytes from `data`, leave the rest in there.
                    This implies `ignore_too_long=True`
    :param force: Force deserialization, even if the conversions to the field
                  types fail. Store unaltered int/bytes in that case
    :return: deserialized fields
    """
    if len(data) < bitstruct_info.num_bytes:
        raise ValueError(f"Invalid length of data: got {len(data)} bytes,"
                         f" expected {bitstruct_info.num_bytes} bytes")
    elif len(data) > bitstruct_info.num_bytes:
        if consume or ignore_too_long:
            pass
        else:
            raise ValueError(f"Invalid length of data: got {len(data)} bytes,"
                             f" expected {bitstruct_info.num_bytes} bytes")

    fields = bitstruct.unpack(bitstruct_info.from_bitstruct, data[0:bitstruct_info.num_bytes])

    converted_fields = {}
    for i, field in enumerate(fields):
        try:
            value = bitstruct_info.from_funcs[i](field)
        except ValueError:
            if force:
                value = RawField(data=field)
            else:
                raise
        converted_fields[bitstruct_info.field_name[i]] = value

    if consume:
        try:
            del data[0:bitstruct_info.num_bytes]
        except TypeError:
            # message is bytes, not bytearray. ignore
            pass

    return converted_fields


def from_bytes(cls: type,
               data: Union[bytes, bytearray],
               bitstruct_info: BitStructInfo = None,
               ignore_too_long=False,
               consume: bool = False,
               force: bool = False):
    """
    Deserialize `data` according to `bitstruct_info`
    :param cls: class of object to create
    :param data: data to deserialize
    :param bitstruct_info: instructions to deserialize. Tries to extract the
                           information from a attr-compatible `cls` if not
                           given
    :param ignore_too_long: ignore trailing bytes that are not decoded
    :param consume: delete the read bytes from `data`, leave the rest in there.
                    This implies `ignore_too_long=True`
    :param force: Force deserialization, even if the conversions to the field
                  types fail. Store unaltered int/bytes in that case
    :return: object of the given type
    """
    if bitstruct_info is None:
        bitstruct_info = BitStructInfo.from_attr_class(cls)

    converted_fields = deserialize(data, bitstruct_info,
                                   ignore_too_long=ignore_too_long,
                                   consume=consume,
                                   force=force)
    strip_leading_underscore(converted_fields)
    return cls(**converted_fields)


def serialize(fields: Iterable, bitstruct_info: BitStructInfo) -> bytes:
    """
    Serialize `self` according to `bitstruct_info`
    :param fields: List of fields to serialize
    :param bitstruct_info: instructions to serialize.
    :return: serialized data
    """
    converted_fields = []
    for i, value in enumerate(fields):
        if isinstance(value, RawField):
            value = value.data
        else:
            value = bitstruct_info.to_funcs[i](value)
        converted_fields.append(value)

    return bitstruct.pack(bitstruct_info.to_bitstruct, *converted_fields)


def to_bytes(self, bitstruct_info: BitStructInfo = None) -> bytes:
    """
    Serialize `self` according to `bitstruct_info`
    :param self: object to serialize
    :param bitstruct_info: instructions to serialize. Tries to extract the
                           information from a attr-compatible `self` if not
                           given
    :return: serialized data
    """
    if bitstruct_info is None:
        bitstruct_info = BitStructInfo.from_attr_class(self.__class__)

    fields = [
        getattr(self, name)
        for name in bitstruct_info.field_name
    ]
    return serialize(fields, bitstruct_info)


def validate(self, convert: bool = False, bitstruct_info: BitStructInfo = None) -> bool:
    """
    Validate if the fields contain correct data
    :param self: object to validate
    :param convert: try to convert fields to the correct type
    :param bitstruct_info: instructions to serialize. Tries to extract the
                           information from a attr-compatible `self` if not
                           given
    :raises: ValueError explaining what field is invalid and why
    :return: always True, if it returns without raising an exception
    """
    if bitstruct_info is None:
        bitstruct_info = BitStructInfo.from_attr_class(self.__class__)

    for i, name in enumerate(bitstruct_info.field_name):
        value = getattr(self, name)
        field_type = bitstruct_info.field_type[i]
        if not isinstance(value, field_type):
            if convert:
                try:
                    value = field_type(value)
                    setattr(self, name, value)
                except ValueError as e:
                    raise ValueError(f"field {name} could not be convertef from type {value.__class__.__name__},"
                                     f" to type {bitstruct_info.field_type[i].__name__}") \
                        from e
            else:
                raise ValueError(f"field {name} is of type {value.__class__.__name__},"
                                 f" not of type {bitstruct_info.field_type[i].__name__}") \

    return True


def get_len(cls) -> int:
    bitstruct_info = BitStructInfo.from_attr_class(cls)
    return bitstruct_info.num_bytes


def strip_leading_underscore(f: Dict[str, Any]):
    keys = list(f.keys())
    for k in keys:
        if k.startswith('_'):
            f[k[1:]] = f[k]
            del f[k]
