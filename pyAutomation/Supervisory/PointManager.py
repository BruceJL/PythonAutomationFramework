from pathlib import Path
from typing import TYPE_CHECKING
import ruamel

from pyAutomation.DataObjects.PointAbstract import PointAbstract
from pyAutomation.DataObjects.ProcessValue import ProcessValue
from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogDual import PointAnalogDual
from pyAutomation.DataObjects.PointAnalogScaled import PointAnalogScaled
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.PointEnumeration import PointEnumeration
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.AlarmAnalog import AlarmAnalog

if TYPE_CHECKING:
    from typing import Dict
    from pyAutomation.DataObjects.PointReadOnly import PointReadOnly
    from pyAutomation.DataObjects.PointReadOnlyAbstract \
      import PointReadOnlyAbstract

    from pyAutomation.Supervisory.PointHandler import PointHandler
    from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
    from logging import Logger

GLOBAL_POINTS = {}  # type: Dict[str, PointAbstract]
GLOBAL_ALARMS = {}  # type: Dict[str, Alarm]


class PointManager:
    ''' Singleton for managing the point database for a system. '''

    logger = None  # type: Logger

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
    def load_points_from_yaml_file(file: 'str') -> 'None':
        ''' Loads points from a yaml file. '''

        path = Path(file)
        data = None
        with path.open() as fp:
            data = PointManager().yml.load(fp)
        PointManager().load_point_from_yaml_string(data)

    @staticmethod
    def load_points_from_yaml_string(
      string: 'str',
    ):
        data = PointManager().yml.load(string)
        PointManager().load_points_from_yaml(data)
        PointManager().configure_points()

    @staticmethod
    def load_points_from_yaml(
      data,
    ) -> 'None':
        for name, obj in data['points'].items():
            PointManager().load_object(
              name=name,
              obj=obj,
            )
        PointManager().configure_points()

    @staticmethod
    def configure_points():
        # now that the dict is fully populated, setup all the point names.
        for k, o in GLOBAL_POINTS.items():
            PointManager.logger.info("setting name for %s", k)
            o.config(k)

    @staticmethod
    def load_object(
      name: 'str',
      obj,
    ):
        if isinstance(obj, (
          PointAbstract,
          PointAnalogScaled,
          PointAnalogDual,
          ProcessValue,
        )):
            if name in GLOBAL_POINTS:
                if isinstance(obj, ProcessValue):
                    # ProcessValues get priority
                    GLOBAL_POINTS[name] = obj
            else:
                GLOBAL_POINTS[name] = obj
            obj.name = name


        elif isinstance(obj, (
          Alarm,
          AlarmAnalog,
        )):
            GLOBAL_ALARMS[name] = obj
            obj.name = name

            for name, obj in data['alarms'].items():
              if isinstance(obj, Alarm) \
                or isinstance(obj, AlarmAnalog):
                  GLOBAL_ALARMS[name] = o
                  obj.config(name)

    @staticmethod
    def assign_points(
      data: 'Dict',
      point_handler: 'PointHandler',
      target_name: 'str',
      supervised_thread: 'SupervisedThread',
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
                      point_handler=point_handler,
                      object_point_name=point_name,
                      database_point_name=db_name,
                      db_rw=db_rw,
                      supervised_thread=supervised_thread,
                      extra_data=data['points'][point_name]
                    )
                else:
                    PointManager.logger.info(
                      "skipping device: %s point: %s as"
                      + " it is unused", target_name, point_name)

    @staticmethod
    def assign_point(
      point_handler: 'PointHandler',
      object_point_name: 'str',
      database_point_name: 'str',
      db_rw: 'str',
      supervised_thread: 'SupervisedThread',
      extra_data: 'Dict[str, str]',
    ) -> 'None':

        assert point_handler.point_name_valid(object_point_name), \
            ("{} is not a valid point for {}").format(
              object_point_name,
              point_handler.name,
          )

        # Determine the access level for this point.
        logic_rw = point_handler.get_point_access(object_point_name)
        assert logic_rw is not None or db_rw is not None, \
            "Neither the config file or " + point_handler.name + \
            " specfiy a access property for " + object_point_name

        if logic_rw is not None and db_rw is not None:
            assert logic_rw == db_rw, \
              " The config file and " + point_handler.name + \
              " disagree on the r/w property for " + object_point_name
            rw = logic_rw

        elif db_rw is None:
            rw = logic_rw

        else:
            rw = db_rw

        obj_type = point_handler.get_point_type(object_point_name)

        if obj_type in (
          'PointAnalog',
          'PointAnalogScaled',
          'PointDiscrete',
          'PointEnumeration',
          'PointAnalogDual',
          'ProcessValue',
        ):
            if rw == 'rw':
                point_handler.add_point(
                  name=object_point_name,
                  point=__get_point_rw(
                    point_name=database_point_name,
                    supervised_thread=supervised_thread,
                  ),
                  access=rw,
                  extra_data=extra_data,
                )

            elif rw == 'ro':
                point_handler.add_point(
                  name=object_point_name,
                  point=__get_point_ro(
                    point_name=database_point_name,
                  ),
                  access=rw,
                  extra_data=extra_data,
                )
            else:
                assert False, (
                  "Invalid read/write property of {} assigned to point {}} of "
                   + "module {}").format(
                       rw,
                       object_point_name,
                       point_handler.name,
                  )

        elif 'Alarm' == obj_type:
            if 'rw' == rw:
                point_handler.__dict__[object_point_name] = \
                  __get_alarm_rw(
                    alarm_name=database_point_name,
                    writer=supervised_thread,
                  )

            elif 'ro' == rw:
                point_handler.__dict__[object_point_name] = \
                  __get_alarm_ro(
                    alarm_name=database_point_name,
                  )
            else:
                assert False, (
                  "Invalid read/write property of {} assigned to point {} of "
                  +" module {}").format(
                    rw,
                    object_point_name,
                    point_handler.name
                  )

        elif obj_type == 'Primative':
            # this is the case for I/O drivers that can be agnostic with the
            # points that they are assigned. We should only allow PointAnalogs,
            # PointAnalogScaleds, and PointDiscretes. Alarms would be nice too,
            # but the behaviour is too ambigious, do we sent the in condition or
            # the alarm condition? Best to have the designer declare it
            # explicitly in thier logic. Plus, I don't want to have to figure
            # out how to determine whether to interrogate the point or the alarm
            # database.

            if rw == 'rw':
                point_handler.add_point(
                  name=database_point_name,
                  point=__get_point_rw(
                    point_name=database_point_name,
                    supervised_thread=supervised_thread,
                  ),
                  access='rw',
                )

            elif rw == 'ro':
                point_handler.add_point(
                  name=database_point_name,
                  point=__get_point_ro(
                    point_name=database_point_name,
                  ),
                  access='ro',
                )

        else:
            assert False, point_handler.name + " attempted to assign point " + \
              object_point_name + " with an invalid type of: " + obj_type

    @staticmethod
    def assign_parameters(
      data: 'Dict[str, str]',
      target) -> 'None':
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
        return find_point(s)


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


