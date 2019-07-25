import unittest
from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointReadOnly import PointReadOnly
import jsonpickle
import datetime


class TestPointReadOnly(unittest.TestCase):

    def setUp(self):
        point_analog = PointAnalog(
            name="temperature_1",
            description="Temperature reading 1 (pressure sensor)",
            u_of_m="ºC",
            hmi_writeable=False,
            # deadband=0.5,
            update_period=datetime.timedelta(seconds=1.0))

        self.point = PointReadOnly(point_analog)

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.__dict__, unpickled_point.__dict__)


if __name__ == '__main__':
    unittest.main()