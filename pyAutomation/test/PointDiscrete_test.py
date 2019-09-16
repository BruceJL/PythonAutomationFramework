import unittest
from DataObjects.PointDiscrete import PointDiscrete
import jsonpickle
import datetime
import ruamel.yaml
from ruamel.yaml.compat import StringIO


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

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)

        self.assertEqual(self.point.description,           unpickled_point.description)
        self.assertEqual(self.point.requestable,           unpickled_point.requestable)
        self.assertEqual(self.point.hmi_writeable,         unpickled_point.hmi_writeable)
        self.assertEqual(self.point.on_state_description,  unpickled_point.on_state_description)
        self.assertEqual(self.point.off_state_description, unpickled_point.off_state_description)
        self.assertEqual(self.point.value,                 unpickled_point.value)


    def test_a_yaml_pickle(self):
        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        yml.register_class(PointDiscrete)

        stream = StringIO()
        yml.dump(self.point, stream)
        s=stream.getvalue()
        unpickled_point = yml.load(s)

        self.assertEqual(self.point.description,           unpickled_point.description)
        self.assertEqual(self.point.requestable,           unpickled_point.requestable)
        self.assertEqual(self.point.retentive,             unpickled_point.retentive)
        self.assertEqual(self.point.hmi_writeable,         unpickled_point.hmi_writeable)
        self.assertEqual(self.point.update_period,         unpickled_point.update_period)
        self.assertEqual(self.point.on_state_description,  unpickled_point.on_state_description)
        self.assertEqual(self.point.off_state_description, unpickled_point.off_state_description)
        self.assertEqual(self.point.value,                 unpickled_point.value)


if __name__ == '__main__':
    unittest.main()
