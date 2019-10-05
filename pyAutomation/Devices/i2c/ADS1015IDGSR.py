'''
ADS1015IDGSR driver
datasheet: http://www.ti.com/lit/ds/symlink/ads1013.pdf
Created on Apr 14, 2016

@author: Bruce
'''


import traceback
import logging
from typing import TYPE_CHECKING
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler
from .linuxi2c3 import IIC

if TYPE_CHECKING:
    from pyAutomation.DataObjects.PointAnalogScaled import PointAnalogScaled

REG_CONVERSION = 0x00
REG_CONFIG = 0x01

#
# DATA_SETUP
#
# Bit 15 One-shot
# 1 = begin a single conversion
# 0 = stay in power down mode
#
# Bit 14-12 Mux setting
# 000 = AIN0 - AIN1
# 001 = AIN0 - AIN3
# 010 = AIN1 - AIN3
# 011 = AIN2 - AIN3
# 100 = AIN0 - GND
# 101 = AIN1 - GND
# 110 = AIN2 - GND
# 111 = AIN3 - GND

# Bits 11-9 Programmable Gain amplifier
# 000 = FS = +/-6.144V
# 001 = FS = +/-4.096V
# 010 = FS = +/-2.048V
# 011 = FS = +/-1.024V
# 100 = FS = +/-0.512V
# 101 = FS = +/-0.256V
# 110 = FS = +/-0.256V
# 111 = FS = +/-0.256V

# Bit 8 Device operating mode
# 0 = continious conversion mode
# 1 = Power down single shot mode

# Bits 7-5 Data rate
# 000 = 128 Samples/s
# 001 = 250 Samples/s
# 010 = 490 Samples/s
# 011 = 920 Samples/s
# 100 = 1600 Samples/s
# 101 = 2400 Samples/s
# 110 = 3300 Samples/s
# 111 = 3300 Samples/s

# Bit 4 COMP_MODE
# 0 : Traditional comparator with hysteresis (default)
# 1 : Window comparator

# Bit 3 COMP_POL Comparator Polarity
# 0 : Active low (default)
# 1 : Active high

# Bit 2 COMP_LAT Latching Comparator
# This bit controls whether the ALERT/RDY pin latches once asserted or clears once
# conversions are within the margin of the upper and lower threshold values. When
# COMP_LAT = '0', the ALERT/RDY pin does not latch when asserted. When
# COMP_LAT = '1', the asserted ALERT/RDY pin remains latched until conversion data
# are read by the master or an appropriate SMBus alert response is sent by the
# master, the device responds with its address, and it is the lowest address
# currently asserting the ALERT/RDY bus line. This bit serves no function on the
# ADS1013
# 0 : Non-latching comparator (default)
# 1 : Latching comparator
#
# Bit 1-0 COMP_QUE: Comparator queue and disable
# These bits perform two functions. When set to '11', they disable the comparator
# function and put the ALERT/RDY pin into a high state. When set to any other
# value, they control the number of successive conversions exceeding the upper or
# lower thresholds required before asserting the ALERT/RDY pin. They serve no
# function on the ADS1013.
# 00 : Assert after one conversion
# 01 : Assert after two conversions
# 10 : Assert after four conversions
# 11 : Disable comparator (default)
#

REG_READ_PORT0_SETUP = [0xC1, 0xE3]  # 1 100 -  001 1 -  000 0 - 0 0 11
# bit 15    -   1 -  power on device
# bit 14-12 - 100 - read port 0 to GND
# bit 11-9  - 000 - +/- 6.144 V range
# bit 8     -   1 - single-shot or power down.
#
# bit 7-5   - 000 - data rate of 128 S/s N/A for single shot
# bit 4     -   0 - traditional comparator
# bit 3     -   0 - comparator polarity active low
# bit 2     -   0 - nonlatching comparator
# bit 1-0   -  11 - disable comparator and set ALRT/RDY
#                   to high impedance
REG_READ_PORT1_SETUP = [0xD1, 0xE3]
REG_READ_PORT2_SETUP = [0xE1, 0xE3]
REG_READ_PORT3_SETUP = [0xF1, 0xE3]


