from .InductiveLoad import InductiveLoad
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointHandler import PointHandler
import datetime


# simple pump controller that

class PumpController(SupervisedThread, PointHandler):

    _points_list = {
      'point_liquid_level':          {'type': 'ProcessValue',  'access': 'ro'},
      'point_run_pump_1':            {'type': 'PointDiscrete', 'access': 'rw'},
      'alarm_pump_runtime_fault':    {'type': 'Alarm',         'access': 'rw'},
      'point_run_pump_2':            {'type': 'PointDiscrete', 'access': 'rw'},
    }

    def __init__(self, name, logger):
        self.period = None
        self.pump_timer = None  # internal timer variable.
        self.state = "IDLE"

        self.pump = None

        super().__init__(
            name=name,
            loop=self.loop,
            period=self.period,
            logger=logger)

    def config(self, config: dict):

        self.primary_pump = InductiveLoad(
            description="Lead Pump",
            inrush_delay=2.0,  # seconds
            cool_down_delay=10.0,  # seconds
            point_run=self.point_run_pump_1,
            inrush_circuit="600VAC",
        )

        self.backup_pump = InductiveLoad(
            description="Lag Pump",
            inrush_delay=2.0,  # seconds
            cool_down_delay=10.0,  # seconds
            point_run=self.point_run_pump_2,
            inrush_circuit="600VAC",
        )

        # register interest in points that will cause the routine to run.
        self.point_liquid_level.add_observer(self.name, self.interrupt)
        self.alarm_pump_runtime_fault.add_observer(self.name, self.interrupt)
        self.point_liquid_level.alarms['H2'].add_observer(self.name, self.interrupt)

    def loop(self) -> float:
        # --------------------------------------------------
        # Pump run routine
        # --------------------------------------------------

        sleep_time = None  # The default sleep time is to run from only point
                           # value interrupts.

        # --------------------------------------------------
        # Failsafe logic
        # Put the pump system into failsafe mode if:
        #   - an o
        #   - a loss of pressure signal is detected, or
        #   - the pump has been running too long.
        if not self.point_liquid_level.quality:
            self.state == "OFFLINE"
            self.logger.warning("LIQUID LEVEL SENSOR FAILURE, PUMP CONTROL DISABLED.")
            self.primary_pump.run(False)
            self.backup_pump.run(False)

        if     "OFFLINE" == self.state \
           and self.point_liquid_level.quality:
             self.state == "IDLE"
             self.logger.warning("LIQUID LEVEL SENSOR RESTORED. PUMP CONTROL ENABLED.")

        if     "IDLE" == self.state \
          and self.point_liquid_level.value >  self.point_liquid_level.control_points['cut_in_1'].value:
            self.state = "RUN_PRIMARY_PUMP"
            self.timer = datetime.datetime.now()
            self.last_level = self.point_liquid_level.value
            self.primary_pump.run(True)

        if    "RUN_PRIMARY_PUMP" == self.state \
          and self.point_liquid_level.value >  self.point_liquid_level.control_points['cut_in_2'].value:
            self.state = "RUN_BACKUP_PUMP"
            self.timer = datetime.datetime.now()
            self.backup_pump.run(True)

        if   "RUN_PRIMARY_PUMP" == self.state \
          or "RUN_BACKUP_PUMP" == self.state:

            if self.timer + datetime.timedelta(seconds=5) < datetime.datetime.now():
                if self.point_liquid_level.value > self.last_level:
                    self.alarm_pump_runtime_fault.input = True
                else:
                    self.alarm_pump_runtime_fault.input = False

                self.last_level = self.point_liquid_level.value

            if self.primary_pump.run_timer > 300.0:
                self.alarm_pump_runtime_fault.input = True

            if self.point_liquid_level.value <  self.point_liquid_level.control_points['cut_out'].value:
                self.state = "IDLE"
                self.primary_pump.run(False)
                self.backup_pump.run(False)
                self.alarm_pump_runtime_fault.input = False

                if self.primary_pump.run_timer < 300.0:
                    self.alarm_pump_runtime_fault.input = False

        primary_sleep_time = self.primary_pump.evaluate()
        backup_sleep_time = self.backup_pump.evaluate()
        t = super().get_lowest_sleep_time(primary_sleep_time, sleep_time)
        t = super().get_lowest_sleep_time(backup_sleep_time, t)
        return t
