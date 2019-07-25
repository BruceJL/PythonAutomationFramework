'''
Created on Apr 11, 2016

@author: Bruce
'''

import logging
from .linuxi2c3 import IIC
import datetime

logger = logging.getLogger('controller')

# Intersil ISL29125IROZ-T7A color sensor
class ISL29125IROZ(object):
    '''
    http://www.intersil.com/content/dam/Intersil/documents/isl2/isl29125.pdf
    '''
    
    ADDRESS = 0x44

    REG_ID = 0x00
    REG_RESET = 0x00
    REG_CONFIG_1 = 0x01
    REG_CONFIG_2 = 0x02
    REG_CONFIG_3 = 0x03
    REG_LOW_THRESHOLD_LSB = 0x04
    REG_LOW_THRESHOLD_MSB = 0x05
    REG_HIGH_THRESHOLD_LSB = 0x06
    REG_HIGH_THRESHOLD_MSB = 0x07
    REG_STATUS_FLAGS = 0x08
    REG_GREEN_LSB = 0x09
    REG_GREEN_MSB = 0x0A
    REG_RED_LSB = 0x0B
    REG_RED_MSB = 0x0C
    REG_BLUE_LSB = 0x0D
    REG_BLUE_MSB = 0x0E

    def __init__(self, bus) -> None:
        self.bus = bus
        self.red_light_level = None
        self.green_light_level = None
        self.blue_light_level = None
        self.nextUpdate = datetime.datetime.now()

    def reset(self):
        self.bus.write_byte_data(self.ADDRESS, self.REG_RESET, 0x46)  # 0001 1101
        self.setup()
        
    def setup(self):
        
        # ---------
        # bits 0-2 RGB operating mode.
        # 000 = off
        # 001 = green only
        # 010 = red only
        # 011 = blue only
        # 100 = standby
        # 101 = green/red/blue
        # 110 = green/red
        # 111 = green/blue
        #
        # ---------
        # bit 3 - RGB sensing range.
        # 0 = 375 lux
        # 1 = 100000 lux
        #
        # ---------
        # bit 4 - ADC resolution.
        # 0 = 16 bit resolution
        # 1 = 12 bit resolution
        #
        # ---------
        # bit 5 - RGB Start Sync'd
        # 0 = ADC start at I2C write 0x01
        #  1 = ADC start at rising ^INT
        #
        # ---------
        # bit 6-7 - Unused
        #
        #

        self.bus.write_byte_data(self.ADDRESS, self.REG_CONFIG_1, 0x1D)  # 0001 1101
        self.bus.write_byte_data(self.ADDRESS, self.REG_CONFIG_2, 0x02)  # max out IR compensation
        
    def read_data(self):
        try:
            self.dev = IIC(ADDRESS, self.bus)
            '''
            read 9 bytes starting at 0x08
            0 - 0x08 - status bytearray
            1 - 0x09 - Green low byte
            2 - 0x10 - Green high byte
            3 - 0x11 - Red high byte
            4 - 0x12 - Red low byte
            5 - 0x13 - blue low byte
            6 - 0x14 - blue high byte
            '''
            b = self.dev.i2c([0x08],7, 0.01)
            
            self.green_light_level.value = (b[2] << 8 | b[1])
            self.red_light_level.value = (b[3] << 8 | b[4])
            self.blue_light_level.value = (b[6] << 8 | b[5])
        except osError as e:
            self.green_light_level.quality = False
            self.red_light_level.quality = False
            self.blue_light_level.quality = False
        return -1
        
    def get_remaining_states(self):
        return 0
        
    def assign_points(self,
                      red_light_level,
                      green_light_level,
                      blue_light_level):
        self.red_light_level = red_light_level
        self.green_light_level = green_light_level
        self.blue_light_level = blue_light_level
