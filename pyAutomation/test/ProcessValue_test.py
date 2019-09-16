from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointDiscrete import PointDiscrete
from DataObjects.Alarm import Alarm
from DataObjects.AlarmAnalog import AlarmAnalog
from DataObjects.ProcessValue import ProcessValue
from DataObjects.PointReadOnly import PointReadOnly

import unittest
import jsonpickle
import datetime
import ruamel.yaml
from ruamel.yaml.compat import StringIO


class TestProcessValue(unittest.TestCase):

    def setUp(self):
        point_pump_water_pressure = PointAnalog(
          description="Pump water pressure",
          u_of_m="psi",
          hmi_writeable=False,
          update_period=0.333333,
        )
        point_pump_water_pressure.config("pump_water_pressure")
        point_pump_water_pressure.value = 123.45

        point_pump_on_water_pressure = PointAnalog(
          description="Pump water pressure on setpoint",
          u_of_m="psi",
          hmi_writeable=True,
          value=115.0,
        )
        point_pump_on_water_pressure.config("pump_on_water_pressure")

        point_pump_off_water_pressure = PointAnalog(
          description="Pump water pressure off setpoint",
          u_of_m="psi",
          hmi_writeable=True,
          value=125.0,
        )
        point_pump_off_water_pressure.config("pump_off_water_pressure")

        alarm_h1_pump_water_pressure = AlarmAnalog(
          description="Pump pressure H1",
          alarm_value=128.0,
          on_delay=1.0,
          off_delay=1.0,
          hysteresis=1.0,
          high_low_limit="HIGH",
          consequences="The pump has been temporarily shut off",
          more_info=
            "The pressure setpoint of the system has probably been set beyond the H1 level. "
            "The H1 level provides a "
            "safety mechanism and prevents the pump from overpressuring the system.",
        )
        alarm_h1_pump_water_pressure.config("h1_pump_water_pressure")

        alarm_h2_pump_water_pressure = AlarmAnalog(
          description="Pump pressure H2",
          alarm_value=132.0,
          on_delay=0.0,
          off_delay=1.0,
          hysteresis=1.0,
          high_low_limit="HIGH",
          consequences=
            "The system will attempt to bleed all pressure. The charge and relief valves will be "
            "opened until this  alarm is acknowledged.",
          more_info=
            "The pump relay is likely stuck closed. The system pressure will be bled to prevent"
            "overpressure and prevent thermal failure of the pump by allowing water to circulate.",
        )
        alarm_h2_pump_water_pressure.config("h2_pump_water_pressure")

        alarm_l1_pump_water_pressure = AlarmAnalog(
          description="Pump pressure L1",
          alarm_value=113.0,
          on_delay=2.0,
          off_delay=1.0,
          hysteresis=1.0,
          high_low_limit="LOW",
          consequences="Feed system is will not satisfy demand",
          more_info="The pump may have failed or a leak may have developed on the high pressure side",
        )
        alarm_l1_pump_water_pressure.config("l1_pump_water_pressure")

        alarm_l2_pump_water_pressure = AlarmAnalog(
          description="Pump pressure L2",
          alarm_value=40.0,
          on_delay=5.0,
          off_delay=5.0,
          hysteresis=1.0,
          high_low_limit="LOW",
          consequences="System will be shut down.",
          more_info="The pump may have failed or a leak may have developed on the high pressure side",
        )
        alarm_l1_pump_water_pressure.config("l2_pump_water_pressure")

        # Logic driven pump related alarms.
        alarm_pump_runtime_fault = Alarm(
          description="Pump runtime exceeded",
          on_delay=60.0,
          off_delay=1.0,
          consequences="The pump has been locked out until this alarm is acknowledged",
          more_info="The following may be happened: pump may be run dry, failing, or a leak may have developed.",
        )
        alarm_pump_runtime_fault.config("pump_runtime_fault")

        # Active pressure decay constant. Measures how fast the pressure in the accumlator tank drops when the
        # valves are open. Too much indicates a leak, not enough and you've got a clog.
        point_active_pressure_decay = PointAnalog(
          description="Active water pressure decay constant",
          u_of_m="%",
          hmi_writeable=False,
        )
        point_active_pressure_decay.config("active_pressure_decay")

        alarm_h1_active_pressure_decay = AlarmAnalog(
          description="Pressure decay high - misting clog detected",
          alarm_value=0.98,
          hysteresis=0.01,
          on_delay=180,
          off_delay=180,
          high_low_limit="HIGH",
          consequences="None",
          more_info="The system has detected that the pressure accumulator is not draing at the proper rate.",
        )
        alarm_h1_active_pressure_decay.config("h1_active_pressure_decay")

        alarm_l1_active_pressure_decay = AlarmAnalog(
          description="Pressure decay low - misting leak",
          alarm_value=0.95,
          hysteresis=0.01,
          on_delay=180,
          off_delay=180,
          high_low_limit="LOW",
          consequences="None",
          more_info="The system has detected that the pressure accumulator is not draining at the proper rate."
        )
        alarm_l1_active_pressure_decay.config("l1_active_pressure_decay")

        process_active_pressure_decay = ProcessValue(point_active_pressure_decay)
        process_active_pressure_decay.high_display_limit = 1.0
        process_active_pressure_decay.low_display_limit = 0.0
        process_active_pressure_decay.add_alarm("H1", alarm_h1_active_pressure_decay)
        process_active_pressure_decay.add_alarm("L1", alarm_l1_active_pressure_decay)

        # Static pressure decay constant, Measure how much the system leaks when the pump is off and valves are closed.
        # Too much decay and there's a leak.
        point_static_pressure_decay = PointAnalog(
          description="Static water pressure decay constant",
          u_of_m="%",
          hmi_writeable=False,
        )
        point_static_pressure_decay.config("static_pressure_decay")

        alarm_l1_static_pressure_decay = AlarmAnalog(
          description="Pressure decay low - accumulator leak",
          alarm_value=0.99,
          hysteresis=0.01,
          on_delay=180,
          off_delay=180,
          high_low_limit="LOW",
        )
        alarm_l1_static_pressure_decay.config("l1_static_pressure_decay")

        process_static_pressure_decay = ProcessValue(point_static_pressure_decay)
        process_static_pressure_decay.high_display_limit = 1.0
        process_static_pressure_decay.low_display_limit = 0.0
        process_static_pressure_decay.add_alarm("L1", alarm_l1_active_pressure_decay)

        point_run_pump = PointDiscrete(
          description="Pump",
          on_state_description="On",
          off_state_description="Off",
          hmi_writeable=False,
        )
        point_run_pump.config("run_pump")

        # Pump ProcessValue assembly.
        self.point = ProcessValue(point_pump_water_pressure)
        self.point.high_display_limit = 135.0
        self.point.low_display_limit = 110.0
        self.point.add_control_point("cut_in", point_pump_on_water_pressure)
        self.point.add_control_point("cut_out", point_pump_off_water_pressure)
        self.point.add_related_point("run", point_run_pump)
        self.point.add_related_point("decay_static", process_static_pressure_decay)
        self.point.add_related_point("decay_active", process_active_pressure_decay)
        self.point.add_alarm("H1", alarm_h1_pump_water_pressure)
        self.point.add_alarm("H2", alarm_h2_pump_water_pressure)
        self.point.add_alarm("L1", alarm_l1_pump_water_pressure)
        self.point.add_alarm("L2", alarm_l2_pump_water_pressure)

        self.point.config("pump_water_pressure")

    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.value, unpickled_point.value)

    def test_yaml_pickle(self):
        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        yml.register_class(ProcessValue)
        yml.register_class(PointAnalog)
        yml.register_class(Alarm)
        yml.register_class(AlarmAnalog)
        yml.register_class(PointDiscrete)
        yml.register_class(PointReadOnly)

        stream = StringIO()
        yml.dump(self.point, stream)
        s=stream.getvalue()
        # print(s)
        unpickled_point = yml.load(s)
        unpickled_point.config("test_scaled_point")

        self.assertEqual(self.point.description, unpickled_point.description)


if __name__ == '__main__':
    unittest.main()
