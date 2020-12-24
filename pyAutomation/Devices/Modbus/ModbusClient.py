from datetime import datetime
from datetime import timedelta
import asyncio
from operator import attrgetter

from pyAutomation.DataObjects.PointAnalogReadOnlyAbstract import valid_data_types
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointHandler import PointHandler
from pyAutomation.Devices.Modbus.CommandModbus import \
  CommandModbus, makeCommandObjects

valid_commands = [
  'COIL',
  'DISCRETE',
  'HOLDING',
  'INPUT',
  ]

class ModbusCient(SupervisedThread, PointHandler):
    """Provides a mechanism to read and write to a single remote Modbus/TCP
    endpoint. If multiple endpoints are required, then multiple ModbusClients
    need to be instanciated."""

    parameters = {
      'endpoint_address': 'string',
      'endpoint_port': 'int',
      'socket_timeout': 'int',
    }

    # data types are used to interpret the data in HOLDING (03) or INPUT (04)
    # registers. COIL (01) and DISCRETE (02) registers are always bits.

    _valid_data_types = 'sub-bit' + valid_data_types # type: List

    def __init__(self, name, logger):
        self.state = "DISCONNECTED" # type: str
        self.sock = None
        self.endpoint_address = ""
        self.endpoint_port = 0
        self.min_sleep_time = timedelta(milliseconds=10)
        self.period = None
        self.point_data = [] # type: List[Dict[str, Any]]
        self.modbus_commands = [] # type: List[ModbusCommand]

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
        allows the Modbus client to get the points form the server using a minimum
        number of requests"""

        self.logger.debug("Entering function")
        self.modbus_commands = [] # type: List[ModbusCommand]

        dicts = dict[str, List[Any]]
        for point in self.point_data:
            key = point['drop'] + '-' + point['command']
            if key not in dicts:
                dicts[key] = []
            dicts[key].append(point)

            # Become an observer to any read-only point.
            if point.readonly:
                point.add_observer(self.name, self.interrupt)

        for group in dicts.values():
            cmds = makeCommandObjects(group)
            for cmd in cmds:
                self.modbus_commands.append(cmd)


    # SupervisedThread manditory override.
    def loop(self) -> 'float':        
        data = bytearray()
        active_modbus_command = None

        # Since python has a GIL, do the connect asyncronously

        reader, writer = await asyncio.open_connection(
          self.endpoint_address,
          self.endpoint_port,
        )

        while True:
            # Deal with the read only (from the perspective of this program) 
            # points. Make write commands and fire them off to the remote end. 
            # Look for ro points and build outgoing commands on an as-needed
            # basis.
            # N.B. read only points are still read from the remote end and sent
            # as 'requested values' to the owning routine when changes are
            # noticed.

            # locate the point in the point_data array and build a commands 
            # to write that data out to the remote end.
            # we expect that the point that initated the interrupt will have
            # its name included in the deque.
            while self.interrupt_request_deque:
                write_item = self.interrupt_request_deque.pop()
                for modbus_command in self.modbus_commands:
                    for (point for point in modbus_command.points if point.name == write_item):                  
                        write_command = CommandModbus(
                          points = {'point': point},
                          command = point.command,
                          write = True,
                          drop = point.drop,
                        )

            # run the business as usual read commands.
            next_update = datetime.max
            active_modbus_command = None
            for modbus_command in self.modbus_commands:
                if modbus_command.next_update < next_update:
                    next_update = modbus_command.next_update
                    active_modbus_command = modbus_command

            if next_update < datetime.now():
                yield next_update
                continue # restart the while loop to preseve the stream.

            # This deals with the read/write points that are owned by this
            # process.
            data = active_modbus_command.command_chars
            return_data =  asyncio.run(self.do_io(data))
            active_modbus_command.processReply(return_data)

    async def do_io(data : 'bytearray') -> 'bytearray':
        """ Run the I/O routine asyncronously."""
        # Send the modbus query
        writer.write(data)
        await writer.drain()

        # Wait for the data to be returned.
        return_data = await reader.read(3)

        # Process the returned data
        message_length = data[2]
        return_data.append(await reader.read(message_length))
        return return_data

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

        # Check the datatype field
        assert 'datatype' in extra_data, (
          "Point {} is missing a datatype for Modbus client {}").format(
            name, self.name)

        # Check the drop field
        assert 'drop' in extra_data, (
          "Point {} is missing a drop number for Modbus client {}").format(
            name, self.name)

        assert extra_data['drop'].isnumeric(), (
          "Point {} command is not numeric").format(extra_data['command']) 

        self.point_data.append({
          'point': point,
          'command': extra_data['command'],
          'address': extra_data['address'],
          'datatype': extra_data['datatype'],
          'drop': extra_data['drop'],
        })
