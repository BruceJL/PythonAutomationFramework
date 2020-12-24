import unittest
import jsonpickle
from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointEnumeration import PointEnumeration
from DataObjects.PointDiscrete import PointDiscrete
from DataObjects.PointReadOnly import PointReadOnly


class TestPointReadOnly(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.point_analog = PointAnalog(
          description   = "Temperature reading",
          u_of_m        = "ºC",
          hmi_writeable = False,
          retentive     = True,
          update_period = 1.0,
        )

        self.point_analog.config("temp_1")

        self.point_discrete= PointDiscrete(
          description="run cooling",
          hmi_writeable=False,
        )
        self.point_discrete.config("run_cooling")

        self.point_enumeration=PointEnumeration(
          description="System mode",
          states=["Hand", "Off", "Auto"],
          hmi_writeable=False,
        )
        self.point_enumeration.config("system_mode")


    def test_json_pickle_analog(self):
        self.point = PointReadOnly(self.point_analog)
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.name, unpickled_point.name)

    def test_json_pickle_discrete(self):
        self.point = PointReadOnly(self.point_discrete)
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.name, unpickled_point.name)

    def test_json_pickle_enumeration(self):
        self.point = PointReadOnly(self.point_enumeration)
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.name, unpickled_point.name)

if __name__ == '__main__':
    unittest.main()
