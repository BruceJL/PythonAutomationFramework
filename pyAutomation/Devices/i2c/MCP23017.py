'''
Created on Apr 14, 2016
@author: Bruce
http://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf
'''
import traceback
import logging

from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.PointReadOnly import PointReadOnly
from pyAutomation.DataObjects.Alarm import Alarm

from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler

from .linuxi2c3 import IIC

ADDRESS = 0x20
REG_A_DIRECTION = 0x00  # IODIRA
REG_B_DIRECTION = 0x01  # IODIRB
REG_A_POLARITY = 0x02  # IPOLA
REG_B_POLARITY = 0x03  # IPOLB
REG_A_INTERRUPT_ENABLE = 0x04  # GPINTENA
REG_B_INTERRUPT_ENABLE = 0x05  # GPINTENB
REG_A_DEFAULT_VALUE = 0x06  # DEFVALA
REG_B_DEFAULT_VALUE = 0x07  # DEFVALB
REG_A_INTERRUPT_CONTROL = 0x08  # INCONA
REG_B_INTERRUPT_CONTROL = 0x09  # INCONB
IOCON = 0x0A
IOCON_B = 0x0B
REG_A_PULL_UP_EN = 0x0C  # GPPUA
REG_B_PULL_UP_EN = 0x0D  # GPPUB
REG_A_INTERRUPT_FLAG = 0x0E  # INTFA RO
REG_B_INTERRUPT_FLAG = 0x0F  # INTFB RO
REG_A_INTERRUPT_CAPTURED = 0x10  # INTCAPA RO
REG_B_INTERRUPT_CAPTURED = 0x11  # INTCAPB RO
REG_A = 0x12  # GPIOA
REG_B = 0x13  # GPIOB
REG_A_OUTPUT_LATCH = 0x14  # OLATA
REG_B_OUTPUT_LATCH = 0x15  # OLATB


# helper function
def _append_if_point_ro(p, point_list):
    if p is not None:
        if  type(p) == "PointReadOnly":
            point_list.append(p)


