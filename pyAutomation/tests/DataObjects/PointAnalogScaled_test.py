from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointAnalogScaled import PointAnalogScaled

import unittest
import jsonpickle
import ruamel.yaml
from ruamel.yaml.compat import StringIO


class TestPointAnalogScaled(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.pa = PointAnalog(
          description="Temperature reading 1 (pressure sensor)",
          u_of_m="ºC",
          hmi_writeable=True,
          update_period=1.2,
        )
        self.pa.config("temperature_1")

        self.point = PointAnalogScaled(
          scaling = 2.0,
          offset = -1.0,
          point = self.pa,
        )
        self.point.config("test_scaled_point")

    def test_scaling(self):
        self.pa.value = 44.0
        self.assertEqual(self.point.value, 22.5)

        self.point.value = 44.0
        self.assertEqual(self.pa.value, 87.0)

    def test_yaml_pickle(self):
        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        yml.register_class(PointAnalogScaled)
        yml.register_class(PointAnalog)

        stream = StringIO()
        yml.dump(self.point, stream)
        s=stream.getvalue()
        unpickled_point = yml.load(s)
        unpickled_point.config("test_scaled_point")

        self.assertEqual(self.point.scaling, unpickled_point.scaling)
        self.assertEqual(self.point.offset, unpickled_point.offset)

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.scaling, unpickled_point.scaling)
        self.assertEqual(self.point.offset, unpickled_point.offset)
        self.assertEqual(self.point.point.name, unpickled_point.point.name)


if __name__ == '__main__':
    unittest.main()
