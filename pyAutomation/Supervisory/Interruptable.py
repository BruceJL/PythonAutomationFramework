from abc import abstractmethod, ABC
from typing import Any


class Interruptable(ABC):

    @abstractmethod
    def interrupt(self, name: 'str', reason: 'Any') -> 'None':
        pass


    @property
    @abstractmethod
    def name(self) -> 'str':
        pass

    @name.setter
    def name(self, name) -> 'None':
        pass
