import jsonpickle
import rpyc
from typing import List, TYPE_CHECKING
from datetime import datetime, timedelta
import logging

if TYPE_CHECKING:
    from DataObjects.Alarm import Alarm
    from DataObjects.PointAbstract import PointAbstract
    from DataObjects.PointReadOnlyAbstract import PointReadOnlyAbstract
    from Supervisory.SupervisedThread import SupervisedThread

logger = logging.getLogger('controller')


# define the rpyc server
class RpcServer(rpyc.Service):
    active_alarm_list = None  # type: List[Alarm]
    point_list = []  # type: List[PointReadOnlyAbstract]
    global_alarm_list = None  # type: Dict[str, Alarm]
    point_dict = {}  # type: Dict[str, PointAbstract]
    thread_list = [] # type: List[SupervisedThread]
    last_read_time = None  # type: datetime

    def on_connect(self):
        # code that runs when a connection is created
        # (to init the serivce, if needed)
        logger.info("GUI Connection Established")
        self.last_read_time = 0

    def on_disconnect(self):
        # code that runs when the connection has already closed
        # (to finalize the service, if needed)
        logger.info("GUI Connection Destroyed")

    def exposed_get_hmi_points_list(self):  # this is an exposed method
        x = datetime.now()
        if 0 == self.last_read_time:
            logger.debug("First request, transmitting all points ")
            p = self.point_list
        else:
            # logger.debug("Processing request with last_read_time of: " + str(self.last_read_time))
            p = []
            for point in self.point_list:
                if (point.last_update - self.last_read_time) > timedelta(seconds=0):
                    p.append(point)
        self.last_read_time = datetime.now()
        pickle_text = jsonpickle.encode(p)
        return pickle_text

    def exposed_get_thread_list(self):
        return jsonpickle.encode(self.thread_list)

    def exposed_get_active_alarm_list(self):
        return jsonpickle.encode(self.active_alarm_list)

    # TODO access the alarm through the active alarm list. There are alarms embedded in comm drivers
    def exposed_acknowledge_alarm(self, alarm: str):
        logger.info("RPC acknowledge received for " + alarm)
        self.global_alarm_list[alarm].acknowledge()

    def exposed_set_hmi_value(self, point: str, value: str):
        logger.debug("attempting to set " + point + " to " + value)
        p = self.point_dict[point]
        p.hmi_value = value

    def exposed_toggle_point_force(self, point: str):
        self.point_dict[point].forced = not self.point_dict[point].forced

    def exposed_toggle_point_quality(self, point: str):
        self.point_dict[point].quality = not self.point_dict[point].quality
