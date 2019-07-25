import unittest
import jsonpickle
from time import sleep
from datetime import timedelta

from DataObjects.Alarm import Alarm
from Supervisory.AlarmHandler import AlarmHandler
import logging


class TestAlarm(unittest.TestCase):

    def setUp(self):
        self.alarm = Alarm(
            name="humidity_comm_failure",
            description="Temperature/humidity sensor communications failure",
            on_delay=5.0,
            off_delay=1.0,
            consequences="Freezer control is unreliable",
            more_info="System does not not ambient tempurature.")

        self.alarm.add_observer(self.name, self.interrupt)

        logger = logging.getLogger('controller')

        self.ah = AlarmHandler(
            name="alarm processer",
            period=timedelta(seconds=5),
            logger=logger
        )

        self.interrupts = 0

        Alarm.set_alarm_handler(self.ah)

    def test_json_pickle(self) -> None:
        pickle_text = jsonpickle.encode(self.alarm)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.alarm.__dict__, unpickled_point.__dict__)

    def test_alarm_with_timer(self) -> None:
        self.interrupts = 0
        self.alarm.on_delay = 5.0
        self.alarm.off_delay = 1.0

        # verify alarm in inactive.
        self.assertFalse(self.alarm.active)
        self.assertTrue(self.alarm._state == "OFF")
        self.assertTrue(self.alarm.alarm_state == "NORMAL")
        self.assertEqual(len(self.ah.active_alarm_list), 0)
        self.assertEqual(self.ah.active_alarm_timer_list_count, 0)

        # Turn on alarm. it's got a 1 second delay so make sure the alarm stays off.
        self.alarm.input = True
        self.assertFalse(self.alarm.active)
        self.assertEqual(self.alarm._state, "ON_DELAY")
        self.assertEqual(self.alarm.alarm_state, "NORMAL")
        self.assertEqual(len(self.ah.active_alarm_list), 0)
        sleep(0.1)
        self.assertEqual(self.ah.active_alarm_timer_list_count, 1)

        # wait for the alarm to be activated.
        sleep(5.1)
        self.assertTrue(self.alarm.active)
        self.assertEqual(self.alarm._state, "ALARM")
        self.assertEqual(self.alarm.alarm_state, "ACTIVE")
        self.assertEqual(len(self.ah.active_alarm_list), 1)
        self.assertEqual(1, self.interrupts)
        sleep(0.1)
        self.assertEqual(self.ah.active_alarm_timer_list_count, 0)

        # Turn off alarm, it's got a 1 second delay so  make sure the alarm is still one.
        self.alarm.input = False
        self.assertTrue(self.alarm.active)
        self.assertEqual(self.alarm._state, "OFF_DELAY")
        self.assertEqual(self.alarm.alarm_state, "ACTIVE")
        self.assertEqual(len(self.ah.active_alarm_list), 1)
        sleep(0.1)
        self.assertEqual(self.ah.active_alarm_timer_list_count, 1)

        # wait for the alarm to normal.
        sleep(1.1)
        self.assertFalse(self.alarm.active)
        self.assertEqual(self.alarm._state, "OFF")
        self.assertEqual(self.alarm.alarm_state, "RESET")
        self.assertEqual(2, self.interrupts)
        self.assertEqual(len(self.ah.active_alarm_list), 1)
        self.assertEqual(self.ah.active_alarm_timer_list_count, 0)

        # acknowledge the alarm ito ensure that it's removed from the active_alarm_list.
        self.alarm.acknowledge()
        self.assertEqual(len(self.ah.active_alarm_list), 0)
        self.assertFalse(self.alarm.active)
        self.assertEqual(self.alarm._state, "OFF")
        self.assertEqual(self.alarm.alarm_state, "NORMAL")
        self.assertEqual(len(self.ah.active_alarm_list), 0)
        self.assertEqual(self.ah.active_alarm_timer_list_count, 0)

    def test_alarm_no_timer(self) -> None:
        self.interrupts = 0
        # modify the alarm to remove the delays.
        self.alarm.on_delay = 0.0
        self.alarm.off_delay = 0.0

        # verify that the alarm is still normal.
        self.assertFalse(self.alarm.active)
        self.assertEqual(self.alarm.alarm_state, "NORMAL")
        self.assertEqual(len(self.ah.active_alarm_list), 0)

        # activate the alarm
        self.alarm.input = True
        self.assertTrue(self.alarm.active)
        self.assertEqual(self.alarm.alarm_state, "ACTIVE")
        self.assertEqual(len(self.ah.active_alarm_list), 1)
        self.assertEqual(1, self.interrupts)

        # acknowledge the alarm
        self.alarm.acknowledge()
        self.assertEqual(self.alarm.alarm_state, "ACKNOWLEDGED")
        self.assertEqual(len(self.ah.active_alarm_list), 1)

        # reset the alarm
        self.alarm.input = False
        self.assertEqual(self.alarm.alarm_state, "NORMAL")
        self.assertEqual(len(self.ah.active_alarm_list), 0)
        self.assertEqual(2, self.interrupts)

    def tearDown(self):
        self.ah.quit()

    def interrupt(self, s: str):
        self.interrupts += 1


if __name__ == '__main__':
    unittest.main()
