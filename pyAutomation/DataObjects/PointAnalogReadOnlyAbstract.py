import struct
import math
from abc import ABC, abstractmethod
from PointReadOnlyAbstract import PointReadOnlyAbstract


valid_data_types = [
    # 'sub-bit', # single bit in a 16 bit word.
    'int16-big-endian', # 2's complement
    'int16-little-endian', # 2's complement
    'uint16-big-endian', # unsigned
    'uint16-little-endian', # unsigned
    'int32-big-endian', # 2's complement
    'int32-little-endian', # 2's complement
    'uint32-big-endian', # unsigned
    'uint32-little-endian', # unsigned
    'float32-big-endian', # IEEE 754
    'float32-little-endian', # IEEE 754
    'float64-big-endian', # IEEE 754 binary64
    'float64-little-endian', # IEEE 754 binary64
]


class PointAnalogReadOnlyAbstract(PointReadOnlyAbstract, ABC):
    """ Abstract implementation of a read-only analog point """

    # unit of measure
    @abstractmethod
    def _get_u_of_m(self) -> str:
        pass

    u_of_m = property(_get_u_of_m)

    @staticmethod
    def datatype_length_bytes(data_type: 'str') -> 'int':
        """ Returns the length in bytes of the valid data types for transport
        over the wire."""
        if   data_type == 'int16-big-endian' \
          or data_type == 'int16-little-endian' \
          or data_type == 'uint16-big-endian' \
          or data_type == 'uint16-little-endian':
            return 2
        if data_type == 'int32-big-endian' \
          or data_type == 'int32-little-endian' \
          or data_type == 'uint32-big-endian' \
          or data_type == 'uint32-little-endian' \
          or data_type == 'float32-big-endian' \
          or data_type == 'float32-little-endian':
            return 4
        if data_type == 'float64-big-endian' \
          or data_type == 'float64-little-endian':
            return 8
        
        return None

    def decode_datatype(self, data: 'bytearray', data_type: 'str') -> 'None':
        """ Converts the a bytearray into a float based upon a supplied
        datatype and stores that value in the point."""
        assert data_type in valid_data_types, \
          "Invalid data type of %s supplied" % data_type

        if data_type == 'int16-little-endian':
            self.value = int.from_bytes(data, byteorder='little', signed=True)

        if data_type == 'int16-big-endian': # unsigned
            self.value = int.from_bytes(data, byteorder='big', signed=True)

        if data_type == 'uint16-little-endian': # unsigned
            self.value = int.from_bytes(data, byteorder='little', signed=False)

        if data_type == 'uint16-big-endian': # unsigned
            self.value = int.from_bytes(data, byteorder='big', signed=False)

        if data_type == 'int32-big-endian': # 2's complement
            self.value = int.from_bytes(data, byteorder='big', signed=True)

        if data_type == 'int32-little-endian': # 2's complement
            self.value = int.from_bytes(data, byteorder='little', signed=True)

        if data_type == 'uint32-big-endian': # unsigned
            self.value = int.from_bytes(data, byteorder='big', signed=False)

        if data_type == 'uint32-little-endian': # unsigned
            self.value = int.from_bytes(data, byteorder='little', signed=False)

        if data_type == 'float32-big-endian': # IEEE 754
            self.value = struct.unpack("f", data)

        if data_type == 'float32-little-endian': # IEEE 754
            data = data[::-1]
            self.value = struct.unpack("f", data)

        if data_type == 'float64-big-endian': # IEEE 754 binary64
            self.value = struct.unpack("d", data)

        if data_type == 'float64-little-endian': # IEEE 754 binary64
            data = data[::-1]
            self.value = struct.unpack("d", data)

    def encode_datatype(self, data_type: 'str') -> 'bytearray':
        """ get the value of this point as a bytearray in the format as
        specified by the supplied datatype. """
        assert data_type in valid_data_types, \
          "Invalid data type of %s supplied" % data_type

        data = None

        if data_type == 'int16-little-endian':
            num = math.trunc(self.value)
            data = int(num).to_bytes(2, byteorder='little', signed=True)

        if data_type == 'int16-big-endian': # unsigned
            num = math.trunc(self.value)
            data = int(num).to_bytes(2, byteorder='big', signed=True)

        if data_type == 'uint16-little-endian': # unsigned
            num = math.trunc(self.value)
            data = int(num).to_bytes(2, byteorder='little', signed=False)

        if data_type == 'uint16-big-endian': # unsigned
            num = math.trunc(self.value)
            data = int(num).to_bytes(2, byteorder='big', signed=False)

        if data_type == 'int32-big-endian': # 2's complement
            num = math.trunc(self.value)
            data = int(num).to_bytes(4, byteorder='big', signed=True)

        if data_type == 'int32-little-endian': # 2's complement
            num = math.trunc(self.value)
            data = int(num).to_bytes(4, byteorder='little', signed=True)

        if data_type == 'uint32-big-endian': # unsigned
            num = math.trunc(self.value)
            data = int(num).to_bytes(4, byteorder='big', signed=False)

        if data_type == 'uint32-little-endian': # unsigned
            num = math.trunc(self.value)
            data = int(num).to_bytes(4, byteorder='little', signed=False)

        if data_type == 'float32-big-endian': # IEEE 754
            data = bytearray(struct.pack("f", self.value))

        if data_type == 'float32-little-endian': # IEEE 754
            data = bytearray(struct.pack("f", self.value))
            data = data[::-1]

        if data_type == 'float64-big-endian': # IEEE 754 binary64
            data = bytearray(struct.pack("d", self.value))

        if data_type == 'float64-little-endian': # IEEE 754 binary64
            data = bytearray(struct.pack("f", self.value))
            data = data[::-1]

        return data
