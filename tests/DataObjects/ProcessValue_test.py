import unittest
import jsonpickle

from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.AlarmAnalog import AlarmAnalog
from pyAutomation.DataObjects.ProcessValue import ProcessValue

from pyAutomation.Supervisory.PointManager import PointManager

test_process_point_name = "test_process_point_name"


class TestProcessValue(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        point_pump_water_pressure = PointAnalog(
          description="Pump water pressure",
          u_of_m="psi",
          hmi_writeable=False,
          update_period=0.333333,
          value = 123.45,
        )

        # PointManager.add_to_database(
        #   name = "pump_water_pressure",
        #   obj = point_pump_water_pressure,
        # )

        # point_pump_water_pressure.value = 123.45

        point_pump_on_water_pressure = PointAnalog(
          description="Pump water pressure on setpoint",
          u_of_m="psi",
          hmi_writeable=True,
          value=115.0,
        )

        # PointManager.add_to_database(
        #   name = "pump_on_water_pressure",
        #   obj = point_pump_on_water_pressure,
        # )

        point_pump_off_water_pressure = PointAnalog(
          description="Pump water pressure off setpoint",
          u_of_m="psi",
          hmi_writeable=True,
          value=125.0,
        )

        # PointManager.add_to_database(
        #   name = "pump_off_water_pressure",
        #   obj = point_pump_off_water_pressure,
        # )

        alarm_h1_pump_water_pressure = AlarmAnalog(
          description="Pump pressure H1",
          alarm_value=128.0,
          on_delay=1.0,
          off_delay=1.0,
          hysteresis=1.0,
          high_low_limit="HIGH",
          consequences="The pump has been temporarily shut off",
          more_info=
            "The pressure setpoint of the system has probably been set beyond "
            "the H1 level. The H1 level provides a safety mechanism and "
            "prevents the pump from overpressuring the system.",
        )

        # PointManager.add_to_database(
        #   name = "h1_pump_water_pressure",
        #   obj = alarm_h1_pump_water_pressure,
        # )

        alarm_h2_pump_water_pressure = AlarmAnalog(
          description="Pump pressure H2",
          alarm_value=132.0,
          on_delay=0.0,
          off_delay=1.0,
          hysteresis=1.0,
          high_low_limit="HIGH",
          consequences=
            "The system will attempt to bleed all pressure. The charge and "
            "relief valves will be opened until this  alarm is acknowledged.",
          more_info=
            "The pump relay is likely stuck closed. The system pressure will "
            "be bled to prevent overpressure and prevent thermal failure of the"
            "pump by allowing water to circulate.",
        )

        # PointManager.add_to_database(
        #   name = "h2_pump_water_pressure",
        #   obj = alarm_h2_pump_water_pressure,
        # )

        alarm_l1_pump_water_pressure = AlarmAnalog(
          description="Pump pressure L1",
          alarm_value=113.0,
          on_delay=2.0,
          off_delay=1.0,
          hysteresis=1.0,
          high_low_limit="LOW",
          consequences="Feed system is will not satisfy demand",
          more_info="The pump may have failed or a leak may have developed on "
            "the high pressure side",
        )

        # PointManager.add_to_database(
        #   name = "l1_pump_water_pressure",
        #   obj = alarm_l1_pump_water_pressure,
        # )

        alarm_l2_pump_water_pressure = AlarmAnalog(
          description="Pump pressure L2",
          alarm_value=40.0,
          on_delay=5.0,
          off_delay=5.0,
          hysteresis=1.0,
          high_low_limit="LOW",
          consequences="System will be shut down.",
          more_info="The pump may have failed or a leak may have developed on "
            "the high pressure side",
        )

        # PointManager.add_to_database(
        #   name = "l2_pump_water_pressure",
        #   obj = alarm_l2_pump_water_pressure,
        # )

        # Logic driven pump related alarms.
        alarm_pump_runtime_fault = Alarm(
          description="Pump runtime exceeded",
          on_delay=60.0,
          off_delay=1.0,
          consequences="The pump has been locked out until this alarm is "
            "acknowledged",
          more_info="The following may be happened: pump may be run dry, "
            "failing, or a leak may have developed.",
        )
        PointManager.add_to_database(
          name = "pump_runtime_fault",
          obj = alarm_pump_runtime_fault,
        )

        # Active pressure decay constant. Measures how fast the pressure in the
        # accumlator tank drops when the valves are open. Too much indicates a
        # leak, not enough and you've got a clog.
        point_active_pressure_decay = PointAnalog(
          description="Active water pressure decay constant",
          u_of_m="%",
          hmi_writeable=False,
        )
        # PointManager.add_to_database(
        #   name = "active_pressure_decay",
        #   obj = point_active_pressure_decay,
        # )

        alarm_h1_active_pressure_decay = AlarmAnalog(
          description="Pressure decay high - misting clog detected",
          alarm_value=0.98,
          hysteresis=0.01,
          on_delay=180,
          off_delay=180,
          high_low_limit="HIGH",
          consequences="None",
          more_info="The system has detected that the pressure accumulator is "
            + "not draing at the proper rate.",
        )
        # PointManager.add_to_database(
        #   name = "active_pressure_decay",
        #   obj = alarm_h1_active_pressure_decay,
        # )

        alarm_l1_active_pressure_decay = AlarmAnalog(
          description="Pressure decay low - misting leak",
          alarm_value=0.95,
          hysteresis=0.01,
          on_delay=180,
          off_delay=180,
          high_low_limit="LOW",
          consequences="None",
          more_info="The system has detected that the pressure accumulator is "
          "not draining at the proper rate."
        )
        # PointManager.add_to_database(
        #   name = "l1_active_pressure_decay",
        #   obj = alarm_l1_active_pressure_decay,
        # )

        process_active_pressure_decay = \
          ProcessValue(point_active_pressure_decay)
        process_active_pressure_decay.high_display_limit = 1.0
        process_active_pressure_decay.low_display_limit = 0.0

        process_active_pressure_decay.add_alarm(
          "H1",
          alarm_h1_active_pressure_decay
        )

        process_active_pressure_decay.add_alarm(
          "L1",
          alarm_l1_active_pressure_decay
        )

        # Static pressure decay constant, Measure how much the system leaks when
        # the pump is off and valves are closed. Too much decay and there's a
        # leak.
        point_static_pressure_decay = PointAnalog(
          description="Static water pressure decay constant",
          u_of_m="%",
          hmi_writeable=False,
        )

        # PointManager.add_to_database(
        #   name = "static_pressure_decay",
        #   obj = point_static_pressure_decay,
        # )

        alarm_l1_static_pressure_decay = AlarmAnalog(
          description="Pressure decay low - accumulator leak",
          alarm_value=0.99,
          hysteresis=0.01,
          on_delay=180,
          off_delay=180,
          high_low_limit="LOW",
        )

        # PointManager.add_to_database(
        #   name = "l1_static_pressure_decay",
        #   obj = alarm_l1_static_pressure_decay,
        # )

        process_static_pressure_decay = ProcessValue(
          point_static_pressure_decay
        )
        process_static_pressure_decay.high_display_limit = 1.0
        process_static_pressure_decay.low_display_limit = 0.0
        process_static_pressure_decay.add_alarm(
          "L1",
          alarm_l1_static_pressure_decay
        )

        # PointManager.add_to_database(
        #   name = "static_pressure_decay",
        #   obj = process_static_pressure_decay,
        # )

        point_run_pump = PointDiscrete(
          description="Pump",
          on_state_description="On",
          off_state_description="Off",
          hmi_writeable=False,
        )
        # PointManager.add_to_database(
        #   name = "run_pump",
        #   obj = point_run_pump,
        # )

        # Pump ProcessValue assembly.
        self.point = ProcessValue(point_pump_water_pressure)
        self.point.high_display_limit = 135.0
        self.point.low_display_limit = 110.0
        self.point.add_control_point("cut_in", point_pump_on_water_pressure)
        self.point.add_control_point("cut_out", point_pump_off_water_pressure)
        self.point.add_related_point("run", point_run_pump)

        self.point.add_related_point(
          "decay_static",
          process_static_pressure_decay,
        )

        self.point.add_related_point(
          "decay_active",
          process_active_pressure_decay,
        )
        self.point.add_alarm("H1", alarm_h1_pump_water_pressure)
        self.point.add_alarm("H2", alarm_h2_pump_water_pressure)
        self.point.add_alarm("L1", alarm_l1_pump_water_pressure)
        self.point.add_alarm("L2", alarm_l2_pump_water_pressure)

        PointManager.add_to_database(
          name = test_process_point_name,
          obj = self.point,
        )

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.value, unpickled_point.value)

    def test_yaml_pickle(self):
        s = PointManager().dump_database_to_yaml()
        # print (f"YAML:\n {s}")
        PointManager().clear_database
        PointManager().load_points_from_yaml_string(s)

        PointManager().find_point(test_process_point_name)

        # Can't do the assertEquals, as it tests the value and that doesn't
        # get included in the yaml dict.

        # self.assertEqual(self.point, unpickled_point)


if __name__ == '__main__':
    unittest.main()
