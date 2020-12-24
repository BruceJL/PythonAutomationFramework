from DataObjects.Point import Point

import unittest
import jsonpickle


class TestPoint(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with patch.multiple(Point, __abstractmethods__=set()):
            self.p = Point(
              description="Temperature reading 1 (pressure sensor)",
              hmi_writeable=True,
              update_period=datetime.timedelta(seconds=1.0))

            self.pa_scaled = PointAnalogScaled(
              name="temperature_scaled",
              scaling= 2.0,
              offset=-1.0,
              point=self.pa,
            )

        self.pa_scaled.config("test_scaled_point")

    def setUp(self):
        pass

    def test_pa_config(self):

    def test_yaml_pickle(self):
        pickle_text =

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point, unpickled_point)

    def test_set_hmi_value(self):
        self.point.hmi_value = "100.0"
        self.assertEqual(100.0, self.point.hmi_value)


if __name__ == '__main__':
    unittest.main()
