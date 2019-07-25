from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

class PointSaveable(ABC):

    @abstractmethod
    def get_yaml_object(self) -> 'Dict[str, Any]':
        pass
