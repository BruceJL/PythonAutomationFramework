import unittest
from DataObjects.PointDiscrete import PointDiscrete
import jsonpickle
import datetime


class TestPointDiscrete(unittest.TestCase):

    def setUp(self):
        self.point = PointDiscrete(
            name="co2_calibration_running",
            description="ABC CO2 Calibration",
            on_state_description="Disabled",
            off_state_description="Enabled",
            hmi_writeable=True,
            requestable=True,
            update_period=datetime.timedelta(seconds=20.0))

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.__dict__, unpickled_point.__dict__)


if __name__ == '__main__':
    unittest.main()