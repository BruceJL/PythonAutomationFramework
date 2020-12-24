from typing import TYPE_CHECKING, List
from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler
from .linuxi2c3 import IIC

if TYPE_CHECKING:
    from pyAutomation.DataObjects.PointAnalog import PointAnalog
    from pyAutomation.DataObjects.PointAbstract import PointAbstract
    from pyAutomation.DataObjects.PointDiscrete import PointDiscrete

# https://www.silabs.com/documents/public/data-sheets/Si7020-A20.pdf
# The information below is lifted directly from the datasheet
ADDRESS = 0x40

CMD_READ_HUMIDITY_HOLD = 0xE5
CMD_READ_HUMIDITY_NO_HOLD = 0xF5
CMD_READ_TEMPERATURE_HOLD = 0xE3
CMD_READ_TEMPERATURE_NO_HOLD = 0xF3
CMD_READ_PREVIOUS_TEMPERATURE = 0xE0
CMD_RESET = 0xFE
CMD_WRITE_USER_REGISTER = 0xE6
CMD_READ_USER_REGISTER = 0xE7
CMD_WRITE_HEATER_CTRL = 0x51
CMD_READ_HEATER_CTRL = 0x11


def format_debug_data(s, data) -> str:
    return s + ''.join('{:02x} '.format(x) for x in data)


# SiLabs Si7020-A20 temperature/humidity sensor
class SI7020(i2cPrototype, PointHandler):
    logger = None

    _points_list = {
      'point_humidity': {'type': 'PointAnalog',   'access': 'rw'},
      'point_temperature': {'type': 'PointAnalog',   'access': 'rw'},
      'point_run_heater': {'type': 'PointDiscrete', 'access': 'rw'},

      'alarm_comm_fail': {'type': "Alarm", 'access': 'rw'},
      'alarm_vdd_low': {'type': "Alarm", 'access': 'rw'},
    }

    parameters = {}

    def __init__(self, name: str, bus: int, logger: str) -> None:
        self.bus = bus  # type: int
        self.point_temperature = None  # type: PointAnalog
        self.point_humidity = None     # type: PointAnalog
        self.point_run_heater = None   # type: PointDiscrete
        self.is_setup = False          # type: bool
        self.device_points = None      # type: List[PointAbstract]
        self.dev = None                # type: IIC

        self.alarm_comm_fail = None
        self.alarm_vdd_low = None

        super().__init__(
          name=name,
          logger=logger)

    def reset(self):
        self._setup()

    @property
    def has_write_data(self) -> bool:
        return self.point_run_heater.request_value is not None

    def write_data(self):
        data = [CMD_READ_USER_REGISTER]
        b = self.dev.i2c(data, 1, 0.01)

        if self.point_run_heater.request_value:
            b = b | 0x04
        elif not self.point_run_heater.request_value:
            b = b & ~0x04

        data = [CMD_WRITE_USER_REGISTER, b]

    def setup(self):
        # Do a sanity check
        assert self.alarm_comm_fail is not None,\
          "Communications alarm (alarm_comm_fail) is not configured."
        assert self.alarm_vdd_low is not None,\
          "Low voltage (alarm_vdd_low) is not configured."

        try:
            self.dev = IIC(ADDRESS, self.bus)

            # Set the heater current draw to 15.24 mA
            data = [CMD_WRITE_HEATER_CTRL, 0x02]
            self.dev.i2c(data, 1, 0.01)

            # Verify heater current draw value
            data = [CMD_READ_HEATER_CTRL]
            self.logger.debug(
              format_debug_data("Reading heater control byte: ", data)
            )

            b = self.dev.i2c(data, 1, 0.01)
            self.logger.debug(format_debug_data("device returned: ", b))

            # Read the control register
            data = [CMD_READ_USER_REGISTER]
            self.logger.debug(
              format_debug_data("Reading user control byte: ", data)
            )

            b = self.dev.i2c(data, 1, 0.01)
            self.logger.debug(
              format_debug_data("device returned: ", b)
            )

            # Write to the control register set the measurement resultion to 12
            # bit (RH) and 15 bit (temperature)
            b[0] = 0x81 | b[0]

            # disable the on chip heater
            b[0] = ~0x04 & b[0]
            self.logger.debug(format_debug_data("Writing control byte: ", data))
            data = [CMD_WRITE_USER_REGISTER, b[0]]
            self.dev.i2c(data, 1, 0.01)

            self.is_setup = True
        except OSError as e:
            self.logger.error("setup I/O error %s", str(e))

        finally:
            if self.dev is not None:
                self.dev.close()
            return self.is_setup

    def read_data(self):
        if self.alarm_comm_fail.active:
            self.point_temperature.quality = False
            self.point_humidity.quality = False
            self.point_run_heater.quality = False

        try:
            self.dev = IIC(ADDRESS, self.bus)

            # get the humidity reading
            data = [CMD_READ_HUMIDITY_HOLD]
            self.logger.debug(
              format_debug_data("Reading humidity - Sending: ", data)
            )
            b = self.dev.i2c(data, 3, 0.01)
            self.logger.debug(
              format_debug_data("device returned: ", b)
            )
            i = b[0] << 8 | b[1]
            self.point_humidity.value = 125 * i / 65536 - 6

            # Get the temperature reading
            data = [CMD_READ_PREVIOUS_TEMPERATURE]
            self.logger.debug(
              format_debug_data("Reading temperature - Sending: ", data)
            )

            b = self.dev.i2c(data, 2, 0.01)
            self.logger.debug(
              format_debug_data("device returned: ", b)
            )
            i = b[0] << 8 | b[1]
            self.point_temperature.value = 175.72 * i / 65536 - 46.85

            # Get the user register
            data = [CMD_READ_USER_REGISTER]
            self.logger.debug(
              format_debug_data("Reading User register = Sending: ", data)
            )

            b = self.dev.i2c(data, 1, 0.01)
            self.logger.debug(format_debug_data("device returned: ", b))
            self.point_run_heater.value = b[0] & 0x04
            if self.point_run_heater.value:
                self.point_temperature.quality = False
                self.point_humidity.quality = False

            if b[0] & 0x40:
                self.alarm_vdd_low.input = True
            else:
                self.alarm_vdd_low.input = False

            self.alarm_comm_fail.input = False

            self.logger.debug(
              "temperature next read: %s",
              str(self.point_temperature.next_update)
            )

            self.logger.debug(
              "humidity next read: %s",
              str(self.point_humidity.next_update)
            )

            self.logger.debug(
              "run heater next read: %s",
              str(self.point_run_heater  .next_update)
            )

            self.logger.debug(
              "SI7020 successfully read. Next read at: %s ",
              str(self.next_update)
            )

        except OSError as e:
            self.logger.error("read I/O error " + str(e))
            self.alarm_comm_fail.input = False
        finally:
            if self.alarm_comm_fail.active:
                self.point_temperature.quality = False
                self.point_humidity.quality = False

    def config(self):
        self.device_points = [
            self.point_temperature,
            self.point_humidity,
            self.point_run_heater]
