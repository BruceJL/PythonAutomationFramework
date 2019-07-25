#!/usr/bin/python3
'''
Created on Apr 11, 2016

@author: Bruce
'''

from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogAbstract import PointAnalogAbstract
from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler

from .linuxi2c3 import IIC
from typing import List
import logging

'''
http://ams.com/eng/content/download/496863/1433517/271695
'''

ADDRESS = 0x39

# The information below is lifted directly from the datasheet
REG_ENABLE = 0x00       # Enables states and interrupts
REG_ATIME = 0x01        # RGBC time
REG_WTIME = 0x03        # Wait time

REG_AILTL = 0x04        # Clear sensor interrupt low threshhold low byte
REG_AILTH = 0x05        # Clear sensor interrupt low threshold high byte
REG_AIHTL = 0x06        # Clear sensor interrupt high threshold low byte
REG_AIHTH = 0x07        # Clear sensor interrupt high threshold low byte

REG_PILTL = 0x08        # Proximity sensor interrupt low threshold low byte
REG_PILTH = 0x09        # Proximity sensor interrupt low threshold high byte
REG_PIHTL = 0x0A        # Proximity sensor interrupt high threshold low byte
REG_PIHTH = 0x0B        # Proximity sensor interrupt high threshold high byte

REG_PERS = 0x0C         # Interrupt presistence filters
REG_CONFIG = 0x0D       # Configuration
REG_PPULSE = 0x0E       # Proximitiy Pulse Count
REG_CONTROL = 0x0F      # Gain control register
REG_REVISION = 0x11     # Die revision Number
REG_ID = 0x12           # Device ID
REG_STATUS = 0x13       # Device status

REG_CDATA = 0x14        # Clear ADC low data register
REG_CDATAH = 0x15       # Clear ADC high data register

REG_RDATA = 0x16        # Red ADC low data register
REG_RDATA_H = 0x17      # Red ADC high data register

REG_GDATA = 0x18        # Green ADC low data register
REG_GDATA_H = 0x19      # Green ADC high data register

REG_BDATA = 0x1A        # Blue ADC low data register
REG_BDATA_H = 0x1B      # Blue ADC high data register

REG_PDATA = 0x1C        # Proximity low data register
REG_PDATA_H = 0x1D      # Proximity high data register

CMD_WRITE = 0x80        # Command register address
CMD_REPEATED_BYTE_PROTOCOL = 0x00
CMD_AUTO_INCREMENT_PROTOCOL = 0x20

def format_debug_data(s, data):
    return s + ''.join('{:02x} '.format(x) for x in data)


