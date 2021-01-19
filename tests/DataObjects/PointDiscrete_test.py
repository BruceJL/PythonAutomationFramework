import unittest
import jsonpickle

from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.Supervisory.PointManager import PointManager


class TestPointDiscrete(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.point = PointDiscrete(
          description           = "Pump run",
          on_state_description  = "Running",
          off_state_description = "Stopped",
          hmi_writeable         = True,
          requestable           = True,
          retentive             = True,
          update_period         = 20.0,
        )
        self.point.value = True
        PointManager().add_to_database(
          name = "pump_run",
          obj = self.point,
        )

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)

        self.assertEqual(
          self.point.description,
          unpickled_point.description,
        )

        self.assertEqual(
          self.point.requestable,
          unpickled_point.requestable,
        )

        self.assertEqual(
          self.point.hmi_writeable,
          unpickled_point.hmi_writeable,
        )

        self.assertEqual(
          self.point.on_state_description,
          unpickled_point.on_state_description,
        )

        self.assertEqual(
          self.point.off_state_description,
          unpickled_point.off_state_description,
        )

        self.assertEqual(
          self.point.value,
          unpickled_point.value,
        )

    def test_a_yaml_pickle(self):
        s = PointManager().dump_database_to_yaml()
        PointManager().clear_database()
        print (f"YAML:\n {s}")
        PointManager().load_points_from_yaml_string(s)
        unpickled_point = PointManager().find_point("pump_run")

        self.assertEqual(
          self.point.description,
          unpickled_point.description,
        )
        self.assertEqual(
          self.point.requestable,
          unpickled_point.requestable,
        )

        self.assertEqual(
          self.point.retentive,
          unpickled_point.retentive,
        )

        self.assertEqual(
          self.point.hmi_writeable,
          unpickled_point.hmi_writeable,
        )

        self.assertEqual(
          self.point.update_period,
          unpickled_point.update_period,
        )

        self.assertEqual(
          self.point.on_state_description,
          unpickled_point.on_state_description
        )

        self.assertEqual(
          self.point.off_state_description,
          unpickled_point.off_state_description
        )

        self.assertEqual(
          self.point.value,
          unpickled_point.value,
        )


if __name__ == '__main__':
    unittest.main()
