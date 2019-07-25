from abc import abstractmethod, ABC


class AbstractWindow(ABC):

    @abstractmethod
    def hmi_get_user_input(self) -> None:
        pass

    @abstractmethod
    def hmi_window_size(self) -> [int, int]:
        pass

    @abstractmethod
    def hmi_draw_window(self) -> None:
        pass
