import unittest
from unittest.mock import patch
import datetime
import logging
from time import sleep
from logging.handlers import RotatingFileHandler
from UserLogic.LightController import LightController
from UserLogic.PointDatabase import PointDatabase
import time


class TestLightController(unittest.TestCase):

    def setUp(self):
        # build the logging formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s.%(funcName)s() - %(message)s')

        # setup the controller logger
        logger_controller = logging.getLogger('controller')
        logger_controller.setLevel(logging.DEBUG)
        fh = RotatingFileHandler(
            './logs/controller-test.log',
            maxBytes=40960,
            backupCount=1)
        fh.setFormatter(formatter)
        logger_controller.addHandler(fh)

        self.time = datetime.datetime(year=2001, month=1, day=1, hour=1, minute=0)

        @patch('datetime.datetime.now', return_value=time)

        # configure the light controller
        self.light_controller = LightController(
            name="light_controller",
            period=None,
            logger=logger_controller
        )

        self.red_light_level = PointDatabase.get_point_rw("red_light_level", self)
        self.blue_light_level = PointDatabase.get_point_rw("blue_light_level", self)
        self.green_light_level = PointDatabase.get_point_rw("green_light_level", self)
        self.clear_light_level = PointDatabase.get_point_rw("clear_light_level", self)
        self.run_lights = PointDatabase.get_point_ro("run_lights")
        self.lighting_mode = PointDatabase.get_point_ro("lighting_mode")
        self.temperature = PointDatabase.get_point_rw("temperature_1", self)
        self.pump_water_pressure = PointDatabase.get_point_rw("pump_water_pressure", self)

    def test_light_mode_change(self):
        time =
        @patch(datetime.datetime.now, return_value=time)

        # switch to VEGATATIVE
        self.lighting_mode.hmi_value = "False"
        sleep(0.5)
        self.assertFalse(self.lighting_mode.value)

        # switch to BLOOM
        self.lighting_mode.hmi_value = "True"
        sleep(0.5)
        self.assertTrue(self.lighting_mode.value)



    def tearDown(self):
        self.light_controller.quit()


if __name__ == '__main__':
    unittest.main()