class MCP23017(i2cPrototype, PointHandler):
    '''
    Microchip MCP23017 Port expander
    Using IOCON.BANK=0
    '''

    _points_list = {
      'port_A0':  {'type': 'PointDiscrete'},
      'port_A1':  {'type': 'PointDiscrete'},
      'port_A2':  {'type': 'PointDiscrete'},
      'port_A3':  {'type': 'PointDiscrete'},
      'port_A4':  {'type': 'PointDiscrete'},
      'port_A5':  {'type': 'PointDiscrete'},
      'port_A6':  {'type': 'PointDiscrete'},
      'port_A7':  {'type': 'PointDiscrete'},
      'port_B0':  {'type': 'PointDiscrete'},
      'port_B1':  {'type': 'PointDiscrete'},
      'port_B2':  {'type': 'PointDiscrete'},
      'port_B3':  {'type': 'PointDiscrete'},
      'port_B4':  {'type': 'PointDiscrete'},
      'port_B5':  {'type': 'PointDiscrete'},
      'port_B6':  {'type': 'PointDiscrete'},
      'port_B7':  {'type': 'PointDiscrete'},

      'alarm_comm_fail':  {'type': 'Alarm', 'access': 'rw'},
    }

    parameters = {}

    def __init__(self, name: str, bus: int, logger: str) -> None:
        self.bus = bus
        self.port_b = 0x00
        self.port_b_cfg = 0xFF  # All ports read by default
        self.port_a = 0x00
        self.port_a_cfg = 0xFF  # All ports read by default
        self.dev = None  # type: IIC

        self.alarm_comm_fail = None

        self.port_A0 = None
        self.port_A1 = None
        self.port_A2 = None
        self.port_A3 = None
        self.port_A4 = None
        self.port_A5 = None
        self.port_A6 = None
        self.port_A7 = None

        self.port_B0 = None
        self.port_B1 = None
        self.port_B2 = None
        self.port_B3 = None
        self.port_B4 = None
        self.port_B5 = None
        self.port_B6 = None
        self.port_B7 = None

        super().__init__(
          name=name,
          logger=logger)

    @property
    def interrupt_points(self):
        point_list = []
        _append_if_point_ro(self.port_A0, point_list)
        _append_if_point_ro(self.port_A1, point_list)
        _append_if_point_ro(self.port_A2, point_list)
        _append_if_point_ro(self.port_A3, point_list)
        _append_if_point_ro(self.port_A4, point_list)
        _append_if_point_ro(self.port_A5, point_list)
        _append_if_point_ro(self.port_A6, point_list)
        _append_if_point_ro(self.port_A7, point_list)

        _append_if_point_ro(self.port_B0, point_list)
        _append_if_point_ro(self.port_B1, point_list)
        _append_if_point_ro(self.port_B2, point_list)
        _append_if_point_ro(self.port_B3, point_list)
        _append_if_point_ro(self.port_B4, point_list)
        _append_if_point_ro(self.port_B5, point_list)
        _append_if_point_ro(self.port_B6, point_list)
        _append_if_point_ro(self.port_B7, point_list)
        return point_list

    def setup(self):
        self.logger.debug("Entering Function")

        # Do a sanity check
        assert self.alarm_comm_fail is not None,\
          "Communications alarm (alarm_comm_Fail) is not configured."

        try:
            self.dev = IIC(ADDRESS, self.bus)

            # Read the IOCON register
            [iocon] = self.dev.i2c([IOCON], 1, 0.01)
            self.logger.debug("IOCON is " + hex(iocon))

            # IOCON DETAIL
            # bit 7 - BANK control register mapping
            # bit 6 - MIRROR - Internally connects Port pins.
            # bit 5 - SEQOP sequential operation automatically increments
            #         address pointer
            # bit 4 - DISSLW Controls SDA slew rate
            # bit 3 - HAEN hardward address enable
            # bit 2 - ODR open drain. enables INT pin open drain configuration
            # bit 1 - INTPOL sets the polarity of the interrupt pin
            # bit 0 - unused

            # Configure PORT A and B (1 = input, 0 = output) (IOBANK is 0 so
            # writes are sequential)
            self.logger.debug("Setting REG_A DIRECTION to %s",
              hex(self.port_a_cfg))
            self.logger.debug("Setting REG_B_DIRECTION to %s",
              hex(self.port_b_cfg))

            b = [REG_A_DIRECTION, self.port_a_cfg, self.port_b_cfg]
            self.logger.debug("writing " + str(b) + " to device")
            self.dev.i2c(b, 0, 0.01)

            [port_a_cfg_as_found, port_b_cfg_as_found] =\
              self.dev.i2c([REG_A_DIRECTION], 2, 0.01)

            self.logger.debug("REG_A_DIRECTION is now %s",
              hex(port_a_cfg_as_found))
            self.logger.debug("REG_B_DIRECTION is now %s",
              hex(port_b_cfg_as_found))

            if (port_a_cfg_as_found == self.port_a_cfg
                    and port_b_cfg_as_found == self.port_b_cfg):
                self.is_setup = True
                self.logger.debug("Setup successful.")
            else:
                self.logger.debug("Setup failed.")

        except OSError as e:
            self.is_setup = False
            self.logger.error("setup I/O error: %s", str(e))

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.is_setup = False

        finally:
            if self.dev is not None:
                self.dev.close()
            return self.is_setup

    def read_data(self):
        self.logger.debug("Entering function")

        def _write_point(point, byte, index):
            if p is not None:
                if type(point) is PointDiscrete:
                    b = (byte >> index) & 0x01
                    point.value = b

        try:
            self.dev = IIC(ADDRESS, self.bus)
            [self.port_a, self.port_b] = self.dev.i2c([REG_A], 2, 0.01)

            _write_point(self.port_A0, self.port_a, 0)
            _write_point(self.port_A1, self.port_a, 1)
            _write_point(self.port_A2, self.port_a, 2)
            _write_point(self.port_A3, self.port_a, 3)
            _write_point(self.port_A4, self.port_a, 4)
            _write_point(self.port_A5, self.port_a, 5)
            _write_point(self.port_A6, self.port_a, 6)
            _write_point(self.port_A7, self.port_a, 7)

            _write_point(self.port_B0, self.port_b, 0)
            _write_point(self.port_B1, self.port_b, 1)
            _write_point(self.port_B2, self.port_b, 2)
            _write_point(self.port_B3, self.port_b, 3)
            _write_point(self.port_B4, self.port_b, 4)
            _write_point(self.port_B5, self.port_b, 5)
            _write_point(self.port_B6, self.port_b, 6)
            _write_point(self.port_B7, self.port_b, 7)

            self.logger.debug(
              "Read successful. next read at: %s", str(self.next_update))

            self.alarm_comm_fail.input = False

        except OSError as e:
            self.alarm_com_fail.input = True
            self.logger.error("read I/O fault:" + str(e))

        except Exception as e:
            self.logger.error(traceback.format_exc())

        finally:
            def _set_bad_quality(point):
                if point is not None and isinstance(point, PointDiscrete):
                    point.quality = False

            _set_bad_quality(self.port_A0)
            _set_bad_quality(self.port_A1)
            _set_bad_quality(self.port_A2)
            _set_bad_quality(self.port_A3)
            _set_bad_quality(self.port_A4)
            _set_bad_quality(self.port_A5)
            _set_bad_quality(self.port_A6)
            _set_bad_quality(self.port_A7)
            _set_bad_quality(self.port_B0)
            _set_bad_quality(self.port_B1)
            _set_bad_quality(self.port_B2)
            _set_bad_quality(self.port_B3)
            _set_bad_quality(self.port_B4)
            _set_bad_quality(self.port_B5)
            _set_bad_quality(self.port_B6)
            _set_bad_quality(self.port_B7)

            self.dev.close()

    def data_updated(self, name):
        self._has_write_data = True
        self.logger.debug("Got Interrupt from %s", name)

    def write_data(self):
        # write data
        self.logger.debug("Entering Function")

        def _update_value(point, byte, index):
            # self.logger.debug("Entering Function, byte is " + str(byte))
            if type(point) is PointReadOnly:
                if 0 == point.value:
                    byte = byte & ~(0x01 << index)
                else:
                    byte = byte | (0x01 << index)

            # self.logger.debug("returning " + hex(byte))
            return byte

        try:
            self.dev = IIC(ADDRESS, self.bus)
            [self.port_a, self.port_b] = self.dev.i2c([REG_A], 2, 0.01)

            self.port_a = _update_value(self.port_A0, self.port_a, 0)
            self.port_a = _update_value(self.port_A1, self.port_a, 1)
            self.port_a = _update_value(self.port_A2, self.port_a, 2)
            self.port_a = _update_value(self.port_A3, self.port_a, 3)
            self.port_a = _update_value(self.port_A4, self.port_a, 4)
            self.port_a = _update_value(self.port_A5, self.port_a, 5)
            self.port_a = _update_value(self.port_A6, self.port_a, 6)
            self.port_a = _update_value(self.port_A7, self.port_a, 7)

            self.port_b = _update_value(self.port_B0, self.port_b, 0)
            self.port_b = _update_value(self.port_B1, self.port_b, 1)
            self.port_b = _update_value(self.port_B2, self.port_b, 2)
            self.port_b = _update_value(self.port_B3, self.port_b, 3)
            self.port_b = _update_value(self.port_B4, self.port_b, 4)
            self.port_b = _update_value(self.port_B5, self.port_b, 5)
            self.port_b = _update_value(self.port_B6, self.port_b, 6)
            self.port_b = _update_value(self.port_B7, self.port_b, 7)

            self.logger.debug("writing %s to port A", hex(self.port_a))
            self.logger.debug("writing %s to port B", hex(self.port_b))

            self.dev.i2c([REG_A, self.port_a, self.port_b], 0, 0.01)

            # mask out the input bits so we don't get false positives.
            masked_port_a_expected = ~self.port_a_cfg & self.port_a
            masked_port_b_expected = ~self.port_b_cfg & self.port_b

            [self.port_a, self.port_b] = self.dev.i2c([REG_A], 2, 0.01)

            masked_port_a_actual = ~self.port_a_cfg & self.port_a
            masked_port_b_actual = ~self.port_b_cfg & self.port_b

            self.logger.debug("port_a is now %s", hex(self.port_a))
            self.logger.debug("port_b is now %s", hex(self.port_b))

            if masked_port_a_expected != masked_port_a_actual \
                    or masked_port_b_expected != masked_port_b_actual:
                self.logger.error("data write was unsuccessful")

                if masked_port_a_expected != masked_port_a_actual:
                    self.logger.error("port A is: {} should be {}".format(
                      hex(masked_port_a_actual),
                      hex(masked_port_a_expected)
                    ))

                if masked_port_b_expected != masked_port_b_actual:
                    self.logger.error(
                      "port B is: %s should be %s",
                      hex(masked_port_b_actual),
                      hex(masked_port_b_expected)
                    )
            else:
                self._has_write_data = False
                self.logger.debug("Write successful")

        except OSError as e:
            self.logger.error("write I/O fault: %s", str(e))
        except Exception as e:
            self.logger.error(traceback.format_exc())
        finally:
            if self.dev is not None:
                self.dev.close()
            return self.is_setup

    def _setup_port(self, point, config_byte, index):
        if type(point) is PointDiscrete or point is None:
            # This point is written by the driver and is therefore an input.

            # write a 1 t othe configration register bit
            b = 0x01 << index
            config_byte = config_byte | b

            if point is not None:
                self.logger.debug(
                  "Setting point %s (%s) bit to 1 by or'ing with %s",
                  point.name, str(index), hex(b))

        elif type(point) is PointReadOnly:
            # This point is read only by the driver and therefor an output.
            # write a zero to the configuration register bit.
            b = ~(0x01 << index)
            config_byte = config_byte & b
            self.logger.debug(
              "Setting point %s (%s) bit to 0 by anding with %s",
              point.name,  str(index),  hex(b))

            # add an observer to the point
            point.add_observer(self.name, self.data_updated)
        else:
            raise ValueError("Invalid object type of " + str(type(point)) + " supplied.")

        self.logger.debug("config byte is now %s", hex(config_byte))
        return config_byte

    def config(self):
        self.device_points = [
          self.port_A0,
          self.port_A1,
          self.port_A2,
          self.port_A3,
          self.port_A4,
          self.port_A5,
          self.port_A6,
          self.port_A7,
          self.port_B0,
          self.port_B1,
          self.port_B2,
          self.port_B3,
          self.port_B4,
          self.port_B5,
          self.port_B6,
          self.port_B7]

        self.port_a_cfg = self._setup_port(self.port_A0, self.port_a_cfg, 0)
        self.port_a_cfg = self._setup_port(self.port_A1, self.port_a_cfg, 1)
        self.port_a_cfg = self._setup_port(self.port_A2, self.port_a_cfg, 2)
        self.port_a_cfg = self._setup_port(self.port_A3, self.port_a_cfg, 3)
        self.port_a_cfg = self._setup_port(self.port_A4, self.port_a_cfg, 4)
        self.port_a_cfg = self._setup_port(self.port_A5, self.port_a_cfg, 5)
        self.port_a_cfg = self._setup_port(self.port_A6, self.port_a_cfg, 6)
        self.port_a_cfg = self._setup_port(self.port_A7, self.port_a_cfg, 7)

        self.port_b_cfg = self._setup_port(self.port_B0, self.port_b_cfg, 0)
        self.port_b_cfg = self._setup_port(self.port_B1, self.port_b_cfg, 1)
        self.port_b_cfg = self._setup_port(self.port_B2, self.port_b_cfg, 2)
        self.port_b_cfg = self._setup_port(self.port_B3, self.port_b_cfg, 3)
        self.port_b_cfg = self._setup_port(self.port_B4, self.port_b_cfg, 4)
        self.port_b_cfg = self._setup_port(self.port_B5, self.port_b_cfg, 5)
        self.port_b_cfg = self._setup_port(self.port_B6, self.port_b_cfg, 6)
        self.port_b_cfg = self._setup_port(self.port_B7, self.port_b_cfg, 7)
