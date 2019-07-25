import jsonpickle
import rpyc
from typing import List, TYPE_CHECKING
from datetime import datetime, timedelta
import logging

if TYPE_CHECKING:
    from pyAutomation.DataObjects.Alarm import Alarm
    from pyAutomation.DataObjects.PointAbstract import PointAbstract
    from pyAutomation.DataObjects.PointReadOnlyAbstract import PointReadOnlyAbstract
    from pyAutomation.Supervisory.SupervisedThread import SupervisedThread

logger = logging.getLogger('supervisory')


# define the rpyc server
class RpcServer(rpyc.Service):
    active_alarm_list = None  # type: List[Alarm]
    point_dict = {}  # type: Dict[str, PointAbstract]
    thread_list = [] # type: List[SupervisedThread]
    last_read_time = None  # type: datetime
    global_alarm_list = None  # type: Dict[str, Alarm]
    remote_point_dict = {} # type: Dict[PointAbstract]
    get_hmi_point = None

    def on_connect(self, credentials):
        # code that runs when a connection is created
        # (to init the serivce, if needed)
        logger.info("GUI Connection Established")
        self.point_list = []  # type: List[PointReadOnlyAbstract]

    def on_disconnect(self):
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        logger.info("GUI Connection Destroyed")
        self.point_list.clear()

    def add_monitored_points(self, points: List[str]) -> None:
        assert self.point_dict is not None
        assert self.get_hmi_point is not None
        for p in points:
            logger.info("Adding point " + p)
            point = self.get_hmi_point(p)
            assert point is not None
            self.remote_point_dict.update({p: point})
        self.last_read_time = 0

    def remove_monitored_points(self, points: List[str]) -> None:
        for p in points:
            self.remote_point_dict.remove(self.point_dict[p])

    def clear_monitored_points(self) -> None:
        self.remote_point_dict.clear()

    def exposed_get_hmi_points_list(self):  # this is an exposed method
        x = datetime.now()
        if 0 == self.last_read_time:
            logger.debug("First request, transmitting all points ")
            p = self.remote_point_dict
        else:
            # logger.debug("Processing request with last_read_time of: " + str(self.last_read_time))
            p = {}
            for key, point in self.remote_point_dict.items():
                if (point.last_update - self.last_read_time) > timedelta(seconds=0):
                    p.update({key: point})
        self.last_read_time = datetime.now()
        pickle_text = jsonpickle.encode(p)
        #logger.debug("transmitting: " + pickle_text)
        return pickle_text

    def exposed_get_thread_list(self):
        d = []
        for t in self.thread_list:
            d.append(t.pickle_dict)
        #logger.debug("sending: " + str(d))
        return jsonpickle.encode(d)

        #return jsonpickle.encode(self.thread_list)

    def exposed_get_active_alarm_list(self):
        return jsonpickle.encode(self.active_alarm_list)

    # TODO access the alarm through the active alarm list. There are alarms embedded in comm drivers
    def exposed_acknowledge_alarm(self, alarm: str):
        logger.info("RPC acknowledge received for " + alarm)
        self.global_alarm_list[alarm].acknowledge()

    def exposed_set_hmi_value(self, point: str, value: str):
        logger.info("attempting to set " + point + " to " + value)
        p = self.point_dict[point]
        p.hmi_value = value

    def exposed_toggle_point_force(self, point: str):
        self.point_dict[point].forced = not self.point_dict[point].forced

    def exposed_toggle_point_quality(self, point: str):
        self.point_dict[point].quality = not self.point_dict[point].quality
