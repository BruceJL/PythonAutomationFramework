import unittest
import jsonpickle

from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogScaled import PointAnalogScaled
from pyAutomation.Supervisory.PointManager import PointManager


class TestPointAnalogScaled(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        point = PointAnalog(
          description="Temperature reading 1 (pressure sensor)",
          u_of_m="ºC",
          update_period=1.2,
        )
        PointManager.add_to_database(
          name = "temperature_source",
          obj = point,
        )

        point = PointAnalogScaled(
          scaling = 2.0,
          offset = -1.0,
          point = point,
          readonly = True,
        )

        PointManager.add_to_database(
          name = "test_scaled_point",
          obj = point,
        )

        point = PointAnalog(
            description="Temperature Setpoint",
            u_of_m="ºC",
            update_period=None,
        )

        PointManager.add_to_database(
          name = "setpoint",
          obj = point,
        )

        point = PointAnalogScaled(
          scaling = 2.0,
          offset = -1.0,
          point = point,
          readonly = False,
        )

        PointManager.add_to_database(
          name = "setpoint_scaled",
          obj = point,
        )

    def test_scaling(self):
        point_analog = \
          PointManager().find_point("temperature_source").readwrite_object
        point_scaled = \
          PointManager().find_point("test_scaled_point").readonly_object

        point_analog.value = 44.0
        print(point_scaled.value)
        self.assertEqual(point_scaled.value, 22.5)

    def test_unscaling(self):
        point_analog = \
            PointManager().find_point("setpoint").readonly_object
        point_scaled = \
            PointManager().find_point("setpoint_scaled").readwrite_object

        point_scaled.value = 44.0
        self.assertEqual(point_analog.value, 87.0)

    def test_yaml_pickle(self):
        point = PointManager().find_point("test_scaled_point")
        s = PointManager().dump_database_to_yaml()
        print (f"YAML:\n {s}")
        PointManager().clear_database
        PointManager().load_points_from_yaml_string(s)
        unpickled_point = PointManager().find_point("test_scaled_point")

        self.assertEqual(point.scaling, unpickled_point.scaling)
        self.assertEqual(point.offset, unpickled_point.offset)

    def test_json_pickle(self):
        point = PointManager().find_point("setpoint_scaled").readwrite_object
        pickle_text = jsonpickle.encode(point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(point.scaling, unpickled_point.scaling)
        self.assertEqual(point.offset, unpickled_point.offset)


if __name__ == '__main__':
    unittest.main()
