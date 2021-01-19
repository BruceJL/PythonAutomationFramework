import unittest
import jsonpickle

from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogDual import PointAnalogDual
from pyAutomation.Supervisory.PointManager import PointManager


class TestPointAnalogDual(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        point_temperature_1 = PointAnalog(
          description   = "Temperature reading 1",
          u_of_m        = "ºC",
          hmi_writeable = False,
          update_period = 1.0,
        )
        point_temperature_1.value = 5.0

        PointManager().add_to_database(
          name="temp_1",
          obj = point_temperature_1
        )

        point_temperature_2 = PointAnalog(
          description   = "Temperature reading 2",
          u_of_m        = "ºC",
          hmi_writeable = False,
          update_period = 1.0,
        )
        PointManager().add_to_database(
          name="temp_2",
          obj = point_temperature_1
        )
        point_temperature_2.value = 5.1

        self.point = PointAnalogDual(
            description = "Temperature reading",
            point_1     = point_temperature_1,
            point_2     = point_temperature_2,
        )
        PointManager().add_to_database(
          name="temp",
          obj = self.point
        )

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)

        self.assertEqual(
          self.point.value,
          unpickled_point.value,
        )

        self.assertEqual(
          self.point.quality,
          unpickled_point.quality,
        )

        self.assertEqual(
          self.point.description,
          unpickled_point.description,
        )
        self.assertEqual(
          self.point.last_update,
          unpickled_point.last_update,
        )

    def test_yaml_pickle(self):
        s = PointManager().dump_database_to_yaml()
        PointManager().clear_database
        PointManager().load_points_from_yaml_string(s)

        unpickled_point = PointManager().find_point("temp")

        self.assertEqual(
          self.point,
          unpickled_point,
        )

        self.assertEqual(
          self.point._point_1,
          unpickled_point._point_1,
        )

        self.assertEqual(
          self.point._point_2,
          unpickled_point._point_2,
        )


if __name__ == '__main__':
    unittest.main()
