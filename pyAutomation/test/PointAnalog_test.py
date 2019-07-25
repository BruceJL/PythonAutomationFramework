import unittest
from DataObjects.PointAnalog import PointAnalog
import jsonpickle
import datetime


class TestPointAnalog(unittest.TestCase):

    def setUp(self):
        self.point = PointAnalog(
            name="temperature_1",
            description="Temperature reading 1 (pressure sensor)",
            u_of_m="ºC",
            hmi_writeable=True,
            update_period=datetime.timedelta(seconds=1.0))

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point, unpickled_point)

    def test_set_hmi_value(self):
        self.point.hmi_value = "100.0"
        self.assertEqual(100.0, self.point.hmi_value)


if __name__ == '__main__':
    unittest.main()