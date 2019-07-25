import unittest
from DataObjects.AlarmAnalog import AlarmAnalog
import jsonpickle


class TestAnalogAlarmAnalog(unittest.TestCase):

    def setUp(self):
        self.alarm = AlarmAnalog(
            name="h1_temperature",
            description="Temperature H1",
            alarm_value=30.0,
            hysteresis=1.0,
            high_low_limit="HIGH",
            consequences="None",
            more_info="Temperature is rising above safe levels. The cooling system may be failing.")

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.alarm)
        unpickled_alarm = jsonpickle.decode(pickle_text)
        self.assertEqual(self.alarm.__dict__, unpickled_alarm.__dict__)


if __name__ == '__main__':
    unittest.main()