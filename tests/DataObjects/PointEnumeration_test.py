import unittest
import jsonpickle

from pyAutomation.DataObjects.PointEnumeration import PointEnumeration
from pyAutomation.Supervisory.PointManager import PointManager


class TestPointEnumeration(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.point = PointEnumeration(
          description="Pump System State",
          hmi_writeable=True,
          requestable=True,
          states=["OFF", "RUN", "DEPRESSURIZE", "FLUSH"],
          retentive=True,
        )
        self.point.value = "FLUSH"

        PointManager().add_to_database(
          name = "feed_state",
          obj = self.point,
        )

    def test_a_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        unpickled_point.name = "feed_state"

        self.assertEqual(
          self.point.name,
          unpickled_point.name,
        )

        self.assertEqual(
          self.point.states,
          unpickled_point.states,
        )

        self.assertEqual(
          self.point.description,
          unpickled_point.description,
        )

        self.assertEqual(
          self.point.value,
          unpickled_point.value,
        )

        self.assertEqual(
          self.point.requestable,
          unpickled_point.requestable,
        )

        self.assertEqual(
          self.point.forced,
          unpickled_point.forced,
        )

        self.assertEqual(
          self.point.last_update,
          unpickled_point.last_update,
        )

        self.assertEqual(
          self.point.quality,
          unpickled_point.quality,
        )

    def test_a_yaml_pickle(self):
        s = PointManager().dump_database_to_yaml()
        PointManager().clear_database()
        # print (f"YAML:\n {s}")
        PointManager().load_points_from_yaml_string(s)
        unpickled_point = PointManager().find_point("feed_state")

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
          unpickled_point.hmi_writeable
        )

        self.assertEqual(
          self.point.update_period,
          unpickled_point.update_period,
        )

        self.assertEqual(
          self.point.states,
          unpickled_point.states,
        )


if __name__ == '__main__':
    unittest.main()
