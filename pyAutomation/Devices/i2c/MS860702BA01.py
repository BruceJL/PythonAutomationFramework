#http://www.phanderson.com/arduino/hih6130.html
#http://cdn.sparkfun.com/datasheets/Prototyping/1443945.pdf
#http://www.phanderson.com/arduino/I2CCommunications.pdf

import datetime
import logging
from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler


class MS860702BA01(i2cPrototype, PointHandler):
    # Honeywell MS860702BA01 Hygroostat

    ADDRESS = 0x27

    _points_list = {
      'point_humidity':    {'type': 'PointAnalog',   'access': 'rw'},
      'point_temperature': {'type': 'PointAnalog',   'access': 'rw'},
    }

    parameters = {}

    def __init__(self, name: str, bus: int, logger: str) -> None:
        self.bus = bus
        self.temperature = -999
        self.humidity = -999
        self.quality = False
        self.lastReadTime = 0
        self.status = -1
        self.states = 2
        self.is_setup = True  # device requires no setup.
        self.nextUpdate = datetime.datetime.now()

        super().__init__(
          name=name,
          logger=logger)

    def _setup(self):
        return True

    def measure(self):
        self.bus.write_quick(self.ADDRESS)

    def _read_data(self):

        try:
            HUMIDITY_MSB = self.bus.read(self.ADDRESS)
            HUMIDITY_LSB = self.bus.read(self.ADDRESS)
            TEMPERATURE_MSB = self.bus.read(self.ADDRESS)
            TEMPERATURE_LSB = self.bus.read(self.ADDRESS)
            self.status = HUMIDITY_MSB >> 6

            if self.status == 0x00:
                self.point_humidity.setQuality(True)
                self.point_temperature.setQuality(True)
                self.point_temperature.setValue(((TEMPERATURE_MSB & 0x3f) << 8 | TEMPERATURE_LSB)/0x3fff * 100)
                self.point_humidity.setValue((HUMIDITY_MSB << 6 | HUMIDITY_LSB >> 2) / 0x3fff * 165 - 40)
            else:
                self.point_humidity.setQuality(False)
                self.point_temperature.setQuality(False)
        except Exception as e:
            self.point_humidity.ioSetQuality(False)
            self.point_temperature.ioSetQuality(False)

    def get_remaining_states(self):
        return

    def config(self):
        self.device_points = [
            self.point_humidity,
            self.point_temperature]
