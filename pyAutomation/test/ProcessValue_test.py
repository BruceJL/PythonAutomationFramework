import unittest
from DataObjects.PointAnalog import PointAnalog
from DataObjects.PointDiscrete import PointDiscrete
from DataObjects.Alarm import Alarm
from DataObjects.AlarmAnalog import AlarmAnalog
from DataObjects.ProcessValue import ProcessValue
import jsonpickle
import datetime


class TestProcessValue(unittest.TestCase):

    def setUp(self):
        point_pump_water_pressure = PointAnalog(
            name="pump_water_pressure",
            description="Pump water pressure",
            u_of_m="psi",
            hmi_writeable=False,
            # deadband=0.2,
            update_period=datetime.timedelta(seconds=1 / 3))

        point_pump_on_water_pressure = PointAnalog(
            name="pump_on_water_pressure",
            description="Pump water pressure on setpoint",
            u_of_m="psi",
            hmi_writeable=True,
            _value=115.0)

        point_pump_off_water_pressure = PointAnalog(
            name="pump_off_water_pressure",
            description="Pump water pressure off setpoint",
            u_of_m="psi",
            hmi_writeable=True,
            _value=125.0)
        
        alarm_h1_pump_water_pressure = AlarmAnalog(
            name="h1_pump_water_pressure",
            description="Pump pressure H1",
            alarm_value=128.0,
            on_delay=1.0,
            off_delay=1.0,
            hysteresis=1.0,
            high_low_limit="HIGH",
            consequences="The pump has been temporarily shut off",
            more_info="The pressure setpoint of the system has probably been set beyond the H1 level. "
                      "The H1 level provides a "
                      "safety mechanism and prevents the pump from overpressuring the system.")
        
        alarm_h2_pump_water_pressure = AlarmAnalog(
            name="h2_pump_water_pressure",
            description="Pump pressure H2",
            alarm_value=132.0,
            on_delay=0.0,
            off_delay=1.0,
            hysteresis=1.0,
            high_low_limit="HIGH",
            consequences="The system will attempt to bleed all pressure. The charge and relief valves will be "
                         "opened until this  alarm is acknowledged.",
            more_info="The pump relay is likely stuck closed. The system pressure will be bled to prevent"
                      "overpressure and prevent thermal failure of the pump by allowing water to circulate.")
        
        alarm_l1_pump_water_pressure = AlarmAnalog(
            name="l1_pump_water_pressure",
            description="Pump pressure L1",
            alarm_value=113.0,
            on_delay=2.0,
            off_delay=1.0,
            hysteresis=1.0,
            high_low_limit="LOW",
            consequences="The mist nozzles are performing at sub optimal levels.",
            more_info="The pump may have failed or a leak may have developed on the high pressure side")
        
        alarm_l2_pump_water_pressure = AlarmAnalog(
            name="l2_pump_water_pressure",
            description="Pump pressure L2",
            alarm_value=40.0,
            on_delay=5.0,
            off_delay=5.0,
            hysteresis=1.0,
            high_low_limit="LOW",
            consequences=" The lights will be shut off and locked out until this alarm is acknowledged."
                         "The plants are not being watered sufficiently.",
            more_info="The pump may have failed or a leak may have developed on the high pressure side")
        
        # Logic driven pump related alarms.
        alarm_pump_runtime_fault = Alarm(
            name="pump_runtime_fault",
            description="Pump runtime exceeded",
            on_delay=60.0,
            off_delay=1.0,
            consequences="The pump has been locked out until this alarm is acknowledged",
            more_info="The following may be happened: pump may be run dry, failing, or a leak may have developed.")
        
        # Active pressure decay constant. Measures how fast the pressure in the accumlator tank drops when the
        # valves are open. Too much indicates a leak, not enough and you've got a clog.
        point_active_pressure_decay = PointAnalog(
            name="active_pressure_decay",
            description="Active water pressure decay constant",
            u_of_m="%",
            hmi_writeable=False,
            # deadband=1.0
            )
        
        alarm_h1_active_pressure_decay = AlarmAnalog(
            name="h1_active_pressure_decay",
            description="Pressure decay high - misting clog detected",
            alarm_value=0.98,
            hysteresis=0.01,
            on_delay=180,
            off_delay=180,
            high_low_limit="HIGH",
            consequences="None",
            more_info="The system has detected that the pressure accumulator is not draing at the proper rate."
                      "It's likely  that there is a clog in the misting system that is prevent water delivery to the"
                      "plants.")
        
        alarm_l1_active_pressure_decay = AlarmAnalog(
            name="l1_active_pressure_decay",
            description="Pressure decay low - misting leak",
            alarm_value=0.95,
            hysteresis=0.01,
            on_delay=180,
            off_delay=180,
            high_low_limit="LOW",
            consequences="None",
            more_info="The system has detected that the pressure accumulator is not draining at the proper rate."
                      "It's likely  that there is a leak in the misting system."
                      " This may prevent the spray nozzles from operating properly.")
        
        process_active_pressure_decay = ProcessValue(point_active_pressure_decay)
        process_active_pressure_decay.high_display_limit = 1.0
        process_active_pressure_decay.low_display_limit = 0.0
        process_active_pressure_decay.add_alarm("H1", alarm_h1_active_pressure_decay)
        process_active_pressure_decay.add_alarm("L1", alarm_l1_active_pressure_decay)
        
        # Static pressure decay constant, Measure how much the system leaks when the pump is off and valves are closed.
        # Too much decay and there's a leak.
        point_static_pressure_decay = PointAnalog(
            name="static_pressure_decay",
            description="Static water pressure decay constant",
            u_of_m="%",
            hmi_writeable=False)
        
        alarm_l1_static_pressure_decay = AlarmAnalog(
            name="l1_static_pressure_decay",
            description="Pressure decay low - accumulator leak",
            alarm_value=0.99,
            hysteresis=0.01,
            on_delay=180,
            off_delay=180,
            high_low_limit="LOW")
        
        process_static_pressure_decay = ProcessValue(point_static_pressure_decay)
        process_static_pressure_decay.high_display_limit = 1.0
        process_static_pressure_decay.low_display_limit = 0.0
        process_static_pressure_decay.add_alarm("L1", alarm_l1_active_pressure_decay)
        
        point_run_pump = PointDiscrete(
            name="run_pump",
            description="Pump",
            on_state_description="On",
            off_state_description="Off",
            hmi_writeable=False)
        
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
        
    def test_json_pickle(self):
        pickle_text = jsonpickle.encode(self.point)
        unpickled_point = jsonpickle.decode(pickle_text)
        self.assertEqual(self.point.__dict__, unpickled_point.__dict__)


if __name__ == '__main__':
    unittest.main()
