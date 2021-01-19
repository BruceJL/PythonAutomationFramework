import unittest
import jsonpickle

from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointEnumeration import PointEnumeration
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.PointReadOnly import PointReadOnly
from pyAutomation.Supervisory.PointManager import PointManager


class TestPointReadOnly(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Build the PointAnalog
        self.point_analog = PointAnalog(
          description   = "Temperature reading",
          u_of_m        = "ºC",
          hmi_writeable = False,
          retentive     = True,
          update_period = 1.0,
        )

        PointManager().add_to_database(
          name = "temp_1",
          obj = self.point_analog,
        )

        # Build the PointDiscrete
        self.point_discrete= PointDiscrete(
          description="run cooling",
          hmi_writeable=False,
        )

        PointManager().add_to_database(
          name = "run_cooling",
          obj = self.point_discrete,
        )

        # Build the PointEnumeration
        self.point_enumeration=PointEnumeration(
          description="System mode",
          states=["Hand", "Off", "Auto"],
          hmi_writeable=False,
        )

        PointManager().add_to_database(
          name = "system_mode",
          obj = self.point_enumeration,
        )

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
