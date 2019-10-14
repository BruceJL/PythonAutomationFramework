from pathlib import Path
from typing import Dict
import ruamel

from pyAutomation.DataObjects.PointAbstract import PointAbstract
from pyAutomation.DataObjects.ProcessValue import ProcessValue
from pyAutomation.DataObjects.PointReadOnly import PointReadOnly
from pyAutomation.DataObjects.PointReadOnlyAbstract \
    import PointReadOnlyAbstract
from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogDual import PointAnalogDual
from pyAutomation.DataObjects.PointAnalogScaled import PointAnalogScaled
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.PointEnumeration import PointEnumeration

from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.AlarmAnalog import AlarmAnalog
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread


GLOBAL_POINTS = {}  # type: Dict[str, PointAbstract]
GLOBAL_ALARMS = {}  # type: Dict[str, Alarm]


class PointManager:

    logger = None

    yml = ruamel.yaml.YAML(typ='safe', pure=True)
    yml.default_flow_style = False
    yml.register_class(PointAnalog)
    yml.register_class(PointAnalogDual)
    yml.register_class(PointAnalogScaled)
    yml.register_class(PointDiscrete)
    yml.register_class(PointEnumeration)
    yml.register_class(ProcessValue)
    yml.register_class(Alarm)
    yml.register_class(AlarmAnalog)

    @staticmethod
    def load_points(file: 'str') -> 'None':

        path = Path(file)
        data = None
        with path.open() as fp:
            data = PointManager().yml.load(fp)

        for k, o in data['points'].items():
            if isinstance(o, (
              PointAbstract,
              PointAnalogScaled,
              PointAnalogDual,
              ProcessValue,
            )):
                if k in GLOBAL_POINTS:
                    if isinstance(o, ProcessValue):
                        # ProcessValues get priority
                        GLOBAL_POINTS[k] = o
                else:
                    GLOBAL_POINTS[k] = o

            elif isinstance(o, (
              Alarm,
              AlarmAnalog,
            )):
                GLOBAL_ALARMS[k] = o
                o.name = k

        # now that the dict is fully populated, setup all the point names.
        for k, o in GLOBAL_POINTS.items():
            PointManager.logger.info("setting name for %s", k)
            o.config(k)

        for k, o in data['alarms'].items():
            if isinstance(o, Alarm) \
              or isinstance(o, AlarmAnalog):
                GLOBAL_ALARMS[k] = o
                o.config(k)

    @staticmethod
    def assign_points(
      data: 'Dict',
      target,
      target_name: 'str',
      thread: 'SupervisedThread',
    ) -> 'None':
        if 'points' in data:
            for point_name in data['points']:
                if 'name' in data['points'][point_name]:
                    db_name = data['points'][point_name]['name']
                    PointManager.logger.info(
                      "assigning database point %s"
                      + " to point: %s in module: %s", db_name, point_name,
                      target_name)
                    if 'access' in data['points'][point_name]:
                        db_rw = data['points'][point_name]['access']
                    else:
                        db_rw = None

                    PointManager().assign_point(
                      target=target,
                      object_point_name=point_name,
                      database_point_name=db_name,
                      db_rw=db_rw,
                      thread=thread,
                    )
                else:
                    PointManager.logger.info(
                      "skipping device: %s point: %s as"
                      + " it is unused", target_name, point_name)

    @staticmethod
    def assign_point(
      target,
      object_point_name: 'str',
      database_point_name: 'str',
      db_rw: 'str',
      thread: 'SupervisedThread',
    ) -> 'None':

        assert target.point_name_valid(object_point_name), \
            object_point_name + " is not a valid point for " + target.name

        # Determine the access level for this point.
        logic_rw = target.get_point_access(object_point_name)
        assert logic_rw is not None or db_rw is not None, \
            "Neither the config file or " + target.name + \
            " specfiy a access property for " + object_point_name

        if logic_rw is not None and db_rw is not None:
            assert logic_rw == db_rw, \
              " The config file and " + target.name + \
              " disagree on the r/w property for " + object_point_name
            rw = logic_rw

        elif db_rw is None:
            rw = logic_rw

        else:
            rw = db_rw

        obj_type = target.get_point_type(object_point_name)

        if obj_type in (
          'PointAnalog',
          'PointAnalogScaled',
          'PointDiscrete',
          'PointEnumeration',
          'PointAnalogDual',
          'ProcessValue',
        ):
            if 'rw' == rw:
                target.__dict__[object_point_name] = \
                  get_point_rw(
                    point_name=database_point_name,
                    writer=thread)

            elif 'ro' == rw:
                target.__dict__[object_point_name] = \
                  get_point_ro(
                    point_name=database_point_name)

        elif 'Alarm' == obj_type:
            if 'rw' == rw:
                target.__dict__[object_point_name] = \
                  get_alarm_rw(
                    alarm_name=database_point_name,
                    writer=thread)

            elif 'ro' == rw:
                target.__dict__[object_point_name] = \
                  get_alarm_ro(
                    alarm_name=database_point_name)
        else:
            assert False, target.name + " attempted to assign point " + \
              object_point_name + " with an invalid type of: " + obj_type

    @staticmethod
    def assign_parameters(data: 'Dict[str, str]', target) -> 'None':
        if 'parameters' in data:
            for parameter_name in data['parameters']:

                assert parameter_name in target.parameters, \
                  "tried to add: " + parameter_name + " to " \
                  + target.name + " but it's not in the parameter list"

                parameter_value = data['parameters'][parameter_name]
                PointManager().logger.info(
                  "assigning %s to %s in module %s",
                  parameter_value, parameter_name, target.name)

                target.__dict__[parameter_name] = parameter_value

    @staticmethod
    def global_points():
        return GLOBAL_POINTS

    @staticmethod
    def global_alarms():
        return GLOBAL_ALARMS

    @staticmethod
    def get_hmi_point(s: 'str') -> 'PointReadOnlyAbstract':
        return get_point_ro(s)


