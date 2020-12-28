from typing import TYPE_CHECKING
from datetime import datetime, timedelta
import logging
import jsonpickle
import rpyc
import pyAutomation.Supervisory.PointManager

if TYPE_CHECKING:
    from typing import List, Dict, Callable
    from pyAutomation.DataObjects.Alarm import Alarm
    from pyAutomation.DataObjects.PointAbstract import PointAbstract
    from pyAutomation.DataObjects.PointReadOnlyAbstract \
        import PointReadOnlyAbstract
    from pyAutomation.Supervisory import SupervisedThread

logger = logging.getLogger('supervisory')


# define the rpyc server
class RpcServer(rpyc.Service):
    active_alarm_list = None  # type: 'List[Alarm]'
    point_dict = {}           # type: 'Dict[str, PointAbstract]'
    thread_list = []          # type: 'List[SupervisedThread]'
    last_read_time = None     # type: 'datetime'
    global_alarm_list = {}    # type: 'Dict[str, Alarm]'
    get_hmi_point = None      # type: 'Callable'

    def __init__(self):
        self.point_list = {}  # type: 'Dict[PointReadOnlyAbstract]'
        super().__init__()

    def on_connect(self, conn) -> 'None':
        # code that runs when a connection is created
        # (to init the serivce, if needed)
        self.point_list.clear()
        logger.info("GUI Connection Established")

    def on_disconnect(self, conn) -> 'None':
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        logger.info("GUI Connection Destroyed")
        self.point_list.clear()

    def exposed_add_monitored_points(self, points: 'List[str]') -> 'None':
        assert self.point_dict is not None
        assert self.get_hmi_point is not None
        for p in points:
            logger.info("Adding point %s", p)
            point = self.get_hmi_point(p)
            assert point is not None
            self.point_list.update({p: point})
        self.last_read_time = datetime.now()

    def exposed_remove_monitored_points(self, points: List[str]) -> 'None':
        for p in points:
            self.point_list.pop(self.point_dict[p], None)

    def exposed_clear_monitored_points(self) -> 'None':
        logger.info("Clearning monitored points")
        self.point_list.clear()

    def exposed_get_hmi_points_list(self) -> 'str':
        if 0 == self.last_read_time:
            logger.debug("First request, transmitting all points.")
            p = self.point_list
        else:
            # logger.debug("Processing request with last_read_time of: %s",
            # str(self.last_read_time))
            p = {}
            for key, point in self.point_list.items():
                if (point.last_update - self.last_read_time)\
                  > timedelta(seconds=0):
                    p.update({key: point})
        self.last_read_time = datetime.now()
        pickle_text = jsonpickle.encode(p)
        # logger.debug("transmitting: " + pickle_text)
        return pickle_text

    def exposed_get_thread_list(self) -> 'List[SupervisedThread]':
        d = []
        for t in self.thread_list:
            d.append(t.pickle_dict)

        logger.debug("sending: %s", str(d))
        return jsonpickle.encode(d)

    def exposed_get_active_alarm_list(self) -> 'None':
        return jsonpickle.encode(self.active_alarm_list)

    def exposed_acknowledge_alarm(self, alarm: str) -> 'None':
        logger.info("RPC acknowledge received for %s", alarm)
        self.global_alarm_list[alarm].acknowledge()

    def exposed_set_hmi_value(self, point: str, value: str) -> 'None':
        logger.info("attempting to set %s to %s", point, value)
        p = pyAutomation.Supervisory.PointManager.find_point(point)
        p.hmi_value = value

    def exposed_toggle_point_force(self, point: str) -> 'None':
        p = pyAutomation.Supervisory.PointManager.find_point(point)
        p.forced = not p.forced

    def exposed_toggle_point_quality(self, point: str) -> 'None':
        p = pyAutomation.Supervisory.PointManager.find_point(point)
        p.quality = not p.quality
