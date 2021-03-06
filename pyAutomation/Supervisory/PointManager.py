from pathlib import Path
from typing import TYPE_CHECKING
import logging
import ruamel
from ruamel.yaml.compat import StringIO

from pyAutomation.DataObjects.PointAbstract import PointAbstract
from pyAutomation.DataObjects.ProcessValue import ProcessValue
from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogReadOnly import PointAnalogReadOnly
from pyAutomation.DataObjects.PointReadOnly import PointReadOnly
from pyAutomation.DataObjects.PointAnalogDual import PointAnalogDual
from pyAutomation.DataObjects.PointAnalogScaled import PointAnalogScaled
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.PointEnumeration import PointEnumeration
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.AlarmAnalog import AlarmAnalog
from pyAutomation.Supervisory.Interruptable import Interruptable
from pyAutomation.Supervisory.ConfigurationException import \
  ConfigurationException

if TYPE_CHECKING:
    from typing import Dict, Any
    from pyAutomation.DataObjects.PointReadOnlyAbstract \
      import PointReadOnlyAbstract

    from pyAutomation.Supervisory.PointHandler import PointHandler
    from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
    from logging import Logger

GLOBAL_POINTS = {}  # type: Dict[str, PointAbstract]
GLOBAL_ALARMS = {}  # type: Dict[str, Alarm]

logger = logging.getLogger('controller')  # type: Logger

# yml parser configuration
yml = ruamel.yaml.YAML(typ='safe', pure=True)
yml.default_flow_style = False
yml.indent(sequence=4, offset=2)

# Register all the requried classes.
yml.register_class(PointAnalog)
yml.register_class(PointAnalogDual)
yml.register_class(PointAnalogScaled)
yml.register_class(PointDiscrete)
yml.register_class(PointEnumeration)
yml.register_class(ProcessValue)
yml.register_class(Alarm)
yml.register_class(AlarmAnalog)
yml.register_class(PointAnalogReadOnly)
yml.register_class(PointReadOnly)


