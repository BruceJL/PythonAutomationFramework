import pytest
from pyAutomation.Devices.Modbus.ModbusServer import ModbusServer
from pyAutomation.Supervisory.PointManager import PointManager
import ruamel
import os


@pytest.fixture
def modbus_server():

    yml = ruamel.yaml.YAML(typ='safe', pure=True)
    yml.default_flow_style = False
    yml.indent(sequence=4, offset=2)
    cfg = None

    filename = os.path.join(
      os.path.dirname(__file__),
      './server_test_logic.yaml',
    )
    with open(filename, 'r') as ymlfile:
        cfg = yml.load(ymlfile)

    logger = 'testbench'

    server = ModbusServer(
        name="Testbench Modbus Server",
        logger=logger,
    )

    filename = os.path.join(
      os.path.dirname(__file__),
      "./test_points.yaml",
    )
    PointManager().load_points_from_yaml_file(filename)

    parameters = {
      'endpoint_address': 'localhost',
      'port': 10587,
      'socket_timeout': 100,
    }

    PointManager().assign_parameters(
        data = parameters,
        target = server,
    )

    PointManager().assign_points(
        data = cfg,
        point_handler = server,
        target_name = 'Modbus Server',
        interruptable = server,
    )

    return server


def test_cmd_01(modbus_server):
    ''' Test read COIL status command.
    Read 3 coils, starting at address 3. Note that only coils 3 and 5 are
    populated. The routine should return a 0 bit for the unpopulated coil.
    '''

    pd1 = PointManager().get_point_test('point_discrete_1')
    pd2 = PointManager().get_point_test('point_discrete_2')
    pd1.value = True
    pd2.value = True

    data_array = []

    # MBAP header
    # transaction ID = 0x12 0x34
    # protocol identifier = 0x00 0x00
    # length = 0x00 0x06
    # Unit identifier = 01
    data_array = [0x12, 0x34, 0x00, 0x00, 0x00, 0x06, 0x01]  # MBAP header

    # read 3 coils starting at address 03
    # command = 0x01
    # starting address = 0x00 0x03
    # coils to read = 0x00 0x03
    data_array += [0x01, 0x00, 0x03, 0x00, 0x03]

    data = bytearray(data_array)
    del data_array

    return_data = modbus_server.process_request(data)
    del data

    # return command 1, one byte, both discretes on
    expected_responce = [0x12, 0x34, 0x00, 0x00, 0x00, 0x04, 0x01]  # MBAP
    expected_responce += [0x01, 0x01, 0x05]
    expected_responce = bytearray(expected_responce)
    assert return_data == expected_responce


def test_cmd_05(modbus_server):
    ''' Test force COIL command.
    Force COIL 3 and verify that 3 changes and 5 doesn't.

    '''
    pd1 = PointManager().get_point_test('point_discrete_1')

def test_cmd_05_fail(modbus_server):
    ''' Test force COIL command.
    Force COIL 4 and verify that the server returns that the
    command is invalid.

    '''
    pd1 = PointManager().get_point_test('point_discrete_1')