import unittest
import logging
import jsonpickle
import ruamel.yaml
from ruamel.yaml.compat import StringIO

from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.AlarmAnalog import AlarmAnalog
from pyAutomation.Supervisory.AlarmHandler import AlarmHandler


class TestAnalogAlarmAnalog(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logger = 'controller'
        self.logger = logging.getLogger(logger)
        self.logger.setLevel('INFO')

        self.alarm = AlarmAnalog(
          alarm_value=30.0,
          hysteresis=1.0,
          high_low_limit="HIGH",

          description="Temperature H1",
          consequences="None",
          on_delay=1.0,
          off_delay=2.0,
          more_info="Temperature is rising above safe levels. The cooling "
            "system may be failing.",
        )
        self.alarm.name = "h1_temperature"

        self.ah = AlarmHandler(
          logger=logger,
          name="alarm processer",
        )

        Alarm.alarm_handler = self.ah
        self.logger.debug("setUpClass completed.")

    def test_a_json_pickle(self):
        # n.b. the a in the test name is so that this test gets executed first,
        # the Mock module doesn't seem to want to relent outside of the 'with'
        # block.

        pickle_text = jsonpickle.encode(self.alarm)
        unpickled_alarm = jsonpickle.decode(pickle_text)

        # make sure all AlarmAnalog properties line up.
        self.assertEqual(
          self.alarm.alarm_value,
          unpickled_alarm.alarm_value,
        )

        self.assertEqual(
          self.alarm.hysteresis,
          unpickled_alarm.hysteresis,
        )

        self.assertEqual(
          self.alarm.high_low_limit,
          unpickled_alarm.high_low_limit,
        )

        # make sure all inherited properties line up.
        self.assertEqual(
          self.alarm.name,
          unpickled_alarm.name,
        )

        self.assertEqual(
          self.alarm.description,
          unpickled_alarm.description,
        )

        self.assertEqual(
          self.alarm.blocked,
          unpickled_alarm.blocked,
        )

        self.assertEqual(
          self.alarm.acknowledged,
          unpickled_alarm.acknowledged,
        )

        self.assertEqual(
          self.alarm.enabled,
          unpickled_alarm.enabled,
        )

        self.assertEqual(
          self.alarm.consequences,
          unpickled_alarm.consequences,
        )

        self.assertEqual(
          self.alarm.more_info,
          unpickled_alarm.more_info,
        )

        self.assertEqual(
          self.alarm.state,
          unpickled_alarm.state,
        )

        self.assertEqual(
          self.alarm.on_delay,
          unpickled_alarm.on_delay,
        )

        self.assertEqual(
          self.alarm.off_delay,
          unpickled_alarm.off_delay,
        )

        self.assertEqual(
          self.alarm._activation_time,
          unpickled_alarm._activation_time,
        )

        self.assertEqual(
          self.alarm._is_reset_time,
          unpickled_alarm._is_reset_time,
        )

    def test_a_yaml_pickle(self):
        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        yml.register_class(AlarmAnalog)

        stream = StringIO()
        yml.dump(self.alarm, stream)
        s=stream.getvalue()
        unpickled_alarm = yml.load(s)

        self.assertEqual(self.alarm.alarm_value, unpickled_alarm.alarm_value)
        self.assertEqual(
          self.alarm.high_low_limit,
          unpickled_alarm.high_low_limit,
        )
        self.assertEqual(self.alarm.hysteresis, unpickled_alarm.hysteresis)

        self.assertEqual(self.alarm.description, unpickled_alarm.description)
        self.assertEqual(self.alarm.consequences, unpickled_alarm.consequences)
        self.assertEqual(self.alarm.more_info, unpickled_alarm.more_info)
        self.assertEqual(self.alarm.on_delay, unpickled_alarm.on_delay)
        self.assertEqual(self.alarm.off_delay, unpickled_alarm.off_delay)

    def test_alarm_high(self):
        self.alarm.evaluate_analog(29.0)
        self.assertFalse(self.alarm.input)

        # into alarm.
        self.alarm.evaluate_analog(31.0)
        self.assertTrue(self.alarm.input)

        # further into alarm.
        self.alarm.evaluate_analog(31.5)
        self.assertTrue(self.alarm.input)

        # out of alarm (note hysteresis)
        self.alarm.evaluate_analog(28.8)
        self.assertFalse(self.alarm.input)

        # back into alarm.
        self.alarm.evaluate_analog(30.3)
        self.assertTrue(self.alarm.input)

        # Drop out less than hysteresis.
        self.alarm.evaluate_analog(29.5)
        self.assertTrue(self.alarm.input)

        # Drop out more than hysteresis.
        self.alarm.evaluate_analog(28.8)
        self.assertFalse(self.alarm.input)


if __name__ == '__main__':
    unittest.main()
