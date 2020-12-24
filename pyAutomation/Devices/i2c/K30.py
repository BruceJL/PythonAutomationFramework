import traceback
from .linuxi2c3 import IIC
from .i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler


REG_CO2 = 0x08
CMD_READ_RAM_TWO_BYTES = 0x22
CMD_WRITE_RAM_TWO_BYTES = 0x12
CMD_BACKGROUND_CALIBRATION = 0x7C06
ADDRESS = 0x68


def _validate_checksum(data):
    checksum = 0
    for i in range(0, len(data) - 1):
        checksum += data[i]
    checksum %= 256
    return checksum == data[len(data) - 1]


def _create_check_sum(data):
    checksum = 0
    for i in range(0, len(data)):
        checksum += data[i]
    checksum %= 256
    return checksum


class K30(i2cPrototype, PointHandler):

    _points_list = {
      'point_co2_level': {'type': 'PointAnalog', 'access': 'rw'},
      'point_calibration_running': {'type': 'PointDiscrete', 'access': 'rw'},
      'point_abc_period': {'type': 'PointAnalog', 'access': 'rw'},

      'alarm_comm_fail': {'type': "Alarm", 'access': 'rw'},
    }

    parameters = {}

    def __init__(self, name: str, bus: int, logger: str):

        self.bus = bus
        self.is_setup = True
        self.read_state = 0

        self.dev = None

        self.point_co2_level = None
        self.point_calibration_running = None
        self.point_abc_period = None
        self.consecutive_faults = 0
        self.alarm_comm_fail = None

        super().__init__(
          name=name,
          logger=logger)

    @staticmethod
    def get_remaining_states():
        return 1

    @property
    def has_write_data(self):
        return (
          self.point_calibration_running.request_value is not None
          or self.point_abc_period.request_value is not None
        )

    def setup(self):
        # Do a sanity check
        assert self.point_co2_level is not None,\
          "CO2 level point is not configured."

        assert self.point_abc_period is not None,\
          "ABC period point is not configured."

        assert self.alarm_comm_fail is not None,\
          "Communications alarm is not configured."

        assert self.point_calibration_running is not None,\
          "CO2 calibration running point is not configured."

        self.is_setup = True
        return self.is_setup

    def read_data(self):
        self.logger.debug("Entering function.")
        if self.read_state == 0:
            retry = self.read_co2_levels()
            if not retry:
                self.read_state = 1
        elif self.read_state == 1:
            retry = self.read_abc_period()
            if not retry:
                self.read_state = 0
        self.logger.debug("Leaving function.")
        return 0

    def read_co2_levels(self):
        try:
            # Open up the IIC channel
            self.dev = IIC(ADDRESS, self.bus)

            # Read from RAM (2) three bytes (3) starting at 0x0007, checksum is
            # 0x2A) Get 5 bytes back, 10ms delay
            # between write and read.
            b = self.dev.i2c([0x23, 0x00, 0x07, 0x2A], 5, 0.01)

            if _validate_checksum(b):
                self.meter_control_byte = b[1]
                self.point_calibration_running.value = \
                  (self.meter_control_byte and 0x02) > 0
                c = [b[2], b[3]]
                self.point_co2_level.value = int.from_bytes(c, byteorder='big')
                self.alarm_comm_fail.input = False
            else:
                self.alarm_comm_fail.input = True
                self.logger.debug("K30 bad checksum.")
            self.consecutive_faults = 0

        except OSError as e:
            self.alarm_comm_fail.input = True
            self.consecutive_faults += 1
            self.logger.info(
              "read I/O fault " + str(self.consecutive_faults) + str(e)
            )

        except Exception as e:
            self.logger.error(traceback.format_exc())

        finally:
            if self.alarm_comm_fail.active:
                self.point_co2_level.quality = False
                self.point_calibration_running.quality = False

            if self.dev is not None:
                self.dev.close()
        return 0

    def read_abc_period(self):
        retry = False
        try:
            # Open up the IIC channel
            self.dev = IIC(ADDRESS, self.bus)
            # Read from RAM (2), two bytes (2) starting at 0x40, checksum is
            # 0x62) Get 5 bytes back, 10ms delay between write and read.
            b = self.dev.i2c([0x22, 0x00, 0x40, 0x62], 4, 0.05)
            if _validate_checksum(b):
                c = [b[1], b[2]]
                self.point_abc_period.value = int.from_bytes(c, byteorder='big')
                self.alarm_comm_fail.input = False
            else:
                self.point_abc_period.quality = False
                self.alarm_comm_fail.input = True
                retry = True

        except OSError as e:
            self.logger.error("I/O error " + str(e))
            self.point_abc_period.quality = False
            retry = True
            self.alarm_comm_fail.input = True

        except Exception as e:
            self.logger.error(traceback.format_exc())

        finally:
            if self.dev is not None:
                self.dev.close()
        return retry

    def write_data(self):
        self.logger.debug("Entering function.")
        if self.point_calibration_running.request_value:
            self.write_abc_request()
        if self.point_abc_period.request_value:
            self.write_abc_period()
        self.logger.debug("Leaving function.")

    def write_abc_request(self):
        # Baseline calibration request
        if not self.point_calibration_running.value:
            try:
                self.logger.debug("Attempting to write K30 baseline "
                  "calibration request")

                self.dev = IIC(ADDRESS, self.bus)

                # self.dev.i2c([CMD_WRITE_TWO_BYTES (0x12), MEMORY_LOCATION
                # (0x00, 0x67), CMD_BACKGROUND_CALIBRATION (0x7C 0x06),
                # Checksum],5, 0.01)
                b = self.dev.i2c([0x12, 0x00, 0x67, 0x7C, 0x06, 0xFB], 2, 0.05)
                if _validate_checksum(b):
                    # Was the write successful? see manual page 30.
                    if b[0] == 0x11:
                        self.point_calibration_running.request_value = None
                        self.logger.debug("K30 command successful.")
                    else:
                        self.logger.debug("K30 command unsuccessful.")
                else:
                    self.logger.debug("K30 write bad checksum.")
            except OSError as e:
                self.logger.info("I/O fault " + str(e))
            finally:
                self.dev.close()
        else:
            self.point_calibration_running.request_value = False

    def write_abc_period(self):
        if self.point_abc_period.request_value is not None:
            try:
                self.logger.debug("Attempting to write K30 ABC period")
                self.dev = IIC(ADDRESS, self.bus)
                # self.dev.i2c([CMD_WRITE_TWO_BYTES (0x12), MEMORY_LOCATION
                # (0x00, 0x40), value, Checksum],5, 0.01)
                b = [0x12, 0x00, 0x40]
                b += bytearray(int(
                  self.point_abc_period.request_value).to_bytes(
                    2,
                    byteorder='big',
                  )
                )

                b += bytearray(
                  create_check_sum(b).to_bytes(1, byteorder='big')
                )

                self.logger.debug("byte array:" + str(b))
                b = self.dev.i2c(b, 2, 0.01)
                if _validate_checksum(b):
                    # Was the write successful? see manual page 30.
                    if b[0] == 0x11:
                        self.logger.info(
                          "K30 write ABC Period of %s successful."
                        )
                        self.point_abc_period.request_value = None
                        # Queue a read.
                    else:
                        self.logger.info("K30 write ABC Period command "
                          "unsuccessful.")
                else:
                    self.logger.debug("K30 write ABC Period bad checksum.")

            except OSError as e:
                self.logger.info("I/O fault " + str(e))

            except Exception as e:
                self.logger.error(traceback.format_exc())

            finally:
                self.dev.close()

    def config(self):
        self.device_points = [
          self.point_co2_level,
          self.point_calibration_running,
          self.point_abc_period,
        ]
