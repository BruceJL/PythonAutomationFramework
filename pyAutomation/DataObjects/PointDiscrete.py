import logging
from typing import TYPE_CHECKING
from .PointAbstract import PointAbstract

if TYPE_CHECKING:
    from .PointReadOnly import PointReadOnly
    from typing import List, Dict, Any

logger = logging.getLogger('controller')


class PointDiscrete(PointAbstract):
    yaml_tag = u'!PointDiscrete'

    def __init__(self, **kwargs):
        self.on_state_description = "ON"
        self.off_state_description = "OFF"
        super().configure_parameters(**kwargs)

    @property
    def keywords(self) -> 'List[str]':
        return super().keywords + \
          ['on_state_description', 'off_state_description']

    # value accessed through HMI
    @property
    def hmi_value(self) -> 'str':
        return super()._get_hmi_value()

    @hmi_value.setter
    def hmi_value(self, v: 'str'):
        if not isinstance(v, str):
            raise ValueError('Supply argument %s is not a string' % v)
        # if v == "True":
        #     x = True
        # else:
        #     x = False
        super()._set_hmi_value(v)

    @property
    def readonly(self) -> 'bool':
        return False

    # human readable value
    @property
    def human_readable_value(self) -> str:
        if self.hmi_value:
            return self.on_state_description
        else:
            return self.off_state_description

    # data display width
    @property
    def data_display_width(self) -> int:
        i = len(self.off_state_description)
        if len(self.on_state_description) > i:
            i = len(self.off_state_description)
        assert isinstance(i, int)
        return i

    # HMI window type
    @property
    def hmi_object_name(self) -> 'str':
        return "PointDiscreteWindow"

    @property
    def readonly_object(self) -> 'PointReadOnly':
        return PointReadOnly(self)

    @property
    def readwrite_object(self) -> 'PointDiscrete':
        return self

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = super().__getstate__()
        d.update({
          'on_state_description': self.on_state_description,
          'off_state_description': self.off_state_description,
        })
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        super().__setstate__(d)
        self.on_state_description = d['on_state_description']
        self.off_state_description = d['off_state_description']

    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = super().yaml_dict
        d.update({
          'on_state_description': self.on_state_description,
          'off_state_description': self.off_state_description,
        })
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointDiscrete',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)
        return PointDiscrete(**value)
