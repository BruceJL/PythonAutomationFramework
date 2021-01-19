from abc import ABC
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from typing import Callable, Any, Dict

logger = logging.getLogger('controller')


class Observable(ABC):

    # name of the point in the global point dict.
    _name = None  # type: Any

    # human readable description of the point
    _description = "No description"

    # object that is able to write to this point.
    _writer = None  # type: object

    _observers = {}  # type: Dict[str, Callable]

    # name
    @property
    def name(self) -> 'str':
        assert self._name is not None, \
          "name is not populated for '" + self.description + "'."
        return self._name

    # description
    @property
    def description(self) -> str:
        return self._description

    # Get and set the owner process
    @property
    def writer(self):
        return self._writer

    @property
    def observers(self) -> 'Dict[str, Callable[[str, Any], str]]':
        return self._observers

    def add_observer(
      self,
      name: 'str',
      observer: 'Callable[[str, Any], Any]') -> 'None':
        """
        Adds an interested routine to this alarm's observer list. This routine
        will be notified whenever this alarm goes from active to inactive or
        vise-versa.
        """

        assert name is not None, (
          "No name supplied for observer added to %s" % self.description
        )
        self._observers.update({name: observer})

        logger.info(f"observer: {name} added to point {self.name}")

    def del_observer(self, name: 'str') -> 'None':
        """ Removes an interseted routine from this alarm's observer list. """
        self._observers.pop(name)
        logger.info(f"observer: {name} removed from point {self.name}")