# AMS TMD3782 color sensor
class TMD3782(i2cPrototype, PointHandler):

    points = {
      'point_clear_light_level': 'get_point_rw',
      'point_red_light_level': 'get_point_rw',
      'point_green_light_level': 'get_point_rw',
      'point_blue_light_level': 'get_point_rw',
    }
    _points_list = {
      'point_clear_light_level': {'type': 'PointAnalog', 'access': 'rw'},
      'point_red_light_level':   {'type': 'PointAnalog', 'access': 'rw'},
      'point_green_light_level': {'type': 'PointAnalog', 'access': 'rw'},
      'point_blue_light_level':  {'type': 'PointAnalog', 'access': 'rw'},
     }

    parameters = {}

    def __init__(self, name: str, bus: int, logger: str) -> None:
        self.bus = bus
        self.point_clear_light_level = None  # type: PointAnalogAbstract
        self.point_red_light_level = None    # type: PointAnalogAbstract
        self.point_green_light_level = None  # type: PointAnalogAbstract
        self.point_blue_light_level = None   # type: PointAnalogAbstract
        self.dev = None                      # type: int
        self.device_points = None            # type: List[PointAnalog]

        self.alarm_comm_fail = Alarm(
          name="light_comm_failure",
          description="light sensor communications failure",
          on_delay=15,
          off_delay=10,
          consequences="Light stuck/loss alarms are unreliable",
          more_info="System cannot verify the presence or absence of light.")

        super().__init__(
          name=name,
          logger=logger)

    def reset(self):
        self._setup()

    def _setup(self):
        try:
            self.dev = IIC(ADDRESS, self.bus)

            # write to the REG_ENABLE to configure the following settings:
            # bit 7:6 reserved as 00
            # bit 5 Proximity interupt enable : 0
            # bit 4 Abient light sensing interrupt enable. : 0
            # bit 3 Wait enable : 0
            # bit 2 proximity enable : 0
            # bit 1 ADC enable : 1
            # bit 0 power on : 1

            data = [CMD_WRITE | CMD_REPEATED_BYTE_PROTOCOL | REG_ENABLE, 0x03]
            self.logger.debug(format_debug_data("writing 0x03 to REG_ENABLE - Sending: ", data))
            b = self.dev.i2c(data, 1, 0.01)
            self.logger.debug(format_debug_data("device returned: ", b))

            # write to REG_CONTROL to configure gain.
            # bit 7:6 Proximity driving power : 00
            # bit 5 reserved as 1
            # bit 4 Proximity saturation behaviour : 0
            # bit 3:2 reserved as 00
            # bit 1:0 analog gain 00 for 1x gain
            #                     01 for 4x gain
            #                     10 for 16x gain
            #                     11 for 60x gain

            data = [CMD_WRITE | CMD_REPEATED_BYTE_PROTOCOL | REG_CONTROL, 0x13]
            self.logger.debug(format_debug_data("writing 0x13 to REG_CONTROL Sending: ", data))
            b = self.dev.i2c(data, 1, 0.01)
            self.logger.debug(format_debug_data("device returned: ", b))

            data = [CMD_WRITE | CMD_REPEATED_BYTE_PROTOCOL | REG_ENABLE]
            self.logger.debug(format_debug_data("Reading from REG_ENABLE - Sending: ", data))
            b = self.dev.i2c(data, 1, 0.01)
            self.logger.debug(format_debug_data("device returned:  ", b))

            self.is_setup = True
        except OSError as e:
            self.logger.info("I/O fault " + str(e))
        finally:
            self.logger.info("Device read successfully")
            self.dev.close()

    def _write_data(self):
        pass

    def _read_data(self):
        if self.alarm_comm_fail.active:
            self.point_clear_light_level.quality = False
            self.point_red_light_level.quality = False
            self.point_green_light_level.quality = False
            self.point_blue_light_level.quality = False

        try:
            self.dev = IIC(ADDRESS, self.bus)

            '''
            read 9 bytes starting at 0x13
            0 - 0x13 - Status register
            1 - 0x14 - Clear low byte
            2 - 0x15 = Clear high byte
            3 - 0x16 - Red high byte
            4 - 0x17 - Red low byte
            5 - 0x18 - Green low byte
            6 - 0x19 - Green high byte
            7 - 0x1A - blue low byte
            8 - 0x1B - blue high byte
            '''
            data = [CMD_WRITE | CMD_AUTO_INCREMENT_PROTOCOL | REG_STATUS]
            self.logger.debug(format_debug_data("Reading data sending: ", data))
            b = self.dev.i2c(data, 9, 0.01)
            self.logger.debug(format_debug_data("device returned: ", b))

            if b[0] & 0x01:
                # analog signals are valid
                self.logger.debug("data read successfully")
                self.point_clear_light_level.value = (b[2] << 8 | b[1])
                self.point_red_light_level.value = (b[4] << 8 | b[3])
                self.point_green_light_level.value = (b[6] << 8 | b[5])
                self.point_blue_light_level.value = (b[8] << 8 | b[7])
                self.alarm_comm_fail.input = False
            else:
                self.logger.warn("data not read successfully")
                self.is_setup = False
                self.alarm_comm_fail.input = True

        except OSError as e:
            self.logger.error("I/O fault " + str(e))
            self.alarm_comm_fail.input = True

        finally:
            self.dev.close()

            if self.alarm_comm_fail.active:
                self.point_clear_light_level.quality = False
                self.point_red_light_level.quality = False
                self.point_green_light_level.quality = False
                self.point_blue_light_level.quality = False

    def config(self):

        self.device_points = [
            self.point_clear_light_level,
            self.point_red_light_level,
            self.point_green_light_level,
            self.point_blue_light_level
        ]

        self.point_clear_light_level.quality = False
        self.point_green_light_level.quality = False
        self.point_red_light_level.quality = False
        self.point_blue_light_level.quality = False