class PointManager:
    ''' Singleton for managing the point database for a system. '''

    @staticmethod
    def load_points_from_yaml_file(file: 'str') -> 'None':
        """ Loads points from a yaml file.

        Parameters:
        file (str): fully qualified path of file to load.

        Returns:
        None

        """

        path = Path(file)
        data = None
        with path.open() as fp:
            data = yml.load(fp)

        for name, obj in data['points'].items():
            PointManager().add_to_database(
              name=name,
              obj=obj,
            )

    @staticmethod
    def load_points_from_yaml_string(string: 'str',) -> 'None':
        data = yml.load(string)
        for name, obj in data['points'].items():
            PointManager().add_to_database(
              name=name,
              obj=obj,
            )

    @staticmethod
    def dump_database_to_yaml() -> 'str':
        stream = StringIO()
        yml.dump(
          {
            'points': GLOBAL_POINTS,
            'alarms': GLOBAL_ALARMS,
          },
          stream,
        )
        return stream.getvalue()

    @staticmethod
    def clear_database() -> 'None':
        GLOBAL_ALARMS.clear()
        GLOBAL_POINTS.clear()

    @staticmethod
    def add_to_database(
      name: 'str',
      obj: 'Any',
    ):
        ''' Add a point to the global point database '''

        if isinstance(
          obj, (
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
            obj.config()

        elif isinstance(obj, (
          Alarm,
          AlarmAnalog,
        )):
            GLOBAL_ALARMS[name] = obj
            obj.name = name

    @staticmethod
    def assign_points(
      data: 'Dict[str, Any]',
      point_handler: 'PointHandler',
      target_name: 'str',
      interruptable: 'Interruptable',
    ) -> 'None':
        if 'points' in data:
            for point_name in data['points']:
                if 'name' in data['points'][point_name]:
                    db_name = data['points'][point_name]['name']
                    logger.info(
                      f"assigning database point {db_name}"
                      f" to point: {point_name} in module: {target_name}"
                    )
                    if 'access' in data['points'][point_name]:
                        db_rw = data['points'][point_name]['access']
                    else:
                        db_rw = None

                    PointManager().assign_point(
                      point_handler=point_handler,
                      point_handler_point_name=point_name,
                      database_point_name=db_name,
                      db_rw=db_rw,
                      interruptable=interruptable,
                      extra_data=data['points'][point_name]
                    )
                else:
                    logger.info(
                      f"skipping device: {target_name} point: {point_name} as"
                      " it is unused"
                    )

    @staticmethod
    def assign_point(
      point_handler: 'PointHandler',
      point_handler_point_name: 'str',
      database_point_name: 'str',
      db_rw: 'str',
      interruptable: 'Interruptable',
      extra_data: 'Dict[str, str]',
    ) -> 'None':
        ''' Assigns a point to a PointHandler
            maps the point in the PointHandler "point_handler_point_name" to the
            point in the database "database_point_name".

            Verifies that the r/w property agrees if possible and places the
            PointHandler in the points interrupt queue.

            Provides the ability to supply a dict with extra information about
            how the point is to be assigned. May continue information such as
            mapping to communications systems.

        '''

        # test to make sure that the point_handler will accept the name of the
        # point being assigned.
        assert point_handler.point_name_valid(point_handler_point_name), (
          f"{point_handler_point_name} is not a valid point for: "
          f"{point_handler.name}"
        )

        # Determine the access level for this point.
        logic_rw = point_handler.get_point_access(point_handler_point_name)
        if logic_rw is None and db_rw is None:
            raise ConfigurationException(
              f"Neither the config file or {point_handler.name} "
              f"specfiy a access property for {point_handler_point_name}"
            )

        if logic_rw is not None and db_rw is not None:
            if logic_rw != db_rw:
                raise ConfigurationException(
                  f"The config file and {point_handler.name} "
                  f"disagree on the r/w property for {point_handler_point_name}"
              )
            rw = logic_rw

        elif db_rw is None:
            rw = logic_rw

        else:
            rw = db_rw

        # get the
        obj_type = point_handler.get_point_type(point_handler_point_name)

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
                  name=point_handler_point_name,
                  point=PointManager().__get_point_rw(
                    point_name=database_point_name,
                    interruptable=interruptable,
                  ),
                  access=rw,
                  extra_data=extra_data,
                )

            elif rw == 'ro':
                point_handler.add_point(
                  name=point_handler_point_name,
                  point=PointManager().__get_point_ro(
                    point_name=database_point_name,
                  ),
                  access=rw,
                  extra_data=extra_data,
                )
            else:
                raise ConfigurationException(
                  f"Invalid read/write property of {rw} assigned to point "
                  f"{point_handler_point_name} of module {point_handler.name}"
                )

        elif 'Alarm' == obj_type:
            if 'rw' == rw:
                point_handler.__dict__[point_handler_point_name] = \
                  PointManager().__get_alarm_rw(
                    alarm_name=database_point_name,
                    writer=interruptable,
                  )

            elif 'ro' == rw:
                point_handler.__dict__[point_handler_point_name] = \
                  PointManager().__get_alarm_ro(
                    alarm_name=database_point_name,
                  )
            else:
                assert False, (
                  f"Invalid read/write property of {rw} assigned to point "
                  f"{point_handler_point_name} of module {point_handler.name}"
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
                  point=PointManager().__get_point_rw(
                    point_name=database_point_name,
                    interruptable=interruptable,
                  ),
                  extra_data=extra_data,
                  access='rw',
                )

            elif rw == 'ro':
                point_handler.add_point(
                  name=database_point_name,
                  point=PointManager().__get_point_ro(
                    point_name=database_point_name,
                  ),
                  access='ro',
                  extra_data=extra_data,
                )

        else:
            assert False, point_handler.name + " attempted to assign point " + \
              point_handler_point_name + " with an invalid type of: " + obj_type

    @staticmethod
    def assign_parameters(
      data: 'Dict[str, Dict[str, str]]',
      target: 'PointHandler',
    ) -> 'None':
        if 'parameters' in data:
            for parameter_name in data['parameters']:

                assert parameter_name in target.parameters, (
                  f"tried to add: {parameter_name} to {target.name} but it's "
                  f"not in the parameter list")

                parameter_value = data['parameters'][parameter_name]
                logger.info(f"assigning {parameter_value} to {parameter_name} "
                  "in module {target.name}")

                target.__dict__[parameter_name] = parameter_value

    @staticmethod
    def global_points():
        return GLOBAL_POINTS

    @staticmethod
    def global_alarms():
        return GLOBAL_ALARMS

    @staticmethod
    def get_hmi_point(s: 'str') -> 'PointReadOnlyAbstract':
        return PointManager().find_point(s)

    @staticmethod
    def find_point(name: 'str') -> 'PointAbstract':
        if name.find('.') == -1:
            assert name in GLOBAL_POINTS, \
                "Cannot locate " + name + " in point database."
            return GLOBAL_POINTS[name]
        else:
            array = name.split('.')
            assert array[0] in GLOBAL_POINTS, (
                f"Cannot locate {array[0]} in point database. ({name})")

            point = GLOBAL_POINTS[array[0]]
            if array[1] == "control_points":
                return point.control_points[array[2]]
            elif array[1] == "related_points":
                return point.related_points[array[2]]
            else:
                raise ValueError(f"process value name {name} is malformed.")

    @staticmethod
    def get_point_test(point_name: 'str'):
        """ Used when creating test benches to retrieve points without all
        of the dressing usually required

        """
        return PointManager().find_point(point_name).readwrite_object

    @staticmethod
    def __get_point_rw(
      point_name: 'str',
      interruptable: 'Interruptable',
    ) -> 'PointAbstract':
        if 'None' != point_name:
            p = PointManager().find_point(point_name).readwrite_object
            assert isinstance(interruptable, Interruptable), (
              f"Supplied writer ({str(type(interruptable))}) for point"
              f"'{point_name}' is not an Interruptable")
            p.writer = interruptable
            return p

    @staticmethod
    def __get_point_ro(point_name: 'str') -> 'PointReadOnly':
        if 'None' != point_name:
            return PointManager().find_point(point_name).readonly_object

    @staticmethod
    def __get_process_ro(point_name: 'str') -> 'ProcessValue':
        if 'None' != point_name:
            return PointManager().find_point(point_name).readonly_object

    @staticmethod
    def __get_alarm_rw(
    alarm_name: 'str',
    writer: 'SupervisedThread') -> 'Alarm':
        if 'None' != alarm_name:
            assert isinstance(writer, SupervisedThread), (
                f"Supplied writer ({str(type(writer))}) for point "
                f"'{alarm_name}' is not a SupervisedThread"
            )
            a = GLOBAL_ALARMS[alarm_name]
            a.writer = writer
            return GLOBAL_ALARMS[alarm_name]

    @staticmethod
    def __get_alarm_ro(alarm_name: 'str') -> 'Alarm':
        if 'None' != alarm_name:
            return GLOBAL_ALARMS[alarm_name]
