import unittest
from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointAnalogDual import PointAnalogDual
import jsonpickle
import datetime
import ruamel.yaml
from ruamel.yaml.compat import StringIO



class TestPointAnalogDual(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        point_temperature_1 = PointAnalog(
        description   = "Temperature reading 1",
          u_of_m        = "ºC",
          hmi_writeable = False,
          update_period = 1.0,
        )
        point_temperature_1.config("temp_1")
        point_temperature_1.value = 5.0

        point_temperature_2 = PointAnalog(
          description   = "Temperature reading 2",
          u_of_m        = "ºC",
          hmi_writeable = False,
          update_period = 1.0,
        )
        point_temperature_2.config("temp_2")
        point_temperature_2.value = 5.1

        self.point = PointAnalogDual(
            description = "Temperature reading",
            point_1     = point_temperature_1,
            point_2     = point_temperature_2,
        )
        self.point.config('temp')

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)

        self.assertEqual(self.point.value,       unpickled_point.value)
        self.assertEqual(self.point.quality,     unpickled_point.quality)
        self.assertEqual(self.point.description, unpickled_point.description)
        self.assertEqual(self.point.last_update, unpickled_point.last_update)

    def test_yaml_pickle(self):
        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        yml.register_class(PointAnalogDual)
        yml.register_class(PointAnalog)

        stream = StringIO()
        yml.dump(self.point, stream)
        s=stream.getvalue()
        # print(s)
        unpickled_point = yml.load(s)
        unpickled_point.config("Temperature reading")

        self.assertEqual(self.point.description, unpickled_point.description)
        self.assertEqual(self.point._point_1.description, unpickled_point._point_1.description)
        self.assertEqual(self.point._point_2.description, unpickled_point._point_2.description)


if __name__ == '__main__':
    unittest.main()
