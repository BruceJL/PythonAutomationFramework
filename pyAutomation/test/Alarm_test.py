import unittest
import jsonpickle
import datetime
import sys
from time import sleep
from mock import patch, Mock

from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.Supervisory.AlarmHandler import AlarmHandler
from pyAutomation.Supervisory.Interruptable import Interruptable
import logging


class TestAlarm(unittest.TestCase, Interruptable):

    @classmethod
    def setUpClass(self):
        logger = 'controller'
        self.logger = logging.getLogger(logger)
        self.logger.setLevel('DEBUG')
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        self.formatter = logging.Formatter(
          '%(asctime)s - %(levelname)s - %(module)s.%(funcName)s() - %(message)s')

        self.alarm_logger = logging.getLogger('alarms')
        self.alarm_logger.setLevel('DEBUG')
        self.alarm_logger.addHandler(logging.StreamHandler(sys.stdout))

        self.name = 'Alarm_test'
        self.alarm = Alarm(
          description="Temperature/humidity sensor communications failure",
          on_delay=5.0,
          off_delay=1.0,
          consequences="Cooling control is unreliable",
          more_info="System does not know ambient temperature")

        self.alarm.config("test alarm")

        self.alarm.input = False

        self.ah = AlarmHandler(
            logger=logger,
            name="alarm processer",
            #period=datetime.timedelta(seconds=5),
        )

        Alarm.set_alarm_handler(self.ah)
        self.logger.info("setUpClass completed.")

    @classmethod
    def tearDownClass(self):
        self.logger.info("tearDownClass started.")

    def interrupt(self, name: 'str') -> 'None':
        self.interrupts += 1

    def setUp(self):
        self.logger.info("Alarm_test: setUp")
        self.interrupts = 0
        # watch to make sure that the alarm executes its callbacks.
        # N.B. This cannot be done in setUpClass. I guess the object isn't
        # fully instanciated at that point.
        self.alarm.add_observer(self.name, self.interrupt)

    def tearDown(self) -> 'None':
        self.logger.info("Alarm_test: teardown")
        # watch to make sure that the alarm executes its callbacks.
        self.alarm.del_observer(self.name)

    def test_a_json_pickle(self) -> 'None':
        # n.b. the a in the test name is so that this test gets executed first,
        # the Mock module doesn't seem to want to relent outside of the 'with'
        # block.

        self.logger.info("----Start test_json_pickle----")
        self.logger.debug(self.alarm._activation_time.isoformat())
        pickle_text = jsonpickle.encode(self.alarm)
        unpickled_point = jsonpickle.decode(pickle_text)

        self.assertEqual(self.alarm.name, unpickled_point.name)
        self.assertEqual(self.alarm.description, unpickled_point.description)
        self.assertEqual(self.alarm.blocked, unpickled_point.blocked)
        self.assertEqual(self.alarm.acknowledged, unpickled_point.acknowledged)
        self.assertEqual(self.alarm.enabled, unpickled_point.enabled)
        self.assertEqual(self.alarm.consequences, unpickled_point.consequences)
        self.assertEqual(self.alarm.more_info, unpickled_point.more_info)
        self.assertEqual(self.alarm.state, unpickled_point.state)
        self.assertEqual(self.alarm.on_delay, unpickled_point.on_delay)
        self.assertEqual(self.alarm.off_delay, unpickled_point.off_delay)
        self.assertEqual(self.alarm._activation_time, unpickled_point._activation_time)
        self.assertEqual(self.alarm._is_reset_time, unpickled_point._is_reset_time)

        def test_a_yaml_pickle(self):
            # n.b. the a in the test name is so that this test gets executed first,
            # the Mock module doesn't seem to want to relent outside of the 'with'
            # block.
            yml = ruamel.yaml.YAML(typ='safe', pure=True)
            yml.default_flow_style = False
            yml.indent(sequence=4, offset=2)

            yml.register_class(AlarmAnalog)

            stream = StringIO()
            yml.dump(self.alarm, stream)
            s=stream.getvalue()
            unpickled_alarm = yml.load(s)

            self.assertEqual(self.alarm.description, unpickled_alarm.description)
            self.assertEqual(self.alarm.consequences, unpickled_alarm.consequences)
            self.assertEqual(self.alarm.more_info, unpickled_alarm.more_info)
            self.assertEqual(self.alarm.on_delay, unpickled_alarm.on_delay)
            self.assertEqual(self.alarm.off_delay, unpickled_alarm.off_delay)


    def test_alarm_with_timer(self) -> 'None':
        self.logger.info("---- Start test_alarm_with_timer ----")
        with patch('pyAutomation.DataObjects.Alarm.datetime') as datetime_mock,\
          patch('pyAutomation.DataObjects.Alarm.time') as time_mock:
            self.interrupts = 0
            self.alarm.on_delay = 5.0
            self.alarm.off_delay = 2.0

            # verify alarm in inactive.
            self.assertFalse(self.alarm.active)
            self.assertTrue(self.alarm._state == "OFF")
            self.assertTrue(self.alarm.alarm_state == "NORMAL")

            # set the time.
            time_mock.monotonic = Mock(return_value = 0.0)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:00.000', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("0.0 second mark.")

            # Turn on alarm. it's got a 5 second delay so make sure the alarm stays off.
            self.logger.info("Turning on alarm.")
            self.alarm.input = True

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            self.assertFalse(self.alarm.active)
            self.assertEqual(self.alarm._state, "ON_DELAY")
            self.assertEqual(self.alarm.alarm_state, "NORMAL")

            # jump 1 second in the future
            time_mock.monotonic = Mock(return_value = 1.0)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:01.000', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("1.0 second mark.")

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            self.assertFalse(self.alarm.active)
            self.assertEqual(self.alarm._state, "ON_DELAY")
            self.assertEqual(self.alarm.alarm_state, "NORMAL")

            # jump 4.001 seconds in the future
            time_mock.monotonic = Mock(return_value = 5.001)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:05.001', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("5.001 second mark.")

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            self.assertTrue(self.alarm.active)
            self.assertEqual(self.alarm._state, "ALARM")
            self.assertEqual(self.alarm.alarm_state, "ACTIVE")
            self.assertEqual(1, self.interrupts)

            # jump to 6 seconds.
            time_mock.monotonic = Mock(return_value = 6.0)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:06.000', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("6.00 second mark.")

            # Turn the alarm off and run the interrupt handler.
            self.logger.info("Turning off alarm.")
            self.alarm.input = False

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            # The alarm's got a 2 second delay so  make sure the alarm is still on.
            self.assertTrue(self.alarm.active)
            self.assertEqual(self.alarm._state, "OFF_DELAY")
            self.assertEqual(self.alarm.alarm_state, "ACTIVE")

            # jump to 7 seconds.
            time_mock.monotonic = Mock(return_value = 7.0)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:06.000', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("7.0 second mark.")

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            # The alarm's got a 2 second delay so  make sure the alarm is still on.
            self.assertTrue(self.alarm.active)
            self.assertEqual(self.alarm._state, "OFF_DELAY")
            self.assertEqual(self.alarm.alarm_state, "ACTIVE")

            # jump to 8.001 seconds..
            time_mock.monotonic = Mock(return_value = 8.001)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:08.001', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("8.001 second mark.")

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            self.assertFalse(self.alarm.active)
            self.assertEqual(self.alarm._state, "OFF")
            self.assertEqual(self.alarm.alarm_state, "RESET")
            self.assertEqual(2, self.interrupts)

            # jump to 9 seconds.
            time_mock.monotonic = Mock(return_value = 9.0)
            datetime_mock.now = Mock(return_value=datetime.datetime.strptime('2019/01/01 00:00:09.000', "%Y/%m/%d %H:%M:%S.%f"))
            self.logger.info("9.0 second mark.")

            # acknowledge the alarm ito ensure that it's removed from the active_alarm_list.
            self.alarm.acknowledge()

            # pretend to run the alarm handler..
            self.alarm.evaluate()

            self.assertEqual(len(self.ah.active_alarm_list), 0)
            self.assertFalse(self.alarm.active)
            self.assertEqual(self.alarm._state, "OFF")
            self.assertEqual(self.alarm.alarm_state, "NORMAL")

    def test_alarm_no_timer(self) -> 'None':
        self.logger.info("---- Starting test_alarm_no_timer ----")
        self.interrupts = 0
        # modify the alarm to remove the delays.
        self.alarm.on_delay = 0.0
        self.alarm.off_delay = 0.0

        # verify that the alarm is still normal.
        self.assertFalse(self.alarm.active)
        self.assertEqual(self.alarm.alarm_state, "NORMAL")

        # activate the alarm
        self.alarm.input = True
        self.assertTrue(self.alarm.active)
        self.assertEqual(self.alarm.alarm_state, "ACTIVE")
        self.assertEqual(1, self.interrupts)

        # acknowledge the alarm
        self.alarm.acknowledge()
        self.assertEqual(self.alarm.alarm_state, "ACKNOWLEDGED")

        # reset the alarm
        self.alarm.input = False
        self.assertEqual(self.alarm.alarm_state, "NORMAL")
        self.assertEqual(2, self.interrupts)

if __name__ == '__main__':
    unittest.main()