class ADS1015IDGSR(i2cPrototype, PointHandler):
    # Texas Instruments 4 channel ADC ADS10

    _points_list = {
      'port_0': {'type': 'PointAnalog',   'access': 'rw'},
      'port_1': {'type': 'PointAnalog',   'access': 'rw'},
      'port_2': {'type': 'PointAnalog',   'access': 'rw'},
      'port_3': {'type': 'PointAnalog',   'access': 'rw'},

      'alarm_comm_fail':  {'type': 'Alarm', 'access': 'rw'},
    }

    parameters = [
        'address',
    ]

    def __init__(self, name: str, bus: int, logger) -> None:
        self.bus = bus
        self.address = None
        self.channels = []
        self.states = 8
        self._state = 0

        self.port_0 = None
        self.port_1 = None
        self.port_2 = None
        self.port_3 = None

        self.alarm_comm_fail = None

        super().__init__(
          name=name,
          logger=logger)

    def reset(self):
        return 0

    def setup(self):
        # Do a sanity check
        assert self.alarm_comm_fail is not None,\
          "Communications alarm is not configured."

        return True

    def _set_state(self, i):
        self.logger.debug("changing state from " + str(self._state)
          + " to " + str(i))
        self._state = i

    def _get_state(self):
        return self._state

    state = property(_get_state, _set_state)

    def _get_has_write_data(self):
        return False

    def write_data(self):
        pass

    has_write_data = property(_get_has_write_data)

    def read_data(self):
        self.logger.debug("Entering function, state is: " + str(self._state))
        try:
            self.logger.debug("setting up IIC to " + str(self.address))
            dev = IIC(self.address, self.bus)

            def _get_byte_string(bits):
                return ' '.join(hex(x) for x in bits)

            def _read_word():
                bits = dev.i2c([REG_CONFIG], 2, 0.01)
                self.logger.debug("REG_CONFIG is: " + _get_byte_string(bits))
                if bits[0] & 0x80 > 0:
                    # conversion complete read the data
                    bits = dev.i2c([REG_CONVERSION], 2, 0.01)
                    point = (bits[0] << 8) + bits[1]
                    point /= 16
                    self.logger.debug("Read : " + _get_byte_string(bits) + " which is: " + str(point))
                    return point
                else:
                    return None

            if 0 == self.state:
                self.logger.debug("State 0 Entered")
                if self.port_0 is not None:
                    b = [REG_CONFIG] + REG_READ_PORT0_SETUP
                    self.logger.debug("sending " + _get_byte_string(b) + " to read port 0")
                    dev.i2c(b, 0, 0.01)
                    self.state = 1
                else:
                    # Jump to the next channel
                    self.state = 2

            if 1 == self.state:
                self.logger.debug("State 1 Entered")
                data = _read_word()
                if data is not None:
                    self.port_0.value = data
                    self.state = 2
                else:
                    dev.close()
                    return 0

            if 2 == self.state:
                self.logger.debug("State 2 Entered")
                if self.port_1 is not None:
                    # Start a measurement for channel 1
                    b = [REG_CONFIG] + REG_READ_PORT1_SETUP
                    self.logger.debug("send " + _get_byte_string(b) + " to read port 1")
                    dev.i2c(b, 0, 0.01)
                    self.state = 3
                else:
                    # Jump to the next channel
                    self.state = 4

            if 3 == self.state:
                self.logger.debug("State 3 Entered")
                data = _read_word()
                if data is not None:
                    self.port_1.value = data
                    self.state = 4
                else:
                    dev.close()
                    return 0

            if 4 == self.state:
                self.logger.debug("State 4 Entered")
                if self.port_2 is not None:
                    # Start a measurement for channel 2
                    b = [REG_CONFIG] + REG_READ_PORT2_SETUP
                    self.logger.debug("send " + _get_byte_string(b) + " to read port 2")
                    dev.i2c(b, 0, 0.01)
                    self._state = 5
                else:
                    # Jump to next channel
                    self._state = 6

            if 5 == self.state:
                self.logger.debug("State 5 Entered")
                data = _read_word()
                if data is not None:
                    self.port_2.value = data
                    self._state = 6
                else:
                    dev.close()
                    return 0

            if 6 == self.state:
                self.logger.debug("State 6 Entered")
                if self.port_3 is not None:
                    # Start a measurement for channel 3
                    b = [REG_CONFIG] + REG_READ_PORT3_SETUP
                    self.logger.debug("send " + _get_byte_string(b) + " to read port 3")
                    dev.i2c(b, 0, 0.01)
                    self.state = 7
                else:
                    self.state = 0

            if 7 == self.state:
                self.logger.debug("State 7 Entered")
                data = _read_word()
                if data is not None:
                    self.port_3.value = data
                    self.state = 0

            self.alarm_comm_fail.input = False
            self.logger.debug(
                "ADS1015 successfully read. Next read at: "
                + str(self.next_update))

        except OSError as e:
            self.logger.debug("Encounted OSError " + str(e))
            self.alarm_comm_fail.input = True
            if 0 == self.state or 1 == self.state:
                # self.point_0.quality = False
                self.state = 2
            elif 2 == self.state or 3 == self.state:
                # self.point_1.quality = False
                self.state = 4
            elif 4 == self.state or 5 == self.state:
                # self.point_2.quality = False
                self.state = 6
            elif 6 == self.state or 7 == self.state:
                # self.point_3.quality = False
                self.state = 0

            self.logger.debug("Read successful. Next read at " + str(self.next_update))

        except Exception as e:
            self.logger.error(traceback.format_exc())

        finally:
            if dev is not None:
                dev.close()

            if self.alarm_comm_fail.active:
                if self.port_0 is not None:
                    self.port_0.quality = False
                if self.port_1 is not None:
                    self.port_1.quality = False
                if self.port_2 is not None:
                    self.port_2.quality = False
                if self.port_3 is not None:
                    self.port_3.quality = False

    def _get_remaining_states(self):
        return 0

    remaining_states = property(_get_remaining_states)

    def config(self):
        self.states = 0

        if self.port_0 is not None:
            self.states += 2
        if self.port_1 is not None:
            self.states += 2
        if self.port_2 is not None:
            self.states += 2
        if self.port_3 is not None:
            self.states += 2

        self.device_points = [
            self.port_0,
            self.port_1,
            self.port_2,
            self.port_3]
