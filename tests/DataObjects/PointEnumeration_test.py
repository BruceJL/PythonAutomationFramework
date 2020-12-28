import unittest
import jsonpickle
import ruamel.yaml
from ruamel.yaml.compat import StringIO

from pyAutomation.DataObjects.PointEnumeration import PointEnumeration


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
        self.point.config("feed_state")
        self.point.value = "FLUSH"

    def test_a_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        unpickled_point.config("feed_state")

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
        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        yml.register_class(PointEnumeration)

        stream = StringIO()
        yml.dump(self.point, stream)
        s=stream.getvalue()
        unpickled_point = yml.load(s)
        unpickled_point.config("feed_state")

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

        self.assertEqual(
          self.point.value,
          unpickled_point.value,
        )


if __name__ == '__main__':
    unittest.main()
