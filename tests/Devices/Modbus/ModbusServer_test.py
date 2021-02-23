import pytest
from pyAutomation.Devices.Modbus.ModbusServer import ModbusServer
from pyAutomation.PoinManager import PointManager
import logging
import ruamel


@pytest.fixture
def modbus_server():

    yml = ruamel.yaml.YAML(typ='safe', pure=True)
    yml.default_flow_style = False
    yml.indent(sequence=4, offset=2)
    cfg = None

    with open('server_test_logic.yaml', 'r') as ymlfile:
        cfg = yml.load(ymlfile)

    logger = logging.getLogger('testbench')

    server = ModbusServer(
        name="Testbench Modbus Server",
        logger=logger,
    )

    PointManager().load_points_from_yaml_file("./test_points.yaml")

    parameters = {
      'endpoint_address': 'localhost',
      'port': 10587,
      'socket_timeout': 100,
    }

    PointManager().assign_parameters(
        data = parameters,
        target = server,
    )

    PointManager().assign_point(
        data = cfg['points'],
        point_handler = server,
        target_name = 'Modbus Server',
        interruptable = server,
    )

    return server


def test_cmd_01(modbus_server):
    pd1 = PointManager().__get_point_rw('point_discrete_1')
    pd2 = PointManager().__get_point_rw('point_discrete_2')
    pd1.value = True
    pd2.value = True

    # read 2 coils starting at address 03
    data_array = [0x01, 0x00, 0x03, 0x00, 0x02, ]

    data = bytearray(data_array)
    return_data = modbus_server.process_request(data)

    # return command 1, one byte, both discretes on
    assert return_data == [0x01, 0x01, 0x03]
