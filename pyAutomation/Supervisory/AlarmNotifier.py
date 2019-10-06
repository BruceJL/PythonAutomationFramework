from abc import ABC, abstractmethod
from pyAutomation.DataObjects.Alarm import Alarm


class AlarmNotifier(ABC):

    @abstractmethod
    def notify(self, alarm: Alarm, verb: str) -> None:
        pass