def find_point(name: 'str') -> 'PointAbstract':
    if name.find('.') == -1:
        assert name in GLOBAL_POINTS, \
            "Cannot locate " + name + " in point database."
        return GLOBAL_POINTS[name]
    else:
        array = name.split('.')
        assert array[0] in GLOBAL_POINTS, \
            "Cannot locate " + array[0] + " in point database. (" \
            + name + ")"
        point = GLOBAL_POINTS[array[0]]
        if array[1] == "control_points":
            return point.control_points[array[2]]
        elif array[1] == "related_points":
            return point.related_points[array[2]]


def get_point_rw(
  point_name: 'str',
  writer: 'SupervisedThread') -> 'PointAbstract':
    if 'None' != point_name:
        p = find_point(point_name).get_readwrite_object()
        assert isinstance(writer, SupervisedThread), \
           "Supplied writer (" + str(type(writer)) + ") for point '" \
           + point_name + "' is not a SupervisedThread"
        p.writer = writer
        return p


def get_point_ro(point_name: 'str') -> 'PointReadOnly':
    if 'None' != point_name:
        return find_point(point_name).get_readonly_object()


def get_process_ro(point_name: 'str') -> 'ProcessValue':
    if 'None' != point_name:
        return find_point(point_name).get_readonly_object()


def get_alarm_rw(
  alarm_name: 'str',
  writer: 'SupervisedThread') -> 'Alarm':
    if 'None' != alarm_name:
        assert isinstance(writer, SupervisedThread), \
           "Supplied writer (" + str(type(writer)) + ") for point '" \
           + alarm_name + "' is not a SupervisedThread"
        a = GLOBAL_ALARMS[alarm_name]
        a.writer = writer
        return GLOBAL_ALARMS[alarm_name]


def get_alarm_ro(alarm_name: 'str') -> 'Alarm':
    if 'None' != alarm_name:
        return GLOBAL_ALARMS[alarm_name]
