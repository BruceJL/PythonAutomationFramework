import unittest
from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointAnalogDual import PointAnalogDual
import jsonpickle
import datetime


class TestPointAnalogDual(unittest.TestCase):

    def setUp(self):
        point_temperature_1 = PointAnalog(
            name="temperature_1",
            description="Temperature reading 1 (pressure sensor)",
            u_of_m="ºC",
            hmi_writeable=False,
            # deadband=0.5,
            update_period=datetime.timedelta(seconds=1.0))

        point_temperature_2 = PointAnalog(
            name="temperature_2",
            description="Temperature reading 2 (hygrostat)",
            u_of_m="ºC",
            hmi_writeable=False,
            # deadband=0.5,
            update_period=datetime.timedelta(seconds=1.0))

        self.point = PointAnalogDual(
            name="temperature",
            description="Temperature reading",
            point_1=point_temperature_1,
            point_2=point_temperature_2)

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.__dict__, unpickled_point.__dict__)


if __name__ == '__main__':
    unittest.main()