import logging
from datetime import datetime, timedelta
from .PointAbstract import PointAbstract
from abc import abstractmethod, ABC
from typing import Dict, TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from .Alarm import Alarm
    from pyAutomation.Supervisory.Interruptable import Interruptable

logger = logging.getLogger('controller')


class Point(PointAbstract, ABC):