def __get_point_rw(
  point_name: 'str',
  supervised_thread: 'SupervisedThread',
) -> 'PointAbstract':
    if 'None' != point_name:
        p = find_point(point_name).get_readwrite_object()
        assert isinstance(supervised_thread, SupervisedThread), (
           f"Supplied writer ({str(type(supervised_thread))}) for point"
           f"'{point_name}' is not a SupervisedThread")
        p.writer = supervised_thread
        return p


def __get_point_ro(point_name: 'str') -> 'PointReadOnly':
    if 'None' != point_name:
        return find_point(point_name).readonly_object


def __get_process_ro(point_name: 'str') -> 'ProcessValue':
    if 'None' != point_name:
        return find_point(point_name).readonly_object


def __get_alarm_rw(
  alarm_name: 'str',
  writer: 'SupervisedThread') -> 'Alarm':
    if 'None' != alarm_name:
        assert isinstance(writer, SupervisedThread), \
           "Supplied writer (" + str(type(writer)) + ") for point '" \
           + alarm_name + "' is not a SupervisedThread"
        a = GLOBAL_ALARMS[alarm_name]
        a.writer = writer
        return GLOBAL_ALARMS[alarm_name]


def __get_alarm_ro(alarm_name: 'str') -> 'Alarm':
    if 'None' != alarm_name:
        return GLOBAL_ALARMS[alarm_name]
