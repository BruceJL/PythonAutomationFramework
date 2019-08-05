from abc import abstractmethod, ABC

class Interruptable(ABC):

    @abstractmethod
    def interrupt(self, name: 'str'):
        pass
