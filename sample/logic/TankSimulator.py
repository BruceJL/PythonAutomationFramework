from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointHandler import PointHandler
import datetime


# simple pump controller that

class TankSimulator(SupervisedThread, PointHandler):

    _points_list = {
      'point_liquid_level':          {'type': 'ProcessValue',  'access': 'rw'},
      'point_fill_rate':             {'type': 'PointAnalog',   'access': 'rw'},
      'point_run_pump_1':            {'type': 'PointDiscrete', 'access': 'ro'},
      'point_pump_1_rate_drain_rate':{'type': 'PointAnalog',   'access': 'rw'},
      'point_run_pump_2':            {'type': 'PointDiscrete', 'access': 'ro'},
      'point_pump_2_rate_drain_rate':{'type': 'PointAnalog',   'access': 'rw'},
    }

    def __init__(self, name, logger):
        self.level = 0.0
        self.period = 0.5 # Run the loop every 0.5 seconds.
        self.last_time = datetime.datetime.now()

        super().__init__(
            name=name,
            loop=self.loop,
            period=self.period,
            logger=logger)

    def config(self, config: dict):
        # register interest in points that will cause the routine to run.
        self.point_run_pump_1.add_observer(self.name, self.interrupt)
        self.point_run_pump_2.add_observer(self.name, self.interrupt)

    def loop(self) -> float:

        # Just blindly accept the drain and fill rates for the pumps
        # should probably do some bounds checking here, but you get the
        # idea.

        if(self.point_fill_rate.request_value is not None):
            self.point_fill_rate.value = self.point_fill_rate.request_value
            self.point_fill_rate.request_value = None

        if(self.point_pump_1_rate_drain_rate.request_value is not None):
            self.point_pump_1_rate_drain_rate.value = self.point_pump_1_rate_drain_rate.request_value
            self.point_pump_1_rate_drain_rate.request_value = None

        if(self.point_pump_2_rate_drain_rate.request_value is not None):
            self.point_pump_2_rate_drain_rate.value = self.point_pump_2_rate_drain_rate.request_value
            self.point_pump_2_rate_drain_rate.request_value = None

        now = datetime.datetime.now()
        time_delta = datetime.timedelta.total_seconds(now - self.last_time)/60.0
        self.last_time = now

        # --------------------------------------------------
        # Liquid level calculation
        # --------------------------------------------------
        self.point_liquid_level.value += \
          self.point_fill_rate.value * time_delta

        if self.point_run_pump_1.value:
            self.point_liquid_level.value -= \
              self.point_pump_1_rate_drain_rate.value * time_delta

        if self.point_run_pump_2.value  :
            self.point_liquid_level.value -= \
              self.point_pump_2_rate_drain_rate.value * time_delta

        return None
