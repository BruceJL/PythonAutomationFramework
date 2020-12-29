from typing import TYPE_CHECKING
from .PointAbstract import PointAbstract
from .PointReadOnly import PointReadOnly

if TYPE_CHECKING:
    from typing import Dict, Any, List
    from .PointReadOnlyAbstract import PointReadOnlyAbstract


class PointEnumeration(PointAbstract):

    def __init__(self, **kwargs) -> None:
        self.states = []  # type: List[str]

        tmp_value = None
        if 'value' in kwargs:
            tmp_value = kwargs['value']
            kwargs.pop('value', None)

        super().configure_parameters(**kwargs)

        if tmp_value is not None:
            super()._set_value(tmp_value)

    def _get_keywords(self):
        return super().keywords + ['states']

    keywords = property(_get_keywords)

    # human readable value
    def _get_human_readable_value(self) -> 'str':
        return self.states[self._value]

    # hmi_value
    def _get_hmi_value(self):
        return self.value

    def _set_hmi_value(self, v: 'str'):
        assert v in self.states, \
          "Tried to set " + self.description + " to a state of " + v + \
          " which is not a valid state."
        super()._set_hmi_value(v)

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # value
    def _get_value(self) -> 'str':
        return self.states[super()._get_value()]

    def _set_value(self, v: "str") -> 'None':
        assert v in self.states, "Tried to set " + self.description + \
          " to a state of " + str(v) + " which is not a valid state."

        super()._set_value(self.states.index(v))

    value = property(_get_value, _set_value)

    # forced value
    def _get_forced_value(self):
        return self.states[super().value]

    def _set_forced_value(self, v):
        super().forced_value(self.states.index(v))

    def _get_data_display_width(self) -> 'int':
        x = 0
        for s in self.states:
            if len(s) > x:
                x = len(s)
        return x

    def _get_hmi_object_name(self)-> 'str':
        return "PointEnumerationWindow"

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

    def yaml_dict(self) -> 'Dict[str, Any]':
        d = super().yaml_dict
        d.update(dict(states=self.states))
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointEnumeration',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        d = constructor.construct_mapping(node)
        return PointEnumeration(**d)
