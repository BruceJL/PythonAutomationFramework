from typing import TYPE_CHECKING
from .PointAbstract import PointAbstract
from .PointReadOnly import PointReadOnly

if TYPE_CHECKING:
    from typing import Dict, Any, List
    from .PointReadOnlyAbstract import PointReadOnlyAbstract


class PointEnumeration(PointAbstract):

    states = []  # type: List[str]

    def __init__(self, **kwargs) -> None:
        tmp_value = None
        if 'value' in kwargs:
            tmp_value = kwargs['value']
            kwargs.pop('value', None)

        super().configure_parameters(**kwargs)

        if tmp_value is not None:
            self._value = tmp_value

    @property
    def keywords(self):
        return super().keywords + ['states']

    # hmi_value
    @property
    def hmi_value(self) -> 'str':
        return self.value

    @hmi_value.setter
    def hmi_value(self, v: 'str') -> 'None':
        self.value = v

    # value
    @property
    def value(self) -> 'str':
        return self.states[self._value]

    @value.setter
    def value(self, v: 'str') -> 'None':
        assert v in self.states, "Tried to set " + self.description + \
          " to a state of " + str(v) + " which is not a valid state."
        self._value = self.states.index(v)

    @property
    def data_display_width(self) -> 'int':
        x = 0
        for s in self.states:
            if len(s) > x:
                x = len(s)
        return x

    @property
    def hmi_object_name(self) -> 'str':
        return "PointEnumerationWindow"

    @property
    def readonly(self) -> 'bool':
        return False

    @property
    def readonly_object(self) -> 'PointReadOnlyAbstract':
        return PointReadOnly(self)

    @property
    def readwrite_object(self) -> 'PointEnumeration':
        return self

    def __getstate__(self) -> 'Dict[str, Any]':
        """
        Gets a dict representation of the point suitable for JSON
        transport to an HMI client. This function is specified by the
        jsonpickle library to pickle an object.

        Returns:
            dict: a dict of point properties.

        """
        d = super().__getstate__()
        d.update({'states': self.states})
        return d

    def __setstate__(self, d: 'Dict[str, Any]'):
        self.states = d['states']
        super().__setstate__(d)

    # used to produce a yaml representation for config storage.
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = super().yaml_dict
        d.update({'states': self.states})
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointEnumeration',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        # d = constructor.construct_mapping(node, deep=True)
        # return PointEnumeration(**d)
        value = constructor.construct_mapping(node, deep=True)

        p = PointEnumeration(
          states = value['states'],
          description = value['description'],
          hmi_writeable = value['hmi_writeable'],
          requestable = value['requestable'],
          retentive = value['retentive'],
          update_period = value['update_period'],
        )

        return p
