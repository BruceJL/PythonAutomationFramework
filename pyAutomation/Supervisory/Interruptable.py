from abc import abstractmethod, ABC
from typing import Any


class Interruptable(ABC):

    @abstractmethod
    def interrupt(self, name: 'str', reason: 'Any') -> 'None':
        pass

    @abstractmethod
    @property
    def name(self) -> 'str':
        pass
