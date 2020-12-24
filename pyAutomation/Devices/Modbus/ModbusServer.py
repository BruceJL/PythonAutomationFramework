from datetime import datetime
from datetime import timedelta
import asyncio
from operator import attrgetter

from pyAutomation.DataObjects.PointAnalogReadOnlyAbstract import \
  valid_data_types
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointHandler import PointHandler
from pyAutomation.Devices.Modbus.CommandModbus import \
  CommandModbus, makeCommandObjects


class ModbusServer(SupervisedThread, PointHandler):
    """Provides a Modbus server to provide visibility of point database
    quantities to remote Modbus clients."""

    parameters = {
      'endpoint_address': 'string',
      'port': 'int',
      'socket_timeout': 'int',
    }

    # mapping is drop, command, address
    point_mapping = dict[int, [int, [int, PointAbstract]]]

    # data types are used to interpret the data in HOLDING (03) or INPUT (04)
    # registers. COIL (01) and DISCRETE (02) registers are always bits.

    _valid_data_types = 'sub-bit' + valid_data_types  # type: List

    def __init__(self, name, logger):
        self.sock = None
        self.endpoint_address = ""
        self.endpoint_port = 0
        self.min_sleep_time = timedelta(milliseconds=10)
        self.period = None
        self.modbus_commands = []  # type: List[ModbusCommand]

        # SupervisedThread __init__ call
        super().__init__(
          name=name,
          logger=logger,
          loop=self.loop,
          period=self.period)

    # SupervisedThread manditory override
    def config(self, data: 'dict') -> 'None':
        """ Takes the points required for this driver and sorts them into
        groups so that commands of nearby addresses are grouped together. This
        allows the Modbus client to get the points form the server using a
        minimum number of requests"""

        self.logger.debug("Entering function")

        coroutine = asyncio.start_server(
          client_connected_cb,
          host=None,
          port=None,
          *,
          # loop=None,
          limit=None,
          family=socket.AF_UNSPEC,
          flags=socket.AI_PASSIVE,
          sock=None,
          backlog=100,
          ssl=None,
          reuse_address=None,
          reuse_port=None,
          ssl_handshake_timeout=None,
          start_serving=True,
        )

    def __from_bytes(data: 'bytearray') -> 'int':
        return int.from_bytes(data, byteorder='little', signed=False)

    def __make_error_response(data: 'bytearray' code: 'int') -> 'bytearray':
        # In a normal response, the slave simply echoes the function code of
        # the original query in the function field of the response.  All
        # function codes have their most-significant bit (msb) set to 0
        # (their values are below 80H).  In an exception response, the slave
        # sets the msb of the function code to 1 in the returned response
        # (i.e. exactly 80H higher than normal) and returns the exception
        # code in the data field.  This is used by the client/master
        # application to actually recognize an exception response and to
        # direct an examination of the data field for the applicable
        # exception code.
        reply_data = bytearray(9)
        reply_data[0:6] = data[0:6]
        reply_data[7] = data[7] + 0x80
        reply_data[8] = code  # illegal function
        return reply_data

    async def do_io(reader, writer) -> None:
        """ Run the I/O routine asyncronously."""
        data = bytearray()
        # Wait on incoming data.
        data = await reader.read(5)

        # Read all the command data from the client.
        transaction_id = __from_bytes(data[0:1])
        protocol_id = __from_bytes(data[2:3])
        message_length = __from_bytesdata[4:5])

        # wait for the remainder of the data from the buffer
        data.append(await reader.read(message_length))

        # populate additional fields.
        unit_identifier = __from_bytes(data[6])
        function_code = _from_bytes(data[7])
        starting_address = __from_bytes(data[8:9])
        payload_data = __from_bytes(data[10:11])

        if   function_code == 0x01 \
          or function_code == 0x05 \
          or function_code == 0x15:
            return reply_data_length / 8 + 1
        else
            return reply_data_length * 2

        reply_data = bytearray(reply_data_length + 9)
        reply_data[0:1]=__from_bytes(transaction_id)
        reply_data[2:3]=__from_bytes(protocol_id)
        # data legnth is the length of the data in bytes + 1 byte for the
        # command byte and another byte for the unit identifier
        reply_data[4:5]=\
          (reply_data_length + 2).to_bytes(2, byteorder='little', signed=False)
        reply_data[6]=unit_identifier
        reply_data[7]=function_code
        reply_data[8]=\
          (reply_data_length).to_bytes(1, byteorder='little', signed=False)

        if function_code = 0x01:
            # Read coil status (0x reference address)

            for i in range(0, payload_data):
                byte = int(0)
                try:
                    point = point_mapping\
                      [unit_identifier]\
                      [function_code]\
                      [starting_address + i]\
                      ['point']

                    if point.value is True:
                        mask = 1 << i
                        byte = byte | mask

                    if i + 1 % 8 == 0 or i - 1 == payload_data:
                        reply_data[9 + (i % 8)] = \
                          byte.to_bytes(1, byteorder='little', signed=False)
                        byte = 0

                except KeyError:
                    pass

        elif function_code == 0x03 or function_code == 0x04:
            # Read Holding Registers (function code 0x03 - 4x reference address)
            # - YES 4X
            # or Input registers (function code 0x04 - 3x reference address)

            # bit in words are dealt with by making fake 'points' that
            # return the correct data.
            i = 0
            while i < reply_data_length:
                try:
                    point = point_mapping\
                      [unit_identifier]\
                      [function_code]\
                      [starting_address + i]\
                      ['point']

                    data_type = point_mapping\
                      [unit_identifier]\
                      [function_code]\
                      [starting_address + i]\
                      ['data_type']

                    point_data = point.encode_datatype(data_type=data_type)
                    reply_data[i:] = point_data
                    i += len(point_data)

                    # return an error if i has exceeded reply_data_length
                    # this would be the case if a client requested data that was
                    # 4 bytes long (e.g. 32 bit int), but didn't request enough
                    # return data to download the entire data structure.
                    # return an 'Illegal Data address' error (Code 02)
                    if i >= reply_data_length:
                        reply_data = __make_error_response(data, 0x02)

                except KeyError:
                    if i == 0:
                        # didn't find any data at the starting address. Return
                        # an illegal data address error. Maybe this is a bad
                        # idea as changes to the data table may break client
                        # behaviour. Whatever! That's what you get for using
                        # Modbus!
                        reply_data = __make_error_response(data, 0x02)
                        i = reply_data_length  # exit the while loop
                    else:
                         i += 1

        elif function_code = 0x05:
            # Force Single Coil  (0x reference address)
            try:
                point = point_mapping\
                  [unit_identifier]\
                  [0x01]\
                  [starting_address]\
                  ['point']

                if point.readonly:
                    # attempted to write to a read only point.
                    reply_data = __make_error_response(data, 0x02)

                elif payload_data == 0xFF00:
                    point.value = True

                elif payload_data == 0x0000:
                    point.value = False

                else
                    # The client didn't supply a valid payload
                    reply_data = __make_error_response(data, 0x02)

            except KeyError:
                # address is invalid, fail the command with a 'illegal data
                # address' error!
                reply_data = __make_error_response(data, 0x02)

        elif function_code = 0x06:
            # Preset Single Register (4x reference address) (16 bits)
            try:
                point = point_mapping\
                  [unit_identifier]\
                  [0x03]\
                  [starting_address]\
                  ['point']

                data_type = point_mapping\
                  [unit_identifier]\
                  [0x03]\
                  [starting_address]\
                  ['data_type']

                if point.readonly:
                    # attempted to write to a read only point.
                    reply_data = __make_error_response(data, 0x02)

                elif point.datatype_length_bytes == 2:
                    point.decode_datatype(
                      data=payload_data,
                      data_type=data_type,
                    )

                    # reply data is already correct.

                else:
                    # attempted to write 2 bytes to a 4 byte data type.
                    reply_data = __make_error_response(data, 0x02)

             except KeyError:
                # address is invalid, fail the command with a 'illegal data
                # address' error!
                reply_data = __make_error_response(data, 0x02)

        elif function_code = 0x15:
            # Force Multiple coils (0x reference address)
            try:
                byte_count = data[12]
                force_data = data[13:]

                # Change this to an assertion.
                if len(force_data) != int(payload_data / 8) + 1:
                     # the amount of force data supplied doesn't match up with
                     # the number of coils to force.
                     reply_data = __make_error_response(data, 0x02)

                else:
                    for i in range(0, payload_data):
                        point = point_mapping\
                          [unit_identifier]\
                          [0x01]\
                          [starting_address + i]\
                          ['point']

                        if point.readonly:
                            # Trying to write to a readonly point.
                            # throw an illegal data address (Code 02)
                            reply_data = __make_error_response(data, 0x02)
                            break

                      # all the points checked out. Proceed with the write.
                      for i in range(0, payload_data):
                          point = point_mapping\
                            [unit_identifier]\
                            [0x01]\
                            [starting_address + i]\
                            ['point']

                          byte_index = i / 8
                          bit_index = i % 8

                          if (force_data[byte_index] && (1 << bit_index)) > 0:
                              point.value = True
                          else
                              point.value = False

                  # reply data is already correct.

            except KeyError:
                # address is invalid, fail the command with a 'illegal data
                # address' error!
                reply_data = __make_error_response(data, 0x02)


        elif function_Code = 0x16:
            # Force Multiple holding registers (04 reference address - command
            # 03). Payload_data is the number of 16-bit registers that are set.

            preset_data = data[12:]
            try:
               if len(preset_Data) != int(payload_data*/ 2):
                     # the amount of force data supplied doesn't match up with
                     # the number of coils to force.
                     reply_data = __make_error_response(data, 0x02)
                else:
                    for i in range(0, payload_data):
                        point = point_mapping\
                          [unit_identifier]\
                          [0x03]\
                          [starting_address + i]\
                          ['point']

                        if point.readonly == True:
                            # Trying to write to a readonly point.
                            # throw an illegal data address (Code 02)
                            reply_data = __make_error_response(data, 0x02)
                            break

                    for i in range(0, payload_data):
                        point = point_mapping\
                          [unit_identifier]\
                          [0x03]\
                          [starting_address + i]\
                          ['point']

                        data_type = point_mapping\
                          [unit_identifier]\
                          [0x03]\
                          [starting_address + i]\
                          ['data_type']

                        index = 13+i*2
                        point.decode_datatype(
                          data=preset_data[index:index+1],
                          data_type=data_type,
                        )

             except KeyError:
                # address is invalid, fail the command with a 'illegal data
                # address' error!
                reply_data = __make_error_response(data, 0x02)

        else:
            # return an illegal function exception (Code 01)
            reply_data = __make_error_response(data, 0x01)

        # send the reply data back to the client
        writer.write(reply_data)
        await writer.drain()
        writer.close() # Not sure I should be doing this now.

    def get_bit_data(int address) -> bool:
        return bool_point[address].value

    # SupervisedThread manditory override.
    # Since this is a deamon that only responds to remote queries, and then
    # goes to sleep, the 'loop' isn't really required. On a DNP3 system, the
    # loop would be required as the DNP3 system is expected to provide
    # unsolicited updates on a running channel.
    def loop(self) -> 'float':
       return None

    # PointHandler override.
    # The modbus client can accept any points so log as they come with
    # the appropriate parameters to read/write them to the remote device.
    def point_name_valid(self, name: 'str') -> 'bool':
        return True

    # PointHandler override.
    # As no strict list of points is defined, it's encumbent on the config
    # file to ensure that the proper data direction is specified.
    def get_point_access(self, name: str) -> str:
        return None

    # PointHandler override
    def add_point(
      self,
      name: 'str',
      point: 'Point',
      access: 'str',
      extra_data: 'Dict[str, str]'
    ) -> None:
        super().add_point(
          name=name,
          point=point,
          access=access,
          extra_data=extra_data,
        )

        # Check the command field
        assert 'command' in extra_data, (
          "Point {} is missing a command type for Modbus client {}").format(
            name)
        assert extra_data['command'] in valid_commands, (
          "Point {} has an invalid command type of {} Modbus client {}").format(
            name,
            extra_data['command'],
            self.name,
          )

        # Check the address field
        assert 'address' in extra_data, (
          "Point {} is missing an address for Modbus client {}").format(
            name, self.name)

        assert extra_data['address'].isnumeric(), (
          "Point {} address is not numeric").format(extra_data['command'])

        assert extra_data['address'] >= 0 and extra_data['address'] <= 15, (
          "Point {} bit address is not between 0 and 15".format(
            extra_data['command'])
        )

        # Check the datatype field.
        assert 'datatype' in extra_data, (
          "Point {} is missing a datatype for Modbus client {}").format(
            name, self.name)

        # verify that the datatype entry is valid.
        assert extra_data['datatype'] in valid_data_types, (
          "Point {} does not have a valid datatype listed.").format(
            name, self.name)

        # Check the drop field.
        assert 'drop' in extra_data, (
          "Point {} is missing a drop number for Modbus client {}").format(
            name, self.name)

        assert extra_data['drop'].isnumeric(), (
          "Point {} command is not numeric").format(extra_data['command'])

        self.point_mapping \
          [extra_data['drop']] \
          [extra_data['command']] \
          [extra_data['address']] =
          {
            'point': point,
            'data_type': extra_data['datatype'],
          }